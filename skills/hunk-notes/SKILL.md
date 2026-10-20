---
name: hunk-notes
description: Store Hunk agent notes on your own committed diff so the human reviewer sees why each change exists. Use before you report a branch, PR, or change as done or ready for review in a git repo. For driving a live Hunk window, use hunk-review instead.
---
Skill version: 1.0.1

# Hunk notes

The reviewer opens a checkout with `hunk-branch` (tmux `prefix + G`). `hunk-branch` diffs the working tree against its fork point from `origin/HEAD`. It shows only the notes stored on `HEAD` under the git-notes ref `hunk`. Notes on an older commit, in a file, or in chat do not appear.

## When

Write the notes after your last commit and before you report done or ready. Git notes stay on the commit they were written for. So if you later commit, amend, or rebase, write the notes again.

## Steps

1. Print the diff the reviewer sees:

   ```bash
   base=$(git merge-base HEAD origin/HEAD)
   git diff -U0 "$base" HEAD
   ```

2. Choose the hunks that the code alone does not explain: intent, a non-obvious decision, a risk, or an open follow-up. Skip mechanical hunks such as renames, formatting, and generated files.

3. Anchor each note to its hunk header `@@ -a,b +c,d @@`:
   - If the hunk adds lines (`d` > 0), use `"newRange": [c, c+d-1]`.
   - If the hunk only deletes lines (`d` = 0), use `"oldRange": [a, a+b-1]`.
   - Hunk does not show a note whose range is outside every hunk.

4. Write the notes in Hunk's `--agent-context` JSON format to a temporary file, never to a tracked path. Then store the file on `HEAD`:

   ```bash
   f=$(mktemp --suffix=.json)
   # write the JSON to "$f"
   python3 -m json.tool "$f" >/dev/null && git notes --ref=hunk add -f -F "$f" HEAD
   git notes --ref=hunk show HEAD   # must print your JSON
   ```

Format, with one file entry per changed file that needs context:

```json
{
  "version": 1,
  "summary": "Retries failed uploads three times before the job reports an error.",
  "files": [
    {
      "path": "src/upload.ts",
      "summary": "Owns the retry loop for one upload.",
      "annotations": [
        {
          "newRange": [41, 58],
          "summary": "uploadFile now retries a failed request up to three times with a 2-second wait.",
          "rationale": "The storage API drops about 1% of requests under load, so one failure no longer fails the whole job. The new test in test/upload.test.ts proves the retry count. A real outage longer than 6 seconds is not tested.",
          "author": "fm/upload-retry"
        }
      ]
    }
  ]
}
```

## Writing rules

The "Assistant response clarity" section of your global instructions owns the style. Apply it to every note as follows:

- Top-level `summary`: one sentence that says what the change does.
- File `summary`: one sentence that says what this file does in the change.
- Annotation `summary`: one sentence of at most 25 words. Name the actor (function, script, rule, or config key) and its action.
- `rationale`: state the cause and the consequence with explicit words such as "because", "so", and "if". Then state what you verified, with the command or test, and what remains unverified.
- Notes are not chat. Do not address the reader, so never write a form of address such as "you", greetings, or progress talk.
- Set `author` to your branch name, or to your agent name when you have no branch.
