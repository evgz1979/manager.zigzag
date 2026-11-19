# plotter.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [plotter.py](../../../plotter.py).

CorelDRAW HP-GL conversion for the cutter folders.

Импорты Python, включая локальные: `event_folder_undo`, `file_trash`, `file_uploads`, `icloud_access`, `io`, `local_metadata`, `math`, `pathlib`, `re`, `thumbnail_cache`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-convert"></a>

## convert

[plotter.py](../../../plotter.py) · `function`.

```python
def convert(body, x_percent, y_percent):
```

Поворачивает контуры вправо на 90°, переносит их к нулю и масштабирует по выходным осям.

Выдаёт HP-GL в стиле e-cut, поднимает нож и возвращает его в (0, 0).

Непосредственные вызовы: `read_strokes`, `min`, `max`, `io.StringIO`, `output.write`, `math.isfinite`, `ValueError`, `round`, `output.getvalue().encode`, `output.getvalue`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
output.getvalue().encode('ascii')
```

<a id="symbol-file_action"></a>

## file_action

[plotter.py](../../../plotter.py) · `function`.

```python
def file_action(path):
```

Определяет действие плитки PLT в ветке папки резки.

Новые и прежние конвертированные копии доступны для скачивания.

Непосредственные вызовы: `Path`, `path.suffix.lower`, `any`, `is_cutter`, `path.name.casefold().endswith`, `path.name.casefold`, `LEGACY_RESULT_STEM.search`.

Выражения возврата (ветки читаются в исходнике):

```python
'download'
'convert'
None
```

<a id="symbol-is_cutter"></a>

## is_cutter

[plotter.py](../../../plotter.py) · `function`.

```python
def is_cutter(name):
```

Проверяет имя папки резки по тем же правилам пробелов и регистра, что у вложений.

Ожидает отдельный компонент пути с начальным знаком #.

Непосредственные вызовы: `name.startswith`, `name[1:].strip().casefold`, `name[1:].strip`.

Выражения возврата (ветки читаются в исходнике):

```python
name.startswith('#') and name[1:].strip().casefold() == 'cutter'
```

<a id="symbol-percent"></a>

## percent

[plotter.py](../../../plotter.py) · `function`.

```python
def percent(value):
```

Читает процент масштаба для одной оси.

Принимает положительное конечное число с точкой или запятой.

Непосредственные вызовы: `isinstance`, `value.strip().replace`, `value.strip`, `re.fullmatch`, `ValueError`, `float`, `type`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
float(value)
```

<a id="symbol-read_strokes"></a>

## read_strokes

[plotter.py](../../../plotter.py) · `function`.

```python
def read_strokes(body):
```

Разбирает отрезки реза с абсолютными или относительными координатами.

Сохраняет порядок и разрывы; команды, меняющие геометрию, выдаёт как ошибку.

Непосредственные вызовы: `body.decode('ascii').split`, `body.decode`, `field.strip`, `field[:2].upper`, `field[2:].strip`, `ValueError`, `re.fullmatch`, `args.strip`, `COORDINATES.fullmatch`, `int`, `args.replace(',', ' ').split`, `args.replace`, `len`, `zip`, `strokes.append`, `stroke.append`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
strokes
```

<a id="symbol-save_conversion"></a>

## save_conversion

[plotter.py](../../../plotter.py) · `function`.

```python
def save_conversion(store, payload):
```

Конвертирует видимый исходный PLT и публикует готовую копию рядом с ним.

Проверяет свежесть источника; при совпадении имени номер ставится перед -gpt.plt.

Непосредственные вызовы: `payload.get`, `isinstance`, `file_action`, `ValueError`, `file_trash.checked`, `source.parent.relative_to(store.root).as_posix`, `source.parent.relative_to`, `guard_database`, `destination`, `file_uploads.token`, `settings`, `icloud_access.read_bytes`, `convert`, `file_uploads.receive`, `io.BytesIO`, `len`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
file_uploads.receive(store, folder_path, token, source.stem + RESULT_SUFFIX, io.BytesIO(converted), len(converted), destination=destination, numbered_suffix=RESULT_SUFFIX)
```

<a id="symbol-save_conversion.destination"></a>

## save_conversion.destination

[plotter.py](../../../plotter.py) · `function`.

```python
def destination(root, _relative_folder):
```

Находит ту же папку для безопасной публикации файла.

Подменённый, перемещённый или устаревший источник вызывает конфликт.

Непосредственные вызовы: `file_trash.checked`, `current.is_file`, `signature`, `current.stat`, `file_uploads.UploadConflict`.

Явные исключения: `file_uploads.UploadConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
current.parent
```

<a id="symbol-settings"></a>

## settings

[plotter.py](../../../plotter.py) · `function`.

```python
def settings(store, payload=None):
```

Читает или сохраняет общие проценты по выходным осям плоттера.

Отсутствующая запись даёт 98,6174%, запись проверяет версию и сохраняет историю SQLite.

Непосредственные вызовы: `MetadataStore`, `metadata.get`, `type`, `record.get`, `ValueError`, `percent`, `payload.get`, `metadata.connect`, `audit`, `metadata.put`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{'revision': 'missing', 'x_percent': DEFAULT_PERCENT, 'y_percent': DEFAULT_PERCENT}
{'revision': record['revision'], 'x_percent': percent(record.get('x_percent')), 'y_percent': percent(record.get('y_percent'))}
```
