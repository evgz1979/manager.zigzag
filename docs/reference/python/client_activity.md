# client_activity.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [client_activity.py](../../../client_activity.py).

Client visibility in SQLite, with initial legacy marker import and old export compatibility.

Импорты Python, включая локальные: `event_folder_undo`, `folder_structure`, `json`, `order_document`, `pathlib`, `threading`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-ClientActivity"></a>

## ClientActivity

[client_activity.py](../../../client_activity.py) · `class`.

```python
class ClientActivity:
```

Поддерживает SQLite-индекс активности клиентов и совместимость прежних отметок.

Основные операции: __init__, connect, schema, record, matches; остальные описаны у методов.

<a id="symbol-ClientActivity.__init__"></a>

## ClientActivity.__init__

[client_activity.py](../../../client_activity.py) · `function`.

```python
def __init__(self, orders, lock=LOCK):
```

Сохраняет зависимости и начальные параметры экземпляра.

Состояние и зависимости сохраняются в полях self для последующих операций.

Прямые присваивания полям/свойствам: `self.orders`, `self.root`, `self.lock`.

<a id="symbol-ClientActivity.accept_file"></a>

## ClientActivity.accept_file

[client_activity.py](../../../client_activity.py) · `function`.

```python
def accept_file(self, payload):
```

Явно принимает файловую версию при разрешении прежнего конфликта активности.

При недопустимом состоянии возбуждает ValueError, ClientActivityConflict.

Непосредственные вызовы: `ValueError`, `payload.get`, `self.target`, `self.connect`, `self.schema`, `db.execute(f'SELECT * FROM {self.table} WHERE path=?', (path,)).fetchone`, `db.execute`, `type`, `ClientActivityConflict`, `value`, `document.load`, `known`, `int`, `raw.strip`, `json.dumps`, `self.get`.

Явные исключения: `ValueError`, `ClientActivityConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
self.get(path)
```

<a id="symbol-ClientActivity.connect"></a>

## ClientActivity.connect

[client_activity.py](../../../client_activity.py) · `function`.

```python
def connect(self):
```

Открывает соединение SQLite и управляет его временем жизни.

Возвращает `self.orders.connect()`.

Непосредственные вызовы: `self.orders.connect`.

Выражения возврата (ветки читаются в исходнике):

```python
self.orders.connect()
```

<a id="symbol-ClientActivity.error"></a>

## ClientActivity.error

[client_activity.py](../../../client_activity.py) · `function`.

```python
def error(self, path, problem):
```

Записывает ошибку обработки для последующего показа или повтора.

Передаёт работу `self.connect`, `self.schema`, `db.execute`.

Непосредственные вызовы: `self.connect`, `self.schema`, `db.execute`, `document.icloud_access.sync_error`.

<a id="symbol-ClientActivity.get"></a>

## ClientActivity.get

[client_activity.py](../../../client_activity.py) · `function`.

```python
def get(self, path):
```

Читает сохранённую отметку активности одного пути.

Возвращает `None`; либо `self.record(row) if row else None`.

Непосредственные вызовы: `self.orders.database.exists`, `self.connect`, `self.schema`, `db.execute(f'SELECT * FROM {self.table} WHERE path=?', (path,)).fetchone`, `db.execute`, `self.record`.

Выражения возврата (ветки читаются в исходнике):

```python
None
self.record(row) if row else None
```

<a id="symbol-ClientActivity.inactive_paths"></a>

## ClientActivity.inactive_paths

[client_activity.py](../../../client_activity.py) · `function`.

```python
def inactive_paths(self):
```

Читает множество неактивных путей из индекса базы.

Возвращает `set()`; либо `{row[0] for row in db.execute(f'SELECT path FROM {self.table} WHERE inactive=1')}`.

Непосредственные вызовы: `self.orders.database.exists`, `set`, `self.connect`, `self.schema`, `db.execute`.

Выражения возврата (ветки читаются в исходнике):

```python
set()
{row[0] for row in db.execute(f'SELECT path FROM {self.table} WHERE inactive=1')}
```

