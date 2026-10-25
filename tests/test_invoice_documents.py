import base64
import json
from pathlib import Path
import unittest
import uuid
from unittest.mock import patch

import invoice_documents as documents
import invoices
import test_server as fixtures

manager = fixtures.manager


class InvoiceDocumentTests(unittest.TestCase):
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url
    path = 'Клиент/2026-10-25 - Вывеска'
    pdf = (Path(__file__).resolve().parents[1] / 'output/pdf/invoice-example.pdf').read_bytes()

    def setUp(self):
        fixtures.ManagerTests.setUp(self)
        mode = patch.object(manager, 'DATABASE_ONLY', True)
        mode.start()
        self.patches.append(mode)
        background = patch.object(manager, 'schedule_order_sync')
        background.start()
        self.patches.append(background)
        self.folder(self.path)
        self.owner = manager.order_store().add(self.path, {'title': 'Вывеска', 'status': 'process', 'amount': 10000, 'paid': 2000})
        self.store = manager.invoice_store()
        self.invoice = self.store.create({'path': self.path, 'id': str(uuid.uuid4())})

    def payload(self, record=None, **changes):
        row = record or self.invoice
        return {'path': row['path'], 'id': row['id'], 'revision': row['revision'], 'document_id': str(uuid.uuid4()),
                'name': 'Акт № 1.pdf', 'content': base64.b64encode(self.pdf).decode(), **changes}

    def test_http_upload_inline_and_download_are_exact_and_list_has_only_metadata(self):
        payload = self.payload()
        with patch('icloud_access.read_bytes', side_effect=AssertionError('No iCloud reads')):
            status, _, body = self.http('/api/invoice-document-upload', 'POST', json.dumps(payload), {'Content-Type': 'application/json'})
            self.assertEqual(status, 201, body)
            row = json.loads(body)
            self.assertEqual([d['name'] for d in row['closing_documents']], ['Акт № 1.pdf'])
            self.assertEqual(row['closing_documents'][0]['size'], len(self.pdf))
            self.assertNotIn('content', row['closing_documents'][0])
            endpoint = self.url('/api/invoice-document', self.path, id=row['id'], document_id=payload['document_id'])
            status, headers, body = self.http(endpoint)
            self.assertEqual((status, body), (200, self.pdf))
            self.assertEqual(headers['Content-Type'], 'application/pdf')
            self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
            self.assertTrue(headers['Content-Disposition'].startswith('inline;'))
            self.assertTrue(self.http(endpoint+'&download=1')[1]['Content-Disposition'].startswith('attachment;'))
        listed = json.loads(self.http(self.url('/api/invoices', self.path))[2])['items'][0]
        self.assertEqual(listed['closing_documents'], row['closing_documents'])
        self.assertEqual(manager.order_store().get(self.path), self.owner)
        with self.store.connect() as db:
            original = json.loads(db.execute('SELECT data FROM invoice_history WHERE id=?', (row['id'],)).fetchone()[0])
            self.assertNotIn(documents.BLOCK, original)
            self.assertEqual(db.execute('SELECT content FROM invoice_documents').fetchone()[0], self.pdf)

    def test_paid_is_fifth_exclusive_mark_and_does_not_change_finances_or_documents(self):
        attached = documents.upload(self.store, self.payload())
        active = self.store.save_list_status({**attached, 'value': 'active'})
        paid = self.store.save_list_status({**active, 'value': 'paid'})
        self.assertEqual(paid['list_status'], 'paid')
        self.assertEqual(paid['closing_documents'], attached['closing_documents'])
        self.assertEqual(manager.order_store().get(self.path), self.owner)
        with self.assertRaises(invoices.InvoiceConflict):
            self.store.save_list_status({**active, 'value': 'sent'})
        self.assertEqual(self.store.save_list_status({**paid, 'value': 'none'})['list_status'], 'none')

    def test_retries_do_not_overwrite_later_marks_or_restore_removed_documents(self):
        payload = self.payload()
        attached = documents.upload(self.store, payload)
        paid = self.store.save_list_status({**attached, 'value': 'paid'})
        self.assertEqual(documents.upload(self.store, payload), paid)
        for changes in ({'name': 'Другой.pdf'}, {'content': base64.b64encode(b'other').decode()}):
            with self.assertRaises(invoices.InvoiceConflict):
                documents.upload(self.store, {**payload, **changes})
        removed = documents.set_deleted(self.store, {**paid, 'document_id': payload['document_id']}, True)
        self.assertFalse(removed['closing_documents'])
        self.assertEqual(len(removed['closing_documents_trash']), 1)
        with self.assertRaises(invoices.InvoiceConflict):
            documents.upload(self.store, payload)
        with self.assertRaises(invoices.InvoiceConflict):
            documents.set_deleted(self.store, {**paid, 'document_id': payload['document_id']}, False)
        restored = documents.set_deleted(self.store, {**removed, 'document_id': payload['document_id']}, False)
        self.assertEqual(restored['closing_documents'], attached['closing_documents'])
        self.assertEqual(restored['list_status'], 'paid')

    def test_binding_rejects_other_invoice_path_trash_and_preserves_rename(self):
        payload = self.payload()
        attached = documents.upload(self.store, payload)
        other = self.store.create({'path': self.path, 'id': str(uuid.uuid4())})
        with self.assertRaises(invoices.InvoiceConflict):
            documents.upload(self.store, {**payload, 'id': other['id'], 'revision': other['revision']})
        with self.assertRaises(FileNotFoundError):
            documents.content(self.store, self.path, other['id'], payload['document_id'])
        renamed = self.path + ' новый'
        with self.store.connect() as db:
            db.execute('UPDATE orders SET path=? WHERE id=?', (renamed, self.owner['id']))
            db.execute('UPDATE invoices SET path=? WHERE id=?', (renamed, attached['id']))
        with self.assertRaises(invoices.InvoiceConflict):
            documents.content(self.store, self.path, attached['id'], payload['document_id'])
        self.assertEqual(documents.content(self.store, renamed, attached['id'], payload['document_id'])[0], self.pdf)
        current = self.store.get(renamed, attached['id'])
        removed = self.store.remove({**current, 'confirmed': True})
        with self.assertRaises(invoices.InvoiceConflict):
            documents.content(self.store, renamed, attached['id'], payload['document_id'])
        restored = self.store.restore(removed)
        self.assertEqual(restored['closing_documents'], attached['closing_documents'])

    def test_draft_save_preserves_links_and_new_based_invoice_has_none(self):
        attached = documents.upload(self.store, self.payload())
        changed = {**attached['data'], 'note': 'Правка', documents.BLOCK: {'fake': 'ignore'}}
        saved = self.store.save({**attached, 'data': changed})
        self.assertEqual(saved['closing_documents'], attached['closing_documents'])
        copy = self.store.create({'path': self.path, 'id': str(uuid.uuid4()), 'source': saved['id']})
        self.assertEqual(copy['closing_documents'], [])
        with self.store.connect() as db:
            db.execute("UPDATE invoices SET data=json_set(data,'$._closing_documents.version',2) WHERE id=?", (saved['id'],))
        unknown = self.store.get(self.path, saved['id'])
        self.assertFalse(unknown['closing_documents_editable'])
        with self.assertRaises(ValueError):
            documents.upload(self.store, self.payload(unknown))
        again = self.store.save({**unknown, 'data': {**unknown['data'], 'note': 'Ещё правка'}})
        self.assertEqual(again['data'][documents.BLOCK], unknown['data'][documents.BLOCK])

    def test_validation_conflicts_and_generic_files(self):
        for changes in ({'revision': None}, {'revision': True}, {'revision': 999}):
            with self.assertRaises(invoices.InvoiceConflict):
                documents.upload(self.store, self.payload(**changes))
        for changes in ({'name': '../bad.pdf'}, {'name': '.hidden'}, {'name': 'a\nb'}, {'content': ''}, {'content': 'invalid'}, {'document_id': '../uuid'}):
            with self.assertRaises(ValueError):
                documents.upload(self.store, self.payload(**changes))
        with patch.object(documents, 'MAX_BYTES', 2):
            with self.assertRaises(ValueError):
                documents.upload(self.store, self.payload(content=base64.b64encode(b'abc').decode()))
        generic = self.payload(name='Документ.html', content=base64.b64encode(b'<script>alert(1)</script>').decode())
        saved = documents.upload(self.store, generic)
        status, headers, body = self.http(self.url('/api/invoice-document', self.path, id=saved['id'], document_id=generic['document_id']))
        self.assertEqual(status, 200)
        self.assertEqual(headers['Content-Type'], 'application/octet-stream')
        self.assertTrue(headers['Content-Disposition'].startswith('attachment;'))
        self.assertEqual(body, b'<script>alert(1)</script>')
        stale = self.payload()
        with self.assertRaises(invoices.InvoiceConflict):
            documents.upload(self.store, stale)

    def test_issue_preserves_paid_mark_and_exact_closing_document(self):
        attached = documents.upload(self.store, self.payload())
        data = {**attached['data'], 'items': [{'name': 'Работы', 'unit': 'шт', 'quantity': '1', 'price': '100'}]}
        saved = self.store.save({**attached, 'data': data})
        paid = self.store.save_list_status({**saved, 'value': 'paid'})
        with patch.object(invoices, 'render', return_value=self.pdf):
            issued = self.store.issue(paid)
        self.assertEqual(issued['state'], 'issued')
        self.assertEqual(issued['list_status'], 'paid')
        self.assertEqual(issued['closing_documents'], attached['closing_documents'])
        document_id = attached['closing_documents'][0]['id']
        self.assertEqual(documents.content(self.store, self.path, issued['id'], document_id)[0], self.pdf)

    def test_copy_outbox_retries_without_changing_revision_and_retains_issued_files(self):
        attached = documents.upload(self.store, self.payload())
        key = attached['closing_documents'][0]['id']
        with patch.object(self.store, 'publish_copy', side_effect=OSError('offline')):
            documents.sync(self.store)
        failed = self.store.get(self.path, attached['id'])
        self.assertEqual(failed['revision'], attached['revision'])
        self.assertIn('offline', failed['closing_documents'][0]['sync_error'])
        documents.sync(self.store)
        copied = self.store.get(self.path, attached['id'])
        target = self.root / self.path / '# bills' / copied['closing_documents'][0]['filename']
        self.assertEqual(target.read_bytes(), self.pdf)
        self.assertEqual(copied['closing_documents'][0]['exported'], 1)
        self.assertEqual(copied['revision'], attached['revision'])
        removed = documents.set_deleted(self.store, {**copied, 'document_id': key}, True)
        self.assertEqual(target.read_bytes(), self.pdf)
        restored = documents.set_deleted(self.store, {**removed, 'document_id': key}, False)
        self.assertEqual(self.store.get(self.path, restored['id'])['closing_documents'][0]['exported'], 1)

    def test_copy_outbox_does_not_overwrite_a_conflicting_file(self):
        attached = documents.upload(self.store, self.payload())
        target = self.root / self.path / '# bills' / attached['closing_documents'][0]['filename']
        target.parent.mkdir()
        target.write_bytes(b'keep existing file')
        documents.sync(self.store)
        current = self.store.get(self.path, attached['id'])
        self.assertEqual(current['closing_documents'][0]['exported'], 0)
        self.assertTrue(current['closing_documents'][0]['sync_error'])
        self.assertEqual(target.read_bytes(), b'keep existing file')
        key = attached['closing_documents'][0]['id']
        self.assertEqual(documents.content(self.store, self.path, attached['id'], key)[0], self.pdf)

