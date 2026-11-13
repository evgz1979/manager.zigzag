"""Move an entire client object, with a verified file inventory and background progress."""
import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import threading
import time
import unicodedata
from contextlib import closing
import sqlite3

import folder_layout as layout
import folder_notes
import folder_rename
from folder_rename import FolderRenameConflict
from folder_structure import client_path, folder_role, is_catalog_group
from order_folders import LOCK
from order_todos import REFRESH_LOCK
import orders

KIND = "client-object-move"
JOBS_LOCK = threading.Lock()
JOBS = {}
DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
CHUNK_SIZE = 1024 * 1024


# Проверяет роль объекта в обычной клиентской ветке.
# Источник может быть вложен в группу объектов, но должен принадлежать конкретному клиенту.
def available(relative, kind):
    return kind == "object" and bool(client_path(relative)) and folder_rename.available(relative)


# Проверяет точный существующий путь объекта или клиента.
# Запрещает ссылки, подмену компонентов и альтернативное написание существующего пути.
def target(root, relative):
    if not isinstance(relative, str) or not relative or "\x00" in relative or Path(relative).as_posix() != relative:
        raise ValueError("Укажи точный путь папки")
    path = folder_rename.target(root, relative)
    # An APFS volume can resolve a differently cased path to the same folder.
    for component in (*path.parents, path):
        if root not in component.parents:
            continue
        with os.scandir(component.parent) as entries:
            if not any(item.name == component.name and item.is_dir(follow_symlinks=False) for item in entries):
                raise ValueError("Открой папку из дерева клиентов, чтобы использовать её точный путь")
    return path


# Привязывает выбор клиента к конкретному экземпляру его папки.
# Отпечаток включает путь и идентичность каталога, без обхода его заказов.
def client_revision(path, relative):
    return hashlib.sha256(json.dumps([relative, layout.identity(path)], sort_keys=True).encode()).hexdigest()


# Готовит форму переноса с клиентами корня и непосредственными клиентами числовых групп.
# Сканирует только уровни каталога клиентов и сохраняет полные пути одноимённых клиентов.
def preview(store, relative):
    root = store.root.resolve()
    target(root, relative)
    if not available(relative, folder_role(root, relative)["folderKind"]):
        raise ValueError("Открой объект клиента для переноса")
    source_client = client_path(relative)
    view = folder_rename.preview(store, relative)
    clients = []
    for parent in root.iterdir():
        if parent.name.startswith((".", "#")) or parent.is_symlink() or not parent.is_dir():
            continue
        candidates = parent.iterdir() if is_catalog_group(parent.name) else [parent]
        for candidate in candidates:
            if candidate.name.startswith((".", "#")) or candidate.is_symlink() or not candidate.is_dir():
                continue
            path = candidate.relative_to(root).as_posix()
            if path != source_client and client_path(path) == path:
                clients.append({"path": path, "revision": client_revision(candidate, path)})
    return {**view, "clients": sorted(clients, key=lambda item: item["path"].casefold())}


# Проверяет подтверждённые пути и версии, включая замену папки назначения во время подготовки.
# Возвращает прежнее имя объекта непосредственно под выбранным другим клиентом.
def move_paths(store, payload):
    root = store.root.resolve()
    source, client = payload.get("path"), payload.get("client")
    path = target(root, source)
    if not available(source, folder_role(root, source)["folderKind"]):
        raise ValueError("Перенос доступен только у объекта клиента")
    parent = target(root, client)
    if client != client_path(client) or client == client_path(source) or folder_role(root, client)["folderKind"] != "client":
        raise ValueError("Выбери другого клиента")
    view = folder_rename.preview(store, source)
    if view["revision"] != payload.get("revision") or client_revision(parent, client) != payload.get("client_revision"):
        raise FolderRenameConflict("Папка объекта или клиента изменилась. Открой перенос заново")
    destination = (Path(client) / path.name).as_posix()
    if layout.exists(root / destination):
        raise FolderRenameConflict("У выбранного клиента этот путь уже занят: " + destination)
    return view, destination


# Разрешает фоновому потоку macOS материализовать файлы iCloud при обычном чтении.
# Меняет политику только текущего потока, который существует до окончания операции.
def enable_cloud_reads():
    if sys.platform == "darwin":
        # sys/resource.h: VFS_MATERIALIZE_DATALESS_FILES, SCOPE_THREAD, FILES_ON.
        policy = ctypes.CDLL(None, use_errno=True).setiopolicy_np
        if policy(3, 1, 2) != 0:
            error = ctypes.get_errno()
            raise OSError(error, os.strerror(error))


