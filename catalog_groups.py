"""Explicit roles of numbered catalog groups in the working SQLite database."""
import json
import sqlite3
import unicodedata
from contextlib import closing
from pathlib import Path

KIND = "catalog_group_type"
LABELS = {"clients": "Группа клиентов", "years": "Группа годов", "": "Группа каталогов"}
DATABASES = {}
UNSET = {"type": "", "revision": "missing"}


# Связывает корень документов с его рабочей SQLite для проверок роли по пути.
# Чтение роли не открывает iCloud и не создаёт базу.
def bind(root, database):
    DATABASES[Path(root)] = Path(database).absolute()


# Читает сохранённый тип группы и токен версии из открытой базы.
# Отсутствие строки означает, что тип ещё не был выбран.
def read(db, path):
    row = db.execute("SELECT id,revision,data FROM metadata_records WHERE kind=? AND path=?",
                     (KIND, unicodedata.normalize("NFC", path))).fetchone()
    if row is None:
        return UNSET.copy()
    return {"type": json.loads(row[2])["type"], "revision": f"{row[0]}:{row[1]}"}


# Определяет явно сохранённый тип по имени непосредственной группы.
# При переданной транзакции видит её собственные изменения пути.
def get(root, path, *, db=None):
    if db is not None:
        has_metadata = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='metadata_records'").fetchone()
        return read(db, path) if has_metadata else UNSET.copy()
    database = DATABASES.get(Path(root))
    if database is not None and database.is_file():
        with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True, timeout=15)) as connection:
            return get(root, path, db=connection)
    return UNSET.copy()


# Сохраняет первый выбранный тип существующей числовой группы.
# Требует отсутствие записи метаданных по полному NFC-пути группы.
def save(store, payload):
    from file_comments import FileCommentConflict
    from folder_structure import is_catalog_group
    from local_metadata import MetadataStore, audit

    path, kind = payload.get("path"), payload.get("type")
    if not isinstance(path, str) or not path or Path(path).parts != (path,) or not is_catalog_group(path):
        raise ValueError("Выбери числовую группу в корне документов")
    if kind not in ("clients", "years"):
        raise ValueError("Выбери группу клиентов или группу годов")
    target = store.root / path
    if target.is_symlink() or not target.is_dir():
        raise FileNotFoundError("Папка группы недоступна")
    metadata = MetadataStore(store)
    if not store.database_only:
        with metadata.connect() as db:
            audit(db, "metadata_records")
    if payload.get("revision") != UNSET["revision"]:
        raise FileCommentConflict("Тип этой группы уже задан")
    try:
        record = metadata.put(KIND, path, {"type": kind}, UNSET["revision"])
    except FileCommentConflict as error:
        raise FileCommentConflict("Тип этой группы уже задан") from error
    return {"type": record["type"], "revision": record["revision"]}
