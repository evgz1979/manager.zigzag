import errno
import json
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import patch
import zipfile

import thumbnail_cache as thumbs
from test_pdf_preview import sample_pdf
from test_sketches import PNG
import test_server as fixtures

manager = fixtures.manager
JPEG = b'\xff\xd8\xff' + b'x' * 150


class ThumbnailTests(unittest.TestCase):
    setUp = fixtures.ManagerTests.setUp
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url

    def cache(self):
        return manager.thumbnail_store()

    def observe(self, path='Фото/кадр.mp4', content=b'video', requested=False):
        self.file(path, content)
        target = self.root / path
        self.cache().observe([(path, target.stat())], requested=requested)
        return self.cache().next_item()

    def test_cache_is_outside_documents_and_http_never_reads_original(self):
        item = self.observe()
        self.cache().finish(item, JPEG)
        self.assertEqual(self.cache().database.parent, manager.DATA_DIR)
        self.assertFalse(list(self.root.glob('**/thumbnails*.sqlite3')))
        with patch.object(thumbs, 'source', side_effect=AssertionError('No source access')), \
             patch.object(manager, 'safe_path', side_effect=AssertionError('No iCloud stat')):
            status, headers, body = self.http(self.url('/api/thumbnail', item['path'], v=item['signature']))
            self.assertEqual((status, body), (200, JPEG))
            self.assertIn('immutable', headers['Cache-Control'])
            status, _, body = self.http('/api/thumbnails', 'POST', json.dumps({'paths': [item['path']]}))
            self.assertEqual(json.loads(body)['items'][0]['state'], 'ready')
        with self.assertRaisesRegex(ValueError, 'вне каталога'):
            thumbs.ThumbnailCache(self.root, self.root / 'cache')

    def test_changed_file_invalidates_preview_and_rejects_late_result(self):
        item = self.observe()
        self.cache().finish(item, JPEG)
        new = self.observe(content=b'new longer video')
        self.assertNotEqual(new['signature'], item['signature'])
        self.cache().finish(item, JPEG)  # Late result from a previous generation.
        self.assertIsNone(self.cache().image(item['path']))
        self.cache().finish(new, JPEG + b'new')
        self.assertIsNone(self.cache().image(item['path'], item['signature']))
        self.assertEqual(self.cache().image(item['path'], new['signature'])[0], JPEG + b'new')
        self.assertEqual(self.http(self.url('/api/thumbnail', item['path'], v=item['signature']))[0], 202)

    def test_error_backoff_is_not_reset_by_open_folder_or_polling(self):
        item = self.observe(requested=True)
        self.cache().finish(item, error='iCloud unavailable')
        self.cache().observe([(item['path'], (self.root / item['path']).stat())], requested=True)
        self.cache().items([item['path']])
        self.assertIsNone(self.cache().next_item())
        other = self.observe('Фото/другое.mp4')
        self.assertEqual(other['path'], 'Фото/другое.mp4')
        with self.cache().connect() as db:
            self.assertGreater(db.execute('SELECT retry_at FROM thumbnails WHERE path=?', (item['path'],)).fetchone()[0], 0)

    def test_requested_file_has_priority_over_background_backlog(self):
        self.observe('Фото/старое.mp4')
        item = self.observe('Фото/нужное.mp4', requested=True)
        self.assertEqual(item['path'], 'Фото/нужное.mp4')

    def test_scan_skips_links_hidden_and_cdr_backups_and_reconciles_removed_files(self):
        self.file('Фото/видно.png', PNG)
        self.file('.history/hidden.png', PNG)
        self.file('Фото/Backup_of_drawing.cdr', b'backup')
        (self.root / 'Фото/link.png').symlink_to(self.root / 'Фото/видно.png')
        (self.root / 'alias').symlink_to(self.root / 'Фото', target_is_directory=True)
        self.cache().scan(threading.Event())
        paths = {row['path'] for row in self.cache().items(['Фото/видно.png'])}
        self.assertIn('Фото/видно.png', paths)
        with self.cache().connect() as db:
            names = [row['path'] for row in db.execute('SELECT path FROM thumbnails')]
        self.assertFalse(any('.history' in path or 'link.png' in path or 'alias/' in path or 'Backup' in path for path in names))
        (self.root / 'Фото/видно.png').unlink()
        self.cache().scan(threading.Event())
        self.assertEqual(self.cache().items(['Фото/видно.png'])[0]['state'], 'missing')

    def test_cloud_directory_error_keeps_ready_preview(self):
        item = self.observe()
        self.cache().finish(item, JPEG)

        def failed_walk(root, **kwargs):
            kwargs['onerror'](OSError(errno.EDEADLK, 'iCloud pending'))
            return iter(())

        with patch.object(thumbs.os, 'walk', side_effect=failed_walk):
            self.cache().scan(threading.Event())
        self.assertEqual(self.cache().image(item['path'])[0], JPEG)
        self.assertIn('iCloud pending', self.cache().status()['scan_error'])

    def test_invalid_paths_and_large_batches_do_not_escape_cache(self):
        for path in ('../secret.png', '/secret.png', '.hidden/a.png', 'Фото/.secret.png'):
            self.assertEqual(self.http(self.url('/api/thumbnail', path))[0], 400)
        for paths in ('not a list', ['x'] * 121):
            self.assertEqual(self.http('/api/thumbnails', 'POST', json.dumps({'paths': paths}))[0], 400)
        self.assertEqual(self.http('/api/thumbnail-status')[0], 200)

    def test_folder_listing_enqueues_video_without_reading_its_bytes(self):
        path = 'Клиент/2026-00-00 - Заказ/Фото/ролик.mp4'
        self.file(path, b'video bytes')
        with patch.object(thumbs, 'generate', side_effect=AssertionError('Rendering belongs to worker')):
            listing = manager.read_folder(str(Path(path).parent))
        video = next(file for file in listing['files'] if file['path'] == path)
        self.assertEqual(video['preview'], 'video')
        self.assertEqual(video['thumbnail_key'], thumbs.signature((self.root / path).stat()))
        self.assertEqual(self.cache().items([path])[0]['state'], 'pending')

    def test_changed_source_during_generation_is_not_published(self):
        item = self.observe()

        def render(command, stop):
            Path(command[2]).write_bytes(JPEG)
            (self.root / item['path']).write_bytes(b'changed while rendering')

        with patch.object(thumbs, 'run_renderer', side_effect=render):
            thumbs.generate(self.cache(), item, Path('/renderer'), threading.Event())
        self.assertIsNone(self.cache().image(item['path']))
        self.assertNotEqual(self.cache().next_item()['signature'], item['signature'])

    def test_cover_prefix_does_not_match_neighbor_folder(self):
        item = self.observe('Фреза/job2/cover.png', PNG)
        self.cache().finish(item, JPEG)
        self.assertEqual(self.cache().cover('Фреза/job')['path'], '')
        self.assertEqual(self.cache().cover('Фреза/job2')['path'], item['path'])

    def test_renderer_timeout_kills_child_before_retry(self):
        stop = threading.Event()
        with patch.object(thumbs, 'RENDER_TIMEOUT', 0.01):
            with self.assertRaisesRegex(ValueError, 'повторим автоматически'):
                thumbs.run_renderer([sys.executable, '-c', 'import time; time.sleep(10)'], stop)

    @unittest.skipUnless(sys.platform == 'darwin', 'Native macOS rendering')
    def test_native_image_pdf_video_and_embedded_cdr_preserve_originals(self):
        binary = thumbs.renderer(manager.DATA_DIR)
        paths = {'Фото/снимок.png': PNG, 'Фото/документ.pdf': sample_pdf(),
                 'Фото/короткий.mp4': Path(__file__).with_name('fixtures').joinpath('thumbnail-video.mp4').read_bytes()}
        cdr = self.root / 'Фото/чертёж.cdr'
        cdr.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(cdr, 'w') as archive:
            archive.writestr('previews/thumbnail.png', PNG)
        paths['Фото/чертёж.cdr'] = cdr.read_bytes()
        for path, raw in paths.items():
            with self.subTest(path=path):
                self.file(path, raw)
                target = self.root / path
                before = target.stat()
                self.cache().observe([(path, before)], requested=True)
                item = self.cache().next_item()
                self.assertEqual(item['path'], path)
                thumbs.generate(self.cache(), item, binary, threading.Event())
                image, mime, _ = self.cache().image(path)
                self.assertTrue(image.startswith(b'\xff\xd8\xff'))
                self.assertEqual(mime, 'image/jpeg')
                self.assertEqual(target.read_bytes(), raw)
                self.assertEqual(target.stat().st_mtime_ns, before.st_mtime_ns)
        self.assertFalse(list(manager.DATA_DIR.glob('.thumbnail-*')))
