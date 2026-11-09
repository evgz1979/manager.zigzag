# invoice_preferences.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [invoice_preferences.py](../../../invoice_preferences.py).

Shared seller details and grouped products; invoices keep independent snapshots.

Импорты Python, включая локальные: `invoices`, `json`, `time`, `uuid`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-history"></a>

## history

[invoice_preferences.py](../../../invoice_preferences.py) · `function`.

```python
def history(db, key, previous):
```

Сохраняет снимок прежней настройки в общей SQLite-истории.

Вызывается внутри транзакции записи; версии разных ключей независимы.

Непосредственные вызовы: `db.execute`, `json.dumps`, `time.time`.

<a id="symbol-identity"></a>

## identity

[invoice_preferences.py](../../../invoice_preferences.py) · `function`.

```python
def identity(value):
```

Проверяет идентификатор группы или товара.

Принимает только канонический UUID, не превращает произвольный ввод в новый ключ.

Непосредственные вызовы: `str`, `uuid.UUID`, `ValueError`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
value
```

<a id="symbol-read_catalog"></a>

## read_catalog

[invoice_preferences.py](../../../invoice_preferences.py) · `function`.

```python
def read_catalog(db):
```

Читает общий каталог только из SQLite без обхода папок или счетов.

Отсутствие ключа означает пустой каталог; повреждённый JSON вызывает отказ.

Непосредственные вызовы: `db.execute("SELECT value FROM invoice_settings WHERE key='products'").fetchone`, `db.execute`, `dict`, `validate_catalog`, `json.loads`, `ValueError`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
dict(version=1, revision=0, groups=[], products=[])
validate_catalog(json.loads(row[0]))
```

<a id="symbol-read_seller"></a>

## read_seller

[invoice_preferences.py](../../../invoice_preferences.py) · `function`.

```python
def read_seller(db):
```

Читает единые реквизиты вместе с монотонной версией настроек.

Прежний ключ seller поддерживается; неизвестные данные не заменяются значениями по умолчанию.

Непосредственные вызовы: `db.execute("SELECT value FROM invoice_settings WHERE key='seller'").fetchone`, `db.execute`, `db.execute("SELECT value FROM invoice_settings WHERE key='seller_revision'").fetchone`, `raw.isascii`, `raw.isdecimal`, `str`, `int`, `ValueError`, `seller_data`, `json.loads`, `dict`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
dict(revision=int(raw), seller=data)
```

<a id="symbol-resource"></a>

## resource

[invoice_preferences.py](../../../invoice_preferences.py) · `function`.

```python
def resource(store, kind, payload=None):
```

Обслуживает чтение или явную запись одной общей настройки счёта.

Все записи используют BEGIN IMMEDIATE; отсутствующий payload означает только чтение.

Непосредственные вызовы: `store.connect`, `db.execute`, `read_seller`, `write_seller`, `payload.get`, `read_catalog`, `write_catalog`.

Выражения возврата (ветки читаются в исходнике):

```python
read_seller(db) if payload is None else write_seller(db, payload.get('seller'), payload.get('revision'))
read_catalog(db) if payload is None else write_catalog(db, payload)
```

<a id="symbol-seller_data"></a>

## seller_data

[invoice_preferences.py](../../../invoice_preferences.py) · `function`.

```python
def seller_data(value):
```

Проверяет единые реквизиты теми же правилами, что и данные счёта.

Возвращает нормализованную копию без выпуска документа или изменения счетов.

Непосредственные вызовы: `isinstance`, `set`, `ValueError`, `dict`, `invoices.validate`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
invoices.validate(sample)['seller']
```

<a id="symbol-text"></a>

## text

[invoice_preferences.py](../../../invoice_preferences.py) · `function`.

```python
def text(value, limit, label, *, empty=False):
```

Проверяет однострочное название или единицу каталога.

Пустые значения допускаются только для единицы; управляющие символы запрещены.

Непосредственные вызовы: `isinstance`, `len`, `any`, `ord`, `value.strip`, `ValueError`, `str`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
value.strip()
```

<a id="symbol-validate_catalog"></a>

## validate_catalog

[invoice_preferences.py](../../../invoice_preferences.py) · `function`.

```python
def validate_catalog(value):
```

Проверяет сохранённый каталог групп и товаров известной версии.

Плоские группы, точные цены и уникальные UUID обязательны; неизвестные поля не отбрасываются молча.

Непосредственные вызовы: `isinstance`, `set`, `type`, `len`, `ValueError`, `identity`, `text`, `groups.add`, `ids.add`, `invoices.decimal`, `invoices.Decimal`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
value
```

<a id="symbol-write_catalog"></a>

## write_catalog

[invoice_preferences.py](../../../invoice_preferences.py) · `function`.

```python
def write_catalog(db, payload):
```

Сохраняет одну группу или товар по версии общего каталога.

История и запись атомарны; повтор прежней версии отклоняется без автоматического слияния.

Непосредственные вызовы: `read_catalog`, `type`, `payload.get`, `invoices.InvoiceConflict`, `identity`, `isinstance`, `ValueError`, `json.loads`, `json.dumps`, `dict`, `text`, `invoices.decimal`, `invoices.Decimal`, `node.update`, `format`, `next`, `enumerate`, `items.append`, `validate_catalog`, `history`, `db.execute`.

Явные исключения: `invoices.InvoiceConflict`, `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
result
```

<a id="symbol-write_seller"></a>

## write_seller

[invoice_preferences.py](../../../invoice_preferences.py) · `function`.

```python
def write_seller(db, value, revision):
```

Записывает единые реквизиты с проверкой версии и историей одной транзакции.

Совместим с прежним remember_seller; существующие документы не переписывает.

Непосредственные вызовы: `read_seller`, `seller_data`, `type`, `invoices.InvoiceConflict`, `history`, `db.execute`, `json.dumps`, `str`, `dict`.

Явные исключения: `invoices.InvoiceConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
previous
dict(revision=revision + 1, seller=data)
```
