from contextlib import contextmanager, nullcontext
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch
import zipfile

import folder_rename_undo
import order_nas_archive
import test_server as fixtures

manager = fixtures.manager


class OrderNASArchiveTests(unittest.TestCase):
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url
    tearDown = fixtures.ManagerTests.tearDown

    def setUp(self):
        fixtures.ManagerTests.setUp(self)
        mode = patch.object(manager, "DATABASE_ONLY", True)
        mode.start()
        self.patches.append(mode)
        self.store = manager.order_store()
        self.nas = self.base / "NAS"
        self.nas.mkdir()
        mount = patch.object(order_nas_archive.nas_archive, "mounted_root", self.mounted_root)
        mount.start()
        self.patches.append(mount)
        self.path = "Клиент/Объект/2026-11-22 - Дубль"
        self.file(self.path + "/Событие/файл.txt", b"source content")
        self.file(self.path + "/.history", b"hidden content")
        self.folder(self.path + "/Пусто")
        (self.root / self.path / "link").symlink_to("Событие/файл.txt")
        self.order = self.store.add(self.path, {"status": "new", "note": "Заметка", "amount": 1000})

    @contextmanager
    def mounted_root(self, _):
        fd = os.open(self.nas, os.O_RDONLY | os.O_DIRECTORY)
        try:
            yield fd, os.fstat(fd).st_dev, self.nas, "smb://test/Safe"
        finally:
            os.close(fd)

    def remove_registration(self):
        return self.store.remove({"path": self.path, "revision": self.order["revision"], "confirmed": True})

    def run_archive(self, proposal):
        return order_nas_archive.archive_order(self.store, proposal, nullcontext, lambda **fields: None)

    def test_only_removed_order_is_eligible_and_stale_confirmation_is_refused(self):
        with self.assertRaisesRegex(ValueError, "из списка"):
            order_nas_archive.preview(self.store, self.path)
        draft = "Клиент/Объект/2026-11-22 - Новый"
        self.folder(draft)
        with self.assertRaisesRegex(ValueError, "из списка"):
            order_nas_archive.preview(self.store, draft)
        self.remove_registration()
        old = order_nas_archive.preview(self.store, self.path)
        self.store.import_folder(self.path)
        with self.assertRaisesRegex(ValueError, "из списка"):
            self.run_archive(old)
        self.assertTrue((self.root / self.path).is_dir())
        self.assertEqual(list(self.nas.iterdir()), [])

    def test_nas_failure_or_invalid_zip_leaves_source_and_database(self):
        self.remove_registration()
        proposal = order_nas_archive.preview(self.store, self.path)
        with patch.object(order_nas_archive.nas_archive, "mounted_root", side_effect=FileNotFoundError("SMB offline")):
            with self.assertRaisesRegex(FileNotFoundError, "SMB offline"):
                self.run_archive(proposal)
        with patch.object(order_nas_archive.subprocess, "run"):
            with self.assertRaises(zipfile.BadZipFile):
                self.run_archive(proposal)
        self.assertEqual(list(self.nas.rglob("*.zip")), [])
        self.assertTrue((self.root / self.path / ".history").is_file())
        self.assertEqual(self.store.get(self.path, include_unregistered=True)["id"], self.order["id"])

    def test_archive_name_collision_preserves_both_folders(self):
        self.remove_registration()
        proposal = order_nas_archive.preview(self.store, self.path)
        collision = self.nas / proposal["archive"]
        collision.parent.mkdir(parents=True)
        collision.write_bytes(b"previous file")
        with self.assertRaises(FileExistsError):
            self.run_archive(proposal)
        self.assertEqual(collision.read_bytes(), b"previous file")
        self.assertTrue((self.root / self.path / ".history").is_file())

    def test_http_archives_full_folder_after_confirmation_and_preserves_card(self):
        self.remove_registration()
        data = json.loads(self.http(self.url("/api/folder", self.path))[2])
        self.assertTrue(data["orderWasRegistered"])
        self.assertTrue(data["canManageServiceFolders"])
        self.assertNotIn("order", data)
        code, _, body = self.http(self.url("/api/order-archive", self.path))
        self.assertEqual(code, 200, body)
        view = json.loads(body)
        self.assertIn("/Deleted Orders/Клиент/Объект/", view["nas_path"])
        headers = {"Content-Type": "application/json", "X-Manager-Order-Archive": "1"}
        endpoint = "/api/order-archive"
        self.assertEqual(self.http(endpoint, "POST", json.dumps({**view, "confirmed": True}))[0], 403)
        self.assertEqual(self.http(endpoint, "POST", json.dumps(view), headers)[0], 400)
        with patch.object(manager, "refresh_after_object_move"):
            code, _, body = self.http(endpoint, "POST", json.dumps({**view, "confirmed": True}), headers)
            self.assertEqual(code, 202, body)
            order_nas_archive.wait_for_jobs()
        code, _, body = self.http("/api/order-archive-status?id=" + view["id"])
        self.assertEqual(code, 200, body)
        result = json.loads(body)
        self.assertEqual(result["phase"], "complete", result)
        self.assertEqual(result["warning"], "")
        self.assertFalse((self.root / self.path).exists())
        self.assertEqual(list((self.root / Path(self.path).parent).iterdir()), [])
        archive = Path(result["nas_path"])
        self.assertEqual(archive, self.nas / view["archive"])
        self.assertTrue(zipfile.is_zipfile(archive))
        self.assertEqual(self.store.list(include_unregistered=True), [])
        with self.store.connect() as db:
            card = db.execute("SELECT path,note,amount,registered FROM orders WHERE id=?", (self.order["id"],)).fetchone()
            self.assertIn(folder_rename_undo.ORDER_NAS_STAGING_PREFIX, card["path"])
            self.assertEqual((card["note"], card["amount"], card["registered"]), ("Заметка", 1000, 0))
            row = db.execute("SELECT state FROM folder_renames").fetchone()
            self.assertEqual(row["state"], "complete")
        self.assertTrue((self.root / result["journal"] / ".verified-archive.json").exists())
