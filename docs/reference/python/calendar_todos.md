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

Включает актуальные задачи заказов и не меняет входную сводку.

Непосредственные вызовы: `date.fromisoformat`, `timedelta`, `snapshot.get`, `order.get`, `set`, `(order.get('calendar_inactive') or {}).get`, `(order.get('calendar_completed') or {}).get`, `active_weeks.add`, `(value - timedelta(days=value.weekday())).isoformat`, `value.weekday`, `marks.get`, `entries.get`, `order_visible`, `(order.get(field) or {}).get`, `flags.append`, `events.append`, `by_path.get`, `plan.get`, `first.isoformat`, `last.isoformat`, `format(plan['amount'] / 100, ',.2f').replace(',', ' ').replace('.', ',').removesuffix`, `format(plan['amount'] / 100, ',.2f').replace(',', ' ').replace`, `format(plan['amount'] / 100, ',.2f').replace`, `format`, `sorted`, `' · '.join`, `filter`, `lines.append`, `group.get`, `item.get`, `order.get('todo_index', {}).get`, `sections.append`, `'\n'.join`, `'\n\n'.join`.

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
