# invoices.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [invoices.py](../../../invoices.py).

Invoice drafts, immutable issued PDFs and a durable folder-copy outbox.

Импорты Python, включая локальные: `base64`, `binascii`, `contextlib`, `datetime`, `decimal`, `event_folder_undo`, `file_comments`, `file_trash`, `folder_layout`, `hashlib`, `invoice_documents`, `json`, `local_metadata`, `native_renderers`, `order_calendar`, `order_folders`, `orders`, `os`, `pathlib`, `re`, `subprocess`, `tempfile`, `threading`, `time`, `unicodedata`, `uuid`, `zoneinfo`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-InvoiceConflict"></a>

## InvoiceConflict

[invoices.py](../../../invoices.py) · `class`.

```python
class InvoiceConflict(ValueError):
```

Обозначает конфликт изменения в этом модуле.

Вызывающий обработчик использует тип исключения для отказа без подмены данных.

<a id="symbol-InvoiceStore"></a>

## InvoiceStore

[invoices.py](../../../invoices.py) · `class`.

```python
class InvoiceStore:
```

Хранит черновики, выпуски, внешние PDF и планы платежей одной рабочей базы.

Основные операции: __init__, connect, owner, record, current; остальные описаны у методов.

<a id="symbol-InvoiceStore.__init__"></a>

## InvoiceStore.__init__

[invoices.py](../../../invoices.py) · `function`.

```python
def __init__(self, store, app_dir):
```

Сохраняет зависимости и начальные параметры экземпляра.

Состояние и зависимости сохраняются в полях self для последующих операций.

Непосредственные вызовы: `Path`.

<a id="symbol-InvoiceStore._save_plan_calendar_flag"></a>

## InvoiceStore._save_plan_calendar_flag

[invoices.py](../../../invoices.py) · `function`.

```python
def _save_plan_calendar_flag(self, payload, field, key):
```

Обновляет одну строгую отметку плана с проверкой версии.

Работает с таблицами invoice_history, invoices.

Непосредственные вызовы: `payload.get`, `type`, `ValueError`, `self.connect`, `db.execute`, `self.current`, `self.owner`, `InvoiceConflict`, `json.loads`, `known_plan`, `data.get`, `time.time`, `json.dumps`, `local_metadata.schema`, `order_calendar.mark_flag_contract`, `self.record`.

Явные исключения: `ValueError`, `InvoiceConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
self.record(self.current(db, row['path'], row['id']))
```

<a id="symbol-InvoiceStore.calendar_plans"></a>

## InvoiceStore.calendar_plans

[invoices.py](../../../invoices.py) · `function`.

```python
def calendar_plans(self, visible_orders):
```

Собирает планы платежей для календаря из SQLite.

Работает с таблицами invoices.

Непосредственные вызовы: `order.get`, `self.connect`, `db.execute`, `owners.get`, `json.loads`, `data.get`, `known_plan`, `result.append`.

Выражения возврата (ветки читаются в исходнике):

```python
result
```

<a id="symbol-InvoiceStore.connect"></a>

## InvoiceStore.connect

[invoices.py](../../../invoices.py) · `function`.

```python
def connect(self):
```

Открывает соединение SQLite и управляет его временем жизни.

Работает с таблицами invoices, invoice_sequences, invoice_settings, invoice_history.

Непосредственные вызовы: `self.store.connect`, `db.execute`, `invoice_documents.schema`.

<a id="symbol-InvoiceStore.create"></a>

## InvoiceStore.create

[invoices.py](../../../invoices.py) · `function`.

```python
def create(self, payload):
```

Создаёт новый черновик счёта, при необходимости на основе существующего.

Работает с таблицами invoices, invoice_sequences, invoice_settings.

Непосредственные вызовы: `payload.get`, `str`, `uuid.UUID`, `ValueError`, `self.connect`, `db.execute`, `self.owner`, `db.execute('SELECT * FROM invoices WHERE id=?', (identity,)).fetchone`, `InvoiceConflict`, `json.loads(existing['data']).get`, `json.loads`, `self.record`, `today`, `db.execute('SELECT value FROM invoice_sequences WHERE year=?', (year,)).fetchone`, `db.execute('SELECT 1 FROM invoices WHERE year=? AND number=?', (year, number)).fetchone`, `db.execute("SELECT value FROM invoice_settings WHERE key='seller'").fetchone`, `data.update`, `today().isoformat`, `(today() + timedelta(days=7)).isoformat`, `timedelta`, `orders.client_name`, `dict`, `self.current`, `validate`, `time.time`, `json.dumps`.

