# Host orchestration

Both hosts use the same controller and saved artifacts. No alternate state machine,
approval policy, or task-store copy is needed. Use actual host agent identities;
never invent an ID to satisfy `run-start`. Prefix new actor records with `codex:`
or `claude:` to keep identities distinct when a task crosses hosts. Resume records
using the exact actor identity already saved, including older unprefixed identities.

## Codex

Invoke `$method`. `agents/openai.yaml` disables implicit invocation.

Create a fresh agent without inheriting conversation history. Its initial message
only establishes its role and asks it to wait; it must not perform task work yet.
Register the returned agent ID with `run-start`, then send the run ID, absolute
workspace, approved artifact references, role contract, and execution limits using
host messaging. Let the controller create a verifier checkout before supplying its
workspace. Use the host's returned process/agent handles to monitor and stop owned
work. Do not replace an unavailable independent agent with self-review.

## Claude Code

Invoke `/method` in the main conversation. The skill's
`disable-model-invocation: true` frontmatter prevents automatic activation. Do not
add `context: fork` to the coordinator, pre-approve all tools, or change the user's
Claude permission settings. Existing `CLAUDE.md`, applicable repository instructions,
and host permissions continue to apply.

Use the native Agent tool with an explicit fresh `general-purpose` subagent. Do not
use a conversation fork, Explore, or Plan as the implementation/verifier worker.
Do not create a second host-managed worktree: Method has already chosen the workspace.

The returned agent ID may arrive only after the first invocation finishes. Use a
registration-only handshake before either role performs work:

1. Launch a fresh general-purpose agent with a short instruction: "This is a
   Method role-registration handshake. Return READY without reading task artifacts,
   running commands, changing files, or spawning agents. Wait for a resumed task."
2. Read the actual agent ID returned by Claude. Call `run-start` as the coordinator
   with the role and `actor: claude:<returned-agent-id>`. Do not reuse an implementer
   identity for verification. If no resumable ID is returned, record a blocker.
3. Resume that exact agent through the Agent tool's resume capability. Supply the
   registered run ID, Method task/store paths, exact workspace, approved revisions,
   baseline/candidate, relevant role reference, execution limits, and absolute
   evidence-output locations. Tell it to run commands in the supplied workspace;
   do not assume the child inherits the verifier checkout as its working directory.
4. Receive its results and inspect actual files, Git state, and evidence. The
   coordinator alone imports evidence, finishes runs, captures candidates, and
   submits verification reports. A worker's completion message is not proof.

Follow the host's actual tool schema for resuming and collecting results; do not
invent parameter names. If background work is used, retain its returned handle and
inspect completion before checkpointing. Keep finite checks within the remaining
budget. The coordinator must stop native agent/tool work on exhaustion, since only
controller-owned commands enforce their process-group timeout directly.

Scoped repairs may resume the implementer. Every verification round gets a fresh
independent verifier, with artifact-only input. Worker prompts prohibit further
delegation, changes to Method records, requirement changes, commits, and delivery.
The verifier also cannot edit product code, tests, or helpers.

## Restart or change hosts

Read Method status before launching anything. A run recorded active is not proof
that its host agent is still working or has stopped. Reconcile the original host's
agent and owned commands before recording `run-finish` as interrupted. If another
host's live work cannot be inspected, leave the run unresolved and ask for the
missing process/agent confirmation; do not launch a competing writer.

After reconciliation, a new host can continue from saved artifacts under existing
valid task authorization and remaining limits. Preserve original actor identities,
decisions, and evidence. New role runs use the new host's actual agent IDs. Never
turn transcript cleanup or a lost agent handle into permission to reset task state.

Claude interface references: [skill invocation controls](https://code.claude.com/docs/en/skills#control-who-invokes-a-skill),
[subagent resumption](https://code.claude.com/docs/en/sub-agents#resume-subagents),
and [fresh subagents versus conversation forks](https://code.claude.com/docs/en/sub-agents#how-forks-differ-from-other-subagents).
