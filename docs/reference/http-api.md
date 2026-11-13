# HTTP API: точки входа

Получено статически из веток обработчиков. Параметры ниже — строковые ключи payload/get, найденные внутри ветки, а не автоматически доказанная обязательная JSON-схема. Точные проверки находятся по ссылке и в вызываемом доменном методе.

На внешнем слушателе все маршруты наследуют проверки входа. HEAD использует общую GET-маршрутизацию. Защитные проверки, общие лимиты тела и специальные загрузки могут находиться перед перечисленными ветками.

## GET / HEAD /api/health

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/health'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'status': 'ok', 'release': RELEASE_ID, 'root': str(DATA_ROOT)}, head=head)
```

Вызовы ветки: `str`.

## GET / HEAD /api/orders

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/orders'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(listed_orders(), head=head)
```

Вызовы ветки: `listed_orders`.

## GET / HEAD /api/hidden-orders

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/hidden-orders'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(hidden_orders.listed(order_store(), client_activity_store().inactive_paths(), object_activity_store().inactive_paths()), head=head)
```

Вызовы ветки: `hidden_orders.listed`, `order_store`, `client_activity_store().inactive_paths`, `object_activity_store().inactive_paths`, `client_activity_store`, `object_activity_store`.

## GET / HEAD /api/calendar-telegram-settings

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/calendar-telegram-settings'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(telegram_calendar.status(DATA_DIR), head=head)
```

Вызовы ветки: `telegram_calendar.status`.

## GET / HEAD /api/inbox

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/inbox'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(telegram_inbox.snapshot(order_store(), DATA_DIR), head=head)
```

Вызовы ветки: `telegram_inbox.snapshot`, `order_store`.

## GET / HEAD /api/inbox-folder

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/inbox-folder'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(inbox_folder.snapshot(DATA_ROOT), head=head)
```

Вызовы ветки: `inbox_folder.snapshot`.

## GET / HEAD /api/object-orders

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/object-orders'`.

Ключи query, читаемые в ветке: `show_inactive`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(listed_object_orders(relative, query.get('show_inactive', [''])[0] == '1'), head=head)
```

Вызовы ветки: `listed_object_orders`.

## GET / HEAD /api/work-orders

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/work-orders'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(listed_work_orders(relative), head=head)
```

Вызовы ветки: `listed_work_orders`.

## GET / HEAD /api/supplier-purchases

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/supplier-purchases'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(supplier_purchases.SupplierPurchases(order_store()).read(relative, inactive=inactive_paths()), head=head)
```

Вызовы ветки: `supplier_purchases.SupplierPurchases(order_store()).read`, `supplier_purchases.SupplierPurchases`, `inactive_paths`, `order_store`.

## GET / HEAD /api/purchase-suppliers

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/purchase-suppliers'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(supplier_purchases.SupplierPurchases(order_store()).catalog(inactive=inactive_paths()), head=head)
```

Вызовы ветки: `supplier_purchases.SupplierPurchases(order_store()).catalog`, `supplier_purchases.SupplierPurchases`, `inactive_paths`, `order_store`.

## GET / HEAD /api/work-supplier-favorites

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/work-supplier-favorites'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(work_orders.read_supplier_favorites(order_store(), relative), head=head)
```

Вызовы ветки: `work_orders.read_supplier_favorites`, `order_store`.

## GET / HEAD /api/storage

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/storage'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(metadata_store().status() if DATABASE_ONLY else {'database_only': False}, head=head)
```

Вызовы ветки: `metadata_store().status`, `metadata_store`.

## GET / HEAD /api/thumbnail-status

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/thumbnail-status'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(thumbnail_store().status(), head=head)
```

Вызовы ветки: `thumbnail_store().status`, `thumbnail_store`.

## GET / HEAD /api/thumbnail

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path in {'/api/thumbnail', '/api/thumbnail-cover'}`.

Ключи query, читаемые в ветке: `v`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'state': 'pending'}, 202, head=head)
```

Вызовы ветки: `thumbnail_store().cover`, `thumbnail_store`, `thumbnail_store().image`, `self.send_response`, `self.send_header`, `self.end_headers`, `str`, `self.wfile.write`, `len`.

## GET / HEAD /api/thumbnail-cover

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path in {'/api/thumbnail', '/api/thumbnail-cover'}`.

Ключи query, читаемые в ветке: `v`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'state': 'pending'}, 202, head=head)
```

Вызовы ветки: `thumbnail_store().cover`, `thumbnail_store`, `thumbnail_store().image`, `self.send_response`, `self.send_header`, `self.end_headers`, `str`, `self.wfile.write`, `len`.

## GET / HEAD /api/invoices

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/invoices'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'items': service.with_links(invoice_store().list(relative)), 'trash': service.with_links(invoice_store().list(relative, trashed=True))}, head=head)
```

Вызовы ветки: `reconciliations.Reconciliations`, `order_store`, `service.with_links`, `invoice_store().list`, `invoice_store`.

## GET / HEAD /api/invoice-catalog

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/invoice-catalog'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'items': invoice_store().catalog()}, head=head)
```

Вызовы ветки: `invoice_store().catalog`, `invoice_store`.

## GET / HEAD /api/invoice-products

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path in {'/api/invoice-seller', '/api/invoice-products'}`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_preferences.resource(invoice_store(), parsed.path.rsplit('-', 1)[1]), head=head)
```

Вызовы ветки: `invoice_preferences.resource`, `invoice_store`, `parsed.path.rsplit`.

## GET / HEAD /api/invoice-seller

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path in {'/api/invoice-seller', '/api/invoice-products'}`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_preferences.resource(invoice_store(), parsed.path.rsplit('-', 1)[1]), head=head)
```

Вызовы ветки: `invoice_preferences.resource`, `invoice_store`, `parsed.path.rsplit`.

## GET / HEAD /api/reconciliations

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/reconciliations'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'items': reconciliations.Reconciliations(order_store()).catalog()}, head=head)
```

Вызовы ветки: `reconciliations.Reconciliations(order_store()).catalog`, `reconciliations.Reconciliations`, `order_store`.

