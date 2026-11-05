# scripts/rebind_order.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [scripts/rebind_order.py](../../../scripts/rebind_order.py).

Explicitly rebind an exported order after a confirmed external folder move.

The copied script can undo database paths after the user moves the folder back.
It never moves documents or replaces the working database with a snapshot.

Импорты Python, включая локальные: `argparse`, `contextlib`, `datetime`, `folder_layout`, `hashlib`, `json`, `order_document`, `os`, `pathlib`, `server`, `shutil`, `sqlite3`, `stat`, `sys`, `zoneinfo`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-append"></a>

## append

[scripts/rebind_order.py](../../../scripts/rebind_order.py) · `function`.

```python
def append(session, phase):
```

Дописывает запись в устойчивый журнал операции.

Передаёт работу `datetime.now(ZoneInfo('Europe/Moscow')).isoformat`, `datetime.now`, `ZoneInfo`.

Непосредственные вызовы: `datetime.now(ZoneInfo('Europe/Moscow')).isoformat`, `datetime.now`, `ZoneInfo`, `(Path(session) / '.journal.jsonl').open`, `Path`, `output.write`, `json.dumps`, `output.flush`, `os.fsync`, `output.fileno`.

<a id="symbol-check_links"></a>

## check_links

[scripts/rebind_order.py](../../../scripts/rebind_order.py) · `function`.

```python
def check_links(db, source, destination, identity):
```

Проверяет согласованность связанных записей до перепривязки заказа.

Работает с таблицами orders, folder_notes, todo_missing_folders, todo_catalog, mobile_operations.

Непосредственные вызовы: `db.execute`, `any`, `inside`, `ValueError`, `table`, `db.execute('SELECT 1 FROM todo_catalog WHERE path=?', (destination,)).fetchone`, `json.loads`, `json.loads(payload).get`.

Явные исключения: `ValueError`.

<a id="symbol-checked_folder"></a>

## checked_folder

[scripts/rebind_order.py](../../../scripts/rebind_order.py) · `function`.

```python
def checked_folder(root, relative):
```

Проверяет точную существующую папку ручной операции.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `Path`, `path.is_absolute`, `any`, `part.startswith`, `ValueError`, `range`, `len`, `(root / Path(*path.parts[:index])).is_symlink`, `target.is_dir`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
target
```

<a id="symbol-inside"></a>

## inside

[scripts/rebind_order.py](../../../scripts/rebind_order.py) · `function`.

```python
def inside(path, prefix):
```

Проверяет принадлежность пути указанной области по границам компонентов.

Возвращает `path == prefix or path.startswith(prefix + '/')`.

Непосредственные вызовы: `path.startswith`.

Выражения возврата (ветки читаются в исходнике):

```python
path == prefix or path.startswith(prefix + '/')
```

<a id="symbol-rebind"></a>

## rebind

[scripts/rebind_order.py](../../../scripts/rebind_order.py) · `function`.

```python
def rebind(store, source, destination, *, perform=False):
```

Перепривязывает проверенную существующую запись к подтверждённому пути.

Работает с таблицами orders.

Непосредственные вызовы: `ValueError`, `os.path.lexists`, `store.path`, `store.require_order_folder`, `checked_folder`, `store.connect`, `db.execute('SELECT * FROM orders WHERE path=?', (source,)).fetchone`, `db.execute`, `dict`, `check_links`, `document.load`, `card.get`, `hashlib.sha256(document.icloud_access.read_bytes(target / document.DOCUMENT)).hexdigest`, `hashlib.sha256`, `document.icloud_access.read_bytes`, `layout.Plan`, `Path`, `str`, `store.database.resolve`, `layout.identity`, `plan.create_session`, `shutil.copyfile`, `closing`, `sqlite3.connect`, `store.database.as_uri`, `source_db.backup`, `append`, `db.execute('SELECT * FROM orders WHERE id=?', (original['id'],)).fetchone`, `update_paths`, `layout.save_json`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
preview
{**preview, 'journal': str(session)}
```

<a id="symbol-table"></a>

## table

[scripts/rebind_order.py](../../../scripts/rebind_order.py) · `function`.

```python
def table(db, name):
```

Проверяет наличие таблицы SQLite перед совместимой перепривязкой.

Работает с таблицами sqlite_master.

Непосредственные вызовы: `db.execute('SELECT 1 FROM sqlite_master WHERE name=?', (name,)).fetchone`, `db.execute`.

Выражения возврата (ветки читаются в исходнике):

```python
db.execute('SELECT 1 FROM sqlite_master WHERE name=?', (name,)).fetchone() is not None
```

<a id="symbol-undo"></a>

## undo

[scripts/rebind_order.py](../../../scripts/rebind_order.py) · `function`.

```python
def undo(session, *, perform=False):
```

Выполняет сохранённые обратные операции после проверки текущего состояния.

Работает с таблицами orders.

Непосредственные вызовы: `Path`, `json.loads`, `(session / '.before.json').read_text`, `checked_folder`, `target.lstat`, `stat.S_IFMT`, `ValueError`, `os.path.lexists`, `closing`, `sqlite3.connect`, `Path(before['database']).as_uri`, `db.execute`, `db.execute('SELECT * FROM orders WHERE id=?', (before['id'],)).fetchone`, `check_links`, `append`, `update_paths`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{'source': before['destination'], 'destination': before['source']}
{'restored': 0}
{'restored': 1}
```

<a id="symbol-update_paths"></a>

## update_paths

[scripts/rebind_order.py](../../../scripts/rebind_order.py) · `function`.

```python
def update_paths(db, source, destination, identity):
```

Переписывает подтверждённые связанные пути в одной транзакции.

Работает с таблицами orders, invoices, todo_catalog, mobile_files.

Непосредственные вызовы: `db.execute`, `table`.
