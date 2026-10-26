from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import unittest
from unittest.mock import patch

import order_calendar
import order_deadlines
import weekly_events_migration as migration
import test_server as fixtures
from orders import OrderConflict

manager = fixtures.manager


def legacy(values):
    return json.dumps({'version': 1, 'comments': values}, ensure_ascii=False)


class UnifiedWeeklyTests(unittest.TestCase):
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    path = 'Клиент/Объект/2026-10-25 - Заказ'

    def setUp(self):
        fixtures.ManagerTests.setUp(self)
        mode = patch.object(manager, 'DATABASE_ONLY', True)
        mode.start(); self.patches.append(mode)
        self.folder(self.path)
        self.store = manager.order_store()
        self.order = self.store.add(self.path, {'status': 'process', 'note': 'Сохранить', 'amount': 10000,
                                              'extra_blocks': {'Особое': 'Не трогать'}})

    def payload(self, record, **changes):
        return {'path': record['path'], 'id': record['id'], 'revision': record['revision'],
                'date': '2026-10-26', 'text': 'На неделю', 'period': 'week', **changes}

    def inject(self, comments, events=None):
        blocks = {**self.order['extra_blocks'], order_deadlines.COMMENTS_BLOCK: legacy(comments)}
        if events is not None:
            blocks[order_calendar.WEEK_BLOCK] = json.dumps({'version': 1, 'events': events}, ensure_ascii=False)
        with self.store.connect() as db:
            db.execute('UPDATE orders SET extra_blocks=?,revision=revision+1 WHERE id=?',
                       (json.dumps(blocks, ensure_ascii=False), self.order['id']))
        return self.store.get(self.path)

    def test_one_source_in_both_routes_and_move_clear_preserve_marks_and_daily_events(self):
        data = self.payload(self.order, date='2026-10-27', text='День', period='day')
        daily = self.store.save_calendar_event(data)
        saved = self.store.save_deadline_comment({**self.payload(daily), 'week': '2026-10-26', 'comment': 'Комментарий стал событием'})
        self.assertEqual(saved['deadline_comments'], saved['calendar_week_events'])
        self.assertEqual(saved['calendar_week_events'], {'2026-10-26': 'Комментарий стал событием'})
        self.assertNotIn(order_deadlines.COMMENTS_BLOCK, saved['extra_blocks'])
        edited = self.store.save_calendar_event(self.payload(saved, text='Правка из календаря'))
        self.assertEqual(edited['deadline_comments'], {'2026-10-26': 'Правка из календаря'})
        moved = self.store.move_calendar_event(self.payload(edited, days=7))
        self.assertEqual(moved['deadline_comments'], {'2026-11-02': 'Правка из календаря'})
        self.assertEqual(moved['calendar_events'], daily['calendar_events'])
        self.assertEqual(moved['updated'], self.order['updated'])
        cleared = self.store.save_deadline_comment({**self.payload(moved), 'week': '2026-11-02', 'comment': ''})
        self.assertEqual(cleared['calendar_week_events'], {})
        self.assertEqual(cleared['calendar_inactive']['week'], [])
        self.assertEqual(cleared['deadline_weeks'], moved['deadline_weeks'])
        self.assertEqual(cleared['calendar_events'], daily['calendar_events'])
        self.assertNotIn(order_deadlines.COMMENTS_BLOCK, cleared['extra_blocks'])
        with self.assertRaises(OrderConflict):
            self.store.save_calendar_event(self.payload(edited))

    def test_checked_snapshot_history_idempotency_and_readonly_migration_without_cloud(self):
        before = self.inject({'2026-10-26': '  Точный текст  ', '2026-11-02': 'Позже'}, {'2026-10-26': '  Точный текст  '})
        with self.store.connect() as db:
            raw_before = db.execute('SELECT extra_blocks FROM orders WHERE id=?', (before['id'],)).fetchone()[0]
        with patch('icloud_access.read_bytes', side_effect=AssertionError('No iCloud reads')):
            result = migration.migrate(self.store.database, self.base/'backups')
        self.assertEqual(result['orders'], 1)
        after = self.store.get(self.path)
        for field in before.keys()-{'revision', 'extra_blocks'}:
            self.assertEqual(after[field], before[field], field)
        self.assertEqual(after['revision'], before['revision']+1)
        self.assertNotIn(order_deadlines.COMMENTS_BLOCK, after['extra_blocks'])
        journal = Path(result['journal']); backup = journal/'before.sqlite3'
        self.assertEqual(hashlib.sha256(backup.read_bytes()).hexdigest(), result['backup_sha256'])
        with closing(sqlite3.connect(backup)) as db:
            self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
            self.assertEqual(db.execute('SELECT extra_blocks FROM orders WHERE id=?', (before['id'],)).fetchone()[0], raw_before)
        with self.store.connect() as db:
            history = [json.loads(row[0]) for row in db.execute("SELECT data FROM metadata_history WHERE entity='orders' AND identity=?", (before['id'],))]
        self.assertTrue(any(row['extra_blocks'] == raw_before for row in history))
        self.assertEqual(migration.migrate(self.store.database, self.base/'backups')['status'], 'already-migrated')
        self.assertEqual(self.store.get(self.path)['revision'], after['revision'])
        # The standalone restoration changes only those fields and keeps history/versions.
        subprocess.run([sys.executable, str(journal/'.restore.py')], check=True, capture_output=True)
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT extra_blocks FROM orders WHERE id=?', (before['id'],)).fetchone()[0], raw_before)

    def test_unknown_or_different_text_aborts_entire_migration_and_restore_refuses_later_edits(self):
        before = self.inject({'2026-10-26': 'Комментарий'}, {'2026-10-26': 'Иной текст'})
        with self.assertRaises(ValueError):
            migration.migrate(self.store.database, self.base/'backups')
        self.assertEqual(self.store.get(self.path), before)
        with self.assertRaises(ValueError):
            self.store.save_calendar_event(self.payload(before))
        with self.store.connect() as db:
            blocks = dict(before['extra_blocks']); blocks[order_deadlines.COMMENTS_BLOCK] = '{"version":2,"comments":{}}'
            db.execute('UPDATE orders SET extra_blocks=? WHERE id=?', (json.dumps(blocks), before['id']))
        with self.assertRaises(ValueError):
            migration.migrate(self.store.database, self.base/'backups')
        before = self.inject({'2026-10-26': 'Комментарий'})
        result = migration.migrate(self.store.database, self.base/'backups')
        current = self.store.get(self.path)
        edited = self.store.save_calendar_event(self.payload(current, text='Поздняя правка'))
        restored = subprocess.run([sys.executable, str(Path(result['journal'])/'.restore.py')], capture_output=True)
        self.assertNotEqual(restored.returncode, 0)
        self.assertEqual(self.store.get(self.path), edited)

    def test_unregistered_draft_migrates_and_old_import_cannot_recreate_comment_storage(self):
        before = self.inject({'2026-10-26': 'После возвращения'})
        removed = self.store.remove({'path': self.path, 'revision': before['revision'], 'confirmed': True})
        # Simulate a draft created by the previous release.
        with self.store.connect() as db:
            row = db.execute('SELECT document FROM folder_notes WHERE path=?', (self.path,)).fetchone()
            body = json.loads(row[0]); body['extra_blocks'] = before['extra_blocks']; body['deadline_comments'] = before['deadline_comments']
            db.execute('UPDATE folder_notes SET document=? WHERE path=?', (json.dumps(body), self.path))
        result = migration.migrate(self.store.database, self.base/'backups')
        self.assertEqual((result['orders'], result['folder_notes']), (1, 1))
        restored = self.store.import_folder(self.path)
        self.assertEqual(restored['calendar_week_events'], {'2026-10-26': 'После возвращения'})
        self.assertNotIn(order_deadlines.COMMENTS_BLOCK, restored['extra_blocks'])
        new_path = 'Клиент/Объект/2026-10-25 - Импорт'
        self.folder(new_path)
        imported = self.store.add(new_path, {'extra_blocks': {order_deadlines.COMMENTS_BLOCK: legacy({'2026-10-26': 'Из старого формата'})}})
        self.assertNotIn(order_deadlines.COMMENTS_BLOCK, imported['extra_blocks'])
        self.assertEqual(imported['calendar_week_events'], {'2026-10-26': 'Из старого формата'})
