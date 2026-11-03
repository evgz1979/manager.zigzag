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


# Обозначает незавершённость операции в этом модуле.
# Вызывающий обработчик использует тип исключения для отказа без подмены данных.
class CloudReadPending(OSError):
    # Сохраняет зависимости и начальные параметры экземпляра.
    # Состояние и зависимости сохраняются в полях self для последующих операций.
    def __init__(self, path):
        self.path = Path(path)
        super().__init__(errno.EDEADLK, "iCloud пока не предоставил файл", str(path))

    # Возвращает текст ошибки, пригодный для показа пользователю.
    # Возвращает `f'iCloud пока не предоставил файл «{self.path.name}». Данные в базе, выгрузка остаётся в очереди; повторим автоматически'`.
    def __str__(self):
        return f"iCloud пока не предоставил файл «{self.path.name}». Данные в базе, выгрузка остаётся в очереди; повторим автоматически"


# Получает собранный Swift-помощник для текущего исходника.
# Возвращает `native_renderers.build(app / 'icloud_read.swift', app / 'data', 'icloud-read', 60)`.
def renderer():
    app = Path(__file__).resolve().parent
    with BUILD_LOCK:
        return native_renderers.build(app / "icloud_read.swift", app / "data", "icloud-read", 60)


# Читает локальный файл напрямую с проверкой ограничения размера.
# Возвращает `stream.read(max_bytes + 1)`.
def _plain_read(path, max_bytes=MAX_BYTES):
    with path.open("rb") as stream:
        return stream.read(max_bytes + 1)


# Читает файл через Foundation-помощник с ограничением времени.
# Запускает внешний процесс; параметры и ограничения заданы в теле функции.
def _coordinated_read(path, max_bytes=MAX_BYTES):
    result = subprocess.run([str(renderer()), str(path), str(max_bytes)],
                            capture_output=True, check=True, timeout=READ_TIMEOUT)
    return result.stdout


# Возвращает ограниченное содержимое файла после необходимых проверок.
# При недопустимом состоянии возбуждает ValueError, CloudReadPending.
def read_bytes(path, *, max_bytes=MAX_BYTES, coordinated=False):
    path = Path(path)
    if type(max_bytes) is not int or not 0 < max_bytes <= 20 * 1024 * 1024:
        raise ValueError("Предел чтения должен быть от 1 байта до 20 МБ")
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Вместо {path.name} должен быть обычный файл")
    arguments = (path,) if max_bytes == MAX_BYTES else (path, max_bytes)
    try:
        raw = _coordinated_read(*arguments) if coordinated and sys.platform == 'darwin' else _plain_read(*arguments)
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


# Преобразует ошибку чтения iCloud в понятное сообщение состояния.
# Возвращает `str(error)`; либо `'iCloud временно заблокировал доступ к файлу. Данные в базе, выгрузка остаётся в очереди; повторим автоматически'`.
def sync_error(error):
    if isinstance(error, CloudReadPending):
        return str(error)
    if isinstance(error, OSError) and error.errno == errno.EDEADLK:
        return "iCloud временно заблокировал доступ к файлу. Данные в базе, выгрузка остаётся в очереди; повторим автоматически"
    return str(error)