## GET / HEAD /api/reconciliation

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/reconciliation'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(reconciliations.Reconciliations(order_store()).get(relative), head=head)
```

Вызовы ветки: `reconciliations.Reconciliations(order_store()).get`, `reconciliations.Reconciliations`, `order_store`.

## GET / HEAD /api/invoice-folder-candidates

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/invoice-folder-candidates'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_discovery.candidates(invoice_store(), relative), head=head)
```

Вызовы ветки: `invoice_discovery.candidates`, `invoice_store`.

## GET / HEAD /api/invoice

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/invoice'`.

Ключи query, читаемые в ветке: `id`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(reconciliations.Reconciliations(order_store()).with_links([item])[0], head=head)
```

Вызовы ветки: `invoice_store().get`, `invoice_store`, `reconciliations.Reconciliations(order_store()).with_links`, `reconciliations.Reconciliations`, `order_store`.

## GET / HEAD /api/invoice-document

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/invoice-document'`.

Ключи query, читаемые в ветке: `document_id`, `download`, `id`.

Вызовы ветки: `invoice_documents.content`, `invoice_store`, `self.send_invoice_document`.

## GET / HEAD /api/invoice-plan-source

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/invoice-plan-source'`.

Ключи query, читаемые в ветке: `id`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_store().plan_source(relative, query.get('id', [''])[0]), head=head)
```

Вызовы ветки: `invoice_store().plan_source`, `invoice_store`.

## GET / HEAD /api/invoice-pdf-info

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path in {'/api/invoice-pdf-info', '/api/invoice-pdf-page'}`.

Ключи query, читаемые в ветке: `id`, `page`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(pdf_info(target), head=head)
```

Вызовы ветки: `invoice_pdf_target`, `self.send_file`, `pdf_info`, `pdf_page`, `int`.

## GET / HEAD /api/invoice-pdf-page

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path in {'/api/invoice-pdf-info', '/api/invoice-pdf-page'}`.

Ключи query, читаемые в ветке: `id`, `page`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(pdf_info(target), head=head)
```

Вызовы ветки: `invoice_pdf_target`, `self.send_file`, `pdf_info`, `pdf_page`, `int`.

## GET / HEAD /api/invoice-pdf

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path in {'/api/invoice-pdf', '/api/invoice-preview'}`.

Ключи query, читаемые в ветке: `download`, `id`.

Вызовы ветки: `invoice_store().pdf`, `invoice_store().preview`, `invoice_store`, `self.send_invoice_pdf`.

## GET / HEAD /api/invoice-preview

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path in {'/api/invoice-pdf', '/api/invoice-preview'}`.

Ключи query, читаемые в ветке: `download`, `id`.

Вызовы ветки: `invoice_store().pdf`, `invoice_store().preview`, `invoice_store`, `self.send_invoice_pdf`.

## GET / HEAD /api/client-activity

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path in {'/api/client-activity', '/api/object-activity'}`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record, head=head)
```

Вызовы ветки: `object_activity_store`, `client_activity_store`, `activity.get`, `FileNotFoundError`.

## GET / HEAD /api/object-activity

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path in {'/api/client-activity', '/api/object-activity'}`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record, head=head)
```

Вызовы ветки: `object_activity_store`, `client_activity_store`, `activity.get`, `FileNotFoundError`.

## GET / HEAD /api/mobile-status

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/mobile-status'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(MobileBridge(order_store()).status(), head=head)
```

Вызовы ветки: `MobileBridge(order_store()).status`, `MobileBridge`, `order_store`.

## GET / HEAD /api/calendar-event

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/calendar-event'`.

Ключи query, читаемые в ветке: `id`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(calendar_events.CalendarEvents(order_store()).get(query.get('id', [''])[0]), head=head)
```

Вызовы ветки: `calendar_events.CalendarEvents(order_store()).get`, `calendar_events.CalendarEvents`, `order_store`.

## GET / HEAD /api/folder-note

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/folder-note'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record, head=head)
```

Вызовы ветки: `folder_note_store().get`, `folder_note_store`, `FileNotFoundError`.

## GET / HEAD /api/event-relevance

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/event-relevance'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(folder_note_store().event_relevances(relative), head=head)
```

Вызовы ветки: `folder_note_store().event_relevances`, `folder_note_store`.

## GET / HEAD /api/sketch-relevance

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/sketch-relevance'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(folder_note_store().sketch_relevances(relative), head=head)
```

Вызовы ветки: `folder_note_store().sketch_relevances`, `folder_note_store`.

## GET / HEAD /api/sketch-preview

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/sketch-preview'`.

Вызовы ветки: `sketch_target`, `sketches.preview`, `self.send_file`.

## GET / HEAD /api/freza-preview

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/freza-preview'`.

Вызовы ветки: `freza_preview_target`, `sketches.preview`, `image_preview`, `target.suffix.lower`, `self.send_file`.

## GET / HEAD /api/event-folders

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/event-folders'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(event_folders.preview(DATA_ROOT, relative, folder_note_store()), head=head)
```

Вызовы ветки: `event_folders.preview`, `folder_note_store`.

## GET / HEAD /api/folder-rename

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/folder-rename'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(folder_rename.preview(order_store(), relative), head=head)
```

Вызовы ветки: `folder_rename.preview`, `order_store`.

## GET / HEAD /api/object-years

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/object-years'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(object_years.preview(order_store(), relative), head=head)
```

Вызовы ветки: `object_years.preview`, `order_store`.

## GET / HEAD /api/object-move

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/object-move'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(object_move.preview(order_store(), relative), head=head)
```

Вызовы ветки: `object_move.preview`, `order_store`.

## GET / HEAD /api/object-move-status

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/object-move-status'`.

Ключи query, читаемые в ветке: `id`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(object_move.status(order_store(), query.get('id', [''])[0]), head=head)
```

Вызовы ветки: `object_move.status`, `order_store`.

## GET / HEAD /api/order

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/order'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({**record, 'purchaseSupplierPath': supplier_purchases.section_path(record['path'])}, head=head)
```

Вызовы ветки: `order_store().get`, `order_store`, `FileNotFoundError`, `supplier_purchases.section_path`.

