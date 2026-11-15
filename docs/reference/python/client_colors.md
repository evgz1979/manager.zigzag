# client_colors.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [client_colors.py](../../../client_colors.py).

Explicit RGB preferences for the web labels of client folders.

Импорты Python, включая локальные: `event_folder_undo`, `folder_rename`, `folder_structure`, `json`, `local_metadata`, `re`, `time`, `unicodedata`, `uuid`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-ClientColorConflict"></a>

## ClientColorConflict

[client_colors.py](../../../client_colors.py) · `class`.

```python
class ClientColorConflict(ValueError):
```

Обозначает устаревшую версию цвета в открытой форме.

HTTP-обработчик возвращает конфликт без записи новых данных.

<a id="symbol-catalog"></a>

## catalog

[client_colors.py](../../../client_colors.py) · `function`.

```python
def catalog(store):
```

Собирает только вручную заданные цвета для подписей.

Читает SQLite без обхода клиентских папок или автоматических назначений.

Непосредственные вызовы: `store.database.is_file`, `store.connect`, `db.execute("SELECT 1 FROM sqlite_master WHERE name='metadata_records'").fetchone`, `db.execute`, `record`.

Выражения возврата (ветки читаются в исходнике):

```python
{}
{row['path']: color for row in db.execute('SELECT * FROM metadata_records WHERE kind=? ORDER BY path', (KIND,)) if (color := record(row)['color']) is not None}
```

<a id="symbol-checked_path"></a>

## checked_path

[client_colors.py](../../../client_colors.py) · `function`.

```python
def checked_path(store, relative):
```

Проверяет, что открыта существующая папка самого клиента.

Возвращает NFC-путь клиента, включая числовую группу.

Непосредственные вызовы: `target`, `client_path`, `ValueError`, `unicodedata.normalize`, `any`, `part.parent.iterdir`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
unicodedata.normalize('NFC', relative)
```

<a id="symbol-read"></a>

## read

[client_colors.py](../../../client_colors.py) · `function`.

```python
def read(store, relative):
```

Читает состояние редактора одного клиента.

У отсутствующей записи пустой цвет и версия missing.

Непосредственные вызовы: `checked_path`, `store.connect`, `assert_unlocked`, `db.execute("SELECT 1 FROM sqlite_master WHERE name='metadata_records'").fetchone`, `db.execute`, `record`, `db.execute('SELECT * FROM metadata_records WHERE kind=? AND path=?', (KIND, path)).fetchone`.

Выражения возврата (ветки читаются в исходнике):

```python
record(None)
record(db.execute('SELECT * FROM metadata_records WHERE kind=? AND path=?', (KIND, path)).fetchone())
```

<a id="symbol-record"></a>

## record

[client_colors.py](../../../client_colors.py) · `function`.

```python
def record(row):
```

Читает цвет и версию записи для редактора.

Незнакомый формат оставляет запись доступной только для чтения.

Непосредственные вызовы: `json.loads`, `isinstance`, `type`, `data.get`, `RGB.fullmatch`, `data['color'].lower`, `bool`.

Выражения возврата (ветки читаются в исходнике):

```python
{'color': None, 'revision': 'missing', 'editable': True}
{'color': data['color'].lower() if valid and data['color'] else None, 'revision': f"{row['id']}:{row['revision']}", 'editable': bool(valid)}
```

<a id="symbol-save"></a>

## save

[client_colors.py](../../../client_colors.py) · `function`.

```python
def save(store, payload):
```

Сохраняет выбранный RGB или снимает цвет клиента.

Проверяет известный формат и версию под той же транзакцией, где пишется история.

Непосредственные вызовы: `payload.get`, `isinstance`, `RGB.fullmatch`, `ValueError`, `color.lower`, `store.connect`, `db.execute`, `checked_path`, `assert_unlocked`, `schema`, `db.execute('SELECT * FROM metadata_records WHERE kind=? AND path=?', (KIND, path)).fetchone`, `record`, `ClientColorConflict`, `audit`, `json.dumps`, `str`, `uuid.uuid4`, `time.time`.

Явные исключения: `ValueError`, `ClientColorConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
current
record(db.execute('SELECT * FROM metadata_records WHERE kind=? AND path=?', (KIND, path)).fetchone())
```
