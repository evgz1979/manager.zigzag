import json
import unittest
from unittest.mock import patch

from orders import OrderConflict, OrderStore
import test_server as fixtures

manager = fixtures.manager


class OrderStatusTests(unittest.TestCase):
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    path = "Клиент/2026-00-00 - Заказ"

    def setUp(self):
        fixtures.ManagerTests.setUp(self)
        mode = patch.object(manager, "DATABASE_ONLY", True)
        mode.start()
        self.patches.append(mode)
        self.store = manager.order_store()
        self.order = self.store.add(self.path, {
            "status": "process", "financial_status": "partial", "note": "Сохранить заметку",
            "amount": 10000, "costs": 2000, "paid": 5000,
            "extra_blocks": {"Задачи": "- [ ] Позвонить", "Избранное": "Да",
                "Закупки и затраты": "- [ ] Стекло\n  Поставщики: glass", "Будущий блок": "Сохранить"}})

    def payload(self, **changes):
        return {"path": self.path, "revision": self.order["revision"], "status": "waiting", **changes}

    def test_offline_status_update_preserves_all_other_card_fields_and_history(self):
        self.root.rename(self.base / "offline")
        with patch.object(OrderStore, "target", side_effect=AssertionError("No iCloud access")):
            saved = self.store.save_status(self.payload(note="Не заменять", amount="999"))
        self.assertEqual(saved["status"], "waiting")
        self.assertEqual(saved["revision"], self.order["revision"] + 1)
        for key in self.order.keys() - {"status", "revision", "updated"}:
            self.assertEqual(saved[key], self.order[key], key)
        with self.store.connect() as db:
            history = [json.loads(row[0]) for row in db.execute(
                "SELECT data FROM metadata_history WHERE entity='orders' AND identity=?", (self.order["id"],))]
        self.assertTrue(any(row["revision"] == self.order["revision"] and row["status"] == "process" for row in history))
        self.assertEqual(self.store.get(self.path), saved)

    def test_invalid_stale_and_unregistered_updates_do_not_change_data(self):
        for invalid in (None, True, [], "missing"):
            with self.subTest(status=invalid), self.assertRaises(ValueError):
                self.store.save_status(self.payload(status=invalid))
        for revision in (None, True, "1"):
            with self.subTest(revision=revision), self.assertRaises(ValueError):
                self.store.save_status(self.payload(revision=revision))
        saved = self.store.save_status(self.payload())
        with self.assertRaises(OrderConflict):
            self.store.save_status(self.payload(status="workshop"))
        self.assertEqual(self.store.get(self.path), saved)
        removed = self.store.remove({"path": self.path, "revision": saved["revision"], "confirmed": True})
        with self.assertRaises(OrderConflict):
            self.store.save_status(self.payload(revision=removed["revision"]))
        self.assertIsNone(self.store.get(self.path))

    def test_http_partial_update_rejects_stale_version_and_exposes_new_status(self):
        with patch.object(manager, "schedule_order_sync") as schedule:
            saved = self.order
            for value in ("waiting", "offer_later"):
                with self.subTest(status=value):
                    payload = self.payload(revision=saved["revision"], status=value)
                    status, _, body = self.http("/api/order-status", "POST", json.dumps(payload))
                    self.assertEqual(status, 200)
                    saved = json.loads(body)
                    self.assertEqual(saved["status"], value)
                    self.assertEqual(self.http("/api/order-status", "POST", json.dumps(payload))[0], 409)
            self.assertEqual(schedule.call_count, 2)
            self.assertEqual(self.http("/api/order-status", "POST", json.dumps(self.payload(status="unknown")))[0], 400)
        listed = json.loads(self.http("/api/orders")[2])["orders"]
        self.assertEqual((listed[0]["status"], listed[0]["revision"]), ("offer_later", saved["revision"]))


if __name__ == "__main__":
    unittest.main()
