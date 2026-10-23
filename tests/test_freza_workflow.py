import io
import json
import struct
import unittest
import zipfile
from unittest.mock import patch

import file_uploads
import order_folders
import test_database_storage as fixtures
from test_sketches import PNG

manager = fixtures.manager


class FrezaWorkflowTests(unittest.TestCase):
    setUp = fixtures.DatabaseStorageTests.setUp
    tearDown = fixtures.DatabaseStorageTests.tearDown
    folder = fixtures.DatabaseStorageTests.folder
    file = fixtures.DatabaseStorageTests.file
    http = fixtures.DatabaseStorageTests.http
    url = fixtures.DatabaseStorageTests.url

    def test_new_task_has_direct_uploads_and_no_events_or_service_folders(self):
        for section in ('# work/# freza', '#work/#FREZA', '# WORK/#  Freza'):
            self.folder(section)
            self.assertTrue(manager.read_folder(section)['frezaSection'])
            created = order_folders.create(self.root, section, '2026-10-23', 'Лавфиш', store=self.store)
            path = created['path']
            self.assertEqual(list((self.root / path).iterdir()), [])
            before = self.store.get(path)
            opened = manager.read_folder(path)
            self.assertTrue(opened['frezaTask'])
            self.assertFalse(opened['canCreateEventFolder'])
            self.assertFalse(opened['hasEventTrash'])
            self.assertEqual(opened['filesScope'], 'folder')
            self.assertIsNotNone(opened['upload'])
            for body in (b'original CDR', b'new CDR'):
                file_uploads.receive(self.store, path, opened['upload']['token'], 'cut.cdr', io.BytesIO(body), len(body))
            self.assertEqual((self.root / path / 'cut.cdr').read_bytes(), b'original CDR')
            self.assertEqual((self.root / path / 'cut (2).cdr').read_bytes(), b'new CDR')
            self.assertEqual(self.store.get(path), before)
            status, _, _ = self.http(self.url('/api/event-folders', path))
            self.assertEqual(status, 400)
            status, _, _ = self.http('/api/event-folder-create', 'POST', json.dumps({'path': path, 'title': 'Лишнее', 'revision': 'old'}))
            self.assertEqual(status, 400)
            self.assertFalse((self.root / path / '00 - Лишнее').exists())
        # Other suppliers and ordinary orders still require events for uploads.
        for path in (self.order, '# work/# laser/2026-10-23 - Лавфиш'):
            self.folder(path)
            self.assertFalse(file_uploads.available(self.root, path))
            self.assertTrue(manager.read_folder(path)['canCreateEventFolder'])

    def test_old_task_lists_direct_and_nested_files_without_changing_records(self):
        path = '# work/# freza/2026-10-23 - лавфиш'
        event = path + '/00 - на фрезу'
        self.file(event + '/шаблоны.cdr', b'original CDR')
        self.file(path + '/preview.png', PNG)
        card = self.store.add(path, {'title': 'Лавфиш', 'note': 'Сохранить', 'status': 'process'})
        note = manager.folder_note_store().read(event)
        note = manager.folder_note_store().save({'path': event, 'revision': note['revision'], 'note': 'Прежняя заметка',
                                                'todo_items': [{'text': 'Проверить', 'done': False}]})
        comment = self.meta.save_comment(self.root / event / 'шаблоны.cdr', 'Фреза 3 мм', 'missing')
        with patch.object(manager.icloud_access, 'read_bytes', side_effect=AssertionError('Listing must not read originals')):
            section = manager.read_folder('# work/# freza')
            opened = manager.read_folder(path)
        self.assertEqual([item['path'] for item in section['directories']], [path])
        self.assertEqual({item['path'] for item in opened['files']}, {path + '/preview.png', event + '/шаблоны.cdr'})
        cdr = next(item for item in opened['files'] if item['preview'] == 'cdr')
        self.assertEqual(cdr['comment'], comment['comment'])
        self.assertNotIn('eventRelevance', opened['directories'][0])
        self.assertEqual(self.store.get(path), card)
        self.assertEqual(manager.folder_note_store().get(event), note)
        self.assertEqual((self.root / event / 'шаблоны.cdr').read_bytes(), b'original CDR')

    def test_lazy_cdr_cover_and_file_preview_preserve_original_and_handle_missing_preview(self):
        task = '# work/# freza/2026-10-23 - лавфиш'
        path = task + '/00 - на фрезу/шаблоны.cdr'
        self.folder(task + '/00 - на фрезу')
        with zipfile.ZipFile(self.root / path, 'w') as archive:
            archive.writestr('previews/thumbnail.png', PNG)
            archive.writestr('content/riffData.cdr', b'original document')
        original = (self.root / path).read_bytes()
        for relative in (task, path):
            status, headers, body = self.http(self.url('/api/freza-preview', relative))
            self.assertEqual(status, 200, body)
            self.assertEqual(headers['Content-Type'], 'image/png')
            self.assertEqual(body, PNG)
        self.assertEqual((self.root / path).read_bytes(), original)
        self.file(task + '/preview.png', PNG)
        self.assertEqual(manager.freza_preview_target(task), self.root / task / 'preview.png')
        for relative in ('# work/# freza', self.order + '/fake.cdr', task + '/.secret.cdr'):
            status, _, _ = self.http(self.url('/api/freza-preview', relative))
            self.assertEqual(status, 400)
        self.file(task + '/bad.cdr', b'not a zip')
        status, _, _ = self.http(self.url('/api/freza-preview', task + '/bad.cdr'))
        self.assertEqual(status, 400)

    def test_corel_bmp_thumbnail_is_converted_locally_without_changing_document(self):
        task = '# work/# freza/2026-10-23 - Лавфиш'
        path = task + '/шаблоны.cdr'
        self.folder(task)
        bmp = (b'BM' + struct.pack('<IHHI', 58, 0, 0, 54) +
               struct.pack('<IiiHHIIiiII', 40, 1, 1, 1, 24, 0, 4, 0, 0, 0, 0) + b'\x33\x77\x22\x00')
        for thumbnail in (bmp, PNG):
            with self.subTest(format=thumbnail[:2]):
                with zipfile.ZipFile(self.root / path, 'w') as archive:
                    archive.writestr('metadata/thumbnails/thumbnail.bmp', thumbnail)
                original = (self.root / path).read_bytes()
                status, headers, body = self.http(self.url('/api/freza-preview', path))
                self.assertEqual(status, 200, body)
                self.assertEqual(headers['Content-Type'], 'image/png')
                self.assertTrue(body.startswith(b'\x89PNG\r\n\x1a\n'))
                self.assertEqual((self.root / path).read_bytes(), original)
        (self.root / task / 'link.cdr').symlink_to(self.root / path)
        status, _, _ = self.http(self.url('/api/freza-preview', task + '/link.cdr'))
        self.assertEqual(status, 400)
