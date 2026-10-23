"""Stream browser files into an existing event directory without overwriting files."""
import errno
import hashlib
import json
import os
from pathlib import Path
import threading
import unicodedata
import uuid

import file_trash
import folder_layout
from folder_notes import parent_order
from folder_structure import folder_role, is_work_root, is_freza_task
from event_folder_undo import guard_database
from order_folders import LOCK

MAX_BYTES = 8 * 1024 ** 3
MAX_FILES = 200
CHUNK = 1024 * 1024
SLOTS = threading.BoundedSemaphore(3)


class UploadConflict(ValueError):
    pass


class UploadTooLarge(ValueError):
    pass


class UploadBusy(ValueError):
    pass


def available(root, relative):
    try:
        file_trash.checked(Path(root).resolve(), relative)
    except ValueError:
        return False
    if is_freza_task(relative):
        return True
    if not relative or folder_role(root, relative)['folderKind'] not in {'event', 'service'}:
        return False
    parts = Path(relative).parts
    # All production sections are dynamic; extra # containers must not stop
    # uploads to their events. The root, section and order levels stay excluded.
    if len(parts)>=4 and is_work_root(parts[0]):
        return True
    return bool(parent_order(root, relative))


def target(root, relative):
    if not isinstance(relative, str) or not relative or '\x00' in relative:
        raise ValueError('Открой событие или папку внутри заказа')
    path = file_trash.checked(Path(root).resolve(), relative)
    if not path.is_dir():
        raise FileNotFoundError('Папка события недоступна')
    if not available(root, relative):
        raise ValueError('Добавлять файлы можно в событие или папку внутри заказа')
    return path


def token(root, relative, folder=None):
    folder = folder or target(root, relative)
    value = [str(Path(root).resolve()), unicodedata.normalize('NFC', relative), folder_layout.identity(folder)]
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def options(root, relative):
    folder = target(root, relative)
    return {'token': token(root, relative, folder), 'maxBytes': MAX_BYTES, 'maxFiles': MAX_FILES}


def filename(value):
    if not isinstance(value, str) or not value or value.startswith('.') or any(c in '/\\:' or ord(c)<32 or ord(c)==127 for c in value):
        raise ValueError('Недопустимое имя файла: скрытые имена и разделители пути не поддерживаются')
    value = unicodedata.normalize('NFC', value)
    if value.casefold() in {name.casefold() for name in file_trash.PROTECTED} or len(os.fsencode(value))>255:
        raise ValueError('Имя занято служебной карточкой или слишком длинное')
    return value


def reserved_names(db, relative):
    prefix = unicodedata.normalize('NFC', relative) + '/'
    names = set()
    def reserve(path):
        path = unicodedata.normalize('NFC', path)
        if path.startswith(prefix):
            names.add(path[len(prefix):].split('/',1)[0].casefold())
    tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for table in ('orders','folder_notes','metadata_records','metadata_imports','metadata_publications','todo_missing_folders'):
        if table in tables:
            for row in db.execute(f'SELECT path FROM {table}'):
                reserve(row[0])
    if 'invoices' in tables:
        for path, name in db.execute("SELECT path,filename FROM invoices WHERE state IN ('issued','external')"):
            if name:
                reserve((Path(path)/'# bills'/name).as_posix())
    return names


def receive(store, relative, expected, name, source, size):
    if not isinstance(size, int) or size < 0:
        raise ValueError('Не указан размер файла')
    if size > MAX_BYTES:
        raise UploadTooLarge('Один файл может занимать до 8 ГБ')
    name = filename(name)
    if not SLOTS.acquire(blocking=False):
        raise UploadBusy('На M4 уже идут загрузки. Повтори через несколько секунд')
    directory = None
    temporary = '.upload-' + uuid.uuid4().hex + '.part'
    try:
        with LOCK:
            folder = target(store.root, relative)
            guard_database(store.database, relative)
            if store.get(relative) and not is_freza_task(relative):
                raise ValueError('Открой событие внутри заказа')
            if not isinstance(expected, str) or token(store.root, relative, folder) != expected:
                raise UploadConflict('Папка изменилась. Открой её заново перед загрузкой')
            directory = os.open(folder, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            stat = os.fstat(directory)
            if (stat.st_dev, stat.st_ino) != (folder.stat().st_dev, folder.stat().st_ino):
                raise UploadConflict('Папка изменилась перед загрузкой')
            descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
        with os.fdopen(descriptor, 'wb') as output:
            remaining = size
            while remaining:
                data = source.read(min(CHUNK, remaining))
                if not data:
                    raise ValueError('Передача оборвалась: файл не сохранён, повтори загрузку')
                output.write(data)
                remaining -= len(data)
            output.flush()
            os.fsync(output.fileno())
            os.fchmod(output.fileno(), 0o644)
            written = os.fstat(output.fileno())
            with LOCK, store.connect() as db:
                current = target(store.root, relative)
                guard_database(store.database, relative)
                if token(store.root, relative, current) != expected:
                    raise UploadConflict('Папка перемещена во время передачи. Открой её заново и повтори загрузку')
                staged = os.stat(temporary, dir_fd=directory, follow_symlinks=False)
                if (staged.st_dev, staged.st_ino) != (written.st_dev, written.st_ino):
                    raise UploadConflict('Временный файл изменился во время загрузки')
                db.execute('BEGIN IMMEDIATE')
                reserved = reserved_names(db, relative)
                for index in range(1, 10001):
                    candidate = name if index==1 else f'{Path(name).stem} ({index}){Path(name).suffix}'
                    if len(os.fsencode(candidate))>255:
                        raise UploadConflict('Для копии с номером нужно более короткое имя файла')
                    if candidate.casefold() in reserved:
                        continue
                    try:
                        folder_layout.rename_exclusive(current/temporary, current/candidate)
                        break
                    except OSError as error:
                        if error.errno not in {errno.EEXIST, errno.ENOTEMPTY, errno.EISDIR}:
                            raise
                else:
                    raise UploadConflict('Слишком много файлов с таким именем. Переименуй исходный файл')
                os.fsync(directory)
        return {'path': (Path(relative)/candidate).as_posix(), 'name':candidate, 'size':size}
    finally:
        if directory is not None:
            try:
                os.unlink(temporary, dir_fd=directory)
            except OSError:
                pass
            os.close(directory)
        SLOTS.release()
