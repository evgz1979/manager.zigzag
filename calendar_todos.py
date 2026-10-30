"""Read-only To-do digest for the same two weeks shown in the calendar PNG."""
from datetime import date, timedelta


def digest(snapshot, start):
    first = date.fromisoformat(start)
    last = first + timedelta(days=13)
    orders = snapshot.get('orders', []) + snapshot.get('calendar_supplier_orders', [])
    by_path = {order['path']: order for order in orders}
    events = []
    for order in orders:
        marks = order.get('calendar_watch_todos') or {}
        days = order.get('calendar_events') or {}
        active_weeks = set(order.get('deadline_weeks') or [])
        for day in days:
            if day not in (order.get('calendar_inactive') or {}).get('day', []) and day not in (order.get('calendar_completed') or {}).get('day', []):
                value = date.fromisoformat(day)
                active_weeks.add((value - timedelta(days=value.weekday())).isoformat())
        for period, entries in [('day', days), ('week', order.get('calendar_week_events') or {})]:
            for day in marks.get(period, []):
                value = date.fromisoformat(day)
                week = (value - timedelta(days=value.weekday())).isoformat()
                if first <= value <= last and week in active_weeks and entries.get(day):
                    flags = [label for field, label in [('calendar_completed', 'Выполнено'), ('calendar_trip', 'Выезд'), ('calendar_inactive', 'Неактуально')]
                             if day in (order.get(field) or {}).get(period, [])]
                    if period == 'week' and week not in (order.get('deadline_weeks') or []):
                        flags.append('Отметка недели снята')
                    events.append((day, period, order, entries[day], flags))
    for plan in snapshot.get('calendar_invoice_plans', []):
        order = by_path.get(plan.get('path'))
        if plan.get('is_watch_todos') is not True or not order or not first.isoformat() <= plan['date'] <= last.isoformat():
            continue
        operation = plan.get('operation', 'invoice')
        text = {'invoice': 'Выписка счёта', 'incoming': 'Получение оплаты', 'outgoing': 'Платёж'}[operation]
        if operation != 'invoice':
            text += ' · ' + format(plan['amount'] / 100, ',.2f').replace(',', ' ').replace('.', ',').removesuffix(',00') + ' ₽'
        if plan.get('text'):
            text += ' · ' + plan['text']
        flags = [label for field, label in [('is_completed', 'Выполнено'), ('is_trip', 'Выезд'), ('is_inactive', 'Неактуально')] if plan.get(field) is True]
        events.append((plan['date'], plan.get('period', 'day'), order, text, flags))
    if not events:
        return ''
    sections = [f'☷ Смотри ту-ду · {first:%d.%m.%Y} — {last:%d.%m.%Y}']
    for day, period, order, text, flags in sorted(events, key=lambda item: (item[0], item[1] != 'week', item[2]['title'], item[2]['path'], item[3])):
        value = date.fromisoformat(day)
        when = f'Неделя {value:%d.%m} — {value + timedelta(days=6):%d.%m}' if period == 'week' else f'{value:%d.%m.%Y}'
        title = ' · '.join(filter(None, [order['work_supplier'], order['title']] if order.get('work_supplier') else [order['title'], order.get('client'), order.get('object')]))
        lines = [f'{when} · {text}', title]
        if flags:
            lines.append(' · '.join(flags))
        found = False
        for group in order.get('todo_groups', []):
            items = group.get('items')
            if items is None:
                lines += [group['label'] + ':', 'Задачи в прежнем формате — открой папку в менеджере.']
                found = True
            else:
                pending = [item['text'] for item in items if item.get('done') is False]
                if pending:
                    lines += [group['label'] + ':', *['○ ' + text for text in pending]]
                    found = True
        if not found:
            lines.append('Актуальных задач нет.')
        error = order.get('todo_index', {}).get('error')
        if error:
            lines.append('Сохранённые задачи · обновление папок: ' + error)
        sections.append('\n'.join(lines))
    return '\n\n'.join(sections)


def message_parts(text, limit=4000):
    """Keep all text; allow for Telegram's UTF-16 entity offsets and emoji."""
    while text:
        used = 0
        end = 0
        for char in text:
            size = 2 if ord(char) > 0xffff else 1
            if used + size > limit:
                break
            used += size
            end += 1
        if end < len(text):
            newline = text.rfind('\n', 0, end)
            if newline > 0:
                end = newline + 1
        yield text[:end]
        text = text[end:]
