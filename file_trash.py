"""Recoverable file removal with a portable journal and standalone restoration."""
import ctypes
import fcntl
import hashlib
import json
import os
import re
import shutil
import sqlite3
import stat
import threading
import unicodedata
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from contextlib import closing

LOCK = threading.RLock()
HISTORY = Path('.folder-layout-history/.file-trash')
PROTECTED = {'!.txt', '!order.txt', '!status.txt', '.order.json', 'status.txt', '.status.txt'}


class TrashConflict(ValueError):
    pass


def checked(root, relative, hidden=False):
    if not isinstance(relative, str) or '\x00' in relative:
        raise ValueError('Некорректный путь')
    path = Path(relative)
    if path.is_absolute() or '..' in path.parts or (not hidden and any(part.startswith('.') for part in path.parts)):
        raise ValueError('Путь за пределами доступных файлов')
    for index in range(1, len(path.parts) + 1):
        if (root / Path(*path.parts[:index])).is_symlink():
            raise ValueError('Символические ссылки не перемещаются')
    return root / path


def fingerprint(path):
    value = path.lstat()
    return {'device': value.st_dev, 'inode': value.st_ino, 'kind': stat.S_IFMT(value.st_mode),
            'size': value.st_size, 'modified': value.st_mtime_ns}


def revision(path):
    return hashlib.sha256(json.dumps([fingerprint(path), path.lstat().st_ctime_ns], sort_keys=True).encode()).hexdigest()


def same(path, expected):
    if not path.exists() or path.is_symlink():
        return False
    value = fingerprint(path)
    keys = ('device', 'inode', 'kind') if expected['kind'] == stat.S_IFDIR else expected.keys()
    return all(value[key] == expected[key] for key in keys)


def rename(source, destination):
    function = ctypes.CDLL(None, use_errno=True).renamex_np
    function.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint)
    function.restype = ctypes.c_int
    if function(os.fsencode(source), os.fsencode(destination), 4):
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(destination))


