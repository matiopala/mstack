"""Grade the checked-in Notes regression test through the same entry point as a trial."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "evals/fixtures/verification"


class NotesVerificationTests(unittest.TestCase):
    def test_search_suite_detects_regression(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            def git(*args):
                return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()

            git("init", "-q", "-b", "main")
            git("config", "user.name", "Notes evaluation")
            git("config", "user.email", "eval@example.invalid")
            app = repo / "notes.py"
            healthy = (FIXTURE / "notes.py").read_text()
            expression = 'query.casefold() in note["title"].casefold()'
            self.assertEqual(healthy.count(expression), 1)
            app.write_text(healthy.replace(expression, 'query in note["title"]'))
            git("add", "notes.py")
            git("commit", "-qm", "Broken search")
            base = git("rev-parse", "HEAD")
            shutil.copytree(FIXTURE / "tests", repo / "tests", ignore=shutil.ignore_patterns("__pycache__"))
            git("add", "tests")
            git("commit", "-qm", "Assert the search contract")
            app.write_text(healthy)
            git("commit", "-qam", "Restore case-insensitive search")

            case = "test_search.SearchTests.test_case_insensitive_substring"
            run = subprocess.run([sys.executable, str(ROOT / "evals/check_notes_delivery.py"), str(repo),
                                  base, case, "--start-dir", "tests"], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn(f"baseline: {case} (tests/test_search.py) fail", run.stdout)
            self.assertIn("AssertionError", run.stdout)
            self.assertIn("Quarterly plan", run.stdout)
            self.assertIn(f"candidate: {case} (tests/test_search.py) pass", run.stdout)
            self.assertRegex(run.stderr, r"(?m)^test_case_insensitive_substring \(.+\) \.\.\. ok$")
