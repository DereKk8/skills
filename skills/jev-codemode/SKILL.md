---
name: jev-codemode
description: >-
  Use when one code-mode script must classify or label more than about 20
  records into named buckets and a cheap model saves real cost or context.
  Skip for fewer records or when plain filtering works.
---
Skill version: 2.0.0

Call Typesafe's `jev-latest` through the Agent Vault profile selected by the `secrets`
skill. The broker injects a placeholder for Typesafe; never fetch
`TYPESAFE_API_KEY` directly, print it, log it, persist it, pass it as an
argument, or include it in the records sent to Jev. If readiness fails, stop
using Jev through alternate credential paths. Since Jev is optional, continue
with the skill's plain filtering method when that method fits the task.

Send Jev only the fields it needs. Treat its answers as evidence to check when
they are uncertain or high stakes, never as approval for a merge, push, or
deploy.
