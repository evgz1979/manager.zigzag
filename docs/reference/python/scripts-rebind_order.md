# scripts/rebind_order.py

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [scripts/rebind_order.py:1](../../../scripts/rebind_order.py#L1).

Explicitly rebind an exported order after a confirmed external folder move.

The copied script can undo database paths after the user moves the folder back.
It never moves documents or replaces the working database with a snapshot.

Импорты Python, включая локальные: `argparse`, `contextlib`, `datetime`, `folder_layout`, `hashlib`, `json`, `order_document`, `os`, `pathlib`, `server`, `shutil`, `sqlite3`, `stat`, `sys`, `zoneinfo`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## inside

[scripts/rebind_order.py:22](../../../scripts/rebind_order.py#L22) · `function`.

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

## table

[scripts/rebind_order.py:28](../../../scripts/rebind_order.py#L28) · `function`.

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

## checked_folder

[scripts/rebind_order.py:34](../../../scripts/rebind_order.py#L34) · `function`.

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

## append

[scripts/rebind_order.py:49](../../../scripts/rebind_order.py#L49) · `function`.

```python
def append(session, phase):
```

Дописывает запись в устойчивый журнал операции.

Передаёт работу `datetime.now(ZoneInfo('Europe/Moscow')).isoformat`, `datetime.now`, `ZoneInfo`.

Непосредственные вызовы: `datetime.now(ZoneInfo('Europe/Moscow')).isoformat`, `datetime.now`, `ZoneInfo`, `(Path(session) / '.journal.jsonl').open`, `Path`, `output.write`, `json.dumps`, `output.flush`, `os.fsync`, `output.fileno`.

## check_links

[scripts/rebind_order.py:59](../../../scripts/rebind_order.py#L59) · `function`.

```python
def check_links(db, source, destination, identity):
```

Проверяет согласованность связанных записей до перепривязки заказа.

Работает с таблицами orders, folder_notes, todo_missing_folders, todo_catalog, mobile_operations.

Непосредственные вызовы: `db.execute`, `any`, `inside`, `ValueError`, `table`, `db.execute('SELECT 1 FROM todo_catalog WHERE path=?', (destination,)).fetchone`, `json.loads`, `json.loads(payload).get`.

Явные исключения: `ValueError`.

## update_paths

[scripts/rebind_order.py:88](../../../scripts/rebind_order.py#L88) · `function`.

```python
def update_paths(db, source, destination, identity):
```

Переписывает подтверждённые связанные пути в одной транзакции.

Работает с таблицами orders, invoices, todo_catalog, mobile_files.

Непосредственные вызовы: `db.execute`, `table`.

## rebind

[scripts/rebind_order.py:100](../../../scripts/rebind_order.py#L100) · `function`.

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

## undo

[scripts/rebind_order.py:161](../../../scripts/rebind_order.py#L161) · `function`.

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
