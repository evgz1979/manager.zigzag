# SQLite: схема из исходников

Статический справочник CREATE/ALTER/INDEX/TRIGGER из собственных Python-файлов. Динамические имена и f-строки показаны как шаблоны. Наличие DDL в совместимой ветке не означает, что она исполняется в текущем режиме. [Как работает хранение](../language/sqlite.md).

## calendar_events.py

[calendar_events.py:18](../../calendar_events.py#L18)

```sql
CREATE TABLE IF NOT EXISTS calendar_events (
        id TEXT PRIMARY KEY, version INTEGER NOT NULL, period TEXT NOT NULL,
        date TEXT NOT NULL, text TEXT NOT NULL, revision INTEGER NOT NULL,
        created REAL NOT NULL, updated REAL NOT NULL, deleted INTEGER NOT NULL DEFAULT 0,
        color TEXT NOT NULL DEFAULT 'gray', is_inactive INTEGER NOT NULL DEFAULT 0,
        is_completed INTEGER NOT NULL DEFAULT 0, is_trip INTEGER NOT NULL DEFAULT 0)
```

[calendar_events.py:25](../../calendar_events.py#L25)

```sql
ALTER TABLE calendar_events ADD COLUMN color TEXT NOT NULL DEFAULT 'gray'
```

[calendar_events.py:27](../../calendar_events.py#L27)

```sql
ALTER TABLE calendar_events ADD COLUMN is_inactive INTEGER NOT NULL DEFAULT 0
```

[calendar_events.py:31](../../calendar_events.py#L31)

```sql
ALTER TABLE calendar_events ADD COLUMN is_completed INTEGER NOT NULL DEFAULT 0
```

[calendar_events.py:35](../../calendar_events.py#L35)

```sql
ALTER TABLE calendar_events ADD COLUMN is_trip INTEGER NOT NULL DEFAULT 0
```

## client_activity.py

[client_activity.py:57](../../client_activity.py#L57)

```sql
-- Динамический шаблон
CREATE TABLE IF NOT EXISTS {cls.table} (
            path TEXT PRIMARY KEY, inactive INTEGER NOT NULL, revision INTEGER NOT NULL,
            exported_revision INTEGER NOT NULL, file_value TEXT NOT NULL, sync_error TEXT NOT NULL DEFAULT '')
```

## event_folder_undo.py

[event_folder_undo.py:74](../../event_folder_undo.py#L74)

```sql
CREATE TABLE IF NOT EXISTS event_renames (session TEXT PRIMARY KEY,state TEXT NOT NULL,mappings TEXT NOT NULL,paths_applied INTEGER NOT NULL DEFAULT 0)
```

[event_folder_undo.py:76](../../event_folder_undo.py#L76)

```sql
ALTER TABLE event_renames ADD COLUMN paths_applied INTEGER NOT NULL DEFAULT 0
```

## event_trash.py

[event_trash.py:98](../../event_trash.py#L98)

```sql
CREATE TABLE IF NOT EXISTS folder_renames (session TEXT PRIMARY KEY,state TEXT NOT NULL,mappings TEXT NOT NULL,paths_applied INTEGER NOT NULL)
```

## folder_notes.py

[folder_notes.py:70](../../folder_notes.py#L70)

```sql
CREATE TABLE IF NOT EXISTS folder_notes (
        path TEXT PRIMARY KEY, id TEXT NOT NULL UNIQUE, parent_order TEXT NOT NULL,
        document TEXT NOT NULL, revision INTEGER NOT NULL, exported_revision INTEGER NOT NULL,
        file_revision TEXT NOT NULL, updated REAL NOT NULL, sync_error TEXT NOT NULL DEFAULT '')
```

## folder_rename.py

[folder_rename.py:104](../../folder_rename.py#L104)

```sql
CREATE TABLE IF NOT EXISTS folder_renames (session TEXT PRIMARY KEY,state TEXT NOT NULL,mappings TEXT NOT NULL,paths_applied INTEGER NOT NULL)
```

## invoice_documents.py

[invoice_documents.py:22](../../invoice_documents.py#L22)

```sql
CREATE TABLE IF NOT EXISTS invoice_documents (
        id TEXT PRIMARY KEY, invoice_id TEXT NOT NULL, version INTEGER NOT NULL,
        name TEXT NOT NULL, mime TEXT NOT NULL, size INTEGER NOT NULL,
        sha256 TEXT NOT NULL, content BLOB NOT NULL, created REAL NOT NULL,
        filename TEXT NOT NULL DEFAULT '', exported INTEGER NOT NULL DEFAULT 0,
        sync_error TEXT NOT NULL DEFAULT '')
```

[invoice_documents.py:31](../../invoice_documents.py#L31)

```sql
ALTER TABLE invoice_documents ADD COLUMN
```

[invoice_documents.py:32](../../invoice_documents.py#L32)

```sql
CREATE INDEX IF NOT EXISTS invoice_documents_invoice ON invoice_documents(invoice_id)
```

## invoices.py

[invoices.py:304](../../invoices.py#L304)

```sql
CREATE TABLE IF NOT EXISTS invoices (
                id TEXT PRIMARY KEY, path TEXT NOT NULL, year INTEGER NOT NULL, number TEXT NOT NULL,
                revision INTEGER NOT NULL, state TEXT NOT NULL, data TEXT NOT NULL, pdf BLOB,
                filename TEXT NOT NULL DEFAULT '', exported INTEGER NOT NULL DEFAULT 0,
                sync_error TEXT NOT NULL DEFAULT '', created REAL NOT NULL, updated REAL NOT NULL,
                UNIQUE(year,number))
```

[invoices.py:310](../../invoices.py#L310)

```sql
CREATE TABLE IF NOT EXISTS invoice_sequences (year INTEGER PRIMARY KEY, value INTEGER NOT NULL)
```

[invoices.py:311](../../invoices.py#L311)

```sql
CREATE TABLE IF NOT EXISTS invoice_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)
```

[invoices.py:312](../../invoices.py#L312)

```sql
CREATE TABLE IF NOT EXISTS invoice_history (id TEXT, revision INTEGER, data TEXT NOT NULL, saved REAL NOT NULL, PRIMARY KEY(id,revision))
```

## local_metadata.py

[local_metadata.py:23](../../local_metadata.py#L23)

```sql
CREATE TABLE IF NOT EXISTS metadata_settings (key TEXT PRIMARY KEY,value TEXT NOT NULL)
```

[local_metadata.py:26](../../local_metadata.py#L26)

```sql
CREATE TABLE IF NOT EXISTS metadata_records (
        id TEXT NOT NULL UNIQUE,kind TEXT NOT NULL,path TEXT NOT NULL,data TEXT NOT NULL,
        revision INTEGER NOT NULL,updated REAL NOT NULL,PRIMARY KEY(kind,path))
```

[local_metadata.py:29](../../local_metadata.py#L29)

```sql
CREATE TABLE IF NOT EXISTS metadata_history (
        seq INTEGER PRIMARY KEY,entity TEXT NOT NULL,identity TEXT NOT NULL,data TEXT NOT NULL,saved REAL NOT NULL)
```

[local_metadata.py:31](../../local_metadata.py#L31)

```sql
CREATE TABLE IF NOT EXISTS legacy_documents (
        path TEXT NOT NULL,digest TEXT NOT NULL,body BLOB NOT NULL,saved REAL NOT NULL,PRIMARY KEY(path,digest))
```

[local_metadata.py:33](../../local_metadata.py#L33)

```sql
CREATE TABLE IF NOT EXISTS metadata_imports (
        kind TEXT NOT NULL,path TEXT NOT NULL,error TEXT NOT NULL,attempted REAL NOT NULL,PRIMARY KEY(kind,path))
```

[local_metadata.py:35](../../local_metadata.py#L35)

```sql
CREATE TABLE IF NOT EXISTS metadata_publications (
        id TEXT PRIMARY KEY,source TEXT NOT NULL,revision TEXT NOT NULL,path TEXT NOT NULL,body BLOB NOT NULL,
        published INTEGER NOT NULL DEFAULT 0,error TEXT NOT NULL DEFAULT '',UNIQUE(source,revision))
```

[local_metadata.py:38](../../local_metadata.py#L38)

```sql
CREATE TABLE IF NOT EXISTS metadata_file_moves (
        session TEXT NOT NULL,source TEXT NOT NULL,destination TEXT NOT NULL,state TEXT NOT NULL,
        PRIMARY KEY(session,source))
```

[local_metadata.py:53](../../local_metadata.py#L53)

```sql
-- Динамический шаблон
CREATE TRIGGER IF NOT EXISTS metadata_audit_{table}_{event}
            BEFORE {event} ON {table} BEGIN
            INSERT INTO metadata_history(entity,identity,data,saved)
            VALUES ('{table}',OLD.{identity},{payload},strftime('%s','now')); END
```

## mobile_sync.py

[mobile_sync.py:124](../../mobile_sync.py#L124)

```sql
CREATE TABLE IF NOT EXISTS mobile_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)
```

[mobile_sync.py:125](../../mobile_sync.py#L125)

```sql
CREATE TABLE IF NOT EXISTS mobile_operations (
                id TEXT PRIMARY KEY, digest TEXT NOT NULL, payload TEXT NOT NULL,
                status TEXT NOT NULL, result TEXT NOT NULL, prepared TEXT NOT NULL DEFAULT '{}')
```

[mobile_sync.py:128](../../mobile_sync.py#L128)

```sql
CREATE TABLE IF NOT EXISTS mobile_tasks (
                order_id TEXT PRIMARY KEY, items TEXT NOT NULL)
```

[mobile_sync.py:130](../../mobile_sync.py#L130)

```sql
CREATE TABLE IF NOT EXISTS mobile_files (
                order_id TEXT PRIMARY KEY, scanned REAL NOT NULL, items TEXT NOT NULL)
```

## object_years.py

[object_years.py:120](../../object_years.py#L120)

```sql
CREATE TABLE IF NOT EXISTS folder_renames (session TEXT PRIMARY KEY,state TEXT NOT NULL,mappings TEXT NOT NULL,paths_applied INTEGER NOT NULL)
```

## order_todos.py

[order_todos.py:167](../../order_todos.py#L167)

```sql
CREATE TABLE IF NOT EXISTS todo_catalog (path TEXT PRIMARY KEY, checked REAL, error TEXT NOT NULL)
```

[order_todos.py:168](../../order_todos.py#L168)

```sql
CREATE TABLE IF NOT EXISTS todo_missing_folders (path TEXT PRIMARY KEY, order_path TEXT NOT NULL, checked REAL NOT NULL)
```

## orders.py

[orders.py:54](../../orders.py#L54)

```sql
CREATE TABLE IF NOT EXISTS orders (
                path TEXT PRIMARY KEY, id TEXT NOT NULL UNIQUE, title TEXT NOT NULL,
                status TEXT NOT NULL, note TEXT NOT NULL, amount INTEGER, costs INTEGER,
                paid INTEGER, revision INTEGER NOT NULL, exported_revision INTEGER NOT NULL DEFAULT 0,
                updated REAL NOT NULL, sync_error TEXT NOT NULL DEFAULT '')
```

[orders.py:63](../../orders.py#L63)

```sql
ALTER TABLE orders ADD COLUMN extra_blocks TEXT NOT NULL DEFAULT '{}'
```

[orders.py:65](../../orders.py#L65)

```sql
ALTER TABLE orders ADD COLUMN export_format INTEGER NOT NULL DEFAULT 0
```

[orders.py:67](../../orders.py#L67)

```sql
ALTER TABLE orders ADD COLUMN registered INTEGER NOT NULL DEFAULT 1
```

[orders.py:69](../../orders.py#L69)

```sql
ALTER TABLE orders ADD COLUMN financial_status TEXT NOT NULL DEFAULT 'unspecified'
```

## reconciliations.py

[reconciliations.py:28](../../reconciliations.py#L28)

```sql
CREATE TABLE IF NOT EXISTS reconciliations (
        path TEXT PRIMARY KEY,id TEXT NOT NULL UNIQUE,data TEXT NOT NULL,
        revision INTEGER NOT NULL,updated REAL NOT NULL)
```

[reconciliations.py:31](../../reconciliations.py#L31)

```sql
CREATE TABLE IF NOT EXISTS reconciliation_invoices (
        id TEXT PRIMARY KEY,reconciliation_id TEXT NOT NULL,revision INTEGER NOT NULL,updated REAL NOT NULL)
```

## scripts/archive_order_duplicate.py

[scripts/archive_order_duplicate.py:175](../../scripts/archive_order_duplicate.py#L175)

```sql
CREATE TABLE IF NOT EXISTS order_duplicate_archive (
            id TEXT PRIMARY KEY, canonical_id TEXT NOT NULL, record TEXT NOT NULL,
            journal TEXT NOT NULL, archived REAL NOT NULL, state TEXT NOT NULL)
```

## thumbnail_cache.py

[thumbnail_cache.py:87](../../thumbnail_cache.py#L87)

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
