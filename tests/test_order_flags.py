import json
import unittest
from unittest.mock import patch

import object_orders
import order_document as document
from orders import OrderConflict, OrderStore
import test_server as fixtures

manager = fixtures.manager


class OrderFlagTests(unittest.TestCase):
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url
    path = "Клиент/Объект/2026-10-25 - Проверка"

    def setUp(self):
        fixtures.ManagerTests.setUp(self)
        mode = patch.object(manager, "DATABASE_ONLY", True)
        mode.start()
        self.patches.append(mode)
        self.folder(self.path)
        self.store = manager.order_store()
        self.order = self.store.add(self.path, {"status": "process", "financial_status": "partial", "note": "Заметка",
            "amount": 10000, "costs": 2000, "paid": 5000,
            "extra_blocks": {"Особое": "Сохранить", "Избранное": "Да", "Задачи": "- [ ] Позвонить"}})

    def payload(self, record=None, **changes):
        record = record or self.order
        return {"path": self.path, "id": record["id"], "revision": record["revision"], "is_flagged": True, **changes}

    def test_flag_is_independent_offline_and_does_not_touch_sort_date(self):
        self.assertIs(self.order["is_flagged"], False)
        self.root.rename(self.base / "offline")
        with patch.object(OrderStore, "target", side_effect=AssertionError("No cloud reads")), \
                patch("icloud_access.read_bytes", side_effect=AssertionError("No original reads")):
            flagged = self.store.save_flag(self.payload(status="done", note="Не заменять", amount="999"))
            self.assertIs(flagged["is_flagged"], True)
            self.assertEqual(flagged["revision"], self.order["revision"] + 1)
            for field in self.order.keys() - {"is_flagged", "revision", "extra_blocks"}:
                self.assertEqual(flagged[field], self.order[field], field)
            for name, value in self.order["extra_blocks"].items():
                self.assertEqual(flagged["extra_blocks"][name], value)
            cleared = self.store.save_flag(self.payload(flagged, is_flagged=False))
        self.assertIs(cleared["is_flagged"], False)
        self.assertEqual(cleared["updated"], self.order["updated"])
        with self.store.connect() as db:
            history = [json.loads(row[0]) for row in db.execute("SELECT data FROM metadata_history WHERE entity='orders' AND identity=?", (self.order["id"],))]
        self.assertTrue(any(json.loads(row["extra_blocks"]).get(document.FLAG_BLOCK) == "Да" for row in history))
        self.assertFalse((self.base / "offline" / self.path / document.DOCUMENT).exists())

    def test_http_lists_version_identity_and_registration(self):
        object_orders.ObjectOrders(self.store).refresh("Клиент/Объект")
        with patch.object(manager, "schedule_order_sync") as schedule:
            status, _, body = self.http("/api/order-flag", "POST", json.dumps(self.payload()))
            self.assertEqual(status, 200)
            schedule.assert_called_once()
        flagged = json.loads(body)
        for route in ("/api/orders", self.url("/api/object-orders", "Клиент/Объект")):
            listed = json.loads(self.http(route)[2])["orders"]
            self.assertIs(listed[0]["is_flagged"], True)
            self.assertEqual(listed[0]["updated"], self.order["updated"])
        for payload in (self.payload(), self.payload(flagged, id="Чужой UUID"), self.payload(flagged, path="Клиент/Другая папка")):
            with self.assertRaises(OrderConflict):
                self.store.save_flag(payload)
        for changes in ({"revision": None}, {"revision": True}, {"id": ""}, {"is_flagged": "true"}, {"is_flagged": 1}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.store.save_flag(self.payload(flagged, **changes))
        self.assertEqual(self.store.get(self.path), flagged)
        removed = self.store.remove({"path": self.path, "revision": flagged["revision"], "confirmed": True})
        with self.assertRaises(OrderConflict):
            self.store.save_flag(self.payload(removed))
        restored = self.store.import_folder(self.path)
        self.assertTrue(restored["is_flagged"])
        restarted = OrderStore(self.root, manager.DATA_DIR, manager.STATUS_LABELS)
        self.assertTrue(restarted.get(self.path)["is_flagged"])

    def test_unknown_flag_survives_card_edits_without_replacement(self):
        unknown = "Будущая отметка"
        with self.store.connect() as db:
            db.execute("UPDATE orders SET extra_blocks=?,revision=revision+1 WHERE path=?", (
                json.dumps({**self.order["extra_blocks"], document.FLAG_BLOCK: unknown}), self.path))
        record = self.store.get(self.path)
        self.assertIsNone(record["is_flagged"])
        with self.assertRaises(ValueError):
            self.store.save_flag(self.payload(record))
        saved = self.store.save({**record, "note": "Новая заметка", "amount": "100", "costs": "20", "paid": "50"})
        self.assertEqual(saved["extra_blocks"][document.FLAG_BLOCK], unknown)

    def test_card_save_keeps_flag(self):
        flagged = self.store.save_flag(self.payload())
        saved = self.store.save({**flagged, "note": "Новая заметка", "amount": "100", "costs": "20", "paid": "50"})
        self.assertTrue(saved["is_flagged"])
        self.assertTrue(saved["is_favorite"])
