import json
import unittest
import uuid
import base64
from unittest.mock import patch

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

    def test_free_payments_have_versions_history_and_calendar_editor_without_order(self):
        payload = self.payload(path='', operation='outgoing', amount='1299,50', text='Курьер')
        status, _, body = self.http('/api/invoice-plan', 'POST', json.dumps(payload))
        self.assertEqual(status, 201, body)
        record = json.loads(body)
        self.assertEqual((record['path'], record['data']['scope']), ('', 'calendar'))
        self.assertEqual(self.store.plan(payload), record)
        status, _, body = self.http(self.url('/api/invoice', '', id=record['id']))
        self.assertEqual(json.loads(body), record)
        plan = json.loads(self.http('/api/orders')[2])['calendar_invoice_plans'][0]
        self.assertEqual((plan['title'], plan['text'], plan['amount']), ('Без заказа', 'Курьер', 129950))
        edited = self.store.plan({**payload, 'revision': record['revision'], 'amount': '1400', 'text': 'Курьер вечером'})
        with self.assertRaises(invoices.InvoiceConflict):
            self.store.plan({**payload, 'revision': record['revision']})
        inactive = self.store.save_plan_calendar_inactive({**edited, 'is_inactive': True})
        again = self.store.plan({**payload, 'revision': inactive['revision'], 'amount': '1500', 'text': 'Курьер вечером'})
        self.assertTrue(again['data']['_calendar_inactive'])
        self.assertEqual(manager.order_store().get(self.path), self.owner)
        self.store.sync()
        self.assertFalse((self.root / '# bills').exists())
        with self.assertRaises(ValueError):
            self.store.plan(self.payload(path=''))
        with self.assertRaises(invoices.InvoiceConflict):
            self.store.plan({**payload, 'path': self.path, 'revision': again['revision']})
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM invoice_history WHERE id=?', (record['id'],)).fetchone()[0], 3)

    def test_issued_source_uses_invoice_total_and_keeps_pdf_link_and_source_unchanged(self):
        draft = self.store.create({'path': self.path, 'id': str(uuid.uuid4())})
        # The source is immutable issued data; rendering is covered by the invoice suite.
        with self.store.connect() as db:
            db.execute("UPDATE invoices SET state='issued',data=json_set(data,'$.total',5880000),pdf=? WHERE id=?", (b'%PDF-immutable', draft['id']))
        source = self.store.get(self.path, draft['id'])
        status, _, body = self.http(self.url('/api/invoice-plan-source', self.path, id=source['id']))
        self.assertEqual(status, 200, body)
        detail = json.loads(body)
        self.assertEqual(detail['total'], 5880000)
        self.assertNotEqual(detail['total'], self.owner['amount'])
        payload = self.payload(operation='incoming', amount='58800', source_invoice=source['id'], source_revision=source['revision'])
        record = self.store.plan(payload)
        self.assertEqual((record['data']['invoice_id'], record['data']['invoice_label']), (source['id'], detail['label']))
        self.assertEqual(self.store.plan(payload), record)
        self.assertEqual(self.store.get(self.path, source['id']), source)
        self.assertEqual(self.store.pdf(self.path, source['id'])[0], b'%PDF-immutable')
        partial = self.store.plan({**record, 'date': record['data']['date'], 'operation': 'incoming', 'amount': '10000'})
        self.assertEqual(partial['data']['invoice_id'], source['id'])
        with self.assertRaises(invoices.InvoiceConflict):
            self.store.plan({**payload, 'id': str(uuid.uuid4()), 'source_revision': source['revision'] + 1})
        with self.assertRaises(ValueError):
            self.store.plan({**payload, 'id': str(uuid.uuid4()), 'operation': 'invoice'})
        self.store.remove({**source, 'confirmed': True})
        with self.assertRaises(invoices.InvoiceConflict):
            self.store.plan({**payload, 'id': str(uuid.uuid4())})
        self.assertEqual(self.store.calendar_plans([self.owner])[0]['invoice_label'], detail['label'])

    def test_weekly_payments_preserve_period_history_conflicts_and_restore(self):
        payload = self.payload(path='', date='2026-10-26', period='week', operation='incoming', amount='28500', text='За неделю')
        status, _, body = self.http('/api/invoice-plan', 'POST', json.dumps(payload))
        self.assertEqual(status, 201, body)
        record = json.loads(body)
        self.assertEqual(record['data']['period'], 'week')
        self.assertEqual([(p['date'], p['period'], p['amount']) for p in self.store.calendar_plans([])],
                         [('2026-10-26', 'week', 2850000)])
        edited = self.store.plan({**payload, 'revision': record['revision'], 'amount': '29000'})
        self.assertEqual(self.store.plan(payload), edited)
        with self.assertRaises(invoices.InvoiceConflict):
            self.store.plan({**payload, 'revision': record['revision']})
        # A partial caller that omits period must not turn a weekly plan into a day.
        changed = self.store.plan({'path': '', 'id': edited['id'], 'revision': edited['revision'],
                                  'date': '2026-11-02', 'operation': 'incoming', 'amount': '30000'})
        self.assertEqual((changed['data']['period'], changed['data']['text']), ('week', 'За неделю'))
        with self.store.connect() as db:
            history = json.loads(db.execute('SELECT data FROM invoice_history WHERE id=? AND revision=?',
                                           (record['id'], edited['revision'])).fetchone()[0])
            self.assertEqual((history['period'], history['date'], history['amount']), ('week', '2026-10-26', 2900000))
        removed = self.store.remove({**changed, 'confirmed': True})
        self.assertFalse(self.store.calendar_plans([]))
        with self.assertRaises(invoices.InvoiceConflict):
            self.store.plan(payload)
        restored = self.store.restore(removed)
        self.assertEqual(restored['data']['period'], 'week')
        daily = self.store.plan({**payload, 'date': '2026-11-04', 'period': 'day', 'revision': restored['revision']})
        self.assertEqual((daily['data']['period'], daily['data']['date']), ('day', '2026-11-04'))
        self.assertEqual(manager.order_store().get(self.path), self.owner)

    def test_weekly_validation_and_legacy_daily_plans(self):
        for period, scheduled in [('week', '2026-10-27'), ('month', '2026-10-26'), (None, '2026-10-26'), ([], '2026-10-26')]:
            with self.subTest(period=period, date=scheduled), self.assertRaises(ValueError):
                self.store.plan(self.payload(period=period, date=scheduled))
        weekly = self.store.plan(self.payload(date='2026-10-26', period='week'))
        daily = self.store.plan(self.payload(date='2026-10-26'))
        with self.store.connect() as db:
            db.execute("UPDATE invoices SET data=json_remove(data,'$.period') WHERE id=?", (daily['id'],))
        self.assertTrue(self.store.get(self.path, daily['id'])['plan_editable'])
        self.assertEqual({p['id']: p['period'] for p in self.store.calendar_plans([self.owner])},
                         {weekly['id']: 'week', daily['id']: 'day'})
        for unknown in ('month', None, []):
            with self.subTest(unknown=unknown):
                with self.store.connect() as db:
                    data = {**weekly['data'], 'period': unknown, 'future': 'keep'}
                    db.execute('UPDATE invoices SET data=? WHERE id=?', (json.dumps(data), weekly['id']))
                current = self.store.get(self.path, weekly['id'])
                self.assertFalse(current['plan_editable'])
                with self.assertRaises(invoices.InvoiceConflict):
                    self.store.plan({**self.payload(id=weekly['id'], date='2026-10-26'), 'revision': current['revision']})
                self.assertEqual(self.store.get(self.path, weekly['id'])['data'], data)

    def test_calendar_can_remove_only_free_day_or_week_payments_and_undo(self):
        for period in ('day', 'week'):
            payload = self.payload(path='', date='2026-10-26', period=period, operation='outgoing', amount='8000', text='Материалы')
            record = self.store.plan(payload)
            status, _, body = self.http('/api/calendar-payment-remove', 'POST', json.dumps({**record, 'confirmed': True}))
            self.assertEqual(status, 200, body)
            removed = json.loads(body)
            self.assertEqual(removed['trash']['state'], 'complete')
            self.assertNotIn(record['id'], [p['id'] for p in self.store.calendar_plans([])])
            with self.assertRaises(invoices.InvoiceConflict):
                self.store.plan(payload)
            self.assertEqual(self.http('/api/calendar-payment-restore', 'POST', json.dumps(record))[0], 409)
            status, _, body = self.http('/api/calendar-payment-restore', 'POST', json.dumps(removed))
            self.assertEqual(status, 200, body)
            restored = json.loads(body)
            self.assertEqual((restored['data']['period'], restored['data']['amount'], restored['data']['text']), (period, 800000, 'Материалы'))
            linked = self.store.plan(self.payload(date='2026-10-26', period=period, operation='incoming', amount='100'))
            self.assertEqual(self.http('/api/calendar-payment-remove', 'POST', json.dumps({**linked, 'confirmed': True}))[0], 400)
            self.assertEqual(self.store.get(self.path, linked['id']), linked)
        self.assertEqual(manager.order_store().get(self.path), self.owner)

    def test_external_pdf_amount_is_local_and_fallback_does_not_guess(self):
        pdf = (manager.APP_DIR / 'output/pdf/invoice-example.pdf').read_bytes()
        record = self.store.upload({'path': self.path, 'id': str(uuid.uuid4()), 'name': 'Готовый.pdf', 'pdf': base64.b64encode(pdf).decode()})
        with patch.object(invoices, 'pdf_total', return_value=1234567) as extract:
            detail = self.store.plan_source(self.path, record['id'])
        self.assertEqual(detail['total'], 1234567)
        self.assertEqual(extract.call_args[0][0], pdf)
        with patch.object(invoices, 'pdf_total', return_value=None):
            detail = self.store.plan_source(self.path, record['id'])
        self.assertIsNone(detail['total'])
        self.assertIn('вручную', detail['hint'])
        self.assertEqual(self.store.get(self.path, record['id']), record)
        self.assertFalse((self.root / self.path / '# bills').exists())

    def test_labelled_total_parser_rejects_conflicts_and_unlabelled_numbers(self):
        for text, expected in [('Итого к оплате: 58 800,00 ₽', 5880000), ('Всего к оплате:\n123.000,50', 12300050),
                               ('Итого 100,00\nВсего к оплате: 120,00', 12000), ('Всего: 15.50 руб.', 1550),
                               ('Итого к оплате: 10,00\nИтого к оплате: 11,00', None), ('ИНН 1234567890\n1 000,00', None),
                               ('Всего к оплате: -1 000,50', None), ('Итого: $100,00', None)]:
            with self.subTest(text=text):
                self.assertEqual(invoices.total_from_text(text), expected)

    def test_native_pdf_text_extraction_reads_generated_invoice(self):
        pdf = (manager.APP_DIR / 'output/pdf/invoice-example.pdf').read_bytes()
        self.assertEqual(invoices.pdf_total(pdf, manager.APP_DIR, manager.APP_DIR / 'data'), 10860000)


if __name__ == '__main__':
    unittest.main()
