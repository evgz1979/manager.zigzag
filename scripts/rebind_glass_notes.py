"""Явная перепривязка выгруженных заметок после переноса # glass в # work.

Без --apply показывает план. Копия в журнале самостоятельно откатывает пути
SQLite после обратного переноса папки пользователем; документы не меняются.
"""
import argparse
from contextlib import closing
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import sqlite3
import sys
from zoneinfo import ZoneInfo


def append_journal(session, record):
    record = {"time": datetime.now(ZoneInfo("Europe/Moscow")).isoformat(), **record}
    with (Path(session) / ".journal.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def inside(path, prefix):
    return path == prefix or path.startswith(prefix + "/")


def checked_folder(root, relative):
    path = Path(relative)
    if path.is_absolute() or not path.parts or any(part.startswith(".") for part in path.parts):
        raise ValueError("Недопустимый путь папки")
    for index in range(1, len(path.parts) + 1):
        if (root / Path(*path.parts[:index])).is_symlink():
            raise ValueError("Символические ссылки не перепривязываются")
    target = root / path
    if not target.is_dir():
        raise ValueError("Папка недоступна: " + relative)
    return target


def check_database(db, source, destination):
    if any(inside(row[0], prefix) for row in db.execute("SELECT path FROM orders") for prefix in (source, destination)):
        raise ValueError("В поддереве есть регистрация заказа; требуется отдельный перенос базы")
    for name in ("event_renames", "folder_renames"):
        if db.execute("SELECT 1 FROM sqlite_master WHERE name=?", (name,)).fetchone():
            for (mappings,) in db.execute(f"SELECT mappings FROM {name} WHERE state='pending'"):
                if any(inside(pair[key], prefix) or inside(prefix, pair[key])
                       for pair in json.loads(mappings) for key in ("source", "destination") for prefix in (source, destination)):
                    raise ValueError("Сначала завершите прерванное переименование")


def rebind(notes, source="# glass", destination="# work/# glass", *, perform=False):
    import folder_layout as layout
    from folder_notes import file_revision
    from folder_structure import supplier_prefix

    if (Path(source).parts != supplier_prefix(source) or len(Path(source).parts) != 1
            or Path(destination).parts != supplier_prefix(destination) or len(Path(destination).parts) != 2):
        raise ValueError("Разрешён только явный перенос корневой # glass в # work/# glass")
    root = notes.store.root
    if os.path.lexists(root / source):
        raise ValueError("Исходная папка ещё существует; перепривязка не выполняется")
    checked_folder(root, destination)
    with notes.connect() as db:
        check_database(db, source, destination)
        rows = [dict(row) for row in db.execute("SELECT * FROM folder_notes") if inside(row["path"], source)]
        if any(inside(row[0], destination) for row in db.execute("SELECT path FROM folder_notes")):
            raise ValueError("По новому пути уже есть заметки; автоматическое объединение запрещено")
    changes = []
    for row in rows:
        if row["revision"] != row["exported_revision"]:
            raise ValueError("Есть невыгруженная заметка; сначала требуется отдельный разбор очереди")
        path = destination + row["path"][len(source):]
        target = checked_folder(root, path)
        if file_revision(target) != row["file_revision"]:
            raise ValueError("Перенесённый !.txt отличается от выгруженной версии: " + path)
        if not inside(row["parent_order"], source):
            raise ValueError("Заметка относится к другому заказу")
        changes.append({"id": row["id"], "source": row["path"], "destination": path,
                        "parent_order": destination + row["parent_order"][len(source):]})
    preview = {"count": len(changes), "changes": changes}
    if not perform or not changes:
        return preview
    plan = layout.Plan(root, [source, Path(destination).parts[0]])
    plan.database_paths = True
    before = {"root": str(root), "database": str(notes.store.database.resolve()), "source": source,
              "destination": destination, "rows": rows, "changes": changes}
    session = plan.create_session(["Перепривязать пути заметок после явно указанного пользователем переноса.",
                                  "Документы и содержимое заметок не меняются.",
                                  "Откат: сначала вернуть папку на прежнее место, затем .restore.py <журнал> --apply."], before)
    shutil.copyfile(__file__, session / ".restore.py")
    try:
        with closing(sqlite3.connect(notes.store.database.as_uri() + "?mode=ro", uri=True)) as original:
            with closing(sqlite3.connect(session / ".before.sqlite3")) as backup:
                original.backup(backup)
        layout.append(session, {"phase": "rebind_intent", "changes": changes})
        with notes.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            check_database(db, source, destination)
            current = [dict(row) for row in db.execute("SELECT * FROM folder_notes") if inside(row["path"], source)]
            if sorted(current, key=lambda row: row["id"]) != sorted(rows, key=lambda row: row["id"]):
                raise ValueError("Заметки изменились после подготовки плана")
            if any(inside(row[0], destination) for row in db.execute("SELECT path FROM folder_notes")):
                raise ValueError("По новому пути появились заметки; данные сохранены без объединения")
            if os.path.lexists(root / source):
                raise ValueError("Исходная папка появилась вновь")
            for row, change in zip(rows, changes):
                if file_revision(checked_folder(root, change["destination"])) != row["file_revision"]:
                    raise ValueError("Файл изменился перед перепривязкой")
                db.execute("UPDATE folder_notes SET path=?,parent_order=?,revision=revision+1,exported_revision=exported_revision+1 WHERE id=?",
                           (change["destination"], change["parent_order"], change["id"]))
        layout.append(session, {"phase": "rebind_commit", "count": len(changes)})
        layout.save_json(session / ".result.json", {"status": "rebound", **preview})
    except Exception as error:
        layout.append(session, {"phase": "rebind_failed", "error": str(error)})
        raise
    return {**preview, "journal": str(session)}


def undo(session, *, perform=False):
    session = Path(session)
    before = json.loads((session / ".before.json").read_text())
    if not perform:
        return {"count": len(before["changes"]), "action": "Вернуть пути заметок после обратного переноса папки"}
    root = Path(before["root"])
    checked_folder(root, before["source"])
    if os.path.lexists(root / before["destination"]):
        raise ValueError("Сначала верните саму папку на прежнее место; документы не перемещаются этим скриптом")
    with closing(sqlite3.connect(Path(before["database"]).as_uri() + "?mode=rw", uri=True)) as db, db:
        db.row_factory = sqlite3.Row
        db.execute("BEGIN IMMEDIATE")
        check_database(db, before["source"], before["destination"])
        updates = []
        for change, old in zip(before["changes"], before["rows"]):
            row = db.execute("SELECT * FROM folder_notes WHERE id=?", (change["id"],)).fetchone()
            if row and row["path"] == change["source"] and row["parent_order"] == old["parent_order"]:
                continue
            if not row or row["path"] != change["destination"] or row["parent_order"] != change["parent_order"]:
                raise ValueError("Привязка заметки изменилась; откат остановлен")
            if db.execute("SELECT 1 FROM folder_notes WHERE path=?", (change["source"],)).fetchone():
                raise ValueError("По прежнему пути есть другая заметка; откат остановлен")
            checked_folder(root, change["source"])
            updates.append((change["source"], old["parent_order"], change["id"]))
        append_journal(session, {"phase": "rebind_undo_intent", "count": len(updates)})
        db.executemany("UPDATE folder_notes SET path=?,parent_order=?,revision=revision+1,exported_revision=exported_revision+1 WHERE id=?", updates)
    append_journal(session, {"phase": "rebind_undone", "count": len(updates)})
    return {"restored": len(updates)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session", nargs="?", help="Журнал для отката; без него готовится перепривязка")
    parser.add_argument("--apply", action="store_true")
    arguments = parser.parse_args()
    if arguments.session:
        result = undo(arguments.session, perform=arguments.apply)
    else:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        import server
        result = rebind(server.folder_note_store(), perform=arguments.apply)
    print(json.dumps(result, ensure_ascii=False, indent=2))
