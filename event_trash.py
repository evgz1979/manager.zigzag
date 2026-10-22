"""Recoverable removal of immediate events in supplier orders."""
from contextlib import closing
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import uuid
from zoneinfo import ZoneInfo

import folder_layout as layout
import folder_notes
import folder_rename
import folder_rename_undo as paths
import orders
from order_folders import LOCK, layout_scope
from order_todos import REFRESH_LOCK
import work_orders

EVENT_TRASH_VERSION = 1
KIND = "supplier-event-trash"


def available(relative):
    if not isinstance(relative, str):
        return False
    path = Path(relative)
    return folder_rename.available(relative) and not path.name.startswith('#') and work_orders.supplier_order(path.parent.as_posix())


def preview(store, relative, db=None):
    if not available(relative):
        raise ValueError("Выбери событие внутри заказа поставщику")
    view = folder_rename.preview(store, relative)
    if db is None:
        with store.connect() as connection:
            return preview(store, relative, connection)
    if any(paths.inside(row[0], relative) for row in db.execute("SELECT path FROM orders WHERE registered=1")):
        raise ValueError("В событии есть отдельная карточка заказа. Сначала убери её из регистрации и проверь данные")
    # Stat only: ordinary attachments are never downloaded or read for a preview.
    inventory = []
    def scan(directory):
        with os.scandir(directory) as entries:
            for entry in entries:
                value = entry.stat(follow_symlinks=False)
                inventory.append([Path(entry.path).relative_to(store.root / relative).as_posix(),
                                  value.st_dev, value.st_ino, value.st_mode, value.st_size, value.st_mtime_ns, value.st_ctime_ns])
                if entry.is_dir(follow_symlinks=False):
                    scan(Path(entry.path))
    scan(store.root / relative)
    versions = {}
    for table in ('folder_notes', 'metadata_records', 'metadata_publications', 'invoices'):
        if paths.table(db, table):
            versions[table] = [list(row) for row in db.execute(f'SELECT path,revision FROM {table} ORDER BY path') if paths.inside(row[0], relative)]
    fingerprint = [view['revision'], sorted(inventory), versions]
    return {**view, 'revision': hashlib.sha256(json.dumps(fingerprint, sort_keys=True).encode()).hexdigest(),
            'count': len(inventory), 'parent': Path(relative).parent.as_posix()}


def remove(store, payload):
    if payload.get('confirmed') is not True:
        raise ValueError('Подтверди перенос события в корзину')
    root = store.root.resolve()
    with LOCK, REFRESH_LOCK, orders.SYNC_LOCK, folder_notes.SYNC_LOCK, store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        view = preview(store, payload.get('path'), db)
        if view['revision'] != payload.get('revision'):
            raise folder_rename.FolderRenameConflict('Событие изменилось после открытия подтверждения. Открой подтверждение заново')
        source = view['path']
        token = uuid.uuid4().hex
        destination = (Path(source).parent / ('.deleted-event-' + token)).as_posix()
        paths.check(db, source, destination)
        plan = layout.Plan(root, [Path(source).parts[0]], **layout_scope(source))
        plan.database_paths = True
        plan.move(source, destination, 'Переместить событие поставщика в корзину с сохранением SQLite')
        session = plan.create_session(['Корзина событий поставщиков. Восстановление через менеджер или .restore.py --apply.'], view)
        layout.save_json(session / '.folder-paths.json', {'database': str(store.database.resolve()), 'source': source, 'destination': destination})
        shutil.copyfile(paths.__file__, session / '.restore.py')
        with closing(sqlite3.connect(store.database.resolve().as_uri() + '?mode=ro', uri=True)) as original:
            with closing(sqlite3.connect(session / '.before.sqlite3')) as backup:
                original.backup(backup)
                if backup.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                    raise ValueError('Снимок базы не прошёл проверку. Событие не изменено')
        if preview(store, source, db)['revision'] != view['revision']:
            raise folder_rename.FolderRenameConflict('Событие изменилось во время подготовки корзины. Открой подтверждение заново')
        mapping = {'source': source, 'destination': destination, 'kind': KIND, 'token': token,
                   'created': datetime.now(ZoneInfo('Europe/Moscow')).isoformat()}
        db.execute('CREATE TABLE IF NOT EXISTS folder_renames (session TEXT PRIMARY KEY,state TEXT NOT NULL,mappings TEXT NOT NULL,paths_applied INTEGER NOT NULL)')
        db.execute("INSERT INTO folder_renames VALUES (?,'pending',?,0)", (str(session), json.dumps([mapping], ensure_ascii=False)))
        db.commit()
        try:
            db.execute('BEGIN IMMEDIATE')
            layout.apply(session)
            paths.rewrite(db, source, destination)
            db.execute("UPDATE folder_renames SET state='complete',paths_applied=1 WHERE session=?", (str(session),))
            db.commit()
        except Exception as error:
            db.rollback()
            try:
                paths.undo(session, True)
            except (OSError, ValueError, sqlite3.Error) as problem:
                layout.append(session, {'phase': 'rollback_failed', 'error': str(problem)})
                raise folder_rename.FolderRenameConflict('Событие сохранено. Восстанови прерванную операцию через «Корзину»: ' + str(session)) from error
            raise folder_rename.FolderRenameConflict('Удаление отменено, событие восстановлено: ' + str(error)) from error
        return {'source': source, 'path': view['parent'], 'session': token}


def list_sessions(store):
    with store.connect() as db:
        if not paths.table(db, 'folder_renames'):
            return []
        result = []
        for row in db.execute("SELECT session,state,mappings FROM folder_renames WHERE state!='undone'"):
            for pair in json.loads(row['mappings']):
                if pair.get('kind') == KIND:
                    result.append({'session': pair['token'], 'path': pair['source'], 'created': pair['created'],
                                   'pending': row['state'] == 'pending'})
        return sorted(result, key=lambda item: item['created'], reverse=True)


def restore(store, token):
    with LOCK, REFRESH_LOCK, orders.SYNC_LOCK, folder_notes.SYNC_LOCK:
        with store.connect() as db:
            rows = list(db.execute('SELECT session,mappings FROM folder_renames')) if paths.table(db, 'folder_renames') else []
        for row in rows:
            for pair in json.loads(row['mappings']):
                if pair.get('kind') == KIND and pair.get('token') == token:
                    session = Path(row['session'])
                    if session.parent != store.root.resolve() / '.folder-layout-history' or session.is_symlink():
                        raise ValueError('Недоступный журнал корзины')
                    paths.undo(session, True)
                    return {'path': pair['source'], 'session': token}
        raise FileNotFoundError('Событие не найдено в корзине')
