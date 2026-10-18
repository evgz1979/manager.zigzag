"""A readable, extensible order document. This file alone can rebuild an order."""
import hashlib
import json
import os
import re
import tempfile
import time
import unicodedata
from decimal import Decimal, InvalidOperation
from pathlib import Path

DOCUMENT = "!.txt"
FORMAT = 2
LEGACY_STATUSES = ("!status.txt", "status.txt", ".status.txt")
LEGACY_DOCUMENTS = (*LEGACY_STATUSES, "!order.txt", ".order.json")
KNOWN_BLOCKS = {"Заказ", "Финансы", "Заметка", "Служебное"}
ORDER_FIELDS = {"status", "title", "client", "path", "amount", "costs", "paid", "id", "revision", "updated"}
MAX_MONEY = 999_999_999_999_99


def folder_note(record):
    return {"note": record.get("note", ""), "extra_blocks": record.get("extra_blocks", {})}


def validate_blocks(blocks):
    if not isinstance(blocks, dict) or any(not isinstance(name, str) or not name
            or any(char in name for char in "[]\r\n") or name in KNOWN_BLOCKS
            or not isinstance(body, str) for name, body in blocks.items()):
        raise ValueError("Некорректные дополнительные разделы карточки")
    return blocks


def money(value):
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise ValueError("Укажите сумму числом")
    try:
        number = Decimal(str(value).replace(" ", "").replace("\u00a0", "").replace(",", "."))
        if not number.is_finite() or number < 0 or number * 100 != (number * 100).to_integral_value() or number * 100 > MAX_MONEY:
            raise ValueError("Сумма должна быть неотрицательной, не более двух знаков после запятой")
        return int(number * 100)
    except InvalidOperation:
        raise ValueError("Укажите сумму числом")


def display_money(value):
    return "Не указано" if value is None else f"{Decimal(value) / 100:,.2f}".replace(",", " ").replace(".", ",") + " ₽"


