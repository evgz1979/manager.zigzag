"""Откат переименования событий с сохранением путей заметок SQLite; копируется в журнал."""
import argparse
import importlib.util
import json
import sqlite3
from contextlib import closing
from pathlib import Path


class EventRenamePending(ValueError):
    pass


def inside(path, prefix):
    return path == prefix or path.startswith(prefix + "/")


def assert_unlocked(db, path, *, include_children=False):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='event_renames'").fetchone():
        return
    for session, mappings in db.execute("SELECT session,mappings FROM event_renames WHERE state='pending'"):
        if any(inside(path, pair[key]) or (include_children and inside(pair[key], path))
               for pair in json.loads(mappings) for key in ("source", "destination")):
            raise EventRenamePending("Переименование прервано. Данные сохранены; выполните откат из журнала: " + session)


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
        operation = db.execute("SELECT state FROM event_renames WHERE session=?", (str(session),)).fetchone()
        if not operation:
            raise ValueError("В базе нет операции переименования; сохраните базу и журнал для разбора")
        if operation[0] == "undone":
            return 0
        pairs = meta["mappings"]
        roots = [pair[key] for pair in pairs for key in ("source", "destination")]
        # Незавершённая другая операция или старые регистрации требуют отдельного разбора.
        for other, mappings in db.execute("SELECT session,mappings FROM event_renames WHERE state='pending'"):
            if other != str(session) and any(inside(pair[key], root) or inside(root, pair[key])
                    for pair in json.loads(mappings) for key in ("source", "destination") for root in roots):
                raise ValueError("Сначала завершите другую операцию: " + other)
        if any(inside(row[0], root) for row in db.execute("SELECT path FROM orders") for root in roots):
            raise ValueError("Во вложенной папке появилась регистрация заказа; откат остановлен")
        updates = []
        rows = db.execute("SELECT id,path FROM folder_notes").fetchall()
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
        db.execute("UPDATE event_renames SET state='undone' WHERE session=?", (str(session),))
    return count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print("Обратных переносов:", undo(args.session, args.apply))
