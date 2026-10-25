"""Versioned deadline week marks and the rolling Moscow calendar shown on orders."""
import json
import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

BLOCK = "Сроки"
MOSCOW = ZoneInfo("Europe/Moscow")


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


def week_options(now=None):
    today = (now or datetime.now(MOSCOW)).astimezone(MOSCOW).date()
    monday = today - timedelta(days=today.weekday())
    result = []
    for offset in range(10):
        start = monday + timedelta(weeks=offset)
        end = start + timedelta(days=6)
        year, number, _ = start.isocalendar()
        result.append({"start": start.isoformat(), "end": end.isoformat(), "number": number, "year": year,
            "label": f"{start:%d.%m.%Y} — {end:%d.%m.%Y}", "current": offset == 0})
    return result
