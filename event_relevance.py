"""Актуальность события — независимый читаемый блок карточки папки."""
from pathlib import Path

BLOCK = "Актуальность события"
LABELS = {"none": "Без статуса", "active": "Актуально", "check": "Проверить", "inactive": "Неактуально"}


def is_event(path, owner):
    return Path(path).parent.as_posix() == owner and not any(part.startswith(("#", ".")) for part in Path(path).parts)


def read(blocks):
    body = blocks.get(BLOCK)
    return "none" if body is None else next((key for key, label in LABELS.items() if body.strip() == label), None)


def write(blocks, value):
    if not isinstance(value, str) or value not in LABELS:
        raise ValueError("Выберите состояние события: " + ", ".join(LABELS.values()))
    if read(blocks) is None:
        raise ValueError(f"Раздел [{BLOCK}] содержит неизвестный текст; он сохранён без замены. Проверьте !.txt события")
    return {**blocks, BLOCK: LABELS[value]}


def info(record, error=""):
    value = read(record["extra_blocks"]) if record else None
    return {"value": value, "revision": record["revision"] if record else None,
            "sync_pending": record["sync_pending"] if record else False,
            "sync_error": record["sync_error"] if record else "",
            "error": error or (f"Проверьте раздел [{BLOCK}] в !.txt события" if record and value is None else "")}
