# catalog_groups.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [catalog_groups.py](../../../catalog_groups.py).

Explicit roles of numbered catalog groups in the working SQLite database.

Импорты Python, включая локальные: `contextlib`, `file_comments`, `folder_structure`, `json`, `local_metadata`, `pathlib`, `sqlite3`, `unicodedata`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-bind"></a>

## bind

[catalog_groups.py](../../../catalog_groups.py) · `function`.

```python
def bind(root, database):
```

Связывает корень документов с его рабочей SQLite для проверок роли по пути.

Чтение роли не открывает iCloud и не создаёт базу.

Непосредственные вызовы: `Path`, `Path(database).absolute`.

<a id="symbol-get"></a>

## get

[catalog_groups.py](../../../catalog_groups.py) · `function`.

```python
def get(root, path, *, db=None):
```

Определяет явно сохранённый тип по имени непосредственной группы.

При переданной транзакции видит её собственные изменения пути.

Непосредственные вызовы: `db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='metadata_records'").fetchone`, `db.execute`, `read`, `UNSET.copy`, `DATABASES.get`, `Path`, `database.is_file`, `closing`, `sqlite3.connect`, `database.as_uri`, `get`.

Выражения возврата (ветки читаются в исходнике):

```python
read(db, path) if has_metadata else UNSET.copy()
get(root, path, db=connection)
UNSET.copy()
```

<a id="symbol-read"></a>

## read

[catalog_groups.py](../../../catalog_groups.py) · `function`.

```python
def read(db, path):
```

Читает сохранённый тип группы и токен версии из открытой базы.

Отсутствие строки означает, что тип ещё не был выбран.

Непосредственные вызовы: `db.execute('SELECT id,revision,data FROM metadata_records WHERE kind=? AND path=?', (KIND, unicodedata.normalize('NFC', path))).fetchone`, `db.execute`, `unicodedata.normalize`, `UNSET.copy`, `json.loads`.

Выражения возврата (ветки читаются в исходнике):

```python
UNSET.copy()
{'type': json.loads(row[2])['type'], 'revision': f'{row[0]}:{row[1]}'}
```

<a id="symbol-save"></a>

## save

[catalog_groups.py](../../../catalog_groups.py) · `function`.

```python
def save(store, payload):
```

Сохраняет первый выбранный тип существующей числовой группы.

Требует отсутствие записи метаданных по полному NFC-пути группы.

Непосредственные вызовы: `payload.get`, `isinstance`, `Path`, `is_catalog_group`, `ValueError`, `target.is_symlink`, `target.is_dir`, `FileNotFoundError`, `MetadataStore`, `metadata.connect`, `audit`, `FileCommentConflict`, `metadata.put`.

Явные исключения: `ValueError`, `FileNotFoundError`, `FileCommentConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
{'type': record['type'], 'revision': record['revision']}
```
