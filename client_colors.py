"""Explicit RGB preferences for the web labels of client folders."""
import json
import re
import time
import unicodedata
import uuid

from event_folder_undo import assert_unlocked
from folder_rename import target
from folder_structure import client_path
from local_metadata import audit, schema

KIND = "client_color"
RGB = re.compile(r"#[0-9a-fA-F]{6}")


# Обозначает устаревшую версию цвета в открытой форме.
# HTTP-обработчик возвращает конфликт без записи новых данных.
class ClientColorConflict(ValueError):
    pass


# Читает цвет и версию записи для редактора.
# Незнакомый формат оставляет запись доступной только для чтения.
def record(row):
    if row is None:
        return {"color": None, "revision": "missing", "editable": True}
    try:
        data = json.loads(row["data"])
    except ValueError:
        data = None
    valid = (isinstance(data, dict) and type(data.get("version")) is int and data["version"] == 1
             and "color" in data and (data["color"] is None or
                                      isinstance(data["color"], str) and RGB.fullmatch(data["color"])))
    return {"color": data["color"].lower() if valid and data["color"] else None,
            "revision": f"{row['id']}:{row['revision']}", "editable": bool(valid)}


# Проверяет, что открыта существующая папка самого клиента.
# Возвращает NFC-путь клиента, включая числовую группу.
def checked_path(store, relative):
    folder = target(store.root, relative)
    if relative != client_path(relative):
        raise ValueError("Открой карточку клиента, чтобы выбрать цвет")
    parts = (folder, folder.parent) if "/" in relative else (folder,)
    for part in parts:
        name = unicodedata.normalize("NFC", part.name)
        if not any(unicodedata.normalize("NFC", entry.name) == name for entry in part.parent.iterdir()):
            raise ValueError("Открой клиента по точному пути из дерева")
    return unicodedata.normalize("NFC", relative)


# Собирает только вручную заданные цвета для подписей.
# Читает SQLite без обхода клиентских папок или автоматических назначений.
def catalog(store):
    if not store.database.is_file():
        return {}
    with store.connect() as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='metadata_records'").fetchone():
            return {}
        return {row["path"]: color for row in db.execute("SELECT * FROM metadata_records WHERE kind=? ORDER BY path", (KIND,))
                if (color := record(row)["color"]) is not None}


# Читает состояние редактора одного клиента.
# У отсутствующей записи пустой цвет и версия missing.
def read(store, relative):
    path = checked_path(store, relative)
    with store.connect() as db:
        assert_unlocked(db, path)
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='metadata_records'").fetchone():
            return record(None)
        return record(db.execute("SELECT * FROM metadata_records WHERE kind=? AND path=?", (KIND, path)).fetchone())


# Сохраняет выбранный RGB или снимает цвет клиента.
# Проверяет известный формат и версию под той же транзакцией, где пишется история.
def save(store, payload):
    color, revision = payload.get("color"), payload.get("revision")
    if ("color" not in payload or not isinstance(revision, str) or
            color is not None and (not isinstance(color, str) or not RGB.fullmatch(color))):
        raise ValueError("Укажи RGB-цвет и версию записи")
    color = color.lower() if color else None
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        path = checked_path(store, payload.get("path"))
        assert_unlocked(db, path)
        schema(db)
        row = db.execute("SELECT * FROM metadata_records WHERE kind=? AND path=?", (KIND, path)).fetchone()
        current = record(row)
        if current["revision"] != revision:
            raise ClientColorConflict("Цвет изменён в другом окне. Проверь сохранённый цвет")
        if not current["editable"]:
            raise ValueError("Неизвестный формат цвета клиента")
        if current["color"] == color:
            return current
        audit(db, "metadata_records")
        data = json.dumps({"version": 1, "color": color})
        if row is None:
            db.execute("INSERT INTO metadata_records VALUES (?,?,?,?,1,?)", (str(uuid.uuid4()), KIND, path, data, time.time()))
        else:
            db.execute("UPDATE metadata_records SET data=?,revision=revision+1,updated=? WHERE id=?", (data, time.time(), row["id"]))
        return record(db.execute("SELECT * FROM metadata_records WHERE kind=? AND path=?", (KIND, path)).fetchone())
