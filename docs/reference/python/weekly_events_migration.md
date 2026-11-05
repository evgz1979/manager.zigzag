# weekly_events_migration.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [weekly_events_migration.py](../../../weekly_events_migration.py).

Consolidate legacy week comments into order calendar events, with a snapshot.

Импорты Python, включая локальные: `argparse`, `contextlib`, `datetime`, `event_folder_undo`, `hashlib`, `json`, `local_metadata`, `order_calendar`, `os`, `pathlib`, `sqlite3`, `uuid`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-changes"></a>

## changes

[weekly_events_migration.py](../../../weekly_events_migration.py) · `function`.

```python
def changes(db):
```

Проверяет весь план объединения недельных полей до первой записи.

Работает с таблицами sqlite_master.

Непосредственные вызовы: `db.execute`, `json.loads`, `value.get`, `order_calendar.unify_weekly_blocks`, `ValueError`, `str`, `json.dumps`, `dict`, `body.pop`, `assert_unlocked`, `result.append`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
result
```

<a id="symbol-main"></a>

## main

[weekly_events_migration.py](../../../weekly_events_migration.py) · `function`.

```python
def main():
```

Разбирает параметры запуска и выполняет основной сценарий программы.

Передаёт работу `argparse.ArgumentParser`, `parser.add_argument`, `parser.parse_args`.

Непосредственные вызовы: `argparse.ArgumentParser`, `parser.add_argument`, `parser.parse_args`, `migrate`, `closing`, `sqlite3.connect`, `args.database.resolve().as_uri`, `args.database.resolve`, `changes`, `sum`, `print`, `json.dumps`.

<a id="symbol-migrate"></a>

## migrate

[weekly_events_migration.py](../../../weekly_events_migration.py) · `function`.

```python
def migrate(database, output):
```

Переносит только допустимые прежние данные с сохранением исходников и истории.

Работает с таблицами metadata_settings.

Непосредственные вызовы: `Path(database).resolve`, `Path`, `closing`, `sqlite3.connect`, `database.as_uri`, `local_metadata.schema`, `local_metadata.audit`, `db.commit`, `db.execute`, `changes`, `db.execute('SELECT value FROM metadata_settings WHERE key=?', (MARKER,)).fetchone`, `db.rollback`, `datetime.now(timezone.utc).strftime`, `datetime.now`, `uuid.uuid4`, `journal.mkdir`, `table_counts`, `source.backup`, `saved.execute`, `saved.execute('PRAGMA integrity_check').fetchone`, `ValueError`, `str`, `hashlib.sha256(backup.read_bytes()).hexdigest`, `hashlib.sha256`, `backup.read_bytes`, `(json.dumps(plan, ensure_ascii=False, indent=2) + '\n').encode`, `json.dumps`, `(journal / 'plan.json').open`, `file.write`, `file.flush`, `os.fsync`, `file.fileno`, `repr`, `hashlib.sha256(raw).hexdigest`, `(journal / '.restore.py').write_text`, `sum`, `(journal / 'result.json').write_text`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{'status': 'already-migrated', 'orders': 0, 'folder_notes': 0}
result
```

<a id="symbol-table_counts"></a>

## table_counts

[weekly_events_migration.py](../../../weekly_events_migration.py) · `function`.

```python
def table_counts(db):
```

Считает строки таблиц для проверки сохранности миграции.

Работает с таблицами sqlite_master.

Непосредственные вызовы: `db.execute`, `db.execute('SELECT count(*) FROM "' + name.replace('"', '""') + '"').fetchone`, `name.replace`.

Выражения возврата (ветки читаются в исходнике):

```python
{name: db.execute('SELECT count(*) FROM "' + name.replace('"', '""') + '"').fetchone()[0] for name in names}
```
