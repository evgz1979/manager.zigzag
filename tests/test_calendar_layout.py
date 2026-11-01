import json
import unittest
import uuid
import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch

import calendar_layout as layout
import calendar_todos
import invoices
import order_calendar
import order_deadlines
from orders import OrderConflict, OrderStore
import test_server as fixtures

manager = fixtures.manager


class CalendarLayoutJavaScriptTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node.js is required for calendar checks")
    def test_small_order_range_and_past_week_row_visibility(self):
        subprocess.run(["node", str(Path(__file__).with_name("calendar-layout.cjs"))], check=True, capture_output=True, text=True)


class CalendarLayoutTests(unittest.TestCase):
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    path = "Клиент/2026-00-00 - Заказ"

    def setUp(self):
        fixtures.ManagerTests.setUp(self)
        mode = patch.object(manager, "DATABASE_ONLY", True)
        mode.start()
        self.patches.append(mode)
        self.store = manager.order_store()
        blocks = order_deadlines.write({"Особое": "Сохранить", "Задачи": "- [ ] Позвонить"}, "2026-10-26", True)
        blocks = order_calendar.write(blocks, "2026-10-27", "Замер")
        self.order = self.store.add(self.path, {"title": "Окна", "status": "process", "financial_status": "partial",
            "note": "Сохранить заметку", "amount": 10000, "costs": 2000, "paid": 5000, "extra_blocks": blocks})

    def compact(self, record=None, **changes):
        return {**(record or self.order), "calendar_compact": True, **changes}

    def test_compact_flag_is_partial_offline_versioned_and_survives_other_edits_and_registration(self):
        self.root.rename(self.base / "offline")
        with patch.object(OrderStore, "target", side_effect=AssertionError("No folders")), \
                patch("icloud_access.read_bytes", side_effect=AssertionError("No documents")):
            saved = self.store.save_calendar_compact(self.compact(note="Do not replace", amount=99999))
        self.assertTrue(saved["calendar_compact"])
        for key in self.order.keys() - {"revision", "extra_blocks", "calendar_compact"}:
            self.assertEqual(saved[key], self.order[key], key)
        self.assertEqual(saved["revision"], self.order["revision"] + 1)
        for key, value in self.order["extra_blocks"].items():
            self.assertEqual(saved["extra_blocks"][key], value)
        with self.store.connect() as db:
            self.assertEqual(db.execute("SELECT value FROM metadata_settings WHERE key='calendar_layout'").fetchone()[0], "1")
            history = [json.loads(row[0]) for row in db.execute("SELECT data FROM metadata_history WHERE entity='orders' AND identity=?", (saved["id"],))]
        self.assertTrue(any(row["revision"] == self.order["revision"] for row in history))
        with self.assertRaises(OrderConflict):
            self.store.save_calendar_compact(self.compact())
        (self.base / "offline").rename(self.root)
        moved = self.store.move_calendar_event({**saved, "date": "2026-10-27", "days": 7, "period": "day"})
        self.assertTrue(moved["calendar_compact"])
        removed = self.store.remove({"path": self.path, "revision": moved["revision"], "confirmed": True})
        restored = self.store.import_folder(self.path)
        self.assertEqual(restored["id"], saved["id"])
        self.assertTrue(restored["calendar_compact"])
        changed = self.store.save({**restored, "amount": "100", "costs": "20", "paid": "50", "note": "Новое"})
        unmarked = self.store.save_calendar_compact(self.compact(changed, calendar_compact=False))
        self.assertFalse(unmarked["calendar_compact"])
        self.assertEqual(unmarked["deadline_weeks"], changed["deadline_weeks"])

    def test_unknown_compact_format_and_invalid_flags_keep_original_data(self):
        for value in (None, 1, "true"):
            with self.assertRaises(ValueError):
                self.store.save_calendar_compact(self.compact(calendar_compact=value))
        for raw in ('{"version":2,"enabled":true}', '{"version":true,"enabled":true}', '{"version":1,"enabled":1}', 'opaque'):
            with self.store.connect() as db:
                db.execute("UPDATE orders SET extra_blocks=? WHERE id=?", (json.dumps({**self.order["extra_blocks"], layout.COMPACT_BLOCK: raw}), self.order["id"]))
            before = self.store.get(self.path)
            self.assertIsNone(before["calendar_compact"])
            with self.assertRaises(ValueError):
                self.store.save_calendar_compact(self.compact(before))
            self.assertEqual(self.store.get(self.path), before)

    def test_carryover_keeps_dates_money_flags_and_survives_edit_move_and_trash_restore(self):
        store = manager.invoice_store()
        for path, period, operation in ((self.path, "day", "incoming"), ("", "week", "outgoing")):
            payload = {"path": path, "id": str(uuid.uuid4()), "date": "2026-10-26", "period": period,
                       "operation": operation, "amount": "123.45", "text": "Оплата"}
            plan = store.plan(payload)
            marked = store.save_plan_calendar_carryover({**plan, "is_carryover": True})
            self.assertEqual({k: v for k, v in marked["data"].items() if k != "_calendar_carryover"}, plan["data"])
            self.assertEqual(marked["revision"], plan["revision"] + 1)
            with self.assertRaises(invoices.InvoiceConflict):
                store.save_plan_calendar_carryover({**plan, "is_carryover": False})
            moved = store.move_calendar_plan({**marked, "date": "2026-10-26", "period": period, "days": 7})
            edited = store.plan({**payload, "revision": moved["revision"], "date": "2026-11-02", "text": "Новый комментарий"})
            self.assertTrue(edited["data"]["_calendar_carryover"])
            shown = next(row for row in store.calendar_plans(self.store.list()) if row["id"] == plan["id"])
            self.assertTrue(shown["is_carryover"])
            if not path:
                request = {**edited, "date": "2026-11-02", "period": period, "confirmed": True}
                status, _, body = self.http("/api/calendar-payment-remove", "POST", json.dumps(request))
                self.assertEqual(status, 200, body)
                removed = json.loads(body)
                status, _, body = self.http("/api/calendar-payment-restore", "POST", json.dumps({**request, "revision": removed["revision"]}))
                self.assertEqual(status, 200, body)
                self.assertTrue(json.loads(body)["data"]["_calendar_carryover"])
        self.assertEqual(self.store.get(self.path), self.order)

    def test_carryover_rejects_unknown_values_and_invoice_issuance(self):
        store = manager.invoice_store()
        invoice = store.plan({"path": self.path, "id": str(uuid.uuid4()), "date": "2026-10-26"})
        with self.assertRaises(ValueError):
            store.save_plan_calendar_carryover({**invoice, "is_carryover": True})
        plan = store.plan({"path": "", "id": str(uuid.uuid4()), "date": "2026-10-26", "operation": "outgoing", "amount": "10"})
        for value in (None, 1, "true"):
            with self.assertRaises(ValueError):
                store.save_plan_calendar_carryover({**plan, "is_carryover": value})
        with store.connect() as db:
            data = {**plan["data"], "_calendar_carryover": "unknown"}
            db.execute("UPDATE invoices SET data=? WHERE id=?", (json.dumps(data), plan["id"]))
        before = store.get("", plan["id"])
        with self.assertRaises(ValueError):
            store.save_plan_calendar_carryover({**before, "is_carryover": True})
        self.assertEqual(store.get("", plan["id"]), before)

    def test_http_compact_and_carryover_and_digest_match_visible_events(self):
        with patch.object(manager, "schedule_order_sync"):
            status, _, body = self.http("/api/order-calendar-compact", "POST", json.dumps(self.compact()))
        self.assertEqual(status, 200, body)
        small = json.loads(body)
        marked = {**small, "calendar_watch_todos": {"day": ["2026-10-27"], "week": []}}
        self.assertEqual(calendar_todos.digest({"orders": [marked]}, "2026-10-26"), "")
        store = manager.invoice_store()
        plan = store.plan({"path": self.path, "id": str(uuid.uuid4()), "date": "2026-10-26", "operation": "incoming", "amount": "100"})
        status, _, body = self.http("/api/invoice-plan-calendar-carryover", "POST", json.dumps({**plan, "is_carryover": True}))
        self.assertEqual(status, 200, body)
        marked_plan = store.save_plan_calendar_watch_todos({**json.loads(body), "is_watch_todos": True})
        shown = next(row for row in store.calendar_plans([marked]) if row["id"] == plan["id"])
        result = calendar_todos.digest({"orders": [marked], "calendar_invoice_plans": [shown]}, "2026-10-26")
        self.assertIn("Получение оплаты", result)
        self.assertNotIn("Замер", result)
