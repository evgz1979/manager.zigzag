import base64
import json
import unittest
from unittest.mock import patch
import test_server as fixtures

manager = fixtures.manager
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=")


class ImageReportTests(unittest.TestCase):
    setUp = fixtures.ManagerTests.setUp
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url

    def build(self, folder, files):
        binary = manager.image_reports.renderer(manager.APP_DIR, manager.APP_DIR / "data")
        with patch.object(manager.image_reports, "renderer", return_value=binary):
            return manager.create_image_report(folder, files)

    def test_mixed_selection_creates_valid_pdf_beside_images_without_overwriting(self):
        folder = "Клиент/2026-00-00 - Заказ"
        image = folder + "/Фото/снимок.png"
        self.file(image, PNG)
        original = (self.root / image).stat()
        manager.file_comments.save(self.root / image, "Размер 1200 мм\nПроверить перед печатью.", "missing")
        other = folder + "/Фото/файл%2F #.txt"
        first = self.build(folder, [image, other, image])
        path = self.root / first["path"]
        before = path.read_bytes()
        self.assertTrue(before.startswith(b"%PDF-"))
        self.assertEqual(path.parent, self.root / folder)
        self.assertEqual((first["imageCount"], first["skippedCount"], first["pages"]), (1, 1, 1))
        second = self.build(folder, [image])
        self.assertNotEqual(first["path"], second["path"])
        self.assertIn(" (2).pdf", second["name"])
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual((self.root / image).read_bytes(), PNG)
        self.assertEqual((self.root / image).stat().st_mtime_ns, original.st_mtime_ns)
        self.assertIn(first["path"], [file["path"] for file in manager.read_folder(folder)["files"]])
        self.assertFalse(list((self.root / folder).glob(".report-*")))

    def test_long_comments_continue_on_new_pages_and_empty_comments_need_no_caption(self):
        folder = "Клиент/2026-00-00 - Заказ"
        first, second = folder + "/a.png", folder + "/b.png"
        self.file(first, PNG)
        self.file(second, PNG)
        manager.file_comments.save(self.root / first, "Строка комментария\n" * 150, "missing")
        report = self.build(folder, [first, second])
        self.assertEqual(report["imageCount"], 2)
        self.assertGreater(report["pages"], 2)

    def test_invalid_paths_nonimages_and_broken_images_create_no_report(self):
        folder = "Клиент/2026-00-00 - Заказ"
        valid = folder + "/a.png"
        self.file(valid, PNG)
        self.file(folder + "/broken.png", b"not an image")
        alias = self.root / folder / "alias.png"
        alias.symlink_to(self.root / valid)
        for files in (None, [], [True], ["../outside.png"], ["# docs/Внутри/readme.txt"],
                      [folder + "/.hidden.png"], [folder + "/alias.png"], [folder + "/Фото/файл%2F #.txt"],
                      [folder + "/broken.png"]):
            with self.subTest(files=files), self.assertRaises((ValueError, FileNotFoundError)):
                self.build(folder, files)
        with patch.object(manager.image_reports, "MAX_IMAGES", 0), self.assertRaises(ValueError):
            self.build(folder, [valid])
        self.assertFalse(list((self.root / folder).glob("report - *.pdf")))
        self.assertFalse(list((self.root / folder).glob(".report-*")))

    def test_http_and_failed_publication_leave_no_partial_file(self):
        folder = "Клиент/2026-00-00 - Заказ"
        image = folder + "/снимок.png"
        self.file(image, PNG)
        payload = json.dumps({"path": folder, "files": [image]})
        binary = manager.image_reports.renderer(manager.APP_DIR, manager.APP_DIR / "data")
        with patch.object(manager.image_reports, "renderer", return_value=binary):
            with patch.object(manager.image_reports, "rename_exclusive", side_effect=PermissionError("Нет доступа")):
                status, _, body = self.http("/api/image-report", "POST", payload)
                self.assertEqual(status, 500)
            self.assertFalse(list((self.root / folder).glob("*report*")))
            self.assertFalse(list((self.root / folder).glob(".report-*")))
            status, _, body = self.http("/api/image-report", "POST", payload)
            self.assertEqual(status, 201)
            self.assertTrue((self.root / json.loads(body)["path"]).exists())
            status, _, body = self.http("/api/image-report", "POST", json.dumps({"path": folder, "files": []}))
            self.assertEqual(status, 400)
