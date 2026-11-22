import json
import os
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "skills/deep-plan/scripts/rounds.py"


class PlanningRoundsTests(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.root = Path(scratch.name).resolve()
        self.project = self.root / "Notes project"
        self.project.mkdir()
        self.brief = "Move Notes to SQLite."
        self.verification = "V01: listing an empty collection leaves no files."
        self.first = self.submit(
            "start", "--brief", self.brief, "--verification", self.verification,
            "--constraint", "Preserve the CLI", "--decision", "Use SQLite",
        )
        self.run_file = self.first["run"]

    def cli(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args], cwd=self.project,
            env={**os.environ, "TMPDIR": str(self.root)},
            text=True, capture_output=True,
        )

    def submit(self, *args):
        result = self.cli(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_simple_task_finishes_after_one_pass(self):
        self.assertEqual((self.first["action"], self.first["round"]), ("explore", 1))
        result = self.submit("advance", self.run_file, "1")
        self.assertEqual((result["action"], result["round"]), ("finish", 1))
        self.assertNotEqual(self.cli("advance", self.run_file, "2").returncode, 0)
        self.assertEqual(list(self.project.iterdir()), [])

    def test_handoff_carries_original_task_and_sourced_findings_across_rounds(self):
        draft = "Create a database whenever Notes starts."
        (self.project / "draft.md").write_text(draft)
        rejected = self.cli("advance", self.run_file, "1", "--draft", draft)
        self.assertNotEqual(rejected.returncode, 0)

        first_fact = {"fact": "First-time reads return an empty list.", "source": "notes.py:20"}
        second_fact = {"fact": "Reads leave the directory absent.", "source": "README.md:15"}
        second = self.submit(
            "advance", self.run_file, "1", "--finding", first_fact["fact"], first_fact["source"],
            "--investigate", "May a read create files?", "When to migrate", "README.md",
        )
        self.assertEqual((second["action"], second["round"]), ("reconsider", 2))
        self.assertEqual(second["handoff"], {
            "project": str(self.project), "brief": self.brief, "verification": self.verification,
            "constraints": ["Preserve the CLI"], "decisions": ["Use SQLite"],
            "findings": [first_fact],
            "investigation": {"question": "May a read create files?", "decision": "When to migrate",
                              "source": "README.md"},
        })
        final = self.submit(
            "advance", self.run_file, "2", "--finding", second_fact["fact"], second_fact["source"],
        )
        self.assertEqual(final["handoff"]["findings"], [first_fact, second_fact])
        self.assertNotIn("investigation", final["handoff"])
        self.assertNotIn(draft, json.dumps(final["handoff"]))

    def test_incomplete_requests_do_not_consume_a_round(self):
        for fields in [
            ("--investigate", "Is migration safe?"),
            ("--investigate", " ", "When to migrate", "README.md"),
            ("--investigate", "Can a read write?", "", "README.md"),
            ("--investigate", "Can a read write?", "When to migrate", " "),
            ("--finding", "Reads create files.", ""),
        ]:
            with self.subTest(fields=fields):
                self.assertNotEqual(self.cli("advance", self.run_file, "1", *fields).returncode, 0)
        self.assertNotEqual(self.cli("advance", self.run_file, "2").returncode, 0)
        final = self.submit("advance", self.run_file, "1", "--unresolved", "Who owns migration?")
        self.assertEqual(final["action"], "finish")
        self.assertEqual(final["handoff"]["unresolved"], [{"question": "Who owns migration?"}])

    def test_round_limit_returns_the_outstanding_decision(self):
        for number in (1, 2):
            result = self.submit(
                "advance", self.run_file, str(number),
                "--investigate", f"Who calls reader {number}?", "When to migrate", "notes.py",
            )
            self.assertEqual((result["action"], result["round"]), ("reconsider", number + 1))
        final = self.submit(
            "advance", self.run_file, "3", "--investigate",
            "Must old binaries still write?", "Whether to support dual writes", "Release owner",
        )
        self.assertEqual((final["action"], final["round"]), ("limit", 3))
        self.assertEqual(final["handoff"]["unresolved"], [{
            "question": "Must old binaries still write?", "decision": "Whether to support dual writes",
            "source": "Release owner",
        }])
        self.assertNotEqual(self.cli("advance", self.run_file, "4").returncode, 0)

    def test_competing_submissions_cannot_branch_a_run_and_winner_can_retry(self):
        reports = [
            ("advance", self.run_file, "1", "--finding", fact, "notes.py",
             "--investigate", "Can a read write?", "When to migrate", "README.md")
            for fact in ("Reads create directories.", "Reads leave directories absent.")
        ]
        with ThreadPoolExecutor(max_workers=2) as workers:
            results = list(workers.map(lambda report: self.cli(*report), reports))
        self.assertCountEqual([result.returncode for result in results], [0, 1])
        winner = next(i for i, result in enumerate(results) if result.returncode == 0)
        handoff = json.loads(results[winner].stdout)
        self.assertEqual(self.submit(*reports[winner]), handoff)
        final = self.submit("advance", self.run_file, "2")
        self.assertEqual(final["handoff"]["findings"], handoff["handoff"]["findings"])
        self.assertEqual(self.submit(*reports[winner]), final)
