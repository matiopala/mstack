---
name: code-review
description: Review a PR, diff, or implemented change for irrefutable proof, regression protection, and code quality. Use when the user requests review or an implementation workflow calls for it.
---

<!-- Inspired by pstack's interrogate, adapted for a focused single-reviewer workflow:
https://github.com/cursor/plugins/blob/main/pstack/skills/interrogate/SKILL.md
Finding criteria, hidden-failure checks, and human notices are also inspired by
Armin Ronacher's Pi review extension:
https://github.com/mitsuhiko/agent-stuff/blob/main/extensions/review.ts
The code rubric follows this repo's implement principles.
-->

Use one reviewer. Delegate only when the user or calling workflow authorizes it
and the host permits it. A delegated reviewer performs the review itself
without spawning another reviewer. Reuse established context and widen
investigation only for concrete questions or risks.
Report findings without changing product code or building missing tests or
verification tools unless the user also requests that work.
When reviewing within an implementation workflow, return findings to the
implementing agent, which owns fixes. Identify a review performed by the
implementing agent in its current session as self-review.

## Ground the review

Establish the diff and comparison base, intended outcome, acceptance criteria,
and existing behavior that must remain working. Read relevant PR or task
context and accepted decisions. Clarify consequential gaps rather than treating
the implementation as its own specification.

Read the verification plan when present and use its scenario identifiers to
assess coverage and evidence. Check that implementation or execution changes
have not weakened required outcomes. Requirement revisions need a recorded
reason grounded in the intended behavior. For a small task without a separate
plan, review against the accepted criteria; a missing document alone is not a defect.

## Examine the proof first

Require irrefutable proof: reproducible, inspectable evidence that the
acceptance criteria hold under the stated test conditions.

Check that supplied evidence covers the intended behavior through meaningful
user or system entry points, including required side effects. It should identify
the tested code state, prerequisites, steps or commands, expected and observed
results, and relevant limitations or mocks. Manual evidence is valid.

Inspect what the cited checks and artifacts actually demonstrate. A green CI
badge, "tested locally," or instructions without observed results are
insufficient on their own.

Rerunning checks is optional, not a condition for a ready verdict. Run targeted
existing checks only when useful to resolve a concrete doubt. Distinguish
supplied evidence from checks you personally executed.

Missing or inadequate required proof blocks a ready verdict. State what remains
unproven and give the reproduction steps or test scenario, prerequisites, and
expected results needed to establish it. Do not invent commands for checks
that do not exist.

## Examine regressions and code quality

Trace the change through affected callers, contracts, stored data, ownership,
and failure or lifecycle paths. Check whether the regression evidence protects
the existing behavior at risk. Favor meaningful integration and end-to-end
checks; use unit tests where helpful, without a coverage-percentage gate.

Keep code findings discrete and actionable: each must identify a problem
introduced or worsened by the change, with a concrete scenario and demonstrable
impact. Identify affected callers or contracts before claiming downstream
breakage. Use requirements and accepted decisions to distinguish intentional
behavior from defects. Match review rigor to the project's conventions and
risk without weakening required acceptance proof.

Judge the code against these principles:

- Make the smallest correct change within scope and existing conventions.
- Prefer simple, explicit code and suitable existing implementations. Justify
  added abstractions, configuration, and dependencies with current requirements
  or concrete constraints; support performance claims with measurements.
- Give each module one coherent responsibility and a small interface that hides
  complexity. Avoid forwarding layers without a useful purpose.
- Keep ownership and dependencies explicit, validate external data at system
  boundaries, and use types or structures that make invalid states hard to represent.
- Handle meaningful failures deliberately; make retryable operations
  idempotent where practical.

Inspect changed catch blocks and fallback paths for failures disguised as
success or empty results. Recovery is valid when it preserves the intended
contract and required failure signals. If the current layer cannot recover
correctly, recommend propagating the error or handling it explicitly at an
appropriate boundary.

Flag maintenance costs introduced or worsened by the change only when you can
explain a concrete consequence and a simpler, scoped alternative. Material
maintainability problems can block even when tests pass. Allow justified,
bounded compromises and make their remaining costs explicit. Keep style
preferences optional and unrelated cleanup outside the review.

## Report the result

Explain the review in plain language, preserving priorities, references,
uncertainty, and reproduction instructions.

Keep the report concise:

1. **Verdict:** ready or not ready, with the reason. A ready verdict requires
   sufficient proof and no material correctness, regression, or maintainability blockers.
2. **Proof:** what the evidence establishes and how to reproduce it, or the
   precise gaps. Link detailed evidence rather than copying long logs.
3. **Findings:** prioritize by consequence. Give each material finding a code
   or evidence reference, a concrete scenario and impact, and the smallest
   useful remedy or check needed to resolve it.
4. **Human notices:** identify migrations, dependency changes, auth or permission
   changes, breaking contracts, and destructive or irreversible operations when
   present. Give locations and practical implications. These notices alone do
   not affect the verdict or create fix tasks; a defect needs its own finding.
   Omit this section when none apply.

Separate confirmed problems, unresolved risks, and optional improvements.
Do not invent findings to fill a review. If no material issue is found, state
what was examined and any relevant verification limits.
