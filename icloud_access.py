"""Ограниченное чтение карточек с восстановлением доступа к файлам iCloud."""
import errno
import subprocess
import sys
import threading
from pathlib import Path

import native_renderers

MAX_BYTES = 1024 * 1024
READ_TIMEOUT = 8
BUILD_LOCK = threading.Lock()


class CloudReadPending(OSError):
    def __init__(self, path):
        self.path = Path(path)
        super().__init__(errno.EDEADLK, "iCloud пока не предоставил файл", str(path))

    def __str__(self):
        return f"iCloud пока не предоставил файл «{self.path.name}». Данные в базе, выгрузка остаётся в очереди; повторим автоматически"


def renderer():
    app = Path(__file__).resolve().parent
    with BUILD_LOCK:
        return native_renderers.build(app / "icloud_read.swift", app / "data", "icloud-read", 60)


def _plain_read(path, max_bytes=MAX_BYTES):
    with path.open("rb") as stream:
        return stream.read(max_bytes + 1)


def _coordinated_read(path, max_bytes=MAX_BYTES):
    result = subprocess.run([str(renderer()), str(path), str(max_bytes)],
                            capture_output=True, check=True, timeout=READ_TIMEOUT)
    return result.stdout


def read_bytes(path, *, max_bytes=MAX_BYTES):
    path = Path(path)
    if type(max_bytes) is not int or not 0 < max_bytes <= 20 * 1024 * 1024:
        raise ValueError("Предел чтения должен быть от 1 байта до 20 МБ")
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Вместо {path.name} должен быть обычный файл")
    arguments = (path,) if max_bytes == MAX_BYTES else (path, max_bytes)
    try:
        raw = _plain_read(*arguments)
    except OSError as error:
        if error.errno != errno.EDEADLK or sys.platform != "darwin":
            raise
        try:
            # Отдельный процесс согласует доступ с iCloud; зависание ограничено таймаутом.
            raw = _coordinated_read(*arguments)
        except (OSError, ValueError, subprocess.SubprocessError) as recovery_error:
            raise CloudReadPending(path) from recovery_error
    if len(raw) > max_bytes:
        raise ValueError(f"Файл {path.name} больше {max_bytes} байт")
    return raw


def sync_error(error):
    if isinstance(error, CloudReadPending):
        return str(error)
    if isinstance(error, OSError) and error.errno == errno.EDEADLK:
        return "iCloud временно заблокировал доступ к файлу. Данные в базе, выгрузка остаётся в очереди; повторим автоматически"
    return str(error)
