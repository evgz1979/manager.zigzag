import json
import subprocess
import sys
import unicodedata
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import folder_layout as layout
import order_folders
import test_server as fixtures

manager = fixtures.manager


class OrderFolderTests(unittest.TestCase):
    setUp = fixtures.ManagerTests.setUp
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url

    def create(self, **changes):
        self.folder("Клиент/Адрес")
        return order_folders.create(self.root, changes.get("path", "Клиент/Адрес"), changes.get("date", "2026-10-19"), changes.get("title", "Вывеска"))

    def test_http_creates_empty_folder_and_portable_journal_without_registering(self):
        self.folder("Клиент/Адрес")
        self.file("Клиент/Адрес/!.txt", b"parent note")
        status, _, body = self.http("/api/order-folder-create", "POST", json.dumps({"path": "Клиент/Адрес", "date": "2026-10-19", "title": "  Новая вывеска  "}))
        self.assertEqual(status, 201)
        created = json.loads(body)
        self.assertEqual(created["path"], "Клиент/Адрес/2026-10-19 - Новая вывеска")
        target = self.root / created["path"]
        self.assertEqual(list(target.iterdir()), [])
        self.assertFalse(manager.order_store().database.exists())
        self.assertEqual((self.root / "Клиент/Адрес/!.txt").read_bytes(), b"parent note")
        session = self.root / created["journal"]
        self.assertTrue((session / ".before.json").exists())
        self.assertEqual(json.loads((session / ".result.json").read_text())["status"], "created")
        self.assertEqual([x["phase"] for x in layout.records(session)], ["session_created", "intent", "commit", "complete"])
        subprocess.run([sys.executable, str(session / ".folder-layout.py"), "undo", str(session), "--apply"], check=True, capture_output=True)
        self.assertFalse(target.exists())

    def test_creation_allowed_only_in_object_not_in_container_order_or_service(self):
        paths = {"": False, "Клиент": False, "Клиент/Адрес": True, "Клиент/Адрес/2026": False,
                 "Клиент/Адрес/2026-10-18 - Работа": False, "Клиент/Адрес/2026-10-18 - Работа/01": False,
                 "Клиент/Адрес/# bills": False, "# docs/Внутри": False}
        for path in paths:
            if path:
                self.folder(path)
        for path, allowed in paths.items():
            with self.subTest(path=path):
                self.assertEqual(manager.read_folder(path)["canCreateOrderFolder"], allowed)
                if not allowed:
                    with self.assertRaises(ValueError):
                        self.create(path=path)

    def test_invalid_names_dates_and_paths_do_not_create_journal_or_folder(self):
        invalid = [{"date": value} for value in (None, 20261019, "2026-02-30", "2026-00-00", "26-10-19", "2026-1-01")]
        invalid += [{"title": value} for value in (None, "", "  ", "a/b", "a\\b", "a:b", "a\n", "a\x00b", "Ж" * 150)]
        invalid += [{"path": value} for value in (None, ".", "..", "../Клиент/Адрес", "/tmp", "Клиент/.hidden")]
        for changes in invalid:
            with self.subTest(changes=changes), self.assertRaises((ValueError, FileNotFoundError)):
                self.create(**changes)
        self.assertEqual(list((self.root / "Клиент/Адрес").iterdir()), [])
        self.assertFalse((self.root / ".folder-layout-history").exists())
        result = self.create(date="2028-02-29")
        self.assertTrue((self.root / result["path"]).is_dir())

    def test_duplicate_normalized_name_and_existing_file_are_never_overwritten(self):
        result = self.create(title="Проём")
        self.file(result["path"] + "/document.txt", b"preserve")
        with self.assertRaises(order_folders.OrderFolderConflict):
            self.create(title=unicodedata.normalize("NFD", "Проём"))
        self.file("Клиент/Адрес/2026-10-19 - Вывеска", b"existing file")
        status, _, _ = self.http("/api/order-folder-create", "POST", json.dumps({"path": "Клиент/Адрес", "date": "2026-10-19", "title": "Вывеска"}))
        self.assertEqual(status, 409)
        self.assertEqual((self.root / result["path"] / "document.txt").read_bytes(), b"preserve")
        self.assertEqual((self.root / "Клиент/Адрес/2026-10-19 - Вывеска").read_bytes(), b"existing file")

    def test_symlinks_and_service_ancestors_are_rejected(self):
        self.folder("Клиент/Адрес")
        (self.root / "Клиент/Ссылка").symlink_to(self.root / "Клиент/Адрес")
        self.folder("Клиент/# work/Адрес")
        for path in ("Клиент/Ссылка", "Клиент/# work/Адрес"):
            with self.assertRaises(ValueError):
                self.create(path=path)
        self.assertEqual(list((self.root / "Клиент/Адрес").iterdir()), [])

    def test_journal_failure_prevents_creation_and_undo_preserves_new_user_files(self):
        with patch.object(layout.Plan, "create_session", side_effect=OSError("journal unavailable")):
            with self.assertRaises(OSError):
                self.create()
        self.assertEqual(list((self.root / "Клиент/Адрес").iterdir()), [])
        result = self.create()
        self.file(result["path"] + "/new.txt", b"new user data")
        with self.assertRaises(OSError):
            layout.undo(self.root / result["journal"], True)
        self.assertEqual((self.root / result["path"] / "new.txt").read_bytes(), b"new user data")

    def test_external_conflict_after_plan_is_preserved(self):
        real_apply = layout.apply
        def conflict(session):
            target = self.root / layout.load_plan(session)["operations"][0]["destination"]
            target.mkdir()
            (target / "external.txt").write_bytes(b"external data")
            real_apply(session)
        with patch.object(layout, "apply", side_effect=conflict):
            with self.assertRaises(order_folders.OrderFolderConflict):
                self.create()
        self.assertEqual((self.root / "Клиент/Адрес/2026-10-19 - Вывеска/external.txt").read_bytes(), b"external data")

    def test_concurrent_submissions_create_only_one_folder(self):
        self.folder("Клиент/Адрес")
        def attempt(_):
            try:
                return self.create()["path"]
            except order_folders.OrderFolderConflict:
                return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            result = list(pool.map(attempt, range(2)))
        self.assertEqual(sum(value is not None for value in result), 1)
        self.assertEqual(len(list((self.root / "Клиент/Адрес").iterdir())), 1)


if __name__ == "__main__":
    unittest.main()
