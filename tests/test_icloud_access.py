import errno
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import icloud_access as access
import native_renderers
import test_server as fixtures

manager = fixtures.manager


class CloudReadTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.card = self.root / "!.txt"
        self.raw = b"\xef\xbb\xbf" + "[Заметка]\r\n> Исходные байты\r\n".encode()
        self.card.write_bytes(self.raw)

    def tearDown(self):
        self.temporary.cleanup()

    def test_local_read_preserves_bytes_without_starting_helper(self):
        before = self.card.stat().st_mtime_ns
        with patch.object(access, "_coordinated_read") as helper:
            self.assertEqual(access.read_bytes(self.card), self.raw)
            helper.assert_not_called()
        self.assertEqual(self.card.stat().st_mtime_ns, before)

    def test_deadlock_uses_bounded_separate_coordinated_read(self):
        with patch.object(access.sys, "platform", "darwin"), \
                patch.object(access, "_plain_read", side_effect=OSError(errno.EDEADLK, "deadlock")), \
                patch.object(access, "renderer", return_value=Path("/helper")), \
                patch.object(access.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, self.raw)) as run:
            self.assertEqual(access.read_bytes(self.card), self.raw)
            self.assertEqual(run.call_args[0][0], ["/helper", str(self.card), str(access.MAX_BYTES)])
            self.assertEqual(run.call_args[1]["timeout"], access.READ_TIMEOUT)
            self.assertTrue(run.call_args[1]["check"])

    def test_other_errors_do_not_request_cloud_download(self):
        with patch.object(access, "_plain_read", side_effect=PermissionError(errno.EACCES, "denied")), \
                patch.object(access, "_coordinated_read") as helper:
            with self.assertRaises(PermissionError):
                access.read_bytes(self.card)
            helper.assert_not_called()

    def test_helper_timeout_keeps_file_and_reports_automatic_retry(self):
        with patch.object(access.sys, "platform", "darwin"), \
                patch.object(access, "_plain_read", side_effect=OSError(errno.EDEADLK, "deadlock")), \
                patch.object(access, "_coordinated_read", side_effect=subprocess.TimeoutExpired("helper", 8)):
            with self.assertRaises(access.CloudReadPending) as error:
                access.read_bytes(self.card)
        self.assertIn("в очереди", str(error.exception))
        self.assertIn("автоматически", str(error.exception))
        self.assertEqual(self.card.read_bytes(), self.raw)

    def test_size_and_symlinks_are_rejected_without_changing_original(self):
        alias = self.root / "link"
        alias.symlink_to(self.card)
        with self.assertRaises(ValueError):
            access.read_bytes(alias)
        self.card.write_bytes(b"x" * (access.MAX_BYTES + 1))
        with self.assertRaises(ValueError):
            access.read_bytes(self.card)
        self.assertEqual(self.card.stat().st_size, access.MAX_BYTES + 1)

    def test_explicit_journal_limit_preserves_the_default_card_limit(self):
        raw = b'x' * (access.MAX_BYTES + 1)
        self.card.write_bytes(raw)
        with self.assertRaises(ValueError):
            access.read_bytes(self.card)
        self.assertEqual(access.read_bytes(self.card, max_bytes=20 * access.MAX_BYTES), raw)
        with patch.object(access.sys, 'platform', 'darwin'), \
                patch.object(access, '_plain_read', side_effect=OSError(errno.EDEADLK, 'deadlock')), \
                patch.object(access, 'renderer', return_value=Path('/helper')), \
                patch.object(access.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, raw)) as run:
            self.assertEqual(access.read_bytes(self.card, max_bytes=20 * access.MAX_BYTES), raw)
        self.assertEqual(run.call_args.args[0][-1], str(20 * access.MAX_BYTES))
        self.assertEqual(self.card.read_bytes(), raw)

    @unittest.skipUnless(sys.platform == "darwin", "Foundation requires macOS")
    def test_native_helper_reads_exact_bytes_and_rejects_symlinks_and_size(self):
        source = Path(__file__).resolve().parents[1] / "icloud_read.swift"
        binary = native_renderers.build(source, self.root / "native", "icloud-test", 60)
        run = lambda path, limit: subprocess.run([str(binary), str(path), str(limit)], capture_output=True, timeout=10)
        result = run(self.card, access.MAX_BYTES)
        self.assertEqual((result.returncode, result.stdout), (0, self.raw), result.stderr)
        alias = self.root / "link"
        alias.symlink_to(self.card)
        self.assertNotEqual(run(alias, access.MAX_BYTES).returncode, 0)
        self.assertNotEqual(run(self.card, 1).returncode, 0)


