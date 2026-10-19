import json
import subprocess
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import event_folders as events
import event_folder_undo as restore
import folder_layout as layout
import test_server as fixtures

manager = fixtures.manager


class EventFolderTests(unittest.TestCase):
    setUp = fixtures.ManagerTests.setUp
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url
    order = "Клиент/Адрес/2026-10-19 - Заказ"

    def view(self):
        self.folder(self.order)
        return events.preview(self.root, self.order, manager.folder_note_store())

    def payload(self, view=None, **changes):
        view = view or self.view()
        return {"path": self.order, "revision": view["revision"], "title": "Замеры", **changes}

    def rename_payload(self, view=None):
        view = view or self.view()
        return {"path": self.order, "revision": view["revision"], "confirmed": True,
            "names": [{"source": item["source"], "title": item["title"] or "Название события"} for item in view["suggestions"]]}

    def test_http_creation_numbering_gaps_and_exclusions(self):
        self.folder(self.order + "/00 - Замеры")
        self.folder(self.order + "/02 - Монтаж")
        self.folder(self.order + "/# 99 - bills")
        self.folder(self.order + "/.999 - hidden")
        self.file(self.order + "/95 - файл.txt", b"file")
        status, _, body = self.http(self.url("/api/event-folders", self.order))
        self.assertEqual(status, 200)
        view = json.loads(body)
        self.assertEqual((view["next_number"], view["suggestions"]), ("03", []))
        status, _, body = self.http("/api/event-folder-create", "POST", json.dumps(self.payload(view, title="  Согласование  ")))
        self.assertEqual(status, 201)
        created = json.loads(body)
        self.assertEqual(created["name"], "03 - Согласование")
        self.assertEqual(list((self.root / created["path"]).iterdir()), [])
        self.assertFalse(manager.order_store().database.exists())
        session = self.root / created["journal"]
        self.assertEqual(layout.undo(session, True), 1)
        self.assertFalse((self.root / created["path"]).exists())

    def test_starts_at_zero_and_continues_after_99(self):
        self.assertEqual(self.view()["next_number"], "00")
        self.folder(self.order + "/99 - Событие")
        created = events.create(self.root, self.payload())
        self.assertEqual(created["name"], "100 - Замеры")

    def test_short_numbers_are_padded_and_date_names_do_not_become_event_numbers(self):
        self.folder(self.order + "/1 - Замеры")
        self.folder(self.order + "/2026-10-19 - Фото")
        view = self.view()
        self.assertEqual(view["next_number"], "02")
        suggestions = {item["source"]: item for item in view["suggestions"]}
        self.assertEqual(suggestions["1 - Замеры"]["name"], "01 - Замеры")
        self.assertEqual(suggestions["2026-10-19 - Фото"]["name"], "02 - 2026-10-19 - Фото")

    def test_parent_card_export_does_not_invalidate_folder_number_preview(self):
        view = self.view()
        manager.save_status(self.order, "process", "Заметка заказа перед созданием события")
        created = events.create(self.root, self.payload(view))
        self.assertEqual(created["name"], "00 - Замеры")

    def test_only_order_parent_allows_creation(self):
        paths = ("", "Клиент", "Клиент/Адрес", "Клиент/Адрес/2026", self.order + "/01", self.order + "/# bills", "# docs/Внутри")
        for path in paths:
            if path:
                self.folder(path)
        for path in paths:
            with self.subTest(path=path):
                self.assertFalse(manager.read_folder(path)["canCreateEventFolder"])
                with self.assertRaises(ValueError):
                    events.preview(self.root, path)
        self.assertTrue(manager.read_folder(self.order)["canCreateEventFolder"])
        (self.root / "Клиент/Ссылка").symlink_to(self.root / "Клиент/Адрес")
        with self.assertRaises(ValueError):
            events.preview(self.root, "Клиент/Ссылка/2026-10-19 - Заказ")

    def test_suggestions_preserve_valid_numbers_and_do_not_inspect_contents(self):
        for name in ("00 - Замеры", "02 - Монтаж", "02 - Повтор", "03", "Фото", "00-01 - Вариант", "# bills"):
            self.folder(self.order + "/" + name)
        self.file(self.order + "/Фото/Внутри/не трогать.txt", b"original")
        view = self.view()
        by_source = {item["source"]: item for item in view["suggestions"]}
        self.assertNotIn("00 - Замеры", by_source)
        self.assertNotIn("02 - Монтаж", by_source)
        self.assertNotIn("# bills", by_source)
        self.assertEqual(by_source["03"]["title"], "")
        self.assertEqual(by_source["03"]["number"], "03")
        self.assertEqual(by_source["00-01 - Вариант"]["title"], "00-01 - Вариант")
        self.assertEqual(len({item["number"] for item in view["suggestions"]}), 4)
        self.assertEqual(view["next_number"], "04")
        self.assertFalse((self.root / ".folder-layout-history").exists())

    def test_stale_preview_invalid_title_and_conflicts_do_not_change_folders(self):
        view = self.view()
        for title in (None, "", " ", "a/b", "a\\b", "a:b", "a\n", "Ж" * 150):
            with self.subTest(title=title), self.assertRaises(ValueError):
                events.create(self.root, self.payload(view, title=title))
        self.assertFalse((self.root / ".folder-layout-history").exists())
        self.folder(self.order + "/00 - Другая вкладка")
        with self.assertRaises(events.EventFolderConflict):
            events.create(self.root, self.payload(view))
        current = self.view()
        self.file(self.order + "/01 - Замеры", b"existing file")
        with self.assertRaises(events.EventFolderConflict):
            events.create(self.root, self.payload(current))
        with self.assertRaises(events.EventFolderConflict):
            events.create(self.root, self.payload())
        self.assertEqual((self.root / self.order / "01 - Замеры").read_bytes(), b"existing file")

    def test_rename_requires_review_and_valid_complete_list(self):
        self.folder(self.order + "/Фото")
        payload = self.rename_payload()
        for changes in ({"confirmed": False}, {"names": []}, {"names": [{"source": "../Фото", "title": "Название"}]},
                        {"names": [{"source": "Фото", "title": "a/b"}]}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                events.rename(manager.folder_note_store(), {**payload, **changes})
        self.assertTrue((self.root / self.order / "Фото").is_dir())
        self.assertFalse((self.root / ".folder-layout-history").exists())

    def test_rename_preserves_all_bytes_and_database_notes_at_every_depth(self):
        store = manager.order_store()
        self.folder(self.order + "/Фото/Глубже/# bills")
        self.file(self.order + "/Фото/image.txt", b"original")
        self.file(self.order + "/Фото/.file-comments/comment.txt", b"comment history")
        store.add(self.order, {"status": "process", "note": "Заказ"})
        store.sync()
        parent = store.get(self.order)
        notes = manager.folder_note_store()
        records = []
        for path in (self.order + "/Фото", self.order + "/Фото/Глубже/# bills"):
            record = notes.read(path)
            record = notes.save({"path": path, "revision": record["revision"], "note": "Своя заметка", "todo_items": [{"text": "Своя задача", "done": True}]})
            if path == self.order + "/Фото":
                record = notes.save_relevance({"path": path, "revision": record["revision"], "value": "active"})
            records.append(record)
        notes.sync()
        original = {p.relative_to(self.root / self.order / "Фото").as_posix(): p.read_bytes() for p in (self.root / self.order / "Фото").rglob("*") if p.is_file()}
        result = events.rename(notes, self.rename_payload())
        self.assertEqual(result["renamed"], [{"source": self.order + "/Фото", "destination": self.order + "/00 - Фото"}])
        self.assertEqual({p.relative_to(self.root / self.order / "00 - Фото").as_posix(): p.read_bytes() for p in (self.root / self.order / "00 - Фото").rglob("*") if p.is_file()}, original)
        for record in records:
            self.assertIsNone(notes.get(record["path"]))
            renamed = notes.get(record["path"].replace("/Фото", "/00 - Фото", 1))
            self.assertEqual(renamed["note"], record["note"])
            self.assertEqual(renamed["todo_items"], record["todo_items"])
            self.assertEqual(renamed["extra_blocks"], record["extra_blocks"])
            self.assertFalse(renamed["sync_pending"])
            with self.assertRaises(manager.FolderNoteConflict):
                notes.save({"path": record["path"], "revision": record["revision"], "note": "Старая вкладка"})
        self.assertEqual(store.get(self.order), parent)
        self.assertEqual([row["path"] for row in store.list()], [self.order])

    def test_pending_exports_and_legacy_registered_descendants_block_rename(self):
        self.folder(self.order + "/Фото")
        notes = manager.folder_note_store()
        record = notes.read(self.order + "/Фото")
        record = notes.save({"path": record["path"], "revision": record["revision"], "note": "В очереди"})
        with self.assertRaisesRegex(events.EventFolderConflict, "выгрузки"):
            events.rename(notes, self.rename_payload())
        notes.sync()
        self.folder(self.order)
        parent = manager.order_store().add(self.order, {"status": "new", "note": ""})
        with manager.order_store().connect() as db:
            db.execute("UPDATE orders SET path=? WHERE id=?", (self.order + "/Фото/Внутри", parent["id"]))
        with self.assertRaisesRegex(events.EventFolderConflict, "запись заказа"):
            events.rename(notes, self.rename_payload())
        self.assertTrue((self.root / self.order / "Фото").exists())

    def test_standalone_undo_restores_paths_and_preserves_new_pending_edits(self):
        self.folder(self.order + "/Фото")
        notes = manager.folder_note_store()
        before = notes.read(self.order + "/Фото")
        result = events.rename(notes, self.rename_payload())
        current = notes.get(self.order + "/00 - Фото")
        notes.save({"path": current["path"], "revision": current["revision"], "note": "Новый ввод после переименования"})
        self.file(current["path"] + "/new.txt", b"new file")
        session = self.root / result["journal"]
        with self.assertRaisesRegex(ValueError, "restore.py"):
            layout.undo(session, True)
        subprocess.run([sys.executable, str(session / ".restore.py"), str(session), "--apply"], check=True, capture_output=True)
        restored = notes.get(before["path"])
        self.assertEqual(restored["note"], "Новый ввод после переименования")
        self.assertTrue(restored["sync_pending"])
        self.assertEqual((self.root / before["path"] / "new.txt").read_bytes(), b"new file")
        self.assertEqual(restore.undo(session, True), 0)
        notes.sync()
        self.assertFalse(notes.get(before["path"])["sync_pending"])
        with self.assertRaises(manager.FolderNoteConflict):
            notes.save({"path": before["path"], "revision": before["revision"], "note": "Старая вкладка"})

    def test_partial_move_failure_rolls_back_and_crash_blocks_paths_until_undo(self):
        for name in ("Фото", "Эскизы"):
            self.folder(self.order + "/" + name)
        notes = manager.folder_note_store()
        record = notes.read(self.order + "/Фото")
        original = layout.rename_exclusive
        count = 0
        def fail_second(source, destination):
            nonlocal count
            count += 1
            if count == 2:
                raise OSError("Сбой второго переноса")
            return original(source, destination)
        with patch.object(layout, "rename_exclusive", side_effect=fail_second):
            with self.assertRaisesRegex(events.EventFolderConflict, "восстановлены"):
                events.rename(notes, self.rename_payload())
        self.assertTrue((self.root / self.order / "Фото").is_dir())
        self.assertTrue((self.root / self.order / "Эскизы").is_dir())
        self.assertEqual(notes.get(record["path"])["note"], record["note"])
        apply = layout.apply
        def interrupted(session):
            apply(session)
            raise KeyboardInterrupt("После переноса, до commit SQLite")
        with patch.object(layout, "apply", side_effect=interrupted):
            with self.assertRaises(KeyboardInterrupt):
                events.rename(notes, self.rename_payload())
        with self.assertRaises(restore.EventRenamePending):
            notes.get(record["path"])
        with self.assertRaises(restore.EventRenamePending):
            notes.read(self.order + "/00 - Фото")
        with self.assertRaises(restore.EventRenamePending):
            events.preview(self.root, self.order, notes)
        with notes.connect() as db:
            session = db.execute("SELECT session FROM event_renames WHERE state='pending'").fetchone()[0]
        self.assertEqual(restore.undo(session, True), 2)
        self.assertTrue((self.root / record["path"]).is_dir())
        self.assertEqual(notes.get(record["path"])["note"], record["note"])

    def test_http_rename_and_concurrent_creation_use_reviewed_snapshot(self):
        self.folder(self.order + "/Фото")
        status, _, body = self.http("/api/event-folders-rename", "POST", json.dumps(self.rename_payload()))
        self.assertEqual(status, 200)
        self.assertEqual(len(json.loads(body)["renamed"]), 1)
        payload = self.payload()
        def attempt(_):
            try:
                return events.create(self.root, payload)["path"]
            except events.EventFolderConflict:
                return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(attempt, range(2)))
        self.assertEqual(len([result for result in results if result]), 1)

    def test_partial_undo_keeps_durable_guard_and_resumes_after_conflict(self):
        for name in ("Фото", "Эскизы"):
            self.folder(self.order + "/" + name)
        notes = manager.folder_note_store()
        record = notes.read(self.order + "/Фото")
        result = events.rename(notes, self.rename_payload())
        self.file(record["path"], b"external conflict")
        session = self.root / result["journal"]
        with self.assertRaises(FileExistsError):
            restore.undo(session, True)
        self.assertEqual((self.root / record["path"]).read_bytes(), b"external conflict")
        with self.assertRaises(restore.EventRenamePending):
            notes.get(self.order + "/00 - Фото")
        (self.root / record["path"]).unlink()
        restore.undo(session, True)
        self.assertTrue((self.root / record["path"]).is_dir())
        self.assertEqual(notes.get(record["path"])["note"], record["note"])

    def test_journal_failure_and_external_destination_preserve_originals(self):
        self.folder(self.order + "/Фото")
        with patch.object(layout.Plan, "create_session", side_effect=OSError("Нет журнала")):
            with self.assertRaises(OSError):
                events.create(self.root, self.payload())
            with self.assertRaises(OSError):
                events.rename(manager.folder_note_store(), self.rename_payload())
        self.assertTrue((self.root / self.order / "Фото").is_dir())
        original_apply = layout.apply
        def conflict(session):
            operation = layout.load_plan(session)["operations"][0]
            self.file(operation["destination"], b"external")
            original_apply(session)
        with patch.object(layout, "apply", side_effect=conflict):
            with self.assertRaises(events.EventFolderConflict):
                events.rename(manager.folder_note_store(), self.rename_payload())
        self.assertTrue((self.root / self.order / "Фото").is_dir())
        self.assertEqual((self.root / self.order / "00 - Фото").read_bytes(), b"external")
