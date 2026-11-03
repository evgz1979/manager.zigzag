# scripts/archive_order_duplicate.py

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [scripts/archive_order_duplicate.py:1](../../../scripts/archive_order_duplicate.py#L1).

Archive an explicitly reviewed stale registration, retaining the current order.

Requires an old UUID in the current folder's own card history. Never moves or
rewrites document files. The journal copy can undo using only Python's stdlib.

Импорты Python, включая локальные: `argparse`, `contextlib`, `folder_layout`, `hashlib`, `json`, `order_document`, `os`, `pathlib`, `server`, `shutil`, `sqlite3`, `sys`, `time`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## table

[scripts/archive_order_duplicate.py:20](../../../scripts/archive_order_duplicate.py#L20) · `function`.

```python
def table(db, name):
```

Проверяет наличие таблицы SQLite перед совместимой перепривязкой.

Работает с таблицами sqlite_master.

Непосредственные вызовы: `bool`, `db.execute('SELECT 1 FROM sqlite_master WHERE name=?', (name,)).fetchone`, `db.execute`.

Выражения возврата (ветки читаются в исходнике):

```python
bool(db.execute('SELECT 1 FROM sqlite_master WHERE name=?', (name,)).fetchone())
```

## inside

[scripts/archive_order_duplicate.py:26](../../../scripts/archive_order_duplicate.py#L26) · `function`.

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

## append

[scripts/archive_order_duplicate.py:32](../../../scripts/archive_order_duplicate.py#L32) · `function`.

```python
def append(session, phase):
```

Дописывает запись в устойчивый журнал операции.

Передаёт работу `(Path(session) / '.journal.jsonl').open`, `Path`, `output.write`.

Непосредственные вызовы: `(Path(session) / '.journal.jsonl').open`, `Path`, `output.write`, `json.dumps`, `time.time`, `output.flush`, `os.fsync`, `output.fileno`.

## source_absent

[scripts/archive_order_duplicate.py:41](../../../scripts/archive_order_duplicate.py#L41) · `function`.

```python
def source_absent(root, source):
```

Доказывает отсутствие прежнего источника перед ручной перепривязкой.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `Path`, `range`, `len`, `path.lstat`, `path.is_symlink`, `ValueError`.

Явные исключения: `ValueError`.

## check_links

[scripts/archive_order_duplicate.py:57](../../../scripts/archive_order_duplicate.py#L57) · `function`.

```python
def check_links(db, source, identity):
```

Проверяет согласованность связанных записей до перепривязки заказа.

Работает с таблицами folder_notes, orders, todo_missing_folders, invoices, mobile_operations.

Непосредственные вызовы: `table`, `any`, `inside`, `db.execute`, `ValueError`, `db.execute('SELECT 1 FROM invoices WHERE path=?', (source,)).fetchone`, `db.execute(f'SELECT 1 FROM {name} WHERE order_id=?', (identity,)).fetchone`, `json.loads(row[0]).get`, `json.loads`, `db.execute(f"SELECT 1 FROM {name} WHERE state='pending'").fetchone`.

Явные исключения: `ValueError`.

## covered

[scripts/archive_order_duplicate.py:82](../../../scripts/archive_order_duplicate.py#L82) · `function`.

```python
def covered(source, current):
```

Доказывает, что дубль не содержит уникальной заметки, денег, задач или блоков.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `ValueError`, `json.loads`, `old_blocks.items`, `document.read_todos`, `any`, `new_blocks.get`.

Явные исключения: `ValueError`.

## archive

[scripts/archive_order_duplicate.py:106](../../../scripts/archive_order_duplicate.py#L106) · `function`.

```python
def archive(store, source, destination, evidence, *, perform=False):
```

Сохраняет исходные байты или снимок до миграции/архивирования.

Работает с таблицами orders, todo_catalog, order_duplicate_archive.

Непосредственные вызовы: `ValueError`, `store.path`, `inside`, `source_absent`, `store.target`, `store.require_order_folder`, `Path`, `proof.is_absolute`, `any`, `range`, `len`, `(folder / Path(*proof.parts[:index])).is_symlink`, `document.parse`, `document.read_text`, `document.load`, `document.icloud_access.read_bytes`, `store.connect`, `db.execute('SELECT * FROM orders WHERE path=?', (source,)).fetchone`, `db.execute`, `db.execute('SELECT * FROM orders WHERE path=?', (destination,)).fetchone`, `dict`, `historical.get`, `current_card.get`, `covered`, `check_links`, `table`, `layout.Plan`, `str`, `store.database.resolve`, `proof.as_posix`, `hashlib.sha256(card_bytes).hexdigest`, `hashlib.sha256`, `hashlib.sha256(proof_bytes).hexdigest`, `plan.create_session`, `shutil.copyfile`, `(session / '.old-card.txt').write_bytes`, `(session / '.current-card.txt').write_bytes`, `closing`, `sqlite3.connect`, `store.database.resolve().as_uri`, `original.backup`, `append`, `db.execute('SELECT * FROM orders WHERE id=?', (expected['id'],)).fetchone`, `hashlib.sha256(document.icloud_access.read_bytes(store.target(destination) / document.DOCUMENT)).hexdigest`, `hashlib.sha256(document.icloud_access.read_bytes(folder / proof)).hexdigest`, `json.dumps`, `time.time`, `layout.save_json`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
preview
{**preview, 'journal': str(session)}
```

## undo

[scripts/archive_order_duplicate.py:190](../../../scripts/archive_order_duplicate.py#L190) · `function`.

```python
def undo(session, *, perform=False):
```

Выполняет сохранённые обратные операции после проверки текущего состояния.

Работает с таблицами order_duplicate_archive, orders, todo_catalog.

Непосредственные вызовы: `Path`, `json.loads`, `(session / '.before.json').read_text`, `closing`, `sqlite3.connect`, `Path(before['database']).as_uri`, `db.execute`, `db.execute('SELECT * FROM order_duplicate_archive WHERE id=?', (old['id'],)).fetchone`, `str`, `ValueError`, `db.execute('SELECT 1 FROM orders WHERE path=? OR id=?', (old['path'], old['id'])).fetchone`, `check_links`, `db.execute('SELECT 1 FROM todo_catalog WHERE path=?', (item['path'],)).fetchone`, `append`, `list`, `','.join`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{'restore': before['source'], 'keep': before['destination']}
{'restored': 0}
{'restored': 1}
```
