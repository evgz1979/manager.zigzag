import json
import subprocess
import sys
import unicodedata
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import folder_layout as layout
import order_folders
import order_creation
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

    def test_http_creates_empty_folder_and_registers_card_with_safe_portable_journal(self):
        manager.DATABASE_ONLY = True
        self.folder("Клиент/Адрес")
        self.file("Клиент/Адрес/!.txt", b"parent note")
        with patch.object(manager, 'schedule_order_sync'), patch.object(manager, 'schedule_todo_refresh'):
            status, _, body = self.http("/api/order-folder-create", "POST", json.dumps({"path": "Клиент/Адрес", "date": "2026-10-19", "title": "  Новая вывеска  "}))
        self.assertEqual(status, 201)
        created = json.loads(body)
        self.assertEqual(created["path"], "Клиент/Адрес/2026-10-19 - Новая вывеска")
        target = self.root / created["path"]
        self.assertEqual(list(target.iterdir()), [])
        self.assertTrue(created['registered'])
        card = manager.order_store().get(created['path'])
        self.assertEqual((card['title'], card['status'], card['note']), ('Новая вывеска', 'new', ''))
        self.assertEqual([item['id'] for item in manager.listed_orders()['orders']], [card['id']])
        self.assertEqual((self.root / "Клиент/Адрес/!.txt").read_bytes(), b"parent note")
        session = self.root / created["journal"]
        self.assertTrue((session / ".before.json").exists())
        self.assertEqual(json.loads((session / ".result.json").read_text())["status"], "created")
        self.assertEqual([x["phase"] for x in layout.records(session)], ["session_created", "intent", "commit", "complete"])
        undone = subprocess.run([sys.executable, str(session / ".folder-layout.py"), "undo", str(session), "--apply"], capture_output=True)
        self.assertNotEqual(undone.returncode, 0)
        self.assertIn('SQLite', undone.stderr.decode())
        self.assertTrue(target.exists())
        self.assertEqual(manager.order_store().get(created['path'])['id'], card['id'])

    def test_manager_creation_registers_in_all_allowed_locations_but_not_events_or_old_folders(self):
        manager.DATABASE_ONLY = True
        parents = ('Клиент/Адрес', 'Клиент/Другой объект/2026', '# work', '#work/# newtek', '# work/# glass', '# moneys/# сверка')
        for index, parent in enumerate(parents):
            self.folder(parent)
            with patch.object(manager, 'schedule_order_sync'), patch.object(manager, 'schedule_todo_refresh'):
                status, _, body = self.http('/api/order-folder-create', 'POST', json.dumps({'path': parent, 'date': '2026-10-21', 'title': 'Новый ' + str(index)}))
            self.assertEqual(status, 201, body)
            created = json.loads(body)
            card = manager.order_store().get(created['path'])
            self.assertIsNotNone(card)
            self.assertEqual(card['title'], 'Новый ' + str(index))
            opened = manager.read_folder(created['path'])
            self.assertEqual(opened['order']['id'], card['id'])
            self.assertNotIn('folderNote', opened)
            duplicate, _, _ = self.http('/api/order-folder-create', 'POST', json.dumps({'path': parent, 'date': '2026-10-21', 'title': 'Новый ' + str(index)}))
            self.assertEqual(duplicate, 409)
            self.assertEqual(manager.order_store().get(created['path'])['id'], card['id'])
            event = created['path'] + '/00 - Вручную'
            self.folder(event)
            self.assertFalse(manager.read_folder(event)['canRegisterOrder'])
            self.assertIsNone(manager.order_store().get(event))
        for path in ('Клиент/Адрес/2026-10-20 - Ранее', '#work/# newtek/2026-10-20 - Вручную'):
            self.folder(path)
            view = manager.read_folder(path)
            self.assertNotIn('order', view)
            self.assertTrue(view['canRegisterOrder'])
            self.assertIsNone(manager.order_store().get(path))
        listed = manager.listed_orders()['orders']
        self.assertFalse(any(item['path'].startswith(('# work/', '#work/')) for item in listed))

    def test_registration_failure_recovers_same_folder_and_identity_after_restart(self):
        manager.DATABASE_ONLY = True
        self.folder('Клиент/Адрес')
        payload = {'path': 'Клиент/Адрес', 'date': '2026-10-21', 'title': 'Восстановление'}
        with patch.object(order_creation, 'register', side_effect=OSError('SQLite временно занята')):
            status, _, body = self.http('/api/order-folder-create', 'POST', json.dumps(payload))
        self.assertEqual(status, 409, body)
        path = 'Клиент/Адрес/2026-10-21 - Восстановление'
        self.assertTrue((self.root / path).is_dir())
        store = manager.order_store()
        self.assertIsNone(store.get(path))
        with store.connect() as db:
            expected = json.loads(db.execute("SELECT data FROM metadata_records WHERE kind='order_creation' AND path=?", (path,)).fetchone()[0])['order_id']
        order_creation.recover(manager.order_store())
        self.assertEqual(store.get(path)['id'], expected)
        order_creation.recover(manager.order_store())
        self.assertEqual(len(store.list()), 1)
        self.assertEqual(self.http('/api/order-folder-create', 'POST', json.dumps(payload))[0], 409)

    def test_dangling_saved_card_is_not_overwritten_by_creating_same_folder(self):
        manager.DATABASE_ONLY = True
        self.folder('Клиент/Адрес')
        path = 'Клиент/Адрес/2026-10-21 - Прежний'
        self.folder(path)
        card = manager.order_store().add(path, {'title': 'Прежняя карточка', 'status': 'done', 'note': 'Сохранить'})
        (self.root / path).rmdir()
        status, _, _ = self.http('/api/order-folder-create', 'POST', json.dumps({'path': 'Клиент/Адрес', 'date': '2026-10-21', 'title': 'Прежний'}))
        self.assertEqual(status, 400)
        self.assertFalse((self.root / path).exists())
        self.assertEqual(manager.order_store().get(path), card)

    def test_explicit_add_retries_pending_manager_creation_with_same_identity(self):
        manager.DATABASE_ONLY = True
        self.folder('Клиент/Адрес')
        with patch.object(order_creation, 'register', side_effect=OSError('Временно занято')):
            self.assertEqual(self.http('/api/order-folder-create', 'POST', json.dumps({'path': 'Клиент/Адрес', 'date': '2026-10-21', 'title': 'Повтор'}))[0], 409)
        path = 'Клиент/Адрес/2026-10-21 - Повтор'
        with manager.order_store().connect() as db:
            identity = json.loads(db.execute("SELECT data FROM metadata_records WHERE kind='order_creation' AND path=?", (path,)).fetchone()[0])['order_id']
        with patch.object(manager, 'schedule_order_sync'), patch.object(manager, 'schedule_todo_refresh'):
            status, _, body = self.http('/api/order-add', 'POST', json.dumps({'path': path}))
        self.assertEqual(status, 201, body)
        self.assertEqual(json.loads(body)['id'], identity)

    def test_external_folder_conflict_is_not_automatically_registered_on_retry(self):
        manager.DATABASE_ONLY = True
        self.folder('Клиент/Адрес')
        real_apply = layout.apply
        def conflict(session):
            destination = self.root / layout.load_plan(session)['operations'][-1]['destination']
            destination.mkdir()
            (destination / 'external.txt').write_bytes(b'preserve')
            real_apply(session)
        with patch.object(layout, 'apply', side_effect=conflict):
            status, _, _ = self.http('/api/order-folder-create', 'POST', json.dumps({'path': 'Клиент/Адрес', 'date': '2026-10-21', 'title': 'Конфликт'}))
        self.assertEqual(status, 409)
        path = 'Клиент/Адрес/2026-10-21 - Конфликт'
        order_creation.recover(manager.order_store())
        self.assertIsNone(manager.order_store().get(path))
        self.assertEqual((self.root / path / 'external.txt').read_bytes(), b'preserve')

    def test_creation_allowed_only_in_object_not_in_container_order_or_service(self):
        paths = {"": False, "Клиент": False, "Клиент/Адрес": True, "Клиент/Адрес/2026": True,
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
        invalid = [{"date": value} for value in (None, 20261019, "2026-02-30", "2026-00-00", "26-10-19", "2026-1-01", "1800-01-01", "2100-01-01")]
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
