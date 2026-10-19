"""Заметки папок внутри заказа: отдельные записи SQLite и устойчивая выгрузка."""
import hashlib
import json
import threading
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

import order_document as document
import event_relevance
from event_folder_undo import assert_unlocked
from folder_structure import folder_role

SYNC_LOCK = threading.Lock()


class FolderNoteConflict(ValueError):
    pass


def parent_order(root, relative):
    parts = Path(relative).parts
    for index in range(1, len(parts)):
        parent = Path(*parts[:index]).as_posix()
        if folder_role(root, parent)["folderKind"] == "order":
            return parent
        if parts[index - 1].startswith("#"):
            break
    return None


def checked_path(root, relative):
    if not isinstance(relative, str) or not relative or "\x00" in relative:
        raise ValueError("Выберите папку внутри заказа")
    path = Path(relative)
    if path.is_absolute() or not path.parts or any(part.startswith(".") for part in path.parts):
        raise ValueError("Выберите папку внутри заказа")
    return Path(root) / path


def file_revision(folder):
    digest = hashlib.sha256()
    found = False
    for name in (document.DOCUMENT, *document.LEGACY_DOCUMENTS):
        path = folder / name
        if not path.exists() and not path.is_symlink():
            continue
        document.read_text(path)
        raw = document.icloud_access.read_bytes(path)
        digest.update(name.encode() + len(raw).to_bytes(8, "big") + raw)
        found = True
        if name == document.DOCUMENT:
            break
    return digest.hexdigest() if found else "missing"


