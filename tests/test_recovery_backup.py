import importlib.util
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import recovery_backup as backup

APP = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("verify_recovery", APP / "scripts/verify_recovery_backup.py")
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


class RecoveryBackupTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name).resolve()
        self.root = self.base / "Зигзаг"
        self.root.mkdir()
        self.app = self.base / "installation"
        self.app.mkdir()
        self.data = self.app / "data"
        self.data.mkdir()
        self.database = self.data / "orders-test.sqlite3"
        self.db = sqlite3.connect(self.database)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA wal_autocheckpoint=0")
        self.db.executescript("""
            CREATE TABLE orders (path TEXT, note TEXT, revision INTEGER);
            CREATE TABLE invoices (id TEXT, pdf BLOB);
            CREATE TABLE metadata_history (entity TEXT, data TEXT);
            CREATE TABLE metadata_publications (path TEXT, body BLOB, published INTEGER);
            CREATE TABLE legacy_documents (path TEXT, body BLOB);
        """)
        self.db.execute("INSERT INTO orders VALUES ('Клиент/Заказ', 'Комментарий в WAL', 7)")
        self.db.execute("INSERT INTO invoices VALUES ('invoice-uuid', ?)", (b'%PDF-immutable\x00\xff',))
        self.db.execute("INSERT INTO metadata_history VALUES ('order', 'history')")
        self.db.execute("INSERT INTO metadata_publications VALUES ('Заказ/print.txt', X'0102', 0)")
        self.db.execute("INSERT INTO legacy_documents VALUES ('Заказ/!.txt', X'0304')")
        self.db.commit()
        (self.app / "server.py").write_text("# recovery source", encoding="utf-8")
        (self.app / "manager.ini").write_text("[storage]\nroot = " + str(self.root), encoding="utf-8")
        (self.app / "scripts").mkdir()
        shutil.copyfile(APP / "scripts/verify_recovery_backup.py", self.app / "scripts/verify_recovery_backup.py")
        (self.app / "static").mkdir()
        (self.app / "static/app.js").write_text("// UI", encoding="utf-8")
        (self.data / "secret-cache.txt").write_text("not a source")
        (self.root / "attachment.pdf").write_bytes(b'ordinary attachment')
        self.now = datetime(2026, 10, 23, 12, 0, tzinfo=backup.TIMEZONE)

    def tearDown(self):
        self.db.close()
        self.temporary.cleanup()

    def create(self, **kwargs):
        return backup.create(self.database, self.root, self.app, now=kwargs.pop("now", self.now), **kwargs)

    def extract(self, archive):
        folder = self.base / ("extracted-" + str(len(list(self.base.glob('extracted-*')))))
        with zipfile.ZipFile(archive) as source:
            source.extractall(folder)
        return folder

    def test_restore_standalone_snapshot_including_live_wal_pdf_history_and_queue(self):
        self.assertTrue(self.database.with_name(self.database.name + '-wal').is_file())
        original = list(self.db.execute("SELECT * FROM orders"))
        archive = self.create()
        folder = self.extract(archive)
        result = subprocess.run([sys.executable, str(folder / 'verify.py'), str(folder)],
                                check=True, capture_output=True, text=True)
        self.assertIn("OK:", result.stdout)
        with sqlite3.connect(folder / 'manager.sqlite3') as restored:
            self.assertEqual(list(restored.execute("SELECT * FROM orders")), original)
            self.assertEqual(restored.execute("SELECT pdf FROM invoices").fetchone()[0], b'%PDF-immutable\x00\xff')
            self.assertEqual(restored.execute("SELECT * FROM metadata_history").fetchone(), ('order', 'history'))
            self.assertEqual(restored.execute("SELECT published FROM metadata_publications").fetchone()[0], 0)
            self.assertEqual(restored.execute("SELECT body FROM legacy_documents").fetchone()[0], b'\x03\x04')
            self.assertEqual(restored.execute("PRAGMA journal_mode").fetchone()[0], 'delete')
        self.assertEqual(list(self.db.execute("SELECT * FROM orders")), original)
        self.assertEqual(self.db.execute("PRAGMA journal_mode").fetchone()[0], 'wal')
        self.assertEqual((folder / 'manager.ini').read_bytes(), (self.app / 'manager.ini').read_bytes())
        names = {p.relative_to(folder).as_posix() for p in folder.rglob('*')}
        self.assertIn('application/static/app.js', names)
        self.assertFalse(any('secret-cache' in name or 'attachment' in name or '-wal' in name for name in names))

    def test_same_moscow_day_needs_no_cloud_access_and_restart_keeps_schedule(self):
        first = self.create()
        # 21:30 UTC is already the next date in Moscow.
        self.assertFalse(backup.due(self.database, self.root, self.now))
        with patch.object(backup, 'source_files', side_effect=AssertionError('must not build again')):
            self.assertIsNone(self.create())
        next_day = datetime(2026, 10, 23, 21, 30, tzinfo=timezone.utc)
        self.assertTrue(backup.due(self.database, self.root, next_day))
        second = self.create(now=next_day)
        self.assertTrue(first.exists())
        self.assertTrue(second.exists())
        self.assertNotEqual(first, second)
        self.assertEqual(backup.status(self.database)['day'], '2026-10-24')

    def test_failed_publication_preserves_old_backup_and_retries_without_partial_zip(self):
        first = self.create()
        before = first.read_bytes()
        tomorrow = self.now + timedelta(days=1)
        with patch.object(backup, 'rename_exclusive', side_effect=OSError('iCloud unavailable')):
            with self.assertRaisesRegex(OSError, 'iCloud unavailable'):
                self.create(now=tomorrow)
        self.assertEqual(first.read_bytes(), before)
        self.assertTrue(backup.due(self.database, self.root, tomorrow))
        self.assertIn('iCloud unavailable', backup.status(self.database)['error'])
        self.assertEqual(list((self.root / backup.DIRECTORY).iterdir()), [first])
        self.assertTrue(self.create(now=tomorrow).exists())
        self.assertFalse(backup.status(self.database)['error'])

    def test_backup_folder_link_is_rejected_without_writing_outside_root(self):
        outside = self.base / 'outside'
        outside.mkdir()
        (self.root / backup.DIRECTORY).symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'ссылкой'):
            self.create()
        self.assertEqual(list(outside.iterdir()), [])

    def test_forced_copy_preserves_existing_archive(self):
        first = self.create()
        second = self.create(force=True)
        self.assertNotEqual(first, second)
        self.assertTrue(first.exists())

    def test_verifier_rejects_changed_files_extra_wal_and_manifest_path_escape(self):
        folder = self.extract(self.create())
        config = folder / 'manager.ini'
        body = config.read_bytes()
        config.write_bytes(body + b'changed')
        with self.assertRaisesRegex(ValueError, 'манифестом'):
            verifier.verify(folder)
        config.write_bytes(body)
        wal = folder / 'manager.sqlite3-wal'
        wal.touch()
        with self.assertRaisesRegex(ValueError, 'WAL'):
            verifier.verify(folder)
        wal.unlink()
        path = folder / 'manifest.json'
        manifest = json.loads(path.read_text())
        manifest['files']['../outside'] = {"sha256": "", "size": 0}
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, 'Недопустимый путь'):
            verifier.verify(folder)

    def test_status_does_not_read_document_root(self):
        self.create()
        with patch.object(Path, 'resolve', side_effect=AssertionError('no cloud access')):
            self.assertFalse(backup.status(self.database)['error'])
