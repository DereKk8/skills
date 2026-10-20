---
name: gh-axi
description: "Operate GitHub through the gh-axi CLI - issues, pull requests, workflow runs, workflows, releases, repositories, labels, search, and raw API access. Use whenever a task touches GitHub: listing or filing issues, reviewing or merging PRs, checking CI runs, triggering workflows, cutting releases, or querying the GitHub API."
user-invocable: false
author: Kun Chen (kunchenguid)
metadata:
  hermes:
    tags: [github, git, ci, pull-requests, releases]
    category: devops
---
Skill version: 3.0.0

# gh-axi
Ergonomic wrapper around `gh`. Prefer over raw `gh`. Use the installed `gh-axi`
command when available. Follow the `secrets` skill for agent profile selection,
startup, and inherited sessions. The operator's existing `gh` keyring login
remains available for human CLI use. It does not replace the agent startup
contract. On an API authentication error, report the profile and GitHub service
to the startup caller. Do not fetch a raw key or use another authentication
route to bypass failed readiness.

Use for: issues, PRs, workflow runs/CI, workflows, releases, repos, labels, search, raw API.

Workflow: bare `npx -y gh-axi` = repo dashboard (open issues/PRs, next commands). Drill command-first: `issue list`, `issue view <n>`, `pr view <n>`, `pr checks <n>`, `run view <id>`. Cross-repo: `-R owner/name` (or `--repo`) AFTER command (`gh-axi issue list --repo=owner/name`). `workflow run <name> --ref <ref>` triggers; `run` manages runs. CI debug: `run list`, then `run view <id> --job <job-id>` or `run view --job <job-id> --log-failed`; long logs keep tail + `full_log` file for grep. Follow `help:` hints every response.

Commands: `(none)=dashboard, issue, pr, run, workflow, release, repo, label, search, api, setup` (+ inherited `update`; `gh-axi update --check` / `gh-axi update`). `--help` globally or per command.

Tips: TOON output, token-efficient; grep/head only huge lists. Truncated logs keep last 20K chars + `full_log` path. Mutations idempotent, safe to retry. Multi-line bodies: write UTF-8 file, pass `--body-file <path>`. `api` covers the rest (ex `api repos/{owner}/{repo}/topics`).
