# event_folders.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [event_folders.py](../../../event_folders.py).

Нумерованные события заказа: создание и подтверждённое исправление имён.

Импорты Python, включая локальные: `event_folder_undo`, `folder_layout`, `folder_notes`, `folder_structure`, `hashlib`, `json`, `order_folders`, `os`, `pathlib`, `re`, `shutil`, `sqlite3`, `stat`, `unicodedata`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-EventFolderConflict"></a>

## EventFolderConflict

[event_folders.py](../../../event_folders.py) · `class`.

```python
class EventFolderConflict(ValueError):
```

Обозначает конфликт изменения в этом модуле.

Вызывающий обработчик использует тип исключения для отказа без подмены данных.

<a id="symbol-create"></a>

## create

[event_folders.py](../../../event_folders.py) · `function`.

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

<a id="symbol-current"></a>

## current

[event_folders.py](../../../event_folders.py) · `function`.

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

<a id="symbol-event_number"></a>

## event_number

[event_folders.py](../../../event_folders.py) · `function`.

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

<a id="symbol-parent"></a>

## parent

[event_folders.py](../../../event_folders.py) · `function`.

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

<a id="symbol-preview"></a>

## preview

[event_folders.py](../../../event_folders.py) · `function`.

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

<a id="symbol-rename"></a>

## rename

[event_folders.py](../../../event_folders.py) · `function`.

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

<a id="symbol-snapshot"></a>

## snapshot

[event_folders.py](../../../event_folders.py) · `function`.

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

<a id="symbol-title_name"></a>

## title_name

[event_folders.py](../../../event_folders.py) · `function`.

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
