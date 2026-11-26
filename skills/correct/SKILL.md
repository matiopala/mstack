---
name: correct
description: Turn an explicit engineering correction or a demonstrated pattern of recurring agent mistakes into a scoped repository fix with reproducible enforcement.
license: MIT
---

# Correct

Start with the supplied correction, diff, or review example. For a requested audit, group concrete incidents from accessible reviews, reverts, or fixes and cite the occurrences that establish recurrence. Distinguish a specific bug, a repository-wide rule, and a preference that depends on context. An explicit project rule can warrant enforcement on its first violation.

State the rule in terms of a known bad case and a nearby legitimate case. Check what already enforces it and how the bad case got through. Choose a remedy proportionate to the mistake:

- If duplicate ownership or an exposed internal operation invites the error, consider eliminating that choice. Use an existing type or API boundary when it can express the rule cleanly.
- For a mechanically recognizable code pattern, prefer configuring the existing linter. Scope it to the files or symbols where the rule holds. A diagnostic should tell the contributor what to use or change. If existing violations are outside the task, use the project's baseline mechanism when appropriate.
- For an incorrect observable outcome, exercise the behavior through its normal entry point. If a correction requires human judgment, capture the specific decision where maintainers need it. A single situational preference is insufficient evidence for a general prohibition.

For an implementation request, fix the in-scope instance and integrate the chosen enforcement into the project's normal check path. For advice or an audit, explain the remedy and its tradeoffs at the requested scope.

Prove executable enforcement against the actual offending change or a faithful minimal reproduction in isolation. Record the command and intended failure, then run that same command on the correction and check the legitimate case still passes. If past code or CI execution is unavailable, identify what was reproduced locally and what remains unverified. Report the incident, the enforcement point, and the evidence. Record a rule in project guidance only when it adds information beyond the check.
