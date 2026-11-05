# hidden_orders.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [hidden_orders.py](../../../hidden_orders.py).

SQLite-only, read-only overview of orders absent from the main table.

Импорты Python, включая локальные: `client_activity`, `folder_structure`, `json`, `pathlib`, `unicodedata`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-canonical"></a>

## canonical

[hidden_orders.py](../../../hidden_orders.py) · `function`.

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

<a id="symbol-catalog_orders"></a>

## catalog_orders

[hidden_orders.py](../../../hidden_orders.py) · `function`.

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

<a id="symbol-listed"></a>

## listed

[hidden_orders.py](../../../hidden_orders.py) · `function`.

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

<a id="symbol-production_path"></a>

## production_path

[hidden_orders.py](../../../hidden_orders.py) · `function`.

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