# Формирует отпечаток файла или каталога, устойчивый к переносу родителя.
# Идентичность каталога сравнивается отдельно от времени его изменения.
def fingerprint(info):
    identity = (info.st_dev, info.st_ino, stat.S_IFMT(info.st_mode))
    if stat.S_ISDIR(info.st_mode):
        return identity
    return (*identity, info.st_size, info.st_mtime_ns)


# Читает обычный файл целиком и проверяет, что открытый файл не подменили.
# Использует ограниченную память, не переходит по ссылкам, сообщает о прочитанных байтах.
def file_digest(directory, name, info, on_bytes):
    with os.fdopen(os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory), "rb") as stream:
        before = os.fstat(stream.fileno())
        if fingerprint(before) != fingerprint(info):
            raise ValueError("Файл изменился перед чтением")
        digest, size = hashlib.sha256(), 0
        for data in iter(lambda: stream.read(CHUNK_SIZE), b""):
            digest.update(data)
            size += len(data)
            on_bytes(len(data))
        after = os.fstat(stream.fileno())
        if size != before.st_size or fingerprint(after) != fingerprint(before):
            raise ValueError("Файл изменился во время чтения")
        return digest.hexdigest()


# Подтверждает отсутствие старого пути, пропуская только явный ENOENT.
# Ошибки доступа и iCloud останавливают сверку.
def require_absent(path):
    try:
        path.lstat()
    except FileNotFoundError:
        return
    raise ValueError("Прежний путь всё ещё занят: " + str(path))


# Обходит все записи папки и по запросу сравнивает их байты и структуру.
# Включает скрытые записи, пустые каталоги и сами ссылки, не читая цели ссылок.
def inventory(root, relative, *, expected=None, digests=None, read=False, progress=None):
    entries, checksums = {}, {}
    files = directories = links = size = 0
    total_files = sum(item[2] == stat.S_IFREG for item in expected.values()) if expected else 0
    total_bytes = sum(item[3] for item in expected.values() if item[2] == stat.S_IFREG) if expected else 0
    last_update, current = 0, ""

    # Обновляет счётчики текущего этапа без публикации на каждый блок файла.
    # Принудительный отчёт ставится перед потенциально долгим чтением каталога или файла.
    def report(force=False):
        nonlocal last_update
        now = time.monotonic()
        if progress and (force or now - last_update >= 0.2):
            last_update = now
            progress(current=current, files=files, folders=directories, links=links, bytes=size,
                     total_files=total_files, total_bytes=total_bytes)

    # Прибавляет только реально прочитанные из файла байты.
    # Вызывается для каждого блока потока.
    def counted(length):
        nonlocal size
        size += length
        report()

    # Сохраняет элемент и сразу обнаруживает отсутствующую или изменённую запись.
    # Использует имена относительно объекта, а не абсолютные пути клиента.
    def record(path, item):
        if expected is not None and (path not in expected or expected[path] != item):
            raise ValueError("Изменился состав папки: " + path)
        entries[path] = item

    # Обходит одну директорию по дескриптору, открывая дочерние каталоги без ссылок.
    # Ошибка любого чтения прерывает сверку и показывает затронутый путь.
    def scan(directory, prefix, info):
        nonlocal current, files, directories, links
        record(prefix, fingerprint(info))
        current = prefix
        report()
        with os.scandir(directory) as listing:
            for entry in listing:
                name = prefix + "/" + entry.name if prefix else entry.name
                current = name
                try:
                    info = entry.stat(follow_symlinks=False)
                    item = fingerprint(info)
                    if stat.S_ISDIR(info.st_mode):
                        report()
                        child = os.open(entry.name, DIR_FLAGS, dir_fd=directory)
                        try:
                            child_info = os.fstat(child)
                            if fingerprint(child_info) != item:
                                raise ValueError("Папка была заменена")
                            directories += 1
                            scan(child, name, child_info)
                        finally:
                            os.close(child)
                        continue
                    if stat.S_ISLNK(info.st_mode):
                        record(name, (*item, os.readlink(entry.name, dir_fd=directory)))
                        links += 1
                    elif stat.S_ISREG(info.st_mode):
                        record(name, item)
                        if read:
                            report(force=True)
                            checksum = file_digest(directory, entry.name, info, counted)
                            if digests is not None and digests[name] != checksum:
                                raise ValueError("Содержимое файла изменилось: " + name)
                            checksums[name] = checksum
                        files += 1
                    else:
                        raise ValueError("Неподдерживаемый тип файла")
                except OSError as error:
                    raise ValueError("Не удалось прочитать «" + name + "»: " + str(error)) from error
                report()

    directory = os.open(root, DIR_FLAGS)
    try:
        for part in Path(relative).parts:
            child = os.open(part, DIR_FLAGS, dir_fd=directory)
            os.close(directory)
            directory = child
        scan(directory, "", os.fstat(directory))
    finally:
        os.close(directory)
    if expected is not None and entries.keys() != expected.keys():
        raise ValueError("Не найдена запись: " + next(iter(expected.keys() - entries.keys())))
    current = ""
    report(force=True)
    return entries, checksums


