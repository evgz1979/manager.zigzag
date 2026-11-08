"""Standalone day/week events in the working SQLite database."""
import time
import uuid
from contextlib import contextmanager
from datetime import date, timedelta

import local_metadata
import order_calendar
from orders import OrderConflict

COLORS = order_calendar.COLORS
CALENDAR_EVENT_COMMENTS_VERSION = 1
COMMENT_LIMIT = 10000


# Создаёт отсутствующие таблицы и совместимые расширения схемы.
# Работает с таблицами calendar_events.
def schema(db):
    local_metadata.schema(db)
    db.execute("""CREATE TABLE IF NOT EXISTS calendar_events (
        id TEXT PRIMARY KEY, version INTEGER NOT NULL, period TEXT NOT NULL,
        date TEXT NOT NULL, text TEXT NOT NULL, revision INTEGER NOT NULL,
        created REAL NOT NULL, updated REAL NOT NULL, deleted INTEGER NOT NULL DEFAULT 0,
        color TEXT NOT NULL DEFAULT 'gray', is_inactive INTEGER NOT NULL DEFAULT 0,
        is_completed INTEGER NOT NULL DEFAULT 0, is_trip INTEGER NOT NULL DEFAULT 0,
        comment TEXT NOT NULL DEFAULT '')""")
    if "color" not in {row[1] for row in db.execute("PRAGMA table_info(calendar_events)")}:
        db.execute("ALTER TABLE calendar_events ADD COLUMN color TEXT NOT NULL DEFAULT 'gray'")
    if "is_inactive" not in {row[1] for row in db.execute("PRAGMA table_info(calendar_events)")}:
        db.execute("ALTER TABLE calendar_events ADD COLUMN is_inactive INTEGER NOT NULL DEFAULT 0")
        for event in ("UPDATE", "DELETE"):
            db.execute("DROP TRIGGER IF EXISTS metadata_audit_calendar_events_" + event)
    if "is_completed" not in {row[1] for row in db.execute("PRAGMA table_info(calendar_events)")}:
        db.execute("ALTER TABLE calendar_events ADD COLUMN is_completed INTEGER NOT NULL DEFAULT 0")
        for event in ("UPDATE", "DELETE"):
            db.execute("DROP TRIGGER IF EXISTS metadata_audit_calendar_events_" + event)
    if "is_trip" not in {row[1] for row in db.execute("PRAGMA table_info(calendar_events)")}:
        db.execute("ALTER TABLE calendar_events ADD COLUMN is_trip INTEGER NOT NULL DEFAULT 0")
        for event in ("UPDATE", "DELETE"):
            db.execute("DROP TRIGGER IF EXISTS metadata_audit_calendar_events_" + event)
    if "comment" not in {row[1] for row in db.execute("PRAGMA table_info(calendar_events)")}:
        db.execute("ALTER TABLE calendar_events ADD COLUMN comment TEXT NOT NULL DEFAULT ''")
        for event in ("UPDATE", "DELETE"):
            db.execute("DROP TRIGGER IF EXISTS metadata_audit_calendar_events_" + event)
    local_metadata.audit(db, "calendar_events")


# Проверяет необязательный многострочный комментарий свободного события.
# Принимает строку до 10000 символов, нормализует переводы строк и крайние пробелы.
def validate_comment(value):
    if not isinstance(value, str) or len(value) > COMMENT_LIMIT or "\x00" in value:
        raise ValueError("Комментарий должен быть текстом не длиннее 10000 символов")
    return value.replace("\r\n", "\n").replace("\r", "\n").strip()


