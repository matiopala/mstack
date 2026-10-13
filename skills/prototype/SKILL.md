---
name: prototype
description: Build a lightweight prototype or exploratory implementation around a concrete goal. Use when the user wants to try an idea, demonstrate behavior, or answer a question through working code.
---

Focus on the user's goal and the quickest useful way to reach it. Reuse the
available context, code, and constraints. Ask only about missing details that
could materially change the result.

Build the smallest useful version, try it, and adjust based on what happens.
Keep choices simple and local. Stop when the goal is achieved or a concrete
blocker prevents further progress.

Choose checks that establish the requested outcome. A working demonstration
may be enough for a functional idea. If the goal is latency, measure it under
relevant conditions; if the goal is quality, define and check that quality.
Use tests when they help answer the question. Honor checks and constraints
explicitly required by the user or project.

Do not add a mandatory code-review loop, general hardening, a broader test
suite, formal planning artifacts, or decision records. Add rigor where the
goal needs it, and keep any shortcuts or mocked behavior visible when they
limit what the result demonstrates. A prototype request does not automatically
expand into production delivery.

Finish with the result, how to try it, what was demonstrated or measured,
and material limitations or remaining blockers. Distinguish observed results
from assumptions.
