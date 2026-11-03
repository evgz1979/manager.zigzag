# folder_rename.py

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [folder_rename.py:1](../../../folder_rename.py#L1).

Rename one opened folder and all its SQLite paths, without duplicating orders.

Импорты Python, включая локальные: `contextlib`, `event_folder_undo`, `folder_layout`, `folder_notes`, `folder_rename_undo`, `folder_structure`, `hashlib`, `json`, `order_folders`, `order_todos`, `orders`, `os`, `pathlib`, `shutil`, `sqlite3`, `unicodedata`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## FolderRenameConflict

[folder_rename.py:23](../../../folder_rename.py#L23) · `class`.

```python
class FolderRenameConflict(ValueError):
```

Обозначает конфликт изменения в этом модуле.

Вызывающий обработчик использует тип исключения для отказа без подмены данных.

## available

[folder_rename.py:29](../../../folder_rename.py#L29) · `function`.

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

## target

[folder_rename.py:38](../../../folder_rename.py#L38) · `function`.

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

## preview

[folder_rename.py:49](../../../folder_rename.py#L49) · `function`.

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

## name

[folder_rename.py:59](../../../folder_rename.py#L59) · `function`.

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

## rename

[folder_rename.py:70](../../../folder_rename.py#L70) · `function`.

```python
def rename(store, payload):
```

Переименовывает объект без перезаписи существующего назначения.

Работает с таблицами orders, folder_renames.

Непосредственные вызовы: `store.root.resolve`, `store.connect`, `db.execute`, `preview`, `payload.get`, `FolderRenameConflict`, `name`, `unicodedata.normalize`, `Path`, `ValueError`, `(Path(source).parent / new_name).as_posix`, `available`, `layout.exists`, `restore.check`, `folder_role`, `restore.inside`, `(root / row[0]).is_dir`, `str`, `store.database.resolve`, `row.keys`, `restore.table`, `layout.Plan`, `list`, `layout_scope`, `plan.move`, `plan.create_session`, `layout.save_json`, `shutil.copyfile`, `closing`, `sqlite3.connect`, `store.database.resolve().as_uri`, `original.backup`, `json.dumps`, `db.commit`, `layout.apply`, `restore.remap`, `restore.rewrite`, `db.rollback`, `restore.undo`, `layout.append`, `session.relative_to(root).as_posix`, `session.relative_to`.

Явные исключения: `FolderRenameConflict`, `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{'path': destination, 'source': source, 'name': new_name, 'journal': session.relative_to(root).as_posix()}
```
