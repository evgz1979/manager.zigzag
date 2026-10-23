"""Нумерованные события заказа: создание и подтверждённое исправление имён."""
import hashlib
import json
import os
import re
import shutil
import sqlite3
import stat
import unicodedata
from pathlib import Path

import event_folder_undo as restore
import folder_layout as layout
import folder_notes
from folder_structure import folder_role, dated, is_service_folder, is_freza_task
from order_folders import LOCK, layout_scope

NUMBER = re.compile(r"^([0-9]+)(?=$|[\s\-–—])")
CANONICAL = re.compile(r"^([0-9]{2,}) - (\S(?:.*\S)?)$")


class EventFolderConflict(ValueError):
    pass


def event_number(name):
    return None if dated(name) else NUMBER.match(name)


def parent(root, relative):
    if isinstance(relative, str) and is_freza_task(relative):
        raise ValueError("В задании на фрезеровку события не нужны. Добавляй файлы прямо в задание")
    if not isinstance(relative, str) or not Path(relative).parts or any(part.startswith(".") for part in Path(relative).parts) or is_service_folder(relative):
        raise ValueError("Выберите папку заказа")
    target = layout.safe_path(root, relative, [Path(relative).parts[0]], **layout_scope(relative))
    if not target.is_dir():
        raise FileNotFoundError("Папка заказа недоступна")
    if folder_role(root, relative)["folderKind"] != "order":
        raise ValueError("Событие создаётся непосредственно в папке заказа")
    return target


def title_name(number, title):
    if not isinstance(title, str) or any(c in '/\\:' or ord(c) < 32 or ord(c) == 127 for c in title):
        raise ValueError("Название события должно быть в одну строку, без /, \\ и :")
    title = unicodedata.normalize("NFC", title.strip())
    if not title:
        raise ValueError("Укажите название события")
    name = f"{number:02d} - {title}"
    if len(os.fsencode(name)) > 255:
        raise ValueError("Сократите название события: имя папки слишком длинное")
    return name


def snapshot(target):
    children = []
    for item in target.iterdir():
        if item.name.startswith("."):
            continue
        children.append({"name": item.name, "identity": layout.identity(item)})
    children.sort(key=lambda item: (unicodedata.normalize("NFC", item["name"]).casefold(), item["name"]))
    return {"parent": layout.identity(target), "children": children}


