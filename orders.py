"""Local order register and durable, retryable exports to document folders."""
import hashlib
import json
import os
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
import order_document as document
from order_document import money, MAX_MONEY

SNAPSHOT = ".order.json"  # Read-only compatibility with the previous export.
CARD = document.DOCUMENT
SYNC_LOCK = threading.Lock()


class OrderConflict(ValueError):
    pass


class OrderStore:
    def __init__(self, root, data_dir, labels):
        self.root = Path(root)
        # Changing the configured document root must never mix separate registers.
        key = hashlib.sha256(str(root).encode()).hexdigest()[:16]
        self.database = Path(data_dir) / f"orders-{key}.sqlite3"
        self.labels = labels

    @contextmanager
    def connect(self):
        self.database.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.database, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("""CREATE TABLE IF NOT EXISTS orders (
                path TEXT PRIMARY KEY, id TEXT NOT NULL UNIQUE, title TEXT NOT NULL,
                status TEXT NOT NULL, note TEXT NOT NULL, amount INTEGER, costs INTEGER,
                paid INTEGER, revision INTEGER NOT NULL, exported_revision INTEGER NOT NULL DEFAULT 0,
                updated REAL NOT NULL, sync_error TEXT NOT NULL DEFAULT '')""")
            with db:
                db.execute("BEGIN IMMEDIATE")
                columns = {row[1] for row in db.execute("PRAGMA table_info(orders)")}
                if "extra_blocks" not in columns:
                    db.execute("ALTER TABLE orders ADD COLUMN extra_blocks TEXT NOT NULL DEFAULT '{}'")
                if "export_format" not in columns:
                    db.execute("ALTER TABLE orders ADD COLUMN export_format INTEGER NOT NULL DEFAULT 0")
            with db:
                yield db
        finally:
            db.close()

    def path(self, relative):
        if not isinstance(relative, str) or not relative or relative == ".":
            raise ValueError("Выберите папку заказа")
        parts = Path(relative).parts
        if Path(relative).is_absolute() or any(part.startswith(".") for part in parts) or parts[0].startswith("#"):
            raise ValueError("Выберите папку внутри клиента")
        return Path(*parts).as_posix()

    def target(self, relative):
        relative = self.path(relative)
        target = self.root / relative
        if any((self.root / Path(*Path(relative).parts[:i + 1])).is_symlink() for i in range(len(Path(relative).parts))):
            raise ValueError("Символические ссылки не редактируются")
        if not target.is_dir():
            raise FileNotFoundError("Папка заказа недоступна. Данные сохранены в базе; проверьте iCloud и путь заказа.")
        return target

    @staticmethod
    def record(row):
        if row is None:
            return None
        result = dict(row)
        result["client"] = Path(result["path"]).parts[0]
        result["profit"] = result["amount"] - result["costs"] if result["amount"] is not None and result["costs"] is not None else None
        result["debt"] = result["amount"] - result["paid"] if result["amount"] is not None and result["paid"] is not None else None
        result["extra_blocks"] = json.loads(result["extra_blocks"])
        exported_revision, export_format = result.pop("exported_revision"), result.pop("export_format")
        result["sync_pending"] = result["revision"] != exported_revision or export_format < document.FORMAT
        return result

    def get(self, relative):
        if not self.database.exists():
            return None
        with self.connect() as db:
            return self.record(db.execute("SELECT * FROM orders WHERE path=?", (relative,)).fetchone())

    def list(self):
        if not self.database.exists():
            return []
        with self.connect() as db:
            return [self.record(row) for row in db.execute("SELECT * FROM orders ORDER BY updated DESC, path")]

    def add(self, relative, initial):
        relative = self.path(relative)
        self.target(relative)
        status, note = initial.get("status", "new"), initial.get("note", "")
        if not isinstance(status, str) or status not in self.labels or not isinstance(note, str):
            raise ValueError("Некорректный статус или заметка")
        with self.connect() as db:
            db.execute("""INSERT OR IGNORE INTO orders
                (path,id,title,status,note,amount,costs,paid,revision,updated,extra_blocks)
                VALUES (?,?,?,?,?,?,?,?,1,?,?)""", (relative, str(uuid.uuid4()), initial.get("title", Path(relative).name),
                status, note, initial.get("amount"), initial.get("costs"), initial.get("paid"), time.time(),
                json.dumps(initial.get("extra_blocks", {}), ensure_ascii=False)))
        return self.get(relative)

    def save(self, payload):
        relative = self.path(payload.get("path"))
        status, note, title = payload.get("status"), payload.get("note"), payload.get("title")
        if not isinstance(status, str) or status not in self.labels or not isinstance(note, str) or len(note) > 100_000:
            raise ValueError("Некорректный статус или заметка")
        if not isinstance(title, str) or not title.strip() or len(title) > 500 or any(c in title for c in "\r\n\x00"):
            raise ValueError("Укажите название одной строкой")
        values = [money(payload.get(key)) for key in ("amount", "costs", "paid")]
        revision = payload.get("revision")
        if type(revision) is not int:
            raise ValueError("Не указана версия заказа. Откройте заказ заново.")
        with self.connect() as db:
            result = db.execute("""UPDATE orders SET title=?,status=?,note=?,amount=?,costs=?,paid=?,
                revision=revision+1,updated=?,sync_error='' WHERE path=? AND revision=?""",
                (title.strip(), status, note, *values, time.time(), relative, revision))
            if not result.rowcount:
                raise OrderConflict("Заказ изменён в другой вкладке. Откройте его заново перед сохранением.")
        return self.get(relative)

    def atomic_write(self, target, body):
        document.atomic_write(target, body)

    def sync(self):
        if not SYNC_LOCK.acquire(blocking=False):
            return
        try:
            for record in self.list():
                if not record["sync_pending"]:
                    continue
                error = ""
                try:
                    folder = self.target(record["path"])
                    existing = document.load(folder, self.labels)
                    record["extra_blocks"].update(existing.get("extra_blocks", {}))
                    self.atomic_write(folder / CARD, document.render(record, self.labels))
                    document.archive_legacy(folder)
                except (OSError, ValueError) as problem:
                    error = str(problem)
                with self.connect() as db:
                    db.execute("""UPDATE orders SET sync_error=?,exported_revision=CASE WHEN ?='' THEN ?
                        ELSE exported_revision END, export_format=CASE WHEN ?='' THEN ? ELSE export_format END,
                        extra_blocks=CASE WHEN ?='' THEN ? ELSE extra_blocks END WHERE path=? AND revision=?""",
                        (error, error, record["revision"], error, document.FORMAT, error,
                         json.dumps(record["extra_blocks"], ensure_ascii=False), record["path"], record["revision"]))
        finally:
            SYNC_LOCK.release()

    def import_folder(self, relative, fallback=None):
        folder = self.target(relative)
        initial = document.load(folder, self.labels) or fallback or {"status": "new", "note": ""}
        if initial.get("id"):
            self.restore(relative, initial)
        else:
            self.add(relative, initial)
        return self.get(relative)

    def restore(self, relative, snapshot):
        """Import only missing records. Existing database values always win."""
        relative = self.path(relative)
        if not isinstance(snapshot, dict) or snapshot.get("schema") not in (1, document.FORMAT):
            raise ValueError("Неподдерживаемый формат карточки заказа")
        status, title, note = (snapshot.get(key) for key in ("status", "title", "note"))
        if (not isinstance(status, str) or status not in self.labels or not isinstance(title, str)
                or not title.strip() or len(title) > 500 or any(char in title for char in "\r\n\x00")
                or not isinstance(note, str) or len(note) > 100_000):
            raise ValueError("Некорректная карточка заказа")
        values = [snapshot.get(key) for key in ("amount", "costs", "paid")]
        if any(value is not None and (type(value) is not int or value < 0 or value > MAX_MONEY) for value in values):
            raise ValueError("Некорректные финансовые данные в карточке заказа")
        try:
            identity = str(uuid.UUID(snapshot.get("id", "")))
        except (ValueError, TypeError, AttributeError):
            raise ValueError("Некорректный идентификатор карточки")
        revision = snapshot.get("revision")
        if type(revision) is not int or not 1 <= revision < 2**63 - 1:
            raise ValueError("Некорректная версия карточки")
        document.validate_blocks(snapshot.get("extra_blocks", {}))
        # A copied folder gets a new identity; never drops the copied order.
        with self.connect() as db:
            if db.execute("SELECT 1 FROM orders WHERE id=? AND path<>?", (identity, relative)).fetchone():
                identity = str(uuid.uuid4())
            db.execute("""INSERT OR IGNORE INTO orders
                (path,id,title,status,note,amount,costs,paid,revision,exported_revision,updated,extra_blocks)
                VALUES (?,?,?,?,?,?,?,?,?,0,?,?)""", (relative, identity, title, status, note,
                *values, revision, time.time(), json.dumps(snapshot.get("extra_blocks", {}), ensure_ascii=False)))

    def discover(self, read_status, progress):
        """Explicit background scan: directory names and metadata, never attachments."""
        if not self.root.is_dir():
            raise FileNotFoundError("Корень документов недоступен")
        for current, dirs, names in os.walk(self.root, followlinks=False,
                onerror=lambda error: progress["errors"].append(str(error))):
            folder = Path(current)
            dirs[:] = [name for name in dirs if not name.startswith(".") and not (folder / name).is_symlink()
                       and not (folder == self.root and name.startswith("#"))]
            progress["folders"] += 1
            relative = folder.relative_to(self.root).as_posix()
            if folder == self.root or self.get(relative):
                continue
            try:
                if not any(name in names for name in (CARD, SNAPSHOT, *document.LEGACY_STATUSES)):
                    continue
                self.import_folder(relative)
                progress["added"] += 1
            except (OSError, ValueError, TypeError, AttributeError) as error:
                progress["errors"].append(relative + ": " + str(error))