Явные исключения: `ValueError`, `InvoiceConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
self.record(existing)
self.record(self.current(db, path, identity))
```

<a id="symbol-InvoiceStore.current"></a>

## InvoiceStore.current

[invoices.py](../../../invoices.py) · `function`.

```python
def current(self, db, path, identity, *, trashed=False):
```

Проверяет текущую запись и ожидаемую версию перед изменением.

Работает с таблицами invoices.

Непосредственные вызовы: `self.store.path`, `assert_unlocked`, `isinstance`, `ValueError`, `db.execute('SELECT * FROM invoices WHERE id=? AND path=?', (identity, path)).fetchone`, `db.execute`, `InvoiceConflict`, `self.owner`, `json.loads(row['data']).get`, `json.loads`.

Явные исключения: `ValueError`, `InvoiceConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
row
```

<a id="symbol-InvoiceStore.get"></a>

## InvoiceStore.get

[invoices.py](../../../invoices.py) · `function`.

```python
def get(self, path, identity):
```

Читает точный счёт по пути владельца и UUID.

Возвращает `invoice_documents.with_copy_status(db, self.record(self.current(db, path, identity)))`.

Непосредственные вызовы: `self.connect`, `invoice_documents.with_copy_status`, `self.record`, `self.current`.

Выражения возврата (ветки читаются в исходнике):

```python
invoice_documents.with_copy_status(db, self.record(self.current(db, path, identity)))
```

<a id="symbol-InvoiceStore.issue"></a>

## InvoiceStore.issue

[invoices.py](../../../invoices.py) · `function`.

```python
def issue(self, payload):
```

Выпускает неизменяемый документ из проверенного черновика.

Работает с таблицами invoices.

Непосредственные вызовы: `self.connect`, `self.current`, `payload.get`, `self.record`, `ValueError`, `type`, `InvoiceConflict`, `validate`, `json.loads`, `render`, `re.sub`, `db.execute`, `self.owner`, `time.time`.

Явные исключения: `ValueError`, `InvoiceConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
self.record(row)
self.record(self.current(db, path, identity))
```

<a id="symbol-InvoiceStore.list"></a>

## InvoiceStore.list

[invoices.py](../../../invoices.py) · `function`.

```python
def list(self, path, *, trashed=False):
```

Читает счета и планы выбранного заказа из SQLite.

Работает с таблицами invoices.

Непосредственные вызовы: `self.connect`, `self.owner`, `db.execute`, `invoice_documents.with_copy_status`, `self.record`.

Выражения возврата (ветки читаются в исходнике):

```python
[invoice_documents.with_copy_status(db, self.record(row)) for row in rows]
```

<a id="symbol-InvoiceStore.move_calendar_plan"></a>

## InvoiceStore.move_calendar_plan

[invoices.py](../../../invoices.py) · `function`.

```python
def move_calendar_plan(self, payload):
```

Переносит дату плана и сохраняет остальные данные платежа.

Работает с таблицами invoice_history, invoices.

Непосредственные вызовы: `self.connect`, `db.execute`, `self.current`, `payload.get`, `self.owner`, `ValueError`, `type`, `InvoiceConflict`, `json.loads`, `known_plan`, `data.get`, `(date.fromisoformat(data['date']) + timedelta(days=days)).isoformat`, `date.fromisoformat`, `timedelta`, `time.time`, `json.dumps`, `self.record`.

Явные исключения: `ValueError`, `InvoiceConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
self.record(self.current(db, row['path'], row['id']))
```

<a id="symbol-InvoiceStore.owner"></a>

## InvoiceStore.owner

[invoices.py](../../../invoices.py) · `function`.

```python
def owner(self, db, path, *, active=False):
```

Проверяет владельца и доступность счёта для операции.

Работает с таблицами orders.

