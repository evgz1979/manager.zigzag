"""Image/comment PDFs generated with macOS, published without overwriting files."""
import json
import os
import shutil
import subprocess
import tempfile
import threading
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from folder_layout import rename_exclusive

BUILD_LOCK = threading.Lock()
SLOTS = threading.BoundedSemaphore(2)
MAX_IMAGES = 200


def renderer(app_dir, data_dir):
    source = Path(app_dir) / "image_report.swift"
    binary = Path(data_dir) / "image-report"
    with BUILD_LOCK:
        if not binary.exists() or binary.stat().st_mtime < source.stat().st_mtime:
            binary.parent.mkdir(parents=True, exist_ok=True)
            temporary = binary.with_suffix(".tmp")
            try:
                subprocess.run(["/usr/bin/swiftc", "-O", "-module-cache-path", str(binary.parent / "swift-cache"),
                                str(source), "-o", str(temporary)], check=True, capture_output=True, timeout=90)
                temporary.replace(binary)
            except (OSError, subprocess.SubprocessError) as error:
                temporary.unlink(missing_ok=True)
                raise ValueError("Не удалось запустить формирование PDF") from error
    return binary


def create(folder, items, app_dir, data_dir):
    """Items must already have validated absolute image paths and current comments."""
    cache = Path(data_dir) / "reports"
    cache.mkdir(parents=True, exist_ok=True)
    with SLOTS, tempfile.TemporaryDirectory(prefix=".report-", dir=cache) as work:
        work = Path(work)
        manifest, output = work / ".images.json", work / ".report.pdf"
        manifest.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
        try:
            result = subprocess.run([str(renderer(app_dir, data_dir)), str(manifest), str(output)],
                                    check=True, capture_output=True, timeout=180)
            pages = json.loads(result.stdout)["pages"]
            with output.open("rb") as stream:
                valid_pdf = stream.read(5) == b"%PDF-"
            if not isinstance(pages, int) or pages < len(items) or not valid_pdf:
                raise ValueError("Не удалось проверить созданный PDF")
        except subprocess.CalledProcessError as error:
            message = error.stderr.decode("utf-8", errors="replace").strip()
            raise ValueError(message or "Не удалось сформировать PDF") from error
        except subprocess.TimeoutExpired as error:
            raise ValueError("Формирование PDF заняло слишком много времени. Попробуйте выбрать меньше изображений.") from error
        stamp = datetime.now(ZoneInfo("Europe/Moscow")).strftime("%Y-%m-%d")
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(prefix=".report-", suffix=".tmp", dir=folder, delete=False) as stream:
                temporary = Path(stream.name)
                with output.open("rb") as source:
                    shutil.copyfileobj(source, stream)
                stream.flush()
                os.fsync(stream.fileno())
            index = 1
            while True:
                target = Path(folder) / (f"report - {stamp}" + (f" ({index})" if index > 1 else "") + ".pdf")
                try:
                    rename_exclusive(temporary, target)
                    break
                except FileExistsError:
                    index += 1
            return target, pages
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
