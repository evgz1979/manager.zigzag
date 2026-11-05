# folder_notes.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [folder_notes.py](../../../folder_notes.py).

Карточки произвольных папок в SQLite; прежняя выгрузка сохранена для совместимости.

Импорты Python, включая локальные: `contextlib`, `event_folder_undo`, `event_relevance`, `file_comments`, `folder_structure`, `hashlib`, `json`, `local_metadata`, `order_document`, `pathlib`, `sketches`, `supplier_purchases`, `threading`, `time`, `uuid`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-FolderNoteConflict"></a>

## FolderNoteConflict

[folder_notes.py](../../../folder_notes.py) · `class`.

```python
class FolderNoteConflict(ValueError):
```

Обозначает конфликт изменения в этом модуле.

Вызывающий обработчик использует тип исключения для отказа без подмены данных.

<a id="symbol-FolderNotes"></a>

## FolderNotes

[folder_notes.py](../../../folder_notes.py) · `class`.

```python
class FolderNotes:
```

Хранит заметки и блоки папок отдельно от зарегистрированных заказов.

Основные операции: __init__, connect, record, get, target; остальные описаны у методов.

<a id="symbol-FolderNotes.__init__"></a>

## FolderNotes.__init__

[folder_notes.py](../../../folder_notes.py) · `function`.

```python
def __init__(self, store, prepare=None):
```

Сохраняет зависимости и начальные параметры экземпляра.

Состояние и зависимости сохраняются в полях self для последующих операций.

Прямые присваивания полям/свойствам: `self.store`, `self.prepare`.

<a id="symbol-FolderNotes._read"></a>

## FolderNotes._read

[folder_notes.py](../../../folder_notes.py) · `function`.

```python
def _read(self, relative):
```

Импортирует отсутствующую заметку, сохраняя преимущество прежней записи SQLite.

Работает с таблицами folder_notes.

Непосредственные вызовы: `self.get`, `self.target`, `parent_order`, `ValueError`, `self.prepare`, `file_revision`, `MetadataStore(self.store).card`, `MetadataStore`, `self.store.get`, `document.load`, `is_service_folder`, `document.folder_note`, `FolderNoteConflict`, `self.connect`, `db.execute`, `assert_unlocked`, `db.execute('SELECT * FROM folder_notes WHERE path=?', (relative,)).fetchone`, `self.record`, `str`, `uuid.uuid4`, `json.dumps`, `time.time`.

Явные исключения: `ValueError`, `FolderNoteConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
previous
self.record(current)
self.record(db.execute('SELECT * FROM folder_notes WHERE path=?', (relative,)).fetchone())
```

<a id="symbol-FolderNotes.connect"></a>

## FolderNotes.connect

[folder_notes.py](../../../folder_notes.py) · `function`.

```python
def connect(self):
```

Открывает соединение SQLite и управляет его временем жизни.

Передаёт ресурс через yield; освобождение выполняется при выходе из контекста.

Непосредственные вызовы: `self.store.connect`, `schema`.

<a id="symbol-FolderNotes.event_relevances"></a>

## FolderNotes.event_relevances

[folder_notes.py](../../../folder_notes.py) · `function`.

```python
def event_relevances(self, owner):
```

Читает актуальность событий из SQLite без обхода документов.

Работает с таблицами folder_notes, orders.

Непосредственные вызовы: `checked_path`, `self.connect`, `db.execute('SELECT * FROM folder_notes WHERE parent_order=?', (owner,)).fetchall`, `db.execute`, `event_relevance.is_event`, `assert_unlocked`, `event_relevance.info`, `self.record`.

Выражения возврата (ветки читаются в исходнике):

```python
result
```

<a id="symbol-FolderNotes.get"></a>

## FolderNotes.get

[folder_notes.py](../../../folder_notes.py) · `function`.

```python
def get(self, relative):
```

Читает сохранённую карточку папки непосредственно из SQLite.

Работает с таблицами folder_notes.

Непосредственные вызовы: `self.path`, `self.store.database.exists`, `self.connect`, `assert_unlocked`, `self.record`, `db.execute('SELECT * FROM folder_notes WHERE path=?', (relative,)).fetchone`, `db.execute`.

Выражения возврата (ветки читаются в исходнике):

```python
None
self.record(db.execute('SELECT * FROM folder_notes WHERE path=?', (relative,)).fetchone())
```

<a id="symbol-FolderNotes.path"></a>

## FolderNotes.path

[folder_notes.py](../../../folder_notes.py) · `function`.

```python
def path(self, relative):
```

Проверяет относительный путь внутри допустимой области.