Непосредственные вызовы: `self.store.path`, `assert_unlocked`, `db.execute('SELECT * FROM orders WHERE path=?', (path,)).fetchone`, `db.execute`, `ValueError`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
row
```

<a id="symbol-InvoiceStore.pdf"></a>

## InvoiceStore.pdf

[invoices.py](../../../invoices.py) · `function`.

```python
def pdf(self, path, identity):
```

Возвращает сохранённый выпущенный PDF после проверки владельца.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `self.connect`, `self.current`, `ValueError`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
(row['pdf'], row['filename'])
```

<a id="symbol-InvoiceStore.plan"></a>

## InvoiceStore.plan

[invoices.py](../../../invoices.py) · `function`.

```python
def plan(self, payload):
```

Проверяет и сохраняет дневной или недельный план платежа.

Работает с таблицами invoices, invoice_history, metadata_settings.

Непосредственные вызовы: `payload.get`, `self.store.path`, `plan_date`, `plan_period`, `isinstance`, `ValueError`, `len`, `any`, `ord`, `int`, `decimal`, `Decimal`, `str`, `uuid.UUID`, `self.connect`, `db.execute`, `self.owner`, `db.execute('SELECT * FROM invoices WHERE id=?', (identity,)).fetchone`, `json.loads`, `data.get`, `InvoiceConflict`, `known_plan`, `self.record`, `type`, `time.time`, `data.pop`, `json.dumps`, `self.current`, `data.update`, `self.source_label`, `local_metadata.schema`.

Явные исключения: `ValueError`, `InvoiceConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
self.record(row)
self.record(self.current(db, path, identity))
```

<a id="symbol-InvoiceStore.plan_source"></a>

## InvoiceStore.plan_source

[invoices.py](../../../invoices.py) · `function`.

```python
def plan_source(self, path, identity):
```

Проверяет выбранный источник плана платежа.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `self.connect`, `self.current`, `self.owner`, `ValueError`, `json.loads`, `data.get`, `self.source_label`, `pdf_total`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
result
```

<a id="symbol-InvoiceStore.preview"></a>

## InvoiceStore.preview

[invoices.py](../../../invoices.py) · `function`.

```python
def preview(self, path, identity):
```

Готовит проверяемое предложение операции без её выполнения.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `self.get`, `ValueError`, `self.pdf`, `validate`, `render`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
self.pdf(path, identity)[0]
render({**data, 'preview': True}, self.app_dir, self.store.database.parent)
```

<a id="symbol-InvoiceStore.publish_copy"></a>

## InvoiceStore.publish_copy

[invoices.py](../../../invoices.py) · `function`.

```python
def publish_copy(self, row):
```

