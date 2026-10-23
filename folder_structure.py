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
          "work_root": "Производство",
          "moneys_root": "Финансовая информация",
          "work_section": "Производственный раздел", "moneys_section": "Финансовый раздел",
          "supplier_root": "Заказы поставщикам · стекло и стеклопакеты",
          "catalog_group": "Группа клиентов",
          "group": "Общая группа", "order": "Заказ", "event": "Событие или материалы заказа", "service": "Служебная папка",
          "invalid": "Папка с некорректной датой"}


def is_supplier_root(name):
    return name.startswith("#") and name[1:].strip().casefold() == "glass"


def is_work_root(name):
    return name.startswith("#") and name[1:].strip().casefold() == "work"


def is_moneys_root(name):
    return name.startswith("#") and name[1:].strip().casefold() == "moneys"


def is_print_section(relative):
    parts = Path(relative).parts
    return len(parts) == 2 and is_work_root(parts[0]) and parts[1].startswith('#') and parts[1][1:].strip().casefold() == 'print'


def in_freza(relative):
    parts = Path(relative).parts
    return len(parts) >= 2 and is_work_root(parts[0]) and parts[1].startswith('#') and parts[1][1:].strip().casefold() == 'freza'


def is_freza_task(relative):
    parts = Path(relative).parts
    return in_freza(relative) and len(parts) == 3 and not parts[2].startswith(('.', '#'))


def supplier_prefix(relative):
    parts = Path(relative).parts
    if parts and is_supplier_root(parts[0]):
        return parts[:1]  # Совместимость с прежним расположением.
    if len(parts) >= 2 and is_work_root(parts[0]) and is_supplier_root(parts[1]):
        return parts[:2]
    return ()


def section_prefix(relative):
    parts = Path(relative).parts
    if parts and is_work_root(parts[0]) and (len(parts) == 1 or dated(parts[1])):
        return parts[:1]
    if len(parts) >= 2 and (is_work_root(parts[0]) or is_moneys_root(parts[0])):
        return parts[:2]
    return supplier_prefix(relative)


def is_service_folder(relative):
    parts = Path(relative).parts
    if len(parts) == 1 and (is_work_root(parts[0]) or is_moneys_root(parts[0])):
        return False
    return any(part.startswith("#") for part in parts[len(section_prefix(relative)):])


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


def is_catalog_group(name):
    numbered = NUMBER.match(name) or re.match(r"^[0-9]\s*[-–—](?=$|\s)", name)
    return bool(numbered and not (dated(name) or DATE.match(name) or DATE_LIKE.match(name) or YEAR.fullmatch(name)))


def grouped_client(parts):
    if len(parts) < 2 or not is_catalog_group(parts[0]):
        return False
    name = parts[1]
    return not (dated(name) or DATE.match(name) or DATE_LIKE.match(name) or YEAR.fullmatch(name) or NUMBER.match(name))


def client_name(relative):
    parts = Path(relative).parts
    return parts[1] if grouped_client(parts) else parts[0] if parts else ""


def client_path(relative):
    """Client identity by full path, without touching document storage."""
    parts = Path(relative).parts
    if not parts or parts[0].startswith((".", "#")):
        return ""
    if is_catalog_group(parts[0]):
        return Path(*parts[:2]).as_posix() if grouped_client(parts) and not parts[1].startswith((".", "#")) else ""
    return parts[0]


def folder_role(root, relative):
    parts = Path(relative).parts
    if not parts:
        kind = "root"
    elif len(parts) == 1 and is_work_root(parts[0]):
        kind = "work_root"
    elif len(parts) == 1 and is_moneys_root(parts[0]):
        kind = "moneys_root"
    elif is_service_folder(relative):
        kind = "service"
    elif len(parts) == 1 and is_catalog_group(parts[0]):
        kind = "catalog_group"
    elif len(parts) >= 2 and (is_work_root(parts[0]) or is_moneys_root(parts[0])):
        if is_work_root(parts[0]) and dated(parts[1]):
            kind = "order" if len(parts) == 2 else "event"
        elif len(parts) == 2:
            if is_moneys_root(parts[0]):
                kind = "moneys_section"
            else:
                kind = "supplier_root" if is_supplier_root(parts[1]) else "work_section"
        else:
            kind = "order" if len(parts) == 3 else "event"
    else:
        prefix = supplier_prefix(relative)
        kind = "supplier_root" if prefix else "client" if grouped_client(parts) else "group" if is_catalog_group(parts[0]) else "client"
        depth = 2 if grouped_client(parts) else len(prefix) or 1
        for index, name in enumerate(parts[depth:], depth):
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
    print_archive = len(parts) == 3 and is_print_section(Path(*parts[:2]).as_posix())
    allowed = kind == "order" and not print_archive
    return {"folderKind": kind, "folderKindLabel": LABELS[kind], "canRegisterOrder": allowed,
            "registrationHint": "Задания печати создаются в отдельном редакторе # print. Прежняя папка сохранена для доступа к данным." if print_archive else "" if allowed else LABELS[kind] + " — не заказ. Выберите папку конкретного заказа по дате или номеру."}
