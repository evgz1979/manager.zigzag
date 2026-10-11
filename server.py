#!/usr/bin/env python3
import configparser
import hashlib
import json
import mimetypes
import os
import re
import subprocess
import sys
import threading
import unicodedata
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
CONFIG_FILE = APP_DIR / "manager.ini"
STATIC_DIR = APP_DIR / "static"
DATA_DIR = APP_DIR / "data"
STATUSES_FILE = DATA_DIR / "statuses.json"
STATUS_LOCK = threading.Lock()
PREVIEW_LOCKS = [threading.Lock() for _ in range(32)]
PREVIEW_SLOTS = threading.BoundedSemaphore(4)
PDF_BUILD_LOCK = threading.Lock()
PDF_INFO_CACHE = {}


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
    "new": "Новый", "measure": "Замеры", "process": "В работе",
    "workshop": "В цех", "install": "Монтаж", "done": "Готово",
}
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
    "docs": {".doc", ".docx", ".xls", ".xlsx", ".txt", ".rtf", ".md", ".csv"},
}
TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".tsv", ".json", ".ini", ".log", ".yaml", ".yml", ".xml", ".py", ".js", ".css"}
BROWSER_IMAGES = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif", ".bmp", ".svg"}


def normalized(value):
    return unicodedata.normalize("NFC", value).casefold()


def sort_key(path):
    return [(1, int(part)) if part.isdigit() else (0, normalized(part)) for part in re.split(r"(\d+)", path.name)]


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


def directory_children(path):
    return sorted((item for item in path.iterdir() if visible(item) and item.is_dir()), key=sort_key)


def folder_node(path):
    try:
        has_children = any(visible(item) and item.is_dir() for item in path.iterdir())
    except OSError:
        has_children = False
    return {"name": path.name, "path": relative_path(path), "hasChildren": has_children}


def read_tree(relative="", query=""):
    target = safe_path(relative)
    if not target.is_dir():
        raise FileNotFoundError("Папка данных не найдена. Проверьте manager.ini")
    children = directory_children(target)
    auxiliary = []
    if target == DATA_ROOT:
        auxiliary = [folder_node(item) for item in children if item.name.startswith("#")]
        children = [item for item in children if not item.name.startswith("#")]
    if query:
        needle = normalized(query.strip())

        def matching_node(path):
            node = folder_node(path)
            try:
                descendants = [result for child in directory_children(path) if (result := matching_node(child))]
            except OSError:
                descendants = []
            if needle in normalized(relative_path(path)) or descendants:
                node["children"] = descendants
                return node
            return None

        nodes = [node for item in children if (node := matching_node(item))]
    else:
        nodes = [folder_node(item) for item in children]
    return {"root": str(DATA_ROOT), "rootName": DATA_ROOT.name, "path": relative,
            "children": nodes, "auxiliary": auxiliary}


def file_group(path):
    return next((group for group, extensions in EXT_GROUPS.items() if path.suffix.lower() in extensions), "other")


def preview_kind(path):
    ext = path.suffix.lower()
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


def load_statuses():
    if not STATUSES_FILE.exists():
        return {}
    records = json.loads(STATUSES_FILE.read_text(encoding="utf-8"))
    if not isinstance(records, dict):
        raise ValueError("Некорректный файл статусов")
    return records


def folder_status(path, directories):
    key = relative_path(path)
    records = load_statuses()
    record = records.get(key)
    if record is None:
        # Read old year-prefixed records without changing the saved file.
        matches = [value for old_key, value in records.items()
                   if re.match(r"^\d{4}/", old_key) and old_key[5:] == key]
        record = matches[0] if len(matches) == 1 else None
    record = record or {}
    haystack = normalized(" ".join([path.name] + [item.name for item in directories]))
    guessed = next((status for status, words in STATUS_KEYWORDS if any(word in haystack for word in words)), "new")
    return {"status": record.get("status", guessed), "note": record.get("note", ""),
            "statusSource": "manual" if record.get("status") else "auto"}


