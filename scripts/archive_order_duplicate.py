"""Archive an explicitly reviewed stale registration, retaining the current order.

Requires an old UUID in the current folder's own card history. Never moves or
rewrites document files. The journal copy can undo using only Python's stdlib.
"""
import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import time


def table(db, name):
    return bool(db.execute("SELECT 1 FROM sqlite_master WHERE name=?", (name,)).fetchone())


def inside(path, prefix):
    return path == prefix or path.startswith(prefix + "/")


def append(session, phase):
    with (Path(session) / ".journal.jsonl").open("a", encoding="utf-8") as output:
        output.write(json.dumps({"time": time.time(), "phase": phase}) + "\n")
        output.flush()
        os.fsync(output.fileno())


def source_absent(root, source):
    # Distinguish confirmed absence from an unreadable directory or symlink.
    parts = Path(source).parts
    for index in range(1, len(parts) + 1):
        path = root / Path(*parts[:index])
        try:
            path.lstat()
        except FileNotFoundError:
            return
        if path.is_symlink():
            raise ValueError("Ссылки не обрабатываются")
    raise ValueError("Исходная папка существует; архивирование не разрешено")


def check_links(db, source, identity):
    if table(db, "folder_notes"):
        if any(inside(row[0], source) or inside(row[1], source)
               for row in db.execute("SELECT path,parent_order FROM folder_notes")):
            raise ValueError("По старому пути есть заметки или задачи папок; требуется отдельное согласование")
    if any(row[0] != source and inside(row[0], source) for row in db.execute("SELECT path FROM orders")):
        raise ValueError("В старом поддереве есть другие заказы")
    if table(db, "todo_missing_folders") and any(inside(row[0], source) or inside(row[1], source)
            for row in db.execute("SELECT path,order_path FROM todo_missing_folders")):
        raise ValueError("По старому пути есть сохранённые отсутствующие папки")
    if table(db, "invoices") and db.execute("SELECT 1 FROM invoices WHERE path=?", (source,)).fetchone():
        raise ValueError("У старой записи есть счета; требуется отдельное согласование")
    for name in ("mobile_tasks", "mobile_files"):
        if table(db, name) and db.execute(f"SELECT 1 FROM {name} WHERE order_id=?", (identity,)).fetchone():
            raise ValueError("Есть мобильные идентичности; требуется отдельное согласование")
    if table(db, "mobile_operations") and any(json.loads(row[0]).get("order_id") == identity
            for row in db.execute("SELECT payload FROM mobile_operations")):
        raise ValueError("Есть мобильные операции этого заказа")
    for name in ("event_renames", "folder_renames"):
        if table(db, name) and db.execute(f"SELECT 1 FROM {name} WHERE state='pending'").fetchone():
            raise ValueError("Сначала завершите прерванное переименование")


def covered(source, current):
    """Do not silently discard unique text, money, tasks or unknown sections."""
    if source["note"] and source["note"] != current["note"]:
        raise ValueError("У старой записи есть отдельная заметка")
    for key in ("amount", "costs", "paid"):
        if source[key] is not None and source[key] != current[key]:
            raise ValueError("Финансовые данные различаются: " + key)
    if source["financial_status"] != "unspecified" and source["financial_status"] != current["financial_status"]:
        raise ValueError("Финансовые статусы различаются")
    import order_document as document
    old_blocks, new_blocks = json.loads(source["extra_blocks"]), json.loads(current["extra_blocks"])
    for key, body in old_blocks.items():
        if key == document.TODO_BLOCK:
            old_tasks, new_tasks = document.read_todos(old_blocks), document.read_todos(new_blocks)
            if old_tasks is not None and new_tasks is not None:
                if any(item["text"] not in {task["text"] for task in new_tasks} for item in old_tasks):
                    raise ValueError("У старой записи есть отдельные задачи")
                continue
        if body != new_blocks.get(key):
            raise ValueError("Дополнительный раздел различается: " + key)


