---
name: plan
description: Create an implementation plan for a defined software change, with an observable final state, acceptance scenarios, regression protection, and irrefutable proof. Use when the user wants to plan a change before implementing it.
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
questions in order; group independent questions when useful. Prior interview
or research artifacts are helpful, not prerequisites.

Consult relevant accepted decision records. Load [adr](../adr/SKILL.md) only
when a consequential planning choice warrants creating or revising a record.

## Define the approach and proof

Define the final state in observable terms. Describe the smallest approach
that achieves it, including consequential interface, data, compatibility,
and failure-handling decisions. Use phases when they make work easier to
verify. Leave routine coding details to implementation.

Map each acceptance criterion to a check and the observable evidence needed
before claiming delivery. Specify the scenario, expected result, prerequisites,
and commands for existing checks when known. For checks to create, describe
the scenario and intended entry point; do not invent executable commands.

Checks must exercise the relevant user or system entry point and establish
required side effects. Irrefutable proof is reproducible, inspectable evidence
that the criteria hold under the stated test conditions.

Reuse relevant journeys from an existing project verification skill when
choosing checks, noting any recipe gaps. Creating a skill or auditing its whole
map is separate work, not a prerequisite for planning this change.

Include regression checks for affected existing functionality. Favor
integration and end-to-end tests that exercise meaningful behavior through
real affected components. Use unit tests where useful; coverage percentage
is not a delivery criterion.

Identify consequential uncertainties that must be resolved before
implementation. Distinguish them from choices that can be made locally while
implementing, and state what evidence or decision is needed to proceed.

## Keep one working plan

Keep the plan and acceptance checklist available for tracking work and resuming
later. When using a task record, add them to that same record in its existing
location. Preserve the agreed brief, acceptance criteria, progress, and evidence;
record consequential revisions explicitly.

A task record is optional. Otherwise, follow the user's requested output format
and project conventions. Finish with the approach, acceptance checks, and any
unresolved decisions. Continue to implementation only when covered by the
user's request and existing authorization.
