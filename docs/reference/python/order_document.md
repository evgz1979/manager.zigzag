# order_document.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [order_document.py](../../../order_document.py).

Legacy card parser and SQLite block codecs; old files cannot rebuild current working metadata.

Импорты Python, включая локальные: `decimal`, `hashlib`, `icloud_access`, `json`, `os`, `pathlib`, `re`, `tempfile`, `time`, `unicodedata`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-archive_current"></a>

## archive_current

[order_document.py](../../../order_document.py) · `function`.

```python
def archive_current(folder):
```

Сохраняет точные исходные байты карточки перед сменой формата.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `source.exists`, `read_text`, `icloud_access.read_bytes`, `hashlib.sha256(raw).hexdigest`, `hashlib.sha256`, `history.is_symlink`, `version.is_symlink`, `ValueError`, `version.mkdir`, `destination.is_symlink`, `destination.exists`, `destination.write_bytes`.

Явные исключения: `ValueError`.

<a id="symbol-archive_legacy"></a>

## archive_legacy

[order_document.py](../../../order_document.py) · `function`.

```python
def archive_legacy(folder):
```

Сохраняет прежние исходники в скрытой истории после успешной записи.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `source.exists`, `source.is_symlink`, `source.is_file`, `ValueError`, `icloud_access.read_bytes`, `hashlib.sha256(raw).hexdigest`, `hashlib.sha256`, `history.is_symlink`, `version.is_symlink`, `version.mkdir`, `destination.is_symlink`, `destination.exists`, `destination.write_bytes`, `source.unlink`.

Явные исключения: `ValueError`.

<a id="symbol-atomic_write"></a>

## atomic_write

[order_document.py](../../../order_document.py) · `function`.

```python
def atomic_write(target, body):
```

Записывает временный файл и атомарно заменяет предусмотренную цель.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `target.is_symlink`, `target.exists`, `target.is_file`, `ValueError`, `tempfile.NamedTemporaryFile`, `Path`, `stream.write`, `stream.flush`, `os.fsync`, `stream.fileno`, `temporary.chmod`, `target.stat`, `temporary.replace`, `temporary.unlink`.

Явные исключения: `ValueError`.

<a id="symbol-display_money"></a>

## display_money

[order_document.py](../../../order_document.py) · `function`.

```python
def display_money(value):
```

Форматирует сохранённое денежное значение для текстовой карточки.

Возвращает `'Не указано' if value is None else f'{Decimal(value) / 100:,.2f}'.replace(',', ' ').replace('.', ',') + ' ₽'`.

Непосредственные вызовы: `f'{Decimal(value) / 100:,.2f}'.replace(',', ' ').replace`, `f'{Decimal(value) / 100:,.2f}'.replace`, `Decimal`.

Выражения возврата (ветки читаются в исходнике):

```python
'Не указано' if value is None else f'{Decimal(value) / 100:,.2f}'.replace(',', ' ').replace('.', ',') + ' ₽'
```

<a id="symbol-folder_note"></a>

## folder_note

[order_document.py](../../../order_document.py) · `function`.

```python
def folder_note(record):
```

Выделяет поля заметки папки из прежней смешанной карточки заказа.

Возвращает `{'note': record.get('note', ''), 'extra_blocks': record.get('extra_blocks', {})}`.

Непосредственные вызовы: `record.get`.

Выражения возврата (ветки читаются в исходнике):

```python
{'note': record.get('note', ''), 'extra_blocks': record.get('extra_blocks', {})}
```

<a id="symbol-load"></a>

## load

[order_document.py](../../../order_document.py) · `function`.

```python
def load(folder, labels):
```

Читает существующий источник и разбирает его поддерживаемым форматом.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `(folder / DOCUMENT).exists`, `(folder / DOCUMENT).is_symlink`, `parse`, `read_text`, `(folder / '.order.json').exists`, `(folder / '.order.json').is_symlink`, `json.loads`, `isinstance`, `ValueError`, `split_statuses`, `card.exists`, `card.is_symlink`, `text.partition`, `tail.rpartition`, `dict`, `line.split`, `heading.splitlines`, `values.get`, `money`, `value.removesuffix`, `(folder / name).exists`, `(folder / name).is_symlink`, `latest.get`, `record.get`, `record.update`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
parse(read_text(folder / DOCUMENT), labels)
split_statuses(value, labels)
record
```

<a id="symbol-money"></a>

## money

[order_document.py](../../../order_document.py) · `function`.

```python
def money(value):
```

Проверяет денежное поле и переводит его в целое внутреннее значение.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `ValueError`, `Decimal`, `str(value).replace(' ', '').replace('\xa0', '').replace`, `str(value).replace(' ', '').replace`, `str(value).replace`, `str`, `number.is_finite`, `(number * 100).to_integral_value`, `int`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
None
int(number * 100)
```

