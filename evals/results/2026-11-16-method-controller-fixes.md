# Method controller review fixes — 2026-11-16

Implemented the four approved review fixes: command cleanup covers recording
failures, explicit store selection takes precedence over workspace discovery,
new verifier runs require unused identities, and clean detached checkouts can
start tasks. Existing records require no migration. Command contracts document
the resulting behavior.

## Verification

All 64 repository tests passed, including five new regression tests. Reproduce:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -v
```

The dashboard test required loopback permission. Test repositories, task stores,
home directories, process groups, agent identities, and human decisions are
disposable fixtures. Evidence is retained in
`/private/tmp/method-four-fixes-jbrgus32/`:

- `before/` and `changes.patch` identify the pre-fix source and scoped changes.
- `regressions-before.log` shows the four regression tests exposing the original
  failures. `regressions-after.log` shows those same tests passing after the fixes.
- `full-tests.log` records the final 64-test run, including the additional legacy
  verifier reconciliation test.
- `metadata-validation.log` and `whitespace-checks.json` retain metadata and
  whitespace results. All 26 skills passed validation; JavaScript syntax passed
  `node --check skills/method/ui/app.js`. Whitespace checks include comparisons
  against the pre-fix snapshot because Method is untracked in this checkout.

Approved verification scenarios:

- **V01 — Command cleanup:** injected failures before and after recording
  `command-started` stop a real subprocess group and reap the child before the
  original exception propagates. A fresh store read retains the pending operation
  and active run; explicit reconciliation still works.
- **V02 — Store selection:** actual CLI calls prove flag/environment/locator/default
  precedence, normalized matching, empty-environment behavior, and explicit task
  selection across stores. An ambiguous mutation is rejected without changing
  either task; an explicit mutation changes only the selected alternate task.
- **V03 — Verifier freshness:** reused identities are rejected across failed and
  interrupted rounds and authorization changes without consuming budget or
  creating a checkout. Fresh verifiers succeed, implementer reuse remains valid,
  and a simulated legacy active verifier can be reconciled without rewriting
  earlier history.
- **V04 — Detached startup:** real detached clones and linked worktrees start
  tasks with the same baseline and product source, a dedicated branch, and a
  published locator. Linked worktrees retain the shared repository identity;
  attached checkouts retain their original branch name.

Final tested SHA-256 identities:

- `skills/method/scripts/core.py`: `28a3aa67a9392199fac816f9fc3f8310eb02b74baaf0df4db8e0a4ab3ab7088e`
- `skills/method/scripts/method.py`: `37e37256c4605bd0e4de36c4a12ee430a9beb88e74fcf6d0ad869c23bf5c5ff5`
- `tests/test_method.py`: `e21251ce666876ca45b5578ad0e42076bc14b44b1bfb27b5cc030ff6c85eb7a6`

## Review

An independent read-only reviewer returned ready with no material findings after
inspecting the scoped diff, lifecycle code, regression evidence, and final suite
results. The reviewer did not rerun the tests.

## Limits

Recording failures are injected at controlled boundaries; these checks do not
simulate power loss or a killed controller. Legacy identity compatibility uses
a constructed historical fixture. No live Codex/Claude agent journey was rerun.
