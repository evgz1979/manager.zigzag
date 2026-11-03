# orders.py

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [orders.py:1](../../../orders.py#L1).

SQLite order register with partial revisions, legacy imports and export compatibility.

Импорты Python, включая локальные: `calendar_layout`, `contextlib`, `event_folder_undo`, `folder_notes`, `folder_structure`, `hashlib`, `json`, `local_metadata`, `mobile_sync`, `order_calendar`, `order_deadlines`, `order_document`, `order_links`, `os`, `pathlib`, `reconciliations`, `sqlite3`, `supplier_purchases`, `threading`, `time`, `uuid`, `work_orders`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## OrderConflict

[orders.py:28](../../../orders.py#L28) · `class`.

```python
class OrderConflict(ValueError):
```

Обозначает конфликт изменения в этом модуле.

Вызывающий обработчик использует тип исключения для отказа без подмены данных.

## OrderStore

[orders.py:34](../../../orders.py#L34) · `class`.

```python
class OrderStore:
```

Хранит реестр заказов и предоставляет версионные частичные операции.

Основные операции: __init__, connect, path, target, record; остальные описаны у методов.

## OrderStore.__init__

[orders.py:37](../../../orders.py#L37) · `function`.

```python
def __init__(self, root, data_dir, labels, *, database_only=True):
```

Сохраняет зависимости и начальные параметры экземпляра.

Состояние и зависимости сохраняются в полях self для последующих операций.

Непосредственные вызовы: `Path`, `hashlib.sha256(str(root).encode()).hexdigest`, `hashlib.sha256`, `str(root).encode`, `str`.

Прямые присваивания полям/свойствам: `self.root`, `self.database_only`, `self.database`, `self.labels`.

## OrderStore.connect

[orders.py:48](../../../orders.py#L48) · `function`.

```python
def connect(self):
```

Открывает соединение SQLite и управляет его временем жизни.

Работает с таблицами orders.

Непосредственные вызовы: `self.database.parent.mkdir`, `sqlite3.connect`, `db.execute`, `local_metadata.schema`, `reconciliations.schema`, `local_metadata.audit`, `db.commit`, `db.close`.

## OrderStore.path

[orders.py:88](../../../orders.py#L88) · `function`.

```python
def path(self, relative):
```

Проверяет относительный путь внутри допустимой области.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `ValueError`, `Path`, `Path(relative).is_absolute`, `any`, `part.startswith`, `is_service_folder`, `Path(*parts).as_posix`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
Path(*parts).as_posix()
```

## OrderStore.target

[orders.py:100](../../../orders.py#L100) · `function`.

```python
def target(self, relative):
```

Находит допустимую существующую цель файловой операции.

При недопустимом состоянии возбуждает ValueError, FileNotFoundError.

Непосредственные вызовы: `self.path`, `guard_database`, `any`, `(self.root / Path(*Path(relative).parts[:i + 1])).is_symlink`, `Path`, `range`, `len`, `ValueError`, `target.is_dir`, `FileNotFoundError`.

Явные исключения: `ValueError`, `FileNotFoundError`.

Выражения возврата (ветки читаются в исходнике):

```python
target
```

## OrderStore.record

[orders.py:112](../../../orders.py#L112) · `function`.

```python
def record(self, row, db):
```

Собирает API-карточку заказа из SQL-строки, блоков и вычисляемых признаков.

Разбирает JSON; вызывающий код должен учитывать ошибки или неизвестный формат.

Непосредственные вызовы: `dict`, `bool`, `client_name`, `result.update`, `order_location`, `work_orders.supplier_name`, `work_orders.supplier_color`, `json.loads`, `work_orders.status_order`, `work_orders.read_status`, `work_orders.archive_time`, `document.read_todos`, `document.read_purchases`, `document.read_favorite`, `document.read_flag`, `document.read_blue_plus`, `document.read_dollar`, `order_links.read`, `order_links.read_primary`, `order_links.primary_items`, `order_links.scope`, `order_deadlines.read`, `calendar_layout.read_compact`, `order_calendar.read`, `order_calendar.read_inactive`, `order_calendar.read_completed`, `order_calendar.read_trip`, `order_calendar.read_watch_todos`, `order_calendar.read_colors`, `work_orders.direct_order`, `result.pop`.

Выражения возврата (ветки читаются в исходнике):

```python
None
result
```

## OrderStore.get

[orders.py:156](../../../orders.py#L156) · `function`.

```python
def get(self, relative, *, include_unregistered=False):
```

Читает сохранённый заказ по пути без импорта его файлов.

Работает с таблицами orders.

Непосредственные вызовы: `is_service_folder`, `in_reconciliations`, `self.database.exists`, `self.connect`, `assert_unlocked`, `db.execute('SELECT * FROM orders WHERE path=?', (relative,)).fetchone`, `db.execute`, `self.record`.

Выражения возврата (ветки читаются в исходнике):

```python
None
self.record(row, db) if row and (include_unregistered or row['registered']) else None
```

## OrderStore.list

[orders.py:166](../../../orders.py#L166) · `function`.

```python
def list(self, *, include_unregistered=False):
```

Читает реестр заказов с учётом выбора снятых регистраций.

Работает с таблицами orders.

Непосредственные вызовы: `self.database.exists`, `self.connect`, `self.record`, `db.execute('SELECT * FROM orders ORDER BY updated DESC, path').fetchall`, `db.execute`, `any`, `part.startswith`, `Path`, `in_reconciliations`, `is_service_folder`.

Выражения возврата (ветки читаются в исходнике):

```python
[]
[self.record(row, db) for row in db.execute('SELECT * FROM orders ORDER BY updated DESC, path').fetchall() if not any((part.startswith('.') for part in Path(row['path']).parts)) and (not in_reconciliations(row['path'], legacy=True)) and (not is_service_folder(row['path'])) and (include_unregistered or row['registered'])]
```

## OrderStore.pending_unregistrations

[orders.py:177](../../../orders.py#L177) · `function`.

```python
def pending_unregistrations(self):
```

Возвращает сохранённые записи со снятой регистрацией.

Формирует возвращаемое значение из проверенного локального состояния.

Непосредственные вызовы: `self.list`.

Выражения возврата (ветки читаются в исходнике):

```python
[{'path': record['path'], 'sync_error': record['sync_error']} for record in self.list(include_unregistered=True) if not record['registered'] and record['sync_pending']]
```

## OrderStore.discard_service_orders

[orders.py:183](../../../orders.py#L183) · `function`.

```python
def discard_service_orders(self):
```

Убирает прежние тестовые регистрации служебных папок в файловом режиме.

Работает с таблицами orders.

Непосредственные вызовы: `self.database.exists`, `self.connect`, `db.execute`, `is_service_folder`, `db.executemany`, `len`.

Выражения возврата (ветки читаются в исходнике):

```python
0
len(paths)
```

## OrderStore.add

[orders.py:194](../../../orders.py#L194) · `function`.

```python
def add(self, relative, initial):
```

Добавляет регистрацию заказа с проверкой существующей записи и UUID.

Работает с таблицами orders.

Непосредственные вызовы: `self.path`, `self.target`, `self.require_order_folder`, `document.split_statuses`, `initial.get`, `isinstance`, `ValueError`, `self.connect`, `assert_unlocked`, `db.execute`, `str`, `uuid.uuid4`, `Path`, `time.time`, `json.dumps`, `order_calendar.normalize_weekly_blocks`, `calendar_layout.mark_contract`, `order_links.mark_status_contract`, `self.get`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
self.get(relative)
```

## OrderStore.require_order_folder

[orders.py:223](../../../orders.py#L223) · `function`.

```python
def require_order_folder(self, relative):
```

Проверяет, что путь соответствует допустимой папке заказа.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `folder_role`, `ValueError`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
role
```

## OrderStore.save

[orders.py:231](../../../orders.py#L231) · `function`.

```python
def save(self, payload):
```

Сохраняет проверенные поля карточки заказа по UUID и ожидаемой revision.

Работает с таблицами orders, sqlite_master, mobile_tasks.

Непосредственные вызовы: `self.path`, `payload.get`, `isinstance`, `ValueError`, `len`, `title.strip`, `any`, `money`, `type`, `self.connect`, `db.execute`, `assert_unlocked`, `db.execute('SELECT extra_blocks FROM orders WHERE path=? AND revision=? AND registered=1', (relative, revision)).fetchone`, `OrderConflict`, `json.loads`, `work_orders.status_order`, `work_orders.write_status`, `write_assignments`, `document.write_todos`, `db.execute("SELECT 1 FROM sqlite_master WHERE name='mobile_tasks'").fetchone`, `db.execute('SELECT id FROM orders WHERE path=?', (relative,)).fetchone`, `db.execute('SELECT items FROM mobile_tasks WHERE order_id=?', (row['id'],)).fetchone`, `reconcile_tasks`, `document.read_todos`, `json.dumps`, `time.time`, `order_links.mark_status_contract`, `self.get`.

Явные исключения: `ValueError`, `OrderConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
self.get(relative)
```

## OrderStore.save_status

[orders.py:281](../../../orders.py#L281) · `function`.

```python
def save_status(self, payload):
```

Меняет только производственный статус по версии, показанной в списке.

Работает с таблицами orders.

Непосредственные вызовы: `self.path`, `payload.get`, `isinstance`, `ValueError`, `type`, `self.connect`, `db.execute`, `assert_unlocked`, `time.time`, `OrderConflict`, `order_links.mark_status_contract`, `self.get`.

Явные исключения: `ValueError`, `OrderConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
self.get(relative)
```

## OrderStore.save_deadline_week

[orders.py:302](../../../orders.py#L302) · `function`.

```python
def save_deadline_week(self, payload):
```

Меняет одну неделю срока без изменения даты сортировки заказа.

Формирует возвращаемое значение из проверенного локального состояния.

Непосредственные вызовы: `self._save_extra_block`.

Выражения возврата (ветки читаются в исходнике):

```python
self._save_extra_block(payload, lambda blocks: order_deadlines.write(blocks, payload.get('week'), payload.get('selected')), update_time=False)
```

## OrderStore.save_deadline_comment

[orders.py:308](../../../orders.py#L308) · `function`.

```python
def save_deadline_comment(self, payload):
```

Меняет текст общего недельного события заказа.

Формирует возвращаемое значение из проверенного локального состояния.

Непосредственные вызовы: `self._save_extra_block`.

Выражения возврата (ветки читаются в исходнике):

```python
self._save_extra_block(payload, lambda blocks: order_deadlines.write_comment(blocks, payload.get('week'), payload.get('comment')), update_time=False)
```

## OrderStore.save_calendar_compact

[orders.py:313](../../../orders.py#L313) · `function`.

```python
def save_calendar_compact(self, payload):
```

Меняет только отметку мелкого заказа с проверкой UUID и версии.

Формирует возвращаемое значение из проверенного локального состояния.

Непосредственные вызовы: `self._save_extra_block`.

Выражения возврата (ветки читаются в исходнике):

```python
self._save_extra_block(payload, lambda blocks: calendar_layout.write_compact(blocks, payload.get('calendar_compact')), update_time=False)
```

## OrderStore.save_flag

[orders.py:318](../../../orders.py#L318) · `function`.

```python
def save_flag(self, payload):
```

Меняет одну независимую отметку заказа без замены остальных полей.

Возвращает `self._save_extra_block(payload, lambda blocks: document.write_flag(blocks, payload.get('is_flagged')), update_time=False)`.

Непосредственные вызовы: `self._save_extra_block`.

Выражения возврата (ветки читаются в исходнике):

```python
self._save_extra_block(payload, lambda blocks: document.write_flag(blocks, payload.get('is_flagged')), update_time=False)
```

## OrderStore.save_blue_plus

[orders.py:323](../../../orders.py#L323) · `function`.

```python
def save_blue_plus(self, payload):
```

Меняет одну независимую отметку заказа без замены остальных полей.

Возвращает `self._save_extra_block(payload, lambda blocks: document.write_blue_plus(blocks, payload.get('is_blue_plus')), update_time=False)`.

Непосредственные вызовы: `self._save_extra_block`.

Выражения возврата (ветки читаются в исходнике):

```python
self._save_extra_block(payload, lambda blocks: document.write_blue_plus(blocks, payload.get('is_blue_plus')), update_time=False)
```

## OrderStore.save_dollar

[orders.py:328](../../../orders.py#L328) · `function`.

```python
def save_dollar(self, payload):
```

Меняет одну независимую отметку заказа без замены остальных полей.

Возвращает `self._save_extra_block(payload, lambda blocks: document.write_dollar(blocks, payload.get('is_dollar')), update_time=False)`.

Непосредственные вызовы: `self._save_extra_block`.

Выражения возврата (ветки читаются в исходнике):

```python
self._save_extra_block(payload, lambda blocks: document.write_dollar(blocks, payload.get('is_dollar')), update_time=False)
```

## OrderStore.save_supplier_status

[orders.py:333](../../../orders.py#L333) · `function`.

```python
def save_supplier_status(self, payload):
```

Меняет самостоятельный статус заказа поставщика.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `work_orders.status_order`, `self.path`, `payload.get`, `ValueError`, `self._save_extra_block`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
self._save_extra_block(payload, lambda blocks: work_orders.write_status(blocks, payload.get('supplier_status')), update_time=False)
```

## OrderStore.save_purchase_done

[orders.py:340](../../../orders.py#L340) · `function`.

```python
def save_purchase_done(self, payload, supplier):
```

Меняет выполнение исходной закупки с проверкой строки и версии.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `self.path`, `payload.get`, `client_path`, `ValueError`, `self._save_extra_block`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
self._save_extra_block(payload, lambda blocks: document.write_purchase_done(blocks, payload.get('index'), payload.get('text'), supplier, payload.get('done')), update_time=False)
```

## OrderStore.save_purchase_text

[orders.py:349](../../../orders.py#L349) · `function`.

```python
def save_purchase_text(self, payload, supplier):
```

Меняет текст исходной закупки с проверкой строки и версии.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `self.path`, `payload.get`, `client_path`, `ValueError`, `self._save_extra_block`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
self._save_extra_block(payload, lambda blocks: document.write_purchase_text(blocks, payload.get('index'), payload.get('text'), supplier, payload.get('new_text')), update_time=False)
```

## OrderStore.save_calendar_event

[orders.py:358](../../../orders.py#L358) · `function`.

```python
def save_calendar_event(self, payload):
```

Сохраняет текст выбранного дневного или недельного события заказа.

Формирует возвращаемое значение из проверенного локального состояния.

Непосредственные вызовы: `self._save_extra_block`.

Выражения возврата (ветки читаются в исходнике):

```python
self._save_extra_block(payload, lambda blocks: order_calendar.write(blocks, payload.get('date'), payload.get('text'), payload.get('period', 'day')), update_time=False)
```

## OrderStore.remove_calendar_event

[orders.py:363](../../../orders.py#L363) · `function`.

```python
def remove_calendar_event(self, payload):
```

Удаляет выбранное событие и связанные с ним отметки.

Формирует возвращаемое значение из проверенного локального состояния.

Непосредственные вызовы: `self._save_extra_block`.

Выражения возврата (ветки читаются в исходнике):

```python
self._save_extra_block(payload, lambda blocks: order_calendar.remove(blocks, payload.get('date'), payload.get('period', 'day')), update_time=False)
```

## OrderStore.restore_calendar_event

[orders.py:368](../../../orders.py#L368) · `function`.

```python
def restore_calendar_event(self, payload):
```

Восстанавливает удалённое событие вместе с его прежними отметками.

Формирует возвращаемое значение из проверенного локального состояния.

Непосредственные вызовы: `self._save_extra_block`.

Выражения возврата (ветки читаются в исходнике):

```python
self._save_extra_block(payload, lambda blocks: order_calendar.restore(blocks, payload.get('date'), payload.get('text'), payload.get('is_inactive'), payload.get('period', 'day'), payload.get('color'), payload.get('is_completed', False), payload.get('is_trip', False), payload.get('is_watch_todos', None if order_calendar.WATCH_TODOS_BLOCK in blocks else False)), update_time=False)
```

## OrderStore.save_calendar_color

[orders.py:373](../../../orders.py#L373) · `function`.

```python
def save_calendar_color(self, payload):
```

Меняет цвет выбранного события заказа с проверкой версии.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `work_orders.supplier_name`, `self.path`, `payload.get`, `ValueError`, `self._save_extra_block`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
self._save_extra_block(payload, lambda blocks: order_calendar.set_color(blocks, payload.get('date'), payload.get('color'), payload.get('period', 'day')), update_time=False)
```

## OrderStore.save_calendar_inactive

[orders.py:380](../../../orders.py#L380) · `function`.

```python
def save_calendar_inactive(self, payload):
```

Меняет только неактуальность выбранного события заказа.

Формирует возвращаемое значение из проверенного локального состояния.

Непосредственные вызовы: `self._save_extra_block`.

Выражения возврата (ветки читаются в исходнике):

```python
self._save_extra_block(payload, lambda blocks: order_calendar.set_inactive(blocks, payload.get('date'), payload.get('is_inactive'), payload.get('period', 'day')), update_time=False)
```

## OrderStore.save_calendar_completed

[orders.py:385](../../../orders.py#L385) · `function`.

```python
def save_calendar_completed(self, payload):
```

Меняет только выполнение выбранного события заказа.

Формирует возвращаемое значение из проверенного локального состояния.

Непосредственные вызовы: `self._save_extra_block`.

Выражения возврата (ветки читаются в исходнике):

```python
self._save_extra_block(payload, lambda blocks: order_calendar.set_completed(blocks, payload.get('date'), payload.get('is_completed'), payload.get('period', 'day')), update_time=False)
```

## OrderStore.save_calendar_trip

[orders.py:390](../../../orders.py#L390) · `function`.

```python
def save_calendar_trip(self, payload):
```

Меняет только отметку выезда выбранного события заказа.

Формирует возвращаемое значение из проверенного локального состояния.

Непосредственные вызовы: `self._save_extra_block`.

Выражения возврата (ветки читаются в исходнике):

```python
self._save_extra_block(payload, lambda blocks: order_calendar.set_trip(blocks, payload.get('date'), payload.get('is_trip'), payload.get('period', 'day')), update_time=False)
```

## OrderStore.save_calendar_watch_todos

[orders.py:395](../../../orders.py#L395) · `function`.

```python
def save_calendar_watch_todos(self, payload):
```

Меняет только отметку показа задач выбранного события заказа.

Формирует возвращаемое значение из проверенного локального состояния.

Непосредственные вызовы: `self._save_extra_block`.

Выражения возврата (ветки читаются в исходнике):

```python
self._save_extra_block(payload, lambda blocks: order_calendar.set_watch_todos(blocks, payload.get('date'), payload.get('is_watch_todos'), payload.get('period', 'day')), update_time=False)
```

## OrderStore.move_calendar_event

[orders.py:400](../../../orders.py#L400) · `function`.

```python
def move_calendar_event(self, payload):
```

Переносит событие заказа вместе с его независимыми отметками.

Формирует возвращаемое значение из проверенного локального состояния.

Непосредственные вызовы: `self._save_extra_block`.

Выражения возврата (ветки читаются в исходнике):

```python
self._save_extra_block(payload, lambda blocks: order_calendar.move(blocks, payload.get('date'), payload.get('days'), payload.get('period', 'day')), update_time=False)
```

## OrderStore._save_extra_block

[orders.py:405](../../../orders.py#L405) · `function`.

```python
def _save_extra_block(self, payload, write, *, update_time=True):
```

Применяет частичную правку блока заказа внутри версионной транзакции.

Работает с таблицами orders, metadata_settings.

Непосредственные вызовы: `self.path`, `payload.get`, `isinstance`, `ValueError`, `type`, `self.connect`, `db.execute`, `assert_unlocked`, `db.execute('SELECT extra_blocks FROM orders WHERE path=? AND id=? AND revision=? AND registered=1', (relative, identity, revision)).fetchone`, `OrderConflict`, `write`, `json.loads`, `calendar_layout.mark_contract`, `order_calendar.mark_relevance_contract`, `order_calendar.mark_completion_contract`, `order_calendar.mark_trip_contract`, `order_calendar.mark_watch_todos_contract`, `json.dumps`, `time.time`, `self.get`.

Явные исключения: `ValueError`, `OrderConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
self.get(relative)
```

## OrderStore.save_favorite

[orders.py:442](../../../orders.py#L442) · `function`.

```python
def save_favorite(self, payload):
```

Меняет только избранное без чтения документов и замены полей карточки.

Работает с таблицами orders.

Непосредственные вызовы: `self.path`, `payload.get`, `type`, `ValueError`, `self.connect`, `db.execute`, `assert_unlocked`, `db.execute('SELECT extra_blocks FROM orders WHERE path=? AND revision=? AND registered=1', (relative, revision)).fetchone`, `OrderConflict`, `document.write_favorite`, `json.loads`, `json.dumps`, `time.time`, `self.get`.

Явные исключения: `ValueError`, `OrderConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
self.get(relative)
```

## OrderStore.work_links

[orders.py:463](../../../orders.py#L463) · `function`.

```python
def work_links(self, relative):
```

Читает сохранённую подборку заказов поставщиков текущего заказа.

Работает с таблицами orders.

Непосредственные вызовы: `self.path`, `work_orders.direct_order`, `ValueError`, `self.connect`, `assert_unlocked`, `db.execute('SELECT * FROM orders WHERE path=? AND registered=1', (relative,)).fetchone`, `db.execute`, `FileNotFoundError`, `work_orders.read_links`, `json.loads`, `dict`, `work_orders.summary`, `rows.values`, `work_orders.supplier_order`, `work_orders.archived`, `candidates.sort`.

Явные исключения: `ValueError`, `FileNotFoundError`.

Выражения возврата (ветки читаются в исходнике):

```python
{'path': relative, 'revision': parent['revision'], 'linked_ids': identities, 'items': items, 'candidates': candidates}
```

## OrderStore.save_work_links

[orders.py:485](../../../orders.py#L485) · `function`.

```python
def save_work_links(self, payload):
```

Сохраняет UUID подборки заказов поставщиков с проверкой версии.

Работает с таблицами orders.

Непосредственные вызовы: `self.path`, `payload.get`, `work_orders.checked_ids`, `work_orders.direct_order`, `ValueError`, `type`, `self.connect`, `db.execute`, `assert_unlocked`, `db.execute('SELECT extra_blocks FROM orders WHERE path=? AND revision=? AND registered=1', (relative, revision)).fetchone`, `OrderConflict`, `json.loads`, `work_orders.read_links`, `work_orders.write_links`, `db.execute('SELECT path,registered,extra_blocks FROM orders WHERE id=?', (identity,)).fetchone`, `work_orders.supplier_order`, `work_orders.archived`, `json.dumps`, `time.time`, `self.get`.

Явные исключения: `ValueError`, `OrderConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
self.get(relative)
```

## OrderStore.remove

[orders.py:517](../../../orders.py#L517) · `function`.

```python
def remove(self, payload):
```

Снимает регистрацию заказа, сохраняя карточку и пользовательскую папку.

Работает с таблицами orders, folder_notes.

Непосредственные вызовы: `payload.get`, `ValueError`, `self.path`, `type`, `self.connect`, `assert_unlocked`, `db.execute`, `time.time`, `OrderConflict`, `folder_notes.schema`, `self.record`, `db.execute('SELECT * FROM orders WHERE path=?', (relative,)).fetchone`, `body.pop`, `str`, `uuid.uuid4`, `json.dumps`, `self.get`.

Явные исключения: `ValueError`, `OrderConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
self.get(relative, include_unregistered=True)
```

## OrderStore.atomic_write

[orders.py:542](../../../orders.py#L542) · `function`.

```python
def atomic_write(self, target, body):
```

Записывает временный файл и атомарно заменяет предусмотренную цель.

Передаёт работу `document.atomic_write`.

Непосредственные вызовы: `document.atomic_write`.

## OrderStore.sync

[orders.py:547](../../../orders.py#L547) · `function`.

```python
def sync(self):
```

Подтверждает версии SQLite либо обслуживает прежнюю файловую выгрузку.

Работает с таблицами orders.

Непосредственные вызовы: `self.connect`, `db.execute`, `SYNC_LOCK.acquire`, `self.list`, `self.target`, `document.load`, `record['extra_blocks'].update`, `existing.get('extra_blocks', {}).items`, `existing.get`, `document.archive_current`, `self.atomic_write`, `document.render`, `document.archive_legacy`, `document.icloud_access.sync_error`, `json.dumps`, `SYNC_LOCK.release`.

## OrderStore.import_folder

[orders.py:586](../../../orders.py#L586) · `function`.

```python
def import_folder(self, relative, fallback=None):
```

Первоначально импортирует карточку папки, сохраняя уже существующие данные.

Возвращает `self._import_folder(relative, fallback)`.

Непосредственные вызовы: `self._import_folder`.

Выражения возврата (ветки читаются в исходнике):

```python
self._import_folder(relative, fallback)
```

## OrderStore._import_folder

[orders.py:594](../../../orders.py#L594) · `function`.

```python
def _import_folder(self, relative, fallback=None):
```

Первоначально импортирует карточку папки, сохраняя уже существующие данные.

Работает с таблицами folder_notes, orders.

Непосредственные вызовы: `self.target`, `self.require_order_folder`, `self.get`, `self.connect`, `db.execute`, `assert_unlocked`, `folder_notes.schema`, `db.execute('SELECT document FROM folder_notes WHERE path=?', (relative,)).fetchone`, `json.loads`, `order_calendar.normalize_weekly_blocks`, `body.get`, `calendar_layout.mark_contract`, `json.dumps`, `time.time`, `FolderNotes(self).connect`, `FolderNotes`, `MetadataStore(self).card`, `MetadataStore`, `document.load`, `initial.get`, `self.restore`, `self.add`.

Выражения возврата (ветки читаются в исходнике):

```python
self.get(relative)
```

## OrderStore.restore

[orders.py:641](../../../orders.py#L641) · `function`.

```python
def restore(self, relative, snapshot):
```

Импортирует только отсутствующие записи; существующая база имеет приоритет.

Работает с таблицами sqlite_master, order_duplicate_archive, orders.

Непосредственные вызовы: `self.path`, `self.target`, `self.require_order_folder`, `isinstance`, `snapshot.get`, `ValueError`, `document.split_statuses`, `title.strip`, `len`, `any`, `type`, `str`, `uuid.UUID`, `document.validate_blocks`, `self.connect`, `assert_unlocked`, `db.execute("SELECT 1 FROM sqlite_master WHERE name='order_duplicate_archive'").fetchone`, `db.execute`, `db.execute("SELECT 1 FROM order_duplicate_archive WHERE id=? AND state='archived'", (identity,)).fetchone`, `OrderConflict`, `db.execute('SELECT path FROM orders WHERE id=? AND path<>?', (identity, relative)).fetchone`, `uuid.uuid4`, `time.time`, `json.dumps`, `order_calendar.normalize_weekly_blocks`, `calendar_layout.mark_contract`, `order_links.mark_status_contract`.

Явные исключения: `ValueError`, `OrderConflict`.

## OrderStore.discover

[orders.py:697](../../../orders.py#L697) · `function`.

```python
def discover(self, read_status, progress):
```

Выполняет явный поиск зарегистрированных карточек без чтения вложений.

При недопустимом состоянии возбуждает FileNotFoundError.

Непосредственные вызовы: `self.root.is_dir`, `FileNotFoundError`, `os.walk`, `Path`, `name.startswith`, `is_service_folder`, `(folder / name).relative_to(self.root).as_posix`, `(folder / name).relative_to`, `(folder / name).is_symlink`, `folder.relative_to(self.root).as_posix`, `folder.relative_to`, `folder_role`, `self.get`, `any`, `document.load(folder, self.labels).get`, `document.load`, `self.import_folder`, `progress['errors'].append`, `str`.

Явные исключения: `FileNotFoundError`.
