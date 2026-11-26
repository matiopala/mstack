---
name: walkthrough
description: Build an interactive, source-grounded HTML walkthrough when someone wants to understand an implemented change before merge or learn how a named feature works.
---

# Walkthrough

Produce one self-contained HTML file that a reader can open locally. Help them predict what the software will do when a relevant condition changes, explain why, and find the code responsible. Follow the project's exploration instructions. Use the supplied repository, revision and evidence.

## Choose the starting point

- `$walkthrough change <MR, branch, commit range, or working changes>`. Identify the actual base and proposed revision, including local edits when requested. Lead with the observable difference. Follow the same concrete input through both versions and mark the first decision where they diverge. Explain why it matters to the caller or user. For an intended behavior-preserving change, show what must stay equivalent and what moved internally.
- `$walkthrough feature <domain, capability, or question>`. Identify the revision being described. Start with a question a user or operator could ask. Introduce the domain terms, who owns the relevant state or decision, and how an ordinary case works. Let the reader follow a materially different case and identify where a future change to the rule would belong.

## Choose the surrounding context

Start at a real entry point and follow the result to an observable effect. Include an unchanged caller, store, worker, configuration value, or external contract when leaving it out would change the reader's prediction. Stop at a boundary whose internal implementation can vary without changing the answer. State any assumption about that boundary. A file's presence in the diff or proximity in the directory tree is a poor reason to include it on its own.

## Build the walkthrough

- On the first screen, answer the reader's main question in domain language and give them a concrete case to explore. Put implementation detail within reach of the decision it explains.
- Choose an interaction that teaches the behavior. A reader might vary one input and compare outcomes, advance through an event sequence, or select a state to see which actions it permits. Show the reason for the outcome. Use the smallest diagram or table that expresses the actual rules.
- Ground consequential claims in the relevant revision and path/symbol. Link to a stable source location or include a short identifiable excerpt. Attach a test, trace, or observed result when available. Distinguish intended behavior, code inspection, observed behavior, and open questions. A test that was read has a different evidentiary value from a test that ran.
- Prefer real fixtures or recorded observations for interactive cases. If you replay a trace or use a teaching model, say which it is and what it leaves open. Keep a material unknown visible where it affects the answer.
- Keep the HTML usable offline, including its controls and diagrams. Open it, exercise the main interaction, and check that the reader can get from a behavioral claim to its evidence. Return the file link with one specific case to try.

The [payment-retry example](payment-retries.html) demonstrates both entry points using an explicitly fictional, executable model.
