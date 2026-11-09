"""Guard HTTP product forms, independent copies, deletion and Russian name sorting."""
from pathlib import Path
import shutil
import subprocess
import unittest


class InvoiceProductBrowserTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node.js is required for JavaScript checks')
    def test_product_forms_without_secure_context(self):
        subprocess.run(['node', str(Path(__file__).with_name('invoice-products.cjs'))],
                       check=True, capture_output=True, text=True)
