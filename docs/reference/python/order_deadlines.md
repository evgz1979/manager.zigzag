# order_deadlines.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [order_deadlines.py](../../../order_deadlines.py).

Versioned Moscow deadline weeks; weekly comments share the order-calendar event field.

Импорты Python, включая локальные: `datetime`, `json`, `order_calendar`, `re`, `zoneinfo`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-read"></a>

## read

[order_deadlines.py](../../../order_deadlines.py) · `function`.

```python
def read(blocks):
```

Читает отсортированные уникальные понедельники сроков либо признак неизвестного блока.

Разбирает JSON; вызывающий код должен учитывать ошибки или неизвестный формат.

Непосредственные вызовы: `json.loads`, `isinstance`, `set`, `type`, `len`, `validate_week`, `sorted`.

Выражения возврата (ветки читаются в исходнике):

```python
[]
None
parsed if parsed == sorted(set(parsed)) else None
```

<a id="symbol-read_comments"></a>

## read_comments

[order_deadlines.py](../../../order_deadlines.py) · `function`.

```python
def read_comments(blocks):
```

Предоставляет совместимое имя чтения действующих недельных событий.

Возвращает `order_calendar.read(blocks, 'week')`.

Непосредственные вызовы: `order_calendar.read`.

Выражения возврата (ветки читаются в исходнике):

```python
order_calendar.read(blocks, 'week')
```

<a id="symbol-read_legacy_comments"></a>

## read_legacy_comments

[order_deadlines.py](../../../order_deadlines.py) · `function`.

```python
def read_legacy_comments(blocks):
```

Читает прежний отдельный блок недельных комментариев для совместимости.

Разбирает JSON; вызывающий код должен учитывать ошибки или неизвестный формат.

Непосредственные вызовы: `json.loads`, `isinstance`, `set`, `type`, `len`, `comments.items`, `validate_week`, `validate_comment`.

Выражения возврата (ветки читаются в исходнике):

```python
{}
None
comments
```

<a id="symbol-validate_comment"></a>

## validate_comment

[order_deadlines.py](../../../order_deadlines.py) · `function`.

```python
def validate_comment(comment):
```

Проверяет текст недельного комментария перед изменением общего события.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `len`, `any`, `ValueError`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
comment
```

<a id="symbol-validate_week"></a>

## validate_week

[order_deadlines.py](../../../order_deadlines.py) · `function`.

```python
def validate_week(value):
```

Проверяет дату понедельника, используемую как ключ срока заказа.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `isinstance`, `re.fullmatch`, `ValueError`, `date.fromisoformat`, `timedelta`, `monday.weekday`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
value
```

<a id="symbol-week_options"></a>

## week_options

[order_deadlines.py](../../../order_deadlines.py) · `function`.

```python
def week_options(now=None):
```

Строит последовательность недель относительно понедельника Москвы.

Возвращает `result`.

Непосредственные вызовы: `(now or datetime.now(MOSCOW)).astimezone(MOSCOW).date`, `(now or datetime.now(MOSCOW)).astimezone`, `datetime.now`, `timedelta`, `today.weekday`, `range`, `start.isocalendar`, `result.append`, `start.isoformat`, `end.isoformat`.

Выражения возврата (ветки читаются в исходнике):

```python
result
```

<a id="symbol-write"></a>

## write

[order_deadlines.py](../../../order_deadlines.py) · `function`.

```python
def write(blocks, week, selected):
```

Ставит или снимает одну неделю срока, сохраняя прочие блоки карточки.

При недопустимом состоянии возбуждает ValueError.

Непосредственные вызовы: `validate_week`, `type`, `ValueError`, `read`, `set`, `weeks.add`, `weeks.discard`, `len`, `json.dumps`, `sorted`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{**blocks, BLOCK: json.dumps({'version': 1, 'weeks': sorted(weeks)}, ensure_ascii=False)}
```

<a id="symbol-write_comment"></a>

## write_comment

[order_deadlines.py](../../../order_deadlines.py) · `function`.

```python
def write_comment(blocks, week, comment):
```

Сохраняет комментарий недели в общем поле недельного события.

Возвращает `order_calendar.clear_week_comment(blocks, week)`; либо `order_calendar.write(blocks, week, comment, 'week')`.

Непосредственные вызовы: `validate_week`, `order_calendar.clear_week_comment`, `order_calendar.write`.

Выражения возврата (ветки читаются в исходнике):

```python
order_calendar.clear_week_comment(blocks, week)
order_calendar.write(blocks, week, comment, 'week')
```
