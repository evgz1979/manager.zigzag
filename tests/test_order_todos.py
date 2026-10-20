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

    def test_missing_folder_is_hidden_without_erasing_saved_tasks(self):
        self.add()
        self.card(self.order + "/Фото", [{"text": "Не потерять", "done": False}])
        summary = OrderTodos(manager.order_store())
        summary.refresh()
        before = manager.folder_note_store().get(self.order + "/Фото")
        (self.root / self.order / "Фото").rename(self.base / "moved")
        summary.refresh()
        result = summary.attach(manager.order_store().list())[0]
        self.assertEqual(result["todo_groups"], [])
        self.assertEqual(result["todo_index"]["error"], "")
        self.assertEqual(manager.folder_note_store().get(self.order + "/Фото"), before)

    def test_external_rename_hides_cached_tasks_without_rebinding_or_erasing_notes(self):
        self.add()
        old = self.order + "/10 - Ручки"
        new = self.order + "/10 - Ручки и доводчики"
        self.card(old, [{"text": "Проверить замки", "done": False}])
        summary = OrderTodos(manager.order_store())
        summary.refresh()
        before = manager.folder_note_store().get(old)
        (self.root / old).rename(self.root / new)
        original = (self.root / new / "!.txt").read_bytes()
        summary.refresh()
        result = summary.attach(manager.order_store().list())[0]
        groups = {group["path"]: group for group in result["todo_groups"]}
        self.assertEqual(set(groups), {new})
        self.assertFalse(groups[new]["unavailable"])
        self.assertEqual(before["todo_items"], groups[new]["items"])
        for _ in range(3):
            summary.refresh()
            self.assertEqual([group["path"] for group in summary.attach(manager.order_store().list())[0]["todo_groups"]], [new])
        self.assertEqual(manager.folder_note_store().get(old), before)
        self.assertEqual((self.root / new / "!.txt").read_bytes(), original)
        self.root.rename(self.base / "offline")
        with patch.object(manager.OrderStore, "target", side_effect=AssertionError("No iCloud on main")):
            result = json.loads(self.http("/api/orders")[2])["orders"][0]
        self.assertEqual([group["path"] for group in result["todo_groups"]], [new])

    def test_returning_folder_becomes_available_without_changing_saved_tasks(self):
        self.add()
        path = self.order + "/Фото"
        self.card(path, [{"text": "Вернуть папку", "done": False}])
        summary = OrderTodos(manager.order_store())
        summary.refresh()
        before = manager.folder_note_store().get(path)
        (self.root / path).rename(self.base / "moved")
        summary.refresh()
        self.assertEqual(summary.attach(manager.order_store().list())[0]["todo_groups"], [])
        (self.base / "moved").rename(self.root / path)
        summary.refresh()
        result = summary.attach(manager.order_store().list())[0]
        self.assertFalse(result["todo_groups"][0]["unavailable"])
        self.assertEqual(result["todo_index"]["error"], "")
        self.assertEqual(manager.folder_note_store().get(path), before)

    def test_missing_folder_keeps_pending_edits_out_of_summary(self):
        self.add()
        old, new = self.order + "/Фото", self.order + "/Фотографии"
        self.card(old, [{"text": "В файле", "done": False}])
        summary = OrderTodos(manager.order_store())
        summary.refresh()
        notes = manager.folder_note_store()
        record = notes.get(old)
        saved = notes.save({"path": old, "revision": record["revision"], "note": "Невыгруженная заметка",
                            "todo_items": [{"text": "Новая задача в базе", "done": False}]})
        (self.root / old).rename(self.root / new)
        original = (self.root / new / "!.txt").read_bytes()
        summary.refresh()
        groups = {group["path"]: group for group in summary.attach(manager.order_store().list())[0]["todo_groups"]}
        self.assertNotIn(old, groups)
        self.assertFalse(groups[new]["unavailable"])
        self.assertEqual(groups[new]["items"][0]["text"], "В файле")
        self.assertEqual(notes.get(old), saved)
        self.assertEqual((self.root / new / "!.txt").read_bytes(), original)

    def test_partial_scan_does_not_mark_unseen_folders_missing_or_clear_previous_missing_state(self):
        self.add()
        for name in ("Фото", "Материалы"):
            self.card(self.order + "/" + name, [{"text": name, "done": False}])
        summary = OrderTodos(manager.order_store())
        summary.refresh()
        def unavailable_walk(target, **kwargs):
            kwargs["onerror"](PermissionError("iCloud временно недоступен"))
            return iter(())
        with patch("order_todos.os.walk", side_effect=unavailable_walk):
            summary.refresh()
        groups = summary.attach(manager.order_store().list())[0]["todo_groups"]
        self.assertFalse(any(group["unavailable"] for group in groups))
        (self.root / self.order / "Фото").rename(self.base / "moved")
        summary.refresh()
        with patch("order_todos.os.walk", side_effect=unavailable_walk):
            summary.refresh()
        groups = {group["label"]: group for group in summary.attach(manager.order_store().list())[0]["todo_groups"]}
        self.assertNotIn("Фото", groups)
        self.assertFalse(groups["Материалы"]["unavailable"])

    def test_equal_tasks_in_two_existing_folders_are_not_deduplicated(self):
        self.add()
        for name in ("10 - Ручки", "10 - Доводчики"):
            self.card(self.order + "/" + name, [{"text": "Проверить", "done": False}])
        summary = OrderTodos(manager.order_store())
        summary.refresh()
        groups = summary.attach(manager.order_store().list())[0]["todo_groups"]
        self.assertEqual(len(groups), 2)
        self.assertFalse(any(group["unavailable"] for group in groups))

    def test_existing_catalog_and_old_code_remain_compatible(self):
        self.add()
        with manager.folder_note_store().connect() as db:
            db.execute("CREATE TABLE todo_catalog (path TEXT PRIMARY KEY, checked REAL, error TEXT NOT NULL)")
            db.execute("INSERT INTO todo_catalog VALUES (?,?,?)", (self.order, 1, "Прежняя ошибка"))
        summary = OrderTodos(manager.order_store())
        summary.refresh()
        with manager.folder_note_store().connect() as db:
            db.execute("INSERT OR REPLACE INTO todo_catalog VALUES (?,?,?)", (self.order, 2, ""))
            self.assertEqual(db.execute("SELECT COUNT(*) FROM todo_missing_folders").fetchone()[0], 0)
        self.assertEqual(summary.attach(manager.order_store().list())[0]["todo_index"]["checked"], 2)

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

    def test_order_page_summary_reads_descendants_only_from_database_including_completed(self):
        own = self.add(items=[{"text": "Своя задача", "done": False}])
        notes = manager.folder_note_store()
        paths = [self.order + suffix for suffix in ("/01 - Замеры", "/01 - Замеры/Глубже/# cdr")]
        for path in paths:
            self.card(path, [{"text": "Выполнено", "done": True}, {"text": "Проверить", "done": False}])
        summary = OrderTodos(manager.order_store())
        summary.refresh()
        original = notes.get(paths[-1])
        saved = notes.save({"path": paths[-1], "revision": original["revision"], "note": "Не менять",
                            "todo_items": [{"text": "Только в базе", "done": False}]})
        self.root.rename(self.base / "offline")
        with patch.object(manager.OrderStore, "target", side_effect=AssertionError("No iCloud on order page")), \
             patch("order_todos.os.walk", side_effect=AssertionError("No scans in summary request")):
            status, _, body = self.http(self.url("/api/order-todos", self.order))
        self.assertEqual(status, 200)
        result = json.loads(body)
        self.assertEqual(result["path"], self.order)
        self.assertEqual([group["path"] for group in result["todo_groups"]], paths)
        self.assertEqual([group["label"] for group in result["todo_groups"]], ["01 - Замеры", "01 - Замеры/Глубже/# cdr"])
        self.assertEqual(result["todo_groups"][0]["items"], [{"text": "Выполнено", "done": True}, {"text": "Проверить", "done": False}])
        self.assertEqual(result["todo_groups"][1]["items"], saved["todo_items"])
        self.assertTrue(result["todo_groups"][1]["sync_pending"])
        self.assertEqual(manager.order_store().get(self.order), own)
        self.assertEqual(notes.get(paths[-1]), saved)

    def test_unregistered_order_page_collects_unopened_descendant_cards_without_registration(self):
        path = self.order + "/02 - Монтаж/Материалы"
        self.card(path, [{"text": "Прочитать без регистрации", "done": False}])
        summary = OrderTodos(manager.order_store())
        with patch.object(manager, "schedule_todo_refresh") as schedule:
            status, _, _ = self.http("/api/todos-refresh", "POST", json.dumps({"path": self.order}))
        self.assertEqual(status, 202)
        schedule.assert_called_once_with(self.order)
        before = (self.root / path / "!.txt").read_bytes()
        summary.refresh([self.order])
        result = summary.in_order(self.order)
        self.assertEqual([group["path"] for group in result["todo_groups"]], [path])
        self.assertTrue(result["todo_index"]["checked"])
        self.assertEqual(manager.order_store().list(), [])
        self.assertEqual((self.root / path / "!.txt").read_bytes(), before)

    def test_order_page_includes_old_nested_registrations_once_but_main_summary_stays_separate(self):
        self.add(items=[{"text": "Родитель", "done": False}])
        nested = self.order + "/Фото"
        self.folder("Клиент/2026-10-19 - Временный")
        child = self.add("Клиент/2026-10-19 - Временный", [{"text": "Вложенная регистрация", "done": False}])
        with manager.order_store().connect() as db:
            db.execute("UPDATE orders SET path=? WHERE id=?", (nested, child["id"]))
        self.card(nested + "/Глубже", [{"text": "В глубине", "done": False}])
        summary = OrderTodos(manager.order_store())
        summary.refresh()
        result = summary.in_order(self.order)
        self.assertEqual([group["label"] for group in result["todo_groups"]], ["Фото", "Фото/Глубже"])
        self.assertEqual([group["items"][0]["text"] for group in result["todo_groups"]], ["Вложенная регистрация", "В глубине"])
        parent = next(order for order in summary.attach(manager.order_store().list()) if order["path"] == self.order)
        self.assertEqual([group["label"] for group in parent["todo_groups"]], ["Заказ"])

    def test_order_page_hides_missing_folders_even_when_only_completed_tasks_remain(self):
        self.add()
        path = self.order + "/01 - Замеры"
        self.card(path, [{"text": "Уже выполнено", "done": True}])
        summary = OrderTodos(manager.order_store())
        summary.refresh()
        before = manager.folder_note_store().get(path)
        self.assertTrue(summary.in_order(self.order)["todo_groups"])
        (self.root / path).rename(self.base / "moved")
        for _ in range(2):
            summary.refresh()
            self.assertEqual(summary.in_order(self.order)["todo_groups"], [])
        self.assertEqual(manager.folder_note_store().get(path), before)

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
