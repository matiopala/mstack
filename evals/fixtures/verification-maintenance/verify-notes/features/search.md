# Search

A user searches titles case-insensitively and sees an empty array for no matches.

Prerequisite: owned state contains exactly one note titled `Quarterly plan`.
If needed, seed it through the CLI's documented add command.

1. Run `python3 notes.py --data-dir "$STATE" search quarterly`.
   Expect exit 0 and a one-element array containing `Quarterly plan`.
2. Run `python3 notes.py --data-dir "$STATE" search volcano`.
   Expect exit 0 and `[]`.

Capture commands and results. Preserve the case-insensitive expectation even
if the current application returns a different result.
