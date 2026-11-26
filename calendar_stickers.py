"""Movable notes over the interactive calendar grid."""
import time

import local_metadata
from calendar_events import CalendarEvents
from order_calendar import validate_key
from orders import OrderConflict


# Создаёт таблицу стикеров и подключает общую историю SQLite.
# Координаты от 0 до 10000 задают долю доступной ширины и высоты недели.
def schema(db):
    local_metadata.schema(db)
    db.execute("""CREATE TABLE IF NOT EXISTS calendar_stickers (
        id TEXT PRIMARY KEY, version INTEGER NOT NULL, revision INTEGER NOT NULL,
        week TEXT NOT NULL, x INTEGER NOT NULL, y INTEGER NOT NULL, text TEXT NOT NULL,
        deleted INTEGER NOT NULL DEFAULT 0, updated REAL NOT NULL)""")
    local_metadata.audit(db, "calendar_stickers")


# Читает неудалённые листки для главной страницы.
# Отдаёт только известный формат, в порядке от старых изменений к новым.
def listed(store):
    with store.connect() as db:
        schema(db)
        return [dict(row) for row in db.execute(
            "SELECT * FROM calendar_stickers WHERE deleted=0 AND version=1 ORDER BY updated,id")]


# Читает один стикер по UUID для разрешения конфликта в редакторе.
# Возвращает также надгробие удалённой записи, если UUID известен.
def read(store, identity):
    try:
        CalendarEvents.identity({"id": identity, "revision": 0})
    except ValueError:
        raise ValueError("Некорректный идентификатор стикера") from None
    with store.connect() as db:
        schema(db)
        row = db.execute("SELECT * FROM calendar_stickers WHERE id=?", (identity,)).fetchone()
        return dict(row) if row is not None else None


# Сохраняет текст и положение стикера или отмечает его удалённым.
# Проверяет ревизию внутри транзакции и допускает точный повтор сохранённого запроса.
def save(store, payload):
    try:
        identity, revision = CalendarEvents.identity(payload)
        week = validate_key(payload.get("week"), "week")
    except ValueError:
        raise ValueError("Укажи идентификатор, версию и понедельник недели стикера") from None
    x, y, body, deleted = (payload.get(key) for key in ("x", "y", "text", "deleted"))
    if any(type(value) is not int or not 0 <= value <= 10000 for value in (x, y)):
        raise ValueError("Некорректное положение стикера")
    if not isinstance(body, str) or len(body) > 2000 or "\x00" in body:
        raise ValueError("Текст стикера должен быть не длиннее 2000 символов")
    if type(deleted) is not bool:
        raise ValueError("Некорректный признак удаления стикера")
    fields = (week, x, y, body.replace("\r\n", "\n").replace("\r", "\n"), int(deleted))
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        schema(db)
        row = db.execute("SELECT * FROM calendar_stickers WHERE id=?", (identity,)).fetchone()
        if row is None:
            if revision != 0 or deleted:
                raise OrderConflict("Стикер больше недоступен")
            db.execute("INSERT INTO calendar_stickers (week,x,y,text,deleted,updated,id,version,revision) VALUES (?,?,?,?,?,?,?,1,1)",
                       (*fields, time.time(), identity))
        else:
            if row["version"] != 1:
                raise OrderConflict("Формат стикера изменился")
            if (row["week"], row["x"], row["y"], row["text"], row["deleted"]) == fields and revision in (row["revision"], row["revision"] - 1):
                return dict(row)
            if row["deleted"] or revision != row["revision"]:
                raise OrderConflict("Стикер изменён в другом окне")
            db.execute("UPDATE calendar_stickers SET week=?,x=?,y=?,text=?,deleted=?,updated=?,revision=revision+1 WHERE id=?",
                       (*fields, time.time(), identity))
        return dict(db.execute("SELECT * FROM calendar_stickers WHERE id=?", (identity,)).fetchone())
