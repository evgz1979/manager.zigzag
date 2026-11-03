# work_orders.py

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [work_orders.py:1](../../../work_orders.py#L1).

Production roles, supplier statuses, palettes, favorite sections and UUID selections.

Импорты Python, включая локальные: `datetime`, `event_folder_undo`, `folder_structure`, `json`, `local_metadata`, `pathlib`, `time`, `unicodedata`, `uuid`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## SupplierFavoriteConflict

[work_orders.py:30](../../../work_orders.py#L30) · `class`.

```python
class SupplierFavoriteConflict(ValueError):
```

Обозначает конфликт изменения в этом модуле.

Вызывающий обработчик использует тип исключения для отказа без подмены данных.

## supplier_root_path

[work_orders.py:36](../../../work_orders.py#L36) · `function`.

```python
def supplier_root_path(relative):
```

Выделяет корень производства или реальный раздел поставщика по пути.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `len`, `Path`, `is_work_root`, `ValueError`, `unicodedata.normalize`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
unicodedata.normalize('NFC', relative)
```

## supplier_section_path

[work_orders.py:44](../../../work_orders.py#L44) · `function`.

```python
def supplier_section_path(relative):
```

Выделяет корень производства или реальный раздел поставщика по пути.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `ValueError`, `Path`, `len`, `is_work_root`, `parts[1].startswith`, `unicodedata.normalize`, `Path(*parts).as_posix`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
unicodedata.normalize('NFC', Path(*parts).as_posix())
```

## is_etc_section

[work_orders.py:55](../../../work_orders.py#L55) · `function`.

```python
def is_etc_section(relative):
```

Распознаёт сводку закупок без выбранного поставщика.

Возвращает `len(parts) == 2 and is_work_root(parts[0]) and (parts[1].removeprefix('#').strip().casefold() == 'etc')`.

Непосредственные вызовы: `Path`, `len`, `is_work_root`, `parts[1].removeprefix('#').strip().casefold`, `parts[1].removeprefix('#').strip`, `parts[1].removeprefix`.

Выражения возврата (ветки читаются в исходнике):

```python
len(parts) == 2 and is_work_root(parts[0]) and (parts[1].removeprefix('#').strip().casefold() == 'etc')
```

## supplier_favorite_record

[work_orders.py:62](../../../work_orders.py#L62) · `function`.

```python
def supplier_favorite_record(row):
```

Читает сохранённую звезду производственного раздела.

Разбирает JSON; вызывающий код должен учитывать ошибки или неизвестный формат.

Непосредственные вызовы: `json.loads`, `isinstance`, `type`, `data.get`.

Выражения возврата (ветки читаются в исходнике):

```python
{'path': row['path'], 'revision': f"{row['id']}:{row['revision']}", 'is_favorite': data['is_favorite'] if valid else None, 'position': data.get('position') if valid else None, 'editable': valid}
```

## supplier_favorites

[work_orders.py:78](../../../work_orders.py#L78) · `function`.

```python
def supplier_favorites(db, root, paths):
```

Однократно инициализирует и читает избранные разделы корня.

Работает с таблицами metadata_records.

Непосредственные вызовы: `supplier_root_path`, `supplier_section_path`, `any`, `Path(path).parent.as_posix`, `Path`, `ValueError`, `db.execute`, `schema`, `audit`, `assert_unlocked`, `db.execute('SELECT data FROM metadata_records WHERE kind=? AND path=?', (SUPPLIER_FAVORITE_INIT_KIND, root)).fetchone`, `json.loads`, `db.execute('SELECT * FROM metadata_records WHERE kind=? AND path=?', (SUPPLIER_FAVORITE_KIND, path)).fetchone`, `Path(path).name[1:].strip().lower`, `Path(path).name[1:].strip`, `bool`, `INITIAL_SUPPLIER_FAVORITES.index`, `str`, `uuid.uuid4`, `json.dumps`, `time.time`, `supplier_favorite_record`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
result
```

## read_supplier_favorites

[work_orders.py:114](../../../work_orders.py#L114) · `function`.

```python
def read_supplier_favorites(store, root):
```

Возвращает список избранных производственных разделов из SQLite.

Работает с таблицами metadata_records.

Непосредственные вызовы: `supplier_root_path`, `store.connect`, `schema`, `assert_unlocked`, `supplier_favorite_record`, `db.execute`, `Path(row['path']).parent.as_posix`, `Path`.

Выражения возврата (ветки читаются в исходнике):

```python
{row['path']: supplier_favorite_record(row) for row in db.execute('SELECT * FROM metadata_records WHERE kind=?', (SUPPLIER_FAVORITE_KIND,)) if Path(row['path']).parent.as_posix() == root}
```

## save_supplier_favorite

[work_orders.py:127](../../../work_orders.py#L127) · `function`.

```python
def save_supplier_favorite(store, payload):
```

Меняет звезду одного раздела с проверкой актуального состояния.

Работает с таблицами metadata_records.

Непосредственные вызовы: `supplier_section_path`, `payload.get`, `type`, `isinstance`, `ValueError`, `store.connect`, `db.execute`, `schema`, `audit`, `assert_unlocked`, `db.execute('SELECT * FROM metadata_records WHERE kind=? AND path=?', (SUPPLIER_FAVORITE_KIND, path)).fetchone`, `supplier_favorite_record`, `SupplierFavoriteConflict`, `json.loads`, `read_favorite_rows`, `Path(path).parent.as_posix`, `Path`, `max`, `json.dumps`, `time.time`, `db.execute('SELECT * FROM metadata_records WHERE id=?', (row['id'],)).fetchone`.

Явные исключения: `ValueError`, `SupplierFavoriteConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
current
supplier_favorite_record(db.execute('SELECT * FROM metadata_records WHERE id=?', (row['id'],)).fetchone())
```

## read_favorite_rows

[work_orders.py:159](../../../work_orders.py#L159) · `function`.

```python
def read_favorite_rows(db, root):
```

Читает строки настроек избранных разделов из текущего соединения.

Работает с таблицами metadata_records.

Непосредственные вызовы: `supplier_favorite_record`, `db.execute`, `Path(row['path']).parent.as_posix`, `Path`.

Выражения возврата (ветки читаются в исходнике):

```python
[supplier_favorite_record(row) for row in db.execute('SELECT * FROM metadata_records WHERE kind=?', (SUPPLIER_FAVORITE_KIND,)) if Path(row['path']).parent.as_posix() == root]
```

## in_work

[work_orders.py:166](../../../work_orders.py#L166) · `function`.

```python
def in_work(relative):
```

Проверяет принадлежность пути производственному дереву # work.

Возвращает `bool(parts and is_work_root(parts[0]))`.

Непосредственные вызовы: `Path`, `bool`, `is_work_root`.

Выражения возврата (ветки читаются в исходнике):

```python
bool(parts and is_work_root(parts[0]))
```

## direct_order

[work_orders.py:173](../../../work_orders.py#L173) · `function`.

```python
def direct_order(relative):
```

Распознаёт непосредственный заказ раздела поставщика.

Возвращает `len(parts) == 2 and is_work_root(parts[0]) and dated(parts[1])`.

Непосредственные вызовы: `Path`, `len`, `is_work_root`, `dated`.

Выражения возврата (ветки читаются в исходнике):

```python
len(parts) == 2 and is_work_root(parts[0]) and dated(parts[1])
```

## supplier_name

[work_orders.py:180](../../../work_orders.py#L180) · `function`.

```python
def supplier_name(relative):
```

Определяет подпись реального раздела поставщика по пути.

Возвращает `''`; либо `parts[1][1:].strip() if parts[1].startswith('#') else parts[1]`.

Непосредственные вызовы: `Path`, `len`, `is_work_root`, `dated`, `parts[1].startswith`, `parts[1][1:].strip`.

Выражения возврата (ветки читаются в исходнике):

```python
''
parts[1][1:].strip() if parts[1].startswith('#') else parts[1]
```

## new_supplier_hue

[work_orders.py:190](../../../work_orders.py#L190) · `function`.

```python
def new_supplier_hue(db, name):
```

Выбирает наименее занятый оттенок только для нового поставщика.

Работает с таблицами metadata_records.

Непосредственные вызовы: `list`, `SUPPLIER_PALETTE.values`, `db.execute('SELECT data FROM metadata_records WHERE kind=?', (SUPPLIER_COLOR_KIND,)).fetchall`, `db.execute`, `json.loads`, `isinstance`, `type`, `data.get`, `used.append`, `ord`, `range`, `max`.

Выражения возврата (ветки читаются в исходнике):

```python
max(candidates, key=lambda hue: min((min((hue - other) % 360, (other - hue) % 360) for other in used)))
```

## supplier_color

[work_orders.py:209](../../../work_orders.py#L209) · `function`.

```python
def supplier_color(db, relative):
```

Читает или однократно назначает устойчивый цвет раздела поставщика.

Работает с таблицами sqlite_master, metadata_records.

Непосредственные вызовы: `Path`, `len`, `is_work_root`, `dated`, `unicodedata.normalize`, `Path(*parts[:2]).as_posix`, `assert_unlocked`, `db.execute("SELECT 1 FROM sqlite_master WHERE name='metadata_records'").fetchone`, `db.execute`, `schema`, `audit`, `parts[1].startswith`, `parts[1][1:].strip`, `unicodedata.normalize('NFC', name).lower`, `db.execute('SELECT * FROM metadata_records WHERE kind=? AND path=?', (SUPPLIER_COLOR_KIND, path)).fetchone`, `new_supplier_hue`, `str`, `uuid.uuid4`, `json.dumps`, `time.time`, `json.loads`, `isinstance`, `type`, `data.get`, `ValueError`, `SUPPLIER_PALETTE.get`, `supplier_color`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
None
supplier_color(db, relative)
{'hue': data['hue'], 'neutral': data['neutral']}
```

## supplier_order

[work_orders.py:247](../../../work_orders.py#L247) · `function`.

```python
def supplier_order(relative):
```

Определяет принадлежность записи заказам поставщиков.

Возвращает `False`; либо `len(parts) == 3 and is_work_root(parts[0]) and (not dated(parts[1])) or (len(parts) == 2 and is_supplier_root(parts[0]))`.

Непосредственные вызовы: `Path`, `is_service_folder`, `is_print_section`, `Path(relative).parent.as_posix`, `len`, `is_work_root`, `dated`, `is_supplier_root`.

Выражения возврата (ветки читаются в исходнике):

```python
False
len(parts) == 3 and is_work_root(parts[0]) and (not dated(parts[1])) or (len(parts) == 2 and is_supplier_root(parts[0]))
```

## status_order

[work_orders.py:257](../../../work_orders.py#L257) · `function`.

```python
def status_order(relative):
```

Проверяет применимость самостоятельного статуса поставщика к пути.

Возвращает `direct_order(relative) or (supplier_order(relative) and (not in_freza(relative)))`.

Непосредственные вызовы: `direct_order`, `supplier_order`, `in_freza`.

Выражения возврата (ветки читаются в исходнике):

```python
direct_order(relative) or (supplier_order(relative) and (not in_freza(relative)))
```

## folder_date

[work_orders.py:263](../../../work_orders.py#L263) · `function`.

```python
def folder_date(relative):
```

Извлекает принятую дату заказа из названия папки.

Возвращает `None`; либо `f'{year:04d}-{month:02d}-{day:02d}'`.

Непосредственные вызовы: `Path`, `dated`, `DATE.match`, `map`, `match.groups`, `len`.

Выражения возврата (ветки читаются в исходнике):

```python
None
f'{year:04d}-{month:02d}-{day:02d}'
```

## read_status

[work_orders.py:276](../../../work_orders.py#L276) · `function`.

```python
def read_status(blocks):
```

Читает самостоятельный статус поставщика из известного блока.

Возвращает `'work'`; либо `next((key for (key, label) in STATUS_LABELS.items() if blocks[STATUS_BLOCK] == label), None)`.

Непосредственные вызовы: `next`, `STATUS_LABELS.items`.

Выражения возврата (ветки читаются в исходнике):

```python
'work'
next((key for (key, label) in STATUS_LABELS.items() if blocks[STATUS_BLOCK] == label), None)
```

## write_status

[work_orders.py:284](../../../work_orders.py#L284) · `function`.

```python
def write_status(blocks, status):
```

Сериализует самостоятельный статус поставщика без изменения остальных блоков.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `ValueError`, `read_status`, `archive_time`, `datetime.now(timezone.utc).isoformat`, `datetime.now`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
updated
```

## archive_time

[work_orders.py:299](../../../work_orders.py#L299) · `function`.

```python
def archive_time(blocks):
```

Читает сохранённое время перемещения заказа в архивную группу.

Возвращает `None`; либо `stamp.timestamp() if stamp.tzinfo is not None else None`.

Непосредственные вызовы: `blocks.get`, `isinstance`, `datetime.fromisoformat`, `stamp.timestamp`.

Выражения возврата (ветки читаются в исходнике):

```python
None
stamp.timestamp() if stamp.tzinfo is not None else None
```

## archived

[work_orders.py:312](../../../work_orders.py#L312) · `function`.

```python
def archived(order):
```

Проверяет попадание производственного заказа в архив по сохранённым данным.

Возвращает `status_order(order['path']) and read_status(order.get('extra_blocks', {})) == 'archived'`.

Непосредственные вызовы: `status_order`, `read_status`, `order.get`.

Выражения возврата (ветки читаются в исходнике):

```python
status_order(order['path']) and read_status(order.get('extra_blocks', {})) == 'archived'
```

## checked_ids

[work_orders.py:318](../../../work_orders.py#L318) · `function`.

```python
def checked_ids(value):
```

Проверяет UUID и уникальность списка связанных сущностей.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `len`, `any`, `ValueError`, `set`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
value
```

## read_links

[work_orders.py:329](../../../work_orders.py#L329) · `function`.

```python
def read_links(blocks):
```

Читает строгий список UUID связанной подборки заказов поставщиков.

Разбирает JSON; вызывающий код должен учитывать ошибки или неизвестный формат.

Непосредственные вызовы: `json.loads`, `isinstance`, `set`, `type`, `checked_ids`.

Выражения возврата (ветки читаются в исходнике):

```python
[]
None
checked_ids(body['order_ids'])
```

## write_links

[work_orders.py:343](../../../work_orders.py#L343) · `function`.

```python
def write_links(blocks, identities):
```

Сохраняет проверенные UUID связанной подборки в дополнительном блоке.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `read_links`, `ValueError`, `json.dumps`, `checked_ids`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{**blocks, LINKS_BLOCK: json.dumps({'version': 1, 'order_ids': checked_ids(identities)}, ensure_ascii=False)}
```

## summary

[work_orders.py:351](../../../work_orders.py#L351) · `function`.

```python
def summary(row):
```

Формирует сводное представление производственного заказа.

Формирует возвращаемое значение из проверенного локального состояния.

Непосредственные вызовы: `Path`, `status_order`, `read_status`, `row.get`.

Выражения возврата (ветки читаются в исходнике):

```python
{key: row[key] for key in ('id', 'path', 'title', 'status', 'registered')} | {'supplier': Path(row['path']).parts[-2]} | ({'supplier_status': read_status(row.get('extra_blocks', {}))} if status_order(row['path']) else {})
```
