"""Создание заказа и управление его непосредственными служебными папками."""
import errno
import os
import re
import stat
import threading
import unicodedata
from datetime import date
from pathlib import Path

import folder_layout as layout
from event_folder_undo import guard_database
from folder_structure import client_path, folder_role, section_prefix, is_catalog_group, is_catalog_year, is_print_section, in_freza, in_payroll, YEAR, DATE, DATE_LIKE, NUMBER

LOCK = threading.RLock()
SERVICE_FOLDERS = ("bills", "cdr", "docs", "freza", "cutter", "pvc", "alum")
DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW


# Обозначает конфликт изменения в этом модуле.
# Вызывающий обработчик использует тип исключения для отказа без подмены данных.
class OrderFolderConflict(ValueError):
    pass


# Проверяет доступность переключателей для непосредственного заказа клиента.
# Учитывает клиентов в числовых группах и готовую роль папки.
def can_manage_service_folders(relative, role):
    return bool(client_path(relative)) and role["canRegisterOrder"]


# Формирует идентификатор открытого заказа для проверки перед записью.
# Изменение содержимого папки сохраняет идентификатор, замена папки меняет его.
def service_parent_key(info):
    return f"{info.st_dev}:{info.st_ino}:{getattr(info, 'st_birthtime', '')}"


# Читает семь переключателей из непосредственных записей открытой папки заказа.
# Проверяет пустоту по первой записи, включая скрытые файлы, ссылки и подпапки.
def service_folder_state(directory):
    matches = {kind: [] for kind in SERVICE_FOLDERS}
    with os.scandir(directory) as entries:
        for entry in entries:
            if entry.name.startswith("#"):
                kind = entry.name[1:].strip().casefold()
                if kind in matches:
                    try:
                        matches[kind].append((entry.name, entry.stat(follow_symlinks=False)))
                    except FileNotFoundError:
                        continue
    folders = []
    for kind, entries in matches.items():
        enabled = any(stat.S_ISDIR(info.st_mode) for _, info in entries)
        name, revision, reason = f"# {kind}", "", ""
        if len(entries) > 1:
            reason = "Есть несколько записей с таким именем"
        elif entries:
            name, info = entries[0]
            revision = f"{service_parent_key(info)}:{info.st_ctime_ns}"
            if enabled:
                try:
                    child = os.open(name, DIRECTORY_FLAGS, dir_fd=directory)
                    try:
                        with os.scandir(child) as children:
                            if next(children, None) is not None:
                                reason = "Папка не пуста"
                    finally:
                        os.close(child)
                except OSError:
                    reason = "Не удалось проверить содержимое папки"
            else:
                reason = "Имя занято файлом или ссылкой"
        folders.append({"kind": kind, "name": name, "enabled": enabled, "revision": revision, "reason": reason})
    return {"parent": service_parent_key(os.fstat(directory)), "folders": folders}


# Читает или меняет одну служебную папку клиентского заказа.
# Сверяет снимок и использует mkdir/rmdir относительно открытой папки без рекурсивного удаления.
def service_folders(store, relative, change=None, *, role=None):
    with LOCK:
        relative = store.path(relative)
        target = store.target(relative)
        if not can_manage_service_folders(relative, role or folder_role(store.root, relative)):
            raise ValueError("Служебные папки настраиваются только в заказе клиента")
        if change is not None:
            guard_database(store.database, relative, include_children=True)
            if change.get("kind") not in SERVICE_FOLDERS or type(change.get("enabled")) is not bool:
                raise ValueError("Выбери служебную папку и состояние переключателя")
        directory = os.open(target, DIRECTORY_FLAGS)
        try:
            snapshot = service_folder_state(directory)
            if change is None:
                return snapshot
            item = next(item for item in snapshot["folders"] if item["kind"] == change["kind"])
            if change.get("parent") != snapshot["parent"] or change.get("revision") != item["revision"]:
                raise OrderFolderConflict("Служебная папка изменилась. Проверь текущее состояние и повтори выбор")
            if item["reason"]:
                raise OrderFolderConflict(item["reason"])
            if change["enabled"] != item["enabled"]:
                try:
                    if change["enabled"]:
                        os.mkdir(item["name"], dir_fd=directory)
                    else:
                        os.rmdir(item["name"], dir_fd=directory)
                except OSError as error:
                    if error.errno in (errno.EEXIST, errno.ENOENT, errno.ENOTDIR, errno.ENOTEMPTY):
                        raise OrderFolderConflict("Служебная папка изменилась. Проверь текущее состояние и повтори выбор") from error
                    raise
            return service_folder_state(directory)
        finally:
            os.close(directory)


