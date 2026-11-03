# calendar_todos.py

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [calendar_todos.py:1](../../../calendar_todos.py#L1).

Read-only To-do digest for the same two or three weeks as the calendar PNG.

Импорты Python, включая локальные: `calendar_delivery`, `datetime`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## digest

[calendar_todos.py:8](../../../calendar_todos.py#L8) · `function`.

```python
def digest(snapshot, start, through=None):
```

Собирает тексты только видимых отмеченных событий и актуальных задач их заказов.

Возвращает `''`; либо `'\n\n'.join(sections)`.

Непосредственные вызовы: `date.fromisoformat`, `timedelta`, `snapshot.get`, `order.get`, `set`, `(order.get('calendar_inactive') or {}).get`, `(order.get('calendar_completed') or {}).get`, `active_weeks.add`, `(value - timedelta(days=value.weekday())).isoformat`, `value.weekday`, `marks.get`, `entries.get`, `order_visible`, `(order.get(field) or {}).get`, `flags.append`, `events.append`, `by_path.get`, `plan.get`, `first.isoformat`, `last.isoformat`, `format(plan['amount'] / 100, ',.2f').replace(',', ' ').replace('.', ',').removesuffix`, `format(plan['amount'] / 100, ',.2f').replace(',', ' ').replace`, `format(plan['amount'] / 100, ',.2f').replace`, `format`, `sorted`, `' · '.join`, `filter`, `lines.append`, `group.get`, `item.get`, `order.get('todo_index', {}).get`, `sections.append`, `'\n'.join`, `'\n\n'.join`.

Выражения возврата (ветки читаются в исходнике):

```python
''
'\n\n'.join(sections)
```

## message_parts

[calendar_todos.py:78](../../../calendar_todos.py#L78) · `function`.

```python
def message_parts(text, limit=4000):
```

Делит текст Telegram по лимиту UTF-16 без потери текста и emoji.

Последовательно выдаёт элементы через yield без потери оставшегося содержимого.

Непосредственные вызовы: `ord`, `len`, `text.rfind`.
