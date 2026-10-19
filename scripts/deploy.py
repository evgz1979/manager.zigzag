#!/usr/bin/env python3
"""Проверка и доставка кода на M4; рабочие данные не входят в обычный деплой."""
import argparse
from contextlib import closing
import configparser
import hashlib
import io
import json
import shlex
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

APP = Path(__file__).resolve().parents[1]


def source_files():
    files = [p for p in APP.iterdir() if p.suffix in {".py", ".swift"}]
    files += [APP / name for name in ("README.md", "AGENTS.md", "PROJECT_NOTES", "deploy.ini")]
    for directory in ("static", "scripts", "tests", "docs", "mobile"):
        for path in (APP / directory).rglob("*"):
            relative = path.relative_to(APP)
            if path.is_file() and not path.is_symlink() and not any(part.startswith(".") or part == "__pycache__" for part in relative.parts):
                if path.suffix not in {".pyc", ".png", ".log"}:
                    files.append(path)
    return {p.relative_to(APP).as_posix(): p.read_bytes() for p in sorted(files)}


def snapshot_bytes(path):
    # Пакет содержит самостоятельный снимок без зависимости от WAL/SHM.
    with tempfile.TemporaryDirectory() as temporary:
        target = Path(temporary) / "initial.sqlite3"
        with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=rw", uri=True)) as source:
            with closing(sqlite3.connect(target)) as snapshot:
                source.backup(snapshot)
        with closing(sqlite3.connect(target)) as snapshot:
            snapshot.execute("PRAGMA journal_mode=DELETE")
            if snapshot.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                raise RuntimeError("Нарушена целостность исходного снимка")
        return target.read_bytes()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--rollback", action="store_true", help="Вернуть предыдущий код, сохранив текущую базу")
    parser.add_argument("--initial-database", type=Path, help="Только первый перенос: согласованный снимок SQLite")
    parser.add_argument("--source-root", help="Корень документов исходной базы при первом переносе")
    args = parser.parse_args()
    if sum((args.status, args.rollback, bool(args.initial_database))) > 1:
        parser.error("Выберите одно действие")
    if bool(args.initial_database) != bool(args.source_root):
        parser.error("Первый перенос требует --initial-database и --source-root")
    config = configparser.ConfigParser(interpolation=None)
    config.read(APP / "deploy.ini", encoding="utf-8")
    settings = dict(config["m4"])
    settings["port"] = int(settings["port"])
    action = "status" if args.status else "rollback" if args.rollback else "deploy"
    payload = None
    release = ""
    if action == "deploy":
        files = source_files()
        subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"], cwd=APP, check=True)
        if files != source_files():
            raise RuntimeError("Исходники изменились во время проверок; повторите деплой")
        release = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + uuid4().hex[:8]
        manifest = {"release": release, "files": {name: hashlib.sha256(body).hexdigest() for name, body in files.items()}}
        files[".release-id"] = (release + "\n").encode()
        if args.initial_database:
            files[".initial.sqlite3"] = snapshot_bytes(args.initial_database)
            manifest["initial_database"] = {"source_root": args.source_root, "sha256": hashlib.sha256(files[".initial.sqlite3"]).hexdigest()}
        files[".manifest.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode()
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
            for name, body in files.items():
                item = tarfile.TarInfo(name)
                item.size = len(body)
                item.mode = 0o644
                archive.addfile(item, io.BytesIO(body))
        payload = buffer.getvalue()
    helper = (APP / "scripts/deploy_remote.py").read_text()
    command = shlex.join([settings["python"], "-c", helper, json.dumps(settings, ensure_ascii=False), action, release])
    result = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", "-o", "StrictHostKeyChecking=yes", settings["ssh"], command], input=payload)
    return result.returncode


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"Деплой остановлен: {error}", file=sys.stderr)
        sys.exit(1)