<a id="symbol-parse"></a>

## parse

[order_document.py](../../../order_document.py) · `function`.

```python
def parse(text, labels):
```

Разбирает исходное содержимое, сохраняя неизвестные поля или блоки.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `text.startswith`, `text.partition`, `ValueError`, `split_statuses`, `heading[8:].strip`, `list`, `re.finditer`, `enumerate`, `heading.end`, `len`, `headings[index + 1].start`, `body.removesuffix`, `fields`, `blocks['Заметка'].split`, `any`, `line.startswith`, `int`, `metadata.get`, `'\n'.join`, `blocks.items`, `main.get`, `finance.get`, `money`, `value.removesuffix`, `str`, `float`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
split_statuses({'status': heading[8:].strip(), 'note': note, 'extra_blocks': {}}, labels)
split_statuses(record, labels)
```

<a id="symbol-parse.fields"></a>

## parse.fields

[order_document.py](../../../order_document.py) · `function`.

```python
def fields(name):
```

Разбирает поля одной строки прежнего текстового формата.

Возвращает `result`.

Непосредственные вызовы: `blocks.get(name, '').splitlines`, `blocks.get`, `line.partition`.

Выражения возврата (ветки читаются в исходнике):

```python
result
```

<a id="symbol-purchase_matches_supplier"></a>

## purchase_matches_supplier

[order_document.py](../../../order_document.py) · `function`.

```python
def purchase_matches_supplier(item, supplier):
```

Проверяет принадлежность закупки выбранному поставщику или etc.

Возвращает `not item['suppliers']`; либо `valid_purchase_supplier(supplier) and supplier in item['suppliers']`.

Непосредственные вызовы: `valid_purchase_supplier`.

Выражения возврата (ветки читаются в исходнике):

```python
not item['suppliers']
valid_purchase_supplier(supplier) and supplier in item['suppliers']
```

<a id="symbol-read_blue_plus"></a>

## read_blue_plus

[order_document.py](../../../order_document.py) · `function`.

```python
def read_blue_plus(blocks):
```

Читает независимую отметку заказа без замены неизвестного значения.

Возвращает `False`; либо `{'да': True, 'нет': False}.get(value.strip().casefold()) if isinstance(value, str) else None`.

Непосредственные вызовы: `isinstance`, `{'да': True, 'нет': False}.get`, `value.strip().casefold`, `value.strip`.

Выражения возврата (ветки читаются в исходнике):

```python
False
{'да': True, 'нет': False}.get(value.strip().casefold()) if isinstance(value, str) else None
```

<a id="symbol-read_dollar"></a>

## read_dollar

[order_document.py](../../../order_document.py) · `function`.

```python
def read_dollar(blocks):
```

Читает независимую отметку заказа без замены неизвестного значения.

Возвращает `False`; либо `{'да': True, 'нет': False}.get(value.strip().casefold()) if isinstance(value, str) else None`.

Непосредственные вызовы: `isinstance`, `{'да': True, 'нет': False}.get`, `value.strip().casefold`, `value.strip`.

Выражения возврата (ветки читаются в исходнике):

```python
False
{'да': True, 'нет': False}.get(value.strip().casefold()) if isinstance(value, str) else None
```

<a id="symbol-read_favorite"></a>

## read_favorite

[order_document.py](../../../order_document.py) · `function`.

```python
def read_favorite(blocks):
```

Читает независимую отметку заказа без замены неизвестного значения.

Возвращает `False`; либо `{'да': True, 'нет': False}.get(blocks[FAVORITE_BLOCK].strip().casefold())`.

Непосредственные вызовы: `{'да': True, 'нет': False}.get`, `blocks[FAVORITE_BLOCK].strip().casefold`, `blocks[FAVORITE_BLOCK].strip`.

Выражения возврата (ветки читаются в исходнике):

```python
False
{'да': True, 'нет': False}.get(blocks[FAVORITE_BLOCK].strip().casefold())
```

<a id="symbol-read_flag"></a>

## read_flag

[order_document.py](../../../order_document.py) · `function`.

```python
def read_flag(blocks):
```

Читает независимую отметку заказа без замены неизвестного значения.

Возвращает `False`; либо `{'да': True, 'нет': False}.get(value.strip().casefold()) if isinstance(value, str) else None`.

Непосредственные вызовы: `isinstance`, `{'да': True, 'нет': False}.get`, `value.strip().casefold`, `value.strip`.

Выражения возврата (ветки читаются в исходнике):

```python
False
{'да': True, 'нет': False}.get(value.strip().casefold()) if isinstance(value, str) else None
```

<a id="symbol-read_purchases"></a>

## read_purchases

[order_document.py](../../../order_document.py) · `function`.

```python
def read_purchases(blocks):
```

Разбирает закупки с сохранением признака неизвестного исходного формата.

Возвращает `None`; либо `validate_purchases(items)`.

Непосредственные вызовы: `blocks.get(PURCHASE_BLOCK, '').splitlines`, `blocks.get`, `line.strip`, `re.fullmatch`, `items.append`, `match[1].lower`, `line.startswith`, `len`, `selected.split`, `validate_purchases`.

Выражения возврата (ветки читаются в исходнике):

```python
None
validate_purchases(items)
```

<a id="symbol-read_text"></a>

## read_text

[order_document.py](../../../order_document.py) · `function`.

```python
def read_text(path):
```

Декодирует текст документа поддерживаемыми правилами чтения.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `path.is_symlink`, `path.is_file`, `path.stat`, `ValueError`, `icloud_access.read_bytes(path).decode('utf-8-sig').replace`, `icloud_access.read_bytes(path).decode`, `icloud_access.read_bytes`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
icloud_access.read_bytes(path).decode('utf-8-sig').replace('\r\n', '\n')
```

