# recovery_backup.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [recovery_backup.py](../../../recovery_backup.py).

Daily, self-contained recovery bundles; the live SQLite stays outside iCloud.

Импорты Python, включая локальные: `argparse`, `contextlib`, `datetime`, `fcntl`, `folder_layout`, `hashlib`, `json`, `os`, `pathlib`, `shutil`, `sqlite3`, `subprocess`, `sys`, `tempfile`, `threading`, `uuid`, `zipfile`, `zoneinfo`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-create"></a>

## create

[recovery_backup.py](../../../recovery_backup.py) · `function`.

```python
def create(database, root, app, *, now=None, force=False):
```

Создаёт и проверяет ZIP со снимком SQLite, исходниками и инструкцией восстановления.

Работает с таблицами sqlite_master.

Непосредственные вызовы: `Path(database).resolve`, `Path`, `Path(root).resolve`, `Path(app).resolve`, `(now or datetime.now(TIMEZONE)).astimezone`, `datetime.now`, `(database.parent / (database.stem + '-recovery-backup.lock')).open`, `fcntl.flock`, `due`, `database.is_file`, `root.is_dir`, `ValueError`, `tempfile.TemporaryDirectory`, `stage.mkdir`, `closing`, `sqlite3.connect`, `database.as_uri`, `original.backup`, `copy.execute('PRAGMA journal_mode=DELETE').fetchone`, `copy.execute`, `copy.execute('PRAGMA integrity_check').fetchall`, `copy.execute('SELECT count(*) FROM "' + name.replace('"', '""') + '"').fetchone`, `name.replace`, `snapshot.with_name`, `sidecar.exists`, `sidecar.stat`, `sidecar.unlink`, `source_files`, `source.relative_to`, `target.parent.mkdir`, `shutil.copyfile`, `(stage / 'application/server.py').is_file`, `Path.home`, `agent.is_file`, `agent.is_symlink`, `(stage / 'RESTORE.txt').write_text`, `now.isoformat`, `str`, `p.relative_to(stage).as_posix`, `p.relative_to`, `digest`, `p.stat`, `sorted`, `stage.rglob`, `p.is_file`, `(stage / 'manifest.json').write_text`, `json.dumps`, `subprocess.run`, `checked.stderr.strip`, `zipfile.ZipFile`, `source.is_file`, `output.write`, `source.relative_to(stage).as_posix`, `check.testzip`, `folder.is_symlink`, `folder.mkdir`, `uuid.uuid4`, `now.strftime`, `archive.open`, `pending.open`, `shutil.copyfileobj`, `output.flush`, `os.fsync`, `output.fileno`, `rename_exclusive`, `save_status`, `now.date().isoformat`, `now.date`, `target.stat`, `failure`, `pending.unlink`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
None
target
```

<a id="symbol-digest"></a>

## digest

[recovery_backup.py](../../../recovery_backup.py) · `function`.

```python
def digest(path):
```

Вычисляет SHA-256 файла резервной копии потоковым чтением.

Возвращает `value.hexdigest()`.

Непосредственные вызовы: `hashlib.sha256`, `Path(path).open`, `Path`, `iter`, `value.update`, `value.hexdigest`.

Выражения возврата (ветки читаются в исходнике):

```python
value.hexdigest()
```

<a id="symbol-due"></a>

## due

[recovery_backup.py](../../../recovery_backup.py) · `function`.

```python
def due(database, root, now=None):
```

Проверяет необходимость очередной ежедневной копии по Москве.

Формирует возвращаемое значение из проверенного локального состояния.

Непосредственные вызовы: `datetime.now`, `status`, `value.get`, `now.astimezone(TIMEZONE).date().isoformat`, `now.astimezone(TIMEZONE).date`, `now.astimezone`, `os.path.abspath`, `bool`.

Выражения возврата (ветки читаются в исходнике):

```python
value.get('day') != now.astimezone(TIMEZONE).date().isoformat() or value.get('root') != os.path.abspath(root) or value.get('format') != FORMAT_VERSION or bool(value.get('error'))
```

<a id="symbol-failure"></a>

## failure

[recovery_backup.py](../../../recovery_backup.py) · `function`.

```python
def failure(database, error):
```

Сохраняет ошибку резервного копирования для следующего повтора и интерфейса.

Передаёт работу `status`, `value.update`, `datetime.now(TIMEZONE).isoformat`.

Непосредственные вызовы: `status`, `value.update`, `str`, `datetime.now(TIMEZONE).isoformat`, `datetime.now`, `save_status`.

<a id="symbol-main"></a>

## main

[recovery_backup.py](../../../recovery_backup.py) · `function`.

```python
def main():
```

Разбирает параметры запуска и выполняет основной сценарий программы.

Передаёт работу `argparse.ArgumentParser`, `parser.add_argument`, `Path(__file__).resolve`.

Непосредственные вызовы: `argparse.ArgumentParser`, `parser.add_argument`, `Path(__file__).resolve`, `Path`, `parser.parse_args`, `create`, `print`.

<a id="symbol-save_status"></a>

## save_status

[recovery_backup.py](../../../recovery_backup.py) · `function`.

```python
def save_status(database, value):
```

Атомарно сохраняет локальное состояние создания резервной копии.

Передаёт работу `state_path`, `path.with_name`, `uuid.uuid4`.

Непосредственные вызовы: `state_path`, `path.with_name`, `uuid.uuid4`, `temporary.open`, `json.dump`, `stream.write`, `stream.flush`, `os.fsync`, `stream.fileno`, `temporary.replace`, `temporary.unlink`.

<a id="symbol-source_files"></a>

## source_files

[recovery_backup.py](../../../recovery_backup.py) · `function`.

```python
def source_files(app):
```

Собирает только исходники приложения без обхода рабочих документов и data.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `app.iterdir`, `(app / directory).is_symlink`, `ValueError`, `os.walk`, `d.startswith`, `(Path(base) / d).is_symlink`, `Path`, `files.extend`, `name.startswith`, `sorted`, `p.is_file`, `p.is_symlink`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
sorted((p for p in files if p.is_file() and (not p.is_symlink())))
```

<a id="symbol-state_path"></a>

## state_path

[recovery_backup.py](../../../recovery_backup.py) · `function`.

```python
def state_path(database):
```

Вычисляет локальный путь состояния резервного копирования.

Возвращает `database.parent / (database.stem + '-recovery-backup.json')`.

Непосредственные вызовы: `Path`.

Выражения возврата (ветки читаются в исходнике):

```python
database.parent / (database.stem + '-recovery-backup.json')
```

<a id="symbol-status"></a>

## status

[recovery_backup.py](../../../recovery_backup.py) · `function`.

```python
def status(database):
```

Возвращает состояние обработки и сохранённые ошибки.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `json.loads`, `state_path(database).read_text`, `state_path`, `isinstance`, `ValueError`, `str`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
value
{}
{'error': str(error)}
```

<a id="symbol-worker"></a>

## worker

[recovery_backup.py](../../../recovery_backup.py) · `function`.

```python
def worker(database, root, app):
```

Выполняет фоновый цикл обработки с контролем остановки или паузами.

Запускает внешний процесс; параметры и ограничения заданы в теле функции.

Непосредственные вызовы: `due`, `subprocess.run`, `str`, `Path`, `RuntimeError`, `result.stderr.strip`, `result.stdout.strip`, `print`, `failure`, `threading.Event().wait`, `threading.Event`.

Явные исключения: `RuntimeError`.
