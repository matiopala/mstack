"""Durable Method records and workflow gates. Standard library only."""
from __future__ import annotations

import contextlib
import copy
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile
import threading
import time
import uuid
from runner_results import selected_result

VERSION = "2.0.0"
STAGES = ("interview", "exploration", "requirements", "verification", "plan")
ID = re.compile(r"^[a-zA-Z0-9_-]+$")


class Error(Exception):
    pass


class ProcessCleanupError(Error):
    pass


def require(condition, message):
    if not condition:
        raise Error(message)


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def skill_digest():
    root = Path(__file__).resolve().parent.parent
    files = sorted(p for p in root.rglob("*") if p.is_file() and p.suffix in (".py", ".md", ".yaml", ".html", ".css", ".js"))
    return digest(encoded({str(p.relative_to(root)): digest(p.read_bytes()) for p in files}))


def encoded(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


def atomic(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".write-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        os.replace(name, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(name):
            os.unlink(name)


@contextlib.contextmanager
def lock(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Error("Another Method operation owns this task; retry after it finishes.")
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def git(workspace, *args, input=None, raw=False, timeout=None, started=None):
    argv = ["git", "-C", str(workspace), *args]
    if timeout is None:
        result = subprocess.run(argv, input=input, capture_output=True, text=not raw)
        stdout, stderr, returncode = result.stdout, result.stderr, result.returncode
    else:
        expires = time.monotonic() + timeout
        # File-backed streams keep Git independent of a blocked recording callback.
        with contextlib.ExitStack() as streams:
            mode = "w+b" if raw else "w+"
            output = streams.enter_context(tempfile.TemporaryFile(mode=mode))
            errors = streams.enter_context(tempfile.TemporaryFile(mode=mode))
            source = None
            if input is not None:
                source = streams.enter_context(tempfile.TemporaryFile(mode=mode))
                source.write(input)
                source.seek(0)
            stop_requested = threading.Event()
            finished = threading.Event()
            outcome = {"timeout": False, "error": None}

            def cleanup():
                try:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.wait()
                except OSError as error:
                    raise ProcessCleanupError(f"Cannot confirm cleanup of Git process group {process.pid}; reconcile the recorded process before continuing") from error

            def monitor():
                try:
                    while process.poll() is None and not stop_requested.is_set():
                        allowance = expires - time.monotonic()
                        if allowance <= 0:
                            outcome["timeout"] = True
                            break
                        stop_requested.wait(min(allowance, 0.05))
                except BaseException as error:
                    outcome["error"] = error
                finally:
                    try:
                        cleanup()
                    except BaseException as error:
                        outcome["error"] = error
                    finally:
                        finished.set()

            watcher = threading.Thread(target=monitor, name="method-git", daemon=True)
            if time.monotonic() >= expires:
                raise subprocess.TimeoutExpired(argv, timeout)
            process = subprocess.Popen(argv, stdin=source, stdout=output, stderr=errors,
                                       text=not raw, start_new_session=True)
            try:
                watcher.start()
                if started is not None:
                    started(process)
                finished.wait()
            finally:
                stop_requested.set()
                if watcher.ident is None:
                    cleanup()
                else:
                    finished.wait()
                    watcher.join()
                if outcome["error"] is not None:
                    raise outcome["error"]
            output.seek(0)
            errors.seek(0)
            stdout, stderr, returncode = output.read(), errors.read(), process.returncode
            if outcome["timeout"]:
                raise subprocess.TimeoutExpired(argv, timeout, output=stdout, stderr=stderr)
    error = stderr.decode("utf-8", errors="replace") if raw else stderr
    require(returncode == 0, error.strip() or "Git operation failed")
    return stdout if raw else stdout.strip()


def require_full_history(workspace):
    require(git(workspace, "rev-parse", "--is-shallow-repository") == "false",
            "Shallow repositories cannot retain self-contained candidates. Obtain complete history before starting or capturing a candidate; Method will not fetch it automatically.")


def remaining_timeout(deadline):
    remaining = deadline - time.time()
    require(remaining > 0, "Execution time exhausted during verifier setup")
    return remaining


def target_ref(workspace, target):
    require(isinstance(target, str) and target and not target.startswith("-"), "Choose an explicit target branch")
    choices = [target] if target.startswith("refs/") else ["refs/heads/" + target, "refs/remotes/" + target]
    matches = []
    for ref in choices:
        if not ref.startswith(("refs/heads/", "refs/remotes/")) or ref.endswith("/HEAD"):
            continue
        result = subprocess.run(["git", "-C", str(workspace), "show-ref", "--verify", "--quiet", ref], capture_output=True)
        if result.returncode == 0:
            matches.append(ref)
    require(len(matches) == 1, "Target must identify one existing local or remote branch; use its full ref if ambiguous. HEAD, tags, and revision expressions are not delivery targets.")
    return matches[0]


def clean(workspace):
    return not git(workspace, "status", "--porcelain", "--untracked-files=all")


def test_file_names(scenario):
    files = scenario.get("test_files")
    require(isinstance(files, list) and files, "Automated scenarios need test_files naming their assertion and fixtures")
    for name in files:
        require(isinstance(name, str) and name and not name.startswith(("/", "-", ":"))
                and name == Path(name).as_posix() and not {"..", ".git", ".tasks"}.intersection(Path(name).parts)
                and name != "." and "\x00" not in name, "test_files must be explicit repository-relative files")
    require(len(set(files)) == len(files), "Duplicate test file")
    return files


def test_sources(workspace, scenario):
    sources = {}
    root = Path(workspace).resolve()
    for name in test_file_names(scenario):
        path = root / name
        require(path.resolve() == path and path.is_file(), "Missing or indirect test file: " + name)
        sources[name] = (path.read_bytes(), bool(path.stat().st_mode & 0o111))
    return sources


def assertion_script(argv, files):
    if "/" in argv[0] and str(Path(argv[0])) in files:
        return True
    interpreter = Path(argv[0]).name
    if len(argv) < 2 or not re.fullmatch(r"python(?:\d+(?:\.\d+)*)?|node|ruby|perl|php|bash|sh|zsh", interpreter):
        return False
    operands = iter(argv[1:])
    script = next(operands, "")
    if interpreter.startswith("python"):
        while script in ("-B", "-u", "-I"):
            script = next(operands, "")
    return str(Path(script)) in files


def check_baseline_tree(workspace, state, scenarios):
    require(git(workspace, "rev-parse", "--show-toplevel") == str(Path(workspace).resolve())
            and git(workspace, "rev-parse", "HEAD") == state["task"]["baseline"],
            "Run the test baseline at the original task commit")
    allowed = {os.fsencode(path) for scenario in scenarios if scenario["kind"] == "automated"
               for path in test_file_names(scenario)}
    # Include index-only changes, deletions, both ends of renames, and untracked files.
    for args in (("diff", "--cached", "--no-renames", "--name-only", "-z", "HEAD"),
                 ("diff", "--no-renames", "--name-only", "-z"),
                 ("ls-files", "--others", "--exclude-standard", "-z")):
        changes = set(git(workspace, *args, raw=True).split(b"\0")) - {b""}
        require(changes <= allowed, "Product or unlisted files changed before the test baseline: "
                + ", ".join(os.fsdecode(name) for name in sorted(changes - allowed)))


def human(data):
    require(isinstance(data.get("instruction"), str) and data["instruction"].strip(),
            "A quoted human instruction is required; never infer authorization.")
    return {"instruction": data["instruction"], "source": data.get("source"), "at": now()}


def initial_state(metadata):
    return {"task": metadata, "artifacts": [], "approved": {}, "authorization": None,
            "runs": [], "candidates": [], "accepted": None, "delivery": None,
            "paused": False, "blocker": None, "pending": {"kind": "start"}}


class Store:
    def __init__(self, root=None):
        self.root = Path(root or os.environ.get("METHOD_HOME") or "~/.local/share/method").expanduser().resolve()

    def task(self, task_id):
        require(isinstance(task_id, str) and ID.fullmatch(task_id), "Invalid task ID")
        return Task(self.root / "tasks" / task_id)

    def start(self, data):
        workspace = Path(data.get("workspace", ".")).resolve()
        require(str(workspace) == git(workspace, "rev-parse", "--show-toplevel"), "Use the worktree root")
        require(clean(workspace), "Workspace is dirty. Preserve it and use a clean checkout or separate worktree.")
        require_full_history(workspace)
        title = data.get("title", "").strip()
        require(title, "Task title is required")
        target = data.get("target", "")
        canonical_target = target_ref(workspace, target)
        target_sha = git(workspace, "rev-parse", "--verify", canonical_target + "^{commit}")
        baseline = git(workspace, "rev-parse", "HEAD")
        branch = git(workspace, "rev-parse", "--abbrev-ref", "HEAD")
        common = Path(git(workspace, "rev-parse", "--path-format=absolute", "--git-common-dir")).resolve()
        with lock(self.root / "registry.lock"), contextlib.ExitStack() as locks:
            for path in (self.root / "tasks").glob("*/task.json"):
                metadata = json.loads(path.read_text())
                if Path(metadata["workspace"]).resolve() == workspace:
                    existing = self.task(metadata["id"]).load()
                    require(not existing["pending"] or existing["pending"]["kind"] != "start",
                            "Workspace startup is unfinished for task " + metadata["id"] + "; inspect and resume that task explicitly.")
            task_dir = workspace / ".tasks"
            locator = task_dir / "locator.json"
            previous_locator = None
            if task_dir.exists() or task_dir.is_symlink():
                require(task_dir.is_dir() and not task_dir.is_symlink()
                        and locator.is_file() and not locator.is_symlink(),
                        "Workspace has an unsafe or unavailable task locator; preserve it and reconcile it first")
                previous_locator = locator.read_bytes()
                saved = json.loads(previous_locator)
                require(isinstance(saved, dict) and isinstance(saved.get("store"), str)
                        and Path(saved["store"]).expanduser().resolve() == self.root,
                        "Workspace locator must identify the selected store; preserve it and reconcile it first")
                previous = self.task(saved.get("task"))
                require((previous.path / "task.json").is_file(), "Previous task is unavailable; preserve its locator")
                previous_state = previous.load()
                require(previous_state["task"]["id"] == saved["task"]
                        and Path(previous_state["task"]["workspace"]).resolve() == workspace,
                        "Previous task belongs to another workspace; preserve its locator")
                require(previous.status(previous_state)[0] == "complete",
                        "Workspace task is not complete; resume it before starting another task")
                locks.enter_context(lock(previous.path / "task.lock"))
                previous_state = previous.load()
                require(previous.status(previous_state)[0] == "complete"
                        and not previous_state["pending"] and not previous.current_run(previous_state),
                        "Previous task must be complete with no pending operation or active run")
            registry = self.root / "repositories"
            repo = None
            for path in registry.glob("*.json"):
                item = json.loads(path.read_text())
                if str(common) in item["common_dirs"]:
                    repo = item
            if data.get("repository"):
                require(ID.fullmatch(data["repository"]), "Invalid repository ID")
                path = registry / (data["repository"] + ".json")
                require(path.is_file(), "Unknown repository ID")
                require(repo is None or repo["id"] == data["repository"], "Clone already has another identity")
                repo = json.loads(path.read_text())
                if str(common) not in repo["common_dirs"]:
                    human(data)
                    repo["common_dirs"].append(str(common))
            if repo is None:
                repo = {"id": uuid.uuid4().hex[:12], "name": workspace.name, "common_dirs": [str(common)]}
            atomic(registry / (repo["id"] + ".json"), encoded(repo))
            task_id = uuid.uuid4().hex[:12]
            task = self.task(task_id)
            task.path.mkdir(parents=True)
            locks.enter_context(lock(task.path / "task.lock"))
            task_branch = "method/" + task_id
            metadata = {"id": task_id, "title": title, "goal": data.get("goal", title),
                        "repository": repo, "workspace": str(workspace), "baseline": baseline,
                        "object_format": git(workspace, "rev-parse", "--show-object-format"),
                        "target": target, "target_ref": canonical_target, "target_at_start": target_sha, "branch": task_branch,
                        "original_branch": None if branch == "HEAD" else branch, "created": now(), "method_version": VERSION, "skill_sha256": skill_digest(),
                        "delivery_requirement": "merge"}
            atomic(task.path / "task.json", encoded(metadata))
            state = initial_state(metadata)
            task.record("start-intent", data, state)
            git(workspace, "switch", "-c", task_branch)
            exclude = common / "info" / "exclude"
            old = exclude.read_text() if exclude.exists() else ""
            if "/.tasks/" not in old.splitlines():
                atomic(exclude, (old + "\n/.tasks/\n").encode())
            new_locator = encoded({"store": str(self.root), "task": task_id})
            publication = {"kind": "start", "phase": "publication",
                           "previous_locator_sha256": digest(previous_locator) if previous_locator is not None else None}
            state["pending"] = publication
            task.record("start-publication-intent", {}, state)
            try:
                task.finish_start(state)
                task.record("started", {}, state)
            except OSError:
                state["pending"] = publication
                task.record("start-incomplete", {}, state)
                if locator.is_file() and locator.read_bytes() == new_locator:
                    if previous_locator is None:
                        locator.unlink()
                    else:
                        atomic(locator, previous_locator)
                raise
            return task.view()

    def list(self):
        result = []
        for path in sorted((self.root / "tasks").glob("*/task.json")):
            try:
                result.append(self.task(path.parent.name).view(detail=False))
            except (Error, OSError, ValueError) as error:
                result.append({"id": path.parent.name, "status": "record_error", "error": str(error)})
        return result


class Task:
    def __init__(self, path):
        self.path = path

    def events(self):
        events = []
        for path in sorted((self.path / "events").glob("*.json")):
            event = json.loads(path.read_text())
            require(event["sequence"] == len(events) + 1, "Event sequence is incomplete; preserve records for recovery")
            events.append(event)
        return events

    def initializing_state(self):
        allowed = {"task.json", "task.lock", "events"}
        require(all(p.name in allowed and not p.is_symlink() for p in self.path.iterdir()),
                "Missing event history with other task records; preserve records for recovery")
        events = self.path / "events"
        if events.exists():
            require(events.is_dir() and all(p.is_file() and not p.is_symlink() and p.name.startswith(".write-")
                                            for p in events.iterdir()),
                    "Incomplete event history; preserve records for recovery")
        metadata = json.loads((self.path / "task.json").read_text())
        strings = ("id", "title", "goal", "workspace", "baseline", "target", "target_at_start",
                   "branch", "created", "method_version", "skill_sha256", "delivery_requirement")
        require(isinstance(metadata, dict)
                and all(isinstance(metadata.get(key), str) and metadata[key] for key in strings),
                "Invalid task initialization metadata")
        repository = metadata.get("repository")
        require(metadata["id"] == self.path.name and ID.fullmatch(metadata["id"])
                and Path(metadata["workspace"]).is_absolute()
                and re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", metadata["baseline"])
                and metadata["branch"] == "method/" + metadata["id"]
                and isinstance(repository, dict)
                and all(isinstance(repository.get(key), str) and repository[key] for key in ("id", "name"))
                and isinstance(repository.get("common_dirs"), list)
                and repository["common_dirs"]
                and all(isinstance(path, str) and Path(path).is_absolute() for path in repository["common_dirs"]),
                "Invalid task initialization identity")
        def valid_target(ref):
            return (isinstance(ref, str) and ref.startswith(("refs/heads/", "refs/remotes/"))
                    and not ref.endswith("/HEAD")
                    and subprocess.run(["git", "check-ref-format", ref], capture_output=True).returncode == 0)

        commits = (metadata["baseline"], metadata["target_at_start"])
        object_format = metadata.get("object_format", {40: "sha1", 64: "sha256"}.get(len(commits[0])))
        size = {"sha1": 40, "sha256": 64}.get(object_format) if isinstance(object_format, str) else None
        targets = ([metadata["target"]] if metadata["target"].startswith("refs/") else
                   ["refs/heads/" + metadata["target"], "refs/remotes/" + metadata["target"]])
        original_branch = metadata.get("original_branch")
        require(size and all(re.fullmatch(r"[0-9a-f]{%d}" % size, commit) for commit in commits)
                and re.fullmatch(r"[0-9a-f]{64}", metadata["skill_sha256"])
                and metadata["delivery_requirement"] == "merge"
                and ID.fullmatch(repository["id"])
                and not metadata["target"].startswith("-")
                and any(valid_target(ref) for ref in targets)
                and ("target_ref" not in metadata or metadata["target_ref"] in targets and valid_target(metadata["target_ref"]))
                and (original_branch is None or isinstance(original_branch, str)
                     and original_branch != "HEAD" and not original_branch.startswith("-")
                     and subprocess.run(["git", "check-ref-format", "refs/heads/" + original_branch],
                                        capture_output=True).returncode == 0),
                "Invalid task initialization fields")
        dt.datetime.fromisoformat(metadata["created"])
        state = initial_state(metadata)
        state["pending"]["phase"] = "initialization"
        return state

    def load(self):
        events = self.events()
        if not events:
            return self.initializing_state()
        state = {}
        for event in events:
            state.update(event["changes"])
        return state

    def record(self, kind, data, state):
        events = self.events()
        previous = self.load() if events else {}
        changes = {key: value for key, value in state.items() if key not in previous or previous[key] != value}
        event = {"sequence": len(events) + 1, "at": now(), "kind": kind, "data": data, "changes": changes}
        atomic(self.path / "events" / ("%06d.json" % event["sequence"]), encoded(event))
        atomic(self.path / "state.json", encoded(state))

    def blob(self, folder, name, content):
        path = self.path / folder / name
        require(not path.exists(), "Refusing to replace retained evidence")
        atomic(path, content)
        return {"path": str(path.relative_to(self.path)), "sha256": digest(content)}

    def read_blob(self, reference, deadline=None, retain=True):
        path = (self.path / reference["path"]).resolve()
        require(self.path.resolve() in path.parents, "Artifact path escapes task")
        checksum = hashlib.sha256()
        chunks = []
        with path.open("rb") as source:
            while True:
                if deadline is not None:
                    remaining_timeout(deadline)
                chunk = source.read(1024 * 1024)
                if not chunk:
                    break
                checksum.update(chunk)
                if retain:
                    chunks.append(chunk)
        require(checksum.hexdigest() == reference.get("content_sha256", reference["sha256"]),
                "Retained artifact changed: " + reference["path"])
        data = b"".join(chunks) if retain else None
        if deadline is not None:
            remaining_timeout(deadline)
        return data

    def read_evidence(self, evidence):
        content = self.read_blob(evidence)
        if evidence.get("runner_report"):
            content += b"\nSelected test report\n" + self.read_blob(evidence["runner_report"])
        return content

    def snapshot(self, state):
        return {stage: state["approved"][stage]["sha256"] for stage in STAGES if stage in state["approved"]}

    def bind_artifact(self, artifact):
        artifact["content_sha256"] = artifact["sha256"]
        artifact["sha256"] = digest(encoded({key: artifact[key] for key in ("stage", "revision", "criteria", "parents", "content_sha256")}))

    def approved_integrity(self, state):
        for stage in state["approved"]:
            artifact = self.latest(state, stage)
            self.read_blob(artifact)
            require(artifact["sha256"] == state["approved"][stage]["sha256"], "Approved revision is stale")

    def latest(self, state, stage):
        return next((a for a in reversed(state["artifacts"]) if a["stage"] == stage), None)

    def current_run(self, state):
        return next((r for r in reversed(state["runs"]) if r["status"] == "running"), None)

    def implementation_run(self, state):
        auth = state["authorization"]
        if not auth:
            return None
        return next((run for run in reversed(state["runs"])
                     if run["role"] == "implementer" and run["authorization"] == auth["id"]), None)

    def needs_candidate(self, state):
        auth = state["authorization"]
        if not auth or auth["mode"] != "implementation":
            return False
        run = self.implementation_run(state)
        candidate = state["candidates"][-1] if state["candidates"] else None
        return bool(auth.get("needs_implementation") or not run or run["status"] != "completed"
                    or not candidate or candidate["run"] != run["id"])

    def remaining(self, state):
        auth = state["authorization"]
        require(auth, "Explicit implementation or evidence authorization is required")
        run = self.current_run(state)
        elapsed = time.time() - run["started_epoch"] if run else 0
        return auth["minutes"] * 60 - auth["used_seconds"] - elapsed

    def legacy_test_design(self, state):
        if "verification" not in state["approved"]:
            return False
        return any(s["kind"] == "automated" and (not s.get("test_files") or "baseline" not in s)
                   for s in self.latest(state, "verification")["criteria"])

    def status(self, state):
        if state["pending"]:
            if state["pending"].get("phase") == "initialization":
                return "recovery", "Inspect the incomplete startup, then resolve it explicitly to abandon this attempt before starting again."
            return "recovery", "Reconcile the recorded operation before continuing."
        if state["paused"]:
            return "paused", "Resume explicitly when ready."
        if state["blocker"]:
            return "blocked", state["blocker"]
        if not state["accepted"] and self.legacy_test_design(state):
            run = self.current_run(state)
            if run:
                return run["role"], "Reconcile this run, then revise the legacy verification design."
            return "verification", "Revise the legacy verification design with test files and baseline expectations."
        for stage in STAGES:
            if stage not in state["approved"]:
                artifact = self.latest(state, stage)
                if artifact and artifact["parents"] == self.snapshot_before(state, stage) and artifact["decision"] == "pending":
                    return "approval", "Review and approve or request changes to " + stage + "."
                return stage, "Prepare a new " + stage + " revision."
        if state["delivery"]:
            return "complete", "Delivery recorded; workspace cleanup is separate."
        if state["accepted"]:
            return "delivery", "Merge manually, then record target-branch evidence or human confirmation."
        auth = state["authorization"]
        if not auth:
            return "authorization", "Explicitly authorize implementation against approved revisions."
        run = self.current_run(state)
        if run:
            if self.remaining(state) <= 0:
                return "limit", "Execution time exhausted; a human decision is required."
            if run["role"] == "implementer":
                design = self.latest(state, "verification")
                for scenario in design["criteria"]:
                    if scenario["kind"] == "automated":
                        baseline = state.get("test_baselines", {}).get(scenario["id"], {})
                        if (baseline.get("revision") != design["sha256"]
                                or not (baseline.get("unavailable") or baseline.get("outcome") == scenario["baseline"])):
                            return "implementer", "Record the test baseline for " + scenario["id"] + " before product edits."
                return "implementer", "Implement against the checkpointed tests, then finish run " + run["id"] + "."
            return run["role"], "Finish or reconcile run " + run["id"] + "."
        candidate = state["candidates"][-1] if state["candidates"] else None
        if candidate and candidate.get("verification") and not self.needs_candidate(state):
            if candidate["verification"]["ready"]:
                return "human_review", "Try and accept the verified candidate, request corrections, or request evidence."
            if auth["mode"] == "evidence":
                return "authorization", "Evidence is not ready. Explicitly authorize further evidence collection or implementation corrections."
        if self.remaining(state) <= 0:
            return "limit", "Execution time exhausted; a human decision is required."
        if self.needs_candidate(state):
            if auth["rounds_used"] >= auth["rounds"]:
                return "limit", "Verification round limit exhausted; a human decision is required."
            implementation = self.implementation_run(state)
            if implementation and implementation["status"] == "completed":
                return "candidate", "Capture an exact candidate from the completed implementation run."
            return "implementer", "Launch or resume the authorized implementation or correction run."
        if candidate and candidate["verification"] is None:
            if auth["rounds_used"] >= auth["rounds"]:
                return "limit", "Verification round limit exhausted; a human decision is required."
            return "verifier", "Launch a fresh verifier against the retained candidate."
        if auth["rounds_used"] >= auth["rounds"]:
            return "limit", "Verification round limit exhausted; a human decision is required."
        return "implementer", "Launch or resume the implementer within the authorized scope."

    def snapshot_before(self, state, stage):
        return {key: state["approved"][key]["sha256"] for key in STAGES[:STAGES.index(stage)] if key in state["approved"]}

    def view(self, detail=True):
        state = self.load()
        status, action = self.status(state)
        events = self.events()
        if state["authorization"]:
            state["authorization"]["needs_implementation"] = self.needs_candidate(state)
        result = {"id": state["task"]["id"], "task": state["task"], "status": status,
                  "next_action": action, "updated": events[-1]["at"] if events else state["task"]["created"],
                  "store_path": str(self.path)}
        if detail:
            result["state"] = state
            result["events"] = events
        return result

    def assert_workspace(self, state, expected=None):
        workspace = state["task"]["workspace"]
        require(git(workspace, "symbolic-ref", "--short", "HEAD") == state["task"]["branch"], "Task branch changed")
        if expected:
            require(git(workspace, "rev-parse", "HEAD") == expected, "Workspace HEAD changed; reconcile before proceeding")
        return workspace

    def apply(self, command, data):
        with lock(self.path / "task.lock"):
            state = self.load()
            require(not state["pending"] or command in ("resume", "resolve"), "Uncertain operation: resume to inspect; do not repeat it")
            require(not state["paused"] or command in ("resume", "resolve"), "Task is paused")
            recovery = command in ("resume", "resolve", "import", "block", "pause") or (
                command == "run-finish" and data.get("status") in ("interrupted", "blocked"))
            require(not state["blocker"] or recovery, "Task is blocked; resume with a resolution before continuing")
            executing = command in ("authorize", "run-start", "baseline", "test", "candidate", "verify", "accept") or (
                command == "run-finish" and data.get("status") == "completed")
            require(not executing or not self.legacy_test_design(state),
                    "Revise the legacy verification design with test files and baseline expectations before execution")
            handler = getattr(self, "do_" + command.replace("-", "_"), None)
            require(handler is not None, "Unknown command")
            handler(state, data)
            self.record(command, data, state)
            return self.view()

    def idle(self, state):
        require(not self.current_run(state), "Stop and finish the active agent run before changing task state")

    def do_submit(self, state, data):
        self.idle(state)
        stage = data.get("stage")
        require(stage in STAGES, "Unknown preparation stage")
        require(all(s in state["approved"] for s in STAGES[:STAGES.index(stage)]), "Earlier stages need approval or a recorded waiver")
        content = Path(data["file"]).read_bytes()
        require(content.strip(), "Artifact must not be empty")
        ids = data.get("criteria", [])
        if stage in ("requirements", "verification"):
            require(isinstance(ids, list) and ids, "Declare stable criteria IDs in criteria")
            require(all(isinstance(x, dict) and ID.fullmatch(x.get("id", "")) and x.get("text") for x in ids), "Each criterion needs id and text")
            require(len({x["id"] for x in ids}) == len(ids), "Duplicate criterion ID")
        if stage == "verification":
            requirements = {x["id"] for x in self.latest(state, "requirements")["criteria"]}
            covered = set()
            for scenario in ids:
                refs = scenario.get("requirements", [])
                require(refs and set(refs) <= requirements, "Scenario must reference approved requirements")
                require(scenario.get("kind") in ("automated", "human"), "Scenario kind must be automated or human")
                if scenario["kind"] == "automated":
                    test_file_names(scenario)
                    require(scenario.get("baseline") in ("pass", "fail"), "Declare the expected baseline pass or fail")
                    if "runner" in scenario:
                        runner = scenario["runner"]
                        require(isinstance(runner, list) and runner and all(isinstance(a, str) and a for a in runner),
                                "The approved native runner must be a nonempty argv prefix")
                covered.update(refs)
            require(covered == requirements, "Every requirement needs a verification scenario")
        revision = 1 + sum(a["stage"] == stage for a in state["artifacts"])
        artifact = {"stage": stage, "revision": revision, "criteria": ids, "decision": "pending",
                    "parents": self.snapshot_before(state, stage), "at": now(),
                    **self.blob("artifacts", f"{stage}-{revision}-{uuid.uuid4().hex[:8]}.md", content)}
        self.bind_artifact(artifact)
        for key in STAGES[STAGES.index(stage):]:
            state["approved"].pop(key, None)
        state["artifacts"].append(artifact)
        state.update(authorization=None, accepted=None, delivery=None, blocker=None)

    def do_decide(self, state, data):
        self.idle(state)
        decision = human(data)
        stage = data.get("stage")
        require(stage in STAGES, "Unknown stage")
        require(all(s in state["approved"] for s in STAGES[:STAGES.index(stage)]), "Earlier stages are not approved")
        verdict = data.get("decision")
        require(verdict in ("approved", "rejected", "skipped"), "Use approved, rejected, or skipped")
        if verdict == "skipped":
            require(stage in ("interview", "exploration", "plan") and data.get("reason"), "Only interview, exploration, or plan can be waived, with a reason")
            revision = 1 + sum(a["stage"] == stage for a in state["artifacts"])
            artifact = {"stage": stage, "revision": revision, "criteria": [], "decision": "pending",
                        "parents": self.snapshot_before(state, stage), "at": now(),
                        **self.blob("artifacts", f"{stage}-{revision}-{uuid.uuid4().hex[:8]}.md", ("# Recorded waiver\n\n" + data["reason"]).encode())}
            self.bind_artifact(artifact)
            state["artifacts"].append(artifact)
        else:
            artifact = self.latest(state, stage)
            require(artifact and artifact["revision"] == data.get("revision") and artifact["sha256"] == data.get("sha256"), "Decision must identify the exact current revision and SHA-256")
            require(artifact["parents"] == self.snapshot_before(state, stage), "Artifact depends on stale approvals; submit a revised artifact")
            self.read_blob(artifact)
        artifact["decision"] = verdict
        artifact["human"] = decision
        for key in STAGES[STAGES.index(stage):]:
            state["approved"].pop(key, None)
        if verdict != "rejected":
            state["approved"][stage] = {"revision": artifact["revision"], "sha256": artifact["sha256"], "decision": verdict}
        state.update(authorization=None, accepted=None, delivery=None, blocker=None)

    def do_import(self, state, data):
        require(data.get("source"), "Imported context needs provenance")
        name = "context-" + uuid.uuid4().hex[:12] + ".md"
        data["retained"] = self.blob("artifacts", name, Path(data["file"]).read_bytes())

    def do_authorize(self, state, data):
        self.idle(state)
        decision = human(data)
        require(len(state["approved"]) == len(STAGES), "All preparation must be approved or explicitly waived")
        require(data.get("revisions") == self.snapshot(state), "Authorization must bind the exact approved revision hashes")
        for stage in STAGES:
            self.read_blob(self.latest(state, stage))
        mode = data.get("mode", "implementation")
        require(mode in ("implementation", "evidence"), "Authorization mode must be implementation or evidence")
        require(mode != "evidence" or state["candidates"], "Evidence-only authorization needs a candidate")
        rounds, minutes = data.get("rounds", 3), data.get("minutes", 120)
        require(type(rounds) is int and rounds > 0 and type(minutes) is int and minutes > 0, "Execution limits must be positive integers")
        state["authorization"] = {"id": uuid.uuid4().hex[:12], "mode": mode, "revisions": self.snapshot(state),
                                  "rounds": rounds, "minutes": minutes, "rounds_used": 0, "used_seconds": 0,
                                  "human": decision}
        state.update(accepted=None, delivery=None, blocker=None)
        if state["candidates"]:
            state["candidates"][-1]["verification"] = None
        if mode == "implementation":
            state["authorization"]["needs_implementation"] = True

    def do_run_start(self, state, data):
        self.idle(state)
        require(not state["blocker"], "Resolve the task blocker before execution")
        require(len(state["approved"]) == len(STAGES), "Preparation approvals are incomplete")
        self.approved_integrity(state)
        require(self.remaining(state) > 0, "Execution time exhausted")
        role, actor = data.get("role"), data.get("actor", "").strip()
        require(role in ("implementer", "verifier") and actor, "Run requires role and actual agent identity")
        auth = state["authorization"]
        require(auth["revisions"] == self.snapshot(state), "Authorization is stale")
        require(auth["rounds_used"] < auth["rounds"], "Verification round limit exhausted")
        run_id = uuid.uuid4().hex[:12]
        candidate = state["candidates"][-1] if state["candidates"] else None
        if role == "implementer":
            require(auth["mode"] == "implementation", "Evidence-only authorization does not allow source changes")
            previous = self.implementation_run(state)
            require(not previous or previous["status"] != "completed" or any(c["run"] == previous["id"] for c in state["candidates"]), "Capture the completed implementation before starting another run")
            require(not candidate or self.needs_candidate(state) or candidate.get("verification") and not candidate["verification"]["ready"], "Verify or review the current candidate before implementing again")
            workspace = self.assert_workspace(state, candidate["commit"] if candidate else state["task"]["baseline"])
            auth["needs_implementation"] = True
        else:
            require(candidate and not self.needs_candidate(state), "Capture the authorized implementation before verifying")
            require(candidate["revisions"] == self.snapshot(state), "Candidate preparation revisions are stale")
            require(not any(r["actor"] == actor and r["role"] == "implementer" for r in state["runs"]), "Verifier must be independent from implementation")
            require(not any(r["actor"] == actor and r["role"] == "verifier" for r in state["runs"]), "Every verifier run requires a fresh agent identity")
            require(candidate["verification"] is None, "Request evidence explicitly before rerunning a finished verification")
            object_format = state["task"].get("object_format") or {40: "sha1", 64: "sha256"}.get(len(candidate["commit"]))
            require(object_format in ("sha1", "sha256"), "Candidate has an unsupported Git object format")
            workspace = str(self.path / "runs" / run_id / "workspace")
        run = {"id": run_id, "role": role, "actor": actor, "authorization": auth["id"],
               "workspace": workspace, "candidate": candidate["id"] if role == "verifier" else None,
               "status": "running", "started": now(), "started_epoch": time.time(), "evidence": []}
        state["runs"].append(run)
        if role == "verifier":
            deadline = run["started_epoch"] + auth["minutes"] * 60 - auth["used_seconds"]
            auth["rounds_used"] += 1
            state["pending"] = {"kind": "verifier-checkout", "run": run_id, "workspace": workspace}
            self.record("checkout-intent", {}, state)

            def setup_git(directory, *args):
                state["pending"].update(argv=["git", "-C", str(directory), *args], pid=None)
                self.record("checkout-command-intent", {}, state)

                def started(process):
                    state["pending"]["pid"] = process.pid
                    self.record("checkout-command-started", {}, state)

                return git(directory, *args, timeout=remaining_timeout(deadline), started=started)

            try:
                self.read_blob(candidate["bundle"], deadline=deadline, retain=False)
                setup_git(self.path, "init", "--quiet", "--object-format=" + object_format, workspace)
                ref = f"refs/method/{state['task']['id']}/{candidate['id']}"
                setup_git(workspace, "fetch", "--quiet", str(self.path / candidate["bundle"]["path"]), ref)
                setup_git(workspace, "checkout", "--quiet", "--detach", candidate["commit"])
                remaining_timeout(deadline)
            except ProcessCleanupError:
                raise
            except (Error, OSError, subprocess.TimeoutExpired) as error:
                state["pending"] = None
                summary = ("Execution time exhausted during verifier setup" if isinstance(error, subprocess.TimeoutExpired)
                           else "Verifier setup failed: " + str(error))
                self.finish(state, {"run": run_id, "status": "interrupted", "summary": summary, "processes_stopped": True})
                self.record("checkout-failed", {"error": summary}, state)
                if isinstance(error, subprocess.TimeoutExpired):
                    raise Error(summary) from error
                raise
            state["pending"] = None

    def finish(self, state, data):
        run = self.current_run(state)
        require(run and run["id"] == data.get("run"), "Identify the active run")
        require(data.get("status") in ("completed", "interrupted", "blocked"), "Run status must be completed, interrupted, or blocked")
        require(data.get("summary"), "Record the result or interruption and owned-process disposition")
        require(data.get("processes_stopped") is True, "Confirm all run-owned modifying commands have stopped")
        elapsed = max(0, time.time() - run["started_epoch"])
        state["authorization"]["used_seconds"] += elapsed
        run.update(status=data["status"], summary=data["summary"], finished=now(), seconds=elapsed)
        return run

    def do_run_finish(self, state, data):
        run = self.current_run(state)
        require(run and (run["role"] == "implementer" or data.get("status") != "completed"), "Complete verifier runs using verify with a criterion report")
        if data.get("status") == "completed":
            self.checked_baselines(state, run["workspace"])
        self.finish(state, data)

    def do_evidence(self, state, data):
        run = self.current_run(state)
        require(run and run["id"] == data.get("run"), "Evidence must belong to an active run")
        require(data.get("description"), "Describe the evidence and its limitations")
        evidence = self.blob("runs/" + run["id"], uuid.uuid4().hex[:12] + ".txt", Path(data["file"]).read_bytes())
        evidence.update(description=data["description"], id=uuid.uuid4().hex[:12])
        run["evidence"].append(evidence)

    def do_command(self, state, data, *, workspace=None):
        run = self.current_run(state)
        require(run and run["id"] == data.get("run"), "Command must belong to an active run")
        admitted = time.monotonic()
        remaining = self.remaining(state)
        require(remaining > 0, "Execution time exhausted")
        argv = data.get("argv")
        require(isinstance(argv, list) and argv and all(isinstance(a, str) for a in argv), "Command needs an argv array, not shell interpolation")
        require(data.get("safe_to_record") is True, "Only record commands whose arguments and output contain no secrets or unnecessary sensitive data")
        timeout = min(remaining, data.get("timeout", remaining))
        require(timeout > 0, "Timeout must be positive")
        deadline = admitted + timeout
        operation = uuid.uuid4().hex[:12]
        state["pending"] = {"kind": "command", "id": operation, "run": run["id"], "argv": argv, "pid": None}
        self.record("command-intent", {}, state)
        with tempfile.TemporaryFile() as output:
            stop_requested = threading.Event()
            finished = threading.Event()
            outcome = {"timeout": False, "error": None}

            def cleanup():
                try:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.wait()
                except OSError as error:
                    raise ProcessCleanupError(f"Cannot confirm cleanup of command process group {process.pid}; reconcile the recorded process before continuing") from error

            def monitor():
                try:
                    while process.poll() is None and not stop_requested.is_set():
                        allowance = deadline - time.monotonic()
                        if allowance <= 0:
                            outcome["timeout"] = True
                            break
                        stop_requested.wait(min(allowance, 0.05))
                except BaseException as error:
                    outcome["error"] = error
                finally:
                    try:
                        cleanup()
                    except BaseException as error:
                        outcome["error"] = error
                    finally:
                        finished.set()

            watcher = threading.Thread(target=monitor, name="method-command-" + operation, daemon=True)
            reason = ("Execution time exhausted before process creation" if self.remaining(state) <= 0 else
                      "Command timeout exhausted before process creation" if time.monotonic() >= deadline else None)
            if reason:
                state["pending"] = None
                self.record("command-not-started", {"reason": reason}, state)
                raise Error(reason)
            try:
                process = subprocess.Popen(argv, cwd=workspace or run["workspace"], stdout=output,
                                           stderr=subprocess.STDOUT, start_new_session=True)
            except OSError as error:
                state["pending"] = None
                self.record("command-not-started", {"reason": str(error)}, state)
                raise
            try:
                watcher.start()
                state["pending"]["pid"] = process.pid
                self.record("command-started", {}, state)
                finished.wait()
            finally:
                stop_requested.set()
                if watcher.ident is None:
                    cleanup()
                else:
                    finished.wait()
                    watcher.join()
                if outcome["error"] is not None:
                    raise outcome["error"]
            output.seek(0)
            content = output.read(10 * 1024 * 1024 + 1)
        truncated = len(content) > 10 * 1024 * 1024
        content = content[:10 * 1024 * 1024]
        header = encoded({"argv": argv, "exit_code": process.returncode, "timeout": outcome["timeout"],
                          "truncated": truncated, "candidate": run["candidate"], "at": now()})
        evidence = self.blob("runs/" + run["id"], operation + ".txt", header + b"\n" + content)
        evidence.update(id=operation, description="Command output", exit_code=process.returncode,
                        timeout=outcome["timeout"], truncated=truncated)
        run["evidence"].append(evidence)
        state["pending"] = None
        return evidence, content

    def checked_baselines(self, state, workspace):
        design = self.latest(state, "verification")
        baselines = {}
        for scenario in design["criteria"]:
            if scenario["kind"] == "human":
                continue
            baseline = state.get("test_baselines", {}).get(scenario["id"])
            require(baseline and baseline["revision"] == design["sha256"],
                    "Record a test baseline for " + scenario["id"] + " under the approved verification design")
            require(baseline["outcome"] == scenario["baseline"] or baseline.get("unavailable"),
                    "Unexpected test baseline for " + scenario["id"] + "; investigate and rerun")
            self.check_test_sources(workspace, scenario, baseline)
            baselines[scenario["id"]] = baseline
        return baselines

    def check_test_sources(self, workspace, scenario, baseline):
        for name, (content, executable) in test_sources(workspace, scenario).items():
            record = baseline["files"][name]
            require(content == self.read_blob(record) and executable == record["executable"],
                    "Test changed since its baseline: " + name + "; review it and rerun on the original product")

    def check_baseline_evidence(self, state, baselines):
        runs = {run["id"]: run for run in state["runs"]}
        for scenario_id, baseline in baselines.items():
            if baseline.get("unavailable"):
                continue
            evidence = next((e for e in runs[baseline["run"]]["evidence"] if e["id"] == baseline["evidence"]), None)
            require(evidence and evidence.get("scenario") == scenario_id and evidence.get("outcome") == baseline["outcome"],
                    "Missing matching runner evidence for the test baseline")
            self.read_evidence(evidence)

    def run_test_case(self, state, data, run, workspace, scenario, binding, expected_source=None):
        with tempfile.TemporaryDirectory(prefix="method-result-") as directory:
            fmt = binding["format"]
            report_path = Path(directory) / ("result.xml" if fmt == "junit" else "result.json")
            command = [arg.replace("{report}", str(report_path)) for arg in binding["argv"]]
            if fmt == "unittest":
                module = command.index("-m")
                command[module:module + 2] = [str(Path(__file__).with_name("unittest_report.py").resolve()),
                                              str(report_path), binding["selector"]]
            attempt, output = self.do_command(state, {**data, "argv": command}, workspace=workspace)
            attempt.update(scenario=scenario["id"], selector=binding["selector"], outcome="unverified")
            # The process is finished even if reading the report or validating the tree fails.
            self.record("test-command-finished", {}, state)
            if attempt["timeout"]:
                return attempt
            if fmt in ("junit", "unittest"):
                if (report_path.is_symlink() or not report_path.is_file()
                        or report_path.stat().st_size > 10 * 1024 * 1024):
                    return attempt
                output = report_path.read_bytes()
                attempt["runner_report"] = self.blob("runs/" + run["id"], attempt["id"] + report_path.suffix, output)
            elif attempt["truncated"]:
                return attempt
            attempt["outcome"], attempt["source"] = selected_result(
                fmt, binding["selector"], output, attempt["exit_code"], workspace, scenario["test_files"], expected_source)
            return attempt

    def do_baseline(self, state, data):
        run = self.current_run(state)
        require(run and run["role"] == "implementer" and data.get("run") == run["id"],
                "Record a baseline during the authorized implementation run")
        require(self.remaining(state) > 0 and data.get("safe_to_record") is True,
                "Baseline requires remaining execution time and safe-to-record test files and output")
        design = self.latest(state, "verification")
        scenario = next((s for s in design["criteria"] if s["id"] == data.get("scenario") and s["kind"] == "automated"), None)
        require(scenario and scenario.get("test_files"), "Identify an approved automated scenario with test_files")
        workspace = Path(data.get("workspace", run["workspace"])).resolve()
        previous = state.get("test_baselines", {}).get(scenario["id"])
        require(workspace == Path(run["workspace"]).resolve() or previous or state["candidates"],
                "Establish the first test baseline in the task workspace before product edits")
        check_baseline_tree(workspace, state, design["criteria"])
        sources = test_sources(workspace, scenario)
        argv, selector, fmt = data.get("argv"), data.get("selector"), data.get("format")
        require(isinstance(argv, list) and argv and all(isinstance(a, str) and a and "\n" not in a for a in argv)
                and isinstance(selector, str) and selector.strip() and "\n" not in selector,
                "Identify the test command argv and exact runner selector")
        # An absolute operand can run the implementer's copy from the verifier checkout.
        # Keep URL schemes usable for integration endpoints.
        outside_checkout = r"(?:^|[=@,'\"\s])/|:(?!//)/|(?:^|[/=\s])\.\.(?:/|$)"
        require(not any(re.search(outside_checkout, arg) for arg in argv),
                "Use a runner on PATH or checkout-relative arguments so the test runs against the selected checkout")
        require(fmt in ("tap", "junit", "unittest") and (fmt != "junit" or any("{report}" in arg for arg in argv)),
                "Use unittest, single-assertion tap, or junit with a fresh {report} output path")
        if fmt == "unittest":
            require("-m" in argv and argv[argv.index("-m") + 1:argv.index("-m") + 2] == ["unittest"],
                    "Use the project's Python interpreter with -m unittest")
        else:
            runner = scenario.get("runner", [])
            native = fmt == "junit" and runner and argv[:len(runner)] == runner
            require(native or assertion_script(argv, scenario["test_files"]),
                    "Invoke an approved assertion script directly or use the approved native JUnit runner")
        binding = {"argv": argv, "selector": selector, "format": fmt}
        if previous:
            require(isinstance(data.get("reason"), str) and data["reason"].strip(),
                    "Explain the baseline retry or assertion change")
        unavailable = data.get("unavailable")
        if unavailable is not None:
            require(isinstance(unavailable, str) and unavailable.strip(), "Identify the unavailable environment prerequisite")
            outcome, evidence, source = "unverified", None, None
        else:
            state.setdefault("test_baselines", {})[scenario["id"]] = {
                "revision": design["sha256"], "outcome": "unverified", "run": run["id"]}
            attempt = self.run_test_case(state, data, run, workspace, scenario, binding)
            outcome, evidence, source = attempt["outcome"], attempt["id"], attempt.get("source")
            check_baseline_tree(workspace, state, design["criteria"])
            require(sources == test_sources(workspace, scenario), "Test files changed during baseline execution")
        folder = "runs/" + run["id"] + "/baselines/" + uuid.uuid4().hex
        files = {}
        for index, (name, (content, executable)) in enumerate(sources.items()):
            # Git may normalize working bytes (e.g. text eol=crlf) before storing a blob.
            object_id = git(workspace, "hash-object", "--path=" + name, "--stdin", input=content, raw=True)
            files[name] = {**self.blob(folder, str(index), content), "executable": executable,
                           "git_blob": object_id.decode("ascii").strip()}
        state.setdefault("test_baselines", {})[scenario["id"]] = {
            "revision": design["sha256"], "commit": state["task"]["baseline"], "run": run["id"],
            "binding": binding, "files": files, "outcome": outcome, "evidence": evidence, "source": source,
            "unavailable": unavailable}

    def do_test(self, state, data):
        run = self.current_run(state)
        require(run and run["role"] == "verifier" and run["id"] == data.get("run"), "Identify the active verifier run")
        candidate = state["candidates"][-1]
        require(run["candidate"] == candidate["id"] and not self.needs_candidate(state), "Verify the authorized candidate")
        scenario_id = data.get("scenario")
        baseline = candidate.get("test_baselines", {}).get(scenario_id)
        require(baseline, "Candidate has no test baseline for this scenario; capture a new implementation candidate")
        scenario = next(s for s in self.latest(state, "verification")["criteria"] if s["id"] == scenario_id)
        workspace = run["workspace"]
        require(git(workspace, "rev-parse", "HEAD") == candidate["commit"] and clean(workspace),
                "Run the selected test on the clean candidate")
        self.check_test_sources(workspace, scenario, baseline)
        latest = run.setdefault("latest_tests", {})
        latest[scenario_id] = None
        attempt = self.run_test_case(state, data, run, workspace, scenario, baseline["binding"], baseline.get("source"))
        require(git(workspace, "rev-parse", "HEAD") == candidate["commit"] and clean(workspace),
                "Test changed candidate source; reconcile the verifier run")
        latest[scenario_id] = attempt["id"]

    def do_candidate(self, state, data):
        self.idle(state)
        require_full_history(state["task"]["workspace"])
        require(self.remaining(state) > 0, "Execution limit exhausted")
        require(state["authorization"]["mode"] == "implementation", "Candidate creation requires implementation authorization")
        run = self.implementation_run(state)
        require(run and run["status"] == "completed", "Finish the current authorized implementation run first")
        require(not any(c["run"] == run["id"] for c in state["candidates"]), "This implementation already has a candidate")
        workspace = self.assert_workspace(state)
        expected = state["candidates"][-1]["commit"] if state["candidates"] else state["task"]["baseline"]
        self.assert_workspace(state, expected)
        baselines = self.checked_baselines(state, workspace)
        self.check_baseline_evidence(state, baselines)
        files = {name: blob for baseline in baselines.values() for name, blob in baseline["files"].items()}
        if files:
            eligible = git(workspace, "--literal-pathspecs", "ls-files", "--cached", "--others", "--exclude-standard",
                           "-z", "--", *files, raw=True).split(b"\0")
            require(all(os.fsencode(name) in eligible for name in files),
                    "A checkpointed test file is ignored or missing; include it in the repository before capture")
        paths = data.get("paths", [])
        require(isinstance(paths, list) and all(isinstance(p, str) and not p.startswith(('-', '/', ':')) and '..' not in Path(p).parts and '.tasks' not in Path(p).parts for p in paths), "Provide explicit relative product paths; no traversal or Git pathspec magic")
        self.check_staged_paths(workspace, paths)
        cid = uuid.uuid4().hex[:12]
        state["pending"] = {"kind": "candidate", "id": cid, "run": run["id"], "before": expected, "paths": paths, "commit": None}
        state["pending"]["test_baselines"] = baselines
        self.record("candidate-intent", {}, state)
        if paths:
            git(workspace, "--literal-pathspecs", "add", "--", *paths)
        self.check_staged_paths(workspace, paths)
        require(not git(workspace, "diff", "--name-only") and not git(workspace, "ls-files", "--others", "--exclude-standard"), "Unstaged source remains; reconcile without discarding it")
        tree = git(workspace, "write-tree")
        for name, blob in files.items():
            entry = git(workspace, "--literal-pathspecs", "ls-tree", "-z", tree, "--", name, raw=True)
            mode = b"100755" if blob["executable"] else b"100644"
            if entry.partition(b"\t")[0].split() != [mode, b"blob", blob["git_blob"].encode("ascii")]:
                state["pending"] = None
                self.record("candidate-rejected", {"file": name}, state)
                raise Error("Staged test differs from its baseline: " + name + "; reconcile the preserved index and retry")
        commit = git(workspace, "commit-tree", tree, "-p", expected, input=f"method: candidate {cid}\n")
        state["pending"]["commit"] = commit
        self.record("candidate-created", {}, state)
        self.finish_candidate(state)

    def check_staged_paths(self, workspace, paths):
        staged = git(workspace, "diff", "--cached", "--no-renames", "--name-only", "-z", raw=True).split(b"\0")
        allowed = [Path(p) for p in paths]
        for item in staged:
            if not item:
                continue
            path = Path(os.fsdecode(item))
            require(".tasks" not in path.parts and any(p == Path(".") or path == p or p in path.parents for p in allowed), "Staged changes include an unlisted path: " + str(path) + ". Preserve the index and explicitly review/enumerate it.")

    def finish_candidate(self, state):
        pending = state["pending"]
        run = self.implementation_run(state)
        require(run and run["id"] == pending["run"] and run["status"] == "completed", "Candidate must belong to the current completed implementation run")
        workspace = self.assert_workspace(state)
        require_full_history(workspace)
        commit = pending["commit"]
        require(commit, "Commit outcome is uncertain; inspect Git and resolve explicitly")
        head = git(workspace, "rev-parse", "HEAD")
        require(head in (pending["before"], commit), "Workspace moved during candidate creation")
        require(git(workspace, "write-tree") == git(workspace, "rev-parse", commit + "^{tree}"), "Index changed during candidate creation")
        ref = f"refs/method/{state['task']['id']}/{pending['id']}"
        git(workspace, "update-ref", ref, commit)
        if head != commit:
            git(workspace, "update-ref", "refs/heads/" + state["task"]["branch"], commit, head)
        require(clean(workspace), "Workspace changed during checkpoint; preserve changes and reconcile")
        folder = self.path / "candidates" / pending["id"]
        folder.mkdir(parents=True, exist_ok=True)
        bundle_path = folder / "candidate.bundle"
        git(workspace, "bundle", "create", str(bundle_path), ref)
        bundle = {"path": str(bundle_path.relative_to(self.path)), "sha256": digest(bundle_path.read_bytes())}
        diff = git(workspace, "diff", "--binary", state["task"]["baseline"], commit, raw=True)
        diff_path = folder / "change.diff"
        atomic(diff_path, diff)
        state["candidates"].append({"id": pending["id"], "commit": commit, "run": pending["run"],
                                    "at": now(), "revisions": self.snapshot(state), "bundle": bundle,
                                    "diff": {"path": str(diff_path.relative_to(self.path)), "sha256": digest(diff)},
                                    "verification": None, "test_baselines": pending.get("test_baselines", {})})
        state["authorization"]["needs_implementation"] = False
        state.update(pending=None, accepted=None, delivery=None)

    def do_verify(self, state, data):
        run = self.current_run(state)
        require(run and run["role"] == "verifier" and run["id"] == data.get("run"), "Identify the active independent verifier run")
        require(data.get("processes_stopped") is True, "Confirm verifier-owned commands have stopped")
        require(not self.needs_candidate(state), "Capture the authorized implementation before verifying; finish this stale verifier as interrupted")
        self.approved_integrity(state)
        require(self.remaining(state) > 0, "Execution time exhausted; finish as interrupted instead")
        candidate = state["candidates"][-1]
        require(git(run["workspace"], "rev-parse", "HEAD") == candidate["commit"] and clean(run["workspace"]), "Verifier changed candidate source; record interruption and return corrections to implementer")
        self.check_baseline_evidence(state, candidate.get("test_baselines", {}))
        scenarios = self.latest(state, "verification")["criteria"]
        results = data.get("results", [])
        require(len(results) == len(scenarios) and {r.get("id") for r in results} == {s["id"] for s in scenarios}, "Report every approved verification scenario exactly once")
        evidence = {e["id"]: e for e in run["evidence"]}
        ready = True
        for result in results:
            require(result.get("outcome") in ("pass", "fail", "unverified", "human_pending"), "Invalid result outcome")
            require(result.get("observed"), "Each scenario needs an observed result or precise gap")
            scenario = next(s for s in scenarios if s["id"] == result["id"])
            if result["outcome"] == "human_pending":
                require(scenario["kind"] == "human", "Automated checks cannot be deferred to human acceptance")
            else:
                ready = ready and result["outcome"] == "pass"
            if result["outcome"] in ("pass", "fail"):
                refs = result.get("evidence", [])
                require(refs and all(ref in evidence for ref in refs), "Pass/fail needs evidence from this run")
                if scenario["kind"] == "automated":
                    latest = evidence.get(run.get("latest_tests", {}).get(scenario["id"]))
                    require(latest and latest["id"] in refs and latest["outcome"] == result["outcome"],
                            "The selected test must execute and its latest runner result must support " + result["outcome"])
                for ref in refs:
                    self.read_evidence(evidence[ref])
        findings = data.get("findings", [])
        require(isinstance(findings, list) and all(f.get("id") and f.get("description") and f.get("severity") in ("blocking", "optional") and f.get("status") in ("open", "resolved", "rejected") for f in findings), "Findings need id, description, severity, and status")
        require(all(f.get("resolution") for f in findings if f["status"] != "open"), "Resolved or rejected findings need supported resolutions")
        prior = {}
        for previous_run in state["runs"]:
            for finding in previous_run.get("report", {}).get("findings", []):
                prior[finding["id"]] = finding
        unresolved = {key for key, finding in prior.items() if finding["severity"] == "blocking" and finding["status"] == "open"}
        require(unresolved <= {f["id"] for f in findings}, "Carry forward unresolved blocking finding IDs and their supported resolutions")
        require(len({f["id"] for f in findings}) == len(findings), "Finding IDs must be unique")
        for finding in findings:
            require(finding["id"] not in unresolved or finding["severity"] == "blocking", "Do not downgrade an unresolved blocking finding to optional")
            if finding["status"] != "open":
                refs = finding.get("evidence", [])
                require(refs and all(ref in evidence for ref in refs), "Finding resolution requires evidence from this candidate's run")
                for ref in refs:
                    self.read_evidence(evidence[ref])
        ready = ready and not any(f["severity"] == "blocking" and f["status"] == "open" for f in findings)
        require(data.get("review") and data.get("launch") and data.get("tradeoffs"), "Record review coverage, launch instructions, and implementation tradeoffs")
        report = {"run": run["id"], "candidate": candidate["id"], "ready": ready, "results": results,
                  "findings": findings, "review": data["review"], "launch": data["launch"], "tradeoffs": data["tradeoffs"],
                  "limitations": data.get("limitations", ""), "at": now()}
        report["artifact"] = self.blob("runs/" + run["id"], "verification-" + uuid.uuid4().hex[:8] + ".json", encoded(report))
        candidate["verification"] = report
        run["report"] = report
        data.update(status="completed", summary=data["review"])
        self.finish(state, data)

    def do_accept(self, state, data):
        self.idle(state)
        decision = human(data)
        self.approved_integrity(state)
        candidate = state["candidates"][-1] if state["candidates"] else None
        require(candidate and data.get("candidate") == candidate["commit"], "Acceptance must name the exact candidate commit")
        require(not self.needs_candidate(state), "Capture and verify the authorized implementation before accepting")
        require(candidate["verification"] and candidate["verification"]["ready"], "Candidate lacks required evidence or has blocking findings")
        self.read_blob(candidate["bundle"])
        self.read_blob(candidate["diff"])
        self.read_blob(candidate["verification"]["artifact"])
        self.check_baseline_evidence(state, candidate.get("test_baselines", {}))
        for baseline in candidate.get("test_baselines", {}).values():
            for source in baseline["files"].values():
                self.read_blob(source)
        verified_run = next(r for r in state["runs"] if r["id"] == candidate["verification"]["run"])
        for evidence in verified_run["evidence"]:
            self.read_evidence(evidence)
        require(data.get("requirements") == state["approved"]["requirements"]["sha256"], "Acceptance must bind current requirements")
        require(candidate["revisions"] == self.snapshot(state), "Candidate approvals are stale")
        workspace = self.assert_workspace(state, candidate["commit"])
        require(clean(workspace), "Workspace changed after verification")
        manual = {s["id"] for s in self.latest(state, "verification")["criteria"] if s["kind"] == "human"}
        observations = data.get("observations", {})
        require(set(observations) == manual and all(isinstance(v, str) and v.strip() for v in observations.values()), "Record human observations for every hands-on scenario")
        state["accepted"] = {"commit": candidate["commit"], "requirements": data["requirements"], "human": decision, "observations": observations}

    def do_delivery(self, state, data):
        self.idle(state)
        decision = human(data)
        require(state["accepted"], "Accept an exact candidate before recording delivery")
        require(data.get("candidate") == state["accepted"]["commit"], "Delivery must identify the accepted candidate")
        require(data.get("target") == state["task"]["target"], "Delivery target differs from the task target")
        canonical_target = state["task"].get("target_ref")
        if canonical_target is None:
            canonical_target = target_ref(state["task"]["workspace"], state["task"]["target"])
        require(canonical_target.startswith(("refs/heads/", "refs/remotes/")) and not canonical_target.endswith("/HEAD"), "Delivery needs a canonical branch target")
        mode = data.get("mode")
        require(mode in ("observed", "human_confirmed"), "Delivery mode must be observed or human_confirmed")
        require(data.get("result_commit") and data.get("evidence"), "Record resulting target commit and delivery evidence")
        require(re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", data["result_commit"]), "Record the full resulting target commit hash")
        if mode == "observed":
            workspace = state["task"]["workspace"]
            target_ref(workspace, canonical_target)
            result = git(workspace, "rev-parse", data["result_commit"] + "^{commit}")
            require(result == git(workspace, "rev-parse", canonical_target + "^{commit}"), "Result is not the observed target tip")
            git(workspace, "merge-base", "--is-ancestor", state["accepted"]["commit"], result)
            require(git(workspace, "rev-parse", result + "^{tree}") == git(workspace, "rev-parse", state["accepted"]["commit"] + "^{tree}"), "Target tree differs from the accepted candidate; verify candidate-changing integration before claiming observed delivery")
        else:
            require(data.get("candidate_unchanged") is True, "Human confirmation must attest that delivery preserved the accepted candidate's changes without unverified corrections")
        state["delivery"] = {**data, "human": decision, "at": now()}

    def do_block(self, state, data):
        self.idle(state)
        require(data.get("reason"), "Describe the missing capability or decision")
        state["blocker"] = data["reason"]

    def do_pause(self, state, data):
        self.idle(state)
        human(data)
        state["paused"] = True

    def finish_start(self, state):
        pending = state["pending"]
        require(pending and pending.get("phase") == "publication", "Startup needs explicit investigation before publication")
        workspace = Path(self.assert_workspace(state, state["task"]["baseline"]))
        require(clean(workspace), "Workspace changed during startup; preserve it and reconcile before publication")
        task_dir = workspace / ".tasks"
        locator = task_dir / "locator.json"
        require(not task_dir.is_symlink() and (not task_dir.exists() or task_dir.is_dir())
                and not locator.is_symlink(), "Unsafe task locator; preserve it and reconcile before publication")
        new_locator = encoded({"store": str(self.path.parent.parent), "task": state["task"]["id"]})
        if locator.exists():
            require(locator.is_file(), "Unexpected task locator; preserve it and reconcile before publication")
            current = locator.read_bytes()
            require(current == new_locator or digest(current) == pending["previous_locator_sha256"],
                    "Task locator changed during startup; preserve it and reconcile before publication")
        else:
            require(pending["previous_locator_sha256"] is None,
                    "Previous task locator disappeared; reconcile before publication")
        common = Path(git(workspace, "rev-parse", "--path-format=absolute", "--git-common-dir"))
        exclude = common / "info" / "exclude"
        require(exclude.is_file() and "/.tasks/" in exclude.read_text().splitlines(),
                "Task ignore entry changed during startup; reconcile before publication")
        atomic(locator, new_locator)
        state["pending"] = None

    def do_resume(self, state, data):
        pending = state["pending"]
        if pending and not ((pending["kind"] == "start" and pending.get("phase") == "publication")
                            or (pending["kind"] == "candidate" and pending.get("commit"))):
            data["observation"] = copy.deepcopy(pending)
            data["next"] = "Inspect recorded paths and processes, then resolve explicitly; no action was repeated."
            return
        if state["blocker"]:
            require(isinstance(data.get("resolution"), str) and data["resolution"].strip(),
                    "Record evidence resolving the blocker")
        if state["pending"]:
            if state["pending"]["kind"] == "start" and state["pending"].get("phase") == "publication":
                self.finish_start(state)
            elif state["pending"]["kind"] == "candidate" and state["pending"].get("commit"):
                self.finish_candidate(state)
        require(not self.current_run(state), "An agent run is still recorded active. Reconcile its actor and owned processes, then finish it before resuming.")
        state["paused"] = False
        if state["blocker"]:
            state["blocker"] = None
        if Path(state["task"]["workspace"]).exists():
            self.assert_workspace(state)

    def do_resolve(self, state, data):
        require(state["pending"], "No uncertain operation to resolve")
        human(data)
        require(data.get("resolution") and data.get("processes_stopped") is True, "Record investigation and confirm owned processes stopped")
        require(state["pending"]["kind"] != "candidate" or not state["pending"].get("commit"), "Known candidate commits must be reconciled with resume")
        initialization = state["pending"]["kind"] == "start" and state["pending"].get("phase") == "initialization"
        state["pending"] = None
        state["blocker"] = ("Startup abandoned before initialization completed. Preserve this record and start a new task."
                            if initialization else "Operation abandoned after inspection. Resolve workspace/setup state before continuing.")
