# object_move.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [object_move.py](../../../object_move.py).

Move an entire client object, with a verified file inventory and background progress.

Импорты Python, включая локальные: `contextlib`, `ctypes`, `errno`, `file_trash`, `folder_layout`, `folder_notes`, `folder_rename`, `folder_structure`, `hashlib`, `json`, `order_folders`, `order_todos`, `orders`, `os`, `pathlib`, `re`, `sqlite3`, `stat`, `sys`, `threading`, `time`, `unicodedata`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-available"></a>

## available

[object_move.py](../../../object_move.py) · `function`.

```python
def available(relative, kind):
```

Проверяет роль объекта в обычной клиентской ветке.

Источник может быть вложен в группу объектов, но должен принадлежать конкретному клиенту.

Непосредственные вызовы: `bool`, `client_path`, `folder_rename.available`.

Выражения возврата (ветки читаются в исходнике):

```python
kind == 'object' and bool(client_path(relative)) and folder_rename.available(relative)
```

<a id="symbol-check_destination"></a>

## check_destination

[object_move.py](../../../object_move.py) · `function`.

```python
def check_destination(db, destination):
```

Проверяет данные назначения с учётом нечувствительности iCloud к регистру и нормализации.

История прежних путей не считается рабочей записью назначения.

Непосредственные вызовы: `unicodedata.normalize('NFC', destination).casefold`, `unicodedata.normalize`, `folder_rename.restore.table`, `db.execute`, `folder_rename.restore.inside`, `unicodedata.normalize('NFC', path).casefold`, `FolderRenameConflict`.

Явные исключения: `FolderRenameConflict`.

<a id="symbol-check_pending"></a>

## check_pending

[object_move.py](../../../object_move.py) · `function`.

```python
def check_pending(db, source):
```

Отсекает незаконченные операции, чьи журналы ещё привязаны к прежнему пути.

Проверяет создание заказов и корзину счетов до физического переноса.

Непосредственные вызовы: `folder_rename.restore.table`, `db.execute(f'SELECT 1 FROM {table} WHERE ({condition}) AND (path=? OR substr(path,1,?)=?)', (source, len(source) + 1, source + '/')).fetchone`, `db.execute`, `len`, `FolderRenameConflict`.

Явные исключения: `FolderRenameConflict`.

<a id="symbol-checked_id"></a>

## checked_id

[object_move.py](../../../object_move.py) · `function`.

```python
def checked_id(identity):
```

Сверяет формат идентификатора клиентского намерения.

Идентификатор возвращается в браузер без использования его в файловых путях.

Непосредственные вызовы: `isinstance`, `re.fullmatch`, `ValueError`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
identity
```

<a id="symbol-client_revision"></a>

## client_revision

[object_move.py](../../../object_move.py) · `function`.

```python
def client_revision(path, relative):
```

Привязывает выбор клиента к конкретному экземпляру его папки.

Отпечаток включает путь и идентичность каталога, без обхода его заказов.

Непосредственные вызовы: `hashlib.sha256(json.dumps([relative, layout.identity(path)], sort_keys=True).encode()).hexdigest`, `hashlib.sha256`, `json.dumps([relative, layout.identity(path)], sort_keys=True).encode`, `json.dumps`, `layout.identity`.

Выражения возврата (ветки читаются в исходнике):

```python
hashlib.sha256(json.dumps([relative, layout.identity(path)], sort_keys=True).encode()).hexdigest()
```

<a id="symbol-enable_cloud_reads"></a>

## enable_cloud_reads

[object_move.py](../../../object_move.py) · `function`.

```python
def enable_cloud_reads():
```

Разрешает фоновому потоку macOS материализовать файлы iCloud при обычном чтении.

Меняет политику только текущего потока, который существует до окончания операции.

Непосредственные вызовы: `ctypes.CDLL`, `policy`, `ctypes.get_errno`, `OSError`, `os.strerror`.

Явные исключения: `OSError`.

<a id="symbol-file_digest"></a>

## file_digest

[object_move.py](../../../object_move.py) · `function`.

```python
def file_digest(directory, name, info, on_bytes):
```

Читает обычный файл целиком и проверяет, что открытый файл не подменили.

Использует ограниченную память, не переходит по ссылкам, сообщает о прочитанных байтах.

Непосредственные вызовы: `os.fdopen`, `os.open`, `os.fstat`, `stream.fileno`, `fingerprint`, `ValueError`, `hashlib.sha256`, `iter`, `digest.update`, `len`, `on_bytes`, `digest.hexdigest`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
digest.hexdigest()
```

<a id="symbol-fingerprint"></a>

## fingerprint

[object_move.py](../../../object_move.py) · `function`.

```python
def fingerprint(info):
```

Формирует отпечаток файла или каталога, устойчивый к переносу родителя.

Идентичность каталога сравнивается отдельно от времени его изменения.

Непосредственные вызовы: `stat.S_IFMT`, `stat.S_ISDIR`.

Выражения возврата (ветки читаются в исходнике):

