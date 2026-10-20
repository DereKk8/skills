---
name: linear-graphql
description: Operate Linear through its GraphQL API using Agent Vault access, verified reads and mutations, and polished, bloat-free UI presentation patterns. Use for Linear issues, projects, milestones, project updates, documents, workflow states, native GitHub PR links, schema discovery, API error handling, and crafting clean, aesthetic Linear pages. Owns reusable API mechanics and presentation standards, not a board's planning or reporting policy.
---
Skill version: 3.0.1

# Linear GraphQL
Direct GraphQL is primary; MCP only as fallback when API cannot do it and an authorized connection exists. Never require or reinstall an MCP server for it. Owns transport + presentation mechanics, not board policy. Refs: `references/access.md` (Agent Vault access through `secrets`, redirect/zero-leak rules, stdlib template), `references/operations.md` (bounded queries, issues/relations/PR links/updates/milestones/docs/comments), `references/presentation.md` (native UI mapping, `+++` drawers, archetypes).

## Before a Request
1. A board's IDs, scope, and templates belong to that board's own skill, not here.
2. Review access.md and follow the `secrets` profile route. Never fetch or expose a real key to chat, output, arguments, reports, or workers.
3. Review presentation.md. Map metadata to native fields (state, priority, milestone, dates, estimate, deps, PRs), never into Markdown text.
4. Consult operations.md before writing queries; narrow live introspection for unknown fields, never guess from MCP names.

## Execution
Stdlib only (`urllib.request`, `json`); variables separate from query string. Bound every connection (`first: <limit>` + `after: $cursor`; 10K complexity ceiling, unbounded = HTTP 400). Verify mutations (`success === true` + independent read-back of object/fields). Label diffs via `addedLabelIds`/`removedLabelIds`. On timeout: read target first to reconcile before retrying creates. URL canonicalization (`[URL](<URL>)`) is cosmetic, compare semantics.

## Presentation
No `**Status:**`/`**Priority:**`/`**Milestone:**` text - set `stateId`/`priority`/`projectMilestoneId`. Deps via `issueRelationCreate(blocks|duplicate|related)`. PRs via `attachmentLinkGitHubPR`. Progress via `projectUpdateCreate`, never appended to overview `content`. Verbose output in `+++ Title / Content / +++` drawers or `commentCreate`. Human dates (`Sep 6th, 2026`), never `today`; no `<linear-date>` tags in API bodies.

Grow from use: update the touched reference file with exact op/inputs/verification/source/date; live-tested vs docs-only labeled; no creds/payloads/private IDs in skill files. Follow global-skill-sync for updates.
