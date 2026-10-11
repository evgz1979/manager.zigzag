import http.client
import importlib.util
import json
import os
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

    def test_notes_keep_existing_records_and_read_legacy_year_keys(self):
        manager.DATA_DIR.mkdir()
        old = {"2025/Клиент/Без года": {"status": "done", "note": "Старая заметка"}}
        manager.STATUSES_FILE.write_text(json.dumps(old))
        self.assertEqual(manager.read_folder("Клиент/Без года")["note"], "Старая заметка")
        manager.save_status("Клиент/Без года", "process", "Новая заметка")
        records = json.loads(manager.STATUSES_FILE.read_text())
        self.assertEqual(records["2025/Клиент/Без года"], old["2025/Клиент/Без года"])
        self.assertEqual(manager.read_folder("Клиент/Без года")["note"], "Новая заметка")

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
