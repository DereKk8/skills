---
name: secrets
description: >
  Use for Agent Vault profile selection, startup, inherited API connections, or
  secrets for GitHub, Notion, Context7, Linear, Typesafe, Cloudflare, and other
  configured HTTP services. Routes general builders and project builders and
  testers through Agent Vault without exposing credential values.
---
Skill version: 4.0.1

# Secrets

Keep outbound HTTP API credentials inside Agent Vault. `agent-access` starts the selected profile and proxies requests with placeholder keys; public profile settings live in `~/.config/agent-access/config.json` and the full startup/readiness contract lives in `~/configs/docs/agent-access.md`.

## Profile selection and startup
- **General-purpose builders:** use `coding` (default readiness checks only; `--services` is not supported on `coding`).
- **Project builders and testers:** read `~/configs/docs/agent-access.md` for the project's profile. Pass `--services <svc>` to check only required services (limits readiness checks, not permissions).
- **New session:** run `agent-access doctor <profile>`, then `agent-access run <profile> -- <command>`.
  ```sh
  agent-access doctor coding && agent-access run coding -- gh-axi api user
  agent-access doctor --services notion <project-profile> && agent-access run --services notion <project-profile> -- notion-axi whoami
  ```
- **Inherited session:** when `AGENT_ACCESS_PROFILE` is already set, invoke the target tool directly in the inherited proxy, certificate, and placeholder environment. Do not run `doctor`, retrieve startup credentials, or start another session. Stop if the public profile lacks a required service or marks it pending.

## Missing keys, failures, and new services
- Stop when `doctor` fails, exits 78, names a missing key, or marks a service pending its authenticated smoke test. Never fetch a raw key directly, alter readiness results, switch credential paths, or claim an unconfigured project profile exists.
- Check a verify skill's `secrets.json` with `agent-access doctor <profile> --needs <file>`. Request missing keys once via `agent-access request <profile> --needs <file> --task <issue URL>` (or `--key`, `--host`, `--description`, `--obtain` for an undeclared key; posts to Discord once), then stop the work needing the key.
- Helper-managed permanent sessions leave startup credentials to the helper (never retrieve, print, copy, persist, or revoke them). A new API service needs an Agent Vault variable, service definition, and authenticated smoke test before readiness passes.

## Boundaries and zero-leak rules
- Use Agent Vault only for configured outbound HTTP APIs. Keep app, database, storage, machine, and Git transport credentials in their own contracts (use SSH for Git; app-config commands do not use the HTTP proxy).
- Never print, log, persist, or pass a real secret (chat, reports, files, env dumps, headers, verbose curl, Docker inspect, worker prompts), and never ask the user to paste one or send one to a subagent. Rotate credentials in Agent Vault; never restore old token files, shell-startup fetchers, or standalone `agent-proxy`.
- `notion-workspaces` owns Notion workspace selection; this skill owns API credential access and handling.
