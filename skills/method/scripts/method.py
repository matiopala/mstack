#!/usr/bin/env python3
"""Method CLI. Mutation payloads are JSON files, never shell-expanded text."""
import argparse
import json
import os
from pathlib import Path
import sys

from core import Error, Store


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", help="Override METHOD_HOME / ~/.local/share/method")
    parser.add_argument("command", choices=("start", "list", "status", "next", "submit", "decide", "import",
                        "authorize", "run-start", "run-finish", "command", "evidence", "candidate", "verify",
                        "accept", "delivery", "block", "pause", "resume", "resolve", "serve"))
    parser.add_argument("--task", help="Task ID; otherwise read current .tasks/locator.json")
    parser.add_argument("--input", help="JSON payload file; '-' reads stdin")
    parser.add_argument("--port", type=int, default=0, help="Dashboard port; default chooses a free port")
    args = parser.parse_args()
    try:
        store_path, task_id = args.store or os.environ.get("METHOD_HOME") or None, args.task
        locator = Path.cwd() / ".tasks" / "locator.json"
        if locator.is_file():
            saved = json.loads(locator.read_text())
            if not store_path or Path(store_path).expanduser().resolve() == Path(saved["store"]).expanduser().resolve():
                store_path = store_path or saved["store"]
                task_id = task_id or saved["task"]
        store = Store(store_path)
        data = json.loads(sys.stdin.read() if args.input == "-" else Path(args.input).read_text()) if args.input else {}
        if not isinstance(data, dict):
            raise Error("Payload must be a JSON object")
        if args.command == "serve":
            from server import serve
            serve(store, args.port)
            return 0
        if args.command == "start":
            result = store.start(data)
        elif args.command == "list":
            result = store.list()
        else:
            task = store.task(task_id)
            result = task.view() if args.command in ("status", "next") else task.apply(args.command, data)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (Error, OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
