"""Per-order calendar entries, independent of weekly deadline marks."""
import json
import re
from datetime import date, timedelta

import order_deadlines

BLOCK = "События календаря"
WEEK_BLOCK = "События календаря на неделю"
MAX_EVENTS = 5200
WEEKLY_EVENTS_UNIFIED_VERSION = 1
CALENDAR_RELEVANCE_VERSION = 1
INACTIVE_BLOCK = "Неактуальные события календаря"
ORDER_CALENDAR_COLORS_VERSION = 1
COLORS_BLOCK = "Цвета событий календаря"
COLORS = {"gray", "red", "orange", "yellow", "green", "blue", "purple"}


def block_name(period):
    if period not in ("day", "week"):
        raise ValueError("Некорректный период события")
    return WEEK_BLOCK if period == "week" else BLOCK


def validate_key(value, period):
    value = validate_date(value)
    if period == "week" and date.fromisoformat(value).weekday() != 0:
        raise ValueError("Событие на неделю должно быть привязано к дате понедельника")
    return value


def validate_date(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("Укажи дату события в формате ГГГГ-ММ-ДД")
    try:
        date.fromisoformat(value)
    except ValueError:
        raise ValueError("Некорректная дата события") from None
    return value


def validate_text(value):
    if not isinstance(value, str) or len(value) > 1000 or any(char in value for char in "\r\n\0"):
        raise ValueError("Событие — одна строка до 1000 символов")
    if value and not value.strip():
        raise ValueError("Введи название события")
    return value


def _read(blocks, period="day"):
    block = block_name(period)
    if block not in blocks:
        return {}
    try:
        value = json.loads(blocks[block])
        if not isinstance(value, dict) or set(value) != {"version", "events"} or type(value["version"]) is not int or value["version"] != 1:
            return None
        events = value["events"]
        if not isinstance(events, dict) or len(events) > MAX_EVENTS:
            return None
        for day, text in events.items():
            validate_key(day, period)
            if not validate_text(text):
                return None
        return events
    except (ValueError, TypeError):
        return None


def unify_weekly_blocks(blocks):
    """Convert known legacy comments without overwriting different texts."""
    if order_deadlines.COMMENTS_BLOCK not in blocks:
        return blocks
    old = order_deadlines.read_legacy_comments(blocks)
    events = _read(blocks, "week")
    if old is None or events is None:
        raise ValueError("Недельные события или прежние комментарии имеют неизвестный формат. Данные оставлены без изменений")
    merged = dict(events)
    for week, text in old.items():
        if not text.strip():
            continue
        if week in merged and merged[week] != text:
            raise ValueError("На неделю " + week + " сохранены разные тексты комментария и события. Оба оставлены без изменений")
        merged[week] = text
    if len(merged) > MAX_EVENTS:
        raise ValueError("Сохранено слишком много недельных событий")
    result = {**blocks, WEEK_BLOCK: json.dumps({"version": 1, "events": merged}, ensure_ascii=False)}
    result.pop(order_deadlines.COMMENTS_BLOCK)
    return result


def normalize_weekly_blocks(blocks):
    """New imports convert known data; unknown legacy blocks remain intact."""
    try:
        return unify_weekly_blocks(blocks)
    except ValueError:
        return blocks


def read(blocks, period="day"):
    if period == "week":
        try:
            blocks = unify_weekly_blocks(blocks)
        except ValueError:
            return None
    return _read(blocks, period)


def read_inactive(blocks):
    if INACTIVE_BLOCK not in blocks:
        return {"day": [], "week": []}
    try:
        value = json.loads(blocks[INACTIVE_BLOCK])
        if not isinstance(value, dict) or set(value) != {"version", "day", "week"} or type(value["version"]) is not int or value["version"] != 1:
            return None
        for period in ("day", "week"):
            days = value[period]
            if not isinstance(days, list) or len(days) > MAX_EVENTS or [validate_key(day, period) for day in days] != sorted(set(days)):
                return None
        return {period: value[period] for period in ("day", "week")}
    except (ValueError, TypeError):
        return None


def read_colors(blocks):
    if COLORS_BLOCK not in blocks:
        return {"day": {}, "week": {}}
    try:
        value = json.loads(blocks[COLORS_BLOCK])
        if not isinstance(value, dict) or set(value) != {"version", "day", "week"} or type(value["version"]) is not int or value["version"] != 1:
            return None
        for period in ("day", "week"):
            entries = value[period]
            if not isinstance(entries, dict) or len(entries) > MAX_EVENTS:
                return None
            for day, color in entries.items():
                validate_key(day, period)
                if not isinstance(color, str) or color not in COLORS:
                    return None
        return {period: value[period] for period in ("day", "week")}
    except (ValueError, TypeError):
        return None


def _write_colors(blocks, colors, period, entries):
    return {**blocks, COLORS_BLOCK: json.dumps({"version": 1, **colors, period: entries}, ensure_ascii=False)}


def set_color(blocks, day, color, period="day"):
    block_name(period)
    day = validate_key(day, period)
    if not isinstance(color, str) or color not in COLORS:
        raise ValueError("Выбери цвет события")
    colors, events = read_colors(blocks), read(blocks, period)
    if colors is None or events is None:
        raise ValueError("Формат события или цветов неизвестен. Данные сохранены без изменений")
    if day not in events:
        raise ValueError("Событие на этой дате отсутствует. Обнови календарь")
    entries = {**colors[period], day: color}
    if len(entries) > MAX_EVENTS:
        raise ValueError("Сохранено слишком много цветов событий")
    return _write_colors(blocks, colors, period, entries)


def mark_relevance_contract(db):
    import local_metadata
    local_metadata.schema(db)
    db.execute("INSERT INTO metadata_settings VALUES ('calendar_event_relevance','1') ON CONFLICT(key) DO UPDATE SET value=excluded.value")


def set_inactive(blocks, day, inactive, period="day"):
    block_name(period)
    if period == "week":
        blocks = unify_weekly_blocks(blocks)
    day = validate_key(day, period)
    if type(inactive) is not bool:
        raise ValueError("Укажи состояние актуальности события")
    flags, events = read_inactive(blocks), read(blocks, period)
    if flags is None or events is None:
        raise ValueError("Формат события или актуальности неизвестен. Данные сохранены без изменений")
    if day not in events:
        raise ValueError("Событие на этой дате отсутствует. Обнови календарь")
    selected = set(flags[period])
    if inactive:
        selected.add(day)
    else:
        selected.discard(day)
    if len(selected) > MAX_EVENTS:
        raise ValueError("Сохранено слишком много отметок актуальности")
    flags = {**flags, period: sorted(selected)}
    return {**blocks, INACTIVE_BLOCK: json.dumps({"version": 1, **flags}, ensure_ascii=False)}


def write(blocks, day, text, period="day"):
    block = block_name(period)
    if period == "week":
        blocks = unify_weekly_blocks(blocks)
    day, text = validate_key(day, period), validate_text(text)
    events = read(blocks, period)
    if events is None:
        raise ValueError("События календаря имеют неизвестный формат и оставлены без изменений")
    events = {**events}
    if text:
        events[day] = text
    elif day in events:
        return set_inactive(blocks, day, True, period)
    if len(events) > MAX_EVENTS:
        raise ValueError("Сохранено слишком много событий календаря")
    return {**blocks, block: json.dumps({"version": 1, "events": events}, ensure_ascii=False)}


def remove(blocks, day, period="day"):
    if period != 'day':
        raise ValueError('Удалять можно только события на день')
    return _remove_entry(blocks, day, period)


def clear_week_comment(blocks, week):
    """An empty card comment explicitly clears the shared weekly event."""
    return _remove_entry(unify_weekly_blocks(blocks), week, 'week', missing_ok=True)


def _remove_entry(blocks, day, period, *, missing_ok=False):
    day = validate_key(day, period)
    events, flags, colors = read(blocks, period), read_inactive(blocks), read_colors(blocks)
    if events is None or flags is None or colors is None:
        raise ValueError('Формат события, актуальности или цветов неизвестен. Данные сохранены без изменений')
    if day not in events and not missing_ok:
        raise ValueError('Событие на этой дате уже отсутствует. Обнови календарь')
    remaining = {key: value for key, value in events.items() if key != day}
    result = {**blocks, block_name(period): json.dumps({'version': 1, 'events': remaining}, ensure_ascii=False)}
    if day in flags[period]:
        result[INACTIVE_BLOCK] = json.dumps({'version': 1, **flags, period: [key for key in flags[period] if key != day]}, ensure_ascii=False)
    if day in colors[period]:
        result = _write_colors(result, colors, period, {key: value for key, value in colors[period].items() if key != day})
    return result


def restore(blocks, day, text, inactive, period="day", color=None):
    if period != 'day':
        raise ValueError('Восстановление удаления доступно только для событий на день')
    day, text = validate_key(day, period), validate_text(text)
    if not text or type(inactive) is not bool:
        raise ValueError('Не указаны текст и актуальность удалённого события')
    events = read(blocks)
    if events is None or read_inactive(blocks) is None or read_colors(blocks) is None:
        raise ValueError('Формат событий неизвестен. Данные сохранены без изменений')
    if day in events:
        raise ValueError('На этой дате уже есть событие. Оно сохранено без изменений')
    result = set_inactive(write(blocks, day, text), day, inactive)
    return set_color(result, day, color) if color is not None else result


def move(blocks, day, days, period="day"):
    block = block_name(period)
    if period == "week":
        blocks = unify_weekly_blocks(blocks)
    day = validate_key(day, period)
    if type(days) is not int or days not in ({-7, 7} if period == "week" else {-7, -1, 1, 7}):
        if period == "week":
            raise ValueError("Недельное событие можно сдвинуть на неделю вперёд или назад")
        raise ValueError("Событие можно сдвинуть на один день или неделю вперёд или назад")
    events = read(blocks, period)
    if events is None:
        raise ValueError("События календаря имеют неизвестный формат и оставлены без изменений")
    if day not in events:
        raise ValueError("Событие на этой дате уже отсутствует. Обнови календарь")
    source_date = date.fromisoformat(day)
    try:
        target_date = source_date + timedelta(days=days)
    except (ValueError, OverflowError):
        raise ValueError("Дата переноса выходит за допустимый диапазон") from None
    target = target_date.isoformat()
    if target in events:
        raise ValueError("На выбранную дату у этого заказа уже есть событие. Оба события оставлены на своих местах")
    flags, colors = read_inactive(blocks), read_colors(blocks)
    if flags is None or colors is None:
        raise ValueError("Формат актуальности или цветов неизвестен. Событие сохранено на прежней дате")
    moved = {**events}
    moved[target] = moved.pop(day)
    result = {**blocks, block: json.dumps({"version": 1, "events": moved}, ensure_ascii=False)}
    if day in flags[period]:
        selected = set(flags[period]); selected.remove(day); selected.add(target)
        result[INACTIVE_BLOCK] = json.dumps({"version": 1, **flags, period: sorted(selected)}, ensure_ascii=False)
    if COLORS_BLOCK in blocks:
        entries = {**colors[period]}
        entries.pop(target, None)
        color = entries.pop(day, None)
        if color is not None:
            entries[target] = color
        result = _write_colors(result, colors, period, entries)
    source_week = source_date - timedelta(days=source_date.weekday())
    target_week = target_date - timedelta(days=target_date.weekday())
    if target_week != source_week:
        result = order_deadlines.write(result, target_week.isoformat(), True)
    return result
