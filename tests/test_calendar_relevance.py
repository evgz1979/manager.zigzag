import json
import unittest
import uuid
from unittest.mock import patch

import calendar_events
import local_metadata
import order_calendar
from orders import OrderConflict
import invoices
import test_server as fixtures

manager = fixtures.manager


class CalendarRelevanceTests(unittest.TestCase):
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    path = 'Клиент/Объект/2026-10-25 - Заказ'

    def setUp(self):
        fixtures.ManagerTests.setUp(self)
        mode = patch.object(manager, 'DATABASE_ONLY', True); mode.start(); self.patches.append(mode)
        self.folder(self.path)
        self.store = manager.order_store()
        self.order = self.store.add(self.path, {'status': 'process', 'financial_status': 'partial', 'note': 'Заметка',
                                              'amount': 10000, 'paid': 3000, 'extra_blocks': {'Особое': 'Сохранить'}})

    def payload(self, record, **changes):
        return {'path': record['path'], 'id': record['id'], 'revision': record['revision'],
                'date': '2026-10-26', 'period': 'day', **changes}

    def test_order_daily_weekly_toggle_move_and_edit_preserve_every_text_and_sorting(self):
        daily = self.store.save_calendar_event(self.payload(self.order, text='Монтаж'))
        weekly = self.store.save_calendar_event(self.payload(daily, period='week', text='План недели'))
        inactive = self.store.save_calendar_inactive(self.payload(weekly, is_inactive=True))
        for field in weekly.keys()-{'calendar_inactive', 'extra_blocks', 'revision'}:
            self.assertEqual(inactive[field], weekly[field], field)
        self.assertEqual(inactive['calendar_inactive'], {'day': ['2026-10-26'], 'week': []})
        moved = self.store.move_calendar_event(self.payload(inactive, days=1))
        self.assertEqual(moved['calendar_inactive']['day'], ['2026-10-27'])
        edited = self.store.save_calendar_event(self.payload(moved, date='2026-10-27', text='Монтаж утром'))
        self.assertEqual(edited['calendar_inactive']['day'], ['2026-10-27'])
        restored = self.store.save_calendar_inactive(self.payload(edited, date='2026-10-27', is_inactive=False))
        self.assertEqual(restored['calendar_inactive']['day'], [])
        week_off = self.store.save_calendar_inactive(self.payload(restored, period='week', is_inactive=True))
        week_moved = self.store.move_calendar_event(self.payload(week_off, period='week', days=7))
        self.assertEqual(week_moved['calendar_inactive']['week'], ['2026-11-02'])
        self.assertEqual(week_moved['deadline_comments'], {'2026-11-02': 'План недели'})
        self.assertEqual(week_moved['updated'], self.order['updated'])
        with self.store.connect() as db:
            old = [json.loads(row[0]) for row in db.execute("SELECT data FROM metadata_history WHERE entity='orders' AND identity=?", (self.order['id'],))]
        self.assertTrue(any(json.loads(row['extra_blocks']).get(order_calendar.INACTIVE_BLOCK) == inactive['extra_blocks'][order_calendar.INACTIVE_BLOCK] for row in old))

    def test_http_versions_unknown_flags_missing_event_and_no_cloud_access(self):
        saved = self.store.save_calendar_event(self.payload(self.order, text='Событие'))
        with patch('icloud_access.read_bytes', side_effect=AssertionError('No iCloud reads')):
            status, _, body = self.http('/api/order-calendar-inactive', 'POST', json.dumps(self.payload(saved, is_inactive=True)))
            self.assertEqual(status, 200)
            off = json.loads(body)
            self.assertEqual(self.http('/api/order-calendar-inactive', 'POST', json.dumps(self.payload(saved, is_inactive=False)))[0], 409)
            for changes in [{'is_inactive': 'true'}, {'id': 'another'}, {'revision': True}, {'date': '2026-10-27'}]:
                code = self.http('/api/order-calendar-inactive', 'POST', json.dumps({**self.payload(off, is_inactive=True), **changes}))[0]
                self.assertIn(code, (400, 409))
        blocks = {**off['extra_blocks'], order_calendar.INACTIVE_BLOCK: '{"version":2,"day":[],"week":[]}'}
        with self.store.connect() as db:
            db.execute('UPDATE orders SET extra_blocks=? WHERE id=?', (json.dumps(blocks), off['id']))
        unknown = self.store.get(self.path)
        self.assertIsNone(unknown['calendar_inactive'])
        with self.assertRaises(ValueError):self.store.save_calendar_inactive(self.payload(unknown, is_inactive=False))
        with self.assertRaises(ValueError):self.store.move_calendar_event(self.payload(unknown, days=1))
        self.assertEqual(self.store.get(self.path), unknown)

    def test_free_event_toggle_preserves_color_and_legacy_clear_keeps_event_visible(self):
        events = calendar_events.CalendarEvents(self.store)
        first = events.save({'id': str(uuid.uuid4()), 'revision': 0, 'date': '2026-10-26', 'period': 'week', 'text': 'Свободное'})
        colored = events.color({**first, 'color': 'purple'})
        off = events.set_inactive({**colored, 'is_inactive': True})
        self.assertEqual(off['color'], 'purple'); self.assertEqual(off['text'], 'Свободное'); self.assertEqual(off['deleted'], 0)
        moved = events.move({**off, 'days': 7})
        self.assertEqual(moved['is_inactive'], 1)
        on = events.set_inactive({**moved, 'is_inactive': False})
        edited = events.save({**on, 'text': 'Новый текст'})
        clear = events.save({**edited, 'text': ''})
        self.assertEqual(clear['text'], edited['text']); self.assertEqual(clear['is_inactive'], 1)
        self.assertEqual(events.list(), [clear])
        with self.assertRaises(OrderConflict):events.set_inactive({**edited, 'is_inactive': False})
        with events.connect() as db:
            history = [json.loads(row[0]) for row in db.execute("SELECT data FROM metadata_history WHERE entity='calendar_events'")]
        self.assertTrue(any(row['is_inactive'] == 1 and row['text'] == 'Свободное' for row in history))

    def test_existing_free_table_adds_active_default_and_audits_new_flag(self):
        with self.store.connect() as db:
            db.execute("CREATE TABLE calendar_events (id TEXT PRIMARY KEY,version INTEGER,period TEXT,date TEXT,text TEXT,revision INTEGER,created REAL,updated REAL,deleted INTEGER,color TEXT)")
            db.execute("INSERT INTO calendar_events VALUES ('a',1,'day','2026-10-26','Прежнее',1,1,1,0,'blue')")
            local_metadata.audit(db, 'calendar_events')
        events = calendar_events.CalendarEvents(self.store)
        first = events.list()[0]
        self.assertEqual(first['is_inactive'], 0); self.assertEqual(first['text'], 'Прежнее')
        with events.connect() as db:
            db.execute("UPDATE calendar_events SET is_inactive=1 WHERE id='a'")
        with events.connect() as db:
            previous = json.loads(db.execute("SELECT data FROM metadata_history WHERE entity='calendar_events' ORDER BY seq DESC LIMIT 1").fetchone()[0])
        self.assertEqual(previous['is_inactive'], 0)

    def test_invoice_and_payment_plans_keep_numbers_finances_and_plan_data(self):
        store = manager.invoice_store()
        for operation in ['invoice', 'incoming', 'outgoing']:
            plan = store.plan({'path': self.path, 'id': str(uuid.uuid4()), 'date': '2026-10-26', 'operation': operation, 'amount': '1200'})
            off = store.save_plan_calendar_inactive({**plan, 'is_inactive': True})
            self.assertEqual({k:v for k,v in off['data'].items() if k!='_calendar_inactive'}, plan['data'])
            shown = next(p for p in store.calendar_plans([self.order]) if p['id']==plan['id'])
            self.assertTrue(shown['is_inactive']); self.assertEqual(shown['revision'], off['revision'])
            self.assertEqual(self.store.get(self.path), self.order)
            with self.assertRaises(invoices.InvoiceConflict):store.save_plan_calendar_inactive({**plan, 'is_inactive': False})
            on = store.save_plan_calendar_inactive({**off, 'is_inactive': False})
            self.assertFalse(on['data']['_calendar_inactive'])
        with store.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM invoice_sequences').fetchone()[0], 0)
