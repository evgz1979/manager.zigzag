# order_creation.py

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [order_creation.py:1](../../../order_creation.py#L1).

Register only folders explicitly created by the manager; retry from SQLite.

Импорты Python, включая локальные: `event_folder_undo`, `folder_layout`, `folder_structure`, `json`, `local_metadata`, `order_folders`, `pathlib`, `reconciliations`, `time`, `uuid`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## complete_service_folders

[order_creation.py:17](../../../order_creation.py#L17) · `function`.

```python
def complete_service_folders(store, path, session, plan, journal):
```

Досоздаёт только собственные отсутствующие служебные папки заказа.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `enumerate`, `Path(relative).parent.as_posix`, `Path`, `ValueError`, `layout.safe_path`, `plan.get`, `target.is_dir`, `layout.identity`, `layout.exists`, `layout.append`, `target.mkdir`, `any`, `len`.

Явные исключения: `ValueError`.

## prepare

[order_creation.py:42](../../../order_creation.py#L42) · `function`.

```python
def prepare(store, path, title, session):
```

Создаёт подготовленное состояние операции до её применения.

Работает с таблицами orders, sqlite_master, metadata_records.

Непосредственные вызовы: `str`, `uuid.uuid4`, `session.resolve`, `store.connect`, `db.execute`, `local_metadata.schema`, `assert_unlocked`, `db.execute('SELECT 1 FROM orders WHERE path=?', (path,)).fetchone`, `ValueError`, `len`, `db.execute('SELECT data FROM metadata_records WHERE kind=? AND path=?', (KIND, path)).fetchone`, `json.loads`, `json.dumps`, `time.time`.

Явные исключения: `ValueError`.

## register

[order_creation.py:69](../../../order_creation.py#L69) · `function`.

```python
def register(store, path):
```

Регистрирует подготовленную папку заказа с сохранением устойчивого UUID.

Работает с таблицами metadata_records, reconciliations, orders, metadata_imports.

Непосредственные вызовы: `store.connect`, `db.execute`, `db.execute('SELECT data FROM metadata_records WHERE kind=? AND path=?', (KIND, path)).fetchone`, `json.loads`, `assert_unlocked`, `Path`, `layout.load_plan`, `Path(plan['root']).resolve`, `store.root.resolve`, `ValueError`, `layout.records`, `next`, `enumerate`, `any`, `store.target`, `layout.identity`, `complete_service_folders`, `in_reconciliations`, `db.execute('SELECT id FROM reconciliations WHERE path=?', (path,)).fetchone`, `reconciliations.insert`, `store.require_order_folder`, `db.execute('SELECT id FROM orders WHERE path=?', (path,)).fetchone`, `time.time`, `data.update`, `json.dumps`.

Явные исключения: `ValueError`.

## failed

[order_creation.py:116](../../../order_creation.py#L116) · `function`.

```python
def failed(store, path, error):
```

Сохраняет диагностический результат неудачного фонового обхода.

Работает с таблицами metadata_records.

Непосредственные вызовы: `store.connect`, `db.execute('SELECT data FROM metadata_records WHERE kind=? AND path=?', (KIND, path)).fetchone`, `db.execute`, `json.loads`, `Path`, `layout.load_plan`, `next`, `enumerate`, `any`, `layout.records`, `data.update`, `str`, `json.dumps`, `time.time`.

## recover

[order_creation.py:136](../../../order_creation.py#L136) · `function`.

```python
def recover(store):
```

Завершает допустимые незавершённые намерения создания после перезапуска.

Работает с таблицами metadata_records.

Непосредственные вызовы: `store.database.exists`, `store.connect`, `local_metadata.schema`, `db.execute`, `register`, `failed`, `local_metadata.MetadataStore(store).error`, `local_metadata.MetadataStore`.

## retry_one

[order_creation.py:154](../../../order_creation.py#L154) · `function`.

```python
def retry_one(store, path):
```

Явно завершает создание прежнего заказа с тем же UUID.

Работает с таблицами metadata_records.

Непосредственные вызовы: `store.connect`, `local_metadata.schema`, `db.execute('SELECT data FROM metadata_records WHERE kind=? AND path=?', (KIND, path)).fetchone`, `db.execute`, `json.loads`, `register`.
