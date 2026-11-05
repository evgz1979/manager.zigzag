# calendar_events.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [calendar_events.py](../../../calendar_events.py).

Standalone day/week events in the working SQLite database.

Импорты Python, включая локальные: `contextlib`, `datetime`, `local_metadata`, `order_calendar`, `orders`, `time`, `uuid`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-CalendarEvents"></a>

## CalendarEvents

[calendar_events.py](../../../calendar_events.py) · `class`.

```python
class CalendarEvents:
```

Хранит свободные дневные и недельные события с UUID/revision и историей.

Основные операции: __init__, connect, identity, record, validate; остальные описаны у методов.

<a id="symbol-CalendarEvents.__init__"></a>

## CalendarEvents.__init__

[calendar_events.py](../../../calendar_events.py) · `function`.

```python
def __init__(self, store):
```

Сохраняет зависимости и начальные параметры экземпляра.

Состояние и зависимости сохраняются в полях self для последующих операций.

Прямые присваивания полям/свойствам: `self.store`.

<a id="symbol-CalendarEvents._set_flag"></a>

## CalendarEvents._set_flag

[calendar_events.py](../../../calendar_events.py) · `function`.

```python
def _set_flag(self, payload, field):
```

Обрабатывает общий контракт независимой отметки календаря.

Работает с таблицами calendar_events.

Непосредственные вызовы: `self.identity`, `payload.get`, `type`, `ValueError`, `self.connect`, `db.execute`, `db.execute('SELECT * FROM calendar_events WHERE id=?', (identity,)).fetchone`, `OrderConflict`, `self.validate`, `int`, `time.time`, `order_calendar.mark_flag_contract`, `self.record`.

Явные исключения: `ValueError`, `OrderConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
self.record(db.execute('SELECT * FROM calendar_events WHERE id=?', (identity,)).fetchone())
```

<a id="symbol-CalendarEvents.color"></a>

## CalendarEvents.color

[calendar_events.py](../../../calendar_events.py) · `function`.

```python
def color(self, payload):
```

Меняет выбранный цвет события, сохраняя остальные признаки.

Работает с таблицами calendar_events.

Непосредственные вызовы: `self.identity`, `payload.get`, `isinstance`, `ValueError`, `self.connect`, `db.execute`, `db.execute('SELECT * FROM calendar_events WHERE id=?', (identity,)).fetchone`, `OrderConflict`, `self.validate`, `time.time`, `self.record`.

Явные исключения: `ValueError`, `OrderConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
self.record(db.execute('SELECT * FROM calendar_events WHERE id=?', (identity,)).fetchone())
```

<a id="symbol-CalendarEvents.connect"></a>

## CalendarEvents.connect

[calendar_events.py](../../../calendar_events.py) · `function`.

```python
def connect(self):
```

Открывает соединение SQLite и управляет его временем жизни.

Передаёт ресурс через yield; освобождение выполняется при выходе из контекста.

Непосредственные вызовы: `self.store.connect`, `schema`.

<a id="symbol-CalendarEvents.get"></a>

## CalendarEvents.get

[calendar_events.py](../../../calendar_events.py) · `function`.

```python
def get(self, identity):
```

Находит свободное событие по UUID в текущей транзакции.

Работает с таблицами calendar_events.

Непосредственные вызовы: `self.identity`, `self.connect`, `db.execute('SELECT * FROM calendar_events WHERE id=?', (identity,)).fetchone`, `db.execute`, `FileNotFoundError`, `self.record`.

Явные исключения: `FileNotFoundError`.

Выражения возврата (ветки читаются в исходнике):

```python
self.record(row)
```

<a id="symbol-CalendarEvents.identity"></a>

## CalendarEvents.identity

[calendar_events.py](../../../calendar_events.py) · `function`.

```python
def identity(payload):
```

