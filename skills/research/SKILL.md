---
name: research
description: Investigate a software question or change through focused codebase research. Use when the user wants findings, constraints, regression risks, and evidence before deciding how to proceed.
---

<!-- Extracted from deliver; workflow inspired by HumanLayer:
https://github.com/humanlayer/humanlayer/tree/main/.claude/commands
Flow tracing also draws on pstack's how:
https://github.com/cursor/plugins/blob/main/pstack/skills/how/SKILL.md
-->

## Establish the question

Read the question, intended outcome, scope, and available requirements. When
given a task record, read its brief, status, and relevant linked context.
Reuse findings from earlier discussion and investigation.

Ask one consequential question at a time when needed to focus the research.
Investigate available context before asking for facts inspection could establish.

Use the [adr](../adr/SKILL.md) skill to consult relevant accepted decisions
and capture consequential choices that emerge during clarification.

## Investigate

Trace affected behavior, dependencies, boundaries, existing patterns, and
tests around specific questions. Verify assumptions against current code.

For behavior questions, follow a concrete example from its entry point through
validation, component boundaries, and state ownership to the observable result.
Include relevant failure paths and source references. Scale the trace to the
question; a list of related files alone does not explain the behavior.

Use parallel research for independent questions when useful and available.
Give each investigation a bounded question and reconcile its findings.

Identify regression risks and how the desired outcome can be demonstrated.
Return to the user when a discovery changes a consequential requirement or
tradeoff, honoring decisions and authorization already given.

## Hand off the findings

Report concise answers with code references, relevant constraints, regression
risks, verification options, and remaining uncertainties. Distinguish observed
facts from assumptions and recommendations.

Record the relevant revision and any uncommitted changes that affect the
findings. When reusing research, recheck the affected code for changes.

When using a task record, add relevant findings there without replacing its
brief, acceptance criteria, progress, or evidence. Otherwise, follow the
user's requested output format and project conventions; a task record is optional.

Continue to planning or implementation only when covered by the user's request.
