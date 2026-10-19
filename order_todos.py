"""Сводка задач из SQLite; чтение файлов вложенных папок выполняется отдельно в фоне."""
import os
import re
import threading
import time
import unicodedata
from pathlib import Path

import order_document as document
from folder_notes import FolderNotes, parent_order

REFRESH_LOCK = threading.Lock()


def path_key(path):
    return [(not name.startswith("#"), [int(part) if part.isdigit() else part
             for part in re.split(r"([0-9]+)", unicodedata.normalize("NFC", name).casefold())]) for name in Path(path).parts]


def group(path, label, items, blocks, **metadata):
    legacy = blocks.get(document.TODO_BLOCK, "") if items is None else ""
    if items is not None:
        items = [item for item in items if not item["done"]]
    if not items and not legacy:
        return None
    return {"path": path, "label": label, "items": items, "legacy_text": legacy, **metadata}


class OrderTodos:
    def __init__(self, store):
        self.store = store
        # Фоновое чтение не переносит прежние служебные файлы и не переписывает карточки.
        self.notes = FolderNotes(store)

    def attach(self, orders):
        if not orders:
            return orders
        by_path = {order["path"]: {**order, "todo_groups": [], "todo_index": {"checked": None, "error": ""}} for order in orders}
        for order in by_path.values():
            own = group(order["path"], "Заказ", order["todo_items"], order["extra_blocks"],
                        sync_pending=order["sync_pending"], sync_error=order["sync_error"])
            if own:
                order["todo_groups"].append(own)
        # Только локальная база. Список, поиск и фильтры не ждут iCloud.
        with self.notes.connect() as db:
            rows = db.execute("SELECT * FROM folder_notes").fetchall()
            catalog = db.execute("SELECT 1 FROM sqlite_master WHERE name='todo_catalog'").fetchone()
            if catalog:
                for row in db.execute("SELECT * FROM todo_catalog"):
                    if row["path"] in by_path:
                        by_path[row["path"]]["todo_index"] = {"checked": row["checked"], "error": row["error"]}
        for row in sorted(rows, key=lambda value: path_key(value["path"])):
            if row["path"] in by_path:
                continue
            # Ближайший зарегистрированный предок исключает дубли прежних вложенных регистраций.
            parts = Path(row["path"]).parts
            owner = next((Path(*parts[:i]).as_posix() for i in range(len(parts) - 1, 0, -1)
                          if Path(*parts[:i]).as_posix() in by_path), None)
            if owner is None:
                continue
            record = self.notes.record(row)
            item = group(record["path"], record["path"][len(owner) + 1:], record["todo_items"], record["extra_blocks"],
                         sync_pending=record["sync_pending"], sync_error=record["sync_error"])
            if item:
                by_path[owner]["todo_groups"].append(item)
        return [by_path[order["path"]] for order in orders]

    def refresh(self):
        if not REFRESH_LOCK.acquire(blocking=False):
            return
        try:
            orders = self.store.list()
            if not orders:
                return
            # Запомнить задачи исчезнувших папок, чтобы не выдавать неполную сводку за пустой список.
            known = {order["path"]: [item["path"] for item in order["todo_groups"] if item["path"] != order["path"]]
                     for order in self.attach(orders)}
            registered = {order["path"] for order in orders}
            for order in orders:
                relative = order["path"]
                seen, errors = set(), []
                try:
                    target = self.store.target(relative)
                    def on_error(error):
                        errors.append(str(error))
                    for current, dirs, _ in os.walk(target, followlinks=False, onerror=on_error):
                        folder = Path(current)
                        in_order = parent_order(self.store.root, (folder / "__todo_scope__").relative_to(self.store.root).as_posix()) is not None
                        dirs[:] = sorted(name for name in dirs if not name.startswith(".") and not (folder / name).is_symlink()
                                         and (not name.startswith("#") or in_order)
                                         and (folder / name).relative_to(self.store.root).as_posix() not in registered)
                        if folder == target:
                            continue
                        path = folder.relative_to(self.store.root).as_posix()
                        seen.add(path)
                        try:
                            cached = self.notes.get(path)
                            has_card = any((folder / name).exists() or (folder / name).is_symlink()
                                           for name in (document.DOCUMENT, *document.LEGACY_DOCUMENTS))
                            if (cached or has_card) and parent_order(self.store.root, path):
                                self.notes.read(path)
                        except (OSError, ValueError) as error:
                            errors.append(path + ": " + str(error))
                    missing = [path for path in known[relative] if path not in seen]
                    if missing:
                        errors.append("Недоступны папки с сохранёнными задачами: " + ", ".join(missing[:3]))
                except (OSError, ValueError) as error:
                    errors.append(str(error))
                with self.notes.connect() as db:
                    db.execute("CREATE TABLE IF NOT EXISTS todo_catalog (path TEXT PRIMARY KEY, checked REAL, error TEXT NOT NULL)")
                    previous = db.execute("SELECT checked FROM todo_catalog WHERE path=?", (relative,)).fetchone()
                    checked = previous[0] if errors and previous else None if errors else time.time()
                    db.execute("INSERT OR REPLACE INTO todo_catalog VALUES (?,?,?)", (relative, checked, " · ".join(errors[:3])))
        finally:
            REFRESH_LOCK.release()
