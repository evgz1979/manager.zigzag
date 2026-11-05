# object_orders.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [object_orders.py](../../../object_orders.py).

Object order lists: bounded folder-name discovery, then SQLite-only refreshes.

Импорты Python, включая локальные: `event_folder_undo`, `folder_structure`, `json`, `local_metadata`, `order_deadlines`, `order_document`, `order_todos`, `pathlib`, `threading`, `time`, `unicodedata`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-ObjectOrders"></a>

## ObjectOrders

[object_orders.py](../../../object_orders.py) · `class`.

```python
class ObjectOrders:
```

Поддерживает каталог заказов объекта отдельно от регистрации заказов.

Основные операции: __init__, path, put, refresh, save_catalog; остальные описаны у методов.

<a id="symbol-ObjectOrders.__init__"></a>

## ObjectOrders.__init__

[object_orders.py](../../../object_orders.py) · `function`.

```python
def __init__(self, store):
```

Сохраняет зависимости и начальные параметры экземпляра.

Состояние и зависимости сохраняются в полях self для последующих операций.

Непосредственные вызовы: `MetadataStore`.

Прямые присваивания полям/свойствам: `self.store`, `self.meta`.

<a id="symbol-ObjectOrders.allowed_paths"></a>

## ObjectOrders.allowed_paths

[object_orders.py](../../../object_orders.py) · `function`.

```python
def allowed_paths(self, relative, inactive, show_inactive):
```

Вычисляет допустимые пути текущего списка из сохранённого каталога.

Возвращает `allowed`.

Непосредственные вызовы: `canonical`, `inside`.

Выражения возврата (ветки читаются в исходнике):

```python
allowed
```

<a id="symbol-ObjectOrders.allowed_paths.allowed"></a>

## ObjectOrders.allowed_paths.allowed

[object_orders.py](../../../object_orders.py) · `function`.

```python
def allowed(path):
```

Проверяет допустимость одной папки в текущем каталоге.

Формирует возвращаемое значение из проверенного локального состояния.

Непосредственные вызовы: `canonical`, `inside`, `any`, `part.startswith`, `Path`.

Выражения возврата (ветки читаются в исходнике):

```python
inside(path, relative) and (not any((part.startswith(('.', '#')) for part in Path(path).parts))) and (show_inactive or not any((path == item or inside(path, item) for item in hidden)))
```

<a id="symbol-ObjectOrders.path"></a>

## ObjectOrders.path

[object_orders.py](../../../object_orders.py) · `function`.

```python
def path(self, relative):
```

Проверяет относительный путь внутри допустимой области.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `canonical`, `self.store.path`, `any`, `part.startswith`, `Path`, `ValueError`, `guard_database`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
relative
```

<a id="symbol-ObjectOrders.put"></a>

## ObjectOrders.put

[object_orders.py](../../../object_orders.py) · `function`.

```python
def put(self, kind, path, body):
```

Создаёт или меняет запись базы с предусмотренной проверкой текущего состояния.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `self.meta.get`, `ValueError`, `current.items`, `type`, `current.get`, `set`, `self.meta.put`.

Явные исключения: `ValueError`.

<a id="symbol-ObjectOrders.read"></a>

## ObjectOrders.read

[object_orders.py](../../../object_orders.py) · `function`.

```python
def read(self, relative, *, inactive=(), show_inactive=False):
```

Собирает список заказов объекта по каталогу и текущим данным SQLite.

Работает с таблицами metadata_records, sqlite_master, folder_notes.

Непосредственные вызовы: `self.path`, `self.meta.get`, `ValueError`, `type`, `scope.get`, `set`, `self.allowed_paths`, `self.store.list`, `allowed`, `records.setdefault(canonical(row['path']), []).append`, `records.setdefault`, `canonical`, `self.meta.connect`, `db.execute`, `json.loads`, `isinstance`, `data.get`, `catalog.add`, `db.execute("SELECT 1 FROM sqlite_master WHERE name='folder_notes'").fetchone`, `records.items`, `any`, `sorted`, `inside`, `result.extend`, `notes.get`, `body.get`, `Path`, `client_name`, `order_location`, `document.read_todos`, `document.read_purchases`, `document.read_favorite`, `order_deadlines.read`, `document.read_flag`, `document.read_blue_plus`, `document.read_dollar`, `order_deadlines.read_comments`, `result.append`, `OrderTodos(self.store).attach`, `OrderTodos`, `order_deadlines.week_options`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{'path': relative, 'orders': OrderTodos(self.store).attach(result), 'checked': scope.get('checked'), 'error': scope.get('error', ''), 'deadline_week_options': order_deadlines.week_options()}
```

<a id="symbol-ObjectOrders.refresh"></a>

## ObjectOrders.refresh

[object_orders.py](../../../object_orders.py) · `function`.

```python
def refresh(self, relative):
```

Перечитывает только имена подпапок объекта и контейнеров годов.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `self.store.path`, `self.path`, `self.store.target`, `folder_role`, `ValueError`, `set`, `stack.pop`, `sorted`, `folder.iterdir`, `child.name.startswith`, `child.is_symlink`, `child.is_dir`, `child.relative_to(self.store.root).as_posix`, `child.relative_to`, `found.add`, `canonical`, `stack.append`, `errors.append`, `str`, `self.save_catalog`.

Явные исключения: `ValueError`.

<a id="symbol-ObjectOrders.save_catalog"></a>

## ObjectOrders.save_catalog

[object_orders.py](../../../object_orders.py) · `function`.

```python
def save_catalog(self, relative, found, errors, *, allowed=None):
```

Сохраняет перечень известных папок без регистрации новых заказов.

Работает с таблицами metadata_records.

Непосредственные вызовы: `self.meta.connect`, `db.execute`, `inside`, `allowed`, `sorted`, `self.put`, `errors.append`, `str`, `set`, `time.time`, `' · '.join`.

<a id="symbol-canonical"></a>

## canonical

[object_orders.py](../../../object_orders.py) · `function`.

```python
def canonical(path):
```

Приводит путь к каноническому виду для сопоставления записей.

Возвращает `unicodedata.normalize('NFC', path)`.

Непосредственные вызовы: `unicodedata.normalize`.

Выражения возврата (ветки читаются в исходнике):

```python
unicodedata.normalize('NFC', path)
```

<a id="symbol-inside"></a>

## inside

[object_orders.py](../../../object_orders.py) · `function`.

```python
def inside(path, scope):
```

Проверяет принадлежность пути указанной области по границам компонентов.

Возвращает `path.startswith(scope + '/')`.

Непосредственные вызовы: `path.startswith`.

Выражения возврата (ветки читаются в исходнике):

```python
path.startswith(scope + '/')
```
