---
name: global-skill-sync
description: >-
  Authoritative protocol for creating, editing, deleting, and syncing global agent
  skills across the workstation and remote git repositories. Use whenever an agent
  needs to create a global skill, update an existing skill, understand where skills
  are stored, or prevent skill duplication and collision conflicts across agent
  runtimes.
---
Skill version: 1.2.1

# Global Skill Sync

Owns where global skills live and how they move (`write-a-skill` owns content and `probes.json`).

## 1. Canonical and project scopes
- **Global catalog:** `DereKk8/skills` at `~/projects/skills`, flat layout `skills/<name>/{SKILL.md, probes.json, scripts/, references/, resources/}` (no category folders or root links). Commit there, open a PR to `main`, and merge only with approval.
- **Scope:** Global is only for cross-project skills; repo-only skills live in `.agents/skills/`. Never create physical skill folders inside runtime dirs, alter Home Manager skill symlinks, or keep project-local copies of global skills unless requested.
- **Project skills:** `~/projects/project-skills/<project>/<name>`, linked flat into repos with `~/projects/project-skills/link-skills.sh <project> <repo-dir>...` (never committed in product repos). Supervisor-only skills live in their own folder in `~/projects/project-skills/` and link only into supervisor homes (`link-skills.sh <group> <home>`), never globally.
- **Private overlays:** `DereKk8/skills` is meant to be public, so keep private projects, hosts, workspaces, and profiles in `~/projects/project-skills/overlays/<name>.md` (probes in `overlays/probes/<name>.json`) and reference that path from the global skill.

## 2. Runtime links, versions, and health
- **Symlinks:** Home Manager (`modules/agents.nix` in `~/configs`) links `~/.agents/skills` and `~/.claude/skills` to `~/projects/skills/skills`. Leave `~/.codex/skills` unlinked (Codex writes `.system/` there and loads user skills via `~/.agents/skills`). Skills reference each other via `~/.agents/skills/<name>/...`, never checkout paths.
- **Frontmatter and versions:** `SKILL.md` needs `name` (kebab-case = folder name), `description`, and `Skill version: X.Y.Z` right after frontmatter for owned skills (vendored skills are listed in `VENDORED.md`). Bump in the same commit: MAJOR = breaking (rename, removed rule/step/command/script/trigger, changed parsed format); MINOR = added rule/step/command/script/trigger; PATCH = wording/cuts keeping all rules and triggers.
- **Lifecycle:** Create at `1.0.0` (`feat(skills): add <name>`), modify with bumped version (`fix(skills): update <name>`), or delete with `git rm -r skills/<name>` after checking references (`chore(skills): remove <name>`). Run `BASE=HEAD scripts/check-skills.sh` before committing.
- **Health check:** `readlink -f ~/.claude/skills ~/.agents/skills` must resolve to `~/projects/skills/skills` (if a path is a real directory, delete it and run `~/configs/rebuild.sh`). Keep runtime-written `synced/` and `.system/` git-ignored.
