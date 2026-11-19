"""CorelDRAW HP-GL conversion for the cutter folders."""
import io
import math
import re
from pathlib import Path

import file_trash
import file_uploads
import icloud_access
from event_folder_undo import guard_database
from local_metadata import MetadataStore, audit
from thumbnail_cache import signature

DEFAULT_PERCENT = 98.6174
KIND = "plotter_scale"
MAX_BYTES = 16 * 1024 * 1024
RESULT_SUFFIX = "-gpt.plt"
LEGACY_RESULT_STEM = re.compile(r" - e-cut(?: \([0-9]+\))?$", re.IGNORECASE)
COORDINATES = re.compile(r"[+-]?[0-9]{1,10}(?:(?:\s*,\s*|\s+)[+-]?[0-9]{1,10})*")


# Проверяет имя папки резки по тем же правилам пробелов и регистра, что у вложений.
# Ожидает отдельный компонент пути с начальным знаком #.
def is_cutter(name):
    return name.startswith("#") and name[1:].strip().casefold() == "cutter"


# Определяет действие плитки PLT в ветке папки резки.
# Новые и прежние конвертированные копии доступны для скачивания.
def file_action(path):
    path = Path(path)
    if path.suffix.lower() == ".plt" and any(is_cutter(part) for part in path.parent.parts):
        if path.name.casefold().endswith(RESULT_SUFFIX) or LEGACY_RESULT_STEM.search(path.stem):
            return "download"
        return "convert"
    return None


# Читает процент масштаба для одной оси.
# Принимает положительное конечное число с точкой или запятой.
def percent(value):
    if isinstance(value, str):
        value = value.strip().replace(",", ".")
        if not re.fullmatch(r"(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)", value):
            raise ValueError("Укажи масштаб X и Y в процентах")
        value = float(value)
    if type(value) not in (float, int) or not 0 < value < math.inf:
        raise ValueError("Укажи положительный масштаб X и Y в процентах")
    return float(value)


# Читает или сохраняет общие проценты по выходным осям плоттера.
# Отсутствующая запись даёт 98,6174%, запись проверяет версию и сохраняет историю SQLite.
def settings(store, payload=None):
    metadata = MetadataStore(store)
    record = metadata.get(KIND, "")
    if record is not None and (type(record.get("version")) is not int or record["version"] != 1):
        raise ValueError("Неизвестный формат настроек плоттера")
    if payload is not None:
        data = {"version": 1, "x_percent": percent(payload.get("x_percent")), "y_percent": percent(payload.get("y_percent"))}
        with metadata.connect() as db:
            audit(db, "metadata_records")
        record = metadata.put(KIND, "", data, payload.get("revision"))
    if record is None:
        return {"revision": "missing", "x_percent": DEFAULT_PERCENT, "y_percent": DEFAULT_PERCENT}
    return {"revision": record["revision"], "x_percent": percent(record.get("x_percent")), "y_percent": percent(record.get("y_percent"))}


# Разбирает отрезки реза с абсолютными или относительными координатами.
# Сохраняет порядок и разрывы; команды, меняющие геометрию, выдаёт как ошибку.
def read_strokes(body):
    strokes = []
    stroke = None
    position = (0, 0)
    relative = down = seen = unselected = False
    for field in body.decode("ascii").split(";"):
        field = field.strip()
        if not field:
            continue
        command, args = field[:2].upper(), field[2:].strip()
        if unselected:
            raise ValueError("После SP0 в PLT остались команды")
        if command == "IN" and not seen and not args:
            seen = True
            continue
        seen = True
        if command == "SP" and re.fullmatch(r"[0-9]+", args):
            unselected = not args.strip("0")
            continue
        if (command in {"VS", "PW", "WU"} and re.fullmatch(r"[-+,.0-9\s]*", args)) or (command == "LT" and not args):
            continue
        if command not in {"PU", "PD", "PA", "PR"}:
            raise ValueError(f"Не поддерживается команда PLT {command!r}. Экспортируй контуры отрезками из CorelDRAW")
        if command in {"PA", "PR"}:
            relative = command == "PR"
        elif command == "PU":
            stroke = None
            down = False
        else:
            down = True
        if not args:
            continue
        if not COORDINATES.fullmatch(args):
            raise ValueError(f"Некорректные координаты команды {command}")
        coords = [int(token) for token in args.replace(",", " ").split()]
        if len(coords) % 2:
            raise ValueError(f"Неполная пара координат команды {command}")
        for x, y in zip(coords[::2], coords[1::2]):
            point = (position[0] + x, position[1] + y) if relative else (x, y)
            if down and point != position:
                if stroke is None:
                    stroke = [position]
                    strokes.append(stroke)
                stroke.append(point)
            position = point
    if not strokes:
        raise ValueError("В PLT нет контуров для резки")
    return strokes


# Поворачивает контуры вправо на 90°, переносит их к нулю и масштабирует по выходным осям.
# Выдаёт HP-GL в стиле e-cut, поднимает нож и возвращает его в (0, 0).
def convert(body, x_percent, y_percent):
    strokes = read_strokes(body)
    left = min(y for stroke in strokes for x, y in stroke)
    bottom = max(x for stroke in strokes for x, y in stroke)
    x_scale, y_scale = x_percent / 100, y_percent / 100
    output = io.StringIO()
    output.write("IN;;\r\n")
    for stroke in strokes:
        previous = None
        start = None
        for x, y in stroke:
            px, py = (y - left) * x_scale, (bottom - x) * y_scale
            if not math.isfinite(px) or not math.isfinite(py):
                raise ValueError("Слишком большой масштаб плоттера")
            point = (round(px), round(py))
            if previous is None:
                start = point
            elif point != previous:
                if start is not None:
                    output.write(f"PU{start[0]} {start[1]};\r\n")
                    start = None
                output.write(f"PD{point[0]} {point[1]};\r\n")
            previous = point
        if start is not None:
            raise ValueError("При таком масштабе один из контуров теряет размер")
    output.write("PU0 0;\r\nPU;\r\n")
    return output.getvalue().encode("ascii")


# Конвертирует видимый исходный PLT и публикует готовую копию рядом с ним.
# Проверяет свежесть источника; при совпадении имени номер ставится перед -gpt.plt.
def save_conversion(store, payload):
    relative = payload.get("path")
    if not isinstance(relative, str) or file_action(relative) != "convert":
        raise ValueError("Выбери исходный PLT из папки # cutter")
    source = file_trash.checked(store.root, relative)
    folder_path = source.parent.relative_to(store.root).as_posix()
    expected = payload.get("source_key")
    guard_database(store.database, folder_path)

    # Находит ту же папку для безопасной публикации файла.
    # Подменённый, перемещённый или устаревший источник вызывает конфликт.
    def destination(root, _relative_folder):
        current = file_trash.checked(root, relative)
        if not current.is_file() or signature(current.stat()) != expected:
            raise file_uploads.UploadConflict("Исходный PLT изменился. Обнови папку перед конвертацией")
        return current.parent

    folder = destination(store.root, folder_path)
    token = file_uploads.token(store.root, folder_path, folder)
    calibration = settings(store)
    body = icloud_access.read_bytes(source, max_bytes=MAX_BYTES)
    converted = convert(body, calibration["x_percent"], calibration["y_percent"])
    return file_uploads.receive(store, folder_path, token, source.stem + RESULT_SUFFIX,
                                io.BytesIO(converted), len(converted), destination=destination,
                                numbered_suffix=RESULT_SUFFIX)
