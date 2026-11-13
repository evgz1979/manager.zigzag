#!/usr/bin/env python3
"""Полный перенос рабочей установки на MacBook и обратно."""
import argparse
import configparser
import fcntl
import json
import os
from pathlib import Path
import plistlib
import shlex
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import uuid
import zipfile

import deploy_remote as deployment
from handoff_host import Bundle, Installation, CONNECTOR, HELPER, RELEASE, TUNNEL

APP = Path(__file__).resolve().parents[1]


# Выполняет одну команду штатного помощника на M4 с проверкой ключа SSH.
# Пакет с закрытыми файлами передаётся напрямую по потокам файлов.
def remote(settings, action, *arguments, source=None, target=None):
    helper = str(Path(settings["directory"]) / "current/scripts/handoff_host.py")
    command = shlex.join([settings["python"], helper, json.dumps(settings, ensure_ascii=False), action, *arguments])
    result = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
                             "-o", "ConnectTimeout=10", settings["ssh"], command],
                            stdin=source if source is not None else subprocess.DEVNULL,
                            stdout=target if target is not None else subprocess.PIPE, check=True)
    return json.loads(result.stdout) if target is None else None


# Готовит MacBook с точной версией M4, штатным запуском и нативными помощниками.
# Рабочая база и закрытые настройки не нужны для этой стадии.
def prepare(local, settings, home_state):
    if home_state["parked"] or not home_state["manager"] or not home_state["tunnel"]:
        raise RuntimeError("Подготовка доступна, когда менеджер и туннель работают на M4")
    if home_state["documents"] != str(local.documents) or not local.documents.is_dir():
        raise RuntimeError("На MacBook нужен тот же корень «Зигзаг» в iCloud Drive")
    if not any(item.is_dir() and not item.name.startswith(".") for item in local.documents.iterdir()):
        raise RuntimeError("Дерево «Зигзаг» на MacBook ещё недоступно")
    if home_state["public_host"] != "manager.actu.cc" or home_state["remote_port"] != 18767:
        raise RuntimeError("Параметры защищённого входа на M4 изменились")
    if not RELEASE.fullmatch(home_state["release"]):
        raise RuntimeError("Неизвестный номер релиза M4")
    with socket.create_connection(("127.0.0.1", 10808), timeout=3):
        pass

    with local.lock():
        state = local.status()
        if state["manager"] or state["tunnel"]:
            raise RuntimeError("На MacBook уже запущен менеджер или туннель")
        local.data.mkdir(exist_ok=True)
        with local.stopped(home_state["remote_port"]):
            local.stop_job(deployment.LABEL)
            local.stop_job(TUNNEL)
            deployment.write_json(local.parked, {"id": "prepared"})
        config = ("[storage]\nroot = " + str(local.documents) +
                  f"\n\n[server]\nhost = {local.host}\nport = {local.port}\n" +
                  "\n[remote_access]\nenabled = true\npublic_host = manager.actu.cc\nport = 18767\n")
        deployment.atomic_write(local.root / "manager.ini", config.encode())
        release = home_state["release"]
        if state["release"] != release or not (local.current / "scripts/handoff_host.py").is_file():
            with tempfile.TemporaryDirectory(dir=local.root) as temporary:
                stage = Path(temporary)
                with tempfile.TemporaryFile(dir=stage) as package:
                    remote(settings, "prepare", target=package)
                    package.seek(0)
                    with zipfile.ZipFile(package) as archive:
                        received = Bundle.read(archive, stage,
                                               lambda name: name.startswith("application/") or name in {"connector", "helper"})
                app = stage / "application"
                manifest = json.loads((app / ".manifest.json").read_text())
                if (received["release"] != release or manifest["release"] != release
                        or (app / ".release-id").read_text().strip() != release
                        or set(received["files"]) != {"application/" + name for name in manifest["files"]}
                        | {"application/.manifest.json", "application/.release-id", "connector", "helper"}
                        or any(received["files"]["application/" + name] != digest
                               for name, digest in manifest["files"].items())):
                    raise RuntimeError("Состав релиза на MacBook отличается от действующего M4")
                (app / "data").symlink_to(local.data)
                (app / "manager.ini").symlink_to(local.root / "manager.ini")
                target = local.root / ".releases" / release
                target.parent.mkdir(exist_ok=True)
                if target.exists():
                    target = target.with_name(release + "-" + uuid.uuid4().hex[:8])
                app.rename(target)
                deploy_connector(local, stage)
                temporary_link = local.root / ".handoff-current"
                temporary_link.unlink(missing_ok=True)
                temporary_link.symlink_to(target.relative_to(local.root))
                temporary_link.replace(local.current)
        deployment.prepare_renderers({"python": local.python}, local.current.resolve())
        launcher = deployment.prepare_launcher(local.current.resolve(), local.root, local.documents)
        write_agents(local, launcher)
    print("MacBook подготовлен. Рабочий менеджер продолжает работать на M4.", flush=True)


