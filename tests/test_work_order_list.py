import json
import unittest
from pathlib import Path
from unittest.mock import patch

from orders import OrderStore
from work_order_list import WorkOrderList
import work_orders
import test_server as fixtures

manager = fixtures.manager


class WorkOrderListTests(unittest.TestCase):
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url
    scope = "# work"

    def setUp(self):
        fixtures.ManagerTests.setUp(self)
        mode = patch.object(manager, "DATABASE_ONLY", True)
        mode.start()
        self.patches.append(mode)
        for section in ("# antares", "#glass", "# HIMLEX", "# newtek", "# laser", "# freza", "# print"):
            self.folder(self.scope + "/" + section)
        self.store = manager.order_store()
        self.listing = WorkOrderList(self.store)

    def add(self, path):
        self.folder(path)
        return self.store.add(path, {"title": "Заказ поставщику", "status": "done", "amount": 12345, "note": "Комментарий"})

    def test_root_lists_first_supplier_group_and_direct_orders_without_registration(self):
        registered = self.add(self.scope + "/# antares/2026-10-20 - Заказ")
        draft = self.scope + "/#glass/Произвольное имя"
        direct = self.scope + "/2026-10-21 - Сборный"
        self.folder(draft)
        self.folder(direct)
        for path in (registered["path"] + "/00 - Событие/Материалы", self.scope + "/#glass/# bills",
                     self.scope + "/#glass/.hidden", self.scope + "/# laser/2026-10-20 - Чужой",
                     self.scope + "/# print/Прежнее задание"):
            self.folder(path)
        self.file(draft + "/original.txt", b"preserve")
        manager.save_note(self.scope, "Прежняя заметка корня")
        opened = manager.read_folder(self.scope)
        before = self.store.list(include_unregistered=True)
        with patch("order_document.load", side_effect=AssertionError("No cards")), patch("icloud_access.read_bytes", side_effect=AssertionError("No attachments")):
            self.listing.refresh(self.scope)
            data = self.listing.read(self.scope)
        rows = {row["path"]: row for row in data["orders"]}
        self.assertEqual(set(rows), {registered["path"], draft, direct})
        self.assertEqual(rows[registered["path"]]["status"], "done")
        self.assertEqual(rows[registered["path"]]["amount"], 12345)
        self.assertFalse(rows[draft]["registered"])
        self.assertEqual(rows[draft]["work_supplier"], "glass")
        self.assertEqual([group["label"].lower() for group in data["groups"]], ["antares", "himlex", "newtek", "glass", "заказы производства"])
        self.assertEqual(self.store.list(include_unregistered=True), before)
        self.assertEqual(opened["note"], "Прежняя заметка корня")
        self.assertFalse((self.root / draft / "!.txt").exists())
        self.assertEqual(json.loads(self.http("/api/orders")[2])["orders"], [])

    def test_poll_uses_only_database_and_follows_current_favorite_sections(self):
        record = self.add(self.scope + "/# antares/Заказ")
        manager.read_folder(self.scope)
        self.store.save_deadline_week({"path": record["path"], "id": record["id"], "revision": record["revision"], "week": "2026-10-26", "selected": True})
        self.root.rename(self.base / "offline")
        with patch.object(OrderStore, "target", side_effect=AssertionError("No filesystem")), patch("folder_structure.os.scandir", side_effect=AssertionError("No enumeration")):
            status, _, body = self.http(self.url("/api/work-orders", self.scope))
            self.assertEqual(status, 200, body)
            row = json.loads(body)["orders"][0]
            self.assertEqual(row["deadline_weeks"], ["2026-10-26"])
            favorite = work_orders.read_supplier_favorites(self.store, self.scope)[self.scope + "/# antares"]
            changed = work_orders.save_supplier_favorite(self.store, {"path": favorite["path"], "revision": favorite["revision"], "is_favorite": False})
            self.assertEqual(self.listing.read(self.scope)["orders"], [])
            work_orders.save_supplier_favorite(self.store, {"path": changed["path"], "revision": changed["revision"], "is_favorite": True})
            self.assertEqual(self.listing.read(self.scope)["orders"][0]["id"], record["id"])

    def test_failed_scan_retains_drafts_and_successful_scan_hides_missing_drafts(self):
        draft = self.scope + "/#glass/Папка без регистрации"
        self.folder(draft)
        manager.read_folder(self.scope)
        original = Path.iterdir
        def unavailable(folder):
            if folder == self.root / self.scope / "#glass":
                raise OSError("iCloud unavailable")
            return original(folder)
        with patch.object(Path, "iterdir", unavailable):
            self.listing.refresh(self.scope)
        self.assertIn("iCloud unavailable", self.listing.read(self.scope)["error"])
        self.assertEqual(self.listing.read(self.scope)["orders"][0]["path"], draft)
        (self.root / draft).rmdir()
        self.listing.refresh(self.scope)
        self.assertEqual(self.listing.read(self.scope)["orders"], [])

    def test_scope_validation_symlinks_spacing_and_unknown_catalog(self):
        self.scope = "#work"
        draft = self.scope + "/#Glass/Папка"
        self.folder(draft)
        (self.root / self.scope / "#Glass/Ссылка").symlink_to(self.root / "Клиент")
        manager.read_folder(self.scope)
        self.assertEqual([row["path"] for row in self.listing.read(self.scope)["orders"]], [draft])
        marker = self.listing.meta.get(self.listing.folder_kind, draft)
        self.listing.meta.put(self.listing.folder_kind, draft, {"version": 2, "future": "Сохранить"}, marker["revision"])
        self.listing.refresh(self.scope)
        self.assertEqual(self.listing.meta.get(self.listing.folder_kind, draft)["future"], "Сохранить")
        self.assertIn("Неизвестный формат", self.listing.read(self.scope)["error"])
        for path in ("Клиент", "# work/#glass", "#work/../Клиент", ""):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.listing.read(path)


if __name__ == "__main__":
    unittest.main()
