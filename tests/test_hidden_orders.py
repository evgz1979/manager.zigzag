import json
import unittest
from unittest.mock import patch

import hidden_orders
import object_orders
from local_metadata import MetadataStore
from orders import OrderStore
import test_server as fixtures

manager = fixtures.manager


class HiddenOrderTests(unittest.TestCase):
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http

    def setUp(self):
        fixtures.ManagerTests.setUp(self)
        mode = patch.object(manager, "DATABASE_ONLY", True)
        mode.start()
        self.patches.append(mode)
        self.store = manager.order_store()

    def add(self, path, status="new", **extra):
        self.folder(path)
        return self.store.add(path, {"status": status, "note": "Первая строка\nОстальное", **extra})

    def test_all_hidden_reasons_and_no_active_orders(self):
        active = self.add("Клиент/Объект/2026-01-01 - Активный")
        for status in ("done_but", "waiting", "offer_later", "deferred", "unspecified"):
            self.add(f"Клиент/Объект/2026-01-01 - {status}", status)
        done = self.add("Клиент/Объект/2026-01-01 - Готово", "done", extra_blocks={"Избранное": "Да"})
        cancelled = self.add("Клиент/Объект/2026-01-01 - Отмена", "cancelled")
        inactive = self.add("Скрытый/Объект/2026-01-01 - Работа")
        similar = self.add("Скрытый 2/Объект/2026-01-01 - Работа")
        production = self.add("# work/2026-01-01 - Производство", extra_blocks={"Статус заказа поставщику": "В архив"})
        supplier = self.add("# work/# glass/2026-01-01 - Архив", extra_blocks={"Статус заказа поставщику": "В архив"})
        removed = self.add("Клиент/Объект/2026-01-01 - Снят")
        self.store.remove({"path": removed["path"], "revision": removed["revision"], "confirmed": True})
        rows = {row["path"]: row for row in hidden_orders.listed(self.store, {"Скрытый"}, {"Скрытый/Объект"})["orders"]}
        self.assertEqual(set(rows), {order["path"] for order in (done, cancelled, inactive, production, supplier, removed)})
        self.assertEqual(rows[done["path"]]["reasons"], ["done"])
        self.assertEqual(rows[inactive["path"]]["reasons"], ["inactive_client", "inactive_object"])
        self.assertEqual(rows[supplier["path"]]["reasons"], ["production", "supplier_archive"])
        self.assertEqual(rows[supplier["path"]]["status_label"], "В архив")
        self.assertEqual(rows[production["path"]]["client"], "Производство")
        self.assertEqual(rows[production["path"]]["reasons"], ["production", "supplier_archive"])
        self.assertEqual(rows[production["path"]]["status_label"], "В архив")
        self.assertEqual(rows[removed["path"]]["reasons"], ["unregistered"])
        self.assertEqual(rows[done["path"]]["note"], "Первая строка")
        self.assertNotIn(active["path"], rows)
        # A similarly named client is a different branch.
        self.assertNotIn(similar["path"], rows)

    def test_known_unregistered_folders_and_identity_paths(self):
        orders = []
        for group in ("01 - Группа", "02 - Группа"):
            path = f"{group}/Клиент/Объект/2026/2026-01-01 - Готово"
            orders.append(self.add(path, "done"))
        draft = "Клиент/Объект/2026-01-02 - Без карточки"
        listing = object_orders.ObjectOrders(self.store)
        listing.put(listing.folder_kind, draft, {"version": 1, "present": True})
        listing.put(listing.folder_kind, draft + "/2026-01-03 - Вложение", {"version": 1, "present": True})
        listing.put(listing.folder_kind, "Клиент/Объект/2026-01-04 - Исчез", {"version": 1, "present": False})
        # A catalog entry must not duplicate an existing card.
        listing.put(listing.folder_kind, orders[0]["path"], {"version": 1, "present": True})
        rows = hidden_orders.listed(self.store, set(), set())["orders"]
        self.assertEqual(len(rows), 3)
        self.assertEqual({row["client_path"] for row in rows if row["id"]}, {"01 - Группа/Клиент", "02 - Группа/Клиент"})
        self.assertEqual({row["object"] for row in rows}, {"Объект"})
        self.assertEqual(next(row for row in rows if not row["id"])["reasons"], ["unregistered"])
        self.assertIsNone(self.store.get(draft, include_unregistered=True))

    def test_offline_read_preserves_records_and_history_and_skips_unknown_catalog(self):
        order = self.add("Клиент/Объект/2026-01-01 - Готово", "done", extra_blocks={"Будущий блок": "Сохранить"})
        MetadataStore(self.store).put("object_order_folder", "Клиент/Объект/2026-01-02 - Будущий", {"version": 2, "present": True}, "missing")
        with self.store.connect() as db:
            before = list(db.iterdump())
        self.root.rename(self.base / "offline")
        with patch.object(OrderStore, "target", side_effect=AssertionError("No iCloud access")):
            result = hidden_orders.listed(self.store, set(), set())
        self.assertEqual([row["id"] for row in result["orders"]], [order["id"]])
        self.assertEqual(len(result["warnings"]), 1)
        with self.store.connect() as db:
            self.assertEqual(list(db.iterdump()), before)

    def test_http_updates_membership_and_serves_page(self):
        done = self.add("Клиент/Объект/2026-01-01 - Готово", "done")
        path = "/api/hidden-orders"
        self.assertEqual(self.http(path)[0], 200)
        self.assertEqual(json.loads(self.http(path)[2])["orders"][0]["id"], done["id"])
        self.store.save_status({"path": done["path"], "revision": done["revision"], "status": "new"})
        self.assertEqual(json.loads(self.http(path)[2])["orders"], [])
        for route in ("/hidden-orders.html", "/hidden-orders.js"):
            status, _, body = self.http(route)
            self.assertEqual(status, 200)
            self.assertTrue(body)

    def test_empty_list_does_not_create_database(self):
        self.assertEqual(hidden_orders.listed(self.store, set(), set())["orders"], [])
        self.assertFalse(self.store.database.exists())


if __name__ == "__main__":
    unittest.main()
