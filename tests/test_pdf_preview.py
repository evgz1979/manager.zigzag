import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import native_renderers
import test_server as fixtures

manager = fixtures.manager


def sample_pdf():
    stream = b"BT /F1 22 Tf 40 200 Td (PDF preview test) Tj ET"
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>",
               b"<< /Type /Pages /Kids [3 0 R 4 0 R] /Count 2 >>",
               b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 400] /Resources << /Font << /F1 5 0 R >> >> /Contents 6 0 R >>",
               b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 400 300] /Resources << /Font << /F1 5 0 R >> >> /Contents 6 0 R >>",
               b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
               b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream"]
    result = b"%PDF-1.4\n"
    offsets = [0]
    for index, body in enumerate(objects, 1):
        offsets.append(len(result))
        result += f"{index} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(result)
    result += f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode()
    result += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:])
    return result + f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()


class PdfPreviewTests(unittest.TestCase):
    setUp = fixtures.ManagerTests.setUp
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file

    def test_failed_info_hides_coregraphics_diagnostics_and_can_retry(self):
        target = self.root / "test.pdf"
        target.write_bytes(sample_pdf())
        noise = b'CoreGraphics PDF has logged an error. Set environment variable "CG_PDF_VERBOSE" to learn more.\n'
        failure = subprocess.CalledProcessError(1, "pdf", stderr=noise + "ZIGZAG_PDF_ERROR: Не удалось получить PDF из папки.\n".encode())
        with patch.object(manager, "pdf_renderer", return_value=Path("/renderer")), \
                patch.object(manager.subprocess, "run", side_effect=[failure, subprocess.CompletedProcess([], 0, b'{"pages":2}')]):
            with self.assertRaisesRegex(ValueError, "^Не удалось получить PDF из папки.$"):
                manager.pdf_info(target)
            self.assertEqual(manager.pdf_info(target), {"pages": 2})
        self.assertEqual(manager.pdf_error(noise, "Не удалось прочитать PDF"), "Не удалось прочитать PDF")

    def test_failed_page_removes_partial_preview_and_next_attempt_succeeds(self):
        target = self.root / "test.pdf"
        original = sample_pdf()
        target.write_bytes(original)
        count = 0

        def render(command, **kwargs):
            nonlocal count
            output = Path(command[-1])
            count += 1
            output.write_bytes(b"partial" if count == 1 else b"\xff\xd8\xffimage")
            if count == 1:
                raise subprocess.CalledProcessError(1, command, stderr="ZIGZAG_PDF_ERROR: PDF временно недоступен\n".encode())

        with patch.object(manager, "pdf_info", return_value={"pages": 2}), \
                patch.object(manager, "pdf_renderer", return_value=Path("/renderer")), \
                patch.object(manager.subprocess, "run", side_effect=render):
            with self.assertRaisesRegex(ValueError, "^PDF временно недоступен$"):
                manager.pdf_page(target, 0)
            self.assertEqual(list((manager.DATA_DIR / "previews").iterdir()), [])
            self.assertTrue(manager.pdf_page(target, 0).read_bytes().startswith(b"\xff\xd8\xff"))
            with self.assertRaises(ValueError):
                manager.pdf_page(target, 2)
        self.assertEqual(target.read_bytes(), original)

    @unittest.skipUnless(sys.platform == "darwin", "PDFKit requires macOS")
    def test_native_reads_bytes_renders_both_pages_and_preserves_original(self):
        source = Path(__file__).resolve().parents[1] / "pdf_preview.swift"
        binary = native_renderers.build(source, manager.DATA_DIR, "pdf-test", 60)
        target = self.root / "Проверка PDF.pdf"
        original = sample_pdf()
        target.write_bytes(original)
        before = target.stat().st_mtime_ns

        def run(*arguments):
            return subprocess.run([str(binary), *map(str, arguments)], capture_output=True, timeout=20)

        info = run(target, "info")
        self.assertEqual(info.returncode, 0, info.stderr)
        self.assertEqual(json.loads(info.stdout), {"pages": 2})
        for page in range(2):
            output = self.base / f"page-{page}.jpg"
            result = run(target, page, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(output.read_bytes().startswith(b"\xff\xd8\xff"))
            self.assertGreater(output.stat().st_size, 1000)
        self.assertEqual(hashlib.sha256(target.read_bytes()).digest(), hashlib.sha256(original).digest())
        self.assertEqual(target.stat().st_mtime_ns, before)
        alias = self.root / "alias.pdf"
        alias.symlink_to(target)
        self.assertNotEqual(run(alias, "info").returncode, 0)
        invalid = self.root / "invalid.pdf"
        invalid.write_bytes(b"not a PDF")
        failed = run(invalid, "info")
        self.assertNotEqual(failed.returncode, 0)
        self.assertIn("ZIGZAG_PDF_ERROR: Не удалось прочитать PDF".encode(), failed.stderr)
