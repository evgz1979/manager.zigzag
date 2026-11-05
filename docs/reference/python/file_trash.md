# file_trash.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [file_trash.py](../../../file_trash.py).

Recoverable file removal with a portable journal and standalone restoration.

Импорты Python, включая локальные: `contextlib`, `ctypes`, `datetime`, `fcntl`, `hashlib`, `json`, `os`, `pathlib`, `re`, `shutil`, `sqlite3`, `stat`, `threading`, `time`, `unicodedata`, `uuid`, `zoneinfo`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-TrashConflict"></a>

## TrashConflict

[file_trash.py](../../../file_trash.py) · `class`.

```python
class TrashConflict(ValueError):
```

Обозначает конфликт изменения в этом модуле.

Вызывающий обработчик использует тип исключения для отказа без подмены данных.

<a id="symbol-append"></a>

## append

[file_trash.py](../../../file_trash.py) · `function`.

```python
def append(session, **record):
```

Дописывает запись в устойчивый журнал операции.

Передаёт работу `datetime.now(ZoneInfo('Europe/Moscow')).isoformat`, `datetime.now`, `ZoneInfo`.

Непосредственные вызовы: `datetime.now(ZoneInfo('Europe/Moscow')).isoformat`, `datetime.now`, `ZoneInfo`, `(session / '.journal.jsonl').open`, `stream.write`, `json.dumps`, `stream.flush`, `os.fsync`, `stream.fileno`.

<a id="symbol-checked"></a>

## checked

[file_trash.py](../../../file_trash.py) · `function`.

```python
def checked(root, relative, hidden=False):
```

Проверяет путь и ограничения допустимой операции.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `ValueError`, `Path`, `path.is_absolute`, `any`, `part.startswith`, `range`, `len`, `(root / Path(*path.parts[:index])).is_symlink`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
root / path
```

<a id="symbol-database_move"></a>

## database_move

[file_trash.py](../../../file_trash.py) · `function`.

```python
def database_move(plan, operation, *, restore=False, finish=False):
```

Перепривязывает комментарии SQLite при журналируемом переносе файла.

Работает с таблицами metadata_file_moves, metadata_records.

Непосредственные вызовы: `plan.get`, `unicodedata.normalize`, `closing`, `sqlite3.connect`, `Path(plan['database']).as_uri`, `Path`, `db.execute`, `db.execute('SELECT state FROM metadata_file_moves WHERE session=? AND source=?', (plan['session'], source)).fetchone`, `db.execute("SELECT id FROM metadata_records WHERE kind='comment' AND path=?", (source,)).fetchone`, `db.execute("SELECT id FROM metadata_records WHERE kind='comment' AND path=?", (destination,)).fetchone`, `TrashConflict`.

Явные исключения: `TrashConflict`.

<a id="symbol-describe"></a>

## describe

[file_trash.py](../../../file_trash.py) · `function`.

```python
def describe(root, plan):
```

Готовит краткое описание сохранённого сеанса для интерфейса.

Работает с таблицами metadata_file_moves.

Непосредственные вызовы: `any`, `os.path.lexists`, `pending.append`, `same`, `removed.append`, `plan.get`, `closing`, `sqlite3.connect`, `Path(plan['database']).as_uri`, `Path`, `db.execute`, `len`.

Выражения возврата (ветки читаются в исходнике):

```python
{'session': plan['session'], 'folder': plan['folder'], 'created': plan['created'], 'files': pending, 'count': len(pending), 'removed': removed}
```

<a id="symbol-fingerprint"></a>

## fingerprint

[file_trash.py](../../../file_trash.py) · `function`.

```python
def fingerprint(path):
```

Вычисляет отпечаток метаданных объекта для проверки свежести.

Формирует возвращаемое значение из проверенного локального состояния.

Непосредственные вызовы: `path.lstat`, `stat.S_IFMT`.

Выражения возврата (ветки читаются в исходнике):

```python
{'device': value.st_dev, 'inode': value.st_ino, 'kind': stat.S_IFMT(value.st_mode), 'size': value.st_size, 'modified': value.st_mtime_ns}
```

<a id="symbol-list_sessions"></a>

## list_sessions

[file_trash.py](../../../file_trash.py) · `function`.

```python
def list_sessions(root, *, reader=None, errors=None):
```

Читает сохранённые сеансы корзины для интерфейса восстановления.

Возвращает `[]`; либо `sorted(result, key=lambda record: record['created'], reverse=True)`.

Непосредственные вызовы: `Path(root).resolve`, `Path`, `checked`, `HISTORY.as_posix`, `folder.exists`, `folder.iterdir`, `session.name.startswith`, `re.fullmatch`, `read_plan`, `describe`, `errors.append`, `str`, `result.append`, `sorted`.

Выражения возврата (ветки читаются в исходнике):

```python
[]
sorted(result, key=lambda record: record['created'], reverse=True)
```

<a id="symbol-preview"></a>

## preview

[file_trash.py](../../../file_trash.py) · `function`.

```python
def preview(root, folder, paths):
```

Готовит проверяемое предложение операции без её выполнения.

При недопустимом состоянии возбуждает FileNotFoundError, ValueError.

Непосредственные вызовы: `Path(root).resolve`, `Path`, `checked`, `parent.is_dir`, `FileNotFoundError`, `isinstance`, `len`, `any`, `ValueError`, `dict.fromkeys`, `path.is_file`, `stat.S_ISREG`, `path.lstat`, `items.append`, `path.stat`, `revision`.

Явные исключения: `FileNotFoundError`, `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{'folder': folder, 'files': items}
```

<a id="symbol-read_plan"></a>

## read_plan

[file_trash.py](../../../file_trash.py) · `function`.

```python
def read_plan(root, token, *, reader=None):
```

Читает и проверяет сохранённый план операции.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `session_path`, `checked`, `(session.relative_to(root) / '.plan.json').as_posix`, `session.relative_to`, `json.loads`, `reader(plan_path).decode`, `reader`, `plan_path.read_text`, `plan.get`, `str`, `ValueError`, `(Path(plan['folder']) / '.trash' / token).as_posix`, `Path`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
(session, plan)
```

