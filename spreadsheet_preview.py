"""Чтение оригиналов Excel для браузерного просмотра без внешних программ."""
import subprocess
import sys
import threading
from pathlib import Path

import icloud_access

EXTENSIONS = {".xls", ".xlsx", ".xlsm", ".xlsb"}
MAX_BYTES = 20 * 1024 * 1024
READ_SLOTS = threading.BoundedSemaphore(2)


def read_bytes(target):
    target = Path(target)
    if target.suffix.lower() not in EXTENSIONS:
        raise ValueError("Выбери таблицу Excel")
    if target.is_symlink() or not target.is_file():
        raise ValueError("Нужен обычный файл Excel")
    if target.stat().st_size > MAX_BYTES:
        raise ValueError("Встроенный просмотр доступен для таблиц до 20 МБ. Скачай файл целиком.")
    if not READ_SLOTS.acquire(timeout=1):
        raise ValueError("Другие таблицы ещё загружаются. Попробуй открыть файл ещё раз.")
    try:
        if sys.platform == "darwin":
            try:
                result = subprocess.run([str(icloud_access.renderer()), str(target), str(MAX_BYTES)],
                                        capture_output=True, check=True, timeout=25)
                raw = result.stdout
            except (OSError, subprocess.SubprocessError) as error:
                raise ValueError("Не удалось прочитать таблицу из iCloud. Попробуй открыть её ещё раз.") from error
        else:
            with target.open("rb") as stream:
                raw = stream.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("Встроенный просмотр доступен для таблиц до 20 МБ. Скачай файл целиком.")
        return raw
    finally:
        READ_SLOTS.release()
