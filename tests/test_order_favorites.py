import json
import unittest
from unittest.mock import patch

import order_document as document
from orders import OrderConflict, OrderStore
import test_server as fixtures

manager = fixtures.manager


class OrderFavoriteTests(unittest.TestCase):
    setUp = fixtures.ManagerTests.setUp
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url
    path = "Клиент/2026-00-00 - Заказ"

    def add(self, blocks=None):
        return manager.order_store().add(self.path, {"status": "process", "financial_status": "partial", "note": "Сохранить заметку",
            "amount": 10000, "costs": 2000, "paid": 5000, "extra_blocks": blocks or {
                "Задачи": "- [ ] Обычная задача", "Закупки и затраты": "- [ ] Стекло\n  Поставщики: glass", "Особое": "Будущий блок"}})

    def toggle(self, record, value):
        return manager.order_store().save_favorite({"path": self.path, "revision": record["revision"], "is_favorite": value})

    def test_partial_update_works_offline_preserves_card_and_checks_version(self):
        before = self.add()
        self.assertIs(before["is_favorite"], False)
        self.root.rename(self.base / "offline")
        with patch.object(OrderStore, "target", side_effect=AssertionError("No iCloud on star or list")):
            starred = self.toggle(before, True)
            self.assertTrue(manager.order_store().list()[0]["is_favorite"])
        self.assertTrue(starred["sync_pending"])
        self.assertEqual(starred["revision"], before["revision"] + 1)
        for field in ("id", "title", "status", "financial_status", "note", "amount", "costs", "paid", "todo_items", "purchase_items"):
            self.assertEqual(starred[field], before[field])
        for name, text in before["extra_blocks"].items():
            self.assertEqual(starred["extra_blocks"][name], text)
        with self.assertRaises(OrderConflict):
            self.toggle(before, False)
        for invalid in (None, 1, "false", []):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                self.toggle(starred, invalid)
        self.assertEqual(manager.order_store().get(self.path), starred)

    def test_export_retry_restart_restore_and_unstar_do_not_resurrect_old_star(self):
        store = manager.order_store()
        starred = self.toggle(self.add(), True)
        store.sync()
        self.assertIn("[Избранное]\nДа", (self.root / self.path / document.DOCUMENT).read_text())
        rebuilt = OrderStore(self.root, self.base / "rebuilt", manager.STATUS_LABELS, database_only=False).import_folder(self.path)
        self.assertTrue(rebuilt["is_favorite"])
        unstarred = self.toggle(store.get(self.path), False)
        with patch.object(document, "atomic_write", side_effect=OSError("iCloud занят")):
            store.sync()
        pending = store.get(self.path)
        self.assertFalse(pending["is_favorite"])
        self.assertTrue(pending["sync_pending"])
        self.assertIn("iCloud занят", pending["sync_error"])
        restarted = OrderStore(self.root, manager.DATA_DIR, manager.STATUS_LABELS, database_only=False)
        self.assertFalse(restarted.get(self.path)["is_favorite"])
        restarted.sync()
        self.assertFalse(restarted.get(self.path)["sync_pending"])
        self.assertEqual(restarted.get(self.path)["extra_blocks"], unstarred["extra_blocks"])
        body = (self.root / self.path / document.DOCUMENT).read_text()
        self.assertIn("[Избранное]\nНет", body)
        restored = OrderStore(self.root, self.base / "rebuilt-off", manager.STATUS_LABELS, database_only=False).import_folder(self.path)
        self.assertFalse(restored["is_favorite"])
        self.assertEqual(restored["id"], starred["id"])

    def test_unknown_block_survives_other_edits_and_cannot_be_replaced_by_star(self):
        before = self.add({document.FAVORITE_BLOCK: "Особая будущая отметка", "Особое": "Не менять"})
        self.assertIsNone(before["is_favorite"])
        with self.assertRaises(ValueError):
            self.toggle(before, True)
        payload = {**before, "note": "Новая заметка", "amount": "100", "costs": "20", "paid": "50"}
        payload.pop("todo_items")
        payload.pop("purchase_items")
        saved = manager.order_store().save(payload)
        manager.order_store().sync()
        self.assertEqual(saved["extra_blocks"], before["extra_blocks"])
        self.assertIn("Особая будущая отметка", (self.root / self.path / document.DOCUMENT).read_text())

    def test_http_switch_is_versioned_and_list_uses_database(self):
        before = self.add()
        payload = {"path": self.path, "revision": before["revision"], "is_favorite": True}
        with patch.object(manager, "schedule_order_sync") as schedule:
            status, _, body = self.http("/api/order-favorite", "POST", json.dumps(payload))
            self.assertEqual(status, 200)
            self.assertTrue(json.loads(body)["is_favorite"])
            schedule.assert_called_once()
            self.assertEqual(self.http("/api/order-favorite", "POST", json.dumps(payload))[0], 409)
        with patch.object(OrderStore, "target", side_effect=AssertionError("No iCloud on main list")):
            listed = json.loads(self.http("/api/orders")[2])["orders"]
        self.assertTrue(listed[0]["is_favorite"])
        removed = manager.order_store().remove({"path": self.path, "revision": listed[0]["revision"], "confirmed": True})
        with self.assertRaises(OrderConflict):
            self.toggle(removed, False)
        self.assertTrue(manager.order_store().get(self.path, include_unregistered=True)["is_favorite"])