def archive(store, source, destination, evidence, *, perform=False):
    if store.database_only:
        raise ValueError("Прежний разбор дублей по !.txt отключён. Нужна проверка всех связанных данных SQLite")
    import folder_layout as layout
    import order_document as document

    source, destination = store.path(source), store.path(destination)
    if source == destination or inside(source, destination) or inside(destination, source):
        raise ValueError("Нужны разные независимые пути заказов")
    source_absent(store.root, source)
    folder = store.target(destination)
    store.require_order_folder(destination)
    proof = Path(evidence)
    if proof.is_absolute() or not proof.parts or proof.parts[0] != ".order-history" or any(part == ".." for part in proof.parts):
        raise ValueError("Укажите карточку из собственной .order-history актуального заказа")
    for index in range(1, len(proof.parts) + 1):
        if (folder / Path(*proof.parts[:index])).is_symlink():
            raise ValueError("История через ссылку не принимается")
    historical = document.parse(document.read_text(folder / proof), store.labels)
    current_card = document.load(folder, store.labels)
    proof_bytes = document.icloud_access.read_bytes(folder / proof)
    card_bytes = document.icloud_access.read_bytes(folder / document.DOCUMENT)
    with store.connect() as db:
        old = db.execute("SELECT * FROM orders WHERE path=?", (source,)).fetchone()
        current = db.execute("SELECT * FROM orders WHERE path=?", (destination,)).fetchone()
        if not old or not current or not old["registered"] or not current["registered"]:
            raise ValueError("Обе записи должны быть зарегистрированы")
        old, current = dict(old), dict(current)
        if any(row["revision"] != row["exported_revision"] or row["export_format"] < document.FORMAT for row in (old, current)):
            raise ValueError("Есть невыгруженные изменения; очередь должна сохраниться до отдельного разбора")
        if historical.get("id") != old["id"] or not 1 <= historical.get("revision", 0) <= old["revision"]:
            raise ValueError("История не подтверждает идентификатор старой записи")
        if current_card.get("id") != current["id"] or current_card.get("revision") != current["revision"]:
            raise ValueError("Карточка актуального заказа не совпадает с базой")
        if current["updated"] < old["updated"]:
            raise ValueError("Актуальная запись старше исходной; требуется отдельный разбор")
        covered(old, current)
        check_links(db, source, old["id"])
        catalog = [dict(row) for row in db.execute("SELECT * FROM todo_catalog WHERE path=?", (source,))] if table(db, "todo_catalog") else []
    preview = {"source": source, "destination": destination, "archived_id": old["id"], "canonical_id": current["id"]}
    if not perform:
        return preview
    plan = layout.Plan(store.root, [Path(source).parts[0], Path(destination).parts[0]])
    plan.database_paths = True
    before = {"root": str(store.root), "database": str(store.database.resolve()), "old": old,
              "current": current, "catalog": catalog, "evidence": proof.as_posix(), **preview,
              "card_hash": hashlib.sha256(card_bytes).hexdigest(), "proof_hash": hashlib.sha256(proof_bytes).hexdigest()}
    session = plan.create_session(["Архивирование подтверждённой устаревшей регистрации после переименования.",
                                  "Старая запись целиком сохраняется в SQLite и журнале; актуальная не меняется.",
                                  "Документы не перемещаются. Откат: .restore.py --undo <журнал> --apply."], before)
    shutil.copyfile(__file__, session / ".restore.py")
    (session / ".old-card.txt").write_bytes(proof_bytes)
    (session / ".current-card.txt").write_bytes(card_bytes)
    with closing(sqlite3.connect(store.database.resolve().as_uri() + "?mode=ro", uri=True)) as original:
        with closing(sqlite3.connect(session / ".before.sqlite3")) as backup:
            original.backup(backup)
    append(session, "archive_intent")
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        for expected in (old, current):
            row = db.execute("SELECT * FROM orders WHERE id=?", (expected["id"],)).fetchone()
            if not row or dict(row) != expected:
                raise ValueError("Запись изменилась после подготовки плана")
        source_absent(store.root, source)
        if hashlib.sha256(document.icloud_access.read_bytes(store.target(destination) / document.DOCUMENT)).hexdigest() != before["card_hash"]:
            raise ValueError("Карточка изменилась перед архивированием")
        if hashlib.sha256(document.icloud_access.read_bytes(folder / proof)).hexdigest() != before["proof_hash"]:
            raise ValueError("История изменилась перед архивированием")
        check_links(db, source, old["id"])
        db.execute("""CREATE TABLE IF NOT EXISTS order_duplicate_archive (
            id TEXT PRIMARY KEY, canonical_id TEXT NOT NULL, record TEXT NOT NULL,
            journal TEXT NOT NULL, archived REAL NOT NULL, state TEXT NOT NULL)""")
        db.execute("INSERT INTO order_duplicate_archive VALUES (?,?,?,?,?,'archived')",
                   (old["id"], current["id"], json.dumps(old, ensure_ascii=False), str(session), time.time()))
        db.execute("DELETE FROM orders WHERE id=?", (old["id"],))
        if table(db, "todo_catalog"):
            db.execute("DELETE FROM todo_catalog WHERE path=?", (source,))
    append(session, "archive_commit")
    layout.save_json(session / ".result.json", {"status": "archived", **preview})
    return {**preview, "journal": str(session)}


def undo(session, *, perform=False):
    session = Path(session)
    before = json.loads((session / ".before.json").read_text(encoding="utf-8"))
    if not perform:
        return {"restore": before["source"], "keep": before["destination"]}
    old = before["old"]
    with closing(sqlite3.connect(Path(before["database"]).as_uri() + "?mode=rw", uri=True)) as db, db:
        db.row_factory = sqlite3.Row
        db.execute("BEGIN IMMEDIATE")
        saved = db.execute("SELECT * FROM order_duplicate_archive WHERE id=?", (old["id"],)).fetchone()
        if not saved or saved["journal"] != str(session):
            raise ValueError("Архив не соответствует журналу")
        if saved["state"] == "undone":
            return {"restored": 0}
        if db.execute("SELECT 1 FROM orders WHERE path=? OR id=?", (old["path"], old["id"])).fetchone():
            raise ValueError("Путь или идентификатор заняты; откат остановлен без перезаписи")
        check_links(db, old["path"], old["id"])
        for item in before["catalog"]:
            if db.execute("SELECT 1 FROM todo_catalog WHERE path=?", (item["path"],)).fetchone():
                raise ValueError("По старому пути появилась другая сводка задач")
        append(session, "archive_undo_intent")
        keys = list(old)
        db.execute("INSERT INTO orders (" + ",".join(keys) + ") VALUES (" + ",".join("?" for _ in keys) + ")", [old[key] for key in keys])
        for item in before["catalog"]:
            db.execute("INSERT INTO todo_catalog (path,checked,error) VALUES (?,?,?)", (item["path"], item["checked"], item["error"]))
        db.execute("UPDATE order_duplicate_archive SET state='undone' WHERE id=?", (old["id"],))
    append(session, "archive_undone")
    return {"restored": 1}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?")
    parser.add_argument("destination", nargs="?")
    parser.add_argument("--evidence")
    parser.add_argument("--undo", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.undo:
        result = undo(args.undo, perform=args.apply)
    else:
        if not args.source or not args.destination or not args.evidence:
            parser.error("Укажите старый путь, актуальный путь и --evidence")
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        import server
        result = archive(server.order_store(), args.source, args.destination, args.evidence, perform=args.apply)
    print(json.dumps(result, ensure_ascii=False, indent=2))
