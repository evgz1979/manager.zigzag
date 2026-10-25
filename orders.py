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
import order_deadlines
import work_orders
from order_document import money, MAX_MONEY
from folder_structure import folder_role, is_service_folder, client_name, order_location
from event_folder_undo import assert_unlocked, guard_database

SNAPSHOT = ".order.json"  # Read-only compatibility with the previous export.
CARD = document.DOCUMENT
SYNC_LOCK = threading.Lock()


class OrderConflict(ValueError):
    pass


class OrderStore:
    def __init__(self, root, data_dir, labels, *, database_only=True):
        self.root = Path(root)
        self.database_only = database_only
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
                if "registered" not in columns:
                    db.execute("ALTER TABLE orders ADD COLUMN registered INTEGER NOT NULL DEFAULT 1")
                if "financial_status" not in columns:
                    db.execute("ALTER TABLE orders ADD COLUMN financial_status TEXT NOT NULL DEFAULT 'unspecified'")
                    db.execute("""UPDATE orders SET financial_status=CASE WHEN status='payment' THEN 'payment' ELSE 'unspecified' END,
                        status=CASE WHEN status='payment' THEN 'unspecified' ELSE status END,
                        revision=revision+CASE WHEN registered=1 THEN 1 ELSE 0 END""")
            with db:
                if self.database_only:
                    import local_metadata
                    local_metadata.schema(db)
                    for table in ("orders","folder_notes","client_activity","object_activity","metadata_records"):
                        local_metadata.audit(db,table)
                    db.commit()
                yield db
        finally:
            db.close()

    def path(self, relative):
        if not isinstance(relative, str) or not relative or relative == ".":
            raise ValueError("Выберите папку заказа")
        parts = Path(relative).parts
        if Path(relative).is_absolute() or any(part.startswith(".") for part in parts):
            raise ValueError("Выберите папку внутри клиента")
        if is_service_folder(relative):
            raise ValueError("Служебные папки с # не являются заказами")
        return Path(*parts).as_posix()

    def target(self, relative):
        relative = self.path(relative)
        guard_database(self.database, relative)
        target = self.root / relative
        if any((self.root / Path(*Path(relative).parts[:i + 1])).is_symlink() for i in range(len(Path(relative).parts))):
            raise ValueError("Символические ссылки не редактируются")
        if not target.is_dir():
            raise FileNotFoundError("Папка заказа недоступна. Данные сохранены в базе; проверьте iCloud и путь заказа.")
        return target

    def record(self,row,db):
        if row is None:
            return None
        result = dict(row)
        result["registered"] = bool(result["registered"])
        result["client"] = client_name(result["path"])
        result.update(order_location(result["path"]))
        result["work_supplier"] = work_orders.supplier_name(result["path"])
        result["work_supplier_color"] = work_orders.supplier_color(db, result["path"]) if result["work_supplier"] else None
        result["profit"] = result["amount"] - result["costs"] if result["amount"] is not None and result["costs"] is not None else None
        result["debt"] = result["amount"] - result["paid"] if result["amount"] is not None and result["paid"] is not None else None
        result["extra_blocks"] = json.loads(result["extra_blocks"])
        result["todo_items"] = document.read_todos(result["extra_blocks"])
        result["purchase_items"] = document.read_purchases(result["extra_blocks"])
        result["is_favorite"] = document.read_favorite(result["extra_blocks"])
        result["is_flagged"] = document.read_flag(result["extra_blocks"])
        result["deadline_weeks"] = order_deadlines.read(result["extra_blocks"])
        result["deadline_comments"] = order_deadlines.read_comments(result["extra_blocks"])
        result["can_group_supplier_orders"] = work_orders.direct_order(result["path"])
        exported_revision, export_format = result.pop("exported_revision"), result.pop("export_format")
        result["sync_pending"] = result["revision"] != exported_revision or (result["registered"] and export_format < document.FORMAT)
        if self.database_only:
            result.update(sync_pending=False,sync_error="",storage="database")
        return result

    def get(self, relative, *, include_unregistered=False):
        if is_service_folder(relative) or not self.database.exists():
            return None
        with self.connect() as db:
            assert_unlocked(db, relative)
            row = db.execute("SELECT * FROM orders WHERE path=?", (relative,)).fetchone()
            return self.record(row, db) if row and (include_unregistered or row["registered"]) else None

    def list(self, *, include_unregistered=False):
        if not self.database.exists():
            return []
        with self.connect() as db:
            return [self.record(row, db) for row in db.execute("SELECT * FROM orders ORDER BY updated DESC, path").fetchall()
                    if not any(part.startswith('.') for part in Path(row['path']).parts)
                    and not is_service_folder(row["path"]) and (include_unregistered or row["registered"])]

    def pending_unregistrations(self):
        return [{"path": record["path"], "sync_error": record["sync_error"]}
                for record in self.list(include_unregistered=True) if not record["registered"] and record["sync_pending"]]

    def discard_service_orders(self):
        """Service-folder registrations were test data; folder files are authoritative."""
        if not self.database.exists():
            return 0
        with self.connect() as db:
            paths = [row["path"] for row in db.execute("SELECT path FROM orders") if is_service_folder(row["path"])]
            db.executemany("DELETE FROM orders WHERE path=?", [(path,) for path in paths])
        return len(paths)

    def add(self, relative, initial):
        relative = self.path(relative)
        self.target(relative)
        self.require_order_folder(relative)
        initial = document.split_statuses(initial, self.labels)
        status, note = initial.get("status", "new"), initial.get("note", "")
        financial_status = initial.get("financial_status", "unspecified")
        if not isinstance(status, str) or status not in self.labels or not isinstance(note, str):
            raise ValueError("Некорректный статус или заметка")
        with self.connect() as db:
            assert_unlocked(db, relative)
            db.execute("""INSERT INTO orders
                (path,id,title,status,financial_status,note,amount,costs,paid,revision,updated,extra_blocks)
                VALUES (?,?,?,?,?,?,?,?,?,1,?,?) ON CONFLICT(path) DO UPDATE SET
                id=excluded.id,title=excluded.title,status=excluded.status,note=excluded.note,
                financial_status=excluded.financial_status,
                amount=excluded.amount,costs=excluded.costs,paid=excluded.paid,registered=1,
                revision=orders.revision+1,updated=excluded.updated,extra_blocks=excluded.extra_blocks,sync_error=''
                WHERE orders.registered=0""", (relative, str(uuid.uuid4()), initial.get("title", Path(relative).name),
                status, financial_status, note, initial.get("amount"), initial.get("costs"), initial.get("paid"), time.time(),
                json.dumps(initial.get("extra_blocks", {}), ensure_ascii=False)))
        return self.get(relative)

    def require_order_folder(self, relative):
        role = folder_role(self.root, relative)
        if not role["canRegisterOrder"]:
            raise ValueError(role["registrationHint"])
        return role

    def save(self, payload):
        relative = self.path(payload.get("path"))
        status, note, title = payload.get("status"), payload.get("note"), payload.get("title")
        financial_status = payload.get("financial_status")
        if "financial_status" in payload and (not isinstance(financial_status, str) or financial_status not in document.FINANCIAL_STATUS_LABELS):
            raise ValueError("Некорректный финансовый статус")
        if not isinstance(status, str) or status not in self.labels or not isinstance(note, str) or len(note) > 100_000:
            raise ValueError("Некорректный статус или заметка")
        if not isinstance(title, str) or not title.strip() or len(title) > 500 or any(c in title for c in "\r\n\x00"):
            raise ValueError("Укажите название одной строкой")
        values = [money(payload.get(key)) for key in ("amount", "costs", "paid")]
        revision = payload.get("revision")
        if type(revision) is not int:
            raise ValueError("Не указана версия заказа. Откройте заказ заново.")
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            assert_unlocked(db, relative)
            current = db.execute("SELECT extra_blocks FROM orders WHERE path=? AND revision=? AND registered=1", (relative, revision)).fetchone()
            if current is None:
                raise OrderConflict("Заказ изменён в другой вкладке. Откройте его заново перед сохранением.")
            blocks = json.loads(current["extra_blocks"])
            if "purchase_items" in payload:
                if document.read_purchases(blocks) is None:
                    raise ValueError("Прежние записи закупок и затрат сохранены. Проверь раздел в !.txt заказа")
                blocks = document.write_purchases(blocks, payload["purchase_items"])
            if "todo_items" in payload:
                blocks = document.write_todos(blocks, payload["todo_items"])
                # Update phone identities in this same transaction, including an
                # empty list. A deletion/re-add between syncs must get a new ID.
                if db.execute("SELECT 1 FROM sqlite_master WHERE name='mobile_tasks'").fetchone():
                    from mobile_sync import reconcile_tasks
                    row = db.execute("SELECT id FROM orders WHERE path=?", (relative,)).fetchone()
                    previous = db.execute("SELECT items FROM mobile_tasks WHERE order_id=?", (row["id"],)).fetchone()
                    if previous:
                        items = reconcile_tasks(json.loads(previous[0]), document.read_todos(blocks))
                        db.execute("UPDATE mobile_tasks SET items=? WHERE order_id=?", (json.dumps(items, ensure_ascii=False), row["id"]))
            result = db.execute("""UPDATE orders SET title=?,status=?,financial_status=COALESCE(?,financial_status),note=?,amount=?,costs=?,paid=?,
                extra_blocks=?,revision=revision+1,updated=?,sync_error='' WHERE path=? AND revision=? AND registered=1""",
                (title.strip(), status, financial_status, note, *values, json.dumps(blocks, ensure_ascii=False), time.time(), relative, revision))
            if not result.rowcount:
                raise OrderConflict("Заказ изменён в другой вкладке. Откройте его заново перед сохранением.")
        return self.get(relative)

    def save_status(self, payload):
        """Change only production status using the version shown in the list."""
        relative = self.path(payload.get("path"))
        status, revision = payload.get("status"), payload.get("revision")
        if not isinstance(status, str) or status not in self.labels:
            raise ValueError("Некорректный производственный статус")
        if type(revision) is not int:
            raise ValueError("Не указана версия заказа. Обнови список заказов.")
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            assert_unlocked(db, relative)
            result = db.execute("""UPDATE orders SET status=?,revision=revision+1,updated=?,sync_error=''
                WHERE path=? AND revision=? AND registered=1""", (status, time.time(), relative, revision))
            if not result.rowcount:
                raise OrderConflict("Заказ изменён в другой вкладке. Проверь актуальный статус и выбери его заново.")
        return self.get(relative)

    def save_deadline_week(self, payload):
        """Change one week's mark without moving the order in the sorted list."""
        return self._save_extra_block(payload, lambda blocks: order_deadlines.write(blocks, payload.get("week"), payload.get("selected")), update_time=False)

    def save_deadline_comment(self, payload):
        return self._save_extra_block(payload, lambda blocks: order_deadlines.write_comment(blocks, payload.get("week"), payload.get("comment")), update_time=False)

    def save_flag(self, payload):
        return self._save_extra_block(payload, lambda blocks: document.write_flag(blocks, payload.get("is_flagged")), update_time=False)

    def _save_extra_block(self, payload, write, *, update_time=True):
        relative = self.path(payload.get("path"))
        revision = payload.get("revision")
        identity = payload.get("id")
        if not isinstance(identity, str) or not identity:
            raise ValueError("Не указан идентификатор заказа. Обнови список заказов.")
        if type(revision) is not int:
            raise ValueError("Не указана версия заказа. Обнови список заказов.")
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            assert_unlocked(db, relative)
            row = db.execute("SELECT extra_blocks FROM orders WHERE path=? AND id=? AND revision=? AND registered=1",
                             (relative, identity, revision)).fetchone()
            if row is None:
                raise OrderConflict("Заказ изменён в другой вкладке. Проверь актуальные данные и повтори изменение.")
            blocks = write(json.loads(row["extra_blocks"]))
            db.execute("""UPDATE orders SET extra_blocks=?,revision=revision+1,updated=CASE WHEN ? THEN ? ELSE updated END,sync_error=''
                WHERE path=? AND id=? AND revision=? AND registered=1""",
                (json.dumps(blocks, ensure_ascii=False), update_time, time.time(), relative, identity, revision))
        return self.get(relative)

    def save_favorite(self, payload):
        """Change just the star, without reading documents or replacing card fields."""
        relative = self.path(payload.get("path"))
        revision = payload.get("revision")
        if type(revision) is not int:
            raise ValueError("Не указана версия заказа. Обнови список заказов.")
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            assert_unlocked(db, relative)
            row = db.execute("SELECT extra_blocks FROM orders WHERE path=? AND revision=? AND registered=1",
                             (relative, revision)).fetchone()
            if row is None:
                raise OrderConflict("Заказ изменён в другой вкладке. Обнови список перед сменой избранного.")
            blocks = document.write_favorite(json.loads(row["extra_blocks"]), payload.get("is_favorite"))
            db.execute("""UPDATE orders SET extra_blocks=?,revision=revision+1,updated=?,sync_error=''
                WHERE path=? AND revision=? AND registered=1""",
                (json.dumps(blocks, ensure_ascii=False), time.time(), relative, revision))
        return self.get(relative)

    def work_links(self, relative):
        relative = self.path(relative)
        if not work_orders.direct_order(relative):
            raise ValueError("Подборка доступна в заказе непосредственно внутри # work")
        with self.connect() as db:
            assert_unlocked(db, relative)
            parent = db.execute("SELECT * FROM orders WHERE path=? AND registered=1", (relative,)).fetchone()
            if parent is None:
                raise FileNotFoundError("Сначала добавь заказ в производство")
            identities = work_orders.read_links(json.loads(parent["extra_blocks"]))
            rows = {row["id"]: row for row in db.execute("SELECT id,path,title,status,registered FROM orders")}
            candidates = [work_orders.summary(row) for row in rows.values() if row["registered"] and work_orders.supplier_order(row["path"])]
            candidates.sort(key=lambda item: (item["supplier"].casefold(), item["title"].casefold(), item["path"]))
            items = [work_orders.summary(rows[identity]) if identity in rows else {
                "id": identity, "path": None, "title": "Заказ недоступен", "supplier": "", "status": None, "registered": False}
                for identity in identities or []]
            return {"path": relative, "revision": parent["revision"], "linked_ids": identities, "items": items, "candidates": candidates}

    def save_work_links(self, payload):
        relative = self.path(payload.get("path"))
        identities = work_orders.checked_ids(payload.get("order_ids"))
        if not work_orders.direct_order(relative):
            raise ValueError("Подборка доступна в заказе непосредственно внутри # work")
        revision = payload.get("revision")
        if type(revision) is not int:
            raise ValueError("Не указана версия заказа. Открой его заново")
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            assert_unlocked(db, relative)
            parent = db.execute("SELECT extra_blocks FROM orders WHERE path=? AND revision=? AND registered=1", (relative, revision)).fetchone()
            if parent is None:
                raise OrderConflict("Заказ изменён в другой вкладке. Открой его заново перед изменением подборки")
            blocks = json.loads(parent["extra_blocks"])
            previous = work_orders.read_links(blocks)
            updated = work_orders.write_links(blocks, identities)
            for identity in identities:
                target = db.execute("SELECT path,registered FROM orders WHERE id=?", (identity,)).fetchone()
                if target:
                    assert_unlocked(db, target["path"])
                if identity not in previous and (not target or not target["registered"] or not work_orders.supplier_order(target["path"])):
                    raise ValueError("Добавлять можно только зарегистрированные заказы из разделов поставщиков")
            db.execute("""UPDATE orders SET extra_blocks=?,revision=revision+1,updated=?,sync_error=''
                WHERE path=? AND revision=? AND registered=1""",
                (json.dumps(updated, ensure_ascii=False), time.time(), relative, revision))
        return self.get(relative)

    def remove(self, payload):
        if payload.get("confirmed") is not True:
            raise ValueError("Подтвердите снятие регистрации заказа")
        relative = self.path(payload.get("path"))
        revision = payload.get("revision")
        if type(revision) is not int:
            raise ValueError("Откройте заказ заново перед снятием регистрации")
        with self.connect() as db:
            assert_unlocked(db, relative)
            result = db.execute("""UPDATE orders SET registered=0,revision=revision+1,updated=?,sync_error=''
                WHERE path=? AND revision=? AND registered=1""", (time.time(), relative, revision))
            if not result.rowcount:
                raise OrderConflict("Заказ изменён или уже убран из списка. Обновите данные перед подтверждением.")
            if self.database_only:
                import folder_notes
                folder_notes.schema(db)
                body = self.record(db.execute("SELECT * FROM orders WHERE path=?",(relative,)).fetchone(), db)
                db.execute("""INSERT INTO folder_notes VALUES (?,?,?,?,1,1,'database',?,'')
                    ON CONFLICT(path) DO UPDATE SET document=excluded.document,revision=folder_notes.revision+1,updated=excluded.updated""",
                    (relative,str(uuid.uuid4()),"",json.dumps(body,ensure_ascii=False),time.time()))
        return self.get(relative, include_unregistered=True)

    def atomic_write(self, target, body):
        document.atomic_write(target, body)

    def sync(self):
        if self.database_only:
            with self.connect() as db:
                db.execute("UPDATE orders SET exported_revision=revision,export_format=?,sync_error='' WHERE exported_revision!=revision OR export_format<? OR sync_error!=''", (document.FORMAT,document.FORMAT))
            return
        if not SYNC_LOCK.acquire(blocking=False):
            return
        try:
            for record in self.list(include_unregistered=True):
                if not record["sync_pending"]:
                    continue
                error = ""
                phase = "Доступ к папке"
                try:
                    folder = self.target(record["path"])
                    phase = "Чтение карточки"
                    existing = document.load(folder, self.labels)
                    record["extra_blocks"].update({key: value for key, value in existing.get("extra_blocks", {}).items()
                        if key not in {document.TODO_BLOCK, document.PURCHASE_BLOCK, document.FAVORITE_BLOCK, order_deadlines.BLOCK} or key not in record["extra_blocks"]})
                    if existing.get("schema", 0) < document.FORMAT:
                        phase = "Сохранение прежней карточки в историю"
                        document.archive_current(folder)
                    phase = "Запись карточки"
                    self.atomic_write(folder / CARD, document.render(record, self.labels))
                    phase = "Архив прежних файлов карточки"
                    document.archive_legacy(folder)
                except (OSError, ValueError) as problem:
                    error = phase + ": " + document.icloud_access.sync_error(problem)
                with self.connect() as db:
                    db.execute("""UPDATE orders SET sync_error=?,exported_revision=CASE WHEN ?='' THEN ?
                        ELSE exported_revision END, export_format=CASE WHEN ?='' THEN ? ELSE export_format END,
                        extra_blocks=CASE WHEN ?='' THEN ? ELSE extra_blocks END WHERE path=? AND revision=?""",
                        (error, error, record["revision"], error, document.FORMAT, error,
                         json.dumps(record["extra_blocks"], ensure_ascii=False), record["path"], record["revision"]))
        finally:
            SYNC_LOCK.release()

    def import_folder(self, relative, fallback=None):
        if self.database_only:
            with SYNC_LOCK:
                return self._import_folder(relative,fallback)
        return self._import_folder(relative,fallback)

    def _import_folder(self, relative, fallback=None):
        folder = self.target(relative)
        self.require_order_folder(relative)
        previous = self.get(relative, include_unregistered=True)
        if self.database_only and previous:
            if not previous["registered"]:
                with self.connect() as db:
                    db.execute("BEGIN IMMEDIATE")
                    assert_unlocked(db,relative)
                    import folder_notes
                    folder_notes.schema(db)
                    draft = db.execute("SELECT document FROM folder_notes WHERE path=?",(relative,)).fetchone()
                    body = json.loads(draft[0]) if draft else previous
                    db.execute("UPDATE orders SET registered=1,note=?,extra_blocks=?,revision=revision+1,updated=? WHERE path=?",
                        (body.get("note",previous["note"]),json.dumps(body.get("extra_blocks",previous["extra_blocks"]),ensure_ascii=False),time.time(),relative))
            return self.get(relative)
        if previous and not previous["registered"] and previous["sync_pending"]:
            with self.connect() as db:
                assert_unlocked(db, relative)
                db.execute("UPDATE orders SET registered=1,revision=revision+1,updated=?,sync_error='' WHERE path=? AND registered=0",
                           (time.time(), relative))
            return self.get(relative)
        if self.database_only:
            from folder_notes import FolderNotes
            from local_metadata import MetadataStore
            with FolderNotes(self).connect() as db:
                draft = db.execute("SELECT document FROM folder_notes WHERE path=?", (relative,)).fetchone()
            initial = json.loads(draft[0]) if draft else MetadataStore(self).card(folder)
            initial = initial or fallback or {"status":"new","note":""}
        else:
            initial = document.load(folder, self.labels) or fallback or {"status": "new", "note": ""}
        if initial.get("id"):
            self.restore(relative, initial)
        else:
            self.add(relative, initial)
        return self.get(relative)

    def restore(self, relative, snapshot):
        """Import only missing records. Existing database values always win."""
        relative = self.path(relative)
        self.target(relative)
        self.require_order_folder(relative)
        if not isinstance(snapshot, dict) or snapshot.get("schema") not in (1, 2, document.FORMAT):
            raise ValueError("Неподдерживаемый формат карточки заказа")
        snapshot = document.split_statuses(snapshot, self.labels)
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
        # A copy is distinct only while the original folder is still present.
        # A missing original may be a Finder rename: keep its queued data and
        # require a separate, journalled repair instead of manufacturing a twin.
        with self.connect() as db:
            assert_unlocked(db, relative)
            archived = db.execute("SELECT 1 FROM sqlite_master WHERE name='order_duplicate_archive'").fetchone()
            if archived and db.execute("SELECT 1 FROM order_duplicate_archive WHERE id=? AND state='archived'", (identity,)).fetchone():
                raise OrderConflict("Карточка относится к сохранённому дублю. Нужна отдельная проверка истории; повторное добавление остановлено.")
            existing = db.execute("SELECT path FROM orders WHERE id=? AND path<>?", (identity, relative)).fetchone()
            if existing:
                try:
                    self.target(existing["path"])
                except FileNotFoundError:
                    raise OrderConflict("Этот заказ уже есть в базе по прежнему пути «" + existing["path"] +
                                        "». Исходная папка недоступна; возможно, её переименовали. Дубль не создан: нужна отдельная перепривязка с сохранением данных.")
                identity = str(uuid.uuid4())
            db.execute("""INSERT INTO orders
                (path,id,title,status,financial_status,note,amount,costs,paid,revision,exported_revision,updated,extra_blocks)
                VALUES (?,?,?,?,?,?,?,?,?,?,0,?,?) ON CONFLICT(path) DO UPDATE SET
                id=excluded.id,title=excluded.title,status=excluded.status,note=excluded.note,
                financial_status=excluded.financial_status,
                amount=excluded.amount,costs=excluded.costs,paid=excluded.paid,registered=1,
                revision=MAX(orders.revision+1,excluded.revision),updated=excluded.updated,
                extra_blocks=excluded.extra_blocks,sync_error='' WHERE orders.registered=0""", (relative, identity, title, status, snapshot.get("financial_status", "unspecified"), note,
                *values, revision, time.time(), json.dumps(snapshot.get("extra_blocks", {}), ensure_ascii=False)))

    def discover(self, read_status, progress):
        """Explicit background scan: directory names and metadata, never attachments."""
        if not self.root.is_dir():
            raise FileNotFoundError("Корень документов недоступен")
        for current, dirs, names in os.walk(self.root, followlinks=False,
                onerror=lambda error: progress["errors"].append(str(error))):
            folder = Path(current)
            dirs[:] = [name for name in dirs if not name.startswith(".")
                       and not is_service_folder((folder / name).relative_to(self.root).as_posix())
                       and not (folder / name).is_symlink()]
            progress["folders"] += 1
            relative = folder.relative_to(self.root).as_posix()
            try:
                role = folder_role(self.root, relative)
                if role["folderKind"] in ("order", "event"):
                    dirs[:] = []
                if not role["canRegisterOrder"] or self.get(relative, include_unregistered=True):
                    continue
                if not any(name in names for name in (CARD, SNAPSHOT, *document.LEGACY_STATUSES)):
                    continue
                if document.load(folder, self.labels).get("registered") is False:
                    continue
                self.import_folder(relative)
                progress["added"] += 1
            except (OSError, ValueError, TypeError, AttributeError) as error:
                progress["errors"].append(relative + ": " + str(error))
