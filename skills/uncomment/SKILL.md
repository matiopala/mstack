---
name: uncomment
description: Remove redundant code comments and private docstrings when asked to clean up a diff or selected files. Preserve documentation and directives that people or tools rely on.
license: MIT
---

# Uncomment

Use the requested files or change. With no target, review comments and docstrings added or edited in the current change, including pending edits. If there is no identifiable change, ask for a target. A review-only request returns candidates and reasons. For cleanup, edit the clear cases.

- Remove prose that merely translates the next line, repeats a name or signature, narrates the editing session, or preserves obsolete commented-out code. If a note conflicts with the implementation, check which reflects the intended behavior before deleting it.
- Keep information a maintainer would otherwise have to rediscover, such as why a particular ordering is required or which vendor behavior forces an exception. Preserve license notices, tool directives, generated-file markers, and the reasons for intentional suppressions. A constraint that only exists in prose deserves investigation.
- Review docstrings by audience and use. A private helper whose docstring only echoes its name is a candidate. Public contracts, units, side effects, error semantics, and executable examples carry information. Check decorators, registrations, docs configuration, and project conventions for indirect consumers such as CLI help, tool descriptions, or generated schemas. When consumption is unclear, keep the docstring and say why.

Keep edits scoped to the prose. Leave a separate suggestion when clearer code or an enforceable invariant would solve the underlying problem. Inspect the diff and run checks that exercise the affected surface. For doctests, confirm the relevant examples still run; for generated help or schemas, compare the output when it could change. Report any consequential keep or unresolved discrepancy.
