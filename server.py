#!/usr/bin/env python3
import configparser
import hashlib
import json
import mimetypes
import os
import plistlib
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unicodedata
import urllib.parse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from zoneinfo import ZoneInfo
from orders import OrderStore, OrderConflict, CARD, SNAPSHOT, is_service_folder
import order_document
import file_comments
from mobile_sync import MobileBridge, RUN_LOCK
import image_reports
import invoices
import native_renderers
import icloud_access
import spreadsheet_preview
from local_metadata import MetadataStore
import order_folders
import order_creation
import event_folders
import folder_rename
import event_trash
import sketches
from event_folder_undo import EventRenamePending, guard_database
from folder_notes import FolderNotes, FolderNoteConflict, parent_order
import event_relevance
from order_todos import OrderTodos
import file_trash
import object_years
import file_uploads
import work_orders
from file_comments import FileCommentConflict
from folder_structure import folder_role, is_catalog_group, client_name, is_print_section
from folder_structure import client_path
from client_activity import ClientActivity, ClientActivityConflict
from client_activity import is_inactive
from object_activity import ObjectActivity

APP_DIR = Path(__file__).resolve().parent
CONFIG_FILE = APP_DIR / "manager.ini"
STATIC_DIR = APP_DIR / "static"
RELEASE_ID = (APP_DIR / ".release-id").read_text().strip() if (APP_DIR / ".release-id").exists() else "development"
DATA_DIR = APP_DIR / "data"
DATABASE_ONLY = True
STATUSES_FILE = DATA_DIR / "statuses.json"
STATUS_DOCUMENT_NAME = order_document.DOCUMENT
LEGACY_STATUS_DOCUMENT_NAMES = order_document.LEGACY_STATUSES
PRINT_HISTORY_DIR = ".print-history"
STATUS_LOCK = threading.RLock()
PREVIEW_LOCKS = [threading.Lock() for _ in range(32)]
PREVIEW_SLOTS = threading.BoundedSemaphore(4)
PDF_BUILD_LOCK = threading.Lock()
PDF_INFO_CACHE = {}
PRINT_LOCK = threading.RLock()
PRINT_TEXT_EXTENSIONS = {".txt", ".text", ".md", ".rtf", ".textclipping", ""}
MAX_PRINT_BYTES = 2 * 1024 * 1024


def read_config(path=CONFIG_FILE):
    config = configparser.ConfigParser(interpolation=None)
    if not config.read(path, encoding="utf-8"):
        raise ValueError(f"Не найден файл настроек: {path}")
    root_value = os.environ.get("ZIGZAG_DATA_ROOT") or config.get("storage", "root", fallback="").strip()
    if not root_value:
        raise ValueError("Укажите root в секции [storage] файла manager.ini")
    root = Path(root_value).expanduser()
    if not root.is_absolute():
        root = Path(path).resolve().parent / root
    host = os.environ.get("MANAGER_HOST") or config.get("server", "host", fallback="127.0.0.1")
    port = config.getint("server", "port", fallback=8765)
    if not 1 <= port <= 65535:
        raise ValueError("Порт в manager.ini должен быть от 1 до 65535")
    return root.resolve(), host, port


DATA_ROOT, SERVER_HOST, SERVER_PORT = read_config()
STATUS_LABELS = {
    "unspecified": "Не указан",
    "new": "Новый", "measure": "Замеры", "process": "Расчеты",
    "workshop": "В цех", "install": "Монтаж", "rework": "Переделка/доделка",
    "finishing": "Завершение/добивка", "deferred": "Отложен/возможно",
    "done": "Готово", "done_but": "Готово, но…", "cancelled": "Отменён",
}
FINANCIAL_STATUS_LABELS = order_document.FINANCIAL_STATUS_LABELS
STATUS_KEYWORDS = [
    ("done", ("готово", "итоги", "заверш")),
    ("install", ("монтаж", "установка")),
    ("workshop", ("в цех", "цех", "покрас", "laser", "glass", "freza", "cutter")),
    ("measure", ("замер", "уточн", "список")),
    ("process", ("process", "делаем", "почти", "temp")),
]
EXT_GROUPS = {
    "images": {".jpg", ".jpeg", ".png", ".gif", ".heic", ".heif", ".webp", ".avif", ".tif", ".tiff", ".bmp"},
    "video": {".mov", ".mp4", ".m4v", ".webm", ".avi"},
    "audio": {".mp3", ".wav", ".m4a", ".ogg", ".aac", ".flac"},
    "pdf": {".pdf"},
    "design": {".cdr", ".ai", ".eps", ".svg", ".psd", ".dxf"},
    "docs": {".doc", ".docx", ".xls", ".xlsx", ".xlsm", ".xlsb", ".txt", ".rtf", ".md", ".csv"},
}
TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".tsv", ".json", ".ini", ".log", ".yaml", ".yml", ".xml", ".py", ".js", ".css"}
BROWSER_IMAGES = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif", ".bmp", ".svg"}


def normalized(value):
    return unicodedata.normalize("NFC", value).casefold()


def hash_folder_name(name):
    return normalized(name[1:].strip()) if name.startswith("#") else None


def search_text(value):
    return re.sub(r"#\s*", "#", normalized(value))


def is_print_folder(relative):
    parts = Path(relative).parts
    return len(parts) >= 2 and hash_folder_name(parts[0]) == "work" and hash_folder_name(parts[1]) == "print"


def print_target(relative, file=False):
    guard_database(order_store().database, relative)
    target = safe_path(relative)
    if any((DATA_ROOT / Path(*Path(relative).parts[:index + 1])).is_symlink() for index in range(len(Path(relative).parts))):
        raise ValueError("Символические ссылки не редактируются")
    folder = relative_path(target.parent) if file else relative_path(target)
    if not is_print_section(folder):
        raise ValueError("Редактирование доступно только в # work/# print")
    if file:
        if not target.is_file():
            raise FileNotFoundError("Задание не найдено")
        if target.is_symlink() or target.suffix.lower() not in PRINT_TEXT_EXTENSIONS:
            raise ValueError("Выберите текстовый файл задания")
    elif not target.is_dir():
        raise FileNotFoundError("Папка заданий не найдена")
    return target


class PrintConflict(ValueError):
    pass


def text_from_rtf(value):
    raw = value.encode("utf-8") if isinstance(value, str) else value
    try:
        result = subprocess.run(["/usr/bin/textutil", "-convert", "txt", "-stdin", "-stdout", "-format", "rtf"],
                                input=raw, capture_output=True, check=True, timeout=15)
        return result.stdout.decode("utf-8")
    except (OSError, subprocess.SubprocessError, UnicodeDecodeError):
        raise ValueError("Не удалось прочитать текст задания")


def text_to_rtf(text):
    escaped = []
    units = text.encode("utf-16-le")
    for offset in range(0, len(units), 2):
        unit = int.from_bytes(units[offset:offset + 2], "little")
        if unit in (ord("\\"), ord("{"), ord("}")):
            escaped.append("\\" + chr(unit))
        elif unit == 10:
            escaped.append("\\par\n")
        elif unit == 9:
            escaped.append("\\tab ")
        elif 32 <= unit < 127:
            escaped.append(chr(unit))
        else:
            escaped.append(f"\\u{unit if unit < 32768 else unit - 65536}?")
    return "{\\rtf1\\ansi\\ansicpg1251\\uc1 " + "".join(escaped) + "}"


def decode_print_document(target, raw):
    extension = target.suffix.lower()
    if extension == ".textclipping":
        try:
            representations = plistlib.loads(raw)["UTI-Data"]
            for key, encoding in (("public.utf8-plain-text", "utf-8"), ("public.utf16-plain-text", "utf-16"), ("public.plain-text", "utf-8")):
                if key in representations:
                    value = representations[key]
                    return (value.decode(encoding) if isinstance(value, bytes) else value), "clipping"
            if "public.rtf" in representations:
                return text_from_rtf(representations["public.rtf"]), "clipping"
        except (plistlib.InvalidFileException, KeyError, TypeError, UnicodeDecodeError, ValueError):
            raise ValueError("Не удалось прочитать текстовое вырезание macOS")
        raise ValueError("В вырезании нет текста")
    if extension == ".rtf":
        return text_from_rtf(raw), "rtf"
    encoding = "utf-8-sig" if raw.startswith(b"\xef\xbb\xbf") else "utf-16" if raw.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8"
    try:
        text = raw.decode(encoding)
    except UnicodeDecodeError:
        encoding = "cp1251"
        text = raw.decode(encoding)
    if "\x00" in text:
        raise ValueError("Файл не является текстовым")
    return text, encoding


def encode_print_document(target, text, encoding="utf-8", original=None):
    if target.suffix.lower() == ".textclipping":
        document = plistlib.loads(original) if original else {}
        document["UTI-Data"] = {"public.utf8-plain-text": text, "public.rtf": text_to_rtf(text)}
        return plistlib.dumps(document, fmt=plistlib.FMT_BINARY)
    if target.suffix.lower() == ".rtf":
        return text_to_rtf(text).encode("ascii")
    try:
        return text.encode(encoding)
    except UnicodeEncodeError:
        raise ValueError("Этот файл не поддерживает введённые символы")


