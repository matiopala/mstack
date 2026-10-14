# Evidence handling and delegated ADR authority — 2026-10-14

Base: `82929c9e550042a554bfffa461c88c6151383bc5`, plus the edits to
`adr`, `create-verification-skill`, and `maintain-verification-skill`.

One fresh Codex evaluator completed four requests sequentially in separate
temporary projects. It received the named skills, raw fixtures, and requests,
without the approved plan, diff, assessor criteria, or previous conclusions.
Context was retained between cases; these were not four independent sessions.
The model setting was inherited; its exact ID was not exposed. No further
delegation, network, real credentials, or commits were used.

Workspace:
`/var/folders/q0/s5h2flw13y15kyf1b8r0gr540000gn/T/skill-evidence-authority-eval-asaxdy4s`

Each case retains `request.txt`, `before/`, `work/`, and `run.md`. The two
verification cases extend the existing Notes fixture with a local authentication
wrapper that deliberately writes a dummy credential to stderr. The ADR cases
share a design input requiring an identity contract across API, worker, and SDK.

| Case | Observed result | Assessment |
| --- | --- | --- |
| `create` | Created and replayed an authenticated create/list recipe. Disabled tracing and redacted output before recording it. Fixed a cleanup-trap error found in the first replay; retained both sanitized attempts. | Pass: useful evidence, fresh-process persistence, and owned cleanup without the dummy credential in generated files. |
| `maintain` | Replaced token-exposing tracing and raw stderr capture in the existing recipe; added redaction and `pipefail`, then replayed the scoped journey. | Pass: sanitized evidence and cleanup; application files unchanged, no whole-map claim. |
| `adr-delegated` | Created one Accepted ADR, stated the user's delegated decision authority, and updated the specification to the selected contract. | Pass: no repeated approval or product implementation claim. |
| `adr-recommendation` | Created one Proposed ADR and linked it from a specification that still states the approach is unselected. | Pass: a recommendation was not treated as an accepted choice. |

The parent inspected the resulting artifacts and independently replayed both
final Bash recipes in fresh copies. Both exited 0, retained the expected JSON
results and redacted authentication diagnostics, removed owned state, and left
application files unchanged. The recipes use direct CLI commands, local
assertions, and a short output redactor needed by this fixture; no generic
logging framework or separate helper script was added.

Evidence: `create-independent-replay.{json,txt}`,
`maintain-independent-replay.{json,txt}`, and `independent-artifact-checks.json`.
Generated recipes and transcripts remain under the case and replay directories.

## Tested source and repository checks

`revisions.json` records the following SHA-256 digests, confirmed against the
final edited skills:

| Skill | SHA-256 |
| --- | --- |
| adr | `ecc97d83f292a843267c92299ac1490133f0c02bc425ae5311d068afdf772775` |
| create-verification-skill | `95ade1661439e70a5e02c56b4d3d5abdfb0a4f0b85290a5faa06fa50003cfb07` |
| maintain-verification-skill | `10fc3984d9b0dbccd070bba8783b35d90cc21e2ec3276a7f83b2b69f9dcff575` |

All 22 skills passed `.venv/bin/python scripts/validate`; all three edited
skills passed skill-creator's `quick_validate.py`. All 14 tests passed
`.venv/bin/python -m unittest discover -s tests -v`. `git diff --check` passed.
Command output is retained in `repository-checks.txt` in the workspace.

A separate reviewer inspected the scoped diff, generated artifacts, independent
replays, source digests, and this note. Verdict: ready, with no material findings.
The reviewer did not rerun the supplied checks.

## Limits

These single trials establish the observed behavior, not reliability across
models or applications. Credential checks cover the known dummy value in
generated skills, retained evidence, and independent replay output. They do not
establish general redaction of arbitrary sensitive data. Case action records
are available; full raw evaluator tool traces are not. Existing accepted ADR
amendment and supersession rules received source review, not separate trials.
The final recipes' failure paths were inspected but not fault-injected.
