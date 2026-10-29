import hashlib
from contextlib import closing
import importlib.util
import io
import json
import sqlite3
import tarfile
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("deploy_remote", Path(__file__).resolve().parents[1] / "scripts/deploy_remote.py")
remote = importlib.util.module_from_spec(spec)
spec.loader.exec_module(remote)
RELEASE = "20261019T180000Z-12345678"
PREVIOUS = "20261019T170000Z-abcdef12"


class DeploymentTests(unittest.TestCase):
    def test_dynamic_purchase_suppliers_block_rollback_to_fixed_list(self):
        release = self.base / 'old-purchase-suppliers'
        release.mkdir()
        (release / 'local_metadata.py').write_text('# SQLite storage')
        with sqlite3.connect(self.db) as db:
            db.execute('CREATE TABLE metadata_settings (key TEXT PRIMARY KEY,value TEXT)')
            db.execute("INSERT INTO metadata_settings VALUES ('purchase_suppliers','1')")
        with self.assertRaisesRegex(RuntimeError, 'поставщики'):
            remote.check_event_rename_compatibility(self.db, release)
        (release / 'order_document.py').write_text('PURCHASE_SUPPLIERS_VERSION = 1')
        remote.check_event_rename_compatibility(self.db, release)

    def test_deleted_inbox_tasks_block_rollback_to_original_receiver(self):
        release = self.base / 'inbox-without-deletion'
        release.mkdir()
        (release / 'local_metadata.py').write_text('# SQLite storage')
        (release / 'telegram_inbox.py').write_text('TELEGRAM_INBOX_VERSION = 1')
        with sqlite3.connect(self.db) as db:
            db.execute('CREATE TABLE metadata_settings (key TEXT PRIMARY KEY,value TEXT)')
            db.execute("INSERT INTO metadata_settings VALUES ('telegram_inbox_delete','1')")
        with self.assertRaisesRegex(RuntimeError, 'удалённые задачи'):
            remote.check_event_rename_compatibility(self.db, release)
        (release / 'telegram_inbox.py').write_text('TELEGRAM_INBOX_VERSION = 1\nTELEGRAM_INBOX_DELETE_VERSION = 1')
        remote.check_event_rename_compatibility(self.db, release)

    def test_telegram_inbox_blocks_rollback_to_code_without_receiver(self):
        release = self.base / 'old-inbox'
        release.mkdir()
        (release / 'local_metadata.py').write_text('# SQLite storage')
        with sqlite3.connect(self.db) as db:
            db.execute('CREATE TABLE metadata_settings (key TEXT PRIMARY KEY,value TEXT)')
            db.execute("INSERT INTO metadata_settings VALUES ('telegram_inbox','1')")
        with self.assertRaisesRegex(RuntimeError, 'Inbox Telegram'):
            remote.check_event_rename_compatibility(self.db, release)
        (release / 'telegram_inbox.py').write_text('TELEGRAM_INBOX_VERSION = 1')
        remote.check_event_rename_compatibility(self.db, release)

    def test_old_code_cannot_lose_paid_marks_or_closing_document_links(self):
        release = self.base / 'old-invoice-documents'
        release.mkdir()
        with sqlite3.connect(self.db) as db:
            db.execute('CREATE TABLE invoices (data TEXT)')
            db.execute('INSERT INTO invoices VALUES (?)', (json.dumps({'_list_status': 'paid'}),))
        with self.assertRaisesRegex(RuntimeError, 'Оплачен'):
            remote.check_event_rename_compatibility(self.db, release)
        (release / 'invoices.py').write_text('INVOICE_PAID_STATUS_VERSION = 1')
        remote.check_event_rename_compatibility(self.db, release)
        with sqlite3.connect(self.db) as db:
            db.execute('INSERT INTO invoices VALUES (?)', (json.dumps({'_closing_documents': {'version': 1, 'items': []}}),))
        with self.assertRaisesRegex(RuntimeError, 'закрывающие документы'):
            remote.check_event_rename_compatibility(self.db, release)
        (release / 'invoices.py').write_text('INVOICE_PAID_STATUS_VERSION = 1\nINVOICE_CLOSING_DOCUMENTS_VERSION = 1')
        (release / 'invoice_documents.py').touch()
        remote.check_event_rename_compatibility(self.db, release)

    def test_old_code_cannot_show_weekly_financial_plans_as_daily(self):
        release = self.base / 'old-week-plans'
        release.mkdir()
        (release / 'invoices.py').write_text('INVOICE_PLAN_VERSION = 1')
        with sqlite3.connect(self.db) as db:
            db.execute('CREATE TABLE invoices (data TEXT)')
            db.execute('INSERT INTO invoices VALUES (?)', (json.dumps({'kind': 'planned', 'period': 'week'}),))
        with self.assertRaisesRegex(RuntimeError, 'недельные финансовые планы'):
            remote.check_event_rename_compatibility(self.db, release)
        (release / 'invoices.py').write_text('INVOICE_PLAN_VERSION = 1\nINVOICE_WEEK_PLAN_VERSION = 1')
        remote.check_event_rename_compatibility(self.db, release)

    def test_old_code_cannot_ignore_invoice_sources_or_free_payments(self):
        release = self.base / 'old-payments'
        release.mkdir()
        (release / 'local_metadata.py').touch()
        with sqlite3.connect(self.db) as db:
            db.execute('CREATE TABLE metadata_settings (key TEXT PRIMARY KEY,value TEXT)')
            db.execute("INSERT INTO metadata_settings VALUES ('invoice_payment_sources','1')")
        with self.assertRaisesRegex(RuntimeError, 'оплаты без заказа'):
            remote.check_event_rename_compatibility(self.db, release)
        (release / 'invoices.py').write_text('INVOICE_PAYMENT_SOURCE_VERSION = 1')
        remote.check_event_rename_compatibility(self.db, release)

    def test_old_code_cannot_ignore_calendar_event_relevance(self):
        release = self.base / 'old-event-relevance'
        release.mkdir()
        (release / 'local_metadata.py').touch()
        with sqlite3.connect(self.db) as db:
            db.execute('CREATE TABLE metadata_settings (key TEXT PRIMARY KEY,value TEXT)')
            db.execute("INSERT INTO metadata_settings VALUES ('calendar_event_relevance','1')")
        with self.assertRaisesRegex(RuntimeError, 'актуальности'):
            remote.check_event_rename_compatibility(self.db, release)
        (release / 'order_calendar.py').write_text('CALENDAR_RELEVANCE_VERSION = 1')
        remote.check_event_rename_compatibility(self.db, release)

    def test_old_code_cannot_ignore_order_event_colors(self):
        release = self.base / 'old-order-event-colors'
        release.mkdir()
        (release / 'local_metadata.py').touch()
        with sqlite3.connect(self.db) as db:
            db.execute('CREATE TABLE metadata_settings (key TEXT PRIMARY KEY,value TEXT)')
            db.execute("INSERT INTO metadata_settings VALUES ('order_calendar_colors','1')")
        with self.assertRaisesRegex(RuntimeError, 'цвета событий заказов'):
            remote.check_event_rename_compatibility(self.db, release)
        (release / 'order_calendar.py').write_text('ORDER_CALENDAR_COLORS_VERSION = 1')
        remote.check_event_rename_compatibility(self.db, release)

    def test_old_code_cannot_ignore_calendar_completion(self):
        release = self.base / 'old-calendar-completion'
        release.mkdir()
        (release / 'local_metadata.py').touch()
        with sqlite3.connect(self.db) as db:
            db.execute('CREATE TABLE metadata_settings (key TEXT PRIMARY KEY,value TEXT)')
            db.execute("INSERT INTO metadata_settings VALUES ('calendar_event_completion','1')")
        with self.assertRaisesRegex(RuntimeError, 'отметки выполнения'):
            remote.check_event_rename_compatibility(self.db, release)
        (release / 'order_calendar.py').write_text('CALENDAR_COMPLETION_VERSION = 1')
        remote.check_event_rename_compatibility(self.db, release)

    def test_old_code_cannot_ignore_calendar_trip(self):
        release = self.base / 'old-calendar-trip'
        release.mkdir()
        (release / 'local_metadata.py').touch()
        with sqlite3.connect(self.db) as db:
            db.execute('CREATE TABLE metadata_settings (key TEXT PRIMARY KEY,value TEXT)')
            db.execute("INSERT INTO metadata_settings VALUES ('calendar_event_trip','1')")
        with self.assertRaisesRegex(RuntimeError, 'отметки выезда'):
            remote.check_event_rename_compatibility(self.db, release)
        (release / 'order_calendar.py').write_text('CALENDAR_TRIP_VERSION = 1')
        remote.check_event_rename_compatibility(self.db, release)

    def test_old_code_cannot_revive_removed_client_order_links(self):
        release = self.base / 'old-client-order-links'
        release.mkdir()
        (release / 'local_metadata.py').write_text('# supported')
        with sqlite3.connect(self.db) as db:
            db.execute("CREATE TABLE metadata_settings (key TEXT PRIMARY KEY,value TEXT NOT NULL)")
            db.execute("INSERT INTO metadata_settings VALUES ('client_order_links','1')")
        with self.assertRaisesRegex(RuntimeError, 'связанные клиентские заказы'):
            remote.check_event_rename_compatibility(self.db, release)
        (release / 'order_links.py').write_text('ORDER_LINKS_VERSION = 1')
        remote.check_event_rename_compatibility(self.db, release)
        with sqlite3.connect(self.db) as db:
            db.execute("INSERT INTO metadata_settings VALUES ('client_order_link_roles','1')")
        with self.assertRaisesRegex(RuntimeError, 'роли связей'):
            remote.check_event_rename_compatibility(self.db, release)
        (release / 'order_links.py').write_text('ORDER_LINKS_VERSION = 1\nORDER_LINK_ROLES_VERSION = 1')
        remote.check_event_rename_compatibility(self.db, release)
        with sqlite3.connect(self.db) as db:
            db.execute("INSERT INTO metadata_settings VALUES ('client_order_link_status','1')")
        with self.assertRaisesRegex(RuntimeError, 'автоматические статусы'):
            remote.check_event_rename_compatibility(self.db, release)
        (release / 'order_links.py').write_text('ORDER_LINKS_VERSION = 1\nORDER_LINK_ROLES_VERSION = 1\nORDER_LINK_STATUS_VERSION = 1')
        remote.check_event_rename_compatibility(self.db, release)
        with sqlite3.connect(self.db) as db:
            db.execute("INSERT INTO metadata_settings VALUES ('client_order_link_star','1')")
        with self.assertRaisesRegex(RuntimeError, 'одного главного'):
            remote.check_event_rename_compatibility(self.db, release)
        (release / 'order_links.py').write_text('ORDER_LINKS_VERSION = 1\nORDER_LINK_ROLES_VERSION = 1\nORDER_LINK_STATUS_VERSION = 1\nORDER_LINK_STAR_VERSION = 1')
        remote.check_event_rename_compatibility(self.db, release)

    def test_old_code_cannot_recreate_separate_week_comment_storage(self):
        release = self.base / 'old-week-comments'
        release.mkdir()
        (release / 'local_metadata.py').touch()
        with sqlite3.connect(self.db) as db:
            db.execute('CREATE TABLE metadata_settings (key TEXT PRIMARY KEY,value TEXT)')
            db.execute("INSERT INTO metadata_settings VALUES ('weekly_events_unified','1')")
        with self.assertRaisesRegex(RuntimeError, 'объединены'):
            remote.check_event_rename_compatibility(self.db, release)
        (release / 'order_calendar.py').write_text('WEEKLY_EVENTS_UNIFIED_VERSION = 1')
        remote.check_event_rename_compatibility(self.db, release)

    def test_old_code_cannot_expose_trashed_supplier_events(self):
        release = self.base / 'old-events'
        release.mkdir()
        with sqlite3.connect(self.db) as db:
            db.execute('CREATE TABLE folder_renames (session TEXT,state TEXT,mappings TEXT,paths_applied INTEGER)')
            db.execute("INSERT INTO folder_renames VALUES ('journal','complete',?,1)",
                       (json.dumps([{'kind': 'supplier-event-trash'}]),))
        with self.assertRaisesRegex(RuntimeError, 'события в корзине'):
            remote.check_event_rename_compatibility(self.db, release)
        (release / 'event_trash.py').write_text('EVENT_TRASH_VERSION = 1')
        remote.check_event_rename_compatibility(self.db, release)

    def test_old_code_cannot_restore_trashed_invoices_into_active_list(self):
        release = self.base / 'old-invoices'
        release.mkdir()
        with sqlite3.connect(self.db) as db:
            db.execute('CREATE TABLE invoices (data TEXT)')
            db.execute('INSERT INTO invoices VALUES (?)', (json.dumps({'_trash': {'state': 'complete'}}),))
        with self.assertRaisesRegex(RuntimeError, 'счета в корзине'):
            remote.check_event_rename_compatibility(self.db, release)
        (release / 'invoices.py').write_text('INVOICE_TRASH_VERSION = 1')
        remote.check_event_rename_compatibility(self.db, release)

    def test_old_code_cannot_open_plans_as_invoice_drafts(self):
        release = self.base / 'old-plans'
        release.mkdir()
        with sqlite3.connect(self.db) as db:
            db.execute('CREATE TABLE invoices (data TEXT)')
            db.execute('INSERT INTO invoices VALUES (?)', (json.dumps({'kind': 'planned', 'version': 1}),))
        with self.assertRaisesRegex(RuntimeError, 'планы счетов или оплат'):
            remote.check_event_rename_compatibility(self.db, release)
        (release / 'invoices.py').write_text('INVOICE_PLAN_VERSION = 1')
        remote.check_event_rename_compatibility(self.db, release)

    def test_old_code_cannot_bypass_pending_folder_rename(self):
        release = self.base / "old-code"
        release.mkdir()
        (release / 'event_folder_undo.py').touch()
        with sqlite3.connect(self.db) as db:
            db.execute("CREATE TABLE folder_renames (session TEXT,state TEXT,mappings TEXT,paths_applied INTEGER)")
            db.execute("INSERT INTO folder_renames VALUES ('journal','pending','[]',1)")
        with self.assertRaisesRegex(RuntimeError, "переименование папки"):
            remote.check_event_rename_compatibility(self.db, release)
        (release / 'folder_rename_undo.py').touch()
        remote.check_event_rename_compatibility(self.db, release)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name).resolve()
        self.documents = self.base / "documents"
        self.documents.mkdir()
        self.root = self.base / "manager"
        self.root.mkdir()
        self.data = self.root / "data"
        self.data.mkdir()
        self.db = self.data / remote.database_name(self.documents)
        with sqlite3.connect(self.db) as db:
            db.execute("CREATE TABLE orders (id TEXT, revision INTEGER, exported_revision INTEGER)")
            db.execute("INSERT INTO orders VALUES ('preserve-me', 7, 5)")
        self.settings = {"directory": str(self.root), "documents": str(self.documents), "port": 8765,
                         "host": "0.0.0.0", "python": "/usr/bin/python3"}

    def tearDown(self):
        self.temporary.cleanup()

    def archive(self, files):
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode="w:gz") as archive:
            for name, body in files.items():
                item = tarfile.TarInfo(name)
                item.size = len(body)
                archive.addfile(item, io.BytesIO(body))
        stream.seek(0)
        return stream

    def package(self):
        files = {"server.py": b"# new code\n"}
        manifest = {"release": RELEASE, "files": {name: hashlib.sha256(body).hexdigest() for name, body in files.items()}}
        files[".release-id"] = RELEASE.encode()
        files[".manifest.json"] = json.dumps(manifest).encode()
        return self.archive(files)

    def test_archive_cannot_write_outside_release_or_follow_links(self):
        target = self.base / "release"
        target.mkdir()
        with self.assertRaises(RuntimeError):
            remote.unpack(self.archive({"../escaped": b"bad"}), target, RELEASE)
        self.assertFalse((self.base / "escaped").exists())
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode="w:gz") as archive:
            item = tarfile.TarInfo("linked")
            item.type = tarfile.SYMTYPE
            item.linkname = str(self.documents)
            archive.addfile(item)
        stream.seek(0)
        with self.assertRaises(RuntimeError):
            remote.unpack(stream, target, RELEASE)

    def test_snapshot_includes_committed_wal_and_never_overwrites(self):
        snapshot = self.base / "snapshot.sqlite3"
        with sqlite3.connect(self.db) as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("UPDATE orders SET revision=9")
            db.commit()
            remote.backup_database(self.db, snapshot)
        with closing(sqlite3.connect(snapshot)) as db:
            self.assertEqual(db.execute("SELECT * FROM orders").fetchall(), [("preserve-me", 9, 5)])
        before = snapshot.read_bytes()
        self.assertEqual(before[18:20], b"\x01\x01")
        self.assertFalse(Path(str(snapshot) + "-wal").exists())
        portable = self.base / "portable"
        portable.mkdir()
        copied = portable / "only-database.sqlite3"
        copied.write_bytes(before)
        with closing(sqlite3.connect(copied.as_uri() + "?mode=ro", uri=True)) as db:
            self.assertEqual(db.execute("SELECT * FROM orders").fetchall(), [("preserve-me", 9, 5)])
        with self.assertRaises(RuntimeError):
            remote.backup_database(self.db, snapshot)
        self.assertEqual(snapshot.read_bytes(), before)

    def test_initial_migration_rejects_other_root_and_existing_database(self):
        release_dir = self.base / "release"
        release_dir.mkdir()
        initial = release_dir / ".initial.sqlite3"
        initial.write_bytes(self.db.read_bytes())
        manifest = {"initial_database": {"source_root": "other", "sha256": hashlib.sha256(initial.read_bytes()).hexdigest()}}
        with self.assertRaisesRegex(RuntimeError, "Пути документов"):
            remote.install_database(release_dir, self.base, self.data, self.documents, manifest)
        manifest["initial_database"]["source_root"] = str(self.documents)
        before = self.db.read_bytes()
        with self.assertRaisesRegex(RuntimeError, "уже есть база"):
            remote.install_database(release_dir, self.base, self.data, self.documents, manifest)
        self.assertEqual(self.db.read_bytes(), before)
        self.db.unlink()
        remote.install_database(release_dir, self.base, self.data, self.documents, manifest)
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute("SELECT * FROM orders").fetchall(), [("preserve-me", 7, 5)])

    def test_old_code_cannot_bypass_pending_event_rename_guards(self):
        release = self.base / "compatibility-release"
        release.mkdir()
        remote.check_event_rename_compatibility(self.db, release)
        with sqlite3.connect(self.db) as db:
            db.execute("CREATE TABLE event_renames (state TEXT)")
            db.execute("INSERT INTO event_renames VALUES ('pending')")
        with self.assertRaisesRegex(RuntimeError, "переименование"):
            remote.check_event_rename_compatibility(self.db, release)
        (release / "event_folder_undo.py").write_text("# guards supported")
        remote.check_event_rename_compatibility(self.db, release)
        (release / "event_folder_undo.py").unlink()
        with sqlite3.connect(self.db) as db:
            db.execute("UPDATE event_renames SET state='undone'")
        remote.check_event_rename_compatibility(self.db, release)

    def run_deploy(self, start, renderers=None):
        with patch.object(remote.Path, "home", return_value=self.base / "home"), \
             patch.object(remote, "service_loaded", return_value=True), \
             patch.object(remote, "prepare_launcher", return_value=self.base / "launcher"), \
             patch.object(remote, "prepare_renderers", side_effect=renderers), \
             patch.object(remote, "stop"), patch.object(remote, "start", side_effect=start), \
             patch.object(remote.sys, "stdout", new_callable=io.StringIO), \
             patch.object(remote.sys, "stdin", SimpleNamespace(buffer=self.package())):
            remote.deploy(self.settings, "deploy", RELEASE)

    def test_renderer_build_failure_keeps_current_release_and_database(self):
        previous = self.root / ".releases" / PREVIOUS
        previous.mkdir(parents=True)
        (previous / "server.py").write_text("# old code\n")
        remote.select_release(self.root, PREVIOUS)
        state = {"release": PREVIOUS, "previous": None}
        remote.write_json(self.root / ".deployment.json", state)
        before = self.db.read_bytes()
        with self.assertRaisesRegex(RuntimeError, "compiler failed"):
            self.run_deploy([], RuntimeError("compiler failed"))
        self.assertEqual((self.root / "current").resolve(), previous)
        self.assertEqual(json.loads((self.root / ".deployment.json").read_text()), state)
        self.assertEqual(self.db.read_bytes(), before)
        result = next(self.root.glob(".deploy-history/*/result.json"))
        self.assertEqual(json.loads(result.read_text())["stage"], "renderers")

    def test_update_rejects_empty_database_before_switching_code(self):
        self.db.write_bytes(b"")
        with self.assertRaisesRegex(RuntimeError, "не содержит базу заказов"):
            self.run_deploy([])
        self.assertFalse((self.root / "current").exists())
        self.assertEqual(self.db.stat().st_size, 0)

    def test_code_deploy_preserves_pending_database_and_creates_snapshot(self):
        self.run_deploy([{"status": "ok", "release": RELEASE}])
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute("SELECT * FROM orders").fetchall(), [("preserve-me", 7, 5)])
        self.assertTrue((self.root / "current/data").is_symlink())
        self.assertEqual((self.root / "current/data").resolve(), self.data)
        self.assertEqual(len(list(self.root.glob(".deploy-history/*/before.sqlite3"))), 1)

    def test_failed_update_restores_previous_code_without_restoring_old_data(self):
        old = self.root / ".releases" / PREVIOUS
        old.mkdir(parents=True)
        (old / "server.py").write_text("# old code\n")
        remote.select_release(self.root, PREVIOUS)
        state = {"release": PREVIOUS, "previous": None}
        remote.write_json(self.root / ".deployment.json", state)
        agent = self.base / "home/Library/LaunchAgents" / (remote.LABEL + ".plist")
        agent.parent.mkdir(parents=True)
        agent.write_bytes(b"previous agent")
        with self.assertRaisesRegex(RuntimeError, "failed health"):
            self.run_deploy([RuntimeError("failed health"), {"status": "ok", "release": PREVIOUS}])
        self.assertEqual((self.root / "current").resolve(), old)
        self.assertEqual(json.loads((self.root / ".deployment.json").read_text()), state)
        self.assertEqual(agent.read_bytes(), b"previous agent")
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute("SELECT revision,exported_revision FROM orders").fetchone(), (7, 5))

    def test_failed_first_start_leaves_database_and_allows_retry(self):
        with self.assertRaises(RuntimeError):
            self.run_deploy([RuntimeError("failed health")])
        self.assertFalse((self.root / "current").is_symlink())
        self.assertFalse((self.root / ".deployment.json").exists())
        self.assertTrue(self.db.exists())


if __name__ == "__main__":
    unittest.main()
