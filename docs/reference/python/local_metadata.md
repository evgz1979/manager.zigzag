# local_metadata.py

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [local_metadata.py:1](../../../local_metadata.py#L1).

SQLite working metadata; legacy files are read only during migration.

Импорты Python, включая локальные: `contextlib`, `event_folder_undo`, `file_comments`, `folder_layout`, `folder_rename_undo`, `hashlib`, `icloud_access`, `json`, `order_document`, `order_folders`, `os`, `pathlib`, `recovery_backup`, `sqlite3`, `threading`, `time`, `unicodedata`, `uuid`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## schema

[local_metadata.py:22](../../../local_metadata.py#L22) · `function`.

```python
def schema(db):
```

Создаёт отсутствующие таблицы и совместимые расширения схемы.

Работает с таблицами metadata_settings, metadata_records, metadata_history, legacy_documents, metadata_imports.

Непосредственные вызовы: `db.execute`, `db.execute("SELECT 1 FROM metadata_settings WHERE key='storage_version'").fetchone`.

## audit

[local_metadata.py:45](../../../local_metadata.py#L45) · `function`.

```python
def audit(db, table):
```

Создаёт триггеры истории до изменения и удаления записей SQLite.

Работает с таблицами metadata_history.

Непосредственные вызовы: `db.execute`, `','.join`.

## MetadataStore

[local_metadata.py:61](../../../local_metadata.py#L61) · `class`.

```python
class MetadataStore:
```

Хранит типизированные SQLite-метаданные, импорт исходников и очередь публикаций.

Основные операции: __init__, key, connect, record, get; остальные описаны у методов.

## MetadataStore.__init__

[local_metadata.py:64](../../../local_metadata.py#L64) · `function`.

```python
def __init__(self, store):
```

Сохраняет зависимости и начальные параметры экземпляра.

Состояние и зависимости сохраняются в полях self для последующих операций.

Прямые присваивания полям/свойствам: `self.store`, `self.root`.

## MetadataStore.key

[local_metadata.py:70](../../../local_metadata.py#L70) · `function`.

```python
def key(self, file):
```

Вычисляет нормализованный ключ для обращения к данным.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `Path`, `os.path.abspath`, `path.relative_to(root).as_posix`, `path.relative_to`, `ValueError`, `unicodedata.normalize`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
unicodedata.normalize('NFC', relative)
```

## MetadataStore.connect

[local_metadata.py:83](../../../local_metadata.py#L83) · `function`.

```python
def connect(self):
```

Открывает соединение SQLite и управляет его временем жизни.

Передаёт ресурс через yield; освобождение выполняется при выходе из контекста.

Непосредственные вызовы: `self.store.connect`, `schema`.

## MetadataStore.record

[local_metadata.py:91](../../../local_metadata.py#L91) · `function`.

```python
def record(row):
```

Преобразует строку SQLite в представление для вызывающего кода.

Разбирает JSON; вызывающий код должен учитывать ошибки или неизвестный формат.

Непосредственные вызовы: `json.loads`.

Выражения возврата (ветки читаются в исходнике):

```python
None
{**json.loads(row['data']), 'revision': f"{row['id']}:{row['revision']}", 'updated': row['updated'], 'path': row['path']}
```

## MetadataStore.get

[local_metadata.py:99](../../../local_metadata.py#L99) · `function`.

```python
def get(self, kind, path):
```

Читает запись kind/path, проверяя незавершённые переносы её пути.

Работает с таблицами metadata_file_moves, metadata_records.

Непосредственные вызовы: `unicodedata.normalize`, `self.connect`, `assert_unlocked`, `db.execute("SELECT 1 FROM metadata_file_moves WHERE state='pending' AND (source=? OR destination=?)", (path, path)).fetchone`, `db.execute`, `ValueError`, `self.record`, `db.execute('SELECT * FROM metadata_records WHERE kind=? AND path=?', (kind, path)).fetchone`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
self.record(db.execute('SELECT * FROM metadata_records WHERE kind=? AND path=?', (kind, path)).fetchone())
```

## MetadataStore.put

[local_metadata.py:109](../../../local_metadata.py#L109) · `function`.

```python
def put(self, kind, path, data, revision):
```

Создаёт или меняет запись базы с предусмотренной проверкой текущего состояния.

Работает с таблицами metadata_file_moves, metadata_records.

Непосредственные вызовы: `unicodedata.normalize`, `self.connect`, `db.execute`, `assert_unlocked`, `db.execute("SELECT 1 FROM metadata_file_moves WHERE state='pending' AND (source=? OR destination=?)", (path, path)).fetchone`, `ValueError`, `db.execute('SELECT * FROM metadata_records WHERE kind=? AND path=?', (kind, path)).fetchone`, `self.record`, `FileCommentConflict`, `json.dumps`, `time.time`, `str`, `uuid.uuid4`.

Явные исключения: `ValueError`, `FileCommentConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
self.record(db.execute('SELECT * FROM metadata_records WHERE kind=? AND path=?', (kind, path)).fetchone())
```

## MetadataStore.archive

[local_metadata.py:130](../../../local_metadata.py#L130) · `function`.

```python
def archive(self, file):
```

Сохраняет исходные байты или снимок до миграции/архивирования.

Работает с таблицами legacy_documents.

Непосредственные вызовы: `icloud_access.read_bytes`, `self.key`, `self.connect`, `db.execute`, `hashlib.sha256(raw).hexdigest`, `hashlib.sha256`, `time.time`.

Выражения возврата (ветки читаются в исходнике):

```python
raw
```

## MetadataStore.error

[local_metadata.py:139](../../../local_metadata.py#L139) · `function`.

```python
def error(self, kind, path, error):
```

Записывает ошибку обработки для последующего показа или повтора.

Работает с таблицами metadata_imports.

Непосредственные вызовы: `unicodedata.normalize`, `self.connect`, `db.execute`, `str`, `time.time`.

## MetadataStore.imported

[local_metadata.py:146](../../../local_metadata.py#L146) · `function`.

```python
def imported(self, kind, path):
```

Фиксирует успешное завершение первоначального импорта записи.

Передаёт работу `self.error`.

Непосредственные вызовы: `self.error`.

## MetadataStore.complete

[local_metadata.py:151](../../../local_metadata.py#L151) · `function`.

```python
def complete(self, kind, path):
```

Проверяет завершение импорта либо меняет выполнение задачи по контракту модуля.

Работает с таблицами metadata_imports.

Непосредственные вызовы: `unicodedata.normalize`, `self.connect`, `bool`, `db.execute("SELECT 1 FROM metadata_imports WHERE kind=? AND path=? AND error=''", (kind, path)).fetchone`, `db.execute`.

Выражения возврата (ветки читаются в исходнике):

```python
bool(db.execute("SELECT 1 FROM metadata_imports WHERE kind=? AND path=? AND error=''", (kind, path)).fetchone())
```

## MetadataStore.backup

[local_metadata.py:158](../../../local_metadata.py#L158) · `function`.

```python
def backup(self, reason='daily'):
```

Создаёт согласованный SQLite-снимок и проверяет quick_check до публикации.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `folder.mkdir`, `time.strftime`, `target.exists`, `target.with_suffix`, `uuid.uuid4`, `closing`, `sqlite3.connect`, `self.store.database.resolve().as_uri`, `self.store.database.resolve`, `source.backup`, `destination.execute('PRAGMA quick_check').fetchone`, `destination.execute`, `ValueError`, `temporary.replace`, `temporary.unlink`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
target
```

## MetadataStore.comment

[local_metadata.py:178](../../../local_metadata.py#L178) · `function`.

```python
def comment(self, file):
```

Читает комментарий, при необходимости однократно импортируя прежний файл.

Возвращает `self._comment(file)`.

Непосредственные вызовы: `self._comment`.

Выражения возврата (ветки читаются в исходнике):

```python
self._comment(file)
```

## MetadataStore._comment

[local_metadata.py:185](../../../local_metadata.py#L185) · `function`.

```python
def _comment(self, file):
```

Читает комментарий, при необходимости однократно импортируя прежний файл.

Работает с таблицами metadata_imports.

Непосредственные вызовы: `self.key`, `self.get`, `self.connect`, `db.execute("SELECT 1 FROM metadata_imports WHERE kind='comment' AND path=? AND error=''", (path,)).fetchone`, `db.execute`, `file_comments.paths`, `target.exists`, `file_comments.parse`, `self.archive`, `unicodedata.normalize`, `Path`, `self.put`, `self.imported`, `self.error`.

Выражения возврата (ветки читаются в исходнике):

```python
{'comment': current['comment'], 'revision': current['revision']}
{'comment': '', 'revision': 'missing'}
{'comment': current['comment'], 'revision': current['revision']} if current else old
```

## MetadataStore.save_comment

[local_metadata.py:213](../../../local_metadata.py#L213) · `function`.

```python
def save_comment(self, file, comment, revision):
```

Сохраняет текст комментария с проверкой ожидаемой версии.

Возвращает `self._save_comment(file, comment, revision)`.

Непосредственные вызовы: `self._save_comment`.

Выражения возврата (ветки читаются в исходнике):

```python
self._save_comment(file, comment, revision)
```

## MetadataStore._save_comment

[local_metadata.py:220](../../../local_metadata.py#L220) · `function`.

```python
def _save_comment(self, file, comment, revision):
```

Сохраняет текст комментария с проверкой ожидаемой версии.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `len`, `ValueError`, `self.comment`, `self.put`, `self.key`, `comment.replace('\r\n', '\n').replace`, `comment.replace`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{'comment': saved['comment'], 'revision': saved['revision']}
```

## MetadataStore.card

[local_metadata.py:230](../../../local_metadata.py#L230) · `function`.

```python
def card(self, folder):
```

Архивирует исходные карточки и передаёт их существующему парсеру.

Возвращает `document.load(folder, self.store.labels)`.

Непосредственные вызовы: `file.exists`, `self.archive`, `document.load`.

Выражения возврата (ветки читаются в исходнике):

```python
document.load(folder, self.store.labels)
```

## MetadataStore.status

[local_metadata.py:241](../../../local_metadata.py#L241) · `function`.

```python
def status(self):
```

Возвращает состояние обработки и сохранённые ошибки.

Работает с таблицами metadata_imports, metadata_publications.

Непосредственные вызовы: `self.connect`, `db.execute`, `MIGRATION_LOCK.locked`, `db.execute("SELECT count(*) FROM metadata_imports WHERE error='' ").fetchone`, `recovery_backup.status`, `db.execute('SELECT count(*) FROM metadata_publications WHERE published=0').fetchone`, `dict`.

Выражения возврата (ветки читаются в исходнике):

```python
{'database_only': True, 'running': MIGRATION_LOCK.locked(), 'imported': db.execute("SELECT count(*) FROM metadata_imports WHERE error='' ").fetchone()[0], 'recovery_backup': recovery_backup.status(self.store.database), 'errors': errors, 'pending_documents': db.execute('SELECT count(*) FROM metadata_publications WHERE published=0').fetchone()[0], 'document_errors': [dict(r) for r in db.execute("SELECT path,error FROM metadata_publications WHERE error!=''")]}
```

## MetadataStore.publish

[local_metadata.py:252](../../../local_metadata.py#L252) · `function`.

```python
def publish(self, source, revision, folder, filename, body):
```

Добавляет неизменяемый документ в устойчивую очередь публикации.

Работает с таблицами metadata_publications.

Непосредственные вызовы: `self.key`, `self.connect`, `db.execute('SELECT * FROM metadata_publications WHERE source=? AND revision=?', (source, revision)).fetchone`, `db.execute`, `str`, `uuid.uuid4`.

Выражения возврата (ветки читаются в исходнике):

```python
{'path': row['path'], 'pending': not row['published'], 'error': row['error']}
```

## MetadataStore.sync

[local_metadata.py:263](../../../local_metadata.py#L263) · `function`.

```python
def sync(self):
```

Сериализует выпуск ожидающих неизменяемых документов через общую блокировку.

Передаёт работу `self._sync`.

Непосредственные вызовы: `self._sync`.

## MetadataStore._sync

[local_metadata.py:270](../../../local_metadata.py#L270) · `function`.

```python
def _sync(self):
```

Обрабатывает сохранённую очередь синхронизации или публикации.

Работает с таблицами metadata_publications.

Непосредственные вызовы: `self.connect`, `list`, `db.execute`, `any`, `part.startswith`, `Path`, `assert_unlocked`, `parent.is_symlink`, `ValueError`, `target.exists`, `target.read_bytes`, `target.with_name`, `temporary.open`, `stream.write`, `stream.flush`, `os.fsync`, `stream.fileno`, `rename_exclusive`, `temporary.unlink`, `str`, `int`.

Явные исключения: `ValueError`.

## MetadataStore.migrate

[local_metadata.py:305](../../../local_metadata.py#L305) · `function`.

```python
def migrate(self, app):
```

Переносит только допустимые прежние данные с сохранением исходников и истории.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `MIGRATION_LOCK.acquire`, `self.upgrade_restoration`, `os.walk`, `Path`, `d.startswith`, `(folder / d).is_symlink`, `folder.relative_to(self.root).as_posix`, `folder.relative_to`, `self.complete`, `self.imported`, `app.folder_role`, `self.card`, `self.store.get`, `app.folder_note_store().read`, `app.folder_note_store`, `app.client_activity_store().read`, `app.client_activity_store`, `app.object_activity_store().read`, `app.object_activity_store`, `self.error`, `name.startswith`, `file.is_symlink`, `app.is_print_folder`, `len`, `file.suffix.lower`, `self.is_publication`, `self.key`, `app.read_print_task`, `file.relative_to(self.root).as_posix`, `file.relative_to`, `comments.is_dir`, `comments.is_symlink`, `comments.glob`, `self.archive`, `raw.decode('utf-8-sig').splitlines`, `raw.decode`, `json.loads`, `isinstance`, `ValueError`, `self.comment`, `history.is_dir`, `history.is_symlink`, `(Path(old_parent) / d).is_symlink`, `file.is_file`, `MIGRATION_LOCK.release`.

Явные исключения: `ValueError`.

## MetadataStore.upgrade_restoration

[local_metadata.py:378](../../../local_metadata.py#L378) · `function`.

```python
def upgrade_restoration(self):
```

Обновляет прежние рецепты отката для сохранения новых полей SQLite.

Работает с таблицами sqlite_master.

Непосредственные вызовы: `self.connect`, `db.execute('SELECT 1 FROM sqlite_master WHERE name=?', (table,)).fetchone`, `db.execute`, `sessions.extend`, `Path`, `str`, `self.key`, `path.startswith`, `any`, `parent.is_symlink`, `ValueError`, `self.archive`, `source.read_bytes`, `order_document.atomic_write`, `new.decode`, `self.imported`, `self.error`.

Явные исключения: `ValueError`.

## MetadataStore.is_publication

[local_metadata.py:407](../../../local_metadata.py#L407) · `function`.

```python
def is_publication(self, path):
```

Проверяет, относится ли путь к выпущенному неизменяемому документу.

Работает с таблицами metadata_publications.

Непосредственные вызовы: `self.connect`, `bool`, `db.execute('SELECT 1 FROM metadata_publications WHERE path=?', (path,)).fetchone`, `db.execute`.

Выражения возврата (ветки читаются в исходнике):

```python
bool(db.execute('SELECT 1 FROM metadata_publications WHERE path=?', (path,)).fetchone())
```
