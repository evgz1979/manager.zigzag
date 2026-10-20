import json
import unittest
from pathlib import Path
from unittest.mock import patch

from client_activity import ClientActivity, ClientActivityConflict, BLOCK
from orders import OrderStore
import test_server as fixtures

manager = fixtures.manager


class ClientActivityTests(unittest.TestCase):
    setUp = fixtures.ManagerTests.setUp
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url

    def mark(self, path, inactive=True):
        activity = manager.client_activity_store()
        record = activity.read(path)
        return activity.save({"path": path, "revision": record["revision"], "inactive": inactive})

    def test_hiding_and_restoring_client_preserves_orders_notes_and_pending_todos(self):
        path = "Клиент/2026-00-00 - Заказ"
        store = manager.order_store()
        order = store.add(path, {"status": "process", "financial_status": "partial", "amount": 14000,
                                 "note": "Сохранить заказ", "extra_blocks": {"Задачи": "- [ ] Заказная задача"}})
        notes = manager.folder_note_store()
        note = notes.read(path + "/Фото")
        note = notes.save({"path": note["path"], "revision": note["revision"], "note": "Сохранить заметку",
                           "todo_items": [{"text": "Глубокая задача", "done": False}]})
        self.assertEqual(len(manager.listed_orders()["orders"][0]["todo_groups"]), 2)
        saved = self.mark("Клиент")
        with patch.object(manager.order_document, "load", side_effect=AssertionError("List/tree cannot read cards")):
            self.assertEqual(manager.listed_orders()["orders"], [])
            self.assertEqual(manager.read_tree()["children"], [])
            self.assertEqual(manager.read_tree(query="Заказ")["children"], [])
            tree = manager.read_tree(query="Заказ", show_inactive=True)
        self.assertTrue(tree["children"][0]["inactive"])
        self.assertTrue(tree["children"][0]["children"][0]["inactive"])
        self.assertEqual(store.get(path), order)
        self.assertEqual(notes.get(note["path"]), note)
        manager.client_activity_store().save({"path": "Клиент", "revision": saved["revision"], "inactive": False})
        restored = manager.listed_orders()["orders"][0]
        self.assertEqual(restored["id"], order["id"])
        self.assertEqual(len(restored["todo_groups"]), 2)
        self.assertEqual(manager.read_tree()["children"][0]["name"], "Клиент")
        self.assertFalse((self.root / "00 - no-active").exists())

    def test_grouped_client_identity_is_full_path_and_container_has_no_marker(self):
        for path in ("01 - Группа/Клиент", "02 - Группа/Клиент", "Клиент2", "# work/# glass"):
            self.folder(path)
        activity = manager.client_activity_store()
        self.mark("01 - Группа/Клиент")
        groups = manager.read_tree()["groups"]
        self.assertEqual(groups[0]["children"], [])
        self.assertEqual(groups[1]["children"][0]["name"], "Клиент")
        self.assertEqual(len(manager.read_tree()["children"]), 2)
        self.assertEqual(manager.read_folder("01 - Группа")["directories"], [])
        self.assertTrue(manager.read_folder("01 - Группа", show_inactive=True)["directories"][0]["inactive"])
        for path in ("01 - Группа", "# work", "Клиент/2026-00-00 - Заказ", "../Клиент", "/Клиент"):
            with self.assertRaises((ValueError, FileNotFoundError)):
                activity.read(path)
        link = self.root / "Ссылка"
        link.symlink_to(self.root / "Клиент", target_is_directory=True)
        with self.assertRaises(ValueError):
            activity.read("Ссылка")

    def test_export_retries_after_restart_and_preserves_external_note_and_unknown_blocks(self):
        card = self.root / "Клиент/!.txt"
        original = {"note": "Прежняя заметка", "extra_blocks": {"Особое": "Сохранить\nстроки"}}
        card.write_text(manager.order_document.render(original, manager.STATUS_LABELS))
        saved = self.mark("Клиент")
        activity = manager.client_activity_store()
        with patch.object(manager.order_document, "atomic_write", side_effect=OSError("iCloud занят")):
            activity.sync()
        self.assertTrue(activity.get("Клиент")["sync_pending"])
        self.assertIn("iCloud занят", activity.get("Клиент")["sync_error"])
        external = manager.order_document.load(card.parent, manager.STATUS_LABELS)
        external["note"] = "Новая внешняя заметка"
        card.write_text(manager.order_document.render(external, manager.STATUS_LABELS))
        restarted = ClientActivity(manager.order_store(), manager.STATUS_LOCK)
        self.assertEqual(restarted.read("Клиент")["revision"], saved["revision"])
        restarted.sync()
        result = manager.order_document.load(card.parent, manager.STATUS_LABELS)
        self.assertEqual(result["note"], "Новая внешняя заметка")
        self.assertEqual(result["extra_blocks"], {"Особое": "Сохранить\nстроки", BLOCK: "Неактивный"})
        self.assertFalse(restarted.get("Клиент")["sync_pending"])
        self.assertTrue(list((card.parent / ".order-history").iterdir()))
        self.assertEqual(manager.read_folder("Клиент")["note"], "Новая внешняя заметка")
        manager.save_note("Клиент", "Правка из менеджера")
        self.assertEqual(manager.order_document.load(card.parent, manager.STATUS_LABELS)["extra_blocks"][BLOCK], "Неактивный")

    def test_external_marker_is_imported_without_losing_unknown_text_or_overwriting_conflict(self):
        activity = manager.client_activity_store()
        saved = self.mark("Клиент")
        card = self.root / "Клиент/!.txt"
        card.write_text(manager.order_document.render({"note": "Внешний ввод", "extra_blocks": {BLOCK: "Активный"}}, manager.STATUS_LABELS))
        external_bytes = card.read_bytes()
        activity.sync()
        self.assertTrue(activity.get("Клиент")["sync_pending"])
        self.assertTrue(activity.get("Клиент")["inactive"])
        self.assertEqual(card.read_bytes(), external_bytes)
        self.assertTrue(activity.read("Клиент")["inactive"])
        resolved = activity.accept_file({"path": "Клиент", "revision": saved["revision"]})
        self.assertFalse(resolved["inactive"])
        self.assertFalse(resolved["sync_pending"])
        # Fully exported files can be changed outside the app and rebuilt on restart.
        card.write_text(card.read_text().replace("Активный", "Неактивный"))
        activity.refresh()
        self.assertTrue(activity.get("Клиент")["inactive"])
        card.write_text(card.read_text().replace("Неактивный", "Особое состояние"))
        unknown_bytes = card.read_bytes()
        record = activity.read("Клиент")
        self.assertTrue(record["inactive"])
        self.assertFalse(record["editable"])
        with self.assertRaises(ClientActivityConflict):
            activity.save({"path": "Клиент", "revision": record["revision"], "inactive": False})
        self.assertEqual(card.read_bytes(), unknown_bytes)

    def test_stale_tabs_are_rejected_and_failed_refresh_retains_hidden_state(self):
        activity = manager.client_activity_store()
        old = activity.read("Клиент")
        activity.save({"path": "Клиент", "revision": old["revision"], "inactive": True})
        with self.assertRaises(ClientActivityConflict):
            activity.save({"path": "Клиент", "revision": old["revision"], "inactive": False})
        with patch.object(manager.order_document, "load", side_effect=OSError("offline")):
            activity.refresh()
        self.assertTrue(activity.get("Клиент")["inactive"])
        self.assertEqual(manager.listed_orders()["orders"], [])

    def test_exported_client_marker_rebuilds_index_from_files(self):
        self.mark("Клиент")
        manager.client_activity_store().sync()
        recovered_orders = OrderStore(self.root, self.base / "recovered", manager.STATUS_LABELS)
        recovered = ClientActivity(recovered_orders)
        recovered.refresh()
        self.assertEqual(recovered.inactive_paths(), {"Клиент"})
        self.assertFalse(recovered.get("Клиент")["sync_pending"])

    def test_http_toggle_filters_main_list_but_show_inactive_only_affects_tree(self):
        path = "Клиент/2026-00-00 - Заказ"
        manager.order_store().add(path, {"status": "new", "note": "", "extra_blocks": {"Задачи": "- [ ] Позвонить"}})
        status, _, body = self.http(self.url("/api/folder", "Клиент"))
        self.assertEqual(status, 200)
        revision = json.loads(body)["clientActivity"]["revision"]
        with patch.object(manager, "schedule_order_sync"):
            status, _, body = self.http("/api/client-activity", "POST", json.dumps({"path": "Клиент", "revision": revision, "inactive": True}))
        self.assertEqual(status, 200)
        status, _, body = self.http("/api/orders?show_inactive=1")
        self.assertEqual(json.loads(body)["orders"], [])
        status, _, body = self.http("/api/tree?show_inactive=1")
        self.assertTrue(json.loads(body)["children"][0]["inactive"])
        status, _, body = self.http(self.url("/api/order", path))
        self.assertEqual(status, 200)  # Direct navigation remains available.


if __name__ == "__main__":
    unittest.main()
