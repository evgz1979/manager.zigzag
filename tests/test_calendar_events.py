import json
import unittest
import uuid
from unittest.mock import patch

from calendar_events import CalendarEvents
import local_metadata
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

    def test_comments_round_trip_retry_conflict_and_legacy_edit(self):
        for period, day in [('day', '2026-12-31'), ('week', '2026-12-28')]:
            with self.subTest(period=period):
                payload = self.payload(period=period, date=day, comment='  Детали <b>без HTML</b>\r\nВторая строка 🧵  ')
                status, _, body = self.http('/api/calendar-event', 'POST', json.dumps(payload))
                self.assertEqual(status, 200, body)
                saved = json.loads(body)
                self.assertEqual(saved['comment'], 'Детали <b>без HTML</b>\nВторая строка 🧵')
                self.assertEqual(self.events.save(payload), saved)
                with self.assertRaises(OrderConflict):
                    self.events.save({**payload, 'comment': 'Другой комментарий'})
                changed = self.events.save(self.payload(saved, comment='Изменённый'))
                with self.assertRaises(OrderConflict):
                    self.events.save(self.payload(saved, comment='Устаревший'))
                legacy = self.events.save(self.payload(changed, text='Новое название'))
                self.assertEqual(legacy['comment'], 'Изменённый')
                self.assertIn(legacy, json.loads(self.http('/api/orders')[2])['calendar_events'])
                cleared = self.events.save(self.payload(legacy, comment='  \n '))
                self.assertEqual(cleared['comment'], '')
                with self.store.connect() as db:
                    history = [json.loads(row[0]) for row in db.execute("SELECT data FROM metadata_history WHERE entity='calendar_events' AND identity=?", (saved['id'],))]
                    self.assertEqual(db.execute("SELECT value FROM metadata_settings WHERE key='calendar_event_comments'").fetchone()[0], '1')
                self.assertTrue(any(row['comment'] == saved['comment'] for row in history))
                self.assertTrue(any(row['comment'] == 'Изменённый' for row in history))

    def test_comments_survive_flags_move_delete_restore_and_restart(self):
        saved = self.events.save(self.payload(comment='Сохранить детали'))
        for operation, changes in [(self.events.color, {'color': 'blue'}),
                                   (self.events.set_completed, {'is_completed': True}),
                                   (self.events.set_inactive, {'is_inactive': True}),
                                   (self.events.set_trip, {'is_trip': True}),
                                   (self.events.move, {'days': 3})]:
            saved = operation({**self.payload(saved), **changes})
            self.assertEqual(saved['comment'], 'Сохранить детали')
        deleted = self.events.set_deleted(self.payload(saved), True)
        restored = self.events.set_deleted(self.payload(deleted), False)
        self.assertEqual(CalendarEvents(manager.order_store()).get(saved['id'])['comment'], 'Сохранить детали')
        self.assertEqual(restored['comment'], deleted['comment'])

    def test_invalid_comments_leave_record_unchanged(self):
        saved = self.events.save(self.payload(comment='Исходный'))
        for invalid in (None, True, 5, [], {}, 'x' * 10001, 'a\x00b'):
            with self.subTest(invalid=repr(invalid)[:60]), self.assertRaises(ValueError):
                self.events.save(self.payload(saved, comment=invalid))
        self.assertEqual(self.events.get(saved['id']), saved)
        with self.store.connect() as db:
            db.execute("UPDATE calendar_events SET comment=? WHERE id=?", ('x' * 10001, saved['id']))
        unknown = self.events.get(saved['id'])
        with self.assertRaises(ValueError):
            self.events.save(self.payload(unknown, comment='Не заменять'))
        self.assertEqual(self.events.get(saved['id']), unknown)

    def test_comment_column_upgrade_preserves_events_and_updates_audit(self):
        identity = str(uuid.uuid4())
        with self.store.connect() as db:
            db.execute("CREATE TABLE calendar_events (id TEXT PRIMARY KEY,version INTEGER,period TEXT,date TEXT,text TEXT,revision INTEGER,created REAL,updated REAL,deleted INTEGER,color TEXT,is_inactive INTEGER,is_completed INTEGER,is_trip INTEGER)")
            db.execute("INSERT INTO calendar_events VALUES (?,1,'day','2026-12-31','Прежнее',7,1,2,0,'blue',0,1,1)", (identity,))
            local_metadata.audit(db, 'calendar_events')
        old = self.events.get(identity)
        self.assertEqual((old['comment'], old['revision'], old['text'], old['is_trip']), ('', 7, 'Прежнее', 1))
        changed = self.events.save(self.payload(old, comment='Добавлено'))
        self.events.save(self.payload(changed, comment='Правка'))
        with self.store.connect() as db:
            history = [json.loads(row[0]) for row in db.execute("SELECT data FROM metadata_history WHERE entity='calendar_events'")]
        self.assertEqual([row['comment'] for row in history], ['', 'Добавлено'])

    def test_daily_soft_delete_and_undo_reject_stale_and_unknown_events(self):
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
        with self.store.connect() as db:
            history = [json.loads(row[0]) for row in db.execute("SELECT data FROM metadata_history WHERE entity='calendar_events'")]
            db.execute('UPDATE calendar_events SET version=2 WHERE id=?', (restored['id'],))
        self.assertTrue(any(row['id'] == saved['id'] and row['deleted'] == 1 for row in history))
        with self.assertRaises(ValueError):
            self.events.set_deleted(self.payload(restored), True)

    def test_weekly_soft_delete_and_undo_preserve_comment_flags_other_events_and_history(self):
        original = self.payload(period='week', date='2026-12-28', text='План недели', comment='Детали\nНе потерять')
        saved = self.events.save(original)
        saved = self.events.color({**self.payload(saved), 'color': 'purple'})
        saved = self.events.set_completed({**self.payload(saved), 'is_completed': True})
        saved = self.events.set_inactive({**self.payload(saved), 'is_inactive': True})
        saved = self.events.set_trip({**self.payload(saved), 'is_trip': True})
        other = self.events.save(self.payload(period='week', date=saved['date'], text='Другой план'))
        status, _, body = self.http('/api/calendar-event-remove', 'POST', json.dumps(self.payload(saved)))
        self.assertEqual(status, 200, body)
        deleted = json.loads(body)
        self.assertEqual(deleted['deleted'], 1)
        self.assertEqual(deleted['revision'], saved['revision'] + 1)
        for field in saved.keys() - {'deleted', 'revision', 'updated'}:
            self.assertEqual(deleted[field], saved[field], field)
        self.assertEqual(self.events.list(), [other])
        self.assertEqual(self.events.get(other['id']), other)
        self.assertEqual(self.http('/api/calendar-event-remove', 'POST', json.dumps(self.payload(saved)))[0], 409)
        self.assertEqual(self.http('/api/calendar-event-restore', 'POST', json.dumps(self.payload(saved)))[0], 409)
        with self.assertRaises(OrderConflict):
            self.events.save(original)
        status, _, body = self.http('/api/calendar-event-restore', 'POST', json.dumps(self.payload(deleted)))
        self.assertEqual(status, 200, body)
        restored = json.loads(body)
        self.assertEqual(restored['deleted'], 0)
        self.assertEqual(restored['revision'], deleted['revision'] + 1)
        for field in saved.keys() - {'revision', 'updated'}:
            self.assertEqual(restored[field], saved[field], field)
        self.assertEqual(CalendarEvents(manager.order_store()).get(restored['id']), restored)
        with self.store.connect() as db:
            history = [json.loads(row[0]) for row in db.execute("SELECT data FROM metadata_history WHERE entity='calendar_events' AND identity=?", (saved['id'],))]
        self.assertTrue(any(row['deleted'] == 1 and row['period'] == 'week' and row['comment'] == saved['comment'] for row in history))

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

    def test_next_seven_days_move_once_preserving_flags_and_reject_stale_requests(self):
        for days in range(1, 8):
            with self.subTest(days=days):
                saved = self.events.save(self.payload(date='2026-12-31'))
                saved = self.events.color({**self.payload(saved), 'color': 'purple'})
                saved = self.events.set_completed({**self.payload(saved), 'is_completed': True})
                saved = self.events.set_trip({**self.payload(saved), 'is_trip': True})
                saved = self.events.set_inactive({**self.payload(saved), 'is_inactive': True})
                request = {**self.payload(saved), 'days': days}
                moved = self.events.move(request)
                self.assertEqual(moved['date'], f'2027-01-{days:02d}')
                self.assertEqual(moved['revision'], saved['revision'] + 1)
                for field in saved.keys() - {'date', 'revision', 'updated'}:
                    self.assertEqual(moved[field], saved[field], field)
                with self.assertRaises(OrderConflict):
                    self.events.move(request)
                for invalid in (-2, 0, 8, True, '2'):
                    with self.assertRaises(ValueError):
                        self.events.move({**self.payload(moved), 'days': invalid})
                self.assertEqual(self.events.get(moved['id']), moved)

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