Публикует сохранённую копию документа в папку без подмены оригиналов.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `self.store.target`, `folder.is_symlink`, `ValueError`, `folder.exists`, `Plan`, `Path`, `layout_scope`, `plan.mkdir`, `folder.relative_to(self.store.root).as_posix`, `folder.relative_to`, `plan.create_session`, `apply`, `os.path.lexists`, `target.is_symlink`, `target.is_file`, `hashlib.sha256(target.read_bytes()).digest`, `hashlib.sha256`, `target.read_bytes`, `hashlib.sha256(row['pdf']).digest`, `tempfile.NamedTemporaryFile`, `stream.write`, `stream.flush`, `os.fsync`, `stream.fileno`, `rename_exclusive`, `temporary.unlink`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
target
```

<a id="symbol-InvoiceStore.record"></a>

## InvoiceStore.record

[invoices.py](../../../invoices.py) · `function`.

```python
def record(row):
```

Собирает представление счёта с суммой, планами и состоянием документов.

Разбирает JSON; вызывающий код должен учитывать ошибки или неизвестный формат.

Непосредственные вызовы: `row.keys`, `json.loads`, `result['data'].get`, `isinstance`, `known_plan`, `str`, `Path`, `invoice_documents.read`, `invoice_documents.copy_name`.

Выражения возврата (ветки читаются в исходнике):

```python
result
```

<a id="symbol-InvoiceStore.remove"></a>

## InvoiceStore.remove

[invoices.py](../../../invoices.py) · `function`.

```python
def remove(self, payload, *, calendar_only=False):
```

Помещает счёт или допустимый план в корзину с сохранением истории.

Работает с таблицами invoice_history, invoices.

Непосредственные вызовы: `payload.get`, `ValueError`, `self.connect`, `db.execute`, `self.current`, `self.require_calendar_payment`, `self.owner`, `json.loads`, `data.get`, `self.record`, `type`, `InvoiceConflict`, `local_metadata.schema`, `uuid.uuid4`, `time.time`, `json.dumps`.

Явные исключения: `ValueError`, `InvoiceConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
self.record(row)
self.record(self.current(db, row['path'], row['id'], trashed=True))
```

<a id="symbol-InvoiceStore.require_calendar_payment"></a>

## InvoiceStore.require_calendar_payment

[invoices.py](../../../invoices.py) · `function`.

```python
def require_calendar_payment(row):
```

Проверяет пригодность записи для операций с планом календаря.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `json.loads`, `data.get`, `known_plan`, `ValueError`.

Явные исключения: `ValueError`.

<a id="symbol-InvoiceStore.restore"></a>

## InvoiceStore.restore

[invoices.py](../../../invoices.py) · `function`.

```python
def restore(self, payload, *, calendar_only=False):
```

Возвращает сохранённый счёт или план из корзины по ожидаемой версии.

Работает с таблицами invoice_history, invoices.

Непосредственные вызовы: `self.connect`, `self.current`, `payload.get`, `self.require_calendar_payment`, `self.owner`, `json.loads(row['data']).get`, `json.loads`, `self.record`, `type`, `InvoiceConflict`, `file_trash.session_path`, `(session / '.plan.json').exists`, `file_trash.restore`, `db.execute`, `data.pop`, `time.time`, `json.dumps`, `self.get`.

Явные исключения: `InvoiceConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
self.record(row)
self.get(payload['path'], payload['id'])
```

<a id="symbol-InvoiceStore.save"></a>

## InvoiceStore.save

[invoices.py](../../../invoices.py) · `function`.

```python
def save(self, payload):
```

Сохраняет проверенный черновик по UUID и ожидаемой версии.

Работает с таблицами invoices, invoice_history, invoice_settings.

Непосредственные вызовы: `validate`, `payload.get`, `self.connect`, `db.execute`, `self.current`, `self.owner`, `type`, `InvoiceConflict`, `json.loads`, `int`, `db.execute('SELECT 1 FROM invoices WHERE year=? AND number=? AND id<>?', (year, data['number'], row['id'])).fetchone`, `time.time`, `json.dumps`, `self.record`.

Явные исключения: `InvoiceConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
self.record(self.current(db, row['path'], row['id']))
```

<a id="symbol-InvoiceStore.save_comment"></a>

## InvoiceStore.save_comment

[invoices.py](../../../invoices.py) · `function`.

```python
def save_comment(self, payload):
```

Сохраняет текст комментария с проверкой ожидаемой версии.

Работает с таблицами invoice_history, invoices.

Непосредственные вызовы: `external_comment`, `payload.get`, `self.connect`, `db.execute`, `self.current`, `self.owner`, `type`, `InvoiceConflict`, `json.loads`, `data.get`, `self.record`, `time.time`, `json.dumps`.

Явные исключения: `InvoiceConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
self.record(row)
self.record(self.current(db, row['path'], row['id']))
```

<a id="symbol-InvoiceStore.save_list_status"></a>

## InvoiceStore.save_list_status

[invoices.py](../../../invoices.py) · `function`.

```python
def save_list_status(self, payload):
```

Сохраняет выбранный статус строки счёта без изменения содержимого PDF.

Работает с таблицами invoice_history, invoices.

Непосредственные вызовы: `payload.get`, `isinstance`, `ValueError`, `self.connect`, `db.execute`, `self.current`, `self.owner`, `type`, `InvoiceConflict`, `json.loads`, `self.record`, `time.time`, `json.dumps`.

Явные исключения: `ValueError`, `InvoiceConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
self.record(row)
self.record(self.current(db, row['path'], row['id']))
```

<a id="symbol-InvoiceStore.save_plan_calendar_carryover"></a>

## InvoiceStore.save_plan_calendar_carryover

[invoices.py](../../../invoices.py) · `function`.

```python
def save_plan_calendar_carryover(self, payload):
```

Сохраняет ручное размещение плана в переносе слева.

Возвращает `self._save_plan_calendar_flag(payload, 'is_carryover', '_calendar_carryover')`.

Непосредственные вызовы: `self._save_plan_calendar_flag`.

Выражения возврата (ветки читаются в исходнике):

```python
self._save_plan_calendar_flag(payload, 'is_carryover', '_calendar_carryover')
```

<a id="symbol-InvoiceStore.save_plan_calendar_completed"></a>

## InvoiceStore.save_plan_calendar_completed

[invoices.py](../../../invoices.py) · `function`.

```python
def save_plan_calendar_completed(self, payload):
```

Сохраняет независимое выполнение плана платежа.

Возвращает `self._save_plan_calendar_flag(payload, 'is_completed', '_calendar_completed')`.

Непосредственные вызовы: `self._save_plan_calendar_flag`.

Выражения возврата (ветки читаются в исходнике):

```python
self._save_plan_calendar_flag(payload, 'is_completed', '_calendar_completed')
```

<a id="symbol-InvoiceStore.save_plan_calendar_inactive"></a>

## InvoiceStore.save_plan_calendar_inactive

[invoices.py](../../../invoices.py) · `function`.

```python
def save_plan_calendar_inactive(self, payload):
```

Сохраняет независимую неактуальность плана платежа.

Возвращает `self._save_plan_calendar_flag(payload, 'is_inactive', '_calendar_inactive')`.

Непосредственные вызовы: `self._save_plan_calendar_flag`.

Выражения возврата (ветки читаются в исходнике):

```python
self._save_plan_calendar_flag(payload, 'is_inactive', '_calendar_inactive')
```

<a id="symbol-InvoiceStore.save_plan_calendar_notified"></a>

## InvoiceStore.save_plan_calendar_notified

[invoices.py](../../../invoices.py) · `function`.

```python
def save_plan_calendar_notified(self, payload):
```

Сохраняет независимую отметку «Сообщил» запланированной суммы.

Требует доход/расход, строгий boolean и текущую UUID/revision; остальные данные сохраняет.

Непосредственные вызовы: `self._save_plan_calendar_flag`.

Выражения возврата (ветки читаются в исходнике):

```python
self._save_plan_calendar_flag(payload, 'is_notified', '_calendar_notified')
```

<a id="symbol-InvoiceStore.save_plan_calendar_trip"></a>

## InvoiceStore.save_plan_calendar_trip

[invoices.py](../../../invoices.py) · `function`.

```python
def save_plan_calendar_trip(self, payload):
```

Сохраняет независимую отметку выезда плана платежа.

Возвращает `self._save_plan_calendar_flag(payload, 'is_trip', '_calendar_trip')`.

Непосредственные вызовы: `self._save_plan_calendar_flag`.

Выражения возврата (ветки читаются в исходнике):

```python
self._save_plan_calendar_flag(payload, 'is_trip', '_calendar_trip')
```

<a id="symbol-InvoiceStore.save_plan_calendar_watch_todos"></a>

## InvoiceStore.save_plan_calendar_watch_todos

[invoices.py](../../../invoices.py) · `function`.

```python
def save_plan_calendar_watch_todos(self, payload):
```

Сохраняет отметку задач у плана, связанного с заказом.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `payload.get`, `ValueError`, `self._save_plan_calendar_flag`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
self._save_plan_calendar_flag(payload, 'is_watch_todos', '_calendar_watch_todos')
```

