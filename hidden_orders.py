"""SQLite-only, read-only overview of orders absent from the main table."""
import json
from pathlib import Path
import unicodedata

from client_activity import is_inactive
from folder_structure import client_name, is_service_folder, is_supplier_root, is_work_root, order_location

HIDDEN_STATUSES = frozenset({"done", "cancelled"})
REASONS = {
    "done": "Готово", "cancelled": "Отменён",
    "inactive_client": "Неактивный клиент", "inactive_object": "Неактивный объект",
    "unregistered": "Не добавлен",
}


def canonical(path):
    return unicodedata.normalize("NFC", path)


def production_path(path):
    parts = Path(path).parts
    return bool(parts and (is_work_root(parts[0]) or is_supplier_root(parts[0])))


def catalog_orders(store, records):
    """Include known unregistered folders, without discovering or registering any."""
    if not store.database.exists():
        return [], []
    known = {canonical(row["path"]) for row in records}
    catalog, warnings = set(), []
    with store.connect() as db:
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for row in (db.execute("SELECT path,data FROM metadata_records WHERE kind='object_order_folder'") if "metadata_records" in tables else []):
            path = row["path"]
            if (not path or Path(path).is_absolute() or any(part.startswith(".") for part in Path(path).parts)
                    or is_service_folder(path) or production_path(path)):
                continue
            try:
                data = json.loads(row["data"])
            except (ValueError, TypeError):
                data = None
            if not isinstance(data, dict) or type(data.get("version")) is not int or data["version"] != 1 or type(data.get("present")) is not bool:
                warnings.append("Неизвестный формат каталога: " + path)
            elif data["present"]:
                catalog.add(canonical(path))
        notes = {canonical(row["path"]): row for row in db.execute("SELECT path,document,updated FROM folder_notes")} if "folder_notes" in tables else {}
    result = []
    for path in sorted(catalog - known):
        if any(path.startswith(parent + "/") for parent in catalog if parent != path):
            continue
        note = notes.get(path)
        try:
            body = json.loads(note["document"]) if note else {}
            if not isinstance(body, dict):
                raise ValueError()
        except (ValueError, TypeError):
            body = {}
            warnings.append("Неизвестный формат карточки: " + path)
        result.append({"path": path, "id": None, "registered": False,
            "title": body.get("title") if isinstance(body.get("title"), str) and body["title"] else Path(path).name,
            "client": client_name(path), **order_location(path),
            "status": body.get("status") if isinstance(body.get("status"), str) else "unspecified", "note": body.get("note", ""),
            "extra_blocks": body.get("extra_blocks") if isinstance(body.get("extra_blocks"), dict) else {},
            "updated": note["updated"] if note else None})
    return result, warnings


def listed(store, inactive_clients, inactive_objects):
    records = [row for row in store.list(include_unregistered=True) if not production_path(row["path"])]
    folders, warnings = catalog_orders(store, records)
    result = []
    for order in [*records, *folders]:
        path = order["path"]
        reasons = []
        if order["status"] in HIDDEN_STATUSES:
            reasons.append(order["status"])
        if is_inactive(path, inactive_clients):
            reasons.append("inactive_client")
        if is_inactive(path, inactive_objects):
            reasons.append("inactive_object")
        if not order["registered"]:
            reasons.append("unregistered")
        if not reasons:
            continue
        location = {key: order[key] for key in ("client", "client_path", "object", "object_path")}
        status_label = store.labels.get(order["status"], "Неизвестный статус")
        note = order.get("note")
        result.append({"path": path, "id": order["id"], "title": order["title"], **location,
            "status": order["status"], "status_label": status_label,
            "reasons": reasons, "note": note.splitlines()[0] if isinstance(note, str) and note else "",
            "updated": order["updated"]})
    return {"orders": result, "reason_labels": REASONS, "warnings": warnings}
