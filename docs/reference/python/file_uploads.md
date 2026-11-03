# file_uploads.py

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [file_uploads.py:1](../../../file_uploads.py#L1).

Stream browser files into an existing event directory without overwriting files.

Импорты Python, включая локальные: `errno`, `event_folder_undo`, `file_trash`, `folder_layout`, `folder_notes`, `folder_structure`, `hashlib`, `json`, `order_folders`, `os`, `pathlib`, `threading`, `unicodedata`, `uuid`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## UploadConflict

[file_uploads.py:26](../../../file_uploads.py#L26) · `class`.

```python
class UploadConflict(ValueError):
```

Обозначает конфликт изменения в этом модуле.

Вызывающий обработчик использует тип исключения для отказа без подмены данных.

## UploadTooLarge

[file_uploads.py:32](../../../file_uploads.py#L32) · `class`.

```python
class UploadTooLarge(ValueError):
```

Обозначает превышение размера в этом модуле.

Вызывающий обработчик использует тип исключения для отказа без подмены данных.

## UploadBusy

[file_uploads.py:38](../../../file_uploads.py#L38) · `class`.

```python
class UploadBusy(ValueError):
```

Обозначает занятость обработчика в этом модуле.

Вызывающий обработчик использует тип исключения для отказа без подмены данных.

## available

[file_uploads.py:44](../../../file_uploads.py#L44) · `function`.

```python
def available(root, relative):
```

Проверяет доступность операции для роли и состояния цели.

Возвращает `False`; либо `True`.

Непосредственные вызовы: `file_trash.checked`, `Path(root).resolve`, `Path`, `is_freza_task`, `folder_role`, `len`, `is_work_root`, `bool`, `parent_order`.

Выражения возврата (ветки читаются в исходнике):

```python
False
True
bool(parent_order(root, relative))
```

## target

[file_uploads.py:63](../../../file_uploads.py#L63) · `function`.

```python
def target(root, relative):
```

Находит допустимую существующую цель файловой операции.

При недопустимом состоянии возбуждает ValueError, FileNotFoundError.

Непосредственные вызовы: `isinstance`, `ValueError`, `file_trash.checked`, `Path(root).resolve`, `Path`, `path.is_dir`, `FileNotFoundError`, `available`.

Явные исключения: `ValueError`, `FileNotFoundError`.

Выражения возврата (ветки читаются в исходнике):

```python
path
```

## token

[file_uploads.py:76](../../../file_uploads.py#L76) · `function`.

```python
def token(root, relative, folder=None):
```

Создаёт подписанный либо вычисляемый проверочный токен текущего контекста.

Возвращает `hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()`.

Непосредственные вызовы: `target`, `str`, `Path(root).resolve`, `Path`, `unicodedata.normalize`, `folder_layout.identity`, `hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest`, `hashlib.sha256`, `json.dumps(value, sort_keys=True).encode`, `json.dumps`.

Выражения возврата (ветки читаются в исходнике):

```python
hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
```

## options

[file_uploads.py:84](../../../file_uploads.py#L84) · `function`.

```python
def options(root, relative):
```

Возвращает ограничения и привязку формы загрузки файлов.

Возвращает `{'token': token(root, relative, folder), 'maxBytes': MAX_BYTES, 'maxFiles': MAX_FILES}`.

Непосредственные вызовы: `target`, `token`.

Выражения возврата (ветки читаются в исходнике):

```python
{'token': token(root, relative, folder), 'maxBytes': MAX_BYTES, 'maxFiles': MAX_FILES}
```

## filename

[file_uploads.py:91](../../../file_uploads.py#L91) · `function`.

```python
def filename(value):
```

Проверяет имя создаваемого или переименовываемого объекта.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `value.startswith`, `any`, `ord`, `ValueError`, `unicodedata.normalize`, `value.casefold`, `name.casefold`, `len`, `os.fsencode`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
value
```

## reserved_names

[file_uploads.py:102](../../../file_uploads.py#L102) · `function`.

```python
def reserved_names(db, relative):
```

Собирает имена, которые нельзя занять новой загрузкой.

Работает с таблицами sqlite_master, invoices.

Непосредственные вызовы: `unicodedata.normalize`, `set`, `db.execute`, `reserve`, `(Path(path) / '# bills' / name).as_posix`, `Path`.

Выражения возврата (ветки читаются в исходнике):

```python
names
```

## reserved_names.reserve

[file_uploads.py:107](../../../file_uploads.py#L107) · `function`.

```python
def reserve(path):
```

Занимает свободное имя файла для текущей загрузки.

Передаёт работу `unicodedata.normalize`, `path.startswith`, `names.add`.

Непосредственные вызовы: `unicodedata.normalize`, `path.startswith`, `names.add`, `path[len(prefix):].split('/', 1)[0].casefold`, `path[len(prefix):].split`, `len`.

## receive

[file_uploads.py:125](../../../file_uploads.py#L125) · `function`.

```python
def receive(store, relative, expected, name, source, size):
```

Принимает ограниченный поток файла и публикует его без перезаписи.

При недопустимом состоянии возбуждает ValueError, UploadTooLarge, UploadBusy.

Непосредственные вызовы: `isinstance`, `ValueError`, `UploadTooLarge`, `filename`, `SLOTS.acquire`, `UploadBusy`, `uuid.uuid4`, `target`, `guard_database`, `store.get`, `is_freza_task`, `token`, `UploadConflict`, `os.open`, `os.fstat`, `folder.stat`, `os.fdopen`, `source.read`, `min`, `output.write`, `len`, `output.flush`, `os.fsync`, `output.fileno`, `os.fchmod`, `store.connect`, `os.stat`, `db.execute`, `reserved_names`, `range`, `Path`, `os.fsencode`, `candidate.casefold`, `folder_layout.rename_exclusive`, `(Path(relative) / candidate).as_posix`, `os.unlink`, `os.close`, `SLOTS.release`.

Явные исключения: `ValueError`, `UploadTooLarge`, `UploadBusy`, `UploadConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
{'path': (Path(relative) / candidate).as_posix(), 'name': candidate, 'size': size}
```
