---
name: blast-radius
description: Assess what a proposed or implemented change could break beyond the edited code. Use when the user asks about blast radius, downstream effects, or regression risks.
---

<!-- Adapted from pstack's blast-radius skill:
https://github.com/cursor/plugins/blob/main/pstack/skills/blast-radius/SKILL.md
-->

Identify meaningful regression risks and the evidence needed to resolve them.

## Trace the change

Establish the intended behavior and review scope from the diff, proposal,
and relevant context. Identify existing behavior that must remain working.

Follow effects beyond direct callers: external contracts, stored data,
pinned dependencies, lifecycle ordering, shared state, and rollout
compatibility. Investigate specific failure scenarios with source references.
Prioritize by impact and realistic exposure; do not invent probability estimates.

## Check the risks

Identify the assumptions that protect affected behavior. Run focused checks
against real components to test those assumptions. Reuse existing regression
tests; add a small reproduction when needed. Use integration or end-to-end
checks when the risk crosses a boundary.

Distinguish source-based reasoning from executed checks and observations in
the running app. Record what ran, the result, and relevant code state and
conditions. Leave unsupported claims visibly unproven.

For a proposed change, current-system checks establish constraints and
baseline behavior; verification of the eventual implementation remains open.

Stay within the requested review scope. Recommend product fixes unless the
user also asked for implementation.

## Explain the result

By default, read and apply [bro](../bro/SKILL.md) to the review draft.
Preserve priorities, evidence, uncertainty, and recommended actions.

Lead with the most important consequence, then cover:

- What changes and which existing behaviors are affected.
- Confirmed problems and unresolved risks, each with a triggering scenario,
  supporting reference, and impact.
- Risks checked and ruled out, with the evidence and its limits.
- The smallest fixes or regression checks needed before delivery.

Return the plain-language review directly. Do not imply that checking the
identified risks proves the entire system free of regressions.
