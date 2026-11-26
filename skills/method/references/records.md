# Controller contracts

Python 3.9+ and Git on macOS/Linux are required. No Python packages or frontend
build are needed. Run `python3 <skill-dir>/scripts/method.py --help`. Options may
precede the command. Mutations take `--input <JSON file>` or `--input -` for stdin.
Every success returns the authoritative task view; errors return JSON on stderr
and a nonzero exit status. `status` and `next` are read-only, as is the dashboard.

The coordinator translates actual human instructions into payloads. Recorded
instructions are an audit trail, not authenticated human signatures. The controller
cannot prevent a process with filesystem access from bypassing it. It does reject
invalid transitions, stale hashes, and missing evidence references through its API.

## Discovery and lifecycle

- `start`: `title`, `goal`, absolute `workspace`, explicit Git `target`. Reuses a
  checked-out branch whose tip equals or is an ancestor of the target, except
  for `main`, `master`, and the target branch itself. A behind branch keeps its
  current tip as the baseline. Other starts create a task branch from HEAD,
  including when HEAD is detached.
  Complete Git history is required at startup and candidate capture, including
  recovery. Obtain missing history separately; Method does not fetch it.
  A detached start retains its baseline commit and records `original_branch: null`;
  an attached start retains the original branch name. Target must be an existing
  local or remote branch; `HEAD`, tags, and revision expressions are rejected.
  Optional `repository` associates a clone with an existing repository ID and
  requires an actual human `instruction`.
  Reusing a workspace requires its located task to be complete and idle, with no
  pending operation, and its locator to match the workspace and selected store.
  Successful setup replaces only `locator.json`; previous records remain.
  Reconcile other locator states before reuse. After interrupted startup, use
  `list` and explicit `--store`/`--task` to inspect recovery instead of repeating
  `start`, even if no locator exists. If valid metadata was published without a
  first event, use `resolve` to abandon the attempt before starting again. This
  preserves metadata, the workspace, and any existing locator; it is not a way
  to discard malformed or partial established history.
- `list`: all tasks in the store. `status`/`next`: task state, pending action,
  events, artifacts, authorization, candidates, and evidence references.
- `serve --port 0`: prints a loopback URL; serves until interrupted. Task URL:
  `http://127.0.0.1:<port>/#task=<id>`. Read-only; no mutation endpoints.
- `import`: `file` (sanitized Markdown), `source` (provenance). Retains context
  without transferring approval or changing stages.
- `block`: `reason`, after finishing active runs. Used for missing capabilities,
  unavailable environments, or consequential decisions.
  A blocker freezes preparation, authorization, execution, candidate capture,
  acceptance, and delivery. Inspection, context imports, blocker updates, pause,
  and recovery remain available. Surviving runs may finish only as interrupted or
  blocked. Rejected progress commands leave records and Git state unchanged.
- `pause`: actual human `instruction`; first stop and finish owned active runs.
- `resume`: reconciles a known checkpoint transaction or reports an uncertain
  operation without repeating it. Use `resolution` to clear a resolved blocker.
  A blocked task requires a nonblank resolution before replaying any known pending
  operation. Failed recovery preserves the blocker and existing execution budget.
  Known candidate commits and startup publication checkpoints can finish after
  state checks. Startup recovery does not repeat branch creation or overwrite an
  unexpected locator. Earlier startup failures, including metadata-only attempts,
  require investigation and `resolve`; `resume` only records their pending state.
  An active recorded run requires actor/process reconciliation and `run-finish`.
- `resolve`: for an uncertain operation with no known checkpoint commit, requires
  `instruction`, investigative `resolution`, and `processes_stopped: true`. Preserves
  files and index, abandons the operation, and leaves a blocker until workspace/setup
  state is reconciled. Never use this to bypass a live command or ignore unknown work.

Store selection uses `--store`, then nonempty `METHOD_HOME`, then the current
workspace's `.tasks/locator.json`, then `~/.local/share/method`. Empty `METHOD_HOME`
behaves as unset. Task commands use `--task`, or inherit the locator's task ID only
when its normalized store path matches the selected store. An override selecting
another store requires `--task` for task commands. Read-only commands do not create
or repair store files. Do not register sample tasks in the user's store.

## Artifacts and decisions

`submit` requires `stage` and `file`. Stages are `interview`, `exploration`,
`requirements`, `verification`, `plan`. Files are copied into immutable revisions.
Earlier stages must already be approved or waived. Resubmission invalidates this
and later approvals and all execution/acceptance authority.

Requirements include structured `criteria` matching the readable document:

```json
{"stage":"requirements","file":"/tmp/requirements.md","criteria":[
  {"id":"R01","text":"New notes remain available after restarting."}
]}
```

Verification scenarios include their requirement references and type:

```json
{"stage":"verification","file":"/tmp/verification.md","criteria":[
  {"id":"V01","text":"Create a note and list it in a fresh process.",
   "requirements":["R01"],"kind":"automated","baseline":"fail",
   "test_files":["tests/test_notes.py"]}
]}
```

