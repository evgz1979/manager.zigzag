# scripts/deploy_remote.py

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [scripts/deploy_remote.py:1](../../../scripts/deploy_remote.py#L1).

Удалённая часть деплоя. Запускается по SSH скриптом deploy.py.

Импорты Python, включая локальные: `configparser`, `contextlib`, `fcntl`, `hashlib`, `json`, `os`, `pathlib`, `plistlib`, `re`, `shutil`, `socket`, `sqlite3`, `subprocess`, `sys`, `tarfile`, `time`, `urllib.request`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## atomic_write

[scripts/deploy_remote.py:25](../../../scripts/deploy_remote.py#L25) · `function`.

```python
def atomic_write(path, body):
```

Записывает временный файл и атомарно заменяет предусмотренную цель.

Передаёт работу `path.with_name`, `temporary.open`, `os.fsync`.

Непосредственные вызовы: `path.with_name`, `temporary.open`, `stream.write`, `stream.flush`, `os.fsync`, `stream.fileno`, `temporary.replace`.

## write_json

[scripts/deploy_remote.py:36](../../../scripts/deploy_remote.py#L36) · `function`.

```python
def write_json(path, value):
```

Атомарно записывает JSON состояния релиза с переводом строки в конце.

Передаёт работу `atomic_write`, `(json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode`, `json.dumps`.

Непосредственные вызовы: `atomic_write`, `(json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode`, `json.dumps`.

## database_name

[scripts/deploy_remote.py:42](../../../scripts/deploy_remote.py#L42) · `function`.

```python
def database_name(documents):
```

Вычисляет имя SQLite по ключу абсолютного корня документов.

Возвращает `'orders-' + hashlib.sha256(str(documents).encode()).hexdigest()[:16] + '.sqlite3'`.

Непосредственные вызовы: `hashlib.sha256(str(documents).encode()).hexdigest`, `hashlib.sha256`, `str(documents).encode`, `str`.

Выражения возврата (ветки читаются в исходнике):

```python
'orders-' + hashlib.sha256(str(documents).encode()).hexdigest()[:16] + '.sqlite3'
```

## backup_database

[scripts/deploy_remote.py:48](../../../scripts/deploy_remote.py#L48) · `function`.

```python
def backup_database(source, destination):
```

Создаёт согласованный проверенный снимок перед переключением релиза.

При недопустимом состоянии возбуждает RuntimeError.

Непосредственные вызовы: `destination.exists`, `RuntimeError`, `closing`, `sqlite3.connect`, `source.as_uri`, `original.backup`, `backup.execute`, `backup.execute('PRAGMA quick_check').fetchone`.

Явные исключения: `RuntimeError`.

## unpack

[scripts/deploy_remote.py:64](../../../scripts/deploy_remote.py#L64) · `function`.

```python
def unpack(stream, destination, release):
```

Распаковывает проверенный пакет исходников в подготовленный каталог релиза.

При недопустимом состоянии возбуждает RuntimeError.

Непосредственные вызовы: `tarfile.open`, `set`, `PurePosixPath`, `item.isfile`, `name.is_absolute`, `str`, `RuntimeError`, `names.add`, `path.parent.mkdir`, `archive.extractfile`, `path.open`, `shutil.copyfileobj`, `json.loads`, `(destination / '.manifest.json').read_text`, `expected.add`, `(destination / '.release-id').read_text().strip`, `(destination / '.release-id').read_text`, `manifest['files'].items`, `hashlib.sha256((destination / name).read_bytes()).hexdigest`, `hashlib.sha256`, `(destination / name).read_bytes`.

Явные исключения: `RuntimeError`.

Выражения возврата (ветки читаются в исходнике):

```python
manifest
```

## install_database

[scripts/deploy_remote.py:91](../../../scripts/deploy_remote.py#L91) · `function`.

```python
def install_database(release_dir, history, data, documents, manifest):
```

Устанавливает только явно переданный первоначальный снимок базы.

Работает с таблицами sqlite_master.

Непосредственные вызовы: `manifest.get`, `database_name`, `database.is_file`, `RuntimeError`, `closing`, `sqlite3.connect`, `database.as_uri`, `db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='orders'").fetchone`, `db.execute`, `str`, `hashlib.sha256(source.read_bytes()).hexdigest`, `hashlib.sha256`, `source.read_bytes`, `target.exists`, `any`, `data.glob`, `source.rename`, `backup_database`, `imported.open`, `temporary.open`, `shutil.copyfileobj`, `output.flush`, `os.fsync`, `output.fileno`, `os.link`, `temporary.unlink`.

Явные исключения: `RuntimeError`.

## launchctl

[scripts/deploy_remote.py:124](../../../scripts/deploy_remote.py#L124) · `function`.

```python
def launchctl(*arguments, check=True):
```

Выполняет предусмотренную команду пользовательского launchd.

Запускает внешний процесс; параметры и ограничения заданы в теле функции.

Непосредственные вызовы: `subprocess.run`.

Выражения возврата (ветки читаются в исходнике):

```python
subprocess.run(['/bin/launchctl', *arguments], check=check, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
```

## service_loaded

[scripts/deploy_remote.py:130](../../../scripts/deploy_remote.py#L130) · `function`.

```python
def service_loaded(domain):
```

Проверяет регистрацию пользовательского сервиса launchd.

Возвращает `launchctl('print', domain + '/' + LABEL, check=False).returncode == 0`.

Непосредственные вызовы: `launchctl`.

Выражения возврата (ветки читаются в исходнике):

```python
launchctl('print', domain + '/' + LABEL, check=False).returncode == 0
```

## stop

[scripts/deploy_remote.py:136](../../../scripts/deploy_remote.py#L136) · `function`.

```python
def stop(domain):
```

Останавливает пользовательский сервис перед предусмотренной операцией.

При недопустимом состоянии возбуждает RuntimeError.

Непосредственные вызовы: `service_loaded`, `launchctl`, `range`, `time.sleep`, `RuntimeError`.

Явные исключения: `RuntimeError`.

## select_release

[scripts/deploy_remote.py:148](../../../scripts/deploy_remote.py#L148) · `function`.

```python
def select_release(root, release):
```

Проверяет и выбирает целевой сохранённый релиз для запуска.

Передаёт работу `temporary.unlink`, `temporary.symlink_to`, `Path`.

Непосредственные вызовы: `temporary.unlink`, `temporary.symlink_to`, `Path`, `temporary.replace`.

## prepare_launcher

[scripts/deploy_remote.py:157](../../../scripts/deploy_remote.py#L157) · `function`.

```python
def prepare_launcher(release_dir, root, documents):
```

Готовит запуск сервиса с параметрами текущей установки M4.

Запускает внешний процесс; параметры и ограничения заданы в теле функции.

Непосредственные вызовы: `hashlib.sha256(source.read_bytes()).hexdigest`, `hashlib.sha256`, `source.read_bytes`, `Path.home`, `ready.exists`, `binary.parent.mkdir`, `atomic_write`, `plistlib.dumps`, `subprocess.run`, `str`, `print`.

Выражения возврата (ветки читаются в исходнике):

```python
binary
```

## health

[scripts/deploy_remote.py:181](../../../scripts/deploy_remote.py#L181) · `function`.

```python
def health(port, release=None):
```

Проверяет ответ запускаемого сервера перед завершением переключения.

При недопустимом состоянии возбуждает RuntimeError.

Непосредственные вызовы: `urllib.request.urlopen`, `json.load`, `value.get`, `RuntimeError`.

Явные исключения: `RuntimeError`.

Выражения возврата (ветки читаются в исходнике):

```python
value
```

## prepare_renderers

[scripts/deploy_remote.py:191](../../../scripts/deploy_remote.py#L191) · `function`.

```python
def prepare_renderers(settings, release_dir):
```

Заранее собирает обязательные Swift-помощники до переключения кода.

Запускает внешний процесс; параметры и ограничения заданы в теле функции.

Непосредственные вызовы: `subprocess.run`, `RuntimeError`.

Явные исключения: `RuntimeError`.

## start

[scripts/deploy_remote.py:200](../../../scripts/deploy_remote.py#L200) · `function`.

```python
def start(domain, agent, port, release, documents):
```

Проверяет профиль и запускает отдельный loopback-слушатель внешнего входа.

При недопустимом состоянии возбуждает RuntimeError.

Непосредственные вызовы: `launchctl`, `str`, `time.monotonic`, `health`, `RuntimeError`, `urllib.request.urlopen`, `json.load`, `time.sleep`.

Явные исключения: `RuntimeError`.

Выражения возврата (ветки читаются в исходнике):

```python
value
```

## check_remote_access_compatibility

[scripts/deploy_remote.py:220](../../../scripts/deploy_remote.py#L220) · `function`.

```python
def check_remote_access_compatibility(config, release_dir):
```

Проверяет наличие обязательного защищённого входа в целевом релизе.

При недопустимом состоянии возбуждает RuntimeError.

Непосредственные вызовы: `config.getboolean`, `source.is_file`, `source.read_text`, `entry.is_file`, `entry.read_text`, `RuntimeError`.

Явные исключения: `RuntimeError`.

## check_event_rename_compatibility

[scripts/deploy_remote.py:231](../../../scripts/deploy_remote.py#L231) · `function`.

```python
def check_event_rename_compatibility(database, release_dir):
```

Проверяет поддержку незавершённых переименований целевым релизом.

Работает с таблицами sqlite_master, metadata_settings, invoices, event_renames, folder_renames.

Непосредственные вызовы: `database.exists`, `closing`, `sqlite3.connect`, `database.as_uri`, `db.execute("SELECT 1 FROM sqlite_master WHERE name='metadata_settings'").fetchone`, `db.execute`, `db.execute("SELECT 1 FROM metadata_settings WHERE key='telegram_calendar_commands' AND value='1'").fetchone`, `source.is_file`, `source.read_text`, `RuntimeError`, `db.execute("SELECT 1 FROM metadata_settings WHERE key='calendar_layout' AND value='1'").fetchone`, `db.execute("SELECT 1 FROM metadata_settings WHERE key='reconciliations' AND value='1'").fetchone`, `db.execute("SELECT 1 FROM metadata_settings WHERE key='purchase_suppliers' AND value='1'").fetchone`, `db.execute("SELECT 1 FROM metadata_settings WHERE key='telegram_inbox_delete' AND value='1'").fetchone`, `db.execute("SELECT 1 FROM metadata_settings WHERE key='telegram_inbox' AND value='1'").fetchone`, `(release_dir / 'local_metadata.py').is_file`, `db.execute("SELECT 1 FROM metadata_settings WHERE key='client_order_links' AND value='1'").fetchone`, `db.execute("SELECT 1 FROM metadata_settings WHERE key='client_order_link_roles' AND value='1'").fetchone`, `db.execute("SELECT 1 FROM metadata_settings WHERE key='client_order_link_status' AND value='1'").fetchone`, `db.execute("SELECT 1 FROM metadata_settings WHERE key='client_order_link_star' AND value='1'").fetchone`, `db.execute("SELECT 1 FROM metadata_settings WHERE key='weekly_events_unified' AND value='1'").fetchone`, `db.execute("SELECT 1 FROM metadata_settings WHERE key='calendar_event_relevance' AND value='1'").fetchone`, `db.execute("SELECT 1 FROM metadata_settings WHERE key='calendar_event_completion' AND value='1'").fetchone`, `db.execute("SELECT 1 FROM metadata_settings WHERE key='calendar_event_trip' AND value='1'").fetchone`, `db.execute("SELECT 1 FROM metadata_settings WHERE key='calendar_watch_todos' AND value='1'").fetchone`, `db.execute("SELECT 1 FROM metadata_settings WHERE key='order_calendar_colors' AND value='1'").fetchone`, `db.execute("SELECT 1 FROM metadata_settings WHERE key='invoice_payment_sources' AND value='1'").fetchone`, `db.execute("SELECT 1 FROM sqlite_master WHERE name='invoices'").fetchone`, `db.execute("SELECT 1 FROM invoices WHERE json_extract(data,'$._list_status')='paid' LIMIT 1").fetchone`, `db.execute("SELECT 1 FROM invoices WHERE json_type(data,'$._closing_documents') IS NOT NULL LIMIT 1").fetchone`, `(release_dir / 'invoice_documents.py').is_file`, `db.execute("SELECT 1 FROM invoices WHERE json_extract(data,'$.kind')='planned' AND json_extract(data,'$.period')='week' LIMIT 1").fetchone`, `db.execute("SELECT 1 FROM invoices WHERE json_extract(data,'$._trash') IS NOT NULL LIMIT 1").fetchone`, `db.execute("SELECT 1 FROM invoices WHERE json_extract(data,'$.kind')='planned' LIMIT 1").fetchone`, `(release_dir / 'event_folder_undo.py').is_file`, `db.execute("SELECT 1 FROM sqlite_master WHERE name='event_renames'").fetchone`, `db.execute("SELECT 1 FROM event_renames WHERE state='pending' LIMIT 1").fetchone`, `db.execute("SELECT 1 FROM sqlite_master WHERE name='folder_renames'").fetchone`, `any`, `pair.get`, `json.loads`, `(release_dir / 'folder_rename_undo.py').is_file`, `db.execute("SELECT 1 FROM folder_renames WHERE state='pending' LIMIT 1").fetchone`.

Явные исключения: `RuntimeError`.

## deploy

[scripts/deploy_remote.py:367](../../../scripts/deploy_remote.py#L367) · `function`.

```python
def deploy(settings, action, release):
```

Подготавливает и переключает проверенный релиз, сохраняя рабочую базу.

При недопустимом состоянии возбуждает RuntimeError.

Непосредственные вызовы: `Path`, `Path(settings['documents']).expanduser().resolve`, `Path(settings['documents']).expanduser`, `root.is_absolute`, `root.is_dir`, `root.is_symlink`, `documents.is_dir`, `RuntimeError`, `str`, `os.getuid`, `int`, `print`, `json.dumps`, `service_loaded`, `health`, `(root / '.deploy.lock').open`, `fcntl.flock`, `state_path.exists`, `json.loads`, `state_path.read_text`, `state.get`, `re.fullmatch`, `current.exists`, `current.is_symlink`, `current.resolve`, `socket.socket`, `probe.connect_ex`, `history_root.mkdir`, `time.strftime`, `time.gmtime`, `history.mkdir`, `write_json`, `data.mkdir`, `release_dir.mkdir`, `unpack`, `install_database`, `(release_dir / 'data').symlink_to`, `(release_dir / 'manager.ini').symlink_to`, `(release_dir / 'server.py').is_file`, `configparser.ConfigParser`, `config_path.exists`, `config.read`, `Path(config['storage']['root']).expanduser().resolve`, `Path(config['storage']['root']).expanduser`, `config.getint`, `atomic_write`, `f"[storage]\nroot = {documents}\n\n[server]\nhost = {settings['host']}\nport = {port}\n".encode`, `check_remote_access_compatibility`, `Path.home`, `agent.parent.mkdir`, `agent.exists`, `agent.read_bytes`, `logs.mkdir`, `prepare_renderers`, `prepare_launcher`, `stop`, `backup_database`, `database_name`, `check_event_rename_compatibility`, `select_release`, `plistlib.dumps`, `start`, `current.unlink`, `state_path.unlink`, `agent.unlink`.

Явные исключения: `RuntimeError`.
