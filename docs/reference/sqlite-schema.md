# SQLite: схема из исходников

Статический справочник CREATE/ALTER/INDEX/TRIGGER из собственных Python-файлов. Динамические имена и f-строки показаны как шаблоны. Наличие DDL в совместимой ветке не означает, что она исполняется в текущем режиме. [Как работает хранение](../language/sqlite.md).

## calendar_events.py

[schema](python/calendar_events.md#symbol-schema)

```sql
ALTER TABLE calendar_events ADD COLUMN color TEXT NOT NULL DEFAULT 'gray'
```

[schema](python/calendar_events.md#symbol-schema)

```sql
ALTER TABLE calendar_events ADD COLUMN comment TEXT NOT NULL DEFAULT ''
```

[schema](python/calendar_events.md#symbol-schema)

```sql
ALTER TABLE calendar_events ADD COLUMN is_completed INTEGER NOT NULL DEFAULT 0
```

[schema](python/calendar_events.md#symbol-schema)

```sql
ALTER TABLE calendar_events ADD COLUMN is_inactive INTEGER NOT NULL DEFAULT 0
```

[schema](python/calendar_events.md#symbol-schema)

```sql
ALTER TABLE calendar_events ADD COLUMN is_trip INTEGER NOT NULL DEFAULT 0
```

[schema](python/calendar_events.md#symbol-schema)

```sql
CREATE TABLE IF NOT EXISTS calendar_events (
        id TEXT PRIMARY KEY, version INTEGER NOT NULL, period TEXT NOT NULL,
        date TEXT NOT NULL, text TEXT NOT NULL, revision INTEGER NOT NULL,
        created REAL NOT NULL, updated REAL NOT NULL, deleted INTEGER NOT NULL DEFAULT 0,
        color TEXT NOT NULL DEFAULT 'gray', is_inactive INTEGER NOT NULL DEFAULT 0,
        is_completed INTEGER NOT NULL DEFAULT 0, is_trip INTEGER NOT NULL DEFAULT 0,
        comment TEXT NOT NULL DEFAULT '')
```

## client_activity.py

[ClientActivity.schema](python/client_activity.md#symbol-ClientActivity.schema)

```sql
-- Динамический шаблон
CREATE TABLE IF NOT EXISTS {cls.table} (
            path TEXT PRIMARY KEY, inactive INTEGER NOT NULL, revision INTEGER NOT NULL,
            exported_revision INTEGER NOT NULL, file_value TEXT NOT NULL, sync_error TEXT NOT NULL DEFAULT '')
```

## event_folder_undo.py

[schema](python/event_folder_undo.md#symbol-schema)

```sql
ALTER TABLE event_renames ADD COLUMN paths_applied INTEGER NOT NULL DEFAULT 0
```

[schema](python/event_folder_undo.md#symbol-schema)

```sql
CREATE TABLE IF NOT EXISTS event_renames (session TEXT PRIMARY KEY,state TEXT NOT NULL,mappings TEXT NOT NULL,paths_applied INTEGER NOT NULL DEFAULT 0)
```

## event_trash.py

[remove](python/event_trash.md#symbol-remove)

```sql
CREATE TABLE IF NOT EXISTS folder_renames (session TEXT PRIMARY KEY,state TEXT NOT NULL,mappings TEXT NOT NULL,paths_applied INTEGER NOT NULL)
```

## folder_notes.py

[schema](python/folder_notes.md#symbol-schema)

```sql
CREATE TABLE IF NOT EXISTS folder_notes (
        path TEXT PRIMARY KEY, id TEXT NOT NULL UNIQUE, parent_order TEXT NOT NULL,
        document TEXT NOT NULL, revision INTEGER NOT NULL, exported_revision INTEGER NOT NULL,
        file_revision TEXT NOT NULL, updated REAL NOT NULL, sync_error TEXT NOT NULL DEFAULT '')
```

## folder_rename.py

[relocate](python/folder_rename.md#symbol-relocate)

```sql
CREATE TABLE IF NOT EXISTS folder_renames (session TEXT PRIMARY KEY,state TEXT NOT NULL,mappings TEXT NOT NULL,paths_applied INTEGER NOT NULL)
```

## invoice_documents.py

[schema](python/invoice_documents.md#symbol-schema)

```sql
ALTER TABLE invoice_documents ADD COLUMN
```

[schema](python/invoice_documents.md#symbol-schema)

```sql
CREATE INDEX IF NOT EXISTS invoice_documents_invoice ON invoice_documents(invoice_id)
```

[schema](python/invoice_documents.md#symbol-schema)

```sql
CREATE TABLE IF NOT EXISTS invoice_documents (
        id TEXT PRIMARY KEY, invoice_id TEXT NOT NULL, version INTEGER NOT NULL,
        name TEXT NOT NULL, mime TEXT NOT NULL, size INTEGER NOT NULL,
        sha256 TEXT NOT NULL, content BLOB NOT NULL, created REAL NOT NULL,
        filename TEXT NOT NULL DEFAULT '', exported INTEGER NOT NULL DEFAULT 0,
        sync_error TEXT NOT NULL DEFAULT '')
```

## invoice_preferences.py

[history](python/invoice_preferences.md#symbol-history)

```sql
CREATE TABLE IF NOT EXISTS invoice_settings_history (
        key TEXT NOT NULL, revision INTEGER NOT NULL, value TEXT NOT NULL, saved REAL NOT NULL,
        PRIMARY KEY(key,revision))
```

## invoices.py

[InvoiceStore.connect](python/invoices.md#symbol-InvoiceStore.connect)

```sql
CREATE TABLE IF NOT EXISTS invoice_history (id TEXT, revision INTEGER, data TEXT NOT NULL, saved REAL NOT NULL, PRIMARY KEY(id,revision))
```

[InvoiceStore.connect](python/invoices.md#symbol-InvoiceStore.connect)

```sql
CREATE TABLE IF NOT EXISTS invoice_sequences (year INTEGER PRIMARY KEY, value INTEGER NOT NULL)
```

[InvoiceStore.connect](python/invoices.md#symbol-InvoiceStore.connect)

```sql
CREATE TABLE IF NOT EXISTS invoice_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)
```

[InvoiceStore.connect](python/invoices.md#symbol-InvoiceStore.connect)

```sql
CREATE TABLE IF NOT EXISTS invoices (
                id TEXT PRIMARY KEY, path TEXT NOT NULL, year INTEGER NOT NULL, number TEXT NOT NULL,
                revision INTEGER NOT NULL, state TEXT NOT NULL, data TEXT NOT NULL, pdf BLOB,
                filename TEXT NOT NULL DEFAULT '', exported INTEGER NOT NULL DEFAULT 0,
                sync_error TEXT NOT NULL DEFAULT '', created REAL NOT NULL, updated REAL NOT NULL,
                UNIQUE(year,number))
```

## local_metadata.py

[audit](python/local_metadata.md#symbol-audit)

```sql
-- Динамический шаблон
CREATE TRIGGER IF NOT EXISTS metadata_audit_{table}_{event}
            BEFORE {event} ON {table} BEGIN
            INSERT INTO metadata_history(entity,identity,data,saved)
            VALUES ('{table}',OLD.{identity},{payload},strftime('%s','now')); END
```

[schema](python/local_metadata.md#symbol-schema)

```sql
CREATE TABLE IF NOT EXISTS legacy_documents (
        path TEXT NOT NULL,digest TEXT NOT NULL,body BLOB NOT NULL,saved REAL NOT NULL,PRIMARY KEY(path,digest))
```

[schema](python/local_metadata.md#symbol-schema)

```sql
CREATE TABLE IF NOT EXISTS metadata_file_moves (
        session TEXT NOT NULL,source TEXT NOT NULL,destination TEXT NOT NULL,state TEXT NOT NULL,
        PRIMARY KEY(session,source))
```

[schema](python/local_metadata.md#symbol-schema)

```sql
CREATE TABLE IF NOT EXISTS metadata_history (
        seq INTEGER PRIMARY KEY,entity TEXT NOT NULL,identity TEXT NOT NULL,data TEXT NOT NULL,saved REAL NOT NULL)
```

[schema](python/local_metadata.md#symbol-schema)

```sql
CREATE TABLE IF NOT EXISTS metadata_imports (
        kind TEXT NOT NULL,path TEXT NOT NULL,error TEXT NOT NULL,attempted REAL NOT NULL,PRIMARY KEY(kind,path))
```

[schema](python/local_metadata.md#symbol-schema)

```sql
CREATE TABLE IF NOT EXISTS metadata_publications (
        id TEXT PRIMARY KEY,source TEXT NOT NULL,revision TEXT NOT NULL,path TEXT NOT NULL,body BLOB NOT NULL,
        published INTEGER NOT NULL DEFAULT 0,error TEXT NOT NULL DEFAULT '',UNIQUE(source,revision))
```

[schema](python/local_metadata.md#symbol-schema)

```sql
CREATE TABLE IF NOT EXISTS metadata_records (
        id TEXT NOT NULL UNIQUE,kind TEXT NOT NULL,path TEXT NOT NULL,data TEXT NOT NULL,
        revision INTEGER NOT NULL,updated REAL NOT NULL,PRIMARY KEY(kind,path))
```

[schema](python/local_metadata.md#symbol-schema)

```sql
CREATE TABLE IF NOT EXISTS metadata_settings (key TEXT PRIMARY KEY,value TEXT NOT NULL)
```

## mobile_sync.py

[MobileBridge.__init__](python/mobile_sync.md#symbol-MobileBridge.__init__)

```sql
CREATE TABLE IF NOT EXISTS mobile_files (
                order_id TEXT PRIMARY KEY, scanned REAL NOT NULL, items TEXT NOT NULL)
```

[MobileBridge.__init__](python/mobile_sync.md#symbol-MobileBridge.__init__)

```sql
CREATE TABLE IF NOT EXISTS mobile_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)
```

[MobileBridge.__init__](python/mobile_sync.md#symbol-MobileBridge.__init__)

```sql
CREATE TABLE IF NOT EXISTS mobile_operations (
                id TEXT PRIMARY KEY, digest TEXT NOT NULL, payload TEXT NOT NULL,
                status TEXT NOT NULL, result TEXT NOT NULL, prepared TEXT NOT NULL DEFAULT '{}')
```

[MobileBridge.__init__](python/mobile_sync.md#symbol-MobileBridge.__init__)

```sql
CREATE TABLE IF NOT EXISTS mobile_tasks (
                order_id TEXT PRIMARY KEY, items TEXT NOT NULL)
```

## object_years.py

[group](python/object_years.md#symbol-group)

```sql
CREATE TABLE IF NOT EXISTS folder_renames (session TEXT PRIMARY KEY,state TEXT NOT NULL,mappings TEXT NOT NULL,paths_applied INTEGER NOT NULL)
```

## order_todos.py

[OrderTodos.refresh](python/order_todos.md#symbol-OrderTodos.refresh)

```sql
CREATE TABLE IF NOT EXISTS todo_catalog (path TEXT PRIMARY KEY, checked REAL, error TEXT NOT NULL)
```

[OrderTodos.refresh](python/order_todos.md#symbol-OrderTodos.refresh)

```sql
CREATE TABLE IF NOT EXISTS todo_missing_folders (path TEXT PRIMARY KEY, order_path TEXT NOT NULL, checked REAL NOT NULL)
```

## orders.py

[OrderStore.connect](python/orders.md#symbol-OrderStore.connect)

```sql
ALTER TABLE orders ADD COLUMN export_format INTEGER NOT NULL DEFAULT 0
```

[OrderStore.connect](python/orders.md#symbol-OrderStore.connect)

```sql
ALTER TABLE orders ADD COLUMN extra_blocks TEXT NOT NULL DEFAULT '{}'
```

[OrderStore.connect](python/orders.md#symbol-OrderStore.connect)

```sql
ALTER TABLE orders ADD COLUMN financial_status TEXT NOT NULL DEFAULT 'unspecified'
```

[OrderStore.connect](python/orders.md#symbol-OrderStore.connect)

```sql
ALTER TABLE orders ADD COLUMN registered INTEGER NOT NULL DEFAULT 1
```

[OrderStore.connect](python/orders.md#symbol-OrderStore.connect)

```sql
CREATE TABLE IF NOT EXISTS orders (
                path TEXT PRIMARY KEY, id TEXT NOT NULL UNIQUE, title TEXT NOT NULL,
                status TEXT NOT NULL, note TEXT NOT NULL, amount INTEGER, costs INTEGER,
                paid INTEGER, revision INTEGER NOT NULL, exported_revision INTEGER NOT NULL DEFAULT 0,
                updated REAL NOT NULL, sync_error TEXT NOT NULL DEFAULT '')
```

## reconciliations.py

[schema](python/reconciliations.md#symbol-schema)

```sql
CREATE TABLE IF NOT EXISTS reconciliation_invoices (
        id TEXT PRIMARY KEY,reconciliation_id TEXT NOT NULL,revision INTEGER NOT NULL,updated REAL NOT NULL)
```

[schema](python/reconciliations.md#symbol-schema)

```sql
CREATE TABLE IF NOT EXISTS reconciliations (
        path TEXT PRIMARY KEY,id TEXT NOT NULL UNIQUE,data TEXT NOT NULL,
        revision INTEGER NOT NULL,updated REAL NOT NULL)
```

## scripts/archive_order_duplicate.py

[archive](python/scripts-archive_order_duplicate.md#symbol-archive)

```sql
CREATE TABLE IF NOT EXISTS order_duplicate_archive (
            id TEXT PRIMARY KEY, canonical_id TEXT NOT NULL, record TEXT NOT NULL,
            journal TEXT NOT NULL, archived REAL NOT NULL, state TEXT NOT NULL)
```

## thumbnail_cache.py

[ThumbnailCache.__init__](python/thumbnail_cache.md#symbol-ThumbnailCache.__init__)

```sql
CREATE TABLE IF NOT EXISTS thumbnails (
                    path TEXT PRIMARY KEY, signature TEXT NOT NULL, modified REAL NOT NULL,
                    state TEXT NOT NULL DEFAULT 'pending', image BLOB, mime TEXT,
                    priority REAL NOT NULL DEFAULT 0, seen REAL NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0, retry_at REAL NOT NULL DEFAULT 0,
                    error TEXT NOT NULL DEFAULT '', updated REAL NOT NULL DEFAULT 0
                );
                CREATE INDEX IF NOT EXISTS thumbnail_queue ON thumbnails(state, retry_at, priority, modified);
                CREATE TABLE IF NOT EXISTS worker_status (key TEXT PRIMARY KEY, value TEXT NOT NULL);
```
