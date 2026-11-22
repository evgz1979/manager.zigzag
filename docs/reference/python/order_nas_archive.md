# order_nas_archive.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [order_nas_archive.py](../../../order_nas_archive.py).

Archive an unregistered client order as a verified ZIP on mounted SMB.

Импорты Python, включая локальные: `file_trash`, `folder_layout`, `folder_notes`, `folder_rename`, `folder_rename_undo`, `folder_structure`, `hashlib`, `json`, `nas_archive`, `object_move`, `order_folders`, `order_todos`, `orders`, `os`, `pathlib`, `shutil`, `stat`, `subprocess`, `threading`, `unicodedata`, `uuid`, `zipfile`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-archive_order"></a>

## archive_order

[order_nas_archive.py](../../../order_nas_archive.py) · `function`.

```python
def archive_order(store, payload, locks, progress):
```

Создаёт архив на SMB и только после сверки исключает исходную папку из рабочего дерева.

Снимок и журнал общего переноса сохраняют метаданные и позволяют откатить незавершённый шаг.

Непосредственные вызовы: `nas_archive.settings`, `store.connect`, `preview`, `folder_rename.FolderRenameConflict`, `object_move.check_pending`, `object_move.enable_cloud_reads`, `store.root.resolve`, `Path`, `(Path(source).parent / (paths.ORDER_NAS_STAGING_PREFIX + identity)).as_posix`, `nas_archive.mounted_root`, `nas_archive.descend`, `check_mount`, `progress`, `object_move.inventory`, `os.open`, `os.fdopen`, `os.fstat`, `file.fileno`, `subprocess.run`, `str`, `os.fsync`, `verify_zip`, `ValueError`, `locks`, `paths.remap_file_trash`, `unicodedata.normalize`, `file_trash.prepare_relocation`, `db.execute`, `folder_rename.relocate`, `object_move.fingerprint`, `final.lstat`, `shutil.rmtree`, `Path(source).parent.as_posix`, `os.path.samestat`, `os.unlink`.

Явные исключения: `folder_rename.FolderRenameConflict`, `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{'path': Path(source).parent.as_posix(), 'nas_path': str(final), 'journal': result['journal'], 'warning': warning}
```

<a id="symbol-archive_order.confirm_copy"></a>

## archive_order.confirm_copy

[order_nas_archive.py](../../../order_nas_archive.py) · `function`.

```python
def confirm_copy(session):
```

Фиксирует проверку ZIP перед фиксацией перепривязки SQLite.

Файловый журнал возвращает рабочую папку, если этот шаг прерван.

Непосредственные вызовы: `check_mount`, `object_move.inventory`, `object_move.fingerprint`, `final.lstat`, `ValueError`, `folder_layout.save_json`, `str`.

Явные исключения: `ValueError`.

<a id="symbol-available"></a>

## available

[order_nas_archive.py](../../../order_nas_archive.py) · `function`.

```python
def available(store, relative, role, order):
```

Определяет доступность удаления для снятого с учёта клиентского заказа.

Новая папка, зарегистрированный заказ и служебные разделы не подходят.

Непосредственные вызовы: `bool`, `order_folders.can_manage_service_folders`.

Выражения возврата (ветки читаются в исходнике):

```python
bool(store.database_only and order and (order['registered'] == 0) and order_folders.can_manage_service_folders(relative, role))
```

<a id="symbol-check_mount"></a>

## check_mount

[order_nas_archive.py](../../../order_nas_archive.py) · `function`.

```python
def check_mount(directory, path):
```

Проверяет, что путь Finder по-прежнему указывает на открытый каталог SMB.

Обнаруживает отмонтирование, замену каталога или появление ссылки.

Непосредственные вызовы: `os.path.samestat`, `os.fstat`, `path.lstat`, `OSError`.

Явные исключения: `OSError`.

<a id="symbol-preview"></a>

## preview

[order_nas_archive.py](../../../order_nas_archive.py) · `function`.

```python
def preview(store, relative, *, identity=None, config=None, db=None):
```

Формирует подтверждение с исходным путём, точным ZIP и версией заказа.

Проверяет наличие снятой регистрации по текущему пути внутри рабочей базы.