## GET / HEAD /api/order-todos

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/order-todos'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(OrderTodos(order_store()).in_order(relative), head=head)
```

Вызовы ветки: `OrderTodos(order_store()).in_order`, `OrderTodos`, `order_store`.

## GET / HEAD /api/order-links

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/order-links'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(OrderLinks(order_store()).read(relative), head=head)
```

Вызовы ветки: `OrderLinks(order_store()).read`, `OrderLinks`, `order_store`.

## GET / HEAD /api/work-order-links

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/work-order-links'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(order_store().work_links(relative), head=head)
```

Вызовы ветки: `order_store().work_links`, `order_store`.

## GET / HEAD /api/tree

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/tree'`.

Ключи query, читаемые в ветке: `q`, `show_inactive`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(read_tree(relative, query.get('q', [''])[0], query.get('show_inactive', [''])[0] == '1'), head=head)
```

Вызовы ветки: `read_tree`.

## GET / HEAD /api/folder

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/folder'`.

Ключи query, читаемые в ветке: `show_inactive`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(read_folder(relative, query.get('show_inactive', [''])[0] == '1'), head=head)
```

Вызовы ветки: `read_folder`.

## GET / HEAD /api/print-task

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/print-task'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(read_print_task(relative), head=head)
```

Вызовы ветки: `read_print_task`.

## GET / HEAD /api/file-comment

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path == '/api/file-comment'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'path': relative, 'comment_key': file_comments.binding(target), **read_file_comment(target)}, head=head)
```

Вызовы ветки: `comment_file`, `file_comments.binding`, `read_file_comment`.

## GET / HEAD /api/file

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path in {'/api/file', '/api/preview', '/api/text', '/api/pdf', '/api/pdf-page', '/api/spreadsheet'}`.

Ключи query, читаемые в ветке: `download`, `page`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(pdf_info(target), head=head)
self.send_json({'text': body[:128 * 1024].decode('utf-8', errors='replace'), 'truncated': len(body) > 128 * 1024}, head=head)
```

Вызовы ветки: `safe_path`, `target.is_file`, `FileNotFoundError`, `spreadsheet_preview.read_bytes`, `self.send_response`, `self.send_header`, `self.end_headers`, `str`, `self.wfile.write`, `len`, `pdf_info`, `self.send_file`, `pdf_page`, `int`, `target.suffix.lower`, `ValueError`, `target.open`, `stream.read`, `image_preview`, `body[:128 * 1024].decode`, `preview_kind`.

## GET / HEAD /api/pdf

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path in {'/api/file', '/api/preview', '/api/text', '/api/pdf', '/api/pdf-page', '/api/spreadsheet'}`.

Ключи query, читаемые в ветке: `download`, `page`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(pdf_info(target), head=head)
self.send_json({'text': body[:128 * 1024].decode('utf-8', errors='replace'), 'truncated': len(body) > 128 * 1024}, head=head)
```

Вызовы ветки: `safe_path`, `target.is_file`, `FileNotFoundError`, `spreadsheet_preview.read_bytes`, `self.send_response`, `self.send_header`, `self.end_headers`, `str`, `self.wfile.write`, `len`, `pdf_info`, `self.send_file`, `pdf_page`, `int`, `target.suffix.lower`, `ValueError`, `target.open`, `stream.read`, `image_preview`, `body[:128 * 1024].decode`, `preview_kind`.

## GET / HEAD /api/pdf-page

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path in {'/api/file', '/api/preview', '/api/text', '/api/pdf', '/api/pdf-page', '/api/spreadsheet'}`.

Ключи query, читаемые в ветке: `download`, `page`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(pdf_info(target), head=head)
self.send_json({'text': body[:128 * 1024].decode('utf-8', errors='replace'), 'truncated': len(body) > 128 * 1024}, head=head)
```

Вызовы ветки: `safe_path`, `target.is_file`, `FileNotFoundError`, `spreadsheet_preview.read_bytes`, `self.send_response`, `self.send_header`, `self.end_headers`, `str`, `self.wfile.write`, `len`, `pdf_info`, `self.send_file`, `pdf_page`, `int`, `target.suffix.lower`, `ValueError`, `target.open`, `stream.read`, `image_preview`, `body[:128 * 1024].decode`, `preview_kind`.

## GET / HEAD /api/preview

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path in {'/api/file', '/api/preview', '/api/text', '/api/pdf', '/api/pdf-page', '/api/spreadsheet'}`.

Ключи query, читаемые в ветке: `download`, `page`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(pdf_info(target), head=head)
self.send_json({'text': body[:128 * 1024].decode('utf-8', errors='replace'), 'truncated': len(body) > 128 * 1024}, head=head)
```

Вызовы ветки: `safe_path`, `target.is_file`, `FileNotFoundError`, `spreadsheet_preview.read_bytes`, `self.send_response`, `self.send_header`, `self.end_headers`, `str`, `self.wfile.write`, `len`, `pdf_info`, `self.send_file`, `pdf_page`, `int`, `target.suffix.lower`, `ValueError`, `target.open`, `stream.read`, `image_preview`, `body[:128 * 1024].decode`, `preview_kind`.

## GET / HEAD /api/spreadsheet

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path in {'/api/file', '/api/preview', '/api/text', '/api/pdf', '/api/pdf-page', '/api/spreadsheet'}`.

Ключи query, читаемые в ветке: `download`, `page`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(pdf_info(target), head=head)
self.send_json({'text': body[:128 * 1024].decode('utf-8', errors='replace'), 'truncated': len(body) > 128 * 1024}, head=head)
```

Вызовы ветки: `safe_path`, `target.is_file`, `FileNotFoundError`, `spreadsheet_preview.read_bytes`, `self.send_response`, `self.send_header`, `self.end_headers`, `str`, `self.wfile.write`, `len`, `pdf_info`, `self.send_file`, `pdf_page`, `int`, `target.suffix.lower`, `ValueError`, `target.open`, `stream.read`, `image_preview`, `body[:128 * 1024].decode`, `preview_kind`.

## GET / HEAD /api/text

[ManagerHandler.handle_get](python/server.md#symbol-ManagerHandler.handle_get).

Условие: `parsed.path in {'/api/file', '/api/preview', '/api/text', '/api/pdf', '/api/pdf-page', '/api/spreadsheet'}`.

Ключи query, читаемые в ветке: `download`, `page`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(pdf_info(target), head=head)
self.send_json({'text': body[:128 * 1024].decode('utf-8', errors='replace'), 'truncated': len(body) > 128 * 1024}, head=head)
```