class CloudExportTests(unittest.TestCase):
    setUp = fixtures.ManagerTests.setUp
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    order = "Клиент/2026-00-00 - Заказ"
    event = order + "/Фото"

    def pending(self):
        orders = manager.order_store()
        first = orders.add(self.order, {"status": "process", "note": "Прежняя",
            "extra_blocks": {"Материалы": "Не потерять"}})
        orders.sync()
        saved = orders.save({"path": self.order, "revision": first["revision"], "title": first["title"],
            "status": "process", "note": "Новая карточка", "todo_items": [{"text": "Сделать", "done": False}]})
        notes = manager.folder_note_store()
        initial = notes.read(self.event)
        initial = notes.save({"path": self.event, "revision": initial["revision"], "note": "Прежняя заметка"})
        notes.sync()
        notes.save({"path": self.event, "revision": initial["revision"], "note": "Новая заметка"})
        return saved

    def test_export_recovers_deadlock_without_losing_fields_or_extra_sections(self):
        self.pending()
        plain = access._plain_read
        def blocked(path):
            if path.name == "!.txt":
                raise OSError(errno.EDEADLK, "deadlock")
            return plain(path)
        with patch.object(access.sys, "platform", "darwin"), \
                patch.object(access, "_plain_read", side_effect=blocked), \
                patch.object(access, "_coordinated_read", side_effect=plain) as recovery:
            manager.order_store().sync()
            manager.folder_note_store().sync()
        self.assertGreater(recovery.call_count, 0)
        order = manager.order_store().get(self.order)
        event = manager.folder_note_store().get(self.event)
        self.assertFalse(order["sync_pending"])
        self.assertFalse(event["sync_pending"])
        self.assertEqual((order["note"], event["note"]), ("Новая карточка", "Новая заметка"))
        body = manager.order_document.load(self.root / self.order, manager.STATUS_LABELS)
        self.assertEqual(body["extra_blocks"]["Материалы"], "Не потерять")
        self.assertEqual(manager.order_document.read_todos(body["extra_blocks"]), [{"text": "Сделать", "done": False}])

    def test_failed_recovery_keeps_durable_queue_and_originals_until_next_success(self):
        self.pending()
        originals = {path: (self.root / path / "!.txt").read_bytes() for path in (self.order, self.event)}
        with patch.object(access.sys, "platform", "darwin"), \
                patch.object(access, "_plain_read", side_effect=OSError(errno.EDEADLK, "deadlock")), \
                patch.object(access, "_coordinated_read", side_effect=subprocess.TimeoutExpired("helper", 8)):
            manager.order_store().sync()
            manager.folder_note_store().sync()
        for record in (manager.order_store().get(self.order), manager.folder_note_store().get(self.event)):
            self.assertTrue(record["sync_pending"])
            self.assertIn("автоматически", record["sync_error"])
        self.assertEqual({path: (self.root / path / "!.txt").read_bytes() for path in originals}, originals)
        manager.order_store().sync()
        manager.folder_note_store().sync()
        self.assertFalse(manager.order_store().get(self.order)["sync_pending"])
        self.assertFalse(manager.folder_note_store().get(self.event)["sync_pending"])
