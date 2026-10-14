# Workflow trigger checks — 2026-10-14

Base: `8fdd8191594f9b3efaffe28ed48ee75c1ba466e8`, plus the changes to
`implement`, `adr`, `deliver`, and the matching `tech-spec` wording.

One fresh Codex subagent completed six requests sequentially in separate
temporary projects. It received the named skills, requests, and raw fixtures,
without the approved plan, source diff, assessor criteria, or prior conclusions.
The agent retained skill context between cases; these are not six independent
sessions. Delegation within the trials was unavailable, so implementation
reviews used the documented self-review fallback. The model setting was
inherited; its exact ID was not exposed.

Workspace:
`/var/folders/q0/s5h2flw13y15kyf1b8r0gr540000gn/T/skill-trigger-eval-vivkj51k`

Each named case contains its exact `request.txt`, a read-only `before/` copy,
the resulting `work/` project, and `run.md` with the evaluator's action record.
These are small Python standard-library or Markdown fixtures. No external
services or commits were used. Source digests are retained in `revisions.json`.

| Case | Observed result | Assessment |
| --- | --- | --- |
| `checks-existing` | Fixed a positive-quantity predicate with one comparison change; the four supplied tests were unchanged and passed. | Pass: reused sufficient checks. |
| `checks-gap` | The original one-test suite missed the bug. Added zero-quantity, missing-SKU, and stock-preservation checks; reproduced failures before the fix; all four final tests passed. | Pass: concrete coverage gaps still prompted checks. |
| `adr-local` | The existing export specification already retained its local decision and rationale. No project files changed and no ADR was created. | Pass: later-session reuse did not require another record. |
| `adr-shared` | Created one Accepted ADR and index for a shared API/worker/client retry contract, then linked it from the specification. | Pass: a decision requiring independent history still received an ADR. |
| `risk-covered` | Reused the supplied risk assessment for a storage-envelope change, completed implementation and self-review, and passed three tests. The evaluator reported no blast-radius invocation or restart of completed stages. | Pass: existing analysis was reused. |
| `risk-new` | Used blast-radius for a newly discovered direct storage reader; reproduced count 2 instead of 3, routed that reader through the compatible loader, and passed four tests. | Pass: new downstream evidence still prompted investigation. |

The parent inspected the generated tests, records, and delivery artifacts and
independently reran all four final Python suites with
`python3 -B -m unittest discover -v` from their `work/` directories. The two
storage cases set `TMPDIR="$PWD/.test-tmp"` to keep disposable state inside
the workspace. All 15 tests passed; exact output is in
`independent-tests.txt`. The test additions cover requested behavior and
compatibility; the changes introduced no custom verification framework.

## Repository checks

- All 22 skills passed `.venv/bin/python scripts/validate`.
- All four edited skills passed the skill-creator `quick_validate.py`.
- All 14 tooling tests passed
  `.venv/bin/python -m unittest discover -s tests -v`.
- `git diff --check` passed.

A separate reviewer inspected the final diff, all six case artifacts, source
digests, and supplied check results. Verdict: ready, with no material findings.
The reviewer did not rerun the checks.

## Limits

Each case had one trial in one agent session. This supports the observed
decisions, not general performance, token savings, or behavior across models.
Skill invocation and stage reuse are documented by the evaluator's action
records; those records are not full raw agent transcripts. The parent directly
checked artifacts and reran tests, not the agent's complete decision process.
The `tech-spec` alignment and unchanged acceptance/history safeguards received
source review; explicit ADR requests and project-mandated ADR conventions were
not separately exercised. Serena metadata and empty test-temp parent directories
remain in the code fixtures. Historical evaluation artifacts were unchanged.
