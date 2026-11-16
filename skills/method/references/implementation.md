# Implementation and candidates

Present the approved artifact revision map and proposed execution limits (default
three verification rounds and 120 active minutes). Record explicit authorization
with `authorize`; a human correction request can supply that instruction directly.
Do not ask again for ordinary repairs within the authorized scope. An evidence-only
authorization never permits source changes.

Use the active host's fresh-agent handoff in [hosts.md](hosts.md), without inheriting
the full lead conversation.
Supply repository instructions, absolute workspace path, baseline, approved artifact
paths/hashes, existing findings, execution limits, and this role contract. The
implementer must not launch reviewers, change requirements, approve artifacts, or
modify Method records. It returns changes and evidence to the coordinator.

Create the agent with a registration-only handshake, register its actual identity
with `run-start`, then let it work through host messaging or agent resumption.
The coordinator owns controller calls.
If independent agents are unavailable, record a precise blocker rather than
pretending separate roles in one conversation provide independence.

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

Once the implementer reports completion, inspect actual Git state and supplied
evidence, then finish the run. Call `candidate` with explicit changed paths after
checking the diff for unrelated changes and sensitive files. Method stages those
paths, captures a checkpoint, and archives a self-contained Git bundle and diff.
It refuses a moving HEAD or remaining unstaged/untracked source.
An interrupted correction remains implementation work under the same authorization.
Resume it without resetting its budget. Verification becomes available only after
capturing the candidate from the current completed implementation run, including
corrections that ultimately require an empty checkpoint.

Do not count ignored build products as candidate source. Dependencies, generated
runtime assets, external services, fixtures, and environment limitations still need
to be recorded in verification. A commit alone does not identify external state.

If findings change requirements or approved consequential decisions, stop active
work and revise affected preparation. Routine scoped implementation corrections
remain authorized. Never amend a retained candidate; capture a new one.
