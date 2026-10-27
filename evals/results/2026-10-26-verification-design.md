# Verification design separation — 2026-10-26

Base: `b83ec77`, plus this change. All 25 skills passed metadata validation,
all ten changed/new skills passed quick validation, and all 14 tooling tests
passed. Installer tests now exercise the new companion for `plan`, `deliver`,
`tech-spec`, and `decompose`, standalone installation, and dependency conflicts.
These checks establish packaging behavior, not the effectiveness of instructions.

Behavioral trials used isolated copies of the Notes CLI and fresh subagents.
Each received its request, raw fixture, and named skill paths, without the
assessor rubric or parent conclusions. The replanning follow-up used the same
session; requirement revision used a fresh session and a saved plan pair.
Models/settings were inherited; exact model identifiers were not exposed.

Retained workspace:

`/var/folders/q0/s5h2flw13y15kyf1b8r0gr540000gn/T/skills-verification-separation-kn7pxf45`

`revisions.json`, `revisions-revised.json`, and `revisions-final.json` record
skill digests. Paths below are relative to that workspace.

## Initial failure and correction

The initial storage-planning trial produced separate implementation and
verification plans, but overconstrained failed writes to preserve identical
storage bytes. The requirement was preservation of saved records. During the
SQLite follow-up, the agent proposed copying and atomically publishing candidate
databases to satisfy that incidental constraint. Preserving identifiers alone
had not established implementation independence.

The independent reviewer confirmed this failure. The skill was clarified to
derive obligations from accepted behavior and compatibility contracts, keep
incidental representations in execution details, and permit documented corrections
to verification-design mistakes. The original skill and initial output remain in
`design-verification-before-refinement.md` and `snapshots/initial/`.

The first follow-up also exposed ambiguity between import on first use and the
documented read-only commands. The fresh trial explicitly requested import on
first add, retaining the read-only contract. The original trial was interrupted;
it is not counted as a passing replan.

## Observed results

| Case | Result and evidence |
| --- | --- |
| Implementation replanning | Pass after correction. A fresh trial created six verification scenarios. Changing the implementation from temporary-file replacement to SQLite transactions changed the implementation plan while leaving the entire verification plan byte-identical. Parent inspected both plans and checked hashes. See `snapshots/revised-initial/`, `snapshots/sqlite-replan/`, and `replan-comparison.json`. |
| Authorized requirement revision | Pass. A fresh session changed search to case-sensitive matching with the explicit user decision recorded. Only V04's scenario row changed; the other five rows and all IDs were preserved. It identified conflicts with older code/docs without editing them. Parent compared the files. See `requirement-revision/docs/features/storage/verification.md` and `requirement-comparison.json`. |
| Missing harness | Pass. Cloud backup scenarios identified absent implementation, accounts, access, and failure injection. No cloud commands or passes were invented and no resources were provisioned. See `missing/docs/features/cloud-backup/verification.md`. |
| Small chat-only task | Pass. Two short scenarios covered the version output and required data-directory regression. No files were created or changed in the fixture. See `small-response.md`. |
| Recipe handoff | Pass. The generated project skill referenced V01–V04 and exercised all four real CLI scenarios. Requirements and app were unchanged, evidence survived cleanup. Parent replayed the exact Bash blocks in a separate copy and independently asserted persistence, ordering, search, and rejected-flag behavior. See `recipe/.claude/skills/verify-notes/SKILL.md`, `recipe/artifacts/verify-notes.6RbJtx/`, `independent-replay.json`, and `replay-command-output.txt`. |
| Failing implementation | Pass. In a separate copy, case folding was deliberately removed from search. Maintenance reported V03 as a product regression, retaining the requirement and recipe; V01, V02, and V04 passed. A fresh code reviewer returned not ready, inspected the raw evidence, and verified source hashes without rerunning the app. See `regression/artifacts/verify-notes.hL3JvZ/` and `failure-review.md`. |

The recipe trial retained a terminal-input error and its successful recovery
rather than presenting it as a product failure or omitting it. Parent replay
used the documented commands without that interaction error. Both runs removed
owned state and retained evidence. Python was 3.9.6; no mocks or network were
used for the CLI journeys.

Parent checks confirmed the app and README remained unchanged in all good
fixtures, the seeded verification plan remained unchanged in recipe/replay/
regression fixtures, and the maintenance recipe was unchanged. The deliberate
search mutation remained confined to the regression fixture.

## Review and limits

One independent source reviewer examined the skill and workflow changes,
installer behavior, and evidence. It confirmed the initial overconstraint,
reviewed the correction and fresh trial, and returned ready with no remaining
material findings. Its summary is retained in `change-review.md`.

These are single trials, not reliability estimates. The missing-harness and
small-task trials preceded the narrow storage-independence clarification.
The final authoring behavior was exercised by the fresh planning/replanning
and requirement-revision trials. `deliver`, `tech-spec`, `decompose`,
`design-review`, and `implement` integrations received source review rather than
separate end-to-end trials. Automatic selection from descriptions alone was
not tested. No SQLite implementation, cloud backup, crash recovery, concurrency,
or power-loss behavior was implemented or claimed verified.
