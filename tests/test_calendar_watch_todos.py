import copy
from datetime import date
import json
import unittest
import uuid
from unittest.mock import patch

import calendar_todos
import invoices
import order_calendar
import test_calendar_relevance as fixtures


class CalendarWatchTodosTests(unittest.TestCase):
    setUp = fixtures.CalendarRelevanceTests.setUp
    tearDown = fixtures.CalendarRelevanceTests.tearDown
    folder = fixtures.CalendarRelevanceTests.folder
    file = fixtures.CalendarRelevanceTests.file
    http = fixtures.CalendarRelevanceTests.http
    payload = fixtures.CalendarRelevanceTests.payload
    path = fixtures.CalendarRelevanceTests.path

    def test_telegram_route_collects_order_and_supplier_tasks_under_lock_without_mutations(self):
        import test_telegram_calendar as telegram_fixtures
        store = self.store
        for path in [self.path, '# work/# glass/2026-10-25 - Поставщику']:
            self.folder(path)
            order = self.order if path == self.path else store.add(path, {})
            order = store.save({**order, 'todo_items': [{'text': 'Задача ' + path, 'done': False}, {'text': 'Выполнено', 'done': True}]})
            event = store.save_calendar_event(self.payload(order, text='Замер ' + path))
            store.save_calendar_watch_todos(self.payload(event, is_watch_todos=True))
        before = store.list()
        def sent(image, start, data_dir, *, todo_text):
            self.assertTrue(fixtures.manager.telegram_calendar.SEND_LOCK.locked())
            self.assertEqual(image, telegram_fixtures.PNG)
            self.assertIn('Задача ' + self.path, todo_text)
            self.assertIn('Задача # work/# glass/', todo_text)
            self.assertNotIn('○ Выполнено', todo_text)
            return {'ok': True, 'todo_messages': 1}
        with patch.object(fixtures.manager.telegram_calendar, 'send', side_effect=sent) as send, patch.object(fixtures.manager.telegram_calendar, 'current_week', return_value=date(2026, 10, 26)), patch('icloud_access.read_bytes', side_effect=AssertionError('No cloud reads')):
            code, _, body = self.http('/api/calendar-telegram?start=2026-10-26', 'POST', telegram_fixtures.PNG, {'Content-Type': 'image/png', 'X-Manager-Calendar': '1'})
        self.assertEqual(code, 200, body)
        send.assert_called_once()
        self.assertEqual(store.list(), before)

    def test_selected_event_lifecycle_preserves_other_fields_and_history(self):
        for path in [self.path, '# work/# glass/2026-10-25 - Поставщику']:
            with self.subTest(path=path):
                self.folder(path)
                initial = self.order if path == self.path else self.store.add(path, {'note': 'Поставщик'})
                daily = self.store.save_calendar_event(self.payload(initial, text='Монтаж'))
                both = self.store.save_calendar_event(self.payload(daily, period='week', text='План недели'))
                marked = self.store.save_calendar_watch_todos(self.payload(both, is_watch_todos=True))
                for field in both.keys() - {'revision', 'extra_blocks', 'calendar_watch_todos'}:
                    self.assertEqual(marked[field], both[field], field)
                self.assertEqual(marked['calendar_watch_todos'], {'day': ['2026-10-26'], 'week': []})
                edited = self.store.save_calendar_event(self.payload(marked, text='Монтаж утром'))
                moved = self.store.move_calendar_event(self.payload(edited, days=1))
                removed = self.store.remove_calendar_event(self.payload(moved, date='2026-10-27'))
                self.assertEqual(removed['calendar_watch_todos']['day'], [])
                restored = self.store.restore_calendar_event(self.payload(removed, date='2026-10-27', text='Монтаж утром', is_inactive=False, is_watch_todos=True))
                self.assertEqual(restored['calendar_watch_todos']['day'], ['2026-10-27'])
                weekly = self.store.save_calendar_watch_todos(self.payload(restored, period='week', is_watch_todos=True))
                weekly = self.store.move_calendar_event(self.payload(weekly, period='week', days=7))
                self.assertEqual(weekly['calendar_watch_todos']['week'], ['2026-11-02'])
                off = self.store.save_calendar_watch_todos(self.payload(weekly, date='2026-10-27', is_watch_todos=False))
                self.assertEqual(off['calendar_watch_todos'], {'day': [], 'week': ['2026-11-02']})
                self.assertEqual(off['updated'], initial['updated'])
        with self.store.connect() as db:
            self.assertEqual(db.execute("SELECT value FROM metadata_settings WHERE key='calendar_watch_todos'").fetchone()[0], '1')
            history = [json.loads(row[0]) for row in db.execute("SELECT data FROM metadata_history WHERE entity='orders'")]
        self.assertTrue(any(order_calendar.WATCH_TODOS_BLOCK in json.loads(row['extra_blocks']) for row in history))

    def test_http_versions_validation_unknown_format_and_no_cloud_reads(self):
        event = self.store.save_calendar_event(self.payload(self.order, text='Замер'))
        with patch('icloud_access.read_bytes', side_effect=AssertionError('No cloud reads')):
            status, _, body = self.http('/api/order-calendar-watch-todos', 'POST', json.dumps(self.payload(event, is_watch_todos=True)))
            self.assertEqual(status, 200)
            marked = json.loads(body)
            self.assertEqual(self.http('/api/order-calendar-watch-todos', 'POST', json.dumps(self.payload(event, is_watch_todos=False)))[0], 409)
            for changes in [{'is_watch_todos': 1}, {'is_watch_todos': 'true'}, {'revision': True}, {'id': 'wrong'}, {'date': '2026-10-27'}, {'period': 'bad'}]:
                self.assertIn(self.http('/api/order-calendar-watch-todos', 'POST', json.dumps({**self.payload(marked, is_watch_todos=False), **changes}))[0], (400, 409))
        blocks = {**marked['extra_blocks'], order_calendar.WATCH_TODOS_BLOCK: '{"version":2,"day":[],"week":[]}'}
        with self.store.connect() as db:
            db.execute('UPDATE orders SET extra_blocks=? WHERE id=?', (json.dumps(blocks), marked['id']))
        unknown = self.store.get(self.path)
        self.assertIsNone(unknown['calendar_watch_todos'])
        with self.assertRaises(ValueError):
            self.store.save_calendar_watch_todos(self.payload(unknown, is_watch_todos=False))
        with self.assertRaises(ValueError):
            self.store.move_calendar_event(self.payload(unknown, days=1))
        with self.assertRaises(ValueError):
            self.store.remove_calendar_event(self.payload(unknown))
        self.assertEqual(self.store.get(self.path)['revision'], unknown['revision'])

    def test_invoice_plan_preserves_data_and_owner_version_rejects_free_and_stale(self):
        store = fixtures.manager.invoice_store()
        for period in ['day', 'week']:
            plan = store.plan({'path': self.path, 'id': str(uuid.uuid4()), 'date': '2026-10-26', 'period': period, 'operation': 'incoming', 'amount': '1234', 'text': 'Аванс'})
            marked = store.save_plan_calendar_watch_todos({**plan, 'is_watch_todos': True})
            self.assertEqual({k: v for k, v in marked['data'].items() if k != '_calendar_watch_todos'}, plan['data'])
            with self.assertRaises(invoices.InvoiceConflict):
                store.save_plan_calendar_watch_todos({**plan, 'is_watch_todos': False})
            moved = store.move_calendar_plan({**marked, 'date': '2026-10-26', 'period': period, 'days': 7})
            self.assertTrue(moved['data']['_calendar_watch_todos'])
            shown = next(item for item in store.calendar_plans([self.order]) if item['id'] == plan['id'])
            self.assertTrue(shown['is_watch_todos'])
            status, _, body = self.http('/api/invoice-plan-calendar-watch-todos', 'POST', json.dumps({**moved, 'is_watch_todos': False}))
            self.assertEqual(status, 200)
            self.assertFalse(json.loads(body)['data']['_calendar_watch_todos'])
        free = store.plan({'path': '', 'id': str(uuid.uuid4()), 'date': '2026-10-26', 'operation': 'incoming', 'amount': '100', 'scope': 'calendar'})
        with self.assertRaises(ValueError):
            store.save_plan_calendar_watch_todos({**free, 'is_watch_todos': True})
        self.assertEqual(self.store.get(self.path), self.order)


