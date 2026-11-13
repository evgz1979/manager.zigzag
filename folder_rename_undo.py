"""Database path rewrite and standalone undo for a folder renamed in the UI."""
import argparse
from contextlib import closing
import importlib.util
import json
from pathlib import Path
import sqlite3
import unicodedata

FILE_TRASH_PATHS_VERSION = 1


# Проверяет принадлежность пути указанной области по границам компонентов.
# Возвращает `path == prefix or path.startswith(prefix + '/')`.
def inside(path, prefix):
    return path == prefix or path.startswith(prefix + "/")


# Проверяет наличие таблицы SQLite перед совместимой перепривязкой.
# Работает с таблицами sqlite_master.
def table(db, name):
    return bool(db.execute("SELECT 1 FROM sqlite_master WHERE name=?", (name,)).fetchone())


# Заменяет только совпадающий префикс пути с учётом границ папок.
# Возвращает `destination + path[len(source):] if inside(path, source) else path`.
def remap(path, source, destination):
    return destination + path[len(source):] if inside(path, source) else path


# Вычисляет затрагиваемые пути SQLite для самостоятельного отката.
# Работает с таблицами folder_renames, metadata_file_moves, metadata_publications.
def metadata_paths(db, source, destination, *, apply=False, file_trash_paths=False):
    """Self-contained: this module is copied into standalone restoration journals."""
    source,destination = (unicodedata.normalize("NFC",value) for value in (source,destination))
    exists = lambda name: db.execute("SELECT 1 FROM sqlite_master WHERE name=?", (name,)).fetchone()
    if exists("folder_renames"):
        for (mappings,) in db.execute("SELECT mappings FROM folder_renames WHERE state='complete'"):
            for pair in json.loads(mappings):
                stored = pair['destination']
                if pair.get('kind') == 'supplier-event-trash' and stored != source and inside(stored, source):
                    raise ValueError("Сначала восстанови события из корзины в этой папке")
    if file_trash_paths:
        remap_file_trash(db, source, destination, apply=apply)
    elif exists("metadata_file_moves"):
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


# Находит записи корзины, затронутые переносом, и проверяет их состояние.
# Файл в общей корзине остаётся на месте, копия счёта внутри объекта переносится вместе с ним.
def remap_file_trash(db, source, destination, *, apply=False):
    if not table(db, "metadata_file_moves"):
        return set()
    destination_key = destination.casefold()
    rows = []
    sessions = set()
    for session, old, stored, state in db.execute("SELECT session,source,destination,state FROM metadata_file_moves"):
        if state != "restored" and (inside(old.casefold(), destination_key) or inside(stored.casefold(), destination_key)):
            raise ValueError("По новому пути есть файл или копия счёта в корзине: " + old)
        if not (inside(old, source) or inside(stored, source)):
            continue
        if state not in ("trashed", "restored"):
            raise ValueError("Перенос файла в корзину или обратно прерван: " + old + ". Заверши его в корзине и повтори перенос объекта")
        new = remap(old, source, destination)
        new_stored = remap(stored, source, destination)
        if new != old and db.execute("SELECT 1 FROM metadata_file_moves WHERE session=? AND source=?", (session, new)).fetchone():
            raise ValueError("В том же сеансе корзины уже есть новый путь: " + new)
        rows.append((session, old, new, new_stored))
        sessions.add(session)
    if apply and rows:
        db.execute("INSERT OR IGNORE INTO metadata_settings VALUES ('file_trash_paths','1')")
        for session, old, new, stored in rows:
            db.execute("UPDATE metadata_file_moves SET source=?,destination=? WHERE session=? AND source=?", (new, stored, session, old))
    return sessions


# Проверяет предпосылки безопасного выполнения операции.
# Работает с таблицами orders, mobile_operations.
def check(db, source, destination, session=None, *, file_trash_paths=False):
    metadata_paths(db,source,destination,file_trash_paths=file_trash_paths)
    for name in ("event_renames", "folder_renames"):
        if table(db, name):
            for other, mappings in db.execute(f"SELECT session,mappings FROM {name} WHERE state='pending'"):
                if other != session and any(inside(pair[key], root) or inside(root, pair[key])
                        for pair in json.loads(mappings) for key in ("source", "destination") for root in (source, destination)):
                    raise ValueError("Сначала завершите переименование из журнала: " + other)
    for name in ("orders", "folder_notes", "todo_catalog", "todo_missing_folders", "client_activity", "object_activity", "invoices", "reconciliations"):
        if table(db, name) and any(inside(row[0], destination) for row in db.execute(f"SELECT path FROM {name}")):
            raise ValueError("По новому пути уже есть сохранённые данные: " + name)
    for name, owner in (("folder_notes", "parent_order"), ("todo_missing_folders", "order_path")):
        if table(db, name) and any(inside(row[1], source) and not inside(row[0], source)
                for row in db.execute(f"SELECT path,{owner} FROM {name}")):
            raise ValueError("Есть связанные данные вне перемещаемого поддерева: " + name)
    identities = {row[0] for row in db.execute("SELECT id,path FROM orders") if inside(row[1], source)}
    if table(db, "mobile_operations") and any(json.loads(row[0]).get("order_id") in identities
            for row in db.execute("SELECT payload FROM mobile_operations WHERE status='prepared'")):
        raise ValueError("Сначала завершите подготовленную операцию iPhone")


