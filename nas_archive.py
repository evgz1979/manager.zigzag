"""Archive folders on the server's mounted SMB share."""
import errno
import hashlib
import json
import os
import re
import subprocess
import threading
import unicodedata
from contextlib import contextmanager, nullcontext
from pathlib import Path
from urllib.parse import quote, unquote

import order_folders
from local_metadata import MetadataStore, audit

DEFAULT_ROOT = "/Safe/Zigzag-archive"
VOLUMES = Path("/Volumes")
SETTINGS = "nas_archive_root"
BINDING = "nas_archive_path"
ARCHIVE = "# nas"
LOCK = threading.RLock()


# Нормализует адрес архивного корня в формате /Том/Папка.
# Принимает только компоненты сетевого тома без переходов и управляющих символов.
def root_path(value):
    if not isinstance(value, str):
        raise ValueError("Укажи путь на NAS, например /Safe/Zigzag-archive")
    value = unicodedata.normalize("NFC", value.strip().rstrip("/"))
    parts = value[1:].split("/")
    if (not value.startswith("/") or len(parts) < 2 or len(value) > 1024
            or any(part in ("", ".", "..") or len(os.fsencode(part)) > 255 for part in parts)
            or any(char == "\\" or ord(char) < 32 or ord(char) == 127 for char in value)):
        raise ValueError("Укажи путь на NAS в формате /Том/Папка")
    return value


# Читает или сохраняет общий адрес SMB-архива в SQLite.
# Проверяет ожидаемую версию и пишет историю, сохранение адреса само папок не создаёт.
def settings(store, payload=None):
    metadata = MetadataStore(store)
    with LOCK if payload is not None else nullcontext():
        record = metadata.get(SETTINGS, "")
        if record and (type(record.get("version")) is not int or record["version"] != 1):
            raise ValueError("Неизвестный формат настроек NAS")
        if payload is not None:
            data = {"version": 1, "root": root_path(payload.get("root"))}
            with metadata.connect() as db:
                audit(db, "metadata_records")
            record = metadata.put(SETTINGS, "", data, payload.get("revision"))
    return {"root": root_path(record.get("root")) if record else DEFAULT_ROOT,
            "revision": record["revision"] if record else "missing"}


# Находит конкретный SMB-том в таблице монтирования macOS.
# Возвращает путь, устройство и адрес SMB без имени пользователя и пароля.
def mounted_volume(name):
    target = VOLUMES / name
    listing = subprocess.run(["/sbin/mount", "-t", "smbfs"], check=True, capture_output=True, text=True, timeout=3)
    marker = f" on {target} (smbfs,"
    for line in listing.stdout.splitlines():
        source, separator, _ = line.rpartition(marker)
        if not separator or not source.startswith("//"):
            continue
        host, _, share = source[2:].partition("/")
        host = host.rsplit("@", 1)[-1]
        host = re.sub(r"\._smb\._tcp(?=\.local(?::[0-9]+)?$)", "", host, flags=re.IGNORECASE)
        if not share or not re.fullmatch(r"(?:[a-zA-Z0-9_.-]+|\[[0-9a-fA-F:]+\])(?::[0-9]+)?", host):
            break
        device = target.stat().st_dev
        if device != VOLUMES.stat().st_dev:
            return target, device, f"smb://{host}/" + quote(unquote(share), safe="/")
    raise FileNotFoundError(f"Том NAS «{name}» не подключён на сервере")


# Открывает компоненты пути по дескриптору того же сетевого тома.
# Ссылки и переход на другое устройство запрещены, создание разрешено только по явному запросу.
@contextmanager
def descend(directory, parts, *, create=False):
    current = os.dup(directory)
    device = os.fstat(current).st_dev
    try:
        for part in parts:
            try:
                child = os.open(part, order_folders.DIRECTORY_FLAGS, dir_fd=current)
            except FileNotFoundError:
                if not create:
                    raise
                try:
                    os.mkdir(part, dir_fd=current)
                except FileExistsError:
                    pass
                child = os.open(part, order_folders.DIRECTORY_FLAGS, dir_fd=current)
            os.close(current)
            current = child
            if os.fstat(current).st_dev != device:
                raise OSError("Путь выходит за пределы сетевого тома")
        yield current
    finally:
        os.close(current)


# Открывает настроенный архивный корень по настоящему SMB-монтированию.
# Передаёт дескриптор, устройство, путь Finder и SMB-адрес существующего корня.
@contextmanager
def mounted_root(path):
    share, *parts = Path(path).parts[1:]
    volume, device, address = mounted_volume(share)
    fd = os.open(volume, order_folders.DIRECTORY_FLAGS)
    try:
        if os.fstat(fd).st_dev != device:
            raise OSError("Сетевой том изменился")
        with descend(fd, parts) as directory:
            yield directory, device, volume.joinpath(*parts), address + "/" + quote("/".join(parts))
    finally:
        os.close(fd)


