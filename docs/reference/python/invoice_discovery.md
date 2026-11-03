# invoice_discovery.py

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [invoice_discovery.py:1](../../../invoice_discovery.py#L1).

Offer manually added # bills PDFs; import only after explicit attachment.

Импорты Python, включая локальные: `file_comments`, `file_trash`, `hashlib`, `icloud_access`, `invoices`, `json`, `orders`, `os`, `pathlib`, `stat`, `subprocess`, `time`, `unicodedata`, `uuid`, `work_orders`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## name_key

[invoice_discovery.py:22](../../../invoice_discovery.py#L22) · `function`.

```python
def name_key(name):
```

Строит нормализованный ключ имени для сравнения файлов.

Возвращает `unicodedata.normalize('NFC', name).casefold()`.

Непосредственные вызовы: `unicodedata.normalize('NFC', name).casefold`, `unicodedata.normalize`.

Выражения возврата (ветки читаются в исходнике):

```python
unicodedata.normalize('NFC', name).casefold()
```

## folder_target

[invoice_discovery.py:28](../../../invoice_discovery.py#L28) · `function`.

```python
def folder_target(store, path):
```

Проверяет непосредственную папку счетов выбранного заказа.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `store.store.path`, `work_orders.in_work`, `ValueError`, `store.store.target`, `folder.is_symlink`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
folder
```

## file_key

[invoice_discovery.py:40](../../../invoice_discovery.py#L40) · `function`.

```python
def file_key(target):
```

Строит нормализованный ключ имени для сравнения файлов.

Возвращает `hashlib.sha256(json.dumps(file_trash.fingerprint(target), sort_keys=True).encode()).hexdigest()`.

Непосредственные вызовы: `hashlib.sha256(json.dumps(file_trash.fingerprint(target), sort_keys=True).encode()).hexdigest`, `hashlib.sha256`, `json.dumps(file_trash.fingerprint(target), sort_keys=True).encode`, `json.dumps`, `file_trash.fingerprint`.

Выражения возврата (ветки читаются в исходнике):

```python
hashlib.sha256(json.dumps(file_trash.fingerprint(target), sort_keys=True).encode()).hexdigest()
```

## known_names

[invoice_discovery.py:46](../../../invoice_discovery.py#L46) · `function`.

```python
def known_names(db, path):
```

Собирает уже известные имена счетов и вложений, включая корзину.

Работает с таблицами invoices, invoice_documents.

Непосредственные вызовы: `name_key`, `db.execute`, `names.update`.

Выражения возврата (ветки читаются в исходнике):

```python
names
```

## candidates

[invoice_discovery.py:56](../../../invoice_discovery.py#L56) · `function`.

```python
def candidates(store, path):
```

Перечисляет ещё не прикреплённые непосредственные PDF без чтения содержимого.

Возвращает `{'items': [], 'warning': ''}`.

Непосредственные вызовы: `store.connect`, `store.owner`, `known_names`, `folder_target`, `list`, `folder.iterdir`, `name.startswith`, `target.suffix.casefold`, `name_key`, `target.lstat`, `stat.S_ISREG`, `any`, `ord`, `items.append`, `file_key`, `sorted`.

Выражения возврата (ветки читаются в исходнике):

```python
{'items': [], 'warning': ''}
{'items': sorted(items, key=lambda item: name_key(item['name'])), 'warning': f'Не предложено PDF: {skipped}. Нужен непустой PDF до 20 МБ с обычным именем.' if skipped else ''}
```

## attach

[invoice_discovery.py:85](../../../invoice_discovery.py#L85) · `function`.

```python
def attach(store, payload):
```

Привязывает существующие данные к выбранной сущности или сводке.

Работает с таблицами invoices.

Непосредственные вызовы: `payload.get`, `isinstance`, `name.startswith`, `any`, `ord`, `Path(name).suffix.casefold`, `Path`, `len`, `os.fsencode`, `ValueError`, `invoices.external_comment`, `store.connect`, `store.owner`, `folder_target`, `target.is_symlink`, `target.is_file`, `file_key`, `invoices.InvoiceConflict`, `target.stat`, `icloud_access.read_bytes`, `pdf.startswith`, `str`, `uuid.uuid5`, `json.dumps`, `unicodedata.normalize`, `hashlib.sha256(pdf).hexdigest`, `hashlib.sha256`, `db.execute`, `db.execute("SELECT * FROM invoices WHERE path=? AND state IN ('issued','external')\n                AND pdf=? ORDER BY created,id LIMIT 1", (path, pdf)).fetchone`, `json.loads(existing['data']).get`, `json.loads`, `store.record`, `name_key`, `known_names`, `invoices.today().isoformat`, `invoices.today`, `time.time`, `store.current`.

Явные исключения: `ValueError`, `invoices.InvoiceConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
store.record(existing)
store.record(store.current(db, path, identity))
```
