"""A readable, extensible order document. This file alone can rebuild an order."""
import hashlib
import json
import os
import re
import tempfile
import time
import unicodedata
import icloud_access
from decimal import Decimal, InvalidOperation
from pathlib import Path

DOCUMENT = "!.txt"
FORMAT = 3
FINANCIAL_STATUS_LABELS = {"unspecified": "Не указан", "payment": "На оплате", "partial": "Частично оплачен", "paid": "Оплачен"}
LEGACY_STATUSES = ("!status.txt", "status.txt", ".status.txt")
LEGACY_DOCUMENTS = (*LEGACY_STATUSES, "!order.txt", ".order.json")
KNOWN_BLOCKS = {"Заказ", "Финансы", "Заметка", "Служебное"}
ORDER_FIELDS = {"status", "financial_status", "title", "client", "path", "amount", "costs", "paid", "id", "revision", "updated"}
MAX_MONEY = 999_999_999_999_99
TODO_BLOCK = "Задачи"
PURCHASE_BLOCK = "Закупки и затраты"
FAVORITE_BLOCK = "Избранное"
FLAG_BLOCK = "Флажок"
BLUE_PLUS_BLOCK = "Синий плюс"
DOLLAR_BLOCK = "Зелёный доллар"
PURCHASE_SUPPLIERS = ("newtek", "glass", "antares", "tbm", "remex")
PRIMARY_PURCHASE_SUPPLIERS = ("antares", "himlex", "newtek", "glass")
UNSET_TODOS = object()


def read_favorite(blocks):
    if FAVORITE_BLOCK not in blocks:
        return False
    return {"да": True, "нет": False}.get(blocks[FAVORITE_BLOCK].strip().casefold())


def write_favorite(blocks, value):
    if type(value) is not bool:
        raise ValueError("Укажите состояние избранного: вкл или выкл")
    if read_favorite(blocks) is None:
        raise ValueError("Прежний раздел «Избранное» сохранён. Проверь его в !.txt заказа")
    return {**blocks, FAVORITE_BLOCK: "Да" if value else "Нет"}


def read_flag(blocks):
    if FLAG_BLOCK not in blocks:
        return False
    value = blocks[FLAG_BLOCK]
    return {"да": True, "нет": False}.get(value.strip().casefold()) if isinstance(value, str) else None


def write_flag(blocks, value):
    if type(value) is not bool:
        raise ValueError("Укажи состояние флажка: вкл или выкл")
    if read_flag(blocks) is None:
        raise ValueError("Неизвестная отметка флажка сохранена без изменений")
    return {**blocks, FLAG_BLOCK: "Да" if value else "Нет"}


def read_blue_plus(blocks):
    if BLUE_PLUS_BLOCK not in blocks:
        return False
    value = blocks[BLUE_PLUS_BLOCK]
    return {"да": True, "нет": False}.get(value.strip().casefold()) if isinstance(value, str) else None


def write_blue_plus(blocks, value):
    if type(value) is not bool:
        raise ValueError("Укажи состояние синего плюса: вкл или выкл")
    if read_blue_plus(blocks) is None:
        raise ValueError("Неизвестная отметка синего плюса сохранена без изменений")
    return {**blocks, BLUE_PLUS_BLOCK: "Да" if value else "Нет"}


def read_dollar(blocks):
    if DOLLAR_BLOCK not in blocks:
        return False
    value = blocks[DOLLAR_BLOCK]
    return {"да": True, "нет": False}.get(value.strip().casefold()) if isinstance(value, str) else None


def write_dollar(blocks, value):
    if type(value) is not bool:
        raise ValueError("Укажи состояние зелёного доллара: вкл или выкл")
    if read_dollar(blocks) is None:
        raise ValueError("Неизвестная отметка зелёного доллара сохранена без изменений")
    return {**blocks, DOLLAR_BLOCK: "Да" if value else "Нет"}


def validate_todos(items):
    if not isinstance(items, list) or len(items) > 200:
        raise ValueError("В списке может быть не более 200 задач")
    result = []
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("text"), str) or type(item.get("done")) is not bool:
            raise ValueError("Некорректная задача")
        text = item["text"].strip()
        if not text or len(text) > 1000 or any(char in text for char in "\r\n\x00"):
            raise ValueError("Укажите задачу одной строкой, до 1000 символов")
        result.append({"text": text, "done": item["done"]})
    return result


def read_todos(blocks):
    body = blocks.get(TODO_BLOCK, "")
    items = []
    for line in body.splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r"- \[([ xX])\] (.+)", line)
        if not match:
            return None  # Preserve an existing free-form section without rewriting it.
        items.append({"text": match[2], "done": match[1].lower() == "x"})
    try:
        return validate_todos(items)
    except ValueError:
        return None


