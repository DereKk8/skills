---
name: config-sync
description: Keep the personal ~/configs repository validated, documented, and synchronized after any intentional edit under ~/configs. Use for Home Manager/Nix, shell configuration, agent runtime hooks, rules, and config, Git and developer tooling, scripts, Neovim, tmux, repository docs, and future configuration areas—not only editor or terminal changes.
---
Skill version: 1.0.1

# Config sync
Keep the `~/configs` repository safe, reviewable, synchronized; never absorb unrelated work.

## Workflow
1. Inventory first: `git status --short`, `git diff --name-status`, `git diff --cached --name-status`. Record pre-existing staged/unstaged/untracked as user-owned; never discard, rewrite, stage, or commit them.
2. Classify each intended path: `flake.nix`/`flake.lock`/`home.nix`/`rebuild.sh` = Nix; `home/.config/{bash,zsh}/` = shells; agent runtime folders under `home/` = agent config; git/CLI/bootstrap/helpers = tooling; `home/.config/nvim/` = Neovim; `home/.config/tmux/` = tmux; `README.md`/`docs/`/indexes = docs; anything else by tool/behavior it controls.
3. Docs only when user-visible behavior or catalog/navigation changes. No churn for internal-only changes.
4. Focused validation per subsystem (report unrunnable checks, never claim unrun validation): Nix = flake/Home Manager eval, `nix flake check` when applicable; shell/scripts = `bash -n`/`zsh -n` + `shellcheck` + safe smoke test; JSON/TOML/YAML = parse/lint; JS hooks = `node --check` + focused test; tool configs = tool's validator or non-destructive smoke test; Lua = parse + headless check; tmux = isolated parse/load; docs = verify links/commands/paths.
5. Review full diff; stage only intended paths: `git add -- <paths>`, `git diff --cached --check`, `git diff --cached`, `git status --short`. Staged diff must contain all intended and zero unrelated changes.
6. Commit with conventional message (`feat(config):`, `fix(config):`, `refactor(config):`, `docs:`), push current branch. Never merge without approval.

Helper: `scripts/sync.sh "<msg>" <relative-paths...>` does guarded stage/review/commit/push. Refuses with no paths or pre-staged changes. Run subsystem validation before it.

Reference: root `~/configs/`; the repo is its `origin` remote.
