---
name: maintain-verification-skill
description: Audit and update a project's existing verification skill and feature map against source and live behavior. Use when the user asks to maintain verification instructions or check them for drift, not as a mandatory step after every change.
---

<!-- Adapted from pstack; MIT license in LICENSE:
https://github.com/cursor/plugins/blob/main/pstack/skills/maintain-verification-skill/SKILL.md
-->

## Establish scope

Locate the project verification skill, its inline or linked recipes, and
owned helpers.
If several targets are plausible, ask which; if none exists, recommend
`create-verification-skill` instead of inventing a target.

Honor a requested subset; otherwise audit the whole map. Edit only the
verification skill's directory. Keep run evidence separately. Do not change
product code, create branches, commit, or open PRs unless separately authorized.

## Check for drift

Within scope, reconcile any index entries with their files and compare recipes
with current source, requirements, and accepted decisions. For a full audit,
also check recent changes for missing user journeys, citing concrete entry
points. Reuse existing checks and investigate only relevant boundaries.

Distinguish intentional behavior changes from product regressions. When intent
is unclear, report the uncertainty instead of rewriting expectations to match
the implementation. Parallel read-only investigation is optional; coordinate
live driving to avoid shared-state interference.

## Exercise the map

Follow the skill's own launch and isolation model. For long-running or shared
instances, health-check before driving and after unexpected failures; reset
or relaunch if the interaction is stuck despite a healthy process. Fix confirmed
health-check drift and retry safely before declaring the environment blocked.

A full audit requires source and live coverage of every mapped feature.
Exercise the documented entry points and report exactly which paths were
covered; one passing path does not establish another. For unreachable paths,
record the attempt and unmet prerequisite, not a pass.

Capture actions, expected and observed results, side effects, code state, and
limitations. Clean up owned resources after failures and at completion; do not
disturb shared instances or unrelated state. Confirm evidence survives every
cleanup. Do not trust a dry-run label as proof of harmlessness.

## Correct and report

Fix confirmed documentation drift and owned harness gaps. Make helper scripts
executable, document invocation, and rerun corrected recipes live. Report
product regressions separately without weakening expected behavior; record a
known failure when useful, preserving the intended result.

Report scope, source and live coverage, corrections, evidence locations, and
remaining failures or blockers. Call the map clean only after full coverage
with no unresolved gaps; a scoped pass is not a whole-map clean verdict.
Unexecuted corrections remain unverified.

Keep reusable instructions in the skill and run-specific results in the task
record or artifacts. Do not commit scratch logs or treat an old successful run
as proof of the current code.