`decide` requires `stage`, `decision` (`approved`, `rejected`, `skipped`), and the
actual human `instruction`; optional `source` identifies its conversation message.
Approval/rejection requires exact `revision` and `sha256` from `status`. Waivers
require `reason`, are limited to interview/exploration/plan, and create readable
artifacts. Requirements and verification cannot be waived.

The revision's `sha256` binds its stage, revision number, structured criteria,
parent revision hashes, and document-content digest. Identical Markdown with
different criteria or approvals is therefore a different revision identity.
`content_sha256` separately checks the retained document bytes.

## Authorization and execution

`authorize` requires `instruction`, `revisions` (all five stage→approved SHA-256
values), optional `source`, `mode` (`implementation` default, or `evidence`), and
optional positive integer `rounds`/`minutes` (defaults 3/120). A correction request
can supply the instruction. A new authorization explicitly resets its limits;
resume and repairs do not. Evidence requests preserve the candidate; implementation
authorization requires a new implementation run/candidate before verification.
Interrupted implementation can resume within the remaining budget. Capture the
candidate from a completed run under the current authorization before verifying;
an earlier authorization's run cannot supply it.

`run-start`: `role` (`implementer` or `verifier`), actual fresh agent `actor` ID.
Format and register actor identities using [hosts.md](hosts.md).
The returned active run contains its `id`, workspace, and start time. Verifiers
cannot share an identity with any implementer in this task. Each new verifier run
also needs an identity unused by earlier verifier runs, including interrupted runs
and previous authorizations. Existing active runs can still be reconciled normally.
The controller creates their isolated checkout from the candidate bundle. One run
is active at a time.

Active time is elapsed wall time while a run is active, including setup and tools.
Verifier setup consumes a round before bundle validation and checkout. An ordinary
setup failure or timeout stops owned commands and records an interrupted run;
time and the round remain consumed. A fresh verifier may retry within the limits.
Abrupt interruption or unconfirmed process cleanup leaves recovery state: reconcile
the recorded run and processes before continuing. Finish runs before waiting on a
human; a run still recorded active continues consuming time across restarts.

`command`: `run`, `argv` (array), `safe_to_record: true`, optional timeout seconds.
Runs in the registered workspace. Its timeout includes recording and process setup
and is capped by remaining authorization time. Expiration before process creation
records `command-not-started` and returns an error without a pending operation.
The process group is stopped on command exit or timeout, so do not start persistent
servers through this command. Records exit code, timeout, candidate identity, and
up to 10 MiB combined output with a truncation marker. Nonzero exits remain evidence;
controller success means the attempt was recorded, not that the check passed.
Recording failures trigger process cleanup; any pending operation still requires
reconciliation. Unconfirmed cleanup retains the process identity and active run.

`evidence`: `run`, sanitized text `file`, `description` including limitations. Copies
native tool/browser/manual observations into retained evidence and returns its ID.
Never submit credentials or unnecessary personal data. The controller does not
claim universal secret redaction; inspect/sanitize material before importing it.

`run-finish`: `run`, `status` (`completed`, `interrupted`, `blocked`), `summary`,
`processes_stopped: true`. Verifier success must use `verify`, not run-finish.

`candidate`: `paths` (explicit relative changed paths; include deleted files).
Requires a completed implementer run, authorized baseline/previous candidate HEAD,
and no staged/unstaged/untracked source outside the explicit path enumeration.
Staged paths outside the enumeration are rejected without discarding them. Paths
are literal; a directory includes its descendants. Creates a checkpoint commit with
the local Git identity, retaining a named ref, self-contained bundle, and baseline diff.
It does not execute commit hooks; run project-required checks explicitly. Empty
checkpoints are permitted for an authorized no-source-change correction.

## Test baselines and candidate runs

`baseline` runs during an active implementer run and before product edits. Bind
a scenario to its actual command and exact runner case. For example, for a
file with one Python test:

```json
{"run":"implementer-run-id","scenario":"V01","safe_to_record":true,
 "format":"unittest","selector":"test_notes.NotesTests.test_persistence",
 "argv":["python3","-B","-m","unittest","discover","-s","tests","-p","test_notes.py","-v"]}
```

The controller requires the original task commit and permits tracked, staged,
or untracked changes only in approved test files. List shared fixtures and
helpers that determine the assertion in every scenario that uses them. The
checkpoint retains the exact files, executable bits, command, and baseline
outcome. A mismatched result blocks completion. Investigate the diagnostic and
retry with a `reason`. If a required environment is unavailable, include
`unavailable` with the precise prerequisite to retain the runnable test and
baseline gap. No pass or failure is credited for that baseline.

On a revision, pass a `reason` and, if needed, an absolute `workspace` pointing
to a separate checkout at the original task commit with the revised tests.
The first baseline for a new task uses the registered implementation workspace.
The current files must still match when finishing implementation, capturing
the candidate, and testing it. Include the tests in the candidate's paths.

`test` takes `run`, `scenario`, `safe_to_record: true`, and optional `timeout`.
It uses the checkpointed argv in the independent verifier checkout. Configure
the project's usual test environment, including on-demand prerequisites.
Use a runner on PATH or a checkout-relative executable and operands. Configure
external service locations through the project's test environment. Both commands
retain output and enforce the command timeout. A successful CLI recording can contain a failed or
unverified test. Inspect the returned evidence's `outcome`.

