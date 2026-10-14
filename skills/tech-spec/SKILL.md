---
name: tech-spec
description: Create or revise a technical specification for a substantial software capability. Use when the user wants a technical design that defines the intended solution and is ready for task decomposition.
---

Turn the requirements into a technical specification that defines the
intended final state, settles consequential design decisions, and explains
how successful implementation will be demonstrated.

Use existing requirements, architectural decisions, and conversation context.
A formal product specification is helpful but not required.

Consult relevant accepted decision records before design. Load
[adr](../adr/SKILL.md) only when a consequential design choice warrants
creating or revising a record.

## 1. Establish the requirements

Identify the intended outcomes, scope, constraints, acceptance criteria,
and existing behavior that must remain working.

Reuse settled decisions. Ask only about consequential gaps that available
context cannot resolve. Resolve dependent questions in order; group independent
questions when useful.

Distinguish requirements, observed facts, assumptions, and proposed decisions.
Clarify assumptions that could materially change the solution.

## 2. Research around design decisions

Inspect the codebase around specific questions: current behavior,
responsibilities, interfaces, data ownership, dependencies, and tests.

Once requirements are sufficiently clear, trace the affected flows to
identify integration points, compatibility constraints, and regression risks.
Reuse findings already established during clarification.

Use parallel research for independent questions when useful and available.
Reconcile findings against current code and record relevant references.

Investigate uncertain technical assumptions before relying on them.
If a consequential uncertainty remains unresolved, identify the missing
evidence and keep the specification provisional.

## 3. Define the proposed solution

Describe the observable final state and the simplest design that achieves it
within the existing system.

Define the details needed for components and future tasks to work together:

- Responsibilities and ownership boundaries.
- Interfaces and contracts.
- Data flow, storage changes, and important state transitions.
- Validation and meaningful failure behavior.
- Compatibility and migration requirements where relevant.
- Operational constraints that materially affect the design.

Make contracts precise enough for independent implementations to agree.
Leave routine internal implementation choices to the implementing task.

Prefer coherent responsibilities, small interfaces, and explicit dependencies.
Keep complexity with the component that owns it. Add abstractions or
infrastructure only when the requirements establish a concrete need.

Reference shared architectural decisions. Identify proposed changes to those
decisions explicitly and explain their consequences.

Use diagrams or concrete examples where they clarify behavior or ownership.
Scale detail to the uncertainty and coordination involved.

## 4. Explain consequential decisions

For decisions that materially affect behavior, complexity, compatibility,
or future work, record the chosen approach and why it fits.

Compare alternatives when they represent a real tradeoff. Include relevant
evidence and acknowledge the costs of the chosen approach.

For choices captured in ADRs, summarize their effect on the proposed solution
and link to the records for rationale, alternatives, and consequences.
Keep smaller decisions inline without repeating requirements or design details.

## 5. Define acceptance and irrefutable proof

Connect each required outcome to observable technical behavior and the
evidence needed to demonstrate it.

Require irrefutable proof: reproducible, inspectable evidence that the
acceptance criteria hold under the stated test conditions.

Define integration and end-to-end scenarios through the affected components,
including important edge cases and failure paths. Identify existing behavior
at risk and the regression checks that must protect it.

Use focused unit tests where helpful; coverage percentage is not a delivery
criterion.

Specify how the assembled capability will be verified. Make relevant test
conditions, external dependencies, and limitations explicit. Task-level
verification can be refined during decomposition.

Define required evidence here; record actual results during implementation.

## 6. Check readiness for decomposition

Mark the specification ready when consequential behavior, contracts, ownership,
invariants, compatibility, and verification are settled enough for tasks to
proceed independently, including intermediate states. Remaining choices must
be local to implementation. Otherwise, label it a draft and identify the
missing evidence or decisions.

## Output

Create or update one authoritative specification covering the relevant
requirements, current state, design, decisions, verification, and remaining
uncertainties described above. Include supporting references.

Follow the user's requested format and destination, then existing repository
conventions. Otherwise, save to:

`docs/features/<feature>/tech-spec.md`

Update an existing specification in place. Preserve established requirements
and record consequential revisions explicitly. Link to authoritative product
and architecture artifacts rather than maintaining competing copies.

Finish with the artifact location, key decisions, and its readiness for
decomposition. Further decomposition or implementation follows the user's
requested scope.
