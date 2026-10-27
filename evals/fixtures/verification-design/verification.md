# Notes verification plan

Requirements source: the Notes README's Behavior section. The application must
preserve these behaviors through implementation and recipe changes.

## Required scenarios

| ID | Starting conditions and action | Required outcome | Evidence |
| --- | --- | --- | --- |
| V01 | In isolated empty state, add a note titled `Quarterly Plan`, then list from a new process. | The saved note retains its assigned ID and exact title. | Add response and fresh-process list output showing the same note. |
| V02 | Add `Second note` after V01, then list from a new process. | Both notes appear in insertion order with distinct IDs. | The two add responses and ordered list output. |
| V03 | With those notes saved, search for `quarterly`, then a substring that matches neither title. | The first search finds `Quarterly Plan` regardless of case; the miss returns an empty list. Neither search changes saved notes. | Search outputs and a fresh list before and after search. |
| V04 | Attempt add with the obsolete `--text` flag. | The command rejects the flag and leaves existing notes unchanged. | Nonzero exit, error output, and fresh lists before and after the attempt. |

## Execution references and limits

The README documents the CLI entry points and disposable data directory.
Recipes may adapt setup and commands while preserving these outcomes. Keep
run-specific evidence under a separate artifacts directory. These scenarios
do not establish concurrency safety, crash recovery, or behavior under disk errors.
