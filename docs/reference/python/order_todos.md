# order_todos.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [order_todos.py](../../../order_todos.py).

Сводка задач из SQLite; чтение файлов вложенных папок выполняется отдельно в фоне.

Импорты Python, включая локальные: `folder_notes`, `order_document`, `os`, `pathlib`, `re`, `threading`, `time`, `unicodedata`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-OrderTodos"></a>

## OrderTodos

[order_todos.py](../../../order_todos.py) · `class`.

```python
class OrderTodos:
```

Объединяет операции модуля: сводки собственных и вложенных задач заказа из локальной базы.

Основные операции: __init__, attach, scope, in_order, refresh.

<a id="symbol-OrderTodos.__init__"></a>

## OrderTodos.__init__

[order_todos.py](../../../order_todos.py) · `function`.

```python
def __init__(self, store):
```

Сохраняет зависимости и начальные параметры экземпляра.

Состояние и зависимости сохраняются в полях self для последующих операций.

Непосредственные вызовы: `FolderNotes`.

Прямые присваивания полям/свойствам: `self.store`, `self.notes`.

<a id="symbol-OrderTodos.attach"></a>

## OrderTodos.attach

[order_todos.py](../../../order_todos.py) · `function`.

```python
def attach(self, orders, *, include_missing=False, include_completed=False):
```

Привязывает существующие данные к выбранной сущности или сводке.

Работает с таблицами folder_notes, sqlite_master, todo_missing_folders, todo_catalog.

Непосредственные вызовы: `by_path.values`, `group`, `order['todo_groups'].append`, `self.notes.connect`, `db.execute('SELECT * FROM folder_notes').fetchall`, `db.execute`, `db.execute("SELECT 1 FROM sqlite_master WHERE name='todo_missing_folders'").fetchone`, `set`, `db.execute("SELECT 1 FROM sqlite_master WHERE name='todo_catalog'").fetchone`, `sorted`, `any`, `part.startswith`, `Path`, `next`, `Path(*parts[:i]).as_posix`, `range`, `len`, `self.notes.record`, `by_path[owner]['todo_groups'].append`.

Выражения возврата (ветки читаются в исходнике):

```python
orders
[by_path[order['path']] for order in orders]
```

<a id="symbol-OrderTodos.in_order"></a>

## OrderTodos.in_order

[order_todos.py](../../../order_todos.py) · `function`.

```python
def in_order(self, relative):
```

Собирает все вложенные задачи для страницы заказа из SQLite.

Формирует возвращаемое значение из проверенного локального состояния.

Непосредственные вызовы: `self.store.path`, `self.store.get`, `self.store.list`, `self.scope`, `orders.items`, `path.startswith`, `self.attach`, `len`, `sorted`, `min`, `' · '.join`, `dict.fromkeys`.

Выражения возврата (ветки читаются в исходнике):

```python
{'path': relative, 'todo_groups': sorted(groups, key=lambda item: path_key(item['path'])), 'todo_index': {'checked': min(checked) if len(checked) == len(indexes) else None, 'error': ' · '.join(dict.fromkeys((index['error'] for index in indexes if index['error'])))}}
```

<a id="symbol-OrderTodos.refresh"></a>

## OrderTodos.refresh

[order_todos.py](../../../order_todos.py) · `function`.

```python
def refresh(self, extra_paths=()):
```

Обновляет индекс из разрешённого источника данных.

Работает с таблицами todo_catalog, todo_missing_folders.

Непосредственные вызовы: `REFRESH_LOCK.acquire`, `self.store.list`, `set`, `self.store.path`, `extra_scopes.add`, `orders.append`, `self.scope`, `self.attach`, `self.store.require_order_folder`, `self.store.target`, `os.walk`, `Path`, `parent_order`, `(folder / '__todo_scope__').relative_to(self.store.root).as_posix`, `(folder / '__todo_scope__').relative_to`, `sorted`, `name.startswith`, `(folder / name).is_symlink`, `(folder / name).relative_to(self.store.root).as_posix`, `(folder / name).relative_to`, `folder.relative_to(self.store.root).as_posix`, `folder.relative_to`, `seen.add`, `self.notes.get`, `any`, `(folder / name).exists`, `self.notes.read`, `errors.append`, `str`, `self.notes.connect`, `db.execute`, `db.executemany`, `time.time`, `db.execute('SELECT checked FROM todo_catalog WHERE path=?', (relative,)).fetchone`, `' · '.join`, `REFRESH_LOCK.release`.

<a id="symbol-OrderTodos.refresh.on_error"></a>

## OrderTodos.refresh.on_error

[order_todos.py](../../../order_todos.py) · `function`.

```python
def on_error(error):
```

Сохраняет ошибку обхода, не выдавая неполный результат за полный.

Передаёт работу `errors.append`.

Непосредственные вызовы: `errors.append`, `str`.

<a id="symbol-OrderTodos.scope"></a>

## OrderTodos.scope

[order_todos.py](../../../order_todos.py) · `function`.

```python
def scope(relative):
```

Вычисляет область видимости и допустимых связей текущей сущности.

Возвращает `{'path': relative, 'todo_items': [], 'extra_blocks': {}, 'sync_pending': False, 'sync_error': ''}`.

Выражения возврата (ветки читаются в исходнике):

```python
{'path': relative, 'todo_items': [], 'extra_blocks': {}, 'sync_pending': False, 'sync_error': ''}
```

<a id="symbol-group"></a>

## group

[order_todos.py](../../../order_todos.py) · `function`.

```python
def group(path, label, items, blocks, *, include_completed=False, **metadata):
```

Группирует проверенные записи или папки в предусмотренные категории.

Возвращает `None`; либо `{'path': path, 'label': label, 'items': items, 'legacy_text': legacy, **metadata}`.

Непосредственные вызовы: `blocks.get`.

Выражения возврата (ветки читаются в исходнике):

```python
None
{'path': path, 'label': label, 'items': items, 'legacy_text': legacy, **metadata}
```

<a id="symbol-path_key"></a>

## path_key

[order_todos.py](../../../order_todos.py) · `function`.

```python
def path_key(path):
```

Вычисляет нормализованный ключ для обращения к данным.

Формирует возвращаемое значение из проверенного локального состояния.

Непосредственные вызовы: `name.startswith`, `part.isdigit`, `int`, `re.split`, `unicodedata.normalize('NFC', name).casefold`, `unicodedata.normalize`, `Path`.

Выражения возврата (ветки читаются в исходнике):

```python
[(not name.startswith('#'), [int(part) if part.isdigit() else part for part in re.split('([0-9]+)', unicodedata.normalize('NFC', name).casefold())]) for name in Path(path).parts]
```
