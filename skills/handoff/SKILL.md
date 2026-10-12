---
name: handoff
description: Create a compact handoff document so another agent or session can continue the current work. Use when the user asks to transfer context or prepare a session handoff.
license: MIT
---

<!-- Adapted from Matt Pocock's handoff:
https://github.com/mattpocock/skills/blob/0f5e033ebc47b142f5ffa56a582ede6d9d9bada3/skills/productivity/handoff/SKILL.md
-->

Write one concise Markdown document that lets a fresh agent continue from
the current stopping point. Tailor it to the user's stated next-session focus.

Capture the goal, decisions not recorded elsewhere, current state, blockers,
and remaining work. Preserve constraints and user corrections that matter
to continuation. For code work, include the relevant repository or worktree,
branch, and uncommitted changes.

Distinguish verified results from unverified work and assumptions. Cite the
checks and outcomes already observed; label missing evidence explicitly.

Reference existing specs, plans, ADRs, task records, commits, and diffs by
resolvable path or URL instead of copying their contents. Retain only the
conversation context needed to connect those artifacts and resume the work.

Suggest available skills when they would help the next agent. End the document
with the exact first action to take, including its target and purpose.

Redact secrets and unnecessary personal information.

Save to the user's requested destination. Otherwise, use a unique, descriptive
Markdown filename in the OS temporary directory (`$TMPDIR`, falling back to
`/tmp`; `%TEMP%` on Windows). Return the full file path and a short instruction
the user can give the next agent to read it and continue.
