import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import inbox_folder
import test_server as fixtures


class InboxFolderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()

    def tearDown(self):
        self.temp.cleanup()

    def test_missing_and_empty_folder_do_not_create_anything(self):
        self.assertEqual(inbox_folder.snapshot(self.root), {'path': '', 'count': 0, 'error': ''})
        self.assertEqual(list(self.root.iterdir()), [])
        (self.root / '# inbox').mkdir()
        self.assertEqual(inbox_folder.snapshot(self.root), {'path': '# inbox', 'count': 0, 'error': ''})

    def test_counts_only_direct_visible_files_without_reading_contents_or_nested_folders(self):
        folder = self.root / '#inbox'
        folder.mkdir()
        for name in ('Фото.jpg', 'Счёт #1.pdf', '.DS_Store', '.скрытый'):
            (folder / name).write_bytes(b'original')
        nested = folder / 'Вложенные'
        nested.mkdir()
        (nested / 'Внутри.txt').write_bytes(b'nested')
        (folder / 'Ссылка').symlink_to(nested / 'Внутри.txt')
        (folder / 'Папка-ссылка').symlink_to(nested, target_is_directory=True)
        (folder / 'Нет файла').symlink_to(folder / 'missing')
        os.mkfifo(folder / 'pipe')
        scan = os.scandir
        visited = []
        def only_direct(path):
            visited.append(Path(path))
            self.assertIn(Path(path), (self.root, folder))
            return scan(path)
        with patch.object(inbox_folder.os, 'scandir', side_effect=only_direct), \
                patch.object(Path, 'open', side_effect=AssertionError('No document reads')):
            self.assertEqual(inbox_folder.snapshot(self.root), {'path': '#inbox', 'count': 2, 'error': ''})
        self.assertEqual(visited, [self.root, folder])
        (folder / 'Фото.jpg').unlink()
        self.assertEqual(inbox_folder.snapshot(self.root)['count'], 1)
        (folder / 'Счёт #1.pdf').unlink()
        self.assertEqual(inbox_folder.snapshot(self.root)['count'], 0)

    def test_root_only_and_symlinks_never_followed(self):
        other = self.root / 'Клиент'
        (other / '#inbox').mkdir(parents=True)
        (other / '#inbox' / 'nested.txt').write_bytes(b'x')
        (self.root / '#inbox').symlink_to(other / '#inbox', target_is_directory=True)
        self.assertEqual(inbox_folder.snapshot(self.root)['count'], 0)
        self.assertEqual(inbox_folder.snapshot(self.root)['path'], '')

    def test_ambiguous_names_and_unreadable_folder_are_unavailable_not_empty(self):
        for name in ('#inbox', '# INBOX'):
            (self.root / name).mkdir()
        result = inbox_folder.snapshot(self.root)
        self.assertIsNone(result['count'])
        self.assertTrue(result['error'])
        (self.root / '# INBOX').rmdir()
        scan = os.scandir
        def denied(path):
            if Path(path) != self.root:
                raise PermissionError('denied')
            return scan(path)
        with patch.object(inbox_folder.os, 'scandir', side_effect=denied):
            result = inbox_folder.snapshot(self.root)
        self.assertIsNone(result['count'])
        self.assertTrue(result['error'])


class InboxFolderHTTPTests(unittest.TestCase):
    setUp = fixtures.ManagerTests.setUp
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http

    def test_count_is_independent_of_telegram_and_finder_opens_the_exact_folder(self):
        manager = fixtures.manager
        self.file('# inbox/Документ.pdf', b'%PDF-test')
        with patch.object(manager.telegram_inbox, 'snapshot', side_effect=AssertionError('No Telegram access')):
            status, _, body = self.http('/api/inbox-folder')
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertEqual(data, {'path': '# inbox', 'count': 1, 'error': ''})
        with patch.object(manager.subprocess, 'Popen') as opener:
            status, _, _ = self.http('/api/open', 'POST', json.dumps({'path': data['path']}))
        self.assertEqual(status, 200)
        opener.assert_called_once_with(['open', str(self.root / '# inbox')])
        self.assertFalse(manager.DATA_DIR.exists())
