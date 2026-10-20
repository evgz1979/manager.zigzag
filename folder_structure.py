"""Recognize folder roles from names and immediate children, without reading cards."""
import os
import re
from datetime import date
from pathlib import Path


YEAR = re.compile(r"^(?:19|20)\d{2}$")
DATE = re.compile(r"^(\d{4}|\d{2})[- ._](\d{2})[- ._](\d{2})(?=$|\D)")
DATE_LIKE = re.compile(r"^(?:19|20)\d{2}[- ._]\d")
NUMBER = re.compile(r"^\d{2,}(?=$|\D)")
LABELS = {"root": "Корень документов", "client": "Клиент", "object": "Объект", "year": "Группа года",
          "supplier_root": "Заказы поставщикам · стекло и стеклопакеты",
          "group": "Общая группа", "order": "Заказ", "event": "Событие или материалы заказа", "service": "Служебная папка",
          "invalid": "Папка с некорректной датой"}


def is_supplier_root(name):
    return name.startswith("#") and name[1:].strip().casefold() == "glass"


def is_service_folder(relative):
    return any(part.startswith("#") and not (index == 0 and is_supplier_root(part))
               for index, part in enumerate(Path(relative).parts))


def dated(name):
    match = DATE.match(name)
    if not match:
        return False
    year, month, day = map(int, match.groups())
    if len(match[1]) == 2:
        year += 2000
    if month == 0:
        return day == 0
    try:
        date(year, month, day or 1)
        return True
    except ValueError:
        return False


def folder_role(root, relative):
    parts = Path(relative).parts
    if not parts:
        kind = "root"
    elif is_service_folder(relative):
        kind = "service"
    else:
        kind = "supplier_root" if is_supplier_root(parts[0]) else "group" if NUMBER.match(parts[0]) else "client"
        for index, name in enumerate(parts[1:], 1):
            if kind == "order":
                kind = "event"
                break  # Never inspect event or service contents.
            if dated(name):
                kind = "order"
            elif DATE.match(name) or DATE_LIKE.match(name):
                kind = "invalid"
            elif YEAR.fullmatch(name) or NUMBER.match(name):
                folder = Path(root).joinpath(*parts[:index + 1])
                with os.scandir(folder) as entries:
                    children = [(entry.name, entry.is_dir(follow_symlinks=False)) for entry in entries
                                if not entry.name.startswith(".") and not entry.is_symlink()]
                directories = [child for child, is_dir in children if is_dir]
                grouped_orders = any(dated(child) or YEAR.fullmatch(child) for child in directories if not child.startswith("#"))
                grouped_folders = any(not child.startswith("#") and not NUMBER.match(child) for child in directories)
                numbered_orders = any(re.match(r"^\d{3,}(?=$|\D)", child) for child in directories)
                if YEAR.fullmatch(name):
                    has_materials = any(not is_dir and child not in ("!.txt", "!status.txt", "!order.txt", "status.txt") for child, is_dir in children)
                    has_events = any(child.startswith("#") or NUMBER.match(child) for child in directories)
                    kind = "year" if grouped_orders or grouped_folders or numbered_orders or not (has_events or has_materials) else "order"
                else:
                    nested_numbers = len(NUMBER.match(name)[0]) == 2 and numbered_orders
                    kind = "group" if grouped_orders or nested_numbers or (len(NUMBER.match(name)[0]) == 2 and grouped_folders) else "order"
            else:
                kind = "object"
    allowed = kind == "order"
    return {"folderKind": kind, "folderKindLabel": LABELS[kind], "canRegisterOrder": allowed,
            "registrationHint": "" if allowed else LABELS[kind] + " — не заказ. Выберите папку конкретного заказа по дате или номеру."}
