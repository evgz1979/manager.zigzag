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
SUPPLIER_FAVORITE_KIND = "work_supplier_favorite"
SUPPLIER_FAVORITE_INIT_KIND = "work_supplier_favorite_defaults"
INITIAL_SUPPLIER_FAVORITES = ("antares", "himlex", "newtek", "glass")
SUPPLIER_PALETTE_VERSION = 2
SUPPLIER_PALETTE = {
    "antares": 0, "cutter": 270, "freza": 180, "glass": 30,
    "himlex": 55, "laser": 215, "newtek": 125, "print": 325,
}


class SupplierFavoriteConflict(ValueError):
    pass


def supplier_root_path(relative):
    if not isinstance(relative, str) or len(Path(relative).parts) != 1 or not is_work_root(relative):
        raise ValueError("Выбери корень # work")
    return unicodedata.normalize("NFC", relative)


def supplier_section_path(relative):
    if not isinstance(relative, str):
        raise ValueError("Выбери раздел производства с #")
    parts = Path(relative).parts
    if len(parts) != 2 or not is_work_root(parts[0]) or not parts[1].startswith("#"):
        raise ValueError("Звезда доступна только у раздела с # в корне # work")
    return unicodedata.normalize("NFC", Path(*parts).as_posix())


def supplier_favorite_record(row):
    try:
        data = json.loads(row["data"])
    except ValueError:
        data = None
    valid = (isinstance(data, dict) and type(data.get("version")) is int and data["version"] == 1
             and type(data.get("is_favorite")) is bool
             and (data.get("position") is None or (type(data["position"]) is int and data["position"] >= 0))
             and (not data["is_favorite"] or data.get("position") is not None))
    return {"path": row["path"], "revision": f"{row['id']}:{row['revision']}",
            "is_favorite": data["is_favorite"] if valid else None,
            "position": data.get("position") if valid else None, "editable": valid}


def supplier_favorites(db, root, paths):
    """Initialize once per root; later sections start without a star."""
    from local_metadata import schema, audit
    root = supplier_root_path(root)
    paths = [supplier_section_path(path) for path in paths]
    if any(Path(path).parent.as_posix() != root for path in paths):
        raise ValueError("Раздел принадлежит другому корню производства")
    if not db.in_transaction:
        db.execute("BEGIN IMMEDIATE")
    schema(db)
    audit(db, "metadata_records")
    assert_unlocked(db, root)
    marker = db.execute("SELECT data FROM metadata_records WHERE kind=? AND path=?", (SUPPLIER_FAVORITE_INIT_KIND, root)).fetchone()
    if marker and json.loads(marker["data"]) != {"version": 1, "initialized": True}:
        raise ValueError("Неизвестные настройки избранных разделов сохранены без изменений")
    result = {}
    for path in paths:
        assert_unlocked(db, path)
        row = db.execute("SELECT * FROM metadata_records WHERE kind=? AND path=?", (SUPPLIER_FAVORITE_KIND, path)).fetchone()
        if row is None:
            name = Path(path).name[1:].strip().lower()
            selected = not marker and name in INITIAL_SUPPLIER_FAVORITES
            data = {"version": 1, "is_favorite": bool(selected),
                    "position": INITIAL_SUPPLIER_FAVORITES.index(name) if selected else None}
            db.execute("INSERT INTO metadata_records VALUES (?,?,?,?,1,?)",
                       (str(uuid.uuid4()), SUPPLIER_FAVORITE_KIND, path, json.dumps(data), time.time()))
            row = db.execute("SELECT * FROM metadata_records WHERE kind=? AND path=?", (SUPPLIER_FAVORITE_KIND, path)).fetchone()
        result[path] = supplier_favorite_record(row)
    if not marker:
        db.execute("INSERT INTO metadata_records VALUES (?,?,?,?,1,?)",
                   (str(uuid.uuid4()), SUPPLIER_FAVORITE_INIT_KIND, root, json.dumps({"version": 1, "initialized": True}), time.time()))
    return result


def read_supplier_favorites(store, root):
    root = supplier_root_path(root)
    with store.connect() as db:
        from local_metadata import schema
        schema(db)
        assert_unlocked(db, root)
        return {row["path"]: supplier_favorite_record(row)
                for row in db.execute("SELECT * FROM metadata_records WHERE kind=?", (SUPPLIER_FAVORITE_KIND,))
                if Path(row["path"]).parent.as_posix() == root}


