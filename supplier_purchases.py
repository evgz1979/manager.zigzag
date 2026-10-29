"""Supplier To-do is a live view of purchases in ordinary source orders."""
import json
import time
import unicodedata
import uuid
from collections import Counter
from pathlib import Path

import order_document as document
from client_activity import is_inactive
from event_folder_undo import guard_database
from folder_structure import client_path, dated, is_work_root, is_supplier_root
import work_orders

CATALOG_KIND = "purchase_supplier_catalog"


def remember_sections(db, root, paths):
    """Remember an explicit, successful #work listing; polling stays SQLite-only."""
    from local_metadata import audit
    root = work_orders.supplier_root_path(root)
    data = {"version": 1, "paths": sorted(unicodedata.normalize("NFC", path) for path in paths)}
    row = db.execute("SELECT * FROM metadata_records WHERE kind=? AND path=?", (CATALOG_KIND, root)).fetchone()
    if row:
        previous = json.loads(row["data"])
        if not valid_catalog(previous):
            raise ValueError("Неизвестный каталог поставщиков сохранён без изменений")
        if previous == data:
            return
    audit(db, "metadata_records")
    if row:
        db.execute("UPDATE metadata_records SET data=?,revision=revision+1,updated=? WHERE id=?",
                   (json.dumps(data, ensure_ascii=False), time.time(), row["id"]))
    else:
        db.execute("INSERT INTO metadata_records VALUES (?,?,?,?,1,?)",
                   (str(uuid.uuid4()), CATALOG_KIND, root, json.dumps(data, ensure_ascii=False), time.time()))


def valid_catalog(data):
    return (isinstance(data, dict) and type(data.get("version")) is int and data["version"] == 1
            and isinstance(data.get("paths"), list) and all(isinstance(path, str) for path in data["paths"]))


def available_suppliers(db):
    """Current starred sections; old assignments do not depend on today's stars."""
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='metadata_records'").fetchone():
        return []
    catalogs = {}
    for row in db.execute("SELECT path,data FROM metadata_records WHERE kind=?", (CATALOG_KIND,)):
        data = json.loads(row["data"])
        catalogs[row["path"]] = set(data["paths"]) if valid_catalog(data) else set()
    options = []
    for row in db.execute("SELECT * FROM metadata_records WHERE kind=?", (work_orders.SUPPLIER_FAVORITE_KIND,)):
        favorite = work_orders.supplier_favorite_record(row)
        name = supplier_name(row["path"])
        root = Path(row["path"]).parent.as_posix()
        if (favorite["is_favorite"] is True and name != "etc" and name
                and (root not in catalogs or row["path"] in catalogs[root])):
            options.append({"name": name, "path": row["path"], "position": favorite["position"]})
    options.sort(key=lambda row: (row["position"], row["path"]))
    result, names = [], set()
    for row in options:
        if row["name"] not in names:
            result.append(row)
            names.add(row["name"])
    return result


def write_assignments(db, blocks, items):
    previous = document.read_purchases(blocks)
    if previous is None:
        raise ValueError("Прежние записи закупок и затрат сохранены без изменений")
    items = document.validate_purchases(items)
    allowed = {row["name"] for row in available_suppliers(db)}
    before = Counter(name for item in previous for name in item["suppliers"])
    after = Counter(name for item in items for name in item["suppliers"])
    if any(count > before[name] for name, count in after.items() if name not in allowed):
        raise ValueError("Поставщик недоступен для назначения. Проверь звёзды разделов в # work и обнови список")
    if after.keys() - set(document.PURCHASE_SUPPLIERS):
        from local_metadata import schema
        schema(db)
        db.execute("INSERT INTO metadata_settings VALUES ('purchase_suppliers','1') ON CONFLICT(key) DO UPDATE SET value=excluded.value")
    return document.write_purchases(blocks, items)


def supplier_name(relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute() or Path(relative).as_posix() != relative:
        return ""
    parts = Path(relative).parts
    if any(part.startswith(".") for part in parts):
        return ""
    if len(parts) == 1 and is_supplier_root(parts[0]):
        return "glass"
    if len(parts) != 2 or not is_work_root(parts[0]) or dated(parts[1]):
        return ""
    name = parts[1].removeprefix("#").strip().casefold()
    name = unicodedata.normalize("NFC", name)
    return name if name == "etc" or document.valid_purchase_supplier(name) else ""


class SupplierPurchases:
    def __init__(self, store):
        self.store = store

    def section(self, relative):
        name = supplier_name(relative)
        if not name:
            raise ValueError("Выбери раздел поставщика закупок в # work")
        guard_database(self.store.database, relative)
        return name

    def source_orders(self, inactive):
        return (order for order in self.store.list() if client_path(order["path"]) and not is_inactive(order["path"], inactive))

    def catalog(self, *, inactive=()):
        with self.store.connect() as db:
            options = available_suppliers(db)
        counts = {"etc": 0}
        for order in self.source_orders(inactive):
            for item in order["purchase_items"] or []:
                if not item["done"]:
                    for name in item["suppliers"] or ["etc"]:
                        counts[name] = counts.get(name, 0) + 1
        return {"suppliers": options, "counts": counts}

    def read(self, relative, *, inactive=()):
        name = self.section(relative)
        groups = []
        for order in self.source_orders(inactive):
            items = [{"index": index, **item} for index, item in enumerate(order["purchase_items"] or []) if document.purchase_matches_supplier(item, name)]
            if items:
                groups.append({key: order[key] for key in ("path", "id", "revision", "title", "client", "object")})
                groups[-1]["items"] = items
        groups.sort(key=lambda row: tuple(unicodedata.normalize("NFC", row[key]).casefold() for key in ("client", "object", "title", "path")))
        return {"path": relative, "supplier": name, "orders": groups}

    def save(self, payload, *, inactive=()):
        name = self.section(payload.get("supplier_path"))
        relative = self.store.path(payload.get("path"))
        if is_inactive(relative, inactive):
            raise ValueError("Заказ скрыт отметкой неактивности. Обнови список закупок")
        return self.store.save_purchase_done(payload, name)
