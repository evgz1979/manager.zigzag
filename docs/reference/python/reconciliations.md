# reconciliations.py

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [reconciliations.py:1](../../../reconciliations.py#L1).

Сверки и единственное назначение счёта; рабочие данные только в SQLite.

Импорты Python, включая локальные: `contextlib`, `event_folder_undo`, `folder_structure`, `json`, `local_metadata`, `order_document`, `pathlib`, `time`, `unicodedata`, `uuid`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## ReconciliationConflict

[reconciliations.py:19](../../../reconciliations.py#L19) · `class`.

```python
class ReconciliationConflict(ValueError):
```

Обозначает конфликт изменения в этом модуле.

Вызывающий обработчик использует тип исключения для отказа без подмены данных.

## schema

[reconciliations.py:25](../../../reconciliations.py#L25) · `function`.

```python
def schema(db):
```

Создаёт отсутствующие таблицы и совместимые расширения схемы.

Работает с таблицами reconciliations, reconciliation_invoices.

Непосредственные вызовы: `local_metadata.schema`, `db.execute`, `local_metadata.audit`.

## mark

[reconciliations.py:39](../../../reconciliations.py#L39) · `function`.

```python
def mark(db):
```

Фиксирует в настройках базы использование несовместимого со старым кодом формата.

Работает с таблицами metadata_settings.

Непосредственные вызовы: `db.execute`.

## checked_path

[reconciliations.py:45](../../../reconciliations.py#L45) · `function`.

```python
def checked_path(path):
```

Проверяет путь и ограничения допустимой операции.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `Path(path).is_absolute`, `Path`, `any`, `p.startswith`, `ValueError`, `unicodedata.normalize`, `Path(path).as_posix`, `in_reconciliations`, `len`, `Path(path).name.startswith`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
path
```

## checked_data

[reconciliations.py:56](../../../reconciliations.py#L56) · `function`.

```python
def checked_data(data):
```

Проверяет точный версионный формат самостоятельной сверки.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `type`, `data.get`, `ValueError`, `len`, `data['title'].strip`, `order_document.validate_todos`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
data
```

## record

[reconciliations.py:72](../../../reconciliations.py#L72) · `function`.

```python
def record(row):
```

Преобразует строку SQLite в представление для вызывающего кода.

Разбирает JSON; вызывающий код должен учитывать ошибки или неизвестный формат.

Непосредственные вызовы: `checked_data`, `json.loads`.

Выражения возврата (ветки читаются в исходнике):

```python
{**data, 'id': row['id'], 'path': row['path'], 'revision': row['revision'], 'updated': row['updated']}
```

## insert

[reconciliations.py:79](../../../reconciliations.py#L79) · `function`.

```python
def insert(db, path, title, identity=None, data=None):
```

Добавляет проверенную запись в текущую транзакцию SQLite.

Работает с таблицами reconciliations.

Непосредственные вызовы: `checked_data`, `db.execute`, `str`, `uuid.uuid4`, `json.dumps`, `time.time`, `mark`.

## invoice_link

[reconciliations.py:88](../../../reconciliations.py#L88) · `function`.

```python
def invoice_link(db, identity):
```

Читает сохранённое назначение счёта самостоятельной сверке.

Работает с таблицами reconciliation_invoices, reconciliations.

Непосредственные вызовы: `db.execute('SELECT * FROM reconciliation_invoices WHERE id=?', (identity,)).fetchone`, `db.execute`, `db.execute('SELECT * FROM reconciliations WHERE id=?', (row['reconciliation_id'],)).fetchone`, `record`.

Выражения возврата (ветки читаются в исходнике):

```python
{'id': row['reconciliation_id'] if row else '', 'revision': row['revision'] if row else 0, 'title': record(target)['title'] if target else '', 'path': target['path'] if target else ''}
```

## untouched_empty_note

[reconciliations.py:97](../../../reconciliations.py#L97) · `function`.

```python
def untouched_empty_note(db, row, data):
```

Распознаёт только нетронутую пустую заметку прежнего фонового импорта.

Работает с таблицами metadata_history.

Непосредственные вызовы: `db.execute("SELECT 1 FROM metadata_history WHERE entity='folder_notes' AND identity=? LIMIT 1", (row['id'],)).fetchone`, `db.execute`.

Выражения возврата (ветки читаются в исходнике):

```python
data == {} and row['revision'] == 1 and (row['exported_revision'] == 1) and (row['file_revision'] == 'database') and (row['parent_order'] == '') and (row['sync_error'] == '') and (not db.execute("SELECT 1 FROM metadata_history WHERE entity='folder_notes' AND identity=? LIMIT 1", (row['id'],)).fetchone())
```

## Reconciliations

[reconciliations.py:106](../../../reconciliations.py#L106) · `class`.

```python
class Reconciliations:
```

Хранит собственные сверки и версионные назначения счетов.

Основные операции: __init__, connect, source, open, catalog; остальные описаны у методов.

## Reconciliations.__init__

[reconciliations.py:109](../../../reconciliations.py#L109) · `function`.

```python
def __init__(self, store):
```

Сохраняет зависимости и начальные параметры экземпляра.

Состояние и зависимости сохраняются в полях self для последующих операций.

Прямые присваивания полям/свойствам: `self.store`.

## Reconciliations.connect

[reconciliations.py:115](../../../reconciliations.py#L115) · `function`.

```python
def connect(self):
```

Открывает соединение SQLite и управляет его временем жизни.

Передаёт ресурс через yield; освобождение выполняется при выходе из контекста.

Непосредственные вызовы: `self.store.connect`, `schema`, `db.commit`.

## Reconciliations.source

[reconciliations.py:123](../../../reconciliations.py#L123) · `function`.

```python
def source(self, db, path):
```

Проверяет прежние источники перед явным переходом карточки в сверку.

Работает с таблицами sqlite_master, orders, folder_notes, reconciliations.

Непосредственные вызовы: `Path`, `db.execute('SELECT 1 FROM sqlite_master WHERE name=?', (table,)).fetchone`, `db.execute`, `len`, `is_moneys_root`, `unicodedata.normalize`, `unicodedata.normalize('NFC', old_parts[1]).lstrip('#').strip().casefold`, `unicodedata.normalize('NFC', old_parts[1]).lstrip('#').strip`, `unicodedata.normalize('NFC', old_parts[1]).lstrip`, `(self.store.root / Path(*old_parts[:2])).exists`, `ReconciliationConflict`, `candidates.add`, `db.execute('SELECT * FROM orders WHERE path=?', (source,)).fetchone`, `db.execute("SELECT 1 FROM sqlite_master WHERE name='folder_notes'").fetchone`, `db.execute('SELECT * FROM folder_notes WHERE path=?', (source,)).fetchone`, `json.loads`, `untouched_empty_note`, `isinstance`, `data.get`, `blocks.get`, `ValueError`, `order_document.read_todos`, `found.append`, `db.execute("SELECT 1 FROM reconciliations WHERE json_extract(data,'$.source_path')=? AND path<>?", (found[0]['source_path'], path)).fetchone`.

Явные исключения: `ReconciliationConflict`, `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
found[0] if found else None
```

## Reconciliations.open

[reconciliations.py:169](../../../reconciliations.py#L169) · `function`.

```python
def open(self, path):
```

Явно открывает сверку и выполняет безопасный переход прежних записей.

Работает с таблицами reconciliations.

Непосредственные вызовы: `checked_path`, `self.store.target`, `target.is_dir`, `FileNotFoundError`, `self.connect`, `assert_unlocked`, `db.execute('SELECT 1 FROM reconciliations WHERE path=?', (path,)).fetchone`, `db.execute`, `self.get`, `local_metadata.MetadataStore(self.store).backup`, `local_metadata.MetadataStore`, `insert`, `Path`, `self.source`.

Явные исключения: `FileNotFoundError`.

Выражения возврата (ветки читаются в исходнике):

```python
self.get(path)
```

## Reconciliations.catalog

[reconciliations.py:189](../../../reconciliations.py#L189) · `function`.

```python
def catalog(self):
```

Собирает доступный каталог сущностей из сохранённых индексов.

Работает с таблицами reconciliations.

Непосредственные вызовы: `self.connect`, `record`, `db.execute`.

Выражения возврата (ветки читаются в исходнике):

```python
[{key: item[key] for key in ('id', 'path', 'title', 'client', 'note', 'revision')} for item in (record(row) for row in db.execute('SELECT * FROM reconciliations ORDER BY path'))]
```

## Reconciliations.with_links

[reconciliations.py:196](../../../reconciliations.py#L196) · `function`.

```python
def with_links(self, items):
```

Дополняет данные сущности её сохранёнными назначениями счетов.

Работает с таблицами reconciliation_invoices.

Непосредственные вызовы: `self.connect`, `db.execute('SELECT 1 FROM reconciliation_invoices WHERE id=?', (item['id'],)).fetchone`, `db.execute`, `invoice_link`.

Выражения возврата (ветки читаются в исходнике):

```python
[{**item, 'reconciliation': invoice_link(db, item['id'])} if db.execute('SELECT 1 FROM reconciliation_invoices WHERE id=?', (item['id'],)).fetchone() else item for item in items]
```

## Reconciliations.get

[reconciliations.py:205](../../../reconciliations.py#L205) · `function`.

```python
def get(self, path):
```

Читает существующую сверку по нормализованному пути из SQLite.

Работает с таблицами reconciliations, sqlite_master, invoices, reconciliation_invoices, orders.

Непосредственные вызовы: `checked_path`, `self.connect`, `assert_unlocked`, `db.execute('SELECT * FROM reconciliations WHERE path=?', (path,)).fetchone`, `db.execute`, `ReconciliationConflict`, `record`, `db.execute("SELECT 1 FROM sqlite_master WHERE name='invoices'").fetchone`, `json.loads`, `db.execute('SELECT title FROM orders WHERE path=?', (invoice['path'],)).fetchone`, `result['invoices'].append`, `data.get`, `bool`.

Явные исключения: `ReconciliationConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
result
```

## Reconciliations.save

[reconciliations.py:230](../../../reconciliations.py#L230) · `function`.

```python
def save(self, payload):
```

Сохраняет клиента, заметку и To-do сверки по UUID и revision.

Работает с таблицами reconciliations.

Непосредственные вызовы: `checked_path`, `payload.get`, `self.connect`, `db.execute`, `assert_unlocked`, `db.execute('SELECT * FROM reconciliations WHERE path=?', (path,)).fetchone`, `type`, `ReconciliationConflict`, `checked_data`, `json.loads`, `json.dumps`, `time.time`, `self.get`.

Явные исключения: `ReconciliationConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
self.get(path)
```

## Reconciliations.assign

[reconciliations.py:248](../../../reconciliations.py#L248) · `function`.

```python
def assign(self, invoices, payload):
```

Переназначает счёт одной сверке с проверкой актуального состояния.

Работает с таблицами reconciliations, reconciliation_invoices.

Непосредственные вызовы: `payload.get`, `isinstance`, `ValueError`, `invoices.connect`, `db.execute`, `schema`, `invoices.current`, `invoice_link`, `type`, `ReconciliationConflict`, `assert_unlocked`, `db.execute('SELECT * FROM reconciliations WHERE id=?', (target_id,)).fetchone`, `checked_path`, `record`, `json.loads(invoice['data']).get`, `json.loads`, `time.time`, `mark`.

Явные исключения: `ValueError`, `ReconciliationConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
invoice_link(db, invoice['id'])
```
