---
name: grill-me
description: Conduct an in-depth interview about a topic, task, idea, or decision to surface assumptions and reach shared understanding. Use when the user asks to be interviewed, grilled, or challenged through questions.
---

<!-- Adapted from Matt Pocock's original grill-me skill:
https://github.com/mattpocock/skills/blob/a6bdfd9fed6c17d21b306aeb7ff6a0de8b72ef3c/grill-me/SKILL.md
-->

Interview the user until you share a clear understanding of the requested
topic, plan, or decision. Examine assumptions and work through consequential
choices in dependency order, resolving foundational questions before the
choices that depend on them.

Ask one focused question at a time, give your recommended answer with a brief
rationale, and wait for the user's response before choosing the next question.

Investigate available context, files, code, and other accessible sources before
asking for facts you can establish yourself. Reuse settled decisions; revisit
them only when new evidence changes their implications.

Challenge vague answers, contradictions, and unsupported assumptions
respectfully. Keep questions focused on gaps that matter to the requested scope.

## Completion and handoff

Finish when the goal, scope, relevant constraints, and consequential decisions
within that scope are clear. Do not extend the interview into unrelated or
later decisions. If the user chooses to stop, close with the remaining gaps
explicit.

Summarize the shared understanding, decisions, and remaining uncertainties.

- **Standalone interview:** Return the summary. Continue with further work only
  when covered by the user's request or existing authorization; an interview-only
  request ends with the summary.
- **Within `deliver`:** Use its interview completion criteria. Once satisfied,
  carry the summary into the next authorized stage without asking for renewed
  approval. If existing context already satisfies those criteria, proceed
  without additional questions. Honor a request to stop instead of advancing.

Keep findings in the conversation unless the requested output or calling
workflow requires a record. Create ADRs only when the user explicitly requests
decision records; an interview or delivery request alone does not request ADR
capture during this stage.
