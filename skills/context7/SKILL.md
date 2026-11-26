---
name: context7
description: >-
  Fetch current docs, API references, and examples via Context7 for any library,
  framework, SDK, CLI tool, or cloud service. Use for API syntax, config
  options, migrations, setup, or library debugging - even for well-known tools -
  instead of memory or web search.
---
Skill version: 2.0.1

# Documentation Lookup
Current docs via Context7 CLI. Prefer the installed `ctx7` command. If it is
unavailable, use `npx -y ctx7@latest` inside the Agent Vault session selected by
the `secrets` skill. Never install it globally or run it outside that session to
bypass brokered access.

Two-step: resolve name to ID first, then query docs. Max 3 CLI calls per question; use best result after that.
Skip it for refactoring, from-scratch scripts, business-logic debugging, code review, and general concepts. If a sandbox blocks DNS or fetch, retry outside the sandbox.

## 1 - Resolve Library
`ctx7 library React "How to clean up useEffect with async operations"`
Use official punctuation ("Next.js" not "nextjs"); retry alternate spellings before changing query. Query arg is required and drives ranking; phrase from user intent, never include secrets (keys, passwords, personal data, proprietary code).

Result fields: Library ID (`/org/project`), Name, Description, Snippet count, Reputation (High/Med/Low/Unknown), Benchmark Score (100 max), Versions (use `/org/project/version` when user names one).
Pick by: name similarity, description relevance, snippet coverage, reputation, score. Acknowledge ties, proceed with best; no good match = say so + suggest refinements; ambiguous = clarify before guessing.

## 2 - Query Docs
`ctx7 docs /facebook/react "How to clean up useEffect with async operations"`
One topic per query (split "routing and auth and caching" unless asking how they interact). Good: `"How to set up authentication with JWT in Express.js"`. Bad: `"auth"`, `"hooks"`, multi-topic blobs. Describe what to look up, not the task. Output: code snippets (titled, language-tagged) + info snippets (prose with breadcrumbs).

Mistakes: IDs need `/` prefix (`/facebook/react`); `docs react "hooks"` without ID fails; single-word queries return generic results; never put secrets in queries.

Auth: follow the `secrets` skill for startup and inherited sessions. If a
Context7 request fails authentication, report the profile and service to the
startup caller for a readiness check. Do not
export a raw key or use CLI login to bypass Agent Vault. For a quota error
("Monthly quota reached"), tell the user and answer from training data only if
the user accepts an answer that may be outdated.
