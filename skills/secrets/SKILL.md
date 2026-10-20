---
name: secrets
description: >
  Use for Agent Vault profile selection, startup, inherited API connections, or
  secrets for GitHub, Notion, Context7, Linear, Typesafe, Cloudflare, and other
  configured HTTP services. Routes general builders and project builders and
  testers through Agent Vault without exposing credential values.
---
Skill version: 4.0.0

# Secrets

Keep API credentials inside Agent Vault. Let `agent-access` start the selected
profile and proxy requests, so agents and child tools receive placeholders
instead of real API keys. The public connection settings are in
`~/.config/agent-access/config.json`; `~/configs/docs/agent-access.md` owns the
full startup and readiness contract.

General-purpose builders use the `coding` profile. Project builders and testers
use their project's profile: read the agent contract in
`~/configs/docs/agent-access.md` before you choose one, because it names the
profile each project uses. Before a new session, run
`agent-access doctor <profile>` and then
`agent-access run <profile> -- <command>`. The `coding` profile currently uses
default readiness checks and does not support a selected-services check. For a
project profile, select only configured services the task needs, such as
`notion`; service selection limits readiness checks, not the profile's
permissions. If `AGENT_ACCESS_PROFILE` is already
set, use the inherited proxy, certificate, and placeholder environment without
starting another session. Invoke the tool directly in that environment. Do not
run doctor or retrieve startup credentials inside the launched agent. Stop if
the public profile lacks a required service or lists that service as pending.

For example, a general builder can use the GitHub tool through `coding`:

```sh
agent-access doctor coding
agent-access run coding -- gh-axi api user
```

A project tester who needs only Notion can check that service and start the
Notion CLI through the project's profile:

```sh
agent-access doctor --services notion <project-profile>
agent-access run --services notion <project-profile> -- notion-axi whoami
```

Stop when doctor fails, reports exit 78, names a missing key, or reports a
service pending its authenticated smoke test. Do not fetch a key directly,
change the readiness result, or switch to another credential path. When a
project's verify skill keeps a `secrets.json`, check it with
`agent-access doctor <profile> --needs <file>`. Ask the owner for each missing
key with `agent-access request <profile> --needs <file> --task <issue URL>`,
or with `--key`, `--host`, `--description`, and `--obtain` for one key that no
file declares. It posts one request to the owner's Discord channel and never
asks twice. Then stop the work that needs the key. In
particular, when a project has no configured profile, do not claim one exists
or fetch that project's key directly.

Use this route only for configured outbound HTTP APIs. Keep application,
database, storage, machine, and Git transport credentials in their existing
project or tool contracts. Use SSH for Git transport. A project's own
application-configuration command keeps its separate contract; it does not use
the HTTP proxy for database or storage access.

A profile that reuses a helper-managed permanent session leaves that session's
startup credential to the helper. The helper does not mint or revoke it.
Never retrieve, print, copy, persist, or revoke that credential manually. A new
API service needs its Agent Vault variable and service definition plus an
authenticated smoke test before readiness can pass.

Never print, log, persist, or pass a real secret as an argument. Do not put
secrets in chat, reports, files, environment dumps, HTTP header logs, verbose
curl output, Docker inspection output, or worker prompts. Never ask the user to
paste a secret into chat or send one to a subagent. Rotate credentials in Agent
Vault. Do not restore old token files, shell-startup fetchers, or the standalone
`agent-proxy` path.

`notion-workspaces` owns Notion workspace selection. This skill owns API
credential access and handling.