<a id="symbol-remove"></a>

## remove

[file_trash.py](../../../file_trash.py) · `function`.

```python
def remove(root, folder, files, confirmed=False, database=None, *, token=None, invoice_id=None):
```

Журналируемо переносит подтверждённые файлы и связанные комментарии в корзину.

При недопустимом состоянии возбуждает ValueError, TrashConflict.

Непосредственные вызовы: `Path(root).resolve`, `Path`, `isinstance`, `any`, `ValueError`, `(session_path(root, token) / '.plan.json').exists`, `session_path`, `read_plan`, `saved.get`, `TrashConflict`, `resume`, `preview`, `item.get`, `len`, `zip`, `uuid.uuid4`, `enumerate`, `hashlib.sha256(unicodedata.normalize('NFC', path.name).encode()).hexdigest`, `hashlib.sha256`, `unicodedata.normalize('NFC', path.name).encode`, `unicodedata.normalize`, `checked`, `source.relative_to(root).as_posix`, `source.relative_to`, `source.exists`, `source.is_file`, `source.is_dir`, `operations.append`, `destination.relative_to(root).as_posix`, `destination.relative_to`, `fingerprint`, `session.mkdir`, `bool`, `str`, `datetime.now(ZoneInfo('Europe/Moscow')).isoformat`, `datetime.now`, `ZoneInfo`, `Path(database).resolve`, `before.exists`, `json.loads`, `before.read_text`, `save`, `helper.is_symlink`, `shutil.copyfile`, `helper.open`, `os.fsync`, `stream.fileno`, `(session / '.report.txt').write_text`.

Явные исключения: `ValueError`, `TrashConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
resume(root, token)
```

<a id="symbol-rename"></a>

## rename

[file_trash.py](../../../file_trash.py) · `function`.

```python
def rename(source, destination):
```

Переименовывает объект без перезаписи существующего назначения.

При недопустимом состоянии возбуждает OSError.

Непосредственные вызовы: `ctypes.CDLL`, `function`, `os.fsencode`, `ctypes.get_errno`, `OSError`, `os.strerror`, `str`.

Явные исключения: `OSError`.

<a id="symbol-restore"></a>

## restore

[file_trash.py](../../../file_trash.py) · `function`.

```python
def restore(root, token):
```

Проверяет сеанс и возвращает файлы и комментарии без перезаписи назначения.

При недопустимом состоянии возбуждает TrashConflict.