def split_print_text(text):
    lines = text.replace("\r\n", "\n").split("\n")

    def is_link(line):
        parsed = urllib.parse.urlparse(line)
        return parsed.scheme.lower() in {"http", "https"} and bool(parsed.netloc) and not any(char.isspace() for char in line)

    # A labelled title keeps the description unambiguous, including URLs in it.
    header_index = 2 if len(lines) > 2 and is_link(lines[0].strip()) and not lines[1] else 0
    if lines[header_index].startswith("Название: ") or lines[header_index] == "Название:":
        title = lines[header_index].partition(":")[2].strip()
        remaining = lines[header_index + 1:]
        if remaining and not remaining[0]:
            remaining.pop(0)
        return lines[0].strip() if header_index else "", title, "\n".join(remaining)

    for index, line in enumerate(lines):
        link = line.strip()
        if not is_link(link):
            continue
        if index > 0 and lines[0].strip() and all(not item.strip() for item in lines[1:index]):
            remaining = lines[index + 1:]
            if remaining and not remaining[0]:
                remaining.pop(0)
            return link, lines[0].strip(), "\n".join(remaining)
        remaining = lines[:index] + lines[index + 1:]
        if index == 0 and remaining and not remaining[0]:
            remaining.pop(0)
        elif index > 0 and not lines[index - 1] and index + 1 < len(lines) and not lines[index + 1]:
            remaining.pop(index - 1)
        return link, "", "\n".join(remaining)
    return "", "", text


def compose_print_text(link, description, title=""):
    if not all(isinstance(value, str) for value in (link, description, title)):
        raise ValueError("Укажите название, ссылку и описание текстом")
    if any(char in title for char in "\r\n\x00"):
        raise ValueError("Название должно быть одной строкой")
    link = link.strip()
    parsed = urllib.parse.urlparse(link)
    if link and (parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc or any(char.isspace() for char in link)):
        raise ValueError("Ссылка должна начинаться с http:// или https://")
    text = (link + "\n\n" if link else "") + "Название: " + title.strip() + "\n\n" + description
    if len(text.encode("utf-8")) > MAX_PRINT_BYTES:
        raise ValueError("Задание слишком большое")
    return text


def read_print_task(relative):
    with PRINT_LOCK:
        return _read_print_task(relative)


def _read_print_task(relative):
    if DATABASE_ONLY:
        if not isinstance(relative,str) or '\x00' in relative:
            raise ValueError("Выбери задание в # work/# print")
        if not is_print_folder(str(Path(relative).parent)) or Path(relative).name.startswith('.') or len(Path(relative).parts)!=3:
            raise ValueError("Выбери задание в # work/# print")
        current = metadata_store().get("print",relative)
        if current:
            return {**current,"name":Path(relative).name,"modified":current["updated"],"storage":"database"}
        if metadata_store().is_publication(relative):
            raise ValueError("Это выпущенный документ, он не создаёт отдельное задание печати")
        target = print_target(relative,file=True)
        raw = metadata_store().archive(target)
        text,_ = decode_print_document(target,raw)
        link,title,description = split_print_text(text)
        current = metadata_store().put("print",relative,{"title":title,"link":link,"description":description},"missing")
        metadata_store().imported("print",relative)
        return {**current,"name":target.name,"modified":current["updated"],"storage":"database"}
    target = print_target(relative, file=True)
    raw = target.read_bytes()
    if len(raw) > MAX_PRINT_BYTES:
        raise ValueError("Задание слишком большое для редактора")
    text, encoding = decode_print_document(target, raw)
    link, title, description = split_print_text(text)
    return {"path": relative_path(target), "name": target.name, "title": title, "link": link, "description": description,
            "revision": hashlib.sha256(raw).hexdigest(), "modified": target.stat().st_mtime}


def next_print_name(folder):
    if DATABASE_ONLY:
        stem = "print - "+datetime.now(ZoneInfo("Europe/Moscow")).strftime("%Y-%m-%d")
        number = 1
        while True:
            filename = stem+("" if number==1 else f" ({number})")+".txt"
            if not (folder/filename).exists() and not metadata_store().get("print",relative_path(folder/filename)):
                return filename
            number += 1
    templates = [item for item in folder.iterdir() if visible(item) and item.is_file()
                 and item.suffix.lower() in PRINT_TEXT_EXTENSIONS and re.match(r"^print\s*-\s*\d{4}-\d{2}-\d{2}", item.name, re.I)]
    extension = max(templates, key=lambda item: item.stat().st_mtime).suffix if templates else ".textClipping"
    date = datetime.now(ZoneInfo("Europe/Moscow")).date().isoformat()
    stem = f"print - {date}"
    name, number = stem + extension, 2
    while (folder / name).exists():
        name = f"{stem} ({number}){extension}"
        number += 1
    return name


def create_print_task(relative, link, description, title=""):
    if DATABASE_ONLY:
        folder = print_target(relative)
        compose_print_text(link,description,title)  # Existing validation.
        with PRINT_LOCK:
            stem = "print - "+datetime.now(ZoneInfo("Europe/Moscow")).strftime("%Y-%m-%d")
            index = 1
            while True:
                filename = stem+("" if index==1 else f" ({index})")+".txt"
                path = str(Path(relative)/filename)
                if not metadata_store().get("print",path) and not (folder/filename).exists():
                    break
                index += 1
            metadata_store().put("print",path,{"title":title.strip(),"link":link.strip(),"description":description},"missing")
            return read_print_task(path)
    folder = print_target(relative)
    text = compose_print_text(link, description, title)
    with PRINT_LOCK:
        while True:
            target = folder / next_print_name(folder)
            body = encode_print_document(target, text)
            if len(body) > MAX_PRINT_BYTES:
                raise ValueError("Задание слишком большое")
            try:
                descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
            except FileExistsError:
                continue
            try:
                with os.fdopen(descriptor, "wb") as stream:
                    stream.write(body)
            except OSError:
                target.unlink(missing_ok=True)
                raise
            return read_print_task(relative_path(target))


def save_print_task(relative, link, description, revision, title=None):
    if DATABASE_ONLY:
        with PRINT_LOCK:
            current = read_print_task(relative)
            title = current["title"] if title is None else title
            compose_print_text(link,description,title)
            metadata_store().put("print",relative,{"title":title.strip(),"link":link.strip(),"description":description},revision)
            return read_print_task(relative)
    target = print_target(relative, file=True)
    with PRINT_LOCK:
        original = target.read_bytes()
        if hashlib.sha256(original).hexdigest() != revision:
            raise PrintConflict("Файл изменён в другой программе. Перезагрузите задание перед сохранением.")
        old_text, encoding = decode_print_document(target, original)
        old_link, old_title, old_description = split_print_text(old_text)
        if title is None:
            title = old_title
        text = compose_print_text(link, description, title)
        if text == old_text or (link.strip() == old_link and title.strip() == old_title and description == old_description):
            return read_print_task(relative)
        body = encode_print_document(target, text, encoding, original)
        if len(body) > MAX_PRINT_BYTES:
            raise ValueError("Задание слишком большое")
        history = target.parent / PRINT_HISTORY_DIR / target.name
        if history.parent.is_symlink() or history.is_symlink():
            raise ValueError("Папка истории не должна быть символической ссылкой")
        history.mkdir(parents=True, exist_ok=True)
        backup = history / (hashlib.sha256(original).hexdigest() + target.suffix)
        if backup.is_symlink():
            raise ValueError("Файл истории не должен быть символической ссылкой")
        if not backup.exists():
            backup.write_bytes(original)
        temporary = target.with_name(".manager-" + target.name + ".tmp")
        try:
            temporary.write_bytes(body)
            temporary.chmod(target.stat().st_mode & 0o777)
            if target.read_bytes() != original:
                raise PrintConflict("Файл изменён в другой программе. Перезагрузите задание перед сохранением.")
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
        return read_print_task(relative)


def sort_key(path):
    return [(1, int(part)) if part.isdigit() else (0, normalized(part)) for part in re.split(r"(\d+)", path.name)]


def directory_sort_key(path):
    name = "#" + path.name[1:].strip() if path.name.startswith("#") else path.name
    return (not path.name.startswith("#"), sort_key(Path(name)))


def folder_sort_key(relative_folder):
    return tuple(directory_sort_key(Path(part)) for part in Path(relative_folder).parts)


def visible(path):
    return not path.name.startswith(".") and not path.is_symlink()


def safe_path(relative_path=""):
    if not isinstance(relative_path, str):
        raise ValueError("Некорректный путь")
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Путь за пределами папки данных")
    target = DATA_ROOT / relative
    resolved = target.resolve()
    if resolved != DATA_ROOT and DATA_ROOT not in resolved.parents:
        raise ValueError("Путь за пределами папки данных")
    if any(part.startswith(".") for part in relative.parts):
        raise ValueError("Скрытые файлы недоступны")
    return target


def relative_path(path):
    return path.relative_to(DATA_ROOT).as_posix() if path != DATA_ROOT else ""


def comment_file(relative):
    guard_database(order_store().database, relative)
    target = safe_path(relative)
    if any((DATA_ROOT / Path(*Path(relative).parts[:index + 1])).is_symlink() for index in range(len(Path(relative).parts))):
        raise ValueError("Комментарии к символическим ссылкам не редактируются")
    if not target.is_file():
        raise FileNotFoundError("Файл не найден")
    return target


