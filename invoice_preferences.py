"""Shared seller details and grouped products; invoices keep independent snapshots."""
import json
import time
import uuid

import invoices


# Проверяет однострочное название или единицу каталога.
# Пустые значения допускаются только для единицы; управляющие символы запрещены.
def text(value, limit, label, *, empty=False):
    if not isinstance(value, str) or len(value) > limit or any(ord(c) < 32 for c in value) or (not empty and not value.strip()):
        raise ValueError(label + ': одна строка до ' + str(limit) + ' символов')
    return value.strip()


# Проверяет идентификатор группы или товара.
# Принимает только канонический UUID, не превращает произвольный ввод в новый ключ.
def identity(value):
    try:
        if str(uuid.UUID(value)) == value:
            return value
    except (ValueError, TypeError, AttributeError):
        pass
    raise ValueError('Не указан идентификатор товара или группы')


# Проверяет единые реквизиты теми же правилами, что и данные счёта.
# Возвращает нормализованную копию без выпуска документа или изменения счетов.
def seller_data(value):
    if not isinstance(value, dict) or set(value) - set(invoices.DEFAULT_SELLER):
        raise ValueError('Неизвестный формат реквизитов исполнителя')
    sample = dict(kind='invoice', number='1', date='2026-01-01', seller=value,
                  items=[dict(name='', quantity='1', unit='шт', price='0')])
    return invoices.validate(sample)['seller']


# Читает единые реквизиты вместе с монотонной версией настроек.
# Прежний ключ seller поддерживается; неизвестные данные не заменяются значениями по умолчанию.
def read_seller(db):
    row = db.execute("SELECT value FROM invoice_settings WHERE key='seller'").fetchone()
    revision = db.execute("SELECT value FROM invoice_settings WHERE key='seller_revision'").fetchone()
    raw = revision[0] if revision else '0'
    if not raw.isascii() or not raw.isdecimal() or str(int(raw)) != raw:
        raise ValueError('Неизвестная версия реквизитов исполнителя')
    try:
        data = seller_data(json.loads(row[0]) if row else dict(invoices.DEFAULT_SELLER))
    except (ValueError, TypeError):
        raise ValueError('Неизвестный формат реквизитов исполнителя') from None
    return dict(revision=int(raw), seller=data)


# Сохраняет снимок прежней настройки в общей SQLite-истории.
# Вызывается внутри транзакции записи; версии разных ключей независимы.
def history(db, key, previous):
    db.execute('''CREATE TABLE IF NOT EXISTS invoice_settings_history (
        key TEXT NOT NULL, revision INTEGER NOT NULL, value TEXT NOT NULL, saved REAL NOT NULL,
        PRIMARY KEY(key,revision))''')
    db.execute('INSERT INTO invoice_settings_history VALUES (?,?,?,?)',
               (key, previous['revision'], json.dumps(previous, ensure_ascii=False), time.time()))


# Записывает единые реквизиты с проверкой версии и историей одной транзакции.
# Совместим с прежним remember_seller; существующие документы не переписывает.
def write_seller(db, value, revision):
    previous, data = read_seller(db), seller_data(value)
    if type(revision) is not int or revision != previous['revision']:
        raise invoices.InvoiceConflict('Реквизиты уже изменены. Обнови настройки перед сохранением; ввод остался в форме')
    if data == previous['seller']:
        return previous
    history(db, 'seller', previous)
    db.execute("INSERT INTO invoice_settings VALUES ('seller',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
               (json.dumps(data, ensure_ascii=False),))
    db.execute("INSERT INTO invoice_settings VALUES ('seller_revision',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
               (str(revision + 1),))
    return dict(revision=revision + 1, seller=data)


# Проверяет сохранённый каталог групп и товаров известной версии.
# Плоские группы, точные цены и уникальные UUID обязательны; неизвестные поля не отбрасываются молча.
def validate_catalog(value):
    if (not isinstance(value, dict) or set(value) != {'version', 'revision', 'groups', 'products'}
            or type(value['version']) is not int or value['version'] != 1
            or type(value['revision']) is not int or value['revision'] < 0
            or not isinstance(value['groups'], list) or len(value['groups']) > 200
            or not isinstance(value['products'], list) or len(value['products']) > 2000):
        raise ValueError('Неизвестный формат каталога товаров')
    groups, ids = set(), set()
    for group in value['groups']:
        if not isinstance(group, dict) or set(group) != {'id', 'name'}:
            raise ValueError('Неизвестный формат группы товаров')
        key = identity(group['id'])
        if key in ids or text(group['name'], 100, 'Группа') != group['name']:
            raise ValueError('Повтор идентификатора или неверное название группы')
        groups.add(key)
        ids.add(key)
    for product in value['products']:
        if not isinstance(product, dict) or set(product) != {'id', 'group_id', 'name', 'unit', 'price'}:
            raise ValueError('Неизвестный формат товара')
        key = identity(product['id'])
        if key in ids or not isinstance(product['group_id'], str) or (product['group_id'] != '' and product['group_id'] not in groups):
            raise ValueError('Повтор идентификатора или неизвестная группа товара')
        ids.add(key)
        if text(product['name'], 500, 'Товар') != product['name'] or text(product['unit'], 16, 'Единица', empty=True) != product['unit']:
            raise ValueError('Некорректное название или единица товара')
        invoices.decimal(product['price'], 'Цена', 2, invoices.Decimal('999999999.99'))
    return value


