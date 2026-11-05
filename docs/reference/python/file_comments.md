# file_comments.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [file_comments.py](../../../file_comments.py).

Legacy portable comment format and file binding; current comments live in SQLite.

Импорты Python, включая локальные: `hashlib`, `json`, `order_document`, `pathlib`, `threading`, `unicodedata`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-FileCommentConflict"></a>

## FileCommentConflict

[file_comments.py](../../../file_comments.py) · `class`.

```python
class FileCommentConflict(ValueError):
```

Обозначает конфликт изменения в этом модуле.

Вызывающий обработчик использует тип исключения для отказа без подмены данных.

<a id="symbol-binding"></a>

## binding

[file_comments.py](../../../file_comments.py) · `function`.

```python
def binding(file):
```

Связывает запрос комментария с точными папкой и именем файла.

Возвращает `hashlib.sha256(json.dumps([unicodedata.normalize('NFC', part) for part in identity], ensure_ascii=False).encode()).hexdigest()`.

Непосредственные вызовы: `Path`, `str`, `file.parent.resolve`, `hashlib.sha256(json.dumps([unicodedata.normalize('NFC', part) for part in identity], ensure_ascii=False).encode()).hexdigest`, `hashlib.sha256`, `json.dumps([unicodedata.normalize('NFC', part) for part in identity], ensure_ascii=False).encode`, `json.dumps`, `unicodedata.normalize`.

Выражения возврата (ветки читаются в исходнике):

```python
hashlib.sha256(json.dumps([unicodedata.normalize('NFC', part) for part in identity], ensure_ascii=False).encode()).hexdigest()
```

<a id="symbol-parse"></a>

## parse

[file_comments.py](../../../file_comments.py) · `function`.

```python
def parse(raw, name):
```

Разбирает исходное содержимое, сохраняя неизвестные поля или блоки.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `raw.decode('utf-8-sig').replace`, `raw.decode`, `text.partition`, `header.splitlines`, `len`, `lines[1].startswith`, `json.loads`, `ValueError`, `body.removesuffix('\n').split`, `body.removesuffix`, `any`, `line.startswith`, `'\n'.join`, `hashlib.sha256(raw).hexdigest`, `hashlib.sha256`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{'comment': '\n'.join((line[2:] for line in note_lines)), 'revision': hashlib.sha256(raw).hexdigest()}
```

<a id="symbol-paths"></a>

## paths

[file_comments.py](../../../file_comments.py) · `function`.

```python
def paths(file):
```

Вычисляет пути прежнего файла комментария и его истории.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `Path`, `unicodedata.normalize`, `hashlib.sha256(name.encode()).hexdigest`, `hashlib.sha256`, `name.encode`, `folder.is_symlink`, `folder.exists`, `folder.is_dir`, `ValueError`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
(name, key, folder, target)
```

<a id="symbol-read"></a>

## read

[file_comments.py](../../../file_comments.py) · `function`.

```python
def read(file):
```

Читает прежний скрытый комментарий и его файловую версию.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `paths`, `target.is_symlink`, `target.exists`, `target.is_file`, `ValueError`, `target.stat`, `target.read_bytes`, `parse`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{'comment': '', 'revision': 'missing'}
parse(raw, name)
```

<a id="symbol-save"></a>

## save

[file_comments.py](../../../file_comments.py) · `function`.

```python
def save(file, comment, revision):
```

Записывает прежний скрытый файл комментария с проверкой привязки и версии.

При недопустимом состоянии возбуждает ValueError, FileCommentConflict.

Непосредственные вызовы: `isinstance`, `len`, `ValueError`, `comment.replace('\r\n', '\n').replace`, `comment.replace`, `read`, `FileCommentConflict`, `paths`, `folder.mkdir`, `target.exists`, `history.is_symlink`, `versions.is_symlink`, `versions.mkdir`, `backup.is_symlink`, `backup.exists`, `backup.is_file`, `target.read_bytes`, `hashlib.sha256(raw).hexdigest`, `hashlib.sha256`, `atomic_write`, `raw.decode`, `backup.read_bytes`, `json.dumps`.

Явные исключения: `ValueError`, `FileCommentConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
current
read(file)
```
