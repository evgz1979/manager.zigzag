"""SQLite working metadata; legacy files are read only during migration."""
import hashlib
import json
import os
import sqlite3
import threading
import time
import unicodedata
import uuid
from contextlib import contextmanager, closing
from pathlib import Path

import icloud_access
from event_folder_undo import assert_unlocked

MIGRATION_LOCK = threading.Lock()
PUBLICATION_LOCK = threading.Lock()


def schema(db):
    db.execute("CREATE TABLE IF NOT EXISTS metadata_settings (key TEXT PRIMARY KEY,value TEXT NOT NULL)")
    if not db.execute("SELECT 1 FROM metadata_settings WHERE key='storage_version'").fetchone():
        db.execute("INSERT INTO metadata_settings VALUES ('storage_version','1')")
    db.execute("""CREATE TABLE IF NOT EXISTS metadata_records (
        id TEXT NOT NULL UNIQUE,kind TEXT NOT NULL,path TEXT NOT NULL,data TEXT NOT NULL,
        revision INTEGER NOT NULL,updated REAL NOT NULL,PRIMARY KEY(kind,path))""")
    db.execute("""CREATE TABLE IF NOT EXISTS metadata_history (
        seq INTEGER PRIMARY KEY,entity TEXT NOT NULL,identity TEXT NOT NULL,data TEXT NOT NULL,saved REAL NOT NULL)""")
    db.execute("""CREATE TABLE IF NOT EXISTS legacy_documents (
        path TEXT NOT NULL,digest TEXT NOT NULL,body BLOB NOT NULL,saved REAL NOT NULL,PRIMARY KEY(path,digest))""")
    db.execute("""CREATE TABLE IF NOT EXISTS metadata_imports (
        kind TEXT NOT NULL,path TEXT NOT NULL,error TEXT NOT NULL,attempted REAL NOT NULL,PRIMARY KEY(kind,path))""")
    db.execute("""CREATE TABLE IF NOT EXISTS metadata_publications (
        id TEXT PRIMARY KEY,source TEXT NOT NULL,revision TEXT NOT NULL,path TEXT NOT NULL,body BLOB NOT NULL,
        published INTEGER NOT NULL DEFAULT 0,error TEXT NOT NULL DEFAULT '',UNIQUE(source,revision))""")
    db.execute("""CREATE TABLE IF NOT EXISTS metadata_file_moves (
        session TEXT NOT NULL,source TEXT NOT NULL,destination TEXT NOT NULL,state TEXT NOT NULL,
        PRIMARY KEY(session,source))""")


def audit(db, table):
    """Triggers also preserve edits made by standalone rename/restore tools."""
    columns = [row[1] for row in db.execute(f"PRAGMA table_info({table})")]
    if not columns:
        return
    identity = "id" if "id" in columns else "path"
    payload = "json_object(" + ",".join("'" + col + "',OLD." + col for col in columns) + ")"
    for event in ("UPDATE", "DELETE"):
        db.execute(f"""CREATE TRIGGER IF NOT EXISTS metadata_audit_{table}_{event}
            BEFORE {event} ON {table} BEGIN
            INSERT INTO metadata_history(entity,identity,data,saved)
            VALUES ('{table}',OLD.{identity},{payload},strftime('%s','now')); END""")