def save_supplier_favorite(store, payload):
    from local_metadata import schema, audit
    path = supplier_section_path(payload.get("path"))
    value, revision = payload.get("is_favorite"), payload.get("revision")
    if type(value) is not bool or not isinstance(revision, str):
        raise ValueError("Укажи отметку и версию раздела")
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        schema(db)
        audit(db, "metadata_records")
        assert_unlocked(db, path)
        row = db.execute("SELECT * FROM metadata_records WHERE kind=? AND path=?", (SUPPLIER_FAVORITE_KIND, path)).fetchone()
        if row is None or supplier_favorite_record(row)["revision"] != revision:
            raise SupplierFavoriteConflict("Звезда изменена в другом окне. Данные обновлены; нажми ещё раз")
        current = supplier_favorite_record(row)
        if not current["editable"]:
            raise ValueError("Неизвестная отметка избранного сохранена без изменений")
        if current["is_favorite"] == value:
            return current
        data = json.loads(row["data"])
        if value and current["position"] is None:
            positions = [item["position"] for item in read_favorite_rows(db, Path(path).parent.as_posix())
                         if item["position"] is not None]
            data["position"] = max(positions, default=-1) + 1
        data["is_favorite"] = value
        db.execute("UPDATE metadata_records SET data=?,revision=revision+1,updated=? WHERE id=? AND revision=?",
                   (json.dumps(data), time.time(), row["id"], row["revision"]))
        return supplier_favorite_record(db.execute("SELECT * FROM metadata_records WHERE id=?", (row["id"],)).fetchone())


def read_favorite_rows(db, root):
    return [supplier_favorite_record(row) for row in db.execute("SELECT * FROM metadata_records WHERE kind=?", (SUPPLIER_FAVORITE_KIND,))
            if Path(row["path"]).parent.as_posix() == root]


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


def new_supplier_hue(db, name):
    """Choose the least occupied hue; only the new supplier gets this color."""
    used = list(SUPPLIER_PALETTE.values())
    for row in db.execute("SELECT data FROM metadata_records WHERE kind=?", (SUPPLIER_COLOR_KIND,)).fetchall():
        try:
            data = json.loads(row["data"])
            if isinstance(data, dict) and type(data.get("hue")) is int and not data.get("neutral"):
                used.append(data["hue"] % 360)
        except ValueError:
            pass  # Unknown records are retained as they are.
    seed = 0
    for character in name:
        seed = (seed * 31 + ord(character)) & 0xffffffff
    candidates = [(seed + offset) % 360 for offset in range(360)]
    return max(candidates, key=lambda hue: min(min((hue - other) % 360, (other - hue) % 360) for other in used))


def supplier_color(db, relative):
    """Persist a distinct palette per section, with a one-time v1 conversion."""
    parts = Path(relative).parts
    if len(parts) < 2 or not is_work_root(parts[0]) or dated(parts[1]):
        return None
    path = unicodedata.normalize("NFC", Path(*parts[:2]).as_posix())
    assert_unlocked(db, path)
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='metadata_records'").fetchone():
        from local_metadata import schema, audit
        schema(db)
        audit(db, "metadata_records")
    name = parts[1][1:].strip() if parts[1].startswith('#') else parts[1]
    name = unicodedata.normalize("NFC", name).lower()
    row = db.execute("SELECT * FROM metadata_records WHERE kind=? AND path=?", (SUPPLIER_COLOR_KIND, path)).fetchone()
    if row is None:
        hue = SUPPLIER_PALETTE[name] if name in SUPPLIER_PALETTE else 0 if name == "razbor" else new_supplier_hue(db, name)
        data = {"version": 1, "palette": SUPPLIER_PALETTE_VERSION, "hue": hue, "neutral": name == "razbor"}
        db.execute("INSERT OR IGNORE INTO metadata_records VALUES (?,?,?,?,1,?)",
                   (str(uuid.uuid4()), SUPPLIER_COLOR_KIND, path, json.dumps(data), time.time()))
        row = db.execute("SELECT * FROM metadata_records WHERE kind=? AND path=?", (SUPPLIER_COLOR_KIND, path)).fetchone()
    data = json.loads(row["data"])
    if (not isinstance(data, dict) or type(data.get("version")) is not int or data["version"] != 1
            or ("palette" in data and (type(data["palette"]) is not int or data["palette"] != SUPPLIER_PALETTE_VERSION))
            or type(data.get("hue")) is not int or not 0 <= data["hue"] < 360
            or type(data.get("neutral")) is not bool):
        raise ValueError("Неизвестный цвет поставщика сохранён в базе без изменений")
    if "palette" not in data:
        data = {**data, "palette": SUPPLIER_PALETTE_VERSION,
                "hue": SUPPLIER_PALETTE.get(name, data["hue"]), "neutral": name == "razbor" or data["neutral"]}
        result = db.execute("UPDATE metadata_records SET data=?,revision=revision+1,updated=? WHERE id=? AND revision=?",
                            (json.dumps(data), time.time(), row["id"], row["revision"]))
        if not result.rowcount:
            return supplier_color(db, relative)
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
