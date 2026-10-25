"""Standalone day/week events in the working SQLite database."""
import time
import uuid
from contextlib import contextmanager
from datetime import date, timedelta

import local_metadata
import order_calendar
from orders import OrderConflict

COLORS = {"gray", "red", "orange", "yellow", "green", "blue", "purple"}


def schema(db):
    local_metadata.schema(db)
    db.execute("""CREATE TABLE IF NOT EXISTS calendar_events (
        id TEXT PRIMARY KEY, version INTEGER NOT NULL, period TEXT NOT NULL,
        date TEXT NOT NULL, text TEXT NOT NULL, revision INTEGER NOT NULL,
        created REAL NOT NULL, updated REAL NOT NULL, deleted INTEGER NOT NULL DEFAULT 0,
        color TEXT NOT NULL DEFAULT 'gray', is_inactive INTEGER NOT NULL DEFAULT 0)""")
    if "color" not in {row[1] for row in db.execute("PRAGMA table_info(calendar_events)")}:
        db.execute("ALTER TABLE calendar_events ADD COLUMN color TEXT NOT NULL DEFAULT 'gray'")
    if "is_inactive" not in {row[1] for row in db.execute("PRAGMA table_info(calendar_events)")}:
        db.execute("ALTER TABLE calendar_events ADD COLUMN is_inactive INTEGER NOT NULL DEFAULT 0")
        for event in ("UPDATE", "DELETE"):
            db.execute("DROP TRIGGER IF EXISTS metadata_audit_calendar_events_" + event)
    local_metadata.audit(db, "calendar_events")


