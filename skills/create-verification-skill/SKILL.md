---
name: create-verification-skill
description: Create and prove a project-local skill for exercising real user journeys and collecting verification evidence. Use when the user asks for reusable verification instructions or a verification skill, not merely to verify the current change.
---

<!-- Adapted from pstack; MIT license in LICENSE:
https://github.com/cursor/plugins/blob/main/pstack/skills/create-verification-skill/SKILL.md
-->

## Inspect the project

Discover user-facing surfaces, documented startup, prerequisites, existing
harnesses, observable results, and isolation options. Reuse working tools
before adding helpers. Ask only what inspection cannot establish.

Check for an existing verification skill before creating another. Follow the
project's skill-location conventions; if absent, establish the target harness
and a discoverable directory. Keep one authoritative source when supporting
multiple harnesses. Do not overwrite an existing skill or repair unrelated
product problems without authorization; report startup blockers precisely.

## Write the project skill

Create `verify-<project>/SKILL.md` with valid name and description frontmatter.
Write for an agent arriving without this conversation. Include:

- Exact setup and launch commands, dependencies, configuration, authentication,
  migrations or seed data, and a readiness check that establishes usability.
- A read-only health check for the correct instance, build, state, and access;
  run it before driving and after unexpected failures. Reset or relaunch when
  health checks cannot detect a stuck interaction.
- Reproducible interaction commands through real user or system entry points,
  using stable selectors or handles. Do not bypass the behavior being proved.
- Evidence capture: actions, expected and observed results, required side
  effects, tested code state, and relevant limitations or mocks. Verify
  persistence with a fresh read where appropriate.
- Isolated state and cleanup of only resources the run owns, including failed
  attempts. Never kill by process name or delete evidence. Name an artifact
  location separate from disposable state.

Use safe local or test environments; check actual side effects rather than
trusting a dry-run label. Document any shared-instance restrictions. Make
owned helper scripts executable and show their invocation.

## Map important journeys

Add `features/README.md` as an index and a small set of feature recipes.
Each describes the user-visible behavior, entry points, prerequisites, exact
actions, observable proof, and gotchas. Link existing checks instead of
duplicating them. Identify unmapped scope and unexecuted recipes; proving one
entry point does not prove another.

## Prove and hand off

Follow the generated instructions through setup, health check, one complete
mapped journey, evidence capture, and cleanup. Confirm artifacts survive
cleanup, including failed iterations. Fix instruction or harness errors and
rerun affected steps; never weaken expected behavior to force a pass.

Report the skill path, executed journey, evidence, and remaining gaps. Without
an end-to-end run, label the result a draft and state the blocker. Keep reusable
recipes in the skill and run-specific evidence in the task record or artifacts.
Mention `maintain-verification-skill` for later upkeep; do not start an audit
automatically.
