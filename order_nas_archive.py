"""Archive an unregistered client order as a verified ZIP on mounted SMB."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import threading
import unicodedata
import uuid
import zipfile

import file_trash
import folder_layout
import folder_notes
import folder_rename
import folder_rename_undo as paths
from folder_structure import folder_role
import nas_archive
import object_move
import order_folders
from order_todos import REFRESH_LOCK
import orders

DIRECTORY = "Deleted Orders"
JOBS_LOCK = threading.Lock()
JOBS = {}
WORKERS = set()


# Определяет доступность удаления для снятого с учёта клиентского заказа.
# Новая папка, зарегистрированный заказ и служебные разделы не подходят.
def available(store, relative, role, order):
    return bool(store.database_only and order and order["registered"] == 0
                and order_folders.can_manage_service_folders(relative, role))


# Формирует подтверждение с исходным путём, точным ZIP и версией заказа.
# Проверяет наличие снятой регистрации по текущему пути внутри рабочей базы.
def preview(store, relative, *, identity=None, config=None, db=None):
    if db is None:
        config = nas_archive.settings(store)
        with store.connect() as connection:
            return preview(store, relative, identity=identity or uuid.uuid4().hex, config=config, db=connection)
    relative = store.path(relative)
    view = folder_rename.preview(store, relative)
    role = folder_role(store.root, relative)
    row = db.execute("SELECT id,revision,registered FROM orders WHERE path=?", (relative,)).fetchone()
    if not available(store, relative, role, row):
        raise ValueError("Сначала убери клиентский заказ из списка заказов")
    if db.execute("SELECT 1 FROM orders WHERE registered=1 AND substr(path,1,?)=? LIMIT 1",
                  (len(relative) + 1, relative + "/")).fetchone():
        raise ValueError("В папке есть вложенный заказ на учёте. Сначала убери его из списка")
    suffix = f" [{identity[:12]}].zip"
    name = Path(relative).name.encode()[:255 - len(suffix.encode())].decode("utf-8", errors="ignore") + suffix
    archive = Path(DIRECTORY, Path(relative).parent, name)
    revision = hashlib.sha256(json.dumps([view["revision"], row["id"], row["revision"], identity, config]).encode()).hexdigest()
    return {**view, "id": identity, "revision": revision, "archive": archive.as_posix(),
            "nas_path": (nas_archive.VOLUMES / config["root"].lstrip("/") / archive).as_posix()}


# Проверяет, что путь Finder по-прежнему указывает на открытый каталог SMB.
# Обнаруживает отмонтирование, замену каталога или появление ссылки.
def check_mount(directory, path):
    if not os.path.samestat(os.fstat(directory), path.lstat()):
        raise OSError("Каталог на NAS изменился или том отключён")


# Сверяет структуру ZIP, цели ссылок и SHA-256 всех обычных файлов.
# Читает архив с NAS и проверяет CRC также у служебных записей метаданных macOS.
def verify_zip(archive, name, entries, digests):
    prefix = unicodedata.normalize("NFC", name) + "/"
    remaining = {unicodedata.normalize("NFC", relative): (relative, item) for relative, item in entries.items()}
    if len(remaining) != len(entries):
        raise ValueError("В заказе есть неоднозначные имена файлов")
    with os.fdopen(os.open(archive, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb") as file:
        before = os.fstat(file.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("Путь ZIP занят другим типом файла")
        with zipfile.ZipFile(file) as saved:
            seen = set()
            for member in saved.infolist():
                # ditto emits UTF-8 names even in ZIPs without the UTF-8 flag.
                decoded = member.filename if member.flag_bits & 0x800 else member.filename.encode("cp437").decode()
                key = unicodedata.normalize("NFC", decoded)
                if key in seen:
                    raise ValueError("ZIP содержит неоднозначные имена")
                seen.add(key)
                if key == "__MACOSX/" or key.startswith("__MACOSX/"):
                    with saved.open(member) as stream:
                        while stream.read(object_move.CHUNK_SIZE):
                            pass
                    continue
                if not key.startswith(prefix):
                    raise ValueError("ZIP содержит постороннюю запись: " + key)
                key = key[len(prefix):].rstrip("/")
                if key not in remaining:
                    raise ValueError("ZIP содержит лишнюю запись: " + key)
                relative, entry = remaining.pop(key)
                kind = stat.S_IFMT(member.external_attr >> 16)
                if kind != entry[2]:
                    raise ValueError("В ZIP изменился тип записи: " + key)
                with saved.open(member) as stream:
                    if kind == stat.S_IFREG:
                        digest = hashlib.sha256()
                        for chunk in iter(lambda: stream.read(object_move.CHUNK_SIZE), b""):
                            digest.update(chunk)
                        if digest.hexdigest() != digests[relative]:
                            raise ValueError("В ZIP изменилось содержимое: " + key)
                    elif kind == stat.S_IFLNK and stream.read() != os.fsencode(entry[-1]):
                        raise ValueError("В ZIP изменилась цель ссылки: " + key)
        if remaining:
            raise ValueError("В ZIP отсутствует запись: " + next(iter(remaining)))
        if object_move.fingerprint(before) != object_move.fingerprint(os.fstat(file.fileno())):
            raise ValueError("ZIP изменился во время проверки")
        return object_move.fingerprint(before)


# Создаёт архив на SMB и только после сверки исключает исходную папку из рабочего дерева.
# Снимок и журнал общего переноса сохраняют метаданные и позволяют откатить незавершённый шаг.
def archive_order(store, payload, locks, progress):
    config = nas_archive.settings(store)
    source, identity = payload["path"], payload["id"]
    with store.connect() as db:
        view = preview(store, source, identity=identity, config=config, db=db)
        if view["revision"] != payload["revision"]:
            raise folder_rename.FolderRenameConflict("Заказ изменился. Открой подтверждение заново")
        object_move.check_pending(db, source)
    object_move.enable_cloud_reads()
    root, archive = store.root.resolve(), Path(view["archive"])
    hidden = (Path(source).parent / (paths.ORDER_NAS_STAGING_PREFIX + identity)).as_posix()
    with nas_archive.mounted_root(config["root"]) as (directory, _, mounted, _):
        with nas_archive.descend(directory, archive.parent.parts, create=True) as parent:
            archive_parent = mounted / archive.parent
            check_mount(parent, archive_parent)
            final = archive_parent / archive.name
            progress(phase="reading")
            entries, digests = object_move.inventory(root, source, read=True)
            created = None
            verified = None
            try:
                progress(phase="copying")
                check_mount(parent, archive_parent)
                fd = os.open(archive.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
                with os.fdopen(fd, "wb") as file:
                    created = os.fstat(file.fileno())
                    subprocess.run(["/usr/bin/ditto", "-c", "-k", "--sequesterRsrc", "--keepParent",
                                    str(root / source), "-"], check=True, stdout=file, stderr=subprocess.PIPE, text=True)
                    os.fsync(file.fileno())
                progress(phase="verifying")
                check_mount(parent, archive_parent)
                signature = verify_zip(final, view["name"], entries, digests)
                if signature[:2] != (created.st_dev, created.st_ino):
                    raise ValueError("ZIP был заменён во время записи")
                verified = signature

                # Фиксирует проверку ZIP перед фиксацией перепривязки SQLite.
                # Файловый журнал возвращает рабочую папку, если этот шаг прерван.
                def confirm_copy(session):
                    check_mount(parent, archive_parent)
                    object_move.inventory(root, hidden, expected=entries)
                    if object_move.fingerprint(final.lstat()) != verified:
                        raise ValueError("Проверенный ZIP был заменён")
                    folder_layout.save_json(session / ".verified-archive.json",
                                            {"path": str(final), "sha256": digests})

                with nas_archive.LOCK, locks(), order_folders.LOCK, REFRESH_LOCK, orders.SYNC_LOCK, folder_notes.SYNC_LOCK, store.connect() as db:
                    current = nas_archive.settings(store)
                    fresh = preview(store, source, identity=identity, config=current, db=db)
                    if fresh != view:
                        raise folder_rename.FolderRenameConflict("Заказ или настройки NAS изменились. Открой подтверждение заново")
                    object_move.inventory(root, source, expected=entries)
                    sessions = paths.remap_file_trash(db, unicodedata.normalize("NFC", source), unicodedata.normalize("NFC", hidden))
                    if sessions:
                        file_trash.prepare_relocation(root, store.database, sessions, source)
                    db.execute("BEGIN IMMEDIATE")
                    if preview(store, source, identity=identity, config=current, db=db) != view:
                        raise folder_rename.FolderRenameConflict("Заказ изменился. Открой подтверждение заново")
                    object_move.check_pending(db, source)
                    progress(phase="moving")
                    result = folder_rename.relocate(
                        store, db, view, hidden, verify=confirm_copy,
                        details={"kind": paths.ORDER_NAS_ARCHIVE, "id": identity,
                                 "nas_path": str(final), "file_trash_paths": True})
                    warning = ""
                    try:
                        check_mount(parent, archive_parent)
                        if object_move.fingerprint(final.lstat()) != verified:
                            raise ValueError("Архив изменился после проверки")
                        object_move.inventory(root, hidden, expected=entries)
                        shutil.rmtree(root / hidden)
                    except (OSError, ValueError) as error:
                        warning = "Заказ в архиве NAS. Не удалось полностью убрать служебную папку: " + str(error)
                return {"path": Path(source).parent.as_posix(), "nas_path": str(final),
                        "journal": result["journal"], "warning": warning}
            finally:
                if created is not None and verified is None:
                    try:
                        check_mount(parent, archive_parent)
                        if os.path.samestat(created, final.lstat()):
                            os.unlink(archive.name, dir_fd=parent)
                    except OSError:
                        pass


# Возвращает прогресс по идентификатору, после перезапуска читает итог из SQLite.
# Журнал хранит путь ZIP даже при обрыве ответа и смене браузерной вкладки.
def status(store, identity):
    identity = object_move.checked_id(identity)
    with JOBS_LOCK:
        job = JOBS.get((store.database, identity))
        if job is not None:
            return dict(job)
    if store.database.exists():
        with store.connect() as db:
            if paths.table(db, "folder_renames"):
                for row in db.execute("SELECT session,state,mappings FROM folder_renames"):
                    for mapping in json.loads(row["mappings"]):
                        if mapping.get("kind") == paths.ORDER_NAS_ARCHIVE and mapping.get("id") == identity:
                            source = mapping["source"]
                            if row["state"] == "complete":
                                staging = store.root / mapping["destination"]
                                warning = "Заказ в архиве NAS. Служебная папка осталась: " + str(staging) if os.path.lexists(staging) else ""
                                return {"id": identity, "source": source, "path": Path(source).parent.as_posix(),
                                        "nas_path": mapping["nas_path"], "phase": "complete", "warning": warning}
                            return {"id": identity, "source": source, "phase": "failed",
                                    "error": "Перенос прерван или отменён. Проверь журнал: " + row["session"]}
    raise FileNotFoundError("Архивация с таким номером не найдена")


# Запускает одно подтверждённое архивирование в отдельном потоке.
# Повтор идентификатора возвращает существующее задание, параллельные записи на NAS не запускаются.
def start(store, payload, locks, after_move):
    identity = object_move.checked_id(payload.get("id"))
    if payload.get("confirmed") is not True:
        raise ValueError("Подтверди архивирование всей папки")
    try:
        return status(store, identity)
    except FileNotFoundError:
        pass
    source = store.path(payload.get("path"))
    view = preview(store, source, identity=identity)
    if payload.get("revision") != view["revision"]:
        raise folder_rename.FolderRenameConflict("Заказ изменился. Открой подтверждение заново")
    key = (store.database, identity)
    with JOBS_LOCK:
        if key in JOBS:
            return dict(JOBS[key])
        if WORKERS:
            raise folder_rename.FolderRenameConflict("Дождись завершения текущей архивации")
        for old in list(JOBS)[:-31]:
            del JOBS[old]
        job = JOBS[key] = {"id": identity, "source": source, "phase": "preparing"}
        initial = dict(job)

        # Публикует снимок фазы для опроса в браузере.
        # Не удерживает блокировку статуса во время операций с файлами или базой.
        def progress(**fields):
            with JOBS_LOCK:
                job.update(fields)

        # Выполняет принятое подтверждение и обновляет индексы при успехе.
        # Ошибка фонового обновления не меняет итог сохранённого переноса.
        def work():
            try:
                try:
                    result = archive_order(store, {**payload, "path": source}, locks, progress)
                except subprocess.CalledProcessError as error:
                    progress(phase="failed", error="Не удалось создать ZIP на NAS: " + (error.stderr or "").strip())
                    return
                except Exception as error:
                    progress(phase="failed", error=str(error))
                    return
                progress(phase="complete", **result)
                after_move()
            finally:
                with JOBS_LOCK:
                    WORKERS.discard(threading.current_thread())

        thread = threading.Thread(target=work, name="order-nas-archive")
        WORKERS.add(thread)
        try:
            thread.start()
        except RuntimeError:
            WORKERS.remove(thread)
            del JOBS[key]
            raise
    return initial


# Дожидается архивации при штатном завершении сервера.
# Блокировка статуса освобождается до ожидания потока.
def wait_for_jobs():
    with JOBS_LOCK:
        workers = tuple(WORKERS)
    for worker in workers:
        worker.join()
