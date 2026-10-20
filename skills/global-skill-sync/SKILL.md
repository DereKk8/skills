---
name: global-skill-sync
description: >-
  Authoritative protocol for creating, editing, deleting, and syncing global agent
  skills across the workstation and remote git repositories. Use whenever an agent
  needs to create a global skill, update an existing skill, understand where skills
  are stored, or prevent skill duplication and collision conflicts across agent
  runtimes.
---
Skill version: 1.2.0

# Global Skill Sync

This skill owns where global skills live and how they move. How to write a skill's content belongs to `write-a-skill`.

## 1. Canonical source
The canonical global skills repo is `DereKk8/skills`, checked out at `~/projects/skills`. It holds one flat folder per skill: `~/projects/skills/skills/<skill-name>/SKILL.md`, with no category folders and no root links. Commit a skill change in that checkout, push it through a PR to `main`, and merge it only after the user approves.

A skill belongs in global scope only when it applies on any project, because every global skill's description loads in every agent session on the machine. A skill for one project lives with that project (section 2). A skill for this repo only lives in this repo at `.agents/skills/`.

Never create a physical skill folder inside an agent runtime's own folder, and never replace or remove a skill-folder symlink that `home.nix` declares. Do not keep a project-local copy of a global skill unless the user asks for an override.

## 2. Project-local skills
Project skills live in a private `project-skills` repo, checked out at `~/projects/project-skills`, with one folder per project. Projects consume it through flat per-skill symlinks, never committed skill files, so product repos stay free of agent files: `<repo>/.agents/skills/<skill-name> -> .../project-skills/<project>/<skill-name>`. Create the links with `~/projects/project-skills/link-skills.sh <project> <repo-dir>...`; its README lists each project's repos. Edit skills in the checkout, never at the project end. On a fresh machine, clone the repo to `~/projects/project-skills` and re-run the links.

This catalog is meant to be public, so a global skill never names a private project, workspace, or host, or a profile or link that belongs to one. When a global skill needs such a detail on this machine, put it in `~/projects/project-skills/overlays/<skill-name>.md`, and have the skill name that path and read it. Project-specific probes go in `overlays/probes/<skill-name>.json`.

Firstmate supervisor skills follow the same pattern in the `firstmate/` folder. They are linked only into Firstmate supervisor homes (the primary `~/firstmate` and each secondmate home), so a session started anywhere else never sees them. Link a new home with `~/projects/project-skills/link-skills.sh firstmate <home>`. Never put a Firstmate-only skill in this global catalog.

## 3. Runtime symlink map
Home Manager (`home.nix` in `~/configs`) links each agent runtime's skill folder to `~/projects/skills/skills`, except Codex. The `home.file."<path>/skills"` lines are the list. Codex is omitted because its CLI installs bundled system skills into `$CODEX_HOME/skills/.system`, and a link would write those files into the checkout. Codex still reads user skills through `~/.agents/skills`. Do not add `home.file.".codex/skills"` back.

Skills refer to each other by the runtime alias `~/.agents/skills/<skill-name>/...`, never by a path into a checkout. The alias works on every machine that runs the runtimes.

## 4. File layout
```
skills/<skill-name>/{SKILL.md, probes.json, scripts/, references/, resources/}
```
`SKILL.md` needs frontmatter with `name` (equal to the folder name, kebab-case) and `description` (what the skill does and when to load it). The `write-a-skill` skill writes the body and the optional `probes.json`.

## 5. Versions
Every owned skill has `Skill version: X.Y.Z` as the first line after its frontmatter. Vendored skills keep upstream bytes and are listed in `VENDORED.md` instead.

- MAJOR: a caller can break, for example a rename, a removed rule, step, command, or script, a changed output or file format another skill or script parses, or a removed load trigger.
- MINOR: an added rule, step, command, script, or load trigger.
- PATCH: wording or cuts that keep every rule and trigger.

Raise the version in the same commit as the change. `scripts/check-skills.sh` fails a changed skill whose version does not rise, counting committed and pending edits under the skill folder. Run `BASE=HEAD scripts/check-skills.sh` before every commit.

## 6. Lifecycle
- Create: check the name is free with `ls ~/projects/skills/skills/`, create `skills/<skill-name>/SKILL.md` with `Skill version: 1.0.0`, run `scripts/check-skills.sh`, then commit with `feat(skills): add <skill-name>`.
- Modify: edit `skills/<skill-name>/SKILL.md`, raise its version, run `scripts/check-skills.sh`, then commit with `fix(skills): update <skill-name>`.
- Delete: `git rm -r skills/<skill-name>`, then commit with `chore(skills): remove <skill-name>`. Check that no skill, script, or `home.nix` line still names it.

## 7. Health check
Each runtime skill folder must resolve to `~/projects/skills/skills`. Run `readlink -f ~/.claude/skills ~/.agents/skills ~/.pi/agent/skills`, and confirm each line prints the absolute path of `~/projects/skills/skills`. If a runtime folder has become a physical folder, remove that path and run `~/configs/rebuild.sh`.

`ls ~/projects/skills/skills/` must show only skill folders. Runtime-written folders such as `synced/` and `.system/` are git-ignored and never committed.