<a id="symbol-InvoiceStore.source_label"></a>

## InvoiceStore.source_label

[invoices.py](../../../invoices.py) · `function`.

```python
def source_label(row):
```

Формирует подпись источника плана из сохранённых данных счёта.

Разбирает JSON; вызывающий код должен учитывать ошибки или неизвестный формат.

Непосредственные вызовы: `json.loads`, `data.get`.

Выражения возврата (ветки читаются в исходнике):

```python
data.get('original_name', 'Внешний счёт') if row['state'] == 'external' else ('Счёт-договор' if data.get('kind') == 'contract' else 'Счёт') + ' № ' + row['number']
```

<a id="symbol-InvoiceStore.sync"></a>

## InvoiceStore.sync

[invoices.py](../../../invoices.py) · `function`.

```python
def sync(self):
```

Публикует ожидающие документы счетов и согласует состояние их копий.

Работает с таблицами invoices.

Непосредственные вызовы: `SYNC_LOCK.acquire`, `self.sync_trash`, `invoice_documents.sync`, `self.connect`, `db.execute`, `db.execute('SELECT * FROM invoices WHERE id=?', (identity,)).fetchone`, `any`, `part.startswith`, `Path`, `json.loads(row['data']).get`, `json.loads`, `assert_unlocked`, `self.publish_copy`, `str`, `int`, `SYNC_LOCK.release`.

