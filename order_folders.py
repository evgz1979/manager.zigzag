"""Создание папки заказа в объекте с журналом и самостоятельным откатом."""
import os
import re
import threading
import unicodedata
from datetime import date
from pathlib import Path

import folder_layout as layout
from folder_structure import folder_role

LOCK = threading.RLock()


class OrderFolderConflict(ValueError):
    pass


def create(root, relative, order_date, title):
    root = Path(root).resolve()
    if not isinstance(relative, str) or not Path(relative).parts or any(part.startswith(".") for part in Path(relative).parts):
        raise ValueError("Выберите папку объекта")
    parent = layout.safe_path(root, relative, [Path(relative).parts[0]])
    if not parent.is_dir():
        raise FileNotFoundError("Папка объекта недоступна")
    if folder_role(root, relative)["folderKind"] != "object":
        raise ValueError("Папку заказа можно создать только внутри объекта клиента")
    if not isinstance(order_date, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", order_date):
        raise ValueError("Укажите дату в формате ГГГГ-ММ-ДД")
    try:
        date.fromisoformat(order_date)
    except ValueError:
        raise ValueError("Укажите существующую дату с годом, месяцем и днём") from None
    if not isinstance(title, str):
        raise ValueError("Укажите название заказа")
    if any(character in '/\\:' or ord(character) < 32 or ord(character) == 127 for character in title):
        raise ValueError("Название должно быть в одну строку, без /, \\ и :")
    title = unicodedata.normalize("NFC", title.strip())
    if not title:
        raise ValueError("Укажите название заказа")
    name = f"{order_date} - {title}"
    if len(os.fsencode(name)) > 255:
        raise ValueError("Название папки слишком длинное. Сократите название заказа")
    destination = parent / name
    with LOCK:
        if layout.exists(destination):
            raise OrderFolderConflict("Папка или файл с таким именем уже существует. Измените дату или название")
        path = destination.relative_to(root).as_posix()
        plan = layout.Plan(root, [Path(relative).parts[0]])
        plan.mkdir(path)
        if not plan.operations:
            raise OrderFolderConflict("Папка или файл с таким именем уже существует. Измените дату или название")
        before = {"parent": relative, "identity": layout.identity(parent),
                  "children": [{"name": item.name, "identity": layout.identity(item)} for item in parent.iterdir()]}
        session = plan.create_session(["Создать папку заказа из интерфейса.", "Дата: " + order_date, "Название: " + title], before)
        try:
            layout.apply(session)
            layout.save_json(session / ".result.json", {"status": "created", "path": path, "identity": layout.identity(destination)})
        except Exception as error:
            try:
                layout.save_json(session / ".result.json", {"status": "failed", "path": path, "error": str(error)})
            except OSError:
                pass
            if isinstance(error, FileExistsError):
                raise OrderFolderConflict("Путь уже занят. Существующие данные сохранены") from error
            raise
    return {"path": path, "name": name, "journal": session.relative_to(root).as_posix()}
