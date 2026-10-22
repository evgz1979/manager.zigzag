"""Supplier-order selections stored as stable identities in the parent card."""
import json
import time
import unicodedata
import uuid
from pathlib import Path

from event_folder_undo import assert_unlocked
from folder_structure import dated, is_service_folder, is_supplier_root, is_work_root, is_print_section

LINKS_BLOCK = "Связанные заказы поставщиков"
MAX_LINKS = 200
SUPPLIER_COLOR_KIND = "work_supplier_color"


def in_work(relative):
    parts = Path(relative).parts
    return bool(parts and is_work_root(parts[0]))


def direct_order(relative):
    parts = Path(relative).parts
    return len(parts) == 2 and is_work_root(parts[0]) and dated(parts[1])


def supplier_name(relative):
    """Actual #work section, without inspecting folders or assigning a root order."""
    parts = Path(relative).parts
    if len(parts) < 3 or not is_work_root(parts[0]) or dated(parts[1]):
        return ""
    return parts[1][1:].strip() if parts[1].startswith('#') else parts[1]


def supplier_color(db, relative):
    """Pin the existing heading color to the section path, entirely in SQLite."""
    parts = Path(relative).parts
    if len(parts) < 2 or not is_work_root(parts[0]) or dated(parts[1]):
        return None
    path = unicodedata.normalize("NFC", Path(*parts[:2]).as_posix())
    assert_unlocked(db, path)
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='metadata_records'").fetchone():
        from local_metadata import schema, audit
        schema(db)
        audit(db, "metadata_records")
    row = db.execute("SELECT data FROM metadata_records WHERE kind=? AND path=?", (SUPPLIER_COLOR_KIND, path)).fetchone()
    if row is None:
        name = parts[1][1:].strip() if parts[1].startswith('#') else parts[1]
        name = unicodedata.normalize("NFC", name).lower()
        # Match the previous JavaScript heading hash, including unsigned overflow.
        color = 0
        for character in name:
            color = (color * 31 + ord(character)) & 0xffffffff
        data = {"version": 1, "hue": color % 360, "neutral": name == "razbor"}
        db.execute("INSERT OR IGNORE INTO metadata_records VALUES (?,?,?,?,1,?)",
                   (str(uuid.uuid4()), SUPPLIER_COLOR_KIND, path, json.dumps(data), time.time()))
        row = db.execute("SELECT data FROM metadata_records WHERE kind=? AND path=?", (SUPPLIER_COLOR_KIND, path)).fetchone()
    data = json.loads(row["data"])
    if (not isinstance(data, dict) or data.get("version") != 1 or type(data.get("hue")) is not int or not 0 <= data["hue"] < 360
            or type(data.get("neutral")) is not bool):
        raise ValueError("Неизвестный цвет поставщика сохранён в базе без изменений")
    return {"hue": data["hue"], "neutral": data["neutral"]}


def supplier_order(relative):
    parts = Path(relative).parts
    if is_service_folder(relative) or is_print_section(Path(relative).parent.as_posix()):
        return False
    return (len(parts) == 3 and is_work_root(parts[0]) and not dated(parts[1])) or (
        len(parts) == 2 and is_supplier_root(parts[0]))


def checked_ids(value):
    if not isinstance(value, list) or len(value) > MAX_LINKS or any(
            not isinstance(item, str) or not item or len(item) > 100 for item in value):
        raise ValueError(f"Выбери не больше {MAX_LINKS} заказов поставщиков")
    if len(set(value)) != len(value):
        raise ValueError("Заказ в подборке не должен повторяться")
    return value


def read_links(blocks):
    if LINKS_BLOCK not in blocks:
        return []
    try:
        body = json.loads(blocks[LINKS_BLOCK])
        if not isinstance(body, dict) or set(body) != {"version", "order_ids"} or type(body["version"]) is not int or body["version"] != 1:
            return None
        return checked_ids(body["order_ids"])
    except (TypeError, ValueError):
        return None


def write_links(blocks, identities):
    if read_links(blocks) is None:
        raise ValueError("Неизвестный раздел связанных заказов сохранён без изменений")
    return {**blocks, LINKS_BLOCK: json.dumps({"version": 1, "order_ids": checked_ids(identities)}, ensure_ascii=False)}


def summary(row):
    return {key: row[key] for key in ("id", "path", "title", "status", "registered")} | {
        "supplier": Path(row["path"]).parts[-2]}
