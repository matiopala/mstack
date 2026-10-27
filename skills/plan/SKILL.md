---
name: plan
description: Create an implementation plan for a defined software change against durable verification requirements. Use when the user wants to plan or replan how a change will be implemented.
---

<!-- Extracted from deliver; workflow inspired by HumanLayer:
https://github.com/humanlayer/humanlayer/tree/main/.claude/commands
-->

## Use the established context

Read the intended outcome, scope, constraints, acceptance criteria, and
available research. When given a task record, read its brief, status, and
relevant linked context. Reuse settled decisions and completed work.

Inspect affected code and tests to resolve specific gaps. Ask only about
consequential gaps that available context cannot resolve. Resolve dependent
questions in order. Prior interview or research artifacts are helpful, not
prerequisites.

When clarification is needed, ask exactly one focused question per message in
plain text, then wait for the user's answer before choosing the next question.
Do not use structured question widgets, batch questions, or combine multiple
requests into one question. Brief options and a recommendation with a short
rationale are welcome; allow free-form answers and adjustments.

Consult relevant accepted decision records. Load [adr](../adr/SKILL.md) only
when a consequential planning choice warrants creating or revising a record.

## Establish the verification reference

Read the existing verification plan before choosing the implementation approach.
Use [design-verification](../design-verification/SKILL.md) when that plan is
missing or materially incomplete. Reuse adequate plans and their scenario
identifiers; do not repeat verification design merely because the approach changes.

Keep the verification plan separate from this implementation plan. Existing
requirements embedded in an older plan can be separated when touched, preserving
their meaning and identifiers. Link to the authoritative artifact rather than
maintaining a second acceptance checklist.

## Define the implementation approach

Define the final state in observable terms. Describe the smallest approach
that achieves it, including consequential interface, data, compatibility,
and failure-handling decisions. Use phases when they make work easier to
verify. Leave routine coding details to implementation.

Reference verification scenario identifiers and schedule the implementation,
check creation, prerequisites, and execution needed to satisfy them. Reuse
existing tests and project recipes. Creating a reusable project verification
skill or auditing its whole map remains separate work.

When replanning, preserve required outcomes and scenario identifiers. Execution
details may change while establishing the same requirements. Route material
verification gaps or requirement revisions through `design-verification`,
with their reasons; do not redefine success to fit the chosen approach.

Identify consequential uncertainties that must be resolved before
implementation. Distinguish them from choices that can be made locally while
implementing, and state what evidence or decision is needed to proceed.

## Keep one working plan

Keep the implementation plan and verification reference available for tracking
work and resuming later. When using a task record, keep implementation progress
and evidence there and link the separate verification plan. Preserve the agreed
brief and record consequential revisions explicitly.

A task record is optional. Otherwise, follow the user's requested output format
and project conventions. Finish with the approach, verification reference, and any
unresolved decisions. Continue to implementation only when covered by the
user's request and existing authorization.
