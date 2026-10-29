"""Сверки и единственное назначение счёта; рабочие данные только в SQLite."""
from contextlib import contextmanager
import json
from pathlib import Path
import time
import unicodedata
import uuid

import local_metadata
import order_document
from event_folder_undo import assert_unlocked
from folder_structure import in_reconciliations, is_moneys_root

RECONCILIATIONS_VERSION = 1


class ReconciliationConflict(ValueError):
    pass


def schema(db):
    # Собственные записи и связи не меняют карточки и версии исходных счетов.
    local_metadata.schema(db)
    db.execute("""CREATE TABLE IF NOT EXISTS reconciliations (
        path TEXT PRIMARY KEY,id TEXT NOT NULL UNIQUE,data TEXT NOT NULL,
        revision INTEGER NOT NULL,updated REAL NOT NULL)""")
    db.execute("""CREATE TABLE IF NOT EXISTS reconciliation_invoices (
        id TEXT PRIMARY KEY,reconciliation_id TEXT NOT NULL,revision INTEGER NOT NULL,updated REAL NOT NULL)""")
    for table in ('reconciliations', 'reconciliation_invoices'):
        local_metadata.audit(db, table)


def mark(db):
    db.execute("INSERT OR REPLACE INTO metadata_settings VALUES ('reconciliations','1')")


def checked_path(path):
    if not isinstance(path, str) or Path(path).is_absolute() or any(p.startswith('.') for p in Path(path).parts):
        raise ValueError('Выбери сверку в разделе reconciliations')
    path = unicodedata.normalize('NFC', Path(path).as_posix())
    if not in_reconciliations(path) or len(Path(path).parts) != 3 or Path(path).name.startswith('#'):
        raise ValueError('Выбери сверку в разделе reconciliations')
    return path


def checked_data(data):
    # Неизвестные форматы не заменяются; дополнительные поля сохраняются.
    if not isinstance(data, dict) or type(data.get('version')) is not int or data['version'] != 1:
        raise ValueError('Неизвестный формат сверки; данные сохранены без изменений')
    for key, limit in (('title', 500), ('client', 1000), ('note', 100000)):
        value = data.get(key)
        if not isinstance(value, str) or len(value) > limit or '\x00' in value:
            raise ValueError('Проверь название, клиента и заметку сверки')
    if not data['title'].strip():
        raise ValueError('Укажи название сверки')
    order_document.validate_todos(data.get('todo_items'))
    return data


def record(row):
    data = checked_data(json.loads(row['data']))
    return {**data, 'id': row['id'], 'path': row['path'], 'revision': row['revision'], 'updated': row['updated']}


def insert(db, path, title, identity=None, data=None):
    data = checked_data(data or {'version': 1, 'title': title, 'client': '', 'note': '', 'todo_items': []})
    db.execute('INSERT INTO reconciliations VALUES (?,?,?,1,?)',
               (path, identity or str(uuid.uuid4()), json.dumps(data, ensure_ascii=False), time.time()))
    mark(db)


def invoice_link(db, identity):
    row = db.execute('SELECT * FROM reconciliation_invoices WHERE id=?', (identity,)).fetchone()
    target = db.execute('SELECT * FROM reconciliations WHERE id=?', (row['reconciliation_id'],)).fetchone() if row and row['reconciliation_id'] else None
    return {'id': row['reconciliation_id'] if row else '', 'revision': row['revision'] if row else 0,
            'title': record(target)['title'] if target else '', 'path': target['path'] if target else ''}


def untouched_empty_note(db, row, data):
    # Прежний фоновый импорт создавал {} по новому пути ещё до открытия сверки.
    return (data == {} and row['revision'] == 1 and row['exported_revision'] == 1
            and row['file_revision'] == 'database' and row['parent_order'] == '' and row['sync_error'] == ''
            and not db.execute("SELECT 1 FROM metadata_history WHERE entity='folder_notes' AND identity=? LIMIT 1", (row['id'],)).fetchone())


