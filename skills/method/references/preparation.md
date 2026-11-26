# Preparation

The sequence is Interview → Exploration → Requirements → Verification Design →
Plan. Each submitted artifact needs human approval before advancing. A response
requesting changes creates a rejected revision; revise rather than overwriting it.
Show the document, revision, and pending decision in chat and the dashboard.

## Interview

Read supplied context first. Ask one consequential question at a time, resolving
dependencies before implementation details. Establish outcome, audience, scope,
constraints, compatibility, examples of success, and important exclusions. Do not
ask for facts discoverable in the repository. Record decisions, assumptions, and
remaining gaps in a short interview artifact.

## Exploration

Inspect instructions, relevant implementation flows, tests, and existing verification
recipes at the recorded baseline. Follow concrete entry points through state changes
and observable results. Report evidence with code references, integration constraints,
regression risks, and feasible verification options. Current behavior is evidence,
not the specification. Reconcile discoveries that change consequential choices.

## Requirements

Describe the smallest complete outcome in observable terms, including success,
failure, compatibility, and relevant regression behavior. Use stable IDs such as
`R01` in the Markdown and the submission's `criteria` array. Distinguish assumptions
from requirements and resolve consequential ambiguity before requesting approval.
Keep incidental implementation choices out of requirements.

## Verification design

Use stable scenario IDs such as `V01`, each referencing approved requirement IDs.
For each, describe starting conditions, the real entry point/action, expected
observable result, required side effects, and evidence that would expose failure.
Declare `kind: automated` for objective tests and `kind: human` for judgments
requiring a person. Every requirement needs coverage. For each automated scenario,
approve the exact repository-relative `test_files` containing its assertions and
supporting fixtures, including new files the implementer will author. Review
those paths as test-only. Declare the expected `baseline` as `fail` for changed
behavior or `pass` for preservation.
If using a native JUnit reporter, identify its actual test runner as an argv
prefix, such as `["python3","-m","pytest"]`. Custom assertion scripts belong
in the approved test files. Inspect that the runner executes the assertion.

Reuse sufficient project commands and recipes; identify missing prerequisites
honestly rather than inventing executable commands. Cover success, failure, and
regression obligations proportional to the change. Coverage percentages are not
proof. Verify persistence with a fresh read or restart where relevant.

Keep the scenario brief. Put machine-checkable expectations in the target
project's normal test suite. Record observed outcomes in run evidence. Correcting a faulty
scenario requires a documented revision and approval; never fit expectations to a
failing implementation. Preserve stable IDs and explain retired/revised obligations.

## Plan

Specify the smallest implementation approach that satisfies approved requirements
and verification scenarios. Resolve consequential APIs, ownership, data flow,
compatibility, failure handling, and migration choices. Schedule the test baseline before product changes and a rerun on the candidate. Reference scenario IDs rather than copying criteria.
Include launch and environment instructions needed by a fresh implementer/verifier.

Interview and exploration may be skipped only on an explicit human decision with
a reason. Requirements and verification design cannot be skipped. Waiving a plan
is exceptional and requires an explicit rationale. Even a waiver has a readable
retained artifact. After preparation approval, stop at implementation authorization.