# Устанавливает проверенный бинарник и помощник в пути действующего коннектора.
# Оставляет уже имеющийся одноимённый файл, если его содержимое совпадает.
def deploy_connector(local, stage):
    for source, destination, mode in ((stage / "connector", local.home / CONNECTOR, 0o700),
                                      (stage / "helper", local.support / HELPER, 0o600)):
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.is_symlink() or (destination.exists() and destination.read_bytes() != source.read_bytes()):
            raise RuntimeError("Занят путь установки коннектора на MacBook: " + str(destination))
        if not destination.exists():
            with destination.open("xb") as output:
                with source.open("rb") as stream:
                    shutil.copyfileobj(stream, output)
        destination.chmod(mode)
    subprocess.run([str(local.home / CONNECTOR), "--version"], stdout=subprocess.DEVNULL, check=True, timeout=10)


# Сохраняет штатные пользовательские задания MacBook без их запуска.
# Оба задания устанавливаются только на подготовленной выключенной машине.
def write_agents(local, launcher):
    local.agents.mkdir(parents=True, exist_ok=True)
    logs = local.home / "Library/Logs/ZigzagManager"
    logs.mkdir(parents=True, exist_ok=True)
    for label, command, log in (
        (deployment.LABEL, [str(launcher), local.python, str(local.current / "server.py"), str(local.documents)], "travel-server"),
        (TUNNEL, [local.python, str(local.support / HELPER)], "travel-tunnel"),
    ):
        agent = {"Label": label, "ProgramArguments": command, "WorkingDirectory": str(local.home),
                 "RunAtLoad": True, "KeepAlive": True, "ThrottleInterval": 10,
                 "EnvironmentVariables": {"PYTHONDONTWRITEBYTECODE": "1"},
                 "StandardOutPath": str(logs / (log + ".log")), "StandardErrorPath": str(logs / (log + "-error.log"))}
        deployment.atomic_write(local.agents / (label + ".plist"), plistlib.dumps(agent))


# Уточняет готовность общей папки перед остановкой источника.
# При повторе уже начатой передачи используется сохранённый номер и прежнее подтверждение.
def confirm(target):
    answer = input("Проверь в Finder, что «Зигзаг» синхронизирован на обеих машинах. "
                   f"Для переключения на {target} введи ДА: ")
    if answer.strip() != "ДА":
        raise RuntimeError("Переключение отменено")


