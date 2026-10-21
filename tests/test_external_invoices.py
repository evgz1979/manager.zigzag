import base64
import json
from pathlib import Path
import unittest
import uuid
from unittest.mock import patch

import file_uploads
import invoices
import test_server as fixtures

manager = fixtures.manager


class ExternalInvoiceTests(unittest.TestCase):
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url
    path = 'Клиент/2026-00-00 - Заказ'
    pdf = (Path(__file__).resolve().parents[1] / 'output/pdf/invoice-example.pdf').read_bytes()

    def setUp(self):
        fixtures.ManagerTests.setUp(self)
        manager.DATABASE_ONLY = True
        manager.order_store().add(self.path, {'title': 'Вывеска', 'status': 'process', 'note': 'Заметка заказа', 'amount': 12345})

    def store(self):
        return manager.invoice_store()

    def payload(self, **changes):
        return {'path': self.path, 'id': str(uuid.uuid4()), 'name': 'Внешний счёт.pdf',
                'comment': 'Оплата за вывеску', 'pdf': base64.b64encode(self.pdf).decode(), **changes}

    def test_http_shared_list_database_pdf_idempotency_and_numbering(self):
        before = manager.order_store().get(self.path)
        draft = self.store().create({'path': self.path, 'id': str(uuid.uuid4())})
        payload = self.payload()
        with patch.object(manager, 'schedule_order_sync'):
            status, _, body = self.http('/api/invoice-upload', 'POST', json.dumps(payload), {'Content-Type': 'application/json'})
            self.assertEqual(status, 201, body)
            record = json.loads(body)
            self.assertEqual(self.http('/api/invoice-upload', 'POST', json.dumps(payload), {'Content-Type': 'application/json'})[0], 201)
        self.assertEqual(record['data']['comment'], payload['comment'])
        status, _, body = self.http(self.url('/api/invoices', self.path))
        listed = json.loads(body)['items']
        self.assertEqual({item['id'] for item in listed}, {draft['id'], record['id']})
        self.assertTrue(all('pdf' not in item for item in listed))
        status, headers, body = self.http(self.url('/api/invoice-pdf', self.path, id=record['id']))
        self.assertEqual((status, headers['Content-Type'], body), (200, 'application/pdf', self.pdf))
        next_draft = self.store().create({'path': self.path, 'id': str(uuid.uuid4())})
        self.assertEqual(int(next_draft['number']), int(draft['number']) + 1)
        self.assertEqual(manager.order_store().get(self.path), before)
        with self.assertRaises(ValueError):
            self.store().create({'path': self.path, 'id': str(uuid.uuid4()), 'source': record['id']})
        with self.assertRaises(ValueError):
            self.store().issue({'path': self.path, 'id': record['id'], 'revision': record['revision']})

    def test_comment_history_conflict_clear_and_retry_preserve_pdf(self):
        payload = self.payload()
        record = self.store().upload(payload)
        saved = self.store().save_comment({**record, 'comment': ''})
        self.assertEqual(saved['data']['comment'], '')
        with self.assertRaises(invoices.InvoiceConflict):
            self.store().save_comment({**record, 'comment': 'Устаревшая вкладка'})
        self.assertEqual(self.store().upload(payload)['data']['comment'], '')
        self.assertEqual(self.store().pdf(self.path, record['id'])[0], self.pdf)
        with self.store().connect() as db:
            old = db.execute('SELECT data FROM invoice_history WHERE id=? AND revision=?', (record['id'], record['revision'])).fetchone()
        self.assertEqual(json.loads(old[0])['comment'], payload['comment'])

    def test_outbox_retry_same_named_uploads_and_reserved_names(self):
        first, second = self.store().upload(self.payload()), self.store().upload(self.payload())
        self.assertNotEqual(first['filename'], second['filename'])
        with self.store().connect() as db:
            self.assertIn(first['filename'].casefold(), file_uploads.reserved_names(db, self.path + '/# bills'))
        self.file(first['pdf_path'], b'other document')
        self.store().sync()
        self.assertTrue(self.store().get(self.path, first['id'])['sync_pending'])
        self.assertEqual((self.root / first['pdf_path']).read_bytes(), b'other document')
        self.assertEqual((self.root / second['pdf_path']).read_bytes(), self.pdf)
        (self.root / first['pdf_path']).unlink()
        self.store().sync()
        self.assertFalse(self.store().get(self.path, first['id'])['sync_pending'])
        stamp = (self.root / first['pdf_path']).stat().st_mtime_ns
        with self.store().connect() as db:
            db.execute('UPDATE invoices SET exported=0 WHERE id=?', (first['id'],))
        self.store().sync()
        self.assertEqual((self.root / first['pdf_path']).stat().st_mtime_ns, stamp)

    def test_rename_undo_and_old_tab_preserve_attachment_and_outbox(self):
        record = self.store().upload(self.payload())
        view = manager.folder_rename.preview(manager.order_store(), self.path)
        moved = manager.folder_rename.rename(manager.order_store(), {**view, 'name': '2026-00-00 - Другое имя'})
        with self.assertRaises(invoices.InvoiceConflict):
            self.store().save_comment({**record, 'comment': 'Старая вкладка'})
        self.assertEqual(self.store().pdf(moved['path'], record['id'])[0], self.pdf)
        manager.folder_rename.restore.undo(self.root / moved['journal'], True)
        self.store().sync()
        self.assertEqual(self.store().get(self.path, record['id'])['data'], record['data'])
        self.assertEqual((self.root / record['pdf_path']).read_bytes(), self.pdf)

    def test_invalid_uploads_never_create_records_and_identity_is_bound(self):
        for changes in ({'name': '../x.pdf'}, {'name': 'x.txt'}, {'pdf': 'not base64!'},
                        {'pdf': base64.b64encode(b'not PDF').decode()}, {'comment': 'x' * 5001},
                        {'path': 'Клиент'}, {'id': 'not-an-id'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.store().upload(self.payload(**changes))
        with patch.object(invoices, 'MAX_EXTERNAL_BYTES', 10):
            with self.assertRaisesRegex(ValueError, '20 МБ'):
                self.store().upload(self.payload())
        self.assertEqual(self.store().list(self.path), [])
        record = self.store().upload(self.payload())
        with self.assertRaises(invoices.InvoiceConflict):
            self.store().upload(self.payload(id=record['id'], name='другой.pdf'))
        payload = self.payload()
        self.assertEqual(self.http('/api/invoice-upload', 'POST', json.dumps(payload), {'Content-Type': 'text/plain'})[0], 400)
        self.assertEqual(self.http('/api/invoice-upload', 'POST', json.dumps(payload), {'Content-Type': 'application/json', 'Origin': 'http://foreign.invalid'})[0], 400)
