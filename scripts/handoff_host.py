"""Принимает и передаёт рабочую установку менеджера между двумя Mac."""
import configparser
from contextlib import closing, contextmanager
import fcntl
import hashlib
import http.client
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile

import deploy_remote as deployment

TUNNEL = deployment.LABEL + ".tunnel"
SUPPORT = Path(".local/share/manager-remote-access")
STATE = ".handoff-parked.json"
PROFILE = "password.json"
TOKEN = "cloudflared/token"
HELPER = "cloudflared/connector-via-existing-proxy.py"
CONNECTOR = Path(".local/bin/cloudflared")
TELEGRAM = ("telegram.ini", "telegram-actu-disabled.ini")
RELEASE = re.compile(r"[0-9]{8}T[0-9]{6}Z-[a-f0-9]{8}")
TRANSFER = re.compile(r"[0-9a-f]{32}")


# Считывает и записывает ZIP одного направления без распаковки произвольных путей.
# Получатель проверяет SHA-256 всех файлов и допускает только ожидаемый состав.
class Bundle:
    # Вычисляет SHA-256 содержимого небольшого файла или открытого потока.
    # Читает блоками по одному мегабайту до конца потока.
    @staticmethod
    def digest(stream):
        value = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
        return value.hexdigest()

    # Записывает закрытый ZIP с SHA-256 и публикует его атомарно.
    # Незавершённый временный файл можно заменить при повторе операции.
    @classmethod
    def write(cls, path, metadata, files):
        temporary = path.with_suffix(".partial")
        checksums = {}
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, source in files.items():
                with source.open("rb") as stream:
                    checksums[name] = cls.digest(stream)
                archive.write(source, name)
            archive.writestr("handoff.json", json.dumps({**metadata, "files": checksums}, ensure_ascii=False))
        os.chmod(temporary, 0o600)
        with temporary.open("rb") as stream:
            os.fsync(stream.fileno())
        temporary.replace(path)

    # Извлекает только разрешённые обычные файлы в отдельную закрытую папку.
    # Проверяет состав, пути, типы, размер и хеш каждого распакованного файла.
    @classmethod
    def read(cls, archive, directory, allowed):
        metadata = json.loads(archive.read("handoff.json"))
        files = metadata["files"]
        names = set(archive.namelist())
        if len(names) != len(archive.infolist()) or names != set(files) | {"handoff.json"}:
            raise RuntimeError("Неверный состав пакета передачи")
        if any(not allowed(name) for name in files):
            raise RuntimeError("Неожиданный путь в пакете передачи")
        if sum(item.file_size for item in archive.infolist()) > shutil.disk_usage(directory).free:
            raise RuntimeError("Не хватает места для распаковки пакета передачи")
        for name, expected in files.items():
            if any(part in ("", ".", "..") for part in name.split("/")):
                raise RuntimeError("Недопустимый путь в пакете передачи")
            target = directory / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(name) as source, target.open("xb") as stream:
                shutil.copyfileobj(source, stream, length=1024 * 1024)
                stream.flush()
                os.fsync(stream.fileno())
            with target.open("rb") as stream:
                if cls.digest(stream) != expected:
                    raise RuntimeError("Не совпала контрольная сумма: " + name)
            os.chmod(target, 0o600)
        return metadata