class CalendarTodoDigestTests(unittest.TestCase):
    def test_digest_matches_visible_events_range_flags_and_pending_tasks(self):
        order = {'path': 'Клиент/Заказ', 'title': 'Окна', 'client': 'Клиент', 'object': 'Объект',
                 'deadline_weeks': ['2026-10-26'],
                 'calendar_events': {'2026-10-26': 'Замер', '2026-11-02': 'Скрытый', '2026-11-09': 'За диапазоном'},
                 'calendar_week_events': {'2026-10-26': 'План недели'},
                 'calendar_watch_todos': {'day': ['2026-10-26', '2026-11-02', '2026-11-09'], 'week': ['2026-10-26']},
                 'calendar_completed': {'day': ['2026-11-02'], 'week': []},
                 'todo_groups': [{'label': 'Заказ', 'items': [{'text': 'Купить <ручки> 😀', 'done': False}, {'text': 'Уже готово', 'done': True}]}, {'label': '01 - Замер', 'items': [{'text': 'Позвонить', 'done': False}]}]}
        snapshot = {'orders': [order], 'calendar_supplier_orders': [], 'calendar_invoice_plans': [
            {'path': order['path'], 'date': '2026-11-08', 'period': 'day', 'is_watch_todos': True, 'operation': 'incoming', 'amount': 123456, 'text': 'Аванс'},
            {'path': '', 'date': '2026-10-26', 'is_watch_todos': True}]}
        original = copy.deepcopy(snapshot)
        text = calendar_todos.digest(snapshot, '2026-10-26')
        for expected in ['Замер', 'План недели', 'Получение оплаты · 1 234,56 ₽', 'Купить <ручки> 😀', '01 - Замер:', 'Позвонить']:
            self.assertIn(expected, text)
        for excluded in ['Скрытый', 'За диапазоном', 'Уже готово']:
            self.assertNotIn(excluded, text)
        self.assertEqual(snapshot, original)
        self.assertEqual(text.count('Купить <ручки> 😀'), 3)

    def test_empty_digest_and_lossless_unicode_chunking(self):
        self.assertEqual(calendar_todos.digest({}, '2026-10-26'), '')
        text = ('☷ Задачи\n' + '😀' * 5000 + '\n○ ' + 'я' * 5000) * 2
        parts = list(calendar_todos.message_parts(text))
        self.assertEqual(''.join(parts), text)
        self.assertTrue(all(0 < len(part.encode('utf-16-le')) // 2 <= 4000 for part in parts))


if __name__ == '__main__':
    unittest.main()
