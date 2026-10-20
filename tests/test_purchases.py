import json
import unittest
from unittest.mock import patch

import order_document as document
from orders import OrderConflict, OrderStore
import test_server as fixtures

manager = fixtures.manager


class PurchaseTests(unittest.TestCase):
    setUp = fixtures.ManagerTests.setUp
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url
    path = "Клиент/2026-00-00 - Заказ"

    def add(self, blocks=None):
        return manager.order_store().add(self.path, {"status": "process", "financial_status": "partial", "note": "Не менять",
            "amount": 10000, "costs": 2000, "paid": 5000, "extra_blocks": blocks or {"Задачи": "- [ ] Обычная задача", "Особое": "Будущий блок"}})

    def save(self, record, items):
        return manager.order_store().save({**record, "amount": "100", "costs": "20", "paid": "50", "purchase_items": items})

    def test_readable_items_supplier_buttons_and_completion_round_trip_independently(self):
        items = [{"text": "Стеклопакеты [Поставщики: glass]", "done": False, "suppliers": ["glass", "tbm"]},
                 {"text": "Профиль и комплектующие", "done": True, "suppliers": list(document.PURCHASE_SUPPLIERS)},
                 {"text": "Без поставщика", "done": False, "suppliers": []}]
        blocks = document.write_purchases({"Особое": "Не терять"}, items)
        self.assertIn("  Поставщики: glass, tbm", blocks[document.PURCHASE_BLOCK])
        self.assertIn("  Поставщики: —", blocks[document.PURCHASE_BLOCK])
        parsed = document.parse(document.render({"note": "", "extra_blocks": blocks}, manager.STATUS_LABELS), manager.STATUS_LABELS)
        self.assertEqual(document.read_purchases(parsed["extra_blocks"]), items)
        self.assertEqual(parsed["extra_blocks"]["Особое"], "Не терять")
        self.assertEqual(document.read_purchases({document.PURCHASE_BLOCK: "- [ ] Старый список"}), [{"text": "Старый список", "done": False, "suppliers": []}])
        for suppliers in (["unknown"], ["tbm", "tbm"], True, [None], [[]]):
            with self.assertRaises(ValueError):
                document.write_purchases({}, [{"text": "Проверка", "done": False, "suppliers": suppliers}])

    def test_database_save_is_offline_versioned_and_does_not_change_todos_money_or_status(self):
        before = self.add()
        self.root.rename(self.base / "offline")
        with patch.object(manager.OrderStore, "target", side_effect=AssertionError("No iCloud on save")):
            saved = self.save(before, [{"text": "Заказать стекло", "done": False, "suppliers": ["glass", "remex"]}])
        self.assertTrue(saved["sync_pending"])
        for key in ("id", "status", "financial_status", "note", "amount", "costs", "paid", "todo_items"):
            self.assertEqual(saved[key], before[key])
        self.assertEqual(saved["extra_blocks"]["Особое"], before["extra_blocks"]["Особое"])
        self.assertEqual(saved["purchase_items"][0]["suppliers"], ["glass", "remex"])
        with self.assertRaises(OrderConflict):
            self.save(before, [])

    def test_failed_export_restart_turning_off_deleting_and_rebuild_do_not_restore_old_values(self):
        store = manager.order_store()
        first = self.save(self.add(), [{"text": "Профиль", "done": False, "suppliers": ["newtek", "antares"]}])
        store.sync()
        cleared = self.save(store.get(self.path), [{"text": "Профиль изменён", "done": True, "suppliers": []}])
        with patch.object(manager.order_document, "atomic_write", side_effect=OSError("iCloud занят")):
            store.sync()
        self.assertTrue(store.get(self.path)["sync_pending"])
        restarted = OrderStore(self.root, manager.DATA_DIR, manager.STATUS_LABELS)
        self.assertEqual(restarted.get(self.path)["purchase_items"], cleared["purchase_items"])
        restarted.sync()
        self.assertFalse(restarted.get(self.path)["sync_pending"])
        rebuilt = OrderStore(self.root, self.base / "rebuilt", manager.STATUS_LABELS).import_folder(self.path)
        self.assertEqual(rebuilt["purchase_items"], cleared["purchase_items"])
        self.assertNotEqual(rebuilt["purchase_items"], first["purchase_items"])
        deleted = self.save(restarted.get(self.path), [])
        restarted.sync()
        self.assertEqual(restarted.get(self.path)["purchase_items"], [])
        body = document.load(self.root / self.path, manager.STATUS_LABELS)["extra_blocks"]
        self.assertIn(document.PURCHASE_BLOCK, body)
        self.assertEqual(body[document.PURCHASE_BLOCK], "")
        self.assertEqual(document.read_purchases(body), deleted["purchase_items"])

    def test_unknown_block_or_future_supplier_is_preserved_during_other_edits(self):
        for raw in ("Свободный прежний текст\nНе удалять", "- [ ] Новый поставщик\n  Поставщики: future-vendor"):
            with self.subTest(raw=raw):
                before = self.add({document.PURCHASE_BLOCK: raw, "Особое": "Не менять"})
                # Simulate an imported opaque block in this fixture's order.
                with manager.order_store().connect() as db:
                    db.execute("UPDATE orders SET extra_blocks=? WHERE path=?", (json.dumps({document.PURCHASE_BLOCK: raw, "Особое": "Не менять"}), self.path))
                before = manager.order_store().get(self.path)
                self.assertIsNone(before["purchase_items"])
                payload = {**before, "amount": "100", "costs": "20", "paid": "50"}
                payload.pop("purchase_items")
                saved = manager.order_store().save(payload)
                self.assertEqual(saved["extra_blocks"][document.PURCHASE_BLOCK], raw)
                with self.assertRaises(ValueError):
                    self.save(saved, [])
                self.assertEqual(manager.order_store().get(self.path), saved)

    def test_unregistered_folder_and_http_save_restore_buttons_after_reload_and_registration(self):
        items = [{"text": "Купить профиль", "done": False, "suppliers": ["antares", "tbm"]}]
        status, _, _ = self.http("/api/status", "POST", json.dumps({"path": self.path, "status": "process", "financial_status": "partial", "note": "Заметка",
            "todo_items": [{"text": "Обычная задача", "done": False}], "purchase_items": items}))
        self.assertEqual(status, 200)
        folder = json.loads(self.http(self.url("/api/folder", self.path))[2])
        self.assertEqual(folder["purchase_items"], items)
        self.assertEqual(folder["todo_items"], [{"text": "Обычная задача", "done": False}])
        registered = manager.order_store().import_folder(self.path)
        self.assertEqual(registered["purchase_items"], items)
        with patch.object(manager, "schedule_order_sync"):
            status, _, body = self.http("/api/order-save", "POST", json.dumps({**registered, "amount": "", "costs": "", "paid": "",
                "purchase_items": [{**items[0], "suppliers": ["tbm"]}]}))
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["purchase_items"][0]["suppliers"], ["tbm"])
        self.assertEqual(json.loads(self.http(self.url("/api/order", self.path))[2])["purchase_items"][0]["suppliers"], ["tbm"])
