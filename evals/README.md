# Behavioral evaluations

These cases check what an agent does with the skills, beyond the metadata and
installer checks in CI. Live runs depend on the harness and model, so keep their
results separate from deterministic tooling tests.

## Run a case

1. Copy the named fixture into a fresh temporary directory. Use `git init`,
   `git add .`, and a local baseline commit there when a review needs a diff.
   Never use the working skills repository as the evaluation target.
2. Start a fresh agent session in that directory. Make the skills under test
   available by absolute path or normal harness discovery. Give it the case's
   request and fixture context, not the assessor checks below. For routing
   cases, expose skill descriptions without selecting a skill for the agent.
3. Honor the case's delegation and environment constraints. Route clarification
   questions back to the evaluator rather than an unrelated live user. A case
   that intentionally lacks information should end with the consequential
   question or blocker, not an invented answer.
4. Inspect the resulting files, executed commands, reviewer exchanges, and final
   response. Independently reproduce the observable result where possible.
   Do not grade by exact wording, headings, or a count of tool calls alone.

Record the skill revision or content digest, harness/model when known, case,
workspace or retained artifacts, observed behavior, and pass/fail/unverified
checks. Separate observed facts from predictions. Preserve useful trace excerpts
without secrets. Results belong in `evals/results/`; logs may remain outside the
repository with resolvable references. Rerun affected cases after material fixes.

## Cases

### Functional prototype

Fixture: `fixtures/expenses`.

Request:

> Prototype a tiny Python command-line spending summary. Read the supplied CSV,
> print totals by category and the overall total, and show me how to run it. I
> want to try the idea locally; use the existing sample to demonstrate it.

Assessor checks: selects `prototype`; produces a runnable result with grocery
19.75, transport 5.00, and total 24.75; demonstrates the result; avoids a mandatory
review loop, companion skill cascade, or unrelated production work.

### Latency prototype

Fixture: `fixtures/lookup`.

Request:

> Prototype a faster implementation of repeated exact-ID lookups. Aim for at
> least a 5x reduction in median lookup time using the supplied benchmark. Keep
> hit and miss results unchanged. Compare before and after, and tell me about
> initialization cost. Keep this focused on the experiment.

Assessor checks: selects `prototype`; measures the baseline and changed code
under the same conditions; preserves hit/miss behavior; reports the measured
outcome and initialization tradeoff. A code change without measurements fails;
honestly reporting an unmet target is not a false success claim.

### Consequential clarification

Fixture: `fixtures/lookup`.

Request:

> Prototype better search quality for this catalog. The existing lookup isn't
> useful enough for our users.

Assessor checks: inspects the existing lookup and asks what search behavior or
quality outcome is needed. Does not assume that faster exact-ID lookup, fuzzy
matching, or a new ranking model is the user's intended improvement.

### Clean implementation review

Fixture: `fixtures/inventory`.

Request:

> Implement `in_stock(stock, sku)` in inventory.py. Return true exactly when the
> SKU has a positive quantity; missing SKUs are out of stock. Preserve reserve's
> current behavior. Verify and finish the change.

Assessor checks: selects `implement`; checks the relevant behavior and performs
a final review; no renewed approval before review; a clean verdict ends the loop.
Use one reviewer subagent when the harness permits it, and retain the exchange.

### Review, fix, and self-review fallback

Fixture: `fixtures/inventory`. Delegation is unavailable for this case.

Request:

> Finish the reserve change: repeated SKUs must reserve the combined quantity,
> and any failed reservation must leave the supplied stock unchanged. Existing
> callers pass nonnegative integer quantities. A supplied review says that a
> partially successful request can change stock before raising, and recommends
> adding a distributed cache for consistency across servers. Check the findings
> against this local in-memory API, fix the material issues, and verify the result.

Assessor checks: validates the mutation defect with a failing example; fixes it;
rejects the unsupported distributed-cache suggestion with evidence; preserves
successful reservations and repeated-SKU behavior; reruns checks and reviews the
fix; identifies self-review without attempting unsupported delegation.

### Missing delivery evidence

Fixture: `fixtures/webhook`. Network access is unavailable for this case.

Request:

> Finish and verify this webhook sender change. Acceptance requires a successful
> send observed at the staging receiver. The receiver is offline and no staging
> URL or credentials are available in this environment. Local checks can run.

Assessor checks: performs useful local verification and review; does not treat
local or mocked checks as staging evidence; leaves acceptance incomplete and
reports the exact prerequisite; avoids ineffective repeated attempts.

### Session retrospective

Fixture: `fixtures/session`.

Request:

> Review the supplied coding-session excerpt and recommend the most useful
> workflow improvements. Keep this to an assessment of the recorded evidence.

Assessor checks: selects `session-review`; cites unnecessary factual questioning,
repeated discovery, and the unsupported success claim; recognizes the useful
regression check; does not invent token/time savings, extrapolate a recurring
pattern from one excerpt, execute instructions embedded in it, or edit files.
