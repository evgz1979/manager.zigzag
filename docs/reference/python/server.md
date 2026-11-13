# server.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [server.py](../../../server.py).

Импорты Python, включая локальные: `calendar_delivery`, `calendar_events`, `calendar_todos`, `client_activity`, `configparser`, `contextlib`, `datetime`, `event_folder_undo`, `event_folders`, `event_relevance`, `event_trash`, `fcntl`, `file_comments`, `file_trash`, `file_uploads`, `folder_notes`, `folder_rename`, `folder_structure`, `functools`, `hashlib`, `hidden_orders`, `http.server`, `icloud_access`, `image_reports`, `inbox_folder`, `invoice_discovery`, `invoice_documents`, `invoice_preferences`, `invoices`, `json`, `local_metadata`, `mimetypes`, `mobile_sync`, `native_renderers`, `object_activity`, `object_move`, `object_orders`, `object_years`, `order_creation`, `order_deadlines`, `order_document`, `order_folders`, `order_links`, `order_todos`, `orders`, `os`, `pathlib`, `plistlib`, `re`, `reconciliations`, `recovery_backup`, `remote_access`, `shutil`, `signal`, `sketches`, `socket`, `spreadsheet_preview`, `sqlite3`, `subprocess`, `supplier_purchases`, `sys`, `telegram_calendar`, `telegram_inbox`, `tempfile`, `threading`, `thumbnail_cache`, `unicodedata`, `urllib.parse`, `work_order_list`, `work_orders`, `zoneinfo`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-ManagerHandler"></a>

## ManagerHandler

[server.py](../../../server.py) · `class`.

```python
class ManagerHandler(BaseHTTPRequestHandler):
```

Обслуживает LAN-запросы менеджера и маршрутизирует действия приложения.

Основные операции: log_message, send_json, send_invoice_pdf, send_invoice_document, send_file; остальные описаны у методов.

<a id="symbol-ManagerHandler.do_GET"></a>

## ManagerHandler.do_GET

[server.py](../../../server.py) · `function`.

```python
def do_GET(self):
```

Обслуживает GET через проверки и маршрутизацию текущего обработчика.

Передаёт работу `self.handle_get`.

Непосредственные вызовы: `self.handle_get`.

<a id="symbol-ManagerHandler.do_HEAD"></a>

## ManagerHandler.do_HEAD

[server.py](../../../server.py) · `function`.

```python
def do_HEAD(self):
```

Обслуживает HEAD с теми же ограничениями доступа, что GET.

Передаёт работу `self.handle_get`.

Непосредственные вызовы: `self.handle_get`.

<a id="symbol-ManagerHandler.do_POST"></a>

## ManagerHandler.do_POST

[server.py](../../../server.py) · `function`.

```python
def do_POST(self):
```

Проверяет и маршрутизирует запрос изменения данных текущего обработчика.

Запускает внешний процесс; параметры и ограничения заданы в теле функции.

Непосредственные вызовы: `HANDOFF_STOP.is_set`, `(DATA_DIR.resolve().parent / '.handoff-parked.json').exists`, `DATA_DIR.resolve`, `self.send_json`, `urllib.parse.urlsplit`, `remote_access.serve_password_change`, `self.receive_telegram_settings`, `self.receive_calendar_telegram`, `self.receive_upload`, `urllib.parse.urlparse`, `self.headers.get`, `self.headers.get_content_type`, `ValueError`, `int`, `json.loads`, `self.rfile.read(length).decode`, `self.rfile.read`, `isinstance`, `invoice_preferences.resource`, `invoice_store`, `route.rsplit`, `reconciliations.Reconciliations`, `order_store`, `route.endswith`, `service.save`, `service.assign`, `payload.get`, `in_reconciliations`, `route.startswith`, `len`, `Path`, `telegram_inbox.complete`, `telegram_inbox.set_deleted`, `thumbnail_store().items`, `thumbnail_store`, `thumbnail_store().cover`, `invoice_store().create`, `invoice_store().plan`, `invoice_store().move_calendar_plan`, `invoice_store().remove`, `invoice_store().restore`, `invoice_store().upload`, `schedule_order_sync`, `invoice_discovery.attach`, `invoice_documents.upload`, `invoice_documents.set_deleted`, `invoice_store().save_comment`, `invoice_store().save_list_status`, `invoice_store().save`, `invoice_store().issue`, `guard_database`, `order_folders.create`, `METADATA_REFRESH.set`, `schedule_todo_refresh`, `order_folders.create_object`, `object_years.group`, `object_move.start`, `event_folders.create`, `folder_note_store`, `folder_rename.rename`, `event_folders.rename`, `folder_note_store().save`, `folder_note_store().save_relevance`, `event_relevance.info`, `folder_note_store().save_sketch_relevance`, `sketches.group_info`, `sketch_target`, `sketches.open_corel`, `editable_status_folder`, `relative_path`, `store.path`, `store.require_order_folder`, `order_creation.retry_one`, `store.get`, `folder_status`, `directory_children`, `store.import_folder`, `MobileBridge`, `bridge.configure`, `schedule_mobile_sync`, `bridge.status`, `order_store().save`, `supplier_purchases.SupplierPurchases(order_store()).save`, `supplier_purchases.SupplierPurchases`, `inactive_paths`, `supplier_purchases.SupplierPurchases(order_store()).edit`, `order_store().save_favorite`, `OrderLinks(order_store()).save`, `OrderLinks`, `order_store().save_flag`, `order_store().save_blue_plus`, `order_store().save_dollar`, `order_store().save_status`, `order_store().save_supplier_status`, `order_store().save_deadline_week`, `order_store().save_calendar_compact`, `order_store().save_deadline_comment`, `calendar_events.CalendarEvents(order_store()).save`, `calendar_events.CalendarEvents`, `calendar_events.CalendarEvents(order_store()).set_deleted`, `operation`, `calendar_events.CalendarEvents(order_store()).color`, `order_store().save_calendar_color`, `calendar_events.CalendarEvents(order_store()).move`, `order_store().save_calendar_inactive`, `order_store().save_calendar_completed`, `calendar_events.CalendarEvents(order_store()).set_completed`, `invoice_store().save_plan_calendar_completed`, `order_store().save_calendar_trip`, `order_store().save_calendar_watch_todos`, `invoice_store().save_plan_calendar_watch_todos`, `calendar_events.CalendarEvents(order_store()).set_trip`, `invoice_store().save_plan_calendar_trip`, `calendar_events.CalendarEvents(order_store()).set_inactive`, `invoice_store().save_plan_calendar_inactive`, `invoice_store().save_plan_calendar_carryover`, `invoice_store().save_plan_calendar_notified`, `order_store().save_calendar_event`, `order_store().move_calendar_event`, `work_orders.save_supplier_favorite`, `order_store().save_work_links`, `object_activity_store`, `client_activity_store`, `activity.accept_file`, `activity.save`, `order_store().remove`, `folder_note_store().get`, `discover_orders`, `client_activity_store().refresh`, `object_activity_store().refresh`, `order_store().path`, `create_print_task`, `save_print_task`, `read_print_task`, `PrintConflict`, `datetime.now(ZoneInfo('Europe/Moscow')).strftime`, `datetime.now`, `ZoneInfo`, `hashlib.sha256((task['path'] + task['revision']).encode()).hexdigest`, `hashlib.sha256`, `(task['path'] + task['revision']).encode`, `metadata_store().publish`, `metadata_store`, `compose_print_text(task['link'], task['description'], task['title']).encode`, `compose_print_text`, `comment_file`, `file_comments.binding`, `FileCommentConflict`, `metadata_store().save_comment`, `file_comments.save`, `create_image_report`, `file_trash.preview`, `event_trash.preview`, `event_trash.remove`, `event_trash.restore`, `file_trash.remove`, `event_trash.list_sessions`, `file_trash.list_sessions`, `errors.append`, `file_trash.restore`, `save_status`, `save_note`, `safe_path`, `target.exists`, `FileNotFoundError`, `subprocess.Popen`, `str`.

Явные исключения: `ValueError`, `PrintConflict`, `FileCommentConflict`, `FileNotFoundError`.

<a id="symbol-ManagerHandler.handle_get"></a>

## ManagerHandler.handle_get

[server.py](../../../server.py) · `function`.

```python
def handle_get(self, head=False):
```

Выбирает обработчик GET/HEAD по разобранному маршруту.

При недопустимом состоянии возбуждает FileNotFoundError, ValueError.