Вызовы ветки: `safe_path`, `target.is_file`, `FileNotFoundError`, `spreadsheet_preview.read_bytes`, `self.send_response`, `self.send_header`, `self.end_headers`, `str`, `self.wfile.write`, `len`, `pdf_info`, `self.send_file`, `pdf_page`, `int`, `target.suffix.lower`, `ValueError`, `target.open`, `stream.read`, `image_preview`, `body[:128 * 1024].decode`, `preview_kind`.

## POST /api/calendar-telegram-settings

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `urllib.parse.urlsplit(self.path).path == '/api/calendar-telegram-settings'`.

Вызовы ветки: `self.receive_telegram_settings`.

## POST /api/calendar-telegram

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `urllib.parse.urlsplit(self.path).path == '/api/calendar-telegram'`.

Вызовы ветки: `self.receive_calendar_telegram`.

## POST /api/file-upload

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `urllib.parse.urlsplit(self.path).path == '/api/file-upload'`.

Вызовы ветки: `self.receive_upload`.

## POST /api/invoice-document-upload

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route in {'/api/invoice-upload', '/api/invoice-document-upload', '/api/invoice-folder-attach'}`.

Вызовы ветки: `self.headers.get`, `ValueError`, `self.headers.get_content_type`, `urllib.parse.urlsplit`.

## POST /api/invoice-folder-attach

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route in {'/api/invoice-upload', '/api/invoice-document-upload', '/api/invoice-folder-attach'}`.

Вызовы ветки: `self.headers.get`, `ValueError`, `self.headers.get_content_type`, `urllib.parse.urlsplit`.

## POST /api/invoice-upload

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route in {'/api/invoice-upload', '/api/invoice-document-upload', '/api/invoice-folder-attach'}`.

Вызовы ветки: `self.headers.get`, `ValueError`, `self.headers.get_content_type`, `urllib.parse.urlsplit`.

## POST /api/invoice-products

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route in {'/api/invoice-seller', '/api/invoice-products'}`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'error': 'Изменяй товары и реквизиты через страницу менеджера'}, 403)
self.send_json(invoice_preferences.resource(invoice_store(), route.rsplit('-', 1)[1], payload))
```

Вызовы ветки: `self.headers.get`, `self.headers.get_content_type`, `urllib.parse.urlsplit`, `invoice_preferences.resource`, `invoice_store`, `route.rsplit`.

## POST /api/invoice-seller

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route in {'/api/invoice-seller', '/api/invoice-products'}`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'error': 'Изменяй товары и реквизиты через страницу менеджера'}, 403)
self.send_json(invoice_preferences.resource(invoice_store(), route.rsplit('-', 1)[1], payload))
```

Вызовы ветки: `self.headers.get`, `self.headers.get_content_type`, `urllib.parse.urlsplit`, `invoice_preferences.resource`, `invoice_store`, `route.rsplit`.

## POST /api/invoice-reconciliation

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route in {'/api/reconciliation-save', '/api/invoice-reconciliation'}`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'error': 'Изменяй сверки через страницу менеджера'}, 403)
self.send_json(service.save(payload) if route.endswith('-save') else service.assign(invoice_store(), payload))
```

Вызовы ветки: `self.headers.get`, `self.headers.get_content_type`, `urllib.parse.urlsplit`, `reconciliations.Reconciliations`, `order_store`, `route.endswith`, `service.save`, `service.assign`, `invoice_store`.

## POST /api/reconciliation-save

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route in {'/api/reconciliation-save', '/api/invoice-reconciliation'}`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'error': 'Изменяй сверки через страницу менеджера'}, 403)
self.send_json(service.save(payload) if route.endswith('-save') else service.assign(invoice_store(), payload))
```

Вызовы ветки: `self.headers.get`, `self.headers.get_content_type`, `urllib.parse.urlsplit`, `reconciliations.Reconciliations`, `order_store`, `route.endswith`, `service.save`, `service.assign`, `invoice_store`.

## POST /api/folder-note-save

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `in_reconciliations(reconciliation_path, legacy=True) and (route.startswith('/api/order-') and route != '/api/order-folder-create' or (route in {'/api/folder-note-save', '/api/status', '/api/note'} and len(Path(reconciliation_path).parts) == 3))`.

Вызовы ветки: `ValueError`.

## POST /api/note

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `in_reconciliations(reconciliation_path, legacy=True) and (route.startswith('/api/order-') and route != '/api/order-folder-create' or (route in {'/api/folder-note-save', '/api/status', '/api/note'} and len(Path(reconciliation_path).parts) == 3))`.

Вызовы ветки: `ValueError`.

## POST /api/order-

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `in_reconciliations(reconciliation_path, legacy=True) and (route.startswith('/api/order-') and route != '/api/order-folder-create' or (route in {'/api/folder-note-save', '/api/status', '/api/note'} and len(Path(reconciliation_path).parts) == 3))`.

Вызовы ветки: `ValueError`.

## POST /api/order-folder-create

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `in_reconciliations(reconciliation_path, legacy=True) and (route.startswith('/api/order-') and route != '/api/order-folder-create' or (route in {'/api/folder-note-save', '/api/status', '/api/note'} and len(Path(reconciliation_path).parts) == 3))`.

Вызовы ветки: `ValueError`.

## POST /api/status

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `in_reconciliations(reconciliation_path, legacy=True) and (route.startswith('/api/order-') and route != '/api/order-folder-create' or (route in {'/api/folder-note-save', '/api/status', '/api/note'} and len(Path(reconciliation_path).parts) == 3))`.

Вызовы ветки: `ValueError`.

## POST /api/inbox-complete

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route in {'/api/inbox-complete', '/api/inbox-remove', '/api/inbox-restore'}`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'error': 'Изменяй задачи через Inbox менеджера'}, 403)
self.send_json(result)
```

Вызовы ветки: `self.headers.get`, `self.headers.get_content_type`, `urllib.parse.urlsplit`, `telegram_inbox.complete`, `telegram_inbox.set_deleted`, `order_store`.

## POST /api/inbox-remove

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route in {'/api/inbox-complete', '/api/inbox-remove', '/api/inbox-restore'}`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'error': 'Изменяй задачи через Inbox менеджера'}, 403)
self.send_json(result)
```

Вызовы ветки: `self.headers.get`, `self.headers.get_content_type`, `urllib.parse.urlsplit`, `telegram_inbox.complete`, `telegram_inbox.set_deleted`, `order_store`.

## POST /api/inbox-restore

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route in {'/api/inbox-complete', '/api/inbox-remove', '/api/inbox-restore'}`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'error': 'Изменяй задачи через Inbox менеджера'}, 403)
self.send_json(result)
```

Вызовы ветки: `self.headers.get`, `self.headers.get_content_type`, `urllib.parse.urlsplit`, `telegram_inbox.complete`, `telegram_inbox.set_deleted`, `order_store`.

## POST /api/thumbnails

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/thumbnails'`.

