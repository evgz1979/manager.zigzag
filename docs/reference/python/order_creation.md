# order_creation.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [order_creation.py](../../../order_creation.py).

Register only folders explicitly created by the manager; retry from SQLite.

Импорты Python, включая локальные: `event_folder_undo`, `folder_layout`, `folder_structure`, `json`, `local_metadata`, `order_folders`, `pathlib`, `reconciliations`, `time`, `uuid`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-complete_service_folders"></a>

## complete_service_folders

[order_creation.py](../../../order_creation.py) · `function`.

```python
def complete_service_folders(store, path, session, plan, journal):
```

Досоздаёт только собственные отсутствующие служебные папки заказа.

Для сверки и записи зарплаты пропускает дочерние шаги старого плана и завершает журнал по выполненным шагам.

Непосредственные вызовы: `len`, `in_payroll`, `in_reconciliations`, `enumerate`, `Path(relative).parent.as_posix`, `Path`, `ValueError`, `layout.safe_path`, `plan.get`, `target.is_dir`, `layout.identity`, `layout.exists`, `layout.append`, `target.mkdir`, `any`.

Явные исключения: `ValueError`.

<a id="symbol-failed"></a>

## failed

[order_creation.py](../../../order_creation.py) · `function`.

```python
def failed(store, path, error):
```

Сохраняет диагностический результат неудачного фонового обхода.

Работает с таблицами metadata_records.

Непосредственные вызовы: `store.connect`, `db.execute('SELECT data FROM metadata_records WHERE kind=? AND path=?', (KIND, path)).fetchone`, `db.execute`, `json.loads`, `Path`, `layout.load_plan`, `next`, `enumerate`, `any`, `layout.records`, `data.update`, `str`, `json.dumps`, `time.time`.

<a id="symbol-prepare"></a>

## prepare

[order_creation.py](../../../order_creation.py) · `function`.

```python
def prepare(store, path, title, session):
```

Создаёт подготовленное состояние операции до её применения.

Работает с таблицами orders, sqlite_master, metadata_records.

Непосредственные вызовы: `str`, `uuid.uuid4`, `session.resolve`, `store.connect`, `db.execute`, `local_metadata.schema`, `assert_unlocked`, `db.execute('SELECT 1 FROM orders WHERE path=?', (path,)).fetchone`, `ValueError`, `len`, `db.execute('SELECT data FROM metadata_records WHERE kind=? AND path=?', (KIND, path)).fetchone`, `json.loads`, `json.dumps`, `time.time`.

Явные исключения: `ValueError`.

<a id="symbol-recover"></a>

## recover

[order_creation.py](../../../order_creation.py) · `function`.

```python
def recover(store):
```

Завершает допустимые незавершённые намерения создания после перезапуска.

Работает с таблицами metadata_records.

Непосредственные вызовы: `store.database.exists`, `store.connect`, `local_metadata.schema`, `db.execute`, `register`, `failed`, `local_metadata.MetadataStore(store).error`, `local_metadata.MetadataStore`.

<a id="symbol-register"></a>

## register

[order_creation.py](../../../order_creation.py) · `function`.

```python
def register(store, path):
```

Регистрирует подготовленную папку заказа с сохранением устойчивого UUID.

Работает с таблицами metadata_records, reconciliations, orders, metadata_imports.

Непосредственные вызовы: `store.connect`, `db.execute`, `db.execute('SELECT data FROM metadata_records WHERE kind=? AND path=?', (KIND, path)).fetchone`, `json.loads`, `assert_unlocked`, `Path`, `layout.load_plan`, `Path(plan['root']).resolve`, `store.root.resolve`, `ValueError`, `layout.records`, `next`, `enumerate`, `any`, `store.target`, `layout.identity`, `complete_service_folders`, `in_reconciliations`, `db.execute('SELECT id FROM reconciliations WHERE path=?', (path,)).fetchone`, `reconciliations.insert`, `store.require_order_folder`, `db.execute('SELECT id FROM orders WHERE path=?', (path,)).fetchone`, `time.time`, `data.update`, `json.dumps`.

Явные исключения: `ValueError`.

<a id="symbol-retry_one"></a>

## retry_one

[order_creation.py](../../../order_creation.py) · `function`.

```python
def retry_one(store, path):
```

Явно завершает создание прежнего заказа с тем же UUID.

Работает с таблицами metadata_records.

Непосредственные вызовы: `store.connect`, `local_metadata.schema`, `db.execute('SELECT data FROM metadata_records WHERE kind=? AND path=?', (KIND, path)).fetchone`, `db.execute`, `json.loads`, `register`.