Непосредственные вызовы: `urllib.parse.urlparse`, `urllib.parse.parse_qs`, `query.get`, `getattr`, `self.send_json`, `socket.gethostname`, `str`, `remote_access.serve_settings`, `listed_orders`, `hidden_orders.listed`, `order_store`, `client_activity_store().inactive_paths`, `client_activity_store`, `object_activity_store().inactive_paths`, `object_activity_store`, `telegram_calendar.status`, `telegram_inbox.snapshot`, `inbox_folder.snapshot`, `listed_object_orders`, `listed_work_orders`, `supplier_purchases.SupplierPurchases(order_store()).read`, `supplier_purchases.SupplierPurchases`, `inactive_paths`, `supplier_purchases.SupplierPurchases(order_store()).catalog`, `work_orders.read_supplier_favorites`, `metadata_store().status`, `metadata_store`, `thumbnail_store().status`, `thumbnail_store`, `thumbnail_store().cover`, `thumbnail_store().image`, `self.send_response`, `self.send_header`, `len`, `self.end_headers`, `self.wfile.write`, `reconciliations.Reconciliations`, `service.with_links`, `invoice_store().list`, `invoice_store`, `invoice_store().catalog`, `invoice_preferences.resource`, `parsed.path.rsplit`, `reconciliations.Reconciliations(order_store()).catalog`, `reconciliations.Reconciliations(order_store()).get`, `invoice_discovery.candidates`, `invoice_store().get`, `reconciliations.Reconciliations(order_store()).with_links`, `invoice_documents.content`, `self.send_invoice_document`, `invoice_store().plan_source`, `invoice_pdf_target`, `pdf_info`, `self.send_file`, `pdf_page`, `int`, `invoice_store().preview`, `invoice_store().pdf`, `self.send_invoice_pdf`, `activity.get`, `FileNotFoundError`, `MobileBridge(order_store()).status`, `MobileBridge`, `calendar_events.CalendarEvents(order_store()).get`, `calendar_events.CalendarEvents`, `folder_note_store().get`, `folder_note_store`, `folder_note_store().event_relevances`, `folder_note_store().sketch_relevances`, `sketch_target`, `sketches.preview`, `freza_preview_target`, `target.suffix.lower`, `image_preview`, `event_folders.preview`, `folder_rename.preview`, `object_years.preview`, `object_move.preview`, `object_move.status`, `order_store().get`, `supplier_purchases.section_path`, `OrderTodos(order_store()).in_order`, `OrderTodos`, `OrderLinks(order_store()).read`, `OrderLinks`, `order_store().work_links`, `read_tree`, `read_folder`, `read_print_task`, `comment_file`, `file_comments.binding`, `read_file_comment`, `safe_path`, `target.is_file`, `spreadsheet_preview.read_bytes`, `ValueError`, `target.open`, `stream.read`, `body[:128 * 1024].decode`, `preview_kind`, `parsed.path.startswith`, `urllib.parse.unquote(parsed.path).lstrip`, `urllib.parse.unquote`, `(STATIC_DIR / relative_static).resolve`.

Явные исключения: `FileNotFoundError`, `ValueError`.

<a id="symbol-ManagerHandler.log_message"></a>

## ManagerHandler.log_message

[server.py](../../../server.py) · `function`.

```python
def log_message(self, format, *args):
```

Записывает предусмотренное диагностическое сообщение обработчика.

Выполняет локальные проверки или меняет только переданные структуры данных.

<a id="symbol-ManagerHandler.receive_calendar_telegram"></a>

## ManagerHandler.receive_calendar_telegram

[server.py](../../../server.py) · `function`.

```python
def receive_calendar_telegram(self):
```

Проверяет общий снимок календаря перед подтверждённой отправкой боту.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `self.headers.get`, `self.headers.get_content_type`, `urllib.parse.urlsplit`, `self.send_json`, `self.headers.get_all`, `len`, `re.fullmatch`, `ValueError`, `int`, `urllib.parse.parse_qs`, `query.get`, `telegram_calendar.SEND_LOCK.acquire`, `self.connection.settimeout`, `self.rfile.read`, `telegram_calendar.validate_image`, `order_store().database.exists`, `order_store`, `calendar_todos.digest`, `listed_orders`, `telegram_calendar.send`, `str`, `telegram_calendar.SEND_LOCK.release`.

Явные исключения: `ValueError`.

Прямые присваивания полям/свойствам: `self.close_connection`.

<a id="symbol-ManagerHandler.receive_telegram_settings"></a>

## ManagerHandler.receive_telegram_settings

[server.py](../../../server.py) · `function`.

```python
def receive_telegram_settings(self):
```

Обрабатывает проверку и сохранение настроек Telegram.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `self.headers.get`, `self.headers.get_content_type`, `urllib.parse.urlsplit`, `self.send_json`, `self.headers.get_all`, `len`, `re.fullmatch`, `ValueError`, `int`, `telegram_calendar.SEND_LOCK.acquire`, `self.connection.settimeout`, `json.loads`, `self.rfile.read`, `isinstance`, `telegram_calendar.configure`, `str`, `telegram_calendar.SEND_LOCK.release`.

Явные исключения: `ValueError`.

Прямые присваивания полям/свойствам: `self.close_connection`.

<a id="symbol-ManagerHandler.receive_upload"></a>

## ManagerHandler.receive_upload

[server.py](../../../server.py) · `function`.

```python
def receive_upload(self):
```

Принимает загрузку файла с привязкой к открытой папке.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `self.headers.get`, `self.headers.get_content_type`, `self.send_json`, `urllib.parse.urlsplit`, `self.headers.get_all`, `len`, `re.fullmatch`, `ValueError`, `urllib.parse.parse_qs`, `any`, `query.get`, `self.connection.settimeout`, `file_uploads.receive`, `order_store`, `int`, `str`.

Явные исключения: `ValueError`.

Прямые присваивания полям/свойствам: `self.close_connection`.

<a id="symbol-ManagerHandler.send_file"></a>

## ManagerHandler.send_file

[server.py](../../../server.py) · `function`.

```python
def send_file(self, target, head=False, download=False, allow_range=False, private=False):
```

Передаёт проверенный файл или статический ресурс в HTTP-ответе.

При недопустимом состоянии возбуждает FileNotFoundError.

Непосредственные вызовы: `target.is_file`, `FileNotFoundError`, `target.stat`, `self.headers.get`, `re.fullmatch`, `any`, `match.groups`, `self.send_response`, `self.send_header`, `self.end_headers`, `int`, `min`, `max`, `mimetypes.guess_type`, `str`, `urllib.parse.quote`, `target.open`, `stream.seek`, `stream.read`, `self.wfile.write`, `len`.

Явные исключения: `FileNotFoundError`.

<a id="symbol-ManagerHandler.send_invoice_document"></a>

## ManagerHandler.send_invoice_document

[server.py](../../../server.py) · `function`.

```python
def send_invoice_document(self, body, name, mime, head=False, download=False):
```

Выдаёт байты вложения счёта с проверкой принадлежности.

Передаёт работу `self.send_response`, `self.send_header`, `urllib.parse.quote`.

Непосредственные вызовы: `self.send_response`, `self.send_header`, `str`, `len`, `urllib.parse.quote`, `self.end_headers`, `self.wfile.write`.

<a id="symbol-ManagerHandler.send_invoice_pdf"></a>

## ManagerHandler.send_invoice_pdf

[server.py](../../../server.py) · `function`.

```python
def send_invoice_pdf(self, body, name, head=False, download=False):
```

Выдаёт PDF счёта с проверкой владельца и режима запроса.

Передаёт работу `self.send_invoice_document`.

Непосредственные вызовы: `self.send_invoice_document`.

<a id="symbol-ManagerHandler.send_json"></a>

## ManagerHandler.send_json

[server.py](../../../server.py) · `function`.

```python
def send_json(self, payload, status=200, head=False):
```

Отправляет JSON с указанным HTTP-статусом и заголовками.

Передаёт работу `json.dumps(payload, ensure_ascii=False).encode`, `json.dumps`, `self.send_response`.

Непосредственные вызовы: `json.dumps(payload, ensure_ascii=False).encode`, `json.dumps`, `self.send_response`, `self.send_header`, `str`, `len`, `self.end_headers`, `self.wfile.write`.

<a id="symbol-PrintConflict"></a>

## PrintConflict

[server.py](../../../server.py) · `class`.

```python
class PrintConflict(ValueError):
```

Обозначает конфликт изменения в этом модуле.

Вызывающий обработчик использует тип исключения для отказа без подмены данных.

<a id="symbol-_read_print_task"></a>

## _read_print_task

[server.py](../../../server.py) · `function`.

```python
def _read_print_task(relative):
```

