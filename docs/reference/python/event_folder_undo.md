# event_folder_undo.py

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [event_folder_undo.py:1](../../../event_folder_undo.py#L1).

Откат переименования событий с сохранением путей заметок SQLite; копируется в журнал.

Импорты Python, включая локальные: `argparse`, `contextlib`, `importlib.util`, `json`, `pathlib`, `sqlite3`, `unicodedata`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## EventRenamePending

[event_folder_undo.py:13](../../../event_folder_undo.py#L13) · `class`.

```python
class EventRenamePending(ValueError):
```

Обозначает незавершённость операции в этом модуле.

Вызывающий обработчик использует тип исключения для отказа без подмены данных.

## inside

[event_folder_undo.py:19](../../../event_folder_undo.py#L19) · `function`.

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

## assert_unlocked

[event_folder_undo.py:25](../../../event_folder_undo.py#L25) · `function`.

```python
def assert_unlocked(db, path, *, include_children=False):
```

Блокирует работу с путём, затронутым незавершённым переименованием.

Работает с таблицами sqlite_master.

Непосредственные вызовы: `db.execute('SELECT 1 FROM sqlite_master WHERE name=?', (name,)).fetchone`, `db.execute`, `any`, `inside`, `json.loads`, `EventRenamePending`.

Явные исключения: `EventRenamePending`.

## guard_database

[event_folder_undo.py:37](../../../event_folder_undo.py#L37) · `function`.

```python
def guard_database(database, path, *, include_children=False):
```

Блокирует работу с путём, затронутым незавершённым переименованием.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `ValueError`, `Path(database).exists`, `Path`, `closing`, `sqlite3.connect`, `Path(database).resolve().as_uri`, `Path(database).resolve`, `assert_unlocked`.

Явные исключения: `ValueError`.

## metadata_paths

[event_folder_undo.py:47](../../../event_folder_undo.py#L47) · `function`.

```python
def metadata_paths(db, source, destination, *, apply=False):
```

Вычисляет затрагиваемые пути SQLite для самостоятельного отката.

Работает с таблицами metadata_file_moves, metadata_publications.

Непосредственные вызовы: `unicodedata.normalize`, `exists`, `db.execute`, `any`, `inside`, `ValueError`, `list`, `len`.

Явные исключения: `ValueError`.

## schema

[event_folder_undo.py:73](../../../event_folder_undo.py#L73) · `function`.

```python
def schema(db):
```

Создаёт отсутствующие таблицы и совместимые расширения схемы.

Работает с таблицами event_renames.

Непосредственные вызовы: `db.execute`.

## undo

[event_folder_undo.py:82](../../../event_folder_undo.py#L82) · `function`.

```python
def undo(session, perform=False):
```

Выполняет сохранённые обратные операции после проверки текущего состояния.

Работает с таблицами event_renames, sqlite_master, orders, folder_notes.

Непосредственные вызовы: `Path`, `json.loads`, `(session / '.event-paths.json').read_text`, `importlib.util.spec_from_file_location`, `importlib.util.module_from_spec`, `spec.loader.exec_module`, `layout.undo`, `closing`, `sqlite3.connect`, `database.as_uri`, `db.execute`, `schema`, `db.execute('SELECT state,paths_applied FROM event_renames WHERE session=?', (str(session),)).fetchone`, `str`, `ValueError`, `db.execute('SELECT 1 FROM sqlite_master WHERE name=?', (name,)).fetchone`, `any`, `inside`, `metadata_paths`, `db.execute('SELECT id,path FROM folder_notes').fetchall`, `len`, `db.execute('SELECT 1 FROM folder_notes WHERE path=?', (old,)).fetchone`, `updates.append`, `db.commit`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
layout.undo(session)
0
count
```
