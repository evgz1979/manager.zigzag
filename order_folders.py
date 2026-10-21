"""Создание папки заказа в объекте с журналом и самостоятельным откатом."""
import os
import re
import threading
import unicodedata
from datetime import date
from pathlib import Path

import folder_layout as layout
from folder_structure import folder_role, section_prefix, YEAR, DATE, DATE_LIKE, NUMBER

LOCK = threading.RLock()


class OrderFolderConflict(ValueError):
    pass


def layout_scope(relative):
    prefix = section_prefix(relative)
    return {"service_roots": [Path(*prefix).as_posix()]} if prefix else {}


def year_container(root, relative):
    parts = Path(relative).parts
    return bool(parts and YEAR.fullmatch(parts[-1]) and folder_role(root,relative)["folderKind"]=="year"
                and folder_role(root,Path(relative).parent.as_posix())["folderKind"]=="object")


def year_groups(root, relative):
    parent = Path(root)/relative
    return [item.name for item in parent.iterdir() if YEAR.fullmatch(item.name)
            and not item.is_symlink() and item.is_dir()
            and folder_role(root,item.relative_to(root).as_posix())["folderKind"]=="year"]


def create_object(root, relative, title):
    root = Path(root).resolve()
    if not isinstance(relative,str) or not Path(relative).parts or any(p.startswith('.') for p in Path(relative).parts):
        raise ValueError("Выбери клиента")
    if not isinstance(title,str) or any(c in '/\\:' or ord(c)<32 or ord(c)==127 for c in title):
        raise ValueError("Укажи название объекта в одну строку без /, \\ и :")
    name = unicodedata.normalize('NFC',title.strip())
    if not name or name.startswith(('.','#')) or len(os.fsencode(name))>255 or YEAR.fullmatch(name) or DATE.match(name) or DATE_LIKE.match(name) or NUMBER.match(name):
        raise ValueError("Укажи название или адрес объекта без даты и числового префикса")
    with LOCK:
        parent = layout.safe_path(root,relative,[Path(relative).parts[0]])
        if not parent.is_dir() or folder_role(root,relative)["folderKind"]!="client":
            raise ValueError("Создать объект можно только в клиенте")
        path = (Path(relative)/name).as_posix()
        if layout.exists(root/path):
            raise OrderFolderConflict("Объект или файл с таким именем уже существует")
        plan = layout.Plan(root,[Path(relative).parts[0]])
        plan.mkdir(path)
        session = plan.create_session(["Создать объект клиента из интерфейса"],{"parent":relative,"identity":layout.identity(parent)})
        try:
            layout.apply(session)
        except FileExistsError as error:
            raise OrderFolderConflict("Путь уже занят; существующие данные сохранены") from error
        layout.save_json(session/'.result.json',{"status":"created","path":path})
        return {"path":path,"name":name,"journal":session.relative_to(root).as_posix()}


def create(root, relative, order_date, title):
    root = Path(root).resolve()
    if not isinstance(relative, str) or not Path(relative).parts or any(part.startswith(".") for part in Path(relative).parts):
        raise ValueError("Выберите папку объекта")
    parent = layout.safe_path(root, relative, [Path(relative).parts[0]], **layout_scope(relative))
    if not parent.is_dir():
        raise FileNotFoundError("Папка объекта недоступна")
    role = folder_role(root, relative)["folderKind"]
    in_year = year_container(root,relative) if role=="year" else False
    if role not in {"object", "supplier_root", "work_root", "work_section", "moneys_section"} and not in_year:
        raise ValueError("Выберите объект клиента, # work или раздел внутри # work / # moneys")
    if not isinstance(order_date, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", order_date):
        raise ValueError("Укажите дату в формате ГГГГ-ММ-ДД")
    try:
        date.fromisoformat(order_date)
    except ValueError:
        raise ValueError("Укажите существующую дату с годом, месяцем и днём") from None
    if not YEAR.fullmatch(order_date[:4]):
        raise ValueError("Укажите год от 1900 до 2099")
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
    with LOCK:
        if not parent.is_dir():
            raise FileNotFoundError("Папка объекта недоступна")
        if in_year and order_date[:4]!=parent.name:
            raise ValueError("Год даты заказа должен совпадать с открытой папкой года")
        if role=="object" and year_groups(root,relative):
            parent = parent/order_date[:4]
            if layout.exists(parent) and (parent.is_symlink() or not parent.is_dir() or not year_container(root,parent.relative_to(root).as_posix())):
                raise OrderFolderConflict("Путь года занят отдельной работой или другим файлом")
        destination = parent/name
        if layout.exists(destination):
            raise OrderFolderConflict("Папка или файл с таким именем уже существует. Измените дату или название")
        path = destination.relative_to(root).as_posix()
        plan = layout.Plan(root, [Path(relative).parts[0]], **layout_scope(relative))
        if not parent.exists():
            plan.mkdir(parent.relative_to(root).as_posix())
        plan.mkdir(path)
        if not plan.operations:
            raise OrderFolderConflict("Папка или файл с таким именем уже существует. Измените дату или название")
        before = {"parent": relative, "identity": layout.identity(root/relative),
                  "children": [{"name": item.name, "identity": layout.identity(item)} for item in (root/relative).iterdir()]}
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
