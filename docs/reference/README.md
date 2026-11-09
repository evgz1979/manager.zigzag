# Справочник исходников

Сгенерировано `scripts/build_documentation.py` из текущего AST/объявлений и двухстрочных комментариев. Ссылки используют постоянные имена объявлений. [Архитектура](../architecture.md), [языки](../language/README.md), [старый код](../legacy-code.md).

[HTTP-маршруты](http-api.md) · [SQLite DDL](sqlite-schema.md) · [использование модулей](module-usage.md) · [машинная инвентаризация](inventory.json).

Включены собственные Python-модули и эксплуатационные скрипты, именованные JS-функции/методы, Swift-типы/методы и функции C-обёртки. Тестовые методы, vendor, анонимные callbacks и вычисляемые свойства не считаются отдельными объявлениями; тесты и встроенные HTML-сценарии объясняются в тематических документах.

## Python

60 файлов; 832 именованных объявлений.

| Модуль | Объявлений |
| --- | ---: |
| [calendar_delivery.py](python/calendar_delivery.md) | 5 |
| [calendar_events.py](python/calendar_events.md) | 18 |
| [calendar_layout.py](python/calendar_layout.md) | 3 |
| [calendar_todos.py](python/calendar_todos.md) | 2 |
| [client_activity.py](python/client_activity.md) | 21 |
| [event_folder_undo.py](python/event_folder_undo.md) | 7 |
| [event_folders.py](python/event_folders.md) | 9 |
| [event_relevance.py](python/event_relevance.md) | 4 |
| [event_trash.py](python/event_trash.md) | 6 |
| [file_comments.py](python/file_comments.md) | 6 |
| [file_trash.py](python/file_trash.md) | 18 |
| [file_uploads.py](python/file_uploads.md) | 11 |
| [folder_layout.py](python/folder_layout.md) | 15 |
| [folder_notes.py](python/folder_notes.md) | 20 |
| [folder_rename.py](python/folder_rename.md) | 6 |
| [folder_rename_undo.py](python/folder_rename_undo.md) | 7 |
| [folder_structure.py](python/folder_structure.md) | 18 |
| [hidden_orders.py](python/hidden_orders.md) | 4 |
| [icloud_access.py](python/icloud_access.md) | 8 |
| [image_reports.py](python/image_reports.md) | 2 |
| [inbox_folder.py](python/inbox_folder.md) | 1 |
| [invoice_discovery.py](python/invoice_discovery.md) | 6 |
| [invoice_documents.py](python/invoice_documents.md) | 13 |
| [invoices.py](python/invoices.md) | 47 |
| [local_metadata.py](python/local_metadata.md) | 26 |
| [mobile_sync.py](python/mobile_sync.md) | 24 |
| [native_renderers.py](python/native_renderers.md) | 1 |
| [object_activity.py](python/object_activity.md) | 4 |
| [object_orders.py](python/object_orders.md) | 11 |
| [object_years.py](python/object_years.md) | 4 |
| [order_calendar.py](python/order_calendar.md) | 31 |
| [order_creation.py](python/order_creation.md) | 6 |
| [order_deadlines.py](python/order_deadlines.md) | 8 |
| [order_document.py](python/order_document.md) | 32 |
| [order_folders.py](python/order_folders.md) | 6 |
| [order_links.py](python/order_links.md) | 18 |
| [order_todos.py](python/order_todos.md) | 9 |
| [orders.py](python/orders.md) | 44 |
| [reconciliations.py](python/reconciliations.md) | 19 |
| [recovery_backup.py](python/recovery_backup.md) | 10 |
| [remote_access.py](python/remote_access.md) | 38 |
| [scripts/archive_order_duplicate.py](python/scripts-archive_order_duplicate.md) | 8 |
| [scripts/build_documentation.py](python/scripts-build_documentation.md) | 22 |
| [scripts/deploy.py](python/scripts-deploy.md) | 3 |
| [scripts/deploy_remote.py](python/scripts-deploy_remote.md) | 17 |
| [scripts/rebind_glass_notes.py](python/scripts-rebind_glass_notes.md) | 6 |
| [scripts/rebind_order.py](python/scripts-rebind_order.md) | 8 |
| [scripts/remote_access_password.py](python/scripts-remote_access_password.md) | 10 |
| [scripts/verify_recovery_backup.py](python/scripts-verify_recovery_backup.md) | 1 |
| [server.py](python/server.md) | 95 |
| [sketches.py](python/sketches.md) | 12 |
| [spreadsheet_preview.py](python/spreadsheet_preview.md) | 1 |
| [supplier_purchases.py](python/supplier_purchases.md) | 13 |
| [telegram_calendar.py](python/telegram_calendar.md) | 14 |
| [telegram_calendar_commands.py](python/telegram_calendar_commands.md) | 4 |
| [telegram_inbox.py](python/telegram_inbox.md) | 10 |
| [thumbnail_cache.py](python/thumbnail_cache.md) | 23 |
| [weekly_events_migration.py](python/weekly_events_migration.md) | 4 |
| [work_order_list.py](python/work_order_list.md) | 8 |
| [work_orders.py](python/work_orders.md) | 25 |