# Переписывает связанные пути SQLite в одной внешней транзакции.
# Работает с таблицами reconciliations, orders, folder_notes, todo_missing_folders, mobile_files.
def rewrite(db, source, destination, *, file_trash_paths=False):
    """Called inside one transaction; preserve every field and pending export."""
    metadata_paths(db,source,destination,apply=True,file_trash_paths=file_trash_paths)
    if table(db, 'reconciliations'):
        for identity, path in list(db.execute('SELECT id,path FROM reconciliations')):
            if inside(path, source):
                db.execute('UPDATE reconciliations SET path=?,revision=revision+1 WHERE id=?', (remap(path, source, destination), identity))
    identities = []
    for row in list(db.execute("SELECT id,path FROM orders")):
        if inside(row[1], source):
            db.execute("UPDATE orders SET path=?,revision=revision+1,sync_error='' WHERE id=?",
                       (remap(row[1], source, destination), row[0]))
            identities.append(row[0])
    if table(db, "folder_notes"):
        for identity, path, owner in list(db.execute("SELECT id,path,parent_order FROM folder_notes")):
            if inside(path, source):
                db.execute("UPDATE folder_notes SET path=?,parent_order=?,revision=revision+1,exported_revision=exported_revision+1 WHERE id=?",
                           (remap(path, source, destination), remap(owner, source, destination), identity))
    for name in ("todo_catalog", "todo_missing_folders", "client_activity", "object_activity"):
        if not table(db, name):
            continue
        for (path,) in list(db.execute(f"SELECT path FROM {name}")):
            if not inside(path, source):
                continue
            values = [remap(path, source, destination)]
            extra = ""
            if name == "todo_missing_folders":
                owner = db.execute("SELECT order_path FROM todo_missing_folders WHERE path=?", (path,)).fetchone()[0]
                extra = ",order_path=?"
                values.append(remap(owner, source, destination))
            if name in {"client_activity", "object_activity"}:
                extra = ",revision=revision+1,exported_revision=exported_revision+1"
            db.execute(f"UPDATE {name} SET path=?{extra} WHERE path=?", (*values, path))
    if table(db, "mobile_files"):
        db.executemany("UPDATE mobile_files SET scanned=0 WHERE order_id=?", [(identity,) for identity in identities])
    if table(db, "invoices"):
        for identity, path in list(db.execute("SELECT id,path FROM invoices")):
            if inside(path, source):
                db.execute("UPDATE invoices SET path=?,revision=revision+1 WHERE id=?",
                           (remap(path, source, destination), identity))


# Выполняет сохранённые обратные операции после проверки текущего состояния.
# Работает с таблицами folder_renames.
def undo(session, perform=False, *, database=None):
    session = Path(session)
    meta = json.loads((session / ".folder-paths.json").read_text(encoding="utf-8"))
    spec = importlib.util.spec_from_file_location("folder_layout_restore", session / ".folder-layout.py")
    layout = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(layout)
    if not perform:
        return layout.undo(session)
    mappings = meta.get("mappings") or ([{"source":meta["source"],"destination":meta["destination"]}] if "source" in meta else [])
    database = Path(database).resolve() if database is not None else Path(meta["database"])
    with closing(sqlite3.connect(database.as_uri() + "?mode=rw", uri=True, timeout=15)) as db, db:
        db.row_factory = sqlite3.Row
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT state,paths_applied FROM folder_renames WHERE session=?", (str(session),)).fetchone()
        if not row:
            raise ValueError("В базе нет этой операции. Сохраните базу и журнал")
        if row[0] == "undone":
            return 0
        committed = bool(row[1])
        for pair in mappings:
            source,destination = pair["source"],pair["destination"]
            options = {"file_trash_paths": True} if pair.get("file_trash_paths") else {}
            check(db,destination if committed else source,source if committed else destination,str(session),**options)
        keep = []
        root = Path(layout.load_plan(session)["root"])
        for directory in meta.get("created_years",[]):
            removed = {Path(pair["destination"]).name for pair in mappings if Path(pair["destination"]).parent.as_posix()==directory}
            target = root/directory
            has_files = target.is_dir() and any(item.name not in removed for item in target.iterdir())
            has_data = any(inside(row[0],directory) and not any(inside(row[0],pair["destination"]) for pair in mappings)
                for name in ("orders","folder_notes","metadata_records","client_activity","object_activity","invoices","reconciliations") if table(db,name)
                for row in db.execute(f"SELECT path FROM {name}"))
            if has_files or has_data:
                keep.append(directory)
        db.execute("UPDATE folder_renames SET state='pending' WHERE session=?", (str(session),))
        db.commit()
        db.execute("BEGIN IMMEDIATE")
        options = {"keep_directories":keep} if "created_years" in meta else {}
        count = layout.undo(session, True, coordinate_database=True,**options)
        if committed:
            for pair in reversed(mappings):
                options = {"file_trash_paths": True} if pair.get("file_trash_paths") else {}
                rewrite(db,pair["destination"],pair["source"],**options)
        db.execute("UPDATE folder_renames SET state='undone',paths_applied=0 WHERE session=?", (str(session),))
    return count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print("Обратных переносов:", undo(args.session, args.apply))
