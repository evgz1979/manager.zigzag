"""Register only folders explicitly created by the manager; retry from SQLite."""
import json
import time
import uuid
from pathlib import Path

import folder_layout as layout
import local_metadata
from event_folder_undo import assert_unlocked
from folder_structure import in_reconciliations

KIND = "order_creation"


def complete_service_folders(store, path, session, plan, journal):
    """Finish only our missing mkdir steps after the order folder is proven owned."""
    completed = {item['id']: item for item in journal if item['phase'] == 'commit'}
    for index, operation in enumerate(plan['operations'], 1):
        relative = operation['destination']
        if Path(relative).parent.as_posix() != path:
            continue
        if operation['operation'] != 'mkdir' or Path(relative).name not in {'# bills', '# cdr'}:
            raise ValueError('Неизвестный шаг создания служебной папки; проверь журнал')
        target = layout.safe_path(store.root, relative, plan['clients'], service_roots=plan.get('service_roots', ()))
        if index in completed:
            if not target.is_dir() or layout.identity(target) != completed[index]['identity']:
                raise ValueError('Служебная папка была заменена после создания: ' + relative)
            continue
        if layout.exists(target):
            raise ValueError('Путь служебной папки занят без подтверждения в журнале: ' + relative)
        layout.append(session, {'phase': 'intent', 'id': index, **operation})
        target.mkdir()
        layout.append(session, {'phase': 'commit', 'id': index, 'identity': layout.identity(target)})
    if not any(item['phase'] == 'complete' for item in journal):
        layout.append(session, {'phase': 'complete', 'operations': len(plan['operations'])})


def prepare(store, path, title, session):
    data = {"state": "pending", "title": title, "order_id": str(uuid.uuid4()),
            "session": str(session.resolve()), "error": ""}
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        local_metadata.schema(db)
        assert_unlocked(db, path)
        if db.execute("SELECT 1 FROM orders WHERE path=?", (path,)).fetchone():
            raise ValueError("По этому пути уже сохранён заказ. Открой прежнюю карточку; новая папка не создана")
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for table in ("orders", "folder_notes", "metadata_records", "metadata_publications", "invoices", "reconciliations"):
            if table not in tables:
                continue
            for saved in db.execute(f"SELECT * FROM {table} WHERE path=? OR substr(path,1,?)=?", (path, len(path) + 1, path + '/')):
                if table == 'metadata_records' and saved['kind'] == KIND and saved['path'] == path:
                    continue
                raise ValueError("По этому пути уже сохранены данные. Новая папка не создана: " + path)
        previous = db.execute("SELECT data FROM metadata_records WHERE kind=? AND path=?", (KIND, path)).fetchone()
        if previous and json.loads(previous[0])["state"] != "failed":
            raise ValueError("По этому пути уже есть операция создания. Открой папку или проверь её журнал")
        db.execute("""INSERT INTO metadata_records VALUES (?,?,?,?,1,?)
            ON CONFLICT(kind,path) DO UPDATE SET data=excluded.data,revision=metadata_records.revision+1,updated=excluded.updated""",
            (str(uuid.uuid4()), KIND, path, json.dumps(data, ensure_ascii=False), time.time()))


def register(store, path):
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT data FROM metadata_records WHERE kind=? AND path=?", (KIND, path)).fetchone()
        data = json.loads(row[0])
        assert_unlocked(db, path)
        if data["state"] == "complete":
            return
        session = Path(data["session"])
        plan = layout.load_plan(session)
        if Path(plan["root"]).resolve() != store.root.resolve():
            raise ValueError("Корень журнала создания не совпадает с рабочим каталогом")
        journal = layout.records(session)
        operation_id = next((i for i, operation in enumerate(plan["operations"], 1) if operation["destination"] == path), None)
        if operation_id is None:
            raise ValueError("Путь заказа изменился после создания; проверь журнал перед регистрацией")
        committed = next((item for item in journal if item["phase"] == "commit" and item["id"] == operation_id), None)
        if not committed or any(item["phase"] == "undone" for item in journal):
            raise ValueError("Создание папки не подтверждено журналом; автоматическая регистрация остановлена")
        target = store.target(path)
        if layout.identity(target) != committed["identity"]:
            raise ValueError("Папка была заменена после создания; автоматическая регистрация остановлена")
        complete_service_folders(store, path, session, plan, journal)
        if in_reconciliations(path):
            import reconciliations
            existing = db.execute('SELECT id FROM reconciliations WHERE path=?', (path,)).fetchone()
            if existing and existing['id'] != data['order_id']:
                raise ValueError('По этому пути уже сохранена другая сверка')
            if not existing:
                reconciliations.insert(db, path, data['title'], data['order_id'])
        else:
            store.require_order_folder(path)
        existing = db.execute("SELECT id FROM orders WHERE path=?", (path,)).fetchone()
        if existing and existing["id"] != data["order_id"]:
            raise ValueError("Путь уже связан с другим заказом; его карточка сохранена")
        if not existing and not in_reconciliations(path):
            db.execute("""INSERT INTO orders (path,id,title,status,financial_status,note,amount,costs,paid,revision,updated,extra_blocks)
                VALUES (?,?,?,'new','unspecified','',NULL,NULL,NULL,1,?,'{}')""",
                (path, data["order_id"], data["title"], time.time()))
        data.update(state="complete", error="")
        db.execute("UPDATE metadata_records SET data=?,revision=revision+1,updated=? WHERE kind=? AND path=?",
                   (json.dumps(data, ensure_ascii=False), time.time(), KIND, path))
        db.execute("DELETE FROM metadata_imports WHERE kind=? AND path=?", (KIND, path))


def failed(store, path, error):
    """Keep a retry only when this journal proves ownership of the new folder."""
    with store.connect() as db:
        row = db.execute("SELECT data FROM metadata_records WHERE kind=? AND path=?", (KIND, path)).fetchone()
        if not row:
            return
        data = json.loads(row[0])
        if data["state"] == "complete":
            return
        session = Path(data["session"])
        plan = layout.load_plan(session)
        operation_id = next((i for i, operation in enumerate(plan["operations"], 1) if operation["destination"] == path), None)
        committed = any(item["phase"] == "commit" and item["id"] == operation_id for item in layout.records(session))
        data.update(state="pending" if committed else "failed", error=str(error))
        db.execute("UPDATE metadata_records SET data=?,revision=revision+1,updated=? WHERE kind=? AND path=?",
                   (json.dumps(data, ensure_ascii=False), time.time(), KIND, path))


def recover(store):
    import order_folders
    if not store.database.exists():
        return
    with order_folders.LOCK:
        with store.connect() as db:
            local_metadata.schema(db)
            pending = [row["path"] for row in db.execute("SELECT path FROM metadata_records WHERE kind=? AND json_extract(data,'$.state')='pending'", (KIND,))]
        for path in pending:
            try:
                register(store, path)
            except (OSError, ValueError) as error:
                failed(store, path, error)
                local_metadata.MetadataStore(store).error(KIND, path, error)


def retry_one(store, path):
    """An explicit Add action finishes our pending creation with the same UUID."""
    import order_folders
    with order_folders.LOCK, store.connect() as db:
        local_metadata.schema(db)
        row = db.execute("SELECT data FROM metadata_records WHERE kind=? AND path=?", (KIND, path)).fetchone()
        pending = row and json.loads(row[0])["state"] == "pending"
    if pending:
        with order_folders.LOCK:
            register(store, path)
