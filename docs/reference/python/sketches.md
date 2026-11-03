# sketches.py

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [sketches.py:1](../../../sketches.py#L1).

Direct CDR sketches, embedded thumbnails and readable per-file relevance.

Импорты Python, включая локальные: `event_relevance`, `hashlib`, `io`, `json`, `pathlib`, `plistlib`, `re`, `struct`, `subprocess`, `tempfile`, `unicodedata`, `zipfile`, `zlib`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## cdr_folder

[sketches.py:24](../../../sketches.py#L24) · `function`.

```python
def cdr_folder(name):
```

Распознаёт непосредственную служебную папку эскизов CorelDRAW.

Возвращает `name.startswith('#') and name[1:].strip().casefold() == 'cdr'`.

Непосредственные вызовы: `name.startswith`, `name[1:].strip().casefold`, `name[1:].strip`.

Выражения возврата (ветки читаются в исходнике):

```python
name.startswith('#') and name[1:].strip().casefold() == 'cdr'
```

## sketch_name

[sketches.py:30](../../../sketches.py#L30) · `function`.

```python
def sketch_name(name):
```

Отбирает поддерживаемый CDR, исключая резервные имена.

Формирует возвращаемое значение из проверенного локального состояния.

Непосредственные вызовы: `unicodedata.normalize('NFC', name).casefold`, `unicodedata.normalize`, `re.match`, `name.startswith`, `Path(name).suffix.casefold`, `Path`, `re.search`.

Выражения возврата (ветки читаются в исходнике):

```python
not name.startswith(('.', '~')) and Path(name).suffix.casefold() == '.cdr' and (not backup) and (not re.search('(?:[ _.-](?:backup|bak|autosave))\\.cdr$', normalized))
```

## folder_path

[sketches.py:39](../../../sketches.py#L39) · `function`.

```python
def folder_path(relative):
```

Проверяет путь папки эскиза внутри заказа.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `Path`, `path.is_absolute`, `len`, `any`, `part.startswith`, `cdr_folder`, `sketch_name`, `ValueError`, `path.parent.as_posix`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
path.parent.as_posix()
```

## read

[sketches.py:49](../../../sketches.py#L49) · `function`.

```python
def read(blocks):
```

Читает данные текущего формата и сохраняет различие пустого и неизвестного.

Возвращает `None`; либо `result`.

Непосредственные вызовы: `blocks.get(BLOCK, '').splitlines`, `blocks.get`, `line.strip`, `json.JSONDecoder().raw_decode`, `json.JSONDecoder`, `next`, `LABELS.items`, `isinstance`, `Path`, `sketch_name`, `unicodedata.normalize`.

Выражения возврата (ветки читаются в исходнике):

```python
None
result
```

## write

[sketches.py:71](../../../sketches.py#L71) · `function`.

```python
def write(blocks, filename, value):
```

Формирует новое представление данных для сохранения.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `ValueError`, `read`, `unicodedata.normalize`, `'\n'.join`, `json.dumps`, `states.items`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{**blocks, BLOCK: body}
```

## info

[sketches.py:84](../../../sketches.py#L84) · `function`.

```python
def info(record, filename, error=''):
```

Формирует представление состояния и ошибок для интерфейса.

Формирует возвращаемое значение из проверенного локального состояния.

Непосредственные вызовы: `read`, `states.get`, `unicodedata.normalize`.

Выражения возврата (ветки читаются в исходнике):

```python
{'value': states.get(unicodedata.normalize('NFC', filename), 'none') if states is not None else None, 'revision': record['revision'] if record else None, 'sync_pending': record['sync_pending'] if record else False, 'sync_error': record['sync_error'] if record else '', 'error': error or (f'Проверьте раздел [{BLOCK}] в !.txt папки #cdr' if record and states is None else '')}
```

## group_info

[sketches.py:95](../../../sketches.py#L95) · `function`.

```python
def group_info(record):
```

Формирует представление состояния и ошибок для интерфейса.

Возвращает `result`.

Непосредственные вызовы: `info`, `result.pop`, `read`.

Выражения возврата (ветки читаются в исходнике):

```python
result
```

## embedded_preview

[sketches.py:104](../../../sketches.py#L104) · `function`.

```python
def embedded_preview(target, *, allow_bmp=False):
```

Извлекает встроенную миниатюру Corel без распаковки путей на диск.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `zipfile.ZipFile`, `entry.filename.casefold`, `archive.infolist`, `entries.get`, `archive.open`, `stream.read`, `len`, `struct.unpack`, `struct.unpack_from`, `abs`, `ValueError`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
raw
```

## fingerprint

[sketches.py:147](../../../sketches.py#L147) · `function`.

```python
def fingerprint(target):
```

Вычисляет отпечаток метаданных объекта для проверки свежести.

Возвращает `hashlib.sha256(f'{target}:{stat.st_dev}:{stat.st_ino}:{stat.st_size}:{stat.st_mtime_ns}:{stat.st_ctime_ns}'.encode()).hexdigest()`.

Непосредственные вызовы: `target.stat`, `hashlib.sha256(f'{target}:{stat.st_dev}:{stat.st_ino}:{stat.st_size}:{stat.st_mtime_ns}:{stat.st_ctime_ns}'.encode()).hexdigest`, `hashlib.sha256`, `f'{target}:{stat.st_dev}:{stat.st_ino}:{stat.st_size}:{stat.st_mtime_ns}:{stat.st_ctime_ns}'.encode`.

Выражения возврата (ветки читаются в исходнике):

```python
hashlib.sha256(f'{target}:{stat.st_dev}:{stat.st_ino}:{stat.st_size}:{stat.st_mtime_ns}:{stat.st_ctime_ns}'.encode()).hexdigest()
```

## preview

[sketches.py:154](../../../sketches.py#L154) · `function`.

```python
def preview(target, data_dir, *, read_bytes=None, allow_bmp=False):
```

Готовит проверяемое предложение операции без её выполнения.

Запускает внешний процесс; параметры и ограничения заданы в теле функции.

Непосредственные вызовы: `fingerprint`, `Path`, `cached.is_file`, `io.BytesIO`, `read_bytes`, `embedded_preview`, `ValueError`, `cache.mkdir`, `tempfile.TemporaryDirectory`, `source.write_bytes`, `subprocess.run`, `str`, `converted.read_bytes`, `tempfile.NamedTemporaryFile`, `stream.write`, `temporary.replace`, `temporary.unlink`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
cached
```

## corel_app

[sketches.py:187](../../../sketches.py#L187) · `function`.

```python
def corel_app():
```

Находит установленное приложение CorelDRAW для открытия оригинала.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `Path`, `Path.home`, `root.glob`, `plistlib.loads`, `(app / 'Contents/Info.plist').read_bytes`, `data.get('CFBundleIdentifier', '').casefold().endswith`, `data.get('CFBundleIdentifier', '').casefold`, `data.get`, `tuple`, `int`, `re.findall`, `candidates.append`, `str`, `ValueError`, `max`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
max(candidates)[1]
```

## open_corel

[sketches.py:206](../../../sketches.py#L206) · `function`.

```python
def open_corel(target):
```

Открывает проверенный исходный CDR в CorelDRAW на серверном Mac.

Запускает внешний процесс; параметры и ограничения заданы в теле функции.

Непосредственные вызовы: `subprocess.run`, `corel_app`, `str`, `ValueError`.

Явные исключения: `ValueError`.
