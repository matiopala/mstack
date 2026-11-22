#!/usr/bin/env python3
"""Build evidence-only handoffs for a bounded planning run."""

import argparse
import json
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path


MAX_ROUNDS = 3


def start(args):
    handoff = {
        "project": str(Path.cwd()),
        "brief": args.brief,
        "constraints": args.constraint,
        "decisions": args.decision,
        "verification": args.verification,
        "findings": [],
    }
    with tempfile.NamedTemporaryFile(prefix="deep-plan-", suffix=".sqlite3", delete=False) as tmp:
        run = tmp.name
    result = {"run": run, "round": 1, "action": "explore", "handoff": handoff}
    with closing(sqlite3.connect(run)) as db, db:
        db.execute("CREATE TABLE deep_plan (step INTEGER PRIMARY KEY, result TEXT NOT NULL)")
        db.execute("INSERT INTO deep_plan VALUES (0, ?)", (json.dumps(result),))
    return result


def advance(args):
    run_uri = Path(args.run).resolve().as_uri() + "?mode=rw"
    with closing(sqlite3.connect(run_uri, uri=True)) as db, db:
        previous = db.execute(
            "SELECT result FROM deep_plan WHERE step = ?", (args.round - 1,)
        ).fetchone()
        if previous is None:
            raise ValueError("the requested round has not started")
        result = json.loads(previous[0])
        if result["action"] in ("finish", "limit"):
            raise ValueError("this run has already finished")

        handoff = result["handoff"]
        handoff.pop("investigation", None)
        handoff["findings"].extend(
            {"fact": fact, "source": source} for fact, source in args.finding
        )
        result["action"] = "finish"
        if args.unresolved:
            handoff["unresolved"] = [{"question": question} for question in args.unresolved]
        if args.investigate:
            question, decision, source = args.investigate
            focus = {"question": question, "decision": decision, "source": source}
            if args.round == MAX_ROUNDS:
                result["action"] = "limit"
                handoff["unresolved"] = [focus]
            else:
                result["action"] = "reconsider"
                result["round"] += 1
                handoff["investigation"] = focus

        encoded = json.dumps(result)
        inserted = db.execute("INSERT OR IGNORE INTO deep_plan VALUES (?, ?)", (args.round, encoded))
        if not inserted.rowcount:
            saved = db.execute("SELECT result FROM deep_plan WHERE step = ?", (args.round,)).fetchone()
            if saved[0] != encoded:
                raise ValueError("this round already has a different submission")
            # Retrying an old submission must not send a worker back to a completed round.
            latest = db.execute("SELECT result FROM deep_plan ORDER BY step DESC LIMIT 1").fetchone()
            return json.loads(latest[0])
    return result


def nonempty(value):
    if not value.strip():
        raise argparse.ArgumentTypeError("expected nonempty text")
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    begin = commands.add_parser("start", help="begin round one in a private temporary run file")
    begin.add_argument("--brief", type=nonempty, required=True)
    begin.add_argument("--verification", type=nonempty, required=True)
    begin.add_argument("--constraint", action="append", type=nonempty, default=[])
    begin.add_argument("--decision", action="append", type=nonempty, default=[])

    step = commands.add_parser("advance", help="submit one round and print the next action")
    step.add_argument("run", help="run file returned by start")
    step.add_argument("round", type=int, choices=range(1, MAX_ROUNDS + 1))
    step.add_argument(
        "--finding", nargs=2, metavar=("FACT", "SOURCE"), action="append", type=nonempty, default=[]
    )
    outcome = step.add_mutually_exclusive_group()
    outcome.add_argument(
        "--investigate", nargs=3, metavar=("QUESTION", "DECISION", "SOURCE"),
        type=nonempty, help="request a further round",
    )
    outcome.add_argument(
        "--unresolved", metavar="QUESTION", action="append", type=nonempty,
        help="finish with an open question (repeatable)",
    )

    args = parser.parse_args()
    try:
        result = start(args) if args.command == "start" else advance(args)
    except (OSError, sqlite3.Error, ValueError) as error:
        parser.exit(1, f"{parser.prog}: {error}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
