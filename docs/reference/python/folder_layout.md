# folder_layout.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [folder_layout.py](../../../folder_layout.py).

Переносы папок без перезаписи, с устойчивым журналом и обратными операциями.

Импорты Python, включая локальные: `argparse`, `ctypes`, `datetime`, `errno`, `fcntl`, `json`, `os`, `pathlib`, `shutil`, `sqlite3`, `stat`, `zoneinfo`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-Plan"></a>

## Plan

[folder_layout.py](../../../folder_layout.py) · `class`.

```python
class Plan:
```

Хранит проверяемый план файловых операций и создаёт журнал отката.

Основные операции: __init__, mkdir, move, create_session.

<a id="symbol-Plan.__init__"></a>

## Plan.__init__

[folder_layout.py](../../../folder_layout.py) · `function`.

```python
def __init__(self, root, clients, *, service_roots=()):
```

Сохраняет зависимости и начальные параметры экземпляра.

Состояние и зависимости сохраняются в полях self для последующих операций.

Непосредственные вызовы: `Path(root).resolve`, `Path`, `list`, `set`.

Прямые присваивания полям/свойствам: `self.root`, `self.clients`, `self.service_roots`, `self.operations`, `self.directories`.

<a id="symbol-Plan.create_session"></a>

## Plan.create_session

[folder_layout.py](../../../folder_layout.py) · `function`.

```python
def create_session(self, notes, before):
```

Создаёт устойчивый сеанс плана и самостоятельную инструкцию отката.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `history.is_symlink`, `ValueError`, `history.mkdir`, `datetime.now(ZoneInfo('Europe/Moscow')).strftime`, `datetime.now`, `ZoneInfo`, `session.mkdir`, `str`, `getattr`, `save_json`, `shutil.copyfile`, `plan.get`, `enumerate`, `operation.get`, `(session / '.report.txt').write_text`, `'\n'.join`, `append`, `len`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
session
```

<a id="symbol-Plan.mkdir"></a>

## Plan.mkdir

[folder_layout.py](../../../folder_layout.py) · `function`.

```python
def mkdir(self, relative):
```

Добавляет или выполняет создание отсутствующей папки в плане.

При недопустимом состоянии возбуждает FileExistsError.

Непосредственные вызовы: `Path(relative).as_posix`, `Path`, `safe_path`, `exists`, `path.is_dir`, `FileExistsError`, `self.operations.append`, `self.directories.add`.

Явные исключения: `FileExistsError`.

<a id="symbol-Plan.move"></a>

## Plan.move

[folder_layout.py](../../../folder_layout.py) · `function`.

```python
def move(self, source, destination, reason, origin=None):
```

Переносит объект или событие с проверкой исходного и целевого состояния.

При недопустимом состоянии возбуждает FileExistsError, ValueError.

Непосредственные вызовы: `Path(source).as_posix`, `Path`, `Path(destination).as_posix`, `safe_path`, `exists`, `FileExistsError`, `len`, `os.fsencode`, `ValueError`, `self.operations.append`, `identity`.

Явные исключения: `FileExistsError`, `ValueError`.

<a id="symbol-append"></a>

## append

[folder_layout.py](../../../folder_layout.py) · `function`.

```python
def append(session, record):
```

Дописывает запись в устойчивый журнал операции.

Передаёт работу `datetime.now(ZoneInfo('Europe/Moscow')).isoformat`, `datetime.now`, `ZoneInfo`.

Непосредственные вызовы: `datetime.now(ZoneInfo('Europe/Moscow')).isoformat`, `datetime.now`, `ZoneInfo`, `(Path(session) / '.journal.jsonl').open`, `Path`, `stream.write`, `json.dumps`, `stream.flush`, `os.fsync`, `stream.fileno`.

<a id="symbol-apply"></a>

## apply

[folder_layout.py](../../../folder_layout.py) · `function`.

```python
def apply(session):
```

Применяет проверенную операцию или подготовленный план.

При недопустимом состоянии возбуждает ValueError, FileExistsError.

Непосредственные вызовы: `Path`, `load_plan`, `(session / '.lock').open`, `fcntl.flock`, `any`, `records`, `ValueError`, `enumerate`, `safe_path`, `plan.get`, `append`, `exists`, `FileExistsError`, `target.mkdir`, `identity`, `str`, `rename_exclusive`, `len`.

Явные исключения: `ValueError`, `FileExistsError`.

<a id="symbol-exists"></a>

## exists

[folder_layout.py](../../../folder_layout.py) · `function`.

```python
def exists(path):
```

Проверяет существование пути, включая повреждённые символические ссылки.

Возвращает `os.path.lexists(path)`.

Непосредственные вызовы: `os.path.lexists`.

Выражения возврата (ветки читаются в исходнике):

```python
os.path.lexists(path)
```

<a id="symbol-identity"></a>

## identity

[folder_layout.py](../../../folder_layout.py) · `function`.

```python
def identity(path):
```

Проверяет или вычисляет устойчивую идентичность объекта.

Возвращает `{'device': value.st_dev, 'inode': value.st_ino, 'kind': stat.S_IFMT(value.st_mode)}`.

Непосредственные вызовы: `Path(path).lstat`, `Path`, `stat.S_IFMT`.

Выражения возврата (ветки читаются в исходнике):

```python
{'device': value.st_dev, 'inode': value.st_ino, 'kind': stat.S_IFMT(value.st_mode)}
```

<a id="symbol-load_plan"></a>

## load_plan

[folder_layout.py](../../../folder_layout.py) · `function`.

```python
def load_plan(session):
```

Загружает и проверяет явно подготовленный план переносов.

Разбирает JSON; вызывающий код должен учитывать ошибки или неизвестный формат.

Непосредственные вызовы: `json.loads`, `(Path(session) / '.plan.json').read_text`, `Path`.

Выражения возврата (ветки читаются в исходнике):

```python
json.loads((Path(session) / '.plan.json').read_text(encoding='utf-8'))
```

<a id="symbol-records"></a>

## records

[folder_layout.py](../../../folder_layout.py) · `function`.

```python
def records(session):
```

Читает последовательность записей журнала операции.

Разбирает JSON; вызывающий код должен учитывать ошибки или неизвестный формат.

Непосредственные вызовы: `(Path(session) / '.journal.jsonl').read_text(encoding='utf-8').splitlines`, `(Path(session) / '.journal.jsonl').read_text`, `Path`, `json.loads`, `line.endswith`.

Выражения возврата (ветки читаются в исходнике):

```python
[json.loads(line) for line in lines if line.endswith('\n')]
```

<a id="symbol-rename_exclusive"></a>

## rename_exclusive

[folder_layout.py](../../../folder_layout.py) · `function`.

```python
def rename_exclusive(source, destination):
```

Выполняет macOS-перенос с запретом замены существующей цели.

При недопустимом состоянии возбуждает OSError.

Непосредственные вызовы: `ctypes.CDLL`, `function`, `os.fsencode`, `ctypes.get_errno`, `OSError`, `os.strerror`, `str`.

Явные исключения: `OSError`.

<a id="symbol-safe_path"></a>

## safe_path

[folder_layout.py](../../../folder_layout.py) · `function`.

```python
def safe_path(root, relative, clients, *, service_roots=()):
```

Проверяет границы корня, допустимую область и компоненты пути.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `Path`, `relative.is_absolute`, `ValueError`, `any`, `first.startswith`, `range`, `len`, `(root / Path(*relative.parts[:index])).is_symlink`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
root / relative
```

