import json
import unittest
import uuid

import invoices
import test_server as fixtures

manager = fixtures.manager


class InvoicePlanTests(unittest.TestCase):
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url
    path = 'Клиент/2026-00-00 - Заказ'

    def setUp(self):
        fixtures.ManagerTests.setUp(self)
        manager.DATABASE_ONLY = True
        self.owner = manager.order_store().add(self.path, {'title': 'Вывеска', 'status': 'process', 'amount': 12345})
        self.store = manager.invoice_store()

    def payload(self, **changes):
        return {'path': self.path, 'id': str(uuid.uuid4()), 'date': '2026-10-27', **changes}

    def test_http_plan_list_and_calendar_without_pdf_number_or_order_changes(self):
        payload = self.payload()
        status, _, body = self.http('/api/invoice-plan', 'POST', json.dumps(payload))
        self.assertEqual(status, 201, body)
        record = json.loads(body)
        self.assertEqual(record['state'], 'planned')
        self.assertTrue(record['plan_editable'])
        self.assertFalse(record['sync_pending'])
        self.assertIsNone(record['pdf_path'])
        self.assertEqual(self.store.list(self.path), [record])
        plans = json.loads(self.http('/api/orders')[2])['calendar_invoice_plans']
        self.assertEqual([(p['id'], p['path'], p['date'], p['title']) for p in plans],
                         [(record['id'], self.path, payload['date'], 'Вывеска')])
        self.assertEqual(manager.order_store().get(self.path), self.owner)
        self.store.sync()
        self.assertFalse((self.root / self.path / '# bills').exists())
        with self.store.connect() as db:
            self.assertIsNone(db.execute('SELECT pdf FROM invoices WHERE id=?', (record['id'],)).fetchone()[0])
            self.assertEqual(db.execute('SELECT COUNT(*) FROM invoice_sequences').fetchone()[0], 0)
        self.assertEqual(self.store.create({'path': self.path, 'id': str(uuid.uuid4())})['number'], '1')
        self.assertEqual(self.http(self.url('/api/invoice-pdf', self.path, id=record['id']))[0], 400)
        self.assertEqual(self.http(self.url('/api/invoice-preview', self.path, id=record['id']))[0], 400)

    def test_date_edit_history_conflicts_idempotency_and_trash_restore(self):
        payload = self.payload()
        original = self.store.plan(payload)
        self.assertEqual(self.store.plan(payload), original)
        edited = self.store.plan({**payload, 'revision': original['revision'], 'date': '2026-11-03'})
        self.assertEqual(edited['revision'], original['revision'] + 1)
        self.assertEqual(self.store.plan(payload), edited)
        with self.assertRaises(invoices.InvoiceConflict):
            self.store.plan({**payload, 'revision': original['revision'], 'date': '2026-10-28'})
        with self.store.connect() as db:
            history = json.loads(db.execute('SELECT data FROM invoice_history WHERE id=?', (original['id'],)).fetchone()[0])
            self.assertEqual(history['date'], payload['date'])
        removed = self.store.remove({**edited, 'confirmed': True})
        self.assertFalse(self.store.calendar_plans([self.owner]))
        with self.assertRaises(invoices.InvoiceConflict):
            self.store.plan(payload)
        with self.assertRaises(invoices.InvoiceConflict):
            self.store.plan({**payload, 'revision': removed['revision']})
        restored = self.store.restore(removed)
        self.assertEqual(restored['data']['date'], '2026-11-03')
        self.assertEqual(self.store.calendar_plans([self.owner])[0]['date'], '2026-11-03')

    def test_multiple_same_day_unknown_format_and_invalid_requests(self):
        original = self.store.plan(self.payload())
        second = self.store.plan(self.payload())
        self.assertEqual(len(self.store.calendar_plans([self.owner])), 2)
        for value in ('2026-02-30', '2026-1-01', '', None, True):
            with self.subTest(date=value), self.assertRaises(ValueError):
                self.store.plan(self.payload(date=value))
        with self.assertRaises(invoices.InvoiceConflict):
            self.store.plan(self.payload(revision=1))
        with self.assertRaises(ValueError):
            self.store.create({'path': self.path, 'id': str(uuid.uuid4()), 'source': original['id']})
        with self.store.connect() as db:
            db.execute("UPDATE invoices SET data=json_set(data,'$.version',2,'$.future','keep') WHERE id=?", (original['id'],))
        unknown = self.store.get(self.path, original['id'])
        self.assertFalse(unknown['plan_editable'])
        with self.assertRaises(invoices.InvoiceConflict):
            self.store.plan({**self.payload(id=original['id']), 'revision': unknown['revision']})
        self.assertEqual(self.store.get(self.path, original['id']), unknown)
        self.assertEqual([p['id'] for p in self.store.calendar_plans([self.owner])], [second['id']])

    def test_calendar_only_uses_visible_registered_orders_and_follows_renamed_path(self):
        record = self.store.plan(self.payload())
        self.assertEqual(self.store.calendar_plans([]), [])
        self.assertEqual(self.store.calendar_plans([{**self.owner, 'registered': False}]), [])
        renamed = self.path + ' новый путь'
        with self.store.connect() as db:
            db.execute('UPDATE invoices SET path=?,revision=revision+1 WHERE id=?', (renamed, record['id']))
        self.assertEqual(self.store.calendar_plans([self.owner]), [])
        plan = self.store.calendar_plans([{**self.owner, 'path': renamed}])[0]
        self.assertEqual(plan['path'], renamed)

    def test_payment_amounts_are_exact_and_independent_of_actual_finances(self):
        incoming = self.store.plan(self.payload(operation='incoming', amount='123 000,05'))
        outgoing = self.store.plan(self.payload(operation='outgoing', amount='62000'))
        self.assertEqual(incoming['data']['amount'], 12300005)
        self.assertEqual(outgoing['data']['amount'], 6200000)
        plans = self.store.calendar_plans([self.owner])
        self.assertEqual([(p['operation'], p['amount']) for p in plans], [('incoming', 12300005), ('outgoing', 6200000)])
        self.assertEqual(manager.order_store().get(self.path), self.owner)
        changed = self.store.plan({**incoming, 'date': incoming['data']['date'], 'operation': 'outgoing', 'amount': '9,99'})
        self.assertEqual((changed['data']['operation'], changed['data']['amount']), ('outgoing', 999))
        with self.assertRaises(invoices.InvoiceConflict):
            self.store.plan({**incoming, 'date': incoming['data']['date'], 'operation': 'incoming', 'amount': '5'})
        invoice = self.store.plan({**changed, 'date': changed['data']['date'], 'operation': 'invoice'})
        self.assertNotIn('amount', invoice['data'])
        for value in ('0', '-1', '0.001', 'NaN', '1000000000', None, True):
            with self.subTest(amount=value), self.assertRaises(ValueError):
                self.store.plan(self.payload(operation='incoming', amount=value))
        for value in (None, [], True, 'other'):
            with self.subTest(operation=value), self.assertRaises(ValueError):
                self.store.plan(self.payload(operation=value))
        self.assertFalse(invoices.known_plan({'version': 1, 'kind': 'planned', 'date': '2026-10-27', 'operation': []}))
        self.assertFalse(invoices.known_plan({'version': 1, 'kind': 'planned', 'date': '2026-10-27', 'operation': 'incoming', 'amount': True}))


if __name__ == '__main__':
    unittest.main()