Ключи payload, читаемые в ветке: `folders`, `paths`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'items': thumbnail_store().items(payload.get('paths', [])), 'covers': {path: thumbnail_store().cover(path) for path in folders}})
```

Вызовы ветки: `ValueError`, `isinstance`, `len`, `thumbnail_store().items`, `thumbnail_store().cover`, `thumbnail_store`.

## POST /api/invoice-create

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/invoice-create'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_store().create(payload), 201)
```

Вызовы ветки: `invoice_store().create`, `invoice_store`.

## POST /api/invoice-plan

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/invoice-plan'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_store().plan(payload), 200 if 'revision' in payload else 201)
```

Вызовы ветки: `invoice_store().plan`, `invoice_store`.

## POST /api/invoice-plan-calendar-move

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/invoice-plan-calendar-move'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_store().move_calendar_plan(payload))
```

Вызовы ветки: `invoice_store().move_calendar_plan`, `invoice_store`.

## POST /api/calendar-payment-remove

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/calendar-payment-remove'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_store().remove(payload, calendar_only=True))
```

Вызовы ветки: `invoice_store().remove`, `invoice_store`.

## POST /api/calendar-payment-restore

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/calendar-payment-restore'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_store().restore(payload, calendar_only=True))
```

Вызовы ветки: `invoice_store().restore`, `invoice_store`.

## POST /api/invoice-document-remove

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route in {'/api/invoice-document-remove', '/api/invoice-document-restore'}`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_documents.set_deleted(invoice_store(), payload, route.endswith('-remove')))
```

Вызовы ветки: `invoice_documents.set_deleted`, `invoice_store`, `route.endswith`, `schedule_order_sync`.

## POST /api/invoice-document-restore

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route in {'/api/invoice-document-remove', '/api/invoice-document-restore'}`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_documents.set_deleted(invoice_store(), payload, route.endswith('-remove')))
```

Вызовы ветки: `invoice_documents.set_deleted`, `invoice_store`, `route.endswith`, `schedule_order_sync`.

## POST /api/invoice-comment

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/invoice-comment'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_store().save_comment(payload))
```

Вызовы ветки: `invoice_store().save_comment`, `invoice_store`.

## POST /api/invoice-list-status

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/invoice-list-status'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_store().save_list_status(payload))
```

Вызовы ветки: `invoice_store().save_list_status`, `invoice_store`.

## POST /api/invoice-remove

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/invoice-remove'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_store().remove(payload))
```

Вызовы ветки: `invoice_store().remove`, `invoice_store`, `schedule_order_sync`.

## POST /api/invoice-restore

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/invoice-restore'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_store().restore(payload))
```

Вызовы ветки: `invoice_store().restore`, `invoice_store`, `schedule_order_sync`.

## POST /api/invoice-save

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/invoice-save'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_store().save(payload))
```

Вызовы ветки: `invoice_store().save`, `invoice_store`.

## POST /api/invoice-issue

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/invoice-issue'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record)
```

Вызовы ветки: `invoice_store().issue`, `invoice_store`, `schedule_order_sync`.

## POST /api/object-folder-create

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/object-folder-create'`.

Ключи payload, читаемые в ветке: `path`, `title`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(order_folders.create_object(DATA_ROOT, payload.get('path'), payload.get('title')), 201)
```

Вызовы ветки: `guard_database`, `order_store`, `order_folders.create_object`.

## POST /api/object-years

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/object-years'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(result)
```

Вызовы ветки: `object_years.group`, `order_store`, `schedule_order_sync`, `schedule_todo_refresh`.

## POST /api/object-move

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/object-move'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'error': 'Запускай перенос из формы объекта'}, 403)
self.send_json(object_move.start(order_store(), payload, object_move_locks, refresh_after_object_move), 202)
```

Вызовы ветки: `self.headers.get`, `self.headers.get_content_type`, `urllib.parse.urlsplit`, `object_move.start`, `order_store`.

## POST /api/event-folder-create

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/event-folder-create'`.

Ключи payload, читаемые в ветке: `path`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(event_folders.create(DATA_ROOT, payload, folder_note_store()), 201)
```

Вызовы ветки: `guard_database`, `order_store`, `event_folders.create`, `folder_note_store`.

## POST /api/folder-rename

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/folder-rename'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(result)
```

Вызовы ветки: `folder_rename.rename`, `order_store`, `schedule_order_sync`, `schedule_todo_refresh`.

## POST /api/event-folders-rename

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/event-folders-rename'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(event_folders.rename(folder_note_store(), payload))
```

Вызовы ветки: `event_folders.rename`, `folder_note_store`, `schedule_todo_refresh`.

## POST /api/event-relevance

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/event-relevance'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(event_relevance.info(record))
```

Вызовы ветки: `folder_note_store().save_relevance`, `folder_note_store`, `schedule_order_sync`, `event_relevance.info`.

## POST /api/sketch-relevance

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/sketch-relevance'`.

Ключи payload, читаемые в ветке: `key`, `path`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'path': payload['path'], 'key': payload['key'], 'folder': record['path'], 'status': sketches.group_info(record)})
```

Вызовы ветки: `folder_note_store().save_sketch_relevance`, `folder_note_store`, `schedule_order_sync`, `sketches.group_info`.

## POST /api/sketch-open

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/sketch-open'`.

