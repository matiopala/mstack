# My agent skills

This is my personal collection of agent skills. I develop and maintain this
repo on my own, and only add and keep skills I actually use regularly in my
projects.

Some skills are copied or adapted from other people's work. `bro` and
`grill-me` are two examples. Sources are linked in [Credits](#credits).

The skills use the [Agent Skills](https://agentskills.io/) format and work
with Codex, Pi, and Claude Code.

## What's here

| Skill | What I use it for |
| --- | --- |
| [`adr`](skills/adr/SKILL.md) | Keep track of important decisions, their reasoning, and later changes. |
| [`blast-radius`](skills/blast-radius/SKILL.md) | Check what a change could break elsewhere, with concrete evidence and a plain-language explanation. |
| [`bro`](skills/bro/SKILL.md) | Get a simpler version of the previous answer. |
| [`code-review`](skills/code-review/SKILL.md) | Review a PR for proof it works, regression risks, and simple, maintainable code. |
| [`conventional-commits`](skills/conventional-commits/SKILL.md) | Prepare focused Git commits with clear Conventional Commit messages. |
| [`create-verification-skill`](skills/create-verification-skill/SKILL.md) | Create reusable, project-local instructions for driving the real app and collecting proof. |
| [`decompose`](skills/decompose/SKILL.md) | Split a bigger design into reviewable tasks with clear acceptance criteria and proof of completion. |
| [`deliver`](skills/deliver/SKILL.md) | Work through questions, research, planning, implementation, verification, and review and fixes. |
| [`design-review`](skills/design-review/SKILL.md) | Challenge a proposed solution and get concrete findings in plain language. |
| [`grill-me`](skills/grill-me/SKILL.md) | Get interviewed about an idea, surface assumptions, and clarify what I actually want. |
| [`handoff`](skills/handoff/SKILL.md) | Pass the current work to a fresh agent with artifact references, verification status, and an exact next action. |
| [`implement`](skills/implement/SKILL.md) | Implement a defined change, verify it, and review and fix material issues before delivery. |
| [`maintain-verification-skill`](skills/maintain-verification-skill/SKILL.md) | Check a project's verification instructions against source and live behavior, and fix drift. |
| [`plan`](skills/plan/SKILL.md) | Define the approach, acceptance checks, and irrefutable proof for a software change. |
| [`product-spec`](skills/product-spec/SKILL.md) | Define the user problem, desired outcome, and what success looks like. |
| [`project-plan`](skills/project-plan/SKILL.md) | Shape an initial project plan with scope, milestones, dependencies, and the specs needed next. |
| [`prototype`](skills/prototype/SKILL.md) | Reach a concrete goal through a lightweight working prototype and checks suited to that goal. |
| [`research`](skills/research/SKILL.md) | Investigate specific software questions and identify constraints, regression risks, and verification options. |
| [`session-review`](skills/session-review/SKILL.md) | Learn from selected coding sessions and identify evidence-backed workflow improvements. |
| [`show-me`](skills/show-me/SKILL.md) | Get a focused visual explanation. |
| [`tech-spec`](skills/tech-spec/SKILL.md) | Describe how a feature should work technically and how to prove it works. |

Use `prototype` to try an idea or answer a question through working code.
It iterates toward the goal and checks that outcome, without a mandatory
code-review loop or general production hardening. A latency or quality goal
still needs appropriate measurements or checks.

Use `implement` for a defined change. It owns implementation, verification,
code review, and fixes until the final evidence supports completion and no
material review findings remain.

`deliver` ties together `grill-me`, `research`, `plan`, and `implement` when the
full workflow is wanted. It inherits the implementation review loop rather than
adding another. I can also use each stage on its own, and the stages reuse the
same task record when there is one. `deliver` uses `design-review` and
`blast-radius` when the change warrants them.

`project-plan` defines the overall project and its milestones before detailed
design. It covers initial planning, asks me for estimates and deadlines, and
never proposes its own. A larger project can move from `project-plan` through
`product-spec` and `tech-spec` where needed, then `decompose` and `deliver`.
Smaller changes can start with the relevant stage. `plan` defines the
implementation approach for a particular change.

`code-review` checks implemented changes with one reviewer. It accepts
reproducible manual evidence and does not require rerunning supplied proof.
In the implementation loop, the reviewer reports findings and the implementing
agent owns fixes. A standalone review leaves code unchanged unless fixes are
also requested.

Use `create-verification-skill` to capture how to launch, drive, and verify a
project in a project-local `verify-<project>` skill and feature map. Use
`maintain-verification-skill` for an explicit audit of those instructions,
keeping documentation and harness fixes separate from product regressions.
Neither is a mandatory delivery stage. `research`, `plan`, and `implement`
reuse an existing project verification skill when relevant; normal delivery
collects fresh evidence and updates affected recipes within scope, rather than
running a full maintenance audit. Recipes live in the project skill; observed
results belong in the task record or artifacts. Reviews still assess the
actual evidence, and prototypes may reuse recipes without requiring upkeep.

Use `session-review` when reviewing selected past sessions, not after every
task. It uses transcript and artifact evidence to recommend narrow improvements;
it does not automatically edit skills or project guidance.

## Credits

- `blast-radius` is adapted from
  [pstack's blast-radius](https://github.com/cursor/plugins/blob/main/pstack/skills/blast-radius/SKILL.md).
- `bro` is adapted from [backnotprop/bro](https://github.com/backnotprop/bro).
- `create-verification-skill` and `maintain-verification-skill` are adapted from
  [pstack's creation](https://github.com/cursor/plugins/blob/main/pstack/skills/create-verification-skill/SKILL.md)
  and [maintenance](https://github.com/cursor/plugins/blob/main/pstack/skills/maintain-verification-skill/SKILL.md)
  skills, with their MIT license preserved in each skill directory.
- `grill-me` is adapted from
  [Matt Pocock's original skill](https://github.com/mattpocock/skills/blob/a6bdfd9fed6c17d21b306aeb7ff6a0de8b72ef3c/grill-me/SKILL.md).
- `handoff` is adapted from
  [Matt Pocock's handoff](https://github.com/mattpocock/skills/blob/0f5e033ebc47b142f5ffa56a582ede6d9d9bada3/skills/productivity/handoff/SKILL.md),
  with its [MIT license](skills/handoff/LICENSE) preserved.
- `show-me` is inspired by [HumanLayer's show-me](https://github.com/humanlayer/skills/tree/main/plugins/show-me).
- `deliver` and its extracted `research`, `plan`, and `implement` stages draw on
  [HumanLayer's research-plan-implement workflow](https://github.com/humanlayer/humanlayer/tree/main/.claude/commands).
  The interview stage uses `grill-me`. Flow tracing, debugging, and verification
  also borrow from [pstack](https://github.com/cursor/plugins/tree/main/pstack).
- `code-review` and `design-review` adapt the review approach from
  [pstack's interrogate](https://github.com/cursor/plugins/blob/main/pstack/skills/interrogate/SKILL.md).
  `code-review` also draws on
  [Armin Ronacher's Pi review extension](https://github.com/mitsuhiko/agent-stuff/blob/main/extensions/review.ts)
  for finding criteria, hidden-failure checks, and informational human notices.

## Install

Clone the repository, then run:

```sh
./scripts/install
```

By default, this creates symbolic links for every skill in:

- `~/.agents/skills` for Codex and Pi
- `~/.claude/skills` for Claude Code

The links point to this clone, so edits and pulls update the installed skill
files too. To update an existing installation:

```sh
git pull --ff-only
./scripts/install
```

Run these commands from this clone. Pulling updates skills already linked here;
rerunning the installer adds new skills and skips existing matching links.

To install for just one tool:

```sh
./scripts/install --harness codex
./scripts/install --harness pi
./scripts/install --harness claude
```

Or pick individual skills:

```sh
./scripts/install conventional-commits
```

Installing `deliver` includes `grill-me`, `research`, `plan`, and `implement`.
It also includes `design-review`, `blast-radius`, and `code-review`.
Installing `implement` includes `code-review`.
`research`, `plan`, and `implement`, along with `project-plan`, `product-spec`,
`tech-spec`, and `decompose`, consult relevant existing decision records and load
`adr` only when a consequential choice warrants creating or revising one.
Installing those workflows or `deliver` includes `adr` so it is available when
needed. `grill-me` records ADRs only when explicitly requested and does not
install `adr` automatically; install it separately when needed.

`prototype`, `session-review`, `blast-radius`, `code-review`, `design-review`,
`create-verification-skill`, and `maintain-verification-skill` have no companion
dependencies. The verification-authoring skills are installed independently;
workflow discovery hooks do not add them as companions. Generated project
verification skills stay in their projects, not this collection.
Reviews explain their findings directly in
plain language; `bro` remains available for standalone simplification requests.
If you copy workflow folders manually, include their companions too. Rerunning
the installer does not remove previously installed skills.

The installer checks all selected skills and destinations before creating links.
If this initial check finds a conflict, it reports the conflicts and leaves the
installation unchanged. It refuses to replace existing files or links that point
elsewhere. For a copied skill directory or a link to another clone, move the old entry
outside the skills directory before reinstalling. Preserve any local edits you
want to keep.
Set `AGENTS_SKILLS_DIR` or `CLAUDE_SKILLS_DIR` to override either installation
directory.

## Uninstall

```sh
./scripts/uninstall
```

The uninstaller removes only links that point to skills in this clone. It does
not delete skill contents or unrelated installations.

## Editing skills

Each skill lives in `skills/<skill-name>/SKILL.md`. Any supporting scripts,
references, or assets stay in the same folder. I keep the shared instructions
compatible with all three tools wherever possible.

Set up the validation dependencies once:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
```

After editing, run:

```sh
.venv/bin/python scripts/validate
.venv/bin/python -m unittest discover -s tests -v
```

The validator parses YAML frontmatter and checks skill names and required
metadata. The tests cover validation and installation behavior in temporary
directories.

[Behavioral evaluations](evals/README.md) exercise the workflows in isolated
agent sessions. They assess outcomes and tool traces, not exact response wording.
Run relevant cases when changing workflow behavior and record live-agent results
separately from deterministic tooling CI.

## License

Licensed under the [Apache License 2.0](LICENSE), except for these MIT-licensed
adaptations:

- [`handoff`](skills/handoff/LICENSE)
- [`create-verification-skill`](skills/create-verification-skill/LICENSE)
- [`maintain-verification-skill`](skills/maintain-verification-skill/LICENSE)