class FolderNotes:
    def __init__(self, store, prepare=None):
        self.store = store
        self.prepare = prepare

    @contextmanager
    def connect(self):
        with self.store.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS folder_notes (
                path TEXT PRIMARY KEY, id TEXT NOT NULL UNIQUE, parent_order TEXT NOT NULL,
                document TEXT NOT NULL, revision INTEGER NOT NULL, exported_revision INTEGER NOT NULL,
                file_revision TEXT NOT NULL, updated REAL NOT NULL, sync_error TEXT NOT NULL DEFAULT '')""")
            yield db

    @staticmethod
    def record(row):
        if row is None:
            return None
        value = dict(row)
        body = json.loads(value.pop("document"))
        return {"path": value["path"], "revision": f"{value['id']}:{value['revision']}",
                "note": body.get("note", ""), "extra_blocks": body.get("extra_blocks", {}),
                "todo_items": document.read_todos(body.get("extra_blocks", {})),
                "sync_pending": value["revision"] != value["exported_revision"], "sync_error": value["sync_error"],
                "file_exists": value["file_revision"] != "missing",
                "parent_order": value["parent_order"]}

    def get(self, relative):
        checked_path(self.store.root, relative)
        if not self.store.database.exists():
            return None
        with self.connect() as db:
            assert_unlocked(db, relative)
            return self.record(db.execute("SELECT * FROM folder_notes WHERE path=?", (relative,)).fetchone())

    def target(self, relative):
        target = checked_path(self.store.root, relative)
        for index in range(1, len(Path(relative).parts) + 1):
            if (self.store.root / Path(*Path(relative).parts[:index])).is_symlink():
                raise ValueError("Заметки через символические ссылки не сохраняются")
        if not target.is_dir():
            raise FileNotFoundError("Папка недоступна; данные сохранены в базе, выгрузка будет повторена")
        return target

    def read(self, relative):
        previous = self.get(relative)
        if previous and previous["sync_pending"]:
            return previous
        target = self.target(relative)
        owner = parent_order(self.store.root, relative)
        if not owner:
            raise ValueError("Эта папка не находится внутри заказа")
        if self.prepare:
            self.prepare(target)
        revision = file_revision(target)
        body = document.load(target, self.store.labels)
        if any(part.startswith("#") for part in Path(relative).parts):
            body = document.folder_note(body)
        if file_revision(target) != revision:
            raise FolderNoteConflict("Файл папки изменился во время чтения. Обновите папку")
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            assert_unlocked(db, relative)
            current = db.execute("SELECT * FROM folder_notes WHERE path=?", (relative,)).fetchone()
            if current and current["revision"] != current["exported_revision"]:
                return self.record(current)
            if current and (not previous or f"{current['id']}:{current['revision']}" != previous["revision"]):
                return self.record(current)
            if not current:
                db.execute("INSERT INTO folder_notes VALUES (?,?,?,?,1,1,?,?, '')",
                           (relative, str(uuid.uuid4()), owner, json.dumps(body, ensure_ascii=False), revision, time.time()))
            elif current["file_revision"] != revision:
                db.execute("UPDATE folder_notes SET document=?, revision=revision+1, exported_revision=revision+1, file_revision=?, updated=?, sync_error='' WHERE path=?",
                           (json.dumps(body, ensure_ascii=False), revision, time.time(), relative))
            return self.record(db.execute("SELECT * FROM folder_notes WHERE path=?", (relative,)).fetchone())

    def save(self, payload):
        relative, note = payload.get("path"), payload.get("note")
        checked_path(self.store.root, relative)
        if not isinstance(note, str) or len(note) > 100_000:
            raise ValueError("Укажите заметку длиной до 100 000 символов")
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            assert_unlocked(db, relative)
            row = db.execute("SELECT * FROM folder_notes WHERE path=?", (relative,)).fetchone()
            if not row or payload.get("revision") != f"{row['id']}:{row['revision']}":
                raise FolderNoteConflict("Заметка или задачи папки изменились. Обновите папку, сохранив свой ввод")
            body = json.loads(row["document"])
            if "todo_items" in payload:
                if document.read_todos(body.get("extra_blocks", {})) is None:
                    raise ValueError("Прежний раздел задач содержит произвольный текст; он сохранён без замены")
                body["extra_blocks"] = document.write_todos(body.get("extra_blocks", {}), payload["todo_items"])
            body["note"] = note
            document.render(body, self.store.labels)
            db.execute("UPDATE folder_notes SET document=?, revision=revision+1, updated=?, sync_error='' WHERE path=?",
                       (json.dumps(body, ensure_ascii=False), time.time(), relative))
            return self.record(db.execute("SELECT * FROM folder_notes WHERE path=?", (relative,)).fetchone())

    def event_relevances(self, owner):
        """Обновление переключателей из SQLite, без чтения документов."""
        checked_path(self.store.root, owner)
        with self.connect() as db:
            rows = db.execute("SELECT * FROM folder_notes WHERE parent_order=?", (owner,)).fetchall()
            registered = {row["path"] for row in db.execute("SELECT path FROM orders WHERE registered=1")}
            result = {}
            for row in rows:
                if event_relevance.is_event(row["path"], owner):
                    assert_unlocked(db, row["path"])
                    result[row["path"]] = event_relevance.info(self.record(row),
                        "Эта папка ещё зарегистрирована как отдельный заказ" if row["path"] in registered else "")
            return result

    def save_relevance(self, payload):
        relative, value = payload.get("path"), payload.get("value")
        checked_path(self.store.root, relative)
        if not isinstance(value, str) or value not in event_relevance.LABELS:
            raise ValueError("Выберите состояние события: " + ", ".join(event_relevance.LABELS.values()))
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            assert_unlocked(db, relative)
            row = db.execute("SELECT * FROM folder_notes WHERE path=?", (relative,)).fetchone()
            if not row or payload.get("revision") != f"{row['id']}:{row['revision']}":
                raise FolderNoteConflict("Событие изменилось. Его состояние обновлено; повторите выбор")
            if not event_relevance.is_event(relative, row["parent_order"]):
                raise ValueError("Актуальность задаётся только событию непосредственно внутри заказа")
            if db.execute("SELECT 1 FROM orders WHERE path=? AND registered=1", (relative,)).fetchone():
                raise ValueError("Эта папка ещё зарегистрирована как отдельный заказ")
            body = json.loads(row["document"])
            body["extra_blocks"] = event_relevance.write(body.get("extra_blocks", {}), value)
            document.render(body, self.store.labels)
            db.execute("UPDATE folder_notes SET document=?, revision=revision+1, updated=?, sync_error='' WHERE path=?",
                       (json.dumps(body, ensure_ascii=False), time.time(), relative))
            return self.record(db.execute("SELECT * FROM folder_notes WHERE path=?", (relative,)).fetchone())

    def sync(self):
        if not self.store.database.exists() or not SYNC_LOCK.acquire(blocking=False):
            return
        try:
            with self.connect() as db:
                rows = db.execute("SELECT * FROM folder_notes WHERE revision!=exported_revision ORDER BY path").fetchall()
            for row in rows:
                try:
                    with self.connect() as db:
                        assert_unlocked(db, row["path"])
                    target = self.target(row["path"])
                    body = document.render(json.loads(row["document"]), self.store.labels)
                    card = target / document.DOCUMENT
                    # Повтор после сбоя между публикацией файла и подтверждением SQLite.
                    already_written = card.is_file() and not card.is_symlink() and document.icloud_access.read_bytes(card) == body.encode()
                    if not already_written:
                        if file_revision(target) != row["file_revision"]:
                            raise FolderNoteConflict("!.txt изменён вне менеджера. Обе версии сохранены: в файле и в базе; выгрузка остановлена")
                        document.archive_current(target)
                        if file_revision(target) != row["file_revision"]:
                            raise FolderNoteConflict("Файл изменился во время выгрузки; правки в базе сохранены")
                        document.atomic_write(card, body)
                    document.archive_legacy(target)
                    raw = body.encode()
                    revision = hashlib.sha256(document.DOCUMENT.encode() + len(raw).to_bytes(8, "big") + raw).hexdigest()
                    if file_revision(target) != revision:
                        raise FolderNoteConflict("Файл изменился после выгрузки. Правки в базе и внешняя версия сохранены")
                    with self.connect() as db:
                        db.execute("UPDATE folder_notes SET exported_revision=?, file_revision=?, sync_error='' WHERE id=?",
                                   (row["revision"], revision, row["id"]))
                except (OSError, ValueError) as error:
                    with self.connect() as db:
                        db.execute("UPDATE folder_notes SET sync_error=? WHERE id=?", (document.icloud_access.sync_error(error), row["id"]))
        finally:
            SYNC_LOCK.release()
