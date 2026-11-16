# Method review fixes — 2026-11-16

Implemented the three approved fixes: corrections require their own captured
candidate, finished non-ready evidence-only reports request authorization, and a
completed task's locator can be replaced when starting another task safely.
Existing event history and recorded human decisions are retained.

## Verification results

All 59 repository tests passed, including 14 new Method regression tests. Run:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -v
```

The HTTP test required local loopback permission. All test repositories, stores,
agent identities, and human instructions are disposable fixtures. Full output:
`/private/tmp/method-review-fixes-3prkdnb4/final-tests.log`.

- **V01 — Corrections:** interrupted corrections with and without source edits
  resume under the same authorization and measured budget. Old candidates cannot
  advance; completed corrections require capture. Older early-cleared flags and
  premature verifiers recover without rewriting events. A completed implementation
  can be captured after a stale verifier is reconciled. Cross-authorization capture
  is rejected; known checkpoint recovery remains idempotent and preserves limits.
- **V02 — Evidence decisions:** fail, unverified, and blocking reports request
  explicit evidence or implementation authorization. Passing reports reach human
  review. Interrupted verification without a report can retry with its original
  remaining budget. A controlled clock boundary confirms finished reports retain
  their decision when final recording crosses the time limit; measured usage and
  execution limits are preserved.
- **V03 — Sequential tasks:** the actual CLI starts a new task after delivery and
  preserves the previous task's records, bundle, and other `.tasks` files. Active,
  paused, blocked, unknown, malformed, wrong-store, and wrong-workspace locators are
  rejected. Registry/task locks prevent replacement during another operation.
  Injected branch, final-record, and locator-publication failures preserve the old
  locator; final-record/publication failures leave the new task in recovery.

All 26 skills passed `.venv/bin/python scripts/validate`. JavaScript syntax and
whitespace checks passed, including comparisons against the pre-change snapshot
because the Method addition is untracked.

## Review and limits

An independent reviewer identified legacy capture recovery, startup publication
ordering, and report-finalization routing gaps. These were fixed and covered by
regressions. The reviewer independently reran nine focused checks successfully.
Final independent verdict: ready, with no remaining material findings.

These checks exercise real Git operations, controller transitions, the CLI, and
the existing HTTP test. Clock and write-failure probes simulate specific boundaries;
they do not establish power-loss durability or recovery from persistent filesystem
failure. Live Codex/Claude agent journeys were not repeated.

Final tested SHA-256 identities:

- `skills/method/scripts/core.py`: `14a329def0d2de246a1ee670f933e3cc05df9499cc232dad8be7c95393424005`
- `tests/test_method.py`: `d4586144ca72bfd12ff417a9f40b7cac63b2906a58213aa7fac95370d3957ef8`
