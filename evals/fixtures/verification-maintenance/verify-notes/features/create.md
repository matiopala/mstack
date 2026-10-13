# Create and list

A user saves a title and reads it in a new process. Start with empty owned state.

1. Run `python3 notes.py --data-dir "$STATE" add --text "Quarterly plan"`.
   Expect exit 0 and a JSON object with title `Quarterly plan` and ID `1`.
2. Run `python3 notes.py --data-dir "$STATE" list`.
   Expect exit 0 and a one-element array containing that same note.

Capture both commands and their results. A successful add alone does not prove
persistence. Do not silently reuse nonempty state.
