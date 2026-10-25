import json
import unittest
from unittest.mock import patch

import order_calendar
import order_deadlines
from orders import OrderConflict, OrderStore
import test_server as fixtures

manager = fixtures.manager


class CalendarFormatTests(unittest.TestCase):
    def test_independent_dates_preserve_exact_text_and_other_blocks(self):
        blocks = {"Особое": "Сохранить"}
        first = order_calendar.write(blocks, "2026-10-26", '  Замер "двери" <эскиз>  ')
        both = order_calendar.write(first, "2026-10-27", "Монтаж")
        final = order_calendar.write(both, "2026-10-26", "")
        self.assertEqual(order_calendar.read(both), {"2026-10-26": '  Замер "двери" <эскиз>  ', "2026-10-27": "Монтаж"})
        self.assertEqual(order_calendar.read(final), {"2026-10-27": "Монтаж"})
        self.assertEqual(final["Особое"], blocks["Особое"])
        self.assertEqual(order_calendar.read(order_calendar.write(final, "2026-10-27", "")), {})

    def test_invalid_dates_text_and_unknown_formats_are_preserved(self):
        for day in (None, True, "26-10-26", "2026-02-30", "2026-10-26T10:00", "2026-2-03"):
            with self.subTest(day=day), self.assertRaises(ValueError):
                order_calendar.write({}, day, "Замер")
        for text in (None, True, 42, "  ", "Две\nстроки", "Две\rстроки", "Ноль\0", "x" * 1001):
            with self.subTest(text=text), self.assertRaises(ValueError):
                order_calendar.write({}, "2026-10-26", text)
        for value in ('[]', '{"version":2,"events":{}}', '{"version":true,"events":{}}',
                      '{"version":1,"events":{},"future":true}', '{"version":1,"events":{"2026-02-30":"Замер"}}',
                      '{"version":1,"events":{"2026-10-26":""}}', '{"version":1,"events":{"2026-10-26":42}}'):
            blocks = {order_calendar.BLOCK: value}
            with self.subTest(value=value):
                self.assertIsNone(order_calendar.read(blocks))
                with self.assertRaises(ValueError):
                    order_calendar.write(blocks, "2026-10-26", "Новый")
                self.assertEqual(blocks[order_calendar.BLOCK], value)


class CalendarApiTests(unittest.TestCase):
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    path = "Клиент/Объект/2026-10-20 - Заказ"

    def setUp(self):
        fixtures.ManagerTests.setUp(self)
        mode = patch.object(manager, "DATABASE_ONLY", True)
        mode.start()
        self.patches.append(mode)
        self.folder(self.path)
        self.store = manager.order_store()
        self.order = self.store.add(self.path, {"status": "process", "financial_status": "partial", "note": "Заметка",
            "amount": 10000, "costs": 2000, "paid": 5000,
            "extra_blocks": order_deadlines.write({"Особое": "Сохранить", "Задачи": "- [ ] Позвонить"}, "2026-10-26", True)})

    def payload(self, record=None, **changes):
        record = record or self.order
        return {"path": self.path, "id": record["id"], "revision": record["revision"],
                "date": "2026-10-27", "text": "Монтаж", **changes}

    def test_offline_partial_write_preserves_fields_sorting_history_and_restart(self):
        self.root.rename(self.base / "offline")
        with patch.object(OrderStore, "target", side_effect=AssertionError("No folder reads")), \
                patch("icloud_access.read_bytes", side_effect=AssertionError("No originals")):
            saved = self.store.save_calendar_event(self.payload(note="Не заменять", amount="999"))
            for field in self.order.keys() - {"calendar_events", "extra_blocks", "revision"}:
                self.assertEqual(saved[field], self.order[field], field)
            both = self.store.save_calendar_event(self.payload(saved, date="2026-10-28", text="Проверка"))
            removed = self.store.save_calendar_event(self.payload(both, text=""))
        self.assertEqual(removed["calendar_events"], {"2026-10-28": "Проверка"})
        for name, value in self.order["extra_blocks"].items():
            self.assertEqual(removed["extra_blocks"][name], value)
        restarted = OrderStore(self.root, manager.DATA_DIR, manager.STATUS_LABELS)
        self.assertEqual(restarted.get(self.path)["calendar_events"], removed["calendar_events"])
        with self.store.connect() as db:
            old = [json.loads(row[0]) for row in db.execute("SELECT data FROM metadata_history WHERE entity='orders' AND identity=?", (self.order["id"],))]
        self.assertTrue(any(order_calendar.read(json.loads(row["extra_blocks"])) == both["calendar_events"] for row in old))
        self.assertFalse((self.base / "offline" / self.path / "!.txt").exists())

    def test_http_version_identity_unknown_format_and_unrelated_saves(self):
        with patch.object(manager, "schedule_order_sync") as schedule:
            status, _, body = self.http("/api/order-calendar-event", "POST", json.dumps(self.payload()))
            self.assertEqual(status, 200)
            saved = json.loads(body)
            schedule.assert_called_once()
            for changes in ({}, {"id": "Чужой UUID"}, {"path": "Клиент/Другой заказ"}):
                self.assertEqual(self.http("/api/order-calendar-event", "POST", json.dumps(self.payload(**changes)))[0], 409)
            for changes in ({"revision": None}, {"revision": True}, {"id": ""}, {"date": "2026-02-30"}, {"text": 42}):
                self.assertEqual(self.http("/api/order-calendar-event", "POST", json.dumps(self.payload(saved, **changes)))[0], 400)
        listed = json.loads(self.http("/api/orders")[2])["orders"][0]
        self.assertEqual(listed["calendar_events"], saved["calendar_events"])
        saved = self.store.save_deadline_week({**self.payload(saved), "week": "2026-10-26", "selected": False})
        self.assertEqual(saved["calendar_events"], {"2026-10-27": "Монтаж"})
        card = self.store.save({**saved, "note": "Новая заметка", "amount": "100", "costs": "20", "paid": "50"})
        self.assertEqual(card["calendar_events"], saved["calendar_events"])
        removed = self.store.remove({"path": self.path, "revision": card["revision"], "confirmed": True})
        with self.assertRaises(OrderConflict):
            self.store.save_calendar_event(self.payload(removed))
        restored = self.store.import_folder(self.path)
        self.assertEqual(restored["calendar_events"], card["calendar_events"])
        unknown = '{"version":2,"events":{},"future":"Сохранить"}'
        with self.store.connect() as db:
            db.execute("UPDATE orders SET extra_blocks=?,revision=revision+1 WHERE path=?", (
                json.dumps({**restored["extra_blocks"], order_calendar.BLOCK: unknown}), self.path))
        record = self.store.get(self.path)
        self.assertIsNone(record["calendar_events"])
        with self.assertRaises(ValueError):
            self.store.save_calendar_event(self.payload(record))
        self.assertEqual(self.store.get(self.path)["extra_blocks"][order_calendar.BLOCK], unknown)