def write_todos(blocks, items):
    result = dict(blocks)
    result[TODO_BLOCK] = "\n".join("- [" + ("x" if item["done"] else " ") + "] " + item["text"] for item in validate_todos(items))
    return result


def validate_purchases(items):
    result = validate_todos(items)
    for raw, item in zip(items, result):
        suppliers = raw.get("suppliers", [])
        if not isinstance(suppliers, list) or any(not isinstance(name, str) or name not in PURCHASE_SUPPLIERS for name in suppliers) or len(set(suppliers)) != len(suppliers):
            raise ValueError("Некорректный выбор поставщиков закупки")
        item["suppliers"] = [name for name in PURCHASE_SUPPLIERS if name in suppliers]
    return result


def read_purchases(blocks):
    items, has_suppliers = [], False
    for line in blocks.get(PURCHASE_BLOCK, "").splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r"- \[([ xX])\] (.+)", line)
        if match:
            items.append({"text": match[2], "done": match[1].lower() == "x", "suppliers": []})
            has_suppliers = False
        elif line.startswith("  Поставщики: ") and items and not has_suppliers:
            selected = line[len("  Поставщики: "):]
            items[-1]["suppliers"] = [] if selected == "—" else selected.split(", ")
            has_suppliers = True
        else:
            return None
    try:
        return validate_purchases(items)
    except ValueError:
        return None


def write_purchases(blocks, items):
    result = dict(blocks)
    result[PURCHASE_BLOCK] = "\n".join("- [" + ("x" if item["done"] else " ") + "] " + item["text"] +
        "\n  Поставщики: " + (", ".join(item["suppliers"]) or "—") for item in validate_purchases(items))
    return result


def purchase_matches_supplier(item, supplier):
    if supplier == "etc":
        return not any(name in PRIMARY_PURCHASE_SUPPLIERS for name in item["suppliers"])
    return isinstance(supplier, str) and supplier in PURCHASE_SUPPLIERS and supplier in item["suppliers"]


def write_purchase_done(blocks, index, text, supplier, done):
    """Change only the original checkbox; retain the rest of the stored block."""
    items = read_purchases(blocks)
    if items is None:
        raise ValueError("Неизвестные записи закупок сохранены без изменений")
    if type(index) is not int or index < 0 or index >= len(items) or type(done) is not bool:
        raise ValueError("Укажи закупку и отметку выполнения")
    item = items[index]
    if not purchase_matches_supplier(item, supplier) or text != item["text"]:
        raise ValueError("Закупка или выбор поставщика изменились. Обнови список")
    lines = blocks[PURCHASE_BLOCK].splitlines(keepends=True)
    position = -1
    for line_index, line in enumerate(lines):
        if line.startswith("- ["):
            position += 1
            if position == index:
                lines[line_index] = line[:3] + ("x" if done else " ") + line[4:]
                break
    return {**blocks, PURCHASE_BLOCK: "".join(lines)}


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
    return icloud_access.read_bytes(path).decode("utf-8-sig").replace("\r\n", "\n")


def status_key(value, labels):
    normalized = lambda item: unicodedata.normalize("NFC", item).casefold()
    if "process" in labels and normalized(value) == normalized("В работе"):
        return "process"  # Previous readable cards keep the same production stage.
    status = next((key for key, label in labels.items() if normalized(label) == normalized(value)), value)
    if status not in labels:
        raise ValueError("Неизвестный статус в карточке заказа")
    return status


def split_statuses(record, labels):
    """Read previous mixed statuses without inventing a production stage."""
    result = dict(record)
    if "status" in result:
        # Cards predating separate financial statuses used this label for payment.
        status_labels = {**labels, "payment": "На оплате"} if "financial_status" in result else {"payment": "На оплате", **labels}
        status = status_key(result["status"], status_labels)
        result["status"] = "unspecified" if status == "payment" else status
        result.setdefault("financial_status", "payment" if status == "payment" else "unspecified")
    if "financial_status" in result:
        result["financial_status"] = status_key(result["financial_status"], FINANCIAL_STATUS_LABELS)
    return result


