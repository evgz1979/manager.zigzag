"""Object order lists: bounded folder-name discovery, then SQLite-only refreshes."""
import json
import threading
import time
import unicodedata
from pathlib import Path

import order_document as document
import order_deadlines
from folder_structure import folder_role, client_name, order_location
from order_todos import OrderTodos
from local_metadata import MetadataStore
from event_folder_undo import guard_database

SCOPE = "object_orders_scope"
FOLDER = "object_order_folder"
LOCK = threading.Lock()


def inside(path, scope):
    return path.startswith(scope + "/")


def canonical(path):
    return unicodedata.normalize("NFC", path)


class ObjectOrders:
    scope_kind = SCOPE
    folder_kind = FOLDER

    def __init__(self, store):
        self.store = store
        self.meta = MetadataStore(store)

    def path(self, relative):
        relative = canonical(self.store.path(relative))
        if any(part.startswith("#") for part in Path(relative).parts):
            raise ValueError("Выбери объект клиента")
        guard_database(self.store.database, relative, include_children=True)
        return relative

    def put(self, kind, path, body):
        try:
            current = self.meta.get(kind, path)
        except TypeError:
            raise ValueError("Неизвестный формат каталога заказов сохранён без изменений: " + path) from None
        data = {key: value for key, value in current.items() if key not in {"path", "revision", "updated"}} if current else None
        if current and (type(current.get("version")) is not int or current["version"] != 1 or set(data) != set(body)):
            raise ValueError("Неизвестный формат каталога заказов сохранён без изменений: " + path)
        if data == body:
            return
        self.meta.put(kind, path, body, current["revision"] if current else "missing")

    def refresh(self, relative):
        """Read directory names only; never import cards or enter an order's contents."""
        source = self.store.path(relative)
        relative = self.path(source)
        target = self.store.target(source)
        if folder_role(self.store.root, source)["folderKind"] != "object":
            raise ValueError("Список заказов доступен в объекте клиента")
        with LOCK:
            found, errors, stack = set(), [], [(target, 0)]
            visited = 0
            while stack:
                folder, depth = stack.pop()
                try:
                    if depth > 32 or visited > 20000:
                        raise ValueError("Каталог объекта слишком большой; показаны последние сохранённые папки")
                    visited += 1
                    children = sorted(folder.iterdir(), key=lambda path: path.name.casefold())
                    for child in children:
                        if child.name.startswith((".", "#")) or child.is_symlink() or not child.is_dir():
                            continue
                        path = child.relative_to(self.store.root).as_posix()
                        role = folder_role(self.store.root, path)["folderKind"]
                        if role == "order":
                            found.add(canonical(path))
                        elif role in {"object", "group", "year"}:
                            stack.append((child, depth + 1))
                except (OSError, ValueError) as error:
                    errors.append(str(error))
            self.save_catalog(relative, found, errors)

    def save_catalog(self, relative, found, errors, *, allowed=None):
        with self.meta.connect() as db:
            previous = [row["path"] for row in db.execute("SELECT path FROM metadata_records WHERE kind=?", (self.folder_kind,))
                        if inside(row["path"], relative) and (allowed is None or allowed(row["path"]))]
        for path in sorted(found):
            try:
                self.put(self.folder_kind, path, {"version": 1, "present": True})
            except ValueError as error:
                errors.append(str(error))
        if not errors:
            for path in set(previous) - found:
                try:
                    self.put(self.folder_kind, path, {"version": 1, "present": False})
                except ValueError as error:
                    errors.append(str(error))
        self.put(self.scope_kind, relative, {"version": 1, "checked": time.time(), "error": " · ".join(errors[:5])})

    def allowed_paths(self, relative, inactive, show_inactive):
        hidden = [canonical(path) for path in inactive if canonical(path) != relative and not inside(relative, canonical(path))]
        def allowed(path):
            path = canonical(path)
            return inside(path, relative) and not any(part.startswith((".", "#")) for part in Path(path).parts) and (
                show_inactive or not any(path == item or inside(path, item) for item in hidden))
        return allowed

    def read(self, relative, *, inactive=(), show_inactive=False):
        relative = self.path(relative)
        try:
            scope = self.meta.get(self.scope_kind, relative)
        except TypeError:
            raise ValueError("Неизвестный формат каталога заказов сохранён без изменений: " + relative) from None
        if not scope or type(scope.get("version")) is not int or scope["version"] != 1 or set(scope) != {"version", "checked", "error", "path", "revision", "updated"}:
            raise ValueError("Открой объект или обнови его папки для загрузки списка заказов")
        allowed = self.allowed_paths(relative, inactive, show_inactive)
        # Match equivalent Unicode spellings without changing the path/identity used by order APIs.
        # Keep distinct database rows even if their canonical paths collide; never merge cards.
        records = {}
        for row in self.store.list(include_unregistered=True):
            if allowed(row["path"]):
                records.setdefault(canonical(row["path"]), []).append(row)
        with self.meta.connect() as db:
            catalog = set()
            for row in db.execute("SELECT path,data FROM metadata_records WHERE kind=?", (self.folder_kind,)):
                if not allowed(row["path"]):
                    continue
                data = json.loads(row["data"])
                if isinstance(data, dict) and type(data.get("version")) is int and data["version"] == 1 and data.get("present") is True:
                    catalog.add(canonical(row["path"]))
            has_notes = db.execute("SELECT 1 FROM sqlite_master WHERE name='folder_notes'").fetchone()
            notes = {canonical(row["path"]): row for row in db.execute("SELECT * FROM folder_notes") if allowed(row["path"])} if has_notes else {}
        paths = catalog | {path for path, rows in records.items() if any(row["registered"] for row in rows)}
        result = []
        for path in sorted(paths):
            if any(inside(path, parent) for parent in catalog if parent != path):
                continue
            if path in records:
                result.extend(records[path])
                continue
            else:
                note = notes.get(path)
                body = json.loads(note["document"]) if note else {}
                blocks = body.get("extra_blocks", {})
                values = {key: body.get(key) if type(body.get(key)) is int else None for key in ("amount", "costs", "paid")}
                row = {"path": path, "id": None, "revision": None, "registered": False,
                    "title": body.get("title") or Path(path).name, "client": client_name(path), **order_location(path),
                    "status": body.get("status", "unspecified"), "financial_status": body.get("financial_status", "unspecified"),
                    "note": body.get("note", ""), "extra_blocks": blocks, "updated": note["updated"] if note else None,
                    "todo_items": document.read_todos(blocks), "purchase_items": document.read_purchases(blocks),
                    "is_favorite": document.read_favorite(blocks), "deadline_weeks": order_deadlines.read(blocks),
                    "is_flagged": document.read_flag(blocks),
                    "is_blue_plus": document.read_blue_plus(blocks),
                    "is_dollar": document.read_dollar(blocks),
                    "deadline_comments": order_deadlines.read_comments(blocks),
                    "sync_pending": False, "sync_error": "", "storage": "database", **values}
                row["profit"] = values["amount"] - values["costs"] if values["amount"] is not None and values["costs"] is not None else None
                row["debt"] = values["amount"] - values["paid"] if values["amount"] is not None and values["paid"] is not None else None
            result.append(row)
        return {"path": relative, "orders": OrderTodos(self.store).attach(result), "checked": scope.get("checked"),
                "error": scope.get("error", ""), "deadline_week_options": order_deadlines.week_options()}