def create_image_report(relative, selected):
    folder = safe_path(relative)
    if not folder.is_dir():
        raise FileNotFoundError("Папка для отчёта не найдена")
    if any((DATA_ROOT / Path(*Path(relative).parts[:index + 1])).is_symlink() for index in range(len(Path(relative).parts))):
        raise ValueError("Отчёт нельзя сохранять через символическую ссылку")
    if not isinstance(selected, list) or not selected or len(selected) > 1000 or any(not isinstance(path, str) for path in selected):
        raise ValueError("Выберите файлы для отчёта")
    items, skipped = [], 0
    for path in dict.fromkeys(selected):
        target = comment_file(path)
        if folder not in target.parents:
            raise ValueError("Выбранный файл находится вне открытой папки")
        if file_group(target) != "images":
            skipped += 1
            continue
        items.append({"path": str(target), "comment": read_file_comment(target)["comment"]})
    if not items:
        raise ValueError("Для PDF-отчёта выберите хотя бы одно изображение")
    if len(items) > image_reports.MAX_IMAGES:
        raise ValueError(f"В один отчёт можно включить до {image_reports.MAX_IMAGES} изображений")
    target, pages = image_reports.create(folder, items, APP_DIR, DATA_DIR)
    return {"path": relative_path(target), "name": target.name, "imageCount": len(items), "skippedCount": skipped, "pages": pages}


def directory_children(path):
    return sorted((item for item in path.iterdir() if visible(item) and item.is_dir()), key=directory_sort_key)


def folder_node(path):
    try:
        has_children = any(visible(item) and item.is_dir() for item in path.iterdir())
    except OSError:
        has_children = False
    return {"name": path.name, "path": relative_path(path), "hasChildren": has_children}


def read_tree(relative="", query="", show_inactive=False):
    target = safe_path(relative)
    if not target.is_dir():
        raise FileNotFoundError("Папка данных не найдена. Проверьте manager.ini")
    inactive = inactive_paths()
    def children_of(path):
        return [item for item in directory_children(path)
                if show_inactive or not is_inactive(relative_path(item), inactive)]
    def node_of(path):
        return {**folder_node(path), "inactive": is_inactive(relative_path(path), inactive)}
    children = children_of(target)
    auxiliary = []
    group_folders = []
    if target == DATA_ROOT:
        auxiliary = [node_of(item) for item in children if item.name.startswith("#")]
        group_folders = [item for item in children if is_catalog_group(item.name)]
        children = [item for item in children if not item.name.startswith("#") and not is_catalog_group(item.name)]
    if query:
        needle = search_text(query.strip())

        def matching_node(path):
            node = node_of(path)
            try:
                descendants = [result for child in children_of(path) if (result := matching_node(child))]
            except OSError:
                descendants = []
            if needle in search_text(relative_path(path)) or descendants:
                node["children"] = descendants
                return node
            return None

        nodes = [node for item in children if (node := matching_node(item))]
        groups = [node for item in group_folders if (node := matching_node(item))]
    else:
        nodes = [node_of(item) for item in children]
        groups = []
        for item in group_folders:
            node = {**node_of(item), "children": []}
            try:
                node["children"] = [node_of(child) for child in children_of(item)]
            except OSError as error:
                node["error"] = "Не удалось прочитать группу: " + str(error)
            groups.append(node)
    return {"root": str(DATA_ROOT), "rootName": DATA_ROOT.name, "path": relative,
            "children": nodes, "groups": groups, "auxiliary": auxiliary}


def file_group(path):
    return next((group for group, extensions in EXT_GROUPS.items() if path.suffix.lower() in extensions), "other")


def preview_kind(path):
    ext = path.suffix.lower()
    if ext in spreadsheet_preview.EXTENSIONS:
        return "spreadsheet"
    if ext in BROWSER_IMAGES or ext in {".heic", ".heif", ".tif", ".tiff"}:
        return "image"
    if ext == ".pdf":
        return "pdf"
    if ext in {".mov", ".mp4", ".m4v", ".webm"}:
        return "video"
    if ext in {".mp3", ".wav", ".m4a", ".ogg", ".aac", ".flac"}:
        return "audio"
    if ext in TEXT_EXTENSIONS:
        return "text"
    return "native"


def load_legacy_statuses():
    if not STATUSES_FILE.exists():
        return {}
    records = json.loads(STATUSES_FILE.read_text(encoding="utf-8"))
    if not isinstance(records, dict):
        raise ValueError("Некорректный файл статусов")
    return records


def status_document(folder):
    target = folder / STATUS_DOCUMENT_NAME
    with STATUS_LOCK:
        if target.is_symlink() or (target.exists() and not target.is_file()):
            raise ValueError(f"Вместо {STATUS_DOCUMENT_NAME} должен быть обычный текстовый файл")
        legacy = any((folder / name).exists() or (folder / name).is_symlink() for name in order_document.LEGACY_DOCUMENTS)
        service = is_service_folder(relative_path(folder))
        if legacy or (service and target.exists()):
            relative = folder.relative_to(DATA_ROOT)
            if any((DATA_ROOT / Path(*relative.parts[:index + 1])).is_symlink() for index in range(len(relative.parts))):
                raise ValueError("Символические ссылки не редактируются")
            record = order_document.load(folder, STATUS_LABELS)
            clean_service_card = service and bool(order_document.ORDER_FIELDS.intersection(record))
            if service:
                record = order_document.folder_note(record)
            if record and (not target.exists() or clean_service_card):
                order_document.atomic_write(target, order_document.render(record, STATUS_LABELS))
            if target.exists():
                order_document.archive_legacy(folder)
    return target


def read_status_document(folder, *, include_registration=False, include_todos=False):
    target = status_document(folder)
    if not target.exists():
        return {}
    record = order_document.load(folder, STATUS_LABELS)
    keys = ("status", "financial_status", "note", "registered") if include_registration else ("status", "financial_status", "note")
    result = {key: record[key] for key in keys if key in record}
    if include_todos:
        blocks = record.get("extra_blocks", {})
        result.update(extra_blocks=blocks, todo_items=order_document.read_todos(blocks),
                      purchase_items=order_document.read_purchases(blocks))
    return result


def write_status_document(folder, status, note, financial_status=None, todo_items=order_document.UNSET_TODOS,
                          purchase_items=order_document.UNSET_TODOS):
    with STATUS_LOCK:
        target = status_document(folder)
        record = order_document.load(folder, STATUS_LABELS)
        if is_service_folder(relative_path(folder)):
            record = order_document.folder_note(record)
        else:
            record["status"] = status
            if financial_status is not None:
                record["financial_status"] = financial_status
            if todo_items is not order_document.UNSET_TODOS:
                record["extra_blocks"] = order_document.write_todos(record.get("extra_blocks", {}), todo_items)
            if purchase_items is not order_document.UNSET_TODOS:
                blocks = record.get("extra_blocks", {})
                if order_document.read_purchases(blocks) is None:
                    raise ValueError("Прежние записи закупок и затрат сохранены. Проверь раздел в !.txt заказа")
                record["extra_blocks"] = order_document.write_purchases(blocks, purchase_items)
        record["note"] = note
        if record.get("schema", 0) < order_document.FORMAT:
            order_document.archive_current(folder)
        order_document.atomic_write(target, order_document.render(record, STATUS_LABELS))


def editable_status_folder(relative):
    guard_database(order_store().database, relative)
    target = safe_path(relative)
    if not relative or not target.is_dir():
        raise ValueError("Выберите папку заказа")
    if any((DATA_ROOT / Path(*Path(relative).parts[:index + 1])).is_symlink() for index in range(len(Path(relative).parts))):
        raise ValueError("Символические ссылки не редактируются")
    return target


def migrate_statuses():
    """Move old app-local records into readable files without replacing local edits."""
    with STATUS_LOCK:
        if not STATUSES_FILE.exists():
            return None
        records = load_legacy_statuses()
        migrated, unresolved = 0, []
        pending = {}
        for relative, record in records.items():
            if not isinstance(relative, str) or not isinstance(record, dict):
                unresolved.append(str(relative))
                continue
            candidates = [relative]
            if re.match(r"^\d{4}/", relative):
                candidates.append(relative[5:])
            folder = None
            for candidate in candidates:
                try:
                    folder = editable_status_folder(candidate)
                    break
                except (ValueError, OSError):
                    continue
            try:
                record = order_document.split_statuses(record, STATUS_LABELS)
            except (ValueError, TypeError):
                unresolved.append(relative)
                continue
            status, note = record.get("status"), record.get("note", "")
            if folder is None or not isinstance(status, str) or status not in STATUS_LABELS or not isinstance(note, str):
                unresolved.append(relative)
                continue
            pending.setdefault(relative_path(folder), []).append((relative, folder, status, note, record.get("financial_status", "unspecified")))
        for key, entries in pending.items():
            direct = next((entry for entry in entries if entry[0] == key), None)
            if direct is None and len(entries) != 1:
                unresolved.extend(entry[0] for entry in entries)
                continue
            _, folder, status, note, financial_status = direct or entries[0]
            if not status_document(folder).exists():
                write_status_document(folder, status, note, financial_status)
                migrated += 1
        archive = DATA_ROOT / ".legacy-statuses.json"
        number = 2
        while archive.exists() or archive.is_symlink():
            archive = DATA_ROOT / f".legacy-statuses-{number}.json"
            number += 1
        shutil.move(str(STATUSES_FILE), str(archive))
        return {"migrated": migrated, "unresolved": unresolved, "archive": str(archive)}


