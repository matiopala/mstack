"""Tiny persistent CLI used by the verification-skill evaluations."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", action="version", version="notes 1.0")
    parser.add_argument("--data-dir", required=True, type=Path)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor")
    add = commands.add_parser("add")
    add.add_argument("--title", required=True)
    commands.add_parser("list")
    search = commands.add_parser("search")
    search.add_argument("query")
    args = parser.parse_args()

    path = args.data_dir / "notes.json"
    notes = json.loads(path.read_text()) if path.exists() else []

    if args.command == "doctor":
        result = {"version": "1.0", "data_dir": str(args.data_dir.resolve()),
                  "count": len(notes)}
    elif args.command == "add":
        result = {"id": len(notes) + 1, "title": args.title}
        notes.append(result)
        args.data_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(notes) + "\n")
    elif args.command == "list":
        result = notes
    else:
        query = args.query
        result = [note for note in notes
                  if query.casefold() in note["title"].casefold()]

    print(json.dumps(result))


if __name__ == "__main__":
    main()
