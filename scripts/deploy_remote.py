"""Удалённая часть деплоя. Запускается по SSH скриптом deploy.py."""
import configparser
from contextlib import closing
import fcntl
import hashlib
import json
import os
import plistlib
import re
import shutil
import socket
import sqlite3
import subprocess
import sys
import tarfile
import time
import urllib.request
from pathlib import Path, PurePosixPath

LABEL = "local.zigzag.manager"


def atomic_write(path, body):
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("wb") as stream:
        stream.write(body)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def write_json(path, value):
    atomic_write(path, (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode())


def database_name(documents):
    return "orders-" + hashlib.sha256(str(documents).encode()).hexdigest()[:16] + ".sqlite3"


def backup_database(source, destination):
    if destination.exists():
        raise RuntimeError("Снимок базы уже существует")
    # rw не создаёт отсутствующую базу и позволяет SQLite подготовить WAL/SHM.
    with closing(sqlite3.connect(source.as_uri() + "?mode=rw", uri=True)) as original:
        with closing(sqlite3.connect(destination)) as backup:
            original.backup(backup)
    # После backup новое соединение перечитывает режим журнала из заголовка.
    with closing(sqlite3.connect(destination)) as backup:
        backup.execute("PRAGMA journal_mode=DELETE")
        if backup.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise RuntimeError("Проверка снимка SQLite не прошла")


def unpack(stream, destination, release):
    with tarfile.open(fileobj=stream, mode="r|gz") as archive:
        names = set()
        for item in archive:
            name = PurePosixPath(item.name)
            if (not item.isfile() or name.is_absolute() or ".." in name.parts or str(name) != item.name
                    or item.name in names or item.size > 100 * 1024 * 1024):
                raise RuntimeError("Недопустимый файл в пакете деплоя")
            names.add(item.name)
            path = destination / item.name
            path.parent.mkdir(parents=True, exist_ok=True)
            with archive.extractfile(item) as source, path.open("xb") as target:
                shutil.copyfileobj(source, target)
    manifest = json.loads((destination / ".manifest.json").read_text())
    expected = set(manifest["files"]) | {".manifest.json", ".release-id"}
    if "initial_database" in manifest:
        expected.add(".initial.sqlite3")
    if names != expected or manifest["release"] != release or (destination / ".release-id").read_text().strip() != release:
        raise RuntimeError("Состав пакета не совпал с манифестом")
    for name, digest in manifest["files"].items():
        if hashlib.sha256((destination / name).read_bytes()).hexdigest() != digest:
            raise RuntimeError("Контрольная сумма не совпала: " + name)
    return manifest


def install_database(release_dir, history, data, documents, manifest):
    initial = manifest.get("initial_database")
    if not initial:
        database = data / database_name(documents)
        if not database.is_file():
            raise RuntimeError("Рабочая база отсутствует; нужен отдельный первый перенос")
        with closing(sqlite3.connect(database.as_uri() + "?mode=rw", uri=True)) as db:
            if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='orders'").fetchone():
                raise RuntimeError("Рабочий файл не содержит базу заказов; данные не заменяются")
        return
    if str(documents) != initial["source_root"]:
        raise RuntimeError("Пути документов различаются; требуется отдельная миграция ключа базы")
    source = release_dir / ".initial.sqlite3"
    if hashlib.sha256(source.read_bytes()).hexdigest() != initial["sha256"]:
        raise RuntimeError("Не совпал хеш исходной базы")
    target = data / database_name(documents)
    if target.exists() or any(data.glob("orders-*.sqlite3*")):
        raise RuntimeError("На M4 уже есть база; первый перенос не перезаписывает данные")
    saved = history / "initial.sqlite3"
    source.rename(saved)
    imported = history / "imported.sqlite3"
    backup_database(saved, imported)
    temporary = data / ".initial-import.sqlite3"
    with imported.open("rb") as source, temporary.open("xb") as output:
        shutil.copyfileobj(source, output)
        output.flush()
        os.fsync(output.fileno())
    os.link(temporary, target)
    temporary.unlink()


def launchctl(*arguments, check=True):
    return subprocess.run(["/bin/launchctl", *arguments], check=check, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def service_loaded(domain):
    return launchctl("print", domain + "/" + LABEL, check=False).returncode == 0


def stop(domain):
    if service_loaded(domain):
        launchctl("bootout", domain + "/" + LABEL)
        for _ in range(50):
            if not service_loaded(domain):
                return
            time.sleep(0.1)
        raise RuntimeError("Прежний сервис не остановился")


def select_release(root, release):
    temporary = root / ".current.tmp"
    temporary.unlink(missing_ok=True)
    temporary.symlink_to(Path(".releases") / release)
    temporary.replace(root / "current")


def prepare_launcher(release_dir, root, documents):
    source = release_dir / "scripts/manager_launcher.c"
    digest = hashlib.sha256(source.read_bytes()).hexdigest()[:16]
    bundle = Path.home() / "Library/Application Support/ZigzagManager/launchers" / digest / "Zigzag Manager.app"
    binary = bundle / "Contents/MacOS/ZigzagManager"
    ready = bundle.parent / ".ready"
    if not ready.exists():
        binary.parent.mkdir(parents=True, exist_ok=True)
        info = {"CFBundleExecutable": "ZigzagManager", "CFBundleIdentifier": "local.zigzag.manager.app",
                "CFBundleInfoDictionaryVersion": "6.0", "CFBundleName": "Zigzag Manager", "CFBundlePackageType": "APPL",
                "CFBundleVersion": "1", "CFBundleShortVersionString": "1.0", "LSUIElement": True,
                "NSRemovableVolumesUsageDescription": "Менеджер хранит приложение и базу заказов на внешнем NVMe.",
                "NSDocumentsFolderUsageDescription": "Менеджер читает и сохраняет документы заказов в iCloud Drive."}
        atomic_write(bundle / "Contents/Info.plist", plistlib.dumps(info))
        subprocess.run(["/usr/bin/clang", "-Wall", "-Wextra", "-Werror", str(source), "-o", str(binary)], check=True)
        subprocess.run(["/usr/bin/codesign", "--force", "--sign", "-", "--identifier", "local.zigzag.manager.app", str(bundle)], check=True)
        print("На M4 подготовлен Zigzag Manager.app; macOS может запросить доступ к NVMe и iCloud.", flush=True)
        subprocess.run(["/usr/bin/open", "-g", "-W", str(bundle), "--args", "--authorize", str(root), str(documents)], check=True, timeout=300)
        atomic_write(ready, b"ready\n")
    return binary


def health(port, release=None):
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=3) as response:
        value = json.load(response)
    if value.get("status") != "ok" or (release and value.get("release") != release):
        raise RuntimeError("Отвечает другой или неготовый сервер")
    return value


def prepare_renderers(settings, release_dir):
    command = [settings["python"], "-c", "import server, image_reports, icloud_access, invoices, thumbnail_cache; server.pdf_renderer(); image_reports.renderer(server.APP_DIR, server.DATA_DIR); icloud_access.renderer(); invoices.renderer(server.APP_DIR, server.DATA_DIR); thumbnail_cache.renderer(server.DATA_DIR)"]
    result = subprocess.run(command, cwd=release_dir, capture_output=True, text=True, timeout=180)
    if result.returncode:
        raise RuntimeError("Не удалось подготовить помощники PDF и iCloud до переключения сервера:\n" + result.stderr[-6000:])


def start(domain, agent, port, release, documents):
    launchctl("enable", domain + "/" + LABEL)
    launchctl("bootstrap", domain, str(agent))
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        try:
            value = health(port, release)
            if value["root"] != str(documents):
                raise RuntimeError("Сервер использует другой корень документов")
            # Доступ к iCloud проверяется самим сервисом, а не только SSH-сессией.
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/tree", timeout=5) as response:
                json.load(response)
            return value
        except (OSError, ValueError, RuntimeError):
            time.sleep(0.5)
    raise RuntimeError("Сервис не прошёл проверку запуска; см. ~/Library/Logs/ZigzagManager/server-error.log")


def check_event_rename_compatibility(database, release_dir):
    if not database.exists():
        return
    with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as db:
        if (db.execute("SELECT 1 FROM sqlite_master WHERE name='metadata_settings'").fetchone()
                and not (release_dir / "local_metadata.py").is_file()):
            raise RuntimeError("База переведена на новый формат хранения. Старый код не поддерживает рабочие комментарии и заметки; откат заблокирован")
        if (db.execute("SELECT 1 FROM sqlite_master WHERE name='metadata_settings'").fetchone()
                and db.execute("SELECT 1 FROM metadata_settings WHERE key='weekly_events_unified' AND value='1'").fetchone()):
            source = release_dir / 'order_calendar.py'
            if not source.is_file() or 'WEEKLY_EVENTS_UNIFIED_VERSION = 1' not in source.read_text(encoding='utf-8'):
                raise RuntimeError('Комментарии недель объединены с событиями календаря. Старый код создаёт отдельное хранение; откат заблокирован')
        if (db.execute("SELECT 1 FROM sqlite_master WHERE name='metadata_settings'").fetchone()
                and db.execute("SELECT 1 FROM metadata_settings WHERE key='calendar_event_relevance' AND value='1'").fetchone()):
            source = release_dir / 'order_calendar.py'
            if not source.is_file() or 'CALENDAR_RELEVANCE_VERSION = 1' not in source.read_text(encoding='utf-8'):
                raise RuntimeError('В календаре есть отметки актуальности. Старый код не сохраняет их; откат заблокирован')
        if (db.execute("SELECT 1 FROM sqlite_master WHERE name='metadata_settings'").fetchone()
                and db.execute("SELECT 1 FROM metadata_settings WHERE key='calendar_event_completion' AND value='1'").fetchone()):
            source = release_dir / 'order_calendar.py'
            if not source.is_file() or 'CALENDAR_COMPLETION_VERSION = 1' not in source.read_text(encoding='utf-8'):
                raise RuntimeError('В календаре есть отметки выполнения. Старый код не сохраняет их; откат заблокирован')
        if (db.execute("SELECT 1 FROM sqlite_master WHERE name='metadata_settings'").fetchone()
                and db.execute("SELECT 1 FROM metadata_settings WHERE key='order_calendar_colors' AND value='1'").fetchone()):
            source = release_dir / 'order_calendar.py'
            if not source.is_file() or 'ORDER_CALENDAR_COLORS_VERSION = 1' not in source.read_text(encoding='utf-8'):
                raise RuntimeError('В календаре есть цвета событий заказов. Старый код не переносит их; откат заблокирован')
        if (db.execute("SELECT 1 FROM sqlite_master WHERE name='metadata_settings'").fetchone()
                and db.execute("SELECT 1 FROM metadata_settings WHERE key='invoice_payment_sources' AND value='1'").fetchone()):
            source = release_dir / 'invoices.py'
            if not source.is_file() or 'INVOICE_PAYMENT_SOURCE_VERSION = 1' not in source.read_text(encoding='utf-8'):
                raise RuntimeError('В базе есть оплаты без заказа или по готовым счетам. Старый код не поддерживает их; откат заблокирован')
        if (db.execute("SELECT 1 FROM sqlite_master WHERE name='invoices'").fetchone()
                and db.execute("SELECT 1 FROM invoices WHERE json_extract(data,'$._list_status')='paid' LIMIT 1").fetchone()):
            source = release_dir / 'invoices.py'
            if not source.is_file() or 'INVOICE_PAID_STATUS_VERSION = 1' not in source.read_text(encoding='utf-8'):
                raise RuntimeError('В базе есть отметки счетов «Оплачен». Старый код не поддерживает их; откат заблокирован')
        if (db.execute("SELECT 1 FROM sqlite_master WHERE name='invoices'").fetchone()
                and db.execute("SELECT 1 FROM invoices WHERE json_type(data,'$._closing_documents') IS NOT NULL LIMIT 1").fetchone()):
            source = release_dir / 'invoices.py'
            if not source.is_file() or 'INVOICE_CLOSING_DOCUMENTS_VERSION = 1' not in source.read_text(encoding='utf-8') or not (release_dir / 'invoice_documents.py').is_file():
                raise RuntimeError('К счетам прикреплены закрывающие документы. Старый код теряет их привязку; откат заблокирован')
        if (db.execute("SELECT 1 FROM sqlite_master WHERE name='invoices'").fetchone()
                and db.execute("SELECT 1 FROM invoices WHERE json_extract(data,'$.kind')='planned' AND json_extract(data,'$.period')='week' LIMIT 1").fetchone()):
            source = release_dir / 'invoices.py'
            if not source.is_file() or 'INVOICE_WEEK_PLAN_VERSION = 1' not in source.read_text(encoding='utf-8'):
                raise RuntimeError('В базе есть недельные финансовые планы. Старый код показывает их как дневные; откат заблокирован')
        if (db.execute("SELECT 1 FROM sqlite_master WHERE name='invoices'").fetchone()
                and db.execute("SELECT 1 FROM invoices WHERE json_extract(data,'$._trash') IS NOT NULL LIMIT 1").fetchone()):
            source = release_dir / 'invoices.py'
            if not source.is_file() or 'INVOICE_TRASH_VERSION = 1' not in source.read_text(encoding='utf-8'):
                raise RuntimeError('В базе есть счета в корзине. Старый код может вернуть их в список и повторно выгрузить PDF; откат заблокирован')
        if (db.execute("SELECT 1 FROM sqlite_master WHERE name='invoices'").fetchone()
                and db.execute("SELECT 1 FROM invoices WHERE json_extract(data,'$.kind')='planned' LIMIT 1").fetchone()):
            source = release_dir / 'invoices.py'
            if not source.is_file() or 'INVOICE_PLAN_VERSION = 1' not in source.read_text(encoding='utf-8'):
                raise RuntimeError('В базе есть планы счетов или оплат. Старый код не поддерживает их формат; откат заблокирован')
        if (not (release_dir / "event_folder_undo.py").is_file()
                and db.execute("SELECT 1 FROM sqlite_master WHERE name='event_renames'").fetchone()
                and db.execute("SELECT 1 FROM event_renames WHERE state='pending' LIMIT 1").fetchone()):
            raise RuntimeError("Есть прерванное переименование событий. Завершите его откат перед переключением на старый код")
        if db.execute("SELECT 1 FROM sqlite_master WHERE name='folder_renames'").fetchone():
            active = any(pair.get('kind') == 'supplier-event-trash'
                         for (mappings,) in db.execute("SELECT mappings FROM folder_renames WHERE state!='undone'")
                         for pair in json.loads(mappings))
            source = release_dir / 'event_trash.py'
            if active and (not source.is_file() or 'EVENT_TRASH_VERSION = 1' not in source.read_text(encoding='utf-8')):
                raise RuntimeError('Есть события в корзине. Старый код не поддерживает их хранение; откат заблокирован')
        if (not (release_dir / "folder_rename_undo.py").is_file()
                and db.execute("SELECT 1 FROM sqlite_master WHERE name='folder_renames'").fetchone()
                and db.execute("SELECT 1 FROM folder_renames WHERE state='pending' LIMIT 1").fetchone()):
            raise RuntimeError("Есть прерванное переименование папки. Завершите откат перед переключением на старый код")


def deploy(settings, action, release):
    root = Path(settings["directory"])
    documents = Path(settings["documents"]).expanduser().resolve()
    if not root.is_absolute() or not root.is_dir() or root.is_symlink() or not documents.is_dir():
        raise RuntimeError("Каталог установки или документы недоступны")
    domain = "gui/" + str(os.getuid())
    port = int(settings["port"])
    if action == "status":
        print(json.dumps({"service_loaded": service_loaded(domain), "health": health(port)}, ensure_ascii=False, indent=2))
        return
    with (root / ".deploy.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state_path = root / ".deployment.json"
        state = json.loads(state_path.read_text()) if state_path.exists() else {}
        previous = state.get("release")
        if action == "rollback":
            release = state.get("previous")
        if not release or not re.fullmatch(r"[0-9]{8}T[0-9]{6}Z-[a-f0-9]{8}", release):
            raise RuntimeError("Нет допустимого релиза для переключения")
        current = root / "current"
        if current.exists() or current.is_symlink():
            if not previous or not current.is_symlink() or current.resolve() != root / ".releases" / previous:
                raise RuntimeError("Текущий каталог отличается от журнала деплоя")
        elif previous:
            raise RuntimeError("Текущий релиз отсутствует")
        if not service_loaded(domain):
            with socket.socket() as probe:
                if probe.connect_ex(("127.0.0.1", port)) == 0:
                    raise RuntimeError("Порт занят посторонним процессом")
        history_root = root / ".deploy-history"
        history_root.mkdir(exist_ok=True)
        history = history_root / (time.strftime("%Y%m%dT%H%M%S", time.gmtime()) + "-" + action + "-" + release)
        history.mkdir()
        write_json(history / "plan.json", {"action": action, "release": release, "previous": previous, "documents": str(documents)})
        data = root / "data"
        data.mkdir(exist_ok=True)
        release_dir = root / ".releases" / release
        if action == "deploy":
            release_dir.mkdir(parents=True)
            manifest = unpack(sys.stdin.buffer, release_dir, release)
            install_database(release_dir, history, data, documents, manifest)
            (release_dir / "data").symlink_to(data)
            (release_dir / "manager.ini").symlink_to(root / "manager.ini")
        elif not (release_dir / "server.py").is_file():
            raise RuntimeError("Предыдущий релиз отсутствует")
        config = configparser.ConfigParser(interpolation=None)
        config_path = root / "manager.ini"
        if config_path.exists():
            config.read(config_path, encoding="utf-8")
            if (Path(config["storage"]["root"]).expanduser().resolve() != documents
                    or config.getint("server", "port") != port or config["server"]["host"] != settings["host"]):
                raise RuntimeError("Настройки M4 изменены; деплой не перезаписывает manager.ini")
        else:
            atomic_write(config_path, (f"[storage]\nroot = {documents}\n\n[server]\nhost = {settings['host']}\nport = {port}\n").encode())
        agent = Path.home() / "Library/LaunchAgents" / (LABEL + ".plist")
        agent.parent.mkdir(parents=True, exist_ok=True)
        old_agent = agent.read_bytes() if agent.exists() else None
        if old_agent:
            atomic_write(history / "previous-agent.plist", old_agent)
        logs = Path.home() / "Library/Logs/ZigzagManager"
        logs.mkdir(parents=True, exist_ok=True)
        try:
            prepare_renderers(settings, release_dir)
        except Exception as error:
            write_json(history / "result.json", {"status": "failed", "stage": "renderers", "error": str(error)})
            raise
        launcher = prepare_launcher(release_dir, root, documents)
        job = {"Label": LABEL, "ProgramArguments": [str(launcher), settings["python"], str(root / "current/server.py"), str(documents)],
               "WorkingDirectory": str(Path.home()), "RunAtLoad": True, "KeepAlive": True, "ThrottleInterval": 10,
               "EnvironmentVariables": {"PYTHONDONTWRITEBYTECODE": "1"},
               "StandardOutPath": str(logs / "server.log"), "StandardErrorPath": str(logs / "server-error.log")}
        stopped = False
        try:
            stop(domain)
            stopped = True
            backup_database(data / database_name(documents), history / "before.sqlite3")
            check_event_rename_compatibility(data / database_name(documents), release_dir)
            select_release(root, release)
            atomic_write(agent, plistlib.dumps(job))
            value = start(domain, agent, port, release, documents)
            write_json(state_path, {"release": release, "previous": previous})
            write_json(history / "result.json", {"status": "ok", "health": value})
            print(json.dumps({"status": "ok", "release": release, "previous": previous, "directory": str(root)}, ensure_ascii=False, indent=2))
        except Exception as error:
            write_json(history / "result.json", {"status": "failed", "error": str(error)})
            if stopped:
                stop(domain)
                if previous and old_agent:
                    check_event_rename_compatibility(data / database_name(documents), root / ".releases" / previous)
                    select_release(root, previous)
                    atomic_write(agent, old_agent)
                    value = start(domain, agent, port, previous, documents)
                    write_json(state_path, state)
                    write_json(history / "recovery.json", {"status": "previous-code-restored", "health": value})
                elif not previous:
                    current.unlink(missing_ok=True)
                    state_path.unlink(missing_ok=True)
                    if old_agent:
                        atomic_write(agent, old_agent)
                    else:
                        agent.unlink(missing_ok=True)
                    write_json(history / "recovery.json", {"status": "stopped", "database": "preserved"})
            raise


if __name__ == "__main__":
    try:
        deploy(json.loads(sys.argv[1]), sys.argv[2], sys.argv[3])
    except Exception as error:
        print(f"Деплой M4 остановлен: {error}", file=sys.stderr)
        sys.exit(1)
