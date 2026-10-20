---
name: handoff
description: Compact the current conversation into a handoff document for another agent to pick up.
argument-hint: "What will the next session be used for?"
disable-model-invocation: true
---
Skill version: 1.0.0

When I invoke /handoff, write a document in the OS temp directory, never the workspace, that lets a fresh agent with no context pick up this work for the purpose I name. It states:

- where things stand, and why
- what was ruled out
- the exact next step
- what you verified, apart from what you assume

Link existing artifacts instead of copying them, and leave out any secret.
