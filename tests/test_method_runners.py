import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / "skills/method/scripts"
sys.path.insert(0, str(SCRIPTS))
from runner_results import selected_result


class RunnerTests(unittest.TestCase):
    def test_unittest_reports_execution_from_the_selected_source(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory).resolve() / "test_case.py"
            report = source.with_name("result.json")
            source.write_text(
                "import unittest, os\n"
                "class Feature(unittest.TestCase):\n"
                "    def setUp(self):\n"
                "        self.assertNotEqual(os.getenv('COND'), 'setup')\n"
                "    def test_feature(self):\n"
                "        \"\"\"A test with a description.\"\"\"\n"
                "        if os.getenv('COND') == 'skip': self.skipTest('no service')\n"
                "        self.assertNotEqual(os.getenv('COND'), 'regression')\n")
            selector = "test_case.Feature.test_feature"
            for mode, expected in (("healthy", "pass"), ("regression", "fail"), ("setup", "unverified"),
                                   ("skip", "unverified"), ("twice", "unverified"), ("missing", "unverified")):
                with self.subTest(mode=mode):
                    targets = [selector, selector] if mode == "twice" else [selector]
                    if mode == "missing":
                        targets = ["test_case.Feature.test_missing"]
                    result = subprocess.run([sys.executable, "-B", str(SCRIPTS / "unittest_report.py"),
                                             str(report), selector, "-v", *targets],
                                            env={**os.environ, "COND": mode}, cwd=directory, capture_output=True)
                    data = report.read_bytes()
                    self.assertEqual(selected_result("unittest", selector, data, result.returncode, directory, {source.name})[0],
                                     expected, result.stderr)
                    self.assertEqual(selected_result("unittest", selector, data, result.returncode, directory, set())[0], "unverified")

    def test_tap_requires_a_completed_assertion_and_consistent_exit(self):
        for line, selector, code, expected in (
                ("ok 1 - greet", "greet", 0, "pass"),
                ("not ok 1 - greet", "greet", 1, "fail"),
                ("ok 1 - greet # SKIP offline", "greet # SKIP offline", 0, "unverified"),
                ("not ok 1 - greet # TODO", "greet # TODO", 1, "unverified"),
                ("ok 1 - other", "greet", 0, "unverified"),
                ("ok 1 - greet", "greet", 1, "unverified")):
            with self.subTest(line=line, code=code):
                self.assertEqual(selected_result("tap", selector, ("1..1\n" + line).encode(), code, ".", ())[0], expected)

    def test_junit_skips_errors_and_ambiguous_cases_are_unverified(self):
        for elements, code, expected in (
                ("<testcase name='case'/>", 0, "pass"),
                ("<testcase name='case'><failure/></testcase>", 1, "fail"),
                ("<testcase name='case'><error/></testcase>", 1, "unverified"),
                ("<testcase name='case' status='notrun'/>", 0, "unverified"),
                ("<testcase name='case' result='suppressed'/>", 0, "unverified"),
                ("<testcase name='case'/><testcase name='case'/>", 0, "unverified")):
            with self.subTest(elements=elements):
                self.assertEqual(selected_result("junit", "case", ("<testsuite>" + elements + "</testsuite>").encode(),
                                                 code, ".", ())[0], expected)
