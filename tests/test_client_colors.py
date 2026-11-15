import json
import unittest

import test_server


class ClientColorTests(unittest.TestCase):
    setUp = test_server.ManagerTests.setUp
    tearDown = test_server.ManagerTests.tearDown
    folder = test_server.ManagerTests.folder
    file = test_server.ManagerTests.file
    http = test_server.ManagerTests.http
    url = test_server.ManagerTests.url

    def test_manual_colors_are_independent_versioned_and_follow_rename(self):
        self.folder('01 - Группа/Клиент')
        root, grouped = 'Клиент', '01 - Группа/Клиент'

        def read(path):
            status, _, body = self.http(self.url('/api/client-color', path))
            self.assertEqual(status, 200, body)
            return json.loads(body)

        def save(path, color, revision):
            status, _, body = self.http('/api/client-color', 'POST', json.dumps({
                'path': path, 'color': color, 'revision': revision,
            }), {'Content-Type': 'application/json'})
            return status, json.loads(body)

        self.assertEqual(read(root), {'color': None, 'revision': 'missing', 'editable': True})
        self.assertEqual(read(grouped)['color'], None)
        self.assertEqual(save(root, '#12ab3F', 'missing')[0], 200)
        self.assertEqual(save(grouped, '#8b1190', 'missing')[0], 200)
        self.assertEqual(save(root, '#ffffff', 'missing')[0], 409)
        self.assertEqual(save(root, '#strange', read(root)['revision'])[0], 400)
        self.assertEqual(save(root + '/2026', '#ffffff', 'missing')[0], 400)
        catalog = json.loads(self.http('/api/orders')[2])['client_colors']
        self.assertEqual(catalog, {root: '#12ab3f', grouped: '#8b1190'})
        self.assertEqual(json.loads(self.http('/api/hidden-orders')[2])['client_colors'], catalog)

        _, _, body = self.http(self.url('/api/folder-rename', root))
        proposal = json.loads(body)
        new_path = 'Новое имя'
        status, _, body = self.http('/api/folder-rename', 'POST', json.dumps({
            'path': root, 'name': new_path, 'revision': proposal['revision'],
        }))
        self.assertEqual(status, 200, body)
        saved = read(new_path)
        self.assertEqual(saved['color'], '#12ab3f')
        status, cleared = save(new_path, None, saved['revision'])
        self.assertEqual(status, 200, cleared)
        self.assertNotEqual(cleared['revision'], saved['revision'])
        self.assertIsNone(cleared['color'])
        self.assertEqual(json.loads(self.http('/api/orders')[2])['client_colors'], {grouped: '#8b1190'})