# Читает наличие и пустоту конечной папки архива без обхода файлов.
# Любая непосредственная запись, в том числе скрытая, блокирует выключение.
def archive_state(directory, parts):
    try:
        with descend(directory, (*parts, ARCHIVE)) as target:
            info = os.fstat(target)
            with os.scandir(target) as entries:
                reason = "Папка NAS не пуста" if next(entries, None) else ""
            return True, f"{order_folders.service_parent_key(info)}:{info.st_ctime_ns}", reason
    except FileNotFoundError:
        return False, "", ""
    except OSError as error:
        if error.errno in (errno.ENOTDIR, errno.ELOOP):
            return False, "", "На пути к архиву есть файл или ссылка"
        raise


# Читает, открывает или меняет # nas по проверенному пути заказа.
# Привязка хранит исходный относительный путь, перемещения заказа обновляют её ключ в SQLite.
def archive(store, relative, payload=None, *, open_finder=False):
    with LOCK if payload is not None or open_finder else nullcontext():
        relative = unicodedata.normalize("NFC", store.path(relative))
        target = store.target(relative)
        if not order_folders.can_manage_service_folders(relative, store.require_order_folder(relative)):
            raise ValueError("Папка NAS доступна только в заказе клиента")
        parent = order_folders.service_parent_key(target.stat())
        config = settings(store)
        metadata = MetadataStore(store)
        binding = metadata.get(BINDING, relative)
        if binding and binding.get("version") != 1:
            raise ValueError("Неизвестный формат пути архива заказа")
        archive_path = store.path(binding.get("archive") if binding else relative)
        parts = Path(archive_path).parts
        state = {"enabled": False, "revision": None, "reason": "", "url": "", "finder_path": ""}
        if payload is not None and type(payload.get("enabled")) is not bool:
            raise ValueError("Выбери состояние переключателя NAS")
        if not binding:
            with metadata.connect() as db:
                used = db.execute("SELECT 1 FROM metadata_records WHERE kind=? AND path<>? AND json_extract(data,'$.archive')=?",
                                  (BINDING, relative, archive_path)).fetchone()
            if used:
                reason = "Этот путь NAS закреплён за ранее перенесённым заказом"
                if payload is not None or open_finder:
                    raise order_folders.OrderFolderConflict(reason)
                return {**state, "reason": reason}
        try:
            with mounted_root(config["root"]) as (directory, device, mounted_path, address):
                enabled, key, reason = archive_state(directory, parts)
                revision_input = [parent, config["revision"], address, device, archive_path]
                revision = hashlib.sha256(json.dumps([*revision_input, key]).encode()).hexdigest()
                if payload is not None and (payload.get("revision") != revision or reason):
                    raise order_folders.OrderFolderConflict(reason or "Архив изменился. Проверь текущее состояние")
                if payload is not None and payload["enabled"] != enabled:
                    if payload["enabled"] and not binding:
                        with order_folders.LOCK:
                            if order_folders.service_parent_key(store.target(relative).stat()) != parent:
                                raise order_folders.OrderFolderConflict("Папка заказа изменилась. Открой её заново")
                            with metadata.connect() as db:
                                audit(db, "metadata_records")
                            metadata.put(BINDING, relative, {"version": 1, "archive": archive_path}, "missing")
                    try:
                        with descend(directory, parts, create=payload["enabled"]) as order:
                            if payload["enabled"]:
                                os.mkdir(ARCHIVE, dir_fd=order)
                            else:
                                os.rmdir(ARCHIVE, dir_fd=order)
                    except OSError as error:
                        if error.errno in (errno.ENOTEMPTY, errno.EEXIST, errno.ENOENT, errno.ENOTDIR, errno.ELOOP):
                            raise order_folders.OrderFolderConflict("Папка NAS изменилась. Проверь её состояние") from error
                        raise
                    enabled, key, reason = archive_state(directory, parts)
                    revision = hashlib.sha256(json.dumps([*revision_input, key]).encode()).hexdigest()
                url = address + "/" + quote("/".join((*parts, ARCHIVE))) if enabled else ""
                finder_path = str(mounted_path.joinpath(*parts, ARCHIVE)) if enabled else ""
                if open_finder:
                    if not enabled:
                        raise order_folders.OrderFolderConflict(reason or "Папка # nas ещё не создана")
                    with descend(directory, (*parts, ARCHIVE)):
                        try:
                            subprocess.run(["/usr/bin/open", "-a", "Finder", finder_path], check=True, capture_output=True, timeout=8)
                        except subprocess.SubprocessError as error:
                            raise order_folders.OrderFolderConflict("Finder не открыл папку NAS") from error
                return {"enabled": enabled, "revision": revision, "reason": reason, "url": url, "finder_path": finder_path}
        except (OSError, subprocess.SubprocessError) as error:
            reason = str(error) if isinstance(error, FileNotFoundError) and error.filename is None else f"Папка NAS {config['root']} недоступна"
            if payload is not None or open_finder:
                raise order_folders.OrderFolderConflict(reason) from error
            return {**state, "reason": reason}