def order_store():
    return OrderStore(DATA_ROOT, DATA_DIR, STATUS_LABELS,database_only=DATABASE_ONLY)


def metadata_store():
    return MetadataStore(order_store())


def read_file_comment(file):
    return metadata_store().comment(file) if DATABASE_ONLY else file_comments.read(file)


def invoice_store():
    return invoices.InvoiceStore(order_store(), APP_DIR)


def schedule_mobile_sync():
    if DATABASE_ONLY:
        return
    threading.Thread(target=MobileBridge(order_store()).run, daemon=True).start()


def mobile_sync_worker():
    if DATABASE_ONLY:
        return
    while True:
        try:
            MobileBridge(order_store()).run()
        except Exception as error:
            print(f"Обмен с iPhone: {error}", flush=True)
        threading.Event().wait(60)


SCAN_LOCK = threading.Lock()
SCAN_STATE = {"running": False, "folders": 0, "added": 0, "errors": []}


def discover_orders():
    with SCAN_LOCK:
        if SCAN_STATE["running"]:
            return dict(SCAN_STATE)
        SCAN_STATE.update(running=True, folders=0, added=0, errors=[])

    def work():
        try:
            order_store().discover(read_status_document, SCAN_STATE)
        except Exception as error:
            SCAN_STATE["errors"].append(str(error))
        finally:
            SCAN_STATE["running"] = False
            schedule_order_sync()
            schedule_todo_refresh()

    threading.Thread(target=work, daemon=True).start()
    return dict(SCAN_STATE)


def schedule_order_sync():
    def sync():
        order_store().sync()
        folder_note_store().sync()
        client_activity_store().sync()
        object_activity_store().sync()
        invoice_store().sync()
        if DATABASE_ONLY:
            metadata_store().sync()
    threading.Thread(target=sync, daemon=True).start()


def folder_note_store():
    return FolderNotes(order_store(), status_document)


def sketch_target(relative, key=None):
    folder = sketches.folder_path(relative)
    target = comment_file(relative)
    order_store().require_order_folder(Path(folder).parent.as_posix())
    if key is not None and key != file_comments.binding(target):
        raise FolderNoteConflict("Страница относится к другому эскизу. Обнови страницу")
    return target


def read_sketches(directories, warnings):
    result = []
    notes = FolderNotes(order_store())
    for folder in directories:
        if not sketches.cdr_folder(folder.name) or folder.is_symlink():
            continue
        record, error = None, ""
        try:
            record = notes.read(relative_path(folder))
        except (OSError, ValueError) as problem:
            error = str(problem)
            try:
                record = notes.get(relative_path(folder))
            except (OSError, ValueError):
                pass
        try:
            for file in sorted(folder.iterdir(), key=sort_key):
                if not visible(file) or not sketches.sketch_name(file.name) or not file.is_file():
                    continue
                try:
                    result.append({"name": file.name, "path": relative_path(file), "folder": relative_path(folder),
                                   "key": file_comments.binding(file), "preview_version": sketches.fingerprint(file),
                                   "relevance": sketches.info(record, file.name, error)})
                except OSError as problem:
                    warnings.append("Не удалось прочитать эскиз: " + file.name + ": " + str(problem))
        except OSError as problem:
            warnings.append("Не удалось прочитать эскизы: " + folder.name + ": " + str(problem))
    return sorted(result, key=lambda item: (sort_key(Path(item["name"])), item["folder"]))


def client_activity_store():
    return ClientActivity(order_store(), STATUS_LOCK)


def object_activity_store():
    return ObjectActivity(order_store(), STATUS_LOCK)


def inactive_paths():
    return client_activity_store().inactive_paths() | object_activity_store().inactive_paths()


def listed_orders():
    store = order_store()
    activity = client_activity_store()
    objects = object_activity_store()
    visible = objects.visible_orders(activity.visible_orders(store.list()))
    return {"orders": OrderTodos(store).attach([order for order in visible if not work_orders.in_work(order["path"])]),
            "favorites": [order for order in visible if order["is_favorite"] is True],
            "unregistrations": objects.visible_orders(activity.visible_orders([
                order for order in store.pending_unregistrations() if not work_orders.in_work(order["path"])])), "scan": dict(SCAN_STATE),
            "storage":metadata_store().status() if DATABASE_ONLY else {"database_only":False}}


METADATA_REFRESH = threading.Event()


def metadata_worker():
    if not DATABASE_ONLY:
        return
    refresh = True
    while True:
        METADATA_REFRESH.clear()
        try:
            metadata_store().backup("before-migration")
            order_creation.recover(order_store())
            if refresh or metadata_store().status()["errors"]:
                metadata_store().migrate(sys.modules[__name__])
                metadata_store().imported("migration","")
            metadata_store().backup("daily")
        except Exception as error:
            metadata_store().error("migration","",error)
            print(f"Перенос метаданных в базу: {error}",flush=True)
        refresh = METADATA_REFRESH.wait(60)


def client_activity_worker():
    # File markers are authoritative once exported. Failed reads retain the index.
    while True:
        for activity in (client_activity_store(), object_activity_store()):
            try:
                activity.refresh()
            except Exception as error:
                print(f"Активность {activity.entity}: {error}", flush=True)
        threading.Event().wait(300)


TODO_REFRESH = threading.Event()
TODO_REFRESH_PATHS = set()
TODO_REFRESH_LOCK = threading.Lock()


def schedule_todo_refresh(relative=None):
    if relative:
        with TODO_REFRESH_LOCK:
            TODO_REFRESH_PATHS.add(relative)
    TODO_REFRESH.set()


def order_todo_worker():
    while True:
        TODO_REFRESH.clear()
        try:
            with TODO_REFRESH_LOCK:
                paths = tuple(TODO_REFRESH_PATHS)
                TODO_REFRESH_PATHS.clear()
            OrderTodos(order_store()).refresh(paths)
        except Exception as error:
            print(f"Обновление To-do папок: {error}", flush=True)
        TODO_REFRESH.wait(300)


def order_sync_worker():
    while True:
        try:
            order_store().sync()
            folder_note_store().sync()
            client_activity_store().sync()
            object_activity_store().sync()
            invoice_store().sync()
            if DATABASE_ONLY:
                metadata_store().sync()
        except Exception as error:
            print(f"Выгрузка заказов: {error}", flush=True)
        threading.Event().wait(15)


def folder_status(path, directories):
    relative = relative_path(path)
    role = folder_role(DATA_ROOT, relative)
    service = is_service_folder(relative)
    owner = parent_order(DATA_ROOT, relative) if relative else None
    if DATABASE_ONLY:
        order = order_store().get(relative,include_unregistered=True) if relative else None
        if order and order["registered"]:
            return {**role,"service":False,"status":order["status"],"financial_status":order["financial_status"],"note":order["note"],
                    "todo_items":order["todo_items"],"purchase_items":order["purchase_items"],"extra_blocks":order["extra_blocks"],"statusSource":"database","order":order}
        record = folder_note_store().read(relative)
        body = record["card"]
        note_only = not role["canRegisterOrder"] or bool(order) or body.get("registered") is False
        return {**role,"service":service,"noteOnly":note_only,"eventFolder":bool(owner),"folderNote":record,"draftCard":body,
                "note":record["note"],"todo_items":record["todo_items"],"purchase_items":order_document.read_purchases(body.get("extra_blocks",{})),
                "extra_blocks":record["extra_blocks"],"status":body.get("status","new"),"financial_status":body.get("financial_status","unspecified"),"statusSource":"database"}
    if service and not owner:
        return {**role, "service": True, "note": read_status_document(path).get("note", ""), "statusSource": "manual"}
    order = order_store().get(relative, include_unregistered=True)
    if order and order["registered"]:
        return {**role, "service": False, "status": order["status"], "financial_status": order["financial_status"], "note": order["note"],
                "todo_items": order["todo_items"], "purchase_items": order["purchase_items"], "extra_blocks": order["extra_blocks"], "statusSource": "database", "order": order}
    if order and order["sync_pending"]:
        return {**role, "service": False, "noteOnly": True, "note": order["note"], "statusSource": "database",
                "registrationPending": True, "registrationError": order["sync_error"]}
    if owner:
        record = folder_note_store().read(relative)
        return {**role, "service": service, "noteOnly": True, "eventFolder": True, "folderNote": record,
                "note": record["note"], "todo_items": record["todo_items"], "extra_blocks": record["extra_blocks"], "statusSource": "database"}
    record = read_status_document(path, include_registration=True, include_todos=True)
    haystack = normalized(" ".join([path.name] + [item.name for item in directories]))
    guessed = next((status for status, words in STATUS_KEYWORDS if any(word in haystack for word in words)), "new")
    return {**role, "service": False, "noteOnly": not role["canRegisterOrder"] or bool(order) or record.get("registered") is False,
            "status": record.get("status", guessed), "note": record.get("note", ""),
            "financial_status": record.get("financial_status", "unspecified"),
            "todo_items": record.get("todo_items", []), "purchase_items": record.get("purchase_items", []), "extra_blocks": record.get("extra_blocks", {}),
            "statusSource": "manual" if record.get("status") else "auto"}


