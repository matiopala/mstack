---
name: deep-plan
description: Plan a software change when a consequential assumption may change the approach. Use for deeper planning or reconsidering an uncertain implementation choice.
---

Use [plan](../plan/SKILL.md) to establish the goal and verification scenarios first.
From the project root run:

```sh
python3 <skill-dir>/scripts/rounds.py start --brief TEXT --verification REF
```

Pass the original task, a verification path or inline scenarios, and any settled
`--constraint TEXT` or `--decision TEXT` (repeatable).

Sketch the smallest viable approach. Which assumption could change it? What
primary evidence could settle it? After each pass use the returned run and round:

```sh
python3 <skill-dir>/scripts/rounds.py advance RUN ROUND [--finding FACT SOURCE]...
```

Keep drafts separate. Add `--investigate QUESTION DECISION SOURCE`
when further investigation could change the plan. Otherwise finish now, using
`--unresolved QUESTION` for any outstanding uncertainty.

For `reconsider`, give only `handoff` to a fresh agent without conversation history.
Ask for sourced findings and an independent approach. If unavailable, use the
handoff locally and disclose the shared context. The main agent advances the run
and delivers one plan. Trace any new requirement to the brief or an accepted
decision. Surface unresolved decisions at the three-round limit.
