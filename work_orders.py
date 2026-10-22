"""Supplier-order selections stored as stable identities in the parent card."""
import json
from pathlib import Path

from folder_structure import dated, is_service_folder, is_supplier_root, is_work_root, is_print_section

LINKS_BLOCK = "Связанные заказы поставщиков"
MAX_LINKS = 200


def in_work(relative):
    parts = Path(relative).parts
    return bool(parts and is_work_root(parts[0]))


def direct_order(relative):
    parts = Path(relative).parts
    return len(parts) == 2 and is_work_root(parts[0]) and dated(parts[1])


def supplier_name(relative):
    """Actual #work section, without inspecting folders or assigning a root order."""
    parts = Path(relative).parts
    if len(parts) < 3 or not is_work_root(parts[0]) or dated(parts[1]):
        return ""
    return parts[1][1:].strip() if parts[1].startswith('#') else parts[1]


def supplier_order(relative):
    parts = Path(relative).parts
    if is_service_folder(relative) or is_print_section(Path(relative).parent.as_posix()):
        return False
    return (len(parts) == 3 and is_work_root(parts[0]) and not dated(parts[1])) or (
        len(parts) == 2 and is_supplier_root(parts[0]))


def checked_ids(value):
    if not isinstance(value, list) or len(value) > MAX_LINKS or any(
            not isinstance(item, str) or not item or len(item) > 100 for item in value):
        raise ValueError(f"Выбери не больше {MAX_LINKS} заказов поставщиков")
    if len(set(value)) != len(value):
        raise ValueError("Заказ в подборке не должен повторяться")
    return value


def read_links(blocks):
    if LINKS_BLOCK not in blocks:
        return []
    try:
        body = json.loads(blocks[LINKS_BLOCK])
        if not isinstance(body, dict) or set(body) != {"version", "order_ids"} or type(body["version"]) is not int or body["version"] != 1:
            return None
        return checked_ids(body["order_ids"])
    except (TypeError, ValueError):
        return None


def write_links(blocks, identities):
    if read_links(blocks) is None:
        raise ValueError("Неизвестный раздел связанных заказов сохранён без изменений")
    return {**blocks, LINKS_BLOCK: json.dumps({"version": 1, "order_ids": checked_ids(identities)}, ensure_ascii=False)}


def summary(row):
    return {key: row[key] for key in ("id", "path", "title", "status", "registered")} | {
        "supplier": Path(row["path"]).parts[-2]}
