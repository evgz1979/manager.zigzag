# mobile_sync.py

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [mobile_sync.py:1](../../../mobile_sync.py#L1).

Offline phone companion: immutable operations, durable receipts, read-only catalog.

SQLite stays on the Mac. The current database_only mode pauses all exchange.
The legacy file protocol below is retained for future adaptation and recovery.
The phone never edits !.txt or a file-comment document directly.

Импорты Python, включая локальные: `collections`, `event_folder_undo`, `file_comments`, `hashlib`, `json`, `math`, `order_document`, `os`, `pathlib`, `threading`, `time`, `uuid`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## MobileConflict

[mobile_sync.py:28](../../../mobile_sync.py#L28) · `class`.

```python
class MobileConflict(ValueError):
```

Обозначает конфликт изменения в этом модуле.

Вызывающий обработчик использует тип исключения для отказа без подмены данных.

## encode

[mobile_sync.py:34](../../../mobile_sync.py#L34) · `function`.

```python
def encode(value):
```

Кодирует данные в устойчивое текстовое представление протокола.

Возвращает `json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n'`.

Непосредственные вызовы: `json.dumps`.

Выражения возврата (ветки читаются в исходнике):

```python
json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n'
```

## identifier

[mobile_sync.py:40](../../../mobile_sync.py#L40) · `function`.

```python
def identifier(value):
```

Проверяет или вычисляет устойчивую идентичность объекта.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `str`, `uuid.UUID`, `ValueError`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
value
```

## regular

[mobile_sync.py:52](../../../mobile_sync.py#L52) · `function`.

```python
def regular(path):
```

Запрещает ссылки и объекты, не являющиеся обычным файлом.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `path.is_symlink`, `path.exists`, `path.is_file`, `ValueError`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
path
```

## read_json

[mobile_sync.py:60](../../../mobile_sync.py#L60) · `function`.

```python
def read_json(path, limit=MAX_OPERATION):
```

Читает ограниченный обычный JSON-файл протокола.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `regular`, `path.stat`, `ValueError`, `json.loads`, `path.read_bytes`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
json.loads(path.read_bytes())
```

## write_json

[mobile_sync.py:69](../../../mobile_sync.py#L69) · `function`.

```python
def write_json(path, value):
```

Записывает JSON только при изменении сериализованного содержимого.

Передаёт работу `regular`, `encode`, `path.exists`.

Непосредственные вызовы: `regular`, `encode`, `path.exists`, `path.read_text`, `document.atomic_write`.

## reconcile_tasks

[mobile_sync.py:78](../../../mobile_sync.py#L78) · `function`.

```python
def reconcile_tasks(previous, current):
```

Сохраняет идентичности однозначных задач и создаёт новые при неоднозначности.

Возвращает `None`; либо `result`.

Непосредственные вызовы: `collections.defaultdict`, `old_groups[item['text']].append`, `new_groups[item['text']].append`, `collections.Counter`, `len`, `str`, `uuid.uuid4`, `old[index].get`, `result.append`.

Выражения возврата (ветки читаются в исходнике):

```python
None
result
```

## file_token

[mobile_sync.py:110](../../../mobile_sync.py#L110) · `function`.

```python
def file_token(path):
```

Вычисляет привязку действия к текущей версии файла.

Возвращает `hashlib.sha256(f'{stat.st_dev}:{stat.st_ino}:{stat.st_size}:{stat.st_mtime_ns}'.encode()).hexdigest()`.

Непосредственные вызовы: `path.stat`, `hashlib.sha256(f'{stat.st_dev}:{stat.st_ino}:{stat.st_size}:{stat.st_mtime_ns}'.encode()).hexdigest`, `hashlib.sha256`, `f'{stat.st_dev}:{stat.st_ino}:{stat.st_size}:{stat.st_mtime_ns}'.encode`.

Выражения возврата (ветки читаются в исходнике):

```python
hashlib.sha256(f'{stat.st_dev}:{stat.st_ino}:{stat.st_size}:{stat.st_mtime_ns}'.encode()).hexdigest()
```

## MobileBridge

[mobile_sync.py:117](../../../mobile_sync.py#L117) · `class`.

```python
class MobileBridge:
```

Объединяет операции модуля: сохранённый протокол отложенного обмена с iphone; при database_only обмен запрещён.

Основные операции: __init__, get_meta, put_meta, configure, status; остальные описаны у методов.

## MobileBridge.__init__

[mobile_sync.py:120](../../../mobile_sync.py#L120) · `function`.

```python
def __init__(self, store):
```

Сохраняет зависимости и начальные параметры экземпляра.

Работает с таблицами mobile_meta, mobile_operations, mobile_tasks, mobile_files.

Непосредственные вызовы: `store.connect`, `db.execute`.

Прямые присваивания полям/свойствам: `self.store`, `self.folder`.

## MobileBridge.get_meta

[mobile_sync.py:136](../../../mobile_sync.py#L136) · `function`.

```python
def get_meta(db, key, default=''):
```

Читает служебное значение сохранённого состояния обмена.

Работает с таблицами mobile_meta.

Непосредственные вызовы: `db.execute('SELECT value FROM mobile_meta WHERE key=?', (key,)).fetchone`, `db.execute`.

Выражения возврата (ветки читаются в исходнике):

```python
row[0] if row else default
```

## MobileBridge.put_meta

[mobile_sync.py:143](../../../mobile_sync.py#L143) · `function`.

```python
def put_meta(db, key, value):
```

Записывает служебное значение сохранённого состояния обмена.

Работает с таблицами mobile_meta.

Непосредственные вызовы: `db.execute`, `str`.

## MobileBridge.configure

[mobile_sync.py:148](../../../mobile_sync.py#L148) · `function`.

```python
def configure(self, enabled):
```

Проверяет и сохраняет настройки функции с учётом режима хранения.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `ValueError`, `type`, `self.store.connect`, `self.put_meta`, `int`, `self.status`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
self.status()
```

## MobileBridge.status

[mobile_sync.py:159](../../../mobile_sync.py#L159) · `function`.

```python
def status(self):
```

Возвращает состояние обработки и сохранённые ошибки.

Работает с таблицами mobile_meta, mobile_operations.

Непосредственные вызовы: `self.store.connect`, `dict`, `db.execute`, `db.execute("SELECT COUNT(*) FROM mobile_operations WHERE status='conflict'").fetchone`, `values.get`, `RUN_LOCK.locked`, `float`, `int`.

Выражения возврата (ветки читаются в исходнике):

```python
{'enabled': not self.store.database_only and values.get('enabled') == '1', 'paused': self.store.database_only, 'running': RUN_LOCK.locked(), 'last_sync': float(values.get('last_sync', 0)), 'error': values.get('error', ''), 'orders': int(values.get('orders', 0)), 'conflicts': conflicts}
```

## MobileBridge.prepare

[mobile_sync.py:169](../../../mobile_sync.py#L169) · `function`.

```python
def prepare(self):
```

Создаёт подготовленное состояние операции до её применения.

При недопустимом состоянии возбуждает FileNotFoundError, ValueError, MobileConflict.

Непосредственные вызовы: `self.store.root.is_dir`, `FileNotFoundError`, `path.is_symlink`, `path.exists`, `path.is_dir`, `ValueError`, `path.mkdir`, `self.store.connect`, `self.get_meta`, `identity_file.exists`, `read_json`, `identifier`, `identity.get`, `MobileConflict`, `str`, `uuid.uuid4`, `write_json`, `self.put_meta`.

Явные исключения: `FileNotFoundError`, `ValueError`, `MobileConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
root_id
```

## MobileBridge.target_file

[mobile_sync.py:193](../../../mobile_sync.py#L193) · `function`.

```python
def target_file(self, relative, order_path):
```

Проверяет точный файл и его привязку для ожидающего действия.

При недопустимом состоянии возбуждает MobileConflict, FileNotFoundError.

Непосредственные вызовы: `isinstance`, `PurePosixPath(relative).is_absolute`, `PurePosixPath`, `PurePosixPath(relative).as_posix`, `any`, `part.startswith`, `relative.split`, `relative.startswith`, `Path`, `MobileConflict`, `target.is_symlink`, `target.is_file`, `self.store.target`, `target.with_name('.' + target.name + '.icloud').exists`, `target.with_name`, `FileNotFoundError`.

Явные исключения: `MobileConflict`, `FileNotFoundError`.

Выражения возврата (ветки читаются в исходнике):

```python
target
```

## MobileBridge.tasks

[mobile_sync.py:214](../../../mobile_sync.py#L214) · `function`.

```python
def tasks(self, db, record):
```

Сопоставляет задачи заказа с устойчивыми идентификаторами обмена.

Работает с таблицами mobile_tasks.

Непосредственные вызовы: `db.execute('SELECT items FROM mobile_tasks WHERE order_id=?', (record['id'],)).fetchone`, `db.execute`, `reconcile_tasks`, `json.loads`, `encode`.

Выражения возврата (ветки читаются в исходнике):

```python
items
```

## MobileBridge.validate

[mobile_sync.py:222](../../../mobile_sync.py#L222) · `function`.

```python
def validate(self, operation, root_id):
```

Проверяет структуру и допустимые значения входных данных.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `operation.get`, `ValueError`, `identifier`, `type`, `math.isfinite`, `text.strip`, `len`, `operation['kind'].startswith`.

Явные исключения: `ValueError`.

## MobileBridge.apply

[mobile_sync.py:253](../../../mobile_sync.py#L253) · `function`.

```python
def apply(self, operation, raw, root_id):
```

Применяет проверенную операцию или подготовленный план.

Работает с таблицами mobile_operations, orders.

Непосредственные вызовы: `self.validate`, `hashlib.sha256(raw).hexdigest`, `hashlib.sha256`, `self.store.connect`, `db.execute('SELECT * FROM mobile_operations WHERE id=?', (op_id,)).fetchone`, `db.execute`, `MobileConflict`, `json.loads`, `receipt_file.exists`, `read_json`, `receipt.get`, `raw.decode`, `encode`, `operation.get`, `db.execute('SELECT status FROM mobile_operations WHERE id=?', (dependency,)).fetchone`, `db.execute('SELECT * FROM orders WHERE id=? AND registered=1', (operation['order_id'],)).fetchone`, `self.store.record`, `assert_unlocked`, `self.apply_file`, `self.apply_order`, `result.update`, `str`.

Явные исключения: `MobileConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
json.loads(previous['result'])
receipt
None
result
```

## MobileBridge.apply_order

[mobile_sync.py:308](../../../mobile_sync.py#L308) · `function`.

```python
def apply_order(self, db, operation, record):
```

Применяет подтверждённую операцию к данным исходного заказа.

Работает с таблицами orders, mobile_tasks.

Непосредственные вызовы: `operation['text'].strip`, `len`, `MobileConflict`, `db.execute`, `time.time`, `self.tasks`, `next`, `enumerate`, `document.validate_todos`, `items.append`, `document.write_todos`, `encode`.

Явные исключения: `MobileConflict`.

## MobileBridge.apply_file

[mobile_sync.py:344](../../../mobile_sync.py#L344) · `function`.

```python
def apply_file(self, db, operation, raw, digest, record, previous):
```

Применяет комментарий к проверенной версии исходного файла.

Работает с таблицами mobile_files, mobile_operations.

Непосредственные вызовы: `db.commit`, `self.target_file`, `operation.get`, `file_comments.read`, `json.loads`, `file_comments.paths`, `history.parent.is_symlink`, `history.parent.parent.is_symlink`, `MobileConflict`, `history.is_symlink`, `history.is_file`, `hashlib.sha256(history.read_bytes()).hexdigest`, `hashlib.sha256`, `history.read_bytes`, `db.execute`, `file_token`, `operation['text'].strip`, `len`, `json.dumps`, `comment.replace('\r\n', '\n').replace('\r', '\n').replace`, `comment.replace('\r\n', '\n').replace`, `comment.replace`, `hashlib.sha256(body.encode()).hexdigest`, `body.encode`, `raw.decode`, `encode`, `file_comments.save`.

Явные исключения: `MobileConflict`.

## MobileBridge.inventory

[mobile_sync.py:383](../../../mobile_sync.py#L383) · `function`.

```python
def inventory(self, record):
```

Собирает ограниченный перечень доступных файлов заказа для каталога телефона.

Работает с таблицами mobile_files.

Непосредственные вызовы: `self.store.connect`, `db.execute('SELECT * FROM mobile_files WHERE order_id=?', (record['id'],)).fetchone`, `db.execute`, `time.time`, `json.loads`, `self.store.target`, `os.walk`, `sorted`, `name.startswith`, `(Path(parent) / name).is_symlink`, `Path`, `target.is_symlink`, `target.is_file`, `target.stat`, `file_comments.read`, `files.append`, `target.relative_to(self.store.root).as_posix`, `target.relative_to`, `file_token`, `len`, `ValueError`, `encode`, `str`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
(json.loads(saved['items']), saved['scanned'], '')
(files, scanned, '')
(json.loads(saved['items']) if saved else [], saved['scanned'] if saved else 0, str(error))
```

## MobileBridge.catalog

[mobile_sync.py:415](../../../mobile_sync.py#L415) · `function`.

```python
def catalog(self, root_id):
```

Собирает доступный каталог сущностей из сохранённых индексов.

Работает с таблицами mobile_operations.

Непосредственные вызовы: `self.store.list`, `self.store.connect`, `self.tasks`, `self.inventory`, `orders.append`, `orders[-1].update`, `record['extra_blocks'].get`, `int`, `self.get_meta`, `self.put_meta`, `json.loads`, `db.execute`, `time.time`.

Выражения возврата (ветки читаются в исходнике):

```python
{'schema': 1, 'root_id': root_id, 'generation': generation, 'generated': time.time(), 'orders': orders, 'receipts': receipts}
```

## MobileBridge.run

[mobile_sync.py:434](../../../mobile_sync.py#L434) · `function`.

```python
def run(self):
```

Сохраняет прежний цикл обмена; при database_only возвращается без файловых операций.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `self.status`, `RUN_LOCK.acquire`, `self.prepare`, `sorted`, `(self.folder / '.inbox').glob`, `regular`, `path.stat`, `ValueError`, `path.read_bytes`, `json.loads`, `self.validate`, `pending.append`, `errors.append`, `pending.sort`, `self.apply`, `write_json`, `self.store.sync`, `self.catalog`, `self.store.connect`, `self.put_meta`, `len`, `'\n'.join`, `str`, `RUN_LOCK.release`.

Явные исключения: `ValueError`.
