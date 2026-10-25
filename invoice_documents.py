"""Immutable closing documents linked to an invoice, with versioned row metadata."""
import base64
import binascii
import hashlib
import json
import os
from pathlib import Path
import time
import unicodedata
import uuid

VERSION = 1
MAX_BYTES = 20 * 1024 * 1024
MAX_DOCUMENTS = 100
BLOCK = '_closing_documents'
MIMES = {'application/pdf', 'image/png', 'image/jpeg', 'application/octet-stream'}


def schema(db):
    db.execute('''CREATE TABLE IF NOT EXISTS invoice_documents (
        id TEXT PRIMARY KEY, invoice_id TEXT NOT NULL, version INTEGER NOT NULL,
        name TEXT NOT NULL, mime TEXT NOT NULL, size INTEGER NOT NULL,
        sha256 TEXT NOT NULL, content BLOB NOT NULL, created REAL NOT NULL,
        filename TEXT NOT NULL DEFAULT '', exported INTEGER NOT NULL DEFAULT 0,
        sync_error TEXT NOT NULL DEFAULT '')''')
    columns = {row[1] for row in db.execute('PRAGMA table_info(invoice_documents)')}
    for column, definition in [('filename', "TEXT NOT NULL DEFAULT ''"), ('exported', 'INTEGER NOT NULL DEFAULT 0'), ('sync_error', "TEXT NOT NULL DEFAULT ''")]:
        if column not in columns:
            db.execute('ALTER TABLE invoice_documents ADD COLUMN ' + column + ' ' + definition)
    db.execute('CREATE INDEX IF NOT EXISTS invoice_documents_invoice ON invoice_documents(invoice_id)')


def identity(value):
    try:
        if not isinstance(value, str) or str(uuid.UUID(value)) != value:
            raise ValueError()
    except (ValueError, AttributeError):
        raise ValueError('Не указан идентификатор закрывающего документа') from None
    return value


