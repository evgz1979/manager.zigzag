"""The same calendar period and renderer for browser delivery and bot commands."""
from datetime import date, timedelta
import json
from pathlib import Path
import subprocess

import native_renderers
from telegram_calendar import current_week, validate_image, TelegramError


def order_visible(order, week, now=None):
    """Past grid rows need an active unfinished event. Unknown text stays visible."""
    if order.get('calendar_compact') is True or week >= current_week(now).isoformat():
        return True
    end = (date.fromisoformat(week) + timedelta(days=7)).isoformat()
    for period, field in [('week', 'calendar_week_events'), ('day', 'calendar_events')]:
        entries = order.get(field)
        if field in order and entries is None:
            return True
        for key, text in (entries or {}).items():
            if (key == week if period == 'week' else week <= key < end) and text.strip():
                if (key not in (order.get('calendar_completed') or {}).get(period, [])
                        and key not in (order.get('calendar_inactive') or {}).get(period, [])):
                    return True
    return False


def period(snapshot, now=None):
    current = current_week(now)
    previous = (current - timedelta(days=7)).isoformat()
    current_key = current.isoformat()
    orders = snapshot.get('orders', []) + snapshot.get('calendar_supplier_orders', [])
    for order in orders:
        if not order.get('path') or order.get('registered') is False:
            continue
        eligible = previous in (order.get('deadline_weeks') or [])
        if order.get('calendar_compact') is not True:
            eligible |= any(previous <= key < current_key
                            and key not in (order.get('calendar_completed') or {}).get('day', [])
                            and key not in (order.get('calendar_inactive') or {}).get('day', [])
                            for key in (order.get('calendar_events') or {}))
        if eligible and order_visible(order, previous, now):
            return previous, (current + timedelta(days=13)).isoformat()
    records = snapshot.get('calendar_events', []) + snapshot.get('calendar_invoice_plans', [])
    has_previous = any(not item.get('deleted') and previous <= item['date'] < current_key for item in records)
    return (previous if has_previous else current_key), (current + timedelta(days=13)).isoformat()


def renderer(app_dir, data_dir):
    return native_renderers.build(Path(app_dir) / 'calendar_renderer.swift', data_dir, 'calendar-renderer', 90)


def html(snapshot, app_dir, now):
    app_dir = Path(app_dir)
    start, through = period(snapshot, now)
    payload = json.dumps({'snapshot': snapshot, 'now': now.isoformat(), 'start': start, 'through': through}, ensure_ascii=True).replace('<', '\\u003c')
    scripts = '\n'.join((app_dir / 'static' / name).read_text() for name in
                        ['vendor/html2canvas/html2canvas.min.js', 'order-sorting.js', 'home-calendar.js', 'calendar-snapshot.js'])
    scripts = scripts.replace('</script', '<\\/script')
    css = (app_dir / 'static/styles.css').read_text()
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body>
<section id="homeCalendar" class="home-calendar"><h2 id="calendarTitle"></h2>
<button id="calendarEarlier"></button><button id="calendarToday"></button><button id="calendarLater"></button>
<div class="calendar-weekdays"><span class="calendar-orders-heading">Заказы</span><span>На неделю</span><span>пн</span><span>вт</span><span>ср</span><span>чт</span><span>пт</span><span class="weekend">сб</span><span class="weekend">вс</span></div>
<div id="calendarViewport" class="calendar-viewport"><div id="calendarWeeks" class="calendar-weeks"></div></div></section>
<script>{scripts}</script><script>
const delivery = {payload};
async function makeCalendar() {{
  try {{
    const data = delivery.snapshot;
    const orders = [...data.orders, ...(data.calendar_supplier_orders || [])].map(order => order.work_supplier ? {{ ...order, client: order.work_supplier }} : order).sort((a,b) => OrderSorting.compare(a,b,'title',1));
    HomeCalendar.show(orders, data.calendar_events || [], data.calendar_invoice_plans || [], new Date(delivery.now));
    const result = await CalendarSnapshot.capture(new Date(delivery.now));
    if (result.start !== delivery.start || result.through !== delivery.through) throw new Error('period');
    const image = await new Promise((resolve,reject) => {{ const reader = new FileReader(); reader.onload = () => resolve(reader.result.split(',')[1]); reader.onerror = reject; reader.readAsDataURL(result.image); }});
    window.webkit.messageHandlers.calendar.postMessage({{image}});
  }} catch (_) {{ window.webkit.messageHandlers.calendar.postMessage({{error:true}}); }}
}}
</script></body></html>'''


def render(snapshot, app_dir, data_dir, now):
    try:
        result = subprocess.run([str(renderer(app_dir, data_dir))], input=html(snapshot, app_dir, now).encode(),
                                capture_output=True, timeout=75, check=True)
        validate_image(result.stdout)
        return result.stdout
    except (OSError, subprocess.SubprocessError, ValueError):
        raise TelegramError('Не удалось создать календарь на M4. Повтори /calendar позже') from None