def read_folder(relative="", show_inactive=False):
    target = safe_path(relative)
    if not target.is_dir():
        raise FileNotFoundError("Папка не найдена")
    directories = directory_children(target)
    status = folder_status(target, directories)
    if status["folderKind"] == "client":
        status["clientActivity"] = client_activity_store().read(relative_path(target))
    elif status["folderKind"] == "object":
        status["objectActivity"] = object_activity_store().read(relative_path(target))
    inactive = inactive_paths()
    # Прямое открытие неактивной папки сохраняет доступ к её содержимому.
    # В остальных контейнерах скрыты отдельно отмеченные дочерние поддеревья.
    hidden_children = {path for path in inactive if not is_inactive(relative, {path})}
    if not show_inactive:
        directories = [item for item in directories if not is_inactive(relative_path(item), hidden_children)]
    files, warnings = [], []
    print_view = is_print_section(relative)
    files_scope = "events" if status["folderKind"] == "order" or status.get("order") else (
        "subfolders" if not print_view and status["folderKind"] in {"client", "object", "catalog_group", "supplier_root", "work_root", "moneys_root", "work_section", "moneys_section"} else "folder")
    hide_files = files_scope != "folder"
    folder_count = len(directories) if hide_files or print_view else 0

    def walk_error(error):
        warnings.append(f"Не удалось прочитать папку: {error.filename}")

    for current, dirs, names in (() if hide_files else os.walk(target, onerror=walk_error, followlinks=False)):
        current_path = Path(current)
        dirs[:] = [name for name in dirs if visible(current_path / name)]
        if print_view:
            dirs[:] = []  # The print editor owns only immediate task sources.
        folder_count += len(dirs)
        if target == DATA_ROOT:
            dirs[:] = []  # List clients at home without scanning all their orders.
        for name in names:
            if name in (STATUS_DOCUMENT_NAME, "!order.txt", *LEGACY_STATUS_DOCUMENT_NAMES):
                continue
            file = current_path / name
            if print_view and (file.suffix.lower() not in PRINT_TEXT_EXTENSIONS or (DATABASE_ONLY and metadata_store().is_publication(relative_path(file)))):
                continue
            if not visible(file) or not file.is_file():
                continue
            try:
                stat = file.stat()
            except OSError:
                warnings.append(f"Не удалось прочитать файл: {name}")
                continue
            try:
                comment = "" if print_view else read_file_comment(file)["comment"]
            except (OSError, ValueError):
                comment = ""
                warnings.append(f"Не удалось прочитать комментарий: {name}")
            files.append({"name": name, "path": relative_path(file),
                          "folder": current_path.relative_to(target).as_posix() if current_path != target else "",
                          "size": stat.st_size, "modified": stat.st_mtime,
                          "type": file_group(file), "preview": preview_kind(file),
                          "extension": file.suffix.lstrip(".").upper() or "ФАЙЛ", "comment": comment,
                          "comment_key": file_comments.binding(file)})
    if print_view and DATABASE_ONLY:
        for file in list(files):
            try:
                if Path(file["path"]).suffix.lower() in PRINT_TEXT_EXTENSIONS and not metadata_store().is_publication(file["path"]):
                    read_print_task(file["path"])
            except (OSError,ValueError) as error:
                warnings.append("Не удалось перенести задание: "+file["name"]+" · "+str(error))
        with metadata_store().connect() as db:
            records = list(db.execute("SELECT * FROM metadata_records WHERE kind='print' ORDER BY updated DESC"))
        files = [{"name":Path(row["path"]).name,"path":row["path"],"modified":row["updated"],"size":len(row["data"].encode()),
                  "folder":"","type":"docs","extension":"TXT","preview":"text",**json.loads(row["data"])}
                 for row in records if str(Path(row["path"]).parent)==relative]
    if print_view:
        files = [file for file in files if file["name"] != STATUS_DOCUMENT_NAME and Path(file["name"]).suffix.lower() in PRINT_TEXT_EXTENSIONS]
    files.sort(key=lambda file: (folder_sort_key(file["folder"]), sort_key(Path(file["name"]))))
    counts = {group: sum(file["type"] == group for file in files) for group in [*EXT_GROUPS, "other"]}
    parts = Path(relative).parts
    nodes = []
    event_notes = FolderNotes(order_store())  # Список событий не переносит и не переписывает их прежние файлы.
    for item in directories:
        node = {**folder_node(item), "inactive": is_inactive(relative_path(item), inactive)}
        if status["folderKind"] == "order" and not item.name.startswith("#") and not item.is_symlink():
            record = None
            try:
                registered = order_store().get(node["path"])
                if registered:
                    raise ValueError("Эта папка ещё зарегистрирована как отдельный заказ")
                record = event_notes.read(node["path"])
                node["eventRelevance"] = event_relevance.info(record)
            except (OSError, ValueError) as error:
                try:
                    record = event_notes.get(node["path"])
                except (OSError, ValueError):
                    record = None
                node["eventRelevance"] = event_relevance.info(record, str(error))
        nodes.append(node)
    breadcrumbs = [{"name": DATA_ROOT.name, "path": ""}]
    breadcrumbs.extend({"name": part, "path": Path(*parts[:index + 1]).as_posix()} for index, part in enumerate(parts))
    sketch_files = read_sketches(directories, warnings) if status["folderKind"] == "order" else []
    return {"name": target.name, "path": relative_path(target), "client": client_name(relative),
            "workSupplier": work_orders.supplier_name(relative),
            "root": str(DATA_ROOT), "breadcrumbs": breadcrumbs,
            "directories": nodes, "files": files, "sketches": sketch_files,
            "fileCount": len(files), "folderCount": folder_count,
            "totalSize": sum(file["size"] for file in files), "counts": counts,
            "warnings": warnings, "storage":"database" if DATABASE_ONLY else "legacy", "view": "print" if print_view else "files",
            "filesScope": files_scope,
            "upload": file_uploads.options(DATA_ROOT,relative) if files_scope=="folder" and file_uploads.available(DATA_ROOT,relative) else None,
            "newFileName": next_print_name(target) if print_view else "",
            "canCreateObjectFolder": status["folderKind"]=="client",
            "canGroupOrdersByYear": status["folderKind"]=="object",
            "canCreateOrderFolder": not print_view and (status["folderKind"] in {"object", "supplier_root", "work_root", "work_section", "moneys_section"} or (status["folderKind"]=="year" and order_folders.year_container(DATA_ROOT,relative))),
            "canCreateEventFolder": status["folderKind"] == "order",
            "canRenameFolder": folder_rename.available(relative_path(target)),
            "canDeleteEvent": event_trash.available(relative_path(target)),
            "hasEventTrash": work_orders.supplier_order(relative_path(target)) or event_trash.available(relative_path(target)),
            **status}


def save_status(relative, status, note, financial_status=None, todo_items=order_document.UNSET_TODOS,
                purchase_items=order_document.UNSET_TODOS):
    target = editable_status_folder(relative)
    if is_service_folder(relative_path(target)):
        raise ValueError("У служебной папки нет статуса заказа. Сохраните заметку.")
    order_store().require_order_folder(relative_path(target))
    if not isinstance(status, str) or status not in STATUS_LABELS or not isinstance(note, str):
        raise ValueError("Некорректный статус или заметка")
    if financial_status is not None and (not isinstance(financial_status, str) or financial_status not in FINANCIAL_STATUS_LABELS):
        raise ValueError("Некорректный финансовый статус")
    record = order_store().get(relative, include_unregistered=True)
    if record:
        if not record["registered"]:
            raise OrderConflict("Папка убрана из списка заказов. Обновите её и сохраните заметку.")
        raise OrderConflict("Заказ ведётся в базе. Откройте его заново и сохраните карточку целиком.")
    with STATUS_LOCK:
        write_status_document(target, status, note, financial_status, todo_items, purchase_items)


def save_note(relative, note):
    if folder_note_store().get(relative):
        raise FolderNoteConflict("Заметка папки теперь ведётся в базе. Обновите страницу, сохранив введённый текст")
    target = editable_status_folder(relative)
    relative = relative_path(target)
    if not isinstance(note, str) or len(note) > 100_000:
        raise ValueError("Укажите заметку")
    if is_service_folder(relative):
        write_status_document(target, None, note)
        return
    removed = order_store().get(relative, include_unregistered=True)
    if removed and removed["registered"]:
        raise OrderConflict("Заказ ведётся в базе. Откройте карточку заново.")
    if removed and removed["sync_pending"]:
        raise OrderConflict("Карточка ещё сохраняется в папку. Повторите сохранение заметки после выгрузки.")
    with STATUS_LOCK:
        status_document(target)
        record = order_document.load(target, STATUS_LABELS)
        if not removed and record.get("registered") is not False and folder_role(DATA_ROOT, relative)["canRegisterOrder"]:
            raise ValueError("У папки заказа сохраните карточку целиком")
        record["note"] = note
        if record.get("schema", 0) < order_document.FORMAT:
            order_document.archive_current(target)
        order_document.atomic_write(target / STATUS_DOCUMENT_NAME, order_document.render(record, STATUS_LABELS))


