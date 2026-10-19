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


def _plain_read(path):
    with path.open("rb") as stream:
        return stream.read(MAX_BYTES + 1)


def _coordinated_read(path):
    result = subprocess.run([str(renderer()), str(path), str(MAX_BYTES)],
                            capture_output=True, check=True, timeout=READ_TIMEOUT)
    return result.stdout


def read_bytes(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Вместо {path.name} должен быть обычный файл")
    try:
        raw = _plain_read(path)
    except OSError as error:
        if error.errno != errno.EDEADLK or sys.platform != "darwin":
            raise
        try:
            # Отдельный процесс согласует доступ с iCloud; зависание ограничено таймаутом.
            raw = _coordinated_read(path)
        except (OSError, ValueError, subprocess.SubprocessError) as recovery_error:
            raise CloudReadPending(path) from recovery_error
    if len(raw) > MAX_BYTES:
        raise ValueError(f"Файл {path.name} больше 1 МБ")
    return raw


def sync_error(error):
    if isinstance(error, CloudReadPending):
        return str(error)
    if isinstance(error, OSError) and error.errno == errno.EDEADLK:
        return "iCloud временно заблокировал доступ к файлу. Данные в базе, выгрузка остаётся в очереди; повторим автоматически"
    return str(error)
