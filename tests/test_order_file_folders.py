import json
import unittest
from unittest.mock import patch

import test_server as fixtures

manager = fixtures.manager


class OrderFileFolderTests(unittest.TestCase):
    setUp = fixtures.ManagerTests.setUp
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url
    order = 'Клиент/2026-00-00 - Заказ'

    def test_only_three_direct_service_branches_are_scanned_with_nested_files(self):
        for name in ('# cutter/01.dxf', '#FREZA/Глубже/02.txt', '#  DoCs/Глубже/Письмо.txt', '# cutter/!.txt',
                     '# cutter/.hidden', '# cutter/.private/secret.txt',
                     '#  DoCs/.private/secret.txt', 'Фото/# cutter/event.dxf', 'Фото/# docs/event.txt',
                     '# cutters/other.dxf', '# docs2/other.txt', 'root.txt'):
            self.file(self.order + '/' + name, b'original')
        (self.root / self.order / '# cutter/link.txt').symlink_to(self.root / self.order / 'root.txt')
        (self.root / self.order / '#  DoCs/link.txt').symlink_to(self.root / self.order / 'root.txt')
        (self.root / self.order / '#FREZA/link').symlink_to(self.root / self.order / 'Фото', target_is_directory=True)
        with patch.object(manager.os, 'walk', wraps=manager.os.walk) as walk:
            listing = manager.read_folder(self.order)
        self.assertEqual({call.args[0].name for call in walk.call_args_list}, {'# cutter', '#FREZA', '#  DoCs'})
        self.assertEqual([item['name'] for item in listing['orderFileFolders']], ['# cutter', '#FREZA', '#  DoCs'])
        self.assertEqual({file['path'] for file in listing['files']}, {
            self.order + '/# cutter/01.dxf', self.order + '/#FREZA/Глубже/02.txt', self.order + '/#  DoCs/Глубже/Письмо.txt'})
        nested = next(file for file in listing['files'] if file['name'] == 'Письмо.txt')
        self.assertEqual(nested['folder'], '#  DoCs/Глубже')
        self.assertEqual(nested['preview'], 'text')
        self.assertEqual(listing['filesScope'], 'events')
        self.assertIsNone(listing['upload'])

    def test_missing_empty_linked_folders_and_other_roles(self):
        self.assertEqual(manager.read_folder(self.order)['orderFileFolders'], [])
        docs = self.root / self.order / '#docs'
        docs.symlink_to(self.root / '# docs', target_is_directory=True)
        self.assertEqual(manager.read_folder(self.order)['orderFileFolders'], [])
        docs.unlink()
        self.folder(self.order + '/#docs')
        listing = manager.read_folder(self.order)
        self.assertEqual(listing['orderFileFolders'], [{'name': '#docs', 'path': self.order + '/#docs'}])
        self.assertEqual(listing['files'], [])
        self.folder(self.order + '/#freza')
        (self.root / self.order / '# cutter').symlink_to(self.root / '# docs', target_is_directory=True)
        listing = manager.read_folder(self.order)
        self.assertEqual([item['name'] for item in listing['orderFileFolders']], ['#freza', '#docs'])
        self.assertEqual(listing['files'], [])
        self.file('Клиент/# cutter/client.txt', b'client')
        self.file('Клиент/# docs/client.txt', b'client')
        self.assertEqual(manager.read_folder('Клиент')['orderFileFolders'], [])
        self.assertEqual(manager.read_folder(self.order + '/Фото')['orderFileFolders'], [])
        self.folder('# work/# freza/2026-11-06 - Задание/# docs')
        self.assertEqual(manager.read_folder('# work/# freza/2026-11-06 - Задание')['orderFileFolders'], [])

    def test_listing_and_download_preserve_original_and_filename(self):
        path = self.order + '/#  Docs/деталь & #1.txt'
        self.file(path, 'Размер 20×30'.encode())
        original = (self.root / path).read_bytes()
        status, _, body = self.http(self.url('/api/folder', self.order))
        self.assertEqual(status, 200)
        file = json.loads(body)['files'][0]
        self.assertEqual(file['path'], path)
        self.assertTrue(file['comment_key'])
        status, headers, body = self.http(self.url('/api/file', path) + '&download=1')
        self.assertEqual(status, 200)
        self.assertIn('attachment', headers['Content-Disposition'])
        self.assertEqual(body, original)
        self.assertEqual((self.root / path).read_bytes(), original)
