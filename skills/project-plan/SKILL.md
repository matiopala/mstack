---
name: project-plan
description: Create an initial software project plan defining overall outcomes, scope, milestones, dependencies, and the specifications needed next. Use when the user wants to shape a whole project before detailed design and task decomposition.
---

Turn a project idea and available context into a bounded initial plan ready
for the necessary product and technical specifications. Plan the whole
intended project, with firmer detail for the first milestone.

Consult relevant accepted decision records. Load [adr](../adr/SKILL.md) only
when a consequential scope or sequencing choice warrants creating or revising
a record. Link the records from the plan.

## Establish the project

Reuse existing requirements, specifications, and conversation context. Clarify
who benefits, the intended outcomes, what completion means, and the boundaries
of the project. Make deliberate exclusions clear.

Inspect relevant repository behavior and existing documentation around
specific questions about current state, constraints, and dependencies before
asking for facts inspection could establish. Keep investigation focused on
project planning; leave detailed design to specifications.

Ask only about consequential gaps that available context cannot resolve.
Resolve dependent questions in order; group independent questions when useful.
Challenge weak assumptions and recommend concrete scope or staging choices.
Reuse settled decisions unless new evidence changes their implications.

Distinguish observed facts, agreed requirements, assumptions, and proposals.
When a larger unknown could change scope or sequencing, identify the bounded
investigation needed and the decision its evidence must enable.

## Gather constraints

Ask for missing estimates, deadlines, capacity, or other constraints only when
needed to decide scope, sequencing, or feasibility. Preserve supplied values
and their stated assumptions. Never generate estimates, durations, delivery
dates, or schedules yourself. Leave unavailable values unspecified and identify
any consequential decision that remains blocked.

Flag conflicts supported by the available scope, dependencies, and constraints.
Recommend scope cuts or staging options for the user to decide, without offering
replacement estimates or dates. Keep uncertain feasibility explicit.

## Shape the milestones

Identify the major capabilities or workstreams needed to achieve the project
outcome. Group them into milestones with observable outcomes and completion
criteria. State what evidence would demonstrate project and milestone
completion; leave detailed acceptance scenarios and test design to specs.

Make the first milestone concrete enough to guide specification work: its
scope, intended result, prerequisites, and completion criteria must be clear.
Keep later milestones less detailed, with their assumptions and uncertainties
explicit rather than treating them as settled commitments.

Sequence milestones by dependencies, value, and risk. Explain what each
dependency supplies. Check that the milestones collectively cover the agreed
project outcome, with no missing prerequisites or circular dependencies.

Identify the product or technical specifications needed for each relevant
capability, including the questions they must settle before task decomposition.
Link existing specifications and decisions instead of duplicating their detail
or reopening settled work. Record risks and investigations needed alongside
the milestones they affect.

## Artifact and handoff

Create one authoritative plan covering the decisions and milestone structure
above, scaled to the project.

Follow the user's requested format and destination, then repository
conventions. Otherwise, save to:

`docs/projects/<project>/project-plan.md`

Refine an existing initial draft in place, preserving agreed decisions and
recording consequential revisions explicitly. This skill covers initial
planning; ongoing replanning and delivery tracking are outside its scope.
Detailed requirements, technical contracts, and task records belong in their
respective artifacts.

Unresolved project-level decisions keep the plan a draft; name what is needed
to proceed. Otherwise, mark it ready for specification work, leaving technical
details to the identified specs.

Finish with the artifact location, agreed project outcome, readiness status,
and specifications or investigations needed next. Creating those artifacts,
decomposing tasks, or implementing work follows the user's requested scope
and existing authorization.