```python
identity
(*identity, info.st_size, info.st_mtime_ns)
```

<a id="symbol-inventory"></a>

## inventory

[object_move.py](../../../object_move.py) · `function`.

```python
def inventory(root, relative, *, expected=None, digests=None, read=False, progress=None):
```

Обходит все записи папки и по запросу сравнивает их байты и структуру.

Включает скрытые записи, пустые каталоги и сами ссылки, не читая цели ссылок.

Непосредственные вызовы: `sum`, `expected.values`, `os.open`, `Path`, `os.close`, `scan`, `os.fstat`, `entries.keys`, `expected.keys`, `ValueError`, `next`, `iter`, `report`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
(entries, checksums)
```

<a id="symbol-inventory.counted"></a>

## inventory.counted

[object_move.py](../../../object_move.py) · `function`.

```python
def counted(length):
```

Прибавляет только реально прочитанные из файла байты.

Вызывается для каждого блока потока.

Непосредственные вызовы: `report`.

<a id="symbol-inventory.record"></a>

## inventory.record

[object_move.py](../../../object_move.py) · `function`.

```python
def record(path, item):
```

Сохраняет элемент и сразу обнаруживает отсутствующую или изменённую запись.

Использует имена относительно объекта, а не абсолютные пути клиента.

Непосредственные вызовы: `ValueError`.

Явные исключения: `ValueError`.

<a id="symbol-inventory.report"></a>

## inventory.report

[object_move.py](../../../object_move.py) · `function`.

```python
def report(force=False):
```

Обновляет счётчики текущего этапа без публикации на каждый блок файла.

Принудительный отчёт ставится перед потенциально долгим чтением каталога или файла.

Непосредственные вызовы: `time.monotonic`, `progress`.

<a id="symbol-inventory.scan"></a>

## inventory.scan

[object_move.py](../../../object_move.py) · `function`.

```python
def scan(directory, prefix, info):
```

Обходит одну директорию по дескриптору, открывая дочерние каталоги без ссылок.

Ошибка любого чтения прерывает сверку и показывает затронутый путь.

Непосредственные вызовы: `record`, `fingerprint`, `report`, `os.scandir`, `entry.stat`, `stat.S_ISDIR`, `os.open`, `os.fstat`, `ValueError`, `scan`, `os.close`, `stat.S_ISLNK`, `os.readlink`, `stat.S_ISREG`, `file_digest`, `str`.

Явные исключения: `ValueError`.

<a id="symbol-move"></a>

## move

[object_move.py](../../../object_move.py) · `function`.

```python
def move(store, payload, progress, locks):
```

Проверяет содержимое и переносит объект через общий протокол файлового журнала.

SQLite получает новые пути только после совпадения всех отпечатков и SHA-256.

Непосредственные вызовы: `store.root.resolve`, `progress`, `enable_cloud_reads`, `move_paths`, `store.connect`, `folder_rename.restore.check`, `check_pending`, `check_destination`, `scan`, `len`, `sum`, `entries.values`, `locks`, `FolderRenameConflict`, `inventory`, `unicodedata.normalize`, `folder_rename.restore.remap_file_trash`, `file_trash.prepare_relocation`, `db.execute`, `folder_rename.relocate`.

Явные исключения: `FolderRenameConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
{**result, **totals}
```

<a id="symbol-move.scan"></a>

## move.scan

[object_move.py](../../../object_move.py) · `function`.

```python
def scan(phase, relative, **options):
```

Передаёт прогресс инвентаризации под именем текущего этапа.

Пустой current означает, что текущий обход завершён.

Непосредственные вызовы: `progress`, `inventory`.

Выражения возврата (ветки читаются в исходнике):

```python
inventory(root, relative, progress=progress, **options)
```

<a id="symbol-move.verify"></a>

## move.verify

[object_move.py](../../../object_move.py) · `function`.

```python
def verify(session):
```

Доказывает наличие всех исходных записей и читаемых байтов по новому пути.

При несовпадении общий перенос откатывает папку до любых изменений путей SQLite.

Непосредственные вызовы: `target`, `require_absent`, `client_revision`, `ValueError`, `scan`, `layout.save_json`, `inventory`.

Явные исключения: `ValueError`.

<a id="symbol-move_paths"></a>

## move_paths

[object_move.py](../../../object_move.py) · `function`.

```python
def move_paths(store, payload):
```

Проверяет подтверждённые пути и версии, включая замену папки назначения во время подготовки.

Возвращает прежнее имя объекта непосредственно под выбранным другим клиентом.

Непосредственные вызовы: `store.root.resolve`, `payload.get`, `target`, `available`, `folder_role`, `ValueError`, `client_path`, `folder_rename.preview`, `client_revision`, `FolderRenameConflict`, `(Path(client) / path.name).as_posix`, `Path`, `layout.exists`.

Явные исключения: `ValueError`, `FolderRenameConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
(view, destination)
```

<a id="symbol-preview"></a>

## preview

[object_move.py](../../../object_move.py) · `function`.

```python
def preview(store, relative):
```

Готовит форму переноса с клиентами корня и непосредственными клиентами числовых групп.

Сканирует только уровни каталога клиентов и сохраняет полные пути одноимённых клиентов.

Непосредственные вызовы: `store.root.resolve`, `target`, `available`, `folder_role`, `ValueError`, `client_path`, `folder_rename.preview`, `root.iterdir`, `parent.name.startswith`, `parent.is_symlink`, `parent.is_dir`, `is_catalog_group`, `parent.iterdir`, `candidate.name.startswith`, `candidate.is_symlink`, `candidate.is_dir`, `candidate.relative_to(root).as_posix`, `candidate.relative_to`, `clients.append`, `client_revision`, `sorted`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{**view, 'clients': sorted(clients, key=lambda item: item['path'].casefold())}
```

