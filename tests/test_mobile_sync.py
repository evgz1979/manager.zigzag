import hashlib
import json
import tempfile
import sqlite3
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

import file_comments
import order_document as document
from orders import OrderStore
from mobile_sync import MobileBridge, MobileConflict, encode


class MobileSyncTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.root = self.base / "documents"
        self.relative = "Клиент/Объект/2026-10-18 - Заказ"
        self.folder = self.root / self.relative
        self.folder.mkdir(parents=True)
        self.store = OrderStore(self.root, self.base / "local", {"new": "Новый", "done": "Готово"}, database_only=False)
        self.record = self.store.add(self.relative, {
            "title": "Заказ", "status": "new", "financial_status": "partial", "note": "Заметка Mac",
            "amount": 10000, "costs": 2000, "paid": 3000,
            "extra_blocks": {"Доставка": "Не потерять", "Задачи": "- [ ] Позвонить"}})
        self.file = self.folder / "Фото #1.txt"
        self.file.write_text("original")
        self.bridge = MobileBridge(self.store)
        self.bridge.configure(True)
        self.bridge.run()
        self.catalog = json.loads((self.bridge.folder / ".catalog.json").read_text())
        self.device = str(uuid.uuid4())
        self.sequence = 0

    def tearDown(self):
        self.temporary.cleanup()

    def operation(self, kind="order_comment", **values):
        self.sequence += 1
        return {"schema": 1, "root_id": self.catalog["root_id"], "id": str(uuid.uuid4()),
                "device_id": self.device, "sequence": self.sequence, "created": 1792300000,
                "order_id": self.record["id"], "kind": kind, "text": "С телефона", "base_version": 1, **values}

    def test_deleted_and_readded_same_task_has_new_identity(self):
        task = self.catalog["orders"][0]["tasks"][0]
        self.save(todo_items=[])
        self.save(todo_items=[{"text": task["text"], "done": False}])
        op = self.operation("todo_set", task_id=task["id"], done=True, base_done=False, base_text=task["text"])
        self.assertEqual(self.publish(op)["status"], "conflict")

    def test_task_changed_and_changed_back_still_detects_stale_toggle(self):
        task = self.catalog["orders"][0]["tasks"][0]
        self.save(todo_items=[{"text": task["text"], "done": True}])
        self.save(todo_items=[{"text": task["text"], "done": False}])
        op = self.operation("todo_set", task_id=task["id"], done=True, base_done=False, base_text=task["text"])
        self.assertEqual(self.publish(op)["status"], "conflict")

    def publish(self, operation):
        raw = encode(operation).encode()
        path = self.bridge.folder / ".inbox" / ("." + operation["id"] + ".json")
        path.write_bytes(raw)
        self.bridge.run()
        receipt_path = self.bridge.folder / ".receipts" / ("." + operation["id"] + ".json")
        return json.loads(receipt_path.read_text()) if receipt_path.exists() else None

    def save(self, **values):
        record = self.store.get(self.relative)
        payload = {**record, **{key: str(record[key] / 100) for key in ("amount", "costs", "paid")}, **values}
        return self.store.save(payload)

    def test_disabled_bridge_does_not_create_exchange_or_visit_cloud(self):
        self.bridge.configure(False)
        with patch.object(self.bridge, "prepare", side_effect=AssertionError("No filesystem access")):
            self.bridge.run()
        self.assertFalse(self.bridge.status()["enabled"])

    def test_comment_appends_to_latest_note_without_changing_other_fields(self):
        op = self.operation()
        self.save(note="Новая заметка Mac", status="done")
        self.assertEqual(self.publish(op)["status"], "applied")
        result = self.store.get(self.relative)
        self.assertEqual(result["note"], "Новая заметка Mac\n\nС телефона")
        self.assertEqual((result["status"], result["financial_status"], result["amount"], result["paid"]), ("done", "partial", 10000, 3000))
        self.assertEqual(result["extra_blocks"]["Доставка"], "Не потерять")
        self.assertIn("С телефона", (self.folder / "!.txt").read_text())

    def test_repeated_delivery_and_restart_never_duplicate_comment(self):
        op = self.operation()
        self.publish(op)
        self.bridge = MobileBridge(self.store)
        self.publish(op)
        self.assertEqual(self.store.get(self.relative)["note"].count("С телефона"), 1)

    def test_receipt_recovers_deduplication_after_ledger_rebuild(self):
        op = self.operation()
        self.publish(op)
        with self.store.connect() as db:
            db.execute("DELETE FROM mobile_operations")
        self.publish(op)
        self.assertEqual(self.store.get(self.relative)["note"].count("С телефона"), 1)

    def test_reusing_operation_id_with_other_bytes_is_rejected(self):
        op = self.operation()
        self.publish(op)
        with self.assertRaises(MobileConflict):
            self.bridge.apply({**op, "text": "Подмена"}, encode({**op, "text": "Подмена"}).encode(), self.catalog["root_id"])
        self.assertNotIn("Подмена", self.store.get(self.relative)["note"])

    def test_offline_mac_order_changes_and_phone_additions_merge(self):
        first = self.operation("todo_add", task_id=str(uuid.uuid4()), text="Новая задача")
        self.save(todo_items=[{"text": "Позвонить", "done": True}, {"text": "С Mac", "done": False}])
        self.assertEqual(self.publish(first)["status"], "applied")
        tasks = self.store.get(self.relative)["todo_items"]
        self.assertEqual([x["text"] for x in tasks], ["Позвонить", "С Mac", "Новая задача"])
        self.assertTrue(tasks[0]["done"])

    def test_dependent_toggle_waits_for_delayed_add_then_applies(self):
        add = self.operation("todo_add", task_id=str(uuid.uuid4()), text="С собой")
        toggle = self.operation("todo_set", task_id=add["task_id"], done=True,
                                base_done=False, base_text="С собой", depends_on=add["id"])
        self.assertIsNone(self.publish(toggle))
        self.publish(add)
        self.assertEqual(self.store.get(self.relative)["todo_items"][-1], {"text": "С собой", "done": True})

    def test_renamed_or_deleted_task_conflicts_without_resurrecting(self):
        task = self.catalog["orders"][0]["tasks"][0]
        self.save(todo_items=[])
        op = self.operation("todo_set", task_id=task["id"], done=True, base_done=False, base_text=task["text"])
        self.assertEqual(self.publish(op)["status"], "conflict")
        self.assertEqual(self.store.get(self.relative)["todo_items"], [])
        self.assertTrue((self.bridge.folder / ".inbox" / f'.{op["id"]}.json').exists())

    def test_plain_text_todos_and_unknown_sections_are_preserved(self):
        with self.store.connect() as db:
            db.execute("UPDATE orders SET extra_blocks=? WHERE id=?", (encode({"Задачи": "Старый текст", "Доставка": "Сохранить"}), self.record["id"]))
        self.assertEqual(self.publish(self.operation("todo_add", task_id=str(uuid.uuid4()), text="Новая"))["status"], "conflict")
        self.assertEqual(self.store.get(self.relative)["extra_blocks"], {"Задачи": "Старый текст", "Доставка": "Сохранить"})

    def test_file_comment_appends_latest_text_and_preserves_original_and_history(self):
        descriptor = self.catalog["orders"][0]["files"][0]
        old = file_comments.save(self.file, "Mac", "missing")
        op = self.operation("file_comment", file_path=descriptor["path"], file_token=descriptor["token"])
        self.assertEqual(self.publish(op)["status"], "applied")
        self.assertEqual(file_comments.read(self.file)["comment"], "Mac\n\nС телефона")
        self.assertEqual(self.file.read_text(), "original")
        self.assertEqual(self.store.get(self.relative)["revision"], self.record["revision"])
        _, key, folder, _ = file_comments.paths(self.file)
        self.assertTrue((folder / ".history" / ("." + key) / ("." + old["revision"] + ".txt")).exists())

    def test_file_comment_crash_after_write_is_recovered_without_duplicate(self):
        descriptor = self.catalog["orders"][0]["files"][0]
        op = self.operation("file_comment", file_path=descriptor["path"], file_token=descriptor["token"])
        save = file_comments.save
        def interrupted(*args):
            save(*args)
            raise OSError("crash after atomic write")
        with patch.object(file_comments, "save", side_effect=interrupted):
            self.assertIsNone(self.publish(op))
        self.assertEqual(self.publish(op)["status"], "applied")
        self.assertEqual(file_comments.read(self.file)["comment"], "С телефона")

    def test_file_io_does_not_hold_database_writer_lock(self):
        descriptor = self.catalog["orders"][0]["files"][0]
        operation = self.operation("file_comment", file_path=descriptor["path"], file_token=descriptor["token"])
        original_read = file_comments.read
        def checked_read(file):
            with sqlite3.connect(self.store.database, timeout=0.1) as db:
                db.execute("BEGIN IMMEDIATE")
                db.execute("UPDATE orders SET note=note WHERE id=?", (self.record["id"],))
            return original_read(file)
        with patch.object(file_comments, "read", side_effect=checked_read):
            receipt = self.bridge.apply(operation, encode(operation).encode(), self.catalog["root_id"])
        self.assertEqual(receipt["status"], "applied")

    def test_crash_recovery_recognizes_history_after_later_desktop_edit(self):
        descriptor = self.catalog["orders"][0]["files"][0]
        op = self.operation("file_comment", file_path=descriptor["path"], file_token=descriptor["token"])
        save = file_comments.save
        def interrupted(*args):
            save(*args)
            raise OSError("crash")
        with patch.object(file_comments, "save", side_effect=interrupted):
            self.publish(op)
        current = file_comments.read(self.file)
        file_comments.save(self.file, "Более новая правка Mac", current["revision"])
        self.assertEqual(self.publish(op)["status"], "applied")
        self.assertEqual(file_comments.read(self.file)["comment"], "Более новая правка Mac")

    def test_replaced_file_and_path_escape_do_not_receive_comment(self):
        descriptor = self.catalog["orders"][0]["files"][0]
        self.file.write_text("replaced")
        op = self.operation("file_comment", file_path=descriptor["path"], file_token=descriptor["token"])
        self.assertEqual(self.publish(op)["status"], "conflict")
        self.assertEqual(file_comments.read(self.file)["comment"], "")
        op = self.operation("file_comment", file_path=self.relative + "/../../outside.txt", file_token=descriptor["token"])
        self.assertEqual(self.publish(op)["status"], "conflict")

    def test_unregistered_order_is_not_added_back(self):
        self.store.remove({"path": self.relative, "revision": self.record["revision"], "confirmed": True})
        self.assertEqual(self.publish(self.operation())["status"], "conflict")
        self.assertIsNone(self.store.get(self.relative))

    def test_offline_export_retries_without_losing_applied_order_operation(self):
        op = self.operation()
        offline = self.base / "offline"
        self.folder.rename(offline)
        self.assertEqual(self.publish(op)["status"], "applied")
        self.assertTrue(self.store.get(self.relative)["sync_pending"])
        offline.rename(self.folder)
        self.bridge.run()
        self.assertFalse(self.store.get(self.relative)["sync_pending"])
        self.assertEqual(self.store.get(self.relative)["note"].count("С телефона"), 1)

    def test_corrupt_inbox_does_not_block_valid_operation(self):
        (self.bridge.folder / ".inbox" / ".broken.json").write_text("{")
        self.assertEqual(self.publish(self.operation())["status"], "applied")
        self.assertIn("broken.json", self.bridge.status()["error"])

    def test_exchange_symlink_and_wrong_archive_are_rejected(self):
        identity = self.bridge.folder / ".identity.json"
        identity.write_text(encode({"schema": 1, "root_id": str(uuid.uuid4())}))
        self.bridge.run()
        self.assertIn("другая", self.bridge.status()["error"])


if __name__ == "__main__":
    unittest.main()
