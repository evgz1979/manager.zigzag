import json
import shutil
import unittest
from unittest.mock import patch

import event_relevance as relevance
import test_server as fixtures
from folder_notes import FolderNoteConflict

manager = fixtures.manager


class EventRelevanceTests(unittest.TestCase):
    setUp = fixtures.ManagerTests.setUp
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url
    order = "Клиент/2026-00-00 - Заказ"
    event = order + "/Фото"

    def change(self, record, value):
        return manager.folder_note_store().save_relevance({"path": record["path"], "revision": record["revision"], "value": value})

    def card(self, blocks, note="Заметка события"):
        self.file(self.event + "/!.txt", manager.order_document.render({"note": note, "extra_blocks": blocks}, manager.STATUS_LABELS).encode())

    def test_existing_and_new_events_default_to_none_only_direct_children_have_switches(self):
        self.folder(self.order + "/00 - Замеры")
        self.folder(self.order + "/# bills")
        self.folder(self.event + "/Глубже")
        listing = manager.read_folder(self.order)
        by_name = {item["name"]: item for item in listing["directories"]}
        for name in ("Фото", "00 - Замеры"):
            self.assertEqual(by_name[name]["eventRelevance"]["value"], "none")
            self.assertTrue(by_name[name]["eventRelevance"]["revision"])
        self.assertNotIn("eventRelevance", by_name["# bills"])
        for path in ("Клиент", self.event):
            self.assertTrue(all("eventRelevance" not in item for item in manager.read_folder(path)["directories"]))
        self.assertFalse((self.root / self.event / "!.txt").exists())
        self.assertEqual(manager.order_store().list(), [])

    def test_switch_is_database_only_preserves_tasks_unknown_blocks_and_parent(self):
        store = manager.order_store()
        store.add(self.order, {"status": "process", "financial_status": "paid", "note": "Заказ"})
        store.sync()
        parent = store.get(self.order)
        blocks = {"Задачи": "Произвольный старый текст", "Материалы": "Плёнка"}
        self.card(blocks)
        record = manager.folder_note_store().read(self.event)
        original = (self.root / self.event / "!.txt").read_bytes()
        self.root.rename(self.base / "offline")
        for value in ("active", "check", "inactive", "none"):
            record = self.change(record, value)
            self.assertEqual(relevance.read(record["extra_blocks"]), value)
            self.assertEqual(record["note"], "Заметка события")
            self.assertIsNone(record["todo_items"])
            self.assertEqual(record["extra_blocks"]["Материалы"], "Плёнка")
        self.assertEqual(store.get(self.order), parent)
        manager.folder_note_store().sync()
        self.assertTrue(manager.folder_note_store().get(self.event)["sync_error"])
        (self.base / "offline").rename(self.root)
        self.assertEqual((self.root / self.event / "!.txt").read_bytes(), original)
        manager.folder_note_store().sync()
        self.assertFalse(manager.folder_note_store().get(self.event)["sync_pending"])

    def test_export_rebuild_external_edit_and_note_edits_keep_relevance(self):
        self.card({"Материалы": "Плёнка", "Задачи": "- [ ] Замер"})
        notes = manager.folder_note_store()
        before = notes.read(self.event)
        record = self.change(before, "check")
        with self.assertRaises(FolderNoteConflict):
            notes.save({"path": self.event, "revision": before["revision"], "note": "Старая вкладка"})
        record = notes.save({"path": self.event, "revision": record["revision"], "note": "Новая заметка", "todo_items": [{"text": "Замер", "done": True}]})
        notes.sync()
        card = self.root / self.event / "!.txt"
        self.assertIn("[Актуальность события]\nПроверить", card.read_text())
        self.assertEqual(relevance.read(manager.order_document.load(card.parent, manager.STATUS_LABELS)["extra_blocks"]), "check")
        shutil.rmtree(manager.DATA_DIR)
        rebuilt = manager.folder_note_store().read(self.event)
        self.assertEqual(relevance.read(rebuilt["extra_blocks"]), "check")
        self.assertEqual(rebuilt["todo_items"], [{"text": "Замер", "done": True}])
        with self.assertRaises(FolderNoteConflict):
            self.change(record, "inactive")
        card.write_text(card.read_text().replace("\nПроверить\n", "\nНеактуально\n"))
        imported = manager.folder_note_store().read(self.event)
        self.assertEqual(relevance.read(imported["extra_blocks"]), "inactive")
        self.assertNotEqual(imported["revision"], rebuilt["revision"])

    def test_external_conflict_keeps_both_versions_and_queue(self):
        self.card({relevance.BLOCK: "Без статуса"})
        record = self.change(manager.folder_note_store().read(self.event), "active")
        self.card({relevance.BLOCK: "Неактуально"}, note="Внешняя правка")
        raw = (self.root / self.event / "!.txt").read_bytes()
        manager.folder_note_store().sync()
        latest = manager.folder_note_store().get(self.event)
        self.assertEqual(relevance.read(latest["extra_blocks"]), "active")
        self.assertEqual(latest["revision"], record["revision"])
        self.assertTrue(latest["sync_pending"])
        self.assertIn("вне менеджера", latest["sync_error"])
        self.assertEqual((self.root / self.event / "!.txt").read_bytes(), raw)

    def test_unknown_relevance_text_is_preserved_without_overwrite(self):
        self.card({relevance.BLOCK: "Ручные подробности\nНе заменять", "Задачи": "- [ ] Сделать"})
        record = manager.folder_note_store().read(self.event)
        self.assertIsNone(relevance.read(record["extra_blocks"]))
        self.assertTrue(relevance.info(record)["error"])
        with self.assertRaisesRegex(ValueError, "неизвестный текст"):
            self.change(record, "active")
        record = manager.folder_note_store().save({"path": self.event, "revision": record["revision"], "note": "Новая заметка"})
        manager.folder_note_store().sync()
        self.assertEqual(record["extra_blocks"][relevance.BLOCK], "Ручные подробности\nНе заменять")

    def test_http_versions_scope_validation_and_local_poll(self):
        self.http(self.url("/api/folder", self.order))
        before = manager.folder_note_store().get(self.event)
        payload = {"path": self.event, "revision": before["revision"], "value": "check"}
        with patch.object(manager, "schedule_order_sync") as schedule:
            status, _, body = self.http("/api/event-relevance", "POST", json.dumps(payload))
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)["value"], "check")
            schedule.assert_called_once()
        self.assertEqual(self.http("/api/event-relevance", "POST", json.dumps(payload))[0], 409)
        for value in (None, [], True, "process", "Актуально"):
            self.assertEqual(self.http("/api/event-relevance", "POST", json.dumps({**payload, "value": value}))[0], 400)
        for path in (self.event + "/Глубже", self.order + "/# bills"):
            self.folder(path)
            record = manager.folder_note_store().read(path)
            self.assertEqual(self.http("/api/event-relevance", "POST", json.dumps({"path": path, "revision": record["revision"], "value": "active"}))[0], 400)
        self.root.rename(self.base / "offline")
        status, _, body = self.http(self.url("/api/event-relevance", self.order))
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)[self.event]["value"], "check")

    def test_unreadable_event_card_does_not_hide_other_events(self):
        self.folder(self.order + "/01 - Монтаж")
        self.file(self.event + "/!.txt", b"broken")
        listing = {item["name"]: item for item in manager.read_folder(self.order)["directories"]}
        self.assertTrue(listing["Фото"]["eventRelevance"]["error"])
        self.assertEqual(listing["01 - Монтаж"]["eventRelevance"]["value"], "none")
