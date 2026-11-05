"""Persistence and HTTP contracts for the payment calendar's «Сообщил» mark."""
import json
import unittest
import uuid
from unittest.mock import patch

import invoices
import test_server as fixtures

manager = fixtures.manager


class CalendarNotifiedTests(unittest.TestCase):
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    path = 'Клиент/2026-00-00 - Заказ'
    route = '/api/invoice-plan-calendar-notified'

    def setUp(self):
        fixtures.ManagerTests.setUp(self)
        mode = patch.object(manager, 'DATABASE_ONLY', True)
        mode.start()
        self.patches.append(mode)
        self.owner = manager.order_store().add(self.path, {'title': 'Вывеска', 'amount': 12345})
        self.store = manager.invoice_store()

    def payload(self, **changes):
        return {'path': self.path, 'id': str(uuid.uuid4()), 'date': '2026-11-02',
                'operation': 'incoming', 'amount': '123.45', 'text': 'Аванс', **changes}

    def test_partial_mark_survives_edit_move_other_flags_trash_and_restore(self):
        for path in (self.path, ''):
            for period in ('day', 'week'):
                for operation in ('incoming', 'outgoing'):
                    with self.subTest(path=path, period=period, operation=operation):
                        payload = self.payload(path=path, period=period, operation=operation)
                        plan = self.store.plan(payload)
                        with patch('icloud_access.read_bytes', side_effect=AssertionError('No document reads')):
                            marked = self.store.save_plan_calendar_notified({**plan, 'is_notified': True})
                        self.assertEqual({k: v for k, v in marked['data'].items() if k != '_calendar_notified'}, plan['data'])
                        self.assertEqual(marked['revision'], plan['revision'] + 1)
                        moved = self.store.move_calendar_plan({**marked, 'date': payload['date'], 'period': period, 'days': 7})
                        edited = self.store.plan({**payload, 'revision': moved['revision'], 'date': '2026-11-09', 'text': 'Остаток', 'amount': '222'})
                        carried = self.store.save_plan_calendar_carryover({**edited, 'is_carryover': True})
                        completed = self.store.save_plan_calendar_completed({**carried, 'is_completed': True})
                        inactive = self.store.save_plan_calendar_inactive({**completed, 'is_inactive': True})
                        shown = next(p for p in self.store.calendar_plans([self.owner]) if p['id'] == plan['id'])
                        self.assertTrue(shown['is_notified'])
                        removed = self.store.remove({**inactive, 'confirmed': True})
                        with self.assertRaises(invoices.InvoiceConflict):
                            self.store.save_plan_calendar_notified({**removed, 'is_notified': False})
                        restored = self.store.restore(removed)
                        self.assertTrue(restored['data']['_calendar_notified'])
                        unmarked = self.store.save_plan_calendar_notified({**restored, 'is_notified': False})
                        self.assertFalse(unmarked['data']['_calendar_notified'])
                        self.assertEqual({k: v for k, v in unmarked['data'].items() if k != '_calendar_notified'},
                                         {k: v for k, v in restored['data'].items() if k != '_calendar_notified'})
                        with self.store.connect() as db:
                            history = [json.loads(r[0]) for r in db.execute('SELECT data FROM invoice_history WHERE id=?', (plan['id'],))]
                        self.assertIn(plan['data'], history)
                        self.assertTrue(any(p.get('_calendar_notified') is True for p in history))
        with self.store.connect() as db:
            self.assertEqual(db.execute("SELECT value FROM metadata_settings WHERE key='invoice_calendar_notified'").fetchone()[0], '1')
        self.assertEqual(manager.order_store().get(self.path), self.owner)

    def test_http_flag_conflicts_strict_values_and_unknown_format(self):
        plan = self.store.plan(self.payload())
        self.assertFalse(self.store.calendar_plans([self.owner])[0]['is_notified'])
        status, _, body = self.http(self.route, 'POST', json.dumps({**plan, 'is_notified': True}))
        self.assertEqual(status, 200, body)
        marked = json.loads(body)
        self.assertTrue(marked['data']['_calendar_notified'])
        self.assertEqual(self.http(self.route, 'POST', json.dumps({**plan, 'is_notified': False}))[0], 409)
        for changes in ({'is_notified': None}, {'is_notified': 1}, {'is_notified': 'true'}, {'revision': True}, {'id': str(uuid.uuid4())}, {'path': ''}):
            self.assertIn(self.http(self.route, 'POST', json.dumps({**marked, 'is_notified': False, **changes}))[0], (400, 404, 409))
        self.assertEqual(self.store.get(self.path, plan['id']), marked)
        for value in (None, 1, 'future'):
            with self.store.connect() as db:
                db.execute('UPDATE invoices SET data=? WHERE id=?', (json.dumps({**marked['data'], '_calendar_notified': value}), plan['id']))
            unknown = self.store.get(self.path, plan['id'])
            self.assertEqual(self.http(self.route, 'POST', json.dumps({**unknown, 'is_notified': False}))[0], 400)
            self.assertEqual(self.store.get(self.path, plan['id']), unknown)
        issuance = self.store.plan(self.payload(operation='invoice'))
        self.assertEqual(self.http(self.route, 'POST', json.dumps({**issuance, 'is_notified': True}))[0], 400)


if __name__ == '__main__':
    unittest.main()
