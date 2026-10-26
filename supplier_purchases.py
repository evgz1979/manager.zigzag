"""Supplier To-do is a live view of purchases in ordinary source orders."""
import unicodedata
from pathlib import Path

import order_document as document
from client_activity import is_inactive
from event_folder_undo import guard_database
from folder_structure import client_path, is_work_root, is_supplier_root


def supplier_name(relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute() or Path(relative).as_posix() != relative:
        return ""
    parts = Path(relative).parts
    if any(part.startswith(".") for part in parts):
        return ""
    if len(parts) == 1 and is_supplier_root(parts[0]):
        return "glass"
    if len(parts) != 2 or not is_work_root(parts[0]):
        return ""
    name = parts[1].removeprefix("#").strip().casefold()
    return name if name == "etc" or name in document.PURCHASE_SUPPLIERS else ""


class SupplierPurchases:
    def __init__(self, store):
        self.store = store

    def section(self, relative):
        name = supplier_name(relative)
        if not name:
            raise ValueError("Выбери раздел поставщика закупок в # work")
        guard_database(self.store.database, relative)
        return name

    def read(self, relative, *, inactive=()):
        name = self.section(relative)
        groups = []
        for order in self.store.list():
            if not client_path(order["path"]) or is_inactive(order["path"], inactive):
                continue
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
