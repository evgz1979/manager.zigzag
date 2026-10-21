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


class SectionTests(unittest.TestCase):
    setUp = fixtures.ManagerTests.setUp
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url

    def post(self, route, payload):
        with patch.object(manager, "schedule_order_sync"), patch.object(manager, "schedule_todo_refresh"):
            status, _, body = self.http(route, "POST", json.dumps(payload))
        self.assertIn(status, (200, 201), body)
        return json.loads(body)

    def test_work_and_financial_sections_support_records_events_todos_and_exports(self):
        sections = ("# work/# laser", "# work/# freza", "# work/# cutter", "# work/# razbor",
                    "# moneys/# сверки", "# moneys/# Зп", "# moneys/# biils", "# moneys/Документы", "#work/Без решётки")
        paths = []
        for section in sections:
            with self.subTest(section=section):
                self.folder(section)
                body = manager.order_document.render({"note": "Заметка раздела", "extra_blocks": {"Контакт": "Сохранить"}}, manager.STATUS_LABELS).encode()
                self.file(section + "/!.txt", body)
                opened = manager.read_folder(section)
                self.assertTrue(opened["canCreateOrderFolder"])
                self.assertFalse(opened["canRegisterOrder"])
                self.assertFalse(opened["service"])
                self.assertEqual((self.root / section / "!.txt").read_bytes(), body)
                record = self.post("/api/order-folder-create", {"path": section, "date": "2026-10-20", "title": "Запись"})
                path = record["path"]
                paths.append(path)
                self.assertEqual(list((self.root / path).iterdir()), [])
                created_card = manager.order_store().get(path)
                self.assertTrue(record['registered'])
                added = self.post('/api/order-save', {'path': path, 'revision': created_card['revision'],
                    'title': created_card['title'], 'status': 'process', 'note': 'Заметка записи', 'financial_status': 'partial',
                    'amount': '', 'costs': '', 'paid': '', 'todo_items': [{"text": "Получить документы", "done": False}]})
                view = event_folders.preview(self.root, path, manager.folder_note_store())
                event = self.post("/api/event-folder-create", {"path": path, "revision": view["revision"], "title": "Согласование"})
                note = manager.read_folder(event["path"])["folderNote"]
                note = self.post("/api/folder-note-save", {"path": event["path"], "revision": note["revision"],
                    "note": "Заметка события", "todo_items": [{"text": "Проверить данные", "done": False}]})
                self.post("/api/event-relevance", {"path": event["path"], "revision": note["revision"], "value": "check"})
                opened = manager.read_folder(path)
                self.assertEqual(opened["view"], "files")
                self.assertTrue(opened["canCreateEventFolder"])
                self.assertEqual(opened["order"]["id"], added["id"])
                self.assertEqual(opened["directories"][0]["eventRelevance"]["value"], "check")
                self.assertEqual(manager.read_folder(event["path"])["view"], "files")
        store, notes = manager.order_store(), manager.folder_note_store()
        self.assertEqual(store.discard_service_orders(), 0)
        with patch("folder_structure.os.scandir", side_effect=AssertionError("Summary must use SQLite")):
            listed = OrderTodos(store).attach(store.list())
        self.assertEqual({item["path"] for item in listed}, set(paths))
        self.assertTrue(all(len(item["todo_groups"]) == 2 for item in listed))
        store.sync()
        notes.sync()
        for path in paths:
            self.assertIn("Заметка записи", (self.root / path / "!.txt").read_text())
            self.assertIn("Заметка события", (self.root / path / "00 - Согласование/!.txt").read_text())
        old_ids = {item["path"]: item["id"] for item in store.list()}
        shutil.rmtree(manager.DATA_DIR)
        rebuilt = manager.order_store()
        progress = {"folders": 0, "added": 0, "errors": []}
        rebuilt.discover(manager.read_status_document, progress)
        self.assertEqual((progress["added"], progress["errors"]), (len(paths), []))
        self.assertEqual({item["path"]: item["id"] for item in rebuilt.list()}, old_ids)
        OrderTodos(rebuilt).refresh()
        self.assertTrue(all(len(item["todo_groups"]) == 2 for item in OrderTodos(rebuilt).attach(rebuilt.list())))

    def test_legacy_names_are_records_by_depth_and_service_descendants_remain_protected(self):
        for section, name in (("# moneys/# Зп", "2026-06 июнь"), ("# moneys/# biils", "01"),
                              ("# moneys/# налоги", "2025 отчётный год"), ("#work/#laser", "Старая работа")):
            path = section + "/" + name
            self.folder(path)
            with patch("folder_structure.os.scandir", side_effect=AssertionError("Roles use the fixed depth")):
                self.assertEqual(folder_role(self.root, section)["folderKind"], "moneys_section" if section.startswith("# moneys") else "work_section")
                self.assertEqual(folder_role(self.root, path)["folderKind"], "order")
                self.assertEqual(folder_role(self.root, path + "/2026-10-20 - Внутри")["folderKind"], "event")
            event = event_folders.create(self.root, {"path": path, "revision": event_folders.preview(self.root, path)["revision"], "title": "Событие"})
            self.assertTrue((self.root / event["path"]).is_dir())
            service = path + "/# bills/Архив"
            self.folder(service)
            self.assertTrue(manager.read_folder(service)["eventFolder"])
            self.assertTrue(is_service_folder(service))
            with self.assertRaises(ValueError):
                manager.order_store().add(service, {})
            with self.assertRaises(ValueError):
                event_folders.preview(self.root, service)
        self.folder("Клиент/# moneys/# сверки/Запись")
        self.assertFalse(folder_role(self.root, "Клиент/# moneys/# сверки/Запись")["canRegisterOrder"])

    def test_creation_and_event_rename_have_standalone_undo_with_exact_section_scope(self):
        for section, sibling in (("#work/#laser", "#work/#freza"), ("# moneys/# сверки", "# moneys/# Зп")):
            self.folder(section)
            created = order_folders.create(self.root, section, "2026-10-20", "Запись")
            session = self.root / created["journal"]
            subprocess.run([sys.executable, str(session / ".folder-layout.py"), "undo", str(session), "--apply"], check=True, capture_output=True)
            self.assertFalse((self.root / created["path"]).exists())
            path = section + "/Существующая запись"
            self.folder(path + "/Фото")
            self.file(path + "/Фото/original.txt", b"preserve")
            notes = manager.folder_note_store()
            old = notes.read(path + "/Фото")
            view = event_folders.preview(self.root, path, notes)
            renamed = event_folders.rename(notes, {"path": path, "revision": view["revision"], "confirmed": True,
                "names": [{"source": item["source"], "title": item["title"]} for item in view["suggestions"]]})
            new = notes.get(path + "/00 - Фото")
            notes.save({"path": new["path"], "revision": new["revision"], "note": "Сохранить новый ввод"})
            session = self.root / renamed["journal"]
            subprocess.run([sys.executable, str(session / ".restore.py"), str(session), "--apply"], check=True, capture_output=True)
            self.assertEqual(notes.get(old["path"])["note"], "Сохранить новый ввод")
            self.assertTrue(notes.get(old["path"])["sync_pending"])
            self.assertEqual((self.root / old["path"] / "original.txt").read_bytes(), b"preserve")
            with self.assertRaises(ValueError):
                folder_layout.safe_path(self.root, sibling, [section.split('/')[0]], **order_folders.layout_scope(section))

    def test_print_editor_is_the_only_creation_flow_and_preserves_old_folder_access(self):
        section = "# work/# print"
        self.folder(section)
        self.file(section + "/print - 2026-10-20.txt", b"Existing print task")
        folder = manager.read_folder(section)
        self.assertEqual(folder["view"], "print")
        self.assertFalse(folder['canCreateOrderFolder'])
        self.assertEqual([item["name"] for item in folder["files"]], ["print - 2026-10-20.txt"])
        with self.assertRaises(ValueError):
            order_folders.create(self.root, section, "2026-10-20", "Печать")
        path = section + '/2026-10-20 - Прежняя папка'
        self.folder(path + "/00 - Макет")
        self.file(path + "/00 - Макет/image.png", b"image")
        self.file(path + "/00 - Макет/Описание.txt", b"Do not import this as a print task")
        self.assertFalse(manager.read_folder(path)['canRegisterOrder'])
        self.assertEqual([item['name'] for item in manager.read_folder(section)['files']], ['print - 2026-10-20.txt'])
        opened = manager.read_folder(path + "/00 - Макет")
        self.assertEqual(opened["view"], "files")
        self.assertEqual({item["name"] for item in opened["files"]}, {"image.png", 'Описание.txt'})
