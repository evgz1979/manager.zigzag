#!/usr/bin/env python3
import json
import mimetypes
import os
import re
import subprocess
import sys
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


APP_DIR = Path(__file__).resolve().parent
DATA_ROOT = Path(
    os.environ.get(
        "ZIGZAG_DATA_ROOT",
        Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/Зигзаг",
    )
).expanduser().resolve()
STATIC_DIR = APP_DIR / "static"
DATA_DIR = APP_DIR / "data"
STATUSES_FILE = DATA_DIR / "statuses.json"
SERVER_HOST = os.environ.get("MANAGER_HOST", "0.0.0.0")

SKIP_DIRS = {
    ".git",
    ".agents",
    ".codex",
    "project-manager",
    "node_modules",
    "__pycache__",
    ".DS_Store",
}

STATUS_KEYWORDS = [
    ("done", ("готово", "итоги", "ок", "заверш")),
    ("install", ("монтаж", "установка")),
    ("workshop", ("в цех", "цех", "покрас", "laser", "glass", "freza", "cutter")),
    ("measure", ("замер", "уточн", "список")),
    ("process", ("process", "делаем", "почти", "temp")),
]

EXT_GROUPS = {
    "images": {".jpg", ".jpeg", ".png", ".heic", ".webp", ".tif", ".tiff"},
    "video": {".mov", ".mp4", ".avi", ".m4v"},
    "pdf": {".pdf"},
    "design": {".cdr", ".ai", ".eps", ".svg", ".psd", ".dxf"},
    "docs": {".doc", ".docx", ".xls", ".xlsx", ".txt", ".rtf"},
}


