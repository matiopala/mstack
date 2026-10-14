# Skill simplification checks — 2026-10-14

Base: `dc5fc7fe44f7dcaa79ff951674b45b28a3469da1`, plus the uncommitted
skill simplifications. All 22 skills passed `scripts/validate`; the nine
changed skills passed `quick_validate.py`; all 14 tooling tests passed.

One fresh Codex subagent performed the two tasks below sequentially in
separate temporary projects, with named skills and raw fixtures. It received
neither the diff nor assessor criteria. Settings were inherited; the exact
model ID was not exposed. Each case had one trial. A separate reviewer
found no material source issues.

Workspace:
`/var/folders/q0/s5h2flw13y15kyf1b8r0gr540000gn/T/skill-simplification-eval-64a0c_g4`

`skills-under-test.json` in that workspace records all nine skill digests.
The behaviorally exercised revisions were:

| Skill | SHA-256 of SKILL.md |
| --- | --- |
| create-verification-skill | `659c809a3b800d45a662b1dd61c03d87419cb79dd4d4f1e08ca406cf49fe9b5f` |
| decompose | `d480c65be79f7130b4bbf74a69a8900011333b453bfc2b0583514b9ad434c950` |

## Verification creation — pass

Used the existing “Create reusable verification” request and
`fixtures/verification`. The agent created
`notes/.claude/skills/verify-notes/SKILL.md` with inline recipes and an
executable `scripts/verify.py` helper. No separate feature index was needed.

The generated instructions were executed against the real CLI: ten subprocess
calls and eleven checks covered health, create/list, insertion order,
fresh-process persistence, stored data, search, and the obsolete flag.
Evidence was retained and owned state removed. Application files were unchanged.

The parent independently copied the application and generated skill into
`notes-replay/` and ran:

```sh
python3 .claude/skills/verify-notes/scripts/verify.py
```

All eleven checks passed again. Source hashes matched the original fixture;
the parent checked that the recorded temporary directory was absent and
evidence files still existed. Retained evidence:

- `notes/artifacts/verify-notes/20261014T104501Z-a0851b85/`
- `notes-replay/artifacts/verify-notes/20261014T104613Z-a6b47cdf/`

Each contains `run.json`, `commands.jsonl`, `persisted-notes.json`, and
`summary.json`. Python was 3.9.6; no mocks or network were involved.

## Small decomposition — pass

Used another copy of the Notes fixture. Request: decompose a settled export
design without implementing it. Export defaults to JSON and also supports
CSV with `id,title` columns and standard quoting, including embedded newlines.
Both formats preserve insertion order, write to stdout, and leave storage
unchanged. Empty JSON is `[]`; empty CSV contains only the header. Existing
commands remain unchanged. Include documentation and verification for a small
project maintained by one developer.

The agent created one authoritative document:
`decompose/docs/features/notes-export/tasks.md`. It contains stable T01/T02
identifiers, dependencies, acceptance scenarios, regression checks, estimates,
and explicit final verification ownership. T01 owns both formats and their
tests; T02 owns documentation and final CLI replay. No task-file scaffold or
feature implementation was created.

The agent also captured ten existing-behavior CLI calls in
`decompose/artifacts/export-decomposition/baseline.json`, clearly labeled as
baseline evidence rather than proof of export. The parent inspected the task
content and confirmed the application and README hashes were unchanged.

## Limits

These checks establish the observed layout choices and retained requirements,
not general brevity, token savings, or behavior across models. Question pacing,
the conditional execution rule in blast-radius, and maintenance of inline
recipes received source review, not separate behavioral trials. Failure-path
cleanup, concurrency, corrupt data, permissions, and other platforms were not
exercised by this run.

## Follow-up: proportionality

Subsequent review found that the earlier layout passes did not establish
proportionate output. The small export breakdown was 1,460 words, and the
verification instructions added a 140-line helper. The follow-up tightened
`decompose`, `create-verification-skill`, and question pacing in `research`,
and added proportionality criteria to the evaluation instructions.

Fresh Codex subagents received the same fixture requests without prior outputs
or assessor criteria. Workspace:
`/var/folders/q0/s5h2flw13y15kyf1b8r0gr540000gn/T/skill-proportionality-eval-60ad3lwl`

| Trial | Assessment | Observed result |
| --- | --- | --- |
| First revised verification creation | Functional pass; proportionality failure | Inline `capture()` introduced a per-command output/status protocol and 26 evidence files. Removing the separate helper file had not removed reporting overhead. |
| Revised decomposition | Pass | One T01 owns implementation, documentation, regression checks, and final verification. Its 755-word brief retains useful dispatch context and concrete acceptance checks, with no artificial split or fabricated size estimate. |
| Verification creation after refinement | Pass | Direct shell commands, explicit expected results, one transcript, and owned cleanup; no custom capture function or helper script. The parent independently replayed the exact recipe in a fresh copy. |

The final replay exited 0. It established an empty collection, exact-title
creation, a matching list from a fresh process, doctor counts changing from
0 to 1, and persisted state before cleanup. The parent confirmed that owned
state was absent, evidence remained, and application/README hashes matched
the fixture across all four copies. Search, multiple-note ordering, and
argument errors remained explicitly unverified in the final recipe.

Retained artifacts, relative to the follow-up workspace:

- `notes/.claude/skills/verify-notes/SKILL.md` and
  `notes/artifacts/verify-notes-Tihr9B/`: first trial, including the excess reporting.
- `decompose/docs/features/export/tasks.md`: the single-task breakdown.
- `notes-second/.claude/skills/verify-notes/SKILL.md` and
  `notes-second/artifacts/verify-notes.pvZf0v/`: final recipe, transcript, and findings.
- `notes-replay/artifacts/verify-notes.Yp1CkO/`: independent transcript and
  `independent-replay.json`.
- `before/`, `creation-first-trial.SKILL.md`, `revisions.json`, and
  `final-revisions.json`: pre-turn source, failed candidate, and revision digests.

Final behaviorally exercised skill digests:

- `decompose`: `601115bfc0ab53804c1e07a4735c2733e2fa92beac5962e3be6b0c2dd6fe89a4`
- `create-verification-skill`: `359ebe465e86a7dbc19a3eba7207b3b1b98532d4b43bead1a96654ff3bb7d568`

All 22 skills passed metadata validation, all three changed skills passed
quick validation, and all 14 tooling tests passed. The refined creation skill
was revalidated after the failed trial. Research pacing received source review
only. Independent review found no material issues in the final changes or
their generated artifacts. These single trials support the observed choices; word counts describe
the artifacts and are not pass thresholds or estimates of general token savings.
