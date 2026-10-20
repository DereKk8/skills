# skills

The canonical global agent skills for this workstation. Each folder under `skills/` is one skill, flat, with its `SKILL.md`. Runtimes read them through `~/.agents/skills` and their own skill folders, which link to this checkout.

## Use on a machine

1. Clone the repo: `git clone git@github.com:DereKk8/skills.git ~/projects/skills`.
2. Let Home Manager (`home.nix` in `~/configs`) link each runtime skill folder to `~/projects/skills/skills`.
3. Edit skills in `~/projects/skills/skills/<name>/`, commit on a branch, and open a PR to `main`.

## Rules

- Owned skills carry `Skill version: X.Y.Z` after the frontmatter. Raise the version in the same commit as the change. The rules are in `skills/global-skill-sync/SKILL.md`.
- Vendored skills keep upstream bytes. Their pins are in `VENDORED.md`.
- `scripts/check-skills.sh` checks the layout, names, versions, and paths. CI runs it with `tests/skill-evidence.test.py`.

## Layout

- `skills/<name>/SKILL.md`: one skill per folder.
- `scripts/check-skills.sh`: layout, name, version, and path checks.
- `scripts/update-pstack.sh`: re-sync the vendored pstack skills.
- `tests/skill-evidence.test.py`: tests the `write-a-skill` scripts.
- `LICENSES/`: upstream licenses for vendored content.