def load_statuses():
    if not STATUSES_FILE.exists():
        return {}
    try:
        return json.loads(STATUSES_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_statuses(statuses):
    DATA_DIR.mkdir(exist_ok=True)
    STATUSES_FILE.write_text(
        json.dumps(statuses, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def is_hidden_or_skipped(path):
    return path.name in SKIP_DIRS or path.name.startswith(".")


def available_years():
    if not DATA_ROOT.exists():
        return []
    return sorted(
        [item.name for item in DATA_ROOT.iterdir() if item.is_dir() and re.fullmatch(r"\d{4}", item.name)],
        reverse=True,
    )


def resolve_year(requested_year=None):
    years = available_years()
    if not years:
        raise ValueError("В папке данных нет каталогов по годам")
    if requested_year in years:
        return requested_year, years
    current_year = str(time.localtime().tm_year)
    return (current_year if current_year in years else years[0]), years


def safe_path(year, relative_path):
    selected_year, _ = resolve_year(year)
    year_root = (DATA_ROOT / selected_year).resolve()
    decoded = urllib.parse.unquote(relative_path).strip("/")
    target = (year_root / decoded).resolve()
    if target == year_root or year_root in target.parents:
        return target
    raise ValueError("Path is outside selected year")


def file_group(path):
    ext = path.suffix.lower()
    for group, extensions in EXT_GROUPS.items():
        if ext in extensions:
            return group
    return "other"


def guess_status(project_path, child_dirs):
    haystack = " ".join([project_path.name] + [item.name for item in child_dirs]).lower()
    for status, words in STATUS_KEYWORDS:
        if any(word in haystack for word in words):
            return status
    return "new"


def newest_mtime(path):
    newest = path.stat().st_mtime
    for current, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        current_path = Path(current)
        for name in files:
            if name.startswith("."):
                continue
            try:
                newest = max(newest, (current_path / name).stat().st_mtime)
            except OSError:
                continue
    return newest


def scan_project(year, year_root, client_path, project_path, statuses):
    child_dirs = []
    file_counts = {key: 0 for key in [*EXT_GROUPS.keys(), "other"]}
    total_files = 0
    latest_files = []

    for current, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        current_path = Path(current)
        if current_path == project_path:
            child_dirs = [(current_path / d) for d in dirs]

        for file_name in files:
            if file_name.startswith("."):
                continue
            file_path = current_path / file_name
            try:
                stat = file_path.stat()
            except OSError:
                continue
            total_files += 1
            file_counts[file_group(file_path)] += 1
            latest_files.append(
                {
                    "name": file_name,
                    "path": str(file_path.relative_to(year_root)),
                    "modified": stat.st_mtime,
                    "size": stat.st_size,
                    "type": file_group(file_path),
                }
            )

    latest_files.sort(key=lambda item: item["modified"], reverse=True)
    rel_path = str(project_path.relative_to(year_root))
    status_key = f"{year}/{rel_path}"
    guessed_status = guess_status(project_path, child_dirs)
    status_record = statuses.get(status_key, statuses.get(rel_path, {}))
    modified = newest_mtime(project_path)

    return {
        "id": status_key,
        "client": client_path.name,
        "name": project_path.name,
        "path": rel_path,
        "status": status_record.get("status", guessed_status),
        "statusSource": "manual" if "status" in status_record else "auto",
        "note": status_record.get("note", ""),
        "modified": modified,
        "modifiedText": time.strftime("%d.%m.%Y %H:%M", time.localtime(modified)),
        "stages": [item.name for item in child_dirs[:20]],
        "stageCount": len(child_dirs),
        "fileCount": total_files,
        "fileCounts": file_counts,
        "latestFiles": latest_files[:8],
    }


def scan_workspace(requested_year=None):
    year, years = resolve_year(requested_year)
    year_root = DATA_ROOT / year
    statuses = load_statuses()
    clients = []
    projects = []

    for client_path in sorted(year_root.iterdir(), key=lambda path: path.name.lower()):
        if not client_path.is_dir() or is_hidden_or_skipped(client_path):
            continue
        project_dirs = [
            item
            for item in sorted(client_path.iterdir(), key=lambda path: path.name.lower())
            if item.is_dir() and not is_hidden_or_skipped(item)
        ]
        client_projects = []
        for project_path in project_dirs:
            project = scan_project(year, year_root, client_path, project_path, statuses)
            projects.append(project)
            client_projects.append(project["id"])
        clients.append(
            {
                "name": client_path.name,
                "path": str(client_path.relative_to(year_root)),
                "projectCount": len(project_dirs),
                "projects": client_projects,
            }
        )

    projects.sort(key=lambda item: item["modified"], reverse=True)
    return {
        "root": str(DATA_ROOT),
        "yearRoot": str(year_root),
        "year": year,
        "years": years,
        "scannedAt": time.strftime("%d.%m.%Y %H:%M"),
        "clients": clients,
        "projects": projects,
    }


class ManagerHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_static(self, request_path):
        relative = request_path.lstrip("/") or "index.html"
        if relative == "":
            relative = "index.html"
        target = (STATIC_DIR / relative).resolve()
        if not str(target).startswith(str(STATIC_DIR.resolve())) or not target.exists():
            self.send_error(404)
            return
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        body = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/projects":
            query = urllib.parse.parse_qs(parsed.query)
            try:
                self.send_json(scan_workspace(query.get("year", [None])[0]))
            except ValueError as error:
                self.send_json({"error": str(error)}, 404)
            return
        self.send_static(parsed.path)

    def do_HEAD(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/projects":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            return

        relative = parsed.path.lstrip("/") or "index.html"
        target = (STATIC_DIR / relative).resolve()
        if not str(target).startswith(str(STATIC_DIR.resolve())) or not target.exists():
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(target.name)[0] or "application/octet-stream")
        self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        payload = json.loads(body or "{}")

        if parsed.path == "/api/status":
            project_id = payload.get("id")
            status = payload.get("status")
            note = payload.get("note", "")
            if not project_id or not status:
                self.send_json({"error": "Missing project id or status"}, 400)
                return
            statuses = load_statuses()
            statuses[project_id] = {"status": status, "note": note}
            save_statuses(statuses)
            self.send_json({"ok": True})
            return

        if parsed.path == "/api/open":
            try:
                target = safe_path(payload.get("year"), payload.get("path", ""))
            except ValueError as error:
                self.send_json({"error": str(error)}, 400)
                return
            if not target.exists():
                self.send_json({"error": "Path does not exist"}, 404)
                return
            subprocess.Popen(["open", str(target)])
            self.send_json({"ok": True})
            return

        self.send_json({"error": "Unknown endpoint"}, 404)


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    server = ThreadingHTTPServer((SERVER_HOST, port), ManagerHandler)
    print(f"Project manager: http://127.0.0.1:{port}")
    print(f"Network binding: {SERVER_HOST}:{port}")
    print(f"Data root: {DATA_ROOT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
