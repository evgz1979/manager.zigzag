# file_uploads.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [file_uploads.py](../../../file_uploads.py).

Stream browser files into an existing event directory without overwriting files.

Импорты Python, включая локальные: `errno`, `event_folder_undo`, `file_trash`, `folder_layout`, `folder_notes`, `folder_structure`, `hashlib`, `json`, `order_folders`, `os`, `pathlib`, `threading`, `unicodedata`, `uuid`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-UploadBusy"></a>

## UploadBusy

[file_uploads.py](../../../file_uploads.py) · `class`.

```python
class UploadBusy(ValueError):
```

Обозначает занятость обработчика в этом модуле.

Вызывающий обработчик использует тип исключения для отказа без подмены данных.

<a id="symbol-UploadConflict"></a>

## UploadConflict

[file_uploads.py](../../../file_uploads.py) · `class`.

```python
class UploadConflict(ValueError):
```

Обозначает конфликт изменения в этом модуле.

Вызывающий обработчик использует тип исключения для отказа без подмены данных.

<a id="symbol-UploadTooLarge"></a>

## UploadTooLarge

[file_uploads.py](../../../file_uploads.py) · `class`.

```python
class UploadTooLarge(ValueError):
```

Обозначает превышение размера в этом модуле.

Вызывающий обработчик использует тип исключения для отказа без подмены данных.

<a id="symbol-available"></a>

## available

[file_uploads.py](../../../file_uploads.py) · `function`.

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

<a id="symbol-filename"></a>

## filename

[file_uploads.py](../../../file_uploads.py) · `function`.

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

<a id="symbol-options"></a>

## options

[file_uploads.py](../../../file_uploads.py) · `function`.

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

<a id="symbol-receive"></a>

## receive

[file_uploads.py](../../../file_uploads.py) · `function`.

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

<a id="symbol-reserved_names"></a>

## reserved_names

[file_uploads.py](../../../file_uploads.py) · `function`.

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

<a id="symbol-reserved_names.reserve"></a>

## reserved_names.reserve

[file_uploads.py](../../../file_uploads.py) · `function`.

```python
def reserve(path):
```

Занимает свободное имя файла для текущей загрузки.

Передаёт работу `unicodedata.normalize`, `path.startswith`, `names.add`.

Непосредственные вызовы: `unicodedata.normalize`, `path.startswith`, `names.add`, `path[len(prefix):].split('/', 1)[0].casefold`, `path[len(prefix):].split`, `len`.

<a id="symbol-target"></a>

## target

[file_uploads.py](../../../file_uploads.py) · `function`.

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

<a id="symbol-token"></a>

## token

[file_uploads.py](../../../file_uploads.py) · `function`.

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