Проверяет или вычисляет устойчивую идентичность объекта.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `payload.get`, `isinstance`, `str`, `uuid.UUID`, `ValueError`, `type`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
(identity, revision)
```

<a id="symbol-CalendarEvents.list"></a>

## CalendarEvents.list

[calendar_events.py](../../../calendar_events.py) · `function`.

```python
def list(self):
```

Читает все неудалённые свободные события из SQLite.

Работает с таблицами calendar_events.

Непосредственные вызовы: `self.connect`, `self.record`, `db.execute`.

Выражения возврата (ветки читаются в исходнике):

```python
[self.record(row) for row in db.execute('SELECT * FROM calendar_events WHERE deleted=0 ORDER BY created,id')]
```

<a id="symbol-CalendarEvents.move"></a>

## CalendarEvents.move

[calendar_events.py](../../../calendar_events.py) · `function`.

```python
def move(self, payload):
```

Переносит объект или событие с проверкой исходного и целевого состояния.

Работает с таблицами calendar_events.

Непосредственные вызовы: `self.identity`, `payload.get`, `self.connect`, `db.execute`, `db.execute('SELECT * FROM calendar_events WHERE id=?', (identity,)).fetchone`, `OrderConflict`, `self.validate`, `type`, `ValueError`, `(date.fromisoformat(row['date']) + timedelta(days=days)).isoformat`, `date.fromisoformat`, `timedelta`, `time.time`, `self.record`.

Явные исключения: `OrderConflict`, `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
self.record(db.execute('SELECT * FROM calendar_events WHERE id=?', (identity,)).fetchone())
```

<a id="symbol-CalendarEvents.record"></a>

## CalendarEvents.record

[calendar_events.py](../../../calendar_events.py) · `function`.

```python
def record(row):
```

Преобразует строку SQLite в представление для вызывающего кода.

Возвращает `dict(row) if row is not None else None`.

Непосредственные вызовы: `dict`.

Выражения возврата (ветки читаются в исходнике):

```python
dict(row) if row is not None else None
```

<a id="symbol-CalendarEvents.save"></a>

## CalendarEvents.save

[calendar_events.py](../../../calendar_events.py) · `function`.

```python
def save(self, payload):
```

Создаёт или меняет свободное событие с проверкой ожидаемой версии.

Работает с таблицами calendar_events.

Непосредственные вызовы: `self.identity`, `payload.get`, `order_calendar.block_name`, `order_calendar.validate_key`, `order_calendar.validate_text`, `self.connect`, `db.execute`, `db.execute('SELECT * FROM calendar_events WHERE id=?', (identity,)).fetchone`, `OrderConflict`, `ValueError`, `time.time`, `self.validate`, `self.record`, `order_calendar.mark_relevance_contract`.

Явные исключения: `OrderConflict`, `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
self.record(row)
self.record(db.execute('SELECT * FROM calendar_events WHERE id=?', (identity,)).fetchone())
```

<a id="symbol-CalendarEvents.set_completed"></a>

## CalendarEvents.set_completed

[calendar_events.py](../../../calendar_events.py) · `function`.

```python
def set_completed(self, payload):
```

Меняет только независимую отметку выполнения события.

Возвращает `self._set_flag(payload, 'is_completed')`.

Непосредственные вызовы: `self._set_flag`.

Выражения возврата (ветки читаются в исходнике):

```python
self._set_flag(payload, 'is_completed')
```

<a id="symbol-CalendarEvents.set_deleted"></a>

## CalendarEvents.set_deleted

[calendar_events.py](../../../calendar_events.py) · `function`.

```python
def set_deleted(self, payload, deleted):
```

Меняет признак корзины, сохраняя саму запись и её историю.

Работает с таблицами calendar_events.

Непосредственные вызовы: `self.identity`, `self.connect`, `db.execute`, `db.execute('SELECT * FROM calendar_events WHERE id=?', (identity,)).fetchone`, `OrderConflict`, `self.validate`, `ValueError`, `bool`, `self.record`, `int`, `time.time`.

Явные исключения: `OrderConflict`, `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
self.record(row)
self.record(db.execute('SELECT * FROM calendar_events WHERE id=?', (identity,)).fetchone())
```

<a id="symbol-CalendarEvents.set_inactive"></a>

## CalendarEvents.set_inactive

[calendar_events.py](../../../calendar_events.py) · `function`.

```python
def set_inactive(self, payload):
```

Меняет только независимую отметку неактуальности события.

Возвращает `self._set_flag(payload, 'is_inactive')`.

Непосредственные вызовы: `self._set_flag`.

Выражения возврата (ветки читаются в исходнике):

```python
self._set_flag(payload, 'is_inactive')
```

<a id="symbol-CalendarEvents.set_trip"></a>

## CalendarEvents.set_trip

[calendar_events.py](../../../calendar_events.py) · `function`.

```python
def set_trip(self, payload):
```

Меняет только независимую отметку выезда события.

Возвращает `self._set_flag(payload, 'is_trip')`.

Непосредственные вызовы: `self._set_flag`.

Выражения возврата (ветки читаются в исходнике):

```python
self._set_flag(payload, 'is_trip')
```

<a id="symbol-CalendarEvents.validate"></a>

## CalendarEvents.validate

[calendar_events.py](../../../calendar_events.py) · `function`.

```python
def validate(row):
```

Проверяет период, реальную дату, текст и цвет свободного события.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `ValueError`, `order_calendar.block_name`, `order_calendar.validate_key`, `order_calendar.validate_text`.

Явные исключения: `ValueError`.

<a id="symbol-schema"></a>

## schema

[calendar_events.py](../../../calendar_events.py) · `function`.

```python
def schema(db):
```

Создаёт отсутствующие таблицы и совместимые расширения схемы.

Работает с таблицами calendar_events.

Непосредственные вызовы: `local_metadata.schema`, `db.execute`, `local_metadata.audit`.