# Хранит свободные дневные и недельные события с UUID/revision и историей.
# Основные операции: __init__, connect, identity, record, validate; остальные описаны у методов.
class CalendarEvents:
    # Сохраняет зависимости и начальные параметры экземпляра.
    # Состояние и зависимости сохраняются в полях self для последующих операций.
    def __init__(self, store):
        self.store = store

    # Открывает соединение SQLite и управляет его временем жизни.
    # Передаёт ресурс через yield; освобождение выполняется при выходе из контекста.
    @contextmanager
    def connect(self):
        with self.store.connect() as db:
            schema(db)
            yield db

    # Проверяет или вычисляет устойчивую идентичность объекта.
    # При недопустимом состоянии возбуждает ValueError.
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

    # Преобразует строку SQLite в представление для вызывающего кода.
    # Возвращает `dict(row) if row is not None else None`.
    @staticmethod
    def record(row):
        return dict(row) if row is not None else None

    # Проверяет период, реальную дату, текст, комментарий и цвет свободного события.
    # При недопустимом состоянии возбуждает ValueError.
    @staticmethod
    def validate(row):
        if row["version"] != 1 or row["color"] not in COLORS or row["is_inactive"] not in (0, 1) or row['is_completed'] not in (0, 1) or row['is_trip'] not in (0, 1):
            raise ValueError("Событие имеет неизвестный формат и сохранено без изменений")
        order_calendar.block_name(row["period"])
        order_calendar.validate_key(row["date"], row["period"])
        if not order_calendar.validate_text(row["text"]):
            raise ValueError("Введи название события")
        validate_comment(row["comment"])

    # Читает все неудалённые свободные события из SQLite.
    # Работает с таблицами calendar_events.
    def list(self):
        with self.connect() as db:
            return [self.record(row) for row in db.execute(
                "SELECT * FROM calendar_events WHERE deleted=0 ORDER BY created,id")]

    # Находит свободное событие по UUID в текущей транзакции.
    # Работает с таблицами calendar_events.
    def get(self, identity):
        self.identity({"id": identity, "revision": 0})
        with self.connect() as db:
            row = db.execute("SELECT * FROM calendar_events WHERE id=?", (identity,)).fetchone()
            if row is None:
                raise FileNotFoundError("Событие больше не найдено")
            return self.record(row)

    # Создаёт или меняет название и комментарий свободного события с UUID/revision.
    # Отсутствующее поле comment сохраняет прежний текст; история и маркер отката атомарны.
    def save(self, payload):
        identity, revision = self.identity(payload)
        period = payload.get("period")
        order_calendar.block_name(period)
        day = order_calendar.validate_key(payload.get("date"), period)
        text = order_calendar.validate_text(payload.get("text"))
        comment = validate_comment(payload["comment"]) if "comment" in payload else None
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM calendar_events WHERE id=?", (identity,)).fetchone()
            if row is None:
                if revision != 0:
                    raise OrderConflict("Событие больше не найдено. Твой текст оставлен в поле")
                if not text:
                    raise ValueError("Введи название события")
                now = time.time()
                db.execute("INSERT INTO calendar_events (id,version,period,date,text,comment,revision,created,updated,deleted) VALUES (?,1,?,?,?,?,1,?,?,0)",
                           (identity, period, day, text, comment or "", now, now))
            else:
                self.validate(row)
                # Retrying an unanswered creation cannot create a second event.
                retry = revision == 0 and row["revision"] == 1 and not row["deleted"]
                if retry and (row["period"], row["date"], row["text"], row["comment"]) == (period, day, text, comment or ""):
                    return self.record(row)
                if revision != row["revision"] or row["deleted"] or (row["period"], row["date"]) != (period, day):
                    raise OrderConflict("Событие изменилось в другом окне. Проверь изменения перед сохранением")
                db.execute("UPDATE calendar_events SET text=?,comment=?,is_inactive=?,revision=revision+1,updated=? WHERE id=?",
                           (text if text else row["text"], row["comment"] if comment is None else comment,
                            row["is_inactive"] if text else 1, time.time(), identity))
                if not text:
                    order_calendar.mark_relevance_contract(db)
            if comment:
                db.execute("INSERT OR IGNORE INTO metadata_settings VALUES ('calendar_event_comments','1')")
            return self.record(db.execute("SELECT * FROM calendar_events WHERE id=?", (identity,)).fetchone())

    # Удаляет или восстанавливает свободное дневное либо недельное событие.
    # Проверяет UUID/revision и формат; меняет только deleted, revision/updated с прежней историей.
    def set_deleted(self, payload, deleted):
        identity, revision = self.identity(payload)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM calendar_events WHERE id=?', (identity,)).fetchone()
            if row is None or revision != row['revision']:
                raise OrderConflict('Событие изменилось в другом окне. Проверь изменения перед повтором')
            self.validate(row)
            if bool(row['deleted']) == deleted:
                return self.record(row)
            db.execute('UPDATE calendar_events SET deleted=?,revision=revision+1,updated=? WHERE id=?',
                       (int(deleted), time.time(), identity))
            return self.record(db.execute('SELECT * FROM calendar_events WHERE id=?', (identity,)).fetchone())

    # Переносит объект или событие с проверкой исходного и целевого состояния.
    # Работает с таблицами calendar_events.
    def move(self, payload):
        identity, revision = self.identity(payload)
        days = payload.get("days")
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM calendar_events WHERE id=?", (identity,)).fetchone()
            if row is None or row["deleted"] or revision != row["revision"]:
                raise OrderConflict("Событие изменилось или удалено в другом окне. Обнови календарь")
            self.validate(row)
            allowed = {-7, 7} if row["period"] == "week" else {-7, -1, 1, 2, 3, 4, 5, 6, 7}
            if type(days) is not int or days not in allowed:
                raise ValueError("Дневное событие можно сдвинуть на 1–7 дней вперёд, день или неделю назад; недельное — на неделю")
            try:
                target = (date.fromisoformat(row["date"]) + timedelta(days=days)).isoformat()
            except (ValueError, OverflowError):
                raise ValueError("Дата переноса выходит за допустимый диапазон") from None
            db.execute("UPDATE calendar_events SET date=?,revision=revision+1,updated=? WHERE id=?",
                       (target, time.time(), identity))
            return self.record(db.execute("SELECT * FROM calendar_events WHERE id=?", (identity,)).fetchone())

    # Меняет выбранный цвет события, сохраняя остальные признаки.
    # Работает с таблицами calendar_events.
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

    # Меняет только независимую отметку неактуальности события.
    # Возвращает `self._set_flag(payload, 'is_inactive')`.
    def set_inactive(self, payload):
        return self._set_flag(payload, 'is_inactive')

    # Меняет только независимую отметку выполнения события.
    # Возвращает `self._set_flag(payload, 'is_completed')`.
    def set_completed(self, payload):
        return self._set_flag(payload, 'is_completed')

    # Меняет только независимую отметку выезда события.
    # Возвращает `self._set_flag(payload, 'is_trip')`.
    def set_trip(self, payload):
        return self._set_flag(payload, 'is_trip')

    # Обрабатывает общий контракт независимой отметки календаря.
    # Работает с таблицами calendar_events.
    def _set_flag(self, payload, field):
        identity, revision = self.identity(payload)
        value = payload.get(field)
        if type(value) is not bool:
            raise ValueError("Укажи логическое состояние отметки события")
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM calendar_events WHERE id=?", (identity,)).fetchone()
            if row is None or row["deleted"] or revision != row["revision"]:
                raise OrderConflict("Событие изменилось в другом окне. Обнови календарь и повтори отметку")
            self.validate(row)
            db.execute("UPDATE calendar_events SET " + field + "=?,revision=revision+1,updated=? WHERE id=?",
                       (int(value), time.time(), identity))
            order_calendar.mark_flag_contract(db, field)
            return self.record(db.execute("SELECT * FROM calendar_events WHERE id=?", (identity,)).fetchone())