def append(session, **record):
    record = {'time': datetime.now(ZoneInfo('Europe/Moscow')).isoformat(), **record}
    with (session / '.journal.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def preview(root, folder, paths):
    root = Path(root).resolve()
    parent = checked(root, folder)
    if not parent.is_dir():
        raise FileNotFoundError('Открытая папка не найдена')
    if not isinstance(paths, list) or not paths or len(paths) > 1000 or any(not isinstance(path, str) for path in paths):
        raise ValueError('Выберите от 1 до 1000 файлов')
    items = []
    for relative in dict.fromkeys(paths):
        path = checked(root, relative)
        if parent not in path.parents or path.name in PROTECTED:
            raise ValueError('Можно удалять только обычные файлы открытой папки и её подпапок')
        if not path.is_file() or not stat.S_ISREG(path.lstat().st_mode):
            raise ValueError('Файл не найден или заменён: ' + relative)
        items.append({'path': relative, 'name': path.name, 'size': path.stat().st_size, 'revision': revision(path)})
    return {'folder': folder, 'files': items}


def session_path(root, token):
    if not isinstance(token, str) or not re.fullmatch('[a-f0-9]{32}', token):
        raise ValueError('Некорректный сеанс корзины')
    return checked(root, (HISTORY / ('.' + token)).as_posix(), hidden=True)


def read_plan(root, token):
    session = session_path(root, token)
    plan_path = checked(root, (session.relative_to(root) / '.plan.json').as_posix(), hidden=True)
    plan = json.loads(plan_path.read_text(encoding='utf-8'))
    if plan.get('kind') != 'file-trash' or plan.get('root') != str(root) or plan.get('session') != token:
        raise ValueError('План корзины не соответствует корню документов')
    for operation in plan['operations']:
        checked(root, operation['source'], hidden=True)
        destination = checked(root, operation['destination'], hidden=True)
        if session / '.files' not in destination.parents:
            raise ValueError('Некорректное место хранения удалённого файла')
    return session, plan


def describe(root, plan):
    pending = []
    removed = []
    for item in plan['files']:
        operations = [op for op in plan['operations'] if op['file'] == item['path']]
        if any(os.path.lexists(root / op['destination']) for op in operations):
            pending.append(item['path'])
        if any(op['source'] == item['path'] and same(root / op['destination'], op['identity']) for op in operations):
            removed.append(item['path'])
    if plan.get('database'):
        with closing(sqlite3.connect(Path(plan['database']).as_uri()+'?mode=rw',uri=True,timeout=15)) as db:
            for (path,) in db.execute("SELECT source FROM metadata_file_moves WHERE session=? AND state!='restored'",(plan['session'],)):
                if path not in pending:
                    pending.append(path)
    return {'session': plan['session'], 'folder': plan['folder'], 'created': plan['created'],
            'files': pending, 'count': len(pending), 'removed': removed}


def database_move(plan, operation, *, restore=False, finish=False):
    """Durable comment relocation; also works from the standalone restore script."""
    if not plan.get('database') or operation['source']!=operation['file']:
        return
    source = unicodedata.normalize('NFC',operation['source'])
    destination = unicodedata.normalize('NFC',operation['destination'])
    with closing(sqlite3.connect(Path(plan['database']).as_uri()+'?mode=rw',uri=True,timeout=15)) as db, db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT state FROM metadata_file_moves WHERE session=? AND source=?',(plan['session'],source)).fetchone()
        if restore:
            if not row or row[0]=='restored':
                return
            original = db.execute("SELECT id FROM metadata_records WHERE kind='comment' AND path=?",(source,)).fetchone()
            stored = db.execute("SELECT id FROM metadata_records WHERE kind='comment' AND path=?",(destination,)).fetchone()
            if original:
                raise TrashConflict('По исходному пути появился другой комментарий; восстановление остановлено: '+source)
            if not finish:
                db.execute("UPDATE metadata_file_moves SET state='pending' WHERE session=? AND source=?",(plan['session'],source))
            if finish:
                if stored:
                    db.execute("UPDATE metadata_records SET path=?,revision=revision+1 WHERE kind='comment' AND path=?",(source,destination))
                db.execute("UPDATE metadata_file_moves SET state='restored' WHERE session=? AND source=?",(plan['session'],source))
        elif finish:
            db.execute("UPDATE metadata_file_moves SET state='trashed' WHERE session=? AND source=?",(plan['session'],source))
        elif not row:
            db.execute("INSERT INTO metadata_file_moves VALUES (?,?,?,'pending')",(plan['session'],source,destination))
            db.execute("UPDATE metadata_records SET path=?,revision=revision+1 WHERE kind='comment' AND path=?",(destination,source))


def remove(root, folder, files, confirmed=False, database=None):
    root = Path(root).resolve()
    if confirmed is not True or not isinstance(files, list) or any(not isinstance(item, dict) for item in files):
        raise ValueError('Подтвердите удаление выбранных файлов')
    with LOCK:
        current = preview(root, folder, [item.get('path') for item in files])
        if len(files) != len(current['files']) or any(item.get('revision') != now['revision'] for item, now in zip(files, current['files'])):
            raise TrashConflict('Файлы изменились после открытия подтверждения. Проверьте выбор заново.')
        token = uuid.uuid4().hex
        session = session_path(root, token)
        operations = []
        for index, item in enumerate(current['files']):
            path = root / item['path']
            key = hashlib.sha256(unicodedata.normalize('NFC', path.name).encode()).hexdigest()
            sidecar = path.parent / '.file-comments' / ('.' + key + '.txt')
            history = sidecar.parent / '.history' / ('.' + key)
            for source in (sidecar, history, path):
                checked(root, source.relative_to(root).as_posix(), hidden=True)
                if not source.exists():
                    continue
                if source == sidecar and not source.is_file() or source == history and not source.is_dir():
                    raise ValueError('Некорректные служебные данные комментария')
                destination = session / '.files' / f'.{index:04}' / source.relative_to(path.parent)
                operations.append({'source': source.relative_to(root).as_posix(),
                                   'destination': destination.relative_to(root).as_posix(),
                                   'identity': fingerprint(source), 'file': item['path']})
        # The plan is durable before any user file or comment is moved.
        session.mkdir(parents=True)
        plan = {'kind': 'file-trash', 'root': str(root), 'session': token, 'folder': folder,
                'created': datetime.now(ZoneInfo('Europe/Moscow')).isoformat(),
                'files': current['files'], 'operations': operations}
        if database is not None:
            plan['database'] = str(Path(database).resolve())
        save(session / '.before.json', current)
        save(session / '.plan.json', plan)
        shutil.copyfile(__file__, session / '.restore.py')
        (session / '.report.txt').write_text('Корзина менеджера. Оригиналы сохранены без изменения содержимого.\n'
            'Восстановление: кнопка «Корзина» в менеджере или запуск python3 с файлом .restore.py из этой папки.\n'
            'Существующие пути не перезаписываются; при конфликте восстановление останавливается.\n', encoding='utf-8')
        error = ''
        with (session / '.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            for index, operation in enumerate(operations):
                try:
                    source = checked(root, operation['source'], hidden=True)
                    destination = checked(root, operation['destination'], hidden=True)
                    if not same(source, operation['identity']):
                        raise TrashConflict('Файл изменился: ' + operation['source'])
                    if source.is_file() and operation['source'] == operation['file']:
                        item = next(item for item in current['files'] if item['path'] == operation['file'])
                        if revision(source) != item['revision']:
                            raise TrashConflict('Файл изменился: ' + operation['source'])
                    append(session, phase='intent', id=index, **operation)
                    database_move(plan,operation)
                    if not destination.parent.exists():
                        append(session, phase='mkdir_intent', path=str(destination.parent.relative_to(root)))
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        append(session, phase='mkdir_commit', path=str(destination.parent.relative_to(root)))
                    rename(source, destination)
                    database_move(plan,operation,finish=True)
                    append(session, phase='commit', id=index)
                except (OSError, ValueError, sqlite3.Error) as problem:
                    error = str(problem)
                    append(session, phase='failed', id=index, error=error)
                    break
            result = {**describe(root, plan), 'error': error}
            save(session / '.after.json', result)
            return result


def list_sessions(root):
    root = Path(root).resolve()
    folder = checked(root, HISTORY.as_posix(), hidden=True)
    if not folder.exists():
        return []
    result = []
    for session in folder.iterdir():
        if not session.name.startswith('.') or not re.fullmatch('[a-f0-9]{32}', session.name[1:]):
            continue
        try:
            _, plan = read_plan(root, session.name[1:])
        except (FileNotFoundError, json.JSONDecodeError):
            continue  # An interrupted preparation never moved any user files.
        record = describe(root, plan)
        if record['count']:
            result.append(record)
    return sorted(result, key=lambda record: record['created'], reverse=True)


def restore(root, token):
    root = Path(root).resolve()
    with LOCK:
        session, plan = read_plan(root, token)
        error = ''
        restored = []
        with (session / '.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            intents = set()
            journal = session / '.journal.jsonl'
            if journal.exists():
                for line in journal.read_text(encoding='utf-8').splitlines(keepends=True):
                    if line.endswith('\n'):
                        record = json.loads(line)
                        if record['phase'] == 'intent':
                            intents.add(record['id'])
            for index, operation in reversed(list(enumerate(plan['operations']))):
                if index not in intents:
                    continue
                try:
                    stored = checked(root, operation['destination'], hidden=True)
                    original = checked(root, operation['source'], hidden=True)
                    if not os.path.lexists(stored):
                        if same(original, operation['identity']):
                            database_move(plan,operation,restore=True,finish=True)
                            continue
                        raise TrashConflict('Не найден сохранённый файл: ' + operation['file'])
                    if not same(stored, operation['identity']):
                        raise TrashConflict('Сохранённый файл изменён: ' + operation['file'])
                    if os.path.lexists(original):
                        raise TrashConflict('Путь уже занят, файл сохранён в корзине: ' + operation['source'])
                    if not original.parent.is_dir():
                        raise TrashConflict('Исходная папка перемещена или удалена: ' + str(original.parent.relative_to(root)))
                    append(session, phase='undo_intent', id=index)
                    database_move(plan,operation,restore=True)
                    rename(stored, original)
                    database_move(plan,operation,restore=True,finish=True)
                    append(session, phase='undone', id=index)
                    if operation['source'] == operation['file']:
                        restored.append(operation['file'])
                except (OSError, ValueError, sqlite3.Error) as problem:
                    error = str(problem)
                    append(session, phase='undo_failed', id=index, error=error)
                    break
            result = {**describe(root, plan), 'restored': restored, 'error': error}
            save(session / ('.restore-result-' + uuid.uuid4().hex + '.json'), result)
            return result


if __name__ == '__main__':
    session = Path(__file__).resolve().parent
    plan = json.loads((session / '.plan.json').read_text(encoding='utf-8'))
    print(json.dumps(restore(plan['root'], plan['session']), ensure_ascii=False, indent=2))
