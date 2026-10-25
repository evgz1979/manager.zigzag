import json
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

import order_deadlines
from orders import OrderConflict, OrderStore
import test_server as fixtures

manager = fixtures.manager


class DeadlineCalendarTests(unittest.TestCase):
    def test_sixteen_iso_weeks_cross_year_without_reusing_week_numbers(self):
        weeks = order_deadlines.week_options(datetime(2020, 12, 31, tzinfo=timezone.utc))
        self.assertEqual(len(weeks), 16)
        self.assertEqual((weeks[0]["start"], weeks[0]["end"], weeks[0]["number"], weeks[0]["year"]),
                         ("2020-12-28", "2021-01-03", 53, 2020))
        self.assertEqual((weeks[1]["start"], weeks[1]["number"], weeks[1]["year"]), ("2021-01-04", 1, 2021))
        self.assertEqual(weeks[-1]["start"], "2021-04-12")
        self.assertEqual(weeks[0]["label"], "28.12.2020 — 03.01.2021")
        self.assertEqual([week["current"] for week in weeks], [True] + [False] * 15)

    def test_current_week_uses_moscow_midnight(self):
        before = order_deadlines.week_options(datetime(2026, 10, 25, 20, 59, tzinfo=timezone.utc))
        after = order_deadlines.week_options(datetime(2026, 10, 25, 21, 0, tzinfo=timezone.utc))
        self.assertEqual((before[0]["start"], before[0]["number"]), ("2026-10-19", 43))
        self.assertEqual((after[0]["start"], after[0]["number"]), ("2026-10-26", 44))

    def test_unknown_deadline_blocks_are_read_only(self):
        values = ["К пятнице", "[]", '{"version":2,"weeks":[]}', '{"version":true,"weeks":[]}',
            '{"version":1,"weeks":[],"future":true}', '{"version":1,"weeks":["2026-10-20"]}',
            '{"version":1,"weeks":["2026-10-19","2026-10-19"]}']
        for value in values:
            with self.subTest(value=value):
                blocks = {order_deadlines.BLOCK: value, "Особое": "Сохранить"}
                self.assertIsNone(order_deadlines.read(blocks))
                with self.assertRaises(ValueError):
                    order_deadlines.write(blocks, "2026-10-19", True)
                self.assertEqual(blocks[order_deadlines.BLOCK], value)


