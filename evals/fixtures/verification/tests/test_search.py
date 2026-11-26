import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


CLI = Path(__file__).resolve().parents[1] / "notes.py"


class SearchTests(unittest.TestCase):
    def test_case_insensitive_substring(self):
        with tempfile.TemporaryDirectory() as state:
            def notes(*args):
                output = subprocess.check_output(
                    [sys.executable, str(CLI), "--data-dir", state, *args], text=True
                )
                return json.loads(output)

            saved = notes("add", "--title", "Quarterly plan")
            notes("add", "--title", "Weekly update")
            self.assertEqual(notes("search", "quarterly"), [saved])
            self.assertEqual(notes("search", "ARTER"), [saved])
            self.assertEqual(notes("search", "volcano"), [])


if __name__ == "__main__":
    unittest.main()
