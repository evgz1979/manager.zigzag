import json
import unittest
from unittest.mock import patch
import test_server as fixtures
from folder_structure import folder_role

manager = fixtures.manager


class FolderStructureTests(unittest.TestCase):
    setUp = fixtures.ManagerTests.setUp
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url

    def test_clients_objects_year_groups_and_common_orders_are_distinct(self):
        paths = {
            "Клиент": "client", "Клиент/Адрес": "object", "Клиент/Адрес/2026": "year",
            "Клиент/Адрес/2026/2026-00-00 - работа": "order",
            "Клиент/Адрес/26 09 00 - работа": "order",
            "Клиент/00 - разное": "group", "Клиент/00 - разное/00001 - работа": "order",
            "Клиент/00002 - разово": "order", "01 - мелкие": "group",
            "01 - мелкие/26 00 00 - работа": "order",
            "Клиент/Адрес/2025": "order", "Клиент/Адрес/2025/01 - работы": "event",
            "Клиент/Адрес/2024": "year", "Клиент/Адрес/2024/00001 - работа": "order",
            "Клиент/Адрес/2026/2026-00-00 - работа/01": "event",
            "Клиент/Адрес/2026/2026-00-00 - работа/#cdr": "service",
            "Клиент/Адрес/2026-00-15 - ошибка": "invalid",
            "Клиент/Адрес/2026-02-30 - ошибка": "invalid",
            "Клиент/Адрес/2026-09": "invalid",
            "# moneys": "moneys_root", "#moneys": "moneys_root",
            "# moneys/# счета": "moneys_section", "# moneys/2026-10-20 - Сверка": "moneys_section",
            "Клиент/# moneys": "service", "# work/# moneys": "work_section",
            "# moneys/# Зп/2026-06 июнь": "order", "# work/# laser/01": "order",
            "# moneys/# Зп/2026-06 июнь/00 - Начисление": "event",
        }
        for path in paths:
            self.folder(path)
        for path, expected in paths.items():
            with self.subTest(path=path):
                role = folder_role(self.root, path)
                self.assertEqual(role["folderKind"], expected)
                self.assertEqual(role["canRegisterOrder"], expected == "order")
        with patch("folder_structure.os.scandir", side_effect=AssertionError("Do not inspect events or service subtrees")):
            self.assertEqual(folder_role(self.root, "Клиент/26 00 00/01/внутри")["folderKind"], "event")
            self.assertEqual(folder_role(self.root, "# docs/внутри")["folderKind"], "service")

    def test_moneys_container_preserves_notes_and_skips_attachments_and_order_import(self):
        root = "# moneys"
        child = root + "/2026-10-20 - Сверка"
        self.folder(root + "/# счета")
        self.folder(child)
        body = manager.order_document.render({"status": "done", "note": "Финансовый раздел",
            "extra_blocks": {"Сверка": "Сохранить сведения"}}, manager.STATUS_LABELS).encode()
        self.file(root + "/!.txt", body)
        self.file(child + "/!.txt", body)
        self.file(child + "/выписка.txt", b"financial document")
        with patch.object(manager.os, "walk", side_effect=AssertionError("Do not collect financial attachments")):
            opened = manager.read_folder(root)
        self.assertEqual(opened["filesScope"], "subfolders")
        self.assertEqual(opened["files"], [])
        self.assertEqual([item["name"] for item in opened["directories"]], ["# счета", "2026-10-20 - Сверка"])
        self.assertTrue(opened["noteOnly"])
        self.assertEqual(opened["note"], "Финансовый раздел")
        self.assertFalse(opened["service"])
        self.assertFalse(opened["canCreateOrderFolder"])
        self.assertFalse(opened["canCreateEventFolder"])
        self.assertIn(root, [item["path"] for item in manager.read_tree()["auxiliary"]])
        manager.save_note(root, "Новая заметка финансов")
        saved = manager.order_document.load(self.root / root, manager.STATUS_LABELS)
        self.assertEqual(saved["note"], "Новая заметка финансов")
        self.assertEqual(saved["extra_blocks"], {"Сверка": "Сохранить сведения"})
        store = manager.order_store()
        for path in (root, child, root + "/# счета"):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    store.add(path, {})
        with self.assertRaises(ValueError):
            manager.order_folders.create(self.root, root, "2026-10-20", "Не создавать")
        progress = {"folders": 0, "added": 0, "errors": []}
        store.discover(manager.read_status_document, progress)
        self.assertEqual((progress["added"], progress["errors"]), (0, []))
        self.assertEqual((self.root / child / "!.txt").read_bytes(), body)
        self.assertEqual(manager.read_folder(child)["filesScope"], "subfolders")
        self.assertEqual(manager.read_folder(child)["files"], [])

    def test_containers_are_note_only_and_cards_do_not_bypass_registration_guard(self):
        order = "Клиент/Адрес/2026/2026-10-00 - работа"
        containers = ("Клиент", "Клиент/Адрес", "Клиент/Адрес/2026", "01 - мелкие")
        self.folder(order)
        store = manager.order_store()
        for path in (*containers, order):
            self.folder(path)
            self.file(path + "/!.txt", manager.order_document.render({"status": "done", "note": "Сохранить",
                "financial_status": "partial", "extra_blocks": {"Контакт": "Телефон клиента"}}, manager.STATUS_LABELS).encode())
        for path in containers:
            with self.subTest(path=path):
                original = (self.root / path / "!.txt").read_bytes()
                folder = manager.read_folder(path)
                self.assertTrue(folder["noteOnly"])
                self.assertFalse(folder["canRegisterOrder"])
                for operation in (lambda: store.add(path, {}), lambda: store.import_folder(path)):
                    with self.assertRaises(ValueError):
                        operation()
                status, _, _ = self.http("/api/order-add", "POST", json.dumps({"path": path}))
                self.assertEqual(status, 400)
                self.assertEqual((self.root / path / "!.txt").read_bytes(), original)
        progress = {"folders": 0, "added": 0, "errors": []}
        store.discover(manager.read_status_document, progress)
        self.assertEqual((progress["added"], progress["errors"]), (1, []))
        self.assertEqual([record["path"] for record in store.list()], [order])
        manager.save_note("Клиент/Адрес", "Заметка объекта")
        card = manager.order_document.load(self.root / "Клиент/Адрес", manager.STATUS_LABELS)
        self.assertEqual((card["note"], card["financial_status"], card["extra_blocks"]),
                         ("Заметка объекта", "partial", {"Контакт": "Телефон клиента"}))
        self.folder("Новый клиент")
        manager.save_note("Новый клиент", "Заметка клиента")
        self.assertFalse(manager.order_document.ORDER_FIELDS.intersection(manager.order_document.load(self.root / "Новый клиент", manager.STATUS_LABELS)))

    def test_existing_mistaken_registration_can_be_removed_without_touching_child_order(self):
        path = "Клиент/Адрес/2026-10-00 - работа"
        self.folder(path)
        store = manager.order_store()
        previous = store.add(path, {"status": "process", "note": "Данные сохранить", "financial_status": "paid"})
        with store.connect() as db:
            db.execute("UPDATE orders SET path=? WHERE path=?", ("Клиент/Адрес", path))
        child = store.add(path, {"status": "new", "note": "Заказ"})
        folder = manager.read_folder("Клиент/Адрес")
        self.assertFalse(folder["canRegisterOrder"])
        self.assertEqual(folder["order"]["note"], previous["note"])
        removed = store.remove({"path": "Клиент/Адрес", "revision": previous["revision"], "confirmed": True})
        store.sync()
        self.assertFalse(removed["registered"])
        self.assertIsNotNone(store.get(child["path"]))
        with self.assertRaises(ValueError):
            store.import_folder("Клиент/Адрес")
        card = manager.order_document.load(self.root / "Клиент/Адрес", manager.STATUS_LABELS)
        self.assertEqual((card["note"], card["financial_status"]), (previous["note"], "paid"))
