# Host orchestration

Both hosts use the same controller and task store. The coordinator alone calls the
controller to register runs, import evidence, capture candidates, and submit reports.
Use actual host agent IDs, prefixed with `codex:` or `claude:` for new records.
Preserve saved actor identities when resuming, including older unprefixed values.

Register each worker before it reads artifacts or starts task work. Then supply:
the run ID, Method task/store paths, repository instructions, absolute workspace,
approved artifact paths/hashes, baseline or candidate, existing findings, environment
instructions, role reference, execution limits, and absolute evidence-output paths.
Use the verifier workspace returned by the controller; do not create another worktree
or assume the worker inherits that directory.

Workers receive artifact-only context. Scoped repairs may resume the implementer;
each verification round needs a fresh agent that has never implemented this task.
If registration or independent agents are unavailable, record a blocker.
Worker prompts prohibit delegation, requirement or record changes, commits, and
delivery; verifiers also cannot edit product code, tests, or helpers.

Use actual host tool schemas and retain agent/process handles. Inspect completion,
files, Git state, and evidence before checkpointing. Stop native host work on budget
exhaustion; only controller-owned commands enforce their timeout automatically.

## Codex

Create a fresh agent without inheriting conversation history. Its initial message
only establishes its role and asks it to wait. Register the returned ID with
`run-start`, then send the worker brief above through host messaging.

## Claude Code

Keep the coordinator in the main conversation; do not add `context: fork`,
pre-approve tools, or change Claude permission settings. Existing `CLAUDE.md`,
repository instructions, and host permissions apply.

Use the native Agent tool with an explicit fresh `general-purpose` subagent. Do not
use a conversation fork, Explore, or Plan as the implementation/verifier worker.

The returned agent ID may arrive only after the first invocation finishes. Use a
registration-only handshake before either role performs work:

1. Launch a fresh general-purpose agent with a short instruction: "This is a
   Method role-registration handshake. Return READY without reading task artifacts,
   running commands, changing files, or spawning agents. Wait for a resumed task."
2. Register its returned ID with `run-start` and `actor: claude:<returned-agent-id>`.
   If no resumable ID is returned, record a blocker.
3. Resume that exact agent with the worker brief above. Require commands to run in
   the supplied workspace and follow the role reference's restrictions.

## Restart or change hosts

Read Method status before launching anything. A run recorded active is not proof
that its host agent is still working or has stopped. Reconcile the original host's
agent and owned commands before recording `run-finish` as interrupted. If another
host's live work cannot be inspected, leave the run unresolved and ask for the
missing process/agent confirmation; do not launch a competing writer.

After reconciliation, continue from saved artifacts under the existing authorization
and remaining limits. Preserve decisions and evidence; a lost agent handle or cleaned
transcript does not authorize resetting task state.

Claude interface references: [skill invocation controls](https://code.claude.com/docs/en/skills#control-who-invokes-a-skill),
[subagent resumption](https://code.claude.com/docs/en/sub-agents#resume-subagents),
and [fresh subagents versus conversation forks](https://code.claude.com/docs/en/sub-agents#how-forks-differ-from-other-subagents).