class OrderDeadlineTests(unittest.TestCase):
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
        self.order = self.store.add(self.path, {"status": "process", "financial_status": "partial",
            "note": "Сохранить заметку", "amount": 10000, "costs": 2000, "paid": 5000,
            "extra_blocks": {"Задачи": "- [ ] Позвонить", "Избранное": "Да",
                "Закупки и затраты": "- [ ] Стекло\n  Поставщики: glass", "Особое": "Сохранить"}})

    def payload(self, record=None, **changes):
        return {"path": self.path, "id": (record or self.order)["id"], "revision": (record or self.order)["revision"],
                "week": "2026-10-19", "selected": True, **changes}

    def test_multiple_marks_offline_preserve_card_and_history(self):
        self.root.rename(self.base / "offline")
        with patch.object(OrderStore, "target", side_effect=AssertionError("No iCloud access")):
            first = self.store.save_deadline_week(self.payload(note="Не заменять", amount="999"))
            both = self.store.save_deadline_week(self.payload(first, week="2026-10-26"))
            final = self.store.save_deadline_week(self.payload(both, selected=False))
        self.assertEqual(both["deadline_weeks"], ["2026-10-19", "2026-10-26"])
        self.assertEqual(final["deadline_weeks"], ["2026-10-26"])
        self.assertEqual(final["revision"], self.order["revision"] + 3)
        for field in self.order.keys() - {"extra_blocks", "deadline_weeks", "revision", "updated"}:
            self.assertEqual(final[field], self.order[field], field)
        for name, value in self.order["extra_blocks"].items():
            self.assertEqual(final["extra_blocks"][name], value)
        with self.store.connect() as db:
            history = [json.loads(row[0]) for row in db.execute(
                "SELECT data FROM metadata_history WHERE entity='orders' AND identity=?", (self.order["id"],))]
        self.assertTrue(any(order_deadlines.read(json.loads(row["extra_blocks"])) == both["deadline_weeks"] for row in history))
        self.assertFalse((self.base / "offline" / self.path / "!.txt").exists())
        restarted = OrderStore(self.root, manager.DATA_DIR, manager.STATUS_LABELS)
        self.assertEqual(restarted.get(self.path)["deadline_weeks"], ["2026-10-26"])

    def test_invalid_and_stale_updates_do_not_replace_marks(self):
        for value in (None, True, "2026-W43", "2026-02-30", "2026-10-20", "26-10-19"):
            with self.subTest(week=value), self.assertRaises(ValueError):
                self.store.save_deadline_week(self.payload(week=value))
        for value in (None, "true", 1):
            with self.subTest(selected=value), self.assertRaises(ValueError):
                self.store.save_deadline_week(self.payload(selected=value))
        for value in (None, "1", True):
            with self.subTest(revision=value), self.assertRaises(ValueError):
                self.store.save_deadline_week(self.payload(revision=value))
        self.assertEqual(self.store.get(self.path), self.order)
        with self.assertRaises(OrderConflict):
            self.store.save_deadline_week(self.payload(id="other-order"))
        saved = self.store.save_deadline_week(self.payload())
        with self.assertRaises(OrderConflict):
            self.store.save_deadline_week(self.payload(week="2026-10-26"))
        self.assertEqual(self.store.get(self.path), saved)
        removed = self.store.remove({"path": self.path, "revision": saved["revision"], "confirmed": True})
        with self.assertRaises(OrderConflict):
            self.store.save_deadline_week(self.payload(removed))
        restored = self.store.import_folder(self.path)
        self.assertEqual(restored["deadline_weeks"], ["2026-10-19"])
        with self.store.connect() as db:
            db.execute("UPDATE orders SET extra_blocks=?,revision=revision+1 WHERE path=?",
                       (json.dumps({**restored["extra_blocks"], order_deadlines.BLOCK: "Особый будущий срок"}), self.path))
        unknown = self.store.get(self.path)
        self.assertIsNone(unknown["deadline_weeks"])
        with self.assertRaises(ValueError):
            self.store.save_deadline_week(self.payload(unknown))
        self.assertEqual(self.store.get(self.path), unknown)

    def test_http_and_other_partial_edits_preserve_weeks(self):
        with patch.object(manager, "schedule_order_sync") as schedule:
            status, _, body = self.http("/api/order-deadline-week", "POST", json.dumps(self.payload()))
            self.assertEqual(status, 200)
            saved = json.loads(body)
            schedule.assert_called_once()
            self.assertEqual(self.http("/api/order-deadline-week", "POST", json.dumps(self.payload()))[0], 409)
            self.assertEqual(self.http("/api/order-deadline-week", "POST", json.dumps(self.payload(saved, selected="yes")))[0], 400)
        saved = self.store.save({**saved, "note": "Правка карточки", "amount": "100", "costs": "20", "paid": "50"})
        saved = self.store.save_favorite({"path": self.path, "revision": saved["revision"], "is_favorite": False})
        saved = self.store.save_status({"path": self.path, "revision": saved["revision"], "status": "waiting"})
        listed = json.loads(self.http("/api/orders")[2])
        self.assertEqual(listed["orders"][0]["deadline_weeks"], ["2026-10-19"])
        self.assertEqual(len(listed["deadline_week_options"]), 16)
        self.assertEqual(saved["deadline_weeks"], ["2026-10-19"])

    def test_overdue_marks_survive_week_rollover_until_explicitly_unchecked(self):
        saved = self.store.save_deadline_week(self.payload())
        saved = self.store.save_deadline_week(self.payload(saved, week="2026-10-26"))
        saved = self.store.save_deadline_comment({"path": self.path, "id": saved["id"],
            "revision": saved["revision"], "week": "2026-10-19", "comment": "Перепланировать"})
        for now, current in ((datetime(2026, 10, 25, 20, 59, tzinfo=timezone.utc), "2026-10-19"),
                             (datetime(2026, 10, 25, 21, 0, tzinfo=timezone.utc), "2026-10-26")):
            with patch.object(order_deadlines, "datetime") as clock:
                clock.now.return_value = now
                listed = json.loads(self.http("/api/orders")[2])
            self.assertEqual(listed["deadline_week_options"][0]["start"], current)
            self.assertEqual(listed["orders"][0]["deadline_weeks"], ["2026-10-19", "2026-10-26"])
            self.assertEqual(listed["orders"][0]["revision"], saved["revision"])
        unchecked = self.store.save_deadline_week(self.payload(saved, selected=False))
        self.assertEqual(unchecked["deadline_weeks"], ["2026-10-26"])
        self.assertEqual(unchecked["deadline_comments"], {"2026-10-19": "Перепланировать"})


if __name__ == "__main__":
    unittest.main()
