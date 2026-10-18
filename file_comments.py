"""Portable comments alongside files; originals are never modified."""
import hashlib
import json
import threading
import unicodedata
from pathlib import Path
from order_document import atomic_write

LOCK = threading.RLock()
MAX_COMMENT = 100_000


class FileCommentConflict(ValueError):
    pass


def paths(file):
    file = Path(file)
    name = unicodedata.normalize("NFC", file.name)
    key = hashlib.sha256(name.encode()).hexdigest()
    folder = file.parent / ".file-comments"
    if folder.is_symlink() or (folder.exists() and not folder.is_dir()):
        raise ValueError("Каталог комментариев должен быть обычной папкой")
    target = folder / ("." + key + ".txt")
    return name, key, folder, target


def read(file):
    name, _, _, target = paths(file)
    if target.is_symlink() or (target.exists() and not target.is_file()):
        raise ValueError("Комментарий должен быть обычным текстовым файлом")
    if not target.exists():
        return {"comment": "", "revision": "missing"}
    if target.stat().st_size > 1024 * 1024:
        raise ValueError("Файл комментария слишком большой")
    raw = target.read_bytes()
    text = raw.decode("utf-8-sig").replace("\r\n", "\n")
    header, separator, body = text.partition("\n\n[Комментарий]\n")
    lines = header.splitlines()
    if (not separator or len(lines) != 3 or lines[0] != "КОММЕНТАРИЙ К ФАЙЛУ"
            or lines[2] != "Формат: 1" or not lines[1].startswith("Файл: ")
            or json.loads(lines[1][6:]) != name):
        raise ValueError("Проверьте формат файла комментария")
    note_lines = body.removesuffix("\n").split("\n")
    if any(not line.startswith("> ") for line in note_lines):
        raise ValueError("Строки комментария должны начинаться с '> '")
    return {"comment": "\n".join(line[2:] for line in note_lines), "revision": hashlib.sha256(raw).hexdigest()}


def save(file, comment, revision):
    if not isinstance(comment, str) or len(comment) > MAX_COMMENT or "\x00" in comment:
        raise ValueError("Комментарий должен быть текстом до 100 000 символов")
    if not isinstance(revision, str):
        raise ValueError("Откройте файл заново перед сохранением комментария")
    comment = comment.replace("\r\n", "\n").replace("\r", "\n")
    with LOCK:
        current = read(file)
        if current["revision"] != revision:
            raise FileCommentConflict("Комментарий изменён в другом окне или вне менеджера. Ваш текст сохранён в поле; обновите данные перед повторной записью.")
        if current["comment"] == comment:
            return current
        name, key, folder, target = paths(file)
        folder.mkdir(exist_ok=True)
        if target.exists():
            history = folder / ".history"
            versions = history / ("." + key)
            if history.is_symlink() or versions.is_symlink():
                raise ValueError("История комментариев должна быть обычной папкой")
            versions.mkdir(parents=True, exist_ok=True)
            backup = versions / ("." + revision + ".txt")
            if backup.is_symlink() or (backup.exists() and not backup.is_file()):
                raise ValueError("Копия комментария должна быть обычным файлом")
            raw = target.read_bytes()
            if hashlib.sha256(raw).hexdigest() != revision:
                raise FileCommentConflict("Комментарий изменился во время сохранения. Повторите открытие файла.")
            if not backup.exists():
                atomic_write(backup, raw.decode("utf-8"))
            if backup.read_bytes() != raw:
                raise ValueError("Не удалось сохранить исходный комментарий в истории")
        if read(file)["revision"] != revision:
            raise FileCommentConflict("Комментарий изменился во время сохранения. Повторите открытие файла.")
        body = "КОММЕНТАРИЙ К ФАЙЛУ\nФайл: " + json.dumps(name, ensure_ascii=False) + "\nФормат: 1\n\n[Комментарий]\n> " + comment.replace("\n", "\n> ") + "\n"
        atomic_write(target, body)
        return read(file)
