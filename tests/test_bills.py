"""Общий список счетов не читает документы и не распределяет входящие файлы."""
import json
import os
from pathlib import Path
import unittest
import uuid
from unittest.mock import patch

from folder_structure import folder_role
import order_folders
import test_external_invoices as fixtures

manager = fixtures.manager


class BillsTests(unittest.TestCase):
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
    section = '# moneys/# bills'

    def test_catalog_collects_created_and_attached_without_plans_or_trash(self):
        store = self.store()
        draft = store.create({'path': self.path, 'id': str(uuid.uuid4())})
        issued = store.create({'path': self.path, 'id': str(uuid.uuid4())})
        external = store.upload(self.payload())
        removed = store.upload(self.payload())
        plan = store.plan({'path': self.path, 'id': str(uuid.uuid4()), 'date': '2026-11-08'})
        second_path = '01 - Группа/Другой клиент/Объект/2026-11-08 - Работа'
        self.folder(second_path)
        manager.order_store().add(second_path, {'title': 'Монтаж', 'status': 'new'})
        second = store.create({'path': second_path, 'id': str(uuid.uuid4())})
        with store.connect() as db:
            data = json.loads(db.execute('SELECT data FROM invoices WHERE id=?', (issued['id'],)).fetchone()[0])
            data.update(total=12345, _list_status='sent')
            db.execute("UPDATE invoices SET state='issued',data=? WHERE id=?", (json.dumps(data), issued['id']))
            data = json.loads(db.execute('SELECT data FROM invoices WHERE id=?', (removed['id'],)).fetchone()[0])
            data['_trash'] = {'state': 'pending', 'token': str(uuid.uuid4())}
            db.execute('UPDATE invoices SET data=? WHERE id=?', (json.dumps(data), removed['id']))
            before = [tuple(row) for row in db.execute('SELECT * FROM invoices ORDER BY id')]
        owner = manager.order_store().get(self.path)
        with patch.object(Path, 'read_bytes', side_effect=AssertionError('Document read')), patch.object(os, 'scandir', side_effect=AssertionError('Folder scan')):
            status, _, body = self.http('/api/invoice-catalog')
        self.assertEqual(status, 200, body)
        rows = {item['id']: item for item in json.loads(body)['items']}
        self.assertEqual(set(rows), {draft['id'], issued['id'], external['id'], second['id']})
        self.assertNotIn(plan['id'], rows)
        self.assertEqual(rows[second['id']]['client'], 'Другой клиент')
        self.assertEqual(rows[second['id']]['client_path'], '01 - Группа/Другой клиент')
        self.assertEqual(rows[draft['id']]['client_path'], 'Клиент')
        self.assertEqual(rows[second['id']]['order_title'], 'Монтаж')
        self.assertEqual(rows[issued['id']]['total'], 12345)
        self.assertEqual(rows[issued['id']]['list_status'], 'sent')
        self.assertEqual(rows[draft['id']]['edit_action'], 'edit')
        self.assertEqual(rows[issued['id']]['edit_action'], 'copy')
        self.assertIsNone(rows[external['id']]['edit_action'])
        self.assertEqual(rows[external['id']]['comment'], 'Оплата за вывеску')
        self.assertIsNone(rows[external['id']]['total'])
        self.assertTrue(all('pdf' not in row and 'data' not in row for row in rows.values()))
        with store.connect() as db:
            self.assertEqual([tuple(row) for row in db.execute('SELECT * FROM invoices ORDER BY id')], before)
        self.assertEqual(manager.order_store().get(self.path), owner)
        self.assertEqual(self.http('/api/invoice-catalog', 'HEAD')[0], 200)

    def test_catalog_uses_metadata_when_document_root_is_unavailable(self):
        draft = self.store().create({'path': self.path, 'id': str(uuid.uuid4())})
        with self.store().connect() as db:
            data = draft['data']
            data['_list_status'] = {'unknown': True}
            db.execute('UPDATE invoices SET data=? WHERE id=?', (json.dumps(data), draft['id']))
            db.execute('DELETE FROM orders WHERE path=?', (self.path,))
        with patch.object(manager.order_store().__class__, 'target', side_effect=AssertionError('Documents unavailable')):
            rows = self.store().catalog()
        self.assertEqual(rows[0]['order_title'], Path(self.path).name)
        self.assertIsNone(rows[0]['list_status'])
        self.assertIsNone(rows[0]['edit_action'])

    def test_removed_owner_keeps_invoices_visible_without_editor_actions(self):
        draft = self.store().create({'path': self.path, 'id': str(uuid.uuid4())})
        external = self.store().upload(self.payload())
        owner = manager.order_store().get(self.path)
        manager.order_store().remove({'path': self.path, 'revision': owner['revision'], 'confirmed': True})
        rows = self.store().catalog()
        self.assertEqual({item['id'] for item in rows}, {draft['id'], external['id']})
        self.assertTrue(all(item['edit_action'] is None for item in rows))

    def test_catalog_distinguishes_same_client_names_in_separate_groups(self):
        first = self.store().create({'path': self.path, 'id': str(uuid.uuid4())})
        second_path = '02 - Группа/Клиент/2026-11-08 - Другой заказ'
        self.folder(second_path)
        manager.order_store().add(second_path, {'title': 'Другой заказ', 'status': 'new'})
        second = self.store().create({'path': second_path, 'id': str(uuid.uuid4())})
        rows = {item['id']: item for item in self.store().catalog()}
        self.assertEqual(rows[first['id']]['client'], rows[second['id']]['client'])
        self.assertEqual(rows[first['id']]['client_path'], 'Клиент')
        self.assertEqual(rows[second['id']]['client_path'], '02 - Группа/Клиент')

    def test_bills_roles_exclude_registration_creation_and_order_bills(self):
        for section in (self.section, '#MONEYS/#BILLS', '#moneys/# Bills'):
            self.folder(section + '/#InBoX/Подпапка')
            for relative, kind in ((section, 'bills_root'), (section + '/#InBoX', 'bills_inbox'),
                                   (section + '/#InBoX/Подпапка', 'bills_contents')):
                role = folder_role(self.root, relative)
                self.assertEqual(role['folderKind'], kind)
                self.assertFalse(role['canRegisterOrder'])
                self.assertFalse(manager.read_folder(relative)['canCreateOrderFolder'])
                with self.assertRaises(ValueError):
                    order_folders.create(self.root, relative, '2026-11-08', 'Запись', store=manager.order_store())
        self.folder(self.path + '/# bills')
        self.assertEqual(folder_role(self.root, self.path + '/# bills')['folderKind'], 'service')

    def test_inbox_lists_only_direct_visible_files_without_import_or_changes(self):
        inbox = self.section + '/# inbox'
        self.file(inbox + '/Счёт.pdf', self.pdf)
        self.file(inbox + '/прочее.txt', b'hello')
        self.file(inbox + '/.hidden.pdf', self.pdf)
        self.file(inbox + '/Вложено/Не входящий.pdf', self.pdf)
        (self.root / inbox / 'Ссылка.pdf').symlink_to(self.root / inbox / 'Счёт.pdf')
        before = self.store().catalog()
        with patch.object(Path, 'read_bytes', side_effect=AssertionError('File content read')):
            root = manager.read_folder(self.section)
            folder = manager.read_folder(inbox)
        self.assertEqual(root['folderKind'], 'bills_root')
        self.assertEqual(root['files'], [])
        self.assertEqual([item['name'] for item in root['directories']], ['# inbox'])
        self.assertEqual({item['name'] for item in folder['files']}, {'Счёт.pdf', 'прочее.txt'})
        self.assertEqual(folder['folderCount'], 1)
        self.assertFalse(folder['canRegisterOrder'])
        self.assertIsNone(folder['upload'])
        self.assertEqual(self.store().catalog(), before)
        self.assertEqual((self.root / inbox / 'Счёт.pdf').read_bytes(), self.pdf)


if __name__ == '__main__':
    unittest.main()