<a id="symbol-ClientActivity.matches"></a>

## ClientActivity.matches

[client_activity.py](../../../client_activity.py) · `function`.

```python
def matches(self, path):
```

Проверяет соответствие папки роли индексируемой сущности.

Возвращает `client_path(path) == path`.

Непосредственные вызовы: `client_path`.

Выражения возврата (ветки читаются в исходнике):

```python
client_path(path) == path
```

<a id="symbol-ClientActivity.read"></a>

## ClientActivity.read

[client_activity.py](../../../client_activity.py) · `function`.

```python
def read(self, path):
```

Получает активность пути с допустимым первоначальным импортом отметки.

Создаёт таблицу индекса активности с именем из доверенного cls.table.

Непосредственные вызовы: `self.get`, `self.target`, `value`, `document.load`, `self.connect`, `self.schema`, `db.execute(f'SELECT * FROM {self.table} WHERE path=?', (path,)).fetchone`, `db.execute`, `known`, `raw.strip`, `bool`, `int`, `json.loads`, `json.dumps`.

Выражения возврата (ветки читаются в исходнике):

```python
current
self.get(path)
```

<a id="symbol-ClientActivity.record"></a>

## ClientActivity.record

[client_activity.py](../../../client_activity.py) · `function`.

```python
def record(self, row):
```

Преобразует строку SQLite в представление для вызывающего кода.

Разбирает JSON; вызывающий код должен учитывать ошибки или неизвестный формат.

Непосредственные вызовы: `dict`, `bool`, `result.pop`, `known`, `json.loads`, `result.update`.

Выражения возврата (ветки читаются в исходнике):

```python
result
```

<a id="symbol-ClientActivity.refresh"></a>

## ClientActivity.refresh

[client_activity.py](../../../client_activity.py) · `function`.

```python
def refresh(self):
```

Обновляет индекс ролей папок без чтения вложений заказов.

Передаёт работу `folders`, `is_catalog_group`, `candidate.relative_to(self.root).as_posix`.

Непосредственные вызовы: `folders`, `is_catalog_group`, `candidate.relative_to(self.root).as_posix`, `candidate.relative_to`, `client_path`, `self.read`, `self.error`, `print`.

<a id="symbol-ClientActivity.refresh.folders"></a>

## ClientActivity.refresh.folders

[client_activity.py](../../../client_activity.py) · `function`.

```python
def folders(parent):
```

Перечисляет допустимые папки текущего ограниченного обхода.

Возвращает `[item for item in parent.iterdir() if not item.name.startswith(('.', '#')) and (not item.is_symlink()) and item.is_dir()]`.

Непосредственные вызовы: `parent.iterdir`, `item.name.startswith`, `item.is_symlink`, `item.is_dir`.

Выражения возврата (ветки читаются в исходнике):

```python
[item for item in parent.iterdir() if not item.name.startswith(('.', '#')) and (not item.is_symlink()) and item.is_dir()]
```

<a id="symbol-ClientActivity.save"></a>

## ClientActivity.save

[client_activity.py](../../../client_activity.py) · `function`.

```python
def save(self, payload):
```

Сохраняет явное решение об активности клиента или объекта по версии.

При недопустимом состоянии возбуждает ValueError, ClientActivityConflict.

Непосредственные вызовы: `payload.get`, `type`, `ValueError`, `isinstance`, `Path(path).is_absolute`, `Path`, `any`, `part.startswith`, `self.target`, `self.connect`, `self.schema`, `assert_unlocked`, `db.execute(f'SELECT * FROM {self.table} WHERE path=?', (path,)).fetchone`, `db.execute`, `ClientActivityConflict`, `known`, `json.loads`, `int`, `self.get`.

Явные исключения: `ValueError`, `ClientActivityConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
self.get(path)
```

<a id="symbol-ClientActivity.schema"></a>

## ClientActivity.schema

[client_activity.py](../../../client_activity.py) · `function`.

```python
def schema(cls, db):
```

