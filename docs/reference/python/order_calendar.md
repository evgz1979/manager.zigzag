# order_calendar.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [order_calendar.py](../../../order_calendar.py).

Per-order calendar entries, independent of weekly deadline marks.

Импорты Python, включая локальные: `calendar_layout`, `datetime`, `json`, `local_metadata`, `order_deadlines`, `re`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-_read"></a>

## _read

[order_calendar.py](../../../order_calendar.py) · `function`.

```python
def _read(blocks, period='day'):
```

Разбирает строгий JSON-блок календарных текстов выбранного периода.

Разбирает JSON; вызывающий код должен учитывать ошибки или неизвестный формат.

Непосредственные вызовы: `block_name`, `json.loads`, `isinstance`, `set`, `type`, `len`, `events.items`, `validate_key`, `validate_text`.

Выражения возврата (ветки читаются в исходнике):

```python
{}
None
events
```

<a id="symbol-_read_flags"></a>

## _read_flags

[order_calendar.py](../../../order_calendar.py) · `function`.

```python
def _read_flags(blocks, block):
```

Разбирает строгие массивы независимых отметок календаря.

Разбирает JSON; вызывающий код должен учитывать ошибки или неизвестный формат.

Непосредственные вызовы: `json.loads`, `isinstance`, `set`, `type`, `len`, `validate_key`, `sorted`.

Выражения возврата (ветки читаются в исходнике):

```python
{'day': [], 'week': []}
None
{period: value[period] for period in ('day', 'week')}
```

<a id="symbol-_remove_entry"></a>

## _remove_entry

[order_calendar.py](../../../order_calendar.py) · `function`.

```python
def _remove_entry(blocks, day, period, *, missing_ok=False):
```

Удаляет выбранную запись из известного блока без замены остальных.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `validate_key`, `read`, `read_inactive`, `read_colors`, `read_completed`, `read_trip`, `read_watch_todos`, `ValueError`, `events.items`, `block_name`, `json.dumps`, `_write_colors`, `colors[period].items`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
result
```

<a id="symbol-_write_colors"></a>

## _write_colors

[order_calendar.py](../../../order_calendar.py) · `function`.

```python
def _write_colors(blocks, colors, period, entries):
```

Читает или сериализует строгий блок индивидуальных цветов событий.

Возвращает `{**blocks, COLORS_BLOCK: json.dumps({'version': 1, **colors, period: entries}, ensure_ascii=False)}`.

Непосредственные вызовы: `json.dumps`.

Выражения возврата (ветки читаются в исходнике):

```python
{**blocks, COLORS_BLOCK: json.dumps({'version': 1, **colors, period: entries}, ensure_ascii=False)}
```

<a id="symbol-block_name"></a>

## block_name

[order_calendar.py](../../../order_calendar.py) · `function`.

```python
def block_name(period):
```

Выбирает имя блока карточки для дневных или недельных событий.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `ValueError`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
WEEK_BLOCK if period == 'week' else BLOCK
```

<a id="symbol-clear_week_comment"></a>

## clear_week_comment

[order_calendar.py](../../../order_calendar.py) · `function`.

```python
def clear_week_comment(blocks, week):
```

Явно очищает общее недельное событие при сохранении пустого комментария.

Возвращает `_remove_entry(unify_weekly_blocks(blocks), week, 'week', missing_ok=True)`.

Непосредственные вызовы: `_remove_entry`, `unify_weekly_blocks`.

Выражения возврата (ветки читаются в исходнике):

```python
_remove_entry(unify_weekly_blocks(blocks), week, 'week', missing_ok=True)
```

<a id="symbol-mark_completion_contract"></a>

## mark_completion_contract

[order_calendar.py](../../../order_calendar.py) · `function`.

```python
def mark_completion_contract(db):
```

Записывает использование версионного контракта выполнения календаря.

Работает с таблицами metadata_settings.

Непосредственные вызовы: `local_metadata.schema`, `db.execute`.

