"""Verify monthly cash-flow arithmetic in the browser's JavaScript implementation."""
from pathlib import Path
import shutil
import subprocess
import unittest


class MoneyOverviewTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node.js is required for JavaScript checks')
    def test_monthly_cash_flow(self):
        subprocess.run(['node', str(Path(__file__).with_name('money-overview.cjs'))], check=True, capture_output=True, text=True)
