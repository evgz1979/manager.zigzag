"""Rename one opened folder and all its SQLite paths, without duplicating orders."""
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import unicodedata

import event_folder_undo
import folder_layout as layout
import folder_notes
import folder_rename_undo as restore
from folder_structure import folder_role, section_prefix
from order_folders import LOCK, layout_scope
import orders
from order_todos import REFRESH_LOCK


class FolderRenameConflict(ValueError):
    pass


def available(relative):
    parts = Path(relative).parts
    if not parts or Path(relative).is_absolute() or any(part.startswith(".") for part in parts):
        return False
    return not parts[0].startswith("#") or len(parts) > len(section_prefix(relative)) > 0


def target(root, relative):
    if not isinstance(relative, str) or not available(relative):
        raise ValueError("Выберите обычную папку клиента, объекта, заказа или события")
    path = layout.safe_path(root, relative, [Path(relative).parts[0]], **layout_scope(relative))
    if not path.is_dir():
        raise FileNotFoundError("Папка недоступна. Открой её заново")
    return path


def preview(store, relative):
    path = target(store.root, relative)
    event_folder_undo.guard_database(store.database, relative, include_children=True)
    fingerprint = {"path": relative, "identity": layout.identity(path), "parent": layout.identity(path.parent)}
    return {"path": relative, "name": path.name,
            "revision": hashlib.sha256(json.dumps(fingerprint, sort_keys=True).encode()).hexdigest(), **fingerprint}


def name(value):
    if not isinstance(value, str) or any(char in '/\\:' or ord(char) < 32 or ord(char) == 127 for char in value):
        raise ValueError("Имя папки должно быть в одну строку, без /, \\ и :")
    value = unicodedata.normalize("NFC", value.strip())
    if not value or value.startswith(".") or len(os.fsencode(value)) > 255:
        raise ValueError("Укажи видимое имя папки до 255 байт")
    return value


def rename(store, payload):
    root = store.root.resolve()
    # The handler also holds file-comments, print and folder-card locks, in the
    # same order as normal writers. Workers cannot export an old path mid-move.
    with LOCK, REFRESH_LOCK, orders.SYNC_LOCK, folder_notes.SYNC_LOCK, store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        view = preview(store, payload.get("path"))
        if view["revision"] != payload.get("revision"):
            raise FolderRenameConflict("Папка изменилась после открытия формы. Обнови её перед переименованием")
        source = view["path"]
        new_name = name(payload.get("name"))
        if unicodedata.normalize("NFC", Path(source).name) == new_name:
            raise ValueError("Имя папки не изменилось")
        destination = (Path(source).parent / new_name).as_posix()
        if not available(destination) or layout.exists(root / destination):
            raise FolderRenameConflict("Это имя уже занято или недоступно. Данные не перезаписаны")
        restore.check(db, source, destination)
        kind = folder_role(root, source)["folderKind"]
        registered = [(row[0], folder_role(root, row[0])["folderKind"]) for row in db.execute("SELECT path FROM orders")
                      if restore.inside(row[0], source) and (root / row[0]).is_dir()]
        before = {"database": str(store.database.resolve()), **view, "destination": destination,
                  "tables": {table: [{key: row[key] for key in row.keys() if key != "pdf"} for row in db.execute(f"SELECT * FROM {table}") if restore.inside(row["path"], source)]
                             for table in ("orders", "folder_notes", "todo_catalog", "todo_missing_folders", "client_activity", "object_activity", "invoices") if restore.table(db, table)}}
        plan = layout.Plan(root, list({Path(source).parts[0], Path(destination).parts[0]}), **layout_scope(source))
        plan.database_paths = True
        plan.move(source, destination, "Переименовать открытую папку с сохранением всех путей SQLite")
        session = plan.create_session(["Переименование из менеджера, без новой регистрации заказов.",
                                      "Откат только через .restore.py, согласующий папку и пути базы."], before)
        layout.save_json(session / ".folder-paths.json", {"database": str(store.database.resolve()), "source": source, "destination": destination})
        shutil.copyfile(restore.__file__, session / ".restore.py")
        # Snapshot before any persistent intent or document mutation.
        with closing(sqlite3.connect(store.database.resolve().as_uri() + "?mode=ro", uri=True)) as original:
            with closing(sqlite3.connect(session / ".before.sqlite3")) as backup:
                original.backup(backup)
        db.execute("CREATE TABLE IF NOT EXISTS folder_renames (session TEXT PRIMARY KEY,state TEXT NOT NULL,mappings TEXT NOT NULL,paths_applied INTEGER NOT NULL)")
        db.execute("INSERT INTO folder_renames VALUES (?,'pending',?,0)",
                   (str(session), json.dumps([{"source": source, "destination": destination}], ensure_ascii=False)))
        db.commit()
        try:
            db.execute("BEGIN IMMEDIATE")
            layout.apply(session)
            if folder_role(root, destination)["folderKind"] != kind:
                raise ValueError("Сохрани тип папки: дату/номер заказа, числовой префикс группы или # служебной папки")
            for path, old_kind in registered:
                if folder_role(root, restore.remap(path, source, destination))["folderKind"] != old_kind:
                    raise ValueError("Новое имя меняет структуру вложенных заказов")
            restore.rewrite(db, source, destination)
            db.execute("UPDATE folder_renames SET state='complete',paths_applied=1 WHERE session=?", (str(session),))
            db.commit()
        except Exception as error:
            db.rollback()
            try:
                restore.undo(session, True)
            except (OSError, ValueError, sqlite3.Error) as undo_error:
                layout.append(session, {"phase": "rollback_failed", "error": str(undo_error)})
                raise FolderRenameConflict("Данные сохранены. Переименование требует отката из журнала: " + str(session)) from error
            raise FolderRenameConflict("Переименование отменено, прежний путь восстановлен: " + str(error)) from error
        layout.save_json(session / ".result.json", {"status": "renamed", "source": source, "path": destination})
        return {"path": destination, "source": source, "name": new_name, "journal": session.relative_to(root).as_posix()}