# Переносит базу на MacBook с продолжением по тому же номеру после обрыва.
# Каждый номер принимается ровно один раз, включая повтор после запуска.
def leave(local, settings, state_file, state):
    if state is None or state["phase"] == "returned":
        home = remote(settings, "status")
        prepare(local, settings, home)
        confirm("MacBook")
        state = {"phase": "leaving", "trip": uuid.uuid4().hex}
        deployment.write_json(state_file, state)
    if state["phase"] == "away":
        local.check_active()
        subprocess.run(["/usr/bin/open", f"http://127.0.0.1:{local.port}"], check=False)
        print("Рабочий менеджер уже на MacBook.")
        return
    if state["phase"] != "leaving":
        raise RuntimeError("Сначала заверши возврат на M4")
    trip = state["trip"]
    history = local.history(trip)
    history.mkdir(parents=True, exist_ok=True)
    if not (history / "installed.json").exists():
        with tempfile.TemporaryFile(dir=history) as package:
            print("Останавливаю M4 и получаю проверенный снимок SQLite…", flush=True)
            remote(settings, "freeze", trip, trip, target=package)
            package.seek(0)
            local.activate(trip, trip, package)
    else:
        local.activate(trip, trip, None)
    deployment.write_json(state_file, {**state, "phase": "away"})
    subprocess.run(["/usr/bin/open", f"http://127.0.0.1:{local.port}"], check=False)
    print("Рабочий менеджер на MacBook. Внешний вход проверен.")


# Передаёт свежий снимок с MacBook на остановленный M4.
# После сбоя повторяет прежнюю передачу и сохраняет записи уже запущенного M4.
def back(local, settings, state_file, state):
    if state is None or state["phase"] == "returned":
        remote(settings, "check")
        print("Рабочий менеджер на M4.")
        return
    if state["phase"] == "away":
        home = remote(settings, "status")
        if not home["parked"] or home["parked"]["id"] != state["trip"] or home["manager"] or home["tunnel"]:
            raise RuntimeError("M4 не остановлен для этой поездки")
        confirm("M4")
        state = {**state, "phase": "returning", "return_id": uuid.uuid4().hex}
        deployment.write_json(state_file, state)
    if state["phase"] != "returning":
        raise RuntimeError("Сначала заверши передачу на MacBook")
    print("Останавливаю MacBook и передаю свежий снимок на M4…", flush=True)
    with local.freeze(state["return_id"], state["trip"]).open("rb") as source:
        remote(settings, "activate", state["return_id"], state["trip"], source=source)
    deployment.write_json(state_file, {**state, "phase": "returned"})
    print("Рабочий менеджер на M4. Внешний вход проверен.")


# Выбирает действие и защищает весь цикл переключения от запуска второй команды.
# Состояние хранится на внутреннем диске MacBook вне проекта и iCloud.
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("status", "prepare", "to-macbook", "to-m4"))
    action = parser.parse_args().action
    config = configparser.ConfigParser(interpolation=None)
    config.read(APP / "deploy.ini", encoding="utf-8")
    settings = dict(config["m4"])
    local = Installation(config["macbook"], settings["documents"], "macbook")
    state_file = local.root / ".handoff-trip.json"
    if action == "status":
        state = json.loads(state_file.read_text()) if state_file.exists() else None
        try:
            home = remote(settings, "status")
        except subprocess.CalledProcessError:
            home = {"reachable": False}
        print(json.dumps({"trip": state, "macbook": local.status(), "m4": home}, ensure_ascii=False, indent=2))
        return
    os.umask(0o077)
    local.root.mkdir(parents=True, exist_ok=True)
    with (local.root / ".handoff-command.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = json.loads(state_file.read_text()) if state_file.exists() else None
        if action == "prepare":
            if state and state["phase"] != "returned":
                raise RuntimeError("Передача уже началась. Повтори команду текущего направления.")
            prepare(local, settings, remote(settings, "status"))
        elif action == "to-macbook":
            leave(local, settings, state_file, state)
        else:
            back(local, settings, state_file, state)


if __name__ == "__main__":
    try:
        main()
    except (OSError, EOFError, ValueError, RuntimeError, sqlite3.Error, subprocess.SubprocessError, zipfile.BadZipFile, KeyError) as error:
        print(f"Передача остановлена: {error}", file=sys.stderr)
        sys.exit(1)