def read_text(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 1024 * 1024:
        raise ValueError(f"Некорректный файл {path.name}")
    return path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")


def status_key(value, labels):
    normalized = lambda item: unicodedata.normalize("NFC", item).casefold()
    status = next((key for key, label in labels.items() if normalized(label) == normalized(value)), value)
    if status not in labels:
        raise ValueError("Неизвестный статус в карточке заказа")
    return status


def parse(text, labels):
    # Old status text is accepted even when manually renamed to !.txt.
    if text.startswith("Статус: "):
        heading, separator, note = text.partition("\n\nЗаметка:\n")
        if not separator:
            raise ValueError("Проверьте формат статуса и заметки")
        return {"status": status_key(heading[8:].strip(), labels), "note": note, "extra_blocks": {}}
    headings = list(re.finditer(r"(?m)^\[([^\]\r\n]+)\]\n", text))
    blocks = {}
    for index, heading in enumerate(headings):
        name = heading[1]
        if name in blocks:
            raise ValueError(f"Раздел [{name}] повторяется в {DOCUMENT}")
        body = text[heading.end():headings[index + 1].start() if index + 1 < len(headings) else len(text)]
        blocks[name] = body.removesuffix("\n\n")
    if "Заметка" not in blocks:
        raise ValueError(f"Проверьте раздел [Заметка] в {DOCUMENT}")

    def fields(name):
        result = {}
        for line in blocks.get(name, "").splitlines():
            key, separator, value = line.partition(": ")
            if separator:
                result[key] = value
        return result

    main, finance, metadata = fields("Заказ"), fields("Финансы"), fields("Служебное")
    note_lines = blocks["Заметка"].split("\n")
    if any(not line.startswith("> ") for line in note_lines):
        raise ValueError(f"Строки заметки в {DOCUMENT} должны начинаться с '> '")
    record = {"schema": FORMAT,
              "note": "\n".join(line[2:] for line in note_lines),
              "extra_blocks": {name: body for name, body in blocks.items() if name not in KNOWN_BLOCKS}}
    if "Заказ" in blocks:
        record["status"] = status_key(main.get("Статус", ""), labels)
    if main.get("Название"):
        record["title"] = main["Название"]
    for key, label in (("amount", "Сумма заказа"), ("costs", "Затраты"), ("paid", "Оплачено")):
        if "Заказ" not in blocks and "Финансы" not in blocks:
            continue
        value = finance.get(label, "Не указано")
        record[key] = None if value == "Не указано" else money(value.removesuffix(" ₽"))
    if metadata:
        if metadata.get("Формат") != str(FORMAT):
            raise ValueError("Неподдерживаемая версия формата карточки")
        if metadata.get("Идентификатор"):
            record["id"] = metadata["Идентификатор"]
            record["revision"] = int(metadata.get("Версия", "0"))
        if metadata.get("Изменено (Unix)"):
            record["updated"] = float(metadata["Изменено (Unix)"])
        if "В списке заказов" in metadata:
            if metadata["В списке заказов"] not in ("да", "нет"):
                raise ValueError("Проверьте поле «В списке заказов» в карточке")
            record["registered"] = metadata["В списке заказов"] == "да"
    return record


def render(record, labels):
    main = []
    for key, label in (("title", "Название"), ("client", "Клиент"), ("path", "Папка")):
        if record.get(key):
            main.append(f"{label}: {record[key]}")
    blocks = []
    if record.get("status"):
        main.append("Статус: " + labels[record["status"]])
        blocks.append(("Заказ", "\n".join(main)))
    if any(key in record for key in ("amount", "costs", "paid")):
        amount, costs, paid = (record.get(key) for key in ("amount", "costs", "paid"))
        profit = amount - costs if amount is not None and costs is not None else None
        debt = amount - paid if amount is not None and paid is not None else None
        blocks.append(("Финансы", "\n".join(label + ": " + display_money(value) for label, value in (
            ("Сумма заказа", amount), ("Затраты", costs), ("Прибыль", profit),
            ("Оплачено", paid), ("Остаток оплаты", debt)))))
    blocks.append(("Заметка", "> " + record.get("note", "").replace("\n", "\n> ")))
    blocks.extend(validate_blocks(record.get("extra_blocks", {})).items())
    metadata = [f"Формат: {FORMAT}"]
    if "registered" in record:
        metadata.append("В списке заказов: " + ("да" if record["registered"] else "нет"))
    if record.get("id"):
        metadata += ["Идентификатор: " + record["id"], "Версия: " + str(record["revision"]),
                     "Обновлено: " + time.strftime("%Y-%m-%d %H:%M:%S %z", time.localtime(record["updated"])),
                     "Изменено (Unix): " + str(record["updated"])]
    blocks.append(("Служебное", "\n".join(metadata)))
    title = "КАРТОЧКА ЗАКАЗА" if record.get("status") else "ЗАМЕТКА ПАПКИ"
    text = title + "\n\n" + "\n\n".join(f"[{name}]\n{body}" for name, body in blocks) + "\n\n"
    if len(text.encode("utf-8")) > 1024 * 1024:
        raise ValueError("Карточка заказа превышает 1 МБ")
    return text


def load(folder, labels):
    if (folder / DOCUMENT).exists() or (folder / DOCUMENT).is_symlink():
        return parse(read_text(folder / DOCUMENT), labels)
    if (folder / ".order.json").exists() or (folder / ".order.json").is_symlink():
        value = json.loads(read_text(folder / ".order.json"))
        if not isinstance(value, dict):
            raise ValueError("Некорректный прежний снимок заказа")
        return value
    record = {}
    card = folder / "!order.txt"
    if card.exists() or card.is_symlink():
        text = read_text(card)
        heading, separator, tail = text.partition("\n\nЗаметка:\n")
        if not separator:
            raise ValueError("Некорректная прежняя карточка !order.txt")
        note, marker, _ = tail.rpartition("\n\nВерсия: ")
        values = dict(line.split(": ", 1) for line in heading.splitlines() if ": " in line)
        record = {"status": status_key(values.get("Статус", ""), labels),
                  "note": note if marker else tail, "title": values.get("Название", folder.name), "extra_blocks": {}}
        for key, label in (("amount", "Сумма заказа"), ("costs", "Затраты"), ("paid", "Оплачено")):
            value = values.get(label, "Не указано")
            record[key] = None if value == "Не указано" else money(value.removesuffix(" ₽"))
    for name in LEGACY_STATUSES:
        if (folder / name).exists() or (folder / name).is_symlink():
            record.update(parse(read_text(folder / name), labels))
            return record
    return record


def atomic_write(target, body):
    if target.is_symlink() or (target.exists() and not target.is_file()):
        raise ValueError(f"Вместо {target.name} должен быть обычный файл")
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", prefix=".manager-order-", suffix=".tmp", dir=target.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(body)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        temporary.chmod(target.stat().st_mode & 0o777 if target.exists() else 0o644)
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)


def archive_legacy(folder):
    """Keep byte-for-byte originals in hidden history after writing the unified file."""
    for name in LEGACY_DOCUMENTS:
        source = folder / name
        if not source.exists() and not source.is_symlink():
            continue
        if source.is_symlink() or not source.is_file():
            raise ValueError(f"Вместо {name} должен быть обычный файл")
        raw = source.read_bytes()
        history = folder / ".order-history"
        version = history / hashlib.sha256(raw).hexdigest()
        if history.is_symlink() or version.is_symlink():
            raise ValueError("История заказа не должна быть символической ссылкой")
        version.mkdir(parents=True, exist_ok=True)
        destination = version / name
        if destination.is_symlink():
            raise ValueError("Файл истории не должен быть символической ссылкой")
        if not destination.exists():
            destination.write_bytes(raw)
        if destination.read_bytes() != raw or source.read_bytes() != raw:
            raise ValueError("Прежний файл изменился во время переноса; повторите выгрузку")
        source.unlink()
