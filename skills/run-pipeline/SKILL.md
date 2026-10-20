---
name: run-pipeline
description: Drive a finished implementation through the no-mistakes pipeline with real CI and the rebase guard. Use when asked to run the no-mistakes pipeline, or to validate and ship a finished branch. Layers over the no-mistakes skill and does not change it.
---
Skill version: 1.0.1

# Run pipeline

Read `~/.agents/skills/no-mistakes/SKILL.md` alongside this skill. It owns the gate loop and the intent rule; this skill adds the rebase guard and the local defaults.

Before you start, the implementation is finished and staged or committed on a feature branch, not the default branch, and `no-mistakes doctor` is healthy.

## 1 - Commit
If only staged changes exist (`git diff --staged` is not empty), the operator reviews and commits them (`git commit -m "<task-id>: <summary>"`). Skip this step when the work is already committed.

## 2 - Drive
Pass the full intent as the no-mistakes skill defines it: what the user set out to accomplish, in their words, with every delivery requirement they stated.
```sh
no-mistakes axi run --intent "<what the user set out to accomplish>"
```
CI always runs: real CI on every ship (standing order since 2026-09-17). Watch it to a result with `gh-axi pr checks <number>`; an unobserved green does not count.

Let `rebase` run, and never skip it on a first run, because a stale but green branch can break on base changes it never saw. At the `pr` step, and after any rerun that touches history, run the guard:
```sh
bash ~/.agents/skills/run-pipeline/rebase-guard.sh --base <base> --feature <branch>
```
The guard classifies the branch by patch-id equivalence (`git cherry`). Act on its verdict only:

| Verdict | Meaning | Action |
|---|---|---|
| `CLEAN` (0) | current, no duplicates | nothing; do not skip rebase |
| `STALE` (10) | behind, no duplicates | rebase, never skip: `git rebase origin/<base>` |
| `DUPLICATED` (20) | a rebase re-applied base commits | `--fix`, `git push --force-with-lease`, then `no-mistakes rerun --skip=rebase` (scoped recovery only) |
| `REAL_CONFLICT` (30) | genuine conflict | rebase by hand with `git rebase origin/<base>`; do not skip |

`--fix` linearizes the branch and keeps the PR-head tree byte for byte. It refuses, with a `NOTE:` that says to run `git rebase` first, when the fix would revert commits that exist only on the base. Use `--skip=rebase` only on a recovery rerun the guard justified, never on a first run.

Run the gate loop per the no-mistakes protocol: auto-fix, then decide; ignore a no-op; escalate `ask-user`; answer `outcome:` with `respond approve|fix|skip`. Use `--yes` only with explicit consent to run unattended.

## 3 - Report
Give the outcome (`checks-passed`, `passed`, `failed`, or `cancelled`) and the PR link from the pipeline `help` line. On failure, say what blocks and how to retry: `no-mistakes rerun`, or rework the change.
