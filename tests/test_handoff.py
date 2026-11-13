from contextlib import closing
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import handoff_host as handoff
sys.path.pop(0)


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        base = Path(self.temporary.name).resolve()
        self.documents = base / "Зигзаг"
        self.documents.mkdir()
        self.release = "20261113T091834Z-bd675c49"
        self.trip = "1" * 32
        self.back = "2" * 32
        self.source = self.installation(base, "m4")
        self.target = self.installation(base, "macbook")
        self.target.parked.write_text('{"id":"prepared"}')
        self.source.support.mkdir(parents=True)
        (self.source.support / handoff.PROFILE).write_bytes(b"profile")
        (self.source.support / handoff.TOKEN).parent.mkdir()
        (self.source.support / handoff.TOKEN).write_bytes(b"token")
        (self.source.data / "telegram.ini").write_bytes(b"telegram")

    def installation(self, base, role):
        settings = {"directory": str(base / role), "python": sys.executable, "port": 0, "host": "127.0.0.1"}
        value = handoff.Installation(settings, self.documents, role)
        value.support = value.root / "private"
        value.data.mkdir(parents=True)
        value.current.mkdir()
        (value.current / ".release-id").write_text(self.release)
        (value.root / "manager.ini").write_text(f"[storage]\nroot = {self.documents}\n[remote_access]\nenabled = true\n")
        value.active = role == "m4"
        value.loaded = lambda label: value.active
        value.stop_job = lambda label: setattr(value, "active", False)
        value.start_job = lambda label: setattr(value, "active", True)
        value.check_service = lambda state: None
        value.check_public = lambda state: None
        return value

    def test_round_trip_preserves_wal_records_pdf_queue_and_later_edits(self):
        with closing(sqlite3.connect(self.source.database)) as original:
            original.execute("PRAGMA journal_mode=WAL")
            original.execute("PRAGMA wal_autocheckpoint=0")
            original.executescript("""
                CREATE TABLE orders (id TEXT, revision INTEGER, note TEXT);
                CREATE TABLE invoices (data TEXT, pdf BLOB);
                CREATE TABLE metadata_publications (path TEXT, published INTEGER);
                INSERT INTO orders VALUES ('order-uuid', 7, 'M4');
                INSERT INTO invoices VALUES ('{}', X'010203');
                INSERT INTO metadata_publications VALUES ('# bills/file.pdf', 0);
            """)
            self.assertTrue(self.source.database.with_name(self.source.database.name + "-wal").exists())
            archive = self.source.freeze(self.trip, self.trip)
            self.assertEqual(self.source.freeze(self.trip, self.trip), archive)
            self.assertFalse(self.source.active)
            self.target.activate(self.trip, self.trip, archive)
            self.assertTrue(self.target.active)
            with closing(sqlite3.connect(self.target.database)) as db, db:
                self.assertEqual(db.execute("SELECT * FROM orders").fetchall(), [("order-uuid", 7, "M4")])
                self.assertEqual(db.execute("SELECT pdf FROM invoices").fetchone()[0], bytes([1, 2, 3]))
                self.assertEqual(db.execute("SELECT published FROM metadata_publications").fetchone()[0], 0)
                db.execute("UPDATE orders SET revision=8,note='MacBook'")
            self.target.activate(self.trip, self.trip, None)
        (self.target.support / handoff.PROFILE).write_bytes(b"new profile")
        archive = self.target.freeze(self.back, self.trip)
        self.source.activate(self.back, self.trip, archive)
        self.assertFalse(self.target.active)
        self.assertTrue(self.source.active)
        self.assertEqual((self.source.support / handoff.PROFILE).read_bytes(), b"new profile")
        self.assertEqual((self.source.support / handoff.TOKEN).read_bytes(), b"token")
        self.assertEqual((self.source.data / "telegram.ini").read_bytes(), b"telegram")
        self.assertTrue(list(self.source.history(self.back).glob("previous/orders-*.sqlite3")))
        with closing(sqlite3.connect(self.source.database)) as db, db:
            self.assertEqual(db.execute("SELECT * FROM orders").fetchall(), [("order-uuid", 8, "MacBook")])
            db.execute("UPDATE orders SET revision=9,note='M4 again'")
        self.source.activate(self.back, self.trip, None)
        with closing(sqlite3.connect(self.source.database)) as db:
            self.assertEqual(db.execute("SELECT * FROM orders").fetchall(), [("order-uuid", 9, "M4 again")])

    def test_pending_operation_stops_export_and_restores_source(self):
        with closing(sqlite3.connect(self.source.database)) as db:
            db.executescript("""
                CREATE TABLE orders (id TEXT);
                CREATE TABLE folder_renames (state TEXT);
                INSERT INTO folder_renames VALUES ('pending');
            """)
        with self.assertRaisesRegex(RuntimeError, "незаконченные операции"):
            self.source.freeze(self.trip, self.trip)
        self.assertFalse(self.source.parked.exists())
        self.assertTrue(self.source.active)
        self.assertFalse((self.source.history(self.trip) / "outgoing.zip").exists())

    def test_failed_health_check_does_not_reinstall_an_activated_database(self):
        with closing(sqlite3.connect(self.source.database)) as db:
            db.executescript("CREATE TABLE orders (id TEXT); INSERT INTO orders VALUES ('initial');")
        archive = self.source.freeze(self.trip, self.trip)
        with patch.object(self.target, "check_public", side_effect=RuntimeError("connection failed")):
            with self.assertRaisesRegex(RuntimeError, "connection failed"):
                self.target.activate(self.trip, self.trip, archive)
        with closing(sqlite3.connect(self.target.database)) as db:
            db.executescript("INSERT INTO orders VALUES ('already changed');")
        self.target.activate(self.trip, self.trip, None)
        with closing(sqlite3.connect(self.target.database)) as db:
            self.assertEqual(db.execute("SELECT * FROM orders").fetchall(), [("initial",), ("already changed",)])

    def test_corrupt_package_does_not_open_target(self):
        with closing(sqlite3.connect(self.source.database)) as db:
            db.executescript("CREATE TABLE orders (id TEXT);")
        archive = self.source.freeze(self.trip, self.trip)
        corrupt = archive.with_name("corrupt.zip")
        with zipfile.ZipFile(archive) as source, zipfile.ZipFile(corrupt, "w") as output:
            for item in source.namelist():
                output.writestr(item, b"corrupted" if item == handoff.PROFILE else source.read(item))
        with self.assertRaisesRegex(RuntimeError, "контрольная сумма"):
            self.target.activate(self.trip, self.trip, corrupt)
        self.assertEqual(json.loads(self.target.parked.read_text()), {"id": "prepared"})
        self.assertFalse(self.target.database.exists())
        self.assertFalse(self.target.active)

    def test_stopped_macbook_can_return_the_active_trip_database(self):
        with closing(sqlite3.connect(self.source.database)) as db:
            db.executescript("CREATE TABLE orders (id TEXT); INSERT INTO orders VALUES ('active');")
        self.target.activate(self.trip, self.trip, self.source.freeze(self.trip, self.trip))
        self.target.active = False
        self.source.activate(self.back, self.trip, self.target.freeze(self.back, self.trip))
        self.assertTrue(self.source.active)


if __name__ == "__main__":
    unittest.main()
