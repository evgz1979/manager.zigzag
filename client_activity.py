"""Client visibility: readable folder marker, SQLite index and durable export queue."""
import json
import threading
from pathlib import Path

import order_document as document
from folder_structure import client_path, is_catalog_group
from event_folder_undo import guard_database

BLOCK = "Активность клиента"
ACTIVE = "Активный"
INACTIVE = "Неактивный"
LOCK = threading.RLock()


class ClientActivityConflict(ValueError):
    pass


def value(record):
    return record.get("extra_blocks", {}).get(BLOCK)


def known(raw):
    return raw is None or raw.strip() in (ACTIVE, INACTIVE)


class ClientActivity:
    def __init__(self, orders, lock=LOCK):
        self.orders = orders
        self.root = orders.root
        self.lock = lock

    def connect(self):
        return self.orders.connect()

    @staticmethod
    def schema(db):
        db.execute("""CREATE TABLE IF NOT EXISTS client_activity (
            path TEXT PRIMARY KEY, inactive INTEGER NOT NULL, revision INTEGER NOT NULL,
            exported_revision INTEGER NOT NULL, file_value TEXT NOT NULL, sync_error TEXT NOT NULL DEFAULT '')""")

    @staticmethod
    def record(row):
        result = dict(row)
        result["inactive"] = bool(result["inactive"])
        result["sync_pending"] = result["revision"] != result.pop("exported_revision")
        result["editable"] = known(json.loads(result.pop("file_value")))
        return result

    def target(self, path):
        if not isinstance(path, str) or not path or Path(path).is_absolute() or client_path(path) != path:
            raise ValueError("Отметка доступна только в карточке клиента")
        guard_database(self.orders.database, path)
        target = self.root / path
        if any((self.root / Path(*Path(path).parts[:index + 1])).is_symlink() for index in range(len(Path(path).parts))):
            raise ValueError("Символические ссылки не редактируются")
        if not target.is_dir():
            raise FileNotFoundError("Папка клиента недоступна")
        return target

    def get(self, path):
        if not self.orders.database.exists():
            return None
        with self.connect() as db:
            self.schema(db)
            row = db.execute("SELECT * FROM client_activity WHERE path=?", (path,)).fetchone()
            return self.record(row) if row else None

    def read(self, path):
        with self.lock:
            folder = self.target(path)
            current = self.get(path)
            if current and current["sync_pending"]:
                return current
            raw = value(document.load(folder, self.orders.labels))
            with self.connect() as db:
                self.schema(db)
                row = db.execute("SELECT * FROM client_activity WHERE path=?", (path,)).fetchone()
                # Unknown user text survives and the last known state remains effective.
                if known(raw):
                    inactive = raw is not None and raw.strip() == INACTIVE
                else:
                    inactive = bool(row and row["inactive"])
                revision = row["revision"] + int(json.loads(row["file_value"]) != raw) if row else 1
                error = "Неизвестный текст [Активность клиента] сохранён. Проверь !.txt клиента." if not known(raw) else ""
                db.execute("""INSERT INTO client_activity VALUES (?,?,?,?,?,?) ON CONFLICT(path) DO UPDATE SET
                    inactive=excluded.inactive,revision=excluded.revision,exported_revision=excluded.exported_revision,
                    file_value=excluded.file_value,sync_error=excluded.sync_error""",
                    (path, int(inactive), revision, revision, json.dumps(raw, ensure_ascii=False), error))
            return self.get(path)

    def save(self, payload):
        path, revision, inactive = payload.get("path"), payload.get("revision"), payload.get("inactive")
        if type(revision) is not int or type(inactive) is not bool:
            raise ValueError("Открой карточку клиента заново перед изменением отметки")
        with self.lock:
            self.target(path)
            with self.connect() as db:
                self.schema(db)
                row = db.execute("SELECT * FROM client_activity WHERE path=?", (path,)).fetchone()
                if not row or row["revision"] != revision:
                    raise ClientActivityConflict("Отметка клиента изменилась. Обнови карточку перед сохранением.")
                if not known(json.loads(row["file_value"])):
                    raise ClientActivityConflict("Неизвестный текст отметки сохранён. Проверь !.txt клиента.")
                db.execute("UPDATE client_activity SET inactive=?,revision=revision+1,sync_error='' WHERE path=? AND revision=?",
                           (int(inactive), path, revision))
        return self.get(path)

    def accept_file(self, payload):
        """Explicit conflict resolution; never discard a pending decision on open."""
        path = payload.get("path")
        with self.lock:
            self.target(path)
            with self.connect() as db:
                self.schema(db)
                row = db.execute("SELECT * FROM client_activity WHERE path=?", (path,)).fetchone()
                if not row or type(payload.get("revision")) is not int or row["revision"] != payload["revision"]:
                    raise ClientActivityConflict("Отметка клиента изменилась. Обнови карточку.")
                raw = value(document.load(self.root / path, self.orders.labels))
                if not known(raw):
                    raise ClientActivityConflict("Неизвестный текст отметки сохранён. Проверь !.txt клиента.")
                db.execute("UPDATE client_activity SET inactive=?,revision=revision+1,exported_revision=revision+1,file_value=?,sync_error='' WHERE path=?",
                           (int(raw is not None and raw.strip() == INACTIVE), json.dumps(raw, ensure_ascii=False), path))
        return self.get(path)

    def inactive_paths(self):
        # Tree/list reads do not create a database or access iCloud cards.
        if not self.orders.database.exists():
            return set()
        with self.connect() as db:
            self.schema(db)
            return {row[0] for row in db.execute("SELECT path FROM client_activity WHERE inactive=1")}

    def visible_orders(self, records):
        inactive = self.inactive_paths()
        return [record for record in records if client_path(record["path"]) not in inactive]

    def refresh(self):
        """Only client cards, never order contents; retain index entries on read errors."""
        def folders(parent):
            return [item for item in parent.iterdir() if not item.name.startswith((".", "#"))
                    and not item.is_symlink() and item.is_dir()]
        for item in folders(self.root):
            try:
                candidates = folders(item) if is_catalog_group(item.name) else [item]
                for candidate in candidates:
                    path = candidate.relative_to(self.root).as_posix()
                    if client_path(path) == path:
                        try:
                            self.read(path)
                        except (OSError, ValueError) as error:
                            self.error(path, error)
            except OSError as error:
                print(f"Активность клиентов · {item.name}: {error}", flush=True)

    def error(self, path, problem):
        with self.connect() as db:
            self.schema(db)
            db.execute("UPDATE client_activity SET sync_error=? WHERE path=?", (document.icloud_access.sync_error(problem), path))

    def sync(self):
        if not self.orders.database.exists():
            return
        with self.lock:
            with self.connect() as db:
                self.schema(db)
                pending = list(db.execute("SELECT * FROM client_activity WHERE revision!=exported_revision"))
            for row in pending:
                try:
                    folder = self.target(row["path"])
                    record = document.load(folder, self.orders.labels)
                    raw, desired = value(record), INACTIVE if row["inactive"] else ACTIVE
                    if raw != json.loads(row["file_value"]) and raw != desired:
                        raise ClientActivityConflict("Отметка в !.txt изменена извне. Сохранены обе версии; выбери отметку из файла или верни прежний текст файла.")
                    if raw != desired:
                        record.setdefault("extra_blocks", {})[BLOCK] = desired
                        document.archive_current(folder)
                        document.atomic_write(folder / document.DOCUMENT, document.render(record, self.orders.labels))
                        document.archive_legacy(folder)
                    with self.connect() as db:
                        db.execute("UPDATE client_activity SET exported_revision=revision,file_value=?,sync_error='' WHERE path=? AND revision=?",
                                   (json.dumps(desired, ensure_ascii=False), row["path"], row["revision"]))
                except (OSError, ValueError) as error:
                    self.error(row["path"], error)