class Reconciliations:
    def __init__(self, store):
        self.store = store

    @contextmanager
    def connect(self):
        with self.store.connect() as db:
            schema(db)
            db.commit()
            yield db

    def source(self, db, path):
        # Разрешённое пользователем переименование report(s): только одна прежняя ветка.
        parts = Path(path).parts
        candidates = {path}
        for table in ('orders', 'folder_notes'):
            if not db.execute("SELECT 1 FROM sqlite_master WHERE name=?", (table,)).fetchone():
                continue
            for (old,) in db.execute(f'SELECT path FROM {table}'):
                old_parts = Path(old).parts
                if len(old_parts) != 3 or not is_moneys_root(old_parts[0]) or unicodedata.normalize('NFC', old_parts[0]) != parts[0]:
                    continue
                if unicodedata.normalize('NFC', old_parts[2]) != parts[2]:
                    continue
                section = unicodedata.normalize('NFC', old_parts[1]).lstrip('#').strip().casefold()
                if section in {'report', 'reports'}:
                    if (self.store.root / Path(*old_parts[:2])).exists():
                        raise ReconciliationConflict('Прежний раздел report(s) ещё существует. Заверши его переименование перед переходом сверок')
                    candidates.add(old)
        found = []
        for source in candidates:
            row = db.execute('SELECT * FROM orders WHERE path=?', (source,)).fetchone()
            note = db.execute('SELECT * FROM folder_notes WHERE path=?', (source,)).fetchone() if db.execute("SELECT 1 FROM sqlite_master WHERE name='folder_notes'").fetchone() else None
            if row and (row['registered'] or not note):
                data = {'title': row['title'], 'note': row['note'], 'extra_blocks': json.loads(row['extra_blocks'])}
            elif note:
                data = json.loads(note['document'])
                if not row and source == path and untouched_empty_note(db, note, data):
                    continue
            else:
                continue
            blocks = data.get('extra_blocks', {}) if isinstance(data, dict) else None
            if not isinstance(blocks, dict) or not isinstance(blocks.get(order_document.TODO_BLOCK, ''), str):
                raise ValueError('Неизвестный формат To-do прежней записи; исходные данные сохранены')
            todos = order_document.read_todos(blocks)
            if todos is None:
                raise ValueError('Неизвестный формат To-do прежней записи; исходные данные сохранены')
            found.append({'version': 1, 'title': data.get('title') or parts[-1], 'client': '',
                          'note': data.get('note', ''), 'todo_items': todos, 'source_path': source})
        if len(found) > 1:
            raise ReconciliationConflict('По старому и новому пути есть разные записи. Автоматический переход остановлен, обе сохранены')
        if found and db.execute("SELECT 1 FROM reconciliations WHERE json_extract(data,'$.source_path')=? AND path<>?", (found[0]['source_path'], path)).fetchone():
            raise ReconciliationConflict('Прежняя запись уже перенесена в другую сверку. Проверь её путь, не создавая дубль')
        return found[0] if found else None

    def open(self, path):
        # Вызывается только явным открытием папки, обычный опрос не читает iCloud.
        path = checked_path(path)
        target = self.store.target(path)
        if not target.is_dir():
            raise FileNotFoundError('Папка сверки недоступна')
        with self.connect() as db:
            assert_unlocked(db, path)
            if db.execute('SELECT 1 FROM reconciliations WHERE path=?', (path,)).fetchone():
                return self.get(path)
        local_metadata.MetadataStore(self.store).backup('before-reconciliations')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            assert_unlocked(db, path)
            if not db.execute('SELECT 1 FROM reconciliations WHERE path=?', (path,)).fetchone():
                insert(db, path, Path(path).name, data=self.source(db, path))
        return self.get(path)

    def catalog(self):
        with self.connect() as db:
            return [{key: item[key] for key in ('id', 'path', 'title', 'client', 'revision')}
                    for item in (record(row) for row in db.execute('SELECT * FROM reconciliations ORDER BY path'))]

    def with_links(self, items):
        # Дополняем HTTP-представление только сохранёнными назначениями, планы прежние.
        with self.connect() as db:
            return [{**item, 'reconciliation': invoice_link(db, item['id'])}
                    if db.execute('SELECT 1 FROM reconciliation_invoices WHERE id=?', (item['id'],)).fetchone()
                    else item for item in items]

    def get(self, path):
        path = checked_path(path)
        with self.connect() as db:
            assert_unlocked(db, path)
            row = db.execute('SELECT * FROM reconciliations WHERE path=?', (path,)).fetchone()
            if not row:
                raise ReconciliationConflict('Сначала открой сверку из раздела reconciliations')
            result = record(row)
            result['invoices'] = []
            if not db.execute("SELECT 1 FROM sqlite_master WHERE name='invoices'").fetchone():
                return result
            for invoice in db.execute('''SELECT i.id,i.path,i.number,i.state,i.data,i.revision,
                    l.revision AS link_revision FROM invoices i JOIN reconciliation_invoices l ON l.id=i.id
                    WHERE l.reconciliation_id=? ORDER BY i.created,i.id''', (row['id'],)):
                data = json.loads(invoice['data'])
                owner = db.execute('SELECT title FROM orders WHERE path=?', (invoice['path'],)).fetchone()
                result['invoices'].append({'id': invoice['id'], 'path': invoice['path'], 'revision': invoice['revision'],
                    'link_revision': invoice['link_revision'], 'state': invoice['state'], 'number': invoice['number'],
                    'label': data.get('original_name', 'Внешний счёт') if invoice['state'] == 'external' else ('Счёт-договор' if data.get('kind') == 'contract' else 'Счёт') + ' № ' + invoice['number'],
                    'date': data.get('date', ''), 'total': data.get('total'), 'comment': data.get('comment') or data.get('note', ''),
                    'order_title': owner['title'] if owner else invoice['path'], 'trash': bool(data.get('_trash'))})
            return result

    def save(self, payload):
        path = checked_path(payload.get('path'))
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            assert_unlocked(db, path)
            row = db.execute('SELECT * FROM reconciliations WHERE path=?', (path,)).fetchone()
            if not row or payload.get('id') != row['id'] or type(payload.get('revision')) is not int or payload['revision'] != row['revision']:
                raise ReconciliationConflict('Сверка изменилась. Твой ввод сохранён; открой актуальную версию перед повтором')
            data = checked_data(json.loads(row['data']))
            for key in ('title', 'client', 'note', 'todo_items'):
                data[key] = payload.get(key)
            checked_data(data)
            db.execute('UPDATE reconciliations SET data=?,revision=revision+1,updated=? WHERE id=?',
                       (json.dumps(data, ensure_ascii=False), time.time(), row['id']))
        return self.get(path)

    def assign(self, invoices, payload):
        # Версии счёта, назначения и выбранной сверки проверяются одной транзакцией.
        target_id = payload.get('reconciliation_id')
        if not isinstance(target_id, str):
            raise ValueError('Выбери сверку или сними назначение')
        with invoices.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            schema(db)
            invoice = invoices.current(db, payload.get('path'), payload.get('id'), trashed=True)
            if invoice['state'] not in {'draft', 'issued', 'external'}:
                raise ValueError('В сверку можно добавить счёт, а не план оплаты')
            link = invoice_link(db, invoice['id'])
            if (type(payload.get('invoice_revision')) is not int or payload['invoice_revision'] != invoice['revision'] or
                    type(payload.get('revision')) is not int or payload['revision'] != link['revision']):
                raise ReconciliationConflict('Счёт или его назначение изменились. Проверь актуальные данные перед повтором')
            if link['path']:
                assert_unlocked(db, link['path'])
            if target_id:
                target = db.execute('SELECT * FROM reconciliations WHERE id=?', (target_id,)).fetchone()
                if not target or type(payload.get('target_revision')) is not int or target['revision'] != payload['target_revision']:
                    raise ReconciliationConflict('Выбранная сверка изменилась. Обнови список сверок')
                checked_path(target['path'])
                record(target)
                assert_unlocked(db, target['path'])
                if json.loads(invoice['data']).get('_trash'):
                    raise ValueError('Сначала восстанови счёт из корзины')
            if target_id != link['id']:
                db.execute('''INSERT INTO reconciliation_invoices VALUES (?,?,1,?) ON CONFLICT(id)
                    DO UPDATE SET reconciliation_id=excluded.reconciliation_id,revision=reconciliation_invoices.revision+1,updated=excluded.updated''',
                    (invoice['id'], target_id, time.time()))
                mark(db)
            return invoice_link(db, invoice['id'])
