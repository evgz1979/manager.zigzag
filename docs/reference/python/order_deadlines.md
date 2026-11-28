# order_deadlines.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [order_deadlines.py](../../../order_deadlines.py).

Versioned Moscow deadline weeks; weekly comments share the order-calendar event field.

Импорты Python, включая локальные: `datetime`, `json`, `local_metadata`, `order_calendar`, `re`, `time`, `uuid`, `zoneinfo`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-WeekHighlightConflict"></a>

## WeekHighlightConflict

[order_deadlines.py](../../../order_deadlines.py) · `class`.

```python
class WeekHighlightConflict(ValueError):
```

Обозначает устаревшую версию общей настройки полосы.

HTTP-обработчик возвращает 409, запись остаётся прежней.

<a id="symbol-highlight_settings"></a>

## highlight_settings

[order_deadlines.py](../../../order_deadlines.py) · `function`.

```python
def highlight_settings(store, payload=None):
```

Читает или сохраняет общие отмеченные недели по ожидаемой версии.

Полный набор, в том числе пустой, и история сохраняются одной транзакцией.

Непосредственные вызовы: `store.connect`, `read_highlights`, `payload.get`, `type`, `ValueError`, `validate_highlights`, `db.execute`, `WeekHighlightConflict`, `schema`, `audit`, `json.dumps`, `str`, `uuid.uuid4`, `time.time`.

Явные исключения: `ValueError`, `WeekHighlightConflict`.

Выражения возврата (ветки читаются в исходнике):

```python
read_highlights(db)
current
{'revision': revision + 1, 'weeks': weeks}
```

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

<a id="symbol-read_highlights"></a>

## read_highlights

[order_deadlines.py](../../../order_deadlines.py) · `function`.

```python
def read_highlights(db):
```

Читает общую настройку полосы из SQLite без доступа к папкам заказов.

Отсутствующая запись даёт прежние семь недель, неизвестный формат даёт weeks=null.

Непосредственные вызовы: `db.execute("SELECT 1 FROM sqlite_master WHERE name='metadata_records'").fetchone`, `db.execute`, `list`, `db.execute("SELECT data,revision FROM metadata_records WHERE kind=? AND path=''", (HIGHLIGHT_KIND,)).fetchone`, `json.loads`, `isinstance`, `set`, `type`, `validate_highlights`.

Выражения возврата (ветки читаются в исходнике):

```python
{'revision': 0, 'weeks': list(DEFAULT_HIGHLIGHTS)}
{'revision': row['revision'], 'weeks': weeks}
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

<a id="symbol-read_todo_week_layout"></a>

## read_todo_week_layout

[order_deadlines.py](../../../order_deadlines.py) · `function`.

```python
def read_todo_week_layout(blocks):
```

Читает сохранённый порядок строк независимо от комментариев и отметок сроков.

Отсутствующий блок даёт пустой список, неизвестный формат — None.

Непосредственные вызовы: `json.loads`, `isinstance`, `set`, `type`, `validate_todo_week_layout`.

Выражения возврата (ветки читаются в исходнике):

```python
[]
data['rows']
None
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

<a id="symbol-validate_highlights"></a>

## validate_highlights

[order_deadlines.py](../../../order_deadlines.py) · `function`.

```python
def validate_highlights(weeks):
```

Проверяет набор недель жёлтой полосы и возвращает отсортированные понедельники.

Повтор, несуществующая дата или слишком длинный список вызывают ValueError.

Непосредственные вызовы: `isinstance`, `len`, `ValueError`, `sorted`, `validate_week`, `set`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
parsed
```

<a id="symbol-validate_todo_week_layout"></a>

## validate_todo_week_layout

[order_deadlines.py](../../../order_deadlines.py) · `function`.

```python
def validate_todo_week_layout(rows):
```

Проверяет последовательность заголовков и индексов задач в карточке.

Понедельники уникальны, null отмечает «Без недели», индексы идут подряд от нуля.

Непосредственные вызовы: `isinstance`, `len`, `ValueError`, `set`, `type`, `validate_week`, `seen.add`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
index
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

<a id="symbol-write_todo_week_layout"></a>

## write_todo_week_layout

[order_deadlines.py](../../../order_deadlines.py) · `function`.

```python
def write_todo_week_layout(blocks, rows, task_count):
```

Сохраняет порядок вместе со списком задач, не меняя сроки и события календаря.

Проверяет охват всех задач и не заменяет неизвестный формат.

Непосредственные вызовы: `read_todo_week_layout`, `ValueError`, `validate_todo_week_layout`, `any`, `isinstance`, `blocks.items`, `json.dumps`.

Явные исключения: `ValueError`.

Выражения возврата (ветки читаются в исходнике):

```python
{key: value for (key, value) in blocks.items() if key != TODO_LAYOUT_BLOCK}
{**blocks, TODO_LAYOUT_BLOCK: json.dumps({'version': 1, 'rows': rows})}
```
