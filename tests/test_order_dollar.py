import json
import unittest
from unittest.mock import patch

import object_orders
import order_document as document
from orders import OrderConflict, OrderStore
import test_server as fixtures

manager = fixtures.manager


class OrderDollarTests(unittest.TestCase):
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url
    path = "Клиент/Объект/2026-10-25 - Зелёный доллар"

    def setUp(self):
        fixtures.ManagerTests.setUp(self)
        mode = patch.object(manager, "DATABASE_ONLY", True)
        mode.start()
        self.patches.append(mode)
        self.folder(self.path)
        self.store = manager.order_store()
        self.order = self.store.add(self.path, {"status": "process", "financial_status": "partial", "note": "Заметка",
            "amount": 10000, "costs": 2000, "paid": 5000,
            "extra_blocks": {"Особое": "Сохранить", "Флажок": "Да", "Избранное": "Да", "Синий плюс": "Да", "Задачи": "- [ ] Позвонить"}})

    def payload(self, record=None, **changes):
        record = record or self.order
        return {"path": self.path, "id": record["id"], "revision": record["revision"], "is_dollar": True, **changes}

    def test_independent_offline_toggle_keeps_sort_date_and_history(self):
        self.assertIs(self.order["is_dollar"], False)
        self.root.rename(self.base / "offline")
        with patch.object(OrderStore, "target", side_effect=AssertionError("No cloud reads")), \
                patch("icloud_access.read_bytes", side_effect=AssertionError("No original reads")):
            marked = self.store.save_dollar(self.payload(status="done", note="Не заменять", amount="999", is_flagged=False))
            self.assertIs(marked["is_dollar"], True)
            self.assertEqual(marked["revision"], self.order["revision"] + 1)
            for field in self.order.keys() - {"is_dollar", "revision", "extra_blocks"}:
                self.assertEqual(marked[field], self.order[field], field)
            self.assertEqual({key: value for key, value in marked["extra_blocks"].items() if key != document.DOLLAR_BLOCK}, self.order["extra_blocks"])
            cleared = self.store.save_dollar(self.payload(marked, is_dollar=False))
        self.assertIs(cleared["is_dollar"], False)
        self.assertEqual(cleared["updated"], self.order["updated"])
        with self.store.connect() as db:
            history = [json.loads(row[0]) for row in db.execute("SELECT data FROM metadata_history WHERE entity='orders' AND identity=?", (self.order["id"],))]
        self.assertTrue(any(json.loads(row["extra_blocks"]).get(document.DOLLAR_BLOCK) == "Да" for row in history))
        self.assertFalse((self.base / "offline" / self.path / document.DOCUMENT).exists())

    def test_http_lists_conflicts_validation_and_registration(self):
        object_orders.ObjectOrders(self.store).refresh("Клиент/Объект")
        with patch.object(manager, "schedule_order_sync"):
            status, _, body = self.http("/api/order-dollar", "POST", json.dumps(self.payload()))
        self.assertEqual(status, 200)
        marked = json.loads(body)
        for route in ("/api/orders", self.url("/api/object-orders", "Клиент/Объект")):
            listed = json.loads(self.http(route)[2])["orders"]
            self.assertIs(listed[0]["is_dollar"], True)
        self.assertEqual(self.http("/api/order-dollar", "POST", json.dumps(self.payload()))[0], 409)
        for changes in ({"revision": None}, {"revision": True}, {"id": ""}, {"is_dollar": "true"}, {"is_dollar": 1}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.store.save_dollar(self.payload(marked, **changes))
        for changes in ({"id": "Другой UUID"}, {"path": "Клиент/Другая папка"}):
            with self.subTest(changes=changes), self.assertRaises(OrderConflict):
                self.store.save_dollar(self.payload(marked, **changes))
        self.assertEqual(self.store.get(self.path), marked)
        removed = self.store.remove({"path": self.path, "revision": marked["revision"], "confirmed": True})
        with self.assertRaises(OrderConflict):
            self.store.save_dollar(self.payload(removed))
        restored = self.store.import_folder(self.path)
        self.assertTrue(restored["is_dollar"])
        restarted = OrderStore(self.root, manager.DATA_DIR, manager.STATUS_LABELS)
        self.assertTrue(restarted.get(self.path)["is_dollar"])

    def test_card_edits_preserve_known_and_unknown_marks(self):
        marked = self.store.save_dollar(self.payload())
        saved = self.store.save({**marked, "note": "Новая заметка", "amount": "100", "costs": "20", "paid": "50"})
        self.assertTrue(saved["is_dollar"])
        self.assertTrue(saved["is_flagged"])
        self.assertTrue(saved["is_blue_plus"])
        self.assertTrue(saved["is_favorite"])
        with self.store.connect() as db:
            db.execute("UPDATE orders SET extra_blocks=?,revision=revision+1 WHERE path=?", (
                json.dumps({**saved["extra_blocks"], document.DOLLAR_BLOCK: "Будущий формат"}), self.path))
        unknown = self.store.get(self.path)
        self.assertIsNone(unknown["is_dollar"])
        with self.assertRaises(ValueError):
            self.store.save_dollar(self.payload(unknown))
        edited = self.store.save({**unknown, "note": "Ещё заметка", "amount": "100", "costs": "20", "paid": "50"})
        self.assertEqual(edited["extra_blocks"][document.DOLLAR_BLOCK], "Будущий формат")
