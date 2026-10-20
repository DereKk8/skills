---
name: quota-axi
description: "Report the local quota windows of every AI provider signed in on this machine via the quota-axi CLI - remaining effective usable runway, percentages, reset times, cycle-average pace vs the reset clock, a per-scope selection signal, and provider status read from local auth sources, with no routing, provider mutation, or default ordering preference. Use before deciding whether it is safe to keep spending a provider's quota, when the user asks about usage, rate limits, pace, or remaining quota, or when comparing local provider headroom."
user-invocable: false
author: Kun Chen (kunchenguid)
metadata:
  hermes:
    tags: [quota, rate-limits, pace, cli]
    category: observability
---
Skill version: 1.0.0

# quota-axi
Data-only local quota reporter for every AI provider signed in on this machine. Never routes, ranks, recommends, or mutates provider state. Use before deciding if spend is safe, on usage/rate-limit/pace questions, or comparing headroom. Run: `npx -y quota-axi` (default TOON), `--help` (commands/flags), `--json` / `--full` (shape/semantics).