<a id="symbol-InvoiceStore.sync_trash"></a>

## InvoiceStore.sync_trash

[invoices.py](../../../invoices.py) · `function`.

```python
def sync_trash(self):
```

Согласует ожидающее перемещение копий документов в корзину.

Работает с таблицами invoices.

Непосредственные вызовы: `self.connect`, `db.execute`, `db.execute('SELECT * FROM invoices WHERE id=?', (identity,)).fetchone`, `any`, `part.startswith`, `Path`, `json.loads(row['data']).get`, `json.loads`, `assert_unlocked`, `file_trash.session_path`, `(session / '.plan.json').exists`, `file_trash.resume`, `(Path(row['path']) / '# bills' / row['filename']).as_posix`, `file_trash.checked`, `str`, `os.path.lexists`, `file_trash.preview`, `self.publish_copy`, `file_trash.remove`.

<a id="symbol-InvoiceStore.upload"></a>

## InvoiceStore.upload

[invoices.py](../../../invoices.py) · `function`.

```python
def upload(self, payload):
```

Принимает проверенный документ и сохраняет его содержимое.

Работает с таблицами invoices.

Непосредственные вызовы: `self.store.path`, `payload.get`, `str`, `uuid.UUID`, `ValueError`, `isinstance`, `name.startswith`, `any`, `ord`, `unicodedata.normalize`, `len`, `os.fsencode`, `Path(name).suffix.casefold`, `Path`, `external_comment`, `base64.b64decode`, `pdf.startswith`, `self.connect`, `db.execute`, `self.owner`, `db.execute('SELECT * FROM invoices WHERE id=?', (identity,)).fetchone`, `json.loads(existing['data']).get`, `json.loads`, `InvoiceConflict`, `self.record`, `today().isoformat`, `today`, `time.time`, `json.dumps`, `self.current`.

Явные исключения: `ValueError`, `InvoiceConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
self.record(existing)
self.record(self.current(db, path, identity))
```

<a id="symbol-decimal"></a>

## decimal

[invoices.py](../../../invoices.py) · `function`.

```python
def decimal(value, label, places, maximum):
```

Проверяет денежное значение и переводит его в точное внутреннее представление.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `len`, `ValueError`, `Decimal`, `value.replace(' ', '').replace('\xa0', '').replace`, `value.replace(' ', '').replace`, `value.replace`, `number.is_finite`, `number.quantize`, `Decimal(1).scaleb`, `str`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
number
```

<a id="symbol-external_comment"></a>

## external_comment

[invoices.py](../../../invoices.py) · `function`.

```python
def external_comment(value):
```

Проверяет комментарий внешнего PDF перед сохранением.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `len`, `any`, `ord`, `ValueError`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
value
```

<a id="symbol-known_plan"></a>

## known_plan

[invoices.py](../../../invoices.py) · `function`.

```python
def known_plan(data):
```

Проверяет строгость внутреннего формата плана платежа.

Возвращает `False`.

Непосредственные вызовы: `type`, `data.get`, `plan_date`, `plan_period`, `isinstance`.

Выражения возврата (ветки читаются в исходнике):

```python
False
isinstance(operation, str) and (operation == 'invoice' or (operation in {'incoming', 'outgoing'} and type(data.get('amount')) is int and (0 < data['amount'] <= 99999999999)))
```

<a id="symbol-pdf_total"></a>

## pdf_total

[invoices.py](../../../invoices.py) · `function`.

```python
def pdf_total(body, app_dir, data_dir):
```

Извлекает текст PDF помощником и ищет однозначную итоговую сумму.

Запускает внешний процесс; параметры и ограничения заданы в теле функции.

Непосредственные вызовы: `Path`, `cache.mkdir`, `hashlib.sha256(body).hexdigest`, `hashlib.sha256`, `cached.is_file`, `total_from_text`, `cached.read_text`, `tempfile.TemporaryDirectory`, `source.write_bytes`, `native_renderers.build`, `subprocess.run`, `str`, `result.stdout[:2000000].decode`, `temporary.write_text`, `temporary.replace`.

Выражения возврата (ветки читаются в исходнике):

