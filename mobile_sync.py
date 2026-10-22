"""Offline phone companion: immutable operations, durable receipts, read-only catalog.

SQLite stays on the Mac. Nothing in the document root is created until enabled.
The phone never edits !.txt or a file-comment document directly.
"""
import collections
import hashlib
import json
import math
import os
import threading
import time
import uuid
from pathlib import Path, PurePosixPath

import file_comments
from event_folder_undo import assert_unlocked
import order_document as document

RUN_LOCK = threading.Lock()
DIRECTORY = ".mobile-sync"
MAX_OPERATION = 64 * 1024


class MobileConflict(ValueError):
    pass


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def identifier(value):
    try:
        valid = isinstance(value, str) and str(uuid.UUID(value)) == value
    except (ValueError, TypeError, AttributeError):
        valid = False
    if not valid:
        raise ValueError("Некорректный идентификатор обмена")
    return value


def regular(path):
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise ValueError("Служебный файл обмена должен быть обычным файлом")
    return path


def read_json(path, limit=MAX_OPERATION):
    regular(path)
    if path.stat().st_size > limit:
        raise ValueError("Служебный файл обмена слишком большой")
    return json.loads(path.read_bytes())


def write_json(path, value):
    regular(path)
    body = encode(value)
    if not path.exists() or path.read_text() != body:
        document.atomic_write(path, body)


def reconcile_tasks(previous, current):
    """Keep identities for unambiguous text matches; never guess after a rename.

    Duplicate texts get new identities when their group changes. An offline toggle
    then conflicts rather than ticking a potentially different task.
    """
    if current is None:
        return None
    old_groups, new_groups = collections.defaultdict(list), collections.defaultdict(list)
    for item in previous or []:
        old_groups[item["text"]].append(item)
    for item in current:
        new_groups[item["text"]].append(item)
    counters = collections.Counter()
    result = []
    for item in current:
        text = item["text"]
        old, group = old_groups[text], new_groups[text]
        same_group = [(x["text"], x["done"]) for x in old] == [(x["text"], x["done"]) for x in group]
        keep = len(old) == len(group) == 1 or same_group
        index = counters[text]
        counters[text] += 1
        identity = old[index]["id"] if keep and index < len(old) else str(uuid.uuid4())
        version = old[index].get("version", 1) if keep and index < len(old) else 1
        if keep and index < len(old) and old[index]["done"] != item["done"]:
            version += 1
        result.append({**item, "id": identity, "version": version})
    return result


def file_token(path):
    stat = path.stat()
    return hashlib.sha256(f"{stat.st_dev}:{stat.st_ino}:{stat.st_size}:{stat.st_mtime_ns}".encode()).hexdigest()


