import json
import unittest
from unittest.mock import patch

import order_calendar
import order_deadlines
from orders import OrderConflict, OrderStore
import test_server as fixtures

manager = fixtures.manager


class CalendarFormatTests(unittest.TestCase):
    def test_cross_week_moves_add_destination_deadline_and_keep_existing_marks(self):
        for period, source, days, target, week in (
            ("day", "2026-11-01", 1, "2026-11-02", "2026-11-02"),
            ("day", "2026-11-02", -1, "2026-11-01", "2026-10-26"),
            ("day", "2026-10-27", 7, "2026-11-03", "2026-11-02"),
            ("day", "2026-11-03", -7, "2026-10-27", "2026-10-26"),
            ("week", "2026-10-26", 7, "2026-11-02", "2026-11-02"),
            ("week", "2026-11-02", -7, "2026-10-26", "2026-10-26"),
        ):
            with self.subTest(period=period, source=source, days=days):
                blocks = order_deadlines.write({"Особое": "Сохранить"}, "2026-10-19", True)
                blocks = order_calendar.write(blocks, source, '  Монтаж "ЛавФиш"  ', period)
                blocks = order_calendar.set_inactive(blocks, source, True, period)
                before = dict(blocks)
                moved = order_calendar.move(blocks, source, days, period)
                self.assertEqual(order_deadlines.read(moved), sorted(["2026-10-19", week]))
                self.assertEqual(order_calendar.read(moved, period), {target: '  Монтаж "ЛавФиш"  '})
                self.assertEqual(order_calendar.read_inactive(moved)[period], [target])
                self.assertEqual(moved["Особое"], blocks["Особое"])
                self.assertEqual(blocks, before)
                selected = order_deadlines.write(blocks, week, True)
                self.assertEqual(order_deadlines.read(order_calendar.move(selected, source, days, period)), sorted(["2026-10-19", week]))

    def test_same_week_move_keeps_deadlines_and_unknown_deadlines_block_cross_week_move(self):
        for deadline in (None, '{"version":2,"weeks":[],"future":true}'):
            with self.subTest(deadline=deadline):
                blocks = {} if deadline is None else {order_deadlines.BLOCK: deadline}
                blocks = order_calendar.write(blocks, "2026-10-31", "Монтаж")
                moved = order_calendar.move(blocks, "2026-10-31", 1)
                self.assertEqual(moved.get(order_deadlines.BLOCK), deadline)
                before = dict(moved)
                if deadline is not None:
                    with self.assertRaises(ValueError):
                        order_calendar.move(moved, "2026-11-01", 1)
                    self.assertEqual(moved, before)
                else:
                    self.assertEqual(order_deadlines.read(order_calendar.move(moved, "2026-11-01", 1)), ["2026-11-02"])

    def test_week_events_are_independent_and_only_move_by_full_weeks(self):
        daily = order_calendar.write({}, "2026-10-26", "Событие понедельника")
        weekly = order_calendar.write(daily, "2026-10-26", '  На всю неделю "окна"  ', "week")
        self.assertEqual(order_calendar.read(weekly), {"2026-10-26": "Событие понедельника"})
        self.assertEqual(order_calendar.read(weekly, "week"), {"2026-10-26": '  На всю неделю "окна"  '})
        moved = order_calendar.move(weekly, "2026-10-26", 7, "week")
        self.assertEqual(moved[order_calendar.BLOCK], daily[order_calendar.BLOCK])
        self.assertEqual(order_calendar.read(moved, "week"), {"2026-11-02": '  На всю неделю "окна"  '})
        restored = order_calendar.move(moved, "2026-11-02", -7, "week")
        self.assertEqual(order_calendar.read(restored, "week"), order_calendar.read(weekly, "week"))
        self.assertEqual(order_calendar.read(order_calendar.write(restored, "2026-10-26", "", "week"), "week"), order_calendar.read(restored, "week"))
        self.assertEqual(order_calendar.read_inactive(order_calendar.write(restored, "2026-10-26", "", "week"))["week"], ["2026-10-26"])
        for day, days in (("2026-10-26", 1), ("2026-10-26", -1), ("2026-10-27", 7)):
            with self.subTest(day=day, days=days), self.assertRaises(ValueError):
                order_calendar.move(weekly, day, days, "week")
        with self.assertRaises(ValueError):
            order_calendar.write({}, "2026-10-27", "Не понедельник", "week")
        for period in (None, True, "month", ""):
            with self.subTest(period=period), self.assertRaises(ValueError):
                order_calendar.write({}, "2026-10-26", "Неизвестный период", period)
        unknown = {**daily, order_calendar.WEEK_BLOCK: '{"version":2,"events":{}}'}
        self.assertIsNone(order_calendar.read(unknown, "week"))
        with self.assertRaises(ValueError):
            order_calendar.write(unknown, "2026-10-26", "Не заменять", "week")
        edited = order_calendar.write(unknown, "2026-10-26", "Новый текст дня")
        self.assertEqual(edited[order_calendar.WEEK_BLOCK], unknown[order_calendar.WEEK_BLOCK])
        invalid = {order_calendar.WEEK_BLOCK: '{"version":1,"events":{"2026-10-27":"Не понедельник"}}'}
        self.assertIsNone(order_calendar.read(invalid, "week"))

    def test_moves_cross_year_and_leap_day_preserving_text_and_other_blocks(self):
        blocks = order_calendar.write({"Особое": "Сохранить"}, "2026-12-31", '  Замер "окна"  ')
        moved = order_calendar.move(blocks, "2026-12-31", 1)
        self.assertEqual(order_calendar.read(moved), {"2027-01-01": '  Замер "окна"  '})
        self.assertEqual(order_calendar.read(order_calendar.move(moved, "2027-01-01", -1)), order_calendar.read(blocks))
        self.assertEqual(moved["Особое"], "Сохранить")
        leap = order_calendar.write({}, "2028-02-28", "Монтаж")
        self.assertEqual(order_calendar.read(order_calendar.move(leap, "2028-02-28", 1)), {"2028-02-29": "Монтаж"})
        for days in (None, True, "1", 0, 2, 14):
            with self.subTest(days=days), self.assertRaises(ValueError):
                order_calendar.move(blocks, "2026-12-31", days)
        for day, days in (("0001-01-01", -1), ("9999-12-31", 7)):
            with self.subTest(day=day), self.assertRaises(ValueError):
                order_calendar.move(order_calendar.write({}, day, "Замер"), day, days)

    def test_independent_dates_preserve_exact_text_and_other_blocks(self):
        blocks = {"Особое": "Сохранить"}
        first = order_calendar.write(blocks, "2026-10-26", '  Замер "двери" <эскиз>  ')
        both = order_calendar.write(first, "2026-10-27", "Монтаж")
        final = order_calendar.write(both, "2026-10-26", "")
        self.assertEqual(order_calendar.read(both), {"2026-10-26": '  Замер "двери" <эскиз>  ', "2026-10-27": "Монтаж"})
        self.assertEqual(order_calendar.read(final), order_calendar.read(both))
        self.assertEqual(order_calendar.read_inactive(final)["day"], ["2026-10-26"])
        self.assertEqual(final["Особое"], blocks["Особое"])
        self.assertEqual(order_calendar.read_inactive(order_calendar.write(final, "2026-10-27", ""))["day"], ["2026-10-26", "2026-10-27"])

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

    def test_daily_delete_and_undo_preserve_other_fields_history_and_weekly_events(self):
        daily = self.store.save_calendar_event(self.payload())
        weekly = self.store.save_calendar_event(self.payload(daily, period='week', date='2026-10-26', text='План недели'))
        before = self.store.save_calendar_inactive(self.payload(weekly, is_inactive=True))
        payload = self.payload(before)
        self.assertEqual(self.http('/api/order-calendar-event-remove', 'POST', json.dumps({**payload, 'period': 'week', 'date': '2026-10-26'}))[0], 400)
        self.assertEqual(self.store.get(self.path), before)
        status, _, body = self.http('/api/order-calendar-event-remove', 'POST', json.dumps(payload))
        self.assertEqual(status, 200, body)
        removed = json.loads(body)
        self.assertEqual(removed['calendar_events'], {})
        self.assertEqual(removed['calendar_inactive']['day'], [])
        for field in before.keys() - {'calendar_events', 'calendar_inactive', 'extra_blocks', 'revision'}:
            self.assertEqual(removed[field], before[field], field)
        self.assertEqual(self.http('/api/order-calendar-event-remove', 'POST', json.dumps(payload))[0], 409)
        undo = self.payload(removed, is_inactive=True)
        status, _, body = self.http('/api/order-calendar-event-restore', 'POST', json.dumps(undo))
        self.assertEqual(status, 200, body)
        restored = json.loads(body)
        self.assertEqual(restored['calendar_events'], before['calendar_events'])
        self.assertEqual(restored['calendar_inactive'], before['calendar_inactive'])
        self.assertEqual(self.http('/api/order-calendar-event-restore', 'POST', json.dumps(self.payload(restored, is_inactive=False)))[0], 400)
        self.assertEqual(self.store.get(self.path), restored)
        with self.store.connect() as db:
            history = [json.loads(row[0]) for row in db.execute("SELECT data FROM metadata_history WHERE entity='orders' AND identity=?", (before['id'],))]
        self.assertTrue(any(order_calendar.read(json.loads(row['extra_blocks'])) == before['calendar_events'] for row in history))
        unknown = {**before['extra_blocks'], order_calendar.BLOCK: '{"version":2,"events":{}}'}
        with self.assertRaises(ValueError):
            order_calendar.remove(unknown, payload['date'])

    def test_weekly_http_save_move_conflict_and_delete_keep_daily_data_and_sorting(self):
        daily = self.store.save_calendar_event(self.payload())
        data = self.payload(daily, period="week", date="2026-10-26", text="Закончить за неделю")
        status, _, body = self.http("/api/order-calendar-event", "POST", json.dumps(data))
        self.assertEqual(status, 200)
        weekly = json.loads(body)
        self.assertEqual(weekly["calendar_week_events"], {"2026-10-26": "Закончить за неделю"})
        for field in daily.keys() - {"calendar_week_events", "deadline_comments", "extra_blocks", "revision"}:
            self.assertEqual(weekly[field], daily[field], field)
        self.assertEqual(weekly["extra_blocks"][order_calendar.BLOCK], daily["extra_blocks"][order_calendar.BLOCK])
        self.assertEqual(self.http("/api/order-calendar-event", "POST", json.dumps(data))[0], 409)
        for changes in ({"date": "2026-10-27"}, {"period": "month"}, {"period": None}):
            invalid = {**self.payload(weekly, period="week", date="2026-10-26"), **changes}
            self.assertEqual(self.http("/api/order-calendar-event", "POST", json.dumps(invalid))[0], 400)
        status, _, body = self.http("/api/order-calendar-move", "POST", json.dumps(self.payload(weekly, period="week", date="2026-10-26", days=7)))
        self.assertEqual(status, 200)
        moved = json.loads(body)
        self.assertEqual(moved["calendar_week_events"], {"2026-11-02": "Закончить за неделю"})
        self.assertEqual(moved["calendar_events"], daily["calendar_events"])
        self.assertEqual(moved["deadline_weeks"], ["2026-10-26", "2026-11-02"])
        self.assertEqual(moved["updated"], daily["updated"])
        self.assertEqual(json.loads(self.http("/api/orders")[2])["orders"][0]["calendar_week_events"], moved["calendar_week_events"])
        restarted = OrderStore(self.root, manager.DATA_DIR, manager.STATUS_LABELS)
        self.assertEqual(restarted.get(self.path)["calendar_week_events"], moved["calendar_week_events"])
        removed = self.store.save_calendar_event(self.payload(moved, period="week", date="2026-11-02", text=""))
        self.assertEqual(removed["calendar_week_events"], moved["calendar_week_events"])
        self.assertEqual(removed["calendar_inactive"]["week"], ["2026-11-02"])
        self.assertEqual(removed["calendar_events"], daily["calendar_events"])

    def test_atomic_moves_keep_other_dates_fields_history_and_registration(self):
        saved = self.store.save_calendar_event(self.payload())
        occupied = self.store.save_calendar_event(self.payload(saved, date="2026-10-28", text="Другое событие"))
        with self.assertRaises(ValueError):
            self.store.move_calendar_event(self.payload(occupied, days=1))
        self.assertEqual(self.store.get(self.path), occupied)
        with self.store.connect() as db:
            history_count = db.execute("SELECT COUNT(*) FROM metadata_history WHERE entity='orders' AND identity=?", (self.order["id"],)).fetchone()[0]
        moved = self.store.move_calendar_event(self.payload(occupied, days=7))
        self.assertEqual(moved["calendar_events"], {"2026-10-28": "Другое событие", "2026-11-03": "Монтаж"})
        self.assertEqual(moved["revision"], occupied["revision"] + 1)
        for field in occupied.keys() - {"calendar_events", "deadline_weeks", "extra_blocks", "revision"}:
            self.assertEqual(moved[field], occupied[field], field)
        self.assertEqual(moved["deadline_weeks"], ["2026-10-26", "2026-11-02"])
        with self.store.connect() as db:
            history = [json.loads(row[0]) for row in db.execute("SELECT data FROM metadata_history WHERE entity='orders' AND identity=?", (self.order["id"],))]
        self.assertEqual(len(history), history_count + 1)
        self.assertTrue(any(order_calendar.read(json.loads(row["extra_blocks"])) == occupied["calendar_events"] for row in history))
        with self.assertRaises(ValueError):
            self.store.move_calendar_event(self.payload(moved, days=-7))
        self.assertEqual(self.store.get(self.path), moved)
        restored = self.store.move_calendar_event(self.payload(moved, date="2026-11-03", days=-7))
        self.assertEqual(restored["calendar_events"], occupied["calendar_events"])
        self.assertEqual(restored["deadline_weeks"], moved["deadline_weeks"])

    def test_unknown_deadlines_reject_cross_week_move_without_revision_or_history_change(self):
        saved = self.store.save_calendar_event(self.payload())
        with self.store.connect() as db:
            db.execute("UPDATE orders SET extra_blocks=?,revision=revision+1 WHERE path=?", (
                json.dumps({**saved["extra_blocks"], order_deadlines.BLOCK: '{"version":2,"weeks":[]}'}), self.path))
        before = self.store.get(self.path)
        with self.store.connect() as db:
            count = db.execute("SELECT COUNT(*) FROM metadata_history").fetchone()[0]
        status, _, body = self.http("/api/order-calendar-move", "POST", json.dumps(self.payload(before, days=7)))
        self.assertEqual(status, 400, body)
        self.assertEqual(self.store.get(self.path), before)
        with self.store.connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM metadata_history").fetchone()[0], count)

    def test_supplier_daily_and_weekly_moves_plan_destination_without_changing_other_orders(self):
        path = "# work/# glass/2026-10-20 - Стекло"
        self.folder(path)
        supplier = self.store.add(path, {"title": "Стекло", "extra_blocks": order_deadlines.write({}, "2026-10-26", True)})
        for period, source, target in (("day", "2026-10-27", "2026-11-03"), ("week", "2026-11-02", "2026-11-09")):
            with self.subTest(period=period):
                saved = self.store.save_calendar_event({"path": path, "id": supplier["id"], "revision": supplier["revision"],
                    "date": source, "text": "Получить стекло", "period": period})
                with patch.object(OrderStore, "target", side_effect=AssertionError("No folder reads")), \
                        patch("icloud_access.read_bytes", side_effect=AssertionError("No iCloud reads")):
                    status, _, body = self.http("/api/order-calendar-move", "POST", json.dumps({
                        "path": path, "id": saved["id"], "revision": saved["revision"], "date": source, "days": 7, "period": period}))
                self.assertEqual(status, 200, body)
                supplier = json.loads(body)
                self.assertEqual(supplier["revision"], saved["revision"] + 1)
                for field in saved.keys() - {"calendar_events", "calendar_week_events", "deadline_comments", "deadline_weeks", "extra_blocks", "revision"}:
                    self.assertEqual(supplier[field], saved[field], field)
                self.assertEqual(supplier["calendar_events" if period == "day" else "calendar_week_events"], {target: "Получить стекло"})
                listed = json.loads(self.http("/api/orders")[2])
                self.assertEqual([order["id"] for order in listed["orders"]], [self.order["id"]])
                self.assertEqual(listed["calendar_supplier_orders"][0]["deadline_weeks"], supplier["deadline_weeks"])
        self.assertEqual(supplier["deadline_weeks"], ["2026-10-26", "2026-11-02", "2026-11-09"])
        self.assertEqual(self.store.get(self.path), self.order)

    def test_http_move_rejects_stale_identity_and_unknown_data_without_cloud(self):
        saved = self.store.save_calendar_event(self.payload())
        self.root.rename(self.base / "offline")
        with patch.object(OrderStore, "target", side_effect=AssertionError("No folder reads")), \
                patch("icloud_access.read_bytes", side_effect=AssertionError("No originals")), \
                patch.object(manager, "schedule_order_sync") as schedule:
            status, _, body = self.http("/api/order-calendar-move", "POST", json.dumps(self.payload(saved, days=-1)))
            self.assertEqual(status, 200)
            moved = json.loads(body)
            self.assertEqual(moved["calendar_events"], {"2026-10-26": "Монтаж"})
            schedule.assert_called_once()
            for changes in ({}, {"id": "Чужой UUID"}):
                self.assertEqual(self.http("/api/order-calendar-move", "POST", json.dumps(self.payload(saved, days=1, **changes)))[0], 409)
            for changes in ({"revision": True}, {"days": True}, {"days": 2}, {"date": "2026-02-30"}):
                data = {**self.payload(moved, date="2026-10-26", days=1), **changes}
                self.assertEqual(self.http("/api/order-calendar-move", "POST", json.dumps(data))[0], 400)
        self.assertEqual(self.store.get(self.path), moved)
        unknown = '{"version":2,"events":{}}'
        with self.store.connect() as db:
            db.execute("UPDATE orders SET extra_blocks=?,revision=revision+1 WHERE path=?", (
                json.dumps({**moved["extra_blocks"], order_calendar.BLOCK: unknown}), self.path))
        record = self.store.get(self.path)
        with self.assertRaises(ValueError):
            self.store.move_calendar_event(self.payload(record, date="2026-10-26", days=1))
        self.assertEqual(self.store.get(self.path), record)

    def test_offline_partial_write_preserves_fields_sorting_history_and_restart(self):
        self.root.rename(self.base / "offline")
        with patch.object(OrderStore, "target", side_effect=AssertionError("No folder reads")), \
                patch("icloud_access.read_bytes", side_effect=AssertionError("No originals")):
            saved = self.store.save_calendar_event(self.payload(note="Не заменять", amount="999"))
            for field in self.order.keys() - {"calendar_events", "extra_blocks", "revision"}:
                self.assertEqual(saved[field], self.order[field], field)
            both = self.store.save_calendar_event(self.payload(saved, date="2026-10-28", text="Проверка"))
            removed = self.store.save_calendar_event(self.payload(both, text=""))
        self.assertEqual(removed["calendar_events"], both["calendar_events"])
        self.assertEqual(removed["calendar_inactive"]["day"], ["2026-10-27"])
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
