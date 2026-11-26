---
name: hunk-notes
description: Store Hunk agent notes on your own committed diff so the human reviewer sees why each change exists. Use before you report a branch, PR, or change as done or ready for review in a git repo. For driving a live Hunk window, use hunk-review instead.
---
Skill version: 1.0.2

# Hunk notes

Reviewers open branches with `hunk-branch` (tmux `prefix + G`), which diffs the working tree against its `origin/HEAD` fork point and reads only git notes stored on `HEAD` under ref `hunk`. Notes on older commits, in files, or in chat do not appear.

Write notes after your final commit and before reporting done or ready. Rewrite them after any later commit, amend, or rebase.

## Steps
1. Inspect the reviewer diff: `base=$(git merge-base HEAD origin/HEAD) && git diff -U0 "$base" HEAD`.
2. Annotate only hunks code alone does not explain (intent, non-obvious decisions, risks, open follow-ups); skip mechanical hunks (renames, formatting, generated files).
3. Anchor each annotation to a hunk header `@@ -a,b +c,d @@`: use `"newRange": [c, c+d-1]` when `d > 0`, or `"oldRange": [a, a+b-1]` when `d = 0`. Out-of-hunk ranges are ignored.
4. Write `--agent-context` JSON to a temp file (never a tracked path), validate, attach, and verify:
   ```bash
   f=$(mktemp --suffix=.json)
   python3 -m json.tool "$f" >/dev/null && git notes --ref=hunk add -f -F "$f" HEAD && git notes --ref=hunk show HEAD
   ```

Schema (one entry per file needing context):
```json
{"version": 1, "summary": "<one sentence>", "files": [{"path": "src/a.ts", "summary": "<one sentence>", "annotations": [{"newRange": [41, 58], "summary": "<=25 words: actor + action>", "rationale": "<cause/consequence + verified command + unverified gaps>", "author": "<branch or agent>"}]}]}
```

## Writing rules
Follow the global clarity rules:
- Top-level and file `summary`: one sentence stating what the change or file does.
- Annotation `summary`: one sentence of at most 25 words naming the actor (function, script, rule, or config key) and its action.
- `rationale`: state cause and consequence (`because`, `so`, `if`), what was verified (exact command or test), and what remains unverified.
- Never address the reader (`you`, greetings, progress talk). Set `author` to the branch name (or agent name when detached).
