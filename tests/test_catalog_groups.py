import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import event_folders
from folder_structure import folder_role
from order_todos import OrderTodos
from scripts.rebind_order import rebind
import test_server as fixtures

manager = fixtures.manager


class CatalogGroupTests(unittest.TestCase):
    setUp = fixtures.ManagerTests.setUp
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url

    def test_groups_are_separate_naturally_sorted_trees_without_reading_cards(self):
        for path in ("10 - Архив/Клиент", "02 - Работа/Другой клиент/Объект", "01 - Личное/Клиент/Объект",
                     "03 - Пусто", "# work/# glass", "# moneys/# сверки"):
            self.folder(path)
        self.file("01 - Личное/Клиент/Объект/secret.txt", b"do not read")
        with patch.object(manager.order_document, "load", side_effect=AssertionError("Tree must not read cards")):
            data = manager.read_tree()
        self.assertEqual([item["name"] for item in data["groups"]], ["01 - Личное", "02 - Работа", "03 - Пусто", "10 - Архив"])
        self.assertEqual([item["name"] for item in data["children"]], ["Клиент"])
        self.assertEqual(data["groups"][0]["children"][0]["path"], "01 - Личное/Клиент")
        self.assertEqual(data["groups"][2]["children"], [])
        self.assertEqual([item["path"] for item in manager.read_tree("01 - Личное/Клиент")["children"]], ["01 - Личное/Клиент/Объект"])
        self.folder("04 - Новая/Ещё клиент")
        self.assertIn("04 - Новая", [item["name"] for item in manager.read_tree()["groups"]])
        self.assertFalse(manager.order_store().database.exists())

    def test_search_keeps_group_paths_and_finds_unloaded_descendants(self):
        self.folder("01 - Группа/Клиент/Объект/2026-10-20 - Заказ/00 - Переклейка")
        self.folder("02 - Другая/Чужой")
        result = manager.read_tree(query="переклейка")
        self.assertEqual(result["children"], [])
        self.assertEqual([item["path"] for item in result["groups"]], ["01 - Группа"])
        node = result["groups"][0]
        while node.get("children"):
            node = node["children"][0]
        self.assertEqual(node["path"], "01 - Группа/Клиент/Объект/2026-10-20 - Заказ/00 - Переклейка")
        self.assertEqual([item["path"] for item in manager.read_tree(query="Клиент")["children"]], ["Клиент"])
        self.folder("05 - Пустая")
        result = manager.read_tree(query="Пустая")
        self.assertEqual(result["groups"][0]["children"], [])

    def test_unavailable_group_does_not_hide_other_trees(self):
        self.folder("01 - Ошибка/Клиент")
        self.folder("02 - Работа/Другой клиент")
        original = manager.directory_children
        def children(path):
            if path == self.root / "01 - Ошибка":
                raise OSError("iCloud unavailable")
            return original(path)
        with patch.object(manager, "directory_children", side_effect=children):
            result = manager.read_tree()
        self.assertIn("error", result["groups"][0])
        self.assertEqual(result["groups"][1]["children"][0]["name"], "Другой клиент")
        self.assertEqual(result["children"][0]["name"], "Клиент")

    def test_grouped_clients_keep_roles_order_creation_events_and_database_only_todos(self):
        roles = {"01 - Группа": "catalog_group", "01 - Группа/Покупатель": "client",
                 "01 - Группа/Покупатель/Адрес": "object", "01 - Группа/Покупатель/Адрес/2026": "year",
                 "01 - Группа/Покупатель/Адрес/2026/2026-00-00 - Работа": "order",
                 "01 - Группа/Покупатель/Адрес/2026/2026-00-00 - Работа/01": "event",
                 "01 - Группа/Покупатель/00 - разное/00001 - Работа": "order",
                 "02 - Старое/2026": "year", "02 - Старое/2026/2026-10-10 - Работа": "order"}
        for path in roles:
            self.folder(path)
        for path, kind in roles.items():
            self.assertEqual(folder_role(self.root, path)["folderKind"], kind, path)
        for path in ("01 - Группа", "01 - Группа/Покупатель"):
            opened = manager.read_folder(path)
            self.assertTrue(opened["noteOnly"])
            self.assertFalse(opened["canRegisterOrder"])
            with self.assertRaises(ValueError):
                manager.order_folders.create(self.root, path, "2026-10-20", "Запрет")
        created = manager.order_folders.create(self.root, "01 - Группа/Покупатель/Адрес", "2026-10-20", "Новый заказ")
        path = created["path"]
        store = manager.order_store()
        record = store.add(path, {"status": "process", "note": "Заметка", "extra_blocks": {"Задачи": "- [ ] Получить счёт"}})
        self.assertEqual(record["client"], "Покупатель")
        self.assertEqual(manager.read_folder(path)["client"], "Покупатель")
        view = event_folders.preview(self.root, path)
        event = event_folders.create(self.root, {"path": path, "revision": view["revision"], "title": "Замеры"})
        notes = manager.folder_note_store()
        note = notes.read(event["path"])
        note = notes.save({"path": note["path"], "revision": note["revision"], "note": "Не потерять",
                           "todo_items": [{"text": "Уточнить размеры", "done": False}]})
        with patch("folder_structure.os.scandir", side_effect=AssertionError("Summary uses SQLite")):
            listed = OrderTodos(store).attach(store.list())
        self.assertEqual(listed[0]["client"], "Покупатель")
        self.assertEqual(len(listed[0]["todo_groups"]), 2)
        store.sync()
        notes.sync()
        self.assertIn("Клиент: Покупатель", (self.root / path / "!.txt").read_text())
        self.assertEqual(manager.read_folder(event["path"])["note"], "Не потерять")

    def moved_order(self):
        source = "Клиент/Адрес/2026-10-20 - Заказ"
        destination = "01 - Группа/Клиент/Адрес/2026-10-20 - Заказ"
        self.folder(source)
        store = manager.order_store()
        record = store.add(source, {"title": "Заказ", "status": "process", "note": "Сохранить",
                                   "financial_status": "partial", "amount": 12300,
                                   "extra_blocks": {"Поставка": "Сохранить блок", "Задачи": "- [ ] Получить счёт"}})
        store.sync()
        (self.root / destination).parent.mkdir(parents=True)
        (self.root / source).rename(self.root / destination)
        return store, record, source, destination

    def test_explicit_order_rebind_preserves_identity_mobile_tasks_and_later_edits_on_undo(self):
        store, record, source, destination = self.moved_order()
        manager.MobileBridge(store)
        with store.connect() as db:
            db.execute("INSERT INTO mobile_tasks VALUES (?,?)", (record["id"], '[{"id":"keep-task"}]'))
            db.execute("INSERT INTO mobile_files VALUES (?,?,?)", (record["id"], 123, '[]'))
            db.execute("CREATE TABLE IF NOT EXISTS todo_catalog (path TEXT PRIMARY KEY, checked REAL, error TEXT NOT NULL)")
            db.execute("INSERT INTO todo_catalog VALUES (?,1,'')", (source,))
        original = (self.root / destination / "!.txt").read_bytes()
        self.assertEqual(rebind(store, source, destination)["id"], record["id"])
        result = rebind(store, source, destination, perform=True)
        rebound = store.get(destination)
        self.assertEqual(rebound["id"], record["id"])
        self.assertTrue(rebound["sync_pending"])
        self.assertEqual(rebound["client"], "Клиент")
        self.assertEqual(rebound["extra_blocks"], record["extra_blocks"])
        self.assertEqual((self.root / destination / "!.txt").read_bytes(), original)
        with store.connect() as db:
            self.assertEqual(db.execute("SELECT items FROM mobile_tasks WHERE order_id=?", (record["id"],)).fetchone()[0], '[{"id":"keep-task"}]')
            self.assertEqual(db.execute("SELECT scanned FROM mobile_files WHERE order_id=?", (record["id"],)).fetchone()[0], 0)
            self.assertEqual(db.execute("SELECT path FROM todo_catalog").fetchone()[0], destination)
            db.execute("UPDATE orders SET note='Новый ввод',revision=revision+1 WHERE id=?", (record["id"],))
        (self.root / destination).rename(self.root / source)
        session = Path(result["journal"])
        subprocess.run([sys.executable, str(session / ".restore.py"), "--undo", str(session), "--apply"], check=True, capture_output=True)
        restored = store.get(source)
        self.assertEqual(restored["note"], "Новый ввод")
        self.assertTrue(restored["sync_pending"])
        self.assertEqual(restored["id"], record["id"])

    def test_order_rebind_rejects_foreign_card_pending_data_and_nested_notes(self):
        store, record, source, destination = self.moved_order()
        card = self.root / destination / "!.txt"
        original = card.read_bytes()
        card.write_text(card.read_text().replace(record["id"], "different-id"))
        with self.assertRaisesRegex(ValueError, "Идентификатор"):
            rebind(store, source, destination, perform=True)
        self.assertIsNotNone(store.get(source))
        card.write_bytes(original)
        with store.connect() as db:
            db.execute("UPDATE orders SET revision=revision+1 WHERE id=?", (record["id"],))
        with self.assertRaisesRegex(ValueError, "невыгруженные"):
            rebind(store, source, destination, perform=True)
        self.assertFalse((self.root / ".folder-layout-history").exists())
        with store.connect() as db:
            db.execute("UPDATE orders SET revision=exported_revision WHERE id=?", (record["id"],))
        self.folder(destination + "/00 - Заметки")
        manager.folder_note_store().read(destination + "/00 - Заметки")
        with self.assertRaisesRegex(ValueError, "вложенные заметки"):
            rebind(store, source, destination, perform=True)
