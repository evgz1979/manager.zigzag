"""Per-order calendar entries, independent of weekly deadline marks."""
import json
import re
from datetime import date

BLOCK = "События календаря"
MAX_EVENTS = 5200


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


def read(blocks):
    if BLOCK not in blocks:
        return {}
    try:
        value = json.loads(blocks[BLOCK])
        if not isinstance(value, dict) or set(value) != {"version", "events"} or type(value["version"]) is not int or value["version"] != 1:
            return None
        events = value["events"]
        if not isinstance(events, dict) or len(events) > MAX_EVENTS:
            return None
        for day, text in events.items():
            validate_date(day)
            if not validate_text(text):
                return None
        return events
    except (ValueError, TypeError):
        return None


def write(blocks, day, text):
    day, text = validate_date(day), validate_text(text)
    events = read(blocks)
    if events is None:
        raise ValueError("События календаря имеют неизвестный формат и оставлены без изменений")
    events = {**events}
    if text:
        events[day] = text
    else:
        events.pop(day, None)
    if len(events) > MAX_EVENTS:
        raise ValueError("Сохранено слишком много событий календаря")
    return {**blocks, BLOCK: json.dumps({"version": 1, "events": events}, ensure_ascii=False)}
