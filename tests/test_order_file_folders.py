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

    def test_service_switches_follow_disk_and_require_a_fresh_empty_folder(self):
        route = '/api/order-service-folders'
        order = self.root / self.order
        self.folder(self.order + '/#  DoCs')
        self.folder(self.order + '/# alUm/Пустая подпапка')
        self.file(self.order + '/# pvc/.hidden', b'original')
        (order / '# cdr').symlink_to(self.root / 'missing', target_is_directory=True)
        self.folder(self.order + '/Фото/# freza')
        self.folder(self.order + '/# other')

        def post(snapshot, kind, enabled):
            item = next(item for item in snapshot['folders'] if item['kind'] == kind)
            return self.http(route, 'POST', json.dumps({'path': self.order, 'parent': snapshot['parent'],
                             'kind': kind, 'enabled': enabled, 'revision': item['revision']}),
                             {'Content-Type': 'application/json'})

        listing = manager.read_folder(self.order)
        snapshot = listing['serviceFolders']
        self.assertEqual(snapshot, json.loads(self.http(self.url(route, self.order))[2]))
        switches = {item['kind']: (item['enabled'], bool(item['reason'])) for item in snapshot['folders']}
        self.assertEqual(switches, {'bills': (False, False), 'cdr': (False, True), 'docs': (True, False),
                                    'freza': (False, False), 'cutter': (False, False), 'pvc': (True, True), 'alum': (True, True)})
        for kind, enabled in [('pvc', False), ('alum', False), ('cdr', True)]:
            self.assertEqual(post(snapshot, kind, enabled)[0], 409)
        self.file(self.order + '/#  DoCs/Новый.txt', b'new')
        self.assertEqual(post(snapshot, 'docs', False)[0], 409)
        self.assertEqual((order / '#  DoCs/Новый.txt').read_bytes(), b'new')
        (order / '#  DoCs/Новый.txt').unlink()

        # Inject an external write after the last scan and before the atomic rmdir.
        original_rmdir = manager.os.rmdir

        def fill_before_remove(name, *, dir_fd=None):
            (order / name / 'Внезапный файл.txt').write_bytes(b'keep')
            return original_rmdir(name, dir_fd=dir_fd)

        snapshot = json.loads(self.http(self.url(route, self.order))[2])
        with patch.object(manager.os, 'rmdir', side_effect=fill_before_remove):
            self.assertEqual(post(snapshot, 'docs', False)[0], 409)
        self.assertEqual((order / '#  DoCs/Внезапный файл.txt').read_bytes(), b'keep')
        (order / '#  DoCs/Внезапный файл.txt').unlink()

        snapshot = json.loads(self.http(self.url(route, self.order))[2])
        status, _, body = post(snapshot, 'docs', False)
        self.assertEqual(status, 200, body)
        self.assertFalse((order / '#  DoCs').exists())
        status, _, body = post(json.loads(body), 'freza', True)
        self.assertEqual(status, 200, body)
        listing = manager.read_folder(self.order)
        self.assertEqual([item['name'] for item in listing['orderFileFolders']], ['# freza', '# pvc', '# alUm'])
        self.assertTrue((order / 'Фото/# freza').is_dir())
        self.assertTrue((order / '# other').is_dir())

    def test_service_switches_only_apply_to_customer_orders(self):
        route = '/api/order-service-folders'
        grouped = '03 - Группа/Клиент/2026-11-19 - Работа'
        self.folder(grouped)
        self.assertTrue(manager.read_folder(grouped)['canManageServiceFolders'])
        self.assertEqual(self.http(self.url(route, grouped))[0], 200)
        for path in ('Клиент', self.order + '/Фото', '# glass/2026-11-19 - Заказ',
                     '# work/2026-11-19 - Заказ', '# work/# glass/2026-11-19 - Заказ',
                     '02 - etc/2026/Заказ', '# moneys/# Зп/2026-11-19 - Запись'):
            with self.subTest(path=path):
                self.folder(path)
                self.assertFalse(manager.read_folder(path)['canManageServiceFolders'])
                self.assertEqual(self.http(self.url(route, path))[0], 400)
                self.assertEqual(self.http(route, 'POST', json.dumps({'path': path, 'kind': 'docs', 'enabled': True}),
                                           {'Content-Type': 'application/json'})[0], 400)
                self.assertFalse((self.root / path / '# docs').exists())

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

    def test_document_status_shared_across_folder_views_and_independent_of_comment(self):
        section = '# moneys/# reconciliations/2026-09-28 - Сверка'
        docs = section + '/#  DoCs'
        path = docs + '/Акты/Документ.pdf'
        same_name = '# docs/Документ.pdf'
        outside = self.order + '/# docs2/Документ.pdf'
        hidden = docs + '/!.txt'
        for file in (path, same_name, outside):
            self.file(file, b'%PDF-1.4 original')
        self.file(hidden, manager.order_document.render({}, manager.STATUS_LABELS).encode())
        (self.root / docs / 'link.pdf').symlink_to(self.root / path)
        route = '/api/document-relevance'
        with patch.object(manager, 'DATABASE_ONLY', True):
            listing = manager.read_folder(section)
            self.assertEqual([file['path'] for file in listing['files']], [path])
            document = listing['files'][0]
            initial = document['document_relevance']
            self.assertEqual((initial['value'], initial['revision']), ('none', 'missing'))
            payload = {'path': path, **initial, 'value': 'check'}
            comment = {'path': path, 'comment_key': document['comment_key'], 'comment': 'Строка\nс правками', 'revision': 'missing'}
            self.assertEqual(self.http('/api/file-comment', 'POST', json.dumps(comment))[0], 200)
            status, _, body = self.http(route, 'POST', json.dumps(payload))
            self.assertEqual(status, 200, body)
            saved = json.loads(body)
            self.assertEqual(self.http(route, 'POST', json.dumps({**payload, 'value': 'inactive'}))[0], 409)
            self.assertEqual(self.http(route, 'POST', json.dumps({**payload, 'revision': saved['revision'], 'value': 'wrong'}))[0], 400)
            for view in (section, docs, docs + '/Акты'):
                item = manager.read_folder(view)['files'][0]
                self.assertEqual(item['document_relevance']['value'], 'check')
                self.assertEqual(item['document_relevance']['revision'], saved['revision'])
                self.assertEqual(item['comment'], comment['comment'])
            self.assertEqual(json.loads(self.http(self.url(route, same_name))[2])['value'], 'none')
            for rejected in (outside, hidden, docs + '/link.pdf', None):
                self.assertEqual(self.http(route, 'POST', json.dumps({**payload, 'path': rejected}))[0], 400)
            self.assertNotIn('document_relevance', manager.read_folder(outside.rsplit('/', 1)[0])['files'][0])
            self.assertEqual(self.http(route, 'POST', json.dumps({**saved, 'value': 'none'}))[0], 200)
            self.assertEqual(json.loads(self.http(self.url(route, path))[2])['value'], 'none')
            self.assertEqual((self.root / path).read_bytes(), b'%PDF-1.4 original')
            with manager.metadata_store().connect() as db:
                previous = db.execute('SELECT data FROM metadata_history WHERE identity=?', (saved['revision'].split(':')[0],)).fetchone()
                self.assertEqual(json.loads(json.loads(previous[0])['data'])['value'], 'check')

    def test_document_status_follows_file_through_trash_and_restore(self):
        scope = '# docs/Внутри'
        path = scope + '/Договор.txt'
        self.file(path, b'original')
        route = '/api/document-relevance'
        with patch.object(manager, 'DATABASE_ONLY', True):
            initial = json.loads(self.http(self.url(route, path))[2])
            status, _, body = self.http(route, 'POST', json.dumps({**initial, 'value': 'active'}))
            self.assertEqual(status, 200, body)
            saved = json.loads(body)
            selected = [{'path': path, 'revision': manager.file_trash.revision(self.root / path)}]
            payload = {'path': scope, 'files': selected, 'confirmed': True}
            status, _, body = self.http('/api/files-trash', 'POST', json.dumps(payload))
            self.assertEqual(status, 200, body)
            self.assertIsNone(manager.metadata_store().get('document_relevance', path))
            session = json.loads(body)['session']
            self.assertEqual(self.http('/api/files-trash-restore', 'POST', json.dumps({'session': session}))[0], 200)
            restored = json.loads(self.http(self.url(route, path))[2])
            self.assertEqual(restored['value'], 'active')
            self.assertEqual(restored['revision'].split(':')[0], saved['revision'].split(':')[0])
            self.assertNotEqual(restored['revision'], saved['revision'])
