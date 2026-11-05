# order_links.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [order_links.py](../../../order_links.py).

Client-order groups with one primary and multiple children, stored by UUID in extra blocks.

Импорты Python, включая локальные: `event_folder_undo`, `folder_structure`, `json`, `orders`, `pathlib`, `uuid`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-OrderLinks"></a>

## OrderLinks

[order_links.py](../../../order_links.py) · `class`.

```python
class OrderLinks:
```

Меняет группы связанных заказов одного объекта в общей транзакции SQLite.

Основные операции: __init__, _rows, _read, read, migrate_statuses; остальные описаны у методов.

<a id="symbol-OrderLinks.__init__"></a>

## OrderLinks.__init__

[order_links.py](../../../order_links.py) · `function`.

```python
def __init__(self, store):
```

Сохраняет зависимости и начальные параметры экземпляра.

Состояние и зависимости сохраняются в полях self для последующих операций.

Прямые присваивания полям/свойствам: `self.store`.

<a id="symbol-OrderLinks._read"></a>

## OrderLinks._read

[order_links.py](../../../order_links.py) · `function`.

```python
def _read(self, db, source):
```

Читает данные текущего формата и сохраняет различие пустого и неизвестного.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `self._rows`, `states(rows).values`, `states`, `group_main`, `str`, `scope`, `ValueError`, `read`, `json.loads`, `rows.values`, `read_primary`, `bool`, `summary.update`, `items.append`, `candidates.append`, `self.store.record`, `sorted`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{'order': self.store.record(source, db), 'linked_ids': identities, 'items': sorted(items, key=key), 'candidates': sorted(candidates, key=key), 'needs_primary': legacy, 'group_error': problem, 'versions': versions}
```

<a id="symbol-OrderLinks._rows"></a>

## OrderLinks._rows

[order_links.py](../../../order_links.py) · `function`.

```python
def _rows(db):
```

Читает строки группы непосредственно из текущей транзакции.

Работает с таблицами orders.

Непосредственные вызовы: `dict`, `db.execute`.

Выражения возврата (ветки читаются в исходнике):

```python
{row['id']: dict(row) for row in db.execute('SELECT * FROM orders')}
```

<a id="symbol-OrderLinks.migrate_statuses"></a>

## OrderLinks.migrate_statuses

[order_links.py](../../../order_links.py) · `function`.

```python
def migrate_statuses(self):
```

Переносит известные прежние статусы по правилам действующего хранилища.

Работает с таблицами metadata_settings, orders.

Непосредственные вызовы: `self.store.connect`, `db.execute`, `db.execute("SELECT 1 FROM metadata_settings WHERE key='client_order_link_status_migrated' AND value='1'").fetchone`, `self._rows`, `child_ids`, `assert_unlocked`, `updates.append`, `db.executemany`, `mark_group_contract`, `len`.

Выражения возврата (ветки читаются в исходнике):

```python
0
len(updates)
```

<a id="symbol-OrderLinks.read"></a>

## OrderLinks.read

[order_links.py](../../../order_links.py) · `function`.

```python
def read(self, relative):
```

Возвращает доступную группу связей и состояние её главного для интерфейса.

Работает с таблицами orders.

Непосредственные вызовы: `self.store.path`, `self.store.connect`, `assert_unlocked`, `db.execute('SELECT * FROM orders WHERE path=?', (relative,)).fetchone`, `db.execute`, `FileNotFoundError`, `self._read`.

Явные исключения: `FileNotFoundError`.

Выражения возврата (ветки читаются в исходнике):

```python
self._read(db, source)
```

<a id="symbol-OrderLinks.save"></a>

## OrderLinks.save

[order_links.py](../../../order_links.py) · `function`.

```python
def save(self, payload):
```

Сохраняет изменение группы и автоматических статусов по проверенным версиям.

Работает с таблицами orders.

Непосредственные вызовы: `self.store.path`, `payload.get`, `checked_ids`, `type`, `ValueError`, `self.store.connect`, `db.execute`, `self._rows`, `rows.get`, `OrderConflict`, `assert_unlocked`, `group_main`, `scope`, `read`, `json.loads`, `isinstance`, `any`, `versions.values`, `json.dumps`, `write`, `updates.append`, `read_primary`, `states(rows).values`, `states`, `self._read`, `set`, `new_ids.add`, `new_ids.discard`, `list`, `db.executemany`, `mark_group_contract`, `db.execute('SELECT * FROM orders WHERE id=?', (main,)).fetchone`, `self.store.record`, `db.execute('SELECT * FROM orders WHERE id=?', (key,)).fetchone`.

Явные исключения: `ValueError`, `OrderConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
{**self._read(db, source), 'records': []}
result
```

<a id="symbol-checked_ids"></a>

## checked_ids

[order_links.py](../../../order_links.py) · `function`.

```python
def checked_ids(value):
```

Проверяет UUID и уникальность списка связанных сущностей.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `len`, `ValueError`, `any`, `set`, `str`, `uuid.UUID`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
value
```

