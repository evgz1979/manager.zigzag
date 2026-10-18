import json
import shutil
import sqlite3
import unittest
from unittest.mock import patch
import test_server as fixtures

manager = fixtures.manager


class OrderTests(unittest.TestCase):
    setUp = fixtures.ManagerTests.setUp
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url

    def add(self, path="Клиент/2026-00-00 - Заказ"):
        return manager.order_store().add(path, {"status": "process", "note": "Позвонить\nклиенту"})

    def payload(self, record, **changes):
        return {"path": record["path"], "revision": record["revision"], "title": record["title"],
                "status": record["status"], "financial_status": record["financial_status"], "note": record["note"], "amount": "100 000,50",
                "costs": "40000.25", "paid": "25000", **changes}

    def test_finances_are_exact_and_empty_is_not_zero(self):
        store = manager.order_store()
        record = self.add()
        self.assertIsNone(record["amount"])
        self.assertIsNone(record["profit"])
        saved = store.save(self.payload(record))
        self.assertEqual((saved["amount"], saved["costs"], saved["profit"], saved["debt"]),
                         (10000050, 4000025, 6000025, 7500050))
        for invalid in ("NaN", "Infinity", "-1", "0.001", "abc", True, "1e1000"):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                store.save(self.payload(saved, amount=invalid))
        cleared = store.save(self.payload(saved, amount="", paid="0"))
        self.assertIsNone(cleared["amount"])
        self.assertEqual(cleared["paid"], 0)
        self.assertIsNone(cleared["debt"])

    def test_todos_survive_offline_edits_export_and_full_database_rebuild(self):
        store = manager.order_store()
        initial = [{"text": "Уточнить размеры", "done": False}]
        record = store.save(self.payload(self.add(), todo_items=initial))
        store.sync()
        folder = self.root / record["path"]
        body = (folder / "!.txt").read_text().replace("[Служебное]", "[Доставка]\nКо входу\n\n[Служебное]")
        (folder / "!.txt").write_text(body)
        self.root.rename(self.base / "offline")
        updated = [{"text": "Уточнить размеры", "done": True}, {"text": "Передать [Финансы] в цех", "done": False}]
        with patch.object(store, "target", side_effect=AssertionError("No iCloud access while saving")):
            record = store.save(self.payload(record, todo_items=updated))
        self.assertEqual(manager.order_store().get(record["path"])["todo_items"], updated)
        (self.base / "offline").rename(self.root)
        store.sync()
        self.assertEqual(store.get(record["path"])["todo_items"], updated)
        self.assertIn("- [x] Уточнить размеры", (folder / "!.txt").read_text())
        self.assertEqual(store.get(record["path"])["extra_blocks"]["Доставка"], "Ко входу")
        shutil.rmtree(manager.DATA_DIR)
        record = manager.order_store().import_folder(record["path"])
        self.assertEqual(record["todo_items"], updated)
        self.assertEqual((record["status"], record["financial_status"], record["amount"]), ("process", "unspecified", 10000050))
        record = store.save(self.payload(record, todo_items=[]))
        store.sync()
        self.assertEqual(manager.order_document.read_todos(manager.order_document.load(folder, manager.STATUS_LABELS)["extra_blocks"]), [])
        self.assertEqual(store.get(record["path"])["todo_items"], [])

    def test_unregistered_todos_and_external_checkboxes_are_imported(self):
        path = "Клиент/2026-00-00 - Заказ"
        manager.save_status(path, "install", "Заметка", "payment", [{"text": "Согласовать монтаж", "done": False}])
        folder = self.root / path
        (folder / "!.txt").write_text((folder / "!.txt").read_text().replace("- [ ] Согласовать", "- [X] Согласовать"))
        self.assertEqual(manager.read_folder(path)["todo_items"], [{"text": "Согласовать монтаж", "done": True}])
        record = manager.order_store().import_folder(path)
        self.assertTrue(record["todo_items"][0]["done"])
        self.assertEqual((record["status"], record["financial_status"]), ("install", "payment"))

    def test_todo_validation_and_stale_edits_cannot_erase_tasks(self):
        store = manager.order_store()
        items = [{"text": "Не потерять", "done": True}]
        record = store.save(self.payload(self.add(), todo_items=items))
        for invalid in (None, {}, [{"text": "", "done": False}], [{"text": "Строка\nЕщё", "done": False}],
                        [{"text": "Задача", "done": "false"}], [{"text": "x" * 1001, "done": True}]):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                store.save(self.payload(record, todo_items=invalid))
        saved = store.save(self.payload(record, note="Меняется только заметка"))
        self.assertEqual(saved["todo_items"], items)
        with self.assertRaises(manager.OrderConflict):
            store.save(self.payload(record, todo_items=[]))
        self.assertEqual(store.get(record["path"])["todo_items"], items)
        with patch.object(manager, "schedule_order_sync"):
            status, _, body = self.http("/api/order-save", "POST", json.dumps(self.payload(saved, todo_items=[{"text": "Новая задача", "done": False}])))
            self.assertEqual((status, json.loads(body)["todo_items"]), (200, [{"text": "Новая задача", "done": False}]))

    def test_existing_free_form_task_section_is_preserved_when_editing_card(self):
        path = "Клиент/2026-00-00 - Заказ"
        opaque = "Произвольный текст\n\nНе превращать в пустой список"
        self.file(path + "/!.txt", manager.order_document.render({"status": "process", "note": "Заметка",
            "extra_blocks": {"Задачи": opaque}}, manager.STATUS_LABELS).encode())
        store = manager.order_store()
        record = store.import_folder(path)
        self.assertIsNone(record["todo_items"])
        record = store.save(self.payload(record, note="Изменить заметку"))
        store.sync()
        self.assertEqual(record["extra_blocks"]["Задачи"], opaque)
        self.assertEqual(manager.order_document.load(self.root / path, manager.STATUS_LABELS)["extra_blocks"]["Задачи"], opaque)

    def test_financial_and_production_statuses_are_independent_even_offline(self):
        store = manager.order_store()
        record = self.add()
        self.root.rename(self.base / "offline")
        try:
            record = store.save(self.payload(record, status="rework", financial_status="paid", amount="", costs="", paid=""))
            self.assertEqual((record["status"], record["financial_status"], record["paid"]), ("rework", "paid", None))
            record = store.save(self.payload(record, status="done_but", financial_status="paid"))
            self.assertEqual((record["status"], record["financial_status"]), ("done_but", "paid"))
            record = store.save(self.payload(record, financial_status="payment", amount="100", paid="100"))
            self.assertEqual((record["status"], record["financial_status"], record["debt"]), ("done_but", "payment", 0))
            payload = self.payload(record, status="install")
            del payload["financial_status"]
            record = store.save(payload)
            self.assertEqual((record["status"], record["financial_status"]), ("install", "payment"))
            store.sync()
            self.assertTrue(store.get(record["path"])["sync_pending"])
        finally:
            (self.base / "offline").rename(self.root)
        store.sync()
        loaded = manager.order_document.load(self.root / record["path"], manager.STATUS_LABELS)
        self.assertEqual((loaded["status"], loaded["financial_status"]), ("install", "payment"))

    def test_legacy_payment_card_is_split_with_original_bytes_preserved(self):
        path = "Клиент/2026-00-00 - Заказ"
        folder = self.root / path
        body = manager.order_document.render({"status": "unspecified", "financial_status": "payment", "note": "Заметка",
            "amount": 12345, "extra_blocks": {"Доставка": "До двери"}}, manager.STATUS_LABELS)
        body = body.replace("Статус: Не указан", "Статус: На оплате").replace("Статус оплаты: На оплате\n", "").replace("Формат: 3", "Формат: 2")
        original = b"\xef\xbb\xbf" + body.replace("\n", "\r\n").encode()
        self.file(path + "/!.txt", original)
        store = manager.order_store()
        record = store.import_folder(path)
        self.assertEqual((record["status"], record["financial_status"]), ("unspecified", "payment"))
        store.sync()
        self.assertEqual(next((folder / ".order-history").rglob("!.txt")).read_bytes(), original)
        loaded = manager.order_document.load(folder, manager.STATUS_LABELS)
        self.assertEqual((loaded["schema"], loaded["amount"], loaded["extra_blocks"]), (3, 12345, {"Доставка": "До двери"}))
        self.assertEqual((loaded["status"], loaded["financial_status"]), ("unspecified", "payment"))

    def test_financial_status_http_rejects_invalid_fields_and_keeps_manual_choice(self):
        with patch.object(manager, "schedule_order_sync"):
            record = self.add()
            status, _, body = self.http("/api/order-save", "POST", json.dumps(self.payload(record, status="done", financial_status="partial")))
            self.assertEqual(status, 200)
            saved = json.loads(body)
            self.assertEqual((saved["status"], saved["financial_status"]), ("done", "partial"))
            for changes in ({"status": "payment"}, {"financial_status": "other"}, {"financial_status": None}):
                status, _, _ = self.http("/api/order-save", "POST", json.dumps(self.payload(saved, **changes)))
                self.assertEqual(status, 400)
            status, _, body = self.http(self.url("/api/order", saved["path"]))
            self.assertEqual((status, json.loads(body)["financial_status"]), (200, "partial"))
            self.assertEqual(manager.order_store().get(saved["path"])["revision"], saved["revision"])

    def test_list_and_save_work_with_unavailable_document_root(self):
        store = manager.order_store()
        record = self.add()
        self.root.rename(self.base / "offline")
        with patch.object(manager.os, "walk", side_effect=AssertionError("No iCloud scan")), \
                patch.object(store, "target", side_effect=AssertionError("No iCloud access")):
            saved = store.save(self.payload(record))
            self.assertEqual(store.list()[0]["amount"], 10000050)
        store.sync()
        record = store.get(saved["path"])
        self.assertTrue(record["sync_pending"])
        self.assertTrue(record["sync_error"])
        (self.base / "offline").rename(self.root)
        store.sync()
        self.assertFalse(store.get(record["path"])["sync_pending"])
        self.assertIn("100 000,50 ₽", (self.root / record["path"] / "!.txt").read_text())

    def test_unified_export_can_rebuild_entire_register(self):
        store = manager.order_store()
        record = store.save(self.payload(self.add(), status="process", financial_status="payment"))
        store.sync()
        target = self.root / record["path"]
        self.assertEqual(manager.read_status_document(target), {"status": "process", "financial_status": "payment", "note": record["note"]})
        snapshot = manager.order_document.load(target, manager.STATUS_LABELS)
        self.assertEqual(snapshot["amount"], 10000050)
        self.assertIn("Остаток оплаты: 75 000,50 ₽", (target / "!.txt").read_text())
        self.assertNotIn("!.txt", [file["name"] for file in manager.read_folder(record["path"])["files"]])
        shutil.rmtree(manager.DATA_DIR)
        progress = {"folders": 0, "added": 0, "errors": []}
        manager.order_store().discover(manager.read_status_document, progress)
        restored = manager.order_store().list()[0]
        self.assertEqual(progress["added"], 1)
        for key in ("id", "title", "status", "financial_status", "note", "amount", "costs", "paid"):
            self.assertEqual(record[key], restored[key])

    def test_imports_only_marked_folders_and_database_wins_on_later_scan(self):
        self.file("Клиент/2026-00-00 - Заказ/!status.txt", "Статус: На оплате\n\nЗаметка:\nИз прежнего !status.txt".encode())
        store = manager.order_store()
        progress = {"folders": 0, "added": 0, "errors": []}
        store.discover(manager.read_status_document, progress)
        self.assertEqual([item["path"] for item in store.list()], ["Клиент/2026-00-00 - Заказ"])
        self.assertEqual(store.list()[0]["note"], "Из прежнего !status.txt")
        store.save(self.payload(store.list()[0], note="Новая заметка из базы"))
        store.discover(manager.read_status_document, progress)
        self.assertEqual(store.list()[0]["note"], "Новая заметка из базы")
        self.assertEqual(manager.read_folder("Клиент/2026-00-00 - Заказ")["note"], "Новая заметка из базы")

    def test_revisions_reject_stale_edits_without_losing_values(self):
        store = manager.order_store()
        original = self.add()
        saved = store.save(self.payload(original, note="Новая версия"))
        with self.assertRaises(manager.OrderConflict):
            store.save(self.payload(original, note="Старая вкладка"))
        self.assertEqual(store.get(saved["path"])["note"], "Новая версия")

    def test_removal_requires_confirmation_and_current_revision(self):
        store = manager.order_store()
        original = self.add()
        payload = {"path": original["path"], "revision": original["revision"]}
        for confirmed in (None, False, "true", 1):
            with self.subTest(confirmed=confirmed), self.assertRaises(ValueError):
                store.remove({**payload, "confirmed": confirmed})
        saved = store.save(self.payload(original))
        with self.assertRaises(manager.OrderConflict):
            store.remove({**payload, "confirmed": True})
        removed = store.remove({**payload, "revision": saved["revision"], "confirmed": True})
        self.assertFalse(removed["registered"])
        self.assertIsNone(store.get(original["path"]))
        with self.assertRaises(manager.OrderConflict):
            store.save(self.payload(saved))

    def test_removal_is_local_durable_and_does_not_remove_child_orders(self):
        store = manager.order_store()
        parent = store.save(self.payload(self.add(), note="Последняя заметка", financial_status="partial"))
        # A historical nested registration must survive removal of its parent.
        with store.connect() as db:
            db.execute("INSERT INTO orders (path,id,title,status,note,revision,updated) VALUES (?,?,?,?,?,1,0)",
                       (parent["path"] + "/Фото", "00000000-0000-4000-8000-000000000099", "Старая вложенная запись", "new", ""))
        child = store.get(parent["path"] + "/Фото")
        original_file = self.root / "Клиент/2026-00-00 - Заказ/Фото/файл%2F #.txt"
        original_bytes = original_file.read_bytes()
        self.root.rename(self.base / "offline")
        with patch.object(store, "target", side_effect=AssertionError("No cloud access")), \
                patch.object(manager.os, "walk", side_effect=AssertionError("No cloud scan")):
            removed = store.remove({"path": parent["path"], "revision": parent["revision"], "confirmed": True})
            self.assertEqual([record["path"] for record in store.list()], [child["path"]])
        store.sync()
        restarted = manager.order_store()
        pending = restarted.get(parent["path"], include_unregistered=True)
        self.assertTrue(pending["sync_pending"])
        self.assertTrue(pending["sync_error"])
        self.assertEqual((pending["note"], pending["amount"]), (parent["note"], parent["amount"]))
        self.assertEqual(restarted.pending_unregistrations()[0]["path"], parent["path"])
        (self.base / "offline").rename(self.root)
        restarted.sync()
        self.assertEqual(restarted.pending_unregistrations(), [])
        self.assertEqual(original_file.read_bytes(), original_bytes)
        self.assertIsNotNone(restarted.get(child["path"]))
        card = manager.order_document.load(self.root / parent["path"], manager.STATUS_LABELS)
        self.assertFalse(card["registered"])
        self.assertEqual((card["note"], card["amount"], card["financial_status"]), (parent["note"], parent["amount"], "partial"))

    def test_removed_card_does_not_reappear_on_scan_or_database_rebuild(self):
        store = manager.order_store()
        original = store.save(self.payload(self.add()))
        store.remove({"path": original["path"], "revision": original["revision"], "confirmed": True})
        progress = {"folders": 0, "added": 0, "errors": []}
        store.discover(manager.read_status_document, progress)
        self.assertEqual(store.list(), [])
        store.sync()
        shutil.rmtree(manager.DATA_DIR)
        store.discover(manager.read_status_document, progress)
        self.assertEqual((store.list(), progress["added"], progress["errors"]), ([], 0, []))
        restored = store.import_folder(original["path"])
        self.assertTrue(restored["registered"])
        self.assertEqual((restored["amount"], restored["note"]), (original["amount"], original["note"]))
        store.sync()
        self.assertTrue(manager.order_document.load(self.root / original["path"], manager.STATUS_LABELS)["registered"])

    def test_manual_readdition_before_export_keeps_newest_database_values(self):
        store = manager.order_store()
        original = self.add()
        store.sync()
        newest = store.save(self.payload(original, note="Ещё не выгружено"))
        store.remove({"path": newest["path"], "revision": newest["revision"], "confirmed": True})
        restored = store.import_folder(newest["path"])
        self.assertTrue(restored["registered"])
        self.assertEqual((restored["note"], restored["amount"]), (newest["note"], newest["amount"]))
        self.assertGreater(restored["revision"], newest["revision"])

    def test_removed_folder_note_keeps_finances_extra_blocks_and_file_edits(self):
        store = manager.order_store()
        record = store.save(self.payload(self.add()))
        folder = self.root / record["path"]
        document = manager.order_document
        (folder / "!.txt").write_text(document.render({"status": "new", "note": "Прежнее", "extra_blocks": {"Материалы": "Стекло"}}, manager.STATUS_LABELS))
        store.remove({"path": record["path"], "revision": record["revision"], "confirmed": True})
        with self.assertRaises(manager.OrderConflict):
            manager.save_note(record["path"], "Подождать выгрузку")
        store.sync()
        manager.save_note(record["path"], "Заметка объекта")
        card = document.load(folder, manager.STATUS_LABELS)
        self.assertFalse(card["registered"])
        self.assertEqual((card["note"], card["amount"], card["extra_blocks"]), ("Заметка объекта", record["amount"], {"Материалы": "Стекло"}))
        self.assertTrue(manager.read_folder(record["path"])["noteOnly"])
        store.sync()
        self.assertEqual(document.load(folder, manager.STATUS_LABELS)["note"], "Заметка объекта")
        restored = store.import_folder(record["path"])
        self.assertEqual((restored["note"], restored["amount"]), ("Заметка объекта", record["amount"]))

    def test_http_remove_confirmation_pending_note_and_manual_readdition(self):
        original = self.add()
        payload = {"path": original["path"], "revision": original["revision"]}
        with patch.object(manager, "schedule_order_sync"):
            status, _, _ = self.http("/api/order-remove", "POST", json.dumps(payload))
            self.assertEqual(status, 400)
            status, _, body = self.http("/api/order-remove", "POST", json.dumps({**payload, "confirmed": True}))
            self.assertEqual(status, 200)
            self.assertFalse(json.loads(body)["registered"])
            status, _, _ = self.http(self.url("/api/order", original["path"]))
            self.assertEqual(status, 404)
            status, _, body = self.http("/api/orders")
            self.assertEqual(json.loads(body)["orders"], [])
            self.assertEqual(json.loads(body)["unregistrations"][0]["path"], original["path"])
            status, _, body = self.http(self.url("/api/folder", original["path"]))
            folder = json.loads(body)
            self.assertTrue(folder["noteOnly"])
            self.assertTrue(folder["registrationPending"])
            self.assertNotIn("order", folder)
            manager.order_store().sync()
            status, _, _ = self.http("/api/note", "POST", json.dumps({"path": original["path"], "note": "Заметка объекта"}))
            self.assertEqual(status, 200)
            status, _, body = self.http("/api/order-add", "POST", json.dumps({"path": original["path"]}))
            self.assertEqual(status, 201)
            self.assertEqual(json.loads(body)["note"], "Заметка объекта")

    def test_service_subtrees_cannot_be_registered_or_discovered(self):
        parent = "Клиент/2026/2026-01-00 - Заказ"
        manager.save_status(parent, "process", "Заказ")
        for suffix in ("#bills", "# bills", "#cdr", "# cdr/Макеты"):
            relative = parent + "/" + suffix
            self.folder(relative)
            self.file(relative + "/!status.txt", "Статус: Новый\n\nЗаметка:\nСлужебная папка".encode())
            with self.subTest(relative=relative), self.assertRaises(ValueError):
                manager.order_store().add(relative, {})
        progress = {"folders": 0, "added": 0, "errors": []}
        store = manager.order_store()
        store.discover(manager.read_status_document, progress)
        self.assertEqual((progress["added"], progress["errors"]), (1, []))
        self.assertEqual([record["path"] for record in store.list()], [parent])
        self.assertEqual(manager.read_folder(parent)["fileCount"], 1)

    def test_previous_service_registration_is_discarded_and_folder_note_wins(self):
        store = manager.order_store()
        record = store.save(self.payload(self.add()))
        relative = "Клиент/2026/2026-01-00 - Заказ/# счета"
        # Simulate an order registered before service folders were excluded.
        with store.connect() as db:
            db.execute("UPDATE orders SET path=? WHERE path=?", (relative, record["path"]))
        self.assertEqual(store.list(), [])
        self.assertIsNone(store.get(relative))
        document = manager.order_document
        folder = self.root / relative
        (folder / "!.txt").write_text(document.render({"note": "Реальная заметка из папки"}, manager.STATUS_LABELS))
        self.assertEqual(manager.read_folder(relative)["note"], "Реальная заметка из папки")
        status, _, _ = self.http(self.url("/api/order", relative))
        self.assertEqual(status, 404)
        store.sync()
        self.assertEqual(manager.read_folder(relative)["note"], "Реальная заметка из папки")
        manager.save_note(relative, "Заметка к счетам")
        saved = document.load(folder, manager.STATUS_LABELS)
        self.assertFalse(document.ORDER_FIELDS.intersection(saved))
        ordinary = self.add("Клиент/2026/2026-01-00 - Заказ")
        self.assertEqual(store.discard_service_orders(), 1)
        self.assertEqual(store.discard_service_orders(), 0)
        with store.connect() as db:
            self.assertIsNone(db.execute("SELECT 1 FROM orders WHERE path=?", (relative,)).fetchone())
        self.assertEqual(store.get(ordinary["path"])["note"], ordinary["note"])
        self.assertEqual(manager.read_folder(relative)["note"], "Заметка к счетам")
        with self.assertRaises(ValueError):
            store.save(self.payload(record, path=relative))

    def test_changes_during_export_stay_pending(self):
        store = manager.order_store()
        record = self.add()
        original_write = store.atomic_write
        def writing(target, body):
            if target.name == "!.txt":
                store.save(self.payload(record, note="Во время выгрузки"))
            original_write(target, body)
        with patch.object(store, "atomic_write", side_effect=writing):
            store.sync()
        self.assertTrue(store.get(record["path"])["sync_pending"])
        store.sync()
        self.assertFalse(store.get(record["path"])["sync_pending"])
        self.assertIn("Во время выгрузки", (self.root / record["path"] / "!.txt").read_text())

    def test_copy_import_keeps_both_folders_and_corrupt_metadata_does_not_stop_scan(self):
        store = manager.order_store()
        record = store.save(self.payload(self.add()))
        store.sync()
        shutil.copytree(self.root / record["path"], self.root / "Клиент/2026-01-00 - Копия")
        self.file("Клиент/2026-02-00 - Сломанная/!.txt", b"invalid document")
        progress = {"folders": 0, "added": 0, "errors": []}
        store.discover(manager.read_status_document, progress)
        self.assertEqual(len(store.list()), 2)
        self.assertEqual(len({row["id"] for row in store.list()}), 2)
        self.assertEqual(len(progress["errors"]), 1)

    def test_export_rejects_symlink_and_preserves_external_file(self):
        store = manager.order_store()
        record = self.add()
        outside = self.base / "external.txt"
        outside.write_text("Не изменять")
        (self.root / record["path"] / "!.txt").symlink_to(outside)
        store.sync()
        self.assertTrue(store.get(record["path"])["sync_error"])
        self.assertEqual(outside.read_text(), "Не изменять")
        for relative in ("../outside", "/private/tmp", "# docs", ".hidden", "."):
            with self.subTest(relative=relative), self.assertRaises(ValueError):
                store.add(relative, {})

    def test_http_add_save_conflict_and_metadata_listing_without_scan(self):
        manager.save_status("Клиент/2026-00-00 - Заказ", "process", "Прочитать статус", "payment")
        with patch.object(manager, "schedule_order_sync"):
            status, _, body = self.http("/api/order-add", "POST", json.dumps({"path": "Клиент/2026-00-00 - Заказ"}))
            self.assertEqual(status, 201)
            record = json.loads(body)
            self.assertEqual((record["status"], record["financial_status"], record["note"]), ("process", "payment", "Прочитать статус"))
            payload = self.payload(record)
            status, _, body = self.http("/api/order-save", "POST", json.dumps(payload))
            self.assertEqual((status, json.loads(body)["amount"]), (200, 10000050))
            status, _, _ = self.http("/api/order-save", "POST", json.dumps(payload))
            self.assertEqual(status, 409)
            with patch.object(manager.os, "walk", side_effect=AssertionError("No cloud traversal")):
                status, _, body = self.http("/api/orders")
                self.assertEqual((status, len(json.loads(body)["orders"])), (200, 1))

    def test_root_switch_has_separate_database(self):
        first = manager.order_store()
        self.add()
        with patch.object(manager, "DATA_ROOT", self.base / "Другие документы"):
            self.assertEqual(manager.order_store().list(), [])
            self.assertNotEqual(manager.order_store().database, first.database)

    def test_unified_document_keeps_multiline_notes_and_future_blocks(self):
        document = manager.order_document
        for note in ("", "\n", "Текст\n", "[Финансы]\n\n[Служебное]\n> цитата\n", "  Пробелы  "):
            with self.subTest(note=note):
                record = {"status": "process", "note": note, "amount": 123456, "paid": 0,
                          "extra_blocks": {"Замеры": "Ширина: 2000 мм\nВысота: 1500 мм", "Материалы": "ПВХ\n\nСтекло"}}
                parsed = document.parse(document.render(record, manager.STATUS_LABELS), manager.STATUS_LABELS)
                self.assertEqual(parsed["note"], note)
                self.assertEqual(parsed["extra_blocks"], record["extra_blocks"])
                self.assertEqual(parsed["amount"], 123456)

    def test_existing_exports_are_combined_and_originals_archived(self):
        store = manager.order_store()
        record = store.save(self.payload(self.add(), note="Всё сохранить\n"))
        folder = self.root / record["path"]
        originals = {
            "!status.txt": "Статус: В работе\n\nЗаметка:\nВсё сохранить\n",
            "!order.txt": "Прежняя карточка для чтения",
            ".order.json": json.dumps({"schema": 1, **record}, ensure_ascii=False),
        }
        for name, body in originals.items():
            (folder / name).write_text(body)
        # Simulate a previously successful export with the old application.
        with store.connect() as db:
            db.execute("UPDATE orders SET exported_revision=revision, export_format=0")
        self.assertTrue(store.get(record["path"])["sync_pending"])
        store.sync()
        self.assertFalse(store.get(record["path"])["sync_pending"])
        self.assertEqual([file.name for file in folder.iterdir() if file.name.startswith("!")], ["!.txt"])
        self.assertFalse((folder / ".order.json").exists())
        for name, body in originals.items():
            self.assertEqual(next((folder / ".order-history").rglob(name)).read_text(), body)
        restored = manager.order_document.load(folder, manager.STATUS_LABELS)
        self.assertEqual((restored["amount"], restored["note"]), (record["amount"], record["note"]))

    def test_status_and_old_card_without_json_keep_all_finances(self):
        path = "Клиент/2026-00-00 - Заказ"
        self.file(path + "/!status.txt", "Статус: На оплате\n\nЗаметка:\nНовая заметка".encode())
        self.file(path + "/!order.txt", ("КАРТОЧКА ЗАКАЗА\n\nНазвание: Особое название\nСтатус: В работе\n\n"
            "Сумма заказа: 100 000,50 ₽\nЗатраты: 40 000,25 ₽\nОплачено: 25 000,00 ₽\n\n"
            "Заметка:\nСтарая заметка\n\nВерсия: 2\nОбновлено: вчера\n").encode())
        record = manager.order_store().import_folder(path)
        self.assertEqual((record["title"], record["status"], record["note"]), ("Особое название", "process", "Новая заметка"))
        self.assertEqual((record["amount"], record["costs"], record["paid"]), (10000050, 4000025, 2500000))
        self.assertEqual(record["financial_status"], "payment")

    def test_unknown_sections_survive_database_edits_and_recovery(self):
        store = manager.order_store()
        record = self.add()
        store.sync()
        path = self.root / record["path"] / "!.txt"
        body = path.read_text().replace("[Служебное]", "[Замеры]\nШирина: 2000 мм\n\n[Служебное]")
        path.write_text(body)
        record = store.save(self.payload(record, note="Изменённая заметка"))
        store.sync()
        self.assertIn("[Замеры]\nШирина: 2000 мм", path.read_text())
        self.assertEqual(store.get(record["path"])["extra_blocks"], {"Замеры": "Ширина: 2000 мм"})
        shutil.rmtree(manager.DATA_DIR)
        recovered = manager.order_store().import_folder(record["path"])
        self.assertEqual(recovered["extra_blocks"], {"Замеры": "Ширина: 2000 мм"})
        self.assertEqual(recovered["note"], "Изменённая заметка")

    def test_failed_unified_export_keeps_previous_files(self):
        store = manager.order_store()
        record = self.add()
        folder = self.root / record["path"]
        old = "Статус: В работе\n\nЗаметка:\nПрежняя заметка"
        (folder / "!status.txt").write_text(old)
        with patch.object(store, "atomic_write", side_effect=OSError("Нет места")):
            store.sync()
        self.assertEqual((folder / "!status.txt").read_text(), old)
        self.assertFalse((folder / "!.txt").exists())
        self.assertTrue(store.get(record["path"])["sync_pending"])

    def test_saving_unregistered_status_keeps_additional_blocks(self):
        folder = self.root / "Клиент/2026-00-00 - Заказ"
        document = manager.order_document
        (folder / "!.txt").write_text(document.render({"status": "new", "note": "Прежняя заметка",
            "amount": 50000, "extra_blocks": {"Доставка": "Адрес согласовать"}}, manager.STATUS_LABELS))
        manager.save_status("Клиент/2026-00-00 - Заказ", "done", "Новая заметка")
        record = document.load(folder, manager.STATUS_LABELS)
        self.assertEqual((record["status"], record["note"], record["amount"]), ("done", "Новая заметка", 50000))
        self.assertEqual(record["extra_blocks"], {"Доставка": "Адрес согласовать"})

    def test_previous_database_schema_is_upgraded_without_losing_orders(self):
        store = manager.order_store()
        store.database.parent.mkdir(parents=True)
        with sqlite3.connect(store.database) as db:
            db.execute("""CREATE TABLE orders (path TEXT PRIMARY KEY,id TEXT NOT NULL UNIQUE,title TEXT NOT NULL,
                status TEXT NOT NULL,note TEXT NOT NULL,amount INTEGER,costs INTEGER,paid INTEGER,
                revision INTEGER NOT NULL,exported_revision INTEGER NOT NULL DEFAULT 0,
                updated REAL NOT NULL,sync_error TEXT NOT NULL DEFAULT '')""")
            db.execute("INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (
                "Клиент/2026-00-00 - Заказ", "00000000-0000-4000-8000-000000000001", "Прежний заказ", "payment",
                "Старая заметка", 123456, 3456, 100000, 7, 7, 1700000000.0, ""))
        record = store.list()[0]
        self.assertEqual((record["title"], record["amount"], record["revision"]), ("Прежний заказ", 123456, 8))
        self.assertEqual((record["status"], record["financial_status"]), ("unspecified", "payment"))
        self.assertEqual(store.list()[0]["revision"], 8)
        with self.assertRaises(manager.OrderConflict):
            store.save(self.payload(record, revision=7))
        self.assertTrue(record["sync_pending"])
        store.sync()
        self.assertFalse(store.get(record["path"])["sync_pending"])
        self.assertEqual(manager.order_document.load(self.root / record["path"], manager.STATUS_LABELS)["amount"], 123456)