Создаёт отсутствующие таблицы и совместимые расширения схемы.

Создаёт таблицу индекса активности с именем из доверенного cls.table.

Непосредственные вызовы: `db.execute`.

<a id="symbol-ClientActivity.sync"></a>

## ClientActivity.sync

[client_activity.py](../../../client_activity.py) · `function`.

```python
def sync(self):
```

Обслуживает прежнюю файловую отметку только вне SQLite-only.

При недопустимом состоянии возбуждает ClientActivityConflict.

Непосредственные вызовы: `self.connect`, `self.schema`, `db.execute`, `self.orders.database.exists`, `list`, `self.target`, `document.load`, `value`, `json.loads`, `ClientActivityConflict`, `record.setdefault`, `document.archive_current`, `document.atomic_write`, `document.render`, `document.archive_legacy`, `json.dumps`, `self.error`.

Явные исключения: `ClientActivityConflict`.

<a id="symbol-ClientActivity.target"></a>

## ClientActivity.target

[client_activity.py](../../../client_activity.py) · `function`.

```python
def target(self, path):
```

Находит допустимую существующую цель файловой операции.

При недопустимом состоянии возбуждает ValueError, FileNotFoundError.

Непосредственные вызовы: `isinstance`, `Path(path).is_absolute`, `Path`, `Path(path).as_posix`, `any`, `part.startswith`, `ValueError`, `guard_database`, `(self.root / Path(*Path(path).parts[:index + 1])).is_symlink`, `range`, `len`, `target.is_dir`, `FileNotFoundError`, `self.matches`.

Явные исключения: `ValueError`, `FileNotFoundError`.

Выражения возврата (ветки читаются в исходнике):

```python
target
```

<a id="symbol-ClientActivity.visible_orders"></a>

## ClientActivity.visible_orders

[client_activity.py](../../../client_activity.py) · `function`.

```python
def visible_orders(self, records):
```

Отбирает заказы вне неактивных клиентов и объектов.

Возвращает `[record for record in records if not is_inactive(record['path'], inactive)]`.

Непосредственные вызовы: `self.inactive_paths`, `is_inactive`.

Выражения возврата (ветки читаются в исходнике):

```python
[record for record in records if not is_inactive(record['path'], inactive)]
```

<a id="symbol-ClientActivityConflict"></a>

## ClientActivityConflict

[client_activity.py](../../../client_activity.py) · `class`.

```python
class ClientActivityConflict(ValueError):
```

Обозначает конфликт изменения в этом модуле.

Вызывающий обработчик использует тип исключения для отказа без подмены данных.

<a id="symbol-is_inactive"></a>

## is_inactive

[client_activity.py](../../../client_activity.py) · `function`.

```python
def is_inactive(path, paths):
```

Проверяет неактивность пути по границам компонентов без чтения документов.

Возвращает `any((path == parent or path.startswith(parent + '/') for parent in paths))`.

Непосредственные вызовы: `any`, `path.startswith`.

Выражения возврата (ветки читаются в исходнике):

```python
any((path == parent or path.startswith(parent + '/') for parent in paths))
```

<a id="symbol-known"></a>

## known

[client_activity.py](../../../client_activity.py) · `function`.

```python
def known(raw):
```

Проверяет, соответствует ли значение известному формату состояния.

Возвращает `raw is None or raw.strip() in (ACTIVE, INACTIVE)`.

Непосредственные вызовы: `raw.strip`.

Выражения возврата (ветки читаются в исходнике):

```python
raw is None or raw.strip() in (ACTIVE, INACTIVE)
```

<a id="symbol-value"></a>

## value

[client_activity.py](../../../client_activity.py) · `function`.

```python
def value(record, block=BLOCK):
```

Извлекает распознанное значение состояния из исходного представления.

Возвращает `record.get('extra_blocks', {}).get(block)`.

Непосредственные вызовы: `record.get('extra_blocks', {}).get`, `record.get`.

Выражения возврата (ветки читаются в исходнике):

```python
record.get('extra_blocks', {}).get(block)
```
