import http.client
import json
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.parse
from pathlib import Path
from unittest.mock import patch

import server
import spreadsheet_preview as preview


class SpreadsheetPreviewTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.target = self.root / "Счёт №1.XLS"
        self.raw = b"\xd0\xcf\x11\xe0Excel original bytes"
        self.target.write_bytes(self.raw)

    def test_original_read_is_bounded_and_does_not_change_file(self):
        before = self.target.stat()
        with patch.object(preview.sys, "platform", "linux"):
            self.assertEqual(preview.read_bytes(self.target), self.raw)
        self.assertEqual(self.target.read_bytes(), self.raw)
        self.assertEqual(self.target.stat().st_mtime_ns, before.st_mtime_ns)
        with patch.object(preview, "MAX_BYTES", 5):
            with self.assertRaisesRegex(ValueError, "20 МБ"):
                preview.read_bytes(self.target)
        for name in ("test.txt", "test.xlsx"):
            target = self.root / name
            target.symlink_to(self.target)
            with self.assertRaises(ValueError):
                preview.read_bytes(target)

    def test_icloud_uses_coordinated_reader_and_timeout_can_be_retried(self):
        with patch.object(preview.sys, "platform", "darwin"), \
                patch.object(preview.icloud_access, "renderer", return_value=Path("/reader")), \
                patch.object(preview.subprocess, "run") as run:
            run.side_effect = subprocess.TimeoutExpired("reader", 25)
            with self.assertRaisesRegex(ValueError, "iCloud"):
                preview.read_bytes(self.target)
            run.side_effect = None
            run.return_value.stdout = self.raw
            self.assertEqual(preview.read_bytes(self.target), self.raw)
            self.assertEqual(run.call_args.args[0], ["/reader", str(self.target), str(preview.MAX_BYTES)])
            self.assertEqual(run.call_args.kwargs["timeout"], 25)
        self.assertEqual(self.target.read_bytes(), self.raw)

    @unittest.skipUnless(sys.platform == "darwin", "Foundation requires macOS")
    def test_native_reader_accepts_spreadsheet_limit_above_metadata_limit(self):
        raw = self.raw * 60000
        self.assertGreater(len(raw), 1024 * 1024)
        self.target.write_bytes(raw)
        self.assertEqual(preview.read_bytes(self.target), raw)
        self.assertEqual(self.target.read_bytes(), raw)

    def test_http_serves_only_supported_files_inside_root(self):
        httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), server.ManagerHandler)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(httpd.server_close)
        self.addCleanup(httpd.shutdown)
        with patch.object(server, "DATA_ROOT", self.root), patch.object(preview.sys, "platform", "linux"):
            def get(path):
                connection = http.client.HTTPConnection("127.0.0.1", httpd.server_port)
                connection.request("GET", "/api/spreadsheet?" + urllib.parse.urlencode({"path": path}))
                response = connection.getresponse()
                result = response.status, dict(response.getheaders()), response.read()
                connection.close()
                return result

            status, headers, raw = get(self.target.name)
            self.assertEqual((status, raw), (200, self.raw))
            self.assertEqual(headers["Cache-Control"], "no-store")
            self.assertEqual(headers["Content-Type"], "application/octet-stream")
            (self.root / "test.txt").write_bytes(b"not excel")
            self.assertEqual(get("test.txt")[0], 400)
            self.assertEqual(get("../outside.xls")[0], 400)
            status, _, error = get("missing.xlsx")
            self.assertEqual(status, 404)
            self.assertIn("error", json.loads(error))
        for extension in ("xls", "XLSX", "xlsm", "xlsb"):
            self.assertEqual(server.preview_kind(Path("table." + extension)), "spreadsheet")


if __name__ == "__main__":
    unittest.main()
