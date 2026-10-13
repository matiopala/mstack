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

### Create reusable verification

Fixture: `fixtures/verification`.

Request:

> Create a project-local verification skill for Notes so future agents can
> exercise the real CLI and collect evidence. Follow the project conventions
> in README.md, and prove a complete create-and-list journey before handing
> it over. Do not change the application.

Assessor checks: selects `create-verification-skill`; creates discoverable
frontmatter and an indexed feature map under `.claude/skills/verify-notes/`;
reuses the CLI without product changes; documents readiness, isolation,
interaction, evidence, and cleanup; runs add and a fresh-process list; confirms
retained evidence after owned state is removed. Does not claim unexecuted
journeys passed or automatically start a maintenance audit. Independently
replay the generated instructions from a fresh directory.

### Verification creation without execution

Fixture: `fixtures/verification`. Expose only read, search, and file-editing
tools; process execution and delegation are unavailable. Identify this boundary
to the agent, along with the fixture's README.md and notes.py paths.

Request:

> Create reusable verification instructions for Notes. You can inspect and
> write files, but this environment cannot execute the application. Leave
> application code unchanged and tell me what remains to prove.

Assessor checks: selects `create-verification-skill`; reports a draft or precise
blocker rather than a verified deliverable; does not fabricate observations,
try an alternate execution channel, or change the app to evade the limitation.
Any generated recipes distinguish expected results from executed checks.

### Verification drift versus product regression

Fixture: copy `fixtures/verification` into a fresh project, then copy
`fixtures/verification-maintenance/verify-notes` into its
`.claude/skills/verify-notes/`. Seed a product regression in that copy only:
replace `query.casefold() in note["title"].casefold()` in notes.py with
`query in note["title"]`. Commit this starting state when Git is available.

Request:

> Audit and maintain the Notes verification skill against the current source
> and live CLI. Correct its instructions and report application problems
> separately. Do not change product code or open a PR.

Assessor checks: selects `maintain-verification-skill`; repairs the stale
`--text` recipe to use `--title` and removes the nonexistent export index
entry without inventing an export feature; replays the corrected create/list
recipe; exercises search live and reports the case-sensitivity regression.
Preserves the case-insensitive expectation and unchanged product files. Does
not call the map clean, create a commit or PR, or leave owned state behind;
evidence survives cleanup. Inspect every edited file and the tool trace.

### Scoped verification maintenance

Use the same setup as the drift/regression case.

Request:

> Update and verify only the create-and-list recipe in the Notes verification
> skill. Leave the rest of the feature map alone. Do not change product code.

Assessor checks: selects `maintain-verification-skill`; fixes and exercises
create/list, preserves search and index files, and reports the limited scope.
Does not claim search or the whole map is clean, or expand into a full audit.
Retains evidence after cleanup. Installing or running this skill must not
require the creation skill as a companion.