Непосредственные вызовы: `nas_archive.settings`, `store.connect`, `preview`, `uuid.uuid4`, `store.path`, `folder_rename.preview`, `folder_role`, `db.execute('SELECT id,revision,registered FROM orders WHERE path=?', (relative,)).fetchone`, `db.execute`, `available`, `ValueError`, `db.execute('SELECT 1 FROM orders WHERE registered=1 AND substr(path,1,?)=? LIMIT 1', (len(relative) + 1, relative + '/')).fetchone`, `len`, `Path(relative).name.encode()[:255 - len(suffix.encode())].decode`, `Path(relative).name.encode`, `Path`, `suffix.encode`, `hashlib.sha256(json.dumps([view['revision'], row['id'], row['revision'], identity, config]).encode()).hexdigest`, `hashlib.sha256`, `json.dumps([view['revision'], row['id'], row['revision'], identity, config]).encode`, `json.dumps`, `archive.as_posix`, `(nas_archive.VOLUMES / config['root'].lstrip('/') / archive).as_posix`, `config['root'].lstrip`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
preview(store, relative, identity=identity or uuid.uuid4().hex, config=config, db=connection)
{**view, 'id': identity, 'revision': revision, 'archive': archive.as_posix(), 'nas_path': (nas_archive.VOLUMES / config['root'].lstrip('/') / archive).as_posix()}
```

<a id="symbol-start"></a>

## start

[order_nas_archive.py](../../../order_nas_archive.py) · `function`.

```python
def start(store, payload, locks, after_move):
```

Запускает одно подтверждённое архивирование в отдельном потоке.

Повтор идентификатора возвращает существующее задание, параллельные записи на NAS не запускаются.

Непосредственные вызовы: `object_move.checked_id`, `payload.get`, `ValueError`, `status`, `store.path`, `preview`, `folder_rename.FolderRenameConflict`, `dict`, `list`, `threading.Thread`, `WORKERS.add`, `thread.start`, `WORKERS.remove`.

Явные исключения: `ValueError`, `folder_rename.FolderRenameConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
status(store, identity)
dict(JOBS[key])
initial
```

<a id="symbol-start.progress"></a>

## start.progress

[order_nas_archive.py](../../../order_nas_archive.py) · `function`.

```python
def progress(**fields):
```

Публикует снимок фазы для опроса в браузере.

Не удерживает блокировку статуса во время операций с файлами или базой.

Непосредственные вызовы: `job.update`.

<a id="symbol-start.work"></a>

## start.work

[order_nas_archive.py](../../../order_nas_archive.py) · `function`.

```python
def work():
```

Выполняет принятое подтверждение и обновляет индексы при успехе.

Ошибка фонового обновления не меняет итог сохранённого переноса.

Непосредственные вызовы: `archive_order`, `progress`, `(error.stderr or '').strip`, `str`, `after_move`, `WORKERS.discard`, `threading.current_thread`.

<a id="symbol-status"></a>

## status

[order_nas_archive.py](../../../order_nas_archive.py) · `function`.

```python
def status(store, identity):
```

Возвращает прогресс по идентификатору, после перезапуска читает итог из SQLite.

Журнал хранит путь ZIP даже при обрыве ответа и смене браузерной вкладки.

Непосредственные вызовы: `object_move.checked_id`, `JOBS.get`, `dict`, `store.database.exists`, `store.connect`, `paths.table`, `db.execute`, `json.loads`, `mapping.get`, `os.path.lexists`, `str`, `Path(source).parent.as_posix`, `Path`, `FileNotFoundError`.

Явные исключения: `FileNotFoundError`.

Выражения возврата (ветки читаются в исходнике):

```python
dict(job)
{'id': identity, 'source': source, 'path': Path(source).parent.as_posix(), 'nas_path': mapping['nas_path'], 'phase': 'complete', 'warning': warning}
{'id': identity, 'source': source, 'phase': 'failed', 'error': 'Перенос прерван или отменён. Проверь журнал: ' + row['session']}
```

<a id="symbol-verify_zip"></a>

## verify_zip

[order_nas_archive.py](../../../order_nas_archive.py) · `function`.

```python
def verify_zip(archive, name, entries, digests):
```

Сверяет структуру ZIP, цели ссылок и SHA-256 всех обычных файлов.

Читает архив с NAS и проверяет CRC также у служебных записей метаданных macOS.

Непосредственные вызовы: `unicodedata.normalize`, `entries.items`, `len`, `ValueError`, `os.fdopen`, `os.open`, `os.fstat`, `file.fileno`, `stat.S_ISREG`, `zipfile.ZipFile`, `set`, `saved.infolist`, `member.filename.encode('cp437').decode`, `member.filename.encode`, `seen.add`, `key.startswith`, `saved.open`, `stream.read`, `key[len(prefix):].rstrip`, `remaining.pop`, `stat.S_IFMT`, `hashlib.sha256`, `iter`, `digest.update`, `digest.hexdigest`, `os.fsencode`, `next`, `object_move.fingerprint`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
object_move.fingerprint(before)
```

<a id="symbol-wait_for_jobs"></a>

## wait_for_jobs

[order_nas_archive.py](../../../order_nas_archive.py) · `function`.

```python
def wait_for_jobs():
```

Дожидается архивации при штатном завершении сервера.

Блокировка статуса освобождается до ожидания потока.

Непосредственные вызовы: `tuple`, `worker.join`.