<a id="symbol-save_json"></a>

## save_json

[folder_layout.py](../../../folder_layout.py) · `function`.

```python
def save_json(path, value):
```

Сохраняет структурированный JSON в предусмотренный файл.

Передаёт работу `Path(path).open`, `Path`, `json.dump`.

Непосредственные вызовы: `Path(path).open`, `Path`, `json.dump`, `stream.write`, `stream.flush`, `os.fsync`, `stream.fileno`.

<a id="symbol-undo"></a>

## undo

[folder_layout.py](../../../folder_layout.py) · `function`.

```python
def undo(session, perform=False, *, coordinate_database=False, keep_directories=()):
```

Выполняет сохранённые обратные операции после проверки текущего состояния.

При недопустимом состоянии возбуждает ValueError, FileExistsError, OSError.

Непосредственные вызовы: `Path`, `load_plan`, `plan.get`, `ValueError`, `sqlite3.connect`, `Path(registration['database']).as_uri`, `registration.get`, `db.execute(f'SELECT 1 FROM {table} WHERE path=?', (registration['path'],)).fetchone`, `db.execute`, `(session / '.lock').open`, `fcntl.flock`, `records`, `sum`, `failed[index].get`, `reversed`, `list`, `intents.items`, `safe_path`, `commits.get(index, {}).get`, `commits.get`, `failed.get(index, {}).get`, `failed.get`, `operation.get`, `exists`, `identity`, `str`, `FileExistsError`, `append`, `any`, `target.iterdir`, `OSError`, `rename_exclusive`, `target.rmdir`.

Явные исключения: `ValueError`, `FileExistsError`, `OSError`.

Выражения возврата (ветки читаются в исходнике):

```python
sum((index not in reverted and (not (index in failed and (not failed[index].get('changed')))) for index in intents))
count
```
