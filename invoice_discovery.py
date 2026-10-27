"""Offer manually added # bills PDFs; import only after explicit attachment."""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import time
import unicodedata
import uuid

import file_comments
import file_trash
import icloud_access
import invoices
import orders
import work_orders


def name_key(name):
    return unicodedata.normalize('NFC', name).casefold()


def folder_target(store, path):
    path = store.store.path(path)
    if work_orders.in_work(path):
        raise ValueError('Счета доступны в клиентском заказе')
    folder = store.store.target(path) / '# bills'
    if folder.is_symlink():
        raise ValueError('# bills является ссылкой; проверка не выполнена')
    return folder


def file_key(target):
    return hashlib.sha256(json.dumps(file_trash.fingerprint(target), sort_keys=True).encode()).hexdigest()


def known_names(db, path):
    # Include trash and removed closing documents: they must not become new invoices.
    names = {name_key(row[0]) for row in db.execute('SELECT filename FROM invoices WHERE path=?', (path,)) if row[0]}
    names.update(name_key(row[0]) for row in db.execute('''SELECT d.filename FROM invoice_documents d
        JOIN invoices i ON i.id=d.invoice_id WHERE i.path=?''', (path,)) if row[0])
    return names


def candidates(store, path):
    with orders.SYNC_LOCK:
        with store.connect() as db:
            owner = store.owner(db, path, active=True)
            path = owner['path']
            known = known_names(db, path)
        folder = folder_target(store, path)
        try:
            entries = list(folder.iterdir())
        except FileNotFoundError:
            return {'items': [], 'warning': ''}
        items, skipped = [], 0
        for target in entries:
            name = target.name
            if name.startswith('.') or target.suffix.casefold() != '.pdf' or name_key(name) in known:
                continue
            info = target.lstat()
            if not stat.S_ISREG(info.st_mode):
                continue
            if not 0 < info.st_size <= invoices.MAX_EXTERNAL_BYTES or any(c in '\\:' or ord(c) < 32 or ord(c) == 127 for c in name):
                skipped += 1
                continue
            items.append({'name': name, 'size': info.st_size, 'key': file_key(target)})
        return {'items': sorted(items, key=lambda item: name_key(item['name'])),
                'warning': f'Не предложено PDF: {skipped}. Нужен непустой PDF до 20 МБ с обычным именем.' if skipped else ''}


def attach(store, payload):
    name = payload.get('name')
    if not isinstance(name, str) or not name or name.startswith('.') or any(c in '/\\:' or ord(c) < 32 or ord(c) == 127 for c in name) or Path(name).suffix.casefold() != '.pdf' or len(os.fsencode(name)) > 255:
        raise ValueError('Выбери PDF из списка найденных счетов')
    comment = invoices.external_comment(payload.get('comment', ''))
    with orders.SYNC_LOCK, file_comments.LOCK:
        with store.connect() as db:
            owner = store.owner(db, payload.get('path'), active=True)
            path, owner_id = owner['path'], owner['id']
        target = folder_target(store, path) / name
        if target.is_symlink() or not target.is_file():
            raise ValueError('Найденный PDF больше недоступен. Проверь папку ещё раз')
        expected = payload.get('key')
        if not isinstance(expected, str) or file_key(target) != expected:
            raise invoices.InvoiceConflict('Файл изменился. Проверь папку и выбери его заново')
        if not 0 < target.stat().st_size <= invoices.MAX_EXTERNAL_BYTES:
            raise ValueError('PDF может занимать до 20 МБ')
        try:
            # Always use the bounded Foundation helper on macOS, including cloud placeholders.
            pdf = icloud_access.read_bytes(target, max_bytes=invoices.MAX_EXTERNAL_BYTES, coordinated=True)
        except (OSError, subprocess.SubprocessError) as error:
            raise ValueError('Не удалось прочитать PDF из iCloud. Проверь загрузку файла и повтори прикрепление') from error
        if target.is_symlink() or file_key(target) != expected:
            raise invoices.InvoiceConflict('Файл изменился при чтении. Проверь папку ещё раз')
        if len(pdf) > invoices.MAX_EXTERNAL_BYTES or not pdf.startswith(b'%PDF-') or b'%%EOF' not in pdf[-2048:]:
            raise ValueError('Файл не похож на завершённый PDF. Проверь исходный документ')
        identity = str(uuid.uuid5(uuid.NAMESPACE_URL, json.dumps(
            ['manager-folder-invoice', owner_id, unicodedata.normalize('NFC', name), hashlib.sha256(pdf).hexdigest()], ensure_ascii=False)))
        with store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            current = store.owner(db, path, active=True)
            if current['id'] != owner_id:
                raise invoices.InvoiceConflict('Заказ изменился. Открой его заново')
            existing = db.execute('''SELECT * FROM invoices WHERE path=? AND state IN ('issued','external')
                AND pdf=? ORDER BY created,id LIMIT 1''', (path, pdf)).fetchone()
            if existing:
                if json.loads(existing['data']).get('_trash'):
                    raise invoices.InvoiceConflict('Этот PDF уже в корзине счетов. Восстанови прежний счёт')
                return store.record(existing)
            if name_key(name) in known_names(db, path):
                raise invoices.InvoiceConflict('Это имя уже связано со счётом или закрывающим документом')
            data = {'kind': 'external', 'original_name': unicodedata.normalize('NFC', name),
                    'comment': comment, 'date': invoices.today().isoformat()}
            stamp = time.time()
            # Adopt the existing copy; no rename, duplicate file or publication is needed.
            db.execute('''INSERT INTO invoices(id,path,year,number,revision,state,data,pdf,filename,exported,created,updated)
                VALUES (?,?,0,?,1,'external',?,?,?,1,?,?)''',
                (identity, path, identity, json.dumps(data, ensure_ascii=False), pdf, name, stamp, stamp))
            return store.record(store.current(db, path, identity))
