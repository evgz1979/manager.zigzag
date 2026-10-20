"""Переносы папок без перезаписи, с устойчивым журналом и обратными операциями."""
import argparse
import ctypes
import errno
import fcntl
import json
import os
import shutil
import stat
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


def identity(path):
    value = Path(path).lstat()
    return {"device": value.st_dev, "inode": value.st_ino, "kind": stat.S_IFMT(value.st_mode)}


def exists(path):
    return os.path.lexists(path)


def rename_exclusive(source, destination):
    function = ctypes.CDLL(None, use_errno=True).renamex_np
    function.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint)
    function.restype = ctypes.c_int
    if function(os.fsencode(source), os.fsencode(destination), 0x00000004):
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(destination))


def append(session, record):
    record = {"time": datetime.now(ZoneInfo("Europe/Moscow")).isoformat(), **record}
    with (Path(session) / ".journal.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def save_json(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def safe_path(root, relative, clients, *, service_roots=()):
    relative = Path(relative)
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise ValueError("Путь должен находиться внутри корня документов")
    first = relative.parts[0]
    service_allowed = any(relative == Path(prefix) or Path(prefix) in relative.parents for prefix in service_roots)
    if first not in clients or first.startswith(".") or (first.startswith("#") and not service_allowed):
        raise ValueError("Папка вне согласованной области переносов")
    for index in range(1, len(relative.parts) + 1):
        if (root / Path(*relative.parts[:index])).is_symlink():
            raise ValueError("Символические ссылки не перемещаются")
    return root / relative


class Plan:
    def __init__(self, root, clients, *, service_roots=()):
        self.root = Path(root).resolve()
        self.clients = clients
        self.service_roots = list(service_roots)
        self.operations = []
        self.directories = set()

    def mkdir(self, relative):
        relative = Path(relative).as_posix()
        if relative in self.directories:
            return
        path = safe_path(self.root, relative, self.clients, service_roots=self.service_roots)
        if exists(path):
            if not path.is_dir():
                raise FileExistsError(path)
            return
        self.operations.append({"operation": "mkdir", "destination": relative})
        self.directories.add(relative)

    def move(self, source, destination, reason, origin=None):
        source, destination = Path(source).as_posix(), Path(destination).as_posix()
        if source == destination:
            return
        original = safe_path(self.root, origin or source, self.clients, service_roots=self.service_roots)
        target = safe_path(self.root, destination, self.clients, service_roots=self.service_roots)
        if exists(target):
            raise FileExistsError(target)
        if len(os.fsencode(target.name)) > 255:
            raise ValueError("Слишком длинное имя: " + destination)
        self.operations.append({"operation": "move", "source": source, "destination": destination,
                                "identity": identity(original), "reason": reason})

    def create_session(self, notes, before):
        history = self.root / ".folder-layout-history"
        if history.is_symlink():
            raise ValueError("Каталог журнала не должен быть ссылкой")
        history.mkdir(exist_ok=True)
        stamp = datetime.now(ZoneInfo("Europe/Moscow")).strftime("%Y-%m-%d_%H-%M-%S_%f")
        session = history / ("." + stamp)
        session.mkdir()
        plan = {"root": str(self.root), "clients": self.clients, "operations": self.operations, "notes": notes}
        if self.service_roots:
            plan["service_roots"] = self.service_roots
        if getattr(self, "database_paths", False):
            plan["database_paths"] = True
        save_json(session / ".plan.json", plan)
        save_json(session / ".before.json", before)
        shutil.copyfile(__file__, session / ".folder-layout.py")
        lines = ["Журнал раскладки папок", "", "Корень: " + str(self.root), "",
                 "Каждый перенос записывается до и после операции в .journal.jsonl.",
                 "Файлы не перезаписываются. Содержимое событий и служебных папок переносится целиком.",
                 "Даты с 00 приблизительные; основания для дат записаны у каждого переноса.", "",
                 "Откат сначала показывает список действий:",
                 (f'python3 "{session / ".restore.py"}" "{session}"' if plan.get("database_paths") else f'python3 "{session / ".folder-layout.py"}" undo "{session}"'),
                 "Для выполнения отката добавьте --apply. Новые файлы не перезаписываются и не удаляются.", "",
                 *notes, "", "ПЛАН:"]
        for index, operation in enumerate(self.operations, 1):
            lines += [f'{index}. {operation["operation"]}: {operation.get("source", "")} -> {operation["destination"]}',
                      "   " + operation.get("reason", "Создать каталог")]
        (session / ".report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        append(session, {"phase": "session_created", "operations": len(self.operations)})
        return session


def load_plan(session):
    return json.loads((Path(session) / ".plan.json").read_text(encoding="utf-8"))


def records(session):
    lines = (Path(session) / ".journal.jsonl").read_text(encoding="utf-8").splitlines(keepends=True)
    return [json.loads(line) for line in lines if line.endswith("\n")]


def apply(session):
    session = Path(session)
    plan = load_plan(session)
    root = Path(plan["root"])
    with (session / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if any(record["phase"] == "intent" for record in records(session)):
            raise ValueError("Этот план уже запускался; сначала проверьте журнал или выполните откат")
        for index, operation in enumerate(plan["operations"], 1):
            target = safe_path(root, operation["destination"], plan["clients"], service_roots=plan.get("service_roots", ()))
            append(session, {"phase": "intent", "id": index, **operation})
            changed = False
            try:
                if exists(target):
                    raise FileExistsError(target)
                if operation["operation"] == "mkdir":
                    target.mkdir()
                else:
                    source = safe_path(root, operation["source"], plan["clients"], service_roots=plan.get("service_roots", ()))
                    if identity(source) != operation["identity"]:
                        raise ValueError("Исходная папка или файл изменились: " + str(source))
                    rename_exclusive(source, target)
                changed = True
                append(session, {"phase": "commit", "id": index, "identity": identity(target)})
            except BaseException as problem:
                append(session, {"phase": "failed", "id": index, "error": str(problem), "changed": changed,
                                 "identity": identity(target) if changed else None})
                raise
        append(session, {"phase": "complete", "operations": len(plan["operations"])})


def undo(session, perform=False, *, coordinate_database=False):
    session = Path(session)
    plan = load_plan(session)
    if perform and plan.get("database_paths") and not coordinate_database:
        raise ValueError("Эта операция меняет пути базы. Используйте .restore.py из этого же журнала")
    root = Path(plan["root"])
    with (session / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        journal = records(session)
        intents = {item["id"]: item for item in journal if item["phase"] == "intent"}
        commits = {item["id"]: item for item in journal if item["phase"] == "commit"}
        reverted = {item["id"] for item in journal if item["phase"] == "undone"}
        failed = {item["id"]: item for item in journal if item["phase"] == "failed"}
        if not perform:
            return sum(index not in reverted and not (index in failed and not failed[index].get("changed"))
                       for index in intents)
        count = 0
        for index, operation in reversed(list(intents.items())):
            if index in reverted or (index in failed and not failed[index].get("changed")):
                continue
            target = safe_path(root, operation["destination"], plan["clients"], service_roots=plan.get("service_roots", ()))
            expected = commits.get(index, {}).get("identity") or failed.get(index, {}).get("identity") or operation.get("identity")
            source = safe_path(root, operation["source"], plan["clients"], service_roots=plan.get("service_roots", ())) if operation["operation"] == "move" else None
            if source and exists(source) and identity(source) == expected and not exists(target):
                continue
            if not expected or not exists(target) or identity(target) != expected:
                raise ValueError("Откат остановлен: объект изменён или перемещён: " + str(target))
            if source and exists(source):
                raise FileExistsError("Откат не перезапишет существующий путь: " + str(source))
            if source is None and any(target.iterdir()):
                raise OSError(errno.ENOTEMPTY, "Новый каталог не пуст; откат сохранит новые данные", str(target))
            count += 1
            if perform:
                append(session, {"phase": "undo_intent", "id": index})
                if source:
                    rename_exclusive(target, source)
                else:
                    target.rmdir()
                append(session, {"phase": "undone", "id": index})
        if perform:
            append(session, {"phase": "undo_complete", "operations": count})
        return count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("apply", "undo"))
    parser.add_argument("session", type=Path)
    parser.add_argument("--apply", action="store_true", dest="perform")
    arguments = parser.parse_args()
    if arguments.action == "apply":
        if not arguments.perform:
            print(json.dumps(load_plan(arguments.session), ensure_ascii=False, indent=2))
        else:
            apply(arguments.session)
    else:
        print("Обратных операций:", undo(arguments.session, arguments.perform))
