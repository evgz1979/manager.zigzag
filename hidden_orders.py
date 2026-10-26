"""SQLite-only, read-only overview of orders absent from the main table."""
import json
from pathlib import Path
import unicodedata

from client_activity import is_inactive
from folder_structure import client_name, is_service_folder, order_location
import work_orders

HIDDEN_STATUSES = frozenset({"done", "cancelled"})
REASONS = {
    "done": "Готово", "cancelled": "Отменён",
    "inactive_client": "Неактивный клиент", "inactive_object": "Неактивный объект",
    "production": "Производство", "supplier_archive": "В архиве",
    "unregistered": "Не добавлен",
}


def canonical(path):
    return unicodedata.normalize("NFC", path)


def catalog_orders(store, records):
    """Include known unregistered folders, without discovering or registering any."""
    if not store.database.exists():
        return [], []
    known = {canonical(row["path"]) for row in records}
    catalog, warnings = set(), []
    with store.connect() as db:
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for row in (db.execute("SELECT path,data FROM metadata_records WHERE kind IN ('object_order_folder','work_order_folder')") if "metadata_records" in tables else []):
            path = row["path"]
            if (not path or Path(path).is_absolute() or any(part.startswith(".") for part in Path(path).parts)
                    or is_service_folder(path)):
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
    records = store.list(include_unregistered=True)
    folders, warnings = catalog_orders(store, records)
    result = []
    for order in [*records, *folders]:
        path = order["path"]
        production = work_orders.in_work(path)
        reasons = []
        if not production and order["status"] in HIDDEN_STATUSES:
            reasons.append(order["status"])
        if is_inactive(path, inactive_clients):
            reasons.append("inactive_client")
        if is_inactive(path, inactive_objects):
            reasons.append("inactive_object")
        if production:
            reasons.append("production")
        if work_orders.archived(order):
            reasons.append("supplier_archive")
        if not order["registered"]:
            reasons.append("unregistered")
        if not reasons:
            continue
        location = {key: order[key] for key in ("client", "client_path", "object", "object_path")}
        if production:
            parts = Path(path).parts
            location = {"client": "Производство", "client_path": parts[0],
                "object": " / ".join(parts[1:-1]),
                "object_path": Path(*parts[:-1]).as_posix() if len(parts) > 2 else ""}
        supplier = work_orders.status_order(path)
        status_label = (work_orders.STATUS_LABELS.get(work_orders.read_status(order["extra_blocks"]), "Неизвестный статус") if supplier
                        else "—" if production else store.labels.get(order["status"], "Неизвестный статус"))
        note = order.get("note")
        result.append({"path": path, "id": order["id"], "title": order["title"], **location,
            "status": order["status"] if not production and not supplier else None, "status_label": status_label,
            "reasons": reasons, "note": note.splitlines()[0] if isinstance(note, str) and note else "",
            "updated": order["updated"]})
    return {"orders": result, "reason_labels": REASONS, "warnings": warnings}
