# scripts/rebind_glass_notes.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [scripts/rebind_glass_notes.py](../../../scripts/rebind_glass_notes.py).

Явная перепривязка выгруженных заметок после переноса # glass в # work.

Без --apply показывает план. Копия в журнале самостоятельно откатывает пути
SQLite после обратного переноса папки пользователем; документы не меняются.

Импорты Python, включая локальные: `argparse`, `contextlib`, `datetime`, `folder_layout`, `folder_notes`, `folder_structure`, `json`, `os`, `pathlib`, `server`, `shutil`, `sqlite3`, `sys`, `zoneinfo`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-append_journal"></a>

## append_journal

[scripts/rebind_glass_notes.py](../../../scripts/rebind_glass_notes.py) · `function`.

```python
def append_journal(session, record):
```

Дописывает запись в устойчивый журнал операции.

Передаёт работу `datetime.now(ZoneInfo('Europe/Moscow')).isoformat`, `datetime.now`, `ZoneInfo`.

Непосредственные вызовы: `datetime.now(ZoneInfo('Europe/Moscow')).isoformat`, `datetime.now`, `ZoneInfo`, `(Path(session) / '.journal.jsonl').open`, `Path`, `stream.write`, `json.dumps`, `stream.flush`, `os.fsync`, `stream.fileno`.

<a id="symbol-check_database"></a>

## check_database

[scripts/rebind_glass_notes.py](../../../scripts/rebind_glass_notes.py) · `function`.

```python
def check_database(db, source, destination):
```

Проверяет целостность и совместимость рабочей SQLite.

Работает с таблицами orders, sqlite_master.

Непосредственные вызовы: `any`, `inside`, `db.execute`, `ValueError`, `db.execute('SELECT 1 FROM sqlite_master WHERE name=?', (name,)).fetchone`, `json.loads`.

Явные исключения: `ValueError`.

<a id="symbol-checked_folder"></a>

## checked_folder

[scripts/rebind_glass_notes.py](../../../scripts/rebind_glass_notes.py) · `function`.

```python
def checked_folder(root, relative):
```

Проверяет точную существующую папку ручной операции.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `Path`, `path.is_absolute`, `any`, `part.startswith`, `ValueError`, `range`, `len`, `(root / Path(*path.parts[:index])).is_symlink`, `target.is_dir`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
target
```

<a id="symbol-inside"></a>

## inside

[scripts/rebind_glass_notes.py](../../../scripts/rebind_glass_notes.py) · `function`.

```python
def inside(path, prefix):
```

Проверяет принадлежность пути указанной области по границам компонентов.

Возвращает `path == prefix or path.startswith(prefix + '/')`.

Непосредственные вызовы: `path.startswith`.

Выражения возврата (ветки читаются в исходнике):

```python
path == prefix or path.startswith(prefix + '/')
```

<a id="symbol-rebind"></a>

## rebind

[scripts/rebind_glass_notes.py](../../../scripts/rebind_glass_notes.py) · `function`.

```python
def rebind(notes, source='# glass', destination='# work/# glass', *, perform=False):
```

Перепривязывает проверенную существующую запись к подтверждённому пути.

Работает с таблицами folder_notes.

Непосредственные вызовы: `ValueError`, `Path`, `supplier_prefix`, `len`, `os.path.lexists`, `checked_folder`, `notes.connect`, `check_database`, `dict`, `db.execute`, `inside`, `any`, `file_revision`, `changes.append`, `layout.Plan`, `str`, `notes.store.database.resolve`, `plan.create_session`, `shutil.copyfile`, `closing`, `sqlite3.connect`, `notes.store.database.as_uri`, `original.backup`, `layout.append`, `sorted`, `zip`, `layout.save_json`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
preview
{**preview, 'journal': str(session)}
```

<a id="symbol-undo"></a>

## undo

[scripts/rebind_glass_notes.py](../../../scripts/rebind_glass_notes.py) · `function`.

```python
def undo(session, *, perform=False):
```

Выполняет сохранённые обратные операции после проверки текущего состояния.

Работает с таблицами folder_notes.

Непосредственные вызовы: `Path`, `json.loads`, `(session / '.before.json').read_text`, `len`, `checked_folder`, `os.path.lexists`, `ValueError`, `closing`, `sqlite3.connect`, `Path(before['database']).as_uri`, `db.execute`, `check_database`, `zip`, `db.execute('SELECT * FROM folder_notes WHERE id=?', (change['id'],)).fetchone`, `db.execute('SELECT 1 FROM folder_notes WHERE path=?', (change['source'],)).fetchone`, `updates.append`, `append_journal`, `db.executemany`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{'count': len(before['changes']), 'action': 'Вернуть пути заметок после обратного переноса папки'}
{'restored': len(updates)}
```