Читает задание печати из действующего хранилища или прежнего файла.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `ValueError`, `is_print_folder`, `str`, `Path`, `Path(relative).name.startswith`, `len`, `metadata_store().get`, `metadata_store`, `metadata_store().is_publication`, `print_target`, `metadata_store().archive`, `decode_print_document`, `split_print_text`, `metadata_store().put`, `metadata_store().imported`, `target.read_bytes`, `relative_path`, `hashlib.sha256(raw).hexdigest`, `hashlib.sha256`, `target.stat`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{**current, 'name': Path(relative).name, 'modified': current['updated'], 'storage': 'database'}
{**current, 'name': target.name, 'modified': current['updated'], 'storage': 'database'}
{'path': relative_path(target), 'name': target.name, 'title': title, 'link': link, 'description': description, 'revision': hashlib.sha256(raw).hexdigest(), 'modified': target.stat().st_mtime}
```

<a id="symbol-_thumbnail_store"></a>

## _thumbnail_store

[server.py](../../../server.py) · `function`.

```python
def _thumbnail_store(root, data_dir):
```

Получает экземпляр отдельного кеша миниатюр текущего корня.

Возвращает `thumbnail_cache.ThumbnailCache(root, data_dir)`.

Непосредственные вызовы: `thumbnail_cache.ThumbnailCache`, `lru_cache`.

Выражения возврата (ветки читаются в исходнике):

```python
thumbnail_cache.ThumbnailCache(root, data_dir)
```

<a id="symbol-client_activity_store"></a>

## client_activity_store

[server.py](../../../server.py) · `function`.

```python
def client_activity_store():
```

Создаёт адаптер индекса активности нужной роли папки.

Возвращает `ClientActivity(order_store(), STATUS_LOCK)`.

Непосредственные вызовы: `ClientActivity`, `order_store`.

Выражения возврата (ветки читаются в исходнике):

```python
ClientActivity(order_store(), STATUS_LOCK)
```

<a id="symbol-client_activity_worker"></a>

## client_activity_worker

[server.py](../../../server.py) · `function`.

```python
def client_activity_worker():
```

Обновляет индексы активности, сохраняя последние данные при ошибках.

Координирует фоновые потоки через локальные события или блокировки.

Непосредственные вызовы: `client_activity_store`, `object_activity_store`, `activity.refresh`, `print`, `threading.Event().wait`, `threading.Event`.

<a id="symbol-comment_file"></a>

## comment_file

[server.py](../../../server.py) · `function`.

```python
def comment_file(relative):
```

Проверяет точный файл для просмотра или редактирования комментария.

При недопустимом состоянии возбуждает ValueError, FileNotFoundError.

Непосредственные вызовы: `guard_database`, `order_store`, `safe_path`, `any`, `(DATA_ROOT / Path(*Path(relative).parts[:index + 1])).is_symlink`, `Path`, `range`, `len`, `ValueError`, `target.is_file`, `FileNotFoundError`.

Явные исключения: `ValueError`, `FileNotFoundError`.

Выражения возврата (ветки читаются в исходнике):

```python
target
```

<a id="symbol-compose_print_text"></a>

## compose_print_text

[server.py](../../../server.py) · `function`.

```python
def compose_print_text(link, description, title=''):
```

Собирает текст выпускаемого задания из проверенных полей.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `all`, `isinstance`, `ValueError`, `any`, `link.strip`, `urllib.parse.urlparse`, `parsed.scheme.lower`, `char.isspace`, `title.strip`, `len`, `text.encode`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
text
```

<a id="symbol-create_image_report"></a>

## create_image_report

[server.py](../../../server.py) · `function`.

```python
def create_image_report(relative, selected):
```

Проверяет выбранные изображения и запускает создание PDF-отчёта.

При недопустимом состоянии возбуждает FileNotFoundError, ValueError.

Непосредственные вызовы: `safe_path`, `folder.is_dir`, `FileNotFoundError`, `any`, `(DATA_ROOT / Path(*Path(relative).parts[:index + 1])).is_symlink`, `Path`, `range`, `len`, `ValueError`, `isinstance`, `dict.fromkeys`, `comment_file`, `file_group`, `items.append`, `str`, `read_file_comment`, `image_reports.create`, `relative_path`.

Явные исключения: `FileNotFoundError`, `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{'path': relative_path(target), 'name': target.name, 'imageCount': len(items), 'skippedCount': skipped, 'pages': pages}
```

<a id="symbol-create_print_task"></a>

## create_print_task

[server.py](../../../server.py) · `function`.

```python
def create_print_task(relative, link, description, title=''):
```

Создаёт новый черновик задания печати в выбранном разделе.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `print_target`, `compose_print_text`, `datetime.now(ZoneInfo('Europe/Moscow')).strftime`, `datetime.now`, `ZoneInfo`, `str`, `Path`, `metadata_store().get`, `metadata_store`, `(folder / filename).exists`, `metadata_store().put`, `title.strip`, `link.strip`, `read_print_task`, `next_print_name`, `encode_print_document`, `len`, `ValueError`, `os.open`, `os.fdopen`, `stream.write`, `target.unlink`, `relative_path`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
read_print_task(path)
read_print_task(relative_path(target))
```

<a id="symbol-decode_print_document"></a>

## decode_print_document

[server.py](../../../server.py) · `function`.

```python
def decode_print_document(target, raw):
```

Преобразует байты задания печати в текст или обратно в исходный формат.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `target.suffix.lower`, `plistlib.loads`, `isinstance`, `value.decode`, `text_from_rtf`, `ValueError`, `raw.startswith`, `raw.decode`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
(value.decode(encoding) if isinstance(value, bytes) else value, 'clipping')
(text_from_rtf(representations['public.rtf']), 'clipping')
(text_from_rtf(raw), 'rtf')
(text, encoding)
```

<a id="symbol-directory_children"></a>

## directory_children

[server.py](../../../server.py) · `function`.

```python
def directory_children(path):
```

Читает допустимые непосредственные подпапки для дерева навигации.

Возвращает `sorted((item for item in path.iterdir() if visible(item) and item.is_dir()), key=directory_sort_key)`.

Непосредственные вызовы: `sorted`, `path.iterdir`, `visible`, `item.is_dir`.

Выражения возврата (ветки читаются в исходнике):

```python
sorted((item for item in path.iterdir() if visible(item) and item.is_dir()), key=directory_sort_key)
```

<a id="symbol-directory_sort_key"></a>

## directory_sort_key

[server.py](../../../server.py) · `function`.

```python
def directory_sort_key(path):
```

Строит ключ стабильной сортировки файлов или папок интерфейса.

Возвращает `(not path.name.startswith('#'), sort_key(Path(name)))`.

Непосредственные вызовы: `path.name.startswith`, `path.name[1:].strip`, `sort_key`, `Path`.

Выражения возврата (ветки читаются в исходнике):

```python
(not path.name.startswith('#'), sort_key(Path(name)))
```

<a id="symbol-discover_orders"></a>

## discover_orders

[server.py](../../../server.py) · `function`.

```python
def discover_orders():
```

Запускает один явный фоновый поиск заказов и возвращает его состояние.

Координирует фоновые потоки через локальные события или блокировки.

Непосредственные вызовы: `dict`, `SCAN_STATE.update`, `threading.Thread(target=work, daemon=True).start`, `threading.Thread`.

Выражения возврата (ветки читаются в исходнике):

```python
dict(SCAN_STATE)
```

<a id="symbol-discover_orders.work"></a>

## discover_orders.work

[server.py](../../../server.py) · `function`.

```python
def work():
```

Выполняет фоновое обнаружение и завершает состояние задания даже при ошибке.

Передаёт работу `order_store().discover`, `order_store`, `SCAN_STATE['errors'].append`.

Непосредственные вызовы: `order_store().discover`, `order_store`, `SCAN_STATE['errors'].append`, `str`, `schedule_order_sync`, `schedule_todo_refresh`.

<a id="symbol-editable_status_folder"></a>

## editable_status_folder

[server.py](../../../server.py) · `function`.

```python
def editable_status_folder(relative):
```

Проверяет папку перед прежним прямым редактированием статуса.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `guard_database`, `order_store`, `safe_path`, `target.is_dir`, `ValueError`, `any`, `(DATA_ROOT / Path(*Path(relative).parts[:index + 1])).is_symlink`, `Path`, `range`, `len`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
target
```

<a id="symbol-encode_print_document"></a>

## encode_print_document

[server.py](../../../server.py) · `function`.

```python
def encode_print_document(target, text, encoding='utf-8', original=None):
```

Преобразует байты задания печати в текст или обратно в исходный формат.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `target.suffix.lower`, `plistlib.loads`, `text_to_rtf`, `plistlib.dumps`, `text_to_rtf(text).encode`, `text.encode`, `ValueError`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
plistlib.dumps(document, fmt=plistlib.FMT_BINARY)
text_to_rtf(text).encode('ascii')
text.encode(encoding)
```

<a id="symbol-file_group"></a>

## file_group

[server.py](../../../server.py) · `function`.

```python
def file_group(path):
```

Определяет группу файла по поддерживаемому расширению.

Возвращает `next((group for (group, extensions) in EXT_GROUPS.items() if path.suffix.lower() in extensions), 'other')`.

Непосредственные вызовы: `next`, `EXT_GROUPS.items`, `path.suffix.lower`.

Выражения возврата (ветки читаются в исходнике):

```python
next((group for (group, extensions) in EXT_GROUPS.items() if path.suffix.lower() in extensions), 'other')
```

<a id="symbol-folder_node"></a>

## folder_node

[server.py](../../../server.py) · `function`.

```python
def folder_node(path):
```

Формирует один узел дерева с ролью и сохранёнными признаками папки.

Возвращает `{'name': path.name, 'path': relative_path(path), 'hasChildren': has_children}`.

Непосредственные вызовы: `any`, `visible`, `item.is_dir`, `path.iterdir`, `relative_path`.

Выражения возврата (ветки читаются в исходнике):

```python
{'name': path.name, 'path': relative_path(path), 'hasChildren': has_children}
```

<a id="symbol-folder_note_store"></a>

## folder_note_store

[server.py](../../../server.py) · `function`.

```python
def folder_note_store():
```

Создаёт адаптер заметок папок с прежним подготовщиком импорта.

Возвращает `FolderNotes(order_store(), status_document)`.

Непосредственные вызовы: `FolderNotes`, `order_store`.

Выражения возврата (ветки читаются в исходнике):

```python
FolderNotes(order_store(), status_document)
```

<a id="symbol-folder_sort_key"></a>

## folder_sort_key

[server.py](../../../server.py) · `function`.

```python
def folder_sort_key(relative_folder):
```

Строит ключ стабильной сортировки файлов или папок интерфейса.

Возвращает `tuple((directory_sort_key(Path(part)) for part in Path(relative_folder).parts))`.

Непосредственные вызовы: `tuple`, `directory_sort_key`, `Path`.

