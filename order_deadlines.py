"""Versioned Moscow deadline weeks; weekly comments share the order-calendar event field."""
import json
import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

BLOCK = "Сроки"
COMMENTS_BLOCK = "Комментарии к срокам"
MOSCOW = ZoneInfo("Europe/Moscow")


# Проверяет дату понедельника, используемую как ключ срока заказа.
# При недопустимом состоянии возбуждает ValueError.
def validate_week(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("Укажи дату понедельника недели")
    try:
        monday = date.fromisoformat(value)
        monday + timedelta(days=6)
    except (ValueError, OverflowError):
        raise ValueError("Некорректная дата недели") from None
    if monday.weekday() != 0:
        raise ValueError("Неделя должна начинаться с понедельника")
    return value


# Читает отсортированные уникальные понедельники сроков либо признак неизвестного блока.
# Разбирает JSON; вызывающий код должен учитывать ошибки или неизвестный формат.
def read(blocks):
    if BLOCK not in blocks:
        return []
    try:
        value = json.loads(blocks[BLOCK])
        if not isinstance(value, dict) or set(value) != {"version", "weeks"} or type(value["version"]) is not int or value["version"] != 1:
            return None
        weeks = value["weeks"]
        if not isinstance(weeks, list) or len(weeks) > 5200:
            return None
        parsed = [validate_week(week) for week in weeks]
        return parsed if parsed == sorted(set(parsed)) else None
    except (ValueError, TypeError):
        return None


# Ставит или снимает одну неделю срока, сохраняя прочие блоки карточки.
# При недопустимом состоянии возбуждает ValueError.
def write(blocks, week, selected):
    week = validate_week(week)
    if type(selected) is not bool:
        raise ValueError("Укажи состояние отметки недели")
    previous = read(blocks)
    if previous is None:
        raise ValueError("Сохранённый раздел «Сроки» имеет неизвестный формат и оставлен без изменений")
    weeks = set(previous)
    if selected:
        weeks.add(week)
    else:
        weeks.discard(week)
    if len(weeks) > 5200:
        raise ValueError("Сохранено слишком много недель сроков")
    return {**blocks, BLOCK: json.dumps({"version": 1, "weeks": sorted(weeks)}, ensure_ascii=False)}


# Читает прежний отдельный блок недельных комментариев для совместимости.
# Разбирает JSON; вызывающий код должен учитывать ошибки или неизвестный формат.
def read_legacy_comments(blocks):
    if COMMENTS_BLOCK not in blocks:
        return {}
    try:
        value = json.loads(blocks[COMMENTS_BLOCK])
        if not isinstance(value, dict) or set(value) != {"version", "comments"} or type(value["version"]) is not int or value["version"] != 1:
            return None
        comments = value["comments"]
        if not isinstance(comments, dict) or len(comments) > 5200:
            return None
        for week, comment in comments.items():
            validate_week(week)
            validate_comment(comment)
        return comments
    except (ValueError, TypeError):
        return None


# Проверяет текст недельного комментария перед изменением общего события.
# При недопустимом состоянии возбуждает ValueError.
def validate_comment(comment):
    if not isinstance(comment, str) or len(comment) > 1000 or any(char in comment for char in "\r\n\0"):
        raise ValueError("Комментарий к неделе — одна строка до 1000 символов")
    return comment


# Предоставляет совместимое имя чтения действующих недельных событий.
# Возвращает `order_calendar.read(blocks, 'week')`.
def read_comments(blocks):
    """Compatibility alias; weekly calendar events are the only live field."""
    import order_calendar
    return order_calendar.read(blocks, "week")


# Сохраняет комментарий недели в общем поле недельного события.
# Возвращает `order_calendar.clear_week_comment(blocks, week)`; либо `order_calendar.write(blocks, week, comment, 'week')`.
def write_comment(blocks, week, comment):
    import order_calendar
    week = validate_week(week)
    if comment == "":
        return order_calendar.clear_week_comment(blocks, week)
    return order_calendar.write(blocks, week, comment, "week")


# Строит последовательность недель относительно понедельника Москвы.
# Возвращает `result`.
def week_options(now=None):
    today = (now or datetime.now(MOSCOW)).astimezone(MOSCOW).date()
    monday = today - timedelta(days=today.weekday())
    result = []
    for offset in range(16):
        start = monday + timedelta(weeks=offset)
        end = start + timedelta(days=6)
        year, number, _ = start.isocalendar()
        result.append({"start": start.isoformat(), "end": end.isoformat(), "number": number, "year": year,
            "label": f"{start:%d.%m.%Y} — {end:%d.%m.%Y}", "current": offset == 0})
    return result
