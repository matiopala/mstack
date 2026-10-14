---
name: adr
description: Create and maintain decision records for consequential product, architecture, and implementation choices. Use when asked to document decisions or when a development workflow calls for durable decision capture.
---

Preserve what was chosen, why, and what remains open so later work can reuse
the decision without reconstructing the conversation.

## Select what deserves a record

Read the repository's decision conventions, index, and relevant records.
Follow amendment and supersession links to establish the current accepted
direction. Reuse existing records rather than duplicating a decision.

Create an ADR when explicitly requested, required by project conventions, or
when a consequential product or technical decision needs broader reuse or
independent revision history. Keep feature-specific rationale in its existing
authoritative specification or task record when that is sufficient; reuse in
a later session alone does not warrant a separate ADR. Keep routine coding
choices, requirements, and task progress in their existing artifacts.

Give each record one independently reconsiderable decision. Do not settle
unrelated future questions to complete it; record those uncertainties without
making them prerequisites for current work.

## Capture with the authority already given

Capture qualifying decisions as they emerge during the workflow, without
waiting for a separate documentation request. Before handoff, check for
significant decisions left only in conversation. Honor requests to discuss
only or avoid file edits.

- **Accepted:** An explicit user decision or approval, including an existing
  documented approval. Recording it requires no repeated confirmation.
- **Proposed:** An agent recommendation, inferred choice, or decision whose
  acceptance is unclear. Do not present it as settled.

Accepted describes agreement, not implementation or verification. Recording
a decision does not authorize implementation, change agreed task scope or
acceptance criteria, or create follow-up tasks.

## Write the record

Follow the user's requested destination and repository conventions. Otherwise,
use `docs/adr/NNNN-short-title.md` with the next available sequential number
and maintain `docs/adr/README.md` as an index of titles, links, and statuses.

Keep each record concise and understandable outside its originating session:

- Title, status, and date.
- Context: the problem and constraints that required a choice.
- Decision or proposal: what is chosen and its scope.
- Rationale: why it fits, actual alternatives considered, and available evidence.
- Consequences: benefits, costs, and important limitations.
- Open questions that remain, where relevant.
- Links to the originating specification, task, discussion, or evidence when
  available, and to related decisions.

Do not invent rationale, alternatives, approval, or source links. Distinguish
observations from assumptions and leave missing evidence explicit.

Specifications own the current intended state and local rationale; task records
own planned work, progress, delivery evidence, and decisions local to the task.
ADRs own separately recorded decisions and their history. Link between them.
Update only summaries affected by a decision change rather than copying the
same explanation into every document.

## Preserve decision history

Revise proposals in place. Mark declined proposals Rejected or use the
repository's equivalent status.

For a substantive change to an accepted decision, add a linked record and
preserve the earlier reasoning. A proposed replacement leaves the accepted
direction in force until the replacement is accepted.

- An accepted full replacement marks the old record **Superseded** and links
  both ways.
- An accepted scoped amendment leaves the still-valid record **Accepted**,
  with links identifying exactly what the later decision changes.
- Corrections or clarifications that do not change meaning can be made in
  place; do not silently rewrite an accepted decision's substance.

Keep the index and directly affected artifact links current. At handoff,
identify created or changed records and their status. If no decision warrants
an ADR, continue without creating one.
