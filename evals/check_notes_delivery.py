"""Replay a delivered Notes test against the original CLI and a clean candidate."""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile


REPORTER = Path(__file__).resolve().parents[1] / "skills/method/scripts"
sys.path.insert(0, str(REPORTER))
from runner_results import selected_result


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args])


def replay(repo, base, candidate, selector, start_dir):
    original = git(repo, "show", base + ":notes.py")
    commit = git(repo, "rev-parse", "--verify", candidate + "^{commit}").decode().strip()
    with tempfile.TemporaryDirectory(prefix="notes-delivery-") as temporary:
        for version, expected in (("baseline", "fail"), ("candidate", "pass")):
            checkout = Path(temporary).resolve() / version
            git(repo, "clone", "--quiet", "--no-checkout", str(Path(repo).resolve()), str(checkout))
            git(checkout, "checkout", "--quiet", "--detach", commit)
            if version == "baseline":
                (checkout / "notes.py").write_bytes(original)
            args = ["discover", "-s", start_dir, "-v"]
            report = checkout.parent / (version + ".json")
            run = subprocess.run([sys.executable, "-B", str(REPORTER / "unittest_report.py"), str(report),
                                  selector, *args], cwd=checkout, capture_output=True)
            tracked = git(checkout, "ls-files", "-z").decode().split("\0")
            outcome, source = selected_result("unittest", selector, report.read_bytes() if report.exists() else b"",
                                              run.returncode, checkout, tracked)
            if outcome != expected:
                raise ValueError(f"{version}: expected {expected}, got {outcome}\n{run.stderr.decode(errors='replace')}")
            print(f"{version}: {selector} ({source}) {outcome}", flush=True)
            if version == "baseline":
                print(run.stderr.decode(errors="replace").rstrip(), flush=True)
            else:
                # Exercise the test's normal entry point without the reporting adapter.
                subprocess.run([sys.executable, "-B", "-m", "unittest", *args], cwd=checkout, check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", type=Path)
    parser.add_argument("base", help="Commit containing the original broken Notes CLI")
    parser.add_argument("selector", help="Fully qualified unittest case ID")
    parser.add_argument("--candidate", default="HEAD", help="Commit containing the delivered tests and fix")
    parser.add_argument("--start-dir", default=".", help="The repository's unittest discovery directory")
    args = parser.parse_args()
    replay(args.repo, args.base, args.candidate, args.selector, args.start_dir)
