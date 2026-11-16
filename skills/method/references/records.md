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

- `start`: `title`, `goal`, absolute `workspace`, explicit Git `target`. Creates a
  dedicated task branch from HEAD, including a clean detached checkout or worktree.
  Complete Git history is required. Shallow repositories are rejected before task
  setup changes the workspace or store; obtain the missing history separately.
  Method never fetches that history automatically. Candidate capture also rejects
  a workspace that became shallow after startup, including resumed captures.
  A detached start retains its baseline commit and records `original_branch: null`;
  an attached start retains the original branch name. Target must be an existing
  local or remote branch;
  the canonical ref is retained. `HEAD`, tags, and revision expressions are rejected.
  Optional `repository` associates a separate clone
  with an existing repository ID and requires `instruction` for that association.
  A clean workspace may start another task after its located task is complete.
  The locator must identify that workspace and the selected store; the previous
  task must have no active run or pending operation. Only `locator.json` is
  replaced, after setup succeeds; previous records and other `.tasks` files remain.
  A failed final record or locator publication preserves the old locator and leaves
  the new task in recovery; inspect it explicitly instead of repeating `start`.
  Startup remains pending until locator publication is durable. The store rejects
  another start for a workspace with unfinished startup, even without a locator.
  Use `list` to find the task and explicit `--store`/`--task` arguments to resume it.
  If initialization stopped after publishing valid task metadata but before its
  first event, inspection reports recovery without creating any files. Another
  start remains blocked until explicit `resolve` abandons the incomplete attempt.
  Resolution retains the metadata and investigation, leaving the workspace and
  existing locator unchanged; a fresh `start` can then proceed.
  Existing caches, artifacts, candidates, or malformed/partial published history
  are not treated as metadata-only initialization.
  Active, blocked, paused, malformed, or unavailable task locators require
  reconciliation before reuse.
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
  A recorded startup publication checkpoint can finish publishing its locator
  after checking the workspace, task branch, baseline, ignore entry, and expected
  previous/current locator. It never repeats branch creation or overwrites an
  unexpected locator. Earlier or legacy startup operations without this checkpoint
  still require explicit investigation and resolution.
  Metadata-only initialization also requires explicit resolution; `resume` records
  the pending recovery state but does not repeat setup or change the workspace.
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
   "requirements":["R01"],"kind":"automated"}
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
Starting or finishing a correction does not satisfy this requirement: capture its
candidate first. Interrupted implementation can resume under the same authorization
and remaining limits. A completed run from an earlier authorization cannot supply
the new authorization's candidate. Status also checks recorded run/candidate links
for older tasks whose implementation flag was cleared when a run started.

`run-start`: `role` (`implementer` or `verifier`), actual fresh agent `actor` ID.
Use `codex:<agent-id>` or `claude:<agent-id>` for new records, following the host
handoff in [hosts.md](hosts.md); preserve existing actor values when resuming.
The returned active run contains its `id`, workspace, and start time. Verifiers
cannot share an identity with any implementer in this task. Each new verifier run
also needs an identity unused by earlier verifier runs, including interrupted runs
and previous authorizations. Existing active runs can still be reconciled normally.
The controller creates their isolated checkout from the candidate bundle. One run
is active at a time.
Verifier checkouts explicitly use the repository's recorded Git object format
(SHA-1 or SHA-256), regardless of Git's current default. Older records derive it
from the retained candidate commit, without requiring the original workspace.

Active time is elapsed wall time while a run is active, including setup and tools.
Verifier admission records its identity, start time, and consumed round before
bundle validation and checkout. Validation checks the remaining budget, and setup
Git subprocesses have bounded timeouts and recorded process-group identities.
An ordinary setup failure or timeout stops/reaps owned commands and records an
interrupted run; its elapsed time and round remain consumed. A fresh verifier may
retry within the remaining limits. Abrupt controller interruption instead leaves
the active run and pending setup operation for explicit process reconciliation.
If stopping or reaping a setup process fails, its run and pending process identity
also remain active for reconciliation; the controller does not claim it stopped.
Timed setup Git commands use a monotonic deadline and an independent monitor that
stops/reaps their process group even while startup-event recording is delayed.
File-backed input/output prevents that delay from blocking pipe transfers. A fast
command keeps its successful result; elapsed setup time still counts against the
authorization. Recording failure or interruption waits for monitor cleanup before
returning, retaining recovery state when cleanup cannot be confirmed.
Finish a run before waiting on a human. An interrupted run remains active until
reconciled, conservatively consuming time; restarting does not erase usage.

`command`: `run`, `argv` (array), `safe_to_record: true`, optional timeout seconds.
Runs in the registered workspace, with a new process group and timeout capped by
remaining authorization time. One monotonic deadline includes intent recording and
process setup. The controller rechecks the authorization budget before spawning;
expiration before spawn records `command-not-started` and returns an error without
creating a process or leaving an uncertain operation. Once spawned, an owned monitor
stops/reaps the process group on exit or deadline independently of delayed event
recording; do not use it to start persistent servers. Records exit code, timeout,
candidate identity, and up to 10 MiB combined output with a truncation marker. Failed
command output remains evidence, never a pass by itself. If recording fails after
process creation, the owned process group is stopped and the child reaped before
the error propagates; any pending operation still needs reconciliation.
The monitor is joined on success, failure, and interruption. If cleanup cannot be
confirmed, the pending process identity and active run remain for reconciliation.
Nonzero child exits appear in the evidence; controller success means the attempt
was recorded.

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
are literal; a directory explicitly includes its descendants. It creates a checkpoint commit with the local
Git identity, retains a named Git ref, self-contained bundle, and baseline diff.
It does not execute commit hooks; run project-required checks explicitly. Empty
checkpoints are permitted for an authorized no-source-change correction.

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
evidence IDs. Findings contain `id`, `description`, `severity` (`blocking`/`optional`),
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

Atomic writes fsync the file and parent directory. A per-task OS lock rejects
concurrent writers and releases on process exit. Before Git/process side effects,
an intent event records the operation. A crash may leave an operation pending;
status exposes it rather than repeating it. Known candidate commits can be completed
idempotently after checking branch/index state. Unknown outcomes require inspection
and explicit resolution. Never reset the workspace during recovery.

The event log preserves superseded authorizations, reports, rejections, and original
failures. Dashboard defaults to current records, with older revisions and raw events
available. Do not delete history during task cleanup. No automatic retention purge
or harness self-modification is implemented.