For JUnit, approve the native test runner in the scenario's optional `runner`
argv prefix (for example `["python3","-m","pytest"]`), or use an approved
repository script. For TAP, execute the approved script by checkout-relative
path, or pass it as the script operand of Python, Node, Ruby, Perl, PHP, or a
shell interpreter. Python can take `-B`, `-I`, or `-u` first. Inspect scripts
for real assertions and use a shebang for other interpreters.

| Format | What establishes execution |
| --- | --- |
| `junit` | Write fresh XML to the literal `{report}` placeholder (e.g. `--junitxml={report}`). Select exactly one `classname.name`, or `name` without a classname. Reported source files must be approved, and a source identified on the baseline must match on the candidate. An assertion failure counts as red. A runner-reported error or skip is unverified. |
| `unittest` | Use the project's Python with `-m unittest` and the fully qualified case ID. Method adds a standard-library result reporter and checks that the case ran exactly once from an approved file. A fixture failure or skipped case is unverified. |
| `tap` | A standalone assertion script emitting a one-test TAP plan (`1..1`) and `ok 1 - <selector>` or `not ok 1 - <selector>`. Diagnostic comment lines are allowed. |

An executed passing case also requires successful process exit. An expected
negative application action belongs inside a test that asserts that behavior.
For JUnit reporters that omit file attribution, choose a unique case ID and
review the bound runner command to confirm it selects the intended test.
A plain transcript can supplement a result. It cannot establish an automated
pass. If a runner uses another format, use its JUnit reporter or an assertion
script that emits the one-test TAP result.

Existing task history and completed deliveries remain readable. To continue
an older task whose approved automated scenarios lack test files and baseline
expectations, revise the verification and downstream preparation and authorize
a new implementation candidate. Prior observations remain historical evidence.

## Verification, acceptance, delivery

`verify` takes the active verifier `run`, `processes_stopped: true`, and:

```json
{
  "run":"actual-run-id",
  "processes_stopped":true,
  "results":[{"id":"V01","outcome":"pass","observed":"A fresh process listed the saved note.",
              "evidence":["retained-evidence-id"]}],
  "findings":[],
  "review":"Reviewed persistence and failure handling in the baseline diff.",
  "launch":"Run the documented application command from the candidate checkout.",
  "tradeoffs":"Reuses the existing storage format.",
  "limitations":"No cross-machine concurrency was exercised."
}
```

Every scenario appears exactly once. Outcomes: `pass`, `fail`, `unverified`, or
`human_pending` for human scenarios only. Pass/fail requires this run's retained
evidence IDs. Automated pass/fail must match the latest `test` result for that
scenario and cite its evidence ID. Findings contain `id`, `description`, `severity` (`blocking`/`optional`),
`status` (`open`/`resolved`/`rejected`), and a supported `resolution` when not open.
Resolved/rejected findings also need `evidence` IDs from the current run. Carry
forward unresolved blocking finding IDs; do not silently omit or downgrade them.
Reports are retained even when not ready. Readiness requires automated passes and
no open blocking findings; human-pending scenarios remain for human review.
After a finished evidence-only report is not ready, status requests explicit
authorization for further evidence collection or implementation corrections.
Neither starts automatically; the candidate, report, and consumed budget remain.
An interrupted verifier without a submitted report may retry within the existing
authorization's remaining limits.
If final report recording crosses the time limit after verification was admitted,
the finished report still routes to human review or an authorization decision.
Measured usage is retained; this does not grant any further execution.

`accept`: exact `candidate` commit, current approved `requirements` hash,
actual human `instruction`, optional `source`, and `observations` mapping every
human scenario ID to the human's concrete observation. Use `{}` when none exist.

`delivery`: `candidate`, configured `target`, `result_commit`, `evidence`, actual
human `instruction`, optional `source`, and `mode` (`observed`/`human_confirmed`).
Observed mode checks local target-tip equality, candidate ancestry, and identical
source trees; describe remote freshness in evidence. This conservative check does
not accept a merge-resolution edit merely because the candidate is an ancestor.
Human-confirmed mode requires `candidate_unchanged: true` recording the human's
assertion that no unverified correction changed the accepted work, including
squash/rebase delivery. It does not claim independent verification.

## Records and recovery

`task.json` retains initial identity; immutable numbered `events/*.json` are the
authority. Each event carries a timestamp, command payload, and changed state fields.
`state.json` is only a rebuildable cache. Submitted documents and run evidence have
SHA-256 digests. Candidate bundles retain code independently of worktree lifetime.

Concurrent writers are rejected. A crash may leave a pending operation; inspect it
with `status` and follow the `resume`/`resolve` contracts above. Never reset the
workspace during recovery.

The event log preserves superseded authorizations, reports, rejections, and original
failures. Dashboard defaults to current records, with older revisions and raw events
available. Do not delete history during task cleanup. No automatic retention purge
or harness self-modification is implemented.
