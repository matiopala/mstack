---
name: create-verification-skill
description: Create and prove a project-local skill for exercising real user journeys and collecting verification evidence. Use when the user asks for reusable verification instructions or a verification skill, not merely to verify the current change.
---

<!-- Adapted from pstack; MIT license in LICENSE:
https://github.com/cursor/plugins/blob/main/pstack/skills/create-verification-skill/SKILL.md
-->

## Inspect the project

Discover user-facing surfaces, documented startup, prerequisites, existing
harnesses, observable results, and isolation options. Ask only what inspection
cannot establish.

Check for an existing verification skill before creating another. Follow the
project's skill-location conventions; if absent, establish the target harness
and a discoverable directory. Keep one authoritative source when supporting
multiple harnesses. Do not overwrite an existing skill or repair unrelated
product problems without authorization; report startup blockers precisely.

## Write the project skill

Create `verify-<project>/SKILL.md` with valid name and description frontmatter.
Default to direct project commands, expected results, and cleanup in a short
recipe. Existing test output or a plain transcript is usually sufficient
evidence; do not build custom logging or reporting code merely to retain it.
Add helpers, including inline code, only when they simplify repeated or fragile
project interactions or checks. Make helper scripts executable and show their invocation.

Write for an agent arriving without this conversation. Include what applies:

- Relevant prerequisites and exact setup and launch commands. Include
  authentication, migrations, and seed data only when the journey needs them.
- For long-running or shared instances, a read-only health check for the
  correct instance, build, state, and access before driving and after unexpected
  failures. Include reset or relaunch steps for stuck interactions.
- Reproducible interaction commands through real user or system entry points,
  with stable selectors or handles where needed. Do not bypass the behavior
  being proved.
- Evidence capture: actions, expected and observed results, required side
  effects, tested code state, and relevant limitations or mocks. Verify
  persistence with a fresh read where appropriate.
- Isolated state and cleanup of only resources the run owns, including failed
  attempts. Never kill by process name. Preserve sanitized evidence in an
  artifact location separate from disposable state.

Keep secrets and unnecessary sensitive data out of recorded commands and
artifacts. Disable tracing around credential setup and commands that expand
secrets; redact sensitive output before retaining it.

Use safe local or test environments; check actual side effects rather than
trusting a dry-run label. Document any shared-instance restrictions.

## Map important journeys

Keep short recipes in `SKILL.md`; split them into linked feature files with
a `features/README.md` index when their number or detail warrants it. Group
recipes by user-visible behavior, noting any journey-specific prerequisites
or gotchas. Link existing checks instead of duplicating them. Identify unmapped
scope and unexecuted recipes; proving one entry point does not prove another.

## Prove and hand off

Replay one complete journey using the generated setup, interaction, evidence,
and cleanup instructions, including applicable health checks. Confirm artifacts
survive cleanup, including failed iterations. Fix instruction or harness errors and
rerun affected steps; never weaken expected behavior to force a pass.

Report the skill path, executed journey, evidence, and remaining gaps. Without
an end-to-end run, label the result a draft and state the blocker. Keep reusable
recipes in the skill and run-specific evidence in the task record or artifacts.
Mention `maintain-verification-skill` for later upkeep; do not start an audit
automatically.
