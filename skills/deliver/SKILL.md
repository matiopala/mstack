---
name: deliver
description: Guide a software change through requirements interviewing, focused research, planning, implementation, and acceptance verification. Use when the user requests this development workflow.
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

## Task records

When working from a task file or tracker issue, read its brief, status, and
relevant linked context. Use it as the authoritative working record. Preserve
the agreed brief and acceptance criteria, and record consequential changes
explicitly.

Add research findings, the implementation plan, progress, and verification
evidence to that same record in its existing location. Maintain one authoritative
task record; link to it rather than creating duplicate task or delivery records.

A task record is optional. For standalone requests, work from the available
context and follow the user's requested output format and project conventions.

## 1. Interview

Use [grill-me](../grill-me/SKILL.md) to clarify the desired outcome, scope,
constraints, concrete acceptance examples, and existing behavior that must
remain working. Finish when these are sufficiently clear to guide research
and planning.

## 2. Research

Use [research](../research/SKILL.md) to investigate the affected behavior,
constraints, integration points, regression risks, and verification options.
Reuse findings from the interview.

## 3. Plan

Use [plan](../plan/SKILL.md) to define the observable final state, smallest
approach, acceptance checks, regression protection, and irrefutable proof.
Resolve consequential uncertainties before implementation.

Use [design-review](../design-review/SKILL.md) before implementation when the
solution introduces consequential design choices, such as new ownership
boundaries or shared contracts. Reuse an existing review when its assumptions
still hold, and address material findings within the authorized scope.

## 4. Implement and prove delivery

For changes to shared contracts, persisted data, lifecycle behavior, or other
concrete downstream risks, use [blast-radius](../blast-radius/SKILL.md) to
identify the regression checks and assumptions to verify. Carry these into
the plan and check them against the final code. Keep review effort proportional
to the change.

Use [implement](../implement/SKILL.md) to make the scoped change, verify it
against the agreed criteria, and report the evidence. Implementation includes
acceptance and regression verification; stop short of claiming delivery when
required evidence is missing.