```python
total_from_text(cached.read_text(encoding='utf-8'))
total_from_text(text)
```

<a id="symbol-plan_date"></a>

## plan_date

[invoices.py](../../../invoices.py) · `function`.

```python
def plan_date(value):
```

Проверяет дату плана платежа и её каноническую запись.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `date.fromisoformat(value).isoformat`, `date.fromisoformat`, `ValueError`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
value
```

<a id="symbol-plan_period"></a>

## plan_period

[invoices.py](../../../invoices.py) · `function`.

```python
def plan_period(value, scheduled):
```

Проверяет дневной или недельный период плана платежа.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `ValueError`, `date.fromisoformat(scheduled).weekday`, `date.fromisoformat`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
value
```

<a id="symbol-render"></a>

## render

[invoices.py](../../../invoices.py) · `function`.

```python
def render(data, app_dir, data_dir):
```

Передаёт проверенную модель счёта Swift-помощнику для получения PDF.

Запускает внешний процесс; параметры и ограничения заданы в теле функции.

Непосредственные вызовы: `Path`, `cache.mkdir`, `tempfile.TemporaryDirectory`, `source.write_text`, `json.dumps`, `subprocess.run`, `str`, `renderer`, `ValueError`, `error.stderr.decode('utf-8', errors='replace').strip`, `error.stderr.decode`, `output.read_bytes`, `body.startswith`, `len`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
body
```

<a id="symbol-renderer"></a>

## renderer

[invoices.py](../../../invoices.py) · `function`.

```python
def renderer(app_dir, data_dir):
```

Получает собранный Swift-помощник для текущего исходника.

Возвращает `native_renderers.build(Path(app_dir) / 'invoice_pdf.swift', data_dir, 'invoice-pdf', 90)`.

Непосредственные вызовы: `native_renderers.build`, `Path`.

Выражения возврата (ветки читаются в исходнике):

```python
native_renderers.build(Path(app_dir) / 'invoice_pdf.swift', data_dir, 'invoice-pdf', 90)
```

<a id="symbol-today"></a>

## today

[invoices.py](../../../invoices.py) · `function`.

```python
def today():
```

Возвращает текущую календарную дату в принятом часовом поясе.

Возвращает `datetime.now(ZoneInfo('Europe/Moscow')).date()`.

Непосредственные вызовы: `datetime.now(ZoneInfo('Europe/Moscow')).date`, `datetime.now`, `ZoneInfo`.

Выражения возврата (ветки читаются в исходнике):

```python
datetime.now(ZoneInfo('Europe/Moscow')).date()
```

<a id="symbol-total_from_text"></a>

## total_from_text

[invoices.py](../../../invoices.py) · `function`.

```python
def total_from_text(text):
```

Извлекает только однозначную подписанную итоговую сумму PDF.

Возвращает `candidates.pop() if len(candidates) == 1 else None`; либо `None`.

Непосредственные вызовы: `text.replace('\xa0', ' ').replace`, `text.replace`, `set`, `re.finditer`, `text[match.end():].split`, `match.end`, `tail.strip`, `text[match.end():].lstrip('\n').split`, `text[match.end():].lstrip`, `list`, `len`, `re.search`, `tail[:values[0].start()].rstrip().endswith`, `tail[:values[0].start()].rstrip`, `values[0].start`, `values[0].group(1).replace`, `values[0].group`, `value.replace('.', '').replace`, `value.replace`, `int`, `Decimal`, `candidates.add`, `candidates.pop`.

Выражения возврата (ветки читаются в исходнике):

```python
candidates.pop() if len(candidates) == 1 else None
None
```

<a id="symbol-validate"></a>

## validate

[invoices.py](../../../invoices.py) · `function`.

```python
def validate(value, *, issuing=False):
```

Проверяет реквизиты, позиции, точность сумм и условия выпуска счёта.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `ValueError`, `FIELDS.items`, `value.get`, `len`, `any`, `ord`, `text.strip`, `re.fullmatch`, `date.fromisoformat(result[field]).isoformat`, `date.fromisoformat`, `seller.get`, `text.isascii`, `text.isdigit`, `item.get`, `decimal`, `Decimal`, `name.strip`, `int`, `(qty * price * 100).quantize`, `result['items'].append`, `unit.strip`, `str`, `all`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
result
```
