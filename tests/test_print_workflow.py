import json
import unittest
from unittest.mock import patch

import order_folders
from folder_structure import folder_role
import test_server as fixtures

manager = fixtures.manager


class PrintWorkflowTests(unittest.TestCase):
    setUp = fixtures.ManagerTests.setUp
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url

    def test_only_editor_creates_print_tasks_and_order_endpoints_reject_parallel_flow(self):
        manager.DATABASE_ONLY = True
        for section in ('# work/# print', '#work/#print', '# WORK/#  PRINT'):
            self.folder(section)
            opened = manager.read_folder(section)
            self.assertFalse(opened['canCreateOrderFolder'])
            payload = {'path': section, 'date': '2026-10-21', 'title': 'Круг'}
            status, _, _ = self.http('/api/order-folder-create', 'POST', json.dumps(payload))
            self.assertEqual(status, 400)
            self.assertFalse((self.root / section / '2026-10-21 - Круг').exists())
            task = manager.create_print_task(section, 'https://example.com', '620×620', 'Круг')
            self.assertEqual([item['path'] for item in manager.read_folder(section)['files']], [task['path']])
            self.assertEqual(manager.order_store().list(), [])
            old = section + '/2026-10-20 - Вручную'
            self.folder(old)
            self.assertFalse(folder_role(self.root, old)['canRegisterOrder'])
            status, _, _ = self.http('/api/order-add', 'POST', json.dumps({'path': old}))
            self.assertEqual(status, 400)

    def test_nested_documents_and_publications_do_not_create_duplicate_drafts(self):
        manager.DATABASE_ONLY = True
        section = '# work/# print'
        self.folder(section)
        task = manager.create_print_task(section, '', 'Размеры', 'Круг')
        nested = section + '/2026-10-20 - Круг/00 - Макет'
        self.file(nested + '/Описание.txt', b'preserve attachment')
        publication = manager.metadata_store().publish(task['path'], task['revision'], self.root / section, 'Выпущено.txt', b'issued')
        manager.metadata_store().sync()
        opened = manager.read_folder(section)
        self.assertEqual([item['path'] for item in opened['files']], [task['path']])
        self.assertEqual(opened['warnings'], [])
        with self.assertRaises(ValueError):
            manager.read_print_task(publication['path'])
        with self.assertRaises(ValueError):
            manager.create_print_task(nested, '', 'Не создавать здесь', 'Вложенное')
        with manager.metadata_store().connect() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM metadata_records WHERE kind='print'").fetchone()[0], 1)
        self.assertEqual((self.root / nested / 'Описание.txt').read_bytes(), b'preserve attachment')

    def test_existing_registered_folder_keeps_identity_note_todos_and_files(self):
        manager.DATABASE_ONLY = True
        section = '# work/# print'
        path = section + '/2026-10-20 - Прежний заказ'
        self.folder(path)
        with patch('orders.folder_role', return_value={'canRegisterOrder': True}):
            card = manager.order_store().add(path, {'title': 'Прежнее название', 'status': 'process', 'note': 'Сохранить заметку',
                'extra_blocks': {'Задачи': '- [ ] Согласовать макет'}})
        self.file(path + '/original.cdr', b'original bytes')
        opened = manager.read_folder(section)
        self.assertEqual([item['path'] for item in opened['directories']], [path])
        self.assertFalse(opened['canCreateOrderFolder'])
        preserved = manager.read_folder(path)['order']
        for field in ('id', 'title', 'note', 'status', 'todo_items', 'revision'):
            self.assertEqual(preserved[field], card[field])
        self.assertEqual((self.root / path / 'original.cdr').read_bytes(), b'original bytes')
        self.assertEqual(opened['files'], [])
