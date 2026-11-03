# icloud_access.py

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [icloud_access.py:1](../../../icloud_access.py#L1).

Ограниченное чтение карточек с восстановлением доступа к файлам iCloud.

Импорты Python, включая локальные: `errno`, `native_renderers`, `pathlib`, `subprocess`, `sys`, `threading`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## CloudReadPending

[icloud_access.py:17](../../../icloud_access.py#L17) · `class`.

```python
class CloudReadPending(OSError):
```

Обозначает незавершённость операции в этом модуле.

Вызывающий обработчик использует тип исключения для отказа без подмены данных.

## CloudReadPending.__init__

[icloud_access.py:20](../../../icloud_access.py#L20) · `function`.

```python
def __init__(self, path):
```

Сохраняет зависимости и начальные параметры экземпляра.

Состояние и зависимости сохраняются в полях self для последующих операций.

Непосредственные вызовы: `Path`, `super().__init__`, `super`, `str`.

Прямые присваивания полям/свойствам: `self.path`.

## CloudReadPending.__str__

[icloud_access.py:26](../../../icloud_access.py#L26) · `function`.

```python
def __str__(self):
```

Возвращает текст ошибки, пригодный для показа пользователю.

Возвращает `f'iCloud пока не предоставил файл «{self.path.name}». Данные в базе, выгрузка остаётся в очереди; повторим автоматически'`.

Выражения возврата (ветки читаются в исходнике):

```python
f'iCloud пока не предоставил файл «{self.path.name}». Данные в базе, выгрузка остаётся в очереди; повторим автоматически'
```

## renderer

[icloud_access.py:32](../../../icloud_access.py#L32) · `function`.

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

## _plain_read

[icloud_access.py:40](../../../icloud_access.py#L40) · `function`.

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

## _coordinated_read

[icloud_access.py:47](../../../icloud_access.py#L47) · `function`.

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

## read_bytes

[icloud_access.py:55](../../../icloud_access.py#L55) · `function`.

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

## sync_error

[icloud_access.py:79](../../../icloud_access.py#L79) · `function`.

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
