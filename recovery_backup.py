"""Daily, self-contained recovery bundles; the live SQLite stays outside iCloud."""
import argparse
from contextlib import closing
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import uuid
import zipfile
from zoneinfo import ZoneInfo

from folder_layout import rename_exclusive

DIRECTORY = ".manager-backups"
FORMAT_VERSION = 1
TIMEZONE = ZoneInfo("Europe/Moscow")


def state_path(database):
    database = Path(database)
    return database.parent / (database.stem + "-recovery-backup.json")


def status(database):
    try:
        value = json.loads(state_path(database).read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("Ожидалось состояние резервного копирования")
        return value
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as error:
        return {"error": str(error)}


def save_status(database, value):
    path = state_path(database)
    temporary = path.with_name("." + path.name + "-" + uuid.uuid4().hex)
    try:
        with temporary.open("x", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def failure(database, error):
    value = status(database)
    value.update(error=str(error), attempted_at=datetime.now(TIMEZONE).isoformat())
    save_status(database, value)


def due(database, root, now=None):
    now = now or datetime.now(TIMEZONE)
    value = status(database)
    return (value.get("day") != now.astimezone(TIMEZONE).date().isoformat()
            or value.get("root") != os.path.abspath(root)
            or value.get("format") != FORMAT_VERSION or bool(value.get("error")))


def source_files(app):
    """Only application sources; never recurse into data or document folders."""
    names = {"README.md", "AGENTS.md", "PROJECT_NOTES", "deploy.ini", "launcher.json",
             "start.command", ".release-id", ".manifest.json"}
    files = [p for p in app.iterdir() if p.suffix in {".py", ".swift"} or p.name in names]
    for directory in ("static", "scripts", "tests", "docs", "mobile"):
        if (app / directory).is_symlink():
            raise ValueError("Ссылка вместо каталога исходников: " + directory)
        for base, dirs, filenames in os.walk(app / directory, followlinks=False):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"
                       and not (Path(base) / d).is_symlink()]
            files.extend(Path(base) / name for name in filenames
                         if not name.startswith(".") and Path(name).suffix not in {".pyc", ".png", ".log"})
    return sorted(p for p in files if p.is_file() and not p.is_symlink())


RESTORE = """Восстановление «Менеджера заказов Зигзаг»

Этот ZIP содержит согласованную SQLite (включая PDF счетов, историю и очереди),
исходники приложения, manager.ini, описание запуска (если найдено) и SHA-256.
Обычные вложения и .folder-layout-history уже находятся в каталоге «Зигзаг»;
в ZIP они не дублируются. Для полного восстановления сохрани весь этот каталог,
включая скрытые папки. Технические кеши и прежние релизы не нужны.

1. Скопируй ZIP из iCloud на локальный диск и распакуй в отдельный новый каталог.
   Проверь: python3 verify.py /путь/к/распакованному/каталогу
   Проверяются все SHA-256, целостность SQLite и числа строк всех таблиц.
2. На M4 останови сервис:
   launchctl bootout gui/$(id -u)/local.zigzag.manager
   Сохрани текущие data/, manager.ini и настройки запуска отдельно, включая
   SQLite, -wal и -shm. Снимок не заменяет более новые данные автоматически.
3. Сверь database, root и installation в manifest.json. Верни исходные абсолютные
   пути установки и корня документов: от корня зависит имя SQLite, журналы могут
   хранить абсолютный путь базы. При смене путей сначала нужна отдельная адаптация.
4. Подготовь восстановление в НОВОЙ пустой папке: скопируй application/,
   manager.ini, создай data/ и положи manager.sqlite3 под исходным именем database_name.
   Не копируй к снимку старые -wal/-shm. Повтори проверку SQLite. Сверь manager.ini
   с фактическим корнем из manifest.json; особенно если использовалась переменная
   ZIGZAG_DATA_ROOT или относительный root. Не запускай второй рабочий сервер.
5. После сохранения текущего состояния установи проверенный код и базу на исходные
   пути; launchd и подписанный запускатель пересоздай штатным scripts/deploy.py
   (назначение в deploy.ini). launch-agent.plist — справочная копия, его старые пути
   к запускателю нельзя использовать без проверки. Сначала проверь корень, карточки,
   заметки, задачи, комментарии, PDF счетов и состояние очередей, затем возобнови работу.

Снимок содержит данные на момент created_at в manifest.json. Возврат файловых
переименований и корзины выполняется по их журналам и самостоятельным .restore.py;
восстановление старой базы само по себе не возвращает прежние пути документов.
Публикация ZIP в iCloud Drive не доказывает завершения облачной передачи.
Ежедневные копии не удаляются автоматически. Рабочая база остаётся локальной на M4.
"""


def create(database, root, app, *, now=None, force=False):
    database, root, app = Path(database).resolve(), Path(root).resolve(), Path(app).resolve()
    now = (now or datetime.now(TIMEZONE)).astimezone(TIMEZONE)
    # The lock and schedule state are local, so a successful day needs no iCloud reads.
    with (database.parent / (database.stem + "-recovery-backup.lock")).open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return None
        if not force and not due(database, root, now):
            return None
        pending = None
        try:
            if not database.is_file() or not root.is_dir():
                raise ValueError("Рабочая база или корень документов недоступны")
            with tempfile.TemporaryDirectory(prefix=".recovery-backup-", dir=database.parent) as temporary:
                stage = Path(temporary) / "bundle"
                stage.mkdir()
                snapshot = stage / "manager.sqlite3"
                with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as original:
                    with closing(sqlite3.connect(snapshot)) as copy:
                        original.backup(copy, pages=256)
                with closing(sqlite3.connect(snapshot)) as copy:
                    if copy.execute("PRAGMA journal_mode=DELETE").fetchone()[0] != "delete":
                        raise ValueError("Снимок не удалось отделить от WAL")
                    if copy.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                        raise ValueError("Проверка целостности снимка SQLite не пройдена")
                    tables = {name: copy.execute('SELECT count(*) FROM "' + name.replace('"', '""') + '"').fetchone()[0]
                              for name, in copy.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                # Apple SQLite may leave an orphan SHM after converting a backup from WAL.
                # Only the private, closed snapshot is cleaned; the live sidecars stay intact.
                for suffix in ("-wal", "-shm", "-journal"):
                    sidecar = snapshot.with_name(snapshot.name + suffix)
                    if suffix != "-shm" and sidecar.exists() and sidecar.stat().st_size:
                        raise ValueError("У снимка остался непустой журнал SQLite")
                    sidecar.unlink(missing_ok=True)
                for source in source_files(app):
                    target = stage / "application" / source.relative_to(app)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source, target)
                if not (stage / "application/server.py").is_file():
                    raise ValueError("Не найдены исходники рабочего сервера")
                shutil.copyfile(app / "manager.ini", stage / "manager.ini")
                shutil.copyfile(app / "scripts/verify_recovery_backup.py", stage / "verify.py")
                agent = Path.home() / "Library/LaunchAgents/local.zigzag.manager.plist"
                if agent.is_file() and not agent.is_symlink():
                    shutil.copyfile(agent, stage / "launch-agent.plist")
                (stage / "RESTORE.txt").write_text(RESTORE, encoding="utf-8")
                manifest = {"format": FORMAT_VERSION, "created_at": now.isoformat(), "root": str(root),
                            "database": str(database), "database_name": database.name,
                            "installation": str(database.parent.parent), "code": str(app), "tables": tables,
                            "files": {p.relative_to(stage).as_posix(): {"sha256": digest(p), "size": p.stat().st_size}
                                      for p in sorted(stage.rglob("*")) if p.is_file()}}
                (stage / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                checked = subprocess.run([sys.executable, str(stage / "verify.py"), str(stage)],
                                         capture_output=True, text=True, timeout=120)
                if checked.returncode:
                    raise ValueError("Проверка комплекта восстановления: " + checked.stderr.strip()[-2000:])
                archive = Path(temporary) / "backup.zip"
                with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as output:
                    for source in sorted(stage.rglob("*")):
                        if source.is_file():
                            output.write(source, source.relative_to(stage).as_posix())
                with zipfile.ZipFile(archive) as check:
                    if check.testzip() is not None:
                        raise ValueError("Проверка ZIP не пройдена")
                checksum = digest(archive)
                folder = root / DIRECTORY
                if folder.is_symlink():
                    raise ValueError("Папка резервных копий не должна быть ссылкой")
                folder.mkdir(exist_ok=True)
                token = uuid.uuid4().hex
                target = folder / ("backup-" + now.strftime("%Y-%m-%d-%H%M%S") + "-" + token[:8] + ".zip")
                pending = folder / (".pending-" + token)
                with archive.open("rb") as source, pending.open("xb") as output:
                    shutil.copyfileobj(source, output, length=1024 * 1024)
                    output.flush()
                    os.fsync(output.fileno())
                if digest(pending) != checksum:
                    raise ValueError("Скопированный ZIP не совпал с проверенным архивом")
                rename_exclusive(pending, target)
                save_status(database, {"format": FORMAT_VERSION, "day": now.date().isoformat(),
                                      "created_at": now.isoformat(), "root": str(root), "path": str(target),
                                      "sha256": checksum, "size": target.stat().st_size, "error": ""})
                return target
        except Exception as error:
            failure(database, error)
            raise
        finally:
            if pending is not None:
                pending.unlink(missing_ok=True)


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def worker(database, root, app):
    while True:
        try:
            if due(database, root):
                result = subprocess.run([sys.executable, str(Path(app) / "recovery_backup.py"),
                                         "--database", str(database), "--root", str(root), "--app", str(app)],
                                        capture_output=True, text=True, timeout=300)
                if result.returncode:
                    raise RuntimeError(result.stderr.strip()[-2000:] or "Не удалось создать резервную копию")
                if result.stdout.strip():
                    print("Резервная копия: " + result.stdout.strip(), flush=True)
        except Exception as error:
            failure(database, error)
            print("Резервная копия ожидает повтора: " + str(error), flush=True)
        threading.Event().wait(60)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--app", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--force", action="store_true", help="Создать дополнительную копию, сохранив прежние")
    args = parser.parse_args()
    target = create(args.database, args.root, args.app, force=args.force)
    if target:
        print(target)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
