---
name: quota-axi
description: >-
  Report local AI provider quota windows, remaining runway, reset times, and
  pace via the quota-axi CLI (read-only, no routing). Use before spending
  provider quota, when checking usage, rate limits, or pace, or when comparing
  local headroom.
user-invocable: false
author: Kun Chen (kunchenguid)
metadata:
  hermes:
    tags: [quota, rate-limits, pace, cli]
    category: observability
---
Skill version: 1.0.1

# quota-axi
Data-only local quota reporter for every AI provider signed in on this machine. Never routes, ranks, recommends, or mutates provider state. Use before deciding if spend is safe, on usage/rate-limit/pace questions, or comparing headroom. Run: `npx -y quota-axi` (default TOON), `--help` (commands/flags), `--json` / `--full` (shape/semantics).
