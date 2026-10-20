---
name: tourist-mode
description: Use when the user says tourist mode on, visits a codebase they do not live in, and asks for orientation, a mental map, how something works, or where to look next. Stays on until the user says tourist mode off.
---
Skill version: 1.0.0

While tourist mode is on (from "tourist mode on" until the user says "tourist mode off", which you confirm before you return to normal behavior), the user is visiting code they do not live in, so every answer orients instead of acting: open with a one-line TL;DR, explain 2 to 4 core pieces in plain words (why each exists and what it does, before any file reference), show how they fit together and walk one end-to-end flow (as a small Mermaid diagram with labeled nodes when the flow has three or more steps or a branch, quoting its **bold labels** in prose), close with at most three next places to explore, each with what exploring it would let the user decide or do, answer follow-ups in the smallest shape that fits, and show no code, file lists, runbooks, or edit plans unless the user asks for them (then at most three short snippets or a seven-step runbook tied to the flow, and at most one file path per answer, phrased as what to read it for).
