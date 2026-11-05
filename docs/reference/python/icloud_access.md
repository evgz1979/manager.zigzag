# icloud_access.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [icloud_access.py](../../../icloud_access.py).

Ограниченное чтение карточек с восстановлением доступа к файлам iCloud.

Импорты Python, включая локальные: `errno`, `native_renderers`, `pathlib`, `subprocess`, `sys`, `threading`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-CloudReadPending"></a>

## CloudReadPending

[icloud_access.py](../../../icloud_access.py) · `class`.

```python
class CloudReadPending(OSError):
```

Обозначает незавершённость операции в этом модуле.

Вызывающий обработчик использует тип исключения для отказа без подмены данных.

<a id="symbol-CloudReadPending.__init__"></a>

## CloudReadPending.__init__

[icloud_access.py](../../../icloud_access.py) · `function`.

```python
def __init__(self, path):
```

Сохраняет зависимости и начальные параметры экземпляра.

Состояние и зависимости сохраняются в полях self для последующих операций.

Непосредственные вызовы: `Path`, `super().__init__`, `super`, `str`.

Прямые присваивания полям/свойствам: `self.path`.

<a id="symbol-CloudReadPending.__str__"></a>

## CloudReadPending.__str__

[icloud_access.py](../../../icloud_access.py) · `function`.

```python
def __str__(self):
```

Возвращает текст ошибки, пригодный для показа пользователю.

Возвращает `f'iCloud пока не предоставил файл «{self.path.name}». Данные в базе, выгрузка остаётся в очереди; повторим автоматически'`.

Выражения возврата (ветки читаются в исходнике):

```python
f'iCloud пока не предоставил файл «{self.path.name}». Данные в базе, выгрузка остаётся в очереди; повторим автоматически'
```

<a id="symbol-_coordinated_read"></a>

## _coordinated_read

[icloud_access.py](../../../icloud_access.py) · `function`.

```python
def _coordinated_read(path, max_bytes=MAX_BYTES):
```

Читает файл через Foundation-помощник с ограничением времени.

Запускает внешний процесс; параметры и ограничения заданы в теле функции.

Непосредственные вызовы: `subprocess.run`, `str`, `renderer`.

Выражения возврата (ветки читаются в исходнике):

```python
result.stdout
```

<a id="symbol-_plain_read"></a>

## _plain_read

[icloud_access.py](../../../icloud_access.py) · `function`.

```python
def _plain_read(path, max_bytes=MAX_BYTES):
```

Читает локальный файл напрямую с проверкой ограничения размера.

Возвращает `stream.read(max_bytes + 1)`.

Непосредственные вызовы: `path.open`, `stream.read`.

Выражения возврата (ветки читаются в исходнике):

```python
stream.read(max_bytes + 1)
```

<a id="symbol-read_bytes"></a>

## read_bytes

[icloud_access.py](../../../icloud_access.py) · `function`.

```python
def read_bytes(path, *, max_bytes=MAX_BYTES, coordinated=False):
```

Возвращает ограниченное содержимое файла после необходимых проверок.

При недопустимом состоянии возбуждает ValueError, CloudReadPending.

Непосредственные вызовы: `Path`, `type`, `ValueError`, `path.is_symlink`, `path.is_file`, `_coordinated_read`, `_plain_read`, `CloudReadPending`, `len`.

Явные исключения: `ValueError`, `CloudReadPending`.

Выражения возврата (ветки читаются в исходнике):

```python
raw
```

<a id="symbol-renderer"></a>

## renderer

[icloud_access.py](../../../icloud_access.py) · `function`.

```python
def renderer():
```

Получает собранный Swift-помощник для текущего исходника.

Возвращает `native_renderers.build(app / 'icloud_read.swift', app / 'data', 'icloud-read', 60)`.

Непосредственные вызовы: `Path(__file__).resolve`, `Path`, `native_renderers.build`.

Выражения возврата (ветки читаются в исходнике):

```python
native_renderers.build(app / 'icloud_read.swift', app / 'data', 'icloud-read', 60)
```

<a id="symbol-sync_error"></a>

## sync_error

[icloud_access.py](../../../icloud_access.py) · `function`.

```python
def sync_error(error):
```

Преобразует ошибку чтения iCloud в понятное сообщение состояния.

Возвращает `str(error)`; либо `'iCloud временно заблокировал доступ к файлу. Данные в базе, выгрузка остаётся в очереди; повторим автоматически'`.

Непосредственные вызовы: `isinstance`, `str`.

Выражения возврата (ветки читаются в исходнике):

```python
str(error)
'iCloud временно заблокировал доступ к файлу. Данные в базе, выгрузка остаётся в очереди; повторим автоматически'
```