<a id="symbol-mark_flag_contract"></a>

## mark_flag_contract

[order_calendar.py](../../../order_calendar.py) · `function`.

```python
def mark_flag_contract(db, field):
```

Обрабатывает общий контракт независимой отметки календаря.

Передаёт работу `{'is_completed': mark_completion_contract, 'is_inactive': mark_relevance_contract, 'is_trip': mark_trip_contract, 'is_watch_todos': mark_watch_todos_contract, 'is_carryover': calendar_layout.mark_contract}[field]`.

Непосредственные вызовы: `{'is_completed': mark_completion_contract, 'is_inactive': mark_relevance_contract, 'is_trip': mark_trip_contract, 'is_watch_todos': mark_watch_todos_contract, 'is_carryover': calendar_layout.mark_contract}[field]`.

<a id="symbol-mark_relevance_contract"></a>

## mark_relevance_contract

[order_calendar.py](../../../order_calendar.py) · `function`.

```python
def mark_relevance_contract(db):
```

Записывает использование версионного контракта актуальности календаря.

Работает с таблицами metadata_settings.

Непосредственные вызовы: `local_metadata.schema`, `db.execute`.

<a id="symbol-mark_trip_contract"></a>

## mark_trip_contract

[order_calendar.py](../../../order_calendar.py) · `function`.

```python
def mark_trip_contract(db):
```

Записывает использование версионного контракта выездов календаря.

Работает с таблицами metadata_settings.

Непосредственные вызовы: `local_metadata.schema`, `db.execute`.

<a id="symbol-mark_watch_todos_contract"></a>

## mark_watch_todos_contract

[order_calendar.py](../../../order_calendar.py) · `function`.

```python
def mark_watch_todos_contract(db):
```

Записывает использование контракта показа задач календаря.

Работает с таблицами metadata_settings.

Непосредственные вызовы: `local_metadata.schema`, `db.execute`.

<a id="symbol-move"></a>

## move

[order_calendar.py](../../../order_calendar.py) · `function`.

```python
def move(blocks, day, days, period='day'):
```

