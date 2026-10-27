import json
import unittest
import uuid
from unittest.mock import patch

import calendar_events
import invoices
import local_metadata
import order_calendar
import test_calendar_relevance as fixtures
from orders import OrderConflict

manager = fixtures.manager


class CalendarCompletionTests(unittest.TestCase):
    setUp = fixtures.CalendarRelevanceTests.setUp
    tearDown = fixtures.CalendarRelevanceTests.tearDown
    folder = fixtures.CalendarRelevanceTests.folder
    file = fixtures.CalendarRelevanceTests.file
    http = fixtures.CalendarRelevanceTests.http
    payload = fixtures.CalendarRelevanceTests.payload
    path = fixtures.CalendarRelevanceTests.path

    def test_order_flags_independent_and_preserved_by_edit_move_delete_restore(self):
        for path in [self.path, '# work/# glass/2026-10-25 - Поставщику']:
            with self.subTest(path=path):
                if path != self.path:
                    self.folder(path)
                    initial = self.store.add(path, {'note': 'Поставщик'})
                else:
                    initial = self.order
                daily = self.store.save_calendar_event(self.payload(initial, text='Монтаж'))
                weekly = self.store.save_calendar_event(self.payload(daily, period='week', text='На неделю'))
                colored = self.store.save_calendar_color(self.payload(weekly, color='purple')) if path == self.path else weekly
                inactive = self.store.save_calendar_inactive(self.payload(colored, is_inactive=True))
                done = self.store.save_calendar_completed(self.payload(inactive, is_completed=True))
                for field in inactive.keys() - {'revision', 'extra_blocks', 'calendar_completed'}:
                    self.assertEqual(done[field], inactive[field], field)
                moved = self.store.move_calendar_event(self.payload(done, days=1))
                edited = self.store.save_calendar_event(self.payload(moved, date='2026-10-27', text='Монтаж утром'))
                self.assertEqual(edited['calendar_completed'], {'day': ['2026-10-27'], 'week': []})
                self.assertEqual(edited['calendar_inactive']['day'], ['2026-10-27'])
                deleted = self.store.remove_calendar_event(self.payload(edited, date='2026-10-27'))
                self.assertEqual(deleted['calendar_completed']['day'], [])
                restored = self.store.restore_calendar_event(self.payload(deleted, date='2026-10-27', text='Монтаж утром', is_inactive=True, is_completed=True, color='purple' if path == self.path else None))
                self.assertEqual(restored['calendar_completed']['day'], ['2026-10-27'])
                active = self.store.save_calendar_completed(self.payload(restored, date='2026-10-27', is_completed=False))
                self.assertEqual(active['calendar_inactive']['day'], ['2026-10-27'])
                if path == self.path:
                    self.assertEqual(active['calendar_colors']['day']['2026-10-27'], 'purple')
                week_done = self.store.save_calendar_completed(self.payload(active, period='week', is_completed=True))
                week_moved = self.store.move_calendar_event(self.payload(week_done, period='week', days=7))
                self.assertEqual(week_moved['calendar_completed']['week'], ['2026-11-02'])
                self.assertIn('2026-11-02', week_moved['deadline_weeks'])
                self.assertEqual(week_moved['updated'], initial['updated'])
        with self.store.connect() as db:
            history = [json.loads(row[0]) for row in db.execute("SELECT data FROM metadata_history WHERE entity='orders'")]
        self.assertTrue(any(order_calendar.COMPLETED_BLOCK in json.loads(row['extra_blocks']) for row in history))

    def test_order_http_conflicts_validation_unknown_format_without_cloud(self):
        event = self.store.save_calendar_event(self.payload(self.order, text='Событие'))
        with patch('icloud_access.read_bytes', side_effect=AssertionError('No cloud reads')):
            status, _, body = self.http('/api/order-calendar-completed', 'POST', json.dumps(self.payload(event, is_completed=True)))
            self.assertEqual(status, 200)
            done = json.loads(body)
            self.assertEqual(self.http('/api/order-calendar-completed', 'POST', json.dumps(self.payload(event, is_completed=False)))[0], 409)
            for changes in [{'is_completed': 'true'}, {'is_completed': 1}, {'id': 'wrong'}, {'revision': True}, {'date': '2026-10-27'}, {'period': 'unknown'}]:
                code = self.http('/api/order-calendar-completed', 'POST', json.dumps({**self.payload(done, is_completed=True), **changes}))[0]
                self.assertIn(code, (400, 409))
                self.assertEqual(self.store.get(self.path), done)
        blocks = {**done['extra_blocks'], order_calendar.COMPLETED_BLOCK: '{"version":2,"day":[],"week":[]}'}
        with self.store.connect() as db:
            db.execute('UPDATE orders SET extra_blocks=? WHERE id=?', (json.dumps(blocks), done['id']))
        unknown = self.store.get(self.path)
        self.assertIsNone(unknown['calendar_completed'])
        with self.assertRaises(ValueError): self.store.save_calendar_completed(self.payload(unknown, is_completed=False))
        with self.assertRaises(ValueError): self.store.move_calendar_event(self.payload(unknown, days=1))
        with self.assertRaises(ValueError): self.store.remove_calendar_event(self.payload(unknown))
        self.assertEqual(self.store.get(self.path), unknown)

    def test_free_migration_audit_and_flag_lifecycle(self):
        identity = str(uuid.uuid4())
        with self.store.connect() as db:
            db.execute("CREATE TABLE calendar_events (id TEXT PRIMARY KEY,version INTEGER,period TEXT,date TEXT,text TEXT,revision INTEGER,created REAL,updated REAL,deleted INTEGER,color TEXT DEFAULT 'gray',is_inactive INTEGER DEFAULT 0)")
            db.execute("INSERT INTO calendar_events VALUES (?,1,'day','2026-10-26','Прежнее',1,1,1,0,'blue',1)", (identity,))
            local_metadata.audit(db, 'calendar_events')
        events = calendar_events.CalendarEvents(self.store)
        first = events.list()[0]
        self.assertEqual(first['is_completed'], 0)
        status, _, body = self.http('/api/calendar-completed', 'POST', json.dumps({**first, 'is_completed': True}))
        self.assertEqual(status, 200)
        done = json.loads(body)
        self.assertEqual(done['is_inactive'], 1)
        edited = events.save({**done, 'text': 'Правка'})
        moved = events.move({**edited, 'days': 1})
        deleted = events.set_deleted(moved, True)
        restored = events.set_deleted(deleted, False)
        self.assertEqual(restored['is_completed'], 1)
        self.assertEqual(restored['color'], 'blue')
        self.assertEqual(restored['is_inactive'], 1)
        off = events.set_completed({**restored, 'is_completed': False})
        self.assertEqual(off['is_inactive'], 1)
        with self.assertRaises(OrderConflict): events.set_completed({**restored, 'is_completed': True})
        with self.assertRaises(ValueError): events.set_completed({**off, 'is_completed': 1})
        with events.connect() as db:
            history = [json.loads(row[0]) for row in db.execute("SELECT data FROM metadata_history WHERE entity='calendar_events' ORDER BY seq")]
        self.assertEqual(history[0]['is_completed'], 0)
        self.assertTrue(any(row['is_completed'] == 1 for row in history))
        weekly = events.save({'id': str(uuid.uuid4()), 'revision': 0, 'date': '2026-10-26', 'period': 'week', 'text': 'Неделя'})
        weekly = events.set_completed({**weekly, 'is_completed': True})
        self.assertEqual(events.move({**weekly, 'days': 7})['is_completed'], 1)

    def test_plans_day_week_incoming_outgoing_and_invoice_preserve_data_finances(self):
        store = manager.invoice_store()
        for operation, path in [('invoice', self.path), ('incoming', self.path), ('outgoing', self.path), ('incoming', ''), ('outgoing', '')]:
            for period in ['day', 'week']:
                plan = store.plan({'path': path, 'id': str(uuid.uuid4()), 'date': '2026-10-26', 'period': period, 'operation': operation, 'amount': '1200', 'text': 'Комментарий'})
                inactive = store.save_plan_calendar_inactive({**plan, 'is_inactive': True})
                status, _, body = self.http('/api/invoice-plan-calendar-completed', 'POST', json.dumps({**inactive, 'is_completed': True}))
                self.assertEqual(status, 200, body)
                done = json.loads(body)
                self.assertEqual({k:v for k,v in done['data'].items() if k != '_calendar_completed'}, inactive['data'])
                shown = next(p for p in store.calendar_plans([self.order]) if p['id'] == plan['id'])
                self.assertTrue(shown['is_completed'])
                moved = store.move_calendar_plan({**done, 'date': '2026-10-26', 'period': period, 'days': 7})
                self.assertTrue(moved['data']['_calendar_completed'])
                off = store.save_plan_calendar_completed({**moved, 'is_completed': False})
                self.assertTrue(off['data']['_calendar_inactive'])
                with self.assertRaises(invoices.InvoiceConflict): store.save_plan_calendar_completed({**done, 'is_completed': False})
                with self.assertRaises(ValueError): store.save_plan_calendar_completed({**off, 'is_completed': 'true'})
        self.assertEqual(self.store.get(self.path), self.order)
        with store.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM invoice_sequences').fetchone()[0], 0)
            history = [json.loads(row[0]) for row in db.execute('SELECT data FROM invoice_history')]
            self.assertTrue(any(row.get('_calendar_completed') is True for row in history))
