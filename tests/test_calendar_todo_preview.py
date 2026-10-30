"""Mouse transition and keyboard regression checks for the calendar To-do popup."""
from pathlib import Path
import shutil
import subprocess
import unittest


class CalendarTodoPreviewTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node.js is required for JavaScript checks')
    def test_popup_mouse_transitions(self):
        subprocess.run(['node', str(Path(__file__).with_name('calendar-todo-preview.cjs'))],
                       check=True, capture_output=True, text=True)
