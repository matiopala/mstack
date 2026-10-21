---
name: go-deeper
description: Rewrite a task prompt for greater depth without expanding scope. Use when the user asks for a deeper version of a task or prompt.
---

Make the user's task deeper, not bigger. Preserve its goal, scope, and
constraints.
Leave choices that belong to the user open instead of deciding them.

Before rewriting, briefly identify:
1. What a top professional in this field would do here that the prompt
   doesn't ask for.
2. The rawest relevant material they would start from, rather than
   summaries or interpretations.
3. The specific methods and tools they would use, and what each would
   establish.
4. What evidence or checks, independent of your or the user's judgment,
   would support or disprove the result.

Then rewrite the prompt to ask for exactly that. Make it concrete and
ready to use; flag unavailable inputs rather than inventing them.
Return the four observations and rewritten prompt. Do not execute it.
