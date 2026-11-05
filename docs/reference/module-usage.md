# Использование модулей

Входящие импорты собственного Python, включая локальные; отдельно — тесты и прямой CLI. Это синтаксические свидетельства, а не профиль рабочего процесса. Динамические загрузки копий отката и вызовы subprocess дополнительно описаны в [старом коде](../legacy-code.md) и [архитектуре](../architecture.md).

| Модуль | Импортируется рабочим кодом / утилитами | Тестовые модули | Прямой запуск |
| --- | --- | ---: | --- |
| [calendar_delivery.py](python/calendar_delivery.md) | `calendar_todos.py`, `server.py` | 1 | Нет |
| [calendar_events.py](python/calendar_events.md) | `server.py` | 4 | Нет |
| [calendar_layout.py](python/calendar_layout.md) | `order_calendar.py`, `orders.py` | 1 | Нет |
| [calendar_todos.py](python/calendar_todos.md) | `server.py`, `telegram_calendar.py` | 3 | Нет |
| [client_activity.py](python/client_activity.md) | `hidden_orders.py`, `object_activity.py`, `server.py`, `supplier_purchases.py` | 2 | Нет |
| [event_folder_undo.py](python/event_folder_undo.md) | `client_activity.py`, `event_folders.py`, `file_uploads.py`, `folder_notes.py`, `folder_rename.py`, `invoices.py`, `local_metadata.py`, `mobile_sync.py`, `object_orders.py`, `object_years.py`, `order_creation.py`, `order_links.py`, `orders.py`, `reconciliations.py`, `server.py`, `supplier_purchases.py`, `weekly_events_migration.py`, `work_order_list.py`, `work_orders.py` | 5 | Да |
| [event_folders.py](python/event_folders.md) | `server.py` | 6 | Нет |
| [event_relevance.py](python/event_relevance.md) | `folder_notes.py`, `server.py`, `sketches.py` | 1 | Нет |
| [event_trash.py](python/event_trash.md) | `server.py` | 1 | Нет |
| [file_comments.py](python/file_comments.md) | `folder_notes.py`, `invoice_discovery.py`, `invoices.py`, `local_metadata.py`, `mobile_sync.py`, `server.py`, `telegram_inbox.py` | 3 | Нет |
| [file_trash.py](python/file_trash.md) | `file_uploads.py`, `invoice_discovery.py`, `invoices.py`, `server.py` | 2 | Да |
| [file_uploads.py](python/file_uploads.md) | `server.py` | 4 | Нет |
| [folder_layout.py](python/folder_layout.md) | `event_folders.py`, `event_trash.py`, `file_uploads.py`, `folder_rename.py`, `image_reports.py`, `invoices.py`, `local_metadata.py`, `object_years.py`, `order_creation.py`, `order_folders.py`, `recovery_backup.py`, `scripts/archive_order_duplicate.py`, `scripts/rebind_glass_notes.py`, `scripts/rebind_order.py` | 8 | Да |
| [folder_notes.py](python/folder_notes.md) | `event_folders.py`, `event_trash.py`, `file_uploads.py`, `folder_rename.py`, `object_years.py`, `order_todos.py`, `orders.py`, `scripts/rebind_glass_notes.py`, `server.py` | 4 | Нет |
| [folder_rename.py](python/folder_rename.md) | `event_trash.py`, `server.py` | 8 | Нет |
| [folder_rename_undo.py](python/folder_rename_undo.md) | `event_trash.py`, `folder_rename.py`, `local_metadata.py`, `object_years.py` | 7 | Да |
| [folder_structure.py](python/folder_structure.md) | `client_activity.py`, `event_folders.py`, `event_relevance.py`, `file_uploads.py`, `folder_notes.py`, `folder_rename.py`, `hidden_orders.py`, `object_activity.py`, `object_orders.py`, `object_years.py`, `order_creation.py`, `order_folders.py`, `order_links.py`, `orders.py`, `reconciliations.py`, `scripts/rebind_glass_notes.py`, `server.py`, `supplier_purchases.py`, `work_order_list.py`, `work_orders.py` | 7 | Нет |
| [hidden_orders.py](python/hidden_orders.md) | `server.py` | 1 | Нет |
| [icloud_access.py](python/icloud_access.md) | `invoice_discovery.py`, `local_metadata.py`, `order_document.py`, `server.py`, `spreadsheet_preview.py` | 1 | Нет |
| [image_reports.py](python/image_reports.md) | `server.py` | 0 | Нет |
| [inbox_folder.py](python/inbox_folder.md) | `server.py` | 1 | Нет |
| [invoice_discovery.py](python/invoice_discovery.md) | `server.py` | 1 | Нет |
| [invoice_documents.py](python/invoice_documents.md) | `invoices.py`, `server.py` | 2 | Нет |
| [invoices.py](python/invoices.md) | `invoice_discovery.py`, `invoice_documents.py`, `server.py` | 12 | Нет |
| [local_metadata.py](python/local_metadata.md) | `calendar_events.py`, `calendar_layout.py`, `folder_notes.py`, `invoices.py`, `object_orders.py`, `order_calendar.py`, `order_creation.py`, `orders.py`, `reconciliations.py`, `server.py`, `supplier_purchases.py`, `telegram_calendar_commands.py`, `telegram_inbox.py`, `weekly_events_migration.py`, `work_orders.py` | 8 | Нет |
| [mobile_sync.py](python/mobile_sync.md) | `orders.py`, `server.py` | 2 | Нет |
| [native_renderers.py](python/native_renderers.md) | `calendar_delivery.py`, `icloud_access.py`, `image_reports.py`, `invoices.py`, `server.py`, `thumbnail_cache.py` | 3 | Нет |
| [object_activity.py](python/object_activity.md) | `server.py` | 1 | Нет |
| [object_orders.py](python/object_orders.md) | `server.py`, `work_order_list.py` | 7 | Нет |
| [object_years.py](python/object_years.md) | `server.py` | 1 | Нет |
| [order_calendar.py](python/order_calendar.md) | `calendar_events.py`, `invoices.py`, `order_deadlines.py`, `orders.py`, `weekly_events_migration.py` | 9 | Нет |
| [order_creation.py](python/order_creation.md) | `order_folders.py`, `server.py` | 2 | Нет |
| [order_deadlines.py](python/order_deadlines.md) | `object_orders.py`, `order_calendar.py`, `orders.py`, `server.py` | 5 | Нет |
| [order_document.py](python/order_document.md) | `client_activity.py`, `file_comments.py`, `folder_notes.py`, `local_metadata.py`, `mobile_sync.py`, `object_orders.py`, `order_todos.py`, `orders.py`, `reconciliations.py`, `scripts/archive_order_duplicate.py`, `scripts/rebind_order.py`, `server.py`, `supplier_purchases.py` | 11 | Нет |
| [order_folders.py](python/order_folders.md) | `event_folders.py`, `event_trash.py`, `file_uploads.py`, `folder_rename.py`, `invoices.py`, `local_metadata.py`, `object_years.py`, `order_creation.py`, `server.py` | 7 | Нет |
| [order_links.py](python/order_links.md) | `orders.py`, `server.py` | 1 | Нет |
| [order_todos.py](python/order_todos.md) | `event_trash.py`, `folder_rename.py`, `object_orders.py`, `object_years.py`, `server.py` | 6 | Нет |
| [orders.py](python/orders.md) | `calendar_events.py`, `event_trash.py`, `folder_rename.py`, `invoice_discovery.py`, `invoice_documents.py`, `invoices.py`, `object_years.py`, `order_links.py`, `server.py` | 30 | Нет |
| [reconciliations.py](python/reconciliations.md) | `order_creation.py`, `orders.py`, `server.py` | 1 | Нет |
| [recovery_backup.py](python/recovery_backup.md) | `local_metadata.py`, `server.py` | 1 | Да |
| [remote_access.py](python/remote_access.md) | `scripts/remote_access_password.py`, `server.py` | 1 | Нет |
| [scripts/archive_order_duplicate.py](python/scripts-archive_order_duplicate.md) | Прямой import не найден; см. точку запуска | 0 | Да |
| [scripts/build_documentation.py](python/scripts-build_documentation.md) | Прямой import не найден; см. точку запуска | 0 | Да |
| [scripts/deploy.py](python/scripts-deploy.md) | Прямой import не найден; см. точку запуска | 0 | Да |
| [scripts/deploy_remote.py](python/scripts-deploy_remote.md) | Прямой import не найден; см. точку запуска | 0 | Да |
| [scripts/rebind_glass_notes.py](python/scripts-rebind_glass_notes.md) | Прямой import не найден; см. точку запуска | 0 | Да |
| [scripts/rebind_order.py](python/scripts-rebind_order.md) | Прямой import не найден; см. точку запуска | 0 | Да |
| [scripts/remote_access_password.py](python/scripts-remote_access_password.md) | Прямой import не найден; см. точку запуска | 0 | Да |
| [scripts/verify_recovery_backup.py](python/scripts-verify_recovery_backup.md) | Прямой import не найден; см. точку запуска | 0 | Да |
| [server.py](python/server.md) | `scripts/archive_order_duplicate.py`, `scripts/rebind_glass_notes.py`, `scripts/rebind_order.py` | 2 | Да |
| [sketches.py](python/sketches.md) | `folder_notes.py`, `server.py`, `thumbnail_cache.py` | 1 | Нет |
| [spreadsheet_preview.py](python/spreadsheet_preview.md) | `server.py` | 1 | Нет |
| [supplier_purchases.py](python/supplier_purchases.md) | `folder_notes.py`, `orders.py`, `server.py` | 1 | Нет |
| [telegram_calendar.py](python/telegram_calendar.md) | `calendar_delivery.py`, `server.py`, `telegram_calendar_commands.py`, `telegram_inbox.py` | 2 | Нет |
| [telegram_calendar_commands.py](python/telegram_calendar_commands.md) | `telegram_inbox.py` | 1 | Нет |
| [telegram_inbox.py](python/telegram_inbox.md) | `server.py` | 2 | Нет |
| [thumbnail_cache.py](python/thumbnail_cache.md) | `server.py` | 1 | Да |
| [weekly_events_migration.py](python/weekly_events_migration.md) | Прямой import не найден; см. точку запуска | 1 | Да |
| [work_order_list.py](python/work_order_list.md) | `server.py` | 2 | Нет |
| [work_orders.py](python/work_orders.md) | `event_trash.py`, `invoice_discovery.py`, `orders.py`, `server.py`, `supplier_purchases.py`, `work_order_list.py` | 6 | Нет |

JavaScript-подключение: `static/index.html` задаёт основной порядок скриптов, `hidden-orders.html` — отдельную страницу; `spreadsheet-preview.js` создаёт Worker, `remote_access.py` добавляет скрипт входа только во внешний HTML. `calendar_delivery.py` встраивает общие модули в автономный HTML WebKit. Swift вызывается соответствующими Python-адаптерами через native_renderers, C компилируется удалённым deploy-помощником. Подробные цепочки — в [сценариях](../flows.md).
