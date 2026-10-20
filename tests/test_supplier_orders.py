import json
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch

import event_folders
import folder_layout
import order_folders
from folder_structure import folder_role, is_service_folder
from order_todos import OrderTodos
import test_server as fixtures

manager = fixtures.manager


class SupplierOrderTests(unittest.TestCase):
    setUp = fixtures.ManagerTests.setUp
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url
    order = "# glass/2026-10-20 - Стеклопакеты для Жуковки"

    def post(self, route, payload):
        with patch.object(manager, "schedule_order_sync"), patch.object(manager, "schedule_todo_refresh"):
            status, _, body = self.http(route, "POST", json.dumps(payload))
        self.assertIn(status, (200, 201), body)
        return json.loads(body)

    def test_create_register_events_notes_todos_and_local_summary(self):
        self.folder("# glass")
        manager.save_note("# glass", "Производство стеклопакетов и стекла")
        root = manager.read_folder("# glass")
        self.assertEqual(root["folderKind"], "supplier_root")
        self.assertEqual(root["filesScope"], "subfolders")
        self.assertTrue(root["canCreateOrderFolder"])
        self.assertFalse(root["canRegisterOrder"])
        self.assertFalse(root["service"])
        self.assertIn("# glass", [item["path"] for item in manager.read_tree()["auxiliary"]])
        created = self.post("/api/order-folder-create", {"path": "# glass", "date": "2026-10-20", "title": "Стеклопакеты для Жуковки"})
        self.assertEqual(created["path"], self.order)
        self.assertEqual(list((self.root / self.order).iterdir()), [])
        self.assertFalse(manager.order_store().database.exists())
        manager.save_status(self.order, "process", "Заметка поставщику", "payment",
                            [{"text": "Получить счёт", "done": False}])
        order = self.post("/api/order-add", {"path": self.order})
        self.assertEqual((order["note"], order["status"], order["financial_status"]),
                         ("Заметка поставщику", "process", "payment"))
        store = manager.order_store()
        store.sync()
        view = event_folders.preview(self.root, self.order, manager.folder_note_store())
        event = self.post("/api/event-folder-create", {"path": self.order, "revision": view["revision"], "title": "Согласование"})
        self.assertEqual(event["path"], self.order + "/00 - Согласование")
        opened = manager.read_folder(event["path"])
        self.assertTrue(opened["eventFolder"])
        self.assertFalse(opened["service"])
        self.assertFalse(opened["canRegisterOrder"])
        note = self.post("/api/folder-note-save", {"path": event["path"], "revision": opened["folderNote"]["revision"],
                         "note": "Проверить формулу", "todo_items": [{"text": "Утвердить толщину", "done": False}]})
        relevance = self.post("/api/event-relevance", {"path": event["path"], "revision": note["revision"], "value": "active"})
        self.assertEqual(relevance["value"], "active")
        nested = event["path"] + "/# bills/Счета"
        self.folder(nested)
        record = manager.read_folder(nested)["folderNote"]
        self.post("/api/folder-note-save", {"path": nested, "revision": record["revision"], "note": "Документы поставщика",
                  "todo_items": [{"text": "Проверить реквизиты", "done": False}]})
        manager.folder_note_store().sync()
        with patch("folder_structure.os.scandir", side_effect=AssertionError("Summary must use SQLite")):
            status, _, body = self.http("/api/orders")
        self.assertEqual(status, 200)
        listed = json.loads(body)["orders"]
        self.assertEqual([item["path"] for item in listed], [self.order])
        self.assertEqual([item["path"] for item in listed[0]["todo_groups"]], [self.order, event["path"], nested])
        self.assertEqual(store.discard_service_orders(), 0)
        opened = manager.read_folder(self.order)
        self.assertFalse(opened["service"])
        self.assertEqual(opened["order"]["note"], "Заметка поставщику")
        self.assertEqual(opened["directories"][0]["eventRelevance"]["value"], "active")
        self.assertIn("[Заказ]", (self.root / self.order / "!.txt").read_text())
        self.assertIn("Проверить формулу", (self.root / event["path"] / "!.txt").read_text())
        self.assertIn("[Актуальность события]\nАктуально", (self.root / event["path"] / "!.txt").read_text())
        self.assertEqual(manager.read_folder("# glass")["note"], "Производство стеклопакетов и стекла")

    def test_discovery_rebuild_and_removal_preserve_full_cards(self):
        self.folder(self.order + "/00 - Замеры")
        body = manager.order_document.render({"title": "Заказ стекла", "note": "Закалённое стекло", "status": "workshop",
            "financial_status": "partial", "amount": 1234500,
            "extra_blocks": {"Поставщик": "Стекольный завод", "Задачи": "- [ ] Получить стекло"}}, manager.STATUS_LABELS)
        self.file(self.order + "/!.txt", body.encode())
        self.file(self.order + "/00 - Замеры/!.txt", manager.order_document.render({"note": "Размеры проёма",
            "extra_blocks": {"Задачи": "- [ ] Проверить диагонали"}}, manager.STATUS_LABELS).encode())
        for parent in ("# docs", "# work/# glass", "Клиент/# glass"):
            self.file(parent + "/2026-10-20 - Не заказ/!.txt", body.encode())
        store = manager.order_store()
        progress = {"folders": 0, "added": 0, "errors": []}
        store.discover(manager.read_status_document, progress)
        self.assertEqual((progress["added"], progress["errors"]), (1, []))
        OrderTodos(store).refresh()
        listed = OrderTodos(store).attach(store.list())
        self.assertEqual(len(listed[0]["todo_groups"]), 2)
        order = store.get(self.order)
        self.assertEqual(order["extra_blocks"]["Поставщик"], "Стекольный завод")
        store.sync()
        shutil.rmtree(manager.DATA_DIR)
        restored = manager.order_store().import_folder(self.order)
        for key in ("id", "title", "status", "financial_status", "note", "amount", "extra_blocks", "todo_items"):
            self.assertEqual(restored[key], order[key])
        note = manager.read_folder(self.order + "/00 - Замеры")["folderNote"]
        self.assertEqual(note["note"], "Размеры проёма")
        store = manager.order_store()
        store.remove({"path": self.order, "revision": restored["revision"], "confirmed": True})
        store.sync()
        progress = {"folders": 0, "added": 0, "errors": []}
        store.discover(manager.read_status_document, progress)
        self.assertEqual(store.list(), [])
        self.assertEqual(progress["added"], 0)
        self.assertIn("В списке заказов: нет", (self.root / self.order / "!.txt").read_text())

    def test_standalone_creation_and_event_rename_undo_work_under_glass(self):
        self.folder("# glass")
        created = order_folders.create(self.root, "# glass", "2026-10-20", "Стекло")
        session = self.root / created["journal"]
        subprocess.run([sys.executable, str(session / ".folder-layout.py"), "undo", str(session), "--apply"],
                       check=True, capture_output=True)
        self.assertFalse((self.root / created["path"]).exists())
        self.folder(self.order + "/Фото")
        self.file(self.order + "/Фото/original.txt", b"preserve bytes")
        notes = manager.folder_note_store()
        before = notes.read(self.order + "/Фото")
        view = event_folders.preview(self.root, self.order, notes)
        result = event_folders.rename(notes, {"path": self.order, "revision": view["revision"], "confirmed": True,
            "names": [{"source": item["source"], "title": item["title"]} for item in view["suggestions"]]})
        renamed = notes.get(self.order + "/00 - Фото")
        self.assertIsNotNone(renamed)
        notes.save({"path": renamed["path"], "revision": renamed["revision"], "note": "Новая заметка"})
        session = self.root / result["journal"]
        subprocess.run([sys.executable, str(session / ".restore.py"), str(session), "--apply"], check=True, capture_output=True)
        self.assertEqual(notes.get(before["path"])["note"], "Новая заметка")
        self.assertTrue(notes.get(before["path"])["sync_pending"])
        self.assertEqual((self.root / before["path"] / "original.txt").read_bytes(), b"preserve bytes")

    def test_exception_is_only_for_root_glass_and_does_not_enable_general_layout(self):
        for root in ("# glass", "#glass"):
            path = root + "/00001 - Стекло"
            self.folder(path)
            self.assertFalse(is_service_folder(path))
            self.assertTrue(folder_role(self.root, path)["canRegisterOrder"])
            with self.assertRaises(ValueError):
                folder_layout.Plan(self.root, [root]).mkdir(root + "/Не разрешено")
        for path in ("# docs/2026-10-20 - Заказ", "# work/# glass/2026-10-20 - Заказ",
                     "Клиент/# glass/2026-10-20 - Заказ", self.order + "/# bills"):
            self.folder(path)
            with self.subTest(path=path):
                self.assertTrue(is_service_folder(path))
                self.assertFalse(folder_role(self.root, path)["canRegisterOrder"])
                with self.assertRaises(ValueError):
                    manager.order_store().add(path, {})
                with self.assertRaises(ValueError):
                    event_folders.preview(self.root, path)
        self.folder("# glass")
        (self.root / "# glass/Ссылка").symlink_to(self.root / "Клиент")
        with self.assertRaises(ValueError):
            order_folders.create(self.root, "# glass/Ссылка", "2026-10-20", "Заказ")