<a id="symbol-read_todos"></a>

## read_todos

[order_document.py](../../../order_document.py) · `function`.

```python
def read_todos(blocks):
```

Разбирает задачи карточки, отличая пустой список от неизвестного текста.

Возвращает `None`; либо `validate_todos(items)`.

Непосредственные вызовы: `blocks.get`, `body.splitlines`, `line.strip`, `re.fullmatch`, `items.append`, `match[1].lower`, `validate_todos`.

Выражения возврата (ветки читаются в исходнике):

```python
None
validate_todos(items)
```

<a id="symbol-render"></a>

## render

[order_document.py](../../../order_document.py) · `function`.

```python
def render(record, labels):
```

Сериализует карточку в прежний читаемый формат с сохранением дополнительных блоков.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `split_statuses`, `record.get`, `main.append`, `blocks.append`, `'\n'.join`, `any`, `finance.extend`, `display_money`, `record.get('note', '').replace`, `blocks.extend`, `validate_blocks(record.get('extra_blocks', {})).items`, `validate_blocks`, `metadata.append`, `str`, `time.strftime`, `time.localtime`, `'\n\n'.join`, `len`, `text.encode`, `ValueError`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
text
```

<a id="symbol-split_statuses"></a>

## split_statuses

[order_document.py](../../../order_document.py) · `function`.

```python
def split_statuses(record, labels):
```

Разделяет прежние смешанные статусы без выдумывания производственного этапа.

Возвращает `result`.

Непосредственные вызовы: `dict`, `status_key`, `result.setdefault`.

Выражения возврата (ветки читаются в исходнике):

```python
result
```

<a id="symbol-status_key"></a>

## status_key

[order_document.py](../../../order_document.py) · `function`.

```python
def status_key(value, labels):
```

Сопоставляет отображаемую подпись с известным ключом статуса.

Прежние названия сохраняют ключ; неизвестный статус вызывает ValueError.

Непосредственные вызовы: `normalized`, `next`, `labels.items`, `ValueError`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
'process'
'done'
status
```

<a id="symbol-valid_purchase_supplier"></a>

## valid_purchase_supplier

[order_document.py](../../../order_document.py) · `function`.

```python
def valid_purchase_supplier(name):
```

Проверяет допустимый ключ поставщика закупки.

Формирует возвращаемое значение из проверенного локального состояния.

Непосредственные вызовы: `isinstance`, `len`, `unicodedata.normalize('NFC', name).strip().casefold`, `unicodedata.normalize('NFC', name).strip`, `unicodedata.normalize`, `name.startswith`, `any`, `ord`, `name.splitlines`.

Выражения возврата (ветки читаются в исходнике):

```python
isinstance(name, str) and 0 < len(name) <= 200 and (name == unicodedata.normalize('NFC', name).strip().casefold()) and (name not in {'etc', '—', '.', '..'}) and (not name.startswith('.')) and (not any((char in name for char in '/\\,#'))) and (not any((ord(char) < 32 for char in name))) and (len(name.splitlines()) == 1)
```