# Читает общий каталог только из SQLite без обхода папок или счетов.
# Отсутствие ключа означает пустой каталог; повреждённый JSON вызывает отказ.
def read_catalog(db):
    row = db.execute("SELECT value FROM invoice_settings WHERE key='products'").fetchone()
    if not row:
        return dict(version=1, revision=0, groups=[], products=[])
    try:
        return validate_catalog(json.loads(row[0]))
    except (ValueError, TypeError, KeyError):
        raise ValueError('Неизвестный формат каталога товаров; сохранённые данные не изменены') from None


# Сохраняет группу или товар либо удаляет подтверждённый товар по версии каталога.
# История атомарна; удалённый UUID не воскрешается старой формой, снимки счетов не меняются.
def write_catalog(db, payload):
    previous = read_catalog(db)
    if type(payload.get('revision')) is not int or payload['revision'] != previous['revision']:
        raise invoices.InvoiceConflict('Каталог уже изменён. Обнови список перед сохранением; ввод остался в форме')
    kind, key = payload.get('kind'), identity(payload.get('id'))
    if not isinstance(kind, str) or kind not in {'group', 'product'}:
        raise ValueError('Выбери товар или группу')
    result = json.loads(json.dumps(previous))
    items = result['groups' if kind == 'group' else 'products']
    found = next((i for i, item in enumerate(items) if item['id'] == key), None)
    action = payload.get('action', 'save')
    if not isinstance(action, str) or action not in {'save', 'create', 'update', 'delete'}:
        raise ValueError('Неизвестное действие с каталогом')
    if action == 'delete':
        if kind != 'product' or payload.get('confirmed') is not True:
            raise ValueError('Подтверди удаление товара из каталога')
        if found is None:
            raise invoices.InvoiceConflict('Товар уже удалён из каталога')
        items.pop(found)
    else:
        if action == 'update' and found is None:
            raise invoices.InvoiceConflict('Запись уже удалена. Создай новый товар; ввод остался в форме')
        if action == 'create' and found is not None:
            raise invoices.InvoiceConflict('Этот идентификатор уже занят. Проверь сохранённые изменения')
        if kind == 'product' and found is None and db.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='invoice_settings_history'").fetchone():
            removed = db.execute('''SELECT 1 FROM invoice_settings_history AS h, json_each(h.value,'$.products') AS p
                WHERE h.key='products' AND json_extract(p.value,'$.id')=? LIMIT 1''', (key,)).fetchone()
            if removed:
                raise invoices.InvoiceConflict('Товар с этим идентификатором уже удалён. Создай новый товар')
        node = dict(id=key, name=text(payload.get('name'), 100 if kind == 'group' else 500, 'Название'))
        if kind == 'product':
            price = invoices.decimal(payload.get('price'), 'Цена', 2, invoices.Decimal('999999999.99'))
            node.update(group_id=payload.get('group_id', ''), unit=text(payload.get('unit'), 16, 'Единица', empty=True), price=format(price, '.2f'))
        if found is None:
            items.append(node)
        else:
            items[found] = node
    result['revision'] += 1
    validate_catalog(result)
    history(db, 'products', previous)
    db.execute("INSERT INTO invoice_settings VALUES ('products',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
               (json.dumps(result, ensure_ascii=False),))
    return result


# Обслуживает чтение или явную запись одной общей настройки счёта.
# Все записи используют BEGIN IMMEDIATE; отсутствующий payload означает только чтение.
def resource(store, kind, payload=None):
    with store.connect() as db:
        if payload is not None:
            db.execute('BEGIN IMMEDIATE')
        if kind == 'seller':
            return read_seller(db) if payload is None else write_seller(db, payload.get('seller'), payload.get('revision'))
        return read_catalog(db) if payload is None else write_catalog(db, payload)
