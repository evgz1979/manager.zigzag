import json
import subprocess
import sys
import unittest
import uuid
from unittest.mock import patch

import test_external_invoices as external
import test_server as fixtures
import file_trash
import invoices

manager = fixtures.manager


class InvoiceTrashTests(unittest.TestCase):
    setUp = external.ExternalInvoiceTests.setUp
    tearDown = external.ExternalInvoiceTests.tearDown
    folder = external.ExternalInvoiceTests.folder
    file = external.ExternalInvoiceTests.file
    http = external.ExternalInvoiceTests.http
    url = external.ExternalInvoiceTests.url
    path = external.ExternalInvoiceTests.path
    pdf = external.ExternalInvoiceTests.pdf
    payload = external.ExternalInvoiceTests.payload
    store = external.ExternalInvoiceTests.store

    def attached(self):
        record = self.store().upload(self.payload())
        self.store().sync()
        return self.store().get(self.path, record['id'])

    def remove(self, record):
        return self.store().remove({**record, 'confirmed': True})

    def test_list_status_survives_trash_and_restore(self):
        record = self.store().save_list_status({**self.attached(), 'value': 'sent'})
        deleted = self.remove(record)
        self.assertEqual(deleted['list_status'], 'sent')
        self.store().sync()
        restored = self.store().restore(deleted)
        self.assertEqual(restored['list_status'], 'sent')
        self.assertEqual(restored['data'], record['data'])
        self.assertEqual(self.store().pdf(self.path, record['id'])[0], self.pdf)

    def test_delete_restore_preserves_pdf_invoice_and_file_comments(self):
        record = self.attached()
        before = manager.order_store().get(self.path)
        comment = manager.metadata_store().comment(self.root / record['pdf_path'])
        manager.metadata_store().save_comment(self.root / record['pdf_path'], 'Комментарий файла', comment['revision'])
        deleted = self.remove(record)
        self.assertEqual(self.store().list(self.path), [])
        self.assertEqual(self.store().list(self.path, trashed=True)[0]['id'], record['id'])
        self.store().sync()
        token = deleted['trash']['token']
        stored = self.root / self.path / '# bills/.trash' / token / record['filename']
        self.assertEqual(stored.read_bytes(), self.pdf)
        self.assertFalse((self.root / record['pdf_path']).exists())
        self.assertEqual(manager.read_folder(self.path + '/# bills')['files'], [])
        self.assertEqual(manager.metadata_store().get('comment', stored.relative_to(self.root).as_posix())['comment'], 'Комментарий файла')
        restored = self.store().restore(deleted)
        self.assertFalse(restored['trash'])
        self.assertEqual(self.store().pdf(self.path, record['id'])[0], self.pdf)
        self.assertEqual((self.root / record['pdf_path']).read_bytes(), self.pdf)
        self.assertEqual(restored['data']['comment'], record['data']['comment'])
        self.assertEqual(manager.metadata_store().get('comment', record['pdf_path'])['comment'], 'Комментарий файла')
        self.assertEqual(manager.order_store().get(self.path), before)
        self.assertGreater(restored['revision'], deleted['revision'])
        with self.store().connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM invoice_history WHERE id=?', (record['id'],)).fetchone()[0], 2)

    def test_confirmation_version_path_and_old_editor_are_checked(self):
        record = self.attached()
        with self.assertRaises(ValueError):
            self.store().remove(record)
        changed = self.store().save_comment({**record, 'comment': 'Новая версия'})
        with self.assertRaises(invoices.InvoiceConflict):
            self.remove(record)
        with self.assertRaises(invoices.InvoiceConflict):
            self.store().remove({**changed, 'path': 'Клиент', 'confirmed': True})
        deleted = self.remove(changed)
        self.assertEqual(self.remove(changed)['revision'], deleted['revision'])
        with self.assertRaises(invoices.InvoiceConflict):
            self.store().save_comment({**changed, 'comment': 'Старая вкладка'})
        with self.assertRaises(invoices.InvoiceConflict):
            self.store().get(self.path, record['id'])
        self.assertEqual(self.store().restore(deleted)['data']['comment'], 'Новая версия')

    def test_draft_and_not_yet_published_pdf_do_not_reappear_until_restored(self):
        draft = self.store().create({'path': self.path, 'id': str(uuid.uuid4())})
        deleted_draft = self.remove(draft)
        pending = self.store().upload(self.payload())
        deleted = self.remove(pending)
        self.store().sync()
        self.assertEqual(self.store().list(self.path), [])
        self.assertFalse((self.root / pending['pdf_path']).exists())
        self.assertEqual(self.store().restore(deleted_draft)['state'], 'draft')
        self.store().restore(deleted)
        self.store().sync()
        self.assertEqual((self.root / pending['pdf_path']).read_bytes(), self.pdf)

    def test_restart_after_move_before_ack_resumes_without_duplicate(self):
        record = self.attached()
        deleted = self.remove(record)
        real_move = file_trash.database_move
        failed = False
        def interrupted(plan, operation, **options):
            nonlocal failed
            if options.get('finish') and not failed:
                failed = True
                raise OSError('Прервано после переноса')
            return real_move(plan, operation, **options)
        with patch.object(file_trash, 'database_move', side_effect=interrupted):
            self.store().sync()
        self.assertTrue(self.store().list(self.path, trashed=True)[0]['trash']['error'])
        self.store().sync()
        item = self.store().list(self.path, trashed=True)[0]
        self.assertEqual(item['trash']['state'], 'complete', item['trash']['error'])
        self.assertFalse(item['trash']['error'])
        self.store().restore(item)
        self.assertEqual((self.root / record['pdf_path']).read_bytes(), self.pdf)

    def test_restore_conflict_keeps_foreign_file_and_supports_standalone_retry(self):
        record = self.attached()
        deleted = self.remove(record)
        self.store().sync()
        self.file(record['pdf_path'], b'foreign file')
        with self.assertRaises(invoices.InvoiceConflict):
            self.store().restore(deleted)
        self.assertEqual((self.root / record['pdf_path']).read_bytes(), b'foreign file')
        (self.root / record['pdf_path']).unlink()
        session = file_trash.session_path(self.root, deleted['trash']['token'])
        result = subprocess.run([sys.executable, str(session / '.restore.py')], capture_output=True, check=True)
        self.assertFalse(json.loads(result.stdout)['error'])
        self.assertFalse(self.store().get(self.path, record['id'])['trash'])
        self.assertEqual((self.root / record['pdf_path']).read_bytes(), self.pdf)

    def test_foreign_copy_is_never_moved_and_http_uses_exact_invoice(self):
        record = self.attached()
        self.file(record['pdf_path'], b'foreign file')
        with patch.object(manager, 'schedule_order_sync'):
            status, _, body = self.http('/api/invoice-remove', 'POST', json.dumps({**record, 'confirmed': True}))
        self.assertEqual(status, 200, body)
        self.store().sync()
        self.assertEqual((self.root / record['pdf_path']).read_bytes(), b'foreign file')
        status, _, body = self.http(self.url('/api/invoices', self.path))
        listing = json.loads(body)
        self.assertEqual(listing['items'], [])
        self.assertTrue(listing['trash'][0]['trash']['error'])
        with patch.object(manager, 'schedule_order_sync'):
            status, _, body = self.http('/api/invoice-restore', 'POST', json.dumps(listing['trash'][0]))
        self.assertEqual(status, 200, body)
