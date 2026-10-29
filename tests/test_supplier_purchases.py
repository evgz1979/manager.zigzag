import json
import unittest
from unittest.mock import patch

import order_document as document
import work_orders
from orders import OrderConflict, OrderStore
from supplier_purchases import SupplierPurchases, supplier_name
import test_server as fixtures

manager = fixtures.manager


class SupplierPurchaseTests(unittest.TestCase):
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url
    path = "Клиент/Объект/2026-10-26 - Заказ"
    section = "# work/# glass"

    def setUp(self):
        fixtures.ManagerTests.setUp(self)
        mode = patch.object(manager, "DATABASE_ONLY", True)
        mode.start()
        self.patches.append(mode)
        self.folder(self.path)
        self.folder(self.section)
        self.store = manager.order_store()
        self.view = SupplierPurchases(self.store)
        for name in document.PURCHASE_SUPPLIERS:
            self.folder("# work/# " + name)
        manager.read_folder("# work")
        for path, row in work_orders.read_supplier_favorites(self.store, "# work").items():
            if not row["is_favorite"]:
                work_orders.save_supplier_favorite(self.store, {**row, "is_favorite": True})
        self.items = [{"text": "Заказать стекло", "done": False, "suppliers": ["glass", "tbm"]},
                      {"text": "Профиль", "done": True, "suppliers": ["antares"]},
                      {"text": "Без поставщика", "done": False, "suppliers": []}]
        blocks = document.write_purchases({"Задачи": "- [ ] Позвонить", "Особое": "Не менять"}, self.items)
        self.order = self.store.add(self.path, {"title": "Заказ клиента", "status": "done", "financial_status": "partial",
            "note": "Заметка", "amount": 10000, "costs": 2000, "paid": 5000, "extra_blocks": blocks})

    def payload(self, order=None, **changes):
        order = order or self.order
        return {"supplier_path": self.section, "path": self.path, "id": order["id"], "revision": order["revision"],
                "index": 0, "text": self.items[0]["text"], "done": True, **changes}

    def test_live_view_uses_selected_suppliers_all_statuses_and_only_ordinary_registered_orders(self):
        for path in ("# work/# glass/Производственный", "# moneys/# bills/Финансовая запись", "Клиент/Объект 2/2026-10-25 - Снят"):
            self.folder(path)
            row = self.store.add(path, {"status": "cancelled", "extra_blocks": self.order["extra_blocks"]})
            if not path.startswith("#"):
                self.store.remove({"path": path, "revision": row["revision"], "confirmed": True})
        before = self.store.list(include_unregistered=True)
        self.root.rename(self.base / "offline")
        with patch.object(OrderStore, "target", side_effect=AssertionError("No folders")), patch("icloud_access.read_bytes", side_effect=AssertionError("No documents")):
            for section in (self.section, "#work/#GLASS", "# work/glass", "#glass"):
                data = self.view.read(section)
                self.assertEqual([row["id"] for row in data["orders"]], [self.order["id"]])
                self.assertEqual(data["orders"][0]["items"], [{"index": 0, **self.items[0]}])
            completed = self.view.read("#work/#antares")["orders"][0]["items"][0]
            self.assertTrue(completed["done"])
            self.assertEqual(self.view.read("#work/#remex")["orders"], [])
        self.assertEqual(self.store.list(include_unregistered=True), before)

    def test_checkbox_changes_original_once_and_preserves_raw_block_sort_date_and_other_fields(self):
        raw = "- [ ] Заказать стекло\r\n  Поставщики: glass, tbm\r\n\r\n- [X] Профиль\r\n  Поставщики: antares\r\n"
        with self.store.connect() as db:
            db.execute("UPDATE orders SET extra_blocks=? WHERE id=?", (json.dumps({**self.order["extra_blocks"], document.PURCHASE_BLOCK: raw}), self.order["id"]))
        before = self.store.get(self.path)
        with self.store.connect() as db:
            count = db.execute("SELECT count(*) FROM metadata_history WHERE entity='orders' AND identity=?", (before["id"],)).fetchone()[0]
        self.root.rename(self.base / "offline")
        with patch.object(OrderStore, "target", side_effect=AssertionError("No folders")), patch("icloud_access.read_bytes", side_effect=AssertionError("No documents")):
            saved = self.view.save(self.payload(before, note="Не заменять", amount=99999))
        self.assertEqual(saved["extra_blocks"][document.PURCHASE_BLOCK], raw.replace("- [ ]", "- [x]", 1))
        self.assertEqual(saved["revision"], before["revision"] + 1)
        for key in before.keys() - {"revision", "extra_blocks", "purchase_items"}:
            self.assertEqual(saved[key], before[key], key)
        self.assertEqual(self.view.read("#work/#tbm")["orders"][0]["items"][0]["done"], True)
        self.assertTrue(self.store.get(self.path)["purchase_items"][0]["done"])
        with self.store.connect() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM metadata_history WHERE entity='orders' AND identity=?", (before["id"],)).fetchone()[0], count + 1)
        with self.assertRaises(OrderConflict):
            self.view.save(self.payload(before))
        restored = self.view.save(self.payload(saved, supplier_path="#work/#tbm", done=False))
        self.assertFalse(restored["purchase_items"][0]["done"])
        self.assertFalse((self.base / "offline" / self.path / "!.txt").exists())

    def test_reorder_removal_and_wrong_supplier_never_update_a_different_purchase(self):
        changed = self.store.save({**self.order, "amount": "100", "costs": "20", "paid": "50", "purchase_items": list(reversed(self.items))})
        with self.assertRaises(OrderConflict):
            self.view.save(self.payload())
        for values in ({"text": "Подмена"}, {"supplier_path": "#work/#antares"}, {"index": 99}, {"index": True}, {"done": "true"}, {"revision": None}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                self.view.save(self.payload(changed, **{"index": 2, **values}))
        self.assertEqual(self.store.get(self.path), changed)
        removed = self.store.remove({"path": self.path, "revision": changed["revision"], "confirmed": True})
        with self.assertRaises(OrderConflict):
            self.view.save(self.payload(removed, index=2))
        self.assertEqual(self.view.read(self.section)["orders"], [])

    def test_duplicate_text_rows_keep_their_own_checkboxes(self):
        items = [self.items[0], {**self.items[0]}]
        current = self.store.save({**self.order, "amount": "100", "costs": "20", "paid": "50", "purchase_items": items})
        saved = self.view.save(self.payload(current, index=1))
        self.assertEqual([item["done"] for item in saved["purchase_items"]], [False, True])
        self.assertEqual([item["index"] for item in self.view.read(self.section)["orders"][0]["items"]], [0, 1])

    def test_inactive_branches_unknown_formats_and_non_supplier_paths_preserve_data(self):
        for scope in ("Клиент", "Клиент/Объект"):
            self.assertEqual(self.view.read(self.section, inactive={scope})["orders"], [])
            with self.assertRaises(ValueError):
                self.view.save(self.payload(), inactive={scope})
        for path in ("#work", "#work/#glass/Заказ", "Клиент/#glass", "#moneys/#glass", "#work/#", "#work/../glass", "/#work/#glass", "#work/2026-10-29 - Заказ", None):
            with self.subTest(path=path):
                self.assertEqual(supplier_name(path), "")
                with self.assertRaises(ValueError):
                    self.view.read(path)
        for raw in ("Прежний неизвестный текст", "- [ ] Закупка\n  Поставщики: #future-vendor"):
            with self.store.connect() as db:
                db.execute("UPDATE orders SET extra_blocks=? WHERE id=?", (json.dumps({document.PURCHASE_BLOCK: raw}), self.order["id"]))
            before = self.store.get(self.path)
            self.assertEqual(self.view.read(self.section)["orders"], [])
            with self.assertRaises(ValueError):
                self.view.save(self.payload(before))
            self.assertEqual(self.store.get(self.path), before)

    def test_http_section_view_and_checkbox_return_shared_source_and_conflicts(self):
        opened = manager.read_folder(self.section)
        self.assertEqual(opened["purchaseSupplier"], "glass")
        self.assertEqual(manager.read_folder(self.path)["purchaseSupplier"], "")
        status, _, body = self.http(self.url("/api/supplier-purchases", self.section))
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["orders"][0]["id"], self.order["id"])
        with patch.object(manager, "schedule_order_sync"):
            status, _, body = self.http("/api/supplier-purchase-done", "POST", json.dumps(self.payload()))
        self.assertEqual(status, 200, body)
        self.assertTrue(json.loads(body)["purchase_items"][0]["done"])
        self.assertEqual(self.http("/api/supplier-purchase-done", "POST", json.dumps(self.payload()))[0], 409)
        self.assertTrue(json.loads(self.http(self.url("/api/order", self.path))[2])["purchase_items"][0]["done"])

    def test_etc_selects_only_unassigned_without_duplicating_any_supplier(self):
        items = [
            {"text": "Без поставщика", "done": False, "suppliers": []},
            {"text": "Фурнитура", "done": False, "suppliers": ["tbm"]},
            {"text": "пленка 8300 на 2 кроншт с 2х сторон = 4 м2", "done": False, "suppliers": ["remex"]},
            {"text": "Стекло и фурнитура", "done": False, "suppliers": ["glass", "tbm"]},
            {"text": "Профиль", "done": False, "suppliers": ["antares", "newtek"]},
        ]
        current = self.store.save({**self.order, "amount": "100", "costs": "20", "paid": "50", "purchase_items": items})
        self.root.rename(self.base / "offline")
        with patch.object(OrderStore, "target", side_effect=AssertionError("No folders")), patch("icloud_access.read_bytes", side_effect=AssertionError("No documents")):
            for section in ("# work/# etc", "#work/#ETC", "# work/etc"):
                data = self.view.read(section)
                self.assertEqual(data["supplier"], "etc")
                self.assertEqual(data["orders"][0]["items"], [{"index": 0, **items[0]}])
            self.assertFalse(document.purchase_matches_supplier({"suppliers": ["himlex"]}, "etc"))
            self.assertEqual(self.view.read("#work/#remex")["orders"][0]["items"], [{"index": 2, **items[2]}])
            self.assertEqual(self.view.catalog()["counts"], {"etc": 1, "tbm": 2, "remex": 1, "glass": 1, "antares": 1, "newtek": 1})
            self.assertEqual(self.store.get(self.path), current)

    def test_dynamic_starred_catalog_new_assignments_and_retained_suppliers(self):
        for name in ("himlex", "Новый завод", "Без звезды"):
            self.folder("# work/# " + name)
        manager.read_folder("# work")
        favorites = work_orders.read_supplier_favorites(self.store, "# work")
        for name in ("himlex", "Новый завод"):
            work_orders.save_supplier_favorite(self.store, {**favorites["# work/# " + name], "is_favorite": True})
        names = [row["name"] for row in self.view.catalog()["suppliers"]]
        self.assertIn("himlex", names)
        self.assertIn("новый завод", names)
        self.assertNotIn("без звезды", names)
        self.assertNotIn("etc", names)
        items = [{"text": "Два поставщика", "done": False, "suppliers": ["himlex", "новый завод"]},
                 {"text": "Дубль", "done": False, "suppliers": ["himlex"]},
                 {"text": "Дубль", "done": False, "suppliers": ["himlex"]},
                 {"text": "Готово", "done": True, "suppliers": ["himlex"]}]
        saved = self.store.save({**self.order, "amount": "100", "costs": "20", "paid": "50", "purchase_items": items})
        self.assertEqual(saved["purchase_items"], items)
        self.assertEqual(self.view.catalog()["counts"], {"etc": 0, "himlex": 3, "новый завод": 1})
        with self.store.connect() as db:
            self.assertEqual(db.execute("SELECT value FROM metadata_settings WHERE key='purchase_suppliers'").fetchone()[0], "1")
        favorite = work_orders.read_supplier_favorites(self.store, "# work")["# work/# himlex"]
        work_orders.save_supplier_favorite(self.store, {**favorite, "is_favorite": False})
        with self.assertRaises(ValueError):
            self.store.save({**saved, "amount": "100", "costs": "20", "paid": "50", "purchase_items": items + [items[1]]})
        self.root.rename(self.base / "offline")
        with patch.object(OrderStore, "target", side_effect=AssertionError("No folders")), patch("icloud_access.read_bytes", side_effect=AssertionError("No documents")):
            self.assertNotIn("himlex", [row["name"] for row in self.view.catalog()["suppliers"]])
            self.assertEqual(len(self.view.read("#work/#himlex")["orders"][0]["items"]), 4)
            self.assertEqual(self.view.read("#work/#etc")["orders"], [])
            retained = self.store.save({**saved, "amount": "100", "costs": "20", "paid": "50", "purchase_items": items})
            self.assertEqual(retained["purchase_items"], items)
            blocked = [{"text": "Не назначать", "done": False, "suppliers": ["без звезды"]}]
            with self.assertRaises(ValueError):
                self.store.save({**retained, "amount": "100", "costs": "20", "paid": "50", "purchase_items": blocked})
            self.assertEqual(self.store.get(self.path), retained)
            self.assertEqual(self.view.catalog(inactive={"Клиент"})["counts"], {"etc": 0})

    def test_removed_section_and_unknown_catalog_are_not_offered_or_rewritten(self):
        with self.store.connect() as db:
            before = dict(db.execute("SELECT * FROM metadata_records WHERE kind='purchase_supplier_catalog'").fetchone())
        manager.read_folder("# work")
        with self.store.connect() as db:
            self.assertEqual(dict(db.execute("SELECT * FROM metadata_records WHERE kind='purchase_supplier_catalog'").fetchone()), before)
        (self.root / "# work/# remex").rmdir()
        manager.read_folder("# work")
        self.assertNotIn("remex", [row["name"] for row in self.view.catalog()["suppliers"]])
        with self.store.connect() as db:
            db.execute("UPDATE metadata_records SET data=? WHERE kind='purchase_supplier_catalog'", (json.dumps({"version": 2, "paths": []}),))
        self.assertEqual(self.view.catalog()["suppliers"], [])
        with self.assertRaises(ValueError):
            manager.read_folder("# work")
        with self.store.connect() as db:
            self.assertEqual(json.loads(db.execute("SELECT data FROM metadata_records WHERE kind='purchase_supplier_catalog'").fetchone()[0])["version"], 2)

    def test_http_catalog_and_supplier_buttons_share_outstanding_counts(self):
        status, _, body = self.http("/api/purchase-suppliers")
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertEqual(data["counts"], {"etc": 1, "glass": 1, "tbm": 1})
        nodes = manager.read_folder("# work")["directories"]
        for node in nodes:
            name = node["name"].removeprefix("#").strip().casefold()
            self.assertEqual(node["supplierPurchaseCount"], data["counts"].get(name, 0))

    def test_etc_checkbox_uses_same_source_and_rejects_a_new_primary_assignment(self):
        before = self.order
        saved = self.view.save(self.payload(before, supplier_path="#work/#etc", index=2, text=self.items[2]["text"]))
        self.assertTrue(saved["purchase_items"][2]["done"])
        self.assertEqual(saved["purchase_items"][2]["suppliers"], [])
        self.assertEqual(saved["updated"], before["updated"])
        self.assertEqual(saved["todo_items"], before["todo_items"])
        for key in ("amount", "costs", "paid", "status", "financial_status"):
            self.assertEqual(saved[key], before[key])
        with self.assertRaises(ValueError):
            self.view.save(self.payload(saved, supplier_path="#work/#etc"))  # glass + tbm stays outside etc.
        items = saved["purchase_items"]
        items[2]["suppliers"] = ["glass"]
        assigned = self.store.save({**saved, "amount": "100", "costs": "20", "paid": "50", "purchase_items": items})
        with self.assertRaises(OrderConflict):
            self.view.save(self.payload(saved, supplier_path="#work/#etc", index=2, text=self.items[2]["text"], done=False))
        with self.assertRaises(ValueError):
            self.view.save(self.payload(assigned, supplier_path="#work/#etc", index=2, text=self.items[2]["text"], done=False))
        self.assertEqual(self.view.read("#work/#etc")["orders"], [])
        self.assertTrue(self.view.read(self.section)["orders"][0]["items"][-1]["done"])
        self.assertEqual(self.store.get(self.path), assigned)
