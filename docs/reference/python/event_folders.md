# event_folders.py

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [event_folders.py:1](../../../event_folders.py#L1).

Нумерованные события заказа: создание и подтверждённое исправление имён.

Импорты Python, включая локальные: `event_folder_undo`, `folder_layout`, `folder_notes`, `folder_structure`, `hashlib`, `json`, `order_folders`, `os`, `pathlib`, `re`, `shutil`, `sqlite3`, `stat`, `unicodedata`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## EventFolderConflict

[event_folders.py:24](../../../event_folders.py#L24) · `class`.

```python
class EventFolderConflict(ValueError):
```

Обозначает конфликт изменения в этом модуле.

Вызывающий обработчик использует тип исключения для отказа без подмены данных.

## event_number

[event_folders.py:30](../../../event_folders.py#L30) · `function`.

```python
def event_number(name):
```

Извлекает допустимый порядковый номер события из имени папки.

Возвращает `None if dated(name) else NUMBER.match(name)`.

Непосредственные вызовы: `dated`, `NUMBER.match`.

Выражения возврата (ветки читаются в исходнике):

```python
None if dated(name) else NUMBER.match(name)
```

## parent

[event_folders.py:36](../../../event_folders.py#L36) · `function`.

```python
def parent(root, relative):
```

Определяет родительскую папку или заказ по допустимому пути.

При недопустимом состоянии возбуждает ValueError, FileNotFoundError.

Непосредственные вызовы: `isinstance`, `is_freza_task`, `ValueError`, `Path`, `any`, `part.startswith`, `is_service_folder`, `layout.safe_path`, `layout_scope`, `target.is_dir`, `FileNotFoundError`, `folder_role`.

Явные исключения: `ValueError`, `FileNotFoundError`.

Выражения возврата (ветки читаются в исходнике):

```python
target
```

## title_name

[event_folders.py:51](../../../event_folders.py#L51) · `function`.

```python
def title_name(number, title):
```

Проверяет имя создаваемого или переименовываемого объекта.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `any`, `ord`, `ValueError`, `unicodedata.normalize`, `title.strip`, `len`, `os.fsencode`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
name
```

## snapshot

[event_folders.py:65](../../../event_folders.py#L65) · `function`.

```python
def snapshot(target):
```

Собирает текущее наблюдаемое состояние для проверки или показа.

Возвращает `{'parent': layout.identity(target), 'children': children}`.

Непосредственные вызовы: `target.iterdir`, `item.name.startswith`, `children.append`, `layout.identity`, `children.sort`.

Выражения возврата (ветки читаются в исходнике):

```python
{'parent': layout.identity(target), 'children': children}
```

## preview

[event_folders.py:77](../../../event_folders.py#L77) · `function`.

```python
def preview(root, relative, notes=None):
```

Готовит проверяемое предложение операции без её выполнения.

Формирует возвращаемое значение из проверенного локального состояния.

Непосредственные вызовы: `Path(root).resolve`, `Path`, `parent`, `notes.store.database.exists`, `notes.connect`, `restore.assert_unlocked`, `snapshot`, `item['name'].startswith`, `events.sort`, `max`, `int`, `event_number`, `set`, `CANONICAL.fullmatch`, `canonical.add`, `used.add`, `re.match`, `name[match.end():].strip`, `match.end`, `suggestions.append`, `hashlib.sha256(json.dumps(fingerprint, sort_keys=True, ensure_ascii=False).encode()).hexdigest`, `hashlib.sha256`, `json.dumps(fingerprint, sort_keys=True, ensure_ascii=False).encode`, `json.dumps`.

Выражения возврата (ветки читаются в исходнике):

```python
{'path': relative, 'revision': hashlib.sha256(json.dumps(fingerprint, sort_keys=True, ensure_ascii=False).encode()).hexdigest(), 'next_number': f'{maximum + 1:02d}', 'suggestions': suggestions, 'before': before}
```

## current

[event_folders.py:119](../../../event_folders.py#L119) · `function`.

```python
def current(root, payload, notes=None):
```

Проверяет текущую запись и ожидаемую версию перед изменением.

При недопустимом состоянии возбуждает EventFolderConflict.

Непосредственные вызовы: `preview`, `payload.get`, `EventFolderConflict`.

Явные исключения: `EventFolderConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
result
```

## create

[event_folders.py:128](../../../event_folders.py#L128) · `function`.

```python
def create(root, payload, notes=None):
```

Создаёт новый объект после проверки области и входных данных.

При недопустимом состоянии возбуждает EventFolderConflict.

Непосредственные вызовы: `Path(root).resolve`, `Path`, `current`, `title_name`, `int`, `payload.get`, `str`, `layout.exists`, `EventFolderConflict`, `layout.Plan`, `layout_scope`, `plan.mkdir`, `plan.create_session`, `layout.identity`, `layout.apply`, `layout.save_json`, `isinstance`, `session.relative_to(root).as_posix`, `session.relative_to`.

Явные исключения: `EventFolderConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
{'path': relative, 'name': name, 'journal': session.relative_to(root).as_posix()}
```

## rename

[event_folders.py:155](../../../event_folders.py#L155) · `function`.

```python
def rename(notes, payload):
```

Переименовывает объект без перезаписи существующего назначения.

Работает с таблицами orders, folder_notes, event_renames.

Непосредственные вызовы: `payload.get`, `ValueError`, `notes.store.root.resolve`, `notes.connect`, `db.execute`, `current`, `restore.assert_unlocked`, `isinstance`, `len`, `item.get`, `set`, `layout.Plan`, `Path`, `layout_scope`, `str`, `title_name`, `int`, `layout.exists`, `EventFolderConflict`, `plan.move`, `mappings.append`, `restore.metadata_paths`, `any`, `restore.inside`, `db.execute('SELECT * FROM folder_notes').fetchall`, `changes.append`, `restore.schema`, `plan.create_session`, `layout.save_json`, `notes.store.database.resolve`, `shutil.copyfile`, `json.dumps`, `db.commit`, `layout.apply`, `db.rollback`, `restore.undo`, `layout.append`, `session.relative_to(root).as_posix`, `session.relative_to`.

Явные исключения: `ValueError`, `EventFolderConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
{'path': view['path'], 'renamed': mappings, 'journal': session.relative_to(root).as_posix()}
```
