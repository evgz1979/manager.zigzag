# calendar_delivery.py

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [calendar_delivery.py](../../../calendar_delivery.py).

The same calendar period and renderer for browser delivery and bot commands.

Импорты Python, включая локальные: `datetime`, `json`, `native_renderers`, `pathlib`, `subprocess`, `telegram_calendar`.

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-html"></a>

## html

[calendar_delivery.py](../../../calendar_delivery.py) · `function`.

```python
def html(snapshot, app_dir, now):
```

Собирает автономный HTML для рендера календаря общими браузерными модулями.

Формирует возвращаемое значение из проверенного локального состояния.

Непосредственные вызовы: `Path`, `period`, `json.dumps({'snapshot': snapshot, 'now': now.isoformat(), 'start': start, 'through': through}, ensure_ascii=True).replace`, `json.dumps`, `now.isoformat`, `'\n'.join`, `(app_dir / 'static' / name).read_text`, `scripts.replace`, `(app_dir / 'static/styles.css').read_text`.

Выражения возврата (ветки читаются в исходнике):

```python
f"""<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body>\n<section id="homeCalendar" class="home-calendar"><h2 id="calendarTitle"></h2>\n<button id="calendarEarlier"></button><button id="calendarToday"></button><button id="calendarLater"></button>\n<div class="calendar-weekdays"><span class="calendar-orders-heading">Заказы</span><span>На неделю</span><span>пн</span><span>вт</span><span>ср</span><span>чт</span><span>пт</span><span class="weekend">сб</span><span class="weekend">вс</span></div>\n<div id="calendarViewport" class="calendar-viewport"><div id="calenda...
```

<a id="symbol-order_visible"></a>

## order_visible

[calendar_delivery.py](../../../calendar_delivery.py) · `function`.

```python
def order_visible(order, week, now=None):
```

Проверяет наличие актуального невыполненного события в прошедшей неделе.

Возвращает `True`; либо `False`.

Непосредственные вызовы: `order.get`, `current_week(now).isoformat`, `current_week`, `(date.fromisoformat(week) + timedelta(days=7)).isoformat`, `date.fromisoformat`, `timedelta`, `(entries or {}).items`, `text.strip`, `(order.get('calendar_completed') or {}).get`, `(order.get('calendar_inactive') or {}).get`.

Выражения возврата (ветки читаются в исходнике):

```python
True
False
```

<a id="symbol-period"></a>

## period

[calendar_delivery.py](../../../calendar_delivery.py) · `function`.

```python
def period(snapshot, now=None):
```

Выбирает две или три недели снимка независимо от просмотра истории в браузере.

Предыдущую неделю удерживают только видимые актуальные невыполненные события сетки.

Непосредственные вызовы: `current_week`, `(current - timedelta(days=7)).isoformat`, `timedelta`, `current.isoformat`, `snapshot.get`, `order.get`, `any`, `(order.get('calendar_completed') or {}).get`, `(order.get('calendar_inactive') or {}).get`, `order_visible`, `(current + timedelta(days=13)).isoformat`, `item.get`.

Выражения возврата (ветки читаются в исходнике):

```python
(previous, (current + timedelta(days=13)).isoformat())
(previous if has_previous else current_key, (current + timedelta(days=13)).isoformat())
```

<a id="symbol-render"></a>

## render

[calendar_delivery.py](../../../calendar_delivery.py) · `function`.

```python
def render(snapshot, app_dir, data_dir, now):
```

Рендерит один общий PNG календаря в отдельном процессе WebKit.

Запускает внешний процесс; параметры и ограничения заданы в теле функции.

Непосредственные вызовы: `subprocess.run`, `str`, `renderer`, `html(snapshot, app_dir, now).encode`, `html`, `validate_image`, `TelegramError`.

Явные исключения: `TelegramError`.

Выражения возврата (ветки читаются в исходнике):

```python
result.stdout
```

<a id="symbol-renderer"></a>

## renderer

[calendar_delivery.py](../../../calendar_delivery.py) · `function`.

```python
def renderer(app_dir, data_dir):
```

Получает собранный Swift-помощник для текущего исходника.

Возвращает `native_renderers.build(Path(app_dir) / 'calendar_renderer.swift', data_dir, 'calendar-renderer', 90)`.

Непосредственные вызовы: `native_renderers.build`, `Path`.

Выражения возврата (ветки читаются в исходнике):

```python
native_renderers.build(Path(app_dir) / 'calendar_renderer.swift', data_dir, 'calendar-renderer', 90)
```
