---
name: decompose
description: Break a larger software design, architecture, or feature specification into small, reviewable tasks with explicit dependencies, acceptance criteria, and proof of completion. Use when the user asks to decompose a larger body of work.
---

Turn the supplied design into coherent tasks that collectively deliver its
intended outcome. Each implementation task should normally fit one focused
PR that a reviewer can understand, verify, and accept independently.

## 1. Understand the goal and constraints

Read the supplied artifact and relevant context. Identify the required
outcomes, scope, shared invariants, and consequential decisions already made.

Consult relevant accepted decision records and carry their links into task
briefs. Load [adr](../adr/SKILL.md) only when a consequential design, rollout,
or compatibility tradeoff warrants creating or revising a record. Ordinary
task splits belong in the task records.

Investigate the codebase around specific decomposition questions: existing
behavior, ownership, interfaces, dependencies, and verification options.
Use this evidence to assess task boundaries and likely size.

Ask the user about consequential ambiguities that the artifact and targeted
inspection cannot resolve. Avoid reopening settled decisions without new
evidence.

If research cannot resolve an uncertainty that prevents useful decomposition,
define a bounded investigation with a question, required evidence, and the
decision it must enable. Mark dependent tasks as provisional.

## 2. Define coherent tasks

Give each task one observable outcome. State what becomes true when it is
complete. Describe implementation activities only as needed to explain scope.

Prefer narrow behavioral slices through existing components. Create a
foundational task when it provides a concrete capability needed by identified
later tasks.

Keep essential invariants together. Each completed task must leave the system
in a valid, testable state without relying on unfinished follow-up work for
correctness. User-facing availability may come later.

Include necessary failure handling, acceptance tests, and regression
protection within the task that introduces the behavior.

Preserve the larger design's shared decisions. Reference their authoritative
source and include enough relevant context for an implementer to proceed.
Leave routine coding decisions to implementation.

## 3. Size for review

Aim for a few hundred handwritten implementation lines per task. Around
1,000 implementation lines should normally trigger another split.

Treat these as estimates. Consider the entire review burden: implementation,
tests, migrations, changed contracts, novelty, risk, and surrounding context.
Identify generated and mechanical changes separately.

Split oversized tasks by coherent behavior or responsibility. Preserve the
tests and failure handling needed to demonstrate correctness.

Check whether a reviewer can explain the task's purpose and judge its
correctness without reconstructing unfinished tasks. If not, revise the
boundaries.

## 4. Define acceptance and irrefutable proof

For each task, specify:

- Concrete acceptance scenarios.
- Expected observable results.
- The tests or checks that demonstrate those results.
- Relevant existing behavior that must remain working.

Require irrefutable proof: reproducible, inspectable evidence that the
acceptance criteria hold under the stated test conditions.

Favor integration and end-to-end tests that exercise meaningful behavior
through real affected components. Reuse existing regression checks and add
coverage where the change creates a concrete gap. Use focused unit tests
where helpful; coverage percentage is not a completion criterion.

Match proof to the output. An investigation needs evidence supporting its
conclusion; a migration needs evidence of data integrity and compatibility.

Establish expected behavior before implementation. Do not weaken acceptance
criteria to accommodate the resulting code.

## 5. Order and reconcile the tasks

Give tasks stable identifiers and explicit dependencies. For each dependency,
state the capability, contract, or decision being consumed.

Order work to expose significant uncertainty and integration risks early.
Where useful, begin with a narrow working path through the affected components.

Identify parallel work only where shared contracts are settled and the tasks
can be implemented and verified separately.

Check the decomposition as a whole:

- Every required outcome has an implementation and verification owner.
- Dependencies are necessary, clear, and acyclic.
- Task scopes do not leave gaps or duplicate ownership.
- Shared invariants remain intact throughout implementation.
- A named task owns final verification of the assembled behavior.

If new evidence changes task size or coupling, revise the remaining
decomposition while preserving completed work and acceptance criteria.

## Output

Present the overall goal, an ordered task list with dependencies, and a
concise brief for each task:

- ID and title: the observable outcome.
- Context: relevant design references, existing behavior, and constraints.
- Scope: what the task owns and boundaries needed to prevent overlap.
- Dependencies: prerequisites and what is consumed from each.
- Acceptance and irrefutable proof: scenarios, expected results, and evidence.
- Regression protection: affected existing behavior and relevant checks.
- Expected size and uncertainty: likely affected areas, approximate
  implementation size, and factors that could require another split.

Identify the owner of final integrated verification and any unresolved
questions or provisional estimates.

Follow the user's requested output format and destination, then existing
repository conventions. Otherwise, save artifacts under
`docs/features/<feature>/tasks/`, with an `index.md` and one file per task
named by its stable ID, such as `T01.md`.

Use the index for the overall goal, task ordering, dependencies, and links
to task files. Each task file owns its brief, acceptance criteria, and status,
and can later hold its implementation plan, progress, and verification evidence.

Maintain one authoritative task record. If the user chooses an issue tracker,
use that destination and link to it rather than maintaining duplicate briefs.
When revising a decomposition, update existing records and preserve task IDs,
progress, implementation plans, and evidence.

Keep the work focused on decomposition until implementation is requested.
