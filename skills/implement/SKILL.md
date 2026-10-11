---
name: implement
description: Implement a defined software change or established plan and prove delivery through acceptance and regression checks. Use when the user wants implementation without repeating the full interview, research, and planning workflow.
---

<!-- Extracted from deliver; workflow inspired by HumanLayer:
https://github.com/humanlayer/humanlayer/tree/main/.claude/commands
Debugging and verification also draw on pstack:
https://github.com/cursor/plugins/blob/main/pstack/skills/poteto-mode/playbooks/bug-fix.md
https://github.com/cursor/plugins/blob/main/pstack/skills/create-verification-skill/SKILL.md
-->

## Resume from the agreed work

Read the established plan or requirements, relevant context, and current code.
Confirm the outcome, scope, acceptance criteria, and existing behavior that
must remain working from that context. Settle only missing details needed for
a correct change; a separate planning document is not required.

When working from a task file or tracker issue, read its brief, status, and
linked context. Preserve the agreed brief and acceptance criteria. Keep the
plan, progress, consequential revisions, and verification evidence in that
same authoritative record. A task record is optional; otherwise, follow the
user's requested output format and project conventions.

Use the [adr](../adr/SKILL.md) skill to consult relevant accepted decisions
before changing code. Capture consequential choices and deviations as they
emerge, and link the records from the plan or task record.

## Implement

Make scoped increments and add or update acceptance and regression checks
where behavior changes or a concrete gap exists. Establish relevant baseline
behavior when useful.

For bug fixes, reproduce the failure through the affected entry point. Form
a cause hypothesis and check it against observed behavior, traces, or a
focused test. Make the smallest fix the evidence supports, then rerun the
original reproduction and relevant regressions. Remove changes justified only
by a disproven hypothesis. If reproduction is unavailable, state the limitation
and do not present a speculative fix as verified.

Apply these principles:

- Make the smallest correct change that fully achieves the goal and fits
  existing conventions.
- Minimize complexity. Add abstractions, configuration, and infrastructure
  only for concrete needs. Measure before optimizing.
- Give each module one coherent responsibility and a small interface.
  Hide its implementation complexity. Avoid empty forwarding layers.
- Keep boundaries explicit. Validate external data, expose dependencies,
  and use structures that make invalid states difficult to represent.
- Handle meaningful failures deliberately. Handle, translate, retry, or
  propagate them. Make retryable operations idempotent where practical.

Favor integration and end-to-end tests that exercise meaningful behavior
through real affected components, with regression checks for existing
functionality at risk. Use unit tests where useful; coverage percentage is
not a delivery criterion.

Adapt routine implementation details as needed. If findings change scope,
acceptance criteria, or consequential design decisions, update the plan
and resolve the decision with the user. Honor authorization already given.

## Prove delivery

Require irrefutable proof: reproducible, inspectable evidence that the
acceptance criteria hold under the stated test conditions.

Exercise the relevant user or system entry point without bypassing the changed
logic. Observe both the action and its result. Verify required side effects;
for persisted state, use a fresh read or restart where appropriate.

Run the acceptance and relevant regression checks against the final code.
Fix failures introduced by the change. Identify pre-existing failures
separately.

For each acceptance criterion, report the result and supporting evidence:
the scenario or test, how to reproduce it, and what was observed. Identify
the code state tested and any relevant environment limitations or mocks.

Do not weaken acceptance criteria to make the implementation pass.
Distinguish verified behavior from assumptions and unverified checks.
If required evidence is unavailable, report the gap and leave the affected
criterion incomplete.

When using a task record, mark it complete only when the required evidence
supports all acceptance criteria.

Finish with the delivered outcome, acceptance evidence, regression
results, and any remaining limitations.