Ключи payload, читаемые в ветке: `key`, `path`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'ok': True})
```

Вызовы ветки: `isinstance`, `ValueError`, `sketch_target`, `sketches.open_corel`.

## POST /api/order-add

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/order-add'`.

Ключи payload, читаемые в ветке: `path`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(store.get(relative), 201)
```

Вызовы ветки: `editable_status_folder`, `relative_path`, `order_store`, `store.path`, `store.require_order_folder`, `order_creation.retry_one`, `store.get`, `folder_status`, `store.import_folder`, `directory_children`, `schedule_order_sync`, `schedule_todo_refresh`.

## POST /api/mobile-sync

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/mobile-sync'`.

Ключи payload, читаемые в ветке: `enabled`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(bridge.status(), 202)
```

Вызовы ветки: `MobileBridge`, `order_store`, `bridge.configure`, `schedule_mobile_sync`, `bridge.status`.

## POST /api/order-save

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/order-save'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record)
```

Вызовы ветки: `order_store().save`, `order_store`, `schedule_order_sync`.

## POST /api/supplier-purchase-done

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/supplier-purchase-done'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(supplier_purchases.SupplierPurchases(order_store()).save(payload, inactive=inactive_paths()))
```

Вызовы ветки: `supplier_purchases.SupplierPurchases(order_store()).save`, `supplier_purchases.SupplierPurchases`, `inactive_paths`, `order_store`, `schedule_order_sync`.

## POST /api/supplier-purchase-text

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/supplier-purchase-text'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'error': 'Изменяй закупки через страницу поставщика'}, 403)
self.send_json(supplier_purchases.SupplierPurchases(order_store()).edit(payload, inactive=inactive_paths()))
```

Вызовы ветки: `self.headers.get`, `self.headers.get_content_type`, `urllib.parse.urlsplit`, `supplier_purchases.SupplierPurchases(order_store()).edit`, `supplier_purchases.SupplierPurchases`, `inactive_paths`, `order_store`, `schedule_order_sync`.

## POST /api/order-favorite

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/order-favorite'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record)
```

Вызовы ветки: `order_store().save_favorite`, `order_store`, `schedule_order_sync`.

## POST /api/order-links

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/order-links'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(OrderLinks(order_store()).save(payload))
```

Вызовы ветки: `OrderLinks(order_store()).save`, `OrderLinks`, `order_store`, `schedule_order_sync`.

## POST /api/order-flag

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/order-flag'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record)
```

Вызовы ветки: `order_store().save_flag`, `order_store`, `schedule_order_sync`.

## POST /api/order-blue-plus

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/order-blue-plus'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record)
```

Вызовы ветки: `order_store().save_blue_plus`, `order_store`, `schedule_order_sync`.

## POST /api/order-dollar

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/order-dollar'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record)
```

Вызовы ветки: `order_store().save_dollar`, `order_store`, `schedule_order_sync`.

## POST /api/order-status

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/order-status'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record)
```

Вызовы ветки: `order_store().save_status`, `order_store`, `schedule_order_sync`.

## POST /api/order-supplier-status

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/order-supplier-status'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record)
```

Вызовы ветки: `order_store().save_supplier_status`, `order_store`, `schedule_order_sync`.

## POST /api/order-deadline-week

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/order-deadline-week'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record)
```

Вызовы ветки: `order_store().save_deadline_week`, `order_store`, `schedule_order_sync`.

## POST /api/order-calendar-compact

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/order-calendar-compact'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(order_store().save_calendar_compact(payload))
```

Вызовы ветки: `order_store().save_calendar_compact`, `order_store`, `schedule_order_sync`.

## POST /api/order-deadline-comment

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/order-deadline-comment'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record)
```

Вызовы ветки: `order_store().save_deadline_comment`, `order_store`, `schedule_order_sync`.

## POST /api/calendar-event

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/calendar-event'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(calendar_events.CalendarEvents(order_store()).save(payload))
```

Вызовы ветки: `calendar_events.CalendarEvents(order_store()).save`, `calendar_events.CalendarEvents`, `order_store`.

## POST /api/calendar-event-remove

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route in ('/api/calendar-event-remove', '/api/calendar-event-restore')`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(calendar_events.CalendarEvents(order_store()).set_deleted(payload, route.endswith('-remove')))
```

Вызовы ветки: `calendar_events.CalendarEvents(order_store()).set_deleted`, `route.endswith`, `calendar_events.CalendarEvents`, `order_store`.

## POST /api/calendar-event-restore

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route in ('/api/calendar-event-remove', '/api/calendar-event-restore')`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(calendar_events.CalendarEvents(order_store()).set_deleted(payload, route.endswith('-remove')))
```

Вызовы ветки: `calendar_events.CalendarEvents(order_store()).set_deleted`, `route.endswith`, `calendar_events.CalendarEvents`, `order_store`.

## POST /api/order-calendar-event-remove

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route in ('/api/order-calendar-event-remove', '/api/order-calendar-event-restore')`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(operation(payload))
```

Вызовы ветки: `route.endswith`, `order_store`, `operation`.

## POST /api/order-calendar-event-restore

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route in ('/api/order-calendar-event-remove', '/api/order-calendar-event-restore')`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(operation(payload))
```

Вызовы ветки: `route.endswith`, `order_store`, `operation`.

## POST /api/calendar-color

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/calendar-color'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(calendar_events.CalendarEvents(order_store()).color(payload))
```

Вызовы ветки: `calendar_events.CalendarEvents(order_store()).color`, `calendar_events.CalendarEvents`, `order_store`.

## POST /api/order-calendar-color

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/order-calendar-color'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(order_store().save_calendar_color(payload))
```

Вызовы ветки: `order_store().save_calendar_color`, `order_store`.

## POST /api/calendar-move

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/calendar-move'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(calendar_events.CalendarEvents(order_store()).move(payload))
```

Вызовы ветки: `calendar_events.CalendarEvents(order_store()).move`, `calendar_events.CalendarEvents`, `order_store`.

## POST /api/order-calendar-inactive

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/order-calendar-inactive'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(order_store().save_calendar_inactive(payload))
```

Вызовы ветки: `order_store().save_calendar_inactive`, `order_store`.

## POST /api/order-calendar-completed

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/order-calendar-completed'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(order_store().save_calendar_completed(payload))
```

