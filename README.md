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
| [`conventional-commits`](skills/conventional-commits/SKILL.md) | Prepare focused Git commits with clear Conventional Commit messages. |
| [`decompose`](skills/decompose/SKILL.md) | Split a bigger design into reviewable tasks with clear acceptance criteria and proof of completion. |
| [`deliver`](skills/deliver/SKILL.md) | Work through questions, research, planning, and implementation, then collect irrefutable proof of delivery. |
| [`design-review`](skills/design-review/SKILL.md) | Challenge a proposed solution and get concrete findings in plain language. |
| [`grill-me`](skills/grill-me/SKILL.md) | Get interviewed about an idea, surface assumptions, and clarify what I actually want. |
| [`implement`](skills/implement/SKILL.md) | Implement a defined change and prove it meets acceptance and regression checks. |
| [`plan`](skills/plan/SKILL.md) | Define the approach, acceptance checks, and irrefutable proof for a software change. |
| [`product-spec`](skills/product-spec/SKILL.md) | Define the user problem, desired outcome, and what success looks like. |
| [`research`](skills/research/SKILL.md) | Investigate specific software questions and identify constraints, regression risks, and verification options. |
| [`show-me`](skills/show-me/SKILL.md) | Get a focused visual explanation. |
| [`tech-spec`](skills/tech-spec/SKILL.md) | Describe how a feature should work technically and how to prove it works. |

`deliver` ties together `grill-me`, `research`, `plan`, and `implement`.
I can also use each stage on its own. `implement` includes verification,
and the stages reuse the same task record when there is one. `deliver` also
uses `design-review` and `blast-radius` when the change warrants them.

## Credits

- `blast-radius` is adapted from
  [pstack's blast-radius](https://github.com/cursor/plugins/blob/main/pstack/skills/blast-radius/SKILL.md).
- `bro` is adapted from [backnotprop/bro](https://github.com/backnotprop/bro).
- `grill-me` is adapted from [Matt Pocock's skills](https://github.com/mattpocock/skills).
- `show-me` is inspired by [HumanLayer's show-me](https://github.com/humanlayer/skills/tree/main/plugins/show-me).
- `deliver` and its extracted `research`, `plan`, and `implement` stages draw on
  [HumanLayer's research-plan-implement workflow](https://github.com/humanlayer/humanlayer/tree/main/.claude/commands).
  The interview stage uses `grill-me`. Flow tracing, debugging, and verification
  also borrow from [pstack](https://github.com/cursor/plugins/tree/main/pstack).
- `design-review` adapts the review approach from
  [pstack's interrogate](https://github.com/cursor/plugins/blob/main/pstack/skills/interrogate/SKILL.md).

## Install

Clone the repository, then run:

```sh
./scripts/install
```

By default, this creates symbolic links for every skill in:

- `~/.agents/skills` for Codex and Pi
- `~/.claude/skills` for Claude Code

The links point to this clone, so edits and pulls update the installed skill
files too.

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
It also includes `design-review`, `blast-radius`, and their `bro` companion.
These stages, along with `product-spec`, `tech-spec`, and `decompose`, use `adr`
to record important decisions, so the installer includes it too. For `grill-me`,
decision capture only applies to software interviews in a repository.

`blast-radius` and `design-review` use `bro` to explain findings in plain language.
The installer includes `bro` when selecting these skills.
If you copy skill folders manually, include their companions too.

The installer refuses to replace existing files or links that point elsewhere.
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

After editing, run:

```sh
./scripts/validate
```

This checks skill names and required metadata.

## License

Licensed under the [Apache License 2.0](LICENSE).