Возвращает `self.store.root`; либо `checked_path(self.store.root, relative)`.

Непосредственные вызовы: `checked_path`.

Выражения возврата (ветки читаются в исходнике):

```python
self.store.root
checked_path(self.store.root, relative)
```

<a id="symbol-FolderNotes.read"></a>

## FolderNotes.read

[folder_notes.py](../../../folder_notes.py) · `function`.

```python
def read(self, relative):
```

Читает карточку папки с блокировкой и допустимым первоначальным импортом.

Возвращает `self._read(relative)`.

Непосредственные вызовы: `self._read`.

Выражения возврата (ветки читаются в исходнике):

```python
self._read(relative)
```

<a id="symbol-FolderNotes.record"></a>

## FolderNotes.record

[folder_notes.py](../../../folder_notes.py) · `function`.

```python
def record(self, row):
```

Преобразует строку SQLite в представление для вызывающего кода.

Разбирает JSON; вызывающий код должен учитывать ошибки или неизвестный формат.

Непосредственные вызовы: `dict`, `json.loads`, `value.pop`, `body.get`, `document.read_todos`.

Выражения возврата (ветки читаются в исходнике):

```python
None
{'path': value['path'], 'revision': f"{value['id']}:{value['revision']}", 'note': body.get('note', ''), 'extra_blocks': body.get('extra_blocks', {}), 'todo_items': document.read_todos(body.get('extra_blocks', {})), 'sync_pending': False if self.store.database_only else value['revision'] != value['exported_revision'], 'sync_error': '' if self.store.database_only else value['sync_error'], 'storage': 'database' if self.store.database_only else 'legacy', **({'card': body} if self.store.database_only else {}), 'file_exists': value['file_revision'] != 'missing', 'parent_order': value['parent_orde...
```

<a id="symbol-FolderNotes.save"></a>

## FolderNotes.save

[folder_notes.py](../../../folder_notes.py) · `function`.

```python
def save(self, payload):
```

Сохраняет заметку и задачи папки с проверкой идентичности и revision.

Работает с таблицами orders, folder_notes.

Непосредственные вызовы: `payload.get`, `self.path`, `isinstance`, `len`, `ValueError`, `self.connect`, `db.execute`, `assert_unlocked`, `db.execute('SELECT 1 FROM orders WHERE path=? AND registered=1', (relative,)).fetchone`, `FolderNoteConflict`, `db.execute('SELECT * FROM folder_notes WHERE path=?', (relative,)).fetchone`, `json.loads`, `is_service_folder`, `body.get`, `value.strip`, `any`, `document.money`, `write_assignments`, `document.read_todos`, `document.write_todos`, `document.render`, `json.dumps`, `time.time`, `self.record`.

Явные исключения: `ValueError`, `FolderNoteConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
self.record(db.execute('SELECT * FROM folder_notes WHERE path=?', (relative,)).fetchone())
```

<a id="symbol-FolderNotes.save_relevance"></a>

## FolderNotes.save_relevance

[folder_notes.py](../../../folder_notes.py) · `function`.

```python
def save_relevance(self, payload):
```

Сохраняет только актуальность выбранного события папки.

Работает с таблицами folder_notes, orders.

Непосредственные вызовы: `payload.get`, `checked_path`, `isinstance`, `ValueError`, `', '.join`, `event_relevance.LABELS.values`, `self.connect`, `db.execute`, `assert_unlocked`, `db.execute('SELECT * FROM folder_notes WHERE path=?', (relative,)).fetchone`, `FolderNoteConflict`, `event_relevance.is_event`, `db.execute('SELECT 1 FROM orders WHERE path=? AND registered=1', (relative,)).fetchone`, `json.loads`, `event_relevance.write`, `body.get`, `document.render`, `json.dumps`, `time.time`, `self.record`.

Явные исключения: `ValueError`, `FolderNoteConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
self.record(db.execute('SELECT * FROM folder_notes WHERE path=?', (relative,)).fetchone())
```

<a id="symbol-FolderNotes.save_sketch_relevance"></a>

## FolderNotes.save_sketch_relevance

[folder_notes.py](../../../folder_notes.py) · `function`.

```python
def save_sketch_relevance(self, payload):
```

Сохраняет только актуальность выбранного эскиза CorelDRAW.

Работает с таблицами folder_notes.

Непосредственные вызовы: `payload.get`, `isinstance`, `ValueError`, `sketches.folder_path`, `checked_path`, `file_comments.binding`, `FolderNoteConflict`, `self.connect`, `db.execute`, `assert_unlocked`, `db.execute('SELECT * FROM folder_notes WHERE path=?', (folder,)).fetchone`, `Path(folder).parent.as_posix`, `Path`, `json.loads`, `sketches.write`, `body.get`, `json.dumps`, `time.time`, `self.record`.

