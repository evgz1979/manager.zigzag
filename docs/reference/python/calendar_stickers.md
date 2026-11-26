# calendar_stickers.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [calendar_stickers.py](../../../calendar_stickers.py).

Movable notes over the interactive calendar grid.

Импорты Python, включая локальные: `calendar_events`, `local_metadata`, `order_calendar`, `orders`, `time`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-listed"></a>

## listed

[calendar_stickers.py](../../../calendar_stickers.py) · `function`.

```python
def listed(store):
```

Читает неудалённые листки для главной страницы.

Отдаёт только известный формат, в порядке от старых изменений к новым.

Непосредственные вызовы: `store.connect`, `schema`, `dict`, `db.execute`.

Выражения возврата (ветки читаются в исходнике):

```python
[dict(row) for row in db.execute('SELECT * FROM calendar_stickers WHERE deleted=0 AND version=1 ORDER BY updated,id')]
```

<a id="symbol-read"></a>

## read

[calendar_stickers.py](../../../calendar_stickers.py) · `function`.

```python
def read(store, identity):
```

Читает один стикер по UUID для разрешения конфликта в редакторе.

Возвращает также надгробие удалённой записи, если UUID известен.

Непосредственные вызовы: `CalendarEvents.identity`, `ValueError`, `store.connect`, `schema`, `db.execute('SELECT * FROM calendar_stickers WHERE id=?', (identity,)).fetchone`, `db.execute`, `dict`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
dict(row) if row is not None else None
```

<a id="symbol-save"></a>

## save

[calendar_stickers.py](../../../calendar_stickers.py) · `function`.

```python
def save(store, payload):
```

Сохраняет текст и положение стикера или отмечает его удалённым.

Проверяет ревизию внутри транзакции и допускает точный повтор сохранённого запроса.

Непосредственные вызовы: `CalendarEvents.identity`, `validate_key`, `payload.get`, `ValueError`, `any`, `type`, `isinstance`, `len`, `body.replace('\r\n', '\n').replace`, `body.replace`, `int`, `store.connect`, `db.execute`, `schema`, `db.execute('SELECT * FROM calendar_stickers WHERE id=?', (identity,)).fetchone`, `OrderConflict`, `time.time`, `dict`.

Явные исключения: `ValueError`, `OrderConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
dict(row)
dict(db.execute('SELECT * FROM calendar_stickers WHERE id=?', (identity,)).fetchone())
```

<a id="symbol-schema"></a>

## schema

[calendar_stickers.py](../../../calendar_stickers.py) · `function`.

```python
def schema(db):
```

Создаёт таблицу стикеров и подключает общую историю SQLite.

Координаты от 0 до 10000 задают долю доступной ширины и высоты недели.

Непосредственные вызовы: `local_metadata.schema`, `db.execute`, `local_metadata.audit`.
