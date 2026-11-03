# client_activity.py

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [client_activity.py:1](../../../client_activity.py#L1).

Client visibility in SQLite, with initial legacy marker import and old export compatibility.

Импорты Python, включая локальные: `event_folder_undo`, `folder_structure`, `json`, `order_document`, `pathlib`, `threading`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## ClientActivityConflict

[client_activity.py:18](../../../client_activity.py#L18) · `class`.

```python
class ClientActivityConflict(ValueError):
```

Обозначает конфликт изменения в этом модуле.

Вызывающий обработчик использует тип исключения для отказа без подмены данных.

## value

[client_activity.py:24](../../../client_activity.py#L24) · `function`.

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

## known

[client_activity.py:30](../../../client_activity.py#L30) · `function`.

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

## ClientActivity

[client_activity.py:36](../../../client_activity.py#L36) · `class`.

```python
class ClientActivity:
```

Поддерживает SQLite-индекс активности клиентов и совместимость прежних отметок.

Основные операции: __init__, connect, schema, record, matches; остальные описаны у методов.

## ClientActivity.__init__

[client_activity.py:43](../../../client_activity.py#L43) · `function`.

```python
def __init__(self, orders, lock=LOCK):
```

Сохраняет зависимости и начальные параметры экземпляра.

Состояние и зависимости сохраняются в полях self для последующих операций.

Прямые присваивания полям/свойствам: `self.orders`, `self.root`, `self.lock`.

## ClientActivity.connect

[client_activity.py:50](../../../client_activity.py#L50) · `function`.

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

## ClientActivity.schema

[client_activity.py:56](../../../client_activity.py#L56) · `function`.

```python
def schema(cls, db):
```

Создаёт отсутствующие таблицы и совместимые расширения схемы.

Создаёт таблицу индекса активности с именем из доверенного cls.table.

Непосредственные вызовы: `db.execute`.

## ClientActivity.record

[client_activity.py:63](../../../client_activity.py#L63) · `function`.

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

## ClientActivity.matches

[client_activity.py:74](../../../client_activity.py#L74) · `function`.

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

## ClientActivity.target

[client_activity.py:79](../../../client_activity.py#L79) · `function`.

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

## ClientActivity.get

[client_activity.py:94](../../../client_activity.py#L94) · `function`.

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

## ClientActivity.read

[client_activity.py:104](../../../client_activity.py#L104) · `function`.

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

## ClientActivity.save

[client_activity.py:133](../../../client_activity.py#L133) · `function`.

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

## ClientActivity.accept_file

[client_activity.py:156](../../../client_activity.py#L156) · `function`.

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

## ClientActivity.inactive_paths

[client_activity.py:177](../../../client_activity.py#L177) · `function`.

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

## ClientActivity.visible_orders

[client_activity.py:187](../../../client_activity.py#L187) · `function`.

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

## ClientActivity.refresh

[client_activity.py:193](../../../client_activity.py#L193) · `function`.

```python
def refresh(self):
```

Обновляет индекс ролей папок без чтения вложений заказов.

Передаёт работу `folders`, `is_catalog_group`, `candidate.relative_to(self.root).as_posix`.

Непосредственные вызовы: `folders`, `is_catalog_group`, `candidate.relative_to(self.root).as_posix`, `candidate.relative_to`, `client_path`, `self.read`, `self.error`, `print`.

## ClientActivity.refresh.folders

[client_activity.py:197](../../../client_activity.py#L197) · `function`.

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

## ClientActivity.error

[client_activity.py:215](../../../client_activity.py#L215) · `function`.

```python
def error(self, path, problem):
```

Записывает ошибку обработки для последующего показа или повтора.

Передаёт работу `self.connect`, `self.schema`, `db.execute`.

Непосредственные вызовы: `self.connect`, `self.schema`, `db.execute`, `document.icloud_access.sync_error`.

## ClientActivity.sync

[client_activity.py:222](../../../client_activity.py#L222) · `function`.

```python
def sync(self):
```

Обслуживает прежнюю файловую отметку только вне SQLite-only.

При недопустимом состоянии возбуждает ClientActivityConflict.

Непосредственные вызовы: `self.connect`, `self.schema`, `db.execute`, `self.orders.database.exists`, `list`, `self.target`, `document.load`, `value`, `json.loads`, `ClientActivityConflict`, `record.setdefault`, `document.archive_current`, `document.atomic_write`, `document.render`, `document.archive_legacy`, `json.dumps`, `self.error`.

Явные исключения: `ClientActivityConflict`.

## is_inactive

[client_activity.py:255](../../../client_activity.py#L255) · `function`.

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