def read_folder(relative=""):
    target = safe_path(relative)
    if not target.is_dir():
        raise FileNotFoundError("Папка не найдена")
    directories = directory_children(target)
    files, warnings = [], []
    folder_count = 0

    def walk_error(error):
        warnings.append(f"Не удалось прочитать папку: {error.filename}")

    for current, dirs, names in os.walk(target, onerror=walk_error, followlinks=False):
        current_path = Path(current)
        dirs[:] = [name for name in dirs if visible(current_path / name)]
        folder_count += len(dirs)
        if target == DATA_ROOT:
            dirs[:] = []  # List clients at home without scanning all their orders.
        for name in names:
            file = current_path / name
            if not visible(file) or not file.is_file():
                continue
            try:
                stat = file.stat()
            except OSError:
                warnings.append(f"Не удалось прочитать файл: {name}")
                continue
            files.append({"name": name, "path": relative_path(file),
                          "folder": current_path.relative_to(target).as_posix() if current_path != target else "",
                          "size": stat.st_size, "modified": stat.st_mtime,
                          "type": file_group(file), "preview": preview_kind(file),
                          "extension": file.suffix.lstrip(".").upper() or "ФАЙЛ"})
    files.sort(key=lambda file: (normalized(file["folder"]), sort_key(Path(file["name"]))))
    counts = {group: sum(file["type"] == group for file in files) for group in [*EXT_GROUPS, "other"]}
    parts = Path(relative).parts
    breadcrumbs = [{"name": DATA_ROOT.name, "path": ""}]
    breadcrumbs.extend({"name": part, "path": Path(*parts[:index + 1]).as_posix()} for index, part in enumerate(parts))
    return {"name": target.name, "path": relative_path(target), "client": parts[0] if parts else "",
            "root": str(DATA_ROOT), "breadcrumbs": breadcrumbs,
            "directories": [folder_node(item) for item in directories], "files": files,
            "fileCount": len(files), "folderCount": folder_count,
            "totalSize": sum(file["size"] for file in files), "counts": counts,
            "warnings": warnings, **folder_status(target, directories)}


def save_status(relative, status, note):
    target = safe_path(relative)
    if not relative or not target.is_dir():
        raise ValueError("Выберите папку заказа")
    if not isinstance(status, str) or status not in STATUS_LABELS or not isinstance(note, str):
        raise ValueError("Некорректный статус или заметка")
    with STATUS_LOCK:
        records = load_statuses()
        records[relative_path(target)] = {"status": status, "note": note}
        DATA_DIR.mkdir(exist_ok=True)
        temporary = STATUSES_FILE.with_suffix(".tmp")
        temporary.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(STATUSES_FILE)


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
    source = APP_DIR / "pdf_preview.swift"
    binary = DATA_DIR / "pdf-renderer"
    with PDF_BUILD_LOCK:
        if not binary.exists() or binary.stat().st_mtime < source.stat().st_mtime:
            DATA_DIR.mkdir(exist_ok=True)
            temporary = binary.with_suffix(".tmp")
            try:
                subprocess.run(["/usr/bin/swiftc", "-O", "-module-cache-path", str(DATA_DIR / "swift-cache"),
                                str(source), "-o", str(temporary)], check=True, capture_output=True, timeout=60)
                temporary.replace(binary)
            except (OSError, subprocess.SubprocessError):
                temporary.unlink(missing_ok=True)
                raise ValueError("Не удалось запустить просмотр PDF. Откройте файл на Mac.")
    return binary


def pdf_key(target):
    stat = target.stat()
    return hashlib.sha256(f"{target}:{stat.st_mtime_ns}:{stat.st_size}".encode()).hexdigest()


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
            raise ValueError(error.stderr.decode("utf-8", errors="replace").strip() or "Не удалось прочитать PDF")
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
            if parsed.path == "/api/tree":
                self.send_json(read_tree(relative, query.get("q", [""])[0]), head=head)
            elif parsed.path == "/api/folder":
                self.send_json(read_folder(relative), head=head)
            elif parsed.path in {"/api/file", "/api/preview", "/api/text", "/api/pdf", "/api/pdf-page"}:
                target = safe_path(relative)
                if not target.is_file():
                    raise FileNotFoundError("Файл не найден")
                if parsed.path == "/api/pdf":
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

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 0 or length > 256 * 1024:
                raise ValueError("Слишком большой запрос")
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            if not isinstance(payload, dict):
                raise ValueError("Некорректный запрос")
            route = urllib.parse.urlparse(self.path).path
            if route == "/api/status":
                save_status(payload.get("path", ""), payload.get("status"), payload.get("note", ""))
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
        except (ValueError, UnicodeDecodeError) as error:
            self.send_json({"error": str(error)}, 400)
        except OSError as error:
            self.send_json({"error": f"Не удалось выполнить действие: {error}"}, 500)


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else SERVER_PORT
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
