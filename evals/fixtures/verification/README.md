# Notes

A Python 3 standard-library CLI. No installation, network, or authentication
is needed. Run from this directory. Application commands print JSON;
`--version` prints plain text. Success exits 0; argparse errors exit 2.

```sh
python3 notes.py --version
python3 notes.py --data-dir /path/to/disposable-state doctor
python3 notes.py --data-dir /path/to/disposable-state add --title "Quarterly plan"
python3 notes.py --data-dir /path/to/disposable-state list
python3 notes.py --data-dir /path/to/disposable-state search quarterly
```

Each invocation is short-lived; there is no server. The explicit data directory
is mandatory. An absent directory represents an empty collection; adding the
first note creates it. `doctor`, `list`, and `search` are read-only.

## Behavior

- Add persists the exact title and assigns an ID.
- List returns every saved note in insertion order, including in a new process.
- Search matches title substrings case-insensitively. A miss returns `[]`.
- The add flag was intentionally renamed from `--text` to `--title`.
  `--text` is no longer supported. No search behavior change was approved.

## Project conventions

This project uses Claude Code project skills in `.claude/skills/`. Keep
verification skills there. Use disposable state for verification and save
evidence under a separate `artifacts/` directory. Never use personal data.
