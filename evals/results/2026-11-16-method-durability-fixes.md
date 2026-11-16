# Method durability and Git compatibility fixes — 2026-11-16

Implemented the four approved controller fixes: recoverable locator publication,
early shallow-repository rejection, preservation of Git object format in verifier
checkouts, and accounting/enforcement of verifier setup time. Command contracts
describe the new behavior. Existing records require no migration; prior approvals,
candidate history, and authorization usage remain intact.

## Verification

All **79 repository tests passed**, including 15 new regression tests. Reproduce:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -v
```

The final run took 52.377 seconds and included the existing dashboard HTTP test,
which required loopback permission. All repositories, stores, human decisions,
agent identities, and owned processes used by these checks are disposable fixtures.
All 26 skills passed metadata validation. JavaScript syntax and whitespace checks
passed; scoped comparisons include the untracked Method files.

- **V01 — Startup recovery:** interruptions before/after locator publication and
  before the final record retain a recoverable task for both first startup and
  replacement of a completed task. Duplicate startup is rejected; repeated resume
  publishes the same task without repeating branch creation. Unexpected branches
  and locators are preserved. Write failures retain existing rollback behavior,
  including interruption after rollback restores the old locator. Older startup
  records without a publication checkpoint still require investigation.
- **V02 — Shallow history:** a depth-one clone is rejected without workspace/store
  changes. Candidate capture and resumed checkpoint completion reject a repository
  that became shallow, before changing refs or creating a bundle. Restoring full
  history allows the same recorded checkpoint to finish and be independently
  checked out. Method does not fetch missing history.
- **V03 — Git object format:** SHA-1 and SHA-256 candidates restore under a
  conflicting Git default, including legacy records without format metadata and
  after deleting the original workspace. Checks confirm the exact commit, source,
  repository format, and successful execution from the verifier checkout.
- **V04 — Setup accounting:** actor identity, run time, and round consumption are
  recorded before bundle validation and checkout. Controlled time advances during
  validation/fetch exhaust the authorization and prevent subsequent commands.
  Real subprocess timeout and interruption checks confirm process-group cleanup
  and child reaping. Failed setup retains usage; retries require a fresh verifier.
  Injected cleanup failure retains the active run and pending PID, blocks new work,
  and requires explicit reconciliation before retrying.

## Evidence and review

Retained evidence: `/private/tmp/method-durability-fixes-4qvssu85/`.

- `before/` and `changes.patch` identify the original files and scoped changes.
- `regressions-before.log` reproduces the original defects using the saved
  controller and eight new regression scenarios.
- `regressions-after.log` and `additional-regressions.log` record focused passes.
- `recovery-regression-before.log`, `rollback-regression-before.log`, and
  `cleanup-regression-before.log` expose three additional recovery gaps found in
  independent review; `review-fixes-after.log` records their fixes and related
  regression checks passing.
- `full-tests.log` contains the final 79-test result. `metadata-validation.log`
  and `final-checks.json` retain validation results and source fingerprints.

The independent reviewer reproduced the three recovery gaps, reviewed their fixes
and regression assertions, and returned **ready, with no remaining material
findings**. The reviewer inspected the final suite output rather than rerunning
the entire suite, and made no file changes.

Final tested SHA-256 identities:

- `skills/method/scripts/core.py`: `81f8d38d3cc76adbd95f7c18566e83761309918115103782b9104d8fc8d94c5c`
- `tests/test_method.py`: `096ecd04b02690ee5d9f53cf9e206c720c00dc391f0e7acd096bb7c2438b74c8`
- `skills/method/references/records.md`: `e9ecb460b6e15fac9641c4da44c849dc880d3048c728076edbf70f3e2a386dc3`

## Limits

Interruption, clock advancement, and cleanup errors are controlled injections;
these checks do not establish power-loss durability or behavior under persistent
filesystem failure. Git formats and owned subprocess cleanup use real local
repositories and processes. No live Codex/Claude agent journey was rerun.
