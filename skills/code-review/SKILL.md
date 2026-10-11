---
name: code-review
description: Review a PR, diff, or implemented change for irrefutable proof, regression protection, and code quality. Use when the user asks for code review or a judgment of whether a change is ready.
---

<!-- Inspired by pstack's interrogate, adapted for a focused single-reviewer workflow:
https://github.com/cursor/plugins/blob/main/pstack/skills/interrogate/SKILL.md
The code rubric follows this repo's implement principles.
-->

Use one reviewer; delegate only when the user requests it. Reuse established
context and widen investigation only for concrete questions or risks.
Report findings without changing product code or building missing tests or
verification tools unless the user also requests that work.

## Ground the review

Establish the diff and comparison base, intended outcome, acceptance criteria,
and existing behavior that must remain working. Read relevant PR or task
context and accepted decisions. Clarify consequential gaps rather than treating
the implementation as its own specification.

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

Judge the code against these principles:

- Make the smallest correct change within scope and existing conventions.
- Prefer simple, explicit code. Justify abstractions, configuration, and
  dependencies with concrete needs; support performance claims with measurements.
- Give each module one coherent responsibility and a small interface that hides
  complexity. Avoid forwarding layers without a useful purpose.
- Keep ownership and dependencies explicit, validate external data at system
  boundaries, and use types or structures that make invalid states hard to represent.
- Handle meaningful failures deliberately; make retryable operations
  idempotent where practical.

Flag maintenance costs introduced or worsened by the change only when you can
explain a concrete consequence and a simpler, scoped alternative. Material
maintainability problems can block even when tests pass. Allow justified,
bounded compromises and make their remaining costs explicit. Keep style
preferences optional and unrelated cleanup outside the review.

## Report the result

Apply [bro](../bro/SKILL.md) to explain the review in plain language while
preserving priorities, references, uncertainty, and reproduction instructions.

Keep the report concise:

1. **Verdict:** ready or not ready, with the reason. A ready verdict requires
   sufficient proof and no material correctness, regression, or maintainability blockers.
2. **Proof:** what the evidence establishes and how to reproduce it, or the
   precise gaps. Link detailed evidence rather than copying long logs.
3. **Findings:** prioritize by consequence. Give each material finding a code
   or evidence reference, a concrete scenario and impact, and the smallest
   useful remedy or check needed to resolve it.

Separate confirmed problems, unresolved risks, and optional improvements.
Do not invent findings to fill a review. If no material issue is found, state
what was examined and any relevant verification limits.
