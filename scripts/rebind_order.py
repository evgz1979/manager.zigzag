"""Explicitly rebind an exported order after a confirmed external folder move.

The copied script can undo database paths after the user moves the folder back.
It never moves documents or replaces the working database with a snapshot.
"""
import argparse
from contextlib import closing
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import stat
import sys
from zoneinfo import ZoneInfo


def inside(path, prefix):
    return path == prefix or path.startswith(prefix + "/")


def table(db, name):
    return db.execute("SELECT 1 FROM sqlite_master WHERE name=?", (name,)).fetchone() is not None


def checked_folder(root, relative):
    path = Path(relative)
    if path.is_absolute() or not path.parts or any(part.startswith(".") for part in path.parts):
        raise ValueError("Недопустимый путь")
    for index in range(1, len(path.parts) + 1):
        if (root / Path(*path.parts[:index])).is_symlink():
            raise ValueError("Ссылки не перепривязываются")
    target = root / path
    if not target.is_dir():
        raise ValueError("Папка недоступна: " + relative)
    return target


def append(session, phase):
    row = {"time": datetime.now(ZoneInfo("Europe/Moscow")).isoformat(), "phase": phase}
    with (Path(session) / ".journal.jsonl").open("a", encoding="utf-8") as output:
        output.write(json.dumps(row) + "\n")
        output.flush()
        os.fsync(output.fileno())


def check_links(db, source, destination, identity):
    prefixes = (source, destination)
    for row in db.execute("SELECT id,path FROM orders"):
        if row["id"] != identity and any(inside(row["path"], prefix) for prefix in prefixes):
            raise ValueError("Есть другая регистрация по затронутому пути")
    if table(db, "folder_notes"):
        for path, owner in db.execute("SELECT path,parent_order FROM folder_notes"):
            if any(inside(value, prefix) for value in (path, owner) for prefix in prefixes):
                raise ValueError("Есть вложенные заметки; требуется отдельный перенос всех путей")
    if table(db, "todo_missing_folders"):
        for path, owner in db.execute("SELECT path,order_path FROM todo_missing_folders"):
            if any(inside(value, prefix) for value in (path, owner) for prefix in prefixes):
                raise ValueError("Есть сохранённые отсутствующие папки; требуется отдельный перенос")
    if table(db, "todo_catalog") and db.execute("SELECT 1 FROM todo_catalog WHERE path=?", (destination,)).fetchone():
        raise ValueError("По новому пути уже есть другая сводка задач")
    for name in ("event_renames", "folder_renames"):
        if table(db, name):
            for (mappings,) in db.execute(f"SELECT mappings FROM {name} WHERE state='pending'"):
                if any(inside(pair[key], prefix) or inside(prefix, pair[key])
                       for pair in json.loads(mappings) for key in ("source", "destination") for prefix in prefixes):
                    raise ValueError("Сначала завершите прерванное переименование")
    if table(db, "mobile_operations"):
        for (payload,) in db.execute("SELECT payload FROM mobile_operations WHERE status='prepared'"):
            if json.loads(payload).get("order_id") == identity:
                raise ValueError("Сначала завершите подготовленную мобильную операцию")


def update_paths(db, source, destination, identity):
    db.execute("UPDATE orders SET path=?,revision=revision+1,sync_error='' WHERE id=?", (destination, identity))
    if table(db, "invoices"):
        db.execute("UPDATE invoices SET path=?,revision=revision+1 WHERE path=?", (destination, source))
    if table(db, "todo_catalog"):
        db.execute("UPDATE todo_catalog SET path=? WHERE path=?", (destination, source))
    if table(db, "mobile_files"):
        db.execute("UPDATE mobile_files SET scanned=0 WHERE order_id=?", (identity,))


