# folder_rename_undo.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [folder_rename_undo.py](../../../folder_rename_undo.py).

Database path rewrite and standalone undo for a folder renamed in the UI.

Импорты Python, включая локальные: `argparse`, `contextlib`, `importlib.util`, `json`, `pathlib`, `sqlite3`, `unicodedata`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-check"></a>

## check

[folder_rename_undo.py](../../../folder_rename_undo.py) · `function`.

```python
def check(db, source, destination, session=None):
```

Проверяет предпосылки безопасного выполнения операции.

Работает с таблицами orders, mobile_operations.

Непосредственные вызовы: `metadata_paths`, `table`, `db.execute`, `any`, `inside`, `json.loads`, `ValueError`, `json.loads(row[0]).get`.

Явные исключения: `ValueError`.

<a id="symbol-inside"></a>

## inside

[folder_rename_undo.py](../../../folder_rename_undo.py) · `function`.

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

<a id="symbol-metadata_paths"></a>

## metadata_paths

[folder_rename_undo.py](../../../folder_rename_undo.py) · `function`.

```python
def metadata_paths(db, source, destination, *, apply=False):
```

Вычисляет затрагиваемые пути SQLite для самостоятельного отката.

Работает с таблицами folder_renames, metadata_file_moves, metadata_publications.

Непосредственные вызовы: `unicodedata.normalize`, `exists`, `db.execute`, `json.loads`, `pair.get`, `inside`, `ValueError`, `any`, `list`, `len`.

Явные исключения: `ValueError`.

<a id="symbol-remap"></a>

## remap

[folder_rename_undo.py](../../../folder_rename_undo.py) · `function`.

```python
def remap(path, source, destination):
```

Заменяет только совпадающий префикс пути с учётом границ папок.

Возвращает `destination + path[len(source):] if inside(path, source) else path`.

Непосредственные вызовы: `inside`, `len`.

Выражения возврата (ветки читаются в исходнике):

```python
destination + path[len(source):] if inside(path, source) else path
```

<a id="symbol-rewrite"></a>

## rewrite

[folder_rename_undo.py](../../../folder_rename_undo.py) · `function`.

```python
def rewrite(db, source, destination):
```

Переписывает связанные пути SQLite в одной внешней транзакции.

Работает с таблицами reconciliations, orders, folder_notes, todo_missing_folders, mobile_files.

Непосредственные вызовы: `metadata_paths`, `table`, `list`, `db.execute`, `inside`, `remap`, `identities.append`, `db.execute('SELECT order_path FROM todo_missing_folders WHERE path=?', (path,)).fetchone`, `values.append`, `db.executemany`.

<a id="symbol-table"></a>

## table

[folder_rename_undo.py](../../../folder_rename_undo.py) · `function`.

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

<a id="symbol-undo"></a>

## undo

[folder_rename_undo.py](../../../folder_rename_undo.py) · `function`.

```python
def undo(session, perform=False):
```

Выполняет сохранённые обратные операции после проверки текущего состояния.

Работает с таблицами folder_renames.

Непосредственные вызовы: `Path`, `json.loads`, `(session / '.folder-paths.json').read_text`, `importlib.util.spec_from_file_location`, `importlib.util.module_from_spec`, `spec.loader.exec_module`, `layout.undo`, `meta.get`, `closing`, `sqlite3.connect`, `Path(meta['database']).as_uri`, `db.execute`, `db.execute('SELECT state,paths_applied FROM folder_renames WHERE session=?', (str(session),)).fetchone`, `str`, `ValueError`, `bool`, `check`, `layout.load_plan`, `Path(pair['destination']).parent.as_posix`, `target.is_dir`, `any`, `target.iterdir`, `inside`, `table`, `keep.append`, `db.commit`, `reversed`, `rewrite`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
layout.undo(session)
0
count
```