Явные исключения: `ValueError`, `FolderNoteConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
self.record(db.execute('SELECT * FROM folder_notes WHERE path=?', (folder,)).fetchone())
```

<a id="symbol-FolderNotes.sketch_relevances"></a>

## FolderNotes.sketch_relevances

[folder_notes.py](../../../folder_notes.py) · `function`.

```python
def sketch_relevances(self, owner):
```

Читает актуальность эскизов из сохранённых карточек базы.

Работает с таблицами folder_notes.

Непосредственные вызовы: `checked_path`, `self.connect`, `db.execute`, `Path(row['path']).parent.as_posix`, `Path`, `sketches.cdr_folder`, `assert_unlocked`, `sketches.group_info`, `self.record`.

Выражения возврата (ветки читаются в исходнике):

```python
result
```

<a id="symbol-FolderNotes.sync"></a>

## FolderNotes.sync

[folder_notes.py](../../../folder_notes.py) · `function`.

```python
def sync(self):
```

Обрабатывает старую выгрузку карточек только в разрешённом режиме хранения.

Работает с таблицами folder_notes.

Непосредственные вызовы: `self.connect`, `db.execute`, `self.store.database.exists`, `SYNC_LOCK.acquire`, `db.execute('SELECT * FROM folder_notes WHERE revision!=exported_revision ORDER BY path').fetchall`, `assert_unlocked`, `self.target`, `document.render`, `json.loads`, `card.is_file`, `card.is_symlink`, `document.icloud_access.read_bytes`, `body.encode`, `file_revision`, `FolderNoteConflict`, `document.archive_current`, `document.atomic_write`, `document.archive_legacy`, `hashlib.sha256(document.DOCUMENT.encode() + len(raw).to_bytes(8, 'big') + raw).hexdigest`, `hashlib.sha256`, `document.DOCUMENT.encode`, `len(raw).to_bytes`, `len`, `document.icloud_access.sync_error`, `SYNC_LOCK.release`.

Явные исключения: `FolderNoteConflict`.

<a id="symbol-FolderNotes.target"></a>

## FolderNotes.target

[folder_notes.py](../../../folder_notes.py) · `function`.

```python
def target(self, relative):
```

Находит допустимую существующую цель файловой операции.

При недопустимом состоянии возбуждает ValueError, FileNotFoundError.

Непосредственные вызовы: `self.path`, `range`, `len`, `Path`, `(self.store.root / Path(*Path(relative).parts[:index])).is_symlink`, `ValueError`, `target.is_dir`, `FileNotFoundError`.

Явные исключения: `ValueError`, `FileNotFoundError`.

Выражения возврата (ветки читаются в исходнике):

```python
target
```

<a id="symbol-checked_path"></a>

## checked_path

[folder_notes.py](../../../folder_notes.py) · `function`.

```python
def checked_path(root, relative):
```

Проверяет путь и ограничения допустимой операции.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `ValueError`, `Path`, `path.is_absolute`, `any`, `part.startswith`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
Path(root) / path
```

<a id="symbol-file_revision"></a>

## file_revision

[folder_notes.py](../../../folder_notes.py) · `function`.

```python
def file_revision(folder):
```

Вычисляет версию прежней карточки папки по файловому состоянию.

Возвращает `digest.hexdigest() if found else 'missing'`.

Непосредственные вызовы: `hashlib.sha256`, `path.exists`, `path.is_symlink`, `document.read_text`, `document.icloud_access.read_bytes`, `digest.update`, `name.encode`, `len(raw).to_bytes`, `len`, `digest.hexdigest`.

Выражения возврата (ветки читаются в исходнике):

```python
digest.hexdigest() if found else 'missing'
```

<a id="symbol-parent_order"></a>

## parent_order

[folder_notes.py](../../../folder_notes.py) · `function`.

```python
def parent_order(root, relative):
```

Определяет родительскую папку или заказ по допустимому пути.

Возвращает `parent`; либо `None`.

Непосредственные вызовы: `Path`, `range`, `len`, `Path(*parts[:index]).as_posix`, `folder_role`, `is_service_folder`.

Выражения возврата (ветки читаются в исходнике):

```python
parent
None
```

<a id="symbol-schema"></a>

## schema

[folder_notes.py](../../../folder_notes.py) · `function`.

```python
def schema(db):
```

Создаёт отсутствующие таблицы и совместимые расширения схемы.

Работает с таблицами folder_notes.

Непосредственные вызовы: `db.execute`.
