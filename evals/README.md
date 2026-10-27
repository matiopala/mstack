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
   Judge whether task splits, documentation, and supporting code serve the
   request. Fewer files alone do not establish proportionality; check for
   repeated requirements, unnecessary separate tasks, and unjustified tooling.

Record the skill revision or content digest, harness/model when known, case,
workspace or retained artifacts, observed behavior, and pass/fail/unverified
checks. Separate observed facts from predictions. Preserve useful trace excerpts
without secrets. Results belong in `evals/results/`; logs may remain outside the
repository with resolvable references. Rerun affected cases after material fixes.

## Cases

### Verification design and implementation replanning

Fixture: `fixtures/verification`. Copy it to a fresh workspace.

Request:

> Use `plan` to plan improved storage reliability for Notes. Preserve the CLI,
> exact titles, IDs, insertion order, case-insensitive substring search, and
> existing saved notes. A failed add must leave existing notes intact, and a
> successful add must be visible from a new process. Start with temporary-file
> writes and atomic replacement. Keep the implementation plan at
> `docs/features/storage/plan.md`. Plan only; do not change application code.

Then give the same session this follow-up:

> Change the implementation approach to SQLite, importing existing saved notes
> on the first add; reads remain read-only. Keep the requested behavior. Update
> the implementation plan.

Assessor checks: `plan` loads `design-verification`; creates a separate,
proportionate verification plan; ties scenarios to requirements; distinguishes
outcomes from execution methods; preserves scenario identifiers and required
outcomes across replanning; updates setup or check mechanics where needed;
links the verification plan from the implementation plan without maintaining
a competing checklist. No application edits or claims of delivered behavior.
Required outcomes must not turn incidental storage representation into an
obligation: record preservation need not mean byte-identical database files.
Retain snapshots before and after the follow-up and compare scenario meaning,
not only file hashes.

### Verification requirement revision

Continue the previous case, or give a fresh session a copy of its saved
verification and implementation plans:

> Requirements changed: search must now be case-sensitive substring matching.
> Update the verification plan to reflect that decision. Keep the other behavior.

Assessor checks: revises the affected scenario with an explicit reason and
source, preserves unrelated scenarios and identifiers, and does not silently
regenerate the whole plan or execute product changes. Missing scenarios may be
added with new identifiers without weakening existing obligations.

### Verification design without a harness

Fixture: `fixtures/verification`. Use a fresh workspace.

Request:

> Use `design-verification` to design verification for an optional cloud backup
> feature. A successful upload must be retrievable by a new authenticated
> session; a failed upload must leave the previous backup available. Backup has
> not been implemented, and there is no cloud test account or harness. Design
> the checks and identify prerequisites; do not implement or provision anything.

Assessor checks: defines observable success, failure, and relevant local-data
regressions; records the missing implementation, access, and harness; invents
no runnable commands or observed passes; does not create a project skill,
product code, or infrastructure as part of verification design.

### Small verification design

Fixture: `fixtures/verification`. Use a fresh workspace.

Request:

> Use `design-verification` for this small change: make `notes.py --version`
> print `notes 1.1`, still exiting successfully without requiring a data
> directory. Give me the verification plan in chat only.

Assessor checks: returns a short, separately labeled plan with stable scenario
identifiers, expected output and exit status, and a proportionate regression
check. No files, helper scripts, or claimed evidence for an unimplemented change.

### Verification recipe handoff and failing implementation

Fixture: `fixtures/verification`, with `fixtures/verification-design/verification.md`
copied to `docs/features/notes/verification.md` in the workspace.

Request:

> Use `create-verification-skill` to create and prove reusable Notes verification
> recipes from `docs/features/notes/verification.md`. Do not change the app.

Assessor checks: reads the plan; references the scenario identifiers in runnable
recipes; proves at least one real journey and keeps evidence separate; reports
which scenarios were exercised; preserves the requirements. Independently
replay a generated recipe after the run.

For the failure case, use a separate copy of the resulting workspace. Change
search to compare the query and title without case folding, leaving the
verification requirements unchanged. Give a fresh session this request:

> Use `maintain-verification-skill` to update the Notes verification recipes and
> check them against the current app. No search behavior change was approved.
> Do not change product code or the verification plan.

Assessor checks: reports the search mismatch as a product regression, preserves
the case-insensitive expectation and scenario reference, and records the failing
observation instead of changing the recipe to accept current behavior. A review
of those artifacts must not claim completion based on the other passing checks.

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

Fixture: `fixtures/inventory`. Delegation is available for this case.

Request:

> Implement `in_stock(stock, sku)` in inventory.py. Return true exactly when the
> SKU has a positive quantity; missing SKUs are out of stock. Preserve reserve's
> current behavior. Verify and finish the change.

Assessor checks: selects `implement`; checks the relevant behavior and performs
labeled self-review for this straightforward change, without a reviewer
handoff or renewed approval. A clean verdict ends the loop; self-review does
not weaken the acceptance or regression evidence.

### Explicit independent implementation review

Use the same fixture and request as the clean implementation case, with
delegation available, and add:

> Have one fresh, independent reviewer review the change before finishing.

Assessor checks: completes the implementation and verification, then uses one
fresh reviewer without renewed approval. Retain the reviewer exchange; the
reviewer reports findings and the implementing agent handles material fixes.
Self-review does not satisfy the explicit request. A clean review ends the loop.

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
frontmatter and discoverable recipes, inline or linked, under
`.claude/skills/verify-notes/`;
reuses the CLI without product changes; documents readiness, isolation,
interaction, evidence, and cleanup; runs add and a fresh-process list; confirms
retained evidence after owned state is removed. Does not claim unexecuted
journeys passed or automatically start a maintenance audit. Independently
replay the generated instructions from a fresh directory.

For this small CLI, assess whether a concise command recipe would suffice.
Any helper, including inline code, should remove concrete repetition or fragile
interaction rather than add a generic reporting framework. Preserve meaningful
assertions, evidence, and cleanup when judging simplicity.

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
create/list without renewed approval, preserves search and index files, and
reports the limited scope.
Does not claim search or the whole map is clean, or expand into a full audit.
Retains evidence after cleanup. Installing or running this skill must not
require the creation skill as a companion.

### Verification drift check without repair

Use the same setup as the drift/regression case.

Request:

> Check the Notes verification instructions for drift against the current source
> and live CLI. Tell me which instructions are stale and whether the application
> violates any documented expectations.

Assessor checks: selects `maintain-verification-skill`; reports the stale `--text`
flag, missing export recipe, and case-sensitivity regression. Leaves verification
instructions, helpers, and product files unchanged, without asking for repair
permission as a prerequisite to completing the audit. Safe diagnostic commands
may use `--title`, but their success does not make the unchanged create recipe
pass. Retains evidence outside the skill directory, cleans up owned state, and
does not call the map clean.
