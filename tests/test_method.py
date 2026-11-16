from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills/method/scripts"
sys.path.insert(0, str(SCRIPTS))
from core import Error, STAGES, Store, Task, atomic, git, lock, target_ref
from server import make_server


class MethodTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="method tests ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.repo = self.root / "project"
        self.repo.mkdir()
        git(self.repo, "init", "-b", "main")
        git(self.repo, "config", "user.email", "method@example.invalid")
        git(self.repo, "config", "user.name", "Method Test")
        (self.repo / "app.py").write_text("print('hello')\n")
        git(self.repo, "add", "app.py")
        git(self.repo, "commit", "-m", "baseline")
        self.store = Store(self.root / "store")
        self.task = self.store.task(self.store.start({"workspace": str(self.repo), "target": "main", "title": "Improve the greeting"})["id"])

    def apply(self, command, **data):
        return self.task.apply(command, data)

    def prepare(self, manual=False):
        for stage in STAGES:
            file = self.root / (stage + ".md")
            file.write_text("# " + stage.title() + "\n\nThe application greets the user.\n")
            criteria = []
            if stage == "requirements":
                criteria = [{"id": "R01", "text": "Greet the user"}]
            if stage == "verification":
                criteria = [{"id": "V01", "text": "Run the actual CLI", "requirements": ["R01"], "kind": "automated"}]
                if manual:
                    criteria.append({"id": "V02", "text": "Check usefulness", "requirements": ["R01"], "kind": "human"})
            self.apply("submit", stage=stage, file=str(file), criteria=criteria)
            artifact = self.task.latest(self.task.load(), stage)
            self.apply("decide", stage=stage, decision="approved", revision=artifact["revision"], sha256=artifact["sha256"], instruction="I approve this revision.")

    def authorize(self, mode="implementation", **kwargs):
        self.apply("authorize", revisions=self.task.snapshot(self.task.load()), instruction="Implement this approved work." if mode == "implementation" else "Collect more evidence.", mode=mode, **kwargs)

    def implementation(self, actor="implementer-1"):
        self.apply("run-start", role="implementer", actor=actor)
        run = self.task.current_run(self.task.load())
        (self.repo / "app.py").write_text("print('hello, world')\n")
        self.apply("run-finish", run=run["id"], status="completed", processes_stopped=True, summary="Changed greeting; all owned commands finished.")
        self.apply("candidate", paths=["app.py"])
        return self.task.load()["candidates"][-1]

    def verification(self, outcome="pass", findings=None, actor="verifier-1"):
        self.apply("run-start", role="verifier", actor=actor)
        run = self.task.current_run(self.task.load())
        self.apply("command", run=run["id"], argv=[sys.executable, "app.py"], safe_to_record=True)
        run = self.task.current_run(self.task.load())
        results = [{"id": "V01", "outcome": outcome, "observed": "Observed actual CLI output", "evidence": [run["evidence"][0]["id"]]}]
        if len(self.task.latest(self.task.load(), "verification")["criteria"]) > 1:
            results.append({"id": "V02", "outcome": "human_pending", "observed": "Requires human judgment"})
        if findings:
            for finding in findings:
                if finding["status"] != "open":
                    finding["evidence"] = [run["evidence"][0]["id"]]
        self.apply("verify", run=run["id"], processes_stopped=True, results=results, findings=findings or [], review="Reviewed the actual diff", launch="python3 app.py", tradeoffs="Keeps the existing CLI")

    def test_complete_flow_requires_actual_delivery(self):
        self.prepare(manual=True)
        self.assertEqual(self.task.view()["status"], "authorization")
        with self.assertRaises(Error):
            self.apply("run-start", role="implementer", actor="i")
        self.authorize()
        candidate = self.implementation()
        self.verification()
        self.assertEqual(self.task.view()["status"], "human_review")
        acceptance = dict(candidate=candidate["commit"], requirements=self.task.snapshot(self.task.load())["requirements"], instruction="I accept this candidate.")
        with self.assertRaises(Error):
            self.apply("accept", **acceptance)
        self.apply("accept", observations={"V02": "The greeting is useful."}, **acceptance)
        self.assertEqual(self.task.view()["status"], "delivery")
        with self.assertRaises(Error):
            self.apply("delivery", mode="observed", candidate=candidate["commit"], target="main", result_commit=candidate["commit"], evidence="Not merged", instruction="Record delivery")
        git(self.repo, "update-ref", "refs/heads/main", candidate["commit"])
        self.apply("delivery", mode="observed", candidate=candidate["commit"], target="main", result_commit=candidate["commit"], evidence="Observed local main tip", instruction="Record the merged result")
        self.assertEqual(self.task.view()["status"], "complete")

    def delivered_task(self):
        self.prepare(); self.authorize()
        candidate = self.implementation(); self.verification()
        self.apply("accept", candidate=candidate["commit"],
                   requirements=self.task.snapshot(self.task.load())["requirements"],
                   instruction="Accept the verified candidate.", observations={})
        git(self.repo, "update-ref", "refs/heads/main", candidate["commit"])
        self.apply("delivery", mode="observed", candidate=candidate["commit"],
                   target="main", result_commit=candidate["commit"],
                   evidence="Observed local main tip.", instruction="Record the merged result.")
        return candidate

    def test_start_after_delivery_preserves_previous_task(self):
        candidate = self.delivered_task()
        old_view = self.task.view()
        bundle = self.task.read_blob(candidate["bundle"])
        git(self.repo, "switch", "main")
        note = self.repo / ".tasks" / "notes.txt"
        note.write_text("Keep workspace notes.")
        payload = self.root / "next-task.json"
        payload.write_text(json.dumps({"workspace": str(self.repo), "target": "main", "title": "Next task"}))
        result = subprocess.run([sys.executable, str(SCRIPTS / "method.py"), "start", "--input", str(payload)],
                                cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        view = json.loads(result.stdout)
        locator = json.loads((self.repo / ".tasks" / "locator.json").read_text())
        self.assertEqual(locator, {"store": str(self.store.root), "task": view["id"]})
        self.assertNotEqual(view["id"], old_view["id"])
        self.assertEqual(view["status"], "interview")
        self.assertEqual(view["task"]["baseline"], candidate["commit"])
        self.assertEqual(view["state"]["approved"], {})
        self.assertEqual(note.read_text(), "Keep workspace notes.")
        fresh = Store(self.store.root)
        self.assertEqual(fresh.task(old_view["id"]).view(), old_view)
        self.assertEqual(fresh.task(old_view["id"]).read_blob(candidate["bundle"]), bundle)
        self.assertEqual({task["status"] for task in fresh.list()}, {"complete", "interview"})

    def test_start_preserves_unsafe_locators(self):
        locator = self.repo / ".tasks" / "locator.json"
        original = locator.read_bytes()
        branch = git(self.repo, "symbolic-ref", "HEAD")
        other = self.root / "other"
        git(self.repo, "worktree", "add", "-b", "other", str(other), "main")
        other_task = self.store.start({"workspace": str(other), "target": "main", "title": "Other task"})
        cases = [
            ("unfinished", original.decode()),
            ("malformed", "{"),
            ("not-an-object", "[]"),
            ("missing-fields", "{}"),
            ("unknown-task", json.dumps({"store": str(self.store.root), "task": "missing-task"})),
            ("different-store", json.dumps({"store": str(self.root / "other-store"), "task": self.task.view()["id"]})),
            ("different-workspace", json.dumps({"store": str(self.store.root), "task": other_task["id"]})),
        ]
        for name, content in cases:
            with self.subTest(name=name):
                locator.write_text(content)
                paths = sorted(str(p.relative_to(self.store.root)) for p in self.store.root.rglob("*"))
                events = self.task.events()
                with self.assertRaises((Error, ValueError)):
                    self.store.start({"workspace": str(self.repo), "target": "main", "title": "Blocked task"})
                self.assertEqual(locator.read_text(), content)
                self.assertEqual(git(self.repo, "symbolic-ref", "HEAD"), branch)
                self.assertEqual(self.task.events(), events)
                self.assertEqual(sorted(str(p.relative_to(self.store.root)) for p in self.store.root.rglob("*")), paths)
        locator.write_bytes(original)

    def test_completed_locator_requires_idle_unblocked_task_and_locks(self):
        self.delivered_task()
        locator = self.repo / ".tasks" / "locator.json"
        original = locator.read_bytes()
        payload = {"workspace": str(self.repo), "target": "main", "title": "Blocked task"}
        self.apply("pause", instruction="Pause this task.")
        with self.assertRaises(Error):
            self.store.start(payload)
        self.apply("resume")
        self.apply("block", reason="Reconcile workspace before reuse.")
        with self.assertRaises(Error):
            self.store.start(payload)
        self.apply("resume", resolution="Workspace reconciled.")
        for path in (self.store.root / "registry.lock", self.task.path / "task.lock"):
            with self.subTest(lock=path.name), lock(path), self.assertRaises(Error):
                self.store.start(payload)
        self.assertEqual(locator.read_bytes(), original)
        self.assertEqual(len(self.store.list()), 1)
        self.authorize()
        self.apply("run-start", role="implementer", actor="active-correction")
        with self.assertRaises(Error):
            self.store.start(payload)
        self.assertEqual(locator.read_bytes(), original)

    def test_failed_start_preserves_completed_locator(self):
        self.delivered_task()
        locator = self.repo / ".tasks" / "locator.json"
        original = locator.read_bytes()
        old_view = self.task.view()
        git(self.repo, "switch", "main")
        def fail_switch(workspace, *args, **kwargs):
            if args[:1] == ("switch",):
                raise Error("Simulated branch setup failure")
            return git(workspace, *args, **kwargs)
        with patch("core.git", side_effect=fail_switch), self.assertRaisesRegex(Error, "setup failure"):
            self.store.start({"workspace": str(self.repo), "target": "main", "title": "Interrupted start"})
        self.assertEqual(locator.read_bytes(), original)
        self.assertEqual(self.task.view(), old_view)
        self.assertEqual(git(self.repo, "symbolic-ref", "--short", "HEAD"), "main")

    def test_start_publication_failures_restore_previous_locator(self):
        self.delivered_task()
        locator = self.repo / ".tasks" / "locator.json"
        original = locator.read_bytes()
        old_view = self.task.view()
        record = Task.record
        for failure in ("before-started-record", "after-started-record", "before-locator-replace", "after-locator-replace"):
            with self.subTest(failure=failure):
                git(self.repo, "switch", "main")
                known = {task["id"] for task in self.store.list()}
                def fail_record(task, kind, data, state):
                    if kind == "started":
                        if failure == "after-started-record":
                            record(task, kind, data, state)
                        raise OSError("Simulated record failure")
                    return record(task, kind, data, state)
                def fail_locator(path, data):
                    if Path(path).resolve() == locator.resolve() and data != original:
                        if failure == "after-locator-replace":
                            atomic(path, data)
                        raise OSError("Simulated locator failure")
                    return atomic(path, data)
                fault = (patch("core.Task.record", new=fail_record) if failure.endswith("started-record")
                         else patch("core.atomic", side_effect=fail_locator))
                with fault, self.assertRaisesRegex(OSError, "Simulated"):
                    self.store.start({"workspace": str(self.repo), "target": "main", "title": "Interrupted publication"})
                self.assertEqual(locator.read_bytes(), original)
                self.assertEqual(self.task.view(), old_view)
                created = [task for task in self.store.list() if task["id"] not in known]
                self.assertEqual(len(created), 1)
                self.assertEqual(created[0]["status"], "recovery")
                self.store.task(created[0]["id"]).apply("resolve", {
                    "instruction": "Fixture: abandon this failed startup",
                    "resolution": "No setup process is running; the next case will restore the branch",
                    "processes_stopped": True})

    def test_metadata_only_startup_can_be_inspected_and_resolved(self):
        self.delivered_task()
        previous = self.task.view()
        for replacement in (False, True):
            with self.subTest(replacement=replacement):
                repo = self.repo if replacement else self.root / "fresh-start"
                if not replacement:
                    git(self.root, "clone", "--quiet", "--branch", "main", str(self.repo), str(repo))
                    git(repo, "switch", "-c", "feature/HEAD")
                locator = repo / ".tasks/locator.json"
                old_locator = locator.read_bytes() if locator.exists() else None
                original_head = git(repo, "rev-parse", "HEAD")
                original_branch = git(repo, "branch", "--show-current")
                known = {p.parent.name for p in (self.store.root / "tasks").glob("*/task.json")}
                record = Task.record
                def interrupt(task, kind, data, state):
                    if kind == "start-intent":
                        raise KeyboardInterrupt("Fixture: before first event")
                    return record(task, kind, data, state)
                payload = {"workspace": str(repo), "target": "main", "title": "Incomplete initialization"}
                with patch.object(Task, "record", interrupt), self.assertRaises(KeyboardInterrupt):
                    self.store.start(payload)
                paths = [p.parent for p in (self.store.root / "tasks").glob("*/task.json") if p.parent.name not in known]
                self.assertEqual(len(paths), 1)
                task = self.store.task(paths[0].name)
                metadata = (task.path / "task.json").read_bytes()
                snapshot = {str(p.relative_to(task.path)): (p.read_bytes(), p.stat().st_mtime_ns)
                            for p in task.path.rglob("*") if p.is_file()}
                cli = [sys.executable, str(SCRIPTS / "method.py"), "--store", str(self.store.root)]
                for command in ("list", "status", "next"):
                    result = subprocess.run([*cli, command, "--task", task.path.name],
                                            cwd=repo, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    view = json.loads(result.stdout)
                    if command == "list":
                        view = next(v for v in view if v["id"] == task.path.name)
                    self.assertEqual(view["status"], "recovery")
                self.assertEqual(snapshot, {str(p.relative_to(task.path)): (p.read_bytes(), p.stat().st_mtime_ns)
                                           for p in task.path.rglob("*") if p.is_file()})
                with self.assertRaisesRegex(Error, "startup is unfinished"):
                    self.store.start(payload)
                resumed = task.apply("resume", {})
                self.assertEqual(resumed["status"], "recovery")
                self.assertEqual(git(repo, "rev-parse", "HEAD"), original_head)
                self.assertEqual(git(repo, "branch", "--show-current"), original_branch)
                self.assertEqual(locator.read_bytes() if locator.exists() else None, old_locator)
                result = subprocess.run([*cli, "resolve", "--task", task.path.name, "--input", "-"],
                                        input=json.dumps({"instruction": "Fixture: abandon this incomplete startup",
                                                          "resolution": "No setup commands ran; the original checkout is unchanged.",
                                                          "processes_stopped": True}),
                                        cwd=repo, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("abandoned", json.loads(result.stdout)["next_action"].lower())
                self.assertEqual((task.path / "task.json").read_bytes(), metadata)
                abandoned = task.view()
                new_task = self.store.start(payload)
                self.assertEqual(new_task["status"], "interview")
                self.assertNotEqual(new_task["id"], task.path.name)
                self.assertEqual(task.view(), abandoned)
                self.assertEqual(self.task.view(), previous)
                self.assertEqual(json.loads(locator.read_text())["task"], new_task["id"])

    def test_initial_event_write_failure_is_recoverable_without_resume(self):
        repo = self.root / "event-write-failure"
        git(self.root, "clone", "--quiet", "--branch", "main", str(self.repo), str(repo))
        def fail_first_event(path, data):
            if Path(path).name == "000001.json":
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                (Path(path).parent / ".write-interrupted").write_bytes(data[:20])
                raise OSError("Fixture: event publication failed")
            return atomic(path, data)
        payload = {"workspace": str(repo), "target": "main", "title": "Failed initial write"}
        with patch("core.atomic", side_effect=fail_first_event), self.assertRaises(OSError):
            self.store.start(payload)
        task = next(self.store.task(p.parent.name) for p in (self.store.root / "tasks").glob("*/task.json")
                    if json.loads(p.read_text())["workspace"] == str(repo.resolve()))
        self.assertEqual(task.view()["status"], "recovery")
        partial = task.path / "events/.write-interrupted"
        original = partial.read_bytes()
        task.apply("resolve", {"instruction": "Fixture: abandon failed initialization",
                               "resolution": "No source or locator changes occurred.", "processes_stopped": True})
        self.assertEqual(partial.read_bytes(), original)
        self.assertEqual(task.events()[0]["kind"], "resolve")
        self.assertEqual(self.store.start(payload)["status"], "interview")

    def test_missing_or_corrupt_history_is_not_initialization(self):
        repo = self.root / "corrupt-initialization"
        git(self.root, "clone", "--quiet", "--branch", "main", str(self.repo), str(repo))
        record = Task.record
        def interrupt(task, kind, data, state):
            if kind == "start-intent":
                raise KeyboardInterrupt("Fixture: before first event")
            return record(task, kind, data, state)
        with patch.object(Task, "record", interrupt), self.assertRaises(KeyboardInterrupt):
            self.store.start({"workspace": str(repo), "target": "main", "title": "Validation fixture"})
        task = next(self.store.task(p.parent.name) for p in (self.store.root / "tasks").glob("*/task.json")
                    if json.loads(p.read_text())["workspace"] == str(repo.resolve()))
        metadata_path = task.path / "task.json"
        metadata = metadata_path.read_bytes()
        self.assertEqual(task.view()["status"], "recovery")
        original = json.loads(metadata)
        malformed = [
            {"id": "wrong-task"}, {"baseline": "not-a-commit"}, {"target_at_start": "not-a-commit"},
            {"skill_sha256": "not-a-sha256"}, {"delivery_requirement": "push"}, {"original_branch": []},
            {"original_branch": "bad branch"}, {"original_branch": "HEAD"}, {"object_format": "invalid"},
            {"object_format": "sha256" if original.get("object_format") == "sha1" else "sha1"}, {"target_ref": "refs/tags/main"}, {"target_ref": "refs/heads/other"},
            {"target_ref": "refs/heads/bad branch"}, {"repository": {**original["repository"], "id": "../other"}},
        ]
        for corrupt in [b"{}", b"not json", *[json.dumps({**original, **change}).encode() for change in malformed]]:
            with self.subTest(metadata=corrupt):
                metadata_path.write_bytes(corrupt)
                with self.assertRaises((Error, ValueError)):
                    task.view()
                metadata_path.write_bytes(metadata)
        legacy = {key: value for key, value in original.items() if key not in ("object_format", "original_branch", "target_ref")}
        metadata_path.write_text(json.dumps(legacy))
        self.assertEqual(task.view()["status"], "recovery")
        metadata_path.write_bytes(metadata)
        for relative, content in (("state.json", b"{}"), ("runs/old/evidence.txt", b"old evidence"),
                                  ("candidates/old/change.diff", b"old candidate"), ("artifacts/old.md", b"old approval"),
                                  ("events/000001.json", b"broken event")):
            with self.subTest(history=relative):
                path = task.path / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
                before = path.read_bytes()
                with self.assertRaises((Error, ValueError)):
                    task.view()
                self.assertEqual(path.read_bytes(), before)
                path.unlink()
                for parent in list(path.parents):
                    if parent == task.path:
                        break
                    if not list(parent.iterdir()):
                        parent.rmdir()
        self.assertEqual(task.view()["status"], "recovery")

    def test_start_interruption_recovers_locator_publication(self):
        for completed in (False, True):
            for boundary in ("before-locator", "after-locator", "before-final-record"):
                with self.subTest(completed=completed, boundary=boundary):
                    fixture = MethodTests()
                    fixture.setUp()
                    try:
                        if completed:
                            fixture.delivered_task()
                            repo = fixture.repo
                            previous = (repo / ".tasks/locator.json").read_bytes()
                            previous_view = fixture.task.view()
                            git(repo, "switch", "main")
                        else:
                            repo = fixture.root / "new"
                            git(fixture.root, "clone", "--quiet", "--branch=main", fixture.repo.as_uri(), str(repo))
                            previous = None
                        locator = repo / ".tasks/locator.json"
                        known = {t["id"] for t in fixture.store.list()}
                        record = Task.record

                        def interrupt_locator(path, data):
                            if Path(path).resolve() == locator.resolve():
                                if boundary == "after-locator":
                                    atomic(path, data)
                                raise KeyboardInterrupt("Interrupted locator publication")
                            return atomic(path, data)

                        def interrupt_record(task, kind, data, state):
                            if kind == "started":
                                raise KeyboardInterrupt("Interrupted final record")
                            return record(task, kind, data, state)

                        fault = (patch("core.Task.record", new=interrupt_record) if boundary == "before-final-record"
                                 else patch("core.atomic", side_effect=interrupt_locator))
                        payload = {"workspace": str(repo), "target": "main", "title": "Recover startup"}
                        with fault, self.assertRaises(KeyboardInterrupt):
                            fixture.store.start(payload)
                        created = [t for t in fixture.store.list() if t["id"] not in known]
                        self.assertEqual(len(created), 1)
                        self.assertEqual(created[0]["status"], "recovery")
                        task = Store(fixture.store.root).task(created[0]["id"])
                        self.assertEqual(task.load()["pending"]["kind"], "start")
                        expected_locator = (previous if boundary == "before-locator"
                                            else json.dumps({"store": str(fixture.store.root), "task": created[0]["id"]}))
                        if expected_locator is None:
                            self.assertFalse(locator.exists())
                        else:
                            self.assertEqual(json.loads(locator.read_bytes()), json.loads(expected_locator))
                        before_files = (repo / "app.py").read_bytes()
                        branch = git(repo, "symbolic-ref", "--short", "HEAD")
                        with self.assertRaises(Error):
                            fixture.store.start(payload)
                        self.assertEqual(len(fixture.store.list()), len(known) + 1)
                        task.apply("resume", {})
                        task.apply("resume", {})
                        self.assertEqual(task.view()["status"], "interview")
                        self.assertEqual(json.loads(locator.read_bytes()), {"store": str(fixture.store.root), "task": created[0]["id"]})
                        self.assertEqual(git(repo, "symbolic-ref", "--short", "HEAD"), branch)
                        self.assertEqual((repo / "app.py").read_bytes(), before_files)
                        if completed:
                            self.assertEqual(fixture.task.view(), previous_view)
                    finally:
                        fixture.doCleanups()

    def test_start_recovery_preserves_unexpected_workspace_or_locator(self):
        repo = self.root / "new"
        git(self.root, "clone", "--quiet", "--branch=main", self.repo.as_uri(), str(repo))
        locator = repo / ".tasks/locator.json"
        known = {t["id"] for t in self.store.list()}
        def interrupt(path, data):
            if Path(path).resolve() == locator.resolve():
                raise KeyboardInterrupt("Before publication")
            return atomic(path, data)
        with patch("core.atomic", side_effect=interrupt), self.assertRaises(KeyboardInterrupt):
            self.store.start({"workspace": str(repo), "target": "main", "title": "Recover startup"})
        task_id = next(t["id"] for t in self.store.list() if t["id"] not in known)
        task = self.store.task(task_id)
        branch = git(repo, "symbolic-ref", "--short", "HEAD")
        git(repo, "switch", "main")
        with self.assertRaises(Error):
            task.apply("resume", {})
        self.assertEqual(git(repo, "symbolic-ref", "--short", "HEAD"), "main")
        git(repo, "switch", branch)
        locator.parent.mkdir(exist_ok=True)
        unexpected = b'{"task":"unrelated","store":"/unrelated"}'
        locator.write_bytes(unexpected)
        with self.assertRaises(Error):
            task.apply("resume", {})
        self.assertEqual(locator.read_bytes(), unexpected)
        self.assertEqual(task.view()["status"], "recovery")

    def test_shallow_clone_is_rejected_without_side_effects(self):
        git(self.repo, "switch", "main")
        (self.repo / "app.py").write_text("print('another baseline')\n")
        git(self.repo, "commit", "-am", "another baseline")
        repo = self.root / "shallow"
        git(self.root, "clone", "--quiet", "--depth=1", "--branch=main", self.repo.as_uri(), str(repo))
        store = Store(self.root / "unused-store")
        before = {str(p.relative_to(repo)): p.read_bytes() for p in repo.rglob("*") if p.is_file()}
        with self.assertRaisesRegex(Error, "[Ss]hallow"):
            store.start({"workspace": str(repo), "target": "main", "title": "Shallow"})
        self.assertFalse(store.root.exists())
        self.assertEqual({str(p.relative_to(repo)): p.read_bytes() for p in repo.rglob("*") if p.is_file()}, before)

    def test_candidate_rejects_repository_that_became_shallow(self):
        self.prepare(); self.authorize(); self.implementation()
        self.authorize()
        self.apply("run-start", role="implementer", actor="correction")
        run = self.task.current_run(self.task.load())
        (self.repo / "app.py").write_text("print('correction')\n")
        self.apply("run-finish", run=run["id"], status="completed", processes_stopped=True, summary="Ready to capture")
        common = Path(git(self.repo, "rev-parse", "--path-format=absolute", "--git-common-dir"))
        (common / "shallow").write_text(git(self.repo, "rev-parse", "HEAD") + "\n")
        before = self.task.view()
        index = git(self.repo, "write-tree")
        with self.assertRaisesRegex(Error, "[Ss]hallow"):
            self.apply("candidate", paths=["app.py"])
        self.assertEqual(self.task.view(), before)
        self.assertEqual(git(self.repo, "write-tree"), index)
        self.assertEqual((self.repo / "app.py").read_text(), "print('correction')\n")

    def test_verifier_preserves_git_object_format_without_original_workspace(self):
        for object_format in ("sha1", "sha256"):
            for legacy in (False, True):
                with self.subTest(object_format=object_format, legacy=legacy):
                    fixture = MethodTests()
                    fixture.setUp()
                    try:
                        repo = fixture.root / "formatted"
                        repo.mkdir()
                        git(repo, "init", "-b", "main", "--object-format=" + object_format)
                        git(repo, "config", "user.email", "method@example.invalid")
                        git(repo, "config", "user.name", "Method Test")
                        (repo / "app.py").write_text("print('baseline')\n")
                        git(repo, "add", "app.py"); git(repo, "commit", "-m", "baseline")
                        fixture.repo = repo
                        fixture.task = fixture.store.task(fixture.store.start({"workspace": str(repo), "target": "main", "title": "Object format"})["id"])
                        fixture.prepare(); fixture.authorize()
                        candidate = fixture.implementation()
                        if legacy:
                            state = fixture.task.load()
                            state["task"].pop("object_format", None)
                            fixture.task.record("legacy-format-fixture", {}, state)
                        shutil.rmtree(repo)
                        with patch.dict(os.environ, {"GIT_DEFAULT_HASH": "sha256" if object_format == "sha1" else "sha1"}):
                            fixture.apply("run-start", role="verifier", actor="format-verifier")
                        run = fixture.task.current_run(fixture.task.load())
                        self.assertEqual(git(run["workspace"], "rev-parse", "--show-object-format"), object_format)
                        self.assertEqual(git(run["workspace"], "rev-parse", "HEAD"), candidate["commit"])
                        self.assertEqual((Path(run["workspace"]) / "app.py").read_text(), "print('hello, world')\n")
                        fixture.apply("command", run=run["id"], argv=[sys.executable, "app.py"], safe_to_record=True)
                        self.assertEqual(fixture.task.current_run(fixture.task.load())["evidence"][-1]["exit_code"], 0)
                    finally:
                        fixture.doCleanups()

    def test_verifier_setup_is_charged_before_commands_are_admitted(self):
        self.prepare(); self.authorize(minutes=1); self.implementation()
        elapsed = [time.time()]
        admitted = []
        def slow_fetch(workspace, *args, **kwargs):
            if args[0] == "fetch":
                running = self.task.current_run(self.task.load())
                admitted.append(running)
                result = git(workspace, *args, **kwargs)
                elapsed[0] += 180
                return result
            return git(workspace, *args, **kwargs)
        with patch("core.time.time", side_effect=lambda: elapsed[0]), patch("core.git", side_effect=slow_fetch):
            with self.assertRaisesRegex(Error, "[Ee]xecution time"):
                self.apply("run-start", role="verifier", actor="slow-verifier")
            state = self.task.load()
            self.assertIsNotNone(admitted[0])
            self.assertEqual(state["runs"][-1]["status"], "interrupted")
            self.assertGreaterEqual(state["authorization"]["used_seconds"], 180)
            self.assertEqual(state["authorization"]["rounds_used"], 1)
            self.assertEqual(self.task.view()["status"], "limit")
            self.assertIsNone(state["pending"])
            with self.assertRaises(Error):
                self.apply("command", run=state["runs"][-1]["id"], argv=[sys.executable, "-c", "print('must not execute')"], safe_to_record=True)
            before = copy.deepcopy(state["authorization"])
            self.apply("resume")
            self.assertEqual(self.task.load()["authorization"], before)

    def test_verifier_setup_interruption_retains_actor_and_budget(self):
        self.prepare(); self.authorize(minutes=1); self.implementation()
        def interrupt_fetch(workspace, *args, **kwargs):
            if args[0] == "fetch":
                raise KeyboardInterrupt("Interrupted setup")
            return git(workspace, *args, **kwargs)
        with patch("core.git", side_effect=interrupt_fetch), self.assertRaises(KeyboardInterrupt):
            self.apply("run-start", role="verifier", actor="interrupted-verifier")
        task = Store(self.store.root).task(self.task.load()["task"]["id"])
        state = task.load()
        run = task.current_run(state)
        self.assertIsNotNone(run)
        self.assertEqual(run["actor"], "interrupted-verifier")
        self.assertEqual(state["authorization"]["rounds_used"], 1)
        self.assertEqual(task.view()["status"], "recovery")
        task.apply("resume", {})
        self.assertEqual(task.current_run(task.load())["id"], run["id"])
        with patch("core.time.time", return_value=run["started_epoch"] + 61):
            task.apply("resolve", {"instruction": "Fixture: investigated setup", "resolution": "Owned setup processes stopped", "processes_stopped": True})
            task.apply("run-finish", {"run": run["id"], "status": "interrupted", "summary": "Reconciled setup", "processes_stopped": True})
        task.apply("resume", {"resolution": "Workspace and setup reconciled"})
        self.assertEqual(task.view()["status"], "limit")
        self.assertGreaterEqual(task.load()["authorization"]["used_seconds"], 61)

    def test_verifier_setup_failure_retains_round_and_allows_fresh_retry(self):
        self.prepare(); self.authorize(); self.implementation()
        def fail_fetch(workspace, *args, **kwargs):
            if args[0] == "fetch":
                raise Error("Fixture fetch failure")
            return git(workspace, *args, **kwargs)
        with patch("core.git", side_effect=fail_fetch), self.assertRaisesRegex(Error, "Fixture fetch failure"):
            self.apply("run-start", role="verifier", actor="failed-verifier")
        state = self.task.load()
        self.assertEqual(state["runs"][-1]["status"], "interrupted")
        self.assertEqual(state["authorization"]["rounds_used"], 1)
        self.assertGreater(state["authorization"]["used_seconds"], 0)
        self.assertIsNone(state["pending"])
        with self.assertRaises(Error):
            self.apply("run-start", role="verifier", actor="failed-verifier")
        self.apply("run-start", role="verifier", actor="fresh-verifier")
        self.assertEqual(self.task.load()["authorization"]["rounds_used"], 2)

    def test_verifier_setup_timeout_stops_and_reaps_owned_process(self):
        self.prepare(); self.authorize(); self.implementation()
        processes = []
        popen = subprocess.Popen
        recorded_pid = []

        def spawn(argv, **kwargs):
            if argv[:1] == ["git"] and "fetch" in argv:
                process = popen([sys.executable, "-c", "import time; time.sleep(30)"], **kwargs)
                processes.append(process)
                return process
            return popen(argv, **kwargs)

        def short_allowance(deadline):
            return 0.1

        record = self.task.record
        def observe_record(kind, data, state):
            if kind == "checkout-command-started" and "fetch" in state["pending"]["argv"]:
                recorded_pid.append(state["pending"]["pid"])
            return record(kind, data, state)

        try:
            with patch("core.subprocess.Popen", side_effect=spawn), patch("core.remaining_timeout", side_effect=short_allowance), patch.object(self.task, "record", side_effect=observe_record):
                with self.assertRaisesRegex(Error, "Execution time exhausted"):
                    self.apply("run-start", role="verifier", actor="timeout-verifier")
            self.assertEqual(len(processes), 1)
            self.assertEqual(recorded_pid, [processes[0].pid])
            self.assertIsNotNone(processes[0].returncode)
            with self.assertRaises(ProcessLookupError):
                os.killpg(processes[0].pid, 0)
            state = Store(self.store.root).task(self.task.view()["id"]).load()
            self.assertEqual(state["runs"][-1]["status"], "interrupted")
            self.assertGreaterEqual(state["authorization"]["used_seconds"], 0.1)
            self.assertEqual(state["authorization"]["rounds_used"], 1)
            self.assertIsNone(state["pending"])
            self.assertTrue(any(event["kind"] == "checkout-failed" for event in self.task.events()))
        finally:
            for process in processes:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGKILL)
                process.wait()

    def test_legacy_start_pending_still_requires_investigation(self):
        state = self.task.load()
        state["pending"] = {"kind": "start"}
        self.task.record("legacy-start-fixture", {}, state)
        before = (self.repo / ".tasks/locator.json").read_bytes()
        self.apply("resume")
        self.assertEqual(self.task.view()["status"], "recovery")
        self.assertEqual(self.task.load()["pending"], {"kind": "start"})
        self.assertEqual((self.repo / ".tasks/locator.json").read_bytes(), before)

    def test_candidate_recovery_rejects_shallow_history_before_side_effects(self):
        git(self.repo, "switch", "main")
        (self.repo / "app.py").write_text("print('second baseline')\n")
        git(self.repo, "commit", "-am", "second baseline")
        repo = self.root / "history"
        git(self.root, "clone", "--quiet", "--branch=main", self.repo.as_uri(), str(repo))
        git(repo, "config", "user.email", "method@example.invalid")
        git(repo, "config", "user.name", "Method Test")
        self.repo = repo
        self.task = self.store.task(self.store.start({"workspace": str(repo), "target": "main", "title": "Recover capture"})["id"])
        self.prepare(); self.authorize()
        self.apply("run-start", role="implementer", actor="initial")
        run = self.task.current_run(self.task.load())
        (self.repo / "app.py").write_text("print('checkpoint')\n")
        self.apply("run-finish", run=run["id"], status="completed", processes_stopped=True, summary="Ready")
        with patch.object(self.task, "finish_candidate", side_effect=KeyboardInterrupt("Before checkpoint completion")):
            with self.assertRaises(KeyboardInterrupt):
                self.apply("candidate", paths=["app.py"])
        pending = self.task.load()["pending"]
        head = git(self.repo, "rev-parse", "HEAD")
        common = Path(git(self.repo, "rev-parse", "--path-format=absolute", "--git-common-dir"))
        (common / "shallow").write_text(head + "\n")
        before = self.task.view()
        refs = git(self.repo, "show-ref")
        with self.assertRaisesRegex(Error, "[Ss]hallow"):
            self.apply("resume")
        self.assertEqual(self.task.view(), before)
        self.assertEqual(git(self.repo, "show-ref"), refs)
        self.assertFalse((self.task.path / "candidates" / pending["id"]).exists())
        (common / "shallow").unlink()
        self.apply("resume")
        self.assertEqual(self.task.load()["candidates"][-1]["commit"], pending["commit"])
        self.apply("run-start", role="verifier", actor="recovery-verifier")
        self.assertEqual(self.task.view()["status"], "verifier")

    def test_verifier_bundle_validation_consumes_setup_budget(self):
        self.prepare(); self.authorize(minutes=1)
        candidate = self.implementation()
        clock = [time.time()]
        read_blob = self.task.read_blob
        def slow_bundle(reference, *args, **kwargs):
            if reference["path"] == candidate["bundle"]["path"]:
                self.assertEqual(self.task.current_run(self.task.load())["actor"], "bundle-verifier")
                clock[0] += 61
            return read_blob(reference, *args, **kwargs)
        with patch("core.time.time", side_effect=lambda: clock[0]), patch.object(self.task, "read_blob", side_effect=slow_bundle):
            with self.assertRaisesRegex(Error, "Execution time exhausted"):
                self.apply("run-start", role="verifier", actor="bundle-verifier")
        state = self.task.load()
        self.assertEqual(state["runs"][-1]["status"], "interrupted")
        self.assertGreaterEqual(state["authorization"]["used_seconds"], 61)
        self.assertEqual(state["authorization"]["rounds_used"], 1)
        self.assertFalse(Path(state["runs"][-1]["workspace"]).exists())
        self.assertEqual(self.task.view()["status"], "limit")

    def test_verifier_setup_record_interruption_stops_owned_process(self):
        self.prepare(); self.authorize(); self.implementation()
        processes = []
        popen = subprocess.Popen
        record = self.task.record
        def spawn(argv, **kwargs):
            if argv[:1] == ["git"] and "fetch" in argv:
                process = popen([sys.executable, "-c", "import time; time.sleep(30)"], **kwargs)
                processes.append(process)
                return process
            return popen(argv, **kwargs)
        def interrupt_record(kind, data, state):
            record(kind, data, state)
            if kind == "checkout-command-started" and "fetch" in state["pending"]["argv"]:
                raise KeyboardInterrupt("Interrupted after process registration")
        try:
            with patch("core.subprocess.Popen", side_effect=spawn), patch.object(self.task, "record", side_effect=interrupt_record):
                with self.assertRaises(KeyboardInterrupt):
                    self.apply("run-start", role="verifier", actor="registered-verifier")
            self.assertEqual(len(processes), 1)
            self.assertIsNotNone(processes[0].returncode)
            with self.assertRaises(ProcessLookupError):
                os.killpg(processes[0].pid, 0)
            state = Store(self.store.root).task(self.task.view()["id"]).load()
            self.assertEqual(state["pending"]["pid"], processes[0].pid)
            self.assertEqual(self.task.current_run(state)["actor"], "registered-verifier")
            self.assertEqual(state["authorization"]["rounds_used"], 1)
            self.assertEqual(self.task.view()["status"], "recovery")
        finally:
            for process in processes:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGKILL)
                process.wait()

    def test_start_rollback_interruption_retains_publication_checkpoint(self):
        self.delivered_task()
        locator = self.repo / ".tasks/locator.json"
        previous = locator.read_bytes()
        previous_view = self.task.view()
        git(self.repo, "switch", "main")
        known = {t["id"] for t in self.store.list()}
        record = Task.record
        def fail_final_record(task, kind, data, state):
            record(task, kind, data, state)
            if kind == "started":
                raise OSError("Final record persisted before failure")
        def interrupt_rollback(path, data):
            atomic(path, data)
            if Path(path).resolve() == locator.resolve() and data == previous:
                raise KeyboardInterrupt("Interrupted after locator rollback")
        payload = {"workspace": str(self.repo), "target": "main", "title": "Recover rollback"}
        with patch("core.Task.record", new=fail_final_record), patch("core.atomic", side_effect=interrupt_rollback):
            with self.assertRaises(KeyboardInterrupt):
                self.store.start(payload)
        created = [t for t in self.store.list() if t["id"] not in known]
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0]["status"], "recovery")
        self.assertEqual(locator.read_bytes(), previous)
        self.assertEqual(self.task.view(), previous_view)
        with self.assertRaises(Error):
            self.store.start(payload)
        task = Store(self.store.root).task(created[0]["id"])
        task.apply("resume", {})
        self.assertEqual(task.view()["status"], "interview")
        self.assertEqual(json.loads(locator.read_bytes())["task"], created[0]["id"])

    def test_verifier_setup_cleanup_failure_requires_process_reconciliation(self):
        self.prepare(); self.authorize(); self.implementation()
        processes = []
        popen = subprocess.Popen
        killpg = os.killpg
        def spawn(argv, **kwargs):
            if argv[:1] == ["git"] and "fetch" in argv:
                process = popen([sys.executable, "-c", "import time; time.sleep(30)"], **kwargs)
                processes.append(process)
                return process
            return popen(argv, **kwargs)
        def refuse_cleanup(pid, sig):
            if processes and pid == processes[0].pid and sig == signal.SIGKILL:
                raise PermissionError("Fixture: cannot stop owned process")
            return killpg(pid, sig)
        try:
            with patch("core.subprocess.Popen", side_effect=spawn), patch("core.remaining_timeout", return_value=0.1), patch("core.os.killpg", side_effect=refuse_cleanup):
                with self.assertRaises((Error, OSError)):
                    self.apply("run-start", role="verifier", actor="cleanup-verifier")
            self.assertEqual(len(processes), 1)
            self.assertIsNone(processes[0].poll())
            state = Store(self.store.root).task(self.task.view()["id"]).load()
            self.assertEqual(self.task.view()["status"], "recovery")
            run = self.task.current_run(state)
            self.assertIsNotNone(run)
            self.assertEqual(run["actor"], "cleanup-verifier")
            self.assertEqual(state["pending"]["pid"], processes[0].pid)
            with self.assertRaises(Error):
                self.apply("run-start", role="verifier", actor="must-wait")
        finally:
            for process in processes:
                if process.poll() is None:
                    killpg(process.pid, signal.SIGKILL)
                process.wait()
        state = self.task.load()
        run = self.task.current_run(state)
        self.apply("resolve", instruction="Fixture: confirmed process cleanup", resolution="Stopped and reaped the recorded process", processes_stopped=True)
        self.apply("run-finish", run=run["id"], status="interrupted", summary="Cleanup reconciled", processes_stopped=True)
        self.apply("resume", resolution="Setup processes reconciled")
        self.apply("run-start", role="verifier", actor="fresh-after-cleanup")
        self.assertEqual(self.task.load()["authorization"]["rounds_used"], 2)

    def test_blocker_freezes_progress_until_explicit_resume(self):
        self.prepare(); self.authorize()
        self.apply("run-start", role="implementer", actor="blocker-fixture")
        run = self.task.current_run(self.task.load())
        (self.repo / "app.py").write_text("print('changed')\n")
        self.apply("run-finish", run=run["id"], status="completed", summary="Ready", processes_stopped=True)
        self.apply("block", reason="Investigate before capturing")
        before = self.task.load()
        events = self.task.events()
        head = git(self.repo, "rev-parse", "HEAD")
        index = git(self.repo, "write-tree")
        for command in ("submit", "decide", "authorize", "run-start", "command", "evidence", "verify", "accept", "delivery", "candidate"):
            with self.subTest(command=command):
                with self.assertRaisesRegex(Error, "Task is blocked"):
                    self.apply(command, paths=["app.py"])
                self.assertEqual(self.task.load(), before)
                self.assertEqual(self.task.events(), events)
                self.assertEqual(git(self.repo, "rev-parse", "HEAD"), head)
                self.assertEqual(git(self.repo, "write-tree"), index)
        for resolution in (None, "", "   "):
            with self.assertRaisesRegex(Error, "resolving the blocker"):
                self.apply("resume", resolution=resolution)
        self.assertEqual(self.task.view()["status"], "blocked")
        self.assertEqual(self.store.list()[0]["status"], "blocked")
        context = self.root / "context.md"
        context.write_text("Investigation notes")
        self.apply("import", file=str(context), source="Fixture investigation")
        self.apply("block", reason="Updated investigation")
        self.apply("pause", instruction="Pause the fixture")
        self.apply("resume", resolution="Investigation complete")
        self.assertEqual(self.task.load()["authorization"], before["authorization"])
        self.apply("candidate", paths=["app.py"])
        self.verification()
        candidate = self.task.load()["candidates"][-1]
        acceptance = dict(candidate=candidate["commit"], requirements=self.task.snapshot(self.task.load())["requirements"], instruction="Accept fixture", observations={})
        self.apply("block", reason="Investigate before acceptance")
        with self.assertRaisesRegex(Error, "Task is blocked"):
            self.apply("accept", **acceptance)
        self.assertIsNone(self.task.load()["accepted"])
        self.apply("resume", resolution="Acceptance investigation complete")
        self.apply("accept", **acceptance)
        self.apply("block", reason="Investigate delivery")
        with self.assertRaisesRegex(Error, "Task is blocked"):
            self.apply("delivery", candidate=candidate["commit"], target="main", result_commit=candidate["commit"], mode="human_confirmed", candidate_unchanged=True, evidence="Fixture confirmation", instruction="Delivered fixture")
        self.assertIsNone(self.task.load()["delivery"])

    def test_blocked_checkpoint_resume_checks_resolution_before_git_changes(self):
        self.prepare(); self.authorize()
        with patch.object(self.task, "finish_candidate", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.implementation()
        state = self.task.load()
        state["blocker"] = "Investigate interrupted capture"
        self.task.record("blocked-recovery-fixture", {}, state)
        head = git(self.repo, "rev-parse", "HEAD")
        events = self.task.events()
        with self.assertRaisesRegex(Error, "resolving the blocker"):
            self.apply("resume")
        self.assertEqual(git(self.repo, "rev-parse", "HEAD"), head)
        self.assertEqual(self.task.events(), events)
        with patch.object(self.task, "assert_workspace", side_effect=Error("Workspace unavailable")):
            with self.assertRaisesRegex(Error, "Workspace unavailable"):
                self.apply("resume", resolution="Investigated")
        self.assertEqual(self.task.load(), state)
        self.apply("resume", resolution="Workspace reconciled")
        self.assertIsNone(self.task.load()["blocker"])
        self.assertEqual(git(self.repo, "rev-parse", "HEAD"), state["pending"]["commit"])
        self.assertEqual(self.task.load()["authorization"]["used_seconds"], state["authorization"]["used_seconds"])

    def test_blocked_run_can_only_finish_as_interrupted_or_blocked(self):
        self.prepare(); self.authorize()
        for verdict in ("interrupted", "blocked"):
            self.apply("run-start", role="implementer", actor="recovery-" + verdict)
            state = self.task.load()
            state["blocker"] = "Recovery fixture"
            self.task.record("blocked-active-fixture", {}, state)
            run = self.task.current_run(state)
            with self.assertRaisesRegex(Error, "Task is blocked"):
                self.apply("run-finish", run=run["id"], status="completed", summary="Cannot complete", processes_stopped=True)
            self.apply("run-finish", run=run["id"], status=verdict, summary="Reconciled owned work", processes_stopped=True)
            self.assertEqual(self.task.view()["status"], "blocked")
            self.apply("resume", resolution="Processes reconciled")

    def test_blocked_unknown_operation_allows_inspection_and_resolution(self):
        state = self.task.load()
        state.update(blocker="Inspect uncertain operation", pending={"kind": "command", "pid": None})
        self.task.record("blocked-pending-fixture", {}, state)
        self.apply("resume")
        self.assertEqual(self.task.load(), state)
        self.assertEqual(self.task.events()[-1]["data"]["observation"], state["pending"])
        self.apply("resolve", instruction="Resolve fixture", resolution="No process started", processes_stopped=True)
        self.assertIsNone(self.task.load()["pending"])
        self.assertTrue(self.task.load()["blocker"])
        self.apply("resume", resolution="Investigation complete")
        self.assertIsNone(self.task.load()["blocker"])

    def test_verifier_setup_deadline_survives_blocked_recording(self):
        self.prepare(); self.authorize(); self.implementation()
        processes = []
        popen, record = subprocess.Popen, self.task.record
        marker = self.root / "setup-after-deadline"
        def spawn(argv, **kwargs):
            if argv[:1] == ["git"] and "fetch" in argv:
                process = popen([sys.executable, "-c", "import pathlib, sys, time; time.sleep(0.4); pathlib.Path(sys.argv[1]).touch(); time.sleep(30)", str(marker)], **kwargs)
                processes.append(process)
                return process
            return popen(argv, **kwargs)
        def delayed(kind, data, state):
            if kind == "checkout-command-started" and "fetch" in state["pending"]["argv"]:
                time.sleep(0.8)
                self.assertFalse(marker.exists())
                self.assertIsNotNone(processes[0].returncode)
                with self.assertRaises(ProcessLookupError):
                    os.killpg(processes[0].pid, 0)
            return record(kind, data, state)
        try:
            with patch("core.subprocess.Popen", side_effect=spawn), patch("core.remaining_timeout", return_value=0.15), patch.object(self.task, "record", side_effect=delayed):
                with self.assertRaisesRegex(Error, "Execution time exhausted"):
                    self.apply("run-start", role="verifier", actor="delayed-setup")
            state = self.task.load()
            self.assertEqual(state["runs"][-1]["status"], "interrupted")
            self.assertEqual(state["authorization"]["rounds_used"], 1)
            self.assertGreaterEqual(state["authorization"]["used_seconds"], 0.8)
            self.assertIsNone(state["pending"])
        finally:
            for process in processes:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGKILL)
                process.wait()

    def test_timed_git_preserves_output_during_delayed_recording(self):
        for raw in (False, True):
            with self.subTest(raw=raw):
                payload = "x" * 200000 + "\n"
                if raw:
                    payload = payload.encode()
                expected = git(self.repo, "hash-object", "-w", "--stdin", input=payload, raw=raw)
                observed = git(self.repo, "hash-object", "--stdin", input=payload, raw=raw,
                               timeout=0.2, started=lambda process: time.sleep(0.5))
                self.assertEqual(observed, expected)
                blob = expected.decode().strip() if raw else expected
                large = git(self.repo, "cat-file", "-p", blob, raw=raw,
                            timeout=0.2, started=lambda process: time.sleep(0.5))
                self.assertEqual(large, payload if raw else payload.strip())
        with self.assertRaisesRegex(Error, "[Nn]ot a valid"):
            git(self.repo, "cat-file", "-p", "nonexistent-fixture-object", timeout=1)

    def test_verifier_setup_record_failure_stops_monitor_and_process(self):
        self.prepare(); self.authorize(); self.implementation()
        processes = []
        popen, record = subprocess.Popen, self.task.record
        def spawn(argv, **kwargs):
            if argv[:1] == ["git"] and "fetch" in argv:
                process = popen([sys.executable, "-c", "import time; time.sleep(30)"], **kwargs)
                processes.append(process)
                return process
            return popen(argv, **kwargs)
        def fail_record(kind, data, state):
            if kind == "checkout-command-started" and "fetch" in state["pending"]["argv"]:
                raise OSError("Fixture recording failure")
            return record(kind, data, state)
        try:
            with patch("core.subprocess.Popen", side_effect=spawn), patch.object(self.task, "record", side_effect=fail_record):
                with self.assertRaisesRegex(OSError, "Fixture recording failure"):
                    self.apply("run-start", role="verifier", actor="failed-recording")
            self.assertIsNotNone(processes[0].returncode)
            with self.assertRaises(ProcessLookupError):
                os.killpg(processes[0].pid, 0)
            self.assertFalse(any(thread.name == "method-git" for thread in threading.enumerate()))
            state = self.task.load()
            self.assertEqual(state["runs"][-1]["status"], "interrupted")
            self.assertEqual(state["authorization"]["rounds_used"], 1)
            self.assertIsNone(state["pending"])
        finally:
            for process in processes:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGKILL)
                process.wait()

    def test_dirty_source_is_preserved(self):
        (self.repo / "app.py").write_text("uncommitted work")
        before = git(self.repo, "status", "--porcelain")
        with self.assertRaises(Error):
            self.store.start({"workspace": str(self.repo), "target": "main", "title": "Another"})
        self.assertEqual(git(self.repo, "status", "--porcelain"), before)
        self.assertEqual((self.repo / "app.py").read_text(), "uncommitted work")

    def test_revision_change_invalidates_downstream_and_execution(self):
        self.prepare()
        self.authorize()
        old = self.task.snapshot(self.task.load())
        self.apply("submit", stage="requirements", file=str(self.root / "requirements.md"), criteria=[{"id": "R01", "text": "Different greeting"}])
        state = self.task.load()
        self.assertEqual(set(state["approved"]), {"interview", "exploration"})
        self.assertIsNone(state["authorization"])
        with self.assertRaises(Error):
            self.apply("authorize", revisions=old, instruction="Use old revisions")
        artifact = self.task.latest(state, "requirements")
        with self.assertRaises(Error):
            self.apply("decide", stage="requirements", revision=artifact["revision"] - 1, sha256=artifact["sha256"], decision="approved", instruction="Approve")

    def test_waivers_and_rejections_are_retained(self):
        for stage in ("interview", "exploration"):
            self.apply("decide", stage=stage, decision="skipped", reason="Already established in the supplied brief", instruction="Skip this stage for that reason")
        with self.assertRaises(Error):
            self.apply("decide", stage="requirements", decision="skipped", reason="small", instruction="Skip")
        path = self.root / "requirements.md"
        path.write_text("# Requirements")
        self.apply("submit", stage="requirements", file=str(path), criteria=[{"id": "R1", "text": "Work"}])
        artifact = self.task.latest(self.task.load(), "requirements")
        self.apply("decide", stage="requirements", decision="rejected", revision=1, sha256=artifact["sha256"], instruction="Needs failure behavior")
        self.assertEqual(self.task.view()["status"], "requirements")
        self.assertIn("Needs failure behavior", json.dumps(self.task.events()))

    def test_independence_and_evidence_are_required(self):
        self.prepare()
        self.authorize()
        self.implementation()
        with self.assertRaises(Error):
            self.apply("run-start", role="verifier", actor="implementer-1")
        self.apply("run-start", role="verifier", actor="verifier")
        run = self.task.current_run(self.task.load())
        with self.assertRaises(Error):
            self.apply("verify", run=run["id"], processes_stopped=True, results=[{"id": "V01", "outcome": "pass", "observed": "Trust me", "evidence": []}], findings=[], review="Good", launch="Run", tradeoffs="None")
        self.assertEqual(self.task.current_run(self.task.load())["status"], "running")

    def test_verifier_identity_must_be_fresh_across_rounds_and_authorizations(self):
        self.prepare(); self.authorize()
        self.implementation()
        self.verification(outcome="fail", actor="used-verifier")
        self.implementation()
        before = self.task.view()
        workspaces = sorted((self.task.path / "runs").glob("*/workspace"))
        with self.assertRaisesRegex(Error, "fresh"):
            self.apply("run-start", role="verifier", actor="used-verifier")
        self.assertEqual(self.task.view(), before)
        self.assertEqual(sorted((self.task.path / "runs").glob("*/workspace")), workspaces)
        self.verification(actor="second-verifier")
        self.authorize(mode="evidence")
        before = self.task.view()
        for actor in ("used-verifier", "second-verifier"):
            with self.subTest(actor=actor), self.assertRaisesRegex(Error, "fresh"):
                self.apply("run-start", role="verifier", actor=actor)
            self.assertEqual(self.task.view(), before)
        self.apply("run-start", role="verifier", actor="interrupted-verifier")
        run = self.task.current_run(self.task.load())
        self.apply("run-finish", run=run["id"], status="interrupted",
                   summary="Fixture: verifier stopped before reporting.", processes_stopped=True)
        before = self.task.view()
        with self.assertRaisesRegex(Error, "fresh"):
            self.apply("run-start", role="verifier", actor="interrupted-verifier")
        self.assertEqual(self.task.view(), before)
        self.verification(actor="fresh-verifier")
        self.assertEqual(self.task.view()["status"], "human_review")

    def test_existing_active_verifier_identity_can_be_reconciled(self):
        self.prepare(); self.authorize()
        self.implementation()
        self.verification(outcome="fail", actor="legacy-verifier")
        self.implementation()
        self.apply("run-start", role="verifier", actor="new-verifier")
        state = self.task.load()
        run = self.task.current_run(state)
        run["actor"] = "legacy-verifier"
        self.task.record("legacy-active-verifier-fixture", {}, state)
        history = copy.deepcopy(state["runs"][:-1])
        self.apply("run-finish", run=run["id"], status="interrupted",
                   summary="Reconciled a verifier registered before the freshness guard.", processes_stopped=True)
        self.apply("resume")
        self.assertEqual(self.task.load()["runs"][:-1], history)
        self.assertEqual(self.task.load()["runs"][-1]["actor"], "legacy-verifier")
        self.assertEqual(self.task.load()["runs"][-1]["status"], "interrupted")
        self.verification(actor="fresh-verifier")
        self.assertEqual(self.task.view()["status"], "human_review")

    def test_verifier_cannot_change_source(self):
        self.prepare(); self.authorize(); self.implementation()
        self.apply("run-start", role="verifier", actor="v")
        run = self.task.current_run(self.task.load())
        (Path(run["workspace"]) / "app.py").write_text("changed")
        with self.assertRaisesRegex(Error, "changed candidate"):
            self.apply("verify", run=run["id"], processes_stopped=True)

    def test_failure_fix_and_new_candidate_preserve_old_evidence(self):
        self.prepare(); self.authorize()
        first = self.implementation()
        self.verification(outcome="fail", findings=[{"id": "F1", "description": "Wrong greeting", "severity": "blocking", "status": "open"}])
        self.assertEqual(self.task.view()["status"], "implementer")
        second = self.implementation()
        self.assertNotEqual(first["commit"], second["commit"])
        self.verification(actor="verifier-2", findings=[{"id": "F1", "description": "Wrong greeting", "severity": "blocking", "status": "resolved", "resolution": "Fresh CLI output demonstrates corrected behavior"}])
        state = self.task.load()
        self.assertEqual(state["candidates"][0]["verification"]["results"][0]["outcome"], "fail")
        self.assertEqual(state["candidates"][1]["verification"]["results"][0]["outcome"], "pass")

    def test_evidence_request_reuses_candidate_and_correction_requires_new_one(self):
        self.prepare(); self.authorize()
        candidate = self.implementation(); self.verification()
        self.authorize(mode="evidence")
        with self.assertRaises(Error):
            self.apply("run-start", role="implementer", actor="new-i")
        self.verification(actor="new-v")
        self.assertEqual(self.task.load()["candidates"][-1]["commit"], candidate["commit"])
        self.authorize()
        self.assertEqual(self.task.view()["status"], "implementer")
        with self.assertRaises(Error):
            self.apply("run-start", role="verifier", actor="another-v")

    def test_interrupted_corrections_require_their_own_candidate(self):
        self.prepare(); self.authorize(); self.implementation(); self.verification()
        for edit in (False, True):
            with self.subTest(edit=edit):
                previous = self.task.load()["candidates"][-1]
                self.authorize()
                authorization = self.task.load()["authorization"]["id"]
                self.apply("run-start", role="implementer", actor="correction")
                run = self.task.current_run(self.task.load())
                if edit:
                    (self.repo / "app.py").write_text("print('corrected greeting')\n")
                work = (self.repo / "app.py").read_bytes()
                self.apply("run-finish", run=run["id"], status="interrupted",
                           processes_stopped=True, summary="Stopped correction; preserved work.")
                used = self.task.load()["authorization"]["used_seconds"]
                self.apply("resume")
                self.assertEqual(self.task.view()["status"], "implementer")
                self.assertTrue(self.task.view()["state"]["authorization"]["needs_implementation"])
                self.assertEqual((self.repo / "app.py").read_bytes(), work)
                with self.assertRaises(Error):
                    self.apply("run-start", role="verifier", actor="premature-verifier")
                with self.assertRaises(Error):
                    self.apply("accept", candidate=previous["commit"],
                               requirements=self.task.snapshot(self.task.load())["requirements"],
                               instruction="Accept the presented candidate.", observations={})

                self.apply("run-start", role="implementer", actor="correction")
                run = self.task.current_run(self.task.load())
                self.apply("run-finish", run=run["id"], status="completed",
                           processes_stopped=True, summary="Correction complete.")
                self.assertEqual(self.task.view()["status"], "candidate")
                with self.assertRaises(Error):
                    self.apply("run-start", role="verifier", actor="premature-verifier")
                self.apply("candidate", paths=["app.py"] if edit else [])
                state = self.task.load()
                self.assertNotEqual(state["candidates"][-1]["commit"], previous["commit"])
                self.assertEqual(state["authorization"]["id"], authorization)
                self.assertEqual(state["authorization"]["rounds_used"], 0)
                self.assertGreaterEqual(state["authorization"]["used_seconds"], used)
                self.assertFalse(self.task.view()["state"]["authorization"]["needs_implementation"])
                self.verification(actor="verifier-" + str(edit))
                candidate = self.task.load()["candidates"][-1]
                self.apply("accept", candidate=candidate["commit"],
                           requirements=self.task.snapshot(self.task.load())["requirements"],
                           instruction="Accept the corrected candidate.", observations={})
                self.assertEqual(self.task.view()["status"], "delivery")

    def test_legacy_correction_flags_do_not_unlock_old_candidates(self):
        self.prepare(); self.authorize(); self.implementation(); self.verification()
        self.authorize()
        for completion, expected in (("interrupted", "implementer"), ("completed", "candidate")):
            with self.subTest(completion=completion):
                self.apply("run-start", role="implementer", actor="correction")
                run = self.task.current_run(self.task.load())
                self.apply("run-finish", run=run["id"], status=completion,
                           processes_stopped=True, summary="Legacy correction fixture.")
                state = self.task.load()
                state["authorization"]["needs_implementation"] = False
                self.task.record("legacy-early-cleared-flag", {}, state)
                events = self.task.events()
                fresh = Store(self.store.root).task(state["task"]["id"])
                view = fresh.view()
                self.assertEqual(view["status"], expected)
                self.assertTrue(view["state"]["authorization"]["needs_implementation"])
                self.assertEqual(fresh.events(), events)
                with self.assertRaises(Error):
                    fresh.apply("run-start", {"role": "verifier", "actor": "premature-verifier"})
        self.apply("candidate", paths=[])
        self.assertEqual(self.task.view()["status"], "verifier")

    def test_legacy_active_verifier_cannot_finish_an_uncaptured_correction(self):
        self.prepare(); self.authorize(); self.implementation(); self.verification()
        self.authorize()
        self.apply("run-start", role="implementer", actor="correction")
        run = self.task.current_run(self.task.load())
        self.apply("run-finish", run=run["id"], status="interrupted",
                   processes_stopped=True, summary="Legacy interrupted correction.")
        with patch.object(self.task, "needs_candidate", return_value=False):
            self.apply("run-start", role="verifier", actor="legacy-premature-verifier")
        run = self.task.current_run(self.task.load())
        with self.assertRaisesRegex(Error, "Capture the authorized implementation"):
            self.apply("verify", run=run["id"], processes_stopped=True)
        self.apply("run-finish", run=run["id"], status="interrupted",
                   processes_stopped=True, summary="Reconciled stale verifier after upgrade.")
        self.assertEqual(self.task.view()["status"], "implementer")
        self.apply("run-start", role="implementer", actor="correction")

    def test_legacy_completed_correction_can_capture_after_stale_verifier(self):
        self.prepare(); self.authorize(); self.implementation(); self.verification()
        self.authorize()
        authorization = self.task.load()["authorization"]["id"]
        self.apply("run-start", role="implementer", actor="correction")
        implementation = self.task.current_run(self.task.load())
        self.apply("run-finish", run=implementation["id"], status="completed",
                   processes_stopped=True, summary="Legacy completed correction.")
        with patch.object(self.task, "needs_candidate", return_value=False):
            self.apply("run-start", role="verifier", actor="legacy-premature-verifier")
        run = self.task.current_run(self.task.load())
        self.apply("run-finish", run=run["id"], status="interrupted",
                   processes_stopped=True, summary="Reconciled stale verifier.")
        self.assertEqual(self.task.view()["status"], "candidate")
        self.apply("candidate", paths=[])
        state = self.task.load()
        self.assertEqual(state["candidates"][-1]["run"], implementation["id"])
        self.assertEqual(state["authorization"]["id"], authorization)
        self.assertEqual(state["authorization"]["rounds_used"], 1)
        self.verification(actor="fresh-verifier")
        self.assertEqual(self.task.view()["status"], "human_review")

    def test_stale_verifier_reconciliation_preserves_exhausted_round_limit(self):
        self.prepare(); self.authorize(); self.implementation(); self.verification()
        self.authorize(rounds=1)
        self.apply("run-start", role="implementer", actor="correction")
        run = self.task.current_run(self.task.load())
        self.apply("run-finish", run=run["id"], status="interrupted",
                   processes_stopped=True, summary="Legacy interrupted correction.")
        with patch.object(self.task, "needs_candidate", return_value=False):
            self.apply("run-start", role="verifier", actor="legacy-premature-verifier")
        run = self.task.current_run(self.task.load())
        self.apply("run-finish", run=run["id"], status="interrupted",
                   processes_stopped=True, summary="Reconciled stale verifier.")
        self.assertEqual(self.task.view()["status"], "limit")
        with self.assertRaisesRegex(Error, "round limit"):
            self.apply("run-start", role="implementer", actor="correction")

    def test_candidate_must_belong_to_current_authorization(self):
        self.prepare(); self.authorize()
        self.apply("run-start", role="implementer", actor="old-implementer")
        run = self.task.current_run(self.task.load())
        self.apply("run-finish", run=run["id"], status="completed",
                   processes_stopped=True, summary="Uncaptured implementation.")
        self.authorize()
        with self.assertRaises(Error):
            self.apply("candidate", paths=[])
        self.assertEqual(self.task.view()["status"], "implementer")
        self.implementation(actor="new-implementer")
        self.assertEqual(self.task.view()["status"], "verifier")

    def test_nonready_evidence_reports_request_authorization(self):
        self.prepare(); self.authorize()
        candidate = self.implementation(); self.verification()
        cases = [("fail", []), ("unverified", []), ("pass", [
            {"id": "F01", "description": "Required behavior is blocked.",
             "severity": "blocking", "status": "open"}])]
        for outcome, findings in cases:
            with self.subTest(outcome=outcome):
                self.authorize(mode="evidence")
                authorization = self.task.load()["authorization"]["id"]
                self.verification(outcome=outcome, findings=findings, actor="evidence-" + outcome)
                view = self.task.view()
                self.assertEqual(view["status"], "authorization")
                self.assertIn("evidence", view["next_action"])
                self.assertIn("implementation", view["next_action"])
                self.assertEqual(view["state"]["candidates"][-1]["commit"], candidate["commit"])
                self.assertEqual(view["state"]["authorization"]["id"], authorization)
                self.assertEqual(view["state"]["authorization"]["rounds_used"], 1)
                self.assertEqual(view["state"]["runs"][-1]["report"]["results"][0]["outcome"], outcome)
                for role in ("implementer", "verifier"):
                    with self.assertRaises(Error):
                        self.apply("run-start", role=role, actor="unauthorized-" + role)
        self.authorize(mode="evidence")
        self.verification(actor="approved-evidence", findings=[
            {"id": "F01", "description": "Required behavior is blocked.",
             "severity": "blocking", "status": "resolved", "resolution": "Additional evidence resolves it."}])
        self.assertEqual(self.task.view()["status"], "human_review")
        self.assertEqual(self.task.load()["candidates"][-1]["commit"], candidate["commit"])

    def test_finished_evidence_reports_keep_decisions_when_finalization_crosses_limit(self):
        self.prepare(); self.authorize(); self.implementation(); self.verification()
        for outcome, expected in (("pass", "human_review"), ("fail", "authorization")):
            with self.subTest(outcome=outcome):
                self.authorize(mode="evidence", minutes=1)
                self.apply("run-start", role="verifier", actor="boundary-" + outcome)
                run = self.task.current_run(self.task.load())
                self.apply("command", run=run["id"], argv=[sys.executable, "app.py"], safe_to_record=True)
                run = self.task.current_run(self.task.load())
                with patch("core.time.time", side_effect=[run["started_epoch"] + 59.9, run["started_epoch"] + 60.1]):
                    self.apply("verify", run=run["id"], processes_stopped=True,
                               results=[{"id": "V01", "outcome": outcome, "observed": "Actual CLI output.",
                                         "evidence": [run["evidence"][0]["id"]]}],
                               findings=[], review="Reviewed the diff.", launch="python3 app.py", tradeoffs="Existing CLI.")
                view = self.task.view()
                self.assertEqual(view["status"], expected)
                self.assertEqual(view["state"]["runs"][-1]["status"], "completed")
                self.assertGreater(view["state"]["authorization"]["used_seconds"], 60)

    def test_interrupted_evidence_run_preserves_retry_budget(self):
        self.prepare(); self.authorize(); self.implementation(); self.verification()
        self.authorize(mode="evidence")
        authorization = self.task.load()["authorization"]["id"]
        self.apply("run-start", role="verifier", actor="interrupted-evidence")
        run = self.task.current_run(self.task.load())
        self.assertEqual(self.task.view()["status"], "verifier")
        self.apply("run-finish", run=run["id"], status="interrupted",
                   processes_stopped=True, summary="Stopped before submitting a report.")
        used = self.task.load()["authorization"]["used_seconds"]
        self.apply("resume")
        self.assertEqual(self.task.view()["status"], "verifier")
        self.verification(actor="resumed-evidence")
        state = self.task.load()
        self.assertEqual(state["authorization"]["id"], authorization)
        self.assertEqual(state["authorization"]["rounds_used"], 2)
        self.assertGreaterEqual(state["authorization"]["used_seconds"], used)
        self.assertEqual(self.task.view()["status"], "human_review")

    def test_limits_survive_resume(self):
        self.prepare(); self.authorize(rounds=1); self.implementation(); self.verification(outcome="fail")
        self.apply("resume")
        self.assertEqual(self.task.view()["status"], "limit")
        with self.assertRaises(Error):
            self.apply("run-start", role="implementer", actor="another-i")

    def test_command_deadline_expires_before_spawn(self):
        self.prepare(); self.authorize(minutes=1)
        self.apply("run-start", role="implementer", actor="deadline-fixture")
        run = self.task.current_run(self.task.load())
        record = self.task.record
        for boundary in ("authorization", "command"):
            with self.subTest(boundary=boundary):
                epoch = [run["started_epoch"] + 1]
                monotonic = [time.monotonic()]
                def advance(kind, data, state):
                    result = record(kind, data, state)
                    if kind == "command-intent":
                        if boundary == "authorization":
                            epoch[0] = run["started_epoch"] + 61
                        else:
                            monotonic[0] += 2
                    return result
                with patch("core.time.time", side_effect=lambda: epoch[0]), \
                     patch("core.time.monotonic", side_effect=lambda: monotonic[0]), \
                     patch.object(self.task, "record", side_effect=advance), \
                     patch("core.subprocess.Popen", wraps=subprocess.Popen) as spawn:
                    with self.assertRaisesRegex(Error, "exhausted"):
                        self.apply("command", run=run["id"], argv=[sys.executable, "-c", "print('must not run')"],
                                   timeout=1, safe_to_record=True)
                    spawn.assert_not_called()
                state = Store(self.store.root).task(self.task.path.name).load()
                self.assertIsNone(state["pending"])
                self.assertEqual(self.task.current_run(state)["id"], run["id"])
                self.assertEqual(self.task.current_run(state)["evidence"], [])
                self.assertEqual(self.task.events()[-1]["kind"], "command-not-started")

    def test_command_monitor_stops_process_while_recording_is_blocked(self):
        self.prepare(); self.authorize()
        self.apply("run-start", role="implementer", actor="blocked-record-fixture")
        run = self.task.current_run(self.task.load())
        marker = self.root / "after-deadline"
        record = self.task.record
        observed = {}
        def delayed(kind, data, state):
            if kind == "command-started":
                time.sleep(0.7)
                observed["late_effect"] = marker.exists()
                observed["stopped"] = False
                try:
                    os.killpg(state["pending"]["pid"], 0)
                except ProcessLookupError:
                    observed["stopped"] = True
                except PermissionError:
                    pass
            return record(kind, data, state)
        with patch.object(self.task, "record", side_effect=delayed):
            self.apply("command", run=run["id"], timeout=0.1, safe_to_record=True,
                       argv=[sys.executable, "-c",
                             "import pathlib, sys, time; time.sleep(0.3); pathlib.Path(sys.argv[1]).write_text('too late')",
                             str(marker)])
        self.assertFalse(observed["late_effect"], "The command must stop before its post-deadline side effect")
        self.assertTrue(observed["stopped"], "The process group must be stopped and reaped while recording is blocked")
        state = Store(self.store.root).task(self.task.path.name).load()
        evidence = state["runs"][-1]["evidence"][-1]
        self.assertTrue(evidence["timeout"])
        self.assertEqual(evidence["exit_code"], -signal.SIGKILL)
        self.assertIsNone(state["pending"])

    def test_fast_command_is_not_timed_out_by_delayed_recording(self):
        self.prepare(); self.authorize()
        self.apply("run-start", role="implementer", actor="fast-command-fixture")
        run = self.task.current_run(self.task.load())
        record = self.task.record
        def delayed(kind, data, state):
            if kind == "command-started":
                time.sleep(0.6)
            return record(kind, data, state)
        with patch.object(self.task, "record", side_effect=delayed):
            self.apply("command", run=run["id"], timeout=0.3, safe_to_record=True,
                       argv=[sys.executable, "-c", "print('finished promptly')"])
        evidence = self.task.current_run(self.task.load())["evidence"][-1]
        self.assertFalse(evidence["timeout"])
        self.assertEqual(evidence["exit_code"], 0)
        self.assertIn(b"finished promptly", self.task.read_blob(evidence))

    def test_command_record_interruption_stops_monitor_and_process(self):
        self.prepare(); self.authorize()
        self.apply("run-start", role="implementer", actor="interrupted-command-fixture")
        run = self.task.current_run(self.task.load())
        record = self.task.record
        processes = []
        popen = subprocess.Popen
        def spawn(*args, **kwargs):
            process = popen(*args, **kwargs)
            processes.append(process)
            return process
        def interrupt(kind, data, state):
            result = record(kind, data, state)
            if kind == "command-started":
                raise KeyboardInterrupt("Fixture: interrupted recording")
            return result
        try:
            with patch("core.subprocess.Popen", side_effect=spawn), patch.object(self.task, "record", side_effect=interrupt):
                with self.assertRaises(KeyboardInterrupt):
                    self.apply("command", run=run["id"], safe_to_record=True,
                               argv=[sys.executable, "-c", "import time; time.sleep(30)"])
            self.assertIsNotNone(processes[0].returncode)
            with self.assertRaises(ProcessLookupError):
                os.killpg(processes[0].pid, 0)
            state = Store(self.store.root).task(self.task.path.name).load()
            self.assertEqual(state["pending"]["pid"], processes[0].pid)
            self.assertEqual(state["runs"][-1]["status"], "running")
            self.assertFalse(any(t.name.startswith("method-command-") for t in threading.enumerate()))
        finally:
            for process in processes:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGKILL)
                process.wait()

    def test_command_interrupted_join_waits_for_actual_cleanup(self):
        self.prepare(); self.authorize()
        self.apply("run-start", role="implementer", actor="join-interruption-fixture")
        run = self.task.current_run(self.task.load())
        processes, monitors = [], []
        popen, join, killpg = subprocess.Popen, threading.Thread.join, os.killpg
        interrupted = [False]
        def spawn(*args, **kwargs):
            process = popen(*args, **kwargs)
            processes.append(process)
            return process
        def interrupted_join(thread, *args, **kwargs):
            if thread.name.startswith("method-command-"):
                if thread not in monitors:
                    monitors.append(thread)
                if not interrupted[0]:
                    interrupted[0] = True
                    raise KeyboardInterrupt("Fixture: join now falsely reports a stopped thread")
                return None
            return join(thread, *args, **kwargs)
        def delayed_cleanup(pid, sig):
            if threading.current_thread().name.startswith("method-command-"):
                time.sleep(0.2)
            return killpg(pid, sig)
        try:
            with patch("core.subprocess.Popen", side_effect=spawn), \
                 patch("core.threading.Thread.join", new=interrupted_join), \
                 patch("core.os.killpg", side_effect=delayed_cleanup):
                with self.assertRaises(KeyboardInterrupt):
                    self.apply("command", run=run["id"], timeout=0.1, safe_to_record=True,
                               argv=[sys.executable, "-c", "import time; time.sleep(30)"])
                self.assertIsNotNone(processes[0].returncode, "Wait for real cleanup even when join becomes a no-op")
                with self.assertRaises(ProcessLookupError):
                    killpg(processes[0].pid, 0)
            self.assertTrue(interrupted[0])
            state = Store(self.store.root).task(self.task.path.name).load()
            self.assertEqual(state["pending"]["pid"], processes[0].pid)
            self.assertEqual(state["runs"][-1]["status"], "running")
        finally:
            for thread in monitors:
                join(thread, timeout=3)
            for process in processes:
                if process.poll() is None:
                    killpg(process.pid, signal.SIGKILL)
                process.wait()

    def test_cli_command_sigint_preserves_record_and_stops_process(self):
        self.prepare(); self.authorize()
        self.apply("run-start", role="implementer", actor="sigint-cli-fixture")
        run = self.task.current_run(self.task.load())
        payload = self.root / "command.json"
        payload.write_text(json.dumps({"run": run["id"], "timeout": 10, "safe_to_record": True,
                                       "argv": [sys.executable, "-c", "import time; time.sleep(30)"]}))
        code = ("import sys, threading, time; sys.path.insert(0, sys.argv[1]); import core, method; "
                "original = core.os.killpg; "
                "core.os.killpg = lambda pid, sig: (time.sleep(0.2) if threading.current_thread().name.startswith('method-command-') else None, original(pid, sig))[1]; "
                "sys.argv = ['method.py', *sys.argv[2:]]; sys.exit(method.main())")
        controller = subprocess.Popen([sys.executable, "-c", code, str(SCRIPTS), "--store", str(self.store.root),
                                       "command", "--task", self.task.path.name, "--input", str(payload)],
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
        owned_pid = None
        try:
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                pending = self.task.load()["pending"]
                if pending and pending.get("pid"):
                    owned_pid = pending["pid"]
                    break
                if controller.poll() is not None:
                    break
                time.sleep(0.01)
            self.assertIsNotNone(owned_pid, "The CLI must publish its owned process before interruption")
            time.sleep(0.05)
            controller.send_signal(signal.SIGINT)
            _, stderr = controller.communicate(timeout=5)
            self.assertNotEqual(controller.returncode, 0, stderr)
            self.assertIn("KeyboardInterrupt", stderr)
            with self.assertRaises(ProcessLookupError):
                os.killpg(owned_pid, 0)
            state = Store(self.store.root).task(self.task.path.name).load()
            self.assertEqual(state["pending"]["pid"], owned_pid)
            self.assertEqual(state["runs"][-1]["status"], "running")
        finally:
            if controller.poll() is None:
                os.killpg(controller.pid, signal.SIGKILL)
            controller.communicate()
            if owned_pid:
                try:
                    os.killpg(owned_pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass

    def test_command_cleanup_failure_keeps_recovery_state(self):
        self.prepare(); self.authorize()
        self.apply("run-start", role="implementer", actor="cleanup-command-fixture")
        run = self.task.current_run(self.task.load())
        processes = []
        popen, killpg = subprocess.Popen, os.killpg
        def spawn(*args, **kwargs):
            process = popen(*args, **kwargs)
            processes.append(process)
            return process
        def refuse(pid, sig):
            if processes and pid == processes[0].pid:
                raise PermissionError("Fixture: cleanup failed")
            return killpg(pid, sig)
        try:
            with patch("core.subprocess.Popen", side_effect=spawn), patch("core.os.killpg", side_effect=refuse):
                with self.assertRaises((Error, OSError)):
                    self.apply("command", run=run["id"], timeout=0.05, safe_to_record=True,
                               argv=[sys.executable, "-c", "import time; time.sleep(30)"])
            self.assertIsNone(processes[0].poll())
            state = Store(self.store.root).task(self.task.path.name).load()
            self.assertEqual(state["pending"]["pid"], processes[0].pid)
            self.assertEqual(state["runs"][-1]["status"], "running")
            self.assertEqual(self.task.view()["status"], "recovery")
            self.assertFalse(any(t.name.startswith("method-command-") for t in threading.enumerate()))
        finally:
            for process in processes:
                if process.poll() is None:
                    killpg(process.pid, signal.SIGKILL)
                process.wait()

    def test_command_timeout_is_retained(self):
        self.prepare(); self.authorize()
        self.apply("run-start", role="implementer", actor="i")
        run = self.task.current_run(self.task.load())
        self.apply("command", run=run["id"], argv=[sys.executable, "-c", "import time; time.sleep(5)"], timeout=0.05, safe_to_record=True)
        evidence = self.task.current_run(self.task.load())["evidence"][0]
        self.assertTrue(evidence["timeout"])
        self.assertNotEqual(evidence["exit_code"], 0)
        self.assertIsNone(self.task.load()["pending"])

    def test_command_record_failure_stops_owned_process(self):
        self.prepare(); self.authorize()
        for published in (False, True):
            with self.subTest(published=published):
                self.apply("run-start", role="implementer", actor="command-fixture")
                run = self.task.current_run(self.task.load())
                processes = []
                popen = subprocess.Popen
                record = self.task.record
                failure = OSError("Injected command-started recording failure")

                def capture_process(*args, **kwargs):
                    process = popen(*args, **kwargs)
                    processes.append(process)
                    return process

                def fail_record(kind, data, state):
                    if kind == "command-started":
                        if published:
                            record(kind, data, state)
                        raise failure
                    return record(kind, data, state)

                try:
                    with patch("core.subprocess.Popen", side_effect=capture_process), patch.object(self.task, "record", side_effect=fail_record):
                        with self.assertRaises(OSError) as raised:
                            self.apply("command", run=run["id"],
                                       argv=[sys.executable, "-c", "import time; time.sleep(30)"],
                                       timeout=0.05, safe_to_record=True)
                    self.assertIs(raised.exception, failure)
                    self.assertEqual(len(processes), 1)
                    self.assertIsNotNone(processes[0].returncode, "The command must be stopped and reaped before propagating the error")
                    with self.assertRaises(ProcessLookupError):
                        os.killpg(processes[0].pid, 0)
                    saved = Store(self.store.root).task(self.task.view()["id"]).load()
                    self.assertEqual(saved["pending"]["kind"], "command")
                    self.assertEqual(saved["pending"]["pid"], processes[0].pid if published else None)
                    self.assertEqual(self.task.current_run(saved)["id"], run["id"])
                finally:
                    for process in processes:
                        if process.poll() is None:
                            os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
                    if self.task.load()["pending"]:
                        self.apply("resolve", instruction="Fixture: reconcile the failed command.",
                                   resolution="The owned command process group has stopped.", processes_stopped=True)
                    self.apply("run-finish", run=run["id"], status="interrupted",
                               summary="Recording failed; the command has stopped.", processes_stopped=True)
                    self.apply("resume", resolution="Confirmed command cleanup; no source changes.")

    def test_history_and_candidate_survive_workspace_deletion(self):
        self.prepare(); self.authorize(); candidate = self.implementation()
        shutil.rmtree(self.repo)
        self.assertTrue(self.task.read_blob(candidate["bundle"]))
        self.apply("run-start", role="verifier", actor="v")
        run = self.task.current_run(self.task.load())
        self.assertEqual(git(run["workspace"], "rev-parse", "HEAD"), candidate["commit"])

    def test_cache_is_not_authoritative_and_lock_prevents_writers(self):
        (self.task.path / "state.json").write_text('{"status":"complete"}')
        self.assertEqual(self.task.view()["status"], "interview")
        with lock(self.task.path / "task.lock"):
            with self.assertRaises(Error):
                self.apply("block", reason="no capability")
        self.apply("block", reason="Independent agents unavailable")
        self.assertEqual(self.task.view()["status"], "blocked")

    def test_unknown_operation_is_not_repeated(self):
        state = self.task.load()
        state["pending"] = {"kind": "command", "argv": ["must-not-run"], "pid": None}
        self.task.record("command-intent", {}, state)
        self.apply("resume")
        self.assertEqual(self.task.view()["status"], "recovery")
        with self.assertRaises(Error):
            self.apply("submit", stage="interview", file="missing")
        self.apply("resolve", instruction="I checked this operation", resolution="No process started", processes_stopped=True)
        self.assertEqual(self.task.view()["status"], "blocked")

    def test_known_checkpoint_recovery_does_not_duplicate_commit(self):
        self.prepare(); self.authorize()
        self.apply("run-start", role="implementer", actor="i")
        run = self.task.current_run(self.task.load())
        self.apply("run-finish", run=run["id"], status="completed", summary="No changes; commands finished", processes_stopped=True)
        self.assertEqual(self.task.view()["status"], "candidate")
        authorization = copy.deepcopy(self.task.load()["authorization"])
        original = self.task.finish_candidate
        self.task.finish_candidate = lambda state: (_ for _ in ()).throw(OSError("simulated crash"))
        with self.assertRaises(OSError):
            self.apply("candidate", paths=[])
        commit = self.task.load()["pending"]["commit"]
        with self.assertRaises(Error):
            self.store.start({"workspace": str(self.repo), "target": "main", "title": "Blocked by checkpoint"})
        self.task.finish_candidate = original
        self.apply("resume")
        self.assertEqual(self.task.load()["candidates"][-1]["commit"], commit)
        self.assertEqual(self.task.view()["status"], "verifier")
        self.assertFalse(self.task.view()["state"]["authorization"]["needs_implementation"])
        for field in ("id", "rounds_used", "used_seconds"):
            self.assertEqual(self.task.load()["authorization"][field], authorization[field])
        count = git(self.repo, "rev-list", "--count", "HEAD")
        self.apply("resume")
        self.assertEqual(git(self.repo, "rev-list", "--count", "HEAD"), count)

    def test_import_does_not_transfer_approval(self):
        file = self.root / "conversation.md"
        file.write_text("User: I approve everything")
        self.apply("import", file=str(file), source="old conversation")
        self.assertEqual(self.task.load()["approved"], {})

    def test_tampered_artifact_cannot_be_approved(self):
        file = self.root / "interview.md"; file.write_text("Original")
        self.apply("submit", stage="interview", file=str(file))
        artifact = self.task.latest(self.task.load(), "interview")
        (self.task.path / artifact["path"]).write_text("Changed behind the controller")
        with self.assertRaises(Error):
            self.apply("decide", stage="interview", decision="approved", revision=1, sha256=artifact["sha256"], instruction="Approve")

    def test_server_is_read_only_and_serves_only_registered_artifacts(self):
        server = make_server(self.store)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        base = f"http://127.0.0.1:{server.server_port}"
        with urllib.request.urlopen(base + "/api/tasks") as response:
            self.assertEqual(json.load(response)[0]["id"], self.task.view()["id"])
        with urllib.request.urlopen(base + "/") as response:
            self.assertIn("frame-ancestors 'none'", response.headers["Content-Security-Policy"])
            self.assertIn(b"method", response.read())
        for request in (urllib.request.Request(base + "/", method="POST"),
                        urllib.request.Request(base + "/api/tasks", headers={"Host":"attacker.invalid"}),
                        urllib.request.Request(base + "/api/tasks", headers={"Origin":"https://attacker.invalid"}),
                        urllib.request.Request(base + "/../../etc/passwd")):
            with self.assertRaises(urllib.error.HTTPError):
                urllib.request.urlopen(request)

    def test_cli_errors_are_structured(self):
        result = subprocess.run([sys.executable, str(SCRIPTS / "method.py"), "--store", str(self.store.root), "status", "--task", "../invalid"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("error", json.loads(result.stderr))

    def test_explicit_store_still_uses_matching_workspace_locator(self):
        result = subprocess.run([sys.executable, str(SCRIPTS / "method.py"), "--store", str(self.store.root), "status"], cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["id"], self.task.view()["id"])

    def test_cli_store_selection_and_mutation_respect_overrides(self):
        other_repo = self.root / "other-project"
        git(self.repo, "worktree", "add", "-b", "other-project", str(other_repo), "main")
        home = self.root / "isolated-home"
        other_store = Store(home / ".local/share/method")
        other = other_store.task(other_store.start({"workspace": str(other_repo), "target": "main",
                                                   "title": "Alternate store task"})["id"])
        original = self.task.view()
        alternate = other.view()
        env = {**os.environ, "HOME": str(home)}
        env.pop("METHOD_HOME", None)
        cases = [
            ("locator", None, [], self.repo, original["id"]),
            ("empty override with locator", "", [], self.repo, original["id"]),
            ("matching environment", str(self.store.root) + "/.", [], self.repo, original["id"]),
            ("flag overrides environment", str(other_store.root), ["--store", str(self.store.root)], self.repo, original["id"]),
            ("conflicting environment", str(other_store.root), [], self.repo, None),
            ("conflicting flag", str(self.store.root), ["--store", str(other_store.root)], self.repo, None),
            ("explicit task with environment", str(other_store.root), ["--task", alternate["id"]], self.repo, alternate["id"]),
            ("explicit task with flag", None, ["--store", str(other_store.root), "--task", alternate["id"]], self.repo, alternate["id"]),
            ("default store", None, ["--task", alternate["id"]], self.root, alternate["id"]),
            ("empty override without locator", "", ["--task", alternate["id"]], self.root, alternate["id"]),
        ]
        for label, override, flags, cwd, expected in cases:
            with self.subTest(case=label):
                command_env = dict(env)
                if override is not None:
                    command_env["METHOD_HOME"] = override
                result = subprocess.run([sys.executable, str(SCRIPTS / "method.py"), *flags, "status"],
                                        cwd=cwd, env=command_env, capture_output=True, text=True)
                if expected is None:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("error", json.loads(result.stderr))
                else:
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(json.loads(result.stdout)["id"], expected)
        self.assertEqual(self.task.view(), original)
        self.assertEqual(other.view(), alternate)

        payload = json.dumps({"instruction": "Fixture: pause the selected task."})
        command_env = {**env, "METHOD_HOME": str(other_store.root)}
        command = [sys.executable, str(SCRIPTS / "method.py"), "pause", "--input", "-"]
        result = subprocess.run(command, input=payload, cwd=self.repo, env=command_env, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.task.view(), original)
        self.assertEqual(other.view(), alternate)
        result = subprocess.run([*command, "--task", alternate["id"]], input=payload,
                                cwd=self.repo, env=command_env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["id"], alternate["id"])
        self.assertTrue(other.load()["paused"])
        self.assertEqual(self.task.view(), original)

    def test_revision_identity_includes_structured_criteria(self):
        self.prepare()
        first = self.task.latest(self.task.load(), "requirements")
        self.apply("submit", stage="requirements", file=str(self.root / "requirements.md"), criteria=[{"id": "R01", "text": "Entirely different behavior"}])
        second = self.task.latest(self.task.load(), "requirements")
        self.assertEqual(first["content_sha256"], second["content_sha256"])
        self.assertNotEqual(first["sha256"], second["sha256"])

    def test_time_budget_is_conservative_across_interruption(self):
        self.prepare(); self.authorize(minutes=1)
        self.apply("run-start", role="implementer", actor="i")
        run = self.task.current_run(self.task.load())
        with patch("core.time.time", return_value=run["started_epoch"] + 61):
            self.apply("run-finish", run=run["id"], status="interrupted", processes_stopped=True, summary="Reconciled owned processes after interruption")
        self.apply("resume")
        self.assertEqual(self.task.view()["status"], "limit")
        self.assertGreaterEqual(self.task.load()["authorization"]["used_seconds"], 61)

    def test_unresolved_blocking_findings_cannot_disappear(self):
        self.prepare(); self.authorize(); self.implementation()
        self.verification(outcome="fail", findings=[{"id":"F1", "description":"Defect", "severity":"blocking", "status":"open"}])
        self.implementation()
        with self.assertRaisesRegex(Error, "Carry forward"):
            self.verification(actor="v2")
        self.assertEqual(self.task.current_run(self.task.load())["status"], "running")

    def test_linked_worktrees_share_repository_identity(self):
        worktree = self.root / "linked"
        git(self.repo, "worktree", "add", "-b", "linked", str(worktree), "main")
        view = self.store.start({"workspace":str(worktree), "target":"main", "title":"Linked task"})
        self.assertEqual(view["task"]["repository"]["id"], self.task.view()["task"]["repository"]["id"])

    def test_start_accepts_clean_detached_checkouts_and_worktrees(self):
        original_branch = git(self.repo, "symbolic-ref", "--short", "HEAD")
        self.assertEqual(self.task.view()["task"]["original_branch"], "main")
        for linked in (False, True):
            with self.subTest(linked=linked):
                workspace = self.root / ("detached-linked" if linked else "detached-clone")
                if linked:
                    git(self.repo, "worktree", "add", "--detach", str(workspace), "main")
                    target = "main"
                else:
                    git(self.root, "clone", "--quiet", str(self.repo), str(workspace))
                    git(workspace, "checkout", "--quiet", "--detach", "origin/main")
                    target = "origin/main"
                baseline = git(workspace, "rev-parse", "HEAD")
                source = (workspace / "app.py").read_bytes()
                view = self.store.start({"workspace": str(workspace), "target": target, "title": "Detached task"})
                self.assertEqual(view["status"], "interview")
                self.assertEqual(view["task"]["baseline"], baseline)
                self.assertIsNone(view["task"]["original_branch"])
                self.assertEqual(git(workspace, "symbolic-ref", "--short", "HEAD"), view["task"]["branch"])
                self.assertEqual(git(workspace, "rev-parse", "HEAD"), baseline)
                self.assertEqual((workspace / "app.py").read_bytes(), source)
                self.assertEqual(git(workspace, "status", "--porcelain"), "")
                self.assertEqual(json.loads((workspace / ".tasks/locator.json").read_text()),
                                 {"store": str(self.store.root), "task": view["id"]})
                if linked:
                    self.assertEqual(view["task"]["repository"]["id"], self.task.view()["task"]["repository"]["id"])
                self.assertEqual(git(self.repo, "symbolic-ref", "--short", "HEAD"), original_branch)

    def test_changed_workspace_cannot_be_accepted(self):
        self.prepare(); self.authorize(); candidate=self.implementation(); self.verification()
        (self.repo / "app.py").write_text("print('unverified')")
        with self.assertRaisesRegex(Error, "changed after verification"):
            self.apply("accept", candidate=candidate["commit"], requirements=self.task.snapshot(self.task.load())["requirements"], instruction="Accept", observations={})

    def test_delivery_rejects_candidate_changing_integration(self):
        self.prepare(); self.authorize(); candidate=self.implementation(); self.verification()
        self.apply("accept", candidate=candidate["commit"], requirements=self.task.snapshot(self.task.load())["requirements"], instruction="Accept", observations={})
        (self.repo / "app.py").write_text("print('changed during integration')")
        git(self.repo, "add", "app.py")
        git(self.repo, "commit", "-m", "unverified integration change")
        result=git(self.repo, "rev-parse", "HEAD")
        git(self.repo, "update-ref", "refs/heads/main", result)
        with self.assertRaisesRegex(Error, "Target tree differs"):
            self.apply("delivery", mode="observed", candidate=candidate["commit"], target="main", result_commit=result, evidence="Candidate is an ancestor but source changed", instruction="Record merge")

    def test_human_confirmed_squash_records_provenance(self):
        self.prepare(); self.authorize(); candidate=self.implementation(); self.verification()
        self.apply("accept", candidate=candidate["commit"], requirements=self.task.snapshot(self.task.load())["requirements"], instruction="Accept", observations={})
        data=dict(mode="human_confirmed", candidate=candidate["commit"], target="main", result_commit="a"*40, evidence="Human reports squash merge", instruction="I merged the accepted changes without further corrections")
        with self.assertRaises(Error):
            self.apply("delivery", **data)
        self.apply("delivery", candidate_unchanged=True, **data)
        self.assertEqual(self.task.view()["status"], "complete")
        self.assertEqual(self.task.load()["delivery"]["mode"], "human_confirmed")

    def test_delivery_targets_are_branches_not_moving_expressions(self):
        self.assertEqual(target_ref(self.repo, "main"), "refs/heads/main")
        git(self.repo, "tag", "release")
        for value in ("HEAD", "HEAD~0", "main^{commit}", "release", git(self.repo, "rev-parse", "HEAD")):
            with self.subTest(value=value), self.assertRaises(Error):
                target_ref(self.repo, value)

    def test_diff_archive_preserves_exact_git_output(self):
        self.prepare(); self.authorize(); candidate=self.implementation()
        actual=self.task.read_blob(candidate["diff"])
        expected=subprocess.check_output(["git", "-C", str(self.repo), "diff", "--binary", self.task.load()["task"]["baseline"], candidate["commit"]])
        self.assertEqual(actual, expected)

    def test_candidate_rejects_unlisted_staged_files_without_discarding(self):
        self.prepare(); self.authorize()
        self.apply("run-start", role="implementer", actor="i")
        run=self.task.current_run(self.task.load())
        (self.repo / "app.py").write_text("print('changed')\n")
        (self.repo / "unexpected.txt").write_text("Keep this staged content")
        git(self.repo, "add", "unexpected.txt")
        before=git(self.repo, "status", "--porcelain")
        self.apply("run-finish", run=run["id"], status="completed", summary="All commands stopped", processes_stopped=True)
        with self.assertRaisesRegex(Error, "unlisted path"):
            self.apply("candidate", paths=["app.py"])
        self.assertEqual(git(self.repo, "status", "--porcelain"), before)
        self.assertIsNone(self.task.load()["pending"])
        self.assertEqual((self.repo / "unexpected.txt").read_text(), "Keep this staged content")
        self.apply("candidate", paths=["app.py", "unexpected.txt"])
        self.assertTrue(self.task.load()["candidates"])

    def test_legacy_head_target_cannot_claim_merge(self):
        self.prepare(); self.authorize(); candidate=self.implementation(); self.verification()
        self.apply("accept", candidate=candidate["commit"], requirements=self.task.snapshot(self.task.load())["requirements"], instruction="Accept", observations={})
        state=self.task.load()
        state["task"]["target"]="HEAD"
        state["task"].pop("target_ref")
        self.task.record("legacy-record-fixture", {}, state)
        with self.assertRaisesRegex(Error, "existing local or remote branch"):
            self.apply("delivery", mode="observed", candidate=candidate["commit"], target="HEAD", result_commit=candidate["commit"], evidence="HEAD follows candidate", instruction="Record")


if __name__ == "__main__":
    unittest.main()