# Управляет одной рабочей установкой и её сохранёнными этапами передачи.
# Использует существующие launchd, SQLite-снимки, настройки и релизы.
class Installation:
    # Определяет локальные пути, порты, роль машины и имя SQLite.
    # MacBook и M4 должны использовать одинаковый абсолютный путь iCloud.
    def __init__(self, settings, documents, role):
        self.root = Path(settings["directory"]).expanduser().resolve()
        self.documents = Path(documents).expanduser().resolve()
        self.python = settings["python"]
        self.port = int(settings["port"])
        self.host = settings["host"]
        self.role = role
        self.data = self.root / "data"
        self.database = self.data / deployment.database_name(self.documents)
        self.parked = self.root / STATE
        self.current = self.root / "current"
        self.home = Path.home()
        self.support = self.home / SUPPORT
        self.domain = "gui/" + str(os.getuid())
        self.agents = self.home / "Library/LaunchAgents"

    # Возвращает папку передачи по проверенному идентификатору.
    # Вызывать после блокировки установки при записи.
    def history(self, identity):
        if not TRANSFER.fullmatch(identity):
            raise ValueError("Неизвестный номер передачи")
        return self.root / ".handoffs" / identity

    # Защищает операции с установкой от параллельного деплоя и другой передачи.
    # Запись выполняется под закрытой маской файлов и общей блокировкой.
    @contextmanager
    def lock(self):
        os.umask(0o077)
        self.root.mkdir(parents=True, exist_ok=True)
        with (self.root / ".deploy.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield

    # Читает текущее состояние установки и параметры защищённого слушателя.
    # Удалённый ответ содержит только проверенные эксплуатационные поля.
    def status(self):
        config = configparser.ConfigParser(interpolation=None)
        config.read(self.root / "manager.ini", encoding="utf-8")
        release_file = self.current / ".release-id"
        return {"documents": str(self.documents), "directory": str(self.root),
                "release": release_file.read_text().strip() if release_file.is_file() else "",
                "parked": json.loads(self.parked.read_text()) if self.parked.exists() else None,
                "manager": self.loaded(deployment.LABEL),
                "tunnel": self.loaded(TUNNEL),
                "public_host": config.get("remote_access", "public_host", fallback=""),
                "remote_port": config.getint("remote_access", "port", fallback=0),
                "configured_remote": config.getboolean("remote_access", "enabled", fallback=False),
                "config_root": str(Path(config.get("storage", "root", fallback="/")).expanduser().resolve())}

    # Проверяет регистрацию заданного задания launchd текущего пользователя.
    # Использует только метки менеджера и его туннеля.
    def loaded(self, label):
        return deployment.launchctl("print", self.domain + "/" + label, check=False).returncode == 0

    # Печатает состояние сетевых входов для проверки перед передачей.
    # Требует подтверждения точного релиза и обоих защищённых маршрутов.
    def check_active(self):
        state = self.status()
        if state["parked"] or not state["manager"] or not state["tunnel"]:
            raise RuntimeError("Установка не активна")
        self.check_service(state)
        self.check_public(state)
        return state

    # Отключает автоматический запуск, выгружает задание и ждёт его остановки.
    # Сохраняет plist для следующего переключения.
    def stop_job(self, label):
        key = self.domain + "/" + label
        deployment.launchctl("disable", key)
        if self.loaded(label):
            deployment.launchctl("bootout", key)
        for _ in range(100):
            if not self.loaded(label):
                return
            time.sleep(0.1)
        raise RuntimeError("Не остановилось задание " + label)

    # Запускает существующее задание launchd, если оно ещё не загружено.
    # Состояние enable сохраняется для входа в сеанс macOS.
    def start_job(self, label):
        if not self.loaded(label):
            deployment.launchctl("enable", self.domain + "/" + label)
            deployment.launchctl("bootstrap", self.domain, str(self.agents / (label + ".plist")))

    # Проверяет, что ни один прежний сервер не удерживает SQLite или сетевой порт.
    # Блокировка остаётся у вызывающего кода на весь период остановки или установки базы.
    @contextmanager
    def stopped(self, remote_port, *, drain=False):
        with (self.data / ".handoff-run.lock").open("a") as lock:
            if drain and self.loaded(deployment.LABEL):
                deployment.launchctl("disable", self.domain + "/" + deployment.LABEL)
                deployment.launchctl("kill", "SIGTERM", self.domain + "/" + deployment.LABEL, check=False)
            deadline = time.monotonic() + 90
            while True:
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        raise RuntimeError("Прежний процесс менеджера ещё удерживает рабочую установку") from None
                    time.sleep(0.1)
            if drain:
                self.stop_job(deployment.LABEL)
            for port in (self.port, remote_port):
                with socket.socket() as probe:
                    if port and probe.connect_ex(("127.0.0.1", port)) == 0:
                        raise RuntimeError(f"Порт {port} всё ещё занят")
            yield

    # Проверяет, что активная база соответствует пути в конфигурации приложения.
    # Обнаруживает отсутствующую базу до остановки рабочего сервера.
    def check_source(self, state):
        if not RELEASE.fullmatch(state["release"]) or state["config_root"] != str(self.documents):
            raise RuntimeError("Настройки документов или релиз источника изменились")
        if not self.database.is_file() or self.database.is_symlink():
            raise RuntimeError("Рабочая база отсутствует или заменена ссылкой")

    # Проверяет рабочий корень и исходные файлы активного релиза перед переездом.
    # Отправляет только файлы, перечисленные в проверенном манифесте деплоя.
    def bootstrap(self, output):
        state = self.status()
        release = state["release"]
        if state["parked"] or not state["manager"] or not state["tunnel"] or not RELEASE.fullmatch(release):
            raise RuntimeError("На M4 нет активной установки для подготовки")
        if state["config_root"] != str(self.documents) or not self.documents.is_dir():
            raise RuntimeError("Рабочий корень на M4 отличается от настроек")
        manifest_path = self.current / ".manifest.json"
        manifest = json.loads(manifest_path.read_text())
        if manifest["release"] != release or not (self.current / "scripts/handoff_host.py").is_file():
            raise RuntimeError("На M4 нужен релиз с поддержкой передачи")
        sources = {"application/.manifest.json": manifest_path, "application/.release-id": self.current / ".release-id",
                   "connector": self.home / CONNECTOR, "helper": self.support / HELPER}
        sources.update({"application/" + name: self.current / name for name in manifest["files"]})
        Bundle.write(output, state, sources)

    # Проверяет незавершённые файловые намерения и целостность SQLite-снимка.
    # Очереди публикации и прочие сохранённые данные переносятся в исходном виде.
    @staticmethod
    def check_database(database):
        with closing(sqlite3.connect(database.as_uri() + "?mode=ro&immutable=1", uri=True)) as db:
            if db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                raise RuntimeError("Проверка целостности SQLite не пройдена")
            tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if "orders" not in tables:
                raise RuntimeError("В снимке нет реестра заказов")
            for table, condition, name in (
                ("event_renames", "state='pending'", "переименование события"),
                ("folder_renames", "state='pending'", "перенос или переименование папки"),
                ("metadata_file_moves", "state='pending'", "перемещение файла в корзине"),
                ("metadata_records", "kind='order_creation' AND json_extract(data,'$.state')='pending'", "создание заказа"),
                ("invoices", "json_extract(data,'$._trash.state')='pending'", "корзина счёта"),
            ):
                if table in tables and db.execute(f"SELECT 1 FROM {table} WHERE {condition} LIMIT 1").fetchone():
                    raise RuntimeError("Сначала заверши незаконченные операции: " + name)

    # Останавливает источник и публикует неизменяемый снимок указанной передачи.
    # После публикации источник остаётся выключенным до получения обратной передачи.
    def freeze(self, identity, trip):
        with self.lock():
            history = self.history(identity)
            history.mkdir(parents=True, exist_ok=True)
            archive = history / "outgoing.zip"
            state = self.status()
            marker = {"id": identity, "trip": trip, "release": state["release"]}
            if state["parked"] and state["parked"] != marker:
                raise RuntimeError("Установка уже остановлена для другой передачи")
            if archive.exists() and state["parked"] == marker:
                return archive
            if not state["parked"] and not state["configured_remote"]:
                raise RuntimeError("У источника отсутствуют настройки защищённого входа")
            if not state["parked"] and not state["manager"] and self.role == "m4":
                raise RuntimeError("На M4 нет активной рабочей установки")
            self.check_source(state)
            if not state["parked"]:
                deployment.write_json(self.parked, marker)
            try:
                self.stop_job(TUNNEL)
                with self.stopped(state["remote_port"], drain=True):
                    snapshot = history / "snapshot.sqlite3"
                    snapshot.unlink(missing_ok=True)
                    deployment.backup_database(self.database, snapshot)
                    self.check_database(snapshot)
                    config = configparser.ConfigParser(interpolation=None)
                    config.read(self.root / "manager.ini", encoding="utf-8")
                    profile = Path(config.get("remote_access", "credentials_file", fallback=str(self.support / PROFILE))).expanduser()
                    if profile.resolve() != self.support / PROFILE:
                        raise RuntimeError("Изменился путь закрытого профиля внешнего входа")
                    files = {"snapshot.sqlite3": snapshot, PROFILE: profile}
                    for name in TELEGRAM:
                        if (self.data / name).is_file():
                            files[name] = self.data / name
                    if self.role == "m4":
                        files[TOKEN] = self.support / TOKEN
                    if any(path.is_symlink() or not path.is_file() for path in files.values()):
                        raise RuntimeError("Один из файлов передачи недоступен")
                    Bundle.write(archive, {**marker, "documents": str(self.documents), "source": self.role}, files)
                return archive
            except Exception:
                if not archive.exists() and not self.loaded(deployment.LABEL):
                    self.parked.unlink(missing_ok=True)
                    self.start_job(deployment.LABEL)
                    self.start_job(TUNNEL)
                raise

    # Устанавливает полученную базу ровно один раз и подтверждает оба входа.
    # При повторе после запуска сохраняет изменения, сделанные на новой машине.
    def activate(self, identity, trip, archive):
        with self.lock():
            history = self.history(identity)
            history.mkdir(parents=True, exist_ok=True)
            receipt = history / "installed.json"
            state = self.status()
            previous = trip if self.role == "m4" else "prepared"
            record = {"id": identity, "trip": trip, "release": state["release"]}
            if receipt.exists():
                installed = json.loads(receipt.read_text())
                if installed["id"] != identity or installed["trip"] != trip:
                    raise RuntimeError("Сохранённое подтверждение относится к другой поездке")
            if not receipt.exists():
                if not state["parked"] or state["parked"]["id"] != previous:
                    raise RuntimeError("Целевая установка не остановлена для этой передачи")
                with tempfile.TemporaryDirectory(dir=history) as temporary:
                    stage = Path(temporary)
                    with zipfile.ZipFile(archive) as source:
                        received = Bundle.read(source, stage,
                                               lambda name: name in {"snapshot.sqlite3", PROFILE, TOKEN, *TELEGRAM})
                    expected_source = "macbook" if self.role == "m4" else "m4"
                    required = {"snapshot.sqlite3", PROFILE} | ({TOKEN} if self.role == "macbook" else set())
                    if (received["id"] != identity or received["trip"] != trip
                            or received["source"] != expected_source or received["release"] != state["release"]
                            or not required <= received["files"].keys() or (self.role == "m4" and TOKEN in received["files"])
                            or received["documents"] != str(self.documents)):
                        raise RuntimeError("Снимок не соответствует машине, релизу или номеру передачи")
                    self.check_database(stage / "snapshot.sqlite3")
                    with self.stopped(state["remote_port"]):
                        self.install_files(history, stage)
                        deployment.write_json(receipt, record)
            if self.parked.exists():
                if json.loads(self.parked.read_text())["id"] != previous:
                    raise RuntimeError("Установка остановлена для другой передачи")
                self.parked.unlink()
            self.start_job(deployment.LABEL)
            self.check_service(state)
            self.start_job(TUNNEL)
            self.check_public(state)
            return self.status()

    # Сохраняет прежнюю SQLite с её журналами, затем атомарно ставит проверенные файлы.
    # Копия прежней базы создаётся один раз и остаётся доступной после прерывания.
    def install_files(self, history, stage):
        saved = history / "previous"
        if not (saved / "ready").exists():
            saved.mkdir(exist_ok=True)
            for suffix in ("", "-wal", "-shm", "-journal"):
                path = self.database.with_name(self.database.name + suffix)
                if path.exists():
                    temporary = saved / (path.name + ".tmp")
                    with path.open("rb") as source, temporary.open("wb") as target:
                        shutil.copyfileobj(source, target, length=1024 * 1024)
                        target.flush()
                        os.fsync(target.fileno())
                    temporary.replace(saved / path.name)
            deployment.atomic_write(saved / "ready", b"ready\n")
        for suffix in ("-wal", "-shm", "-journal"):
            self.database.with_name(self.database.name + suffix).unlink(missing_ok=True)
        self.support.mkdir(parents=True, exist_ok=True)
        for name, destination in ((PROFILE, self.support / PROFILE), (TOKEN, self.support / TOKEN),
                                  *((name, self.data / name) for name in TELEGRAM)):
            path = stage / name
            if path.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                if destination.is_symlink():
                    raise RuntimeError("Символическая ссылка вместо файла настроек")
                deployment.atomic_write(destination, path.read_bytes())
            elif name in TELEGRAM:
                destination.unlink(missing_ok=True)
        (stage / "snapshot.sqlite3").replace(self.database)

    # Проверяет номер релиза, корень документов и защищённый локальный слушатель.
    # Открывает дерево самим сервером и проверяет, что внешний API требует входа.
    def check_service(self, state):
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            try:
                value = deployment.health(self.port, state["release"])
                if value["root"] != str(self.documents):
                    raise RuntimeError("Сервер использует другой корень документов")
                with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/api/tree", timeout=5) as response:
                    json.load(response)
                connection = http.client.HTTPConnection("127.0.0.1", state["remote_port"], timeout=3)
                try:
                    connection.request("GET", "/api/health", headers={"Host": state["public_host"]})
                    if connection.getresponse().status != 401:
                        raise RuntimeError("Внешний API не подтвердил защиту паролем")
                finally:
                    connection.close()
                return
            except (OSError, ValueError, RuntimeError, http.client.HTTPException):
                time.sleep(0.5)
        raise RuntimeError("Активный менеджер не прошёл проверку. Повтори ту же команду после проверки логов.")

    # Проверяет, что прежний HTTPS-адрес отвечает с принимающей машины.
    # Использует короткую штатную сессию в памяти, без вывода или записи подписи.
    def check_public(self, state):
        sys.path.insert(0, str(self.current.resolve()))
        from remote_access import PasswordGate, SESSION_COOKIE, settings

        config = settings(self.root / "manager.ini")
        gate = PasswordGate(config["credentials_file"], state["public_host"])
        cookie = SESSION_COOKIE + "=" + gate.token(gate.document(), "session", 120)
        url = "https://" + state["public_host"]
        login_url = url + "/_auth/login"
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(login_url, timeout=5) as response:
                    if response.status != 200 or response.geturl() != login_url:
                        raise RuntimeError("Не открылась форма входа")
                # HTTPSConnection не пересылает подписанную сессию на другие адреса.
                connection = http.client.HTTPSConnection(state["public_host"], timeout=5)
                try:
                    connection.request("GET", "/api/handoff-health", headers={"Cookie": cookie})
                    response = connection.getresponse()
                    if response.status == 200:
                        value = json.load(response)
                        if value.get("host") == socket.gethostname() and value.get("release") == state["release"]:
                            return
                finally:
                    connection.close()
            except (OSError, ValueError, RuntimeError, http.client.HTTPException):
                pass
            time.sleep(1)
        raise RuntimeError("Внешний адрес ещё не отвечает. Проверь туннель и повтори ту же команду.")


# Выполняет одну строго заданную операцию на M4 через SSH.
# Бинарные пакеты передаёт по stdin/stdout без вывода файлов настроек в журнал.
def main():
    settings = json.loads(sys.argv[1])
    action = sys.argv[2]
    installation = Installation(settings, settings["documents"], "m4")
    if action == "status":
        print(json.dumps(installation.status(), ensure_ascii=False))
    elif action == "check":
        print(json.dumps(installation.check_active(), ensure_ascii=False))
    elif action == "prepare":
        with installation.lock(), tempfile.TemporaryDirectory(dir=installation.root) as temporary:
            path = Path(temporary) / "release.zip"
            installation.bootstrap(path)
            with path.open("rb") as stream:
                shutil.copyfileobj(stream, sys.stdout.buffer)
    elif action == "freeze":
        path = installation.freeze(*sys.argv[3:5])
        with path.open("rb") as stream:
            shutil.copyfileobj(stream, sys.stdout.buffer)
    elif action == "activate":
        os.umask(0o077)
        with tempfile.TemporaryFile(dir=installation.root) as stream:
            shutil.copyfileobj(sys.stdin.buffer, stream)
            stream.seek(0)
            print(json.dumps(installation.activate(*sys.argv[3:5], stream), ensure_ascii=False))
    else:
        raise ValueError("Неизвестное действие передачи")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, sqlite3.Error, subprocess.SubprocessError, zipfile.BadZipFile, KeyError) as error:
        print(f"Передача остановлена: {error}", file=sys.stderr)
        sys.exit(1)
