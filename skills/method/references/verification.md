# Independent verification

Register a fresh independent verifier using [hosts.md](hosts.md). Include this role
contract and the baseline-to-candidate diff. Give it artifact-only context, never
implementation chat or a request to agree with the implementer. No further delegation.

Verify build and instance identity before exercising a long-running app and after
unexpected failures. Use safe local/test environments and state owned by this run.
Follow project instructions for persistent staging profiles; never reset persistent
state without explicit approval. Record relevant external versions, mocks, and limits.

Execute required automated scenarios through real entry points. Capture actions,
commands, expected and observed results, side effects, and failure diagnostics.
Inspect what tests actually establish. Green output, a plan, and an implementer's
completion message are insufficient proof. A manual observation can be evidence,
but scenarios explicitly requiring human judgment remain for the human reviewer.

Review the baseline-to-candidate diff for concrete correctness, regression, and
material maintainability defects. Trace affected callers and contracts before
asserting impact. Check hidden failures, ignored exceptions, and fallbacks that mask
errors. Separate blocking findings from optional style suggestions.

Use `command` to retain safe command output, or `evidence` to import sanitized native
tool observations. Every pass/fail references evidence IDs from this run. Report
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
