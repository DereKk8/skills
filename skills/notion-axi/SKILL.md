---
name: notion-axi
description: "Operate Notion through the notion-axi CLI — search; read, create, update, archive, and move pages; create and edit databases and query/set typed row properties; manage blocks, comments, and file uploads; or call any REST endpoint directly. Use whenever a task touches Notion: finding pages or databases, reading or editing content, working with database rows, comments, files, or anything else in a Notion workspace."
user-invocable: false
author: Maxime Bourmaud (maximebrmd)
metadata:
  hermes:
    tags: [notion, notes, docs, databases, knowledge-base]
    category: productivity
---
Skill version: 2.0.0

# notion-axi
Ergonomic Notion CLI. Prefer over MCP/raw API. Use the installed `notion-axi`
command when available. If it is unavailable, invoke `npx -y notion-axi` inside
the Agent Vault session selected by `notion-workspaces` and `secrets`. Those
skills own workspace selection, readiness, and inherited sessions. On an API
authentication error, report the profile and Notion service to the startup
caller for a readiness check.
Do not run `ntn login`, export a raw key, or use another credential path to
bypass Agent Vault. `users` can return `RESTRICTED_RESOURCE` when access is not
available; handle it gracefully.

Use for: search, page read/create/update/archive/move, DB schema/rows, blocks, comments, files, raw API.

Workflow: bare call = recent pages/DBs. `search <q>` → note `id`. `page view <id>` (preview ~1500 chars; `--full` for all). `db view <id>` schema; `db query <id>` rows (title+3 cols; `--full`, `--limit <n>`); server-side `--where Name=value` (repeatable, schema-typed) or raw `--filter <json>` (mutually exclusive), `--sort F:asc|desc` (repeatable), `--cursor <c>` (`next_cursor`/`has_more`). `db create --parent <page> --title <n> --prop Name:type`; `db edit <id> --add/--remove Name[:type]`. `page create --parent <id> --title <t>` (`--db` for row, `--content <md>`, `--set Name=value` repeatable). `page update <id>` (`--append/--replace` body or `--*-file`, `--set` props). `page archive <id>` (`--restore` undo, idempotent); `page move <id> --to <parent>`; `block list/delete`; `comments list/add/delete`; `users get`; `whoami` (token identity). `file upload <path> [--attach <page>]` (single-part multipart). `api <method> <path> [--body <json>]` escape hatch. Follow `help:` hints.

Commands: `(none)=home, search, page, db, block, users, comments, whoami, file, api, setup`; page: view/create/update/archive/move; db: view/query/create/edit; block: list/delete; users: list/get; comments: list/add/delete; file: upload. `--help` globally/per command.

Tips: TOON output; grep only huge lists. `ntn` token acts as user, so `OBJECT_NOT_FOUND` = wrong id, not sharing. `<id>` accepts DB or data-source id (auto first source; `--source` to target). Widen with `--fields url` (search) / `--fields a,b` / `--full`. Prefer `--where Status=Todo` over fetch-all-filter; page with `--cursor`. Bodies are markdown (`--content/--append/--replace/--*-file`). `--set` typed: dates `start..end`, multi-select/people/relation comma-separated, checkbox true/false. Views/notes/templates/paginated props via `api`. Exits: 0 ok, 1 error, 2 usage; errors carry `error`/`code`/`help`.
