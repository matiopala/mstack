# Method controller internals

These notes explain implementation and compatibility details for maintainers.
For operating Method, use the [command contracts](../skills/method/references/records.md).

## Startup and recovery

Startup records an intent before creating the task branch. It remains pending until
locator publication is durable. A workspace with unfinished startup cannot start
another task, even if no locator exists. A failed final record or locator publication
preserves the previous locator and leaves the new task available for recovery.

Recovery from a startup publication checkpoint checks the workspace, task branch,
baseline, ignore entry, and expected previous or current locator. It does not repeat
branch creation or overwrite an unexpected locator. Earlier startup operations
without this checkpoint require explicit investigation and resolution.

Valid task metadata without a first event is recognized as incomplete initialization.
Inspection does not create files; explicit resolution retains the metadata and
investigation before another start is allowed. Existing caches, artifacts, candidates,
or malformed or partial published history are not treated as metadata-only startup.
Shallow repositories are rejected before startup changes the workspace or store.

## Execution deadlines and cleanup

Verifier admission records the actor, start time, and consumed round before bundle
validation and checkout. Validation checks the remaining budget. Setup Git commands
have bounded timeouts and recorded process-group identities.

Timed setup Git commands use a monotonic deadline and an independent monitor to stop
and reap the process group even when event recording is delayed. File-backed input
and output prevent a delayed callback from blocking pipe transfers. Fast commands
retain successful results; all elapsed setup time still counts against authorization.

The `command` deadline covers intent recording and process setup. Authorization is
checked again before spawning. If it expires first, `command-not-started` is recorded
without creating a process or leaving an uncertain operation. After spawning, the
monitor stops and reaps the process group on exit or deadline independently of event
recording. Output retention is limited to 10 MiB combined output with a truncation
marker.

Recording failure or interruption waits for monitor cleanup. The monitor is joined
on success, failure, and interruption. If cleanup cannot be confirmed, the pending
process identity and active run remain for reconciliation. These mechanisms govern
controller-owned processes; they are not an OS sandbox for native host tools.

## Compatibility

Verifier checkouts use the repository's recorded Git object format, SHA-1 or SHA-256,
regardless of Git's current default. Older records derive the format from the retained
candidate commit without requiring the original workspace.

Candidate eligibility checks the recorded run and authorization links as well as
the implementation flag. This protects older tasks whose flag was cleared when an
implementation run started, before its candidate was captured.

## Record durability

Atomic writes fsync the file and parent directory. A per-task OS lock rejects
concurrent writers and releases on process exit. Intent events precede Git and process
side effects. Recovery can complete known candidate commits idempotently after
checking branch and index state; unknown outcomes require explicit investigation.

Numbered events are authoritative; `state.json` is a rebuildable cache. Candidate
bundles retain code independently of worktree lifetime. The event history preserves
superseded decisions and original failures. No automatic retention purge or controller
self-modification is implemented.