def parse(text, labels):
    # Old status text is accepted even when manually renamed to !.txt.
    if text.startswith("Статус: "):
        heading, separator, note = text.partition("\n\nЗаметка:\n")
        if not separator:
            raise ValueError("Проверьте формат статуса и заметки")
        return split_statuses({"status": heading[8:].strip(), "note": note, "extra_blocks": {}}, labels)
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
    record = {"schema": int(metadata.get("Формат", FORMAT)),
              "note": "\n".join(line[2:] for line in note_lines),
              "extra_blocks": {name: body for name, body in blocks.items() if name not in KNOWN_BLOCKS}}
    if "Заказ" in blocks:
        record["status"] = main.get("Статус", "")
    if "Статус оплаты" in finance:
        record["financial_status"] = finance["Статус оплаты"]
    if main.get("Название"):
        record["title"] = main["Название"]
    for key, label in (("amount", "Сумма заказа"), ("costs", "Затраты"), ("paid", "Оплачено")):
        if "Заказ" not in blocks and "Финансы" not in blocks:
            continue
        value = finance.get(label, "Не указано")
        record[key] = None if value == "Не указано" else money(value.removesuffix(" ₽"))
    if metadata:
        if metadata.get("Формат") not in ("2", str(FORMAT)):
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
    return split_statuses(record, labels)


def render(record, labels):
    record = split_statuses(record, labels)
    main = []
    for key, label in (("title", "Название"), ("client", "Клиент"), ("path", "Папка")):
        if record.get(key):
            main.append(f"{label}: {record[key]}")
    blocks = []
    if record.get("status"):
        main.append("Статус: " + labels[record["status"]])
        blocks.append(("Заказ", "\n".join(main)))
    if any(key in record for key in ("financial_status", "amount", "costs", "paid")):
        amount, costs, paid = (record.get(key) for key in ("amount", "costs", "paid"))
        profit = amount - costs if amount is not None and costs is not None else None
        debt = amount - paid if amount is not None and paid is not None else None
        finance = ["Статус оплаты: " + FINANCIAL_STATUS_LABELS[record["financial_status"]]] if "financial_status" in record else []
        finance.extend(label + ": " + display_money(value) for label, value in (
            ("Сумма заказа", amount), ("Затраты", costs), ("Прибыль", profit),
            ("Оплачено", paid), ("Остаток оплаты", debt)))
        blocks.append(("Финансы", "\n".join(finance)))
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
        return split_statuses(value, labels)
    record = {}
    card = folder / "!order.txt"
    if card.exists() or card.is_symlink():
        text = read_text(card)
        heading, separator, tail = text.partition("\n\nЗаметка:\n")
        if not separator:
            raise ValueError("Некорректная прежняя карточка !order.txt")
        note, marker, _ = tail.rpartition("\n\nВерсия: ")
        values = dict(line.split(": ", 1) for line in heading.splitlines() if ": " in line)
        record = split_statuses({"status": values.get("Статус", ""),
                  "note": note if marker else tail, "title": values.get("Название", folder.name), "extra_blocks": {}}, labels)
        for key, label in (("amount", "Сумма заказа"), ("costs", "Затраты"), ("paid", "Оплачено")):
            value = values.get(label, "Не указано")
            record[key] = None if value == "Не указано" else money(value.removesuffix(" ₽"))
    for name in LEGACY_STATUSES:
        if (folder / name).exists() or (folder / name).is_symlink():
            latest = parse(read_text(folder / name), labels)
            if latest.get("status") == "unspecified" and latest.get("financial_status") == "payment" and record.get("status"):
                latest["status"] = record["status"]
            record.update(latest)
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


def archive_current(folder):
    """Preserve the original card bytes before a format upgrade."""
    source = folder / DOCUMENT
    if not source.exists():
        return
    read_text(source)
    raw = icloud_access.read_bytes(source)
    history = folder / ".order-history"
    version = history / hashlib.sha256(raw).hexdigest()
    if history.is_symlink() or version.is_symlink():
        raise ValueError("История заказа не должна быть символической ссылкой")
    version.mkdir(parents=True, exist_ok=True)
    destination = version / DOCUMENT
    if destination.is_symlink():
        raise ValueError("Файл истории не должен быть символической ссылкой")
    if not destination.exists():
        destination.write_bytes(raw)
    if icloud_access.read_bytes(destination) != raw or icloud_access.read_bytes(source) != raw:
        raise ValueError("Карточка изменилась во время переноса; повторите выгрузку")


def archive_legacy(folder):
    """Keep byte-for-byte originals in hidden history after writing the unified file."""
    for name in LEGACY_DOCUMENTS:
        source = folder / name
        if not source.exists() and not source.is_symlink():
            continue
        if source.is_symlink() or not source.is_file():
            raise ValueError(f"Вместо {name} должен быть обычный файл")
        raw = icloud_access.read_bytes(source)
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
        if icloud_access.read_bytes(destination) != raw or icloud_access.read_bytes(source) != raw:
            raise ValueError("Прежний файл изменился во время переноса; повторите выгрузку")
        source.unlink()
