import json
import unittest
import uuid
from unittest.mock import patch

from calendar_events import CalendarEvents
from orders import OrderConflict
import test_server as fixtures

manager = fixtures.manager


class FreeCalendarTests(unittest.TestCase):
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http

    def setUp(self):
        fixtures.ManagerTests.setUp(self)
        mode = patch.object(manager, 'DATABASE_ONLY', True)
        mode.start()
        self.patches.append(mode)
        self.store = manager.order_store()
        self.events = CalendarEvents(self.store)

    def payload(self, record=None, **changes):
        return {'id': record['id'] if record else str(uuid.uuid4()),
                'revision': record['revision'] if record else 0,
                'date': record['date'] if record else '2026-12-31',
                'period': record['period'] if record else 'day', 'text': '  Позвонить <клиенту>  ', **changes}

    def test_daily_soft_delete_and_undo_reject_weekly_stale_and_unknown_events(self):
        original = self.payload()
        saved = self.events.save(original)
        colored = self.events.color({**self.payload(saved), 'color': 'blue'})
        status, _, body = self.http('/api/calendar-event-remove', 'POST', json.dumps(self.payload(colored)))
        self.assertEqual(status, 200, body)
        deleted = json.loads(body)
        self.assertEqual(deleted['deleted'], 1)
        self.assertEqual((deleted['text'], deleted['color']), (colored['text'], 'blue'))
        self.assertEqual(self.events.list(), [])
        for payload in (original, self.payload(colored), self.payload(deleted)):
            with self.assertRaises(OrderConflict):
                self.events.save(payload)
        self.assertEqual(self.http('/api/calendar-event-restore', 'POST', json.dumps(self.payload(colored)))[0], 409)
        status, _, body = self.http('/api/calendar-event-restore', 'POST', json.dumps(self.payload(deleted)))
        self.assertEqual(status, 200, body)
        restored = json.loads(body)
        self.assertEqual(restored['deleted'], 0)
        self.assertEqual(self.events.list(), [restored])
        week = self.events.save(self.payload(period='week', date='2026-12-28'))
        for route in ('/api/calendar-event-remove', '/api/calendar-event-restore'):
            self.assertEqual(self.http(route, 'POST', json.dumps(self.payload(week, period='day')))[0], 400)
        self.assertEqual(self.events.get(week['id']), week)
        with self.store.connect() as db:
            history = [json.loads(row[0]) for row in db.execute("SELECT data FROM metadata_history WHERE entity='calendar_events'")]
            db.execute('UPDATE calendar_events SET version=2 WHERE id=?', (restored['id'],))
        self.assertTrue(any(row['id'] == saved['id'] and row['deleted'] == 1 for row in history))
        with self.assertRaises(ValueError):
            self.events.set_deleted(self.payload(restored), True)

    def test_multiple_events_same_date_week_and_restart_are_independent(self):
        first = self.events.save(self.payload())
        second = self.events.save(self.payload(text='Встреча'))
        week = self.events.save(self.payload(date='2026-12-28', period='week', text='План недели'))
        changed = self.events.save(self.payload(first, text='Новое название'))
        other_changed = self.events.color({'id': second['id'], 'revision': second['revision'], 'color': 'blue'})
        restarted = CalendarEvents(manager.order_store()).list()
        self.assertEqual({r['id'] for r in restarted}, {first['id'], second['id'], week['id']})
        self.assertEqual(self.events.get(first['id'])['text'], changed['text'])
        self.assertEqual(self.events.get(second['id'])['color'], other_changed['color'])
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM orders').fetchone()[0], 0)
            history = [json.loads(row[0]) for row in db.execute("SELECT data FROM metadata_history WHERE entity='calendar_events'")]
        self.assertTrue(any(row['text'] == first['text'] and row['id'] == first['id'] for row in history))
        self.assertTrue(any(row['color'] == 'gray' and row['id'] == second['id'] for row in history))

    def test_idempotent_creation_and_stale_save_color_move_delete_conflict(self):
        data = self.payload()
        first = self.events.save(data)
        self.assertEqual(self.events.save(data), first)
        colored = self.events.color({'id': first['id'], 'revision': first['revision'], 'color': 'red'})
        for operation, payload in [(self.events.save, self.payload(first)),
                                   (self.events.save, data),
                                   (self.events.save, self.payload(first, text='')),
                                   (self.events.move, {**self.payload(first), 'days': 1}),
                                   (self.events.color, {**self.payload(first), 'color': 'green'})]:
            with self.subTest(operation=operation), self.assertRaises(OrderConflict):
                operation(payload)
        self.assertEqual(self.events.get(first['id']), colored)
        deleted = self.events.save(self.payload(colored, text=''))
        self.assertFalse(deleted['deleted'])
        self.assertEqual(deleted['is_inactive'], 1)
        self.assertEqual(self.events.list(), [deleted])
        self.assertEqual(deleted['text'], colored['text'])
        edited = self.events.save(self.payload(deleted, text='Правка неактуального'))
        self.assertEqual(edited['is_inactive'], 1)
        with self.assertRaises(OrderConflict):
            self.events.save(data)

    def test_moves_keep_color_and_text_and_allow_multiple_on_target_date(self):
        source = self.events.save(self.payload())
        colored = self.events.color({**self.payload(source), 'color': 'purple'})
        occupied = self.events.save(self.payload(date='2027-01-01', text='Другой план'))
        moved = self.events.move({**self.payload(colored), 'days': 1})
        self.assertEqual(moved['date'], '2027-01-01')
        self.assertEqual(moved['color'], 'purple')
        self.assertEqual(moved['text'], source['text'])
        self.assertEqual(self.events.get(occupied['id']), occupied)
        weekly = self.events.save(self.payload(period='week', date='2026-12-28'))
        with self.assertRaises(ValueError):
            self.events.move({**self.payload(weekly), 'days': 1})
        next_week = self.events.move({**self.payload(weekly), 'days': 7})
        self.assertEqual(next_week['date'], '2027-01-04')
        leap = self.events.save(self.payload(date='2028-02-28'))
        self.assertEqual(self.events.move({**self.payload(leap), 'days': 1})['date'], '2028-02-29')

    def test_validation_and_unknown_formats_leave_records_unchanged(self):
        saved = self.events.save(self.payload())
        for changes in [{'revision': None}, {'revision': True}, {'id': '../outside'}, {'period': 'month'},
                        {'period': 'week', 'date': '2026-12-31'}, {'date': '2026-02-30'},
                        {'text': 'x'*1001}, {'text': 'a\nb'}, {'text': '   '}]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.events.save(self.payload(saved, **changes))
        with self.assertRaises(ValueError):
            self.events.color({**self.payload(saved), 'color': '<red>'})
        self.assertEqual(self.events.get(saved['id']), saved)
        with self.store.connect() as db:
            db.execute('UPDATE calendar_events SET version=2 WHERE id=?', (saved['id'],))
        unknown = self.events.get(saved['id'])
        for operation, data in [(self.events.save, self.payload(unknown)),
                                (self.events.move, {**self.payload(unknown), 'days': 1}),
                                (self.events.color, {**self.payload(unknown), 'color': 'blue'})]:
            with self.assertRaises(ValueError):
                operation(data)
        self.assertEqual(self.events.get(saved['id']), unknown)

    def test_http_save_color_move_delete_and_main_poll_without_document_reads(self):
        self.folder('Клиент/2026-10-25 - Обычный заказ')
        order = self.store.add('Клиент/2026-10-25 - Обычный заказ', {'title': 'Обычный заказ', 'note': 'Сохранить'})
        with patch.object(type(self.store), 'target', side_effect=AssertionError('No folder reads')), \
                patch('icloud_access.read_bytes', side_effect=AssertionError('No iCloud reads')):
            status, _, body = self.http('/api/calendar-event', 'POST', json.dumps(self.payload()))
            self.assertEqual(status, 200)
            saved = json.loads(body)
            self.assertEqual(json.loads(self.http('/api/calendar-event?id='+saved['id'])[2]), saved)
            colored = json.loads(self.http('/api/calendar-color', 'POST', json.dumps({**self.payload(saved), 'color': 'orange'}))[2])
            status, _, body = self.http('/api/calendar-move', 'POST', json.dumps({**self.payload(colored), 'days': 7}))
            self.assertEqual(status, 200)
            moved = json.loads(body)
            listing = json.loads(self.http('/api/orders')[2])
            self.assertEqual(listing['calendar_events'], [moved])
            self.assertEqual([r['id'] for r in listing['orders']], [order['id']])
            self.assertEqual(self.store.get(order['path']), order)
            self.assertEqual(self.http('/api/calendar-event', 'POST', json.dumps(self.payload(saved)))[0], 409)
            self.assertEqual(self.http('/api/calendar-color', 'POST', json.dumps({**self.payload(moved), 'color': False}))[0], 400)
            self.assertEqual(self.http('/api/calendar-event', 'POST', json.dumps(self.payload(moved, text='')))[0], 200)
            listed = json.loads(self.http('/api/orders')[2])['calendar_events']
            self.assertEqual(len(listed), 1)
            self.assertEqual(listed[0]['is_inactive'], 1)
            self.assertEqual(listed[0]['text'], moved['text'])
