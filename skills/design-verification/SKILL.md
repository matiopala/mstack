---
name: design-verification
description: Design or revise a durable verification plan for a defined feature or change, independently of its implementation approach. Use when defining what must be proved, its scenarios, and required evidence.
---

Define how to establish that the requested behavior holds. Keep the verification
plan authoritative as implementation approaches and task breakdowns change.

## Ground the requirements

Read the user's requirements, accepted decisions, affected existing behavior,
and any verification plan. Inspect relevant code, tests, and project verification
recipes for constraints and available checks. Current behavior is evidence,
not the specification; flag conflicts with the intended behavior.

Ask only about consequential gaps that available context cannot resolve.
Preserve settled requirements and keep assumptions and unresolved scope explicit.

## Design the verification

Require reproducible, inspectable evidence that the requirements hold under
stated conditions. Coverage percentages alone do not establish correctness.

Give each scenario a stable identifier, such as `V01`, and connect it to the
requirement or accepted decision it establishes. Describe:

- The starting conditions and action through a real user or system entry point.
- The expected observable outcome, including required side effects.
- The evidence that would establish the outcome and expose a failure.

Express required outcomes independently of proposed mechanisms. Preserve
internal representations only when a requirement or accepted compatibility
contract makes them an obligation. Otherwise keep those details in execution
design; preserving saved records does not by itself require identical storage bytes.

Cover meaningful success, failure, and regression scenarios in proportion to
the change. Include performance or other quality checks when required, with
justified conditions and thresholds. Prefer checks through real affected
components; use focused unit checks where they establish the requirement.

Keep required outcomes separate from execution details. Reference existing
tests and project recipes by path or command. For missing checks, describe the
intended entry point, prerequisites, and work needed; do not invent executable
commands. Record limitations, mocks, and coverage gaps. A planned check is not
an observed result, and a passing check proves only what it exercises.

## Preserve the plan through change

Replanning preserves scenario identifiers and required outcomes. Setup,
commands, and tools may change when they still establish the same requirements;
record the reason and any change in evidence strength or limitations.

When requirements change, a missing scenario is discovered, or verification
design misstates a requirement, revise the affected scenarios and explain why,
citing the supporting requirement or decision. Preserve unrelated scenarios and
do not reuse retired identifiers
for different obligations. Resolve changes to intended behavior with the user
when they are not already authorized. Never weaken an expectation to fit a
failing implementation. Unchanged requirements still need evidence for the
code being delivered; an older pass does not verify a new implementation.

## Hand off one verification plan

Reuse an existing dedicated verification artifact. Otherwise follow the user's
destination and repository conventions, defaulting to
`docs/features/<slug>/verification.md`. For chat-only work, return a separately
labeled verification plan. Keep it short enough for the task; a small change
may need only a few scenarios, with no template or additional files.

Reference requirements instead of duplicating a product spec. Keep the
verification plan separate from replaceable implementation plans and link it
from any task record. When separating an existing embedded plan, preserve its
requirements and identifiers and replace the old detail with a reference.

Report the plan, assumptions, and gaps. This task designs verification;
implementing tests, collecting delivery evidence, or creating a reusable
project verification skill requires that work to be in the requested scope.
