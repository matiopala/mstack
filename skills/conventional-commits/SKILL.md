---
name: conventional-commits
description: Prepare or create focused Git commits using a simplified Conventional Commits format. Use when asked to commit changes, prepare a commit message, or commit during a larger workflow.
license: Apache-2.0
---

# Conventional Commits

Format commit subjects as:

```text
<type>: <summary>
```

Use one of these types: `feat`, `fix`, `test`, `research`, `refactor`, `docs`,
or `chore`.

- Write the summary in lowercase imperative form with no trailing period.
- Keep each commit focused on one coherent change.
- Inspect the relevant diff to prepare the message. Do not run checks for a
  message-only request.
- Before committing, exclude unrelated changes. Reuse sufficient verification
  evidence for unchanged code; run relevant checks when evidence is missing,
  stale, or inadequate.
- Commit only when the user explicitly asks.

Examples:

```text
feat: add health check endpoint
fix: handle empty evaluation results
test: cover malformed requests
research: evaluate retrieval strategies
chore: configure pytest
```
