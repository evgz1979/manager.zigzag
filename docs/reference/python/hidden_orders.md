# hidden_orders.py

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [hidden_orders.py:1](../../../hidden_orders.py#L1).

SQLite-only, read-only overview of orders absent from the main table.

Импорты Python, включая локальные: `client_activity`, `folder_structure`, `json`, `pathlib`, `unicodedata`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## canonical

[hidden_orders.py:19](../../../hidden_orders.py#L19) · `function`.

```python
def canonical(path):
```

Приводит путь к каноническому виду для сопоставления записей.

Возвращает `unicodedata.normalize('NFC', path)`.

Непосредственные вызовы: `unicodedata.normalize`.

Выражения возврата (ветки читаются в исходнике):

```python
unicodedata.normalize('NFC', path)
```

## production_path

[hidden_orders.py:25](../../../hidden_orders.py#L25) · `function`.

```python
def production_path(path):
```

Проверяет принадлежность пути производственной области.

Возвращает `bool(parts and (is_work_root(parts[0]) or is_supplier_root(parts[0])))`.

Непосредственные вызовы: `Path`, `bool`, `is_work_root`, `is_supplier_root`.

Выражения возврата (ветки читаются в исходнике):

```python
bool(parts and (is_work_root(parts[0]) or is_supplier_root(parts[0])))
```

## catalog_orders

[hidden_orders.py:32](../../../hidden_orders.py#L32) · `function`.

```python
def catalog_orders(store, records):
```

Добавляет известные незарегистрированные папки без нового обхода.

Работает с таблицами sqlite_master, metadata_records, folder_notes.

Непосредственные вызовы: `store.database.exists`, `canonical`, `set`, `store.connect`, `db.execute`, `Path(path).is_absolute`, `Path`, `any`, `part.startswith`, `is_service_folder`, `production_path`, `json.loads`, `isinstance`, `type`, `data.get`, `warnings.append`, `catalog.add`, `sorted`, `path.startswith`, `notes.get`, `ValueError`, `result.append`, `body.get`, `client_name`, `order_location`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
([], [])
(result, warnings)
```

## listed

[hidden_orders.py:77](../../../hidden_orders.py#L77) · `function`.

```python
def listed(store, inactive_clients, inactive_objects):
```

Готовит список скрытых заказов с применением сохранённых фильтров.

Возвращает `{'orders': result, 'reason_labels': REASONS, 'warnings': warnings}`.

Непосредственные вызовы: `store.list`, `production_path`, `catalog_orders`, `reasons.append`, `is_inactive`, `store.labels.get`, `order.get`, `result.append`, `isinstance`, `note.splitlines`.

Выражения возврата (ветки читаются в исходнике):

```python
{'orders': result, 'reason_labels': REASONS, 'warnings': warnings}
```
