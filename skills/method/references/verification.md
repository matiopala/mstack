# Independent verification

Register a fresh independent verifier using [hosts.md](hosts.md). Include this role
contract and the baseline-to-candidate diff. Give it artifact-only context, never
implementation chat or a request to agree with the implementer. No further delegation.

Verify build and instance identity before exercising a long-running app and after
unexpected failures. Use safe local/test environments and state owned by this run.
Follow project instructions for persistent staging profiles; never reset persistent
state without explicit approval. Record relevant external versions, mocks, and limits.

Inspect the checkpointed test and its dependencies against the requirement.
Use `test` on the clean candidate for each automated scenario. Method reruns the
bound command and records the selected case's outcome. Examine failures and
side effects. An unavailable environment, skipped case, or empty selection
leaves the scenario unverified. Compare baseline and candidate evidence and
surface baseline gaps to the reviewer. Human judgments remain for the human reviewer.

Review the baseline-to-candidate diff for concrete correctness, regression, and
material maintainability defects. Trace affected callers and contracts before
asserting impact. Check hidden failures, ignored exceptions, and fallbacks that mask
errors. Separate blocking findings from optional style suggestions.

Use `command` or `evidence` for supplementary diagnostics and observations. An
automated pass/fail must reference the latest `test` result for that scenario. Report
every approved scenario as `pass`, `fail`, `unverified`, or (only for human scenarios)
`human_pending`. Missing required evidence blocks readiness.

The verifier does not edit product code, tests, or helpers. Return corrections to
the implementer. Dirty verifier source cannot pass the controller gate. Record
resolved/rejected findings with supporting reasoning and evidence references. Keep
the original finding IDs and failure history visible across rounds.

Submit `verify` with scenario results, findings, review coverage, launch instructions,
tradeoffs, limitations, and confirmation that owned commands stopped. Inspect its
readiness result. A failed round returns to implementation under existing authority;
capture a new candidate and verify again. A missing environment capability can
instead be recorded as a blocker. Repeated ineffective attempts require a changed
diagnosis or human decision, not another identical retry.

For evidence-only authorization, a finished report that is not ready instead needs
a human decision: authorize another evidence attempt or authorize implementation
corrections. Present that exact decision and retain the current candidate and report.
An interrupted verifier that has not submitted a report can retry within the
remaining authorization limits.

Human review requires all automated scenarios to pass and no open blocking findings.
Optional suggestions do not keep the loop alive. Stop at the execution limit and
preserve work.
