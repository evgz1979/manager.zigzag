import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import unittest
from unittest.mock import patch

import folder_rename
import folder_rename_undo
from event_folder_undo import EventRenamePending
import test_server as fixtures

manager = fixtures.manager


class FolderRenameTests(unittest.TestCase):
    setUp = fixtures.ManagerTests.setUp
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url

    def populated(self):
        source = "Клиент/2026-00-00 - Заказ"
        store = manager.order_store()
        order = store.add(source, {"status": "rework", "note": "Карточка", "amount": 14200,
                                   "financial_status": "partial", "extra_blocks": {"Задачи": "- [ ] Задача заказа", "Особое": "Сохранить"}})
        store.sync()
        order = store.get(source)
        notes = manager.folder_note_store()
        record = notes.read(source + "/Фото")
        record = notes.save({"path": record["path"], "revision": record["revision"], "note": "Невыгруженная заметка",
                             "todo_items": [{"text": "Задача папки", "done": False}]})
        manager.MobileBridge(store)
        with store.connect() as db:
            db.execute("INSERT INTO mobile_tasks VALUES (?,?)", (order["id"], '[{"id":"keep-task","text":"Задача заказа","done":false}]'))
            db.execute("INSERT INTO mobile_files VALUES (?,?,?)", (order["id"], 123, '[]'))
            db.execute("CREATE TABLE IF NOT EXISTS todo_catalog (path TEXT PRIMARY KEY,checked REAL,error TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS todo_missing_folders (path TEXT PRIMARY KEY,order_path TEXT NOT NULL,checked REAL NOT NULL)")
            db.execute("INSERT INTO todo_catalog VALUES (?,123,'')", (source,))
            db.execute("INSERT INTO todo_missing_folders VALUES (?,?,123)", (source + "/Пропало", source))
        file = self.root / source / "Фото/файл%2F #.txt"
        manager.file_comments.save(file, "Комментарий файла", manager.file_comments.read(file)["revision"])
        return store, source, order, record

    def rename(self, source, name):
        store = manager.order_store()
        return folder_rename.rename(store, {**folder_rename.preview(store, source), "name": name})

    def test_rename_order_preserves_identity_all_pending_data_comments_and_single_registration(self):
        store, source, order, note = self.populated()
        before = {path.relative_to(self.root / source).as_posix(): path.read_bytes()
                  for path in (self.root / source).rglob('*') if path.is_file()}
        result = self.rename(source, "2026-00-00 - Новое имя")
        destination = result["path"]
        self.assertFalse((self.root / source).exists())
        self.assertEqual({path.relative_to(self.root / destination).as_posix(): path.read_bytes()
                          for path in (self.root / destination).rglob('*') if path.is_file()}, before)
        moved = store.get(destination)
        self.assertEqual(moved["id"], order["id"])
        self.assertEqual(len(store.list()), 1)
        self.assertTrue(moved["sync_pending"])
        for key in ("title", "status", "financial_status", "amount", "note", "extra_blocks"):
            self.assertEqual(moved[key], order[key])
        folder = manager.folder_note_store().get(destination + "/Фото")
        self.assertEqual(folder["note"], note["note"])
        self.assertEqual(folder["todo_items"], note["todo_items"])
        self.assertTrue(folder["sync_pending"])
        self.assertEqual(folder["parent_order"], destination)
        with self.assertRaises(manager.FolderNoteConflict):
            manager.folder_note_store().save({"path": note["path"], "revision": note["revision"], "note": "Старая вкладка"})
        with store.connect() as db:
            self.assertEqual(db.execute("SELECT path,order_path FROM todo_missing_folders").fetchone()[:], (destination + "/Пропало", destination))
            self.assertEqual(db.execute("SELECT scanned FROM mobile_files").fetchone()[0], 0)
            self.assertIn('keep-task', db.execute("SELECT items FROM mobile_tasks").fetchone()[0])
        store.sync()
        manager.folder_note_store().sync()
        self.assertFalse(store.get(destination)["sync_pending"])
        self.assertFalse(manager.folder_note_store().get(destination + "/Фото")["sync_pending"])
        progress = {"folders": 0, "added": 0, "errors": []}
        store.discover(manager.read_status_document, progress)
        self.assertEqual(progress["added"], 0)
        self.assertEqual(len(store.list()), 1)
        comment = manager.file_comments.read(self.root / destination / "Фото/файл%2F #.txt")
        self.assertEqual(comment["comment"], "Комментарий файла")

    def test_client_and_group_rename_update_nested_orders_and_inactive_marker_queue(self):
        store, source, order, note = self.populated()
        activity = manager.client_activity_store()
        record = activity.read("Клиент")
        activity.save({"path": "Клиент", "revision": record["revision"], "inactive": True})
        result = self.rename("Клиент", "Другой клиент")
        self.assertEqual(store.list()[0]["client"], "Другой клиент")
        self.assertTrue(activity.get("Другой клиент")["sync_pending"])
        self.assertTrue(activity.get("Другой клиент")["inactive"])
        self.assertEqual(manager.listed_orders()["orders"], [])
        activity.sync()
        self.assertFalse(activity.get("Другой клиент")["sync_pending"])
        self.folder("01 - Группа/Покупатель/Объект/2026-10-20 - Заказ")
        grouped = store.add("01 - Группа/Покупатель/Объект/2026-10-20 - Заказ", {"status": "new", "note": ""})
        self.rename("01 - Группа", "05 - Группа")
        self.assertEqual(store.get("05 - Группа/Покупатель/Объект/2026-10-20 - Заказ")["id"], grouped["id"])

    def test_collision_stale_identity_and_changed_role_leave_everything_unchanged(self):
        store, source, order, note = self.populated()
        self.folder("Клиент/2026-00-00 - Занято")
        with self.assertRaises(folder_rename.FolderRenameConflict):
            self.rename(source, "2026-00-00 - Занято")
        with self.assertRaises(folder_rename.FolderRenameConflict):
            folder_rename.rename(store, {"path": source, "revision": "stale", "name": "2026-00-00 - Новое"})
        with self.assertRaisesRegex(folder_rename.FolderRenameConflict, "тип папки"):
            self.rename(source, "Пропала дата")
        self.assertEqual(store.get(source), order)
        self.assertTrue((self.root / source).is_dir())
        for path in ("", "# docs", "# work", "# work/# glass", "../Клиент"):
            with self.assertRaises(ValueError):
                folder_rename.preview(store, path)

    def test_standalone_undo_retains_new_files_later_edits_and_pending_exports(self):
        store, source, order, note = self.populated()
        result = self.rename(source, "2026-00-00 - Другое")
        moved = store.get(result["path"])
        moved = store.save({**moved, "note": "Более поздняя правка", "amount": "142", "costs": None, "paid": None})
        self.file(result["path"] + "/Новый файл.txt", b"new data")
        session = self.root / result["journal"]
        subprocess.run([sys.executable, str(session / ".restore.py"), str(session), "--apply"], check=True, capture_output=True)
        restored = store.get(source)
        self.assertEqual(restored["id"], order["id"])
        self.assertEqual(restored["note"], "Более поздняя правка")
        self.assertTrue(restored["sync_pending"])
        self.assertTrue((self.root / source / "Новый файл.txt").exists())
        self.assertTrue(manager.folder_note_store().get(source + "/Фото")["sync_pending"])

    def test_interruption_blocks_old_and_new_paths_until_standalone_recovery(self):
        store, source, order, note = self.populated()
        with patch.object(folder_rename.restore, "rewrite", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.rename(source, "2026-00-00 - Прервано")
        destination = "Клиент/2026-00-00 - Прервано"
        for path in (source, destination):
            with self.assertRaises(EventRenamePending):
                store.get(path)
            with self.assertRaises(EventRenamePending):
                manager.folder_note_store().get(path + "/Фото")
        bridge = manager.MobileBridge(store)
        with patch.object(bridge, "validate"):
            with self.assertRaises(EventRenamePending):
                bridge.apply({"id": "pending-operation", "order_id": order["id"], "kind": "order_comment", "text": "Сохранить ввод"}, b'pending', 'root')
        with store.connect() as db:
            session = Path(db.execute("SELECT session FROM folder_renames WHERE state='pending'").fetchone()[0])
        subprocess.run([sys.executable, str(session / ".restore.py"), str(session), "--apply"], check=True, capture_output=True)
        self.assertEqual(store.get(source), order)
        self.assertTrue((self.root / source).exists())

    def test_reverse_interruption_can_be_resumed_after_durable_pending_marker(self):
        store, source, order, note = self.populated()
        result = self.rename(source, "2026-00-00 - Другое")
        session = self.root / result["journal"]
        with patch.object(folder_rename_undo, "rewrite", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                folder_rename_undo.undo(session, True)
        with self.assertRaises(EventRenamePending):
            store.get(source)
        subprocess.run([sys.executable, str(session / ".restore.py"), str(session), "--apply"], check=True, capture_output=True)
        self.assertEqual(store.get(source)["id"], order["id"])

    def test_http_rename_has_preview_and_preserves_a_single_order(self):
        store, source, order, note = self.populated()
        status, _, body = self.http(self.url("/api/folder", source))
        self.assertTrue(json.loads(body)["canRenameFolder"])
        status, _, body = self.http(self.url("/api/folder-rename", source))
        view = json.loads(body)
        with patch.object(manager, "schedule_order_sync"), patch.object(manager, "schedule_todo_refresh"):
            status, _, body = self.http("/api/folder-rename", "POST", json.dumps({**view, "name": "2026-00-00 - Новое"}))
        self.assertEqual(status, 200, body)
        self.assertEqual(len(store.list()), 1)
        self.assertEqual(store.list()[0]["id"], order["id"])

    def test_supplier_order_and_ordinary_event_can_be_renamed(self):
        source = "# work/# glass/2026-10-20 - Поставщик"
        self.folder(source + "/00 - Замеры")
        store = manager.order_store()
        order = store.add(source, {"status": "new", "note": "Заказ поставщику"})
        result = self.rename(source, "2026-10-20 - Стекло")
        self.assertEqual(store.get(result["path"])["id"], order["id"])
        event = result["path"] + "/00 - Замеры"
        notes = manager.folder_note_store()
        note = notes.read(event)
        notes.save({"path": event, "revision": note["revision"], "note": "Событие", "todo_items": [{"text": "Проверить", "done": False}]})
        renamed = self.rename(event, "00 - Проверка замеров")
        self.assertEqual(notes.get(renamed["path"])["note"], "Событие")
        self.assertEqual(len(store.list()), 1)


if __name__ == '__main__':
    unittest.main()