## JavaScript

21 файлов; 423 именованных объявлений.

| Модуль | Объявлений |
| --- | ---: |
| [static/app.js](javascript/static-app.md) | 232 |
| [static/bills.js](javascript/static-bills.md) | 11 |
| [static/calendar-snapshot.js](javascript/static-calendar-snapshot.md) | 4 |
| [static/calendar-telegram.js](javascript/static-calendar-telegram.md) | 6 |
| [static/hidden-orders.js](javascript/static-hidden-orders.md) | 10 |
| [static/home-calendar.js](javascript/static-home-calendar.md) | 33 |
| [static/inbox.js](javascript/static-inbox.md) | 14 |
| [static/invoice-documents.js](javascript/static-invoice-documents.md) | 17 |
| [static/invoices.js](javascript/static-invoices.md) | 41 |
| [static/mobile.js](javascript/static-mobile.md) | 3 |
| [static/money-overview.js](javascript/static-money-overview.md) | 8 |
| [static/navigation.js](javascript/static-navigation.md) | 1 |
| [static/order-sorting.js](javascript/static-order-sorting.md) | 2 |
| [static/reconciliations.js](javascript/static-reconciliations.md) | 10 |
| [static/remote-access.js](javascript/static-remote-access.md) | 2 |
| [static/settings.js](javascript/static-settings.md) | 2 |
| [static/spreadsheet-preview.js](javascript/static-spreadsheet-preview.md) | 7 |
| [static/spreadsheet-worker.js](javascript/static-spreadsheet-worker.md) | 2 |
| [static/supplier-purchases.js](javascript/static-supplier-purchases.md) | 9 |
| [static/work-orders.js](javascript/static-work-orders.md) | 4 |
| [scripts/documentation_js.cjs](javascript/scripts-documentation_js.md) | 5 |

## Swift и C

10 файлов; 91 именованных объявлений.

| Модуль | Объявлений |
| --- | ---: |
| [calendar_renderer.swift](native/calendar_renderer.md) | 8 |
| [icloud_read.swift](native/icloud_read.md) | 0 |
| [image_report.swift](native/image_report.md) | 4 |
| [invoice_pdf.swift](native/invoice_pdf.md) | 10 |
| [mobile/Core.swift](native/mobile-Core.md) | 20 |
| [mobile/DriveTransport.swift](native/mobile-DriveTransport.md) | 7 |
| [mobile/PhoneApp.swift](native/mobile-PhoneApp.md) | 36 |
| [pdf_preview.swift](native/pdf_preview.md) | 1 |
| [scripts/manager_launcher.c](native/scripts-manager_launcher.md) | 3 |
| [thumbnail_preview.swift](native/thumbnail_preview.md) | 2 |

## Встроенный JavaScript

1 файлов; 1 именованных объявлений.

| Модуль | Объявлений |
| --- | ---: |
| [calendar_delivery.py](embedded/calendar_delivery.md) | 1 |