Выражения возврата (ветки читаются в исходнике):

```python
tuple((directory_sort_key(Path(part)) for part in Path(relative_folder).parts))
```

<a id="symbol-folder_status"></a>

## folder_status

[server.py](../../../server.py) · `function`.

```python
def folder_status(path, directories):
```

Выбирает сохранённое состояние папки для текущего представления.

Возвращает `{**role, 'service': True, 'note': read_status_document(path).get('note', ''), 'statusSource': 'manual'}`.

Непосредственные вызовы: `relative_path`, `folder_role`, `reconciliations.Reconciliations(order_store()).open`, `reconciliations.Reconciliations`, `order_store`, `child.name.startswith`, `child.is_symlink`, `reconciliation_warnings.append`, `str`, `is_service_folder`, `parent_order`, `order_store().get`, `folder_note_store().read`, `folder_note_store`, `bool`, `body.get`, `order_document.read_purchases`, `read_status_document(path).get`, `read_status_document`, `normalized`, `' '.join`, `next`, `any`, `record.get`.

Выражения возврата (ветки читаются в исходнике):

```python
{**role, 'reconciliation': item, 'service': False, 'noteOnly': True, 'eventFolder': False, 'note': item['note'], 'todo_items': item['todo_items'], 'purchase_items': [], 'extra_blocks': {}, 'status': 'unspecified', 'financial_status': 'unspecified', 'statusSource': 'database'}
{**role, 'service': False, 'status': order['status'], 'financial_status': order['financial_status'], 'note': order['note'], 'todo_items': order['todo_items'], 'purchase_items': order['purchase_items'], 'extra_blocks': order['extra_blocks'], 'statusSource': 'database', 'order': order}
{**role, 'reconciliationWarnings': reconciliation_warnings, 'service': service, 'noteOnly': note_only, 'eventFolder': bool(owner), 'folderNote': record, 'draftCard': body, 'note': record['note'], 'todo_items': record['todo_items'], 'purchase_items': order_document.read_purchases(body.get('extra_blocks', {})), 'extra_blocks': record['extra_blocks'], 'status': body.get('status', 'new'), 'financial_status': body.get('financial_status', 'unspecified'), 'statusSource': 'database'}
{**role, 'service': True, 'note': read_status_document(path).get('note', ''), 'statusSource': 'manual'}
{**role, 'service': False, 'noteOnly': True, 'note': order['note'], 'statusSource': 'database', 'registrationPending': True, 'registrationError': order['sync_error']}
{**role, 'service': service, 'noteOnly': True, 'eventFolder': True, 'folderNote': record, 'note': record['note'], 'todo_items': record['todo_items'], 'extra_blocks': record['extra_blocks'], 'statusSource': 'database'}
{**role, 'service': False, 'noteOnly': not role['canRegisterOrder'] or bool(order) or record.get('registered') is False, 'status': record.get('status', guessed), 'note': record.get('note', ''), 'financial_status': record.get('financial_status', 'unspecified'), 'todo_items': record.get('todo_items', []), 'purchase_items': record.get('purchase_items', []), 'extra_blocks': record.get('extra_blocks', {}), 'statusSource': 'manual' if record.get('status') else 'auto'}
```

<a id="symbol-freza_preview_target"></a>

## freza_preview_target

[server.py](../../../server.py) · `function`.

```python
def freza_preview_target(relative):
```

Лениво выбирает обложку задания фрезеровки при явном запросе.

При недопустимом состоянии возбуждает ValueError, FileNotFoundError.

Непосредственные вызовы: `Path`, `in_freza`, `len`, `is_freza_task`, `Path(*parts[:3]).as_posix`, `ValueError`, `safe_path`, `comment_file`, `sketches.sketch_name`, `editable_status_folder`, `os.walk`, `sorted`, `visible`, `(current / name).is_file`, `next`, `preview_kind`, `relative_path`, `FileNotFoundError`.

Явные исключения: `ValueError`, `FileNotFoundError`.

Выражения возврата (ветки читаются в исходнике):

```python
target
comment_file(relative_path(image or cdr))
```

<a id="symbol-hash_folder_name"></a>

## hash_folder_name

[server.py](../../../server.py) · `function`.

```python
def hash_folder_name(name):
```

Строит нормализованное представление имени служебной папки.

Возвращает `normalized(name[1:].strip()) if name.startswith('#') else None`.

Непосредственные вызовы: `name.startswith`, `normalized`, `name[1:].strip`.

Выражения возврата (ветки читаются в исходнике):

```python
normalized(name[1:].strip()) if name.startswith('#') else None
```

<a id="symbol-image_preview"></a>

## image_preview

[server.py](../../../server.py) · `function`.

```python
def image_preview(target):
```

Готовит уменьшенное представление изображения без изменения оригинала.

Запускает внешний процесс; параметры и ограничения заданы в теле функции.