Переносит объект или событие с проверкой исходного и целевого состояния.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `block_name`, `unify_weekly_blocks`, `validate_key`, `type`, `ValueError`, `read`, `date.fromisoformat`, `timedelta`, `target_date.isoformat`, `read_inactive`, `read_colors`, `read_completed`, `read_trip`, `read_watch_todos`, `moved.pop`, `json.dumps`, `set`, `selected.remove`, `selected.add`, `sorted`, `entries.pop`, `_write_colors`, `source_date.weekday`, `target_date.weekday`, `order_deadlines.write`, `target_week.isoformat`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
result
```

<a id="symbol-normalize_weekly_blocks"></a>

## normalize_weekly_blocks

[order_calendar.py](../../../order_calendar.py) · `function`.

```python
def normalize_weekly_blocks(blocks):
```

Нормализует известные недельные блоки при первоначальном импорте.

Возвращает `unify_weekly_blocks(blocks)`; либо `blocks`.

Непосредственные вызовы: `unify_weekly_blocks`.

Выражения возврата (ветки читаются в исходнике):

```python
unify_weekly_blocks(blocks)
blocks
```

<a id="symbol-read"></a>

## read

[order_calendar.py](../../../order_calendar.py) · `function`.

```python
def read(blocks, period='day'):
```

Читает дневные или недельные события из дополнительных блоков заказа.

Возвращает `None`; либо `_read(blocks, period)`.

Непосредственные вызовы: `unify_weekly_blocks`, `_read`.

Выражения возврата (ветки читаются в исходнике):

```python
None
_read(blocks, period)
```

<a id="symbol-read_colors"></a>

## read_colors

[order_calendar.py](../../../order_calendar.py) · `function`.

```python
def read_colors(blocks):
```

Читает или сериализует строгий блок индивидуальных цветов событий.

Разбирает JSON; вызывающий код должен учитывать ошибки или неизвестный формат.

Непосредственные вызовы: `json.loads`, `isinstance`, `set`, `type`, `len`, `entries.items`, `validate_key`.

Выражения возврата (ветки читаются в исходнике):

```python
{'day': {}, 'week': {}}
None
{period: value[period] for period in ('day', 'week')}
```

<a id="symbol-read_completed"></a>

## read_completed

[order_calendar.py](../../../order_calendar.py) · `function`.

```python
def read_completed(blocks):
```

Читает независимые отметки выполнения дневных и недельных событий.

Возвращает `_read_flags(blocks, COMPLETED_BLOCK)`.

Непосредственные вызовы: `_read_flags`.

Выражения возврата (ветки читаются в исходнике):

```python
_read_flags(blocks, COMPLETED_BLOCK)
```

<a id="symbol-read_inactive"></a>

## read_inactive

[order_calendar.py](../../../order_calendar.py) · `function`.

```python
def read_inactive(blocks):
```

Читает независимые отметки неактуальности дневных и недельных событий.

Возвращает `_read_flags(blocks, INACTIVE_BLOCK)`.

Непосредственные вызовы: `_read_flags`.

Выражения возврата (ветки читаются в исходнике):

```python
_read_flags(blocks, INACTIVE_BLOCK)
```

<a id="symbol-read_trip"></a>

## read_trip

[order_calendar.py](../../../order_calendar.py) · `function`.

```python
def read_trip(blocks):
```

Читает независимые отметки выездов дневных и недельных событий.

Возвращает `_read_flags(blocks, TRIP_BLOCK)`.

Непосредственные вызовы: `_read_flags`.

Выражения возврата (ветки читаются в исходнике):

```python
_read_flags(blocks, TRIP_BLOCK)
```

<a id="symbol-read_watch_todos"></a>

## read_watch_todos

[order_calendar.py](../../../order_calendar.py) · `function`.

```python
def read_watch_todos(blocks):
```

Читает независимые отметки показа задач у событий заказа.

Возвращает `_read_flags(blocks, WATCH_TODOS_BLOCK)`.

Непосредственные вызовы: `_read_flags`.

Выражения возврата (ветки читаются в исходнике):

```python
_read_flags(blocks, WATCH_TODOS_BLOCK)
```

<a id="symbol-remove"></a>

## remove

[order_calendar.py](../../../order_calendar.py) · `function`.

```python
def remove(blocks, day, period='day'):
```

Удаляет дневное событие и соответствующие независимые отметки.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `ValueError`, `_remove_entry`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
_remove_entry(blocks, day, period)
```

<a id="symbol-restore"></a>

## restore

[order_calendar.py](../../../order_calendar.py) · `function`.

```python
def restore(blocks, day, text, inactive, period='day', color=None, completed=False, trip=False, watch_todos=False):
```

Возвращает удалённый текст вместе с его отметками, не занимая чужую дату.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `ValueError`, `validate_key`, `validate_text`, `type`, `read`, `read_inactive`, `read_colors`, `read_completed`, `read_trip`, `read_watch_todos`, `set_inactive`, `write`, `set_completed`, `set_trip`, `set_watch_todos`, `set_color`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
set_color(result, day, color) if color is not None else result
```

<a id="symbol-set_color"></a>

## set_color

[order_calendar.py](../../../order_calendar.py) · `function`.

```python
def set_color(blocks, day, color, period='day'):
```

Меняет выбранный цвет события, сохраняя остальные признаки.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `block_name`, `validate_key`, `isinstance`, `ValueError`, `read_colors`, `read`, `len`, `_write_colors`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
_write_colors(blocks, colors, period, entries)
```

<a id="symbol-set_completed"></a>

## set_completed

[order_calendar.py](../../../order_calendar.py) · `function`.

```python
def set_completed(blocks, day, completed, period='day'):
```

