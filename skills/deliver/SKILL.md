---
name: deliver
description: Guide a software change through requirements interviewing, research, verification design, implementation planning, implementation, and review and fixes. Use when the user requests this development workflow.
---

<!-- Inspired by Matt Pocock's grill-me and HumanLayer's research-plan-implement workflow:
https://github.com/mattpocock/skills
https://github.com/humanlayer/humanlayer/tree/main/.claude/commands
-->

Follow the stages covered by the user's request and existing authorization.
Resume from established decisions and completed work.

Read and apply each stage's skill when entering it. Carry findings, decisions,
and the working record forward. An end-to-end delivery request already
authorizes moving between stages; do not ask for repeated approval simply
because a stage ends. A request for only part of the workflow ends at that
boundary.

For interview and clarification messages throughout the workflow, ask exactly
one focused question per message in plain text, then wait for the user's answer
before choosing the next question. Do not use structured question widgets,
batch questions, or combine multiple requests into one question. Brief options
and a recommendation with a short rationale are welcome; allow free-form
answers and adjustments.

## Task records

Task records are optional. When working from a task file or tracker issue,
read its brief, status, and relevant linked context. Use it as the progress hub:
preserve the agreed brief, link the separate verification plan, and keep
findings, implementation plans, progress, and evidence in place. Record
consequential revisions without copying verification requirements into competing
checklists. Otherwise, follow the user's requested format and project conventions.

## 1. Interview

Use [grill-me](../grill-me/SKILL.md) to clarify the desired outcome, scope,
constraints, concrete acceptance examples, and existing behavior that must
remain working. Ask only about consequential gaps not settled by available
context. When these are sufficiently clear to guide research and planning,
carry the interview summary into the next authorized stage. If they are
already clear, proceed without additional interview questions.

## 2. Research

Use [research](../research/SKILL.md) to investigate the affected behavior,
constraints, integration points, regression risks, and verification options.
Reuse findings from the interview.

## 3. Design verification

Use [design-verification](../design-verification/SKILL.md) to establish the
required scenarios, outcomes, regression obligations, and evidence separately
from implementation choices. Reuse an adequate existing verification plan.
Carry its reference and scenario identifiers into the following stages.

## 4. Plan implementation

Use [plan](../plan/SKILL.md) to define the smallest approach and the work needed
to satisfy the verification plan. Preserve its requirements during replanning.
Resolve consequential uncertainties before implementation.

Use [design-review](../design-review/SKILL.md) before implementation when the
solution introduces consequential design choices, such as new ownership
boundaries or shared contracts. Reuse an existing review when its assumptions
still hold, and address material findings within the authorized scope.

## 5. Implement, verify, and review

Reuse downstream risk analysis from research and planning, including effects
on shared contracts, persisted data, and lifecycle behavior. Use
[blast-radius](../blast-radius/SKILL.md) when concrete downstream questions
remain unresolved or new evidence introduces risks. Carry the assumptions and
regression obligations into the verification plan and check them against the
final code. Keep review effort proportional to the change.

Use [implement](../implement/SKILL.md) to make the scoped change, verify it
against the agreed criteria, and complete its review-and-fix loop. Let that
skill own the loop; do not add a second delivery review. Report the final
evidence and review outcome. Missing required evidence or unresolved material
review findings prevent a completion claim.