<a id="symbol-validate_blocks"></a>

## validate_blocks

[order_document.py](../../../order_document.py) · `function`.

```python
def validate_blocks(blocks):
```

Проверяет имена и текст дополнительных блоков карточки.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `any`, `blocks.items`, `ValueError`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
blocks
```

<a id="symbol-validate_purchases"></a>

## validate_purchases

[order_document.py](../../../order_document.py) · `function`.

```python
def validate_purchases(items):
```

Проверяет структуру закупок, их текст, выполнение и назначения.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `validate_todos`, `zip`, `raw.get`, `isinstance`, `len`, `any`, `valid_purchase_supplier`, `set`, `ValueError`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
result
```

<a id="symbol-validate_todos"></a>

## validate_todos

[order_document.py](../../../order_document.py) · `function`.

```python
def validate_todos(items):
```

Проверяет допустимую структуру строк собственных задач.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `len`, `ValueError`, `item.get`, `type`, `item['text'].strip`, `any`, `result.append`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
result
```

<a id="symbol-write_blue_plus"></a>

## write_blue_plus

[order_document.py](../../../order_document.py) · `function`.

```python
def write_blue_plus(blocks, value):
```

Сериализует одну отметку заказа, сохраняя остальные блоки.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `type`, `ValueError`, `read_blue_plus`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{**blocks, BLUE_PLUS_BLOCK: 'Да' if value else 'Нет'}
```

<a id="symbol-write_dollar"></a>

## write_dollar

[order_document.py](../../../order_document.py) · `function`.

```python
def write_dollar(blocks, value):
```

Сериализует одну отметку заказа, сохраняя остальные блоки.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `type`, `ValueError`, `read_dollar`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{**blocks, DOLLAR_BLOCK: 'Да' if value else 'Нет'}
```

<a id="symbol-write_favorite"></a>

## write_favorite

[order_document.py](../../../order_document.py) · `function`.

```python
def write_favorite(blocks, value):
```

Сериализует одну отметку заказа, сохраняя остальные блоки.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `type`, `ValueError`, `read_favorite`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{**blocks, FAVORITE_BLOCK: 'Да' if value else 'Нет'}
```

<a id="symbol-write_flag"></a>

## write_flag

[order_document.py](../../../order_document.py) · `function`.

```python
def write_flag(blocks, value):
```

Сериализует одну отметку заказа, сохраняя остальные блоки.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `type`, `ValueError`, `read_flag`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{**blocks, FLAG_BLOCK: 'Да' if value else 'Нет'}
```

<a id="symbol-write_purchase_done"></a>

## write_purchase_done

[order_document.py](../../../order_document.py) · `function`.

```python
def write_purchase_done(blocks, index, text, supplier, done):
```

Меняет только исходный checkbox закупки, сохраняя формат остальных строк.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `read_purchases`, `ValueError`, `type`, `len`, `purchase_matches_supplier`, `blocks[PURCHASE_BLOCK].splitlines`, `enumerate`, `line.startswith`, `''.join`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{**blocks, PURCHASE_BLOCK: ''.join(lines)}
```

<a id="symbol-write_purchase_text"></a>

## write_purchase_text

[order_document.py](../../../order_document.py) · `function`.

```python
def write_purchase_text(blocks, index, text, supplier, new_text):
```

Меняет текст одной закупки, сохраняя выполнение, назначения и переводы строк.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `read_purchases`, `ValueError`, `type`, `len`, `purchase_matches_supplier`, `validate_todos`, `value.splitlines`, `blocks[PURCHASE_BLOCK].splitlines`, `enumerate`, `line.startswith`, `line.rstrip`, `''.join`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{**blocks, PURCHASE_BLOCK: ''.join(lines)}
```

<a id="symbol-write_purchases"></a>

## write_purchases

[order_document.py](../../../order_document.py) · `function`.

```python
def write_purchases(blocks, items):
```

Сериализует известные закупки и сохраняет прочие блоки карточки.

Возвращает `result`.

Непосредственные вызовы: `dict`, `'\n'.join`, `', '.join`, `validate_purchases`.

Выражения возврата (ветки читаются в исходнике):

```python
result
```

<a id="symbol-write_todos"></a>

## write_todos

[order_document.py](../../../order_document.py) · `function`.

```python
def write_todos(blocks, items):
```

Сериализует задачи и сохраняет прочие дополнительные блоки.

Возвращает `result`.

Непосредственные вызовы: `dict`, `'\n'.join`, `validate_todos`.

Выражения возврата (ветки читаются в исходнике):

```python
result
```
