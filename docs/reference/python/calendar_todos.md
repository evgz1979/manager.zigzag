# calendar_todos.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [calendar_todos.py](../../../calendar_todos.py).

Read-only To-do digest for the same two or three weeks as the calendar PNG.

Импорты Python, включая локальные: `calendar_delivery`, `datetime`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-digest"></a>

## digest

[calendar_todos.py](../../../calendar_todos.py) · `function`.

```python
def digest(snapshot, start, through=None):
```

Собирает отмеченные события сетки и расписания поставщиков за период PNG.

Для каждого события включает актуальные задачи на его неделю и задачи без недели.

Непосредственные вызовы: `date.fromisoformat`, `timedelta`, `snapshot.get`, `order.get`, `set`, `(order.get('calendar_inactive') or {}).get`, `(order.get('calendar_completed') or {}).get`, `active_weeks.add`, `(value - timedelta(days=value.weekday())).isoformat`, `value.weekday`, `marks.get`, `entries.get`, `order_visible`, `(order.get(field) or {}).get`, `flags.append`, `events.append`, `by_path.get`, `plan.get`, `first.isoformat`, `last.isoformat`, `format(plan['amount'] / 100, ',.2f').replace(',', ' ').replace('.', ',').removesuffix`, `format(plan['amount'] / 100, ',.2f').replace(',', ' ').replace`, `format(plan['amount'] / 100, ',.2f').replace`, `format`, `sorted`, `' · '.join`, `filter`, `lines.append`, `week_group_items`, `item.get`, `order.get('todo_index', {}).get`, `sections.append`, `'\n'.join`, `'\n\n'.join`.

Выражения возврата (ветки читаются в исходнике):

```python
''
'\n\n'.join(sections)
```

<a id="symbol-message_parts"></a>

## message_parts

[calendar_todos.py](../../../calendar_todos.py) · `function`.

```python
def message_parts(text, limit=4000):
```

Делит текст Telegram по лимиту UTF-16 без потери текста и emoji.

Последовательно выдаёт элементы через yield без потери оставшегося содержимого.

Непосредственные вызовы: `ord`, `len`, `text.rfind`.

<a id="symbol-week_group_items"></a>

## week_group_items

[calendar_todos.py](../../../calendar_todos.py) · `function`.

```python
def week_group_items(order, group, week):
```

Отбирает собственные задачи на неделю события по исходным индексам карточки.

Включает задачи без недели, а для добавленных в конец строк учитывает последний видимый заголовок.

Непосредственные вызовы: `group.get`, `order.get`, `isinstance`, `set`, `type`, `len`, `enumerate`, `assignments.get`.

Выражения возврата (ветки читаются в исходнике):

```python
items
[item for (index, item) in enumerate(own_items) if assignments.get(index, trailing_week) in (None, week)]
```
