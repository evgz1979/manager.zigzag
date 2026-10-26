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
        for path in ("Клиент", "#work/#glass/Заказ", "#work/../Клиент", "", "#work/#print", "#work/#freza"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.listing.read(path)

    def test_etc_group_stays_last_when_a_later_supplier_is_starred(self):
        self.folder(self.scope + '/#etc')
        self.folder(self.scope + '/# cutter')
        manager.read_folder(self.scope)
        favorite = work_orders.read_supplier_favorites(self.store, self.scope)[self.scope + '/# cutter']
        work_orders.save_supplier_favorite(self.store, {**favorite, 'is_favorite': True})
        sections = self.listing.sections(self.scope)
        self.assertEqual(sections[-1]['path'], self.scope + '/#etc')
        self.assertLess(sections[-1]['position'], sections[-2]['position'])
        self.assertEqual(self.listing.read(self.scope)['groups'][-2]['key'], self.scope + '/#etc')

    def test_supplier_section_lists_its_orders_and_drafts_without_entering_orders(self):
        section = self.scope + "/#glass"
        registered = self.add(section + "/2026-10-20 - Стекло")
        draft = section + "/Произвольное имя"
        self.folder(draft)
        self.file(draft + "/original.txt", b"preserve")
        for path in (registered["path"] + "/00 - Событие/Вложение", section + "/# bills", section + "/.hidden"):
            self.folder(path)
        self.add(self.scope + "/# antares/Чужой заказ")
        (self.root / section / "Ссылка").symlink_to(self.root / "Клиент")
        manager.save_note(section, "Заметка поставщика")
        opened = manager.read_folder(section)
        before = self.store.list(include_unregistered=True)
        with patch("order_document.load", side_effect=AssertionError("No cards")), patch("icloud_access.read_bytes", side_effect=AssertionError("No contents")):
            self.listing.refresh(section)
            data = self.listing.read(section)
        rows = {row["path"]: row for row in data["orders"]}
        self.assertEqual(set(rows), {registered["path"], draft})
        self.assertFalse(rows[draft]["registered"])
        self.assertEqual(rows[registered["path"]]["id"], registered["id"])
        self.assertEqual([group["key"] for group in data["groups"]], [section])
        self.assertEqual(rows[draft]["work_supplier_color"], data["groups"][0]["color"])
        self.assertTrue(opened["workOrderList"])
        self.assertEqual(opened["note"], "Заметка поставщика")
        self.assertEqual(self.store.list(include_unregistered=True), before)
        self.assertFalse((self.root / draft / "!.txt").exists())

    def test_section_poll_reads_sqlite_with_current_weeks_without_a_favorite(self):
        section = self.scope + "/# laser"
        record = self.add(section + "/2026-10-21 - Резка")
        manager.read_folder(section)
        record = self.store.save_deadline_week({"path": record["path"], "id": record["id"], "revision": record["revision"],
                                                "week": "2026-10-26", "selected": True})
        self.root.rename(self.base / "offline")
        with patch.object(OrderStore, "target", side_effect=AssertionError("No filesystem")), patch("folder_structure.os.scandir", side_effect=AssertionError("No enumeration")):
            status, _, body = self.http(self.url("/api/work-orders", section))
        self.assertEqual(status, 200, body)
        data = json.loads(body)
        self.assertEqual([row["id"] for row in data["orders"]], [record["id"]])
        self.assertEqual(data["orders"][0]["deadline_weeks"], ["2026-10-26"])
        self.assertEqual(data["groups"][0]["key"], section)

    def test_root_refresh_does_not_hide_unstarred_section_catalog_and_failed_section_keeps_it(self):
        section = self.scope + "/# laser"
        draft = section + "/Заказ без регистрации"
        sibling = self.scope + "/#glass/Другой заказ"
        self.folder(draft)
        self.folder(sibling)
        manager.read_folder(section)
        manager.read_folder(self.scope)
        self.assertEqual([row["path"] for row in self.listing.read(section)["orders"]], [draft])
        self.assertEqual([row["path"] for row in self.listing.read(self.scope)["orders"]], [sibling])
        original = Path.iterdir
        def unavailable(folder):
            if folder == self.root / section:
                raise OSError("iCloud unavailable")
            return original(folder)
        with patch.object(Path, "iterdir", unavailable):
            self.listing.refresh(section)
        self.assertIn("iCloud unavailable", self.listing.read(section)["error"])
        self.assertEqual([row["path"] for row in self.listing.read(section)["orders"]], [draft])
        (self.root / draft).rmdir()
        self.listing.refresh(section)
        self.assertEqual(self.listing.read(section)["orders"], [])
        self.assertEqual([row["path"] for row in self.listing.read(self.scope)["orders"]], [sibling])

    def test_legacy_glass_etc_and_other_sections_use_table_but_special_editors_keep_their_views(self):
        for section in ("#glass", self.scope + "/# etc", self.scope + "/Поставщик без решётки"):
            with self.subTest(section=section):
                self.folder(section + "/2026-10-21 - Заказ")
                opened = manager.read_folder(section)
                self.assertTrue(opened["workOrderList"])
                self.assertEqual([row["path"] for row in opened["objectOrders"]["orders"]], [section + "/2026-10-21 - Заказ"])
        for section in (self.scope + "/# print", self.scope + "/# freza"):
            opened = manager.read_folder(section)
            self.assertFalse(opened["workOrderList"])
            self.assertIsNone(opened["objectOrders"])

    def test_folder_date_sorts_old_orders_by_their_name_not_creation_update_title_or_favorite(self):
        section = self.scope + "/#glass"
        newer = self.add(section + "/2026-10-20 - Новая дата")
        older = self.add(section + "/2024-01-12 - Старый заказ добавлен сейчас")
        self.store.save_favorite({"path": older["path"], "revision": older["revision"], "is_favorite": True})
        with self.store.connect() as db:
            db.execute("UPDATE orders SET title='Дата в заголовке 2030-01-01',updated=9999999999 WHERE id=?", (older["id"],))
            db.execute("UPDATE orders SET updated=1 WHERE id=?", (newer["id"],))
        manager.read_folder(section)
        for scope in (section, self.scope):
            if scope == self.scope:
                manager.read_folder(scope)
            data = self.listing.read(scope)
            self.assertEqual([row["id"] for row in data["orders"]], [newer["id"], older["id"]])
            self.assertEqual([row["folder_date"] for row in data["orders"]], ["2026-10-20", "2024-01-12"])

    def test_folder_date_handles_partial_dates_short_years_and_missing_dates(self):
        section = self.scope + "/#glass"
        names = ["Без даты", "2026-02-30 - Ошибка даты", "2026-00-00 - Только год",
                 "2026-10-00 - Только месяц", "26-10-03 - Короткий год", "2025-12-31 - Прошлый год"]
        for name in names:
            self.folder(section + "/" + name)
        manager.read_folder(section)
        rows = self.listing.read(section)["orders"]
        self.assertEqual([row["folder_date"] for row in rows], ["2026-10-03", "2026-10-00", "2026-00-00", "2025-12-31", None, None])
        self.assertEqual({row["path"] for row in rows[-2:]}, {section + "/Без даты", section + "/2026-02-30 - Ошибка даты"})


if __name__ == "__main__":
    unittest.main()
