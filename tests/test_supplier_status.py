import json
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import order_document as document
from orders import OrderConflict, OrderStore
from work_order_list import WorkOrderList
import work_orders
import test_server as fixtures

manager = fixtures.manager


class SupplierStatusTests(unittest.TestCase):
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url
    section = "# work/# glass"
    path = section + "/2026-10-21 - Стеклопакеты"

    def setUp(self):
        fixtures.ManagerTests.setUp(self)
        mode = patch.object(manager, "DATABASE_ONLY", True)
        mode.start()
        self.patches.append(mode)
        self.folder(self.path)
        self.store = manager.order_store()
        blocks = document.write_favorite({"Особое": "Сохранить"}, True)
        self.order = self.store.add(self.path, {"title": "Стеклопакеты", "status": "process", "financial_status": "partial",
            "note": "Заметка", "amount": 12345, "costs": 2000, "paid": 5000, "extra_blocks": blocks})
        self.listing = WorkOrderList(self.store)
        manager.read_folder(self.section)
        manager.read_folder("# work")

    def payload(self, order=None, **changes):
        order = order or self.order
        return {"path": order["path"], "id": order["id"], "revision": order["revision"], "supplier_status": "cancelled", **changes}

    def save_card(self, order, **changes):
        return self.store.save({**order, **{key: str(order[key] / 100) for key in ("amount", "costs", "paid")}, **changes})

    def test_partial_status_preserves_other_fields_sort_date_and_writes_one_history(self):
        self.assertEqual(self.order["supplier_status"], "work")
        self.assertNotIn(work_orders.STATUS_BLOCK, self.order["extra_blocks"])
        with self.store.connect() as db:
            before = db.execute("SELECT count(*) FROM metadata_history WHERE entity='orders' AND identity=?", (self.order["id"],)).fetchone()[0]
        self.root.rename(self.base / "offline")
        with patch.object(OrderStore, "target", side_effect=AssertionError("No folders")):
            saved = self.store.save_supplier_status(self.payload())
        self.assertEqual(saved["supplier_status"], "cancelled")
        self.assertEqual(saved["revision"], self.order["revision"] + 1)
        self.assertEqual(saved["extra_blocks"], {**self.order["extra_blocks"], work_orders.STATUS_BLOCK: "Отменён"})
        for key in self.order.keys() - {"supplier_status", "extra_blocks", "revision"}:
            self.assertEqual(saved[key], self.order[key], key)
        with self.store.connect() as db:
            after = db.execute("SELECT count(*) FROM metadata_history WHERE entity='orders' AND identity=?", (self.order["id"],)).fetchone()[0]
        self.assertEqual(after, before + 1)

    def test_cancelled_stays_in_lists_archived_hides_and_restoring_returns_same_order(self):
        cancelled = self.store.save_supplier_status(self.payload())
        self.assertEqual([row["id"] for row in self.listing.read(self.section)["orders"]], [self.order["id"]])
        archived = self.store.save_supplier_status(self.payload(cancelled, supplier_status="archived"))
        self.assertEqual(self.listing.read(self.section)["orders"], [])
        self.assertEqual(self.listing.read("# work")["orders"], [])
        status, _, body = self.http("/api/orders")
        self.assertEqual(status, 200, body)
        self.assertNotIn(archived["id"], [row["id"] for row in json.loads(body)["favorites"]])
        self.assertIn(archived["id"], [row["id"] for row in json.loads(body)["calendar_supplier_orders"]])
        self.assertEqual(self.store.get(self.path)["supplier_status"], "archived")
        self.assertEqual(manager.read_folder(self.path)["order"]["id"], archived["id"])
        restored = self.store.save_supplier_status(self.payload(archived, supplier_status="work"))
        self.assertEqual([row["id"] for row in self.listing.read(self.section)["orders"]], [restored["id"]])
        self.assertEqual([row["id"] for row in self.listing.read("# work")["orders"]], [restored["id"]])
        self.assertEqual(restored["updated"], self.order["updated"])

    def test_http_requires_identity_version_valid_status_and_registered_supplier(self):
        for changes in ({"id": "wrong"}, {"revision": True}, {"revision": 0}, {"supplier_status": "done"}, {"supplier_status": None}):
            with self.subTest(changes=changes):
                status, _, _ = self.http("/api/order-supplier-status", "POST", json.dumps(self.payload(**changes)))
                self.assertIn(status, (400, 409))
                self.assertEqual(self.store.get(self.path), self.order)
        with patch.object(manager, "schedule_order_sync"):
            status, _, body = self.http("/api/order-supplier-status", "POST", json.dumps(self.payload()))
        self.assertEqual(status, 200, body)
        saved = json.loads(body)
        self.assertEqual(saved["supplier_status"], "cancelled")
        with self.assertRaises(OrderConflict):
            self.store.save_supplier_status(self.payload())
        removed = self.store.remove({"path": self.path, "revision": saved["revision"], "confirmed": True})
        with self.assertRaises(OrderConflict):
            self.store.save_supplier_status(self.payload(removed))

    def test_scope_excludes_regular_orders_events_print_and_freza(self):
        for path in ("Клиент/Объект/2026-10-21 - Заказ", "# work/# freza/Задание"):
            with self.subTest(path=path):
                self.folder(path)
                row = self.store.add(path, {"status": "new"})
                self.assertNotIn("supplier_status", row)
                with self.assertRaises(ValueError):
                    self.store.save_supplier_status(self.payload(row))
                self.assertEqual(self.store.get(path), row)
        for path in (self.path + "/00 - Событие", "# work/# print/Задание"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.store.save_supplier_status(self.payload(path=path))

    def test_full_card_save_supports_supplier_status_without_changing_hidden_ordinary_status(self):
        saved = self.save_card(self.order, supplier_status="archived", note="Новая заметка")
        self.assertEqual(saved["supplier_status"], "archived")
        self.assertEqual(saved["status"], self.order["status"])
        self.assertEqual(saved["financial_status"], self.order["financial_status"])
        self.assertEqual(saved["note"], "Новая заметка")
        self.assertEqual(saved["extra_blocks"]["Особое"], "Сохранить")

    def test_unknown_status_is_not_hidden_or_overwritten_and_note_can_still_be_saved(self):
        blocks = {**self.order["extra_blocks"], work_orders.STATUS_BLOCK: {"version": 8, "future": "Сохранить"}}
        with self.store.connect() as db:
            db.execute("UPDATE orders SET extra_blocks=? WHERE id=?", (json.dumps(blocks), self.order["id"]))
        current = self.store.get(self.path)
        self.assertIsNone(current["supplier_status"])
        self.assertEqual(len(self.listing.read(self.section)["orders"]), 1)
        with self.assertRaises(ValueError):
            self.store.save_supplier_status(self.payload(current))
        with self.assertRaises(ValueError):
            self.save_card(current, supplier_status="work")
        payload = {key: value for key, value in current.items() if key != "supplier_status"}
        saved = self.save_card(payload, note="Сохраняем заметку")
        for key, value in blocks.items():
            self.assertEqual(saved["extra_blocks"][key], value)

    def test_archived_link_is_hidden_without_deleting_relation_and_new_link_is_rejected(self):
        parent_path = "# work/2026-10-21 - Сборный"
        self.folder(parent_path)
        parent = self.store.add(parent_path, {"status": "new"})
        linked = self.store.save_work_links({"path": parent_path, "revision": parent["revision"], "order_ids": [self.order["id"]]})
        archived = self.store.save_supplier_status(self.payload(supplier_status="archived"))
        links = self.store.work_links(parent_path)
        self.assertEqual(links["linked_ids"], [archived["id"]])
        self.assertEqual(links["items"], [])
        self.assertNotIn(archived["id"], [row["id"] for row in links["candidates"]])
        unlinked = self.store.save_work_links({"path": parent_path, "revision": linked["revision"], "order_ids": []})
        with self.assertRaises(ValueError):
            self.store.save_work_links({"path": parent_path, "revision": unlinked["revision"], "order_ids": [archived["id"]]})
        self.store.save_supplier_status(self.payload(archived, supplier_status="work"))
        self.assertIn(archived["id"], [row["id"] for row in self.store.work_links(parent_path)["candidates"]])

    def test_legacy_glass_and_etc_support_status_without_data_migration(self):
        for section in ("#glass", "# work/# etc"):
            path = section + "/2026-10-21 - Заказ"
            self.folder(path)
            row = self.store.add(path, {"status": "done"})
            self.assertEqual(row["supplier_status"], "work")
            archived = self.store.save_supplier_status(self.payload(row, supplier_status="archived"))
            self.listing.refresh(section)
            self.assertEqual(self.listing.read(section)["orders"], [])
            self.assertEqual(archived["status"], "done")

    def test_direct_production_order_has_the_same_statuses_and_archive_restore(self):
        path = "# work/2026-10-22 - Общий заказ"
        self.folder(path)
        order = self.store.add(path, {"status": "done", "note": "Общая заметка"})
        self.assertEqual(order["supplier_status"], "work")
        cancelled = self.store.save_supplier_status(self.payload(order))
        manager.read_folder("# work")
        self.assertIn(order["id"], [row["id"] for row in self.listing.read("# work")["orders"]])
        archived = self.store.save_supplier_status(self.payload(cancelled, supplier_status="archived"))
        data = self.listing.read("# work")
        self.assertNotIn(order["id"], [row["id"] for row in data["orders"]])
        self.assertIn(path, data["archived_paths"])
        self.assertIn(order["id"], [row["id"] for row in data["archived_orders"]])
        restored = self.store.save_supplier_status(self.payload(archived, supplier_status="work"))
        self.assertEqual(restored["status"], "done")
        self.assertEqual(restored["note"], "Общая заметка")
        self.assertEqual(restored["updated"], order["updated"])

    def test_archive_shows_latest_ten_archive_actions_not_folder_dates_and_rearchive_is_new(self):
        archived = []
        start = datetime(2026, 10, 26, 12, tzinfo=timezone.utc)
        with patch.object(work_orders, "datetime", wraps=datetime) as clock:
            for index in range(12):
                path = self.section + f"/2020-01-{12-index:02d} - Архив {index}"
                self.folder(path)
                order = self.store.add(path, {"status": "new"})
                clock.now.return_value = start + timedelta(seconds=index)
                archived.append(self.store.save_supplier_status(self.payload(order, supplier_status="archived")))
        self.listing.refresh(self.section)
        data = self.listing.read(self.section)
        self.assertEqual(len(data["archived_paths"]), 12)
        self.assertEqual([row["id"] for row in data["archived_orders"]], [row["id"] for row in reversed(archived[2:])])
        restored = self.store.save_supplier_status(self.payload(archived[-1], supplier_status="work"))
        self.assertEqual(restored["archived_at"], archived[-1]["archived_at"])
        self.assertNotIn(restored["id"], [row["id"] for row in self.listing.read(self.section)["archived_orders"]])
        with patch.object(work_orders, "datetime", wraps=datetime) as clock:
            clock.now.return_value = start + timedelta(seconds=120)
            again = self.store.save_supplier_status(self.payload(restored, supplier_status="archived"))
        self.assertGreater(again["archived_at"], archived[-1]["archived_at"])
        self.assertEqual(self.listing.read(self.section)["archived_orders"][0]["id"], again["id"])

    def test_older_archive_without_timestamp_uses_history_without_rewriting_data(self):
        archived = self.store.save_supplier_status(self.payload(supplier_status="archived"))
        blocks = {key: value for key, value in archived["extra_blocks"].items() if key != work_orders.ARCHIVED_AT_BLOCK}
        with self.store.connect() as db:
            db.execute("UPDATE orders SET extra_blocks=? WHERE id=?", (json.dumps(blocks), archived["id"]))
        before = self.store.get(self.path)
        data = self.listing.read(self.section)
        self.assertEqual(data["archived_orders"][0]["id"], archived["id"])
        self.assertGreater(data["archived_orders"][0]["archived_at"], 0)
        self.assertEqual(self.store.get(self.path), before)


if __name__ == "__main__":
    unittest.main()
