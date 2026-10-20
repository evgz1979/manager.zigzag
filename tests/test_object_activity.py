import json
import subprocess
import sys
import unittest
from unittest.mock import patch

import folder_rename
from client_activity import ClientActivityConflict
from object_activity import ObjectActivity, BLOCK
from orders import OrderStore
from order_todos import OrderTodos
import test_server as fixtures

manager = fixtures.manager


class ObjectActivityTests(unittest.TestCase):
    setUp = fixtures.ManagerTests.setUp
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url

    def mark(self, path, inactive=True):
        activity = manager.object_activity_store()
        record = activity.read(path)
        return activity.save({"path": path, "revision": record["revision"], "inactive": inactive})

    def add_order(self, obj="Клиент/Объект"):
        path = obj + "/2026-10-20 - Заказ"
        self.folder(path + "/01 - Замеры/Глубже/# cdr")
        return manager.order_store().add(path, {"status": "process", "financial_status": "partial", "amount": 14000,
                                               "note": "Сохранить заказ", "extra_blocks": {"Задачи": "- [ ] Своя задача"}})

    def test_object_hides_only_its_subtree_from_tree_search_main_totals_and_todos(self):
        order = self.add_order()
        sibling = self.add_order("Клиент/Объект 2")
        notes = manager.folder_note_store()
        path = order["path"] + "/01 - Замеры/Глубже/# cdr"
        record = notes.read(path)
        pending = notes.save({"path": path, "revision": record["revision"], "note": "Не потерять",
                              "todo_items": [{"text": "Глубокая задача", "done": False}]})
        self.mark("Клиент/Объект")
        with patch.object(manager.order_document, "load", side_effect=AssertionError("No card reads in list/tree")):
            result = manager.listed_orders()["orders"]
            self.assertEqual([row["path"] for row in result], [sibling["path"]])
            self.assertEqual(sum(row["amount"] for row in result), sibling["amount"])
            self.assertEqual([node["name"] for node in manager.read_tree("Клиент")["children"]], ["2026", "2026-00-00 - Заказ", "Объект 2"])
            self.assertEqual(manager.read_tree(query="Глубже")["children"][0]["name"], "Клиент")  # Only sibling remains.
            shown = manager.read_tree("Клиент/Объект", show_inactive=True)["children"]
            self.assertTrue(shown[0]["inactive"])
            hidden_search = manager.read_tree(query="Клиент/Объект/2026-10-20")
            self.assertEqual(hidden_search["children"], [])
        self.assertEqual(manager.order_store().get(order["path"]), order)
        self.assertEqual(notes.get(path), pending)
        self.assertEqual(len(OrderTodos(manager.order_store()).in_order(order["path"])["todo_groups"]), 1)
        self.assertEqual([item["name"] for item in manager.read_folder("Клиент")["directories"]], ["2026", "2026-00-00 - Заказ", "Объект 2"])
        self.assertTrue(manager.read_folder("Клиент/Объект")["directories"])  # Direct open works.
        self.mark("Клиент/Объект", False)
        self.assertEqual(len(manager.listed_orders()["orders"]), 2)

    def test_client_and_object_flags_are_independent_and_group_paths_do_not_collide(self):
        first = self.add_order("01 - Группа/Покупатель/Объект")
        second = self.add_order("02 - Группа/Покупатель/Объект")
        self.mark("01 - Группа/Покупатель/Объект")
        self.assertEqual([row["id"] for row in manager.listed_orders()["orders"]], [second["id"]])
        clients = manager.client_activity_store()
        record = clients.read("01 - Группа/Покупатель")
        record = clients.save({"path": record["path"], "revision": record["revision"], "inactive": True})
        self.mark("01 - Группа/Покупатель/Объект", False)
        self.assertEqual([row["id"] for row in manager.listed_orders()["orders"]], [second["id"]])
        clients.save({"path": record["path"], "revision": record["revision"], "inactive": False})
        self.assertEqual({row["id"] for row in manager.listed_orders()["orders"]}, {first["id"], second["id"]})

    def test_failed_export_restarts_and_preserves_other_blocks_note_and_history(self):
        self.add_order()
        folder = self.root / "Клиент/Объект"
        original = {"note": "Прежняя заметка", "extra_blocks": {"Особое": "Строки\nсохраняются", "Активность клиента": "Посторонний блок"}}
        card = folder / "!.txt"
        card.write_text(manager.order_document.render(original, manager.STATUS_LABELS))
        saved = self.mark("Клиент/Объект")
        with patch.object(manager.order_document, "atomic_write", side_effect=OSError("iCloud занят")):
            manager.object_activity_store().sync()
        self.assertTrue(manager.object_activity_store().get(saved["path"])["sync_pending"])
        external = manager.order_document.load(folder, manager.STATUS_LABELS)
        external["note"] = "Внешняя заметка"
        card.write_text(manager.order_document.render(external, manager.STATUS_LABELS))
        restarted = ObjectActivity(manager.order_store(), manager.STATUS_LOCK)
        self.assertEqual(restarted.read(saved["path"])["revision"], saved["revision"])
        restarted.sync()
        result = manager.order_document.load(folder, manager.STATUS_LABELS)
        self.assertEqual(result["note"], external["note"])
        self.assertEqual(result["extra_blocks"], {**original["extra_blocks"], BLOCK: "Неактивный"})
        self.assertFalse(restarted.get(saved["path"])["sync_pending"])
        self.assertTrue(list((folder / ".order-history").iterdir()))
        manager.save_note(saved["path"], "Заметка менеджера")
        self.assertEqual(manager.order_document.load(folder, manager.STATUS_LABELS)["extra_blocks"][BLOCK], "Неактивный")

    def test_conflicts_unknown_text_stale_version_and_external_changes(self):
        self.add_order()
        activity = manager.object_activity_store()
        saved = self.mark("Клиент/Объект")
        with self.assertRaises(ClientActivityConflict):
            activity.save({"path": saved["path"], "revision": saved["revision"] - 1, "inactive": False})
        card = self.root / saved["path"] / "!.txt"
        card.write_text(manager.order_document.render({"note": "Не перезаписать", "extra_blocks": {BLOCK: "Активный"}}, manager.STATUS_LABELS))
        before = card.read_bytes()
        activity.sync()
        self.assertEqual(card.read_bytes(), before)
        self.assertTrue(activity.read(saved["path"])["inactive"])
        resolved = activity.accept_file({"path": saved["path"], "revision": saved["revision"]})
        self.assertFalse(resolved["inactive"])
        card.write_text(card.read_text().replace("Активный", "Неактивный"))
        activity.refresh()
        self.assertTrue(activity.get(saved["path"])["inactive"])
        card.write_text(card.read_text().replace("Неактивный", "Неизвестный текст"))
        unknown = activity.read(saved["path"])
        self.assertTrue(unknown["inactive"])
        self.assertFalse(unknown["editable"])
        with self.assertRaises(ClientActivityConflict):
            activity.save({"path": saved["path"], "revision": unknown["revision"], "inactive": False})
        with patch.object(manager.order_document, "load", side_effect=OSError("offline")):
            activity.refresh()
        self.assertEqual(manager.listed_orders()["orders"], [])

    def test_background_rebuild_reads_object_cards_and_stops_before_orders_and_services(self):
        order = self.add_order()
        self.mark("Клиент/Объект")
        manager.object_activity_store().sync()
        self.folder("Клиент/.hidden/Объект")
        self.folder("# docs/Внутри/Объект")
        (self.root / "Клиент/Ссылка").symlink_to(self.root / "Клиент/Объект")
        rebuilt = ObjectActivity(OrderStore(self.root, self.base / "rebuilt", manager.STATUS_LABELS, database_only=False))
        load = manager.order_document.load
        seen = []
        def only_objects(folder, *args, **kwargs):
            seen.append(folder.relative_to(self.root).as_posix())
            self.assertEqual(folder.relative_to(self.root).as_posix(), "Клиент/Объект")
            return load(folder, *args, **kwargs)
        with patch.object(manager.order_document, "load", side_effect=only_objects):
            rebuilt.refresh()
        self.assertEqual(seen, ["Клиент/Объект"])
        self.assertEqual(rebuilt.inactive_paths(), {"Клиент/Объект"})
        self.assertFalse(rebuilt.get("Клиент/Объект")["sync_pending"])
        self.assertEqual(manager.order_store().get(order["path"]), order)

    def test_api_scope_and_offline_list_and_direct_order_access(self):
        order = self.add_order()
        status, _, body = self.http(self.url("/api/folder", "Клиент/Объект"))
        self.assertEqual(status, 200)
        revision = json.loads(body)["objectActivity"]["revision"]
        with patch.object(manager, "schedule_order_sync"):
            status, _, _ = self.http("/api/object-activity", "POST", json.dumps({"path": "Клиент/Объект", "revision": revision, "inactive": True}))
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(self.http("/api/orders?show_inactive=1")[2])["orders"], [])
        self.assertTrue(json.loads(self.http(self.url("/api/tree", "Клиент", show_inactive="1"))[2])["children"][-1]["inactive"])
        self.assertEqual(self.http(self.url("/api/order", order["path"]))[0], 200)
        self.root.rename(self.base / "offline")
        with patch.object(manager.order_document, "load", side_effect=AssertionError("No iCloud on main")):
            self.assertEqual(json.loads(self.http("/api/orders")[2])["orders"], [])
            self.assertTrue(json.loads(self.http(self.url("/api/object-activity", "Клиент/Объект"))[2])["inactive"])

    def test_only_objects_accept_markers(self):
        order = self.add_order()
        activity = manager.object_activity_store()
        for path in ("", "Клиент", "Клиент/2026", order["path"], order["path"] + "/01 - Замеры", "# docs/Внутри", "../Клиент/Объект", "Клиент//Объект"):
            with self.assertRaises((ValueError, FileNotFoundError), msg=path):
                activity.read(path)
        (self.root / "Клиент/Ссылка").symlink_to(self.root / "Клиент/Объект")
        with self.assertRaises(ValueError):
            activity.read("Клиент/Ссылка")

    def test_rename_and_standalone_undo_preserve_pending_flag_and_later_changes(self):
        order = self.add_order()
        source = "Клиент/Объект"
        self.mark(source)
        result = folder_rename.rename(manager.order_store(), {**folder_rename.preview(manager.order_store(), source), "name": "Новое имя"})
        activity = manager.object_activity_store()
        moved = activity.get(result["path"])
        self.assertTrue(moved["inactive"])
        self.assertTrue(moved["sync_pending"])
        self.assertEqual(manager.listed_orders()["orders"], [])
        activity.save({"path": moved["path"], "revision": moved["revision"], "inactive": False})
        session = self.root / result["journal"]
        subprocess.run([sys.executable, str(session / ".restore.py"), str(session), "--apply"], check=True, capture_output=True)
        restored = activity.get(source)
        self.assertFalse(restored["inactive"])
        self.assertTrue(restored["sync_pending"])
        self.assertIsNone(activity.get(result["path"]))
        self.assertEqual(manager.order_store().get(order["path"])["id"], order["id"])
        activity.sync()
        self.assertFalse(activity.get(source)["sync_pending"])
        self.assertEqual(manager.order_document.load(self.root / source, manager.STATUS_LABELS)["extra_blocks"][BLOCK], "Активный")