Меняет только независимую отметку выполнения события.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `block_name`, `unify_weekly_blocks`, `validate_key`, `type`, `ValueError`, `read_completed`, `read`, `set`, `selected.add`, `selected.discard`, `len`, `json.dumps`, `sorted`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{**blocks, COMPLETED_BLOCK: json.dumps({'version': 1, **flags, period: sorted(selected)}, ensure_ascii=False)}
```

<a id="symbol-set_inactive"></a>

## set_inactive

[order_calendar.py](../../../order_calendar.py) · `function`.

```python
def set_inactive(blocks, day, inactive, period='day'):
```

Меняет только независимую отметку неактуальности события.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `block_name`, `unify_weekly_blocks`, `validate_key`, `type`, `ValueError`, `read_inactive`, `read`, `set`, `selected.add`, `selected.discard`, `len`, `sorted`, `json.dumps`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{**blocks, INACTIVE_BLOCK: json.dumps({'version': 1, **flags}, ensure_ascii=False)}
```

<a id="symbol-set_trip"></a>

## set_trip

[order_calendar.py](../../../order_calendar.py) · `function`.

```python
def set_trip(blocks, day, trip, period='day'):
```

Меняет только независимую отметку выезда события.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `block_name`, `unify_weekly_blocks`, `validate_key`, `type`, `ValueError`, `read_trip`, `read`, `set`, `selected.add`, `selected.discard`, `len`, `json.dumps`, `sorted`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{**blocks, TRIP_BLOCK: json.dumps({'version': 1, **flags, period: sorted(selected)}, ensure_ascii=False)}
```

<a id="symbol-set_watch_todos"></a>

## set_watch_todos

[order_calendar.py](../../../order_calendar.py) · `function`.

```python
def set_watch_todos(blocks, day, marked, period='day'):
```

Меняет только отметку показа задач у события заказа.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `block_name`, `unify_weekly_blocks`, `validate_key`, `type`, `ValueError`, `read_watch_todos`, `read`, `set`, `selected.add`, `selected.discard`, `len`, `json.dumps`, `sorted`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{**blocks, WATCH_TODOS_BLOCK: json.dumps({'version': 1, **flags, period: sorted(selected)}, ensure_ascii=False)}
```

<a id="symbol-unify_weekly_blocks"></a>

## unify_weekly_blocks

[order_calendar.py](../../../order_calendar.py) · `function`.

```python
def unify_weekly_blocks(blocks):
```

Объединяет известные прежние недельные записи без подмены разных текстов.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `order_deadlines.read_legacy_comments`, `_read`, `ValueError`, `dict`, `old.items`, `text.strip`, `len`, `json.dumps`, `result.pop`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
blocks
result
```

<a id="symbol-validate_date"></a>

## validate_date

[order_calendar.py](../../../order_calendar.py) · `function`.

```python
def validate_date(value):
```

Проверяет реальную календарную дату и канонический формат ключа.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `re.fullmatch`, `ValueError`, `date.fromisoformat`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
value
```

<a id="symbol-validate_key"></a>

## validate_key

[order_calendar.py](../../../order_calendar.py) · `function`.

```python
def validate_key(value, period):
```

Проверяет ключ события с учётом выбранного периода.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `validate_date`, `date.fromisoformat(value).weekday`, `date.fromisoformat`, `ValueError`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
value
```

<a id="symbol-validate_text"></a>

## validate_text

[order_calendar.py](../../../order_calendar.py) · `function`.

```python
def validate_text(value):
```

Проверяет длину и допустимость текста события.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `len`, `any`, `ValueError`, `value.strip`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
value
```

<a id="symbol-write"></a>

## write

[order_calendar.py](../../../order_calendar.py) · `function`.

```python
def write(blocks, day, text, period='day'):
```

Меняет текст одной календарной даты без замены других событий и отметок.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `block_name`, `unify_weekly_blocks`, `validate_key`, `validate_text`, `read`, `ValueError`, `set_inactive`, `len`, `json.dumps`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
set_inactive(blocks, day, True, period)
{**blocks, block: json.dumps({'version': 1, 'events': events}, ensure_ascii=False)}
```
