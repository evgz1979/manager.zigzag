"""Versioned Moscow deadline weeks; weekly comments share the order-calendar event field."""
import json
import re
import time
import uuid
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from local_metadata import audit, schema

BLOCK = "Сроки"
COMMENTS_BLOCK = "Комментарии к срокам"
MOSCOW = ZoneInfo("Europe/Moscow")
HIGHLIGHT_KIND = "deadline_highlights"
DEFAULT_HIGHLIGHTS = tuple((date(2026, 12, 14) + timedelta(weeks=index)).isoformat() for index in range(7))


# Обозначает устаревшую версию общей настройки полосы.
# HTTP-обработчик возвращает 409, запись остаётся прежней.
class WeekHighlightConflict(ValueError):
    pass


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


# Проверяет набор недель жёлтой полосы и возвращает отсортированные понедельники.
# Повтор, несуществующая дата или слишком длинный список вызывают ValueError.
def validate_highlights(weeks):
    if not isinstance(weeks, list) or len(weeks) > 5200:
        raise ValueError("Укажи список недель для жёлтой полосы")
    parsed = sorted(validate_week(week) for week in weeks)
    if len(parsed) != len(set(parsed)):
        raise ValueError("Неделя жёлтой полосы указана дважды")
    return parsed


# Читает общую настройку полосы из SQLite без доступа к папкам заказов.
# Отсутствующая запись даёт прежние семь недель, неизвестный формат даёт weeks=null.
def read_highlights(db):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='metadata_records'").fetchone():
        return {"revision": 0, "weeks": list(DEFAULT_HIGHLIGHTS)}
    row = db.execute("SELECT data,revision FROM metadata_records WHERE kind=? AND path=''", (HIGHLIGHT_KIND,)).fetchone()
    if row is None:
        return {"revision": 0, "weeks": list(DEFAULT_HIGHLIGHTS)}
    weeks = None
    try:
        data = json.loads(row["data"])
        if isinstance(data, dict) and set(data) == {"version", "weeks"} and type(data["version"]) is int and data["version"] == 1:
            weeks = validate_highlights(data["weeks"])
    except ValueError:
        pass
    return {"revision": row["revision"], "weeks": weeks}


# Читает или сохраняет общие отмеченные недели по ожидаемой версии.
# Полный набор, в том числе пустой, и история сохраняются одной транзакцией.
def highlight_settings(store, payload=None):
    if payload is None:
        with store.connect() as db:
            return read_highlights(db)
    revision = payload.get("revision")
    if type(revision) is not int or revision < 0:
        raise ValueError("Укажи версию жёлтой полосы")
    weeks = validate_highlights(payload.get("weeks"))
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        current = read_highlights(db)
        if revision != current["revision"]:
            raise WeekHighlightConflict("Отметки изменились в другом окне.")
        if current["weeks"] is None:
            raise ValueError("Неизвестный формат жёлтой полосы")
        if current["weeks"] == weeks:
            return current
        schema(db)
        audit(db, "metadata_records")
        data = json.dumps({"version": 1, "weeks": weeks})
        db.execute("""INSERT INTO metadata_records VALUES (?,?,'',?,1,?)
            ON CONFLICT(kind,path) DO UPDATE SET data=excluded.data,revision=revision+1,updated=excluded.updated""",
                   (str(uuid.uuid4()), HIGHLIGHT_KIND, data, time.time()))
        return {"revision": revision + 1, "weeks": weeks}


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