<a id="symbol-child_ids"></a>

## child_ids

[order_links.py](../../../order_links.py) · `function`.

```python
def child_ids(rows):
```

Определяет идентификаторы подчинённых заказов текущей группы.

Возвращает `children`.

Непосредственные вызовы: `set`, `states(rows).items`, `states`, `group_main`, `children.update`, `scope`.

Выражения возврата (ветки читаются в исходнике):

```python
children
```

<a id="symbol-group_main"></a>

## group_main

[order_links.py](../../../order_links.py) · `function`.

```python
def group_main(rows, identity):
```

Находит главного группы и необходимость инициализации прежней связи.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `states`, `ValueError`, `known.items`, `len`, `next`, `iter`, `bool`, `set`, `any`, `known.values`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
(identity, False)
(main, legacy)
```

<a id="symbol-mark_group_contract"></a>

## mark_group_contract

[order_links.py](../../../order_links.py) · `function`.

```python
def mark_group_contract(db):
```

Фиксирует использование направленной группы связанных заказов.

Работает с таблицами metadata_settings.

Непосредственные вызовы: `db.execute`, `mark_status_contract`.

<a id="symbol-mark_status_contract"></a>

## mark_status_contract

[order_links.py](../../../order_links.py) · `function`.

```python
def mark_status_contract(db):
```

Фиксирует использование статуса подчинённого связанного заказа.

Работает с таблицами metadata_settings.

Непосредственные вызовы: `db.execute`.

<a id="symbol-primary_items"></a>

## primary_items

[order_links.py](../../../order_links.py) · `function`.

```python
def primary_items(db, path, identities):
```

Строит компактные ссылки на подчинённые заказы главного.

Работает с таблицами orders.

Непосредственные вызовы: `db.execute`, `','.join`, `rows.get`, `result.append`, `bool`, `scope`, `sorted`.

Выражения возврата (ветки читаются в исходнике):

```python
None
[]
sorted(result, key=lambda item: (item['title'].casefold(), item['id']))
```

<a id="symbol-read"></a>

## read

[order_links.py](../../../order_links.py) · `function`.

```python
def read(blocks, block=BLOCK):
```

Разбирает строгий блок UUID связанных клиентских заказов.

Разбирает JSON; вызывающий код должен учитывать ошибки или неизвестный формат.

Непосредственные вызовы: `json.loads`, `isinstance`, `set`, `type`, `checked_ids`.

Выражения возврата (ветки читаются в исходнике):

```python
[]
None
checked_ids(body['order_ids'])
```

<a id="symbol-read_primary"></a>

## read_primary

[order_links.py](../../../order_links.py) · `function`.

```python
def read_primary(blocks):
```

Читает выбранного главного в группе связанных заказов.

Возвращает `primary if identities is not None and primary is not None and (set(primary) <= set(identities)) else None`.

Непосредственные вызовы: `read`, `set`.

Выражения возврата (ветки читаются в исходнике):

```python
primary if identities is not None and primary is not None and (set(primary) <= set(identities)) else None
```

<a id="symbol-scope"></a>

## scope

[order_links.py](../../../order_links.py) · `function`.

```python
def scope(path):
```

Вычисляет область видимости и допустимых связей текущей сущности.

Возвращает `None`; либо `(location['client_path'], location['object_path'])`.

Непосредственные вызовы: `any`, `part.startswith`, `Path`, `order_location`.

Выражения возврата (ветки читаются в исходнике):

```python
None
(location['client_path'], location['object_path'])
```

<a id="symbol-states"></a>

## states

[order_links.py](../../../order_links.py) · `function`.

```python
def states(rows):
```

Строит состояние группы связей для интерфейса выбора.

Разбирает JSON; вызывающий код должен учитывать ошибки или неизвестный формат.

Непосредственные вызовы: `rows.items`, `json.loads`, `read`, `read_primary`, `set`.

Выражения возврата (ветки читаются в исходнике):

```python
result
```

<a id="symbol-write"></a>

## write

[order_links.py](../../../order_links.py) · `function`.

```python
def write(blocks, identities, primary=None):
```

Сериализует проверенную группу связей, сохраняя остальные блоки заказа.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `read`, `read_primary`, `ValueError`, `checked_ids`, `set`, `json.dumps`, `sorted`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
result
```
