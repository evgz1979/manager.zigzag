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

    def test_delete_preserves_other_products_groups_invoice_and_history(self):
        manager.order_store().add(self.path, {'status': 'new', 'title': 'Вывеска'})
        invoice = manager.invoice_store().create({'path': self.path, 'id': str(uuid.uuid4())})
        group = dict(kind='group', id=str(uuid.uuid4()), revision=0, name='Вывески')
        self.resource(payload=group)
        first = self.product(1)
        first['group_id'] = group['id']
        self.resource(payload=first)
        second = self.product(2)
        previous = self.resource(payload=second)
        invoice['data']['items'] = [dict(name=first['name'], quantity='1', unit=first['unit'], price=first['price'])]
        invoice = manager.invoice_store().save(dict(path=self.path, id=invoice['id'], revision=invoice['revision'], data=invoice['data']))
        result = self.resource(payload=dict(action='delete', kind='product', id=first['id'], revision=3, confirmed=True))
        self.assertEqual(result['revision'], 4)
        self.assertEqual([item['id'] for item in result['products']], [second['id']])
        self.assertEqual(result['groups'], previous['groups'])
        self.assertEqual(manager.invoice_store().get(self.path, invoice['id']), invoice)
        with manager.invoice_store().connect() as db:
            saved = db.execute("SELECT value FROM invoice_settings_history WHERE key='products' AND revision=3").fetchone()
            self.assertEqual(json.loads(saved[0]), previous)

    def test_delete_requires_confirmation_current_revision_and_known_product(self):
        product = self.product()
        before = self.resource(payload=product)
        request = dict(action='delete', kind='product', id=product['id'], revision=1, confirmed=True)
        for changes in ({'confirmed': False}, {'confirmed': 1}, {'kind': 'group'}, {'action': 'unknown'},
                        {'revision': 0}, {'revision': True}, {'id': str(uuid.uuid4())}):
            with self.assertRaises(ValueError):
                self.resource(payload={**request, **changes})
            self.assertEqual(self.resource(), before)

    def test_removed_uuid_cannot_be_recreated_by_old_form_or_explicit_create(self):
        product = self.product()
        self.resource(payload=product)
        result = self.resource(payload=dict(action='delete', kind='product', id=product['id'], revision=1, confirmed=True))
        for action in ('save', 'update', 'create'):
            with self.assertRaises(invoices.InvoiceConflict):
                self.resource(payload={**product, 'revision': result['revision'], 'action': action})
            self.assertEqual(self.resource(), result)
        copied = {**product, 'id': str(uuid.uuid4()), 'revision': 2, 'action': 'create'}
        self.assertEqual(self.resource(payload=copied)['products'][0]['id'], copied['id'])

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
