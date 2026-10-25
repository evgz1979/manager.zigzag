import json
import unittest
from unittest.mock import patch

import order_calendar
from orders import OrderStore
import test_server as fixtures

manager = fixtures.manager


class OrderCalendarColorTests(unittest.TestCase):
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    path = 'Клиент/Объект/2026-10-25 - Заказ'

    def setUp(self):
        fixtures.ManagerTests.setUp(self)
        mode = patch.object(manager, 'DATABASE_ONLY', True)
        mode.start(); self.patches.append(mode)
        self.folder(self.path)
        self.store = manager.order_store()
        self.order = self.store.add(self.path, {'status': 'process', 'financial_status': 'partial',
            'amount': 10000, 'costs': 2000, 'paid': 3000, 'note': 'Заметка',
            'extra_blocks': {'Особое': 'Сохранить', 'Задачи': '- [ ] Позвонить'}})

    def payload(self, record, **changes):
        return {'path': record['path'], 'id': record['id'], 'revision': record['revision'],
                'date': '2026-10-26', 'period': 'day', **changes}

    def test_color_http_is_partial_versioned_persistent_and_audited_without_cloud(self):
        saved = self.store.save_calendar_event(self.payload(self.order, text='Монтаж'))
        with patch('icloud_access.read_bytes', side_effect=AssertionError('No iCloud reads')):
            status, _, body = self.http('/api/order-calendar-color', 'POST', json.dumps(self.payload(saved, color='blue')))
        self.assertEqual(status, 200, body)
        colored = json.loads(body)
        self.assertEqual(colored['calendar_colors'], {'day': {'2026-10-26': 'blue'}, 'week': {}})
        for field in saved.keys() - {'calendar_colors', 'extra_blocks', 'revision'}:
            self.assertEqual(colored[field], saved[field], field)
        self.assertEqual(colored['revision'], saved['revision'] + 1)
        for key, value in saved['extra_blocks'].items():
            self.assertEqual(colored['extra_blocks'][key], value)
        self.assertEqual(self.http('/api/order-calendar-color', 'POST', json.dumps(self.payload(saved, color='red')))[0], 409)
        restarted = OrderStore(self.root, manager.DATA_DIR, manager.STATUS_LABELS, database_only=True)
        self.assertEqual(restarted.get(self.path)['calendar_colors'], colored['calendar_colors'])
        listed = json.loads(self.http('/api/orders')[2])['orders']
        self.assertEqual(next(row for row in listed if row['id'] == saved['id'])['calendar_colors'], colored['calendar_colors'])
        with self.store.connect() as db:
            self.assertEqual(db.execute("SELECT value FROM metadata_settings WHERE key='order_calendar_colors'").fetchone()[0], '1')
            previous = json.loads(db.execute("SELECT data FROM metadata_history WHERE entity='orders' AND identity=? ORDER BY seq DESC LIMIT 1", (saved['id'],)).fetchone()[0])
        self.assertEqual(previous['revision'], saved['revision'])
        self.assertNotIn(order_calendar.COLORS_BLOCK, json.loads(previous['extra_blocks']))

    def test_day_week_colors_follow_events_independently_through_edit_move_and_inactive(self):
        record = self.store.save_calendar_event(self.payload(self.order, text='Дневное'))
        record = self.store.save_calendar_event(self.payload(record, period='week', text='Недельное'))
        record = self.store.save_calendar_color(self.payload(record, color='red'))
        record = self.store.save_calendar_color(self.payload(record, period='week', color='purple'))
        record = self.store.save_calendar_inactive(self.payload(record, is_inactive=True))
        record = self.store.save_calendar_event(self.payload(record, text='Дневное — правка'))
        record = self.store.move_calendar_event(self.payload(record, days=1))
        self.assertEqual(record['calendar_colors'], {'day': {'2026-10-27': 'red'}, 'week': {'2026-10-26': 'purple'}})
        self.assertEqual(record['calendar_inactive']['day'], ['2026-10-27'])
        record = self.store.move_calendar_event(self.payload(record, period='week', days=7))
        self.assertEqual(record['calendar_colors'], {'day': {'2026-10-27': 'red'}, 'week': {'2026-11-02': 'purple'}})
        self.assertEqual(record['updated'], self.order['updated'])
        record = self.store.save_calendar_inactive(self.payload(record, date='2026-10-27', is_inactive=False))
        self.assertEqual(record['calendar_colors']['day']['2026-10-27'], 'red')

    def test_deletion_and_undo_restore_color_but_new_event_does_not_inherit_it(self):
        saved = self.store.save_calendar_event(self.payload(self.order, text='Монтаж'))
        colored = self.store.save_calendar_color(self.payload(saved, color='orange'))
        removed = self.store.remove_calendar_event(self.payload(colored))
        self.assertEqual(removed['calendar_colors'], {'day': {}, 'week': {}})
        status, _, body = self.http('/api/order-calendar-event-restore', 'POST', json.dumps(self.payload(removed, text='Монтаж', is_inactive=False, color='orange')))
        self.assertEqual(status, 200, body)
        restored = json.loads(body)
        self.assertEqual(restored['calendar_colors'], colored['calendar_colors'])
        removed = self.store.remove_calendar_event(self.payload(restored))
        new = self.store.save_calendar_event(self.payload(removed, text='Другое событие'))
        self.assertEqual(new['calendar_colors'], {'day': {}, 'week': {}})

    def test_invalid_payloads_missing_events_and_unknown_color_formats_never_replace_data(self):
        saved = self.store.save_calendar_event(self.payload(self.order, text='Монтаж'))
        for changes in ({'color': False}, {'color': 'pink'}, {'date': '2026-10-27'}, {'id': 'another'},
                        {'revision': True}, {'period': 'month'}, {'period': 'week', 'date': '2026-10-27'}):
            status = self.http('/api/order-calendar-color', 'POST', json.dumps({**self.payload(saved, color='green'), **changes}))[0]
            self.assertIn(status, (400, 409))
            self.assertEqual(self.store.get(self.path), saved)
        for value in ('[]', '{"version":2,"day":{},"week":{}}',
                      '{"version":1,"day":{"2026-10-26":"pink"},"week":{}}',
                      '{"version":1,"day":{},"week":{"2026-10-27":"red"}}'):
            blocks = {**saved['extra_blocks'], order_calendar.COLORS_BLOCK: value}
            self.assertIsNone(order_calendar.read_colors(blocks))
            for operation in (lambda: order_calendar.set_color(blocks, '2026-10-26', 'blue'),
                              lambda: order_calendar.move(blocks, '2026-10-26', 1),
                              lambda: order_calendar.remove(blocks, '2026-10-26')):
                with self.assertRaises(ValueError): operation()
            self.assertEqual(order_calendar.write(blocks, '2026-10-26', 'Правка')[order_calendar.COLORS_BLOCK], value)

    def test_all_palette_colors_and_week_date_validation(self):
        blocks = order_calendar.write({}, '2026-10-26', 'Неделя', 'week')
        for color in order_calendar.COLORS:
            blocks = order_calendar.set_color(blocks, '2026-10-26', color, 'week')
            self.assertEqual(order_calendar.read_colors(blocks)['week'], {'2026-10-26': color})
        self.assertEqual(order_calendar.read_colors({}), {'day': {}, 'week': {}})

    def test_supplier_events_reject_palette_for_both_periods(self):
        path = '# work/# glass/2026-10-25 - Стекло'
        self.folder(path)
        record = self.store.add(path, {'title': 'Стекло'})
        record = self.store.save_calendar_event(self.payload(record, text='Доставка'))
        record = self.store.save_calendar_event(self.payload(record, period='week', text='План поставщика'))
        self.assertTrue(record['work_supplier'])
        for period in ('day', 'week'):
            status, _, body = self.http('/api/order-calendar-color', 'POST', json.dumps(self.payload(record, period=period, color='red')))
            self.assertEqual(status, 400, body)
            self.assertIn('фиксированный', json.loads(body)['error'])
            self.assertEqual(self.store.get(path), record)
