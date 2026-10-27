import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import unittest
import uuid
from unittest.mock import patch

import invoice_discovery
import invoice_documents
import invoices
import test_external_invoices as fixtures

manager = fixtures.manager


class InvoiceDiscoveryTests(unittest.TestCase):
    setUp = fixtures.ExternalInvoiceTests.setUp
    tearDown = fixtures.ExternalInvoiceTests.tearDown
    folder = fixtures.ExternalInvoiceTests.folder
    file = fixtures.ExternalInvoiceTests.file
    http = fixtures.ExternalInvoiceTests.http
    url = fixtures.ExternalInvoiceTests.url
    store = fixtures.ExternalInvoiceTests.store
    payload = fixtures.ExternalInvoiceTests.payload
    path = fixtures.ExternalInvoiceTests.path
    pdf = fixtures.ExternalInvoiceTests.pdf

    def scan(self):
        return invoice_discovery.candidates(self.store(), self.path)

    def source(self, name='Новый счёт.pdf', content=None):
        relative = self.path + '/# bills/' + name
        self.file(relative, self.pdf if content is None else content)
        return self.root / relative

    def attach_payload(self, candidate=None, **changes):
        return {'path': self.path, **(candidate or self.scan()['items'][0]), 'comment': 'Из папки', **changes}

    def test_open_checks_only_direct_pdf_metadata_without_import_or_file_reads(self):
        before = manager.order_store().get(self.path)
        target = self.source('Счёт.PDF')
        self.source('.скрытый.pdf')
        self.source('пустой.pdf', b'')
        self.source('акт.txt')
        self.source('вложено/ещё.pdf')
        self.source('ссылка.pdf').unlink()
        (target.parent / 'ссылка.pdf').symlink_to(target)
        with patch.object(Path, 'read_bytes', side_effect=AssertionError('PDF read during listing')):
            status, _, body = self.http(self.url('/api/invoice-folder-candidates', self.path))
        self.assertEqual(status, 200, body)
        result = json.loads(body)
        self.assertEqual([item['name'] for item in result['items']], ['Счёт.PDF'])
        self.assertTrue(result['warning'])
        self.assertEqual(self.store().list(self.path), [])
        self.assertEqual(manager.order_store().get(self.path), before)

    def test_confirm_adopts_original_and_retry_preserves_comment_and_numbering(self):
        before = manager.order_store().get(self.path)
        target = self.source()
        initial_stat = target.stat()
        payload = self.attach_payload()
        status, _, body = self.http('/api/invoice-folder-attach', 'POST', json.dumps(payload), {'Content-Type': 'application/json'})
        self.assertEqual(status, 201, body)
        record = json.loads(body)
        self.assertEqual((record['state'], record['exported'], record['sync_pending']), ('external', 1, False))
        self.assertEqual((record['filename'], record['data']['original_name']), (target.name, target.name))
        self.assertEqual(record['data']['comment'], payload['comment'])
        self.assertEqual(self.store().pdf(self.path, record['id'])[0], self.pdf)
        self.assertEqual(self.scan()['items'], [])
        saved = self.store().save_comment({**record, 'comment': 'Поздняя правка'})
        repeated = invoice_discovery.attach(self.store(), payload)
        self.assertEqual((repeated['id'], repeated['revision'], repeated['data']['comment']), (saved['id'], saved['revision'], 'Поздняя правка'))
        self.assertEqual(len(self.store().list(self.path)), 1)
        self.assertEqual(list(target.parent.iterdir()), [target])
        self.assertEqual((target.stat().st_ino, target.stat().st_mtime_ns), (initial_stat.st_ino, initial_stat.st_mtime_ns))
        self.assertEqual(target.read_bytes(), self.pdf)
        self.assertEqual(manager.order_store().get(self.path), before)
        draft = self.store().create({'path': self.path, 'id': str(uuid.uuid4())})
        self.assertEqual(draft['number'], '1')

    def test_known_invoices_and_closing_documents_including_deleted_are_excluded(self):
        record = self.store().upload(self.payload())
        self.store().sync()
        document = invoice_documents.upload(self.store(), {**record, 'document_id': str(uuid.uuid4()),
            'name': 'Акт.pdf', 'content': self.payload()['pdf']})
        invoice_documents.sync(self.store())
        self.assertEqual(self.scan()['items'], [])
        document_id = document['closing_documents'][0]['id']
        invoice_documents.set_deleted(self.store(), {**document, 'document_id': document_id}, True)
        self.assertEqual(self.scan()['items'], [])
        self.store().remove({**self.store().get(self.path, record['id']), 'confirmed': True})
        # Even a pending trash file in # bills is never offered as a new invoice.
        self.assertEqual(self.scan()['items'], [])

    def test_modified_removed_invalid_and_oversize_files_do_not_import(self):
        target = self.source()
        payload = self.attach_payload()
        target.write_bytes(self.pdf + b' changed')
        with self.assertRaises(invoices.InvoiceConflict):
            invoice_discovery.attach(self.store(), payload)
        target.unlink()
        with self.assertRaises(ValueError):
            invoice_discovery.attach(self.store(), payload)
        self.source(content=b'%PDF-incomplete')
        with self.assertRaises(ValueError):
            invoice_discovery.attach(self.store(), self.attach_payload())
        with target.open('wb') as stream:
            stream.truncate(invoices.MAX_EXTERNAL_BYTES + 1)
        self.assertEqual(self.scan()['items'], [])
        self.assertTrue(self.scan()['warning'])
        self.assertEqual(self.store().list(self.path), [])

    def test_file_changes_during_coordinated_read_and_cloud_error_preserve_data(self):
        target = self.source()
        payload = self.attach_payload()
        def change(*args):
            target.write_bytes(self.pdf + b' changed')
            return self.pdf
        with patch.object(invoice_discovery.icloud_access.sys, 'platform', 'darwin'), patch.object(invoice_discovery.icloud_access, '_coordinated_read', side_effect=change):
            with self.assertRaises(invoices.InvoiceConflict):
                invoice_discovery.attach(self.store(), payload)
        payload = self.attach_payload()
        with patch.object(invoice_discovery.icloud_access.sys, 'platform', 'darwin'), patch.object(invoice_discovery.icloud_access, '_coordinated_read', side_effect=OSError('cloud')):
            with self.assertRaisesRegex(ValueError, 'iCloud'):
                invoice_discovery.attach(self.store(), payload)
        self.assertEqual(self.store().list(self.path), [])

    def test_duplicates_do_not_create_second_invoice_or_revive_trash(self):
        self.source()
        record = invoice_discovery.attach(self.store(), self.attach_payload())
        self.source('Копия.pdf')
        payload = self.attach_payload()
        duplicate = invoice_discovery.attach(self.store(), payload)
        self.assertEqual(duplicate['id'], record['id'])
        self.assertEqual(len(self.store().list(self.path)), 1)
        self.store().remove({**record, 'confirmed': True})
        with self.assertRaises(invoices.InvoiceConflict):
            invoice_discovery.attach(self.store(), payload)
        self.assertEqual(self.store().list(self.path), [])

    def test_simultaneous_confirmations_and_adopted_file_trash_restore(self):
        target = self.source()
        payload = self.attach_payload()
        with ThreadPoolExecutor(max_workers=2) as pool:
            records = list(pool.map(lambda _: invoice_discovery.attach(self.store(), payload), range(2)))
        self.assertEqual(records[0]['id'], records[1]['id'])
        self.assertEqual(len(self.store().list(self.path)), 1)
        removed = self.store().remove({**records[0], 'confirmed': True})
        self.store().sync()
        self.assertFalse(target.exists())
        self.assertEqual(self.scan()['items'], [])
        restored = self.store().restore(removed)
        self.assertEqual(restored['id'], records[0]['id'])
        self.assertEqual(target.read_bytes(), self.pdf)
        self.assertEqual(self.scan()['items'], [])

    def test_missing_folder_is_empty_but_symlinks_paths_and_cross_origin_are_rejected(self):
        self.assertEqual(self.scan(), {'items': [], 'warning': ''})
        target = self.source()
        candidate = self.scan()['items'][0]
        for name in ('../счёт.pdf', '/tmp/счёт.pdf', '.скрытый.pdf', 'чужой\\счёт.pdf', 'не-pdf.txt'):
            with self.assertRaises(ValueError):
                invoice_discovery.attach(self.store(), self.attach_payload(candidate, name=name))
        status, _, _ = self.http('/api/invoice-folder-attach', 'POST', json.dumps(self.attach_payload(candidate)),
                               {'Content-Type': 'application/json', 'Origin': 'https://foreign.example'})
        self.assertEqual(status, 400)
        target.unlink()
        target.parent.rmdir()
        target.parent.symlink_to(self.root / 'Клиент')
        with self.assertRaises(ValueError):
            self.scan()


if __name__ == '__main__':
    unittest.main()
