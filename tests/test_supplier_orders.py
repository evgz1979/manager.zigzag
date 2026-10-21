import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import event_folders
import folder_layout
import order_folders
from folder_structure import folder_role, is_service_folder
from order_todos import OrderTodos
from scripts.rebind_glass_notes import rebind
import test_server as fixtures

manager = fixtures.manager


class SupplierOrderTests(unittest.TestCase):
    setUp = fixtures.ManagerTests.setUp
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url
    section = "# work/# glass"
    order = section + "/2026-10-20 - Стеклопакеты для Жуковки"

    def post(self, route, payload):
        with patch.object(manager, "schedule_order_sync"), patch.object(manager, "schedule_todo_refresh"):
            status, _, body = self.http(route, "POST", json.dumps(payload))
        self.assertIn(status, (200, 201), body)
        return json.loads(body)

    def test_create_register_events_notes_todos_and_local_summary(self):
        self.folder(self.section)
        manager.save_note(self.section, "Производство стеклопакетов и стекла")
        root = manager.read_folder(self.section)
        self.assertEqual(root["folderKind"], "supplier_root")
        self.assertEqual(root["filesScope"], "subfolders")
        self.assertTrue(root["canCreateOrderFolder"])
        self.assertFalse(root["canRegisterOrder"])
        self.assertFalse(root["service"])
        self.assertIn("# work", [item["path"] for item in manager.read_tree()["auxiliary"]])
        self.assertIn(self.section, [item["path"] for item in manager.read_tree("# work")["children"]])
        created = self.post("/api/order-folder-create", {"path": self.section, "date": "2026-10-20", "title": "Стеклопакеты для Жуковки"})
        self.assertEqual(created["path"], self.order)
        self.assertEqual(list((self.root / self.order).iterdir()), [])
        created_card = manager.order_store().get(self.order)
        self.assertTrue(created['registered'])
        order = self.post('/api/order-save', {'path': self.order, 'revision': created_card['revision'],
            'title': created_card['title'], 'status': 'process', 'note': 'Заметка поставщику', 'financial_status': 'payment',
            'amount': '', 'costs': '', 'paid': '', 'todo_items': [{"text": "Получить счёт", "done": False}]})
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
        self.assertEqual(listed, [])
        listed = OrderTodos(store).attach(store.list())
        self.assertEqual([item["path"] for item in listed[0]["todo_groups"]], [self.order, event["path"], nested])
        self.assertEqual(store.discard_service_orders(), 0)
        opened = manager.read_folder(self.order)
        self.assertFalse(opened["service"])
        self.assertEqual(opened["order"]["note"], "Заметка поставщику")
        self.assertEqual(opened["directories"][0]["eventRelevance"]["value"], "active")
        self.assertIn("[Заказ]", (self.root / self.order / "!.txt").read_text())
        self.assertIn("Проверить формулу", (self.root / event["path"] / "!.txt").read_text())
        self.assertIn("[Актуальность события]\nАктуально", (self.root / event["path"] / "!.txt").read_text())
        self.assertEqual(manager.read_folder(self.section)["note"], "Производство стеклопакетов и стекла")

    def test_discovery_rebuild_and_removal_preserve_full_cards(self):
        self.folder(self.order + "/00 - Замеры")
        body = manager.order_document.render({"title": "Заказ стекла", "note": "Закалённое стекло", "status": "workshop",
            "financial_status": "partial", "amount": 1234500,
            "extra_blocks": {"Поставщик": "Стекольный завод", "Задачи": "- [ ] Получить стекло"}}, manager.STATUS_LABELS)
        self.file(self.order + "/!.txt", body.encode())
        self.file(self.order + "/00 - Замеры/!.txt", manager.order_document.render({"note": "Размеры проёма",
            "extra_blocks": {"Задачи": "- [ ] Проверить диагонали"}}, manager.STATUS_LABELS).encode())
        for parent in ("# docs", "# work/# laser/# bills", "# work/# razbor/# glass", "Клиент/# glass"):
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
        self.folder(self.section)
        created = order_folders.create(self.root, self.section, "2026-10-20", "Стекло")
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

    def test_glass_locations_and_spacing_do_not_enable_other_sections_or_layout(self):
        for root in ("# work/# glass", "#work/#glass", "# work/#glass", "#work/# glass", "# glass", "#glass"):
            path = root + "/00001 - Стекло"
            self.folder(path)
            self.assertFalse(is_service_folder(path))
            self.assertTrue(folder_role(self.root, path)["canRegisterOrder"])
            with self.assertRaises(ValueError):
                folder_layout.Plan(self.root, [root.split('/')[0]]).mkdir(root + "/Не разрешено")
        for path in ("# docs/2026-10-20 - Заказ", "# work/# laser/# bills/2026-10-20 - Заказ", "# work/# razbor/# glass/2026-10-20 - Заказ",
                     "Клиент/# glass/2026-10-20 - Заказ", self.order + "/# bills"):
            self.folder(path)
            with self.subTest(path=path):
                self.assertTrue(is_service_folder(path))
                self.assertFalse(folder_role(self.root, path)["canRegisterOrder"])
                with self.assertRaises(ValueError):
                    manager.order_store().add(path, {})
                with self.assertRaises(ValueError):
                    event_folders.preview(self.root, path)
        self.folder(self.section)
        (self.root / self.section / "Ссылка").symlink_to(self.root / "Клиент")
        with self.assertRaises(ValueError):
            order_folders.create(self.root, self.section + "/Ссылка", "2026-10-20", "Заказ")
        scope = order_folders.layout_scope(self.section)
        with self.assertRaises(ValueError):
            folder_layout.safe_path(self.root, "# work/# laser", ["# work"], **scope)

    def test_work_is_a_container_with_immediate_sections_without_attachment_walk(self):
        for path in (self.section, "# work/# laser", "# work/# print"):
            self.folder(path)
        self.file("# work/# laser/deep/document.txt", b"keep")
        with patch.object(manager.os, "walk", side_effect=AssertionError("Do not collect section attachments")):
            work = manager.read_folder("# work")
        self.assertEqual(work["folderKind"], "work_root")
        self.assertEqual(work["filesScope"], "subfolders")
        self.assertEqual(work["fileCount"], 0)
        self.assertEqual([item["name"] for item in work["directories"]], ["# glass", "# laser", "# print"])
        self.assertTrue(work["canCreateOrderFolder"])
        self.assertFalse(work["canRegisterOrder"])
        manager.save_note("# work", "Производство")
        self.assertEqual(manager.read_folder("# work")["note"], "Производство")

    def moved_note(self, *, pending=False):
        path = "# glass/2026-10-20 - Стекло/00 - Задание"
        self.folder(path)
        notes = manager.folder_note_store()
        record = notes.read(path)
        record = notes.save({"path": path, "revision": record["revision"], "note": "Стеклопакеты",
            "todo_items": [{"text": "Проверить размеры", "done": False}]})
        if not pending:
            notes.sync()
            record = notes.get(path)
        self.folder("# work")
        (self.root / "# glass").rename(self.root / self.section)
        return notes, record

    def test_explicit_rebind_preserves_identity_bytes_and_new_edits_on_standalone_undo(self):
        notes, record = self.moved_note()
        path = "# work/" + record["path"]
        original = (self.root / path / "!.txt").read_bytes()
        self.assertEqual(rebind(notes)["count"], 1)
        self.assertIsNone(notes.get(path))
        result = rebind(notes, perform=True)
        rebound = notes.get(path)
        self.assertEqual(rebound["revision"].split(":")[0], record["revision"].split(":")[0])
        self.assertEqual(rebound["parent_order"], "# work/" + record["parent_order"])
        self.assertEqual(rebound["todo_items"], record["todo_items"])
        self.assertFalse(rebound["sync_pending"])
        self.assertEqual((self.root / path / "!.txt").read_bytes(), original)
        self.assertTrue((Path(result["journal"]) / ".before.sqlite3").is_file())
        with self.assertRaises(manager.FolderNoteConflict):
            notes.save({"path": record["path"], "revision": record["revision"], "note": "Старая вкладка"})
        notes.save({"path": path, "revision": rebound["revision"], "note": "Новое дополнение"})
        (self.root / self.section).rename(self.root / "# glass")
        session = Path(result["journal"])
        subprocess.run([sys.executable, str(session / ".restore.py"), str(session), "--apply"], check=True, capture_output=True)
        restored = notes.get(record["path"])
        self.assertEqual(restored["note"], "Новое дополнение")
        self.assertTrue(restored["sync_pending"])
        self.assertIsNone(notes.get(path))
        self.assertEqual((self.root / record["path"] / "!.txt").read_bytes(), original)

    def test_rebind_rejects_unexported_notes_without_dropping_queue(self):
        notes, record = self.moved_note(pending=True)
        with self.assertRaisesRegex(ValueError, "невыгруженная"):
            rebind(notes, perform=True)
        self.assertEqual(notes.get(record["path"]), record)
        self.assertFalse((self.root / ".folder-layout-history").exists())

    def test_rebind_rejects_changed_files_or_existing_destination_notes(self):
        notes, record = self.moved_note()
        path = "# work/" + record["path"]
        card = self.root / path / "!.txt"
        original = card.read_bytes()
        card.write_bytes(original + b"\n[External]\nKeep\n")
        with self.assertRaisesRegex(ValueError, "отличается"):
            rebind(notes, perform=True)
        self.assertIn(b"[External]", card.read_bytes())
        self.assertEqual(notes.get(record["path"]), record)
        card.write_bytes(original)
        notes.read(path)
        with self.assertRaisesRegex(ValueError, "уже есть заметки"):
            rebind(notes, perform=True)
        self.assertIsNotNone(notes.get(record["path"]))
        self.assertIsNotNone(notes.get(path))
