---
name: design-review
description: Critically review a proposed product spec, architecture, technical design, or implementation plan against its goals, constraints, and acceptance criteria. Use when the user asks to challenge a design or review a proposal.
---

<!-- Inspired by pstack's interrogate skill, adapted for design review:
https://github.com/cursor/plugins/blob/main/pstack/skills/interrogate/SKILL.md
-->

Assess whether the proposed solution can achieve its goal with reasonable
complexity and convincing verification.

## Ground the review

Read the proposal, its intended outcome, constraints, acceptance criteria,
and relevant accepted decisions. Inspect code, tests, or other evidence around
specific design assumptions. Ask about missing context only when it could
materially change the review; otherwise state the uncertainty.

Judge the design at its current stage. Missing detail is a finding only when
it must be settled now; leave routine implementation choices to delivery.

## Challenge the design

Focus on the questions that matter for this proposal:

- Does the proposed behavior achieve the goal? Are important user paths or
  requirements missing, contradictory, or outside the agreed scope?
- Are responsibilities, ownership, interfaces, and data flow clear enough
  for the affected components to work together?
- Are significant edge cases, failures, compatibility requirements, and
  regressions addressed? Can rollout leave the system in a valid state?
- Is the complexity justified? Prefer the smallest correct solution, coherent
  responsibilities, and small interfaces that hide implementation details.
- Can the acceptance criteria produce irrefutable proof: reproducible,
  inspectable evidence that the required behavior holds under stated
  conditions? Check meaningful integration, end-to-end, and regression
  scenarios where relevant; coverage percentages alone prove little.

Use independent reviewers for substantial or risky designs when available
and useful. Give them the same proposal, goals, and relevant context.
Reconcile disagreements and verify findings against evidence; reviewer
agreement is not proof.

## Judge the findings

Prioritize by consequence. Separate issues that block the design's next step
from optional improvements and questions needing evidence.

For each material finding, explain:

- The specific weakness, with an artifact reference or explicit assumption.
- A concrete scenario showing why it matters.
- The smallest useful improvement and how to check that it resolves the issue.

Preserve sound decisions. Do not invent flaws to fill a review or turn style
preferences into requirements. If no material issue is found, say what was
examined and what remains unverified.

Keep proposed changes visibly recommended. Revise artifacts or start
implementation only when included in the user's requested scope.

## Explain the review

By default, read and apply [bro](../bro/SKILL.md) to the review draft before
presenting findings.
Preserve the verdict, priorities, supporting references, uncertainty, and
recommended actions while simplifying the language.

Lead with whether the design is ready for its intended next step and why.
Follow with the important findings and the decisions or evidence needed.
Return the plain-language review directly, without a separate technical
version or commentary about rewriting it.