Вызовы ветки: `order_store().save_calendar_completed`, `order_store`.

## POST /api/calendar-completed

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/calendar-completed'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(calendar_events.CalendarEvents(order_store()).set_completed(payload))
```

Вызовы ветки: `calendar_events.CalendarEvents(order_store()).set_completed`, `calendar_events.CalendarEvents`, `order_store`.

## POST /api/invoice-plan-calendar-completed

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/invoice-plan-calendar-completed'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_store().save_plan_calendar_completed(payload))
```

Вызовы ветки: `invoice_store().save_plan_calendar_completed`, `invoice_store`.

## POST /api/order-calendar-trip

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/order-calendar-trip'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(order_store().save_calendar_trip(payload))
```

Вызовы ветки: `order_store().save_calendar_trip`, `order_store`.

## POST /api/order-calendar-watch-todos

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/order-calendar-watch-todos'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(order_store().save_calendar_watch_todos(payload))
```

Вызовы ветки: `order_store().save_calendar_watch_todos`, `order_store`.

## POST /api/invoice-plan-calendar-watch-todos

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/invoice-plan-calendar-watch-todos'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_store().save_plan_calendar_watch_todos(payload))
```

Вызовы ветки: `invoice_store().save_plan_calendar_watch_todos`, `invoice_store`.

## POST /api/calendar-trip

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/calendar-trip'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(calendar_events.CalendarEvents(order_store()).set_trip(payload))
```

Вызовы ветки: `calendar_events.CalendarEvents(order_store()).set_trip`, `calendar_events.CalendarEvents`, `order_store`.

## POST /api/invoice-plan-calendar-trip

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/invoice-plan-calendar-trip'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_store().save_plan_calendar_trip(payload))
```

Вызовы ветки: `invoice_store().save_plan_calendar_trip`, `invoice_store`.

## POST /api/calendar-inactive

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/calendar-inactive'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(calendar_events.CalendarEvents(order_store()).set_inactive(payload))
```

Вызовы ветки: `calendar_events.CalendarEvents(order_store()).set_inactive`, `calendar_events.CalendarEvents`, `order_store`.

## POST /api/invoice-plan-calendar-inactive

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/invoice-plan-calendar-inactive'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_store().save_plan_calendar_inactive(payload))
```

Вызовы ветки: `invoice_store().save_plan_calendar_inactive`, `invoice_store`.

## POST /api/invoice-plan-calendar-carryover

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/invoice-plan-calendar-carryover'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_store().save_plan_calendar_carryover(payload))
```

Вызовы ветки: `invoice_store().save_plan_calendar_carryover`, `invoice_store`.

## POST /api/invoice-plan-calendar-notified

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/invoice-plan-calendar-notified'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_store().save_plan_calendar_notified(payload))
```

Вызовы ветки: `invoice_store().save_plan_calendar_notified`, `invoice_store`.

## POST /api/order-calendar-event

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/order-calendar-event'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record)
```

Вызовы ветки: `order_store().save_calendar_event`, `order_store`, `schedule_order_sync`.

## POST /api/order-calendar-move

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/order-calendar-move'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record)
```

Вызовы ветки: `order_store().move_calendar_event`, `order_store`, `schedule_order_sync`.

## POST /api/work-supplier-favorite

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/work-supplier-favorite'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(work_orders.save_supplier_favorite(order_store(), payload))
```

Вызовы ветки: `work_orders.save_supplier_favorite`, `order_store`.

## POST /api/work-order-links

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/work-order-links'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(order_store().save_work_links(payload))
```

Вызовы ветки: `order_store().save_work_links`, `order_store`, `schedule_order_sync`.

## POST /api/client-activity

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route in {'/api/client-activity', '/api/client-activity-file', '/api/object-activity', '/api/object-activity-file'}`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record)
```

Вызовы ветки: `route.startswith`, `object_activity_store`, `client_activity_store`, `route.endswith`, `activity.accept_file`, `activity.save`, `schedule_order_sync`.

## POST /api/client-activity-file

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route in {'/api/client-activity', '/api/client-activity-file', '/api/object-activity', '/api/object-activity-file'}`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record)
```

Вызовы ветки: `route.startswith`, `object_activity_store`, `client_activity_store`, `route.endswith`, `activity.accept_file`, `activity.save`, `schedule_order_sync`.

## POST /api/object-activity

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route in {'/api/client-activity', '/api/client-activity-file', '/api/object-activity', '/api/object-activity-file'}`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record)
```

Вызовы ветки: `route.startswith`, `object_activity_store`, `client_activity_store`, `route.endswith`, `activity.accept_file`, `activity.save`, `schedule_order_sync`.

## POST /api/object-activity-file

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route in {'/api/client-activity', '/api/client-activity-file', '/api/object-activity', '/api/object-activity-file'}`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record)
```

Вызовы ветки: `route.startswith`, `object_activity_store`, `client_activity_store`, `route.endswith`, `activity.accept_file`, `activity.save`, `schedule_order_sync`.

## POST /api/order-remove

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/order-remove'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record)
```

Вызовы ветки: `order_store().remove`, `order_store`, `folder_note_store().get`, `folder_note_store`, `schedule_order_sync`.

## POST /api/orders-discover

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/orders-discover'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(discover_orders(), 202)
```

Вызовы ветки: `discover_orders`.

## POST /api/orders-sync

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/orders-sync'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'ok': True})
```

Вызовы ветки: `schedule_order_sync`, `METADATA_REFRESH.set`.

## POST /api/clients-refresh

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/clients-refresh'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'ok': True})
```

Вызовы ветки: `client_activity_store().refresh`, `client_activity_store`, `object_activity_store().refresh`, `object_activity_store`.

## POST /api/todos-refresh

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/todos-refresh'`.

Ключи payload, читаемые в ветке: `path`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'ok': True}, 202)
```

Вызовы ветки: `order_store().path`, `order_store`, `schedule_todo_refresh`.

## POST /api/print-create

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/print-create'`.

Ключи payload, читаемые в ветке: `description`, `link`, `path`, `title`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(create_print_task(payload.get('path', ''), payload.get('link', ''), payload.get('description', ''), payload.get('title', '')), 201)
```

Вызовы ветки: `create_print_task`.

## POST /api/print-save

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/print-save'`.

