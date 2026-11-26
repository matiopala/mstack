---
name: design-verification
description: Design acceptance and regression tests for a defined change. Identify observable outcomes, reusable repository tests, missing assertions, and any human judgments.
---

Map accepted behavior to tests someone can rerun from the repository. A
design-only request returns that mapping in chat. Write a verification document
when the user requests one, or use an existing task or spec during delivery.

## Choose the tests

Read the requirements, relevant existing tests, and project conventions. Treat
current behavior as evidence. Resolve consequential disagreements with the
accepted behavior before choosing an expected result.

For each meaningful success, failure, or compatibility obligation, identify

- The starting state and action through the affected user or system entry point.
- The observable outcome and side effects. For persistence, a new process or a
  fresh read can distinguish saved data from cached state.
- The test selector that already asserts this outcome, or the missing assertion
  and where to add it. Describe proposed commands as proposed until exercised.

Choose the narrowest test that covers the affected boundary. Use the project's
normal suite. Indicate a PR or on-demand invocation and any missing environment,
mocks, or limits. Specify performance thresholds when the requirement calls for
them. Reserve manual acceptance for judgments that need a person.

## Preserve the contract

Use stable IDs when scenarios are referenced across artifacts. Keep outcomes
and IDs through replanning. Preserve internal representations only when they
are part of the compatibility contract. Record the source and reason for a
changed requirement or a corrected scenario. Investigate a failing assertion
before revising its expected result.

For small changes the task or chat can hold the whole design. A separate
document can help with a complex contract or human judgment. Once tests exist,
link their selectors instead of repeating setup and assertions in prose. Keep
observed results with the run that produced them.
