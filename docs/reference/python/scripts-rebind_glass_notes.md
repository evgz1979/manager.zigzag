# scripts/rebind_glass_notes.py

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [scripts/rebind_glass_notes.py:1](../../../scripts/rebind_glass_notes.py#L1).

Явная перепривязка выгруженных заметок после переноса # glass в # work.

Без --apply показывает план. Копия в журнале самостоятельно откатывает пути
SQLite после обратного переноса папки пользователем; документы не меняются.

Импорты Python, включая локальные: `argparse`, `contextlib`, `datetime`, `folder_layout`, `folder_notes`, `folder_structure`, `json`, `os`, `pathlib`, `server`, `shutil`, `sqlite3`, `sys`, `zoneinfo`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## append_journal

[scripts/rebind_glass_notes.py:20](../../../scripts/rebind_glass_notes.py#L20) · `function`.

```python
def append_journal(session, record):
```

Дописывает запись в устойчивый журнал операции.

Передаёт работу `datetime.now(ZoneInfo('Europe/Moscow')).isoformat`, `datetime.now`, `ZoneInfo`.

Непосредственные вызовы: `datetime.now(ZoneInfo('Europe/Moscow')).isoformat`, `datetime.now`, `ZoneInfo`, `(Path(session) / '.journal.jsonl').open`, `Path`, `stream.write`, `json.dumps`, `stream.flush`, `os.fsync`, `stream.fileno`.

## inside

[scripts/rebind_glass_notes.py:30](../../../scripts/rebind_glass_notes.py#L30) · `function`.

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

## checked_folder

[scripts/rebind_glass_notes.py:36](../../../scripts/rebind_glass_notes.py#L36) · `function`.

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

## check_database

[scripts/rebind_glass_notes.py:51](../../../scripts/rebind_glass_notes.py#L51) · `function`.

```python
def check_database(db, source, destination):
```

Проверяет целостность и совместимость рабочей SQLite.

Работает с таблицами orders, sqlite_master.

Непосредственные вызовы: `any`, `inside`, `db.execute`, `ValueError`, `db.execute('SELECT 1 FROM sqlite_master WHERE name=?', (name,)).fetchone`, `json.loads`.

Явные исключения: `ValueError`.

## rebind

[scripts/rebind_glass_notes.py:64](../../../scripts/rebind_glass_notes.py#L64) · `function`.

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

## undo

[scripts/rebind_glass_notes.py:136](../../../scripts/rebind_glass_notes.py#L136) · `function`.

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
