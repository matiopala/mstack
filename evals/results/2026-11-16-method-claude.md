# Method in Claude Code — 2026-11-16

Added Claude Code orchestration without changing Method's controller, state schema,
approval gates, candidate capture, verification criteria, or delivery semantics.
Both installed skill links resolve to the same source and use the same task store.

Claude's explicit-only `disable-model-invocation: true` field is in the shared
SKILL.md; Codex retains `allow_implicit_invocation: false` in agents/openai.yaml.
The coordinator stays in the main conversation. The new hosts reference specifies
a registration-only general-purpose subagent handshake: obtain a real returned
agent ID, register the run, then resume that agent with its role and exact workspace.
Verifier registration precedes work in the controller-created candidate checkout.
Conversation forks, extra host-managed worktrees, recursive delegation, and tool
permission bypasses are not part of the adapter. Restart across hosts requires
reconciling previous active work before launching a new actor.

## Verification

- All 45 repository tests passed, including a packaging regression checking both
  installed invocation policies and that both hosts share the controller source.
- All 26 skills passed repository metadata validation; JavaScript syntax and
  `git diff --check` passed.
- Codex's actual local app-server `skills/list` API loaded Method successfully with
  the Claude frontmatter extension. Retained probe and result:
  `/private/tmp/method_codex_loader_check.py` and
  `/private/tmp/method-codex-loader-result.json`. This was a discovery request, not
  a model execution. The sandboxed process could not start; the permitted local
  process completed the check without changing skill settings.
- Installed Method using `./scripts/install --harness claude method`; the result is
  `~/.claude/skills/method -> /Users/mati/Projects/mstack/skills/method`.
- Local Claude Code version was 2.1.319. Authentication status, checked outside the
  sandbox to avoid a credential-access false negative, reported `loggedIn: false`.
  No live Claude agent journey was attempted or claimed verified. Existing Codex
  behavioral trials remain documented separately; they are not Claude evidence.

The generic skill-creator quick validator rejects the Claude-specific frontmatter
extension because its allowlist lacks that field. It was not changed or bypassed.
Repository validation, the explicit-policy regression, official Claude documentation,
and actual Codex discovery establish the tested packaging compatibility. This does
not claim compatibility with generic skill-upload services that reject extensions.

## Interface sources

Checked against official documentation and the installed CLI:

- [Claude skill invocation controls](https://code.claude.com/docs/en/skills#control-who-invokes-a-skill)
- [Resuming Claude subagents](https://code.claude.com/docs/en/sub-agents#resume-subagents)
- [Fresh subagents and conversation forks](https://code.claude.com/docs/en/sub-agents#how-forks-differ-from-other-subagents)

No user Claude settings, authentication state, or permission rules were changed.
