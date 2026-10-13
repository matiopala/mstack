# Verification skills — 2026-10-13

The four new [behavioral cases](../README.md#create-reusable-verification)
are **unverified**. Fresh-agent execution was blocked by the local harness's
credential-store permissions. Metadata, installer, and fixture checks passed;
these are not substitutes for observing an agent apply the skills.

## Tested state

Source base: `8cf2f26`, plus the new verification skills, discovery hooks,
documentation, fixtures, and tooling-test changes in this working tree.

| Skill | SHA-256 of SKILL.md |
| --- | --- |
| create-verification-skill | `224427f2b4e149c6051a7be76353fe8754d6ecd1ef80358a66c053ac75cd5b86` |
| maintain-verification-skill | `c834d07d110cd6ac6106e743ee2413682530636b7d755e742aeae3fc26cdc7af` |
| research | `c69be6a60e6166d8477ca118b2dfb425ce361040f28b1ab7d281a4b97a2ee33c` |
| plan | `dbb2475f1fba7083b3079b687bda53122d599a12fe702a379d463ae85aa73dd6` |
| implement | `a797065e0167c74ae9e7a8bff11148a5ffc20cf7b0adee4f2c30fcdeb302df68` |

## Deterministic checks

- `.venv/bin/python scripts/validate`: all 21 collection skills passed.
- `.venv/bin/python -m unittest discover -s tests -v`: all 14 tests passed.
  Expanded subtests cover independent installation of both new skills for
  Codex, Pi, and Claude, and unchanged companion sets for `research`, `plan`,
  `implement`, and `deliver`. No installer implementation change was needed.
- `git diff --check`: passed. Collection documentation links and the fixture
  skill's frontmatter passed direct checks; both license copies match upstream.

## Direct fixture checks

Ran 18 CLI commands in temporary copies, not the source fixture:

- Version and doctor reported Notes 1.0 and the owned state path.
- Doctor, list, and search did not create an absent state directory.
- Add persisted `Quarterly plan`; a fresh list process returned it with ID 1.
- Healthy search for `quarterly` found it; `volcano` returned `[]`.
- The stale `--text` flag exited 2 without adding a note; `--title` worked.
- In the deliberately regressed copy, `quarterly` returned `[]` while
  `Quarterly` found the note. The fixture therefore exposes a product defect
  distinct from the stale recipe. The dead export index entry has no file.
- Owned scratch state was removed and captured command/result evidence survived.

The first check attempt compared the macOS `/tmp` alias with the canonical
`/private/tmp` path reported by doctor and stopped on that assertion. Corrected
only the check's path comparison; the fixture required no change.

Command arguments, exit codes, stdout, and stderr are retained locally at:

`/private/tmp/skills-verification-checks.VHhq1w/evidence/fixture-checks.json`

This temporary artifact may eventually disappear. The fixture and behavioral
case setup remain in the repository for reproduction. These commands establish
fixture behavior, not the quality of agent-generated verification instructions.

## Fresh-agent blocker and remaining proof

A no-tools Pi availability probe requested provider `openai-codex`, model
`gpt-6-astra`, with extensions, MCP, skill discovery, project context, session
saving, and startup networking disabled. It exited 1 before a model response:

```text
Credential store read failed for openai-codex: EPERM: operation not permitted,
mkdir '/Users/mati/.pi/agent/auth.json.lock'
```

No credentials were copied or permissions changed to bypass the restriction.
No behavioral case or delegated review ran. Self-review clarified that index
repairs respect a requested subset and corrected the fixture README's JSON
claim to exempt `--version`. No material source issue remains identified,
but live behavior is still unverified.

Rerun all four cases in fresh sessions with working harness credentials and
record the tool traces and outcomes. In particular, generated-recipe replay,
honest draft reporting, regression-versus-drift triage, and scoped-audit claims
still require live-agent evidence. Cross-harness behavior and shared/server
instance cleanup were not exercised by these checks.
