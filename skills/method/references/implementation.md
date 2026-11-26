# Implementation and candidates

Present the approved artifact revision map and proposed execution limits (default
three verification rounds and 120 active minutes). Record explicit authorization
with `authorize`; a human correction request can supply that instruction directly.
Do not ask again for ordinary repairs within the authorized scope. An evidence-only
authorization never permits source changes.

Register and brief the implementer using [hosts.md](hosts.md). Include this role
contract. The implementer returns changes and evidence to the coordinator; it must
not delegate, change requirements, approve artifacts, or modify Method records.

Brief the implementer to select or write the approved tests first, then yield
before editing product code. Use the project's normal suite. The coordinator
runs `baseline` for each automated scenario and inspects the runner outcome.
For a change or bug, confirm the assertion failed for the intended reason.
Preservation tests should pass. Investigate an unexpected result. A required
on-demand environment can be recorded as unavailable with its exact prerequisite.
See the [test command contracts](records.md#test-baselines-and-candidate-runs).

After the checkpoints, implement the scoped product change. Keep reusable tests
in the repository, document their normal invocation and any on-demand setup,
and include new tests and fixtures in the candidate. Review changed assertions
and refresh their checkpoints on the original product. When the task workspace
already has product edits, use a separate baseline checkout with the revised
test files. Preserve the existing workspace. Reuse current checkpoints on retries.

Use `command` for finite checks with safe-to-record output; it tracks process groups,
timeouts, and evidence. For native/browser tools or long-running application servers,
retain actual handles, identity/build checks, observations, and sanitized evidence.
Before `run-finish`, stop or reconcile every owned modifying process. Record failed
attempts as well as their resolutions. Never commit from the implementer; Method
captures checkpoint commits. Do not push, open PRs, or merge.

Once the implementer reports completion, inspect Git state, the diff, and evidence
for unrelated changes or sensitive files, then finish the run. Call `candidate`
with explicit changed paths to retain a checkpoint, bundle, and diff. See
[candidate requirements](records.md#authorization-and-execution) for Git constraints.
Resume interrupted corrections under the same authorization. Capture a candidate
from the current completed implementation run before verification, even when the
correction requires an empty checkpoint. Never amend a retained candidate.

Do not count ignored build products as candidate source. Dependencies, generated
runtime assets, external services, fixtures, and environment limitations still need
to be recorded in verification. A commit alone does not identify external state.

If findings change requirements or approved consequential decisions, stop active
work and return them to the coordinator for preparation revisions.
