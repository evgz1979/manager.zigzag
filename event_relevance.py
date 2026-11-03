"""Актуальность события — независимый читаемый блок карточки папки."""
from pathlib import Path
from folder_structure import is_service_folder

BLOCK = "Актуальность события"
LABELS = {"none": "Без статуса", "active": "Актуально", "check": "Проверить", "inactive": "Неактуально"}


# Проверяет, является ли папка непосредственным событием заказа.
# Формирует возвращаемое значение из проверенного локального состояния.
def is_event(path, owner):
    return (Path(path).parent.as_posix() == owner and not is_service_folder(path)
            and not any(part.startswith(".") for part in Path(path).parts))


# Сопоставляет текст блока актуальности с известным состоянием события.
# Возвращает `'none' if body is None else next((key for (key, label) in LABELS.items() if body.strip() == label), None)`.
def read(blocks):
    body = blocks.get(BLOCK)
    return "none" if body is None else next((key for key, label in LABELS.items() if body.strip() == label), None)


# Меняет только известный блок актуальности папки события.
# При недопустимом состоянии возбуждает ValueError.
def write(blocks, value):
    if not isinstance(value, str) or value not in LABELS:
        raise ValueError("Выберите состояние события: " + ", ".join(LABELS.values()))
    if read(blocks) is None:
        raise ValueError(f"Раздел [{BLOCK}] содержит неизвестный текст; он сохранён без замены. Проверьте !.txt события")
    return {**blocks, BLOCK: LABELS[value]}


# Формирует представление состояния и ошибок для интерфейса.
# Формирует возвращаемое значение из проверенного локального состояния.
def info(record, error=""):
    value = read(record["extra_blocks"]) if record else None
    return {"value": value, "revision": record["revision"] if record else None,
            "sync_pending": record["sync_pending"] if record else False,
            "sync_error": record["sync_error"] if record else "",
            "error": error or (f"Проверьте раздел [{BLOCK}] в !.txt события" if record and value is None else "")}