def image_preview(target):
    if target.suffix.lower() == ".svg":
        return target
    stat = target.stat()
    digest = hashlib.sha256(f"{target}:{stat.st_mtime_ns}:{stat.st_size}".encode()).hexdigest()
    cache = DATA_DIR / "previews"
    preview = cache / f"{digest}.jpg"
    with PREVIEW_LOCKS[int(digest[:8], 16) % len(PREVIEW_LOCKS)], PREVIEW_SLOTS:
        if not preview.exists():
            cache.mkdir(parents=True, exist_ok=True)
            temporary = cache / f"{digest}.tmp.jpg"
            try:
                subprocess.run(["/usr/bin/sips", "-s", "format", "jpeg", "-Z", "1100",
                                str(target), "--out", str(temporary)],
                               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
                temporary.replace(preview)
            except (OSError, subprocess.SubprocessError):
                temporary.unlink(missing_ok=True)
                if target.suffix.lower() in BROWSER_IMAGES:
                    return target
                raise ValueError("Не удалось создать просмотр. Откройте файл на Mac.")
    return preview


def pdf_renderer():
    with PDF_BUILD_LOCK:
        try:
            return native_renderers.build(APP_DIR / "pdf_preview.swift", DATA_DIR, "pdf-renderer", 60)
        except (OSError, subprocess.SubprocessError) as error:
            raise ValueError("Не удалось запустить просмотр PDF. Откройте файл на Mac.") from error


def pdf_key(target):
    stat = target.stat()
    return hashlib.sha256(f"{target}:{stat.st_mtime_ns}:{stat.st_size}".encode()).hexdigest()


def pdf_error(stderr, fallback):
    for line in stderr.decode("utf-8", errors="replace").splitlines():
        if line.startswith("ZIGZAG_PDF_ERROR: "):
            return line.removeprefix("ZIGZAG_PDF_ERROR: ").strip() or fallback
    return fallback


def pdf_info(target):
    if target.suffix.lower() != ".pdf":
        raise ValueError("Выберите PDF")
    key = pdf_key(target)
    if key not in PDF_INFO_CACHE:
        try:
            result = subprocess.run([str(pdf_renderer()), str(target), "info"],
                                    check=True, capture_output=True, timeout=20)
            PDF_INFO_CACHE[key] = json.loads(result.stdout)
        except subprocess.CalledProcessError as error:
            raise ValueError(pdf_error(error.stderr or b"", "Не удалось прочитать PDF. Открой его на Mac."))
        except (OSError, subprocess.TimeoutExpired):
            raise ValueError("Не удалось прочитать PDF. Откройте его на Mac.")
    return PDF_INFO_CACHE[key]


def pdf_page(target, page):
    if not 0 <= page < pdf_info(target)["pages"]:
        raise ValueError("Страница не найдена")
    key = pdf_key(target)
    cache = DATA_DIR / "previews"
    preview = cache / f"{key}-page-{page}.jpg"
    with PREVIEW_LOCKS[int(key[:8], 16) % len(PREVIEW_LOCKS)], PREVIEW_SLOTS:
        if not preview.exists():
            cache.mkdir(parents=True, exist_ok=True)
            try:
                subprocess.run([str(pdf_renderer()), str(target), str(page), str(preview)],
                               check=True, capture_output=True, timeout=30)
            except subprocess.CalledProcessError as error:
                preview.unlink(missing_ok=True)
                raise ValueError(pdf_error(error.stderr or b"", "Не удалось показать страницу PDF. Открой его на Mac."))
            except (OSError, subprocess.SubprocessError):
                preview.unlink(missing_ok=True)
                raise ValueError("Не удалось показать страницу PDF. Откройте его на Mac.")
    return preview


class ManagerHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def send_json(self, payload, status=200, head=False):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if not head:
            self.wfile.write(body)

    def send_invoice_pdf(self, body, name, head=False):
        self.send_response(200)
        self.send_header("Content-Type", "application/pdf")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Disposition", "inline; filename*=UTF-8''" + urllib.parse.quote(name))
        self.end_headers()
        if not head:
            self.wfile.write(body)

    def send_file(self, target, head=False, download=False, allow_range=False, private=False):
        if not target.is_file():
            raise FileNotFoundError("Файл не найден")
        size = target.stat().st_size
        start, end, partial = 0, size - 1, False
        requested_range = self.headers.get("Range") if allow_range else None
        if requested_range:
            match = re.fullmatch(r"bytes=(\d*)-(\d*)", requested_range)
            if not match or not any(match.groups()):
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.end_headers()
                return
            first, last = match.groups()
            if first:
                start = int(first)
                end = min(int(last), size - 1) if last else size - 1
            else:
                start = max(0, size - int(last))
            if start >= size or end < start:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.end_headers()
                return
            partial = True
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        # User HTML and other active documents are downloads, never app pages.
        if private and content_type in {"text/html", "application/xhtml+xml", "application/javascript", "text/javascript"}:
            download = True
        self.send_response(206 if partial else 200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(max(0, end - start + 1)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "private, max-age=300" if private else "no-cache")
        if private and content_type in {"image/svg+xml", "text/html", "application/xhtml+xml"}:
            self.send_header("Content-Security-Policy", "sandbox")
        disposition = "attachment" if download else "inline"
        self.send_header("Content-Disposition", f"{disposition}; filename*=UTF-8''{urllib.parse.quote(target.name)}")
        if allow_range:
            self.send_header("Accept-Ranges", "bytes")
        if partial:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        if head:
            return
        with target.open("rb") as stream:
            stream.seek(start)
            remaining = end - start + 1
            while remaining > 0:
                chunk = stream.read(min(256 * 1024, remaining))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remaining -= len(chunk)

    def handle_get(self, head=False):
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        relative = query.get("path", [""])[0]
        try:
            if parsed.path == "/api/health":
                self.send_json({"status": "ok", "release": RELEASE_ID, "root": str(DATA_ROOT)}, head=head)
            elif parsed.path == "/api/orders":
                self.send_json(listed_orders(), head=head)
            elif parsed.path == "/api/storage":
                self.send_json(metadata_store().status() if DATABASE_ONLY else {"database_only":False},head=head)
            elif parsed.path == "/api/invoices":
                self.send_json({"items": invoice_store().list(relative), "trash": invoice_store().list(relative, trashed=True)}, head=head)
            elif parsed.path in {"/api/invoice-pdf", "/api/invoice-preview"}:
                identity = query.get("id", [""])[0]
                if parsed.path == "/api/invoice-preview":
                    body, name = invoice_store().preview(relative, identity), "Предпросмотр счёта.pdf"
                else:
                    body, name = invoice_store().pdf(relative, identity)
                self.send_invoice_pdf(body, name, head=head)
            elif parsed.path in {"/api/client-activity", "/api/object-activity"}:
                activity = object_activity_store() if parsed.path == "/api/object-activity" else client_activity_store()
                record = activity.get(relative)
                if not record:
                    raise FileNotFoundError(f"Отметка {activity.entity} не найдена")
                self.send_json(record, head=head)
            elif parsed.path == "/api/mobile-status":
                self.send_json(MobileBridge(order_store()).status(), head=head)
            elif parsed.path == "/api/folder-note":
                record = folder_note_store().get(relative)
                if not record:
                    raise FileNotFoundError("Заметка папки не найдена в базе")
                self.send_json(record, head=head)
            elif parsed.path == "/api/event-relevance":
                self.send_json(folder_note_store().event_relevances(relative), head=head)
            elif parsed.path == "/api/sketch-relevance":
                self.send_json(folder_note_store().sketch_relevances(relative), head=head)
            elif parsed.path == "/api/sketch-preview":
                target = sketch_target(relative)
                preview = sketches.preview(target, DATA_DIR)
                self.send_file(preview, head=head, private=True)
            elif parsed.path == "/api/event-folders":
                self.send_json(event_folders.preview(DATA_ROOT, relative, folder_note_store()), head=head)
            elif parsed.path == "/api/folder-rename":
                self.send_json(folder_rename.preview(order_store(), relative), head=head)
            elif parsed.path == "/api/object-years":
                self.send_json(object_years.preview(order_store(),relative),head=head)
            elif parsed.path == "/api/order":
                record = order_store().get(relative)
                if not record:
                    raise FileNotFoundError("Заказ не найден в списке")
                self.send_json(record, head=head)
            elif parsed.path == "/api/order-todos":
                self.send_json(OrderTodos(order_store()).in_order(relative), head=head)
            elif parsed.path == "/api/work-order-links":
                self.send_json(order_store().work_links(relative), head=head)
            elif parsed.path == "/api/tree":
                self.send_json(read_tree(relative, query.get("q", [""])[0], query.get("show_inactive", [""])[0] == "1"), head=head)
            elif parsed.path == "/api/folder":
                self.send_json(read_folder(relative, query.get("show_inactive", [""])[0] == "1"), head=head)
            elif parsed.path == "/api/print-task":
                self.send_json(read_print_task(relative), head=head)
            elif parsed.path == "/api/file-comment":
                target = comment_file(relative)
                self.send_json({"path": relative, "comment_key": file_comments.binding(target),
                                **read_file_comment(target)}, head=head)
            elif parsed.path in {"/api/file", "/api/preview", "/api/text", "/api/pdf", "/api/pdf-page", "/api/spreadsheet"}:
                target = safe_path(relative)
                if not target.is_file():
                    raise FileNotFoundError("Файл не найден")
                if parsed.path == "/api/spreadsheet":
                    body = spreadsheet_preview.read_bytes(target)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/octet-stream")
                    self.send_header("Content-Length", str(len(body)))
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("X-Content-Type-Options", "nosniff")
                    self.end_headers()
                    if not head:
                        self.wfile.write(body)
                elif parsed.path == "/api/pdf":
                    self.send_json(pdf_info(target), head=head)
                elif parsed.path == "/api/pdf-page":
                    self.send_file(pdf_page(target, int(query.get("page", ["0"])[0])), head=head, private=True)
                elif parsed.path == "/api/text":
                    if target.suffix.lower() not in TEXT_EXTENSIONS:
                        raise ValueError("Текстовый просмотр недоступен")
                    with target.open("rb") as stream:
                        body = stream.read(128 * 1024 + 1)
                    self.send_json({"text": body[:128 * 1024].decode("utf-8", errors="replace"),
                                    "truncated": len(body) > 128 * 1024}, head=head)
                else:
                    if parsed.path == "/api/preview":
                        if preview_kind(target) != "image":
                            raise ValueError("Просмотр изображения недоступен")
                        target = image_preview(target)
                    self.send_file(target, head=head, download=query.get("download") == ["1"], allow_range=True, private=True)
            elif parsed.path.startswith("/api/"):
                self.send_json({"error": "Неизвестный запрос"}, 404, head=head)
            else:
                relative_static = urllib.parse.unquote(parsed.path).lstrip("/") or "index.html"
                target = (STATIC_DIR / relative_static).resolve()
                if STATIC_DIR not in target.parents:
                    raise FileNotFoundError("Страница не найдена")
                self.send_file(target, head=head)
        except (FileNotFoundError, NotADirectoryError) as error:
            self.send_json({"error": str(error)}, 404, head=head)
        except (ValueError, configparser.Error) as error:
            self.send_json({"error": str(error)}, 400, head=head)
        except PermissionError:
            self.send_json({"error": "Нет доступа к папке или файлу"}, 403, head=head)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except OSError as error:
            self.send_json({"error": f"Не удалось прочитать данные: {error}"}, 500, head=head)

    def do_GET(self):
        self.handle_get()

    def do_HEAD(self):
        self.handle_get(head=True)

    def receive_upload(self):
        self.close_connection = True
        try:
            if self.headers.get('X-Manager-Upload') != '1' or self.headers.get_content_type() != 'application/octet-stream':
                self.send_json({'error':'Загрузка доступна через кнопку «Добавить файлы»'},403)
                return
            origin = self.headers.get('Origin')
            if origin and urllib.parse.urlsplit(origin).netloc != self.headers.get('Host'):
                self.send_json({'error':'Загрузка с другой страницы запрещена'},403)
                return
            lengths = self.headers.get_all('Content-Length') or []
            if self.headers.get('Transfer-Encoding') or len(lengths)!=1 or not re.fullmatch(r'[0-9]+',lengths[0]):
                raise ValueError('Не указан размер файла')
            query = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query,keep_blank_values=True)
            if any(len(query.get(key,[]))!=1 for key in ('path','name','token')):
                raise ValueError('Не указана папка или имя файла')
            self.connection.settimeout(60)
            saved = file_uploads.receive(order_store(),query['path'][0],query['token'][0],query['name'][0],self.rfile,int(lengths[0]))
            self.send_json(saved,201)
        except file_uploads.UploadTooLarge as error:
            self.send_json({'error':str(error)},413)
        except file_uploads.UploadBusy as error:
            self.send_json({'error':str(error)},429)
        except (file_uploads.UploadConflict,EventRenamePending) as error:
            self.send_json({'error':str(error)},409)
        except FileNotFoundError as error:
            self.send_json({'error':str(error)},404)
        except ValueError as error:
            self.send_json({'error':str(error)},400)
        except (BrokenPipeError,ConnectionResetError):
            return
        except sqlite3.Error:
            self.send_json({'error':'База M4 сейчас занята или недоступна. Повтори загрузку позже'},500)
        except OSError as error:
            self.send_json({'error':'Не удалось сохранить файл на M4: '+str(error)},500)

    def do_POST(self):
        if urllib.parse.urlsplit(self.path).path == '/api/file-upload':
            self.receive_upload()
            return
        try:
            route = urllib.parse.urlparse(self.path).path
            if route == '/api/invoice-upload':
                origin = self.headers.get('Origin')
                if self.headers.get_content_type() != 'application/json' or (origin and urllib.parse.urlsplit(origin).netloc != self.headers.get('Host')):
                    raise ValueError('Прикрепляй PDF через кнопку «Прикрепить PDF» в заказе')
            length = int(self.headers.get("Content-Length", "0"))
            limit = invoices.EXTERNAL_REQUEST_LIMIT if route == '/api/invoice-upload' else (1024 * 1024 if route in {"/api/file-comment", "/api/order-save", "/api/status"} else 256 * 1024)
            if length < 0 or length > limit:
                raise ValueError("Слишком большой запрос")
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            if not isinstance(payload, dict):
                raise ValueError("Некорректный запрос")
            if route == "/api/invoice-create":
                self.send_json(invoice_store().create(payload), 201)
                return
            elif route == '/api/invoice-upload':
                self.send_json(invoice_store().upload(payload), 201)
                schedule_order_sync()
                return
            elif route == '/api/invoice-comment':
                self.send_json(invoice_store().save_comment(payload))
                return
            elif route == '/api/invoice-remove':
                self.send_json(invoice_store().remove(payload))
                schedule_order_sync()
                return
            elif route == '/api/invoice-restore':
                self.send_json(invoice_store().restore(payload))
                schedule_order_sync()
                return
            elif route == "/api/invoice-save":
                self.send_json(invoice_store().save(payload))
                return
            elif route == "/api/invoice-issue":
                record = invoice_store().issue(payload)
                self.send_json(record)
                schedule_order_sync()
                return
            elif route == "/api/order-folder-create":
                store = order_store()
                guard_database(store.database, payload.get("path", ""), include_children=True)
                try:
                    created = order_folders.create(DATA_ROOT, payload.get("path"), payload.get("date"), payload.get("title"), store=store)
                finally:
                    METADATA_REFRESH.set()
                self.send_json(created, 201)
                schedule_order_sync()
                schedule_todo_refresh()
                return
            elif route == "/api/object-folder-create":
                guard_database(order_store().database,payload.get('path',''),include_children=True)
                self.send_json(order_folders.create_object(DATA_ROOT,payload.get('path'),payload.get('title')),201)
                return
            elif route == "/api/object-years":
                with RUN_LOCK, file_comments.LOCK, PRINT_LOCK, STATUS_LOCK:
                    result = object_years.group(order_store(),payload)
                self.send_json(result)
                schedule_order_sync()
                schedule_todo_refresh()
                return
            elif route == "/api/event-folder-create":
                guard_database(order_store().database, payload.get("path", ""), include_children=True)
                self.send_json(event_folders.create(DATA_ROOT, payload, folder_note_store()), 201)
                return
            elif route == "/api/folder-rename":
                with RUN_LOCK, file_comments.LOCK, PRINT_LOCK, STATUS_LOCK:
                    result = folder_rename.rename(order_store(), payload)
                self.send_json(result)
                schedule_order_sync()
                schedule_todo_refresh()
                return
            elif route == "/api/event-folders-rename":
                with file_comments.LOCK:
                    self.send_json(event_folders.rename(folder_note_store(), payload))
                schedule_todo_refresh()
                return
            elif route == "/api/folder-note-save":
                record = folder_note_store().save(payload)
                self.send_json(record)
                schedule_order_sync()
                return
            elif route == "/api/event-relevance":
                record = folder_note_store().save_relevance(payload)
                self.send_json(event_relevance.info(record))
                schedule_order_sync()
                return
            elif route == "/api/sketch-relevance":
                record = folder_note_store().save_sketch_relevance(payload)
                self.send_json({"path": payload["path"], "key": payload["key"], "folder": record["path"], "status": sketches.group_info(record)})
                schedule_order_sync()
                return
            elif route == "/api/sketch-open":
                if not isinstance(payload.get("key"), str):
                    raise ValueError("Открой страницу эскиза заново")
                with file_comments.LOCK:
                    target = sketch_target(payload.get("path", ""), payload["key"])
                    sketches.open_corel(target)
                self.send_json({"ok": True})
                return
            elif route == "/api/order-add":
                relative = payload.get("path", "")
                target = editable_status_folder(relative)
                relative = relative_path(target)
                store = order_store()
                store.path(relative)
                store.require_order_folder(relative)
                order_creation.retry_one(store, relative)
                if not store.get(relative):
                    fallback = folder_status(target, directory_children(target))
                    store.import_folder(relative, fallback)
                self.send_json(store.get(relative), 201)
                schedule_order_sync()
                schedule_todo_refresh()
                return
            elif route == "/api/mobile-sync":
                bridge = MobileBridge(order_store())
                if "enabled" in payload:
                    bridge.configure(payload["enabled"])
                schedule_mobile_sync()
                self.send_json(bridge.status(), 202)
                return
            elif route == "/api/order-save":
                record = order_store().save(payload)
                self.send_json(record)
                schedule_order_sync()
                return
            elif route == "/api/order-favorite":
                record = order_store().save_favorite(payload)
                self.send_json(record)
                schedule_order_sync()
                return
            elif route == "/api/work-order-links":
                self.send_json(order_store().save_work_links(payload))
                schedule_order_sync()
                return
            elif route in {"/api/client-activity", "/api/client-activity-file", "/api/object-activity", "/api/object-activity-file"}:
                activity = object_activity_store() if route.startswith("/api/object-") else client_activity_store()
                record = activity.accept_file(payload) if route.endswith("-file") else activity.save(payload)
                self.send_json(record)
                schedule_order_sync()
                return
            elif route == "/api/order-remove":
                record = order_store().remove(payload)
                if DATABASE_ONLY:
                    record["folderNote"] = folder_note_store().get(record["path"])
                self.send_json(record)
                schedule_order_sync()
                return
            elif route == "/api/orders-discover":
                self.send_json(discover_orders(), 202)
                return
            elif route == "/api/orders-sync":
                schedule_order_sync()
                if DATABASE_ONLY:
                    METADATA_REFRESH.set()
                self.send_json({"ok": True})
                return
            elif route == "/api/clients-refresh":
                client_activity_store().refresh()
                object_activity_store().refresh()
                self.send_json({"ok": True})
                return
            elif route == "/api/todos-refresh":
                relative = payload.get("path")
                if relative:
                    relative = order_store().path(relative)
                schedule_todo_refresh(relative) if relative else schedule_todo_refresh()
                self.send_json({"ok": True}, 202)
                return
            elif route == "/api/print-create":
                self.send_json(create_print_task(payload.get("path", ""), payload.get("link", ""), payload.get("description", ""), payload.get("title", "")), 201)
                return
            elif route == "/api/print-save":
                self.send_json(save_print_task(payload.get("path", ""), payload.get("link", ""), payload.get("description", ""), payload.get("revision"), payload.get("title")))
                return
            elif route == "/api/print-publish":
                with PRINT_LOCK:
                    task = read_print_task(payload.get("path",""))
                    if payload.get("revision")!=task["revision"]:
                        raise PrintConflict("Задание изменилось. Открой актуальную версию перед выпуском")
                    filename = "Задание - "+datetime.now(ZoneInfo("Europe/Moscow")).strftime("%Y-%m-%d")+" - "+hashlib.sha256((task["path"]+task["revision"]).encode()).hexdigest()[:10]+".txt"
                    result = metadata_store().publish(task["path"],task["revision"],DATA_ROOT/Path(task["path"]).parent,filename,compose_print_text(task["link"],task["description"],task["title"]).encode())
                self.send_json(result,202)
                schedule_order_sync()
                return
            elif route == "/api/file-comment":
                relative = payload.get("path", "")
                with file_comments.LOCK:
                    target = comment_file(relative)
                    key = file_comments.binding(target)
                    if not payload.get("comment_key"):
                        raise FileCommentConflict("Страница устарела. Скопируйте несохранённый комментарий и обновите страницу для проверки файла и папки")
                    if payload.get("comment_key") != key:
                        raise FileCommentConflict("Комментарий относится к другому файлу или папке. Ваш текст остался в поле; откройте нужный файл заново")
                    record = metadata_store().save_comment(target,payload.get("comment"),payload.get("revision")) if DATABASE_ONLY else file_comments.save(target, payload.get("comment"), payload.get("revision"))
                self.send_json({"path": relative, "comment_key": key, **record})
                return
            elif route == "/api/image-report":
                guard_database(order_store().database, payload.get("path", ""), include_children=True)
                self.send_json(create_image_report(payload.get("path", ""), payload.get("files")), 201)
                return
            elif route == "/api/files-trash-preview":
                self.send_json(file_trash.preview(DATA_ROOT, payload.get("path", ""), payload.get("files")))
                return
            elif route == "/api/event-trash-preview":
                self.send_json(event_trash.preview(order_store(), payload.get('path')))
                return
            elif route == "/api/event-trash":
                with RUN_LOCK, file_comments.LOCK, PRINT_LOCK, STATUS_LOCK:
                    result = event_trash.remove(order_store(), payload)
                self.send_json(result)
                schedule_todo_refresh()
                return
            elif route == "/api/event-trash-restore":
                with RUN_LOCK, file_comments.LOCK, PRINT_LOCK, STATUS_LOCK:
                    result = event_trash.restore(order_store(), payload.get('session'))
                self.send_json(result)
                schedule_order_sync()
                schedule_todo_refresh()
                return
            elif route == "/api/files-trash":
                with file_comments.LOCK:
                    guard_database(order_store().database, payload.get("path", ""), include_children=True)
                    result = file_trash.remove(DATA_ROOT, payload.get("path", ""), payload.get("files"), payload.get("confirmed"),database=order_store().database if DATABASE_ONLY else None)
                self.send_json(result)
                return
            elif route in {"/api/files-trash-list", "/api/event-trash-list"}:
                events = event_trash.list_sessions(order_store())
                sessions, errors = [], []
                if route == "/api/files-trash-list":
                    try:
                        sessions = file_trash.list_sessions(DATA_ROOT, errors=errors,
                            reader=lambda path: icloud_access.read_bytes(path, max_bytes=20 * 1024 * 1024))
                    except (OSError, ValueError, sqlite3.Error):
                        errors.append({"session": None})
                warning = "Часть корзины файлов сейчас недоступна. Список файлов может быть неполным; закрой и открой корзину ещё раз. События показаны из базы." if errors else ""
                self.send_json({"sessions": sessions, "events": events, "warning": warning})
                return
            elif route == "/api/files-trash-restore":
                with file_comments.LOCK:
                    guard_database(order_store().database, "", include_children=True)
                    result = file_trash.restore(DATA_ROOT, payload.get("session"))
                self.send_json(result)
                return
            elif route == "/api/status":
                if DATABASE_ONLY:
                    raise ValueError("Сохрани карточку через редактор базы с проверкой версии")
                save_status(payload.get("path", ""), payload.get("status"), payload.get("note", ""), payload.get("financial_status"),
                            payload.get("todo_items", order_document.UNSET_TODOS), payload.get("purchase_items", order_document.UNSET_TODOS))
            elif route == "/api/note":
                if DATABASE_ONLY:
                    raise ValueError("Сохрани заметку через редактор базы с проверкой версии")
                save_note(payload.get("path", ""), payload.get("note", ""))
            elif route == "/api/open":
                target = safe_path(payload.get("path", ""))
                if not target.exists():
                    raise FileNotFoundError("Папка или файл не найдены")
                subprocess.Popen(["open", "-R", str(target)] if payload.get("reveal") else ["open", str(target)])
            else:
                self.send_json({"error": "Неизвестный запрос"}, 404)
                return
            self.send_json({"ok": True})
        except FileNotFoundError as error:
            self.send_json({"error": str(error)}, 404)
        except (invoices.InvoiceConflict, PrintConflict, OrderConflict, ClientActivityConflict, FileCommentConflict, file_trash.TrashConflict, order_folders.OrderFolderConflict, object_years.YearGroupConflict, folder_rename.FolderRenameConflict, FolderNoteConflict, event_folders.EventFolderConflict, EventRenamePending) as error:
            self.send_json({"error": str(error)}, 409)
        except (ValueError, UnicodeDecodeError) as error:
            self.send_json({"error": str(error)}, 400)
        except OSError as error:
            self.send_json({"error": f"Не удалось выполнить действие: {error}"}, 500)


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else SERVER_PORT
    if DATABASE_ONLY:
        with metadata_store().connect():
            pass
        metadata_store().backup("before-migration")
    discarded = order_store().discard_service_orders() if not DATABASE_ONLY else 0
    if discarded:
        print(f"Тестовые регистрации служебных папок убраны: {discarded}", flush=True)
    migration = migrate_statuses() if not DATABASE_ONLY else None
    if migration:
        print(f"Статусы перенесены в папки: {migration['migrated']}. Архив: {migration['archive']}", flush=True)
        if migration["unresolved"]:
            print("Папки не сопоставлены; записи сохранены в архиве: " + ", ".join(migration["unresolved"]), flush=True)
    threading.Thread(target=order_sync_worker, daemon=True).start()
    threading.Thread(target=mobile_sync_worker, daemon=True).start()
    threading.Thread(target=order_todo_worker, daemon=True).start()
    threading.Thread(target=client_activity_worker, daemon=True).start()
    threading.Thread(target=metadata_worker, daemon=True).start()
    server = ThreadingHTTPServer((SERVER_HOST, port), ManagerHandler)
    print(f"Менеджер заказов: http://127.0.0.1:{port}", flush=True)
    print(f"Адрес сервера: {SERVER_HOST}:{port}", flush=True)
    print(f"Папка данных: {DATA_ROOT}", flush=True)
    print(f"Настройки: {CONFIG_FILE}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
