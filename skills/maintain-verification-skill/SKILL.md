---
name: maintain-verification-skill
description: Audit a project's verification instructions and feature map against source and live behavior, and repair them when maintenance is requested. Use for drift checks or verification-instruction upkeep, not as a mandatory step after every change.
---

<!-- Adapted from pstack; MIT license in LICENSE:
https://github.com/cursor/plugins/blob/main/pstack/skills/maintain-verification-skill/SKILL.md
-->

## Establish scope

Locate the project verification skill, its inline or linked recipes, and
owned helpers.
Read any linked verification plans and preserve their scenario references and
required outcomes while updating execution details. Report gaps or conflicts
with those requirements; this workflow does not rewrite the verification plan
to match current behavior.
If several targets are plausible, ask which; if none exists, recommend
`create-verification-skill` instead of inventing a target.

For audit or drift-check requests without repair authorization, report findings
without editing verification instructions or helpers. Maintenance, update, or
repair requests authorize scoped fixes; proceed without renewed approval.

Honor a requested subset; otherwise audit the whole map. When repairing, edit
only the verification skill's directory. Keep run evidence separately. Do not
change product code, create branches, commit, or open PRs unless separately authorized.

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
or relaunch if the interaction is stuck despite a healthy process. During
authorized maintenance, fix confirmed health-check drift and retry safely
before declaring the environment blocked.

Audits may use safe diagnostic commands without editing recipes; distinguish
these from successful replay of the documented instructions.

A full audit requires source and live coverage of every mapped feature.
Exercise the documented entry points and report exactly which paths were
covered; one passing path does not establish another. For unreachable paths,
record the attempt and unmet prerequisite, not a pass.

Capture actions, expected and observed results, side effects, code state, and
limitations. Existing check output or a plain transcript is usually sufficient
evidence; do not build custom logging or reporting code merely to retain it.
Add helpers, including inline code, only when they simplify repeated or fragile
interactions or checks. Keep additional records only when they serve a distinct
purpose rather than duplicate captured results or metadata.

Keep secrets and unnecessary sensitive data out of recorded commands and
artifacts. Disable tracing around credential setup and commands that expand
secrets; redact sensitive output before retaining it.

Clean up owned resources after failures and at completion; do not disturb
shared instances or unrelated state. Confirm sanitized evidence survives every
cleanup. Do not trust a dry-run label as proof of harmlessness.

## Correct and report

When repairs are authorized, fix confirmed documentation drift and owned harness
gaps. Make helper scripts executable, document invocation, and rerun corrected
recipes live. Report product regressions separately without weakening expected
behavior; record a known failure when useful, preserving the intended result.

Report scope, source and live coverage, corrections, evidence locations, and
remaining failures or blockers. Reference retained evidence instead of repeating
it. Call the map clean only after full coverage with no unresolved gaps; a scoped
pass is not a whole-map clean verdict. Unexecuted corrections remain unverified.

Keep reusable instructions in the skill and run-specific results in the task
record or artifacts. Do not commit scratch logs or treat an old successful run
as proof of the current code.