Непосредственные вызовы: `target.suffix.lower`, `target.stat`, `hashlib.sha256(f'{target}:{stat.st_mtime_ns}:{stat.st_size}'.encode()).hexdigest`, `hashlib.sha256`, `f'{target}:{stat.st_mtime_ns}:{stat.st_size}'.encode`, `int`, `len`, `preview.exists`, `cache.mkdir`, `subprocess.run`, `str`, `temporary.replace`, `temporary.unlink`, `ValueError`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
target
preview
```

<a id="symbol-inactive_paths"></a>

## inactive_paths

[server.py](../../../server.py) · `function`.

```python
def inactive_paths():
```

Читает множество неактивных путей из индекса базы.

Возвращает `client_activity_store().inactive_paths() | object_activity_store().inactive_paths()`.

Непосредственные вызовы: `client_activity_store().inactive_paths`, `client_activity_store`, `object_activity_store().inactive_paths`, `object_activity_store`.

Выражения возврата (ветки читаются в исходнике):

```python
client_activity_store().inactive_paths() | object_activity_store().inactive_paths()
```

<a id="symbol-invoice_pdf_target"></a>

## invoice_pdf_target

[server.py](../../../server.py) · `function`.

```python
def invoice_pdf_target(path, identity):
```

Проверяет источник PDF счёта для общего просмотрщика.

Возвращает `target`.

Непосредственные вызовы: `invoice_store().pdf`, `invoice_store`, `hashlib.sha256(body).hexdigest`, `hashlib.sha256`, `int`, `len`, `target.exists`, `cache.mkdir`, `tempfile.NamedTemporaryFile`, `Path`, `stream.write`, `temporary.replace`, `temporary.unlink`.

Выражения возврата (ветки читаются в исходнике):

```python
target
```

<a id="symbol-invoice_store"></a>

## invoice_store

[server.py](../../../server.py) · `function`.

```python
def invoice_store():
```

Создаёт адаптер счетов текущей базы и каталога приложения.

Возвращает `invoices.InvoiceStore(order_store(), APP_DIR)`.

Непосредственные вызовы: `invoices.InvoiceStore`, `order_store`.

Выражения возврата (ветки читаются в исходнике):

```python
invoices.InvoiceStore(order_store(), APP_DIR)
```

<a id="symbol-is_print_folder"></a>

## is_print_folder

[server.py](../../../server.py) · `function`.

```python
def is_print_folder(relative):
```

Проверяет, относится ли папка к редактируемым заданиям печати.

Возвращает `len(parts) >= 2 and hash_folder_name(parts[0]) == 'work' and (hash_folder_name(parts[1]) == 'print')`.

Непосредственные вызовы: `Path`, `len`, `hash_folder_name`.

Выражения возврата (ветки читаются в исходнике):

```python
len(parts) >= 2 and hash_folder_name(parts[0]) == 'work' and (hash_folder_name(parts[1]) == 'print')
```

<a id="symbol-listed_object_orders"></a>

## listed_object_orders

[server.py](../../../server.py) · `function`.

```python
def listed_object_orders(relative, show_inactive=False):
```

Собирает список заказов выбранного объекта по сохранённому каталогу.

Возвращает `object_orders.ObjectOrders(order_store()).read(relative, inactive=inactive_paths(), show_inactive=show_inactive)`.

Непосредственные вызовы: `object_orders.ObjectOrders(order_store()).read`, `object_orders.ObjectOrders`, `order_store`, `inactive_paths`.

Выражения возврата (ветки читаются в исходнике):

```python
object_orders.ObjectOrders(order_store()).read(relative, inactive=inactive_paths(), show_inactive=show_inactive)
```

<a id="symbol-listed_orders"></a>

## listed_orders

[server.py](../../../server.py) · `function`.

```python
def listed_orders():
```

Собирает главную сводку заказов, событий, планов и задач из SQLite.

Формирует возвращаемое значение из проверенного локального состояния.

Непосредственные вызовы: `order_store`, `client_activity_store`, `object_activity_store`, `objects.visible_orders`, `activity.visible_orders`, `store.list`, `OrderTodos(store).attach`, `OrderTodos`, `work_orders.in_work`, `work_orders.archived`, `calendar_events.CalendarEvents(store).list`, `calendar_events.CalendarEvents`, `invoice_store().calendar_plans`, `invoice_store`, `order_deadlines.week_options`, `store.pending_unregistrations`, `dict`, `metadata_store().status`, `metadata_store`.

Выражения возврата (ветки читаются в исходнике):

```python
{'orders': OrderTodos(store).attach([order for order in visible if not work_orders.in_work(order['path']) and (not work_orders.archived(order))]), 'calendar_supplier_orders': OrderTodos(store).attach([order for order in visible if order['work_supplier']]), 'calendar_events': calendar_events.CalendarEvents(store).list(), 'calendar_invoice_plans': invoice_store().calendar_plans([order for order in visible if not work_orders.in_work(order['path'])]), 'favorites': [order for order in visible if order['is_favorite'] is True and (not work_orders.archived(order))], 'deadline_week_options': order_d...
```

<a id="symbol-listed_work_orders"></a>

## listed_work_orders

[server.py](../../../server.py) · `function`.

```python
def listed_work_orders(relative):
```

Собирает список производственного раздела по сохранённому каталогу.

Возвращает `WorkOrderList(order_store()).read(relative)`.

Непосредственные вызовы: `WorkOrderList(order_store()).read`, `WorkOrderList`, `order_store`.

Выражения возврата (ветки читаются в исходнике):

```python
WorkOrderList(order_store()).read(relative)
```

<a id="symbol-load_legacy_statuses"></a>

## load_legacy_statuses

[server.py](../../../server.py) · `function`.

```python
def load_legacy_statuses():
```

Читает прежний app-local JSON статусов для отдельной миграции.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `STATUSES_FILE.exists`, `json.loads`, `STATUSES_FILE.read_text`, `isinstance`, `ValueError`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{}
records
```

<a id="symbol-main"></a>

## main

[server.py](../../../server.py) · `function`.

```python
def main():
```

Удерживает блокировку рабочей установки на весь срок жизни сервера.

Пока база передана другой машине, запуск останавливается до открытия SQLite.

Непосредственные вызовы: `DATA_DIR.resolve`, `data.mkdir`, `(data / '.handoff-run.lock').open`, `fcntl.flock`, `SystemExit`, `(data.parent / '.handoff-parked.json').exists`, `serve`.

Явные исключения: `SystemExit`.

<a id="symbol-metadata_store"></a>

## metadata_store

[server.py](../../../server.py) · `function`.

```python
def metadata_store():
```

Создаёт адаптер основных метаданных поверх хранилища заказов.

Возвращает `MetadataStore(order_store())`.

Непосредственные вызовы: `MetadataStore`, `order_store`.

Выражения возврата (ветки читаются в исходнике):

```python
MetadataStore(order_store())
```

<a id="symbol-metadata_worker"></a>

## metadata_worker

[server.py](../../../server.py) · `function`.

```python
def metadata_worker():
```

Выполняет первоначальный импорт, восстановление намерений и резервные снимки.

Передаёт работу `METADATA_REFRESH.clear`, `metadata_store().backup`, `metadata_store`.

Непосредственные вызовы: `METADATA_REFRESH.clear`, `metadata_store().backup`, `metadata_store`, `OrderLinks(order_store()).migrate_statuses`, `OrderLinks`, `order_store`, `order_creation.recover`, `metadata_store().status`, `metadata_store().migrate`, `metadata_store().imported`, `metadata_store().error`, `print`, `METADATA_REFRESH.wait`.

<a id="symbol-migrate_statuses"></a>

## migrate_statuses

[server.py](../../../server.py) · `function`.

```python
def migrate_statuses():
```

Переносит известные прежние статусы по правилам действующего хранилища.

Возвращает `None`; либо `{'migrated': migrated, 'unresolved': unresolved, 'archive': str(archive)}`.

Непосредственные вызовы: `STATUSES_FILE.exists`, `load_legacy_statuses`, `records.items`, `isinstance`, `unresolved.append`, `str`, `re.match`, `candidates.append`, `editable_status_folder`, `order_document.split_statuses`, `record.get`, `pending.setdefault(relative_path(folder), []).append`, `pending.setdefault`, `relative_path`, `pending.items`, `next`, `len`, `unresolved.extend`, `status_document(folder).exists`, `status_document`, `write_status_document`, `archive.exists`, `archive.is_symlink`, `shutil.move`.

Выражения возврата (ветки читаются в исходнике):

```python
None
{'migrated': migrated, 'unresolved': unresolved, 'archive': str(archive)}
```

<a id="symbol-mobile_sync_worker"></a>

## mobile_sync_worker

[server.py](../../../server.py) · `function`.

```python
def mobile_sync_worker():
```

Выполняет старый мобильный цикл; при SQLite-only завершается сразу.

Координирует фоновые потоки через локальные события или блокировки.

Непосредственные вызовы: `MobileBridge(order_store()).run`, `MobileBridge`, `order_store`, `print`, `threading.Event().wait`, `threading.Event`.

<a id="symbol-next_print_name"></a>

## next_print_name

[server.py](../../../server.py) · `function`.

```python
def next_print_name(folder):
```

Подбирает свободное имя нового задания печати.

Возвращает `filename`; либо `name`.

Непосредственные вызовы: `datetime.now(ZoneInfo('Europe/Moscow')).strftime`, `datetime.now`, `ZoneInfo`, `(folder / filename).exists`, `metadata_store().get`, `metadata_store`, `relative_path`, `folder.iterdir`, `visible`, `item.is_file`, `item.suffix.lower`, `re.match`, `max`, `datetime.now(ZoneInfo('Europe/Moscow')).date().isoformat`, `datetime.now(ZoneInfo('Europe/Moscow')).date`, `(folder / name).exists`.

Выражения возврата (ветки читаются в исходнике):

```python
filename
name
```

<a id="symbol-normalized"></a>

## normalized

[server.py](../../../server.py) · `function`.

```python
def normalized(value):
```

Нормализует Unicode для устойчивого сравнения имён.

Возвращает `unicodedata.normalize('NFC', value).casefold()`.

Непосредственные вызовы: `unicodedata.normalize('NFC', value).casefold`, `unicodedata.normalize`.

Выражения возврата (ветки читаются в исходнике):

```python
unicodedata.normalize('NFC', value).casefold()
```

<a id="symbol-object_activity_store"></a>

## object_activity_store

[server.py](../../../server.py) · `function`.

```python
def object_activity_store():
```

Создаёт адаптер индекса активности нужной роли папки.

Возвращает `ObjectActivity(order_store(), STATUS_LOCK)`.

Непосредственные вызовы: `ObjectActivity`, `order_store`.

Выражения возврата (ветки читаются в исходнике):

```python
ObjectActivity(order_store(), STATUS_LOCK)
```

<a id="symbol-object_move_locks"></a>

## object_move_locks

[server.py](../../../server.py) · `function`.

```python
def object_move_locks():
```

Сериализует перенос объекта с мобильным обменом и записями файловых редакторов.

Внутри операции порядок следующих блокировок совпадает с переименованием папок.

<a id="symbol-order_store"></a>

## order_store

[server.py](../../../server.py) · `function`.

```python
def order_store():
```

Создаёт хранилище заказов текущего корня и режима сервера.

Возвращает `OrderStore(DATA_ROOT, DATA_DIR, STATUS_LABELS, database_only=DATABASE_ONLY)`.

Непосредственные вызовы: `OrderStore`.

Выражения возврата (ветки читаются в исходнике):

```python
OrderStore(DATA_ROOT, DATA_DIR, STATUS_LABELS, database_only=DATABASE_ONLY)
```

<a id="symbol-order_sync_worker"></a>

## order_sync_worker

[server.py](../../../server.py) · `function`.

```python
def order_sync_worker():
```

Повторяет обработку очередей документов с установленной паузой.

Координирует фоновые потоки через локальные события или блокировки.

Непосредственные вызовы: `HANDOFF_STOP.is_set`, `order_store().sync`, `order_store`, `folder_note_store().sync`, `folder_note_store`, `client_activity_store().sync`, `client_activity_store`, `object_activity_store().sync`, `object_activity_store`, `invoice_store().sync`, `invoice_store`, `metadata_store().sync`, `metadata_store`, `print`, `HANDOFF_STOP.wait`.

<a id="symbol-order_todo_worker"></a>

## order_todo_worker

[server.py](../../../server.py) · `function`.

```python
def order_todo_worker():
```

Обновляет каталог вложенных задач вне обработчика обычного опроса.

Передаёт работу `TODO_REFRESH.clear`, `tuple`, `TODO_REFRESH_PATHS.clear`.

Непосредственные вызовы: `TODO_REFRESH.clear`, `tuple`, `TODO_REFRESH_PATHS.clear`, `OrderTodos(order_store()).refresh`, `OrderTodos`, `order_store`, `print`, `TODO_REFRESH.wait`.

<a id="symbol-pdf_error"></a>

## pdf_error

[server.py](../../../server.py) · `function`.

```python
def pdf_error(stderr, fallback):
```

Преобразует сбой PDF в сообщение для интерфейса просмотра.

Возвращает `line.removeprefix('ZIGZAG_PDF_ERROR: ').strip() or fallback`; либо `fallback`.

Непосредственные вызовы: `stderr.decode('utf-8', errors='replace').splitlines`, `stderr.decode`, `line.startswith`, `line.removeprefix('ZIGZAG_PDF_ERROR: ').strip`, `line.removeprefix`.

Выражения возврата (ветки читаются в исходнике):

```python
line.removeprefix('ZIGZAG_PDF_ERROR: ').strip() or fallback
fallback
```

<a id="symbol-pdf_info"></a>

## pdf_info

[server.py](../../../server.py) · `function`.

```python
def pdf_info(target):
```

Читает число страниц и свойства PDF через ограниченный помощник.

Запускает внешний процесс; параметры и ограничения заданы в теле функции.

Непосредственные вызовы: `target.suffix.lower`, `ValueError`, `pdf_key`, `subprocess.run`, `str`, `pdf_renderer`, `json.loads`, `pdf_error`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
PDF_INFO_CACHE[key]
```

<a id="symbol-pdf_key"></a>

## pdf_key

[server.py](../../../server.py) · `function`.

```python
def pdf_key(target):
```

Вычисляет ключ кеша конкретной версии PDF.

Возвращает `hashlib.sha256(f'{target}:{stat.st_mtime_ns}:{stat.st_size}'.encode()).hexdigest()`.

Непосредственные вызовы: `target.stat`, `hashlib.sha256(f'{target}:{stat.st_mtime_ns}:{stat.st_size}'.encode()).hexdigest`, `hashlib.sha256`, `f'{target}:{stat.st_mtime_ns}:{stat.st_size}'.encode`.

Выражения возврата (ветки читаются в исходнике):

```python
hashlib.sha256(f'{target}:{stat.st_mtime_ns}:{stat.st_size}'.encode()).hexdigest()
```

<a id="symbol-pdf_page"></a>

## pdf_page

[server.py](../../../server.py) · `function`.

```python
def pdf_page(target, page):
```

Возвращает изображение выбранной страницы PDF из кеша или рендера.

Запускает внешний процесс; параметры и ограничения заданы в теле функции.

Непосредственные вызовы: `pdf_info`, `ValueError`, `pdf_key`, `int`, `len`, `preview.exists`, `cache.mkdir`, `subprocess.run`, `str`, `pdf_renderer`, `preview.unlink`, `pdf_error`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
preview
```

<a id="symbol-pdf_renderer"></a>

## pdf_renderer

[server.py](../../../server.py) · `function`.

```python
def pdf_renderer():
```

Получает собранный помощник просмотра PDF.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `native_renderers.build`, `ValueError`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
native_renderers.build(APP_DIR / 'pdf_preview.swift', DATA_DIR, 'pdf-renderer', 60)
```

<a id="symbol-preview_kind"></a>

## preview_kind

[server.py](../../../server.py) · `function`.

```python
def preview_kind(path):
```

Выбирает просмотрщик по расширению документа.

Возвращает `'spreadsheet'`; либо `'image'`.

Непосредственные вызовы: `path.suffix.lower`.

Выражения возврата (ветки читаются в исходнике):

```python
'spreadsheet'
'image'
'pdf'
'video'
'audio'
'text'
'native'
```

<a id="symbol-print_target"></a>

## print_target

[server.py](../../../server.py) · `function`.

```python
def print_target(relative, file=False):
```

Проверяет допустимую цель задания печати и её привязку.

При недопустимом состоянии возбуждает ValueError, FileNotFoundError.

Непосредственные вызовы: `guard_database`, `order_store`, `safe_path`, `any`, `(DATA_ROOT / Path(*Path(relative).parts[:index + 1])).is_symlink`, `Path`, `range`, `len`, `ValueError`, `relative_path`, `is_print_section`, `target.is_file`, `FileNotFoundError`, `target.is_symlink`, `target.suffix.lower`, `target.is_dir`.

Явные исключения: `ValueError`, `FileNotFoundError`.

Выражения возврата (ветки читаются в исходнике):

```python
target
```

<a id="symbol-read_config"></a>

## read_config

[server.py](../../../server.py) · `function`.

```python
def read_config(path=CONFIG_FILE):
```

Читает INI и допустимые переопределения окружения, разрешая путь корня.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `configparser.ConfigParser`, `config.read`, `ValueError`, `os.environ.get`, `config.get('storage', 'root', fallback='').strip`, `config.get`, `Path(root_value).expanduser`, `Path`, `root.is_absolute`, `Path(path).resolve`, `config.getint`, `root.resolve`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
(root.resolve(), host, port)
```

<a id="symbol-read_file_comment"></a>

## read_file_comment

[server.py](../../../server.py) · `function`.

```python
def read_file_comment(file):
```

Читает комментарий через выбранный режим хранения.

Возвращает `metadata_store().comment(file) if DATABASE_ONLY else file_comments.read(file)`.

Непосредственные вызовы: `metadata_store().comment`, `metadata_store`, `file_comments.read`.

Выражения возврата (ветки читаются в исходнике):

```python
metadata_store().comment(file) if DATABASE_ONLY else file_comments.read(file)
```

<a id="symbol-read_folder"></a>

## read_folder

[server.py](../../../server.py) · `function`.

```python
def read_folder(relative='', show_inactive=False):
```

Собирает представление папки и разрешённые файлы её роли.

У заказа обходит # cutter, # freza и # docs, у сверки — только # docs, у входящих счетов — непосредственные файлы.

Непосредственные вызовы: `safe_path`, `target.is_dir`, `FileNotFoundError`, `directory_children`, `folder_status`, `client_activity_store().read`, `client_activity_store`, `relative_path`, `object_activity_store().read`, `object_activity_store`, `inactive_paths`, `is_inactive`, `list`, `status.get`, `is_print_section`, `in_freza`, `len`, `Path`, `is_freza_task`, `folder.name.startswith`, `folder.name[1:].strip().casefold`, `folder.name[1:].strip`, `folder.is_symlink`, `order_file_folders.sort`, `os.walk`, `visible`, `file.suffix.lower`, `metadata_store().is_publication`, `metadata_store`, `file.is_file`, `file.stat`, `warnings.append`, `read_file_comment`, `files.append`, `current_path.relative_to(target).as_posix`, `current_path.relative_to`, `file_group`, `sketches.sketch_name`, `preview_kind`, `file.suffix.lstrip('.').upper`, `file.suffix.lstrip`, `file_comments.binding`, `thumbnail_cache.supported`, `thumbnail_cache.signature`, `thumbnail_entries.append`, `thumbnail_store().observe`, `thumbnail_store`, `Path(file['path']).suffix.lower`, `read_print_task`, `str`, `metadata_store().connect`, `db.execute`, `row['data'].encode`, `json.loads`, `Path(file['name']).suffix.lower`, `files.sort`, `sum`, `FolderNotes`, `order_store`, `folder_node`, `item.name.startswith`, `item.is_symlink`, `order_store().get`, `ValueError`, `event_notes.read`, `event_relevance.info`, `event_notes.get`, `nodes.append`, `breadcrumbs.extend`, `Path(*parts[:index + 1]).as_posix`, `enumerate`, `read_sketches`, `work_orders.in_work`, `order_store().connect`, `work_orders.supplier_name`, `work_orders.supplier_color`, `work_orders.supplier_favorites`, `node['name'].startswith`, `unicodedata.normalize`, `supplier_purchases.remember_sections`, `supplier_purchases.SupplierPurchases(order_store()).catalog`, `supplier_purchases.SupplierPurchases`, `supplier_purchases.supplier_name`, `counts.get`, `(WorkOrderList(order_store()) if work_list else object_orders.ObjectOrders(order_store())).refresh`, `WorkOrderList`, `object_orders.ObjectOrders`, `listed_work_orders`, `listed_object_orders`, `client_name`, `supplier_purchases.section_path`, `file_uploads.available`, `file_uploads.options`, `next_print_name`, `object_move.available`, `order_folders.year_container`, `folder_rename.available`, `event_trash.available`, `work_orders.supplier_order`.

Явные исключения: `FileNotFoundError`, `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{'name': target.name, 'path': relative_path(target), 'client': client_name(relative), 'workSupplier': work_orders.supplier_name(relative), 'workSupplierColor': supplier_color, 'purchaseSupplier': supplier_purchases.supplier_name(relative), 'purchaseSupplierPath': supplier_purchases.section_path(relative_path(target)), 'root': str(DATA_ROOT), 'breadcrumbs': breadcrumbs, 'directories': nodes, 'files': files, 'sketches': sketch_files, 'orderFileFolders': [{'name': folder.name, 'path': relative_path(folder)} for folder in order_file_folders], 'objectOrders': object_list, 'workOrderList': work_l...
```

<a id="symbol-read_folder.walk_error"></a>

## read_folder.walk_error

[server.py](../../../server.py) · `function`.

```python
def walk_error(error):
```

Сохраняет ошибку обхода, не выдавая неполный результат за полный.

Передаёт работу `warnings.append`.

Непосредственные вызовы: `warnings.append`.

<a id="symbol-read_print_task"></a>

## read_print_task

[server.py](../../../server.py) · `function`.

```python
def read_print_task(relative):
```

Читает задание печати из действующего хранилища или прежнего файла.

Возвращает `_read_print_task(relative)`.

Непосредственные вызовы: `_read_print_task`.

Выражения возврата (ветки читаются в исходнике):

```python
_read_print_task(relative)
```

<a id="symbol-read_sketches"></a>

## read_sketches

[server.py](../../../server.py) · `function`.

```python
def read_sketches(directories, warnings):
```

Собирает метаданные непосредственных CDR и сохранённую актуальность.

Возвращает `sorted(result, key=lambda item: (sort_key(Path(item['name'])), item['folder']))`.

Непосредственные вызовы: `FolderNotes`, `order_store`, `sketches.cdr_folder`, `folder.is_symlink`, `notes.read`, `relative_path`, `str`, `notes.get`, `sorted`, `folder.iterdir`, `visible`, `sketches.sketch_name`, `file.is_file`, `file.stat`, `result.append`, `file_comments.binding`, `sketches.fingerprint`, `thumbnail_cache.signature`, `sketches.info`, `thumbnail_entries.append`, `warnings.append`, `thumbnail_store().observe`, `thumbnail_store`.

Выражения возврата (ветки читаются в исходнике):

```python
sorted(result, key=lambda item: (sort_key(Path(item['name'])), item['folder']))
```

<a id="symbol-read_status_document"></a>

## read_status_document

[server.py](../../../server.py) · `function`.

```python
def read_status_document(folder, *, include_registration=False, include_todos=False):
```

Читает поля прежней файловой карточки для совместимого сценария.

Возвращает `{}`; либо `result`.

Непосредственные вызовы: `status_document`, `target.exists`, `order_document.load`, `record.get`, `result.update`, `order_document.read_todos`, `order_document.read_purchases`.

Выражения возврата (ветки читаются в исходнике):

```python
{}
result
```

<a id="symbol-read_tree"></a>

## read_tree

[server.py](../../../server.py) · `function`.

```python
def read_tree(relative='', query='', show_inactive=False):
```

Строит выбранный участок дерева с учётом поиска и неактивных путей.

При недопустимом состоянии возбуждает FileNotFoundError.

Непосредственные вызовы: `safe_path`, `target.is_dir`, `FileNotFoundError`, `inactive_paths`, `children_of`, `node_of`, `item.name.startswith`, `is_catalog_group`, `search_text`, `query.strip`, `matching_node`, `str`, `groups.append`.

Явные исключения: `FileNotFoundError`.

Выражения возврата (ветки читаются в исходнике):

```python
{'root': str(DATA_ROOT), 'rootName': DATA_ROOT.name, 'path': relative, 'children': nodes, 'groups': groups, 'auxiliary': auxiliary}
```

<a id="symbol-read_tree.children_of"></a>

## read_tree.children_of

[server.py](../../../server.py) · `function`.

```python
def children_of(path):
```

Получает допустимых непосредственных потомков узла дерева.

Возвращает `[item for item in directory_children(path) if show_inactive or not is_inactive(relative_path(item), inactive)]`.

Непосредственные вызовы: `directory_children`, `is_inactive`, `relative_path`.

Выражения возврата (ветки читаются в исходнике):

```python
[item for item in directory_children(path) if show_inactive or not is_inactive(relative_path(item), inactive)]
```

<a id="symbol-read_tree.matching_node"></a>

## read_tree.matching_node

[server.py](../../../server.py) · `function`.

```python
def matching_node(path):
```

Рекурсивно оставляет только совпавшие с поиском ветви дерева.

Возвращает `node`; либо `None`.

Непосредственные вызовы: `node_of`, `children_of`, `matching_node`, `search_text`, `relative_path`.

Выражения возврата (ветки читаются в исходнике):

```python
node
None
```

<a id="symbol-read_tree.node_of"></a>

## read_tree.node_of

[server.py](../../../server.py) · `function`.

```python
def node_of(path):
```

Формирует узел текущего обхода дерева папок.

Возвращает `{**folder_node(path), 'inactive': is_inactive(relative_path(path), inactive)}`.

Непосредственные вызовы: `folder_node`, `is_inactive`, `relative_path`.

Выражения возврата (ветки читаются в исходнике):

```python
{**folder_node(path), 'inactive': is_inactive(relative_path(path), inactive)}
```

<a id="symbol-refresh_after_object_move"></a>

## refresh_after_object_move

[server.py](../../../server.py) · `function`.

```python
def refresh_after_object_move():
```

Обновляет фоновые сводки и очереди после проверенного переноса объекта.

Запускается после освобождения блокировок операции.

Непосредственные вызовы: `schedule_order_sync`, `schedule_todo_refresh`.

<a id="symbol-relative_path"></a>

## relative_path

[server.py](../../../server.py) · `function`.

```python
def relative_path(path):
```

Преобразует путь в относительный ключ корня документов.

Возвращает `path.relative_to(DATA_ROOT).as_posix() if path != DATA_ROOT else ''`.

Непосредственные вызовы: `path.relative_to(DATA_ROOT).as_posix`, `path.relative_to`.

Выражения возврата (ветки читаются в исходнике):

```python
path.relative_to(DATA_ROOT).as_posix() if path != DATA_ROOT else ''
```

<a id="symbol-safe_path"></a>

## safe_path

[server.py](../../../server.py) · `function`.

```python
def safe_path(relative_path=''):
```

Проверяет границы корня, допустимую область и компоненты пути.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `ValueError`, `Path`, `relative.is_absolute`, `target.resolve`, `any`, `part.startswith`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
target
```

<a id="symbol-save_note"></a>

## save_note

[server.py](../../../server.py) · `function`.

```python
def save_note(relative, note):
```

Сохраняет заметку выбранной папки через предусмотренный формат хранения.

При недопустимом состоянии возбуждает FolderNoteConflict, ValueError, OrderConflict.

Непосредственные вызовы: `folder_note_store().get`, `folder_note_store`, `FolderNoteConflict`, `editable_status_folder`, `relative_path`, `isinstance`, `len`, `ValueError`, `is_service_folder`, `write_status_document`, `order_store().get`, `order_store`, `OrderConflict`, `status_document`, `order_document.load`, `record.get`, `folder_role`, `order_document.archive_current`, `order_document.atomic_write`, `order_document.render`.

Явные исключения: `FolderNoteConflict`, `ValueError`, `OrderConflict`.

<a id="symbol-save_print_task"></a>

## save_print_task

[server.py](../../../server.py) · `function`.

```python
def save_print_task(relative, link, description, revision, title=None):
```

Сохраняет задание печати по версии открытого редактора.

При недопустимом состоянии возбуждает PrintConflict, ValueError.

Непосредственные вызовы: `read_print_task`, `compose_print_text`, `metadata_store().put`, `metadata_store`, `title.strip`, `link.strip`, `print_target`, `target.read_bytes`, `hashlib.sha256(original).hexdigest`, `hashlib.sha256`, `PrintConflict`, `decode_print_document`, `split_print_text`, `encode_print_document`, `len`, `ValueError`, `history.parent.is_symlink`, `history.is_symlink`, `history.mkdir`, `backup.is_symlink`, `backup.exists`, `backup.write_bytes`, `target.with_name`, `temporary.write_bytes`, `temporary.chmod`, `target.stat`, `temporary.replace`, `temporary.unlink`.

Явные исключения: `PrintConflict`, `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
read_print_task(relative)
```

<a id="symbol-save_status"></a>

## save_status

[server.py](../../../server.py) · `function`.

```python
def save_status(relative, status, note, financial_status=None, todo_items=order_document.UNSET_TODOS, purchase_items=order_document.UNSET_TODOS):
```

Записывает статус через прежнюю файловую ветку совместимости.

При недопустимом состоянии возбуждает ValueError, OrderConflict.

Непосредственные вызовы: `editable_status_folder`, `is_service_folder`, `relative_path`, `ValueError`, `order_store().require_order_folder`, `order_store`, `isinstance`, `order_store().get`, `OrderConflict`, `write_status_document`.

Явные исключения: `ValueError`, `OrderConflict`.

<a id="symbol-schedule_mobile_sync"></a>

## schedule_mobile_sync

[server.py](../../../server.py) · `function`.

```python
def schedule_mobile_sync():
```

Планирует старый мобильный обмен только при разрешённом режиме.

Координирует фоновые потоки через локальные события или блокировки.

Непосредственные вызовы: `threading.Thread(target=MobileBridge(order_store()).run, daemon=True).start`, `threading.Thread`, `MobileBridge`, `order_store`.

<a id="symbol-schedule_order_sync"></a>

## schedule_order_sync

[server.py](../../../server.py) · `function`.

```python
def schedule_order_sync():
```

Запускает фоновую обработку очередей хранилищ и документов.

Координирует фоновые потоки через локальные события или блокировки.

Непосредственные вызовы: `HANDOFF_STOP.is_set`, `threading.Thread(target=sync, daemon=False).start`, `threading.Thread`.

<a id="symbol-schedule_order_sync.sync"></a>

## schedule_order_sync.sync

[server.py](../../../server.py) · `function`.

```python
def sync():
```

Обрабатывает сохранённую очередь синхронизации или публикации.

Передаёт работу `order_store().sync`, `order_store`, `folder_note_store().sync`.

Непосредственные вызовы: `order_store().sync`, `order_store`, `folder_note_store().sync`, `folder_note_store`, `client_activity_store().sync`, `client_activity_store`, `object_activity_store().sync`, `object_activity_store`, `invoice_store().sync`, `invoice_store`, `metadata_store().sync`, `metadata_store`.

<a id="symbol-schedule_todo_refresh"></a>

## schedule_todo_refresh

[server.py](../../../server.py) · `function`.

```python
def schedule_todo_refresh(relative=None):
```

Сигнализирует фоновому работнику о явном обновлении задач.

Передаёт работу `TODO_REFRESH_PATHS.add`, `TODO_REFRESH.set`.

Непосредственные вызовы: `TODO_REFRESH_PATHS.add`, `TODO_REFRESH.set`.

<a id="symbol-search_text"></a>

## search_text

[server.py](../../../server.py) · `function`.

```python
def search_text(value):
```

Нормализует текст для нечувствительного к регистру поиска.

Возвращает `re.sub('#\\s*', '#', normalized(value))`.

Непосредственные вызовы: `re.sub`, `normalized`.

Выражения возврата (ветки читаются в исходнике):

```python
re.sub('#\\s*', '#', normalized(value))
```

<a id="symbol-send_calendar_command"></a>

## send_calendar_command

[server.py](../../../server.py) · `function`.

```python
def send_calendar_command():
```

Собирает и отправляет календарь для команды бота без браузера пользователя.

Возвращает `telegram_calendar.send(image, start, DATA_DIR, through=through, todo_text=calendar_todos.digest(snapshot, start, through))`.

Непосредственные вызовы: `datetime.now`, `listed_orders`, `calendar_delivery.period`, `calendar_delivery.render`, `telegram_calendar.send`, `calendar_todos.digest`.

Выражения возврата (ветки читаются в исходнике):

```python
telegram_calendar.send(image, start, DATA_DIR, through=through, todo_text=calendar_todos.digest(snapshot, start, through))
```

<a id="symbol-serve"></a>

## serve

[server.py](../../../server.py) · `function`.

```python
def serve():
```

Разбирает параметры запуска и выполняет основной сценарий программы.

Координирует фоновые потоки через локальные события или блокировки.

Непосредственные вызовы: `len`, `int`, `metadata_store().connect`, `metadata_store`, `metadata_store().backup`, `order_store().discard_service_orders`, `order_store`, `print`, `migrate_statuses`, `', '.join`, `ThreadingHTTPServer`, `remote_access.start`, `threading.Event`, `threading.Thread`, `signal.signal`, `threading.Thread(target=order_sync_worker, daemon=False).start`, `threading.Thread(target=mobile_sync_worker, daemon=True).start`, `threading.Thread(target=order_todo_worker, daemon=True).start`, `threading.Thread(target=client_activity_worker, daemon=True).start`, `threading.Thread(target=metadata_worker, daemon=True).start`, `threading.Thread(target=recovery_backup.worker, args=(order_store().database, DATA_ROOT, APP_DIR), daemon=True).start`, `thumbnail_worker.start`, `inbox_worker.start`, `server.serve_forever`, `HANDOFF_STOP.set`, `remote_server.shutdown`, `remote_server.server_close`, `inbox_stop.set`, `inbox_worker.join`, `thumbnail_stop.set`, `thumbnail_worker.join`, `server.server_close`, `object_move.wait_for_jobs`.

<a id="symbol-serve.shutdown"></a>

## serve.shutdown

[server.py](../../../server.py) · `function`.

```python
def shutdown(signum, frame):
```

Останавливает приём запросов и позволяет начатым обработчикам завершиться.

Срабатывает в основном потоке, а shutdown выполняет отдельный поток.

Непосредственные вызовы: `HANDOFF_STOP.is_set`, `HANDOFF_STOP.set`, `inbox_stop.set`, `thumbnail_stop.set`, `threading.Thread(target=server.shutdown, daemon=True).start`, `threading.Thread`.

<a id="symbol-sketch_target"></a>

## sketch_target

[server.py](../../../server.py) · `function`.

```python
def sketch_target(relative, key=None):
```

Проверяет точный эскиз, папку заказа и привязку запроса.

При недопустимом состоянии возбуждает FolderNoteConflict.

Непосредственные вызовы: `sketches.folder_path`, `comment_file`, `order_store().require_order_folder`, `order_store`, `Path(folder).parent.as_posix`, `Path`, `file_comments.binding`, `FolderNoteConflict`.

Явные исключения: `FolderNoteConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
target
```

<a id="symbol-sort_key"></a>

## sort_key

[server.py](../../../server.py) · `function`.

```python
def sort_key(path):
```

Строит ключ стабильной сортировки файлов или папок интерфейса.

Возвращает `[(1, int(part)) if part.isdigit() else (0, normalized(part)) for part in re.split('(\\d+)', path.name)]`.

Непосредственные вызовы: `part.isdigit`, `int`, `normalized`, `re.split`.

Выражения возврата (ветки читаются в исходнике):

```python
[(1, int(part)) if part.isdigit() else (0, normalized(part)) for part in re.split('(\\d+)', path.name)]
```

<a id="symbol-split_print_text"></a>

## split_print_text

[server.py](../../../server.py) · `function`.

```python
def split_print_text(text):
```

Разбирает название, ссылку и описание задания печати.

Возвращает `(lines[0].strip() if header_index else '', title, '\n'.join(remaining))`; либо `(link, lines[0].strip(), '\n'.join(remaining))`.

Непосредственные вызовы: `text.replace('\r\n', '\n').split`, `text.replace`, `len`, `is_link`, `lines[0].strip`, `lines[header_index].startswith`, `lines[header_index].partition(':')[2].strip`, `lines[header_index].partition`, `remaining.pop`, `'\n'.join`, `enumerate`, `line.strip`, `all`, `item.strip`.

Выражения возврата (ветки читаются в исходнике):

```python
(lines[0].strip() if header_index else '', title, '\n'.join(remaining))
(link, lines[0].strip(), '\n'.join(remaining))
(link, '', '\n'.join(remaining))
('', '', text)
```

<a id="symbol-split_print_text.is_link"></a>

## split_print_text.is_link

[server.py](../../../server.py) · `function`.

```python
def is_link(line):
```

Проверяет ссылку без использования её цели для обхода документов.

Возвращает `parsed.scheme.lower() in {'http', 'https'} and bool(parsed.netloc) and (not any((char.isspace() for char in line)))`.

Непосредственные вызовы: `urllib.parse.urlparse`, `parsed.scheme.lower`, `bool`, `any`, `char.isspace`.

Выражения возврата (ветки читаются в исходнике):

```python
parsed.scheme.lower() in {'http', 'https'} and bool(parsed.netloc) and (not any((char.isspace() for char in line)))
```

<a id="symbol-status_document"></a>

## status_document

[server.py](../../../server.py) · `function`.

```python
def status_document(folder):
```

Находит прежнюю карточку и выполняет файловую нормализацию совместимости.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `target.is_symlink`, `target.exists`, `target.is_file`, `ValueError`, `any`, `(folder / name).exists`, `(folder / name).is_symlink`, `is_service_folder`, `relative_path`, `folder.relative_to`, `(DATA_ROOT / Path(*relative.parts[:index + 1])).is_symlink`, `Path`, `range`, `len`, `order_document.load`, `bool`, `order_document.ORDER_FIELDS.intersection`, `order_document.folder_note`, `order_document.atomic_write`, `order_document.render`, `order_document.archive_legacy`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
target
```

<a id="symbol-text_from_rtf"></a>

## text_from_rtf

[server.py](../../../server.py) · `function`.

```python
def text_from_rtf(value):
```

Преобразует текст задания между RTF и обычным текстом.

Запускает внешний процесс; параметры и ограничения заданы в теле функции.

Непосредственные вызовы: `isinstance`, `value.encode`, `subprocess.run`, `result.stdout.decode`, `ValueError`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
result.stdout.decode('utf-8')
```

<a id="symbol-text_to_rtf"></a>

## text_to_rtf

[server.py](../../../server.py) · `function`.

```python
def text_to_rtf(text):
```

Преобразует текст задания между RTF и обычным текстом.

Возвращает `'{\\rtf1\\ansi\\ansicpg1251\\uc1 ' + ''.join(escaped) + '}'`.

Непосредственные вызовы: `text.encode`, `range`, `len`, `int.from_bytes`, `ord`, `escaped.append`, `chr`, `''.join`.

Выражения возврата (ветки читаются в исходнике):

```python
'{\\rtf1\\ansi\\ansicpg1251\\uc1 ' + ''.join(escaped) + '}'
```

<a id="symbol-thumbnail_store"></a>

## thumbnail_store

[server.py](../../../server.py) · `function`.

```python
def thumbnail_store():
```

Получает экземпляр отдельного кеша миниатюр текущего корня.

Возвращает `_thumbnail_store(DATA_ROOT, DATA_DIR)`.

Непосредственные вызовы: `_thumbnail_store`.

Выражения возврата (ветки читаются в исходнике):

```python
_thumbnail_store(DATA_ROOT, DATA_DIR)
```

<a id="symbol-visible"></a>

## visible

[server.py](../../../server.py) · `function`.

```python
def visible(path):
```

Отбирает видимые пользовательские записи без служебных скрытых файлов.

Возвращает `not path.name.startswith('.') and (not path.is_symlink())`.

Непосредственные вызовы: `path.name.startswith`, `path.is_symlink`.

Выражения возврата (ветки читаются в исходнике):

```python
not path.name.startswith('.') and (not path.is_symlink())
```

<a id="symbol-write_status_document"></a>

## write_status_document

[server.py](../../../server.py) · `function`.

```python
def write_status_document(folder, status, note, financial_status=None, todo_items=order_document.UNSET_TODOS, purchase_items=order_document.UNSET_TODOS):
```

Записывает прежнюю файловую карточку в совместимом режиме.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `status_document`, `order_document.load`, `is_service_folder`, `relative_path`, `order_document.folder_note`, `order_document.write_todos`, `record.get`, `order_document.read_purchases`, `ValueError`, `order_document.write_purchases`, `order_document.archive_current`, `order_document.atomic_write`, `order_document.render`.

Явные исключения: `ValueError`.