# Проверяет допустимую клиентскую область для создания папок.
# Возвращает `{'service_roots': [Path(*prefix).as_posix()]} if prefix else {}`.
def layout_scope(relative):
    prefix = section_prefix(relative)
    return {"service_roots": [Path(*prefix).as_posix()]} if prefix else {}


# Распознаёт контейнер года, в котором можно создать заказ.
# В группе годов проверяет явный тип; в объекте проверяет роли года и его родителя.
def year_container(root, relative):
    if is_catalog_year(root, relative):
        return True
    parts = Path(relative).parts
    return bool(parts and YEAR.fullmatch(parts[-1]) and folder_role(root,relative)["folderKind"]=="year"
                and folder_role(root,Path(relative).parent.as_posix())["folderKind"]=="object")


# Читает допустимые группы годов выбранного объекта.
# Формирует возвращаемое значение из проверенного локального состояния.
def year_groups(root, relative):
    parent = Path(root)/relative
    return [item.name for item in parent.iterdir() if YEAR.fullmatch(item.name)
            and not item.is_symlink() and item.is_dir()
            and folder_role(root,item.relative_to(root).as_posix())["folderKind"]=="year"]


# Создаёт объект клиента после проверки имени и отсутствия назначения.
# При недопустимом состоянии возбуждает ValueError, OrderFolderConflict.
def create_object(root, relative, title):
    return create_client_container(root, relative, title, "object")


# Создаёт пустую папку клиента в корне документов или выбранной группе клиентов.
# Использует общий план создания контейнера с журналом и откатом.
def create_client(store, relative, title):
    return create_client_container(store.root, relative, title, "client", database=store.database)


# Создаёт клиентский контейнер по роли родителя и безопасному имени.
# План работает без перезаписи, регистрации заказа и создания служебных папок.
def create_client_container(root, relative, title, kind, *, database=None):
    root = Path(root).resolve()
    client = kind == "client"
    at_root = client and relative == ""
    entity = "клиента" if client else "объекта"
    choose_parent = "Выбери корень документов или группу клиентов" if client else "Выбери клиента"
    if not isinstance(relative, str) or (not at_root and not Path(relative).parts) or any(p.startswith('.') for p in Path(relative).parts):
        raise ValueError(choose_parent)
    if not isinstance(title,str) or any(c in '/\\:' or ord(c)<32 or ord(c)==127 for c in title):
        raise ValueError(f"Укажи название {entity} в одну строку без /, \\ и :")
    name = unicodedata.normalize('NFC',title.strip())
    if not name or name.startswith(('.','#')) or len(os.fsencode(name))>255 or YEAR.fullmatch(name) or DATE.match(name) or DATE_LIKE.match(name) or NUMBER.match(name):
        raise ValueError(f"Укажи название {entity} без даты и числового префикса")
    if client and is_catalog_group(name):
        raise ValueError("Укажи имя клиента без числового префикса")
    with LOCK:
        path = (Path(relative) / name).as_posix()
        roots = [Path(path).parts[0]]
        if database is not None:
            guard_database(database, path, include_children=True)
        parent = root if at_root else layout.safe_path(root, relative, roots)
        if not parent.is_dir():
            raise ValueError(choose_parent)
        role = folder_role(root, relative)
        if client and not at_root:
            if (role["catalogGroup"] or {}).get("type") != "clients":
                raise ValueError(choose_parent)
        elif not client and role["folderKind"] != "client":
            raise ValueError(choose_parent)
        if layout.exists(root/path):
            raise OrderFolderConflict("Папка или файл с таким именем уже существует")
        plan = layout.Plan(root, roots)
        plan.mkdir(path)
        if not plan.operations:
            raise OrderFolderConflict("Папка или файл с таким именем уже существует")
        session = plan.create_session([f"Создать папку {entity} из интерфейса"],{"parent":relative,"identity":layout.identity(parent)})
        try:
            layout.apply(session)
        except FileExistsError as error:
            raise OrderFolderConflict("Путь уже занят; существующие данные сохранены") from error
        layout.save_json(session/'.result.json',{"status":"created","path":path})
        return {"path":path,"name":name,"journal":session.relative_to(root).as_posix()}


