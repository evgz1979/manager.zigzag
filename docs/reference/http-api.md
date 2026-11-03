# HTTP API: точки входа

Получено статически из веток обработчиков. Параметры ниже — строковые ключи payload/get, найденные внутри ветки, а не автоматически доказанная обязательная JSON-схема. Точные проверки находятся по ссылке и в вызываемом доменном методе.

На внешнем слушателе все маршруты наследуют проверки входа. HEAD использует общую GET-маршрутизацию. Защитные проверки, общие лимиты тела и специальные загрузки могут находиться перед перечисленными ветками.

## GET / HEAD /api/health

[server.py:1612](../../server.py#L1612) · `handle_get`.

Условие: `parsed.path == '/api/health'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'status': 'ok', 'release': RELEASE_ID, 'root': str(DATA_ROOT)}, head=head)
```

Вызовы ветки: `str`.

## GET / HEAD /api/orders

[server.py:1614](../../server.py#L1614) · `handle_get`.

Условие: `parsed.path == '/api/orders'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(listed_orders(), head=head)
```

Вызовы ветки: `listed_orders`.

## GET / HEAD /api/hidden-orders

[server.py:1616](../../server.py#L1616) · `handle_get`.

Условие: `parsed.path == '/api/hidden-orders'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(hidden_orders.listed(order_store(), client_activity_store().inactive_paths(), object_activity_store().inactive_paths()), head=head)
```

Вызовы ветки: `hidden_orders.listed`, `order_store`, `client_activity_store().inactive_paths`, `object_activity_store().inactive_paths`, `client_activity_store`, `object_activity_store`.

## GET / HEAD /api/calendar-telegram-settings

[server.py:1619](../../server.py#L1619) · `handle_get`.

Условие: `parsed.path == '/api/calendar-telegram-settings'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(telegram_calendar.status(DATA_DIR), head=head)
```

Вызовы ветки: `telegram_calendar.status`.

## GET / HEAD /api/inbox

[server.py:1621](../../server.py#L1621) · `handle_get`.

Условие: `parsed.path == '/api/inbox'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(telegram_inbox.snapshot(order_store(), DATA_DIR), head=head)
```

Вызовы ветки: `telegram_inbox.snapshot`, `order_store`.

## GET / HEAD /api/inbox-folder

[server.py:1623](../../server.py#L1623) · `handle_get`.

Условие: `parsed.path == '/api/inbox-folder'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(inbox_folder.snapshot(DATA_ROOT), head=head)
```

Вызовы ветки: `inbox_folder.snapshot`.

## GET / HEAD /api/object-orders

[server.py:1625](../../server.py#L1625) · `handle_get`.

Условие: `parsed.path == '/api/object-orders'`.

Ключи query, читаемые в ветке: `show_inactive`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(listed_object_orders(relative, query.get('show_inactive', [''])[0] == '1'), head=head)
```

Вызовы ветки: `listed_object_orders`.

## GET / HEAD /api/work-orders

[server.py:1627](../../server.py#L1627) · `handle_get`.

Условие: `parsed.path == '/api/work-orders'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(listed_work_orders(relative), head=head)
```

Вызовы ветки: `listed_work_orders`.

## GET / HEAD /api/supplier-purchases

[server.py:1629](../../server.py#L1629) · `handle_get`.

Условие: `parsed.path == '/api/supplier-purchases'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(supplier_purchases.SupplierPurchases(order_store()).read(relative, inactive=inactive_paths()), head=head)
```

Вызовы ветки: `supplier_purchases.SupplierPurchases(order_store()).read`, `supplier_purchases.SupplierPurchases`, `inactive_paths`, `order_store`.

## GET / HEAD /api/purchase-suppliers

[server.py:1631](../../server.py#L1631) · `handle_get`.

Условие: `parsed.path == '/api/purchase-suppliers'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(supplier_purchases.SupplierPurchases(order_store()).catalog(inactive=inactive_paths()), head=head)
```

Вызовы ветки: `supplier_purchases.SupplierPurchases(order_store()).catalog`, `supplier_purchases.SupplierPurchases`, `inactive_paths`, `order_store`.

## GET / HEAD /api/work-supplier-favorites

[server.py:1633](../../server.py#L1633) · `handle_get`.

Условие: `parsed.path == '/api/work-supplier-favorites'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(work_orders.read_supplier_favorites(order_store(), relative), head=head)
```

Вызовы ветки: `work_orders.read_supplier_favorites`, `order_store`.

## GET / HEAD /api/storage

[server.py:1635](../../server.py#L1635) · `handle_get`.

Условие: `parsed.path == '/api/storage'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(metadata_store().status() if DATABASE_ONLY else {'database_only': False}, head=head)
```

Вызовы ветки: `metadata_store().status`, `metadata_store`.

## GET / HEAD /api/thumbnail-status

[server.py:1637](../../server.py#L1637) · `handle_get`.

Условие: `parsed.path == '/api/thumbnail-status'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(thumbnail_store().status(), head=head)
```

Вызовы ветки: `thumbnail_store().status`, `thumbnail_store`.

## GET / HEAD /api/thumbnail

[server.py:1639](../../server.py#L1639) · `handle_get`.

Условие: `parsed.path in {'/api/thumbnail', '/api/thumbnail-cover'}`.

Ключи query, читаемые в ветке: `v`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'state': 'pending'}, 202, head=head)
```

Вызовы ветки: `thumbnail_store().cover`, `thumbnail_store`, `thumbnail_store().image`, `self.send_response`, `self.send_header`, `self.end_headers`, `str`, `self.wfile.write`, `len`.

## GET / HEAD /api/thumbnail-cover

[server.py:1639](../../server.py#L1639) · `handle_get`.

Условие: `parsed.path in {'/api/thumbnail', '/api/thumbnail-cover'}`.

Ключи query, читаемые в ветке: `v`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'state': 'pending'}, 202, head=head)
```

Вызовы ветки: `thumbnail_store().cover`, `thumbnail_store`, `thumbnail_store().image`, `self.send_response`, `self.send_header`, `self.end_headers`, `str`, `self.wfile.write`, `len`.

## GET / HEAD /api/invoices

[server.py:1655](../../server.py#L1655) · `handle_get`.

Условие: `parsed.path == '/api/invoices'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'items': service.with_links(invoice_store().list(relative)), 'trash': service.with_links(invoice_store().list(relative, trashed=True))}, head=head)
```

Вызовы ветки: `reconciliations.Reconciliations`, `order_store`, `service.with_links`, `invoice_store().list`, `invoice_store`.

## GET / HEAD /api/reconciliations

[server.py:1658](../../server.py#L1658) · `handle_get`.

Условие: `parsed.path == '/api/reconciliations'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'items': reconciliations.Reconciliations(order_store()).catalog()}, head=head)
```

Вызовы ветки: `reconciliations.Reconciliations(order_store()).catalog`, `reconciliations.Reconciliations`, `order_store`.

## GET / HEAD /api/reconciliation

[server.py:1660](../../server.py#L1660) · `handle_get`.

Условие: `parsed.path == '/api/reconciliation'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(reconciliations.Reconciliations(order_store()).get(relative), head=head)
```

Вызовы ветки: `reconciliations.Reconciliations(order_store()).get`, `reconciliations.Reconciliations`, `order_store`.

## GET / HEAD /api/invoice-folder-candidates

[server.py:1662](../../server.py#L1662) · `handle_get`.

Условие: `parsed.path == '/api/invoice-folder-candidates'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_discovery.candidates(invoice_store(), relative), head=head)
```

Вызовы ветки: `invoice_discovery.candidates`, `invoice_store`.

## GET / HEAD /api/invoice

[server.py:1664](../../server.py#L1664) · `handle_get`.

Условие: `parsed.path == '/api/invoice'`.

Ключи query, читаемые в ветке: `id`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(reconciliations.Reconciliations(order_store()).with_links([item])[0], head=head)
```

Вызовы ветки: `invoice_store().get`, `invoice_store`, `reconciliations.Reconciliations(order_store()).with_links`, `reconciliations.Reconciliations`, `order_store`.

## GET / HEAD /api/invoice-document

[server.py:1667](../../server.py#L1667) · `handle_get`.

Условие: `parsed.path == '/api/invoice-document'`.

Ключи query, читаемые в ветке: `document_id`, `download`, `id`.

Вызовы ветки: `invoice_documents.content`, `invoice_store`, `self.send_invoice_document`.

## GET / HEAD /api/invoice-plan-source

[server.py:1670](../../server.py#L1670) · `handle_get`.

Условие: `parsed.path == '/api/invoice-plan-source'`.

Ключи query, читаемые в ветке: `id`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_store().plan_source(relative, query.get('id', [''])[0]), head=head)
```

Вызовы ветки: `invoice_store().plan_source`, `invoice_store`.

## GET / HEAD /api/invoice-pdf-info

[server.py:1672](../../server.py#L1672) · `handle_get`.

Условие: `parsed.path in {'/api/invoice-pdf-info', '/api/invoice-pdf-page'}`.

Ключи query, читаемые в ветке: `id`, `page`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(pdf_info(target), head=head)
```

Вызовы ветки: `invoice_pdf_target`, `self.send_file`, `pdf_info`, `pdf_page`, `int`.

## GET / HEAD /api/invoice-pdf-page

[server.py:1672](../../server.py#L1672) · `handle_get`.

Условие: `parsed.path in {'/api/invoice-pdf-info', '/api/invoice-pdf-page'}`.

Ключи query, читаемые в ветке: `id`, `page`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(pdf_info(target), head=head)
```

Вызовы ветки: `invoice_pdf_target`, `self.send_file`, `pdf_info`, `pdf_page`, `int`.

## GET / HEAD /api/invoice-pdf

[server.py:1678](../../server.py#L1678) · `handle_get`.

Условие: `parsed.path in {'/api/invoice-pdf', '/api/invoice-preview'}`.

Ключи query, читаемые в ветке: `download`, `id`.

Вызовы ветки: `invoice_store().pdf`, `invoice_store().preview`, `invoice_store`, `self.send_invoice_pdf`.

## GET / HEAD /api/invoice-preview

[server.py:1678](../../server.py#L1678) · `handle_get`.

Условие: `parsed.path in {'/api/invoice-pdf', '/api/invoice-preview'}`.

Ключи query, читаемые в ветке: `download`, `id`.

Вызовы ветки: `invoice_store().pdf`, `invoice_store().preview`, `invoice_store`, `self.send_invoice_pdf`.

## GET / HEAD /api/client-activity

[server.py:1685](../../server.py#L1685) · `handle_get`.

Условие: `parsed.path in {'/api/client-activity', '/api/object-activity'}`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record, head=head)
```

Вызовы ветки: `object_activity_store`, `client_activity_store`, `activity.get`, `FileNotFoundError`.

## GET / HEAD /api/object-activity

[server.py:1685](../../server.py#L1685) · `handle_get`.

Условие: `parsed.path in {'/api/client-activity', '/api/object-activity'}`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record, head=head)
```

Вызовы ветки: `object_activity_store`, `client_activity_store`, `activity.get`, `FileNotFoundError`.

## GET / HEAD /api/mobile-status

[server.py:1691](../../server.py#L1691) · `handle_get`.

Условие: `parsed.path == '/api/mobile-status'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(MobileBridge(order_store()).status(), head=head)
```

Вызовы ветки: `MobileBridge(order_store()).status`, `MobileBridge`, `order_store`.

## GET / HEAD /api/calendar-event

[server.py:1693](../../server.py#L1693) · `handle_get`.

Условие: `parsed.path == '/api/calendar-event'`.

Ключи query, читаемые в ветке: `id`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(calendar_events.CalendarEvents(order_store()).get(query.get('id', [''])[0]), head=head)
```

Вызовы ветки: `calendar_events.CalendarEvents(order_store()).get`, `calendar_events.CalendarEvents`, `order_store`.

## GET / HEAD /api/folder-note

[server.py:1695](../../server.py#L1695) · `handle_get`.

Условие: `parsed.path == '/api/folder-note'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record, head=head)
```

Вызовы ветки: `folder_note_store().get`, `folder_note_store`, `FileNotFoundError`.

## GET / HEAD /api/event-relevance

[server.py:1700](../../server.py#L1700) · `handle_get`.

Условие: `parsed.path == '/api/event-relevance'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(folder_note_store().event_relevances(relative), head=head)
```

Вызовы ветки: `folder_note_store().event_relevances`, `folder_note_store`.

## GET / HEAD /api/sketch-relevance

[server.py:1702](../../server.py#L1702) · `handle_get`.

Условие: `parsed.path == '/api/sketch-relevance'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(folder_note_store().sketch_relevances(relative), head=head)
```

Вызовы ветки: `folder_note_store().sketch_relevances`, `folder_note_store`.

## GET / HEAD /api/sketch-preview

[server.py:1704](../../server.py#L1704) · `handle_get`.

Условие: `parsed.path == '/api/sketch-preview'`.

Вызовы ветки: `sketch_target`, `sketches.preview`, `self.send_file`.

## GET / HEAD /api/freza-preview

[server.py:1708](../../server.py#L1708) · `handle_get`.

Условие: `parsed.path == '/api/freza-preview'`.

Вызовы ветки: `freza_preview_target`, `sketches.preview`, `image_preview`, `target.suffix.lower`, `self.send_file`.

## GET / HEAD /api/event-folders

[server.py:1712](../../server.py#L1712) · `handle_get`.

Условие: `parsed.path == '/api/event-folders'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(event_folders.preview(DATA_ROOT, relative, folder_note_store()), head=head)
```

Вызовы ветки: `event_folders.preview`, `folder_note_store`.

## GET / HEAD /api/folder-rename

[server.py:1714](../../server.py#L1714) · `handle_get`.

Условие: `parsed.path == '/api/folder-rename'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(folder_rename.preview(order_store(), relative), head=head)
```

Вызовы ветки: `folder_rename.preview`, `order_store`.

## GET / HEAD /api/object-years

[server.py:1716](../../server.py#L1716) · `handle_get`.

Условие: `parsed.path == '/api/object-years'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(object_years.preview(order_store(), relative), head=head)
```

Вызовы ветки: `object_years.preview`, `order_store`.

## GET / HEAD /api/order

[server.py:1718](../../server.py#L1718) · `handle_get`.

Условие: `parsed.path == '/api/order'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record, head=head)
```

Вызовы ветки: `order_store().get`, `order_store`, `FileNotFoundError`.

## GET / HEAD /api/order-todos

[server.py:1723](../../server.py#L1723) · `handle_get`.

Условие: `parsed.path == '/api/order-todos'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(OrderTodos(order_store()).in_order(relative), head=head)
```

Вызовы ветки: `OrderTodos(order_store()).in_order`, `OrderTodos`, `order_store`.

## GET / HEAD /api/order-links

[server.py:1725](../../server.py#L1725) · `handle_get`.

Условие: `parsed.path == '/api/order-links'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(OrderLinks(order_store()).read(relative), head=head)
```

Вызовы ветки: `OrderLinks(order_store()).read`, `OrderLinks`, `order_store`.

## GET / HEAD /api/work-order-links

[server.py:1727](../../server.py#L1727) · `handle_get`.

Условие: `parsed.path == '/api/work-order-links'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(order_store().work_links(relative), head=head)
```

Вызовы ветки: `order_store().work_links`, `order_store`.

## GET / HEAD /api/tree

[server.py:1729](../../server.py#L1729) · `handle_get`.

Условие: `parsed.path == '/api/tree'`.

Ключи query, читаемые в ветке: `q`, `show_inactive`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(read_tree(relative, query.get('q', [''])[0], query.get('show_inactive', [''])[0] == '1'), head=head)
```

Вызовы ветки: `read_tree`.

## GET / HEAD /api/folder

[server.py:1731](../../server.py#L1731) · `handle_get`.

Условие: `parsed.path == '/api/folder'`.

Ключи query, читаемые в ветке: `show_inactive`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(read_folder(relative, query.get('show_inactive', [''])[0] == '1'), head=head)
```

Вызовы ветки: `read_folder`.

## GET / HEAD /api/print-task

[server.py:1733](../../server.py#L1733) · `handle_get`.

Условие: `parsed.path == '/api/print-task'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(read_print_task(relative), head=head)
```

Вызовы ветки: `read_print_task`.

## GET / HEAD /api/file-comment

[server.py:1735](../../server.py#L1735) · `handle_get`.

Условие: `parsed.path == '/api/file-comment'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'path': relative, 'comment_key': file_comments.binding(target), **read_file_comment(target)}, head=head)
```

Вызовы ветки: `comment_file`, `file_comments.binding`, `read_file_comment`.

## GET / HEAD /api/file

[server.py:1739](../../server.py#L1739) · `handle_get`.

Условие: `parsed.path in {'/api/file', '/api/preview', '/api/text', '/api/pdf', '/api/pdf-page', '/api/spreadsheet'}`.

Ключи query, читаемые в ветке: `download`, `page`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(pdf_info(target), head=head)
self.send_json({'text': body[:128 * 1024].decode('utf-8', errors='replace'), 'truncated': len(body) > 128 * 1024}, head=head)
```

Вызовы ветки: `safe_path`, `target.is_file`, `FileNotFoundError`, `spreadsheet_preview.read_bytes`, `self.send_response`, `self.send_header`, `self.end_headers`, `str`, `self.wfile.write`, `len`, `pdf_info`, `self.send_file`, `pdf_page`, `int`, `target.suffix.lower`, `ValueError`, `target.open`, `stream.read`, `image_preview`, `body[:128 * 1024].decode`, `preview_kind`.

## GET / HEAD /api/pdf

[server.py:1739](../../server.py#L1739) · `handle_get`.

Условие: `parsed.path in {'/api/file', '/api/preview', '/api/text', '/api/pdf', '/api/pdf-page', '/api/spreadsheet'}`.

Ключи query, читаемые в ветке: `download`, `page`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(pdf_info(target), head=head)
self.send_json({'text': body[:128 * 1024].decode('utf-8', errors='replace'), 'truncated': len(body) > 128 * 1024}, head=head)
```

Вызовы ветки: `safe_path`, `target.is_file`, `FileNotFoundError`, `spreadsheet_preview.read_bytes`, `self.send_response`, `self.send_header`, `self.end_headers`, `str`, `self.wfile.write`, `len`, `pdf_info`, `self.send_file`, `pdf_page`, `int`, `target.suffix.lower`, `ValueError`, `target.open`, `stream.read`, `image_preview`, `body[:128 * 1024].decode`, `preview_kind`.

## GET / HEAD /api/pdf-page

[server.py:1739](../../server.py#L1739) · `handle_get`.

Условие: `parsed.path in {'/api/file', '/api/preview', '/api/text', '/api/pdf', '/api/pdf-page', '/api/spreadsheet'}`.

Ключи query, читаемые в ветке: `download`, `page`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(pdf_info(target), head=head)
self.send_json({'text': body[:128 * 1024].decode('utf-8', errors='replace'), 'truncated': len(body) > 128 * 1024}, head=head)
```

Вызовы ветки: `safe_path`, `target.is_file`, `FileNotFoundError`, `spreadsheet_preview.read_bytes`, `self.send_response`, `self.send_header`, `self.end_headers`, `str`, `self.wfile.write`, `len`, `pdf_info`, `self.send_file`, `pdf_page`, `int`, `target.suffix.lower`, `ValueError`, `target.open`, `stream.read`, `image_preview`, `body[:128 * 1024].decode`, `preview_kind`.

## GET / HEAD /api/preview

[server.py:1739](../../server.py#L1739) · `handle_get`.

Условие: `parsed.path in {'/api/file', '/api/preview', '/api/text', '/api/pdf', '/api/pdf-page', '/api/spreadsheet'}`.

Ключи query, читаемые в ветке: `download`, `page`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(pdf_info(target), head=head)
self.send_json({'text': body[:128 * 1024].decode('utf-8', errors='replace'), 'truncated': len(body) > 128 * 1024}, head=head)
```

Вызовы ветки: `safe_path`, `target.is_file`, `FileNotFoundError`, `spreadsheet_preview.read_bytes`, `self.send_response`, `self.send_header`, `self.end_headers`, `str`, `self.wfile.write`, `len`, `pdf_info`, `self.send_file`, `pdf_page`, `int`, `target.suffix.lower`, `ValueError`, `target.open`, `stream.read`, `image_preview`, `body[:128 * 1024].decode`, `preview_kind`.

## GET / HEAD /api/spreadsheet

[server.py:1739](../../server.py#L1739) · `handle_get`.

Условие: `parsed.path in {'/api/file', '/api/preview', '/api/text', '/api/pdf', '/api/pdf-page', '/api/spreadsheet'}`.

Ключи query, читаемые в ветке: `download`, `page`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(pdf_info(target), head=head)
self.send_json({'text': body[:128 * 1024].decode('utf-8', errors='replace'), 'truncated': len(body) > 128 * 1024}, head=head)
```

Вызовы ветки: `safe_path`, `target.is_file`, `FileNotFoundError`, `spreadsheet_preview.read_bytes`, `self.send_response`, `self.send_header`, `self.end_headers`, `str`, `self.wfile.write`, `len`, `pdf_info`, `self.send_file`, `pdf_page`, `int`, `target.suffix.lower`, `ValueError`, `target.open`, `stream.read`, `image_preview`, `body[:128 * 1024].decode`, `preview_kind`.

## GET / HEAD /api/text

[server.py:1739](../../server.py#L1739) · `handle_get`.

Условие: `parsed.path in {'/api/file', '/api/preview', '/api/text', '/api/pdf', '/api/pdf-page', '/api/spreadsheet'}`.

Ключи query, читаемые в ветке: `download`, `page`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(pdf_info(target), head=head)
self.send_json({'text': body[:128 * 1024].decode('utf-8', errors='replace'), 'truncated': len(body) > 128 * 1024}, head=head)
```

Вызовы ветки: `safe_path`, `target.is_file`, `FileNotFoundError`, `spreadsheet_preview.read_bytes`, `self.send_response`, `self.send_header`, `self.end_headers`, `str`, `self.wfile.write`, `len`, `pdf_info`, `self.send_file`, `pdf_page`, `int`, `target.suffix.lower`, `ValueError`, `target.open`, `stream.read`, `image_preview`, `body[:128 * 1024].decode`, `preview_kind`.

## POST /api/calendar-telegram-settings

[server.py:1947](../../server.py#L1947) · `do_POST`.

Условие: `urllib.parse.urlsplit(self.path).path == '/api/calendar-telegram-settings'`.

Вызовы ветки: `self.receive_telegram_settings`.

## POST /api/calendar-telegram

[server.py:1950](../../server.py#L1950) · `do_POST`.

Условие: `urllib.parse.urlsplit(self.path).path == '/api/calendar-telegram'`.

Вызовы ветки: `self.receive_calendar_telegram`.

## POST /api/file-upload

[server.py:1953](../../server.py#L1953) · `do_POST`.

Условие: `urllib.parse.urlsplit(self.path).path == '/api/file-upload'`.

Вызовы ветки: `self.receive_upload`.

## POST /api/invoice-document-upload

[server.py:1958](../../server.py#L1958) · `do_POST`.

Условие: `route in {'/api/invoice-upload', '/api/invoice-document-upload', '/api/invoice-folder-attach'}`.

Вызовы ветки: `self.headers.get`, `ValueError`, `self.headers.get_content_type`, `urllib.parse.urlsplit`.

## POST /api/invoice-folder-attach

[server.py:1958](../../server.py#L1958) · `do_POST`.

Условие: `route in {'/api/invoice-upload', '/api/invoice-document-upload', '/api/invoice-folder-attach'}`.

Вызовы ветки: `self.headers.get`, `ValueError`, `self.headers.get_content_type`, `urllib.parse.urlsplit`.

## POST /api/invoice-upload

[server.py:1958](../../server.py#L1958) · `do_POST`.

Условие: `route in {'/api/invoice-upload', '/api/invoice-document-upload', '/api/invoice-folder-attach'}`.

Вызовы ветки: `self.headers.get`, `ValueError`, `self.headers.get_content_type`, `urllib.parse.urlsplit`.

## POST /api/invoice-reconciliation

[server.py:1969](../../server.py#L1969) · `do_POST`.

Условие: `route in {'/api/reconciliation-save', '/api/invoice-reconciliation'}`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'error': 'Изменяй сверки через страницу менеджера'}, 403)
self.send_json(service.save(payload) if route.endswith('-save') else service.assign(invoice_store(), payload))
```

Вызовы ветки: `self.headers.get`, `self.headers.get_content_type`, `urllib.parse.urlsplit`, `reconciliations.Reconciliations`, `order_store`, `route.endswith`, `service.save`, `service.assign`, `invoice_store`.

## POST /api/reconciliation-save

[server.py:1969](../../server.py#L1969) · `do_POST`.

Условие: `route in {'/api/reconciliation-save', '/api/invoice-reconciliation'}`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'error': 'Изменяй сверки через страницу менеджера'}, 403)
self.send_json(service.save(payload) if route.endswith('-save') else service.assign(invoice_store(), payload))
```

Вызовы ветки: `self.headers.get`, `self.headers.get_content_type`, `urllib.parse.urlsplit`, `reconciliations.Reconciliations`, `order_store`, `route.endswith`, `service.save`, `service.assign`, `invoice_store`.

## POST /api/folder-note-save

[server.py:1979](../../server.py#L1979) · `do_POST`.

Условие: `in_reconciliations(reconciliation_path, legacy=True) and (route.startswith('/api/order-') and route != '/api/order-folder-create' or (route in {'/api/folder-note-save', '/api/status', '/api/note'} and len(Path(reconciliation_path).parts) == 3))`.

Вызовы ветки: `ValueError`.

## POST /api/note

[server.py:1979](../../server.py#L1979) · `do_POST`.

Условие: `in_reconciliations(reconciliation_path, legacy=True) and (route.startswith('/api/order-') and route != '/api/order-folder-create' or (route in {'/api/folder-note-save', '/api/status', '/api/note'} and len(Path(reconciliation_path).parts) == 3))`.

Вызовы ветки: `ValueError`.

## POST /api/order-

[server.py:1979](../../server.py#L1979) · `do_POST`.

Условие: `in_reconciliations(reconciliation_path, legacy=True) and (route.startswith('/api/order-') and route != '/api/order-folder-create' or (route in {'/api/folder-note-save', '/api/status', '/api/note'} and len(Path(reconciliation_path).parts) == 3))`.

Вызовы ветки: `ValueError`.

## POST /api/order-folder-create

[server.py:1979](../../server.py#L1979) · `do_POST`.

Условие: `in_reconciliations(reconciliation_path, legacy=True) and (route.startswith('/api/order-') and route != '/api/order-folder-create' or (route in {'/api/folder-note-save', '/api/status', '/api/note'} and len(Path(reconciliation_path).parts) == 3))`.

Вызовы ветки: `ValueError`.

## POST /api/status

[server.py:1979](../../server.py#L1979) · `do_POST`.

Условие: `in_reconciliations(reconciliation_path, legacy=True) and (route.startswith('/api/order-') and route != '/api/order-folder-create' or (route in {'/api/folder-note-save', '/api/status', '/api/note'} and len(Path(reconciliation_path).parts) == 3))`.

Вызовы ветки: `ValueError`.

## POST /api/inbox-complete

[server.py:1983](../../server.py#L1983) · `do_POST`.

Условие: `route in {'/api/inbox-complete', '/api/inbox-remove', '/api/inbox-restore'}`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'error': 'Изменяй задачи через Inbox менеджера'}, 403)
self.send_json(result)
```

Вызовы ветки: `self.headers.get`, `self.headers.get_content_type`, `urllib.parse.urlsplit`, `telegram_inbox.complete`, `telegram_inbox.set_deleted`, `order_store`.

## POST /api/inbox-remove

[server.py:1983](../../server.py#L1983) · `do_POST`.

Условие: `route in {'/api/inbox-complete', '/api/inbox-remove', '/api/inbox-restore'}`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'error': 'Изменяй задачи через Inbox менеджера'}, 403)
self.send_json(result)
```

Вызовы ветки: `self.headers.get`, `self.headers.get_content_type`, `urllib.parse.urlsplit`, `telegram_inbox.complete`, `telegram_inbox.set_deleted`, `order_store`.

## POST /api/inbox-restore

[server.py:1983](../../server.py#L1983) · `do_POST`.

Условие: `route in {'/api/inbox-complete', '/api/inbox-remove', '/api/inbox-restore'}`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'error': 'Изменяй задачи через Inbox менеджера'}, 403)
self.send_json(result)
```

Вызовы ветки: `self.headers.get`, `self.headers.get_content_type`, `urllib.parse.urlsplit`, `telegram_inbox.complete`, `telegram_inbox.set_deleted`, `order_store`.

## POST /api/thumbnails

[server.py:1993](../../server.py#L1993) · `do_POST`.

Условие: `route == '/api/thumbnails'`.

Ключи payload, читаемые в ветке: `folders`, `paths`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'items': thumbnail_store().items(payload.get('paths', [])), 'covers': {path: thumbnail_store().cover(path) for path in folders}})
```

Вызовы ветки: `ValueError`, `isinstance`, `len`, `thumbnail_store().items`, `thumbnail_store().cover`, `thumbnail_store`.

## POST /api/invoice-create

[server.py:2000](../../server.py#L2000) · `do_POST`.

Условие: `route == '/api/invoice-create'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_store().create(payload), 201)
```

Вызовы ветки: `invoice_store().create`, `invoice_store`.

## POST /api/invoice-plan

[server.py:2003](../../server.py#L2003) · `do_POST`.

Условие: `route == '/api/invoice-plan'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_store().plan(payload), 200 if 'revision' in payload else 201)
```

Вызовы ветки: `invoice_store().plan`, `invoice_store`.

## POST /api/invoice-plan-calendar-move

[server.py:2006](../../server.py#L2006) · `do_POST`.

Условие: `route == '/api/invoice-plan-calendar-move'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_store().move_calendar_plan(payload))
```

Вызовы ветки: `invoice_store().move_calendar_plan`, `invoice_store`.

## POST /api/calendar-payment-remove

[server.py:2009](../../server.py#L2009) · `do_POST`.

Условие: `route == '/api/calendar-payment-remove'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_store().remove(payload, calendar_only=True))
```

Вызовы ветки: `invoice_store().remove`, `invoice_store`.

## POST /api/calendar-payment-restore

[server.py:2012](../../server.py#L2012) · `do_POST`.

Условие: `route == '/api/calendar-payment-restore'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_store().restore(payload, calendar_only=True))
```

Вызовы ветки: `invoice_store().restore`, `invoice_store`.

## POST /api/invoice-document-remove

[server.py:2026](../../server.py#L2026) · `do_POST`.

Условие: `route in {'/api/invoice-document-remove', '/api/invoice-document-restore'}`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_documents.set_deleted(invoice_store(), payload, route.endswith('-remove')))
```

Вызовы ветки: `invoice_documents.set_deleted`, `invoice_store`, `route.endswith`, `schedule_order_sync`.

## POST /api/invoice-document-restore

[server.py:2026](../../server.py#L2026) · `do_POST`.

Условие: `route in {'/api/invoice-document-remove', '/api/invoice-document-restore'}`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_documents.set_deleted(invoice_store(), payload, route.endswith('-remove')))
```

Вызовы ветки: `invoice_documents.set_deleted`, `invoice_store`, `route.endswith`, `schedule_order_sync`.

## POST /api/invoice-comment

[server.py:2030](../../server.py#L2030) · `do_POST`.

Условие: `route == '/api/invoice-comment'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_store().save_comment(payload))
```

Вызовы ветки: `invoice_store().save_comment`, `invoice_store`.

## POST /api/invoice-list-status

[server.py:2033](../../server.py#L2033) · `do_POST`.

Условие: `route == '/api/invoice-list-status'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_store().save_list_status(payload))
```

Вызовы ветки: `invoice_store().save_list_status`, `invoice_store`.

## POST /api/invoice-remove

[server.py:2036](../../server.py#L2036) · `do_POST`.

Условие: `route == '/api/invoice-remove'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_store().remove(payload))
```

Вызовы ветки: `invoice_store().remove`, `invoice_store`, `schedule_order_sync`.

## POST /api/invoice-restore

[server.py:2040](../../server.py#L2040) · `do_POST`.

Условие: `route == '/api/invoice-restore'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_store().restore(payload))
```

Вызовы ветки: `invoice_store().restore`, `invoice_store`, `schedule_order_sync`.

## POST /api/invoice-save

[server.py:2044](../../server.py#L2044) · `do_POST`.

Условие: `route == '/api/invoice-save'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_store().save(payload))
```

Вызовы ветки: `invoice_store().save`, `invoice_store`.

## POST /api/invoice-issue

[server.py:2047](../../server.py#L2047) · `do_POST`.

Условие: `route == '/api/invoice-issue'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record)
```

Вызовы ветки: `invoice_store().issue`, `invoice_store`, `schedule_order_sync`.

## POST /api/object-folder-create

[server.py:2063](../../server.py#L2063) · `do_POST`.

Условие: `route == '/api/object-folder-create'`.

Ключи payload, читаемые в ветке: `path`, `title`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(order_folders.create_object(DATA_ROOT, payload.get('path'), payload.get('title')), 201)
```

Вызовы ветки: `guard_database`, `order_store`, `order_folders.create_object`.

## POST /api/object-years

[server.py:2067](../../server.py#L2067) · `do_POST`.

Условие: `route == '/api/object-years'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(result)
```

Вызовы ветки: `object_years.group`, `order_store`, `schedule_order_sync`, `schedule_todo_refresh`.

## POST /api/event-folder-create

[server.py:2074](../../server.py#L2074) · `do_POST`.

Условие: `route == '/api/event-folder-create'`.

Ключи payload, читаемые в ветке: `path`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(event_folders.create(DATA_ROOT, payload, folder_note_store()), 201)
```

Вызовы ветки: `guard_database`, `order_store`, `event_folders.create`, `folder_note_store`.

## POST /api/folder-rename

[server.py:2078](../../server.py#L2078) · `do_POST`.

Условие: `route == '/api/folder-rename'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(result)
```

Вызовы ветки: `folder_rename.rename`, `order_store`, `schedule_order_sync`, `schedule_todo_refresh`.

## POST /api/event-folders-rename

[server.py:2085](../../server.py#L2085) · `do_POST`.

Условие: `route == '/api/event-folders-rename'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(event_folders.rename(folder_note_store(), payload))
```

Вызовы ветки: `event_folders.rename`, `folder_note_store`, `schedule_todo_refresh`.

## POST /api/event-relevance

[server.py:2095](../../server.py#L2095) · `do_POST`.

Условие: `route == '/api/event-relevance'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(event_relevance.info(record))
```

Вызовы ветки: `folder_note_store().save_relevance`, `folder_note_store`, `schedule_order_sync`, `event_relevance.info`.

## POST /api/sketch-relevance

[server.py:2100](../../server.py#L2100) · `do_POST`.

Условие: `route == '/api/sketch-relevance'`.

Ключи payload, читаемые в ветке: `key`, `path`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'path': payload['path'], 'key': payload['key'], 'folder': record['path'], 'status': sketches.group_info(record)})
```

Вызовы ветки: `folder_note_store().save_sketch_relevance`, `folder_note_store`, `schedule_order_sync`, `sketches.group_info`.

## POST /api/sketch-open

[server.py:2105](../../server.py#L2105) · `do_POST`.

Условие: `route == '/api/sketch-open'`.

Ключи payload, читаемые в ветке: `key`, `path`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'ok': True})
```

Вызовы ветки: `isinstance`, `ValueError`, `sketch_target`, `sketches.open_corel`.

## POST /api/order-add

[server.py:2113](../../server.py#L2113) · `do_POST`.

Условие: `route == '/api/order-add'`.

Ключи payload, читаемые в ветке: `path`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(store.get(relative), 201)
```

Вызовы ветки: `editable_status_folder`, `relative_path`, `order_store`, `store.path`, `store.require_order_folder`, `order_creation.retry_one`, `store.get`, `folder_status`, `store.import_folder`, `directory_children`, `schedule_order_sync`, `schedule_todo_refresh`.

## POST /api/mobile-sync

[server.py:2128](../../server.py#L2128) · `do_POST`.

Условие: `route == '/api/mobile-sync'`.

Ключи payload, читаемые в ветке: `enabled`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(bridge.status(), 202)
```

Вызовы ветки: `MobileBridge`, `order_store`, `bridge.configure`, `schedule_mobile_sync`, `bridge.status`.

## POST /api/order-save

[server.py:2135](../../server.py#L2135) · `do_POST`.

Условие: `route == '/api/order-save'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record)
```

Вызовы ветки: `order_store().save`, `order_store`, `schedule_order_sync`.

## POST /api/supplier-purchase-done

[server.py:2140](../../server.py#L2140) · `do_POST`.

Условие: `route == '/api/supplier-purchase-done'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(supplier_purchases.SupplierPurchases(order_store()).save(payload, inactive=inactive_paths()))
```

Вызовы ветки: `supplier_purchases.SupplierPurchases(order_store()).save`, `supplier_purchases.SupplierPurchases`, `inactive_paths`, `order_store`, `schedule_order_sync`.

## POST /api/supplier-purchase-text

[server.py:2144](../../server.py#L2144) · `do_POST`.

Условие: `route == '/api/supplier-purchase-text'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'error': 'Изменяй закупки через страницу поставщика'}, 403)
self.send_json(supplier_purchases.SupplierPurchases(order_store()).edit(payload, inactive=inactive_paths()))
```

Вызовы ветки: `self.headers.get`, `self.headers.get_content_type`, `urllib.parse.urlsplit`, `supplier_purchases.SupplierPurchases(order_store()).edit`, `supplier_purchases.SupplierPurchases`, `inactive_paths`, `order_store`, `schedule_order_sync`.

## POST /api/order-favorite

[server.py:2153](../../server.py#L2153) · `do_POST`.

Условие: `route == '/api/order-favorite'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record)
```

Вызовы ветки: `order_store().save_favorite`, `order_store`, `schedule_order_sync`.

## POST /api/order-links

[server.py:2158](../../server.py#L2158) · `do_POST`.

Условие: `route == '/api/order-links'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(OrderLinks(order_store()).save(payload))
```

Вызовы ветки: `OrderLinks(order_store()).save`, `OrderLinks`, `order_store`, `schedule_order_sync`.

## POST /api/order-flag

[server.py:2162](../../server.py#L2162) · `do_POST`.

Условие: `route == '/api/order-flag'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record)
```

Вызовы ветки: `order_store().save_flag`, `order_store`, `schedule_order_sync`.

## POST /api/order-blue-plus

[server.py:2167](../../server.py#L2167) · `do_POST`.

Условие: `route == '/api/order-blue-plus'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record)
```

Вызовы ветки: `order_store().save_blue_plus`, `order_store`, `schedule_order_sync`.

## POST /api/order-dollar

[server.py:2172](../../server.py#L2172) · `do_POST`.

Условие: `route == '/api/order-dollar'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record)
```

Вызовы ветки: `order_store().save_dollar`, `order_store`, `schedule_order_sync`.

## POST /api/order-status

[server.py:2177](../../server.py#L2177) · `do_POST`.

Условие: `route == '/api/order-status'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record)
```

Вызовы ветки: `order_store().save_status`, `order_store`, `schedule_order_sync`.

## POST /api/order-supplier-status

[server.py:2182](../../server.py#L2182) · `do_POST`.

Условие: `route == '/api/order-supplier-status'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record)
```

Вызовы ветки: `order_store().save_supplier_status`, `order_store`, `schedule_order_sync`.

## POST /api/order-deadline-week

[server.py:2187](../../server.py#L2187) · `do_POST`.

Условие: `route == '/api/order-deadline-week'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record)
```

Вызовы ветки: `order_store().save_deadline_week`, `order_store`, `schedule_order_sync`.

## POST /api/order-calendar-compact

[server.py:2192](../../server.py#L2192) · `do_POST`.

Условие: `route == '/api/order-calendar-compact'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(order_store().save_calendar_compact(payload))
```

Вызовы ветки: `order_store().save_calendar_compact`, `order_store`, `schedule_order_sync`.

## POST /api/order-deadline-comment

[server.py:2196](../../server.py#L2196) · `do_POST`.

Условие: `route == '/api/order-deadline-comment'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record)
```

Вызовы ветки: `order_store().save_deadline_comment`, `order_store`, `schedule_order_sync`.

## POST /api/calendar-event

[server.py:2201](../../server.py#L2201) · `do_POST`.

Условие: `route == '/api/calendar-event'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(calendar_events.CalendarEvents(order_store()).save(payload))
```

Вызовы ветки: `calendar_events.CalendarEvents(order_store()).save`, `calendar_events.CalendarEvents`, `order_store`.

## POST /api/calendar-event-remove

[server.py:2204](../../server.py#L2204) · `do_POST`.

Условие: `route in ('/api/calendar-event-remove', '/api/calendar-event-restore')`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(calendar_events.CalendarEvents(order_store()).set_deleted(payload, route.endswith('-remove')))
```

Вызовы ветки: `calendar_events.CalendarEvents(order_store()).set_deleted`, `route.endswith`, `calendar_events.CalendarEvents`, `order_store`.

## POST /api/calendar-event-restore

[server.py:2204](../../server.py#L2204) · `do_POST`.

Условие: `route in ('/api/calendar-event-remove', '/api/calendar-event-restore')`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(calendar_events.CalendarEvents(order_store()).set_deleted(payload, route.endswith('-remove')))
```

Вызовы ветки: `calendar_events.CalendarEvents(order_store()).set_deleted`, `route.endswith`, `calendar_events.CalendarEvents`, `order_store`.

## POST /api/order-calendar-event-remove

[server.py:2207](../../server.py#L2207) · `do_POST`.

Условие: `route in ('/api/order-calendar-event-remove', '/api/order-calendar-event-restore')`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(operation(payload))
```

Вызовы ветки: `route.endswith`, `order_store`, `operation`.

## POST /api/order-calendar-event-restore

[server.py:2207](../../server.py#L2207) · `do_POST`.

Условие: `route in ('/api/order-calendar-event-remove', '/api/order-calendar-event-restore')`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(operation(payload))
```

Вызовы ветки: `route.endswith`, `order_store`, `operation`.

## POST /api/calendar-color

[server.py:2211](../../server.py#L2211) · `do_POST`.

Условие: `route == '/api/calendar-color'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(calendar_events.CalendarEvents(order_store()).color(payload))
```

Вызовы ветки: `calendar_events.CalendarEvents(order_store()).color`, `calendar_events.CalendarEvents`, `order_store`.

## POST /api/order-calendar-color

[server.py:2214](../../server.py#L2214) · `do_POST`.

Условие: `route == '/api/order-calendar-color'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(order_store().save_calendar_color(payload))
```

Вызовы ветки: `order_store().save_calendar_color`, `order_store`.

## POST /api/calendar-move

[server.py:2217](../../server.py#L2217) · `do_POST`.

Условие: `route == '/api/calendar-move'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(calendar_events.CalendarEvents(order_store()).move(payload))
```

Вызовы ветки: `calendar_events.CalendarEvents(order_store()).move`, `calendar_events.CalendarEvents`, `order_store`.

## POST /api/order-calendar-inactive

[server.py:2220](../../server.py#L2220) · `do_POST`.

Условие: `route == '/api/order-calendar-inactive'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(order_store().save_calendar_inactive(payload))
```

Вызовы ветки: `order_store().save_calendar_inactive`, `order_store`.

## POST /api/order-calendar-completed

[server.py:2223](../../server.py#L2223) · `do_POST`.

Условие: `route == '/api/order-calendar-completed'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(order_store().save_calendar_completed(payload))
```

Вызовы ветки: `order_store().save_calendar_completed`, `order_store`.

## POST /api/calendar-completed

[server.py:2226](../../server.py#L2226) · `do_POST`.

Условие: `route == '/api/calendar-completed'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(calendar_events.CalendarEvents(order_store()).set_completed(payload))
```

Вызовы ветки: `calendar_events.CalendarEvents(order_store()).set_completed`, `calendar_events.CalendarEvents`, `order_store`.

## POST /api/invoice-plan-calendar-completed

[server.py:2229](../../server.py#L2229) · `do_POST`.

Условие: `route == '/api/invoice-plan-calendar-completed'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_store().save_plan_calendar_completed(payload))
```

Вызовы ветки: `invoice_store().save_plan_calendar_completed`, `invoice_store`.

## POST /api/order-calendar-trip

[server.py:2232](../../server.py#L2232) · `do_POST`.

Условие: `route == '/api/order-calendar-trip'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(order_store().save_calendar_trip(payload))
```

Вызовы ветки: `order_store().save_calendar_trip`, `order_store`.

## POST /api/order-calendar-watch-todos

[server.py:2235](../../server.py#L2235) · `do_POST`.

Условие: `route == '/api/order-calendar-watch-todos'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(order_store().save_calendar_watch_todos(payload))
```

Вызовы ветки: `order_store().save_calendar_watch_todos`, `order_store`.

## POST /api/invoice-plan-calendar-watch-todos

[server.py:2238](../../server.py#L2238) · `do_POST`.

Условие: `route == '/api/invoice-plan-calendar-watch-todos'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_store().save_plan_calendar_watch_todos(payload))
```

Вызовы ветки: `invoice_store().save_plan_calendar_watch_todos`, `invoice_store`.

## POST /api/calendar-trip

[server.py:2241](../../server.py#L2241) · `do_POST`.

Условие: `route == '/api/calendar-trip'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(calendar_events.CalendarEvents(order_store()).set_trip(payload))
```

Вызовы ветки: `calendar_events.CalendarEvents(order_store()).set_trip`, `calendar_events.CalendarEvents`, `order_store`.

## POST /api/invoice-plan-calendar-trip

[server.py:2244](../../server.py#L2244) · `do_POST`.

Условие: `route == '/api/invoice-plan-calendar-trip'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_store().save_plan_calendar_trip(payload))
```

Вызовы ветки: `invoice_store().save_plan_calendar_trip`, `invoice_store`.

## POST /api/calendar-inactive

[server.py:2247](../../server.py#L2247) · `do_POST`.

Условие: `route == '/api/calendar-inactive'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(calendar_events.CalendarEvents(order_store()).set_inactive(payload))
```

Вызовы ветки: `calendar_events.CalendarEvents(order_store()).set_inactive`, `calendar_events.CalendarEvents`, `order_store`.

## POST /api/invoice-plan-calendar-inactive

[server.py:2250](../../server.py#L2250) · `do_POST`.

Условие: `route == '/api/invoice-plan-calendar-inactive'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_store().save_plan_calendar_inactive(payload))
```

Вызовы ветки: `invoice_store().save_plan_calendar_inactive`, `invoice_store`.

## POST /api/invoice-plan-calendar-carryover

[server.py:2253](../../server.py#L2253) · `do_POST`.

Условие: `route == '/api/invoice-plan-calendar-carryover'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(invoice_store().save_plan_calendar_carryover(payload))
```

Вызовы ветки: `invoice_store().save_plan_calendar_carryover`, `invoice_store`.

## POST /api/order-calendar-event

[server.py:2256](../../server.py#L2256) · `do_POST`.

Условие: `route == '/api/order-calendar-event'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record)
```

Вызовы ветки: `order_store().save_calendar_event`, `order_store`, `schedule_order_sync`.

## POST /api/order-calendar-move

[server.py:2261](../../server.py#L2261) · `do_POST`.

Условие: `route == '/api/order-calendar-move'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record)
```

Вызовы ветки: `order_store().move_calendar_event`, `order_store`, `schedule_order_sync`.

## POST /api/work-supplier-favorite

[server.py:2266](../../server.py#L2266) · `do_POST`.

Условие: `route == '/api/work-supplier-favorite'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(work_orders.save_supplier_favorite(order_store(), payload))
```

Вызовы ветки: `work_orders.save_supplier_favorite`, `order_store`.

## POST /api/work-order-links

[server.py:2269](../../server.py#L2269) · `do_POST`.

Условие: `route == '/api/work-order-links'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(order_store().save_work_links(payload))
```

Вызовы ветки: `order_store().save_work_links`, `order_store`, `schedule_order_sync`.

## POST /api/client-activity

[server.py:2273](../../server.py#L2273) · `do_POST`.

Условие: `route in {'/api/client-activity', '/api/client-activity-file', '/api/object-activity', '/api/object-activity-file'}`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record)
```

Вызовы ветки: `route.startswith`, `object_activity_store`, `client_activity_store`, `route.endswith`, `activity.accept_file`, `activity.save`, `schedule_order_sync`.

## POST /api/client-activity-file

[server.py:2273](../../server.py#L2273) · `do_POST`.

Условие: `route in {'/api/client-activity', '/api/client-activity-file', '/api/object-activity', '/api/object-activity-file'}`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record)
```

Вызовы ветки: `route.startswith`, `object_activity_store`, `client_activity_store`, `route.endswith`, `activity.accept_file`, `activity.save`, `schedule_order_sync`.

## POST /api/object-activity

[server.py:2273](../../server.py#L2273) · `do_POST`.

Условие: `route in {'/api/client-activity', '/api/client-activity-file', '/api/object-activity', '/api/object-activity-file'}`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record)
```

Вызовы ветки: `route.startswith`, `object_activity_store`, `client_activity_store`, `route.endswith`, `activity.accept_file`, `activity.save`, `schedule_order_sync`.

## POST /api/object-activity-file

[server.py:2273](../../server.py#L2273) · `do_POST`.

Условие: `route in {'/api/client-activity', '/api/client-activity-file', '/api/object-activity', '/api/object-activity-file'}`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record)
```

Вызовы ветки: `route.startswith`, `object_activity_store`, `client_activity_store`, `route.endswith`, `activity.accept_file`, `activity.save`, `schedule_order_sync`.

## POST /api/order-remove

[server.py:2279](../../server.py#L2279) · `do_POST`.

Условие: `route == '/api/order-remove'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(record)
```

Вызовы ветки: `order_store().remove`, `order_store`, `folder_note_store().get`, `folder_note_store`, `schedule_order_sync`.

## POST /api/orders-discover

[server.py:2286](../../server.py#L2286) · `do_POST`.

Условие: `route == '/api/orders-discover'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(discover_orders(), 202)
```

Вызовы ветки: `discover_orders`.

## POST /api/orders-sync

[server.py:2289](../../server.py#L2289) · `do_POST`.

Условие: `route == '/api/orders-sync'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'ok': True})
```

Вызовы ветки: `schedule_order_sync`, `METADATA_REFRESH.set`.

## POST /api/clients-refresh

[server.py:2295](../../server.py#L2295) · `do_POST`.

Условие: `route == '/api/clients-refresh'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'ok': True})
```

Вызовы ветки: `client_activity_store().refresh`, `client_activity_store`, `object_activity_store().refresh`, `object_activity_store`.

## POST /api/todos-refresh

[server.py:2300](../../server.py#L2300) · `do_POST`.

Условие: `route == '/api/todos-refresh'`.

Ключи payload, читаемые в ветке: `path`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'ok': True}, 202)
```

Вызовы ветки: `order_store().path`, `order_store`, `schedule_todo_refresh`.

## POST /api/print-create

[server.py:2307](../../server.py#L2307) · `do_POST`.

Условие: `route == '/api/print-create'`.

Ключи payload, читаемые в ветке: `description`, `link`, `path`, `title`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(create_print_task(payload.get('path', ''), payload.get('link', ''), payload.get('description', ''), payload.get('title', '')), 201)
```

Вызовы ветки: `create_print_task`.

## POST /api/print-save

[server.py:2310](../../server.py#L2310) · `do_POST`.

Условие: `route == '/api/print-save'`.

Ключи payload, читаемые в ветке: `description`, `link`, `path`, `revision`, `title`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(save_print_task(payload.get('path', ''), payload.get('link', ''), payload.get('description', ''), payload.get('revision'), payload.get('title')))
```

Вызовы ветки: `save_print_task`.

## POST /api/print-publish

[server.py:2313](../../server.py#L2313) · `do_POST`.

Условие: `route == '/api/print-publish'`.

Ключи payload, читаемые в ветке: `path`, `revision`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(result, 202)
```

Вызовы ветки: `read_print_task`, `metadata_store().publish`, `PrintConflict`, `compose_print_text(task['link'], task['description'], task['title']).encode`, `metadata_store`, `hashlib.sha256((task['path'] + task['revision']).encode()).hexdigest`, `Path`, `compose_print_text`, `datetime.now(ZoneInfo('Europe/Moscow')).strftime`, `hashlib.sha256`, `datetime.now`, `(task['path'] + task['revision']).encode`, `ZoneInfo`, `schedule_order_sync`.

## POST /api/file-comment

[server.py:2323](../../server.py#L2323) · `do_POST`.

Условие: `route == '/api/file-comment'`.

Ключи payload, читаемые в ветке: `comment`, `comment_key`, `path`, `revision`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'path': relative, 'comment_key': key, **record})
```

Вызовы ветки: `comment_file`, `file_comments.binding`, `FileCommentConflict`, `metadata_store().save_comment`, `file_comments.save`, `metadata_store`.

## POST /api/image-report

[server.py:2335](../../server.py#L2335) · `do_POST`.

Условие: `route == '/api/image-report'`.

Ключи payload, читаемые в ветке: `files`, `path`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(create_image_report(payload.get('path', ''), payload.get('files')), 201)
```

Вызовы ветки: `guard_database`, `order_store`, `create_image_report`.

## POST /api/files-trash-preview

[server.py:2339](../../server.py#L2339) · `do_POST`.

Условие: `route == '/api/files-trash-preview'`.

Ключи payload, читаемые в ветке: `files`, `path`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(file_trash.preview(DATA_ROOT, payload.get('path', ''), payload.get('files')))
```

Вызовы ветки: `file_trash.preview`.

## POST /api/event-trash-preview

[server.py:2342](../../server.py#L2342) · `do_POST`.

Условие: `route == '/api/event-trash-preview'`.

Ключи payload, читаемые в ветке: `path`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(event_trash.preview(order_store(), payload.get('path')))
```

Вызовы ветки: `event_trash.preview`, `order_store`.

## POST /api/event-trash

[server.py:2345](../../server.py#L2345) · `do_POST`.

Условие: `route == '/api/event-trash'`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(result)
```

Вызовы ветки: `event_trash.remove`, `order_store`, `schedule_todo_refresh`.

## POST /api/event-trash-restore

[server.py:2351](../../server.py#L2351) · `do_POST`.

Условие: `route == '/api/event-trash-restore'`.

Ключи payload, читаемые в ветке: `session`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(result)
```

Вызовы ветки: `event_trash.restore`, `order_store`, `schedule_order_sync`, `schedule_todo_refresh`.

## POST /api/files-trash

[server.py:2358](../../server.py#L2358) · `do_POST`.

Условие: `route == '/api/files-trash'`.

Ключи payload, читаемые в ветке: `confirmed`, `files`, `path`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(result)
```

Вызовы ветки: `guard_database`, `file_trash.remove`, `order_store`.

## POST /api/event-trash-list

[server.py:2364](../../server.py#L2364) · `do_POST`.

Условие: `route in {'/api/files-trash-list', '/api/event-trash-list'}`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'sessions': sessions, 'events': events, 'warning': warning})
```

Вызовы ветки: `event_trash.list_sessions`, `order_store`, `file_trash.list_sessions`, `errors.append`, `icloud_access.read_bytes`.

## POST /api/files-trash-list

[server.py:2364](../../server.py#L2364) · `do_POST`.

Условие: `route in {'/api/files-trash-list', '/api/event-trash-list'}`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json({'sessions': sessions, 'events': events, 'warning': warning})
```

Вызовы ветки: `event_trash.list_sessions`, `order_store`, `file_trash.list_sessions`, `errors.append`, `icloud_access.read_bytes`.

## POST /api/files-trash-restore

[server.py:2376](../../server.py#L2376) · `do_POST`.

Условие: `route == '/api/files-trash-restore'`.

Ключи payload, читаемые в ветке: `session`.

Выражения JSON-ответа (значения раскрываются в вызываемом методе):

```python
self.send_json(result)
```

Вызовы ветки: `guard_database`, `file_trash.restore`, `order_store`.

## POST /api/open

[server.py:2391](../../server.py#L2391) · `do_POST`.

Условие: `route == '/api/open'`.

Ключи payload, читаемые в ветке: `path`, `reveal`.

Вызовы ветки: `safe_path`, `target.exists`, `FileNotFoundError`, `subprocess.Popen`, `str`.

## GET / HEAD /_auth/session

[remote_access.py:319](../../remote_access.py#L319) · `get_remote`.

Условие: `route == '/_auth/session'`.

Вызовы ветки: `cookie`, `hmac.new(gate.key(document), ('logout:' + token).encode(), hashlib.sha256).hexdigest`, `hmac.new`, `gate.key`, `('logout:' + token).encode`, `self.reply`.

## POST /_auth/logout

[remote_access.py:361](../../remote_access.py#L361) · `do_POST`.

Условие: `route in {LOGIN_PATH, '/_auth/logout'}`.

Вызовы ветки: `self.headers.get_all`, `self.rfile.read(int(lengths[0])).decode`, `urllib.parse.parse_qs`, `any`, `self.headers.get`, `ValueError`, `fields.get`, `self.reply`, `len`, `re.fullmatch`, `int`, `self.headers.get_content_type`, `self.rfile.read`, `'Некорректная форма'.encode`, `fields.values`, `hmac.new(gate.key(document), ('logout:' + cookie(self, SESSION_COOKIE)).encode(), hashlib.sha256).hexdigest`, `hmac.compare_digest`, `hmac.new`, `expected.encode`, `csrf.encode`, `gate.key`, `('logout:' + cookie(self, SESSION_COOKIE)).encode`, `cookie_header`, `cookie`, `self.login_page`, `gate.valid`, `cookie(self, LOGIN_COOKIE).encode`, `gate.retry_after`, `gate.verifying.acquire`, `gate.verifying.release`, `hashlib.pbkdf2_hmac`, `digest.hex`, `password.encode`, `bytes.fromhex`, `gate.token`, `safe_next`.

## Специальные обработчики и ограничения перечня

Потоковые `/api/file-upload`, `/api/calendar-telegram` и настройка Telegram обрабатываются также отдельными receive-методами до общего JSON-dispatch. `/_auth/login`, `/_auth/session`, `/_auth/logout` проверяются в `remote_access.py`. GET/POST одной строки могут иметь разные правила. Список веток не является разрешением выполнять произвольные POST.