def rebind(store, source, destination, *, perform=False):
    if store.database_only:
        raise ValueError("Прежняя перепривязка по !.txt отключена. Нужен перенос всех связанных путей SQLite")
    import folder_layout as layout
    import order_document as document

    if source == destination or os.path.lexists(store.root / source):
        raise ValueError("Исходная папка ещё существует или путь не изменился")
    store.path(source)
    destination = store.path(destination)
    store.require_order_folder(destination)
    target = checked_folder(store.root, destination)
    with store.connect() as db:
        row = db.execute("SELECT * FROM orders WHERE path=?", (source,)).fetchone()
        if row is None:
            raise ValueError("Исходная запись заказа не найдена")
        original = dict(row)
        check_links(db, source, destination, original["id"])
    if original["revision"] != original["exported_revision"]:
        raise ValueError("Есть невыгруженные изменения; требуется отдельный разбор очереди")
    card = document.load(target, store.labels)
    if card.get("id") != original["id"] or card.get("revision") != original["revision"]:
        raise ValueError("Идентификатор или версия перенесённой карточки не совпали")
    card_hash = hashlib.sha256(document.icloud_access.read_bytes(target / document.DOCUMENT)).hexdigest()
    preview = {"id": original["id"], "source": source, "destination": destination}
    if not perform:
        return preview
    plan = layout.Plan(store.root, [Path(source).parts[0], Path(destination).parts[0]])
    plan.database_paths = True
    before = {"root": str(store.root), "database": str(store.database.resolve()), "order": original,
              **preview, "identity": layout.identity(target), "card_hash": card_hash}
    session = plan.create_session(["Перепривязка заказа после подтверждённого внешнего переноса.",
                                  "Идентичность и все поля сохраняются. Документы не перемещаются.",
                                  "Откат: вернуть папку, затем .restore.py --undo <журнал> --apply."], before)
    shutil.copyfile(__file__, session / ".restore.py")
    with closing(sqlite3.connect(store.database.as_uri() + "?mode=ro", uri=True)) as source_db:
        with closing(sqlite3.connect(session / ".before.sqlite3")) as backup:
            source_db.backup(backup)
    try:
        append(session, "rebind_intent")
        with store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            current = db.execute("SELECT * FROM orders WHERE id=?", (original["id"],)).fetchone()
            if current is None or dict(current) != original:
                raise ValueError("Запись изменилась после подготовки плана")
            check_links(db, source, destination, original["id"])
            if os.path.lexists(store.root / source) or layout.identity(checked_folder(store.root, destination)) != before["identity"]:
                raise ValueError("Папки изменились после подготовки плана")
            if hashlib.sha256(document.icloud_access.read_bytes(target / document.DOCUMENT)).hexdigest() != card_hash:
                raise ValueError("Карточка изменилась после подготовки плана")
            update_paths(db, source, destination, original["id"])
        append(session, "rebind_commit")
        layout.save_json(session / ".result.json", {"status": "rebound", **preview})
    except Exception:
        append(session, "rebind_failed")
        raise
    return {**preview, "journal": str(session)}


def undo(session, *, perform=False):
    session = Path(session)
    before = json.loads((session / ".before.json").read_text())
    if not perform:
        return {"source": before["destination"], "destination": before["source"]}
    root = Path(before["root"])
    target = checked_folder(root, before["source"])
    value = target.lstat()
    identity = {"device": value.st_dev, "inode": value.st_ino, "kind": stat.S_IFMT(value.st_mode)}
    if identity != before["identity"]:
        raise ValueError("На старом месте другая папка; откат остановлен")
    if os.path.lexists(root / before["destination"]):
        raise ValueError("Сначала верните саму папку на старое место")
    with closing(sqlite3.connect(Path(before["database"]).as_uri() + "?mode=rw", uri=True)) as db, db:
        db.row_factory = sqlite3.Row
        db.execute("BEGIN IMMEDIATE")
        current = db.execute("SELECT * FROM orders WHERE id=?", (before["id"],)).fetchone()
        if current and current["path"] == before["source"]:
            return {"restored": 0}
        if not current or current["path"] != before["destination"]:
            raise ValueError("Путь заказа изменился; откат остановлен")
        check_links(db, before["destination"], before["source"], before["id"])
        append(session, "rebind_undo_intent")
        update_paths(db, before["destination"], before["source"], before["id"])
    append(session, "rebind_undone")
    return {"restored": 1}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?")
    parser.add_argument("destination", nargs="?")
    parser.add_argument("--undo", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.undo:
        result = undo(args.undo, perform=args.apply)
    else:
        if not args.source or not args.destination:
            parser.error("Укажите исходный и новый пути")
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        import server
        result = rebind(server.order_store(), args.source, args.destination, perform=args.apply)
    print(json.dumps(result, ensure_ascii=False, indent=2))
