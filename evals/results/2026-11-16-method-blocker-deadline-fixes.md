# Method blocker and verifier deadline fixes — 2026-11-16

Implemented the approved freeze-progress policy and independent verifier setup
deadlines. Blocked tasks cannot change preparation, authorize execution, capture
candidates, accept, or record delivery. Inspection, context imports, pause, blocker
updates, and recovery remain available. Surviving runs may finish as interrupted
or blocked. Resume requires a nonblank resolution before replaying a known pending
operation or clearing a blocker; inspection-only resume remains available.

Timed Git commands now start an independent monitor before recording their process
identity. File-backed streams preserve input/output while recording is delayed.
The monitor stops and reaps the owned process group at its deadline, including
during a blocked recording callback. Failures retain existing recovery and budget
accounting. No schema migration or new dependency is required.

## Verification

All **96 repository tests passed** in 81.024 seconds, including seven new regression
tests. Reproduce with loopback access for the dashboard HTTP test:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -v
```

- Blocked operations reject before records or Git change. Acceptance and delivery
  cannot bypass the guard. Recovery preserves budgets; checkpoint replay requires
  resolution before changing HEAD. Unknown operations remain inspectable.
- A real subprocess cannot perform its delayed side effect while setup-event
  recording is blocked beyond the deadline. The process group is stopped and reaped
  before recording resumes; time and verification-round usage remain consumed.
- Delayed callbacks preserve successful results and large text/binary transfers.
  Existing timeout, interruption, and cleanup-failure checks pass; a new recording
  failure check also confirms monitor and process cleanup.

The new checkpoint and delayed-setup scenarios both failed against the saved
pre-change controller: HEAD moved before blocker resolution, and a subprocess
performed its post-deadline side effect. The first full run exposed only a
case-sensitive error-message assertion in a new test; this was corrected before
the final run. All 26 skills passed metadata validation. JavaScript syntax and
whitespace checks passed, including scoped comparisons of untracked files.

## Review and evidence

An independent reviewer checked the guard, monitor, cleanup, I/O, and recovery
ordering. The reviewer identified the inspection-only resume restriction; it was
corrected and independently retested. Final verdict: ready, no remaining material
findings. The implementing agent ran the final full suite.

Evidence is retained at `/private/tmp/method-blocker-deadline-review/`: baseline
snapshots, `changes.patch`, `fingerprints.json`, and `final-tests.log`.

Final tested identities:

- Controller: `5cb23097ab75edb1c3e37f340cd7091c66190ec2d3cd3b058950bd36ad33236c`
- Tests: `706c7c6f200c8cab8b09775220884b162c2a8599efd93d9ad7b788dc9c57da13`
- Contracts: `1804b6706b5fec4ff0bd94381d0f25159891dc6df2ab53befd5a8e3fdb0361f3`

Tests use disposable repositories, task stores, and processes, with controlled
recording delays and failures. They do not establish power-loss durability or a
live Codex/Claude journey. No user task store or persistent staging environment
was changed.
