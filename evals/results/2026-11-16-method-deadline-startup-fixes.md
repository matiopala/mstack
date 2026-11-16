# Method command deadlines and startup recovery — 2026-11-16

Implemented both approved fixes. Commands use one monotonic deadline covering
intent recording and setup, recheck authorization before spawning, and stop/reap
their process group independently of delayed event recording. Interrupted startup
with valid metadata but no first event is inspectable and can be explicitly
abandoned through `resolve`, allowing a fresh start while retaining the old record.
Existing history, approvals, authorization usage, and CLI arguments are preserved.
No migration or new dependency is required.

## Verification

All **89 repository tests passed**, including ten new regression tests. The final
run took 58.378 seconds. Reproduce:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -v
```

The dashboard HTTP test required local loopback permission. The initial sandboxed
run passed its other 86 tests; its only error was the denied socket bind. The final
run, including the two additional interruption tests, passed with that permission.
All 26 skills passed metadata validation. JavaScript syntax and whitespace checks
passed; scoped whitespace comparisons include the untracked Method files.

- **V01 — Command deadlines and cleanup:** exhaustion during intent recording
  prevents process creation and leaves a recorded cancellation. A real command is
  killed before its delayed side effect while `command-started` recording is still
  blocked. Fast commands keep their successful result despite delayed recording.
  Recording failures and interruption stop/reap owned processes; unconfirmed cleanup
  retains the pending PID and active run. A portable regression covers interrupted
  joins that falsely report a stopped thread. The CLI test sends actual SIGINT while
  cleanup is deliberately delayed.
- **V02 — Startup recovery:** actual CLI `list`, `status`, and `next` inspect
  metadata-only initialization without writing files. Duplicate startup is blocked;
  `resume` does not replay setup; explicit `resolve` preserves metadata and permits
  a fresh task. First startup, replacement of a completed task, an interrupted event
  write, and a valid `feature/HEAD` source branch are covered. Previous records and
  locators remain intact until normal new-task publication. Malformed metadata and
  missing/corrupt established history remain errors; legacy missing optional metadata
  fields are supported.

## Evidence and review

Retained evidence: `/private/tmp/method-deadline-startup-fixes-mz9cd_bc/`.

- `before/` and `changes.patch` identify the original source and final scoped diff.
- `original-defects.log` runs the new regression scenarios against the saved
  pre-change controller and reproduces both original defects.
- `regressions-after.log`, `join-interruption-after.log`,
  `metadata-validation-after.log`, and `source-branch-after.log` retain focused
  passes. Corresponding before logs expose the original and review-discovered gaps.
- `review_sigint_probe.py` and `review-sigint-before.log` reproduce the interrupted
  join defect on Python 3.11/3.12. `review-sigint-after.log` independently verifies
  the unchanged final command-monitor implementation on Python 3.9, 3.11, 3.12,
  and 3.13: the process group is gone before CLI exit, with recovery records retained.
- `full-tests.log`, `metadata-validation.log`, and `final-checks.json` retain the
  final suite results, metadata validation, whitespace results, and fingerprints.

The independent reviewer found an interrupted-join cleanup gap and insufficient
metadata validation, then caught an overly strict source-branch check in that
correction. All were reproduced, fixed, and covered. Final independent verdict:
**ready, with no remaining material findings**. The reviewer inspected the passing
focused checks and the preceding 89-test run; the implementing agent completed the
final full-suite run after the branch-name correction.

Final tested SHA-256 identities:

- `skills/method/scripts/core.py`: `c544e276f7384dc1edfdf78864d597770f019eb52416d1af425c93347442c54e`
- `tests/test_method.py`: `bb30f2f18011f246394d19301fa7091d458f6d6d7ae39ab1f1cab65d4cf9d14b`
- `skills/method/references/records.md`: `066fa53a255d78f4ba11d61c86f6697b488d18c417cdb333758c397334c7541c`

## Limits

All task stores, repositories, actors, human instructions, and processes used for
these checks were disposable fixtures. Clock advancement and write failures are
controlled injections; they do not establish power-loss durability or recovery from
persistent filesystem failure. Native SIGINT probes exercise real CLI subprocesses,
but live Codex/Claude agent journeys were not rerun. No user task store or persistent
staging environment was changed.