# Создаёт папку заказа или сверки и при наличии базы регистрирует карточку.
# В группе годов имя равно названию; для сверки и зарплаты планирует только основную папку.
def create(root, relative, order_date, title, *, store=None):
    root = Path(root).resolve()
    if store and store.root.resolve() != root:
        raise ValueError("Рабочая база относится к другому корню документов")
    if not isinstance(relative, str) or not Path(relative).parts or any(part.startswith(".") for part in Path(relative).parts):
        raise ValueError("Выберите папку объекта")
    if is_print_section(relative):
        raise ValueError("Для печати используй «Новое задание» в редакторе # print")
    parent = layout.safe_path(root, relative, [Path(relative).parts[0]], **layout_scope(relative))
    if not parent.is_dir():
        raise FileNotFoundError("Папка объекта недоступна")
    role = folder_role(root, relative)["folderKind"]
    in_year = year_container(root,relative) if role=="year" else False
    title_only = is_catalog_year(root, relative)
    if role not in {"object", "supplier_root", "work_root", "work_section", "moneys_section", "reconciliations_root"} and not in_year:
        raise ValueError("Выберите объект, папку года в группе годов, # work или раздел внутри # work / # moneys")
    if not title_only:
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
    if title_only and title.startswith((".", "#")):
        raise ValueError("Название заказа должно начинаться без точки и #")
    name = title if title_only else f"{order_date} - {title}"
    if len(os.fsencode(name)) > 255:
        raise ValueError("Название папки слишком длинное. Сократите название заказа")
    with LOCK:
        if not parent.is_dir():
            raise FileNotFoundError("Папка объекта недоступна")
        if in_year and not title_only and order_date[:4]!=parent.name:
            raise ValueError("Год даты заказа должен совпадать с открытой папкой года")
        if role=="object" and year_groups(root,relative):
            parent = parent/order_date[:4]
            if layout.exists(parent) and (parent.is_symlink() or not parent.is_dir() or not year_container(root,parent.relative_to(root).as_posix())):
                raise OrderFolderConflict("Путь года занят отдельной работой или другим файлом")
        destination = parent/name
        duplicate = "Папка или файл с таким именем уже существует."
        if layout.exists(destination):
            raise OrderFolderConflict(duplicate + (" Измените название" if title_only else " Измените дату или название"))
        path = destination.relative_to(root).as_posix()
        reconciliation = role == "reconciliations_root"
        plan = layout.Plan(root, [Path(relative).parts[0]], **layout_scope(relative))
        if store:
            plan.order_registration = {"database": str(store.database.resolve()), "path": path,
                                       "table": "reconciliations" if reconciliation else "orders"}
        if not parent.exists():
            plan.mkdir(parent.relative_to(root).as_posix())
        plan.mkdir(path)
        if not reconciliation and not in_freza(relative) and not in_payroll(relative):
            for service in ('# bills', '# cdr'):
                plan.mkdir((Path(path) / service).as_posix())
        if not plan.operations:
            raise OrderFolderConflict(duplicate)
        before = {"parent": relative, "identity": layout.identity(root/relative),
                  "children": [{"name": item.name, "identity": layout.identity(item)} for item in (root/relative).iterdir()]}
        summary = ["Создать папку заказа из интерфейса.", "Название: " + title]
        if not title_only:
            summary.insert(1, "Дата: " + order_date)
        session = plan.create_session(summary, before)
        if store:
            import order_creation
            order_creation.prepare(store, path, title, session)
        applied = False
        registered = False
        try:
            layout.apply(session)
            applied = True
            if store:
                order_creation.register(store, path)
                registered = True
            layout.save_json(session / ".result.json", {"status": "created", "path": path, "identity": layout.identity(destination)})
        except Exception as error:
            if store:
                order_creation.failed(store, path, error)
            try:
                layout.save_json(session / ".result.json", {"status": "failed", "path": path, "error": str(error)})
            except OSError:
                pass
            if isinstance(error, FileExistsError):
                raise OrderFolderConflict("Путь уже занят. Существующие данные сохранены") from error
            if store and applied and not registered:
                raise OrderFolderConflict("Папка создана, но карточка пока не сохранена: " + path + ". Регистрация повторится автоматически в течение минуты; не создавай вторую папку. " + str(error)) from error
            raise
    return {"path": path, "name": name, "journal": session.relative_to(root).as_posix(), "registered": bool(store)}