def filename(value):
    if not isinstance(value, str) or not value or value.startswith('.') or any(c in '/\\:' or ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError('Некорректное имя закрывающего документа')
    value = unicodedata.normalize('NFC', value)
    if len(os.fsencode(value)) > 255:
        raise ValueError('Имя закрывающего документа: до 255 байт')
    return value


def read(data):
    if BLOCK not in data:
        return []
    block = data[BLOCK]
    if not isinstance(block, dict) or set(block) != {'version', 'items'} or type(block['version']) is not int or block['version'] != VERSION:
        return None
    items = block['items']
    if not isinstance(items, list) or len(items) > MAX_DOCUMENTS:
        return None
    seen = set()
    try:
        for item in items:
            if not isinstance(item, dict) or set(item) != {'id', 'name', 'mime', 'size', 'sha256', 'deleted'}:
                return None
            key = identity(item['id'])
            if key in seen or filename(item['name']) != item['name'] or item['mime'] not in MIMES:
                return None
            if type(item['size']) is not int or not 0 < item['size'] <= MAX_BYTES or type(item['deleted']) is not bool:
                return None
            if not isinstance(item['sha256'], str) or len(item['sha256']) != 64 or any(c not in '0123456789abcdef' for c in item['sha256']):
                return None
            seen.add(key)
    except (ValueError, TypeError):
        return None
    return items


def metadata(row):
    return {**{key: row[key] for key in ('id', 'name', 'mime', 'size', 'sha256')}, 'deleted': False}


def copy_name(name, key):
    suffix = ' - ' + key + Path(name).suffix
    stem = Path(name).stem
    while len(os.fsencode(stem + suffix)) > 255:
        stem = stem[:-1]
    return stem + suffix


def with_copy_status(db, record):
    copies = {row['id']: dict(row) for row in db.execute('SELECT id,filename,exported,sync_error FROM invoice_documents WHERE invoice_id=?', (record['id'],))}
    for field in ('closing_documents', 'closing_documents_trash'):
        record[field] = [{**item, **{key: copies.get(item['id'], {}).get(key, default) for key, default in [('filename', ''), ('exported', 0), ('sync_error', '')]}} for item in record[field]]
    return record


def parent(store, db, path, invoice_id, *, write=False):
    row = store.current(db, path, invoice_id)
    if write:
        store.owner(db, row['path'], active=True)
    if row['state'] not in {'draft', 'issued', 'external'}:
        raise ValueError('Прикрепить закрывающие можно к счёту, а не к плану')
    data = json.loads(row['data'])
    items = read(data)
    if items is None:
        raise ValueError('Неизвестный формат закрывающих документов сохранён без изменений')
    return row, data, items


def save(store, db, row, data, items):
    data[BLOCK] = {'version': VERSION, 'items': items}
    db.execute('INSERT INTO invoice_history VALUES (?,?,?,?)', (row['id'], row['revision'], row['data'], time.time()))
    db.execute('UPDATE invoices SET data=?,revision=revision+1,updated=? WHERE id=?',
               (json.dumps(data, ensure_ascii=False), time.time(), row['id']))
    return store.record(store.current(db, row['path'], row['id']))


def upload(store, payload):
    from invoices import InvoiceConflict
    key, name = identity(payload.get('document_id')), filename(payload.get('name'))
    encoded = payload.get('content')
    if not isinstance(encoded, str) or len(encoded) > ((MAX_BYTES + 2) // 3) * 4:
        raise ValueError('Закрывающий документ: до 20 МБ')
    try:
        content = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error):
        raise ValueError('Не удалось прочитать документ. Выбери файл ещё раз') from None
    if not 0 < len(content) <= MAX_BYTES:
        raise ValueError('Выбери непустой документ до 20 МБ')
    mime = ('application/pdf' if content.startswith(b'%PDF-') and b'%%EOF' in content[-2048:] else
            'image/png' if content.startswith(b'\x89PNG\r\n\x1a\n') else
            'image/jpeg' if content.startswith(b'\xff\xd8\xff') else 'application/octet-stream')
    digest = hashlib.sha256(content).hexdigest()
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        row, data, items = parent(store, db, payload.get('path'), payload.get('id'), write=True)
        existing = db.execute('SELECT id,invoice_id,version,name,sha256,size FROM invoice_documents WHERE id=?', (key,)).fetchone()
        if existing:
            if existing['invoice_id'] != row['id'] or existing['version'] != VERSION or (existing['name'], existing['sha256'], existing['size']) != (name, digest, len(content)):
                raise InvoiceConflict('Этот идентификатор относится к другому документу или счёту')
            if not any(item['id'] == key and not item['deleted'] for item in items):
                raise InvoiceConflict('Документ удалён из строки. Восстанови его из корзины закрывающих')
            return store.record(row)
        if type(payload.get('revision')) is not int or payload['revision'] != row['revision']:
            raise InvoiceConflict('Счёт изменился. Проверь изменения перед прикреплением')
        if len(items) >= MAX_DOCUMENTS:
            raise ValueError('К одному счёту можно прикрепить до 100 закрывающих документов')
        db.execute('INSERT INTO invoice_documents (id,invoice_id,version,name,mime,size,sha256,content,created,filename) VALUES (?,?,?,?,?,?,?,?,?,?)',
                   (key, row['id'], VERSION, name, mime, len(content), digest, content, time.time(), copy_name(name, key)))
        item = {'id': key, 'name': name, 'mime': mime, 'size': len(content), 'sha256': digest, 'deleted': False}
        return save(store, db, row, data, [*items, item])


def set_deleted(store, payload, deleted):
    from invoices import InvoiceConflict
    key = identity(payload.get('document_id'))
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        row, data, items = parent(store, db, payload.get('path'), payload.get('id'), write=True)
        if type(payload.get('revision')) is not int or payload['revision'] != row['revision']:
            raise InvoiceConflict('Счёт изменился. Обнови строку и повтори действие с документом')
        item = next((item for item in items if item['id'] == key), None)
        if item is None:
            raise InvoiceConflict('Документ не найден у этого счёта')
        document = db.execute('SELECT id,version FROM invoice_documents WHERE id=? AND invoice_id=?', (key, row['id'])).fetchone()
        if document is None or document['version'] != VERSION:
            raise ValueError('Неизвестный формат документа сохранён без изменений')
        if item['deleted'] == deleted:
            return store.record(row)
        return save(store, db, row, data, [{**item, 'deleted': deleted} if item['id'] == key else item for item in items])


def content(store, path, invoice_id, document_id):
    key = identity(document_id)
    with store.connect() as db:
        row, _, items = parent(store, db, path, invoice_id)
        item = next((item for item in items if item['id'] == key and not item['deleted']), None)
        document = db.execute('SELECT * FROM invoice_documents WHERE id=? AND invoice_id=?', (key, row['id'])).fetchone()
        if item is None or document is None:
            raise FileNotFoundError('Закрывающий документ не найден у этого счёта')
        if document['version'] != VERSION or metadata(document) != item:
            raise ValueError('Неизвестный формат документа сохранён без изменений')
        body = document['content']
        if len(body) != document['size'] or hashlib.sha256(body).hexdigest() != document['sha256']:
            raise ValueError('Не совпадает контрольная сумма документа')
        return body, document['name'], document['mime']


def sync(store):
    import orders
    with store.connect() as db:
        pending = [row[0] for row in db.execute('SELECT id FROM invoice_documents WHERE exported=0')]
    for key in pending:
        with orders.SYNC_LOCK:
            try:
                with store.connect() as db:
                    document = db.execute('SELECT * FROM invoice_documents WHERE id=?', (key,)).fetchone()
                    if document is None:
                        continue
                    invoice = db.execute('SELECT path,data,state FROM invoices WHERE id=?', (document['invoice_id'],)).fetchone()
                    if not invoice or json.loads(invoice['data']).get('_trash'):
                        continue
                    items = read(json.loads(invoice['data']))
                    item = next((item for item in items or [] if item['id'] == key and not item['deleted']), None)
                    if item is None:
                        continue
                    if document['version'] != VERSION or metadata(document) != item or hashlib.sha256(document['content']).hexdigest() != document['sha256']:
                        raise ValueError('Не совпадает формат или контрольная сумма закрывающего документа')
                    name = copy_name(document['name'], key)
                    if document['filename'] and document['filename'] != name:
                        raise ValueError('Неизвестное имя копии закрывающего документа сохранено без изменений')
                store.publish_copy({'id': document['invoice_id'], 'path': invoice['path'], 'filename': name, 'pdf': document['content']})
                error = ''
            except (OSError, ValueError, RuntimeError) as problem:
                error = str(problem)
            with store.connect() as db:
                db.execute('UPDATE invoice_documents SET filename=CASE WHEN filename=\'\' THEN ? ELSE filename END,exported=?,sync_error=? WHERE id=?',
                           (copy_name(document['name'], key), 0 if error else 1, error, key))