class CalendarEvents:
    def __init__(self, store):
        self.store = store

    @contextmanager
    def connect(self):
        with self.store.connect() as db:
            schema(db)
            yield db

    @staticmethod
    def identity(payload):
        identity, revision = payload.get("id"), payload.get("revision")
        try:
            if not isinstance(identity, str) or str(uuid.UUID(identity)) != identity:
                raise ValueError()
        except (ValueError, AttributeError):
            raise ValueError("Некорректный идентификатор события") from None
        if type(revision) is not int or revision < 0:
            raise ValueError("Нужна версия события")
        return identity, revision

    @staticmethod
    def record(row):
        return dict(row) if row is not None else None

    @staticmethod
    def validate(row):
        if row["version"] != 1 or row["color"] not in COLORS or row["is_inactive"] not in (0, 1):
            raise ValueError("Событие имеет неизвестный формат и сохранено без изменений")
        order_calendar.block_name(row["period"])
        order_calendar.validate_key(row["date"], row["period"])
        if not order_calendar.validate_text(row["text"]):
            raise ValueError("Введи название события")

    def list(self):
        with self.connect() as db:
            return [self.record(row) for row in db.execute(
                "SELECT * FROM calendar_events WHERE deleted=0 ORDER BY created,id")]

    def get(self, identity):
        self.identity({"id": identity, "revision": 0})
        with self.connect() as db:
            row = db.execute("SELECT * FROM calendar_events WHERE id=?", (identity,)).fetchone()
            if row is None:
                raise FileNotFoundError("Событие больше не найдено")
            return self.record(row)

    def save(self, payload):
        identity, revision = self.identity(payload)
        period = payload.get("period")
        order_calendar.block_name(period)
        day = order_calendar.validate_key(payload.get("date"), period)
        text = order_calendar.validate_text(payload.get("text"))
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM calendar_events WHERE id=?", (identity,)).fetchone()
            if row is None:
                if revision != 0:
                    raise OrderConflict("Событие больше не найдено. Твой текст оставлен в поле")
                if not text:
                    raise ValueError("Введи название события")
                now = time.time()
                db.execute("INSERT INTO calendar_events (id,version,period,date,text,revision,created,updated,deleted) VALUES (?,1,?,?,?,1,?,?,0)",
                           (identity, period, day, text, now, now))
            else:
                self.validate(row)
                # Retrying an unanswered creation cannot create a second event.
                retry = revision == 0 and row["revision"] == 1 and not row["deleted"]
                if retry and (row["period"], row["date"], row["text"]) == (period, day, text):
                    return self.record(row)
                if revision != row["revision"] or row["deleted"] or (row["period"], row["date"]) != (period, day):
                    raise OrderConflict("Событие изменилось в другом окне. Проверь изменения перед сохранением")
                db.execute("UPDATE calendar_events SET text=?,is_inactive=?,revision=revision+1,updated=? WHERE id=?",
                           (text if text else row["text"], row["is_inactive"] if text else 1, time.time(), identity))
                if not text:
                    order_calendar.mark_relevance_contract(db)
            return self.record(db.execute("SELECT * FROM calendar_events WHERE id=?", (identity,)).fetchone())

    def set_deleted(self, payload, deleted):
        identity, revision = self.identity(payload)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM calendar_events WHERE id=?', (identity,)).fetchone()
            if row is None or revision != row['revision']:
                raise OrderConflict('Событие изменилось в другом окне. Проверь изменения перед повтором')
            self.validate(row)
            if row['period'] != 'day':
                raise ValueError('Удалять можно только события на день')
            if bool(row['deleted']) == deleted:
                return self.record(row)
            db.execute('UPDATE calendar_events SET deleted=?,revision=revision+1,updated=? WHERE id=?',
                       (int(deleted), time.time(), identity))
            return self.record(db.execute('SELECT * FROM calendar_events WHERE id=?', (identity,)).fetchone())

    def move(self, payload):
        identity, revision = self.identity(payload)
        days = payload.get("days")
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM calendar_events WHERE id=?", (identity,)).fetchone()
            if row is None or row["deleted"] or revision != row["revision"]:
                raise OrderConflict("Событие изменилось или удалено в другом окне. Обнови календарь")
            self.validate(row)
            allowed = {-7, 7} if row["period"] == "week" else {-7, -1, 1, 7}
            if type(days) is not int or days not in allowed:
                raise ValueError("Дневное событие можно сдвинуть на день или неделю; недельное — на неделю")
            try:
                target = (date.fromisoformat(row["date"]) + timedelta(days=days)).isoformat()
            except (ValueError, OverflowError):
                raise ValueError("Дата переноса выходит за допустимый диапазон") from None
            db.execute("UPDATE calendar_events SET date=?,revision=revision+1,updated=? WHERE id=?",
                       (target, time.time(), identity))
            return self.record(db.execute("SELECT * FROM calendar_events WHERE id=?", (identity,)).fetchone())

    def color(self, payload):
        identity, revision = self.identity(payload)
        color = payload.get("color")
        if not isinstance(color, str) or color not in COLORS:
            raise ValueError("Выбери цвет события")
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM calendar_events WHERE id=?", (identity,)).fetchone()
            if row is None or row["deleted"] or revision != row["revision"]:
                raise OrderConflict("Событие изменилось или удалено в другом окне. Обнови календарь")
            self.validate(row)
            db.execute("UPDATE calendar_events SET color=?,revision=revision+1,updated=? WHERE id=?",
                       (color, time.time(), identity))
            return self.record(db.execute("SELECT * FROM calendar_events WHERE id=?", (identity,)).fetchone())

    def set_inactive(self, payload):
        identity, revision = self.identity(payload)
        inactive = payload.get("is_inactive")
        if type(inactive) is not bool:
            raise ValueError("Укажи состояние актуальности события")
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM calendar_events WHERE id=?", (identity,)).fetchone()
            if row is None or row["deleted"] or revision != row["revision"]:
                raise OrderConflict("Событие изменилось в другом окне. Обнови календарь и повтори отметку")
            self.validate(row)
            db.execute("UPDATE calendar_events SET is_inactive=?,revision=revision+1,updated=? WHERE id=?",
                       (int(inactive), time.time(), identity))
            order_calendar.mark_relevance_contract(db)
            return self.record(db.execute("SELECT * FROM calendar_events WHERE id=?", (identity,)).fetchone())
