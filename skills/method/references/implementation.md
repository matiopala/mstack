# Implementation and candidates

Present the approved artifact revision map and proposed execution limits (default
three verification rounds and 120 active minutes). Record explicit authorization
with `authorize`; a human correction request can supply that instruction directly.
Do not ask again for ordinary repairs within the authorized scope. An evidence-only
authorization never permits source changes.

Register and brief the implementer using [hosts.md](hosts.md). Include this role
contract. The implementer returns changes and evidence to the coordinator; it must
not delegate, change requirements, approve artifacts, or modify Method records.

Implement the smallest complete scoped change using project conventions. For bugs,
reproduce the failure through the affected entry point and test the cause hypothesis.
Reuse existing checks; add tests/helpers for concrete missing coverage. Measure
performance claims. Do not add unrelated abstractions or maintenance work.

The implementer owns product, tests, and necessary verification recipes/helpers.
Any created recipe should contain exact prerequisites, launch, health checks,
interaction, expected outcomes, evidence, and cleanup. Helpers need to simplify
fragile or repeated interactions. Prove the recipe against the app before relying
on it. Product defects must not become weaker recipe expectations.

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
