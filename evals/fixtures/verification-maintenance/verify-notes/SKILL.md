---
name: verify-notes
description: Verify Notes CLI creation, persistence, and case-insensitive search.
---

## Launch and health

Run from the project root with Python 3. No dependencies or long-lived processes.
Create a fresh `STATE=$(mktemp -d)` and a separate evidence directory beneath
`artifacts/` for each run. Record commands, stdout, stderr, exit codes, and
`notes.py`'s SHA-256 there.

Run `python3 notes.py --data-dir "$STATE" doctor` before driving and after
unexpected failures. Expect version `1.0`, the owned data directory, and a
count matching known state. Do not drive an unknown or shared data directory.

## Drive and evidence

Read [the feature index](features/README.md). Run its recipes through the CLI;
capture actions and results, including a fresh read of persisted state.

## Cleanup

Remove only the temporary state directory created for this run, including
after failures. Never remove the separate evidence directory. Check that its
artifacts still exist after cleanup.
