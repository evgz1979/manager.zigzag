# object_years.py

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [object_years.py:1](../../../object_years.py#L1).

Group an object's dated orders by year, with coordinated SQLite paths and undo.

Импорты Python, включая локальные: `contextlib`, `datetime`, `event_folder_undo`, `folder_layout`, `folder_notes`, `folder_rename_undo`, `folder_structure`, `hashlib`, `json`, `order_folders`, `order_todos`, `orders`, `pathlib`, `shutil`, `sqlite3`, `zoneinfo`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## YearGroupConflict

[object_years.py:23](../../../object_years.py#L23) · `class`.

```python
class YearGroupConflict(ValueError):
```

Обозначает конфликт изменения в этом модуле.

Вызывающий обработчик использует тип исключения для отказа без подмены данных.

## _preview

[object_years.py:29](../../../object_years.py#L29) · `function`.

```python
def _preview(store, relative, db):
```

Готовит проверяемое предложение операции без её выполнения.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `Path`, `any`, `p.startswith`, `ValueError`, `store.root.resolve`, `layout.safe_path`, `parent.is_dir`, `folder_role`, `assert_unlocked`, `sorted`, `year_groups`, `parent.iterdir`, `child.name.startswith`, `inventory.append`, `layout.identity`, `child.iterdir`, `p.name.startswith`, `child.is_symlink`, `child.is_dir`, `child.relative_to(root).as_posix`, `child.relative_to`, `dated`, `skipped.append`, `DATE.match`, `len`, `YEAR.fullmatch`, `(container / child.name).relative_to(root).as_posix`, `(container / child.name).relative_to`, `layout.exists`, `conflicts.append`, `restore.check`, `str`, `mappings.append`, `datetime.now(ZoneInfo('Europe/Moscow')).strftime`, `datetime.now`, `ZoneInfo`, `hashlib.sha256(json.dumps(token, sort_keys=True).encode()).hexdigest`, `hashlib.sha256`, `json.dumps(token, sort_keys=True).encode`, `json.dumps`, `list`, `dict.fromkeys`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{'path': relative, 'revision': hashlib.sha256(json.dumps(token, sort_keys=True).encode()).hexdigest(), 'mappings': mappings, 'created_years': created, 'existing_years': existing, 'skipped': skipped, 'conflicts': list(dict.fromkeys(conflicts)), 'before': token}
```

## preview

[object_years.py:88](../../../object_years.py#L88) · `function`.

```python
def preview(store, relative):
```

Готовит проверяемое предложение операции без её выполнения.

Возвращает `_preview(store, relative, db)`.

Непосредственные вызовы: `store.connect`, `_preview`.

Выражения возврата (ветки читаются в исходнике):

```python
_preview(store, relative, db)
```

## group

[object_years.py:95](../../../object_years.py#L95) · `function`.

```python
def group(store, payload):
```

Группирует проверенные записи или папки в предусмотренные категории.

Работает с таблицами folder_renames.

Непосредственные вызовы: `payload.get`, `ValueError`, `store.root.resolve`, `store.connect`, `db.execute`, `_preview`, `YearGroupConflict`, `'; '.join`, `layout.Plan`, `Path`, `plan.mkdir`, `plan.move`, `plan.create_session`, `layout.save_json`, `str`, `store.database.resolve`, `shutil.copyfile`, `closing`, `sqlite3.connect`, `store.database.resolve().as_uri`, `source.backup`, `json.dumps`, `db.commit`, `layout.apply`, `folder_role`, `restore.rewrite`, `db.rollback`, `restore.undo`, `layout.append`, `len`, `session.relative_to(root).as_posix`, `session.relative_to`.

Явные исключения: `ValueError`, `YearGroupConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
{'path': view['path'], 'moved': len(view['mappings']), 'journal': session.relative_to(root).as_posix()}
```
