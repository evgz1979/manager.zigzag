import json
import unittest
import unicodedata
from pathlib import Path
from unittest.mock import patch

import object_orders
import folder_rename
import folder_rename_undo
from orders import OrderStore
from folder_notes import FolderNotes
import test_server as fixtures

manager = fixtures.manager


class ObjectOrderTests(unittest.TestCase):
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url
    scope = "Клиент/Объект"

    def setUp(self):
        fixtures.ManagerTests.setUp(self)
        mode = patch.object(manager, "DATABASE_ONLY", True)
        mode.start()
        self.patches.append(mode)
        self.folder(self.scope)
        self.store = manager.order_store()
        self.listing = object_orders.ObjectOrders(self.store)

    def add(self, name, status="new"):
        path = self.scope + "/" + name
        self.folder(path)
        return self.store.add(path, {"status": status, "note": "Заметка " + name})

    def test_registered_unregistered_years_and_boundaries_without_reading_documents(self):
        active = self.add("2026-10-20 - Активный")
        done = self.add("2026/2026-01-00 - Готовый", "done")
        cancelled = self.add("2025/2025-01-00 - Отмена", "cancelled")
        draft = self.scope + "/2026/2026-02-00 - Не добавлен"
        self.folder(draft)
        notes = FolderNotes(self.store)
        note = notes.read(draft)
        notes.save({"path": draft, "revision": note["revision"], "note": "Только черновик"})
        for path in (active["path"] + "/00 - Событие/2026-10-21 - Вложение", self.scope + "/# files/2026-10-21 - Служебное",
                     "Клиент/Объект 2/2026-10-21 - Чужой"):
            self.folder(path)
        self.file(active["path"] + "/original.pdf", b"do not read")
        before = self.store.list(include_unregistered=True)
        with patch("order_document.load", side_effect=AssertionError("No legacy cards")), patch("icloud_access.read_bytes", side_effect=AssertionError("No file contents")):
            self.listing.refresh(self.scope)
            listed = self.listing.read(self.scope)
        rows = {row["path"]: row for row in listed["orders"]}
        self.assertEqual(set(rows), {active["path"], done["path"], cancelled["path"], draft})
        self.assertTrue(rows[done["path"]]["registered"])
        self.assertFalse(rows[draft]["registered"])
        self.assertEqual({row["object"] for row in rows.values()}, {"Объект"})
        self.assertEqual({row["object_path"] for row in rows.values()}, {self.scope})
        self.assertEqual(rows[draft]["note"], "Только черновик")
        self.assertIsNone(rows[draft]["id"])
        self.assertEqual(self.store.list(include_unregistered=True), before)
        self.assertEqual((self.root / active["path"] / "original.pdf").read_bytes(), b"do not read")
        self.assertEqual(len(listed["deadline_week_options"]), 16)

    def test_metadata_poll_reads_only_sqlite_and_receives_updated_status_and_weeks(self):
        record = self.add("2026-10-20 - Заказ")
        self.listing.refresh(self.scope)
        record = self.store.save_status({"path": record["path"], "revision": record["revision"], "status": "done"})
        self.store.save_deadline_week({"path": record["path"], "id": record["id"], "revision": record["revision"], "week": "2026-10-19", "selected": True})
        self.root.rename(self.base / "offline")
        with patch.object(OrderStore, "target", side_effect=AssertionError("No target access")), patch("folder_structure.os.scandir", side_effect=AssertionError("No folder enumeration")):
            row = self.listing.read(self.scope)["orders"][0]
            status, _, body = self.http(self.url("/api/object-orders", self.scope))
        self.assertEqual(status, 200)
        self.assertEqual((row["status"], row["deadline_weeks"]), ("done", ["2026-10-19"]))
        self.assertEqual(json.loads(body)["orders"][0]["id"], record["id"])

    def test_incomplete_scan_retains_last_catalog_and_full_scan_hides_missing_drafts(self):
        registered = self.add("2026-10-20 - В базе")
        draft = self.scope + "/2025/2025-01-00 - Папка"
        self.folder(draft)
        self.listing.refresh(self.scope)
        original = Path.iterdir
        def unavailable(folder):
            if folder == self.root / self.scope / "2025":
                raise OSError("iCloud unavailable")
            return original(folder)
        with patch.object(Path, "iterdir", unavailable):
            self.listing.refresh(self.scope)
        listed = self.listing.read(self.scope)
        self.assertIn("iCloud unavailable", listed["error"])
        self.assertEqual({row["path"] for row in listed["orders"]}, {registered["path"], draft})
        (self.root / draft).rmdir()
        self.listing.refresh(self.scope)
        self.assertEqual([row["path"] for row in self.listing.read(self.scope)["orders"]], [registered["path"]])

    def test_unregistered_working_record_wins_over_old_draft_without_registration(self):
        record = self.add("2026-10-20 - Снят")
        removed = self.store.remove({"path": record["path"], "revision": record["revision"], "confirmed": True})
        self.listing.refresh(self.scope)
        row = self.listing.read(self.scope)["orders"][0]
        self.assertEqual((row["id"], row["revision"], row["note"]), (removed["id"], removed["revision"], removed["note"]))
        self.assertFalse(row["registered"])
        self.assertIsNone(self.store.get(record["path"]))

    def test_object_open_keeps_note_and_does_not_register_order_folders(self):
        draft = self.scope + "/2026-10-20 - Папка"
        self.folder(draft)
        folder = manager.read_folder(self.scope)
        self.assertEqual(folder["folderKind"], "object")
        self.assertTrue(folder["noteOnly"])
        self.assertEqual([row["path"] for row in folder["objectOrders"]["orders"]], [draft])
        self.assertEqual(self.store.list(), [])
        self.assertFalse((self.root / draft / "!.txt").exists())

    def test_inactive_descendants_and_symlinks_do_not_mix_neighboring_objects(self):
        own = self.add("2026-10-20 - Свой")
        nested = self.add("Подобъект/2026-10-21 - Вложенный")
        outside = self.root / "Чужой"
        outside.mkdir()
        (outside / "2026-10-21 - Не наш").mkdir()
        (self.root / self.scope / "Ссылка").symlink_to(outside, target_is_directory=True)
        self.listing.refresh(self.scope)
        inactive = {"Клиент", self.scope, self.scope + "/Подобъект"}
        self.assertEqual([row["path"] for row in self.listing.read(self.scope, inactive=inactive)["orders"]], [own["path"]])
        self.assertEqual({row["path"] for row in self.listing.read(self.scope, inactive=inactive, show_inactive=True)["orders"]},
                         {own["path"], nested["path"]})

    def test_unknown_catalog_is_preserved_and_incomplete_state_is_reported(self):
        record = self.add("2026-10-20 - Заказ")
        self.listing.refresh(self.scope)
        marker = self.listing.meta.get(object_orders.FOLDER, record["path"])
        self.listing.meta.put(object_orders.FOLDER, record["path"], {"version": 2, "future": "Сохранить"}, marker["revision"])
        self.listing.refresh(self.scope)
        self.assertEqual(self.listing.meta.get(object_orders.FOLDER, record["path"])["future"], "Сохранить")
        self.assertIn("Неизвестный формат", self.listing.read(self.scope)["error"])
        self.assertEqual(self.listing.read(self.scope)["orders"][0]["id"], record["id"])

    def test_erroneous_registered_container_does_not_hide_real_child_orders(self):
        year = self.scope + "/2026"
        self.file(year + "/original.txt", b"year work")
        self.store.add(year, {"status": "new", "note": "Прежняя карточка"})
        child = year + "/2026-10-20 - Дочерний"
        self.folder(child)
        self.listing.refresh(self.scope)
        self.assertEqual({row["path"] for row in self.listing.read(self.scope)["orders"]}, {year, child})

    def test_object_rename_and_undo_keep_catalog_identity_and_sqlite_only_read(self):
        order = self.add("2026-10-20 - Заказ")
        draft = self.scope + "/2026-10-21 - Папка"
        self.folder(draft)
        self.listing.refresh(self.scope)
        marker = self.listing.meta.get(object_orders.FOLDER, draft)
        result = folder_rename.rename(self.store, {**folder_rename.preview(self.store, self.scope), "name": "Другой объект"})
        destination = result["path"]
        renamed_draft = destination + "/" + Path(draft).name
        with patch("folder_structure.os.scandir", side_effect=AssertionError("No catalog rescan")):
            self.assertEqual({row["path"] for row in self.listing.read(destination)["orders"]},
                             {destination + "/" + Path(order["path"]).name, renamed_draft})
        moved = self.listing.meta.get(object_orders.FOLDER, renamed_draft)
        self.assertEqual(moved["revision"].split(":")[0], marker["revision"].split(":")[0])
        folder_rename_undo.undo(self.root / result["journal"], perform=True)
        self.assertEqual({row["path"] for row in self.listing.read(self.scope)["orders"]}, {order["path"], draft})

    def test_unicode_equivalent_catalog_paths_do_not_duplicate_registered_orders(self):
        scope = unicodedata.normalize("NFD", "Клиент/Новый объект")
        path = scope + "/" + unicodedata.normalize("NFD", "2026-10-20 - Первый павильон")
        self.folder(path)
        record = self.store.add(path, {"status": "new", "note": "Сохранить путь и UUID"})
        self.listing.refresh(scope)
        rows = self.listing.read(unicodedata.normalize("NFC", scope))["orders"]
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0]["id"], rows[0]["path"], rows[0]["revision"]),
                         (record["id"], record["path"], record["revision"]))
        self.assertTrue(rows[0]["registered"])
        self.assertEqual(self.store.get(path), record)


if __name__ == "__main__":
    unittest.main()