<a id="symbol-require_absent"></a>

## require_absent

[object_move.py](../../../object_move.py) · `function`.

```python
def require_absent(path):
```

Подтверждает отсутствие старого пути, пропуская только явный ENOENT.

Ошибки доступа и iCloud останавливают сверку.

Непосредственные вызовы: `path.lstat`, `ValueError`, `str`.

Явные исключения: `ValueError`.

<a id="symbol-saved_status"></a>

## saved_status

[object_move.py](../../../object_move.py) · `function`.

```python
def saved_status(store, identity):
```

Восстанавливает статус по устойчивому журналу SQLite после перезапуска сервера.

Незавершённый перенос требует согласованного восстановления через .restore.py.

Непосредственные вызовы: `store.database.exists`, `store.database.resolve().as_uri`, `store.database.resolve`, `closing`, `sqlite3.connect`, `folder_rename.restore.table`, `db.execute`, `json.loads`, `mapping.get`, `Path(session).relative_to(store.root.resolve()).as_posix`, `Path(session).relative_to`, `Path`, `store.root.resolve`.

Выражения возврата (ветки читаются в исходнике):

```python
{**result, 'phase': 'complete'}
{**result, 'phase': 'failed', 'error': error}
None
```

<a id="symbol-start"></a>

## start

[object_move.py](../../../object_move.py) · `function`.

```python
def start(store, payload, locks, after_move):
```

Принимает одно подтверждённое намерение и запускает перенос в отдельном потоке.

Повтор того же идентификатора возвращает статус, а параллельный перенос отклоняется.

Непосредственные вызовы: `checked_id`, `payload.get`, `ValueError`, `any`, `isinstance`, `saved_status`, `JOBS.get`, `dict`, `JOBS.items`, `FolderRenameConflict`, `threading.Thread`, `JOB_THREADS.add`, `thread.start`, `JOB_THREADS.discard`, `progress`, `str`.

Явные исключения: `ValueError`, `FolderRenameConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
dict(previous)
initial
```

<a id="symbol-start.progress"></a>

## start.progress

[object_move.py](../../../object_move.py) · `function`.

```python
def progress(**fields):
```

Публикует короткий снимок прогресса для HTTP-опроса.

Никогда не держит блокировку статуса во время чтения файлов или SQLite.

Непосредственные вызовы: `job.update`.

<a id="symbol-start.work"></a>

## start.work

[object_move.py](../../../object_move.py) · `function`.

```python
def work():
```

Запускает перенос и сообщает о завершении или восстановлении исходного пути.

Сбой последующего обновления индексов не меняет результат уже сохранённой операции.

Непосредственные вызовы: `move`, `progress`, `str`, `after_move`, `JOB_THREADS.discard`, `threading.current_thread`.

<a id="symbol-status"></a>

## status

[object_move.py](../../../object_move.py) · `function`.

```python
def status(store, identity):
```

Возвращает последний прогресс без ожидания iCloud или блокировки файловой операции.

При отсутствии процесса читает подтверждённое состояние журнала.

Непосредственные вызовы: `checked_id`, `JOBS.get`, `dict`, `saved_status`, `FileNotFoundError`.

Явные исключения: `FileNotFoundError`.

Выражения возврата (ветки читаются в исходнике):

```python
dict(job)
saved
```

<a id="symbol-target"></a>

## target

[object_move.py](../../../object_move.py) · `function`.

```python
def target(root, relative):
```

Проверяет точный существующий путь объекта или клиента.

Запрещает ссылки, подмену компонентов и альтернативное написание существующего пути.

Непосредственные вызовы: `isinstance`, `Path(relative).as_posix`, `Path`, `ValueError`, `folder_rename.target`, `os.scandir`, `any`, `item.is_dir`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
path
```

<a id="symbol-wait_for_jobs"></a>

## wait_for_jobs

[object_move.py](../../../object_move.py) · `function`.

```python
def wait_for_jobs():
```

Дожидается завершения уже принятых фоновых переносов перед остановкой сервера.

Вызывать после завершения HTTP-обработчиков, способных создать новые задания.

Непосредственные вызовы: `tuple`, `thread.join`.
