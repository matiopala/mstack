"""Run the project's unittest command and report the selected test's actual result."""
import inspect
import json
from pathlib import Path
import sys
import unittest


def main():
    report, selector, *args = sys.argv[1:]
    sys.path[0] = str(Path.cwd())
    sys.argv[:] = ["python -m unittest", *args]
    matches = []

    class Result(unittest.TextTestResult):
        def startTest(self, test):
            super().startTest(test)
            if test.id() == selector:
                method = inspect.unwrap(getattr(test, test._testMethodName))
                source = inspect.getsourcefile(method)
                matches.append({"file": str(Path(source).resolve()) if source else None,
                                "outcome": "unverified"})

        def addSuccess(self, test):
            super().addSuccess(test)
            if test.id() == selector:
                matches[-1]["outcome"] = "pass"

        def selected_failure(self, test, err):
            if test.id() != selector:
                return
            # unittest also calls addFailure for assertion errors in setup or teardown.
            # Only a traceback from the test invocation establishes a failing baseline.
            method = getattr(test, test._testMethodName)
            frames = {getattr(method, "__code__", None), getattr(test._callTestMethod, "__code__", None)}
            trace = err[2]
            while trace:
                if trace.tb_frame.f_code in frames:
                    matches[-1]["outcome"] = "fail"
                    return
                trace = trace.tb_next

        def addFailure(self, test, err):
            super().addFailure(test, err)
            self.selected_failure(test, err)

        def addSubTest(self, test, subtest, err):
            super().addSubTest(test, subtest, err)
            if err and issubclass(err[0], test.failureException):
                self.selected_failure(test, err)

    class Runner(unittest.TextTestRunner):
        resultclass = Result

    program = unittest.main(module=None, testRunner=Runner, exit=False)
    Path(report).write_text(json.dumps({"selector": selector, "matches": matches}))
    return 0 if program.result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
