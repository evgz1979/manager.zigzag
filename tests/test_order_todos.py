import json
import shutil
import unittest
from unittest.mock import patch

import test_server as fixtures
from order_todos import OrderTodos

manager = fixtures.manager


class OrderTodoTests(unittest.TestCase):
    setUp = fixtures.ManagerTests.setUp
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url
    order = "Клиент/2026-00-00 - Заказ"

    def add(self, path=None, items=None):
        return manager.order_store().add(path or self.order, {"status": "process", "note": "Заказ", "extra_blocks":
            manager.order_document.write_todos({}, items or [])})

    def card(self, path, items=None, legacy=None):
        blocks = {"Задачи": legacy} if legacy is not None else manager.order_document.write_todos({}, items or [])
        self.file(path + "/!.txt", manager.order_document.render({"note": "Заметка", "extra_blocks": blocks}, manager.STATUS_LABELS).encode())

    def test_list_reads_only_database_and_includes_independent_pending_tasks_at_every_depth(self):
        self.add(items=[{"text": "Задача заказа", "done": False}])
        notes = manager.folder_note_store()
        for suffix in ("Фото", "Фото/Детали/# bills"):
            path = self.order + "/" + suffix
            self.folder(path)
            record = notes.read(path)
            notes.save({"path": path, "revision": record["revision"], "note": "", "todo_items": [{"text": suffix, "done": False}]})
        self.root.rename(self.base / "offline")
        with patch.object(manager.OrderStore, "target", side_effect=AssertionError("No document reads on main page")), \
             patch("order_todos.os.walk", side_effect=AssertionError("No scans on main page")):
            status, _, body = self.http("/api/orders")
        self.assertEqual(status, 200)
        order = json.loads(body)["orders"][0]
        self.assertEqual([item["label"] for item in order["todo_groups"]], ["Заказ", "Фото", "Фото/Детали/# bills"])
        self.assertEqual(order["todo_items"], [{"text": "Задача заказа", "done": False}])
        self.assertTrue(order["todo_groups"][2]["sync_pending"])
        self.assertFalse(order["todo_groups"][2]["items"][0]["done"])

    def test_background_refresh_imports_unopened_cards_read_only_and_skips_hidden_symlinks(self):
        self.add()
        paths = [self.order + suffix for suffix in ("/02 - Монтаж", "/02 - Монтаж/Глубже/Детали", "/# bills")]
        originals = {}
        for path in paths:
            self.card(path, [{"text": path.rsplit("/", 1)[-1], "done": False}])
            originals[path] = (self.root / path / "!.txt").read_bytes()
        self.card(self.order + "/.hidden", [{"text": "Скрытые", "done": False}])
        outside = self.base / "outside"
        outside.mkdir()
        (outside / "!.txt").write_text(manager.order_document.render({"note": "", "extra_blocks": {"Задачи": "- [ ] Снаружи"}}, manager.STATUS_LABELS))
        (self.root / self.order / "Ссылка").symlink_to(outside)
        self.card("# docs/Внутри", [{"text": "Общие", "done": False}])
        summary = OrderTodos(manager.order_store())
        summary.refresh()
        result = summary.attach(manager.order_store().list())[0]
        self.assertEqual({item["path"] for item in result["todo_groups"]}, set(paths))
        self.assertTrue(result["todo_index"]["checked"])
        self.assertEqual(result["todo_index"]["error"], "")
        for path, before in originals.items():
            self.assertEqual((self.root / path / "!.txt").read_bytes(), before)

    def test_external_edits_and_empty_lists_update_but_pending_database_wins(self):
        self.add()
        path = self.order + "/Фото"
        self.card(path, [{"text": "Было", "done": False}])
        summary = OrderTodos(manager.order_store())
        summary.refresh()
        self.card(path, [{"text": "Изменено в файле", "done": False}])
        summary.refresh()
        self.assertEqual(summary.attach(manager.order_store().list())[0]["todo_groups"][0]["items"], [{"text": "Изменено в файле", "done": False}])
        self.card(path, [])
        summary.refresh()
        self.assertEqual(summary.attach(manager.order_store().list())[0]["todo_groups"], [])
        notes = manager.folder_note_store()
        record = notes.get(path)
        notes.save({"path": path, "revision": record["revision"], "note": "", "todo_items": [{"text": "Невыгруженное", "done": False}]})
        self.card(path, [{"text": "Одновременно с iPhone", "done": True}])
        summary.refresh()
        group = summary.attach(manager.order_store().list())[0]["todo_groups"][0]
        self.assertEqual(group["items"], [{"text": "Невыгруженное", "done": False}])
        self.assertTrue(group["sync_pending"])

    def test_opaque_legacy_tasks_preserved_and_offline_error_does_not_erase_cache(self):
        self.add()
        opaque = "Прежний текст\n\nНе преобразовывать"
        self.card(self.order + "/Фото", legacy=opaque)
        summary = OrderTodos(manager.order_store())
        summary.refresh()
        first = summary.attach(manager.order_store().list())[0]
        self.assertIsNone(first["todo_groups"][0]["items"])
        self.assertEqual(first["todo_groups"][0]["legacy_text"], opaque)
        self.root.rename(self.base / "offline")
        summary.refresh()
        second = summary.attach(manager.order_store().list())[0]
        self.assertEqual(second["todo_groups"], first["todo_groups"])
        self.assertEqual(second["todo_index"]["checked"], first["todo_index"]["checked"])
        self.assertTrue(second["todo_index"]["error"])

    def test_previous_nested_registrations_do_not_duplicate_or_mix_tasks(self):
        self.add(items=[{"text": "Родитель", "done": False}])
        nested = self.order + "/Фото"
        # Старая ошибочная регистрация сохраняется; её задачи принадлежат собственной строке.
        self.folder("Клиент/2026-10-19 - Временный")
        child = self.add("Клиент/2026-10-19 - Временный", [{"text": "Отдельная старая запись", "done": False}])
        with manager.order_store().connect() as db:
            db.execute("UPDATE orders SET path=? WHERE id=?", (nested, child["id"]))
        self.card(nested + "/Глубже", [{"text": "В глубине", "done": False}])
        summary = OrderTodos(manager.order_store())
        summary.refresh()
        result = {row["path"]: row for row in summary.attach(manager.order_store().list())}
        self.assertEqual([group["label"] for group in result[self.order]["todo_groups"]], ["Заказ"])
        self.assertEqual([group["label"] for group in result[nested]["todo_groups"]], ["Заказ", "Глубже"])

    def test_missing_folder_keeps_saved_tasks_and_reports_incomplete_catalog(self):
        self.add()
        self.card(self.order + "/Фото", [{"text": "Не потерять", "done": False}])
        summary = OrderTodos(manager.order_store())
        summary.refresh()
        (self.root / self.order / "Фото").rename(self.base / "moved")
        summary.refresh()
        result = summary.attach(manager.order_store().list())[0]
        self.assertEqual(result["todo_groups"][0]["items"][0]["text"], "Не потерять")
        self.assertIn("Недоступны", result["todo_index"]["error"])

    def test_finishing_status_round_trips_database_file_rebuild_and_independent_finance(self):
        record = self.add()
        store = manager.order_store()
        saved = store.save({"path": record["path"], "revision": record["revision"], "title": record["title"],
            "status": "finishing", "financial_status": "paid", "note": "Добить мелочи", "amount": "100", "costs": "50", "paid": "100"})
        store.sync()
        self.assertEqual(store.get(self.order)["financial_status"], "paid")
        self.assertIn("Статус: Завершение/добивка", (self.root / self.order / "!.txt").read_text())
        shutil.rmtree(manager.DATA_DIR)
        restored = manager.order_store().import_folder(self.order)
        self.assertEqual((restored["status"], restored["financial_status"]), ("finishing", "paid"))

    def test_order_listing_does_not_read_attachments_but_event_and_deeper_do(self):
        self.file(self.order + "/root.pdf", b"root")
        self.file(self.order + "/Фото/Глубже/file.txt", b"event")
        with patch.object(manager.os, "walk", side_effect=AssertionError("Order must not read attachments")):
            folder = manager.read_folder(self.order)
        self.assertEqual((folder["filesScope"], folder["files"], folder["fileCount"]), ("events", [], 0))
        listing = manager.read_folder(self.order + "/Фото")
        self.assertEqual(listing["filesScope"], "folder")
        self.assertTrue(any(file["name"] == "file.txt" for file in listing["files"]))
        self.assertEqual((self.root / self.order / "root.pdf").read_bytes(), b"root")

    def test_explicit_refresh_endpoint_schedules_background_work(self):
        with patch.object(manager, "schedule_todo_refresh") as schedule:
            status, _, _ = self.http("/api/todos-refresh", "POST", "{}")
        self.assertEqual(status, 202)
        schedule.assert_called_once()

    def test_main_page_shows_only_open_tasks_without_erasing_completed_items(self):
        completed = {"text": "Выполнено у заказа", "done": True}
        self.add(items=[completed, {"text": "Актуально у заказа", "done": False}])
        self.card(self.order + "/Фото", [{"text": "Выполнено у события", "done": True}, {"text": "Актуально у события", "done": False}])
        self.card(self.order + "/Фото/Готово", [{"text": "Всё выполнено", "done": True}])
        summary = OrderTodos(manager.order_store())
        summary.refresh()
        result = summary.attach(manager.order_store().list())[0]
        self.assertEqual([item["text"] for group in result["todo_groups"] for item in (group["items"] or [])], ["Актуально у заказа", "Актуально у события"])
        self.assertIn(completed, manager.order_store().get(self.order)["todo_items"])
        event = manager.folder_note_store().get(self.order + "/Фото")
        self.assertTrue(event["todo_items"][0]["done"])
        self.assertEqual(len(event["todo_items"]), 2)
        self.assertTrue(manager.folder_note_store().get(self.order + "/Фото/Готово")["todo_items"][0]["done"])