Ключи payload, читаемые в ветке: `description`, `link`, `path`, `revision`, `title`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(save_print_task(payload.get('path', ''), payload.get('link', ''), payload.get('description', ''), payload.get('revision'), payload.get('title')))
```

Вызовы ветки: `save_print_task`.

## POST /api/print-publish

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/print-publish'`.

Ключи payload, читаемые в ветке: `path`, `revision`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(result, 202)
```

Вызовы ветки: `read_print_task`, `metadata_store().publish`, `PrintConflict`, `compose_print_text(task['link'], task['description'], task['title']).encode`, `metadata_store`, `hashlib.sha256((task['path'] + task['revision']).encode()).hexdigest`, `Path`, `compose_print_text`, `datetime.now(ZoneInfo('Europe/Moscow')).strftime`, `hashlib.sha256`, `datetime.now`, `(task['path'] + task['revision']).encode`, `ZoneInfo`, `schedule_order_sync`.

## POST /api/file-comment

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/file-comment'`.

Ключи payload, читаемые в ветке: `comment`, `comment_key`, `path`, `revision`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'path': relative, 'comment_key': key, **record})
```

Вызовы ветки: `comment_file`, `file_comments.binding`, `FileCommentConflict`, `metadata_store().save_comment`, `file_comments.save`, `metadata_store`.

## POST /api/image-report

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/image-report'`.

Ключи payload, читаемые в ветке: `files`, `path`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(report, 201)
```

Вызовы ветки: `guard_database`, `create_image_report`, `order_store`.

## POST /api/files-trash-preview

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/files-trash-preview'`.

Ключи payload, читаемые в ветке: `files`, `path`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(file_trash.preview(DATA_ROOT, payload.get('path', ''), payload.get('files')))
```

Вызовы ветки: `file_trash.preview`.

## POST /api/event-trash-preview

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/event-trash-preview'`.

Ключи payload, читаемые в ветке: `path`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(event_trash.preview(order_store(), payload.get('path')))
```

Вызовы ветки: `event_trash.preview`, `order_store`.

## POST /api/event-trash

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/event-trash'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(result)
```

Вызовы ветки: `event_trash.remove`, `order_store`, `schedule_todo_refresh`.

## POST /api/event-trash-restore

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/event-trash-restore'`.

Ключи payload, читаемые в ветке: `session`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(result)
```

Вызовы ветки: `event_trash.restore`, `order_store`, `schedule_order_sync`, `schedule_todo_refresh`.

## POST /api/files-trash

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/files-trash'`.

Ключи payload, читаемые в ветке: `confirmed`, `files`, `path`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(result)
```

Вызовы ветки: `guard_database`, `file_trash.remove`, `order_store`.

## POST /api/event-trash-list

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route in {'/api/files-trash-list', '/api/event-trash-list'}`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'sessions': sessions, 'events': events, 'warning': warning})
```

Вызовы ветки: `event_trash.list_sessions`, `order_store`, `file_trash.list_sessions`, `errors.append`, `icloud_access.read_bytes`.

## POST /api/files-trash-list

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route in {'/api/files-trash-list', '/api/event-trash-list'}`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'sessions': sessions, 'events': events, 'warning': warning})
```

Вызовы ветки: `event_trash.list_sessions`, `order_store`, `file_trash.list_sessions`, `errors.append`, `icloud_access.read_bytes`.

## POST /api/files-trash-restore

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/files-trash-restore'`.

Ключи payload, читаемые в ветке: `session`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(result)
```

Вызовы ветки: `guard_database`, `file_trash.restore`, `order_store`.

## POST /api/open

[ManagerHandler.do_POST](python/server.md#symbol-ManagerHandler.do_POST).

Условие: `route == '/api/open'`.

Ключи payload, читаемые в ветке: `path`, `reveal`.

Вызовы ветки: `safe_path`, `target.exists`, `FileNotFoundError`, `subprocess.Popen`, `str`.

## GET / HEAD /_auth/session

[handler_class.RemoteHandler.get_remote](python/remote_access.md#symbol-handler_class.RemoteHandler.get_remote).

Условие: `route == '/_auth/session'`.

Вызовы ветки: `cookie`, `hmac.new(gate.key(document), ('logout:' + token).encode(), hashlib.sha256).hexdigest`, `hmac.new`, `gate.key`, `('logout:' + token).encode`, `self.reply`.

## POST /_auth/logout

[handler_class.RemoteHandler.do_POST](python/remote_access.md#symbol-handler_class.RemoteHandler.do_POST).

Условие: `route in {LOGIN_PATH, '/_auth/logout'}`.

Вызовы ветки: `self.headers.get_all`, `self.rfile.read(int(lengths[0])).decode`, `urllib.parse.parse_qs`, `any`, `self.headers.get`, `ValueError`, `fields.get`, `self.reply`, `len`, `re.fullmatch`, `int`, `self.headers.get_content_type`, `self.rfile.read`, `'Некорректная форма'.encode`, `fields.values`, `hmac.new(gate.key(document), ('logout:' + cookie(self, SESSION_COOKIE)).encode(), hashlib.sha256).hexdigest`, `hmac.compare_digest`, `hmac.new`, `expected.encode`, `csrf.encode`, `gate.key`, `('logout:' + cookie(self, SESSION_COOKIE)).encode`, `cookie_header`, `cookie`, `self.login_page`, `gate.valid`, `cookie(self, LOGIN_COOKIE).encode`, `gate.retry_after`, `gate.verifying.acquire`, `gate.verifying.release`, `hashlib.pbkdf2_hmac`, `digest.hex`, `password.encode`, `bytes.fromhex`, `gate.token`, `safe_next`.

## Специальные обработчики и ограничения перечня

Потоковые `/api/file-upload`, `/api/calendar-telegram` и настройка Telegram обрабатываются также отдельными receive-методами до общего JSON-dispatch. `/_auth/login`, `/_auth/session`, `/_auth/logout` проверяются в `remote_access.py`. GET/POST одной строки могут иметь разные правила. Список веток не является разрешением выполнять произвольные POST.
