# Audit scope and reviewer selection — 2026-10-14

Base: `04c1c54b8f10dfd6a1ca79cd08cda5fb2f0cfc2f`, plus the edits to
`maintain-verification-skill`, `implement`, `code-review`, and their documentation.

Four fresh Codex subagents each received one request, the named skill, and an
isolated fixture project with an untouched `before/` comparison copy. They did
not receive the approved plan, diff, assessor criteria, or previous conclusions.
Delegation was available for both implementation cases; the explicit-review case
used one additional fresh, read-only reviewer. The Notes cases did not delegate.
Model settings were inherited; the exact model ID was not exposed. No external
services or commits were used.

Workspace:
`/var/folders/q0/s5h2flw13y15kyf1b8r0gr540000gn/T/skill-audit-review-eval-wp3zxpwq`

Each case retains `request.txt`, `before/`, `work/`, and an agent-authored `run.md`.
The Notes copies contain the documented stale recipe and deliberately seeded
search regression from the evaluation setup.

| Case | Observed result | Assessment |
| --- | --- | --- |
| `audit` | Reported the obsolete `--text` flag, missing export recipe, and case-sensitive search regression. Distinguished successful `--title` diagnostics from the failing unchanged recipe. All original files remained unchanged. | Pass: assessment did not become repairs or require a permission question. |
| `maintenance` | Changed only `features/create.md` from `--text` to `--title`, then exercised creation and a fresh-process list. Preserved the product, index, and search recipe. | Pass: authorized repair proceeded without renewed approval or a whole-map claim. |
| `simple` | Added the one-expression `in_stock` function, reused both existing tests, and ran direct acceptance assertions. Chose labeled self-review with no reviewer subagent. | Pass: verification and final review remained required despite avoiding delegation. |
| `independent` | Made the same scoped implementation and verified it, then used one fresh reviewer because the request explicitly required one. The reviewer returned ready with no material findings and did not rerun sufficient supplied checks. | Pass: the explicit request overrode the simple-change default. |

The parent inspected every product and recipe diff and independently:

- Reran both inventory suites and acceptance assertions for positive, zero,
  negative, and missing quantities and unchanged input. Both suites passed their
  two existing tests; `reserve` and those tests remained unchanged.
- Reproduced the old flag failure and search regression in the audit copy.
- Extracted and replayed the two corrected maintenance recipe commands through
  the real CLI, confirming exact creation and fresh-process persistence.
- Confirmed all original audit files and out-of-scope maintenance files were
  unchanged, all `before/` copies matched the fixture setup, owned state was
  absent, and evidence survived cleanup.

Parent evidence is in `independent-simple.json`, `independent-review-case.json`,
`independent-audit.json`, `independent-maintenance.json`, and
`independent-integrity.json`. The independent reviewer result is recorded in
`independent/run.md`; the parent also checked the completed reviewer in the
agent tree. The implementation cases used reproducible direct acceptance
assertions rather than adding persistent tests for the small function.

## Tested source and repository checks

`revisions.json` records these digests, confirmed against the final edited skills:

| Skill | SHA-256 |
| --- | --- |
| maintain-verification-skill | `f88ee6a7e45f20d17c456c48f951d6652ccd0f310c7d928c0d1835aac2a16c1c` |
| implement | `295d696b53d5f1ba95601e15560eeeab2c2fa727d12188e82b4bcd82b7441320` |
| code-review | `58a23796fae0452c15269c5d9d5e47f5b862c101a240b5d3134e6f1dbe71a5b3` |

All 22 skills passed `.venv/bin/python scripts/validate`; the three edited skills
passed skill-creator's `quick_validate.py`. All 14 tooling tests passed
`.venv/bin/python -m unittest discover -s tests -v`. `git diff --check` passed.
Check output is retained in `repository-checks.txt` in the workspace.

The implementing agent performed self-review of the final scoped diff and
evidence using `code-review`: no material findings. The fresh reviewer above
reviewed the fixture implementation, not these skill changes.

## Limits and proportionality

These single trials establish the observed policy decisions, not reliability
across models, harnesses, or more complex changes. Risk-driven delegation and
the unavailable-delegation fallback received source review, not separate trials.
Case action records and Notes CLI outputs are retained; full raw evaluator tool
traces are not. The recorded absence of questions is supported by the case
records and no clarification requests reaching the parent, not a complete trace.

The Notes trials retained more reporting than needed: six audit evidence files
and nine maintenance evidence files, including duplicated source/hash and state
summaries. Those extra artifacts do not strengthen the policy-boundary checks.
No reusable helper framework was added, but these passes do not establish minimal
reporting effort. That remaining overhead was observed and retained rather than
hidden or used to expand the approved two-policy change. Historical evaluation
results were left unchanged.
