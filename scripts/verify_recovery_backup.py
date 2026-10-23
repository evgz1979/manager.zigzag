#!/usr/bin/env python3
"""Standalone verification of an extracted recovery bundle, without the application."""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3


def verify(directory):
    directory = Path(directory).resolve()
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("format") != 1:
        raise ValueError("Неизвестный формат резервной копии")
    files = manifest["files"]
    for required in ("manager.sqlite3", "manager.ini", "application/server.py", "RESTORE.txt", "verify.py"):
        if required not in files:
            raise ValueError("Нет обязательного файла: " + required)
    for name, expected in files.items():
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts or relative.as_posix() != name:
            raise ValueError("Недопустимый путь: " + name)
        path = directory / relative
        if any((directory / Path(*relative.parts[:i])).is_symlink() for i in range(1, len(relative.parts) + 1)):
            raise ValueError("Ссылка вместо файла: " + name)
        checksum = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                checksum.update(chunk)
        if path.stat().st_size != expected["size"] or checksum.hexdigest() != expected["sha256"]:
            raise ValueError("Файл не совпадает с манифестом: " + name)
    database = directory / "manager.sqlite3"
    if any(database.with_name(database.name + suffix).exists() for suffix in ("-wal", "-shm", "-journal")):
        raise ValueError("Рядом со снимком не должно быть WAL/SHM/journal")
    with closing(sqlite3.connect(database.as_uri() + "?mode=ro&immutable=1", uri=True)) as db:
        if db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
            raise ValueError("Целостность SQLite нарушена")
        tables = {name: db.execute('SELECT count(*) FROM "' + name.replace('"', '""') + '"').fetchone()[0]
                  for name, in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if tables != manifest["tables"]:
            raise ValueError("Состав таблиц или число строк не совпали")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, nargs="?", default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    result = verify(args.directory)
    print("OK: SHA-256 всех файлов, SQLite и строки всех таблиц; " + result["created_at"])
