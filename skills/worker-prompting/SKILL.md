---
name: worker-prompting
description: >-
  Agent-only authoring policy for the instructions a dispatched worker acts on.
  Use before writing a worker's brief or task prompt, a standing charter, or a steer to a running worker.
user-invocable: false
metadata:
  internal: true
---
Skill version: 1.1.0

When you write a worker's brief, charter, or steer, give it:

- the outcome and why it matters
- done as evidence it can show
- what it cannot find, trust, or know to look for
- the scope, and the irreversible or shared actions that need a stop
- the facts you have, with any theory labeled a hypothesis

Keep the user's ask in the user's words, with must kept apart from prefer. Resolve every "that report" into its name, because the worker never saw this conversation. Invent no implementation, tests, workflow, or follow-up work, because an invented detail gets built. In a steer, say what changed and what still holds. On an ambiguous request, ask the worker to restate the goal in its first status line. Match the detail to the worker model's reasoning class: the outcome and its limits for a strong model, and an explicit spec with named files and symbols, acceptance checks, edge cases, non-goals, and real verification steps for a weaker one.
