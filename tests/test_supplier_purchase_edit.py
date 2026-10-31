import json
import unittest
from unittest.mock import patch

import order_document as document
import work_orders
from orders import OrderConflict, OrderStore
import test_supplier_purchases as fixtures

manager = fixtures.manager


class SupplierPurchaseEditTests(unittest.TestCase):
    setUp = fixtures.SupplierPurchaseTests.setUp
    tearDown = fixtures.SupplierPurchaseTests.tearDown
    folder = fixtures.SupplierPurchaseTests.folder
    file = fixtures.SupplierPurchaseTests.file
    http = fixtures.SupplierPurchaseTests.http
    url = fixtures.SupplierPurchaseTests.url
    payload = fixtures.SupplierPurchaseTests.payload
    path = fixtures.SupplierPurchaseTests.path
    section = fixtures.SupplierPurchaseTests.section

    def test_edit_changes_only_target_text_and_keeps_raw_format_history_and_source_fields(self):
        raw = "- [X] Дубль\r\n  Поставщики: glass, tbm\r\n\r\n- [ ] Дубль\r\n  Поставщики: glass, tbm\r\n"
        with self.store.connect() as db:
            db.execute("UPDATE orders SET extra_blocks=? WHERE id=?",
                       (json.dumps({**self.order["extra_blocks"], document.PURCHASE_BLOCK: raw}), self.order["id"]))
            count = db.execute("SELECT count(*) FROM metadata_history WHERE entity='orders' AND identity=?",
                               (self.order["id"],)).fetchone()[0]
        before = self.store.get(self.path)
        self.root.rename(self.base / "offline")
        with patch.object(OrderStore, "target", side_effect=AssertionError("No folders")), \
                patch("icloud_access.read_bytes", side_effect=AssertionError("No documents")):
            saved = self.view.edit(self.payload(before, index=1, text="Дубль", new_text="  Новое стекло 🪟  ",
                                                note="Не заменять", suppliers=[], done=True, amount=99999))
        expected = raw.replace("- [ ] Дубль", "- [ ] Новое стекло 🪟", 1)
        self.assertEqual(saved["extra_blocks"][document.PURCHASE_BLOCK], expected)
        self.assertEqual(saved["revision"], before["revision"] + 1)
        self.assertEqual(saved["purchase_items"], [
            {"text": "Дубль", "done": True, "suppliers": ["glass", "tbm"]},
            {"text": "Новое стекло 🪟", "done": False, "suppliers": ["glass", "tbm"]}])
        for key in before.keys() - {"revision", "extra_blocks", "purchase_items"}:
            self.assertEqual(saved[key], before[key], key)
        self.assertEqual(self.view.read("#work/#tbm")["orders"][0]["items"][1]["text"], "Новое стекло 🪟")
        with self.store.connect() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM metadata_history WHERE entity='orders' AND identity=?",
                                       (before["id"],)).fetchone()[0], count + 1)
        self.assertFalse((self.base / "offline" / self.path / "!.txt").exists())

    def test_invalid_text_source_and_identity_do_not_change_anything(self):
        for changes in (
            *({"new_text": value} for value in (None, True, [], "  ", "A\nB", "A\rB", "A\x00B", "A\u2028B", "x" * 1001)),
            {"index": True}, {"index": -1}, {"index": 200}, {"text": "Другой текст"},
            {"supplier_path": "#work/#antares"}, {"supplier_path": "#work"},
            {"revision": True}, {"id": "other"},
        ):
            payload = {**self.payload(new_text="Правка"), **changes}
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.view.edit(payload)
            self.assertEqual(self.store.get(self.path), self.order)
        with self.assertRaises(ValueError):
            self.view.edit(self.payload(new_text="Правка"), inactive={"Клиент"})
        self.assertEqual(self.store.get(self.path), self.order)

    def test_reordered_removed_and_unknown_purchases_are_never_replaced(self):
        changed = self.store.save({**self.order, "amount": "100", "costs": "20", "paid": "50",
                                   "purchase_items": list(reversed(self.items))})
        with self.assertRaises(OrderConflict):
            self.view.edit(self.payload(new_text="Правка"))
        self.assertEqual(self.store.get(self.path), changed)
        removed = self.store.remove({"path": self.path, "revision": changed["revision"], "confirmed": True})
        with self.assertRaises(OrderConflict):
            self.view.edit(self.payload(removed, index=2, new_text="Правка"))
        for raw in ("Неизвестный прежний текст", "- [ ] Закупка\n  Поставщики: #future"):
            with self.store.connect() as db:
                db.execute("UPDATE orders SET registered=1,extra_blocks=? WHERE id=?",
                           (json.dumps({document.PURCHASE_BLOCK: raw}), self.order["id"]))
            current = self.store.get(self.path)
            with self.assertRaises(ValueError):
                self.view.edit(self.payload(current, new_text="Правка"))
            self.assertEqual(self.store.get(self.path), current)

    def test_etc_completed_and_supplier_without_star_keep_assignments_and_completion(self):
        current = self.view.edit(self.payload(supplier_path="#work/#etc", index=2, text=self.items[2]["text"], new_text="Уточнить закупку"))
        self.assertEqual(current["purchase_items"][2], {**self.items[2], "text": "Уточнить закупку"})
        current = self.view.edit(self.payload(current, supplier_path="#glass", new_text="Стекло по замеру"))
        self.assertEqual(current["purchase_items"][0]["suppliers"], ["glass", "tbm"])
        favorite = work_orders.read_supplier_favorites(self.store, "# work")[self.section]
        work_orders.save_supplier_favorite(self.store, {**favorite, "is_favorite": False})
        current = self.view.edit(self.payload(current, text="Стекло по замеру", new_text="Стекло по чертежу"))
        current = self.view.edit(self.payload(current, supplier_path="#work/#antares", index=1,
                                              text=self.items[1]["text"], new_text="Профиль для створки"))
        self.assertEqual(current["purchase_items"][1], {**self.items[1], "text": "Профиль для створки"})

    def test_http_edit_validates_page_and_returns_shared_text_and_stale_conflict(self):
        body = json.dumps(self.payload(new_text="Стекло 8 мм"))
        route = "/api/supplier-purchase-text"
        self.assertEqual(self.http(route, "POST", body)[0], 403)
        self.assertEqual(self.http(route, "POST", body,
                                  {"Content-Type": "application/json", "Origin": "https://foreign.invalid"})[0], 403)
        self.assertEqual(self.store.get(self.path), self.order)
        with patch.object(manager, "schedule_order_sync"):
            status, _, data = self.http(route, "POST", body, {"Content-Type": "application/json"})
        self.assertEqual(status, 200, data)
        self.assertEqual(json.loads(data)["purchase_items"][0], {**self.items[0], "text": "Стекло 8 мм"})
        self.assertEqual(self.http(route, "POST", body, {"Content-Type": "application/json"})[0], 409)
        data = json.loads(self.http(self.url("/api/supplier-purchases", "#work/#tbm"))[2])
        self.assertEqual(data["orders"][0]["items"][0]["text"], "Стекло 8 мм")
