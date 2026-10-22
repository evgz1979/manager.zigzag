import json
import errno
import subprocess
import unittest
from unittest.mock import patch
import test_server as fixtures

manager = fixtures.manager
trash = manager.file_trash


class FileTrashTests(unittest.TestCase):
    setUp = fixtures.ManagerTests.setUp
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url
    scope = 'Клиент/2026-00-00 - Заказ'
    document = scope + '/Фото/файл%2F #.txt'

    def prepare(self, paths=None):
        return trash.preview(self.root, self.scope, paths or [self.document])['files']

    def remove(self, paths=None):
        return trash.remove(self.root, self.scope, self.prepare(paths), True)

    def test_round_trip_preserves_file_comments_history_and_order_card(self):
        target = self.root / self.document
        before = target.stat()
        first = manager.file_comments.save(target, 'Старый комментарий', 'missing')
        manager.file_comments.save(target, 'Комментарий\nк выбранному файлу', first['revision'])
        _, _, metadata, sidecar = manager.file_comments.paths(target)
        originals = {path.relative_to(metadata): path.read_bytes() for path in metadata.rglob('*') if path.is_file()}
        order = manager.order_store().add(self.scope, {'note': 'Сохранить заметку заказа', 'status': 'process'})
        manager.order_store().sync()
        card = (self.root / self.scope / '!.txt').read_bytes()
        result = self.remove()
        self.assertFalse(result['error'])
        self.assertFalse(target.exists())
        self.assertFalse(sidecar.exists())
        self.assertEqual(manager.read_folder(self.scope)['fileCount'], 0)
        self.assertEqual(trash.list_sessions(self.root)[0]['count'], 1)
        self.assertEqual(manager.order_store().get(self.scope)['revision'], order['revision'])
        self.assertEqual((self.root / self.scope / '!.txt').read_bytes(), card)
        session = trash.session_path(self.root, result['session'])
        self.assertTrue(all((session / name).exists() for name in ('.before.json', '.plan.json', '.after.json', '.journal.jsonl', '.restore.py')))
        restored = trash.restore(self.root, result['session'])
        self.assertFalse(restored['error'])
        self.assertEqual(target.read_bytes(), b'0123456789')
        self.assertEqual(target.stat().st_mtime_ns, before.st_mtime_ns)
        self.assertEqual({path.relative_to(metadata): path.read_bytes() for path in metadata.rglob('*') if path.is_file()}, originals)
        self.assertEqual(trash.list_sessions(self.root), [])
        self.assertFalse(trash.restore(self.root, result['session'])['error'])

    def test_preview_is_read_only_and_confirmation_checks_revision(self):
        files = self.prepare()
        self.assertFalse((self.root / trash.HISTORY).exists())
        with self.assertRaises(ValueError):
            trash.remove(self.root, self.scope, files)
        (self.root / self.document).write_bytes(b'new content')
        with self.assertRaises(trash.TrashConflict):
            trash.remove(self.root, self.scope, files, True)
        self.assertEqual((self.root / self.document).read_bytes(), b'new content')
        self.assertFalse((self.root / trash.HISTORY).exists())

    def test_deleting_one_file_never_changes_surviving_comments_or_empty_caption(self):
        event = self.scope + '/Фото'
        survivor = event + '/02 - оставить.txt'
        empty = event + '/03 - без комментария.txt'
        nested = event + '/Глубже/02 - оставить.txt'
        for path in (survivor, empty, nested):
            self.file(path, path.encode())
        expected = {self.document: 'Комментарий удаляемого', survivor: 'Свой комментарий',
                    empty: '', nested: 'Комментарий одноимённого в другой папке'}
        for path, text in expected.items():
            if text:
                first = manager.file_comments.save(self.root / path, 'Прежняя версия: ' + text, 'missing')
                manager.file_comments.save(self.root / path, text, first['revision'])
        before = {path: manager.file_comments.read(self.root / path) for path in expected}
        metadata = self.root / event / '.file-comments'
        saved_bytes = {path: path.read_bytes() for path in metadata.rglob('*') if path.is_file()}
        status, _, body = self.http('/api/files-trash', 'POST', json.dumps({
            'path': event, 'files': trash.preview(self.root, event, [self.document])['files'], 'confirmed': True}))
        self.assertEqual(status, 200)
        result = json.loads(body)
        self.assertEqual(result['removed'], [self.document])
        self.assertFalse(result['error'])
        listing = {item['path']: item['comment'] for item in manager.read_folder(event)['files']}
        self.assertEqual(listing, {path: text for path, text in expected.items() if path != self.document})
        for path in (survivor, empty, nested):
            self.assertEqual(manager.file_comments.read(self.root / path), before[path])
            self.assertEqual(self.http(self.url('/api/file-comment', path))[0], 200)
        # Запоздавшее сохранение старого окна не создаёт комментарий другому файлу.
        self.assertEqual(self.http('/api/file-comment', 'POST', json.dumps({
            'path': self.document, 'comment': 'Старое окно', 'revision': before[self.document]['revision']}))[0], 404)
        self.assertFalse(manager.file_comments.paths(self.root / self.document)[3].exists())
        self.assertFalse(trash.restore(self.root, result['session'])['error'])
        self.assertEqual({path: manager.file_comments.read(self.root / path) for path in expected}, before)
        self.assertEqual({path: path.read_bytes() for path in metadata.rglob('*') if path.is_file()}, saved_bytes)

    def test_invalid_paths_folders_hidden_cards_and_symlinks_are_rejected(self):
        self.file(self.scope + '/!.txt', b'card')
        (self.root / self.scope / 'alias.txt').symlink_to(self.root / self.document)
        (self.root / 'alias-folder').symlink_to(self.root / self.scope)
        for paths in ([], [None], ['../outside'], ['# docs/Внутри/readme.txt'], [self.scope + '/!.txt'],
                      [self.scope + '/Фото'], [self.scope + '/.секрет'], [self.scope + '/alias.txt']):
            with self.subTest(paths=paths), self.assertRaises(ValueError):
                trash.preview(self.root, self.scope, paths)
        with self.assertRaises(ValueError):
            trash.preview(self.root, 'alias-folder', ['alias-folder/Фото/файл%2F #.txt'])
        self.assertTrue((self.root / self.document).exists())

    def test_restore_does_not_overwrite_new_files_and_can_resume(self):
        result = self.remove()
        target = self.root / self.document
        target.write_bytes(b'new user document')
        conflict = trash.restore(self.root, result['session'])
        self.assertTrue(conflict['error'])
        self.assertEqual(target.read_bytes(), b'new user document')
        self.assertEqual(conflict['count'], 1)
        target.rename(target.with_name('новый файл.txt'))
        restored = trash.restore(self.root, result['session'])
        self.assertFalse(restored['error'])
        self.assertEqual(target.read_bytes(), b'0123456789')
        self.assertEqual(target.with_name('новый файл.txt').read_bytes(), b'new user document')

    def test_partial_failure_and_crash_after_move_are_recoverable(self):
        target = self.root / self.document
        manager.file_comments.save(target, 'Сохранить', 'missing')
        rename = trash.rename
        calls = []

        def fail_second(source, destination):
            calls.append(source)
            if len(calls) == 2:
                raise PermissionError('Нет доступа')
            rename(source, destination)

        with patch.object(trash, 'rename', side_effect=fail_second):
            result = self.remove()
        self.assertTrue(result['error'])
        self.assertTrue(target.exists())
        self.assertFalse(trash.restore(self.root, result['session'])['error'])
        self.assertEqual(manager.file_comments.read(target)['comment'], 'Сохранить')
        append = trash.append

        class Crash(BaseException):
            pass

        def crash_after_move(session, **record):
            if record['phase'] == 'commit':
                raise Crash()
            append(session, **record)

        with patch.object(trash, 'append', side_effect=crash_after_move), self.assertRaises(Crash):
            self.remove()
        pending = trash.list_sessions(self.root)
        self.assertEqual(len(pending), 1)
        self.assertFalse(trash.restore(self.root, pending[0]['session'])['error'])
        self.assertTrue(target.exists())
        self.assertEqual(manager.file_comments.read(target)['comment'], 'Сохранить')

    def test_saved_restore_script_works_without_the_application(self):
        result = self.remove()
        script = trash.session_path(self.root, result['session']) / '.restore.py'
        response = subprocess.run(['/usr/bin/python3', str(script)], cwd=self.base, capture_output=True, check=True)
        self.assertFalse(json.loads(response.stdout)['error'])
        self.assertEqual((self.root / self.document).read_bytes(), b'0123456789')

    def test_unreadable_plan_keeps_other_sessions_and_retries_without_mutation(self):
        first = self.remove()
        second_file = self.scope + '/Фото/второй.txt'
        self.file(second_file, b'second original')
        second = self.remove([second_file])
        blocked = trash.session_path(self.root, first['session']) / '.plan.json'
        before = blocked.read_bytes()
        def reader(path):
            if path == blocked:
                raise OSError(errno.EDEADLK, 'iCloud unavailable')
            return path.read_bytes()
        errors = []
        sessions = trash.list_sessions(self.root, reader=reader, errors=errors)
        self.assertEqual([item['session'] for item in sessions], [second['session']])
        self.assertEqual(errors[0]['session'], first['session'])
        self.assertEqual(blocked.read_bytes(), before)
        self.assertEqual(len(trash.list_sessions(self.root)), 2)

    def test_http_plan_uses_coordinated_icloud_recovery_and_reports_timeout(self):
        result = self.remove()
        access = manager.icloud_access
        plain = access._plain_read
        def blocked(path, max_bytes=access.MAX_BYTES):
            if path.name == '.plan.json':
                raise OSError(errno.EDEADLK, 'Resource deadlock avoided')
            return plain(path, max_bytes)
        with patch.object(access.sys, 'platform', 'darwin'), \
                patch.object(access, '_plain_read', side_effect=blocked), \
                patch.object(access, '_coordinated_read', side_effect=plain) as recovery:
            status, _, body = self.http('/api/files-trash-list', 'POST', '{}')
        self.assertEqual(status, 200, body)
        data = json.loads(body)
        self.assertEqual(data['sessions'][0]['session'], result['session'])
        self.assertFalse(data['warning'])
        self.assertEqual(recovery.call_args.args[1], 20 * 1024 * 1024)
        with patch.object(access.sys, 'platform', 'darwin'), \
                patch.object(access, '_plain_read', side_effect=blocked), \
                patch.object(access, '_coordinated_read', side_effect=subprocess.TimeoutExpired('helper', 8)):
            status, _, body = self.http('/api/files-trash-list', 'POST', '{}')
        self.assertEqual(status, 200, body)
        self.assertTrue(json.loads(body)['warning'])
        self.assertEqual(trash.list_sessions(self.root)[0]['session'], result['session'])

    def test_http_confirmation_conflict_removal_listing_and_restore(self):
        status, _, body = self.http('/api/files-trash-preview', 'POST', json.dumps({'path': self.scope, 'files': [self.document]}))
        files = json.loads(body)['files']
        self.assertEqual(status, 200)
        payload = {'path': self.scope, 'files': files}
        self.assertEqual(self.http('/api/files-trash', 'POST', json.dumps(payload))[0], 400)
        stale = [{**files[0], 'revision': 'stale'}]
        self.assertEqual(self.http('/api/files-trash', 'POST', json.dumps({**payload, 'files': stale, 'confirmed': True}))[0], 409)
        status, _, body = self.http('/api/files-trash', 'POST', json.dumps({**payload, 'confirmed': True}))
        self.assertEqual(status, 200)
        result = json.loads(body)
        self.assertEqual(result['removed'], [self.document])
        status, _, body = self.http('/api/files-trash-list', 'POST', '{}')
        self.assertEqual(len(json.loads(body)['sessions']), 1)
        status, _, body = self.http('/api/files-trash-restore', 'POST', json.dumps({'session': result['session']}))
        self.assertFalse(json.loads(body)['error'])
        self.assertEqual(self.http('/api/files-trash-restore', 'POST', json.dumps({'session': '../invalid'}))[0], 400)
