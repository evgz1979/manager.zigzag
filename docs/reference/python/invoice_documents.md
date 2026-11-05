# invoice_documents.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [invoice_documents.py](../../../invoice_documents.py).

Immutable closing documents linked to an invoice, with versioned row metadata.

Импорты Python, включая локальные: `base64`, `binascii`, `hashlib`, `invoices`, `json`, `orders`, `os`, `pathlib`, `time`, `unicodedata`, `uuid`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-content"></a>

## content

[invoice_documents.py](../../../invoice_documents.py) · `function`.

```python
def content(store, path, invoice_id, document_id):
```

Читает сохранённые байты документа после проверки владельца.

Работает с таблицами invoice_documents.

Непосредственные вызовы: `identity`, `store.connect`, `parent`, `next`, `db.execute('SELECT * FROM invoice_documents WHERE id=? AND invoice_id=?', (key, row['id'])).fetchone`, `db.execute`, `FileNotFoundError`, `metadata`, `ValueError`, `len`, `hashlib.sha256(body).hexdigest`, `hashlib.sha256`.

Явные исключения: `FileNotFoundError`, `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
(body, document['name'], document['mime'])
```

<a id="symbol-copy_name"></a>

## copy_name

[invoice_documents.py](../../../invoice_documents.py) · `function`.

```python
def copy_name(name, key):
```

Подбирает имя публикуемой копии без замены существующих файлов.

Возвращает `stem + suffix`.

Непосредственные вызовы: `Path`, `len`, `os.fsencode`.

Выражения возврата (ветки читаются в исходнике):

```python
stem + suffix
```

<a id="symbol-filename"></a>

## filename

[invoice_documents.py](../../../invoice_documents.py) · `function`.

```python
def filename(value):
```

Проверяет имя создаваемого или переименовываемого объекта.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `value.startswith`, `any`, `ord`, `ValueError`, `unicodedata.normalize`, `len`, `os.fsencode`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
value
```

<a id="symbol-identity"></a>

## identity

[invoice_documents.py](../../../invoice_documents.py) · `function`.

```python
def identity(value):
```

Проверяет или вычисляет устойчивую идентичность объекта.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `str`, `uuid.UUID`, `ValueError`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
value
```

<a id="symbol-metadata"></a>

## metadata

[invoice_documents.py](../../../invoice_documents.py) · `function`.

```python
def metadata(row):
```

Возвращает метаданные документа без передачи его полного содержимого.

Возвращает `{**{key: row[key] for key in ('id', 'name', 'mime', 'size', 'sha256')}, 'deleted': False}`.

Выражения возврата (ветки читаются в исходнике):

```python
{**{key: row[key] for key in ('id', 'name', 'mime', 'size', 'sha256')}, 'deleted': False}
```

<a id="symbol-parent"></a>

## parent

[invoice_documents.py](../../../invoice_documents.py) · `function`.

```python
def parent(store, db, path, invoice_id, *, write=False):
```

Определяет родительскую папку или заказ по допустимому пути.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `store.current`, `store.owner`, `ValueError`, `json.loads`, `read`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
(row, data, items)
```

<a id="symbol-read"></a>

## read

[invoice_documents.py](../../../invoice_documents.py) · `function`.

```python
def read(data):
```

Разбирает строгий блок назначенных счёту закрывающих документов.

Возвращает `[]`; либо `None`.

Непосредственные вызовы: `isinstance`, `set`, `type`, `len`, `identity`, `filename`, `any`, `seen.add`.

Выражения возврата (ветки читаются в исходнике):

```python
[]
None
items
```

<a id="symbol-save"></a>

## save

[invoice_documents.py](../../../invoice_documents.py) · `function`.

```python
def save(store, db, row, data, items):
```

Сохраняет новый список вложений счёта вместе с invoice_history и revision.

Работает с таблицами invoice_history, invoices.

Непосредственные вызовы: `db.execute`, `time.time`, `json.dumps`, `store.record`, `store.current`.

Выражения возврата (ветки читаются в исходнике):

```python
store.record(store.current(db, row['path'], row['id']))
```

<a id="symbol-schema"></a>

## schema

[invoice_documents.py](../../../invoice_documents.py) · `function`.

```python
def schema(db):
```

Создаёт отсутствующие таблицы и совместимые расширения схемы.

Работает с таблицами invoice_documents.

Непосредственные вызовы: `db.execute`.

<a id="symbol-set_deleted"></a>

## set_deleted

[invoice_documents.py](../../../invoice_documents.py) · `function`.

```python
def set_deleted(store, payload, deleted):
```

Меняет признак корзины, сохраняя саму запись и её историю.

Работает с таблицами invoice_documents.

Непосредственные вызовы: `identity`, `payload.get`, `store.connect`, `db.execute`, `parent`, `type`, `InvoiceConflict`, `next`, `db.execute('SELECT id,version FROM invoice_documents WHERE id=? AND invoice_id=?', (key, row['id'])).fetchone`, `ValueError`, `store.record`, `save`.

Явные исключения: `InvoiceConflict`, `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
store.record(row)
save(store, db, row, data, [{**item, 'deleted': deleted} if item['id'] == key else item for item in items])
```

<a id="symbol-sync"></a>

## sync

[invoice_documents.py](../../../invoice_documents.py) · `function`.

```python
def sync(store):
```

Публикует ожидающие BLOB-вложения в папки без подмены существующих копий.

Работает с таблицами invoice_documents, invoices.

Непосредственные вызовы: `store.connect`, `db.execute`, `db.execute('SELECT * FROM invoice_documents WHERE id=?', (key,)).fetchone`, `db.execute('SELECT path,data,state FROM invoices WHERE id=?', (document['invoice_id'],)).fetchone`, `json.loads(invoice['data']).get`, `json.loads`, `read`, `next`, `metadata`, `hashlib.sha256(document['content']).hexdigest`, `hashlib.sha256`, `ValueError`, `copy_name`, `store.publish_copy`, `str`.

Явные исключения: `ValueError`.

<a id="symbol-upload"></a>

## upload

[invoice_documents.py](../../../invoice_documents.py) · `function`.

```python
def upload(store, payload):
```

Принимает проверенный документ и сохраняет его содержимое.

Работает с таблицами invoice_documents.

Непосредственные вызовы: `identity`, `payload.get`, `filename`, `isinstance`, `len`, `ValueError`, `base64.b64decode`, `content.startswith`, `hashlib.sha256(content).hexdigest`, `hashlib.sha256`, `store.connect`, `db.execute`, `parent`, `db.execute('SELECT id,invoice_id,version,name,sha256,size FROM invoice_documents WHERE id=?', (key,)).fetchone`, `InvoiceConflict`, `any`, `store.record`, `type`, `time.time`, `copy_name`, `save`.

Явные исключения: `ValueError`, `InvoiceConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
store.record(row)
save(store, db, row, data, [*items, item])
```

<a id="symbol-with_copy_status"></a>

## with_copy_status

[invoice_documents.py](../../../invoice_documents.py) · `function`.

```python
def with_copy_status(db, record):
```

Добавляет состояние публикации копии к данным документа.

Работает с таблицами invoice_documents.

Непосредственные вызовы: `dict`, `db.execute`, `copies.get(item['id'], {}).get`, `copies.get`.

Выражения возврата (ветки читаются в исходнике):

```python
record
```
