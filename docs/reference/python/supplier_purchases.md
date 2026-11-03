# supplier_purchases.py

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [supplier_purchases.py:1](../../../supplier_purchases.py#L1).

Supplier To-do is a live view of purchases in ordinary source orders.

Импорты Python, включая локальные: `client_activity`, `collections`, `event_folder_undo`, `folder_structure`, `json`, `local_metadata`, `order_document`, `pathlib`, `time`, `unicodedata`, `uuid`, `work_orders`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## remember_sections

[supplier_purchases.py:20](../../../supplier_purchases.py#L20) · `function`.

```python
def remember_sections(db, root, paths):
```

Запоминает явное успешное перечисление # work для опроса из SQLite.

Работает с таблицами metadata_records.

Непосредственные вызовы: `work_orders.supplier_root_path`, `sorted`, `unicodedata.normalize`, `db.execute('SELECT * FROM metadata_records WHERE kind=? AND path=?', (CATALOG_KIND, root)).fetchone`, `db.execute`, `json.loads`, `valid_catalog`, `ValueError`, `audit`, `json.dumps`, `time.time`, `str`, `uuid.uuid4`.

Явные исключения: `ValueError`.

## valid_catalog

[supplier_purchases.py:43](../../../supplier_purchases.py#L43) · `function`.

```python
def valid_catalog(data):
```

Проверяет формат сохранённого каталога поставщиков.

Формирует возвращаемое значение из проверенного локального состояния.

Непосредственные вызовы: `isinstance`, `type`, `data.get`, `all`.

Выражения возврата (ветки читаются в исходнике):

```python
isinstance(data, dict) and type(data.get('version')) is int and (data['version'] == 1) and isinstance(data.get('paths'), list) and all((isinstance(path, str) for path in data['paths']))
```

## available_suppliers

[supplier_purchases.py:50](../../../supplier_purchases.py#L50) · `function`.

```python
def available_suppliers(db):
```

Читает текущие избранные разделы без отмены прежних назначений.

Работает с таблицами sqlite_master, metadata_records.

Непосредственные вызовы: `db.execute("SELECT 1 FROM sqlite_master WHERE name='metadata_records'").fetchone`, `db.execute`, `json.loads`, `valid_catalog`, `set`, `work_orders.supplier_favorite_record`, `supplier_name`, `Path(row['path']).parent.as_posix`, `Path`, `options.append`, `options.sort`, `result.append`, `names.add`.

Выражения возврата (ветки читаются в исходнике):

```python
[]
result
```

## write_assignments

[supplier_purchases.py:77](../../../supplier_purchases.py#L77) · `function`.

```python
def write_assignments(db, blocks, items):
```

Сериализует выбранные назначения закупки существующим поставщикам.

Работает с таблицами metadata_settings.

Непосредственные вызовы: `document.read_purchases`, `ValueError`, `document.validate_purchases`, `available_suppliers`, `Counter`, `any`, `after.items`, `after.keys`, `set`, `schema`, `db.execute`, `document.write_purchases`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
document.write_purchases(blocks, items)
```

## supplier_name

[supplier_purchases.py:96](../../../supplier_purchases.py#L96) · `function`.

```python
def supplier_name(relative):
```

Определяет подпись реального раздела поставщика по пути.

Возвращает `''`; либо `'glass'`.

Непосредственные вызовы: `isinstance`, `Path(relative).is_absolute`, `Path`, `Path(relative).as_posix`, `any`, `part.startswith`, `len`, `is_supplier_root`, `is_work_root`, `dated`, `parts[1].removeprefix('#').strip().casefold`, `parts[1].removeprefix('#').strip`, `parts[1].removeprefix`, `unicodedata.normalize`, `document.valid_purchase_supplier`.

Выражения возврата (ветки читаются в исходнике):

```python
''
'glass'
name if name == 'etc' or document.valid_purchase_supplier(name) else ''
```

## SupplierPurchases

[supplier_purchases.py:113](../../../supplier_purchases.py#L113) · `class`.

```python
class SupplierPurchases:
```

Собирает закупки у поставщика и частично изменяет строки исходных заказов.

Основные операции: __init__, section, source_orders, catalog, read; остальные описаны у методов.

## SupplierPurchases.__init__

[supplier_purchases.py:116](../../../supplier_purchases.py#L116) · `function`.

```python
def __init__(self, store):
```

Сохраняет зависимости и начальные параметры экземпляра.

Состояние и зависимости сохраняются в полях self для последующих операций.

Прямые присваивания полям/свойствам: `self.store`.

## SupplierPurchases.section

[supplier_purchases.py:121](../../../supplier_purchases.py#L121) · `function`.

```python
def section(self, relative):
```

Проверяет текущий раздел поставщика и правила его сводки.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `supplier_name`, `ValueError`, `guard_database`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
name
```

## SupplierPurchases.source_orders

[supplier_purchases.py:130](../../../supplier_purchases.py#L130) · `function`.

```python
def source_orders(self, inactive):
```

Читает исходные заказы, из которых собираются закупки поставщика.

Возвращает `(order for order in self.store.list() if client_path(order['path']) and (not is_inactive(order['path'], inactive)))`.

Непосредственные вызовы: `self.store.list`, `client_path`, `is_inactive`.

Выражения возврата (ветки читаются в исходнике):

```python
(order for order in self.store.list() if client_path(order['path']) and (not is_inactive(order['path'], inactive)))
```

## SupplierPurchases.catalog

[supplier_purchases.py:135](../../../supplier_purchases.py#L135) · `function`.

```python
def catalog(self, *, inactive=()):
```

Собирает доступный каталог сущностей из сохранённых индексов.

Возвращает `{'suppliers': options, 'counts': counts}`.

Непосредственные вызовы: `self.store.connect`, `available_suppliers`, `self.source_orders`, `counts.get`.

Выражения возврата (ветки читаются в исходнике):

```python
{'suppliers': options, 'counts': counts}
```

## SupplierPurchases.read

[supplier_purchases.py:148](../../../supplier_purchases.py#L148) · `function`.

```python
def read(self, relative, *, inactive=()):
```

Читает SQLite-сводку исходных закупок выбранного поставщика или etc.

Возвращает `{'path': relative, 'supplier': name, 'orders': groups}`.

Непосредственные вызовы: `self.section`, `self.source_orders`, `enumerate`, `document.purchase_matches_supplier`, `groups.append`, `groups.sort`.

Выражения возврата (ветки читаются в исходнике):

```python
{'path': relative, 'supplier': name, 'orders': groups}
```

## SupplierPurchases.save

[supplier_purchases.py:161](../../../supplier_purchases.py#L161) · `function`.

```python
def save(self, payload, *, inactive=()):
```

Меняет выполнение точной исходной закупки с проверкой её назначения.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `self.section`, `payload.get`, `self.store.path`, `is_inactive`, `ValueError`, `self.store.save_purchase_done`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
self.store.save_purchase_done(payload, name)
```

## SupplierPurchases.edit

[supplier_purchases.py:170](../../../supplier_purchases.py#L170) · `function`.

```python
def edit(self, payload, *, inactive=()):
```

Частично меняет текст исходной закупки после проверки её идентичности.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `self.section`, `payload.get`, `self.store.path`, `is_inactive`, `ValueError`, `self.store.save_purchase_text`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
self.store.save_purchase_text(payload, name)
```
