import http.client
import importlib.util
import json
import os
import plistlib
import sys
import tempfile
import threading
import unittest
import urllib.parse
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("manager_server", Path(__file__).resolve().parents[1] / "server.py")
manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manager)


class ManagerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name).resolve()
        self.root = self.base / "Зигзаг"
        self.root.mkdir()
        self.patches = [
            patch.object(manager, "DATA_ROOT", self.root),
            patch.object(manager, "DATA_DIR", self.base / "local"),
            patch.object(manager, "STATUSES_FILE", self.base / "local" / "statuses.json"),
        ]
        for item in self.patches:
            item.start()
        self.folder("Клиент/2026/Заказ/# счета")
        self.folder("Клиент/Без года/Фото")
        self.folder("# docs/Внутри")
        self.folder(".скрыто")
        self.file("Клиент/2026/Заказ/# счета/Счёт.pdf", b"%PDF-1.4 test")
        self.file("Клиент/Без года/Фото/файл%2F #.txt", b"0123456789")
        self.file("Клиент/Без года/.секрет", b"secret")
        self.file("# docs/Внутри/readme.txt", b"common")
        self.server = None

    def tearDown(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        for item in reversed(self.patches):
            item.stop()
        self.temporary.cleanup()

    def folder(self, name):
        (self.root / name).mkdir(parents=True, exist_ok=True)

    def file(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def http(self, route, method="GET", body=None, headers=None):
        if self.server is None:
            self.server = manager.ThreadingHTTPServer(("127.0.0.1", 0), manager.ManagerHandler)
            threading.Thread(target=self.server.serve_forever, daemon=True).start()
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port)
        connection.request(method, route, body=body, headers=headers or {})
        response = connection.getresponse()
        result = response.status, dict(response.getheaders()), response.read()
        connection.close()
        return result

    def url(self, route, path, **extra):
        return route + "?" + urllib.parse.urlencode({"path": path, **extra})

    def test_root_hash_folders_are_buttons_not_clients(self):
        tree = manager.read_tree()
        self.assertEqual([node["name"] for node in tree["children"]], ["Клиент"])
        self.assertEqual([node["name"] for node in tree["auxiliary"]], ["# docs"])
        self.assertEqual(manager.read_tree("Клиент/2026/Заказ")["children"][0]["name"], "# счета")

    def test_mixed_years_and_arbitrary_depth_follow_disk(self):
        nodes = manager.read_tree("Клиент")["children"]
        self.assertEqual({node["name"] for node in nodes}, {"2026", "Без года"})
        folder = manager.read_folder("Клиент")
        self.assertEqual(folder["fileCount"], 2)
        self.assertEqual(folder["folderCount"], 5)
        self.assertEqual({file["folder"] for file in folder["files"]}, {"2026/Заказ/# счета", "Без года/Фото"})

    def test_root_home_does_not_scan_all_orders(self):
        self.assertEqual(manager.read_folder()["fileCount"], 0)
        self.assertEqual(manager.read_folder("# docs")["fileCount"], 1)

    def test_search_finds_unloaded_folders_and_normalizes_unicode(self):
        self.folder("Клиент/переклейка")
        result = manager.read_tree(query="переклейка")
        self.assertEqual(result["children"][0]["children"][0]["name"], "переклейка")
        self.assertEqual(manager.read_tree(query="docs")["children"], [])

    def test_path_escape_hidden_files_and_external_symlinks_are_blocked(self):
        outside = self.base / "outside.txt"
        outside.write_text("private")
        (self.root / "Клиент" / "outside.txt").symlink_to(outside)
        for path in ("../outside.txt", str(outside), ".скрыто", "Клиент/outside.txt"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                manager.safe_path(path)
        self.assertEqual(manager.read_folder("Клиент")["fileCount"], 2)

    def test_config_accepts_relative_paths_and_literal_hash_percent(self):
        config = self.base / "manager.ini"
        config.write_text("[storage]\nroot = папка # 100%\n[server]\nhost = 127.0.0.1\nport = 9876\n")
        with patch.dict(os.environ, {"ZIGZAG_DATA_ROOT": "", "MANAGER_HOST": ""}):
            root, host, port = manager.read_config(config)
        self.assertEqual(root, self.base / "папка # 100%")
        self.assertEqual((host, port), ("127.0.0.1", 9876))

    def test_notes_migrate_legacy_year_keys_into_folder_and_archive_original(self):
        manager.DATA_DIR.mkdir()
        old = {"2025/Клиент/Без года": {"status": "done", "note": "Старая заметка"}}
        manager.STATUSES_FILE.write_text(json.dumps(old))
        result = manager.migrate_statuses()
        self.assertEqual(result["migrated"], 1)
        self.assertEqual(json.loads(Path(result["archive"]).read_text()), old)
        self.assertFalse(manager.STATUSES_FILE.exists())
        self.assertEqual(manager.read_folder("Клиент/Без года")["note"], "Старая заметка")
        manager.save_status("Клиент/Без года", "process", "Новая заметка")
        self.assertEqual(json.loads(Path(result["archive"]).read_text()), old)
        self.assertEqual(manager.read_folder("Клиент/Без года")["note"], "Новая заметка")
        self.assertIsNone(manager.migrate_statuses())

    def test_status_and_multiline_note_are_readable_portable_and_editable_without_app(self):
        relative = "Клиент/Без года"
        note = "Позвонить клиенту\n\nРазмеры: 3×2 м\nЗаметка:\nДополнение\n"
        manager.save_status(relative, "process", note)
        document = self.root / relative / manager.STATUS_DOCUMENT_NAME
        self.assertEqual(document.read_text(), "Статус: В работе\n\nЗаметка:\n" + note)
        self.assertFalse(manager.DATA_DIR.exists())
        self.assertEqual(manager.read_folder(relative)["note"], note)
        document.write_text("Статус: Готово\n\nЗаметка:\nИзменено в текстовом редакторе", encoding="utf-8")
        folder = manager.read_folder(relative)
        self.assertEqual((folder["status"], folder["note"], folder["statusSource"]), ("done", "Изменено в текстовом редакторе", "manual"))
        copied_root = self.base / "Скопированные документы"
        import shutil
        shutil.copytree(self.root, copied_root)
        with patch.object(manager, "DATA_ROOT", copied_root):
            self.assertEqual(manager.read_folder(relative)["note"], folder["note"])

    def test_status_migration_preserves_local_edits_and_unresolved_records(self):
        manager.save_status("Клиент", "process", "Правка в папке")
        manager.DATA_DIR.mkdir()
        old = {"Клиент": {"status": "new", "note": "Прежняя правка"}, "Пропавшая папка": {"status": "done", "note": "Не потерять"}}
        manager.STATUSES_FILE.write_text(json.dumps(old))
        archive = self.root / ".legacy-statuses.json"
        archive.write_text("Предыдущий архив")
        result = manager.migrate_statuses()
        self.assertEqual(result["migrated"], 0)
        self.assertEqual(result["unresolved"], ["Пропавшая папка"])
        self.assertEqual(manager.read_folder("Клиент")["note"], "Правка в папке")
        self.assertEqual(archive.read_text(), "Предыдущий архив")
        self.assertEqual(json.loads(Path(result["archive"]).read_text()), old)

    def test_ambiguous_legacy_year_records_are_archived_without_guessing(self):
        manager.DATA_DIR.mkdir()
        old = {"2024/Клиент": {"status": "done", "note": "Первый год"}, "2025/Клиент": {"status": "new", "note": "Второй год"}}
        manager.STATUSES_FILE.write_text(json.dumps(old))
        result = manager.migrate_statuses()
        self.assertEqual(result["migrated"], 0)
        self.assertCountEqual(result["unresolved"], old.keys())
        self.assertFalse((self.root / "Клиент" / manager.STATUS_DOCUMENT_NAME).exists())
        self.assertEqual(json.loads(Path(result["archive"]).read_text()), old)

    def test_status_save_rejects_symlinks_and_does_not_create_files_on_read(self):
        relative = "Клиент/Без года"
        manager.read_folder(relative)
        document = self.root / relative / manager.STATUS_DOCUMENT_NAME
        self.assertFalse(document.exists())
        outside = self.base / "outside-status.txt"
        outside.write_text("Не изменять")
        document.symlink_to(outside)
        with self.assertRaises(ValueError):
            manager.save_status(relative, "done", "test")
        self.assertEqual(outside.read_text(), "Не изменять")
        (self.root / "alias").symlink_to(self.root / "Клиент")
        with self.assertRaises(ValueError):
            manager.save_status("alias", "done", "test")

    def test_http_literal_percent_hash_unicode_and_byte_ranges(self):
        path = "Клиент/Без года/Фото/файл%2F #.txt"
        route = self.url("/api/file", path)
        status, headers, body = self.http(route, headers={"Range": "bytes=2-5"})
        self.assertEqual((status, body), (206, b"2345"))
        self.assertEqual(headers["Content-Range"], "bytes 2-5/10")
        status, headers, body = self.http(route, method="HEAD")
        self.assertEqual((status, body, headers["Content-Length"]), (200, b"", "10"))
        status, headers, body = self.http(route, headers={"Range": "bytes=-3"})
        self.assertEqual((status, body), (206, b"789"))
        status, headers, body = self.http(route, headers={"Range": "bytes=100-200"})
        self.assertEqual(status, 416)

    def test_http_errors_and_native_open_use_exact_path(self):
        status, _, _ = self.http(self.url("/api/file", "../outside.txt"))
        self.assertEqual(status, 400)
        status, _, _ = self.http(self.url("/api/folder", "missing"))
        self.assertEqual(status, 404)
        path = "Клиент/Без года/Фото/файл%2F #.txt"
        with patch.object(manager.subprocess, "Popen") as open_mock:
            status, _, body = self.http("/api/open", "POST", json.dumps({"path": path, "reveal": True}))
            self.assertEqual(status, 200)
            self.assertTrue(json.loads(body)["ok"])
            open_mock.assert_called_once_with(["open", "-R", str(self.root / path)])

    def test_active_documents_download_and_text_is_json(self):
        self.file("Клиент/page.html", b"<script>alert(1)</script>")
        status, headers, _ = self.http(self.url("/api/file", "Клиент/page.html"))
        self.assertEqual(status, 200)
        self.assertTrue(headers["Content-Disposition"].startswith("attachment"))
        status, headers, body = self.http(self.url("/api/text", "Клиент/Без года/Фото/файл%2F #.txt"))
        self.assertEqual(json.loads(body)["text"], "0123456789")

    def print_folder(self, work="# work", printing="# print"):
        relative = work + "/" + printing
        self.folder(relative)
        return relative

    def test_print_view_accepts_hash_names_with_or_without_spaces(self):
        for work, printing in (("#work", "#print"), ("# work", "#print"), ("#work", "# print"), ("# work", "#  print")):
            with self.subTest(work=work, printing=printing):
                relative = self.print_folder(work, printing)
                self.file(relative + "/задание.txt", b"task")
                self.file(relative + "/не текст.png", b"not text")
                folder = manager.read_folder(relative)
                self.assertEqual(folder["view"], "print")
                self.assertEqual([file["name"] for file in folder["files"]], ["задание.txt"])
        self.assertEqual(manager.read_folder("Клиент")["view"], "files")

    def test_print_clipping_reads_rtf_and_keeps_original_on_unchanged_save(self):
        folder = self.print_folder()
        path = folder + "/print - 2000-01-01.textClipping"
        original = plistlib.dumps({"UTI-Data": {"public.rtf": manager.text_to_rtf("Баннер 3×2 м\nТираж 2 шт.")}, "fixture": True}, fmt=plistlib.FMT_BINARY)
        self.file(path, original)
        task = manager.read_print_task(path)
        self.assertEqual(task["link"], "")
        self.assertIn("Баннер 3×2 м", task["description"])
        manager.save_print_task(path, task["link"], task["description"], task["revision"])
        self.assertEqual((self.root / path).read_bytes(), original)

    def test_legacy_print_link_after_heading_is_separate_without_rewriting(self):
        folder = self.print_folder()
        path = folder + "/print - 2000-01-01.textClipping"
        text = "В печать\n\nhttps://example.com/files\n\nБаннер 3×2 м\n"
        original = plistlib.dumps({"UTI-Data": {"public.utf8-plain-text": text}}, fmt=plistlib.FMT_BINARY)
        self.file(path, original)
        task = manager.read_print_task(path)
        self.assertEqual(task["link"], "https://example.com/files")
        self.assertEqual(task["title"], "В печать")
        self.assertEqual(task["description"], "Баннер 3×2 м\n")
        manager.save_print_task(path, task["link"], task["description"], task["revision"], task["title"])
        self.assertEqual((self.root / path).read_bytes(), original)

    def test_print_save_stores_link_first_and_backs_up_original_clipping(self):
        folder = self.print_folder()
        path = folder + "/print - 2000-01-01.textClipping"
        original = plistlib.dumps({"UTI-Data": {"public.rtf": manager.text_to_rtf("Старое задание")}}, fmt=plistlib.FMT_BINARY)
        self.file(path, original)
        before = manager.read_print_task(path)
        title, link, description = "Баннеры для клиента", "https://example.com/banner", "Баннер 3×2 м\n2 шт. 🙂 {проверить}"
        after = manager.save_print_task(path, link, description, before["revision"], title)
        expected = link + "\n\nНазвание: " + title + "\n\n" + description
        representations = plistlib.loads((self.root / path).read_bytes())["UTI-Data"]
        self.assertEqual(representations["public.utf8-plain-text"], expected)
        self.assertEqual(manager.text_from_rtf(representations["public.rtf"]).rstrip("\n"), expected)
        self.assertEqual((after["title"], after["link"], after["description"]), (title, link, description))
        self.assertNotEqual(before["revision"], after["revision"])
        backup = next(path for path in (self.root / folder / manager.PRINT_HISTORY_DIR).rglob("*.textClipping") if path.is_file())
        self.assertEqual(backup.read_bytes(), original)
        self.assertFalse(manager.DATA_DIR.exists())
        self.assertEqual(manager.read_folder(folder)["fileCount"], 1)
        self.assertEqual(manager.read_tree(folder)["children"], [])

    def test_new_print_tasks_follow_sample_and_do_not_overwrite_today(self):
        folder = self.print_folder()
        self.file(folder + "/print - 2000-01-01.textClipping", plistlib.dumps({"UTI-Data": {"public.utf8-plain-text": "Образец"}}, fmt=plistlib.FMT_BINARY))
        expected = manager.next_print_name(self.root / folder)
        first = manager.create_print_task(folder, "https://example.com/files", "Первый баннер")
        second = manager.create_print_task(folder, "", "Второй баннер")
        self.assertEqual(first["name"], expected)
        self.assertEqual(second["name"], expected.replace(".textClipping", " (2).textClipping"))
        self.assertRegex(first["name"], r"^print - \d{4}-\d{2}-\d{2}\.textClipping$")
        self.assertEqual(manager.read_print_task(first["path"])["description"], "Первый баннер")

    def test_print_http_conflict_keeps_external_edits(self):
        folder = self.print_folder()
        task = manager.create_print_task(folder, "", "Исходное задание")
        external = plistlib.dumps({"UTI-Data": {"public.utf8-plain-text": "Изменено в другой программе"}}, fmt=plistlib.FMT_BINARY)
        (self.root / task["path"]).write_bytes(external)
        status, _, body = self.http("/api/print-save", "POST", json.dumps({"path": task["path"], "revision": task["revision"], "link": "", "description": "Устаревшая правка"}))
        self.assertEqual(status, 409)
        self.assertIn("другой программе", json.loads(body)["error"])
        self.assertEqual((self.root / task["path"]).read_bytes(), external)

    def test_print_writes_are_restricted_and_link_is_validated(self):
        folder = self.print_folder()
        for path in ("Клиент", "# docs", "../outside", folder + "/missing"):
            with self.subTest(path=path), self.assertRaises((ValueError, FileNotFoundError)):
                manager.create_print_task(path, "", "test")
        with self.assertRaises(ValueError):
            manager.create_print_task(folder, "javascript:alert(1)", "test")
        (self.root / folder / "alias").symlink_to(self.root / "Клиент")
        with self.assertRaises(ValueError):
            manager.create_print_task(folder + "/alias", "", "test")

    def test_plain_text_print_files_keep_unicode_encoding_and_api_fields(self):
        folder = self.print_folder("#work", "#print")
        path = folder + "/print - 2000-01-01.txt"
        self.file(path, "https://example.com/files\n\nПлакат 60×90 см".encode("utf-16"))
        status, _, body = self.http(self.url("/api/print-task", path))
        task = json.loads(body)
        self.assertEqual(status, 200)
        self.assertEqual(task["link"], "https://example.com/files")
        self.assertEqual(task["title"], "")
        self.assertEqual(task["description"], "Плакат 60×90 см")
        manager.save_print_task(path, task["link"], "Плакат 60×90 см, 3 шт.", task["revision"])
        self.assertEqual((self.root / path).read_text(encoding="utf-16"), "https://example.com/files\n\nНазвание: \n\nПлакат 60×90 см, 3 шт.")

    def test_print_title_round_trip_keeps_description_urls_and_blank_lines(self):
        folder = self.print_folder()
        description = "\nНазвание: это часть описания\n\nhttps://example.com/extra\n\n"
        for link in ("", "https://example.com/files"):
            for title in ("", "Плакаты 🙂"):
                with self.subTest(link=link, title=title):
                    task = manager.create_print_task(folder, link, description, title)
                    self.assertEqual((task["title"], task["link"], task["description"]), (title, link, description))
                    cleared = manager.save_print_task(task["path"], link, description, task["revision"], "")
                    self.assertEqual(cleared["title"], "")
                    self.assertEqual(cleared["description"], description)

    def test_print_title_http_create_and_edit_preserves_filename(self):
        folder = self.print_folder()
        status, _, body = self.http("/api/print-create", "POST", json.dumps({"path": folder, "title": "Плакаты", "link": "", "description": "2 шт."}))
        self.assertEqual(status, 201)
        task = json.loads(body)
        self.assertEqual(task["title"], "Плакаты")
        status, _, body = self.http("/api/print-save", "POST", json.dumps({**task, "title": "Новые плакаты"}))
        self.assertEqual(status, 200)
        saved = json.loads(body)
        self.assertEqual(saved["title"], "Новые плакаты")
        self.assertEqual(saved["name"], task["name"])
        self.assertEqual(saved["description"], "2 шт.")
        with self.assertRaises(ValueError):
            manager.create_print_task(folder, "", "описание", "Название\nвторая строка")

    @unittest.skipUnless(sys.platform == "darwin", "PDFKit requires macOS")
    def test_pdf_pages_render_without_browser_pdf_plugin(self):
        # A real two-page PDF, with different page sizes and content.
        drawing = b"0 0 1 rg 20 20 40 40 re f"
        objects = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R 4 0 R] /Count 2 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 200] /Resources << >> /Contents 5 0 R >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 100] /Resources << >> /Contents 5 0 R >>",
            b"<< /Length " + str(len(drawing)).encode() + b" >>\nstream\n" + drawing + b"\nendstream",
        ]
        content = b"%PDF-1.4\n"
        offsets = [0]
        for index, obj in enumerate(objects, 1):
            offsets.append(len(content))
            content += str(index).encode() + b" 0 obj\n" + obj + b"\nendobj\n"
        xref = len(content)
        content += b"xref\n0 6\n0000000000 65535 f \n"
        content += b"".join(f"{offset:010} 00000 n \n".encode() for offset in offsets[1:])
        content += b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n" + str(xref).encode() + b"\n%%EOF\n"
        self.file("Клиент/две страницы.pdf", content)
        binary = manager.APP_DIR / "data" / "pdf-renderer"
        binary = binary if binary.exists() else manager.pdf_renderer()
        with patch.object(manager, "pdf_renderer", return_value=binary):
            status, _, body = self.http(self.url("/api/pdf", "Клиент/две страницы.pdf"))
            self.assertEqual((status, json.loads(body)["pages"]), (200, 2))
            for page in (0, 1):
                status, headers, body = self.http(self.url("/api/pdf-page", "Клиент/две страницы.pdf", page=page))
                self.assertEqual(status, 200)
                self.assertEqual(headers["Content-Type"], "image/jpeg")
                self.assertTrue(body.startswith(b"\xff\xd8"))
                self.assertGreater(len(body), 1000)
            status, _, _ = self.http(self.url("/api/pdf-page", "Клиент/две страницы.pdf", page=2))
            self.assertEqual(status, 400)


if __name__ == "__main__":
    unittest.main()
