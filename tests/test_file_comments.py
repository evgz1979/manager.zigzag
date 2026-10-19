import json
import unittest
import unicodedata
from unittest.mock import patch
import test_server as fixtures

manager = fixtures.manager
comments = manager.file_comments


class FileCommentTests(unittest.TestCase):
    setUp = fixtures.ManagerTests.setUp
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url

    def test_comments_for_every_file_type_are_portable_and_do_not_modify_originals(self):
        for extension in ("pdf", "cdr", "jpg", "mp4", "mp3", "txt", "zip"):
            path = "Клиент/2026-00-00 - Заказ/Фото/файл # %." + extension
            self.file(path, b"original bytes")
            target = self.root / path
            before = target.stat()
            original_count = manager.read_folder("Клиент/2026-00-00 - Заказ/Фото")["fileCount"]
            record = comments.read(target)
            self.assertEqual(record, {"comment": "", "revision": "missing"})
            note = "Проверить " + extension + "\n\n[Комментарий]\n> не терять переносы\n"
            saved = comments.save(target, note, record["revision"])
            self.assertEqual(comments.read(target), saved)
            self.assertEqual(saved["comment"], note)
            name, _, folder, document = comments.paths(target)
            self.assertIn(json.dumps(name, ensure_ascii=False), document.read_text())
            self.assertEqual(target.read_bytes(), b"original bytes")
            self.assertEqual(target.stat().st_mtime_ns, before.st_mtime_ns)
            listing = manager.read_folder("Клиент/2026-00-00 - Заказ/Фото")
            self.assertEqual(listing["fileCount"], original_count)
            self.assertEqual(next(file["comment"] for file in listing["files"] if file["path"] == path), note)

    def test_folder_captions_follow_external_changes_and_invalid_comment_keeps_file_visible(self):
        path = "# docs/Внутри/readme.txt"
        target = self.root / path
        listing = lambda: manager.read_folder("# docs/Внутри")
        self.assertEqual(listing()["files"][0]["comment"], "")
        comments.save(target, "Подпись к превью", "missing")
        self.assertEqual(listing()["files"][0]["comment"], "Подпись к превью")
        _, _, _, document = comments.paths(target)
        document.write_text(document.read_text().replace("Подпись к превью", "Изменено извне"))
        self.assertEqual(listing()["files"][0]["comment"], "Изменено извне")
        record = comments.read(target)
        comments.save(target, "", record["revision"])
        self.assertEqual(listing()["files"][0]["comment"], "")
        document.write_text("Нераспознанный комментарий")
        broken = listing()
        self.assertEqual(broken["fileCount"], 1)
        self.assertEqual(broken["files"][0]["path"], path)
        self.assertEqual(broken["files"][0]["comment"], "")
        self.assertTrue(any("комментарий" in warning for warning in broken["warnings"]))

    def test_versions_external_edits_history_and_clear_do_not_lose_data(self):
        target = self.root / "# docs/Внутри/readme.txt"
        self.assertEqual(comments.read(target)["revision"], "missing")
        self.assertFalse((target.parent / ".file-comments").exists())
        first = comments.save(target, "Первый комментарий", "missing")
        _, key, folder, document = comments.paths(target)
        original = document.read_bytes()
        second = comments.save(target, "Второй\nкомментарий", first["revision"])
        history = folder / ".history" / ("." + key) / ("." + first["revision"] + ".txt")
        self.assertEqual(history.read_bytes(), original)
        with self.assertRaises(manager.FileCommentConflict):
            comments.save(target, "Устаревшая запись", first["revision"])
        document.write_text(document.read_text().replace("> Второй", "> Правка извне"))
        external = comments.read(target)
        with self.assertRaises(manager.FileCommentConflict):
            comments.save(target, "Не затирать внешнее", second["revision"])
        self.assertEqual(comments.read(target), external)
        cleared = comments.save(target, "", external["revision"])
        self.assertEqual(cleared["comment"], "")
        self.assertEqual(comments.read(target), cleared)

    def test_external_deletion_does_not_attach_orphan_comment_to_another_file(self):
        event = "Клиент/2026-00-00 - Заказ/Фото"
        removed = self.root / event / "01 - удалить.txt"
        survivor = self.root / event / "02 - оставить.txt"
        empty = self.root / event / "03 - без комментария.txt"
        for target in (removed, survivor, empty):
            target.write_text(target.name)
        comments.save(removed, "Комментарий удалённого", "missing")
        previous = comments.save(survivor, "Свой комментарий", "missing")
        previous_key = comments.binding(survivor)
        orphan = comments.paths(removed)[3]
        original = orphan.read_bytes()
        removed.unlink()  # Удаление вне менеджера оставляет прежний файл комментария.
        for _ in range(2):
            listing = {item["path"]: item["comment"] for item in manager.read_folder(event)["files"]}
            self.assertNotIn(event + "/01 - удалить.txt", listing)
            self.assertEqual(listing[event + "/02 - оставить.txt"], "Свой комментарий")
            self.assertEqual(listing[event + "/03 - без комментария.txt"], "")
        self.assertEqual(comments.read(survivor), previous)
        self.assertEqual(comments.binding(survivor), previous_key)
        self.assertEqual(orphan.read_bytes(), original)
        self.assertEqual(self.http(self.url("/api/file-comment", event + "/01 - удалить.txt"))[0], 404)

    def test_failed_atomic_write_keeps_current_comment_and_original_file(self):
        target = self.root / "# docs/Внутри/readme.txt"
        first = comments.save(target, "Не потерять", "missing")
        _, _, _, document = comments.paths(target)
        original = document.read_bytes()
        write = comments.atomic_write

        def fail_current(path, body):
            if path == document:
                raise OSError("Запись недоступна")
            write(path, body)

        with patch.object(comments, "atomic_write", side_effect=fail_current), self.assertRaises(OSError):
            comments.save(target, "Новый текст", first["revision"])
        self.assertEqual(document.read_bytes(), original)
        self.assertEqual(target.read_bytes(), b"common")
        self.assertEqual(comments.read(target), first)

    def test_http_comments_conflicts_validation_and_hidden_sidecars(self):
        path = "Клиент/2026-00-00 - Заказ/Фото/файл%2F #.txt"
        status, _, body = self.http(self.url("/api/file-comment", path))
        self.assertEqual((status, json.loads(body)["revision"]), (200, "missing"))
        payload = {"path": path, "comment": "Комментарий\nс телефона", "revision": "missing",
                   "comment_key": json.loads(body)["comment_key"]}
        status, _, body = self.http("/api/file-comment", "POST", json.dumps(payload))
        saved = json.loads(body)
        self.assertEqual((status, saved["comment"]), (200, payload["comment"]))
        status, _, _ = self.http("/api/file-comment", "POST", json.dumps({**payload, "comment": "Старая версия"}))
        self.assertEqual(status, 409)
        for invalid in (None, True, "x" * 100001, "nul\x00"):
            status, _, _ = self.http("/api/file-comment", "POST", json.dumps({**payload, "revision": saved["revision"], "comment": invalid}))
            self.assertEqual(status, 400)
        for invalid in ("../outside.txt", "/tmp/outside", "# docs", "Клиент/.secret", path + "/нет"):
            status, _, _ = self.http(self.url("/api/file-comment", invalid))
            self.assertIn(status, (400, 404))
        _, _, _, hidden = comments.paths(self.root / path)
        status, _, _ = self.http(self.url("/api/file", hidden.relative_to(self.root).as_posix()))
        self.assertEqual(status, 400)

    def test_browser_binding_rejects_another_filename_folder_and_stale_folder_location(self):
        event = "Клиент/2026-00-00 - Заказ/Фото"
        paths = [event + "/first.txt", event + "/second.txt", event + "/Глубже/first.txt"]
        for path in paths:
            self.file(path, b"original")
        records = {path: json.loads(self.http(self.url("/api/file-comment", path))[2]) for path in paths}
        self.assertEqual(len({row["comment_key"] for row in records.values()}), len(paths))
        listing = {row["path"]: row for row in manager.read_folder(event)["files"]}
        self.assertTrue(all(listing[path]["comment_key"] == row["comment_key"] for path, row in records.items()))
        source = records[paths[0]]
        for other in paths[1:]:
            status, _, _ = self.http("/api/file-comment", "POST", json.dumps({**source, "path": other, "comment": "Текст другого файла"}))
            self.assertEqual(status, 409)
            self.assertEqual(comments.read(self.root / other), {"comment": "", "revision": "missing"})
        self.assertEqual(self.http("/api/file-comment", "POST", json.dumps({
            "path": paths[0], "comment": "Без привязки", "revision": "missing"}))[0], 409)
        status, _, body = self.http("/api/file-comment", "POST", json.dumps({**source, "comment": "Своя подпись"}))
        self.assertEqual(status, 200)
        before = json.loads(body)
        # Перенос целой папки сохраняет текст, но старое окно получает другой ключ пути.
        destination = "Клиент/2026-00-00 - Заказ/00 - Фото"
        (self.root / event).rename(self.root / destination)
        moved_path = destination + "/first.txt"
        current = json.loads(self.http(self.url("/api/file-comment", moved_path))[2])
        self.assertEqual(current["comment"], "Своя подпись")
        self.assertNotEqual(current["comment_key"], before["comment_key"])
        self.assertEqual(self.http("/api/file-comment", "POST", json.dumps({**before, "path": moved_path, "comment": "Старая вкладка"}))[0], 409)
        self.assertEqual(comments.read(self.root / moved_path)["comment"], "Своя подпись")

    def test_symlinks_cannot_redirect_comments_or_history(self):
        target = self.root / "# docs/Внутри/readme.txt"
        alias = target.parent / "alias.txt"
        alias.symlink_to(target)
        status, _, _ = self.http(self.url("/api/file-comment", alias.relative_to(self.root).as_posix()))
        self.assertEqual(status, 400)
        outside = self.base / "outside"
        outside.mkdir()
        _, _, folder, _ = comments.paths(target)
        folder.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            comments.save(target, "Не записывать наружу", "missing")
        self.assertEqual(list(outside.iterdir()), [])
        folder.unlink()
        first = comments.save(target, "Первый", "missing")
        (folder / ".history").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            comments.save(target, "Второй", first["revision"])
        self.assertEqual(comments.read(target), first)
        self.assertEqual(list(outside.iterdir()), [])

    def test_unicode_filename_normalization_uses_the_same_comment(self):
        target = self.root / "Счёт.pdf"
        other = target.with_name(unicodedata.normalize("NFD", target.name))
        self.assertEqual(comments.paths(target)[1:], comments.paths(other)[1:])
