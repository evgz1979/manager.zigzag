# event_trash.py

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [event_trash.py:1](../../../event_trash.py#L1).

Recoverable removal of immediate events in supplier orders.

Импорты Python, включая локальные: `contextlib`, `datetime`, `folder_layout`, `folder_notes`, `folder_rename`, `folder_rename_undo`, `hashlib`, `json`, `order_folders`, `order_todos`, `orders`, `os`, `pathlib`, `shutil`, `sqlite3`, `uuid`, `work_orders`, `zoneinfo`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## available

[event_trash.py:28](../../../event_trash.py#L28) · `function`.

```python
def available(relative):
```

Проверяет доступность операции для роли и состояния цели.

Возвращает `False`; либо `folder_rename.available(relative) and (not path.name.startswith('#')) and work_orders.supplier_order(path.parent.as_posix())`.

Непосредственные вызовы: `isinstance`, `Path`, `folder_rename.available`, `path.name.startswith`, `work_orders.supplier_order`, `path.parent.as_posix`.

Выражения возврата (ветки читаются в исходнике):

```python
False
folder_rename.available(relative) and (not path.name.startswith('#')) and work_orders.supplier_order(path.parent.as_posix())
```

## preview

[event_trash.py:37](../../../event_trash.py#L37) · `function`.

```python
def preview(store, relative, db=None):
```

Готовит проверяемое предложение операции без её выполнения.

Работает с таблицами orders.

Непосредственные вызовы: `available`, `ValueError`, `folder_rename.preview`, `store.connect`, `preview`, `any`, `paths.inside`, `db.execute`, `scan`, `paths.table`, `list`, `sorted`, `hashlib.sha256(json.dumps(fingerprint, sort_keys=True).encode()).hexdigest`, `hashlib.sha256`, `json.dumps(fingerprint, sort_keys=True).encode`, `json.dumps`, `len`, `Path(relative).parent.as_posix`, `Path`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
preview(store, relative, connection)
{**view, 'revision': hashlib.sha256(json.dumps(fingerprint, sort_keys=True).encode()).hexdigest(), 'count': len(inventory), 'parent': Path(relative).parent.as_posix()}
```

## preview.scan

[event_trash.py:50](../../../event_trash.py#L50) · `function`.

```python
def scan(directory):
```

Обходит разрешённые имена/метаданные для обновления фонового индекса.

Передаёт работу `os.scandir`, `entry.stat`, `inventory.append`.

Непосредственные вызовы: `os.scandir`, `entry.stat`, `inventory.append`, `Path(entry.path).relative_to(store.root / relative).as_posix`, `Path(entry.path).relative_to`, `Path`, `entry.is_dir`, `scan`.

## remove

[event_trash.py:70](../../../event_trash.py#L70) · `function`.

```python
def remove(store, payload):
```

Перемещает подтверждённую папку события поставщика с сохранением журнала и метаданных.

Работает с таблицами folder_renames.

Непосредственные вызовы: `payload.get`, `ValueError`, `store.root.resolve`, `store.connect`, `db.execute`, `preview`, `folder_rename.FolderRenameConflict`, `uuid.uuid4`, `(Path(source).parent / ('.deleted-event-' + token)).as_posix`, `Path`, `paths.check`, `layout.Plan`, `layout_scope`, `plan.move`, `plan.create_session`, `layout.save_json`, `str`, `store.database.resolve`, `shutil.copyfile`, `closing`, `sqlite3.connect`, `store.database.resolve().as_uri`, `original.backup`, `backup.execute('PRAGMA quick_check').fetchone`, `backup.execute`, `datetime.now(ZoneInfo('Europe/Moscow')).isoformat`, `datetime.now`, `ZoneInfo`, `json.dumps`, `db.commit`, `layout.apply`, `paths.rewrite`, `db.rollback`, `paths.undo`, `layout.append`.

Явные исключения: `ValueError`, `folder_rename.FolderRenameConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
{'source': source, 'path': view['parent'], 'session': token}
```

## list_sessions

[event_trash.py:120](../../../event_trash.py#L120) · `function`.

```python
def list_sessions(store):
```

Читает сохранённые сеансы корзины для интерфейса восстановления.

Работает с таблицами folder_renames.

Непосредственные вызовы: `store.connect`, `paths.table`, `db.execute`, `json.loads`, `pair.get`, `result.append`, `sorted`.

Выражения возврата (ветки читаются в исходнике):

```python
[]
sorted(result, key=lambda item: item['created'], reverse=True)
```

## restore

[event_trash.py:135](../../../event_trash.py#L135) · `function`.

```python
def restore(store, token):
```

Возвращает папку события и связанные данные по сохранённому сеансу.

Работает с таблицами folder_renames.

Непосредственные вызовы: `store.connect`, `paths.table`, `list`, `db.execute`, `json.loads`, `pair.get`, `Path`, `store.root.resolve`, `session.is_symlink`, `ValueError`, `paths.undo`, `FileNotFoundError`.

Явные исключения: `ValueError`, `FileNotFoundError`.

Выражения возврата (ветки читаются в исходнике):

```python
{'path': pair['source'], 'session': token}
```