Непосредственные вызовы: `Path(root).resolve`, `Path`, `read_plan`, `(session / '.lock').open`, `fcntl.flock`, `set`, `journal.exists`, `journal.read_text(encoding='utf-8').splitlines`, `journal.read_text`, `line.endswith`, `json.loads`, `intents.add`, `reversed`, `list`, `enumerate`, `checked`, `os.path.lexists`, `same`, `database_move`, `TrashConflict`, `original.parent.is_dir`, `str`, `original.parent.relative_to`, `append`, `rename`, `restored.append`, `restore_invoice_record`, `describe`, `save`, `uuid.uuid4`.

Явные исключения: `TrashConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
result
```

<a id="symbol-restore_invoice_record"></a>

## restore_invoice_record

[file_trash.py](../../../file_trash.py) · `function`.

```python
def restore_invoice_record(plan):
```

Восстанавливает привязку копии счёта из самостоятельного журнала корзины.

Работает с таблицами invoices, invoice_history.

Непосредственные вызовы: `plan.get`, `closing`, `sqlite3.connect`, `Path(plan['database']).as_uri`, `Path`, `db.execute`, `db.execute('SELECT id,path,filename,data,revision FROM invoices WHERE id=?', (plan['invoice_id'],)).fetchone`, `TrashConflict`, `json.loads`, `data.get`, `(Path(row[1]) / '# bills' / row[2]).as_posix`, `data.pop`, `time.time`, `json.dumps`.

Явные исключения: `TrashConflict`.

<a id="symbol-resume"></a>

## resume

[file_trash.py](../../../file_trash.py) · `function`.

```python
def resume(root, token):
```

Завершает подготовленный перенос после сбоя без перезаписи сторон.

При недопустимом состоянии возбуждает TrashConflict.

Непосредственные вызовы: `Path(root).resolve`, `Path`, `read_plan`, `(session / '.lock').open`, `fcntl.flock`, `enumerate`, `checked`, `os.path.lexists`, `same`, `TrashConflict`, `database_move`, `source.is_file`, `next`, `revision`, `append`, `destination.parent.exists`, `str`, `destination.parent.relative_to`, `destination.parent.mkdir`, `rename`, `describe`, `after.exists`, `uuid.uuid4`, `save`.

Явные исключения: `TrashConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
result
```

<a id="symbol-revision"></a>

## revision

[file_trash.py](../../../file_trash.py) · `function`.

```python
def revision(path):
```

Вычисляет версию файлового состояния для обнаружения изменений.

Возвращает `hashlib.sha256(json.dumps([fingerprint(path), path.lstat().st_ctime_ns], sort_keys=True).encode()).hexdigest()`.

Непосредственные вызовы: `hashlib.sha256(json.dumps([fingerprint(path), path.lstat().st_ctime_ns], sort_keys=True).encode()).hexdigest`, `hashlib.sha256`, `json.dumps([fingerprint(path), path.lstat().st_ctime_ns], sort_keys=True).encode`, `json.dumps`, `fingerprint`, `path.lstat`.

Выражения возврата (ветки читаются в исходнике):

```python
hashlib.sha256(json.dumps([fingerprint(path), path.lstat().st_ctime_ns], sort_keys=True).encode()).hexdigest()
```

<a id="symbol-same"></a>

## same

[file_trash.py](../../../file_trash.py) · `function`.

```python
def same(path, expected):
```

Сравнивает текущий объект с сохранённым отпечатком.

Возвращает `False`; либо `all((value[key] == expected[key] for key in keys))`.

Непосредственные вызовы: `path.exists`, `path.is_symlink`, `fingerprint`, `expected.keys`, `all`.

Выражения возврата (ветки читаются в исходнике):

```python
False
all((value[key] == expected[key] for key in keys))
```

<a id="symbol-save"></a>

## save

[file_trash.py](../../../file_trash.py) · `function`.

```python
def save(path, value):
```

Сохраняет состояние плана корзины для продолжения после прерывания.

Передаёт работу `path.open`, `json.dump`, `os.fsync`.

Непосредственные вызовы: `path.open`, `json.dump`, `stream.write`, `stream.flush`, `os.fsync`, `stream.fileno`.

<a id="symbol-session_path"></a>

## session_path

[file_trash.py](../../../file_trash.py) · `function`.

```python
def session_path(root, token):
```

Проверяет путь конкретного сеанса журнала или корзины.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `re.fullmatch`, `ValueError`, `checked`, `(HISTORY / ('.' + token)).as_posix`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
checked(root, (HISTORY / ('.' + token)).as_posix(), hidden=True)
```
