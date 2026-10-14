---
name: implement
description: Implement a defined software change, verify it, and review and fix material issues before delivery. Use when the user wants implementation without repeating the full interview, research, and planning workflow.
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

Consult relevant accepted decision records before changing code. Load
[adr](../adr/SKILL.md) only when a consequential choice or deviation warrants
creating or revising a record; link it from the plan or task record.

## Implement

Make scoped increments. Reuse sufficient existing acceptance and regression
checks; add or update checks only for concrete coverage gaps. Establish relevant
baseline behavior when useful.

For bug fixes, reproduce the failure through the affected entry point. Form
a cause hypothesis and check it against observed behavior, traces, or a
focused test. Make the smallest fix the evidence supports, then rerun the
original reproduction and relevant regressions. Remove changes justified only
by a disproven hypothesis. If reproduction is unavailable, state the limitation
and do not present a speculative fix as verified.

Apply these principles:

- Make the smallest correct change that fully achieves the goal and fits
  existing conventions.
- Apply YAGNI: add features, abstractions, configuration, and infrastructure
  only for current requirements or concrete constraints. Measure before optimizing.
- Prefer suitable existing project code, standard-library or platform features,
  and installed dependencies before adding custom code or a new dependency.
- Default to no comments. Add a brief comment only for non-obvious reasons or
  constraints the code cannot express. Preserve required documentation, legal
  notices, and tool directives.
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

Use relevant recipes from an existing project verification skill to collect
fresh evidence. Update affected recipes within the authorized change scope;
do not weaken expected behavior to match a regression. Keep reusable steps in
the skill and observed results in the task record or artifacts. Do not require
skill creation or a full maintenance audit for routine delivery.

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

## Review and fix

After implementation and initial verification, use
[code-review](../code-review/SKILL.md) to review the actual changes. Provide the
requirements, comparison base and change scope, relevant decisions, and
verification evidence. Include uncommitted and new files within that scope.

For straightforward, low-risk changes, review in the current session and
identify the result as self-review. Prefer one reviewer subagent with fresh
context when the change's risk or complexity benefits from an independent
perspective and delegation is available and permitted. Honor explicit requests
for independent review. If delegation is unavailable, self-review and disclose
any unmet independent-review request.

When delegating, give the reviewer the necessary artifacts rather than the full
implementation conversation. The reviewer reports findings; the implementing
agent owns fixes.

Check findings against the code and requirements. Fix confirmed, material
issues within scope without asking for renewed approval. Explain findings
rejected with evidence; optional polish does not prolong the loop.

After fixes, rerun affected checks, refresh the evidence, and review the fixes
and their consequences. Widen review only when changes or new evidence warrant
it. Repeat while material issues remain. One clean review ends the loop when
the required acceptance and regression evidence supports the final code.

If the loop stops making progress, revisit the diagnosis. Report any concrete
blocker, missing evidence, or decision requiring the user; do not repeat
ineffective rounds or turn an iteration limit into a ready verdict.

When using a task record, mark it complete only when all acceptance criteria
are supported and no material review findings remain unresolved.

Finish with the delivered outcome, acceptance evidence, regression
results, review outcome, and any remaining limitations.