# Отсекает незаконченные операции, чьи журналы ещё привязаны к прежнему пути.
# Проверяет создание заказов и корзину счетов до физического переноса.
def check_pending(db, source):
    for table, condition, message in (
        ("metadata_records", "kind='order_creation' AND json_extract(data,'$.state')='pending'", "Дождись регистрации создаваемого заказа"),
        ("invoices", "json_extract(data,'$._trash.state')='pending'", "Дождись переноса счёта в корзину"),
    ):
        if folder_rename.restore.table(db, table) and db.execute(
                f"SELECT 1 FROM {table} WHERE ({condition}) AND (path=? OR substr(path,1,?)=?)",
                (source, len(source) + 1, source + "/")).fetchone():
            raise FolderRenameConflict(message)


# Проверяет данные назначения с учётом нечувствительности iCloud к регистру и нормализации.
# История прежних путей не считается рабочей записью назначения.
def check_destination(db, destination):
    key = unicodedata.normalize("NFC", destination).casefold()
    for table in ("orders", "folder_notes", "todo_catalog", "todo_missing_folders", "client_activity",
                  "object_activity", "invoices", "metadata_records", "metadata_imports", "metadata_publications"):
        if folder_rename.restore.table(db, table):
            for (path,) in db.execute(f"SELECT path FROM {table}"):
                if folder_rename.restore.inside(unicodedata.normalize("NFC", path).casefold(), key):
                    raise FolderRenameConflict("По новому пути уже есть сохранённые данные: " + path)


# Проверяет содержимое и переносит объект через общий протокол файлового журнала.
# SQLite получает новые пути только после совпадения всех отпечатков и SHA-256.
def move(store, payload, progress, locks):
    root = store.root.resolve()
    progress(phase="preparing")
    enable_cloud_reads()
    view, destination = move_paths(store, payload)
    source = view["path"]
    with store.connect() as db:
        folder_rename.restore.check(db, source, destination)
        check_pending(db, source)
        check_destination(db, destination)

    # Передаёт прогресс инвентаризации под именем текущего этапа.
    # Пустой current означает, что текущий обход завершён.
    def scan(phase, relative, **options):
        progress(phase=phase, current="", files=0, folders=0, links=0, bytes=0, total_files=0, total_bytes=0)
        return inventory(root, relative, progress=progress, **options)

    entries, _ = scan("scanning", source)
    _, digests = scan("reading", source, expected=entries, read=True)
    totals = {"files": len(digests),
              "folders": sum(item[2] == stat.S_IFDIR for item in entries.values()) - 1,
              "links": sum(item[2] == stat.S_IFLNK for item in entries.values()),
              "bytes": sum(entries[path][3] for path in digests)}
    progress(phase="preparing", current="", **totals)
    with locks(), LOCK, REFRESH_LOCK, orders.SYNC_LOCK, folder_notes.SYNC_LOCK, store.connect() as db:
        # Recheck after the potentially long iCloud read, without taking a write transaction for that read.
        fresh, fresh_destination = move_paths(store, payload)
        if fresh != view or fresh_destination != destination:
            raise FolderRenameConflict("Папки изменились во время проверки. Открой перенос заново")
        inventory(root, source, expected=entries)
        db.execute("BEGIN IMMEDIATE")
        check_pending(db, source)
        check_destination(db, destination)

        # Доказывает наличие всех исходных записей и читаемых байтов по новому пути.
        # При несовпадении общий перенос откатывает папку до любых изменений путей SQLite.
        def verify(session):
            parent = target(root, payload["client"])
            require_absent(root / source)
            if client_revision(parent, payload["client"]) != payload["client_revision"]:
                raise ValueError("После переноса изменилась папка клиента")
            scan("verifying", destination, expected=entries, digests=digests, read=True)
            layout.save_json(session / ".verified-files.json", {"counts": totals, "sha256": digests})
            inventory(root, destination, expected=entries)
            require_absent(root / source)

        result = folder_rename.relocate(store, db, view, destination,
                                       details={"kind": KIND, "id": payload["id"], "counts": totals},
                                       verify=verify, progress=lambda phase: progress(phase=phase, current=""))
    return {**result, **totals}


