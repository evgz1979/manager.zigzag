import json
import shutil
import unittest
from unittest.mock import patch

import test_server as fixtures
from folder_notes import FolderNoteConflict, parent_order

manager = fixtures.manager


class FolderNoteTests(unittest.TestCase):
    setUp = fixtures.ManagerTests.setUp
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url
    order = "Клиент/2026-00-00 - Заказ"
    event = order + "/Фото"

    def save(self, record, **changes):
        return manager.folder_note_store().save({"path": record["path"], "revision": record["revision"],
            "note": record["note"], **changes})

    def card(self, relative, note="", **fields):
        self.file(relative + "/!.txt", manager.order_document.render({"note": note, **fields}, manager.STATUS_LABELS).encode())

    def test_all_order_contents_belong_to_parent_including_deep_and_dated_names(self):
        for relative in (self.event, self.event + "/2027-10-01 - Внутри/Детали", self.order + "/# bills/2026/Внутри"):
            self.folder(relative)
            self.assertEqual(parent_order(self.root, relative), self.order)
            folder = manager.read_folder(relative)
            self.assertTrue(folder["eventFolder"])
            self.assertTrue(folder["noteOnly"])
            self.assertFalse(folder["canRegisterOrder"])
            self.assertNotIn("order", folder)
        for relative in ("Клиент", "Клиент/Объект", "Клиент/2026", "# docs/Внутри", self.order):
            self.assertIsNone(parent_order(self.root, relative))
            if (self.root / relative).is_dir():
                self.assertNotIn("folderNote", manager.read_folder(relative))
        self.assertEqual(manager.order_store().list(), [])

    def test_independent_records_same_database_export_and_rebuild(self):
        store = manager.order_store()
        store.add(self.order, {"status": "process", "note": "Заказ"})
        store.sync()
        parent = store.get(self.order)
        self.card(self.event, "Событие", extra_blocks={"Материалы": "Плёнка", "Задачи": "- [ ] Замер"})
        original = (self.root / self.event / "!.txt").read_bytes()
        record = manager.folder_note_store().read(self.event)
        items = [{"text": "Замер", "done": True}, {"text": "Передать в цех", "done": False}]
        record = self.save(record, note="Отдельная заметка\n\n[Заметка]\n> текст", todo_items=items)
        self.assertTrue(record["sync_pending"])
        self.assertEqual(store.get(self.order), parent)
        self.assertEqual(store.get(self.order)["note"], "Заказ")
        self.assertEqual(store.get(self.order)["todo_items"], [])
        self.assertEqual([row["path"] for row in store.list()], [self.order])
        sibling = self.order + "/# bills"
        self.folder(sibling)
        self.assertEqual(manager.folder_note_store().read(sibling)["todo_items"], [])
        manager.folder_note_store().sync()
        record = manager.folder_note_store().get(self.event)
        self.assertFalse(record["sync_pending"])
        loaded = manager.order_document.load(self.root / self.event, manager.STATUS_LABELS)
        self.assertEqual(loaded["note"], record["note"])
        self.assertEqual(loaded["extra_blocks"]["Материалы"], "Плёнка")
        self.assertEqual(manager.order_document.read_todos(loaded["extra_blocks"]), items)
        self.assertEqual(next((self.root / self.event / ".order-history").rglob("!.txt")).read_bytes(), original)
        shutil.rmtree(manager.DATA_DIR)
        rebuilt = manager.folder_note_store().read(self.event)
        self.assertEqual((rebuilt["note"], rebuilt["todo_items"]), (record["note"], items))
        with self.assertRaises(FolderNoteConflict):
            self.save(record, note="Устаревший браузер после восстановления")
        self.save(rebuilt, todo_items=[])
        manager.folder_note_store().sync()
        self.assertEqual(manager.folder_note_store().read(self.event)["todo_items"], [])
        self.assertIn("[Задачи]\n\n", (self.root / self.event / "!.txt").read_text())

    def test_offline_save_and_persistent_failed_export_retry(self):
        store = manager.folder_note_store()
        record = store.read(self.event)
        self.assertFalse(record["file_exists"])
        self.root.rename(self.base / "offline")
        with patch.object(store, "target", side_effect=AssertionError("Saving must not access documents")):
            record = store.save({"path": self.event, "revision": record["revision"], "note": "Сохранено без iCloud",
                                 "todo_items": [{"text": "Не потерять", "done": False}]})
        manager.folder_note_store().sync()
        pending = manager.folder_note_store().get(self.event)
        self.assertTrue(pending["sync_pending"])
        self.assertTrue(pending["sync_error"])
        self.assertEqual(manager.folder_note_store().read(self.event), pending)
        (self.base / "offline").rename(self.root)
        manager.folder_note_store().sync()
        self.assertFalse(manager.folder_note_store().get(self.event)["sync_pending"])
        self.assertTrue(manager.folder_note_store().get(self.event)["file_exists"])
        self.assertEqual(manager.order_document.load(self.root / self.event, manager.STATUS_LABELS)["note"], record["note"])

    def test_external_changes_import_only_without_pending_edits(self):
        self.card(self.event, "Прежний текст")
        first = manager.folder_note_store().read(self.event)
        self.card(self.event, "Правка в файле", extra_blocks={"Доставка": "К воротам"})
        second = manager.folder_note_store().read(self.event)
        self.assertEqual(second["note"], "Правка в файле")
        self.assertNotEqual(first["revision"], second["revision"])
        with self.assertRaises(FolderNoteConflict):
            self.save(first, note="Старая вкладка")
        saved = self.save(second, note="Правка в менеджере")
        self.card(self.event, "Одновременная внешняя правка")
        external = (self.root / self.event / "!.txt").read_bytes()
        manager.folder_note_store().sync()
        record = manager.folder_note_store().read(self.event)
        self.assertEqual(record["note"], saved["note"])
        self.assertTrue(record["sync_pending"])
        self.assertIn("вне менеджера", record["sync_error"])
        self.assertEqual((self.root / self.event / "!.txt").read_bytes(), external)

    def test_export_race_with_new_save_keeps_new_revision_pending(self):
        record = self.save(manager.folder_note_store().read(self.event), note="Первая версия")
        atomic_write = manager.order_document.atomic_write
        def concurrent_save(target, body):
            self.save(record, note="Следующая версия")
            atomic_write(target, body)
        with patch.object(manager.order_document, "atomic_write", side_effect=concurrent_save):
            manager.folder_note_store().sync()
        latest = manager.folder_note_store().get(self.event)
        self.assertEqual(latest["note"], "Следующая версия")
        self.assertTrue(latest["sync_pending"])
        manager.folder_note_store().sync()
        self.assertFalse(manager.folder_note_store().get(self.event)["sync_pending"])
        self.assertEqual(manager.order_document.load(self.root / self.event, manager.STATUS_LABELS)["note"], latest["note"])

    def test_crash_after_publication_retries_without_overwriting_or_duplicates(self):
        self.save(manager.folder_note_store().read(self.event), note="Опубликовано")
        with patch.object(manager.order_document, "archive_legacy", side_effect=OSError("Сбой после публикации")):
            manager.folder_note_store().sync()
        self.assertTrue(manager.folder_note_store().get(self.event)["sync_pending"])
        with patch.object(manager.order_document, "atomic_write", side_effect=AssertionError("Already published")):
            manager.folder_note_store().sync()
        self.assertFalse(manager.folder_note_store().get(self.event)["sync_pending"])

    def test_legacy_and_unknown_sections_survive_note_edits(self):
        opaque = "Произвольный текст\n\nНе список"
        self.card(self.event, "Прежняя", extra_blocks={"Задачи": opaque, "Материалы": "Плёнка"})
        record = manager.folder_note_store().read(self.event)
        self.assertIsNone(record["todo_items"])
        with self.assertRaises(ValueError):
            self.save(record, todo_items=[])
        self.save(record, note="Новая")
        manager.folder_note_store().sync()
        self.assertEqual(manager.order_document.load(self.root / self.event, manager.STATUS_LABELS)["extra_blocks"],
                         {"Задачи": opaque, "Материалы": "Плёнка"})

    def test_symlink_and_failed_atomic_write_preserve_originals_and_queue(self):
        legacy = (self.root / self.event / "!status.txt")
        legacy_bytes = "Статус: Новый\n\nЗаметка:\nИсходник".encode()
        legacy.write_bytes(legacy_bytes)
        record = manager.folder_note_store().read(self.event)
        self.assertEqual(next((self.root / self.event / ".order-history").rglob("!status.txt")).read_bytes(), legacy_bytes)
        original = (self.root / self.event / "!.txt").read_bytes()
        self.save(record, note="Не потерять")
        with patch.object(manager.order_document, "atomic_write", side_effect=OSError("Нет места")):
            manager.folder_note_store().sync()
        self.assertEqual((self.root / self.event / "!.txt").read_bytes(), original)
        self.assertTrue(manager.folder_note_store().get(self.event)["sync_pending"])
        outside = self.base / "outside.txt"
        outside.write_text("Не менять")
        (self.root / self.event / "!.txt").unlink()
        (self.root / self.event / "!.txt").symlink_to(outside)
        manager.folder_note_store().sync()
        self.assertEqual(outside.read_text(), "Не менять")
        self.assertTrue(manager.folder_note_store().get(self.event)["sync_error"])

    def test_http_versions_database_only_status_and_old_browser_protection(self):
        status, _, body = self.http(self.url("/api/folder", self.event))
        self.assertEqual(status, 200)
        folder = json.loads(body)
        record = folder["folderNote"]
        with patch.object(manager, "schedule_order_sync") as schedule:
            status, _, body = self.http("/api/folder-note-save", "POST", json.dumps({"path": self.event,
                "revision": record["revision"], "note": "Из браузера", "todo_items": [{"text": "Сделать", "done": True}]}))
            self.assertEqual(status, 200)
            self.assertTrue(json.loads(body)["sync_pending"])
            schedule.assert_called_once()
        status, _, _ = self.http("/api/folder-note-save", "POST", json.dumps({"path": self.event, "revision": record["revision"], "note": "Старая"}))
        self.assertEqual(status, 409)
        status, _, _ = self.http("/api/note", "POST", json.dumps({"path": self.event, "note": "Старая вкладка"}))
        self.assertEqual(status, 409)
        self.root.rename(self.base / "offline")
        status, _, body = self.http(self.url("/api/folder-note", self.event))
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["note"], "Из браузера")