def preview(root, relative, notes=None):
    root = Path(root).resolve()
    target = parent(root, relative)
    if notes and notes.store.database.exists():
        with notes.connect() as db:
            restore.assert_unlocked(db, relative, include_children=True)
    before = snapshot(target)
    events = [item["name"] for item in before["children"] if not item["name"].startswith("#")
              and item["identity"]["kind"] == stat.S_IFDIR]
    events.sort(key=lambda name: (int(event_number(name)[1]) if event_number(name) else float("inf"),
                                 unicodedata.normalize("NFC", name).casefold(), name))
    maximum = max((int(event_number(name)[1]) for name in events if event_number(name)), default=-1)
    used, canonical = set(), set()
    for name in events:
        match = CANONICAL.fullmatch(name)
        if match and match[1] == f"{int(match[1]):02d}" and int(match[1]) not in used:
            canonical.add(name)
            used.add(int(match[1]))
    suggestions = []
    next_number = maximum + 1
    for name in events:
        if name in canonical:
            continue
        match = event_number(name)
        candidate = int(match[1]) if match else None
        number = candidate if candidate is not None and candidate not in used else next_number
        used.add(number)
        next_number = max(next_number, number + 1)
        # Составной номер 00-01 сохраняется в названии, его смысл не угадываем.
        compound = re.match(r"^[0-9]{2,}-[0-9]{2,}", name)
        title = name[match.end():].strip(" -–—") if match and not compound else name
        suggestions.append({"source": name, "number": f"{number:02d}", "title": title,
                            "name": f"{number:02d} - {title}" if title else "",
                            "reason": "Нет названия события" if not title else "Привести имя и номер к формату события"})
    fingerprint = {"parent": before["parent"], "directories": [item for item in before["children"]
                   if item["identity"]["kind"] in (stat.S_IFDIR, stat.S_IFLNK)]}
    return {"path": relative, "revision": hashlib.sha256(json.dumps(fingerprint, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
            "next_number": f"{maximum + 1:02d}", "suggestions": suggestions, "before": before}


def current(root, payload, notes=None):
    result = preview(root, payload.get("path"), notes)
    if result["revision"] != payload.get("revision"):
        raise EventFolderConflict("Состав папки заказа изменился. Обновите предложение и проверьте имена ещё раз")
    return result


def create(root, payload, notes=None):
    root = Path(root).resolve()
    with LOCK:
        view = current(root, payload, notes)
        name = title_name(int(view["next_number"]), payload.get("title"))
        relative = str(Path(view["path"]) / name)
        destination = root / relative
        if layout.exists(destination):
            raise EventFolderConflict("Папка или файл с таким именем уже существует. Измените название события")
        plan = layout.Plan(root, [Path(relative).parts[0]], **layout_scope(relative))
        plan.mkdir(relative)
        session = plan.create_session(["Создать событие заказа", "Имя: " + name], view["before"])
        try:
            if layout.identity(destination.parent) != view["before"]["parent"]:
                raise EventFolderConflict("Папка заказа перемещена. Откройте её заново")
            layout.apply(session)
            layout.save_json(session / ".result.json", {"status": "created", "path": relative, "identity": layout.identity(destination)})
        except Exception as error:
            layout.save_json(session / ".result.json", {"status": "failed", "error": str(error)})
            if isinstance(error, FileExistsError):
                raise EventFolderConflict("Путь уже занят; существующие данные сохранены") from error
            raise
        return {"path": relative, "name": name, "journal": session.relative_to(root).as_posix()}


def rename(notes, payload):
    if payload.get("confirmed") is not True:
        raise ValueError("Подтвердите переименование по показанному списку")
    root = notes.store.root.resolve()
    with LOCK, folder_notes.SYNC_LOCK, notes.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        view = current(root, payload)
        restore.assert_unlocked(db, view["path"], include_children=True)
        supplied = payload.get("names")
        if not isinstance(supplied, list) or len(supplied) != len(view["suggestions"]) or not supplied:
            raise ValueError("Обновите список предлагаемых переименований")
        by_source = {item.get("source"): item.get("title") for item in supplied if isinstance(item, dict) and isinstance(item.get("source"), str)}
        if set(by_source) != {item["source"] for item in view["suggestions"]}:
            raise ValueError("Список папок изменён. Обновите предложение")
        plan = layout.Plan(root, [Path(view["path"]).parts[0]], **layout_scope(view["path"]))
        plan.database_paths = True
        mappings = []
        for item in view["suggestions"]:
            source = str(Path(view["path"]) / item["source"])
            destination = str(Path(view["path"]) / title_name(int(item["number"]), by_source[item["source"]]))
            restore.assert_unlocked(db, source)
            restore.assert_unlocked(db, destination)
            if layout.exists(root / destination):
                raise EventFolderConflict("Предлагаемое имя уже занято: " + destination)
            plan.move(source, destination, "Подтверждённое исправление имени события")
            mappings.append({"source": source, "destination": destination})
            restore.metadata_paths(db,source,destination)
        roots = [pair[key] for pair in mappings for key in ("source", "destination")]
        if any(restore.inside(row[0], prefix) for row in db.execute("SELECT path FROM orders") for prefix in roots):
            raise EventFolderConflict("Во вложенной папке есть прежняя запись заказа. Для неё нужен отдельный перенос с проверкой регистрации")
        rows = db.execute("SELECT * FROM folder_notes").fetchall()
        changes = []
        for row in rows:
            for pair in mappings:
                if restore.inside(row["path"], pair["destination"]):
                    raise EventFolderConflict("По новому пути уже сохранена другая заметка: " + row["path"])
                if restore.inside(row["path"], pair["source"]):
                    if not notes.store.database_only and row["revision"] != row["exported_revision"]:
                        raise EventFolderConflict("Сначала дождитесь выгрузки заметок и задач этой папки: " + row["path"])
                    changes.append((pair["destination"] + row["path"][len(pair["source"]):], row["id"]))
                    break
        restore.schema(db)
        session = plan.create_session(["Переименовать события по подтверждённому списку.",
            "Для этой операции используйте .restore.py: обычный откат раскладки не обновляет пути базы."], view["before"])
        layout.save_json(session / ".event-paths.json", {"database": str(notes.store.database.resolve()), "mappings": mappings})
        shutil.copyfile(Path(restore.__file__), session / ".restore.py")
        db.execute("INSERT INTO event_renames(session,state,mappings) VALUES (?, 'pending', ?)", (str(session), json.dumps(mappings, ensure_ascii=False)))
        db.commit()  # Устойчивая блокировка старых и новых путей до первого переноса.
        try:
            db.execute("BEGIN IMMEDIATE")
            layout.apply(session)
            for destination, identity in changes:
                db.execute("UPDATE folder_notes SET path=?,revision=revision+1,exported_revision=exported_revision+1 WHERE id=?", (destination, identity))
            for pair in mappings:
                restore.metadata_paths(db,pair["source"],pair["destination"],apply=True)
            db.execute("UPDATE event_renames SET state='complete',paths_applied=1 WHERE session=?", (str(session),))
            db.commit()
        except Exception as error:
            db.rollback()
            try:
                restore.undo(session, True)
            except (OSError, ValueError, sqlite3.Error) as undo_error:
                layout.append(session, {"phase": "rollback_failed", "error": str(undo_error)})
                raise EventFolderConflict("Переименование остановлено, данные сохранены. Нужен откат из журнала: " + str(session)) from error
            layout.save_json(session / ".result.json", {"status": "rolled_back", "error": str(error)})
            raise EventFolderConflict("Переименование отменено после ошибки; исходные пути восстановлены: " + str(error)) from error
        layout.save_json(session / ".result.json", {"status": "renamed", "mappings": mappings})
        return {"path": view["path"], "renamed": mappings, "journal": session.relative_to(root).as_posix()}
