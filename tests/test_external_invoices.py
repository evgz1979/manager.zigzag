import base64
import json
from pathlib import Path
import unittest
import uuid
from unittest.mock import patch

import file_uploads
import invoices
from test_pdf_preview import sample_pdf
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

    def test_list_status_is_versioned_partial_and_does_not_change_pdf_or_order(self):
        record = self.store().upload(self.payload())
        initial = record
        order = manager.order_store().get(self.path)
        self.assertEqual(record['list_status'], 'none')
        for value in ('active', 'inactive', 'later', 'sent', 'none'):
            previous = record
            status, _, body = self.http('/api/invoice-list-status', 'POST', json.dumps({
                'path': self.path, 'id': record['id'], 'revision': record['revision'], 'value': value}))
            self.assertEqual(status, 200, body)
            record = json.loads(body)
            self.assertEqual(record['list_status'], value)
            self.assertEqual(record['revision'], previous['revision'] + 1)
            self.assertEqual(record['data'], {**initial['data'], '_list_status': value})
            self.assertEqual(self.store().pdf(self.path, record['id'])[0], self.pdf)
            self.assertEqual((record['filename'], record['exported'], record['sync_pending']),
                             (initial['filename'], initial['exported'], initial['sync_pending']))
            with self.store().connect() as db:
                history = db.execute('SELECT data FROM invoice_history WHERE id=? AND revision=?', (record['id'], previous['revision'])).fetchone()
            self.assertEqual(json.loads(history[0]), previous['data'])
        self.assertEqual(self.store().save_list_status({**record, 'value': 'none'}), record)
        for revision in (initial['revision'], None, True):
            status, _, _ = self.http('/api/invoice-list-status', 'POST', json.dumps({**record, 'revision': revision, 'value': 'active'}))
            self.assertEqual(status, 409)
        commented = self.store().save_comment({**record, 'comment': 'Новая заметка'})
        self.assertEqual(commented['list_status'], 'none')
        self.assertEqual(manager.order_store().get(self.path), order)
        self.assertEqual(self.store().get(self.path, record['id'])['data']['comment'], 'Новая заметка')

    def test_list_status_rejects_unknown_data_wrong_paths_and_trashed_invoices(self):
        record = self.store().upload(self.payload())
        for value in ('invalid', None, True, {}):
            with self.assertRaises(ValueError):
                self.store().save_list_status({**record, 'value': value})
        with self.assertRaises(ValueError):
            self.store().save_list_status({**record, 'path': 'Клиент/2026-00-00 - Другой', 'value': 'sent'})
        future = {**record['data'], '_list_status': {'version': 99, 'value': 'future'}, 'unknown': 'сохранить'}
        with self.store().connect() as db:
            db.execute('UPDATE invoices SET data=? WHERE id=?', (json.dumps(future), record['id']))
        self.assertIsNone(self.store().get(self.path, record['id'])['list_status'])
        with self.assertRaisesRegex(ValueError, 'неизвестная отметка'):
            self.store().save_list_status({**record, 'value': 'active'})
        self.assertEqual(self.store().get(self.path, record['id'])['data'], future)
        with self.store().connect() as db:
            data = {**record['data'], '_trash': {'token': str(uuid.uuid4()), 'state': 'pending', 'error': ''}}
            db.execute('UPDATE invoices SET data=? WHERE id=?', (json.dumps(data), record['id']))
        with self.assertRaises(invoices.InvoiceConflict):
            self.store().save_list_status({**record, 'value': 'sent'})

    def test_viewer_renders_database_pdf_before_export_without_document_access(self):
        original = sample_pdf()
        record = self.store().upload(self.payload(pdf=base64.b64encode(original).decode()))
        self.assertFalse((self.root / record['pdf_path']).exists())
        before = self.store().get(self.path, record['id'])
        stat = Path.stat

        def local_stat(path, *args, **kwargs):
            if path == self.root or self.root in path.parents:
                raise AssertionError('Invoice viewer must not access document folders')
            return stat(path, *args, **kwargs)

        with patch.object(Path, 'stat', local_stat):
            status, _, body = self.http(self.url('/api/invoice', self.path, id=record['id']))
            self.assertEqual((status, json.loads(body)['revision']), (200, record['revision']))
            status, _, body = self.http(self.url('/api/invoice-pdf-info', self.path, id=record['id']))
            self.assertEqual((status, json.loads(body)['pages']), (200, 2))
            for page in (0, 1):
                status, headers, body = self.http(self.url('/api/invoice-pdf-page', self.path, id=record['id'], page=page))
                self.assertEqual((status, headers['Content-Type']), (200, 'image/jpeg'))
                self.assertTrue(body.startswith(b'\xff\xd8'))
                self.assertGreater(len(body), 1000)
            self.assertEqual(self.http(self.url('/api/invoice-pdf-page', self.path, id=record['id'], page=2))[0], 400)
        self.assertEqual(self.store().get(self.path, record['id']), before)
        self.assertEqual(self.store().pdf(self.path, record['id'])[0], original)
        status, headers, body = self.http(self.url('/api/invoice-pdf', self.path, id=record['id'], download=1))
        self.assertEqual((status, body), (200, original))
        self.assertTrue(headers['Content-Disposition'].startswith('attachment;'))

    def test_cached_viewer_still_checks_invoice_path_and_trash(self):
        record = self.store().upload(self.payload())
        cached = manager.invoice_pdf_target(self.path, record['id'])
        self.assertEqual(cached.read_bytes(), self.pdf)
        stamp = cached.stat().st_mtime_ns
        self.assertEqual(manager.invoice_pdf_target(self.path, record['id']).stat().st_mtime_ns, stamp)
        other = 'Клиент/2026-00-00 - Другой'
        self.folder(other)
        manager.order_store().add(other, {'title': 'Другой заказ'})
        routes = ('/api/invoice', '/api/invoice-pdf-info', '/api/invoice-pdf-page')
        for route in routes:
            self.assertEqual(self.http(self.url(route, other, id=record['id']))[0], 400)
        with self.store().connect() as db:
            data = json.loads(db.execute('SELECT data FROM invoices WHERE id=?', (record['id'],)).fetchone()[0])
            data['_trash'] = {'token': str(uuid.uuid4()), 'state': 'pending', 'error': ''}
            db.execute('UPDATE invoices SET data=? WHERE id=?', (json.dumps(data), record['id']))
        for route in routes:
            self.assertEqual(self.http(self.url(route, self.path, id=record['id']))[0], 400)
        self.assertEqual(cached.read_bytes(), self.pdf)

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
        record = self.store().save_list_status({**record, 'value': 'sent'})
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
