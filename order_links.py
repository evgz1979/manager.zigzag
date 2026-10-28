"""Symmetric client-order links, stored by UUID in existing order extra blocks."""
import json
import uuid
from pathlib import Path

from event_folder_undo import assert_unlocked
from folder_structure import order_location

BLOCK = "Связанные клиентские заказы"
ORDER_LINKS_VERSION = 1
MAX_LINKS = 200


def checked_ids(value):
    if not isinstance(value, list) or len(value) > MAX_LINKS:
        raise ValueError(f"Выбери не больше {MAX_LINKS} разных заказов")
    if any(not isinstance(item, str) for item in value):
        raise ValueError("Некорректный идентификатор связанного заказа")
    if len(set(value)) != len(value):
        raise ValueError("Связанный заказ не должен повторяться")
    for identity in value:
        try:
            if str(uuid.UUID(identity)) != identity:
                raise ValueError()
        except (ValueError, AttributeError):
            raise ValueError("Некорректный идентификатор связанного заказа") from None
    return value


def read(blocks):
    if BLOCK not in blocks:
        return []
    try:
        body = json.loads(blocks[BLOCK])
        if not isinstance(body, dict) or set(body) != {"version", "order_ids"} or type(body["version"]) is not int or body["version"] != 1:
            return None
        return checked_ids(body["order_ids"])
    except (TypeError, ValueError):
        return None


def write(blocks, identities):
    if read(blocks) is None:
        raise ValueError("Неизвестный формат связанных заказов сохранён без изменений")
    return {**blocks, BLOCK: json.dumps({"version": 1, "order_ids": sorted(checked_ids(identities))}, ensure_ascii=False)}


def scope(path):
    if any(part.startswith(("#", ".")) for part in Path(path).parts):
        return None
    location = order_location(path)
    if not location["client_path"] or not location["object_path"]:
        return None
    return location["client_path"], location["object_path"]


class OrderLinks:
    def __init__(self, store):
        self.store = store

    def _read(self, db, source):
        source_scope = scope(source["path"])
        if not source_scope:
            raise ValueError("Связывать можно только заказы объекта клиента")
        identities = read(json.loads(source["extra_blocks"]))
        candidates, items = [], []
        rows = {row["id"]: row for row in db.execute("SELECT * FROM orders")}
        for row in rows.values():
            if row["id"] == source["id"]:
                continue
            available = bool(row["registered"]) and scope(row["path"]) == source_scope
            summary = {key: row[key] for key in ("id", "path", "title", "revision")}
            summary.update(available=available, registered=bool(row["registered"]), editable=read(json.loads(row["extra_blocks"])) is not None)
            if identities is not None and row["id"] in identities:
                items.append(summary)
            elif available:
                candidates.append(summary)
        for identity in identities or []:
            if identity not in rows:
                items.append({"id": identity, "path": None, "title": "Заказ недоступен", "revision": None, "available": False, "registered": False, "editable": True})
        key = lambda row: (row["title"].casefold(), row["path"] or "", row["id"])
        return {"order": self.store.record(source, db), "linked_ids": identities,
                "items": sorted(items, key=key), "candidates": sorted(candidates, key=key)}

    def read(self, relative):
        relative = self.store.path(relative)
        with self.store.connect() as db:
            assert_unlocked(db, relative)
            source = db.execute("SELECT * FROM orders WHERE path=? AND registered=1", (relative,)).fetchone()
            if source is None:
                raise FileNotFoundError("Сначала добавь заказ в список объекта")
            return self._read(db, source)

    def save(self, payload):
        from orders import OrderConflict
        relative = self.store.path(payload.get("path"))
        identity, target_id = payload.get("id"), payload.get("target_id")
        checked_ids([identity, target_id])
        revision, target_revision, linked = payload.get("revision"), payload.get("target_revision"), payload.get("linked")
        if type(revision) is not int or type(linked) is not bool or (target_revision is not None and type(target_revision) is not int):
            raise ValueError("Нужны версии заказов и логическое состояние связи")
        with self.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            assert_unlocked(db, relative)
            source = db.execute("SELECT * FROM orders WHERE path=? AND id=? AND registered=1", (relative, identity)).fetchone()
            target = db.execute("SELECT * FROM orders WHERE id=?", (target_id,)).fetchone()
            if source is None or source["revision"] != revision or (target["revision"] if target else None) != target_revision:
                raise OrderConflict("Один из заказов изменён. Обнови список связей перед повтором")
            if not scope(relative):
                raise ValueError("Связывать можно только заказы объекта клиента")
            if linked and (target is None or not target["registered"] or scope(target["path"]) != scope(relative)):
                raise ValueError("Выбери зарегистрированный заказ этого же объекта и клиента")
            source_blocks = json.loads(source["extra_blocks"])
            source_ids = read(source_blocks)
            if source_ids is None:
                raise ValueError("Неизвестный формат связанных заказов сохранён без изменений")
            if not linked and target_id not in source_ids:
                return {**self._read(db, source), "records": []}
            updates = []
            for row, other_id in ((source, target_id), (target, identity)):
                if row is None:
                    continue
                assert_unlocked(db, row["path"])
                blocks = json.loads(row["extra_blocks"])
                identities = read(blocks)
                if identities is None:
                    raise ValueError("Неизвестный формат связанных заказов сохранён без изменений")
                new_ids = set(identities)
                if linked:
                    new_ids.add(other_id)
                else:
                    new_ids.discard(other_id)
                if new_ids != set(identities):
                    updates.append((json.dumps(write(blocks, list(new_ids)), ensure_ascii=False), row["id"]))
            db.executemany("UPDATE orders SET extra_blocks=?,revision=revision+1 WHERE id=?", updates)
            if updates and self.store.database_only:
                db.execute("INSERT INTO metadata_settings VALUES ('client_order_links','1') ON CONFLICT(key) DO UPDATE SET value=excluded.value")
            source = db.execute("SELECT * FROM orders WHERE id=?", (identity,)).fetchone()
            result = self._read(db, source)
            result["records"] = [self.store.record(db.execute("SELECT * FROM orders WHERE id=?", (row_id,)).fetchone(), db) for _, row_id in updates]
            return result
