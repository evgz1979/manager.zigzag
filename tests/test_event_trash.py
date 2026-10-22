"""Supplier event removal: data preservation, stale confirmations and crash recovery."""
import json
import shutil
import sqlite3
import subprocess
import sys
import unittest
from unittest.mock import patch

import event_trash
import folder_layout
import folder_rename
import folder_rename_undo
from order_todos import OrderTodos
from local_metadata import MetadataStore
import test_server as fixtures

manager = fixtures.manager


class EventTrashTests(unittest.TestCase):
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url
    tearDown = fixtures.ManagerTests.tearDown

    def setUp(self):
        fixtures.ManagerTests.setUp(self)
        mode = patch.object(manager, 'DATABASE_ONLY', True)
        mode.start()
        self.patches.append(mode)
        self.parent = '# work/# newtek/2026-10-22 - Профиль'
        self.event = self.parent + '/00 - Замеры'
        self.folder(self.event + '/Вложенное')
        self.file(self.event + '/Вложенное/оригинал.txt', b'original bytes')
        self.store = manager.order_store()
        self.store.add(self.parent, {'status': 'new', 'note': 'Заказ', 'amount': 15000})
        self.notes = manager.folder_note_store()
        record = self.notes.read(self.event)
        self.note = self.notes.save({'path': self.event, 'revision': record['revision'], 'note': 'Заметка события',
                                     'todo_items': [{'text': 'Проверить', 'done': False}]})
        self.meta = MetadataStore(self.store)
        self.file_path = self.root / self.event / 'Вложенное/оригинал.txt'
        comment = self.meta.comment(self.file_path)
        self.comment = self.meta.save_comment(self.file_path, 'Полный комментарий', comment['revision'])

    def remove(self):
        return event_trash.remove(self.store, {**event_trash.preview(self.store, self.event), 'confirmed': True})

    def test_delete_restore_preserves_all_bytes_notes_history_and_parent(self):
        original = self.store.get(self.parent)
        before = {file.relative_to(self.root / self.event).as_posix(): file.read_bytes()
                  for file in (self.root / self.event).rglob('*') if file.is_file()}
        result = self.remove()
        self.assertFalse((self.root / self.event).exists())
        self.assertEqual(self.store.get(self.parent), original)
        self.assertEqual(OrderTodos(self.store).in_order(self.parent)['todo_groups'], [])
        self.assertNotIn(self.event, [item['path'] for item in manager.read_folder(self.parent)['directories']])
        sessions = event_trash.list_sessions(self.store)
        self.assertEqual(sessions[0]['session'], result['session'])
        with self.store.connect() as db:
            row = db.execute('SELECT session,mappings FROM folder_renames').fetchone()
            stored = json.loads(row['mappings'])[0]['destination']
            self.assertGreater(db.execute('SELECT count(*) FROM metadata_history').fetchone()[0], 0)
        self.assertEqual({file.relative_to(self.root / stored).as_posix(): file.read_bytes()
                          for file in (self.root / stored).rglob('*') if file.is_file()}, before)
        # Standalone restoration is independent of the application's imports.
        journal = self.root / '.folder-layout-history' / row['session'].split('/')[-1]
        output = subprocess.run([sys.executable, str(journal / '.restore.py'), str(journal), '--apply'],
                                cwd=self.base, capture_output=True, text=True)
        self.assertEqual(output.returncode, 0, output.stderr)
        restored = self.notes.get(self.event)
        self.assertEqual(restored['revision'].split(':')[0], self.note['revision'].split(':')[0])
        self.assertEqual(restored['note'], self.note['note'])
        self.assertEqual(restored['todo_items'], self.note['todo_items'])
        comment = self.meta.comment(self.file_path)
        self.assertEqual(comment['comment'], self.comment['comment'])
        self.assertEqual(event_trash.list_sessions(self.store), [])
        self.assertEqual(len(OrderTodos(self.store).in_order(self.parent)['todo_groups']), 1)

    def test_confirmation_rejects_changed_file_note_identity_and_missing_confirmation(self):
        view = event_trash.preview(self.store, self.event)
        self.file_path.write_bytes(b'changed externally')
        with self.assertRaises(folder_rename.FolderRenameConflict):
            event_trash.remove(self.store, {**view, 'confirmed': True})
        view = event_trash.preview(self.store, self.event)
        self.notes.save({'path': self.event, 'revision': self.note['revision'], 'note': 'Новая заметка'})
        with self.assertRaises(folder_rename.FolderRenameConflict):
            event_trash.remove(self.store, {**view, 'confirmed': True})
        with self.assertRaises(ValueError):
            event_trash.remove(self.store, event_trash.preview(self.store, self.event))
        self.assertTrue(self.file_path.exists())

    def test_scope_and_symlinks_and_registration_are_protected(self):
        for path in (self.parent, '# work/# newtek', '# work', self.event + '/Вложенное',
                     self.parent + '/# bills', 'Клиент/2026-00-00 - Заказ/Фото',
                     '# work/2026-10-22 - Заказ/00 - Событие', '# work/# print/2026-10-22 - Заказ/00 - Событие'):
            self.assertFalse(event_trash.available(path), path)
        link = self.root / self.parent / '01 - Ссылка'
        link.symlink_to(self.root / self.event, target_is_directory=True)
        with self.assertRaises(ValueError):
            event_trash.preview(self.store, str(link.relative_to(self.root)))
        self.assertTrue(event_trash.available('#glass/2026-10-22 - Заказ/00 - Событие'))
        with self.store.connect() as db:
            db.execute('UPDATE orders SET path=?', (self.event,))
        with self.assertRaises(ValueError):
            event_trash.preview(self.store, self.event)

    def test_restore_conflict_keeps_both_folders_and_rename_requires_restoration(self):
        result = self.remove()
        with self.assertRaisesRegex(ValueError, 'восстанови события'):
            folder_rename.rename(self.store, {**folder_rename.preview(self.store, self.parent), 'name': '2026-10-22 - Новое'})
        self.file(self.event + '/новый.txt', b'new file')
        with self.assertRaises((ValueError, OSError)):
            event_trash.restore(self.store, result['session'])
        self.assertEqual((self.root / self.event / 'новый.txt').read_bytes(), b'new file')
        self.assertTrue(event_trash.list_sessions(self.store))
        shutil.rmtree(self.root / self.event)
        event_trash.restore(self.store, result['session'])
        self.assertEqual(self.file_path.read_bytes(), b'original bytes')

    def test_crash_after_move_before_database_commit_can_be_restored(self):
        apply = folder_layout.apply
        def crash(session):
            apply(session)
            raise KeyboardInterrupt('simulated power loss')
        with patch.object(folder_layout, 'apply', crash), self.assertRaises(KeyboardInterrupt):
            self.remove()
        self.assertFalse((self.root / self.event).exists())
        sessions = event_trash.list_sessions(self.store)
        self.assertTrue(sessions[0]['pending'])
        event_trash.restore(self.store, sessions[0]['session'])
        self.assertEqual(self.file_path.read_bytes(), b'original bytes')
        self.assertEqual(self.notes.get(self.event)['revision'], self.note['revision'])
        self.assertEqual(event_trash.list_sessions(self.store), [])

    def test_pending_publication_waits_until_event_is_restored(self):
        self.meta.publish(self.event + '/задание.txt', 'v1', self.root / self.event, 'выпуск.txt', b'issued document')
        result = self.remove()
        self.meta.sync()
        with self.store.connect() as db:
            publication = db.execute('SELECT path,published,error FROM metadata_publications').fetchone()
        self.assertEqual(tuple(publication)[1:], (0, ''))
        self.assertFalse((self.root / publication['path']).exists())
        event_trash.restore(self.store, result['session'])
        self.meta.sync()
        self.assertEqual((self.root / self.event / 'выпуск.txt').read_bytes(), b'issued document')

    def test_database_failure_rolls_folder_back_without_losing_notes(self):
        with patch.object(folder_rename_undo, 'rewrite', side_effect=sqlite3.OperationalError('simulated failure')):
            with self.assertRaisesRegex(folder_rename.FolderRenameConflict, 'событие восстановлено'):
                self.remove()
        self.assertEqual(self.file_path.read_bytes(), b'original bytes')
        self.assertEqual(self.notes.get(self.event)['revision'], self.note['revision'])
        self.assertEqual(event_trash.list_sessions(self.store), [])

    def test_http_button_scope_remove_list_restore_and_stale_save(self):
        status, _, body = self.http(self.url('/api/folder', self.event))
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)['canDeleteEvent'])
        status, _, body = self.http('/api/event-trash-preview', 'POST', json.dumps({'path': self.event}))
        self.assertEqual(status, 200)
        preview = json.loads(body)
        with patch.object(manager, 'schedule_todo_refresh'):
            status, _, body = self.http('/api/event-trash', 'POST', json.dumps({**preview, 'confirmed': True}))
        self.assertEqual(status, 200, body)
        token = json.loads(body)['session']
        status, _, body = self.http('/api/folder-note-save', 'POST', json.dumps({'path': self.event, 'revision': self.note['revision'], 'note': 'Старая вкладка'}))
        self.assertNotEqual(status, 200)
        status, _, body = self.http('/api/files-trash-list', 'POST', '{}')
        self.assertEqual(json.loads(body)['events'][0]['session'], token)
        with patch.object(manager, 'schedule_todo_refresh'), patch.object(manager, 'schedule_order_sync'):
            status, _, body = self.http('/api/event-trash-restore', 'POST', json.dumps({'session': token}))
        self.assertEqual(status, 200, body)
        self.assertTrue(self.file_path.exists())
