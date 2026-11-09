import copy
import json
import uuid
import unittest

import invoice_preferences as preferences
import invoices
import test_server as fixtures

manager = fixtures.manager


class InvoicePreferencesTests(unittest.TestCase):
    setUp = fixtures.ManagerTests.setUp
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url
    path = 'Клиент/2026-00-00 - Заказ'

    def resource(self, kind='products', payload=None):
        return preferences.resource(manager.invoice_store(), kind, payload)

    def product(self, revision=0, **changes):
        return dict(revision=revision, kind='product', id=str(uuid.uuid4()),
                    name='Буквы <LED>', unit='шт', price='4200,50', group_id='', **changes)

    def test_catalog_persists_groups_prices_and_history_without_changing_invoices(self):
        manager.order_store().add(self.path, {'status': 'new', 'title': 'Вывеска'})
        invoice = manager.invoice_store().create({'path': self.path, 'id': str(uuid.uuid4())})
        group = dict(revision=0, kind='group', id=str(uuid.uuid4()), name='Вывески')
        self.resource(payload=group)
        product = self.product(revision=1)
        product['group_id'] = group['id']
        catalog = self.resource(payload=product)
        self.assertEqual(catalog['products'][0]['price'], '4200.50')
        product.update(revision=2, price='4250', name='Буквы')
        self.resource(payload=product)
        self.assertEqual(self.resource()['products'][0]['price'], '4250.00')
        self.assertEqual(manager.invoice_store().get(self.path, invoice['id']), invoice)
        with manager.invoice_store().connect() as db:
            history = db.execute("SELECT * FROM invoice_settings_history WHERE key='products' ORDER BY revision").fetchall()
            self.assertEqual([row['revision'] for row in history], [0, 1, 2])
            self.assertEqual(json.loads(history[-1]['value'])['products'][0]['price'], '4200.50')

    def test_stale_catalog_and_retry_do_not_duplicate_or_overwrite(self):
        payload = self.product()
        saved = self.resource(payload=payload)
        for candidate in (payload, self.product()):
            with self.assertRaises(invoices.InvoiceConflict):
                self.resource(payload=candidate)
        self.assertEqual(self.resource(), saved)

    def test_invalid_products_are_atomic_and_unknown_catalog_is_preserved(self):
        for changes in ({'price': 'NaN'}, {'price': '-1'}, {'price': '1.001'}, {'price': '1000000000'},
                        {'group_id': str(uuid.uuid4())}, {'group_id': []}, {'name': '<script>\n'},
                        {'unit': 'x' * 17}, {'name': ''}, {'revision': False}, {'kind': 'tree'}, {'id': 'bad'}):
            candidate = self.product()
            candidate.update(changes)
            with self.assertRaises(ValueError):
                self.resource(payload=candidate)
            self.assertEqual(self.resource()['revision'], 0)
        with manager.invoice_store().connect() as db:
            db.execute("INSERT INTO invoice_settings VALUES ('products',?)", ('{"version":2}',))
        with self.assertRaises(ValueError):
            self.resource()
        with self.assertRaises(ValueError):
            self.resource(payload=self.product())
        with manager.invoice_store().connect() as db:
            self.assertEqual(db.execute("SELECT value FROM invoice_settings WHERE key='products'").fetchone()[0], '{"version":2}')

    def test_seller_settings_new_and_copied_invoices_keep_independent_snapshots(self):
        manager.order_store().add(self.path, {'status': 'new', 'title': 'Вывеска'})
        store = manager.invoice_store()
        original = store.create({'path': self.path, 'id': str(uuid.uuid4())})
        settings = self.resource('seller')
        updated = copy.deepcopy(settings)
        updated['seller']['bank'] = 'Новый банк'
        result = self.resource('seller', updated)
        self.assertEqual(result['revision'], 1)
        self.assertEqual(self.resource('seller'), result)
        for source in (None, original['id']):
            created = store.create({'path': self.path, 'id': str(uuid.uuid4()), 'source': source})
            self.assertEqual(created['data']['seller']['bank'], 'Новый банк')
        self.assertEqual(store.get(self.path, original['id']), original)
        with self.assertRaises(invoices.InvoiceConflict):
            self.resource('seller', settings)
        bad = copy.deepcopy(result)
        bad['seller']['inn'] = 'bad'
        with self.assertRaises(ValueError):
            self.resource('seller', bad)
        self.assertEqual(self.resource('seller'), result)

    def test_http_preferences_require_json_header_same_origin_and_revision(self):
        for route in ('/api/invoice-products', '/api/invoice-seller'):
            status, _, body = self.http(route)
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)['revision'], 0)
        payload = json.dumps(self.product())
        for headers in ({'Content-Type': 'application/json'},
                        {'X-Manager-Invoice-Preferences': '1', 'Content-Type': 'text/plain'},
                        {'X-Manager-Invoice-Preferences': '1', 'Content-Type': 'application/json', 'Origin': 'https://evil.invalid'}):
            self.assertEqual(self.http('/api/invoice-products', 'POST', payload, headers)[0], 403)
        headers = {'X-Manager-Invoice-Preferences': '1', 'Content-Type': 'application/json'}
        self.assertEqual(self.http('/api/invoice-products', 'POST', payload, headers)[0], 200)
        self.assertEqual(self.http('/api/invoice-products', 'POST', payload, headers)[0], 409)


if __name__ == '__main__':
    unittest.main()
