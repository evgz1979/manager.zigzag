import tempfile
import unittest
from pathlib import Path

import folder_layout as layout


class FolderLayoutTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        (self.root / 'Client/Object/Old').mkdir(parents=True)
        self.source = self.root / 'Client/Object/Old'
        (self.source / 'file.cdr').write_bytes(b'original\x00\xff')

    def tearDown(self):
        self.temporary.cleanup()

    def plan(self):
        plan = layout.Plan(self.root, ['Client'])
        plan.move('Client/Object/Old', 'Client/Object/2026-00-00 - Order', 'test')
        plan.mkdir('Client/Object/2026-00-00 - Order/# cdr')
        plan.move('Client/Object/2026-00-00 - Order/file.cdr',
                  'Client/Object/2026-00-00 - Order/# cdr/file.cdr', 'test',
                  origin='Client/Object/Old/file.cdr')
        return plan.create_session([], {})

    def test_round_trip_keeps_bytes_metadata_and_event_subtrees(self):
        (self.source / '01/deeper').mkdir(parents=True)
        (self.source / '01/deeper/private.txt').write_bytes(b'do not inspect')
        original = (self.source / 'file.cdr').stat()
        session = self.plan()
        layout.apply(session)
        self.assertEqual(layout.undo(session), 3)
        self.assertEqual(layout.undo(session, True), 3)
        self.assertEqual(layout.undo(session, True), 0)
        self.assertEqual((self.source / 'file.cdr').read_bytes(), b'original\x00\xff')
        self.assertEqual((self.source / 'file.cdr').stat().st_mtime_ns, original.st_mtime_ns)
        self.assertEqual((self.source / '01/deeper/private.txt').read_bytes(), b'do not inspect')

    def test_apply_and_undo_never_overwrite_a_conflicting_path(self):
        session = self.plan()
        target = self.root / 'Client/Object/2026-00-00 - Order'
        target.mkdir()
        with self.assertRaises(FileExistsError):
            layout.apply(session)
        self.assertTrue(self.source.exists())
        target.rmdir()
        other = self.plan()
        layout.apply(other)
        self.source.mkdir()
        (self.source / 'new.txt').write_text('new user data')
        with self.assertRaises(FileExistsError):
            layout.undo(other, True)
        self.assertEqual((self.source / 'new.txt').read_text(), 'new user data')

    def test_crash_after_move_before_commit_can_be_reversed(self):
        session = self.plan()
        operation = layout.load_plan(session)['operations'][0]
        layout.append(session, {'phase': 'intent', 'id': 1, **operation})
        layout.rename_exclusive(self.source, self.root / operation['destination'])
        self.assertEqual(layout.undo(session, True), 1)
        self.assertEqual((self.source / 'file.cdr').read_bytes(), b'original\x00\xff')

    def test_root_service_folders_and_symlinks_are_blocked(self):
        plan = layout.Plan(self.root, ['Client', '# work'])
        for source in ('# work/file', '../outside'):
            with self.assertRaises(ValueError):
                plan.move(source, 'Client/new', 'test')
        (self.root / 'Client/link').symlink_to(self.source)
        with self.assertRaises(ValueError):
            plan.move('Client/link', 'Client/new', 'test')

    def test_new_user_files_block_removal_of_created_directory(self):
        plan = layout.Plan(self.root, ['Client'])
        plan.mkdir('Client/New')
        session = plan.create_session([], {})
        layout.apply(session)
        (self.root / 'Client/New/new.txt').write_bytes(b'keep')
        with self.assertRaises(OSError):
            layout.undo(session, True)
        self.assertEqual((self.root / 'Client/New/new.txt').read_bytes(), b'keep')
