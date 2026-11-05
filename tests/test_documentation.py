"""End-to-end checks that source movement does not rewrite the reference."""
from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('build_documentation', APP / 'scripts/build_documentation.py')
documentation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(documentation)
NODE = shutil.which('node')
BABEL = os.environ.get('MANAGER_DOCUMENTATION_BABEL')
if NODE and not BABEL:
    result = subprocess.run([NODE, '-p', "require('path').join(require('path').dirname(require.resolve('playwright/package.json')), 'lib/transform/babelBundle.js')"], capture_output=True, text=True)
    if result.returncode == 0:
        BABEL = result.stdout.strip()


@unittest.skipUnless(NODE and BABEL, 'Node and Playwright Babel are required for documentation checks')
class DocumentationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.reference = self.root / 'docs/reference'
        for name in ('scripts', 'static', 'mobile', 'docs/language'):
            (self.root / name).mkdir(parents=True)
        for name in ('README.md', 'mobile/README.md', 'docs/architecture.md', 'docs/flows.md', 'docs/legacy-code.md', 'docs/language/README.md', 'docs/language/sqlite.md', 'docs/language/swift-c.md'):
            (self.root / name).write_text('')
        shutil.copyfile(APP / 'scripts/documentation_js.cjs', self.root / 'scripts/documentation_js.cjs')
        (self.root / 'sample.py').write_text('# Calculates a charge.\n# Returns the input plus one.\ndef charge(amount):\n    return amount + 1\n\n# Creates the test table.\n# Returns a DDL string without opening SQLite.\ndef schema():\n    return "CREATE TABLE sample (id TEXT)"\n')
        (self.root / 'server.py').write_text('# Serves test routes.\n# Never runs a server.\nclass Handler:\n    # Dispatches test requests.\n    # Returns one field without network calls.\n    def do_POST(self, route, payload):\n        if route == "/api/sample":\n            return payload.get("amount")\n')
        (self.root / 'remote_access.py').write_text('# Parses a login route.\n# Returns a constant without authentication side effects.\ndef get_remote(path):\n    if path == "/_auth/login":\n        return True\n')
        (self.root / 'static/sample.js').write_text('// Scopes a local action.\n// Returns its result.\nfunction outer() {\n  // Computes one value.\n  // Returns the input unchanged.\n  const moved = value => value;\n  return moved(1);\n}\n')
        (self.root / 'sample.swift').write_text('// Holds a native fixture.\n// Only declares methods.\nstruct Sample {\n    // Accepts an integer.\n    // Returns the input.\n    func value(_ input: Int) -> Int { input }\n    // Accepts text.\n    // Returns the input.\n    func value(_ input: String) -> String { input }\n}\n')
        (self.root / 'scripts/manager_launcher.c').write_text('// Declares the fixture entry point.\n// Returns success.\nint main(void) { return 0; }\n')
        (self.root / 'embedded.py').write_text('TEMPLATE = """\n// Computes a browser value.\n// Returns one.\nfunction embedded() { return 1; }\n"""\n')
        for item in (patch.object(documentation, 'ROOT', self.root), patch.object(documentation, 'REFERENCE', self.reference)):
            item.start()
            self.addCleanup(item.stop)
        self.assertEqual(self.build()[0], 0)

    def build(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(sys, 'argv', ['build_documentation.py', '--node', NODE, '--babel', BABEL, *args]), redirect_stdout(stdout), redirect_stderr(stderr):
            result = documentation.main()
        return result, stdout.getvalue(), stderr.getvalue()

    def snapshot(self):
        return {p.relative_to(self.reference).as_posix(): p.read_bytes() for p in self.reference.rglob('*') if p.is_file()}

    def test_line_shifts_leave_all_references_identical_and_locator_uses_current_line(self):
        before = self.snapshot()
        for name in ('sample.py', 'server.py', 'remote_access.py', 'embedded.py', 'static/sample.js', 'sample.swift', 'scripts/manager_launcher.c'):
            path = self.root / name
            comment = '#' if path.suffix == '.py' else '//'
            path.write_text('\n' + comment + ' An ordinary comment.\n\n' + path.read_text())
        self.assertEqual(self.build('--check')[0], 0)
        self.assertEqual(self.build()[0], 0)
        self.assertEqual(self.snapshot(), before)
        result, output, _ = self.build('--locate', 'sample.py::charge')
        self.assertEqual(result, 0)
        self.assertIn('sample.py:6 def charge(amount)', output)
        self.assertEqual(self.snapshot(), before)

    def test_small_body_change_updates_only_its_module_reference(self):
        before = self.snapshot()
        path = self.root / 'sample.py'
        path.write_text(path.read_text().replace('return amount + 1', 'return amount + 2'))
        result, _, error = self.build('--check')
        self.assertEqual(result, 1)
        self.assertIn('Stale reference', error)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.build()[0], 0)
        after = self.snapshot()
        self.assertEqual([p for p in before if before[p] != after[p]], ['python/sample.md'])

    def test_removed_symbol_missing_anchor_and_missing_comments_are_reported(self):
        (self.root / 'docs/flows.md').write_text('[charge](reference/python/sample.md#symbol-charge)\n')
        path = self.root / 'sample.py'
        original = path.read_text()
        path.write_text(original.replace('def charge(', 'def renamed('))
        self.assertIn('missing symbol', self.build('--check')[2])
        path.write_text(original.replace('# Returns the input plus one.\n', ''))
        self.assertIn('expected two description lines', self.build('--check')[2])
        path.write_text(original)
        page = self.reference / 'python/sample.md'
        page.write_text(page.read_text().replace('<a id="symbol-charge"></a>', ''))
        self.assertIn('missing symbol', self.build('--check')[2])

    def test_inventory_contains_stable_names_and_unique_overload_anchors(self):
        inventory = json.loads((self.reference / 'inventory.json').read_text())
        self.assertEqual(inventory['version'], 2)
        for files in inventory['groups'].values():
            for file in files:
                self.assertNotIn('sha256', file)
                self.assertTrue(all(set(symbol) == {'name', 'type', 'anchor'} for symbol in file['symbols']))
                self.assertEqual(len({s['anchor'] for s in file['symbols']}), len(file['symbols']))
        js = next(f for f in inventory['groups']['javascript'] if f['path'] == 'static/sample.js')
        self.assertIn('outer.moved', [s['name'] for s in js['symbols']])
        native = next(f for f in inventory['groups']['native'] if f['path'] == 'sample.swift')
        self.assertEqual(len([s for s in native['symbols'] if s['name'] == 'Sample.value']), 2)


if __name__ == '__main__':
    unittest.main()