class MetadataStore:
    def __init__(self, store):
        self.store = store
        self.root = store.root

    def key(self, file):
        # Lexical path normalization does not require iCloud or the original file.
        root = Path(os.path.abspath(self.root))
        path = Path(os.path.abspath(file))
        try:
            relative = path.relative_to(root).as_posix()
        except ValueError:
            raise ValueError("Путь за пределами папки документов")
        return unicodedata.normalize("NFC", relative)

    @contextmanager
    def connect(self):
        with self.store.connect() as db:
            schema(db)
            yield db

    @staticmethod
    def record(row):
        if row is None:
            return None
        return {**json.loads(row["data"]), "revision": f"{row['id']}:{row['revision']}",
                "updated": row["updated"], "path": row["path"]}

    def get(self, kind, path):
        path = unicodedata.normalize("NFC",path)
        with self.connect() as db:
            assert_unlocked(db, path)
            if db.execute("SELECT 1 FROM metadata_file_moves WHERE state='pending' AND (source=? OR destination=?)", (path,path)).fetchone():
                raise ValueError("Перенос файла прерван. Восстанови операцию через корзину")
            return self.record(db.execute("SELECT * FROM metadata_records WHERE kind=? AND path=?", (kind,path)).fetchone())

    def put(self, kind, path, data, revision):
        path = unicodedata.normalize("NFC",path)
        from file_comments import FileCommentConflict
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            assert_unlocked(db, path)
            if db.execute("SELECT 1 FROM metadata_file_moves WHERE state='pending' AND (source=? OR destination=?)", (path,path)).fetchone():
                raise ValueError("Перенос файла прерван. Восстанови операцию через корзину")
            row = db.execute("SELECT * FROM metadata_records WHERE kind=? AND path=?", (kind,path)).fetchone()
            current = self.record(row)
            if (current["revision"] if current else "missing") != revision:
                raise FileCommentConflict("Данные изменились в другом окне. Твой ввод остался в поле; обнови данные перед сохранением")
            if row:
                db.execute("UPDATE metadata_records SET data=?,revision=revision+1,updated=? WHERE kind=? AND path=?",
                           (json.dumps(data,ensure_ascii=False),time.time(),kind,path))
            else:
                db.execute("INSERT INTO metadata_records VALUES (?,?,?,?,1,?)", (str(uuid.uuid4()),kind,path,json.dumps(data,ensure_ascii=False),time.time()))
            return self.record(db.execute("SELECT * FROM metadata_records WHERE kind=? AND path=?", (kind,path)).fetchone())

    def archive(self, file):
        raw = icloud_access.read_bytes(file)
        path = self.key(file)
        with self.connect() as db:
            db.execute("INSERT OR IGNORE INTO legacy_documents VALUES (?,?,?,?)", (path,hashlib.sha256(raw).hexdigest(),raw,time.time()))
        return raw

    def error(self, kind, path, error):
        path = unicodedata.normalize("NFC",path)
        with self.connect() as db:
            db.execute("INSERT OR REPLACE INTO metadata_imports VALUES (?,?,?,?)", (kind,path,str(error),time.time()))

    def imported(self, kind, path):
        self.error(kind,path,"")

    def complete(self,kind,path):
        path = unicodedata.normalize("NFC",path)
        with self.connect() as db:
            return bool(db.execute("SELECT 1 FROM metadata_imports WHERE kind=? AND path=? AND error=''",(kind,path)).fetchone())

    def backup(self,reason="daily"):
        folder = self.store.database.parent/"backups"
        folder.mkdir(exist_ok=True)
        target = folder/(self.store.database.stem+"-"+time.strftime("%Y-%m-%d")+"-"+reason+".sqlite3")
        if target.exists():
            return target
        temporary = target.with_suffix(".tmp-"+uuid.uuid4().hex)
        try:
            with closing(sqlite3.connect(self.store.database.resolve().as_uri()+"?mode=ro",uri=True)) as source:
                with closing(sqlite3.connect(temporary)) as destination:
                    source.backup(destination)
                    if destination.execute("PRAGMA quick_check").fetchone()[0]!="ok":
                        raise ValueError("Проверка резервной копии базы не пройдена")
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
        return target

    def comment(self, file):
        import file_comments
        with file_comments.LOCK:
            return self._comment(file)

    def _comment(self,file):
        import file_comments
        path = self.key(file)
        current = self.get("comment",path)
        if current:
            return {"comment":current["comment"],"revision":current["revision"]}
        with self.connect() as db:
            done = db.execute("SELECT 1 FROM metadata_imports WHERE kind='comment' AND path=? AND error=''", (path,)).fetchone()
        if done:
            return {"comment":"","revision":"missing"}
        try:
            _,_,_,target = file_comments.paths(file)
            if target.exists():
                old = file_comments.parse(self.archive(target),unicodedata.normalize("NFC",Path(file).name))
            else:
                old = {"comment":"","revision":"missing"}
            if old["revision"] != "missing":
                current = self.get("comment",path)
                if not current:
                    current = self.put("comment",path,{"comment":old["comment"]},"missing")
            self.imported("comment",path)
            return {"comment":current["comment"],"revision":current["revision"]} if current else old
        except (OSError,ValueError) as error:
            self.error("comment",path,error)
            raise

    def save_comment(self, file, comment, revision):
        import file_comments
        with file_comments.LOCK:
            return self._save_comment(file,comment,revision)

    def _save_comment(self,file,comment,revision):
        from file_comments import MAX_COMMENT
        if not isinstance(comment,str) or len(comment)>MAX_COMMENT or "\x00" in comment:
            raise ValueError("Комментарий должен быть текстом до 100 000 символов")
        self.comment(file)  # Initial legacy migration must succeed before replacing text.
        saved = self.put("comment",self.key(file),{"comment":comment.replace("\r\n","\n").replace("\r","\n")},revision)
        return {"comment":saved["comment"],"revision":saved["revision"]}

    def card(self, folder):
        """Archive source bytes before the normal parsers import a folder card."""
        import order_document as document
        for name in (document.DOCUMENT,*document.LEGACY_DOCUMENTS):
            file = folder/name
            if file.exists():
                self.archive(file)
        return document.load(folder,self.store.labels)

    def status(self):
        import recovery_backup
        with self.connect() as db:
            errors = [{"kind":r[0],"path":r[1],"error":r[2]} for r in db.execute("SELECT kind,path,error FROM metadata_imports WHERE error!='' ORDER BY path")]
            return {"database_only":True,"running":MIGRATION_LOCK.locked(),"imported":db.execute("SELECT count(*) FROM metadata_imports WHERE error='' ").fetchone()[0],
                    "recovery_backup":recovery_backup.status(self.store.database),
                    "errors":errors,"pending_documents":db.execute("SELECT count(*) FROM metadata_publications WHERE published=0").fetchone()[0],
                    "document_errors":[dict(r) for r in db.execute("SELECT path,error FROM metadata_publications WHERE error!=''")]}

    def publish(self, source, revision, folder, filename, body):
        path = self.key(folder/filename)
        with self.connect() as db:
            row = db.execute("SELECT * FROM metadata_publications WHERE source=? AND revision=?",(source,revision)).fetchone()
            if not row:
                db.execute("INSERT INTO metadata_publications(id,source,revision,path,body) VALUES (?,?,?,?,?)",(str(uuid.uuid4()),source,revision,path,body))
                row = db.execute("SELECT * FROM metadata_publications WHERE source=? AND revision=?",(source,revision)).fetchone()
            return {"path":row["path"],"pending":not row["published"],"error":row["error"]}

    def sync(self):
        import order_folders
        with PUBLICATION_LOCK, order_folders.LOCK:
            self._sync()

    def _sync(self):
        from folder_layout import rename_exclusive
        with self.connect() as db:
            rows = list(db.execute("SELECT * FROM metadata_publications WHERE published=0"))
        for row in rows:
            if any(part.startswith('.') for part in Path(row['path']).parts):
                continue
            error = ""
            try:
                with self.connect() as db:
                    assert_unlocked(db,row["path"])
                target = self.root/row["path"]
                for parent in [target,*target.parents]:
                    if parent==self.root:
                        break
                    if parent.is_symlink():
                        raise ValueError("Документы через ссылки не выпускаются")
                if target.exists():
                    if target.read_bytes()!=row["body"]:
                        raise ValueError("Путь выпущенного документа занят другим файлом")
                else:
                    temporary = target.with_name(".issue-"+row["id"]+".tmp")
                    try:
                        with temporary.open("wb") as stream:
                            stream.write(row["body"]); stream.flush(); os.fsync(stream.fileno())
                        rename_exclusive(temporary,target)
                    finally:
                        temporary.unlink(missing_ok=True)
            except (OSError,ValueError) as problem:
                error = str(problem)
            with self.connect() as db:
                db.execute("UPDATE metadata_publications SET published=?,error=? WHERE id=?",(int(not error),error,row["id"]))

    def migrate(self, app):
        if not MIGRATION_LOCK.acquire(blocking=False):
            return
        try:
            self.upgrade_restoration()
            for parent,dirs,names in os.walk(self.root,followlinks=False,
                    onerror=lambda error:self.error("walk",self.key(error.filename),error)):
                folder = Path(parent)
                dirs[:] = [d for d in dirs if not d.startswith('.') and not (folder/d).is_symlink()]
                relative = folder.relative_to(self.root).as_posix()
                relative = "" if relative=="." else relative
                if self.complete("walk",relative) is False:
                    self.imported("walk",relative)
                try:
                    if not self.complete("folder",relative):
                        if not relative or not self.store.get(relative,include_unregistered=True):
                            app.folder_note_store().read(relative)
                        else:
                            self.card(folder)  # Existing SQLite values win, source bytes survive.
                        if app.folder_role(self.root,relative)["folderKind"]=="client":
                            app.client_activity_store().read(relative)
                        if app.folder_role(self.root,relative)["folderKind"]=="object":
                            app.object_activity_store().read(relative)
                        self.imported("folder",relative)
                except (OSError,ValueError) as error:
                    self.error("folder",relative,error)
                for name in names:
                    file = folder/name
                    if name.startswith('.') or file.is_symlink():
                        continue
                    if app.is_print_folder(relative) and len(Path(relative).parts)==2 and file.suffix.lower() in app.PRINT_TEXT_EXTENSIONS and name not in app.order_document.LEGACY_DOCUMENTS and name!=app.order_document.DOCUMENT and not self.is_publication(self.key(file)):
                        try:
                            app.read_print_task(file.relative_to(self.root).as_posix())
                        except (OSError,ValueError) as error:
                            self.error("print",self.key(file),error)
                comments = folder/".file-comments"
                if comments.is_dir() and not comments.is_symlink():
                    for file in comments.glob(".*.txt"):
                        if self.complete("legacy",self.key(file)):
                            continue
                        try:
                            raw = self.archive(file)
                            first = raw.decode("utf-8-sig").splitlines()
                            name = json.loads(first[1][6:])
                            if not isinstance(name,str) or Path(name).name!=name or name.startswith('.'):
                                raise ValueError("Некорректное имя файла в старом комментарии")
                            self.comment(folder/name)
                            self.imported("legacy",self.key(file))
                        except (OSError,ValueError,IndexError) as error:
                            self.error("legacy",self.key(file),error)
                for history in (folder/".order-history",folder/".print-history",comments/".history"):
                    if history.is_dir() and not history.is_symlink():
                        for old_parent,old_dirs,old_names in os.walk(history,followlinks=False):
                            old_dirs[:] = [d for d in old_dirs if not (Path(old_parent)/d).is_symlink()]
                            for name in old_names:
                                file = Path(old_parent)/name
                                if file.is_symlink() or not file.is_file():
                                    continue
                                if self.complete("history",self.key(file)):
                                    continue
                                try:
                                    self.archive(file)
                                    self.imported("history",self.key(file))
                                except (OSError,ValueError) as error:
                                    self.error("history",self.key(file),error)
        finally:
            MIGRATION_LOCK.release()

    def upgrade_restoration(self):
        """Old portable undo recipes must also preserve new SQLite-only fields."""
        import order_document
        import event_folder_undo
        import folder_rename_undo
        import order_folders
        with order_folders.LOCK:
            sessions = []
            with self.connect() as db:
                for table, module in (("event_renames",event_folder_undo),("folder_renames",folder_rename_undo)):
                    if db.execute("SELECT 1 FROM sqlite_master WHERE name=?",(table,)).fetchone():
                        sessions.extend((Path(row[0]),Path(module.__file__)) for row in db.execute(f"SELECT session FROM {table}"))
            for session, source in sessions:
                file = session/".restore.py"
                path = str(session)
                try:
                    path = self.key(file)
                    if not path.startswith('.folder-layout-history/') or any(parent.is_symlink() for parent in [file,*file.parents] if parent!=self.root):
                        raise ValueError("Журнал восстановления находится вне служебного каталога")
                    old = self.archive(file)
                    new = source.read_bytes()
                    if old!=new:
                        order_document.atomic_write(file,new.decode('utf-8'))
                    self.imported("restore-helper",path)
                except (OSError,ValueError) as error:
                    self.error("restore-helper",path,error)

    def is_publication(self,path):
        with self.connect() as db:
            return bool(db.execute("SELECT 1 FROM metadata_publications WHERE path=?",(path,)).fetchone())
