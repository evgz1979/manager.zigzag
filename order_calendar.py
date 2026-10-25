"""Per-order calendar entries, independent of weekly deadline marks."""
import json
import re
from datetime import date, timedelta

BLOCK = "События календаря"
WEEK_BLOCK = "События календаря на неделю"
MAX_EVENTS = 5200
WEEKLY_EVENTS_UNIFIED_VERSION = 1


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
    import order_deadlines
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
    else:
        events.pop(day, None)
    if len(events) > MAX_EVENTS:
        raise ValueError("Сохранено слишком много событий календаря")
    return {**blocks, block: json.dumps({"version": 1, "events": events}, ensure_ascii=False)}


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
    try:
        target = (date.fromisoformat(day) + timedelta(days=days)).isoformat()
    except (ValueError, OverflowError):
        raise ValueError("Дата переноса выходит за допустимый диапазон") from None
    if target in events:
        raise ValueError("На выбранную дату у этого заказа уже есть событие. Оба события оставлены на своих местах")
    moved = {**events}
    moved[target] = moved.pop(day)
    return {**blocks, block: json.dumps({"version": 1, "events": moved}, ensure_ascii=False)}
