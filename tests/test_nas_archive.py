import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import nas_archive
from nas_archive import mounted_volume
import test_server as fixtures

manager = fixtures.manager


class NasArchiveTests(unittest.TestCase):
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url
    order = 'Клиент/Объект/2026-11-20 - Архив # 1'

    def setUp(self):
        fixtures.ManagerTests.setUp(self)
        self.folder(self.order)
        self.volume = self.base / 'Safe'
        self.archive_root = self.volume / 'Zigzag-archive'
        self.archive_root.mkdir(parents=True)
        mount = patch.object(nas_archive, 'mounted_volume', return_value=(self.volume, self.volume.stat().st_dev, 'smb://TNAS.local/Safe'))
        self.mount = mount.start()
        self.addCleanup(mount.stop)
        self.target = self.archive_root / self.order / '# nas'

    def status(self, path=None):
        status, _, body = self.http(self.url('/api/order-nas', path or self.order))
        self.assertEqual(status, 200, body)
        return json.loads(body)

    def post(self, route, payload, headers=None):
        return self.http(route, 'POST', json.dumps(payload), headers or {'Content-Type': 'application/json', 'X-Manager-Nas': '1'})

    def toggle(self, state, enabled, path=None):
        return self.post('/api/order-nas', {'path': path or self.order, 'revision': state['revision'], 'enabled': enabled})

    def test_nas_folder_is_created_under_the_exact_order_path_and_only_empty_can_be_removed(self):
        initial = self.status()
        self.assertFalse(initial['enabled'])
        self.assertFalse(self.target.exists())
        status, _, body = self.toggle(initial, True)
        self.assertEqual(status, 200, body)
        created = json.loads(body)
        self.assertTrue(created['enabled'])
        self.assertTrue(created['url'].startswith('smb://TNAS.local/Safe/Zigzag-archive/'))
        self.assertTrue(created['url'].endswith('%23%201/%23%20nas'))
        self.assertEqual(created['finder_path'], str(self.target))
        self.assertTrue(self.target.is_dir())
        self.assertFalse((self.root / self.order / '# nas').exists())
        self.assertEqual(manager.read_folder(self.order)['files'], [])
        hidden = self.target / '.large-archive'
        hidden.write_bytes(b'original')
        self.assertEqual(self.toggle(created, False)[0], 409)
        locked = self.status()
        self.assertTrue(locked['enabled'])
        self.assertEqual(locked['reason'], 'Папка NAS не пуста')
        self.assertEqual(locked['url'], created['url'])
        self.assertEqual(self.toggle(locked, False)[0], 409)
        self.assertEqual(hidden.read_bytes(), b'original')
        hidden.unlink()
        self.assertEqual(self.toggle(self.status(), False)[0], 200)
        self.assertFalse(self.target.exists())
        self.assertTrue(self.target.parent.is_dir())

    def test_archive_binding_survives_renaming_and_is_not_reused_by_another_order(self):
        result, _, body = self.toggle(self.status(), True)
        self.assertEqual(result, 200, body)
        address = json.loads(body)['url']
        (self.target / 'Archive.zip').write_bytes(b'original')
        store = manager.order_store()
        preview = manager.folder_rename.preview(store, self.order)
        moved = manager.folder_rename.rename(store, {**preview, 'name': '2026-11-20 - Новое имя'})['path']
        self.assertEqual(self.status(moved)['url'], address)
        self.folder(self.order)
        self.assertFalse(self.status()['url'])
        self.assertIn('закреплён', self.status()['reason'])
        self.assertEqual((self.target / 'Archive.zip').read_bytes(), b'original')

    def test_open_finder_uses_the_existing_archive_mount_path_after_order_rename(self):
        route = '/api/order-nas-open'
        with patch.object(nas_archive.subprocess, 'run') as command:
            self.assertEqual(self.post(route, {'path': self.order})[0], 409)
            command.assert_not_called()
            self.assertEqual(self.toggle(self.status(), True)[0], 200)
            (self.target / 'Archive.zip').write_bytes(b'original')
            store = manager.order_store()
            preview = manager.folder_rename.preview(store, self.order)
            moved = manager.folder_rename.rename(store, {**preview, 'name': '2026-11-20 - Другое имя'})['path']
            status, _, body = self.post(route, {'path': moved, 'finder_path': str(self.root)})
            self.assertEqual(status, 200, body)
            command.assert_called_once_with(['/usr/bin/open', '-a', 'Finder', str(self.target)],
                                            check=True, capture_output=True, timeout=8)
            self.assertEqual((self.target / 'Archive.zip').read_bytes(), b'original')

    def test_settings_conflicts_blocked_paths_and_unmounted_share(self):
        settings = json.loads(self.http('/api/nas-settings')[2])
        self.assertEqual(settings, {'root': '/Safe/Zigzag-archive', 'revision': 'missing'})
        for path in ('/Safe/../ elsewhere', '/Safe', 'http://nas/Safe', '/Safe//archive', '/Safe/./archive', '/Safe/ar\x00chive'):
            self.assertEqual(self.post('/api/nas-settings', {**settings, 'root': path})[0], 400)
        initial = self.status()
        self.assertEqual(self.post('/api/nas-settings', {**settings, 'root': '/Safe/Other/'})[0], 200)
        self.assertEqual(self.post('/api/nas-settings', settings)[0], 409)
        self.assertEqual(self.toggle(initial, True)[0], 409)
        self.assertFalse((self.volume / 'Other').exists())
        (self.volume / 'Other').symlink_to(self.root, target_is_directory=True)
        self.assertIsNone(self.status()['revision'])
        self.assertFalse((self.root / self.order / '# nas').exists())
        self.mount.side_effect = FileNotFoundError('Том не подключён')
        self.assertEqual(self.status()['reason'], 'Том не подключён')
        self.assertEqual(self.http(self.url('/api/order-nas', self.order + '/# docs'))[0], 400)
        self.folder('# work/# glass/2026-11-20 - Заказ')
        self.assertEqual(self.http(self.url('/api/order-nas', '# work/# glass/2026-11-20 - Заказ'))[0], 400)
        self.assertEqual(self.post('/api/order-nas', {}, {'Content-Type': 'application/json'})[0], 403)

    def test_smb_mount_marker_cannot_point_to_an_ordinary_local_directory(self):
        marker = f'//user@TNAS._smb._tcp.local/Safe on {self.volume} (smbfs, nodev)'
        with patch.object(nas_archive, 'VOLUMES', self.base), patch.object(nas_archive.subprocess, 'run') as run:
            run.return_value.stdout = marker
            with self.assertRaises(FileNotFoundError):
                mounted_volume('Safe')
            with patch.object(nas_archive.Path, 'stat', side_effect=[SimpleNamespace(st_dev=19), SimpleNamespace(st_dev=12)]):
                self.assertEqual(mounted_volume('Safe'), (self.volume, 19, 'smb://TNAS.local/Safe'))
