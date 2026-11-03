"""Client visibility in SQLite, with initial legacy marker import and old export compatibility."""
import json
import threading
from pathlib import Path

import order_document as document
from folder_structure import client_path, is_catalog_group
from event_folder_undo import guard_database, assert_unlocked

BLOCK = "Активность клиента"
ACTIVE = "Активный"
INACTIVE = "Неактивный"
LOCK = threading.RLock()


# Обозначает конфликт изменения в этом модуле.
# Вызывающий обработчик использует тип исключения для отказа без подмены данных.
class ClientActivityConflict(ValueError):
    pass


# Извлекает распознанное значение состояния из исходного представления.
# Возвращает `record.get('extra_blocks', {}).get(block)`.
def value(record, block=BLOCK):
    return record.get("extra_blocks", {}).get(block)


# Проверяет, соответствует ли значение известному формату состояния.
# Возвращает `raw is None or raw.strip() in (ACTIVE, INACTIVE)`.
def known(raw):
    return raw is None or raw.strip() in (ACTIVE, INACTIVE)


# Поддерживает SQLite-индекс активности клиентов и совместимость прежних отметок.
# Основные операции: __init__, connect, schema, record, matches; остальные описаны у методов.
class ClientActivity:
    table = "client_activity"
    block = BLOCK
    entity = "клиента"

    # Сохраняет зависимости и начальные параметры экземпляра.
    # Состояние и зависимости сохраняются в полях self для последующих операций.
    def __init__(self, orders, lock=LOCK):
        self.orders = orders
        self.root = orders.root
        self.lock = lock

    # Открывает соединение SQLite и управляет его временем жизни.
    # Возвращает `self.orders.connect()`.
    def connect(self):
        return self.orders.connect()

    # Создаёт отсутствующие таблицы и совместимые расширения схемы.
    # Создаёт таблицу индекса активности с именем из доверенного cls.table.
    @classmethod
    def schema(cls, db):
        db.execute(f"""CREATE TABLE IF NOT EXISTS {cls.table} (
            path TEXT PRIMARY KEY, inactive INTEGER NOT NULL, revision INTEGER NOT NULL,
            exported_revision INTEGER NOT NULL, file_value TEXT NOT NULL, sync_error TEXT NOT NULL DEFAULT '')""")

    # Преобразует строку SQLite в представление для вызывающего кода.
    # Разбирает JSON; вызывающий код должен учитывать ошибки или неизвестный формат.
    def record(self,row):
        result = dict(row)
        result["inactive"] = bool(result["inactive"])
        result["sync_pending"] = result["revision"] != result.pop("exported_revision")
        result["editable"] = known(json.loads(result.pop("file_value")))
        if self.orders.database_only:
            result.update(sync_pending=False,sync_error="",storage="database")
        return result

    # Проверяет соответствие папки роли индексируемой сущности.
    # Возвращает `client_path(path) == path`.
    def matches(self, path):
        return client_path(path) == path

    # Находит допустимую существующую цель файловой операции.
    # При недопустимом состоянии возбуждает ValueError, FileNotFoundError.
    def target(self, path):
        if not isinstance(path, str) or not path or "\x00" in path or Path(path).is_absolute() or Path(path).as_posix() != path or any(part.startswith(".") for part in Path(path).parts):
            raise ValueError(f"Отметка доступна только в карточке {self.entity}")
        guard_database(self.orders.database, path)
        target = self.root / path
        if any((self.root / Path(*Path(path).parts[:index + 1])).is_symlink() for index in range(len(Path(path).parts))):
            raise ValueError("Символические ссылки не редактируются")
        if not target.is_dir():
            raise FileNotFoundError(f"Папка {self.entity} недоступна")
        if not self.matches(path):
            raise ValueError(f"Отметка доступна только в карточке {self.entity}")
        return target

    # Читает сохранённую отметку активности одного пути.
    # Возвращает `None`; либо `self.record(row) if row else None`.
    def get(self, path):
        if not self.orders.database.exists():
            return None
        with self.connect() as db:
            self.schema(db)
            row = db.execute(f"SELECT * FROM {self.table} WHERE path=?", (path,)).fetchone()
            return self.record(row) if row else None

    # Получает активность пути с допустимым первоначальным импортом отметки.
    # Создаёт таблицу индекса активности с именем из доверенного cls.table.
    def read(self, path):
        with self.lock:
            if self.orders.database_only:
                current = self.get(path)
                if current:
                    return current
            folder = self.target(path)
            current = self.get(path)
            if current and current["sync_pending"]:
                return current
            raw = value(document.load(folder, self.orders.labels), self.block)
            with self.connect() as db:
                self.schema(db)
                row = db.execute(f"SELECT * FROM {self.table} WHERE path=?", (path,)).fetchone()
                # Unknown user text survives and the last known state remains effective.
                if known(raw):
                    inactive = raw is not None and raw.strip() == INACTIVE
                else:
                    inactive = bool(row and row["inactive"])
                revision = row["revision"] + int(json.loads(row["file_value"]) != raw) if row else 1
                error = f"Неизвестный текст [{self.block}] сохранён. Проверь !.txt {self.entity}." if not known(raw) else ""
                db.execute(f"""INSERT INTO {self.table} VALUES (?,?,?,?,?,?) ON CONFLICT(path) DO UPDATE SET
                    inactive=excluded.inactive,revision=excluded.revision,exported_revision=excluded.exported_revision,
                    file_value=excluded.file_value,sync_error=excluded.sync_error""",
                    (path, int(inactive), revision, revision, json.dumps(raw, ensure_ascii=False), error))
            return self.get(path)

    # Сохраняет явное решение об активности клиента или объекта по версии.
    # При недопустимом состоянии возбуждает ValueError, ClientActivityConflict.
    def save(self, payload):
        path, revision, inactive = payload.get("path"), payload.get("revision"), payload.get("inactive")
        if type(revision) is not int or type(inactive) is not bool:
            raise ValueError(f"Открой карточку {self.entity} заново перед изменением отметки")
        if not isinstance(path,str) or not path or Path(path).is_absolute() or any(part.startswith('.') for part in Path(path).parts):
            raise ValueError("Выбери карточку клиента или объекта")
        with self.lock:
            if not self.orders.database_only:
                self.target(path)
            with self.connect() as db:
                self.schema(db)
                assert_unlocked(db,path)
                row = db.execute(f"SELECT * FROM {self.table} WHERE path=?", (path,)).fetchone()
                if not row or row["revision"] != revision:
                    raise ClientActivityConflict(f"Отметка {self.entity} изменилась. Обнови карточку перед сохранением.")
                if not known(json.loads(row["file_value"])):
                    raise ClientActivityConflict(f"Неизвестный текст отметки сохранён. Проверь !.txt {self.entity}.")
                db.execute(f"UPDATE {self.table} SET inactive=?,revision=revision+1,sync_error='' WHERE path=? AND revision=?",
                           (int(inactive), path, revision))
        return self.get(path)

    # Явно принимает файловую версию при разрешении прежнего конфликта активности.
    # При недопустимом состоянии возбуждает ValueError, ClientActivityConflict.
    def accept_file(self, payload):
        """Explicit conflict resolution; never discard a pending decision on open."""
        if self.orders.database_only:
            raise ValueError("Рабочая отметка хранится в базе; импорт старого файла поверх неё отключён")
        path = payload.get("path")
        with self.lock:
            self.target(path)
            with self.connect() as db:
                self.schema(db)
                row = db.execute(f"SELECT * FROM {self.table} WHERE path=?", (path,)).fetchone()
                if not row or type(payload.get("revision")) is not int or row["revision"] != payload["revision"]:
                    raise ClientActivityConflict(f"Отметка {self.entity} изменилась. Обнови карточку.")
                raw = value(document.load(self.root / path, self.orders.labels), self.block)
                if not known(raw):
                    raise ClientActivityConflict(f"Неизвестный текст отметки сохранён. Проверь !.txt {self.entity}.")
                db.execute(f"UPDATE {self.table} SET inactive=?,revision=revision+1,exported_revision=revision+1,file_value=?,sync_error='' WHERE path=?",
                           (int(raw is not None and raw.strip() == INACTIVE), json.dumps(raw, ensure_ascii=False), path))
        return self.get(path)

    # Читает множество неактивных путей из индекса базы.
    # Возвращает `set()`; либо `{row[0] for row in db.execute(f'SELECT path FROM {self.table} WHERE inactive=1')}`.
    def inactive_paths(self):
        # Tree/list reads do not create a database or access iCloud cards.
        if not self.orders.database.exists():
            return set()
        with self.connect() as db:
            self.schema(db)
            return {row[0] for row in db.execute(f"SELECT path FROM {self.table} WHERE inactive=1")}

    # Отбирает заказы вне неактивных клиентов и объектов.
    # Возвращает `[record for record in records if not is_inactive(record['path'], inactive)]`.
    def visible_orders(self, records):
        inactive = self.inactive_paths()
        return [record for record in records if not is_inactive(record["path"], inactive)]

    # Обновляет индекс ролей папок без чтения вложений заказов.
    # Передаёт работу `folders`, `is_catalog_group`, `candidate.relative_to(self.root).as_posix`.
    def refresh(self):
        """Only client cards, never order contents; retain index entries on read errors."""
        # Перечисляет допустимые папки текущего ограниченного обхода.
        # Возвращает `[item for item in parent.iterdir() if not item.name.startswith(('.', '#')) and (not item.is_symlink()) and item.is_dir()]`.
        def folders(parent):
            return [item for item in parent.iterdir() if not item.name.startswith((".", "#"))
                    and not item.is_symlink() and item.is_dir()]
        for item in folders(self.root):
            try:
                candidates = folders(item) if is_catalog_group(item.name) else [item]
                for candidate in candidates:
                    path = candidate.relative_to(self.root).as_posix()
                    if client_path(path) == path:
                        try:
                            self.read(path)
                        except (OSError, ValueError) as error:
                            self.error(path, error)
            except OSError as error:
                print(f"Активность клиентов · {item.name}: {error}", flush=True)

    # Записывает ошибку обработки для последующего показа или повтора.
    # Передаёт работу `self.connect`, `self.schema`, `db.execute`.
    def error(self, path, problem):
        with self.connect() as db:
            self.schema(db)
            db.execute(f"UPDATE {self.table} SET sync_error=? WHERE path=?", (document.icloud_access.sync_error(problem), path))

    # Обслуживает прежнюю файловую отметку только вне SQLite-only.
    # При недопустимом состоянии возбуждает ClientActivityConflict.
    def sync(self):
        if self.orders.database_only:
            with self.connect() as db:
                self.schema(db)
                db.execute(f"UPDATE {self.table} SET exported_revision=revision,sync_error='' WHERE revision!=exported_revision OR sync_error!=''")
            return
        if not self.orders.database.exists():
            return
        with self.lock:
            with self.connect() as db:
                self.schema(db)
                pending = list(db.execute(f"SELECT * FROM {self.table} WHERE revision!=exported_revision"))
            for row in pending:
                try:
                    folder = self.target(row["path"])
                    record = document.load(folder, self.orders.labels)
                    raw, desired = value(record, self.block), INACTIVE if row["inactive"] else ACTIVE
                    if raw != json.loads(row["file_value"]) and raw != desired:
                        raise ClientActivityConflict("Отметка в !.txt изменена извне. Сохранены обе версии; выбери отметку из файла или верни прежний текст файла.")
                    if raw != desired:
                        record.setdefault("extra_blocks", {})[self.block] = desired
                        document.archive_current(folder)
                        document.atomic_write(folder / document.DOCUMENT, document.render(record, self.orders.labels))
                        document.archive_legacy(folder)
                    with self.connect() as db:
                        db.execute(f"UPDATE {self.table} SET exported_revision=revision,file_value=?,sync_error='' WHERE path=? AND revision=?",
                                   (json.dumps(desired, ensure_ascii=False), row["path"], row["revision"]))
                except (OSError, ValueError) as error:
                    self.error(row["path"], error)


# Проверяет неактивность пути по границам компонентов без чтения документов.
# Возвращает `any((path == parent or path.startswith(parent + '/') for parent in paths))`.
def is_inactive(path, paths):
    """Проверка индекса по границам пути, без чтения документов."""
    return any(path == parent or path.startswith(parent + "/") for parent in paths)
