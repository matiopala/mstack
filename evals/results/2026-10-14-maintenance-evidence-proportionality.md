# Maintenance evidence proportionality — 2026-10-14

Base: `1112f77926a464422b7f71d4531cd229c0aea42b`, plus the focused evidence
guidance change in `maintain-verification-skill`.

One fresh Codex evaluator ran the existing **Scoped verification maintenance**
case in an isolated Notes fixture. It received the request, named skill, and
raw project, without the plan, previous outputs, or assessor criteria. Its
model setting was inherited; the exact model ID was not exposed. No further
delegation, network, or commits were used.

Workspace:
`/var/folders/q0/s5h2flw13y15kyf1b8r0gr540000gn/T/skill-maintenance-evidence-eval-6p0hyvgu`

The workspace retains `request.txt`, the untouched `before/` project, `work/`,
and `skill-under-test.md`. The tested skill SHA-256, confirmed against the final
repository file, is:
`4bafa78721791186d69506094f73bfae7cae9b4f8903fe4e70786f35f248dd0d`.

## Observed outcome — pass

The evaluator changed only `features/create.md`, replacing `--text` with
`--title`. It observed the old command fail with exit 2, then replayed the
corrected command and a fresh-process list with the expected ID and exact title.
Owned state from both runs was removed. Its final response reported a scoped
pass and left search and export explicitly unverified.

Evidence under `work/artifacts/create-list-maintenance/` consists of:

- `verification.txt`: direct shell/CLI commands, expected and observed results,
  exit codes, source identity, persistence, cleanup, and scope limits.
- `unchanged.sha256`: a standard checksum manifest actually used to verify that
  product code and unrelated instructions remained unchanged.

The transcript and manifest serve distinct purposes. No helper script, custom
reporting protocol, or separate state/cleanup summaries were added. This is a
proportionality pass based on their contents and use, not a file-count threshold.

The parent inspected every resulting file, confirmed the baseline matches the
seeded fixture and only the requested flag changed, and independently replayed
the two corrected recipe commands in a fresh `replay/` copy. Both exited 0 with
empty stderr and exact expected JSON; doctor counts changed from 0 to 1. Persisted
state matched the fresh list, cleanup completed, and product files stayed
unchanged. Commands and observed results are in `independent-replay.txt`.

## Repository checks and limits

Skill quick validation and validation of all 22 repository skills passed. All
14 existing tooling tests passed. Output is retained in `repository-checks.txt`.
The implementing agent self-reviewed the scoped diff and artifacts; no material
findings remained. The fresh evaluator tested behavior, not the skill change
as an independent code reviewer.

This single trial supports the observed output choices, not reliability across
models or projects. CLI traces are retained; the full evaluator tool trace is
not. Cleanup after the expected CLI error was observed, but unexpected crashes,
credential redaction, and cleanup failures were not fault-injected. No whole-map
audit or search verification was performed.
