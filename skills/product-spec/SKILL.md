---
name: product-spec
description: Define the user problem, intended outcomes, required behavior, and evidence of success for a software product or feature before technical design.
---

Create a product specification anchored in user outcomes. Every requirement
must advance an agreed outcome or protect a necessary constraint.

Consult relevant accepted decision records. Load [adr](../adr/SKILL.md) only
when a consequential product choice warrants creating or revising a record.
Link the records from the specification.

## Discover

Reuse established context and decisions. Ask only about consequential gaps
that available context cannot resolve. Investigate factual gaps before asking;
resolve dependent questions in order and group independent questions when useful.

Clarify who experiences the problem, when it occurs, their current workaround,
and why improvement matters. Connect requested features to this underlying
goal before expanding the solution.

Distinguish evidence, requirements, assumptions, and proposed decisions.
Challenge unsupported claims respectfully and recommend concrete tradeoffs
when helpful.

## Specify

Define:

- **Outcome:** The primary improvement in what users can accomplish or
  experience, its connection to business objectives where relevant, and
  outcomes that must not worsen.

- **Scope and behavior:** The smallest complete experience that achieves
  the outcome. Describe starting situations, actions, expected results,
  and important failure or recovery paths. Resolve ambiguous product
  semantics, identify necessary constraints, and make deliberate exclusions
  clear. Leave technical mechanisms to technical design.

- **Acceptance:** Observable criteria for the required behavior, including
  affected existing functionality that must remain working. Require
  irrefutable proof: reproducible, inspectable evidence that these criteria
  hold under stated conditions. Detailed test implementation belongs to
  technical design and delivery.

- **Product value:** Meaningful success measures and how remaining value
  hypotheses will be evaluated through observation, experiments, or usage.
  Specify baselines, targets, and evaluation periods when justified;
  otherwise identify what must be learned. Keep measurement proportional
  to the decision. Passing acceptance tests does not establish usefulness.

- **Decisions and uncertainty:** Consequential tradeoffs and unresolved
  questions that could change the design. Link ADRs for durable rationale.

## Artifact and readiness

Create or update one authoritative specification using the structure above,
scaled to the work. Keep supporting evidence close to the claims it supports.

Follow the user's requested format and destination, then repository
conventions. Otherwise, save to:

`docs/features/<feature>/product-spec.md`

Preserve agreed requirements and record consequential revisions explicitly.
Reference existing sources rather than maintaining competing copies.

Mark the specification ready for technical design when scope, required
behavior, acceptance criteria, and consequential product decisions are clear.
Otherwise, label it as a draft and identify what is needed to proceed.
Unvalidated value hypotheses may remain if their validation approach is explicit.

Finish with the artifact location, agreed outcome, and readiness status.
Further work follows the user's requested scope.
