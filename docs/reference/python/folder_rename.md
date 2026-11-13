# folder_rename.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [folder_rename.py](../../../folder_rename.py).

Rename one opened folder and all its SQLite paths, without duplicating orders.

Импорты Python, включая локальные: `contextlib`, `event_folder_undo`, `folder_layout`, `folder_notes`, `folder_rename_undo`, `folder_structure`, `hashlib`, `json`, `order_folders`, `order_todos`, `orders`, `os`, `pathlib`, `shutil`, `sqlite3`, `unicodedata`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-FolderRenameConflict"></a>

## FolderRenameConflict

[folder_rename.py](../../../folder_rename.py) · `class`.

```python
class FolderRenameConflict(ValueError):
```

Обозначает конфликт изменения в этом модуле.

Вызывающий обработчик использует тип исключения для отказа без подмены данных.

<a id="symbol-available"></a>

## available

[folder_rename.py](../../../folder_rename.py) · `function`.

```python
def available(relative):
```

Проверяет доступность операции для роли и состояния цели.

Возвращает `False`; либо `not parts[0].startswith('#') or len(parts) > len(section_prefix(relative)) > 0`.

Непосредственные вызовы: `Path`, `Path(relative).is_absolute`, `any`, `part.startswith`, `parts[0].startswith`, `len`, `section_prefix`.

Выражения возврата (ветки читаются в исходнике):

```python
False
not parts[0].startswith('#') or len(parts) > len(section_prefix(relative)) > 0
```

<a id="symbol-name"></a>

## name

[folder_rename.py](../../../folder_rename.py) · `function`.

```python
def name(value):
```

Проверяет имя создаваемого или переименовываемого объекта.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `any`, `ord`, `ValueError`, `unicodedata.normalize`, `value.strip`, `value.startswith`, `len`, `os.fsencode`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
value
```

<a id="symbol-preview"></a>

## preview

[folder_rename.py](../../../folder_rename.py) · `function`.

```python
def preview(store, relative):
```

Готовит проверяемое предложение операции без её выполнения.

Формирует возвращаемое значение из проверенного локального состояния.

Непосредственные вызовы: `target`, `event_folder_undo.guard_database`, `layout.identity`, `hashlib.sha256(json.dumps(fingerprint, sort_keys=True).encode()).hexdigest`, `hashlib.sha256`, `json.dumps(fingerprint, sort_keys=True).encode`, `json.dumps`.

Выражения возврата (ветки читаются в исходнике):

```python
{'path': relative, 'name': path.name, 'revision': hashlib.sha256(json.dumps(fingerprint, sort_keys=True).encode()).hexdigest(), **fingerprint}
```

<a id="symbol-relocate"></a>

## relocate

[folder_rename.py](../../../folder_rename.py) · `function`.

```python
def relocate(store, db, view, destination, *, details=None, verify=None, progress=None):
```

Переносит папку и согласует пути SQLite с файловым журналом и снимком базы.

Вызывается под блокировками и BEGIN IMMEDIATE; дополнительная сверка проходит до перепривязки.

Непосредственные вызовы: `store.root.resolve`, `(details or {}).get`, `restore.check`, `folder_role`, `db.execute`, `restore.inside`, `(root / row[0]).is_dir`, `str`, `store.database.resolve`, `row.keys`, `restore.table`, `layout.Plan`, `sorted`, `Path`, `layout_scope`, `plan.move`, `FolderRenameConflict`, `plan.create_session`, `layout.save_json`, `shutil.copyfile`, `closing`, `sqlite3.connect`, `store.database.resolve().as_uri`, `original.backup`, `backup.execute('PRAGMA quick_check').fetchone`, `backup.execute`, `ValueError`, `json.dumps`, `db.commit`, `report`, `layout.apply`, `verify`, `restore.remap`, `restore.rewrite`, `db.rollback`, `restore.undo`, `layout.append`, `session.relative_to(root).as_posix`, `session.relative_to`, `print`.

Явные исключения: `FolderRenameConflict`, `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
result
```

<a id="symbol-rename"></a>

## rename

[folder_rename.py](../../../folder_rename.py) · `function`.

```python
def rename(store, payload):
```

Переименовывает объект без перезаписи существующего назначения.

Работает с таблицами orders, folder_renames.

Непосредственные вызовы: `store.root.resolve`, `store.connect`, `db.execute`, `preview`, `payload.get`, `FolderRenameConflict`, `name`, `unicodedata.normalize`, `Path`, `ValueError`, `(Path(source).parent / new_name).as_posix`, `available`, `layout.exists`, `relocate`.

Явные исключения: `FolderRenameConflict`, `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
relocate(store, db, view, destination)
```

<a id="symbol-target"></a>

## target

[folder_rename.py](../../../folder_rename.py) · `function`.

```python
def target(root, relative):
```

Находит допустимую существующую цель файловой операции.

При недопустимом состоянии возбуждает ValueError, FileNotFoundError.

Непосредственные вызовы: `isinstance`, `available`, `ValueError`, `layout.safe_path`, `Path`, `layout_scope`, `path.is_dir`, `FileNotFoundError`.

Явные исключения: `ValueError`, `FileNotFoundError`.

Выражения возврата (ветки читаются в исходнике):

```python
path
```
