import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import native_renderers


class NativeRendererTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.data = self.root / "data"
        self.data.mkdir()

    def tearDown(self):
        self.temporary.cleanup()

    def release(self, name, content):
        folder = self.root / name
        folder.mkdir()
        (folder / "data").symlink_to(self.data)
        source = folder / "preview.swift"
        source.write_text(content)
        os.utime(source, (0, 0))
        return source

    def compile(self, command, **kwargs):
        Path(command[-1]).write_bytes(b"compiled")

    def test_two_releases_share_canonical_cache_and_reuse_same_source_binary(self):
        first = self.release("release1", "print(1)")
        second = self.release("release2", "print(1)")
        with patch.object(native_renderers.subprocess, "run", side_effect=self.compile) as compile:
            binary1 = native_renderers.build(first, first.parent / "data", "pdf", 60)
            binary2 = native_renderers.build(second, second.parent / "data", "pdf", 60)
        self.assertEqual(binary1, binary2)
        self.assertEqual(compile.call_count, 1)
        command = compile.call_args[0][0]
        self.assertEqual(command[command.index("-module-cache-path") + 1], str(self.data / "swift-cache-v2"))

    def test_source_change_with_same_timestamp_builds_separately_and_keeps_old_binary(self):
        first = self.release("release1", "print(1)")
        second = self.release("release2", "print(2)")
        with patch.object(native_renderers.subprocess, "run", side_effect=self.compile) as compile:
            binary1 = native_renderers.build(first, first.parent / "data", "pdf", 60)
            binary2 = native_renderers.build(second, second.parent / "data", "pdf", 60)
        self.assertNotEqual(binary1, binary2)
        self.assertEqual(compile.call_count, 2)
        self.assertEqual(binary1.read_bytes(), b"compiled")

    def test_failed_build_publishes_no_partial_binary_and_can_retry(self):
        source = self.release("release1", "print(1)")
        def failed(command, **kwargs):
            Path(command[-1]).write_bytes(b"partial")
            raise subprocess.CalledProcessError(1, command, stderr=b"compiler failed")
        with patch.object(native_renderers.subprocess, "run", side_effect=failed):
            with self.assertRaises(subprocess.CalledProcessError):
                native_renderers.build(source, source.parent / "data", "pdf", 60)
        self.assertEqual(list((self.data / "native-renderers").iterdir()), [])
        with patch.object(native_renderers.subprocess, "run", side_effect=self.compile):
            self.assertTrue(native_renderers.build(source, source.parent / "data", "pdf", 60).is_file())


if __name__ == "__main__":
    unittest.main()