class MobileBridge:
    def __init__(self, store):
        self.store = store
        self.folder = store.root / DIRECTORY
        with store.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS mobile_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            db.execute("""CREATE TABLE IF NOT EXISTS mobile_operations (
                id TEXT PRIMARY KEY, digest TEXT NOT NULL, payload TEXT NOT NULL,
                status TEXT NOT NULL, result TEXT NOT NULL, prepared TEXT NOT NULL DEFAULT '{}')""")
            db.execute("""CREATE TABLE IF NOT EXISTS mobile_tasks (
                order_id TEXT PRIMARY KEY, items TEXT NOT NULL)""")
            db.execute("""CREATE TABLE IF NOT EXISTS mobile_files (
                order_id TEXT PRIMARY KEY, scanned REAL NOT NULL, items TEXT NOT NULL)""")

    @staticmethod
    def get_meta(db, key, default=""):
        row = db.execute("SELECT value FROM mobile_meta WHERE key=?", (key,)).fetchone()
        return row[0] if row else default

    @staticmethod
    def put_meta(db, key, value):
        db.execute("INSERT OR REPLACE INTO mobile_meta VALUES (?,?)", (key, str(value)))

    def configure(self, enabled):
        if self.store.database_only and enabled:
            raise ValueError("Обмен с iPhone отложен; очередь сохранена")
        if type(enabled) is not bool:
            raise ValueError("Укажите, включён ли обмен")
        with self.store.connect() as db:
            self.put_meta(db, "enabled", int(enabled))
        return self.status()

    def status(self):
        with self.store.connect() as db:
            values = dict(db.execute("SELECT key,value FROM mobile_meta"))
            conflicts = db.execute("SELECT COUNT(*) FROM mobile_operations WHERE status='conflict'").fetchone()[0]
        return {"enabled": not self.store.database_only and values.get("enabled") == "1", "paused":self.store.database_only, "running": RUN_LOCK.locked(),
                "last_sync": float(values.get("last_sync", 0)), "error": values.get("error", ""),
                "orders": int(values.get("orders", 0)), "conflicts": conflicts}

    def prepare(self):
        if not self.store.root.is_dir():
            raise FileNotFoundError("Корень документов недоступен; обмен будет повторён")
        for path in (self.folder, self.folder / ".inbox", self.folder / ".receipts"):
            if path.is_symlink() or (path.exists() and not path.is_dir()):
                raise ValueError("Каталог обмена должен быть обычной папкой")
            path.mkdir(exist_ok=True)
        identity_file = self.folder / ".identity.json"
        with self.store.connect() as db:
            root_id = self.get_meta(db, "root_id")
            if identity_file.exists():
                identity = read_json(identity_file)
                disk_id = identifier(identity.get("root_id"))
                if identity.get("schema") != 1 or (root_id and root_id != disk_id):
                    raise MobileConflict("Выбрана другая папка обмена; существующие данные сохранены")
                root_id = disk_id
            else:
                root_id = root_id or str(uuid.uuid4())
                write_json(identity_file, {"schema": 1, "root_id": root_id})
            self.put_meta(db, "root_id", root_id)
        return root_id

    def target_file(self, relative, order_path):
        if (not isinstance(relative, str) or not relative or "\x00" in relative
                or PurePosixPath(relative).is_absolute() or PurePosixPath(relative).as_posix() != relative
                or any(part.startswith(".") for part in relative.split("/"))
                or not relative.startswith(order_path + "/")
                or Path(relative).name in (document.DOCUMENT, *document.LEGACY_DOCUMENTS)):
            raise MobileConflict("Файл вне выбранного заказа или является служебным")
        target = self.store.root
        for component in relative.split("/"):
            target = target / component
            if target.is_symlink():
                raise MobileConflict("Символические ссылки не поддерживаются")
        if not target.is_file():
            self.store.target(order_path)
            if target.with_name("." + target.name + ".icloud").exists():
                raise FileNotFoundError("Файл пока не загружен из iCloud; обмен будет повторён")
            raise MobileConflict("Файл удалён или переименован; комментарий сохранён в обмене")
        return target

    def tasks(self, db, record):
        saved = db.execute("SELECT items FROM mobile_tasks WHERE order_id=?", (record["id"],)).fetchone()
        items = reconcile_tasks(json.loads(saved[0]) if saved else [], record["todo_items"])
        db.execute("INSERT OR REPLACE INTO mobile_tasks VALUES (?,?)", (record["id"], encode(items)))
        return items

    def validate(self, operation, root_id):
        if not isinstance(operation, dict) or operation.get("schema") != 1 or operation.get("root_id") != root_id:
            raise ValueError("Неподдерживаемый обмен или другая папка документов")
        for key in ("id", "order_id", "device_id"):
            identifier(operation.get(key))
        if type(operation.get("sequence")) is not int or operation["sequence"] < 1:
            raise ValueError("Некорректный номер операции")
        if operation.get("kind") not in {"order_comment", "file_comment", "todo_add", "todo_set"}:
            raise ValueError("Неизвестное мобильное действие")
        if operation.get("depends_on") is not None:
            identifier(operation["depends_on"])
            if operation["depends_on"] == operation["id"]:
                raise ValueError("Действие не может зависеть от самого себя")
        created = operation.get("created")
        if type(created) not in (float, int) or not math.isfinite(created) or not 0 < created < 100_000_000_000:
            raise ValueError("Некорректное время операции")
        if operation["kind"] != "todo_set":
            text = operation.get("text")
            maximum = 1000 if operation["kind"] == "todo_add" else 5000
            if not isinstance(text, str) or not text.strip() or len(text) > maximum or "\x00" in text:
                raise ValueError("Пустой или слишком длинный текст")
        if operation["kind"].startswith("todo_"):
            identifier(operation.get("task_id"))
        if operation["kind"] == "todo_set":
            if (type(operation.get("done")) is not bool or type(operation.get("base_done")) is not bool
                    or not isinstance(operation.get("base_text"), str)
                    or type(operation.get("base_version")) is not int or operation["base_version"] < 1):
                raise ValueError("Не указана исходная версия задачи")

    def apply(self, operation, raw, root_id):
        self.validate(operation, root_id)
        digest = hashlib.sha256(raw).hexdigest()
        op_id = operation["id"]
        # File comments use a persistent prepared record across the filesystem/DB
        # boundary. The shared lock also excludes desktop edits and file trash.
        with file_comments.LOCK, self.store.connect() as db:
            previous = db.execute("SELECT * FROM mobile_operations WHERE id=?", (op_id,)).fetchone()
            if previous and previous["digest"] != digest:
                raise MobileConflict("Идентификатор уже использован для другого содержимого")
            if previous and previous["status"] != "prepared":
                return json.loads(previous["result"])
            receipt_file = self.folder / ".receipts" / f".{op_id}.json"
            if not previous and receipt_file.exists():
                receipt = read_json(receipt_file)
                if receipt.get("digest") != digest or receipt.get("root_id") != root_id or receipt.get("status") not in ("applied", "conflict"):
                    raise MobileConflict("Подтверждение не соответствует сохранённому действию")
                db.execute("INSERT INTO mobile_operations (id,digest,payload,status,result) VALUES (?,?,?,?,?)",
                           (op_id, digest, raw.decode(), receipt["status"], encode(receipt)))
                return receipt
            # Read any cloud receipt before acquiring a writer lock, then check
            # the ledger again in case another process applied the same action.
            db.execute("BEGIN IMMEDIATE")
            previous = db.execute("SELECT * FROM mobile_operations WHERE id=?", (op_id,)).fetchone()
            if previous and previous["digest"] != digest:
                raise MobileConflict("Идентификатор уже использован для другого содержимого")
            if previous and previous["status"] != "prepared":
                return json.loads(previous["result"])
            dependency = operation.get("depends_on")
            if dependency:
                parent = db.execute("SELECT status FROM mobile_operations WHERE id=?", (dependency,)).fetchone()
                if not parent or parent[0] == "prepared":
                    return None  # iCloud may deliver a dependent file first.
            result = {"id": op_id, "digest": digest, "root_id": root_id, "status": "applied", "message": "Применено на Mac"}
            try:
                if dependency and parent[0] != "applied":
                    raise MobileConflict("Предыдущее действие требует разбора; новый ввод сохранён")
                row = db.execute("SELECT * FROM orders WHERE id=? AND registered=1", (operation["order_id"],)).fetchone()
                if not row:
                    raise MobileConflict("Заказ убран из списка или имеет другой идентификатор")
                record = self.store.record(row, db)
                assert_unlocked(db, record["path"])
                if operation["kind"] == "file_comment":
                    self.apply_file(db, operation, raw, digest, record, previous)
                else:
                    self.apply_order(db, operation, record)
            except MobileConflict as error:
                result.update(status="conflict", message=str(error))
            db.execute("""INSERT INTO mobile_operations (id,digest,payload,status,result) VALUES (?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET status=excluded.status,result=excluded.result""",
                       (op_id, digest, raw.decode(), result["status"], encode(result)))
            return result

    def apply_order(self, db, operation, record):
        kind = operation["kind"]
        if kind == "order_comment":
            note = record["note"] + ("\n\n" if record["note"] else "") + operation["text"].strip()
            if len(note) > 100_000:
                raise MobileConflict("В заметке нет места; новый комментарий сохранён в обмене")
            db.execute("UPDATE orders SET note=?,revision=revision+1,updated=?,sync_error='' WHERE id=?",
                       (note, time.time(), record["id"]))
            return
        items = self.tasks(db, record)
        if items is None:
            raise MobileConflict("Прежний раздел задач содержит произвольный текст; он сохранён без изменений")
        index = next((i for i, item in enumerate(items) if item["id"] == operation["task_id"]), None)
        if kind == "todo_add":
            if index is not None:
                raise MobileConflict("Идентификатор задачи уже существует")
            new = document.validate_todos([{"text": operation["text"], "done": False}])[0]
            if len(items) >= 200:
                raise MobileConflict("В заказе уже 200 задач; новая задача сохранена в обмене")
            items.append({**new, "id": operation["task_id"], "version": 1})
        else:
            if index is None or items[index]["text"] != operation["base_text"]:
                raise MobileConflict("Задача удалена, переименована или неоднозначна; отметка не применена")
            if items[index]["done"] == operation["done"]:
                return
            if items[index]["done"] != operation["base_done"] or items[index]["version"] != operation["base_version"]:
                raise MobileConflict("Отметка задачи изменилась; обе версии сохранены")
            items[index]["done"] = operation["done"]
            items[index]["version"] += 1
        blocks = document.write_todos(record["extra_blocks"], items)
        db.execute("UPDATE orders SET extra_blocks=?,revision=revision+1,updated=?,sync_error='' WHERE id=?",
                   (encode(blocks), time.time(), record["id"]))
        db.execute("INSERT OR REPLACE INTO mobile_tasks VALUES (?,?)", (record["id"], encode(items)))

    def apply_file(self, db, operation, raw, digest, record, previous):
        # No SQLite write lock may be held across iCloud filesystem access.
        # The prepared intent bridges the two stores without blocking card saves.
        db.commit()
        target = self.target_file(operation.get("file_path"), record["path"])
        current = file_comments.read(target)
        if previous:
            prepared = json.loads(previous["prepared"])
            _, key, folder, comment_path = file_comments.paths(target)
            history = folder / ".history" / ("." + key) / ("." + prepared["after_revision"] + ".txt")
            if history.parent.is_symlink() or history.parent.parent.is_symlink():
                raise MobileConflict("История комментария заменена ссылкой; действие сохранено для разбора")
            # Recovery after a successful atomic write but before SQLite commit.
            if current["revision"] == prepared["after_revision"] or (not history.is_symlink() and history.is_file()
                    and hashlib.sha256(history.read_bytes()).hexdigest() == prepared["after_revision"]):
                db.execute("DELETE FROM mobile_files WHERE order_id=?", (record["id"],))
                return
            if current["revision"] != prepared["before_revision"]:
                raise MobileConflict("Комментарий изменился после прерванной записи; новый текст сохранён")
        else:
            if file_token(target) != operation.get("file_token"):
                raise MobileConflict("Файл изменён или заменён с момента получения; комментарий сохранён отдельно")
            comment = current["comment"] + ("\n\n" if current["comment"] else "") + operation["text"].strip()
            if len(comment) > file_comments.MAX_COMMENT:
                raise MobileConflict("Комментарий слишком длинный; добавление сохранено в обмене")
            name = file_comments.paths(target)[0]
            body = "КОММЕНТАРИЙ К ФАЙЛУ\nФайл: " + json.dumps(name, ensure_ascii=False) + "\nФормат: 1\n\n[Комментарий]\n> " + comment.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\n> ") + "\n"
            prepared = {"comment": comment, "before_revision": current["revision"],
                        "after_revision": hashlib.sha256(body.encode()).hexdigest()}
            db.execute("INSERT INTO mobile_operations (id,digest,payload,status,result,prepared) VALUES (?,?,?,'prepared','{}',?)",
                       (operation["id"], digest, raw.decode(), encode(prepared)))
            db.commit()  # Durable intent BEFORE changing a comment document.
        if file_token(target) != operation.get("file_token"):
            raise MobileConflict("Оригинал изменился; добавление комментария требует разбора")
        file_comments.save(target, prepared["comment"], prepared["before_revision"])
        db.execute("DELETE FROM mobile_files WHERE order_id=?", (record["id"],))

    def inventory(self, record):
        with self.store.connect() as db:
            saved = db.execute("SELECT * FROM mobile_files WHERE order_id=?", (record["id"],)).fetchone()
        if saved and time.time() - saved["scanned"] < 300:
            return json.loads(saved["items"]), saved["scanned"], ""
        try:
            folder = self.store.target(record["path"])
            files = []
            for parent, dirs, names in os.walk(folder):
                dirs[:] = sorted(name for name in dirs if not name.startswith(".") and not (Path(parent) / name).is_symlink())
                for name in sorted(names):
                    if name.startswith(".") or name in (document.DOCUMENT, *document.LEGACY_DOCUMENTS):
                        continue
                    target = Path(parent) / name
                    if target.is_symlink() or not target.is_file():
                        continue
                    stat = target.stat()
                    comment = file_comments.read(target)
                    files.append({"path": target.relative_to(self.store.root).as_posix(), "name": name,
                                  "size": stat.st_size, "modified": stat.st_mtime, "token": file_token(target),
                                  "comment": comment["comment"]})
                    if len(files) > 5000:
                        raise ValueError("Больше 5000 файлов в заказе; каталог вложений пока не обновлён")
            scanned = time.time()
            with self.store.connect() as db:
                db.execute("INSERT OR REPLACE INTO mobile_files VALUES (?,?,?)", (record["id"], scanned, encode(files)))
            return files, scanned, ""
        except (OSError, ValueError) as error:
            return (json.loads(saved["items"]) if saved else []), (saved["scanned"] if saved else 0), str(error)

    def catalog(self, root_id):
        orders = []
        for record in self.store.list():
            with self.store.connect() as db:
                items = self.tasks(db, record)
            files, scanned, error = self.inventory(record)
            orders.append({key: record[key] for key in ("id", "path", "title", "client", "note", "revision", "updated", "amount", "costs", "paid", "profit", "debt")})
            orders[-1].update(status=self.store.labels[record["status"]],
                             financial_status=document.FINANCIAL_STATUS_LABELS[record["financial_status"]],
                             tasks=items, tasks_text=record["extra_blocks"].get(document.TODO_BLOCK, ""),
                             files=files, files_updated=scanned, files_error=error)
        with self.store.connect() as db:
            generation = int(self.get_meta(db, "generation", 0)) + 1
            self.put_meta(db, "generation", generation)
            receipts = [json.loads(row[0]) for row in db.execute("SELECT result FROM mobile_operations WHERE status!='prepared'")]
        return {"schema": 1, "root_id": root_id, "generation": generation, "generated": time.time(), "orders": orders, "receipts": receipts}

    def run(self):
        if self.store.database_only:
            return
        if not self.status()["enabled"] or not RUN_LOCK.acquire(blocking=False):
            return
        try:
            root_id = self.prepare()
            pending, errors = [], []
            for path in sorted((self.folder / ".inbox").glob(".*.json")):
                try:
                    regular(path)
                    if path.stat().st_size > MAX_OPERATION:
                        raise ValueError("Слишком большое действие")
                    raw = path.read_bytes()
                    operation = json.loads(raw)
                    self.validate(operation, root_id)
                    if path.name != f'.{operation["id"]}.json':
                        raise ValueError("Имя файла не соответствует идентификатору")
                    pending.append((operation, raw))
                except (OSError, ValueError, TypeError, AttributeError) as error:
                    errors.append(f"{path.name}: {error}")
            pending.sort(key=lambda item: (item[0]["device_id"], item[0]["sequence"]))
            for operation, raw in pending:
                try:
                    receipt = self.apply(operation, raw, root_id)
                    if receipt:
                        write_json(self.folder / ".receipts" / f'.{operation["id"]}.json', receipt)
                except (OSError, ValueError) as error:
                    errors.append(f'{operation["id"]}: {error}')
            self.store.sync()
            catalog = self.catalog(root_id)
            write_json(self.folder / ".catalog.json", catalog)
            with self.store.connect() as db:
                self.put_meta(db, "last_sync", catalog["generated"])
                self.put_meta(db, "orders", len(catalog["orders"]))
                self.put_meta(db, "error", "\n".join(errors[:20]))
        except (OSError, ValueError) as error:
            with self.store.connect() as db:
                self.put_meta(db, "error", str(error))
        finally:
            RUN_LOCK.release()
