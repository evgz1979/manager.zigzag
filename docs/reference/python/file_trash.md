# file_trash.py

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [file_trash.py:1](../../../file_trash.py#L1).

Recoverable file removal with a portable journal and standalone restoration.

Импорты Python, включая локальные: `contextlib`, `ctypes`, `datetime`, `fcntl`, `hashlib`, `json`, `os`, `pathlib`, `re`, `shutil`, `sqlite3`, `stat`, `threading`, `time`, `unicodedata`, `uuid`, `zoneinfo`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## TrashConflict

[file_trash.py:26](../../../file_trash.py#L26) · `class`.

```python
class TrashConflict(ValueError):
```

Обозначает конфликт изменения в этом модуле.

Вызывающий обработчик использует тип исключения для отказа без подмены данных.

## checked

[file_trash.py:32](../../../file_trash.py#L32) · `function`.

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

## fingerprint

[file_trash.py:46](../../../file_trash.py#L46) · `function`.

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

## revision

[file_trash.py:54](../../../file_trash.py#L54) · `function`.

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

## same

[file_trash.py:60](../../../file_trash.py#L60) · `function`.

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

## rename

[file_trash.py:70](../../../file_trash.py#L70) · `function`.

```python
def rename(source, destination):
```

Переименовывает объект без перезаписи существующего назначения.

При недопустимом состоянии возбуждает OSError.

Непосредственные вызовы: `ctypes.CDLL`, `function`, `os.fsencode`, `ctypes.get_errno`, `OSError`, `os.strerror`, `str`.

Явные исключения: `OSError`.

## append

[file_trash.py:81](../../../file_trash.py#L81) · `function`.

```python
def append(session, **record):
```

Дописывает запись в устойчивый журнал операции.

Передаёт работу `datetime.now(ZoneInfo('Europe/Moscow')).isoformat`, `datetime.now`, `ZoneInfo`.

Непосредственные вызовы: `datetime.now(ZoneInfo('Europe/Moscow')).isoformat`, `datetime.now`, `ZoneInfo`, `(session / '.journal.jsonl').open`, `stream.write`, `json.dumps`, `stream.flush`, `os.fsync`, `stream.fileno`.

## save

[file_trash.py:91](../../../file_trash.py#L91) · `function`.

```python
def save(path, value):
```

Сохраняет состояние плана корзины для продолжения после прерывания.

Передаёт работу `path.open`, `json.dump`, `os.fsync`.

Непосредственные вызовы: `path.open`, `json.dump`, `stream.write`, `stream.flush`, `os.fsync`, `stream.fileno`.

## preview

[file_trash.py:101](../../../file_trash.py#L101) · `function`.

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

## session_path

[file_trash.py:121](../../../file_trash.py#L121) · `function`.

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

## read_plan

[file_trash.py:129](../../../file_trash.py#L129) · `function`.

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

## describe

[file_trash.py:148](../../../file_trash.py#L148) · `function`.

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

## database_move

[file_trash.py:168](../../../file_trash.py#L168) · `function`.

```python
def database_move(plan, operation, *, restore=False, finish=False):
```

Перепривязывает комментарии SQLite при журналируемом переносе файла.

Работает с таблицами metadata_file_moves, metadata_records.

Непосредственные вызовы: `plan.get`, `unicodedata.normalize`, `closing`, `sqlite3.connect`, `Path(plan['database']).as_uri`, `Path`, `db.execute`, `db.execute('SELECT state FROM metadata_file_moves WHERE session=? AND source=?', (plan['session'], source)).fetchone`, `db.execute("SELECT id FROM metadata_records WHERE kind='comment' AND path=?", (source,)).fetchone`, `db.execute("SELECT id FROM metadata_records WHERE kind='comment' AND path=?", (destination,)).fetchone`, `TrashConflict`.

Явные исключения: `TrashConflict`.

## remove

[file_trash.py:199](../../../file_trash.py#L199) · `function`.

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

## resume

[file_trash.py:261](../../../file_trash.py#L261) · `function`.

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

## restore_invoice_record

[file_trash.py:307](../../../file_trash.py#L307) · `function`.

```python
def restore_invoice_record(plan):
```

Восстанавливает привязку копии счёта из самостоятельного журнала корзины.

Работает с таблицами invoices, invoice_history.

Непосредственные вызовы: `plan.get`, `closing`, `sqlite3.connect`, `Path(plan['database']).as_uri`, `Path`, `db.execute`, `db.execute('SELECT id,path,filename,data,revision FROM invoices WHERE id=?', (plan['invoice_id'],)).fetchone`, `TrashConflict`, `json.loads`, `data.get`, `(Path(row[1]) / '# bills' / row[2]).as_posix`, `data.pop`, `time.time`, `json.dumps`.

Явные исключения: `TrashConflict`.

## list_sessions

[file_trash.py:330](../../../file_trash.py#L330) · `function`.

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

## restore

[file_trash.py:356](../../../file_trash.py#L356) · `function`.

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
