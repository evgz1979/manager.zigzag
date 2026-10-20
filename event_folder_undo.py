"""Откат переименования событий с сохранением путей заметок SQLite; копируется в журнал."""
import argparse
import importlib.util
import json
import sqlite3
import unicodedata
from contextlib import closing
from pathlib import Path


class EventRenamePending(ValueError):
    pass


def inside(path, prefix):
    return path == prefix or path.startswith(prefix + "/")


def assert_unlocked(db, path, *, include_children=False):
    for name in ("event_renames", "folder_renames"):
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name=?", (name,)).fetchone():
            continue
        for session, mappings in db.execute(f"SELECT session,mappings FROM {name} WHERE state='pending'"):
            if any(inside(path, pair[key]) or (include_children and (not path or inside(pair[key], path)))
                   for pair in json.loads(mappings) for key in ("source", "destination")):
                raise EventRenamePending("Переименование прервано. Данные сохранены; выполните откат из журнала: " + session)


def guard_database(database, path, *, include_children=False):
    if not isinstance(path, str):
        raise ValueError("Укажите путь папки")
    if Path(database).exists():
        with closing(sqlite3.connect(Path(database).resolve().as_uri() + "?mode=ro", uri=True, timeout=15)) as db:
            assert_unlocked(db, path, include_children=include_children)


def metadata_paths(db, source, destination, *, apply=False):
    """Self-contained: this module is copied into standalone restoration journals."""
    source,destination = (unicodedata.normalize("NFC",value) for value in (source,destination))
    exists = lambda name: db.execute("SELECT 1 FROM sqlite_master WHERE name=?", (name,)).fetchone()
    if exists("metadata_file_moves"):
        for old, new in db.execute("SELECT source,destination FROM metadata_file_moves WHERE state!='restored'"):
            if any(inside(path, root) for path in (old,new) for root in (source,destination)):
                raise ValueError("Сначала восстанови файлы из корзины в этой папке")
    for name in ("metadata_records", "metadata_imports", "metadata_publications"):
        if not exists(name):
            continue
        if any(inside(row[0], destination) for row in db.execute(f"SELECT path FROM {name}")):
            raise ValueError("По новому пути есть данные базы: " + name)
        if not apply:
            continue
        columns = "rowid,path" + (",source" if name=="metadata_publications" else "")
        for row in list(db.execute(f"SELECT {columns} FROM {name}")):
            if inside(row[1], source):
                extra = ",revision=revision+1" if name=="metadata_records" else ""
                db.execute(f"UPDATE {name} SET path=?{extra} WHERE rowid=?", (destination+row[1][len(source):],row[0]))
            if name=="metadata_publications" and inside(row[2],source):
                db.execute("UPDATE metadata_publications SET source=? WHERE rowid=?", (destination+row[2][len(source):],row[0]))


def schema(db):
    db.execute("CREATE TABLE IF NOT EXISTS event_renames (session TEXT PRIMARY KEY,state TEXT NOT NULL,mappings TEXT NOT NULL,paths_applied INTEGER NOT NULL DEFAULT 0)")
    if "paths_applied" not in {row[1] for row in db.execute("PRAGMA table_info(event_renames)")}:
        db.execute("ALTER TABLE event_renames ADD COLUMN paths_applied INTEGER NOT NULL DEFAULT 0")
        db.execute("UPDATE event_renames SET paths_applied=1 WHERE state='complete'")


def undo(session, perform=False):
    session = Path(session)
    meta = json.loads((session / ".event-paths.json").read_text())
    spec = importlib.util.spec_from_file_location("event_layout_restore", session / ".folder-layout.py")
    layout = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(layout)
    if not perform:
        return layout.undo(session)
    database = Path(meta["database"])
    # Никогда не создавать пустую базу вместо прежней рабочей.
    with closing(sqlite3.connect(database.as_uri() + "?mode=rw", uri=True, timeout=15)) as db, db:
        db.row_factory = sqlite3.Row
        db.execute("BEGIN IMMEDIATE")
        schema(db)
        operation = db.execute("SELECT state,paths_applied FROM event_renames WHERE session=?", (str(session),)).fetchone()
        if not operation:
            raise ValueError("В базе нет операции переименования; сохраните базу и журнал для разбора")
        if operation[0] == "undone":
            return 0
        pairs = meta["mappings"]
        roots = [pair[key] for pair in pairs for key in ("source", "destination")]
        # Незавершённая другая операция или старые регистрации требуют отдельного разбора.
        for name in ("event_renames", "folder_renames"):
            if not db.execute("SELECT 1 FROM sqlite_master WHERE name=?", (name,)).fetchone():
                continue
            for other, mappings in db.execute(f"SELECT session,mappings FROM {name} WHERE state='pending'"):
                if other != str(session) and any(inside(pair[key], root) or inside(root, pair[key])
                        for pair in json.loads(mappings) for key in ("source", "destination") for root in roots):
                    raise ValueError("Сначала завершите другую операцию: " + other)
        if any(inside(row[0], root) for row in db.execute("SELECT path FROM orders") for root in roots):
            raise ValueError("Во вложенной папке появилась регистрация заказа; откат остановлен")
        updates = []
        if operation[1]:
            for pair in pairs:
                metadata_paths(db,pair["destination"],pair["source"])
        rows = db.execute("SELECT id,path FROM folder_notes").fetchall() if operation[1] else []
        for row in rows:
            for pair in pairs:
                if inside(row["path"], pair["destination"]):
                    old = pair["source"] + row["path"][len(pair["destination"]):]
                    if db.execute("SELECT 1 FROM folder_notes WHERE path=?", (old,)).fetchone():
                        raise ValueError("По исходному пути есть другая заметка; откат остановлен: " + old)
                    updates.append((old, row["id"]))
                    break
        # Блокировка переживает сбой во время обратных переносов и откат транзакции.
        db.execute("UPDATE event_renames SET state='pending' WHERE session=?", (str(session),))
        db.commit()
        db.execute("BEGIN IMMEDIATE")
        count = layout.undo(session, True, coordinate_database=True)
        for old, identity in updates:
            db.execute("UPDATE folder_notes SET path=?,revision=revision+1,exported_revision=exported_revision+1 WHERE id=?", (old, identity))
        if operation[1]:
            for pair in pairs:
                metadata_paths(db,pair["destination"],pair["source"],apply=True)
        db.execute("UPDATE event_renames SET state='undone',paths_applied=0 WHERE session=?", (str(session),))
    return count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print("Обратных переносов:", undo(args.session, args.apply))