# Сверяет формат идентификатора клиентского намерения.
# Идентификатор возвращается в браузер без использования его в файловых путях.
def checked_id(identity):
    if not isinstance(identity, str) or not re.fullmatch("[0-9a-f]{32}", identity):
        raise ValueError("Не указан идентификатор переноса")
    return identity


# Восстанавливает статус по устойчивому журналу SQLite после перезапуска сервера.
# Незавершённый перенос требует согласованного восстановления через .restore.py.
def saved_status(store, identity):
    if store.database.exists():
        uri = store.database.resolve().as_uri() + "?mode=ro"
        with closing(sqlite3.connect(uri, uri=True, timeout=2)) as db:
            if folder_rename.restore.table(db, "folder_renames"):
                for session, state, mappings in db.execute("SELECT session,state,mappings FROM folder_renames"):
                    for mapping in json.loads(mappings):
                        if mapping.get("kind") != KIND or mapping.get("id") != identity:
                            continue
                        result = {"id": identity, "source": mapping["source"], "path": mapping["destination"],
                                  "journal": Path(session).relative_to(store.root.resolve()).as_posix(), **mapping["counts"]}
                        if state == "complete":
                            return {**result, "phase": "complete"}
                        error = ("Перенос прерван. Восстанови папку и базу из журнала: " + session
                                 if state == "pending" else "Прежний путь восстановлен")
                        return {**result, "phase": "failed", "error": error}
    return None


# Возвращает последний прогресс без ожидания iCloud или блокировки файловой операции.
# При отсутствии процесса читает подтверждённое состояние журнала.
def status(store, identity):
    identity = checked_id(identity)
    with JOBS_LOCK:
        job = JOBS.get((store.database, identity))
        if job is not None:
            return dict(job)
    saved = saved_status(store, identity)
    if saved:
        return saved
    raise FileNotFoundError("Перенос с таким номером не найден. Проверь исходную папку")


# Принимает одно подтверждённое намерение и запускает перенос в отдельном потоке.
# Повтор того же идентификатора возвращает статус, а параллельный перенос отклоняется.
def start(store, payload, locks, after_move):
    identity = checked_id(payload.get("id"))
    if payload.get("confirmed") is not True:
        raise ValueError("Подтверди перенос всего объекта")
    if any(not isinstance(payload.get(key), str) for key in ("path", "client", "revision", "client_revision")):
        raise ValueError("Укажи объект и клиента из формы переноса")
    key = (store.database, identity)
    saved = saved_status(store, identity)
    with JOBS_LOCK:
        previous = JOBS.get(key) or saved
        if previous is not None:
            return dict(previous)
        if any(database == store.database and job["phase"] not in {"complete", "failed"}
               for (database, _), job in JOBS.items()):
            raise FolderRenameConflict("Дождись завершения текущего переноса объекта")
        finished = [old for old, job in JOBS.items() if job["phase"] in {"complete", "failed"}]
        for old in finished[:-31]:
            del JOBS[old]
        job = {"id": identity, "source": payload["path"], "phase": "preparing"}
        JOBS[key] = job
        initial = dict(job)

    # Публикует короткий снимок прогресса для HTTP-опроса.
    # Никогда не держит блокировку статуса во время чтения файлов или SQLite.
    def progress(**fields):
        with JOBS_LOCK:
            job.update(fields)

    # Запускает перенос и сообщает о завершении или восстановлении исходного пути.
    # Сбой последующего обновления индексов не меняет результат уже сохранённой операции.
    def work():
        try:
            result = move(store, payload, progress, locks)
        except Exception as error:
            progress(phase="failed", error=str(error))
            return
        progress(phase="complete", **result)
        after_move()

    try:
        threading.Thread(target=work, name="client-object-move", daemon=True).start()
    except RuntimeError as error:
        progress(phase="failed", error="Не удалось запустить перенос: " + str(error))
    return initial
