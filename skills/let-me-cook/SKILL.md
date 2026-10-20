---
name: let-me-cook
description: >-
  Explicit slash command only. Invoke as /let-me-cook or /skill:let-me-cook.
  Investigate recent AI use, prove at most one improvement in isolation, and
  stop for approval. Do not load for quota, usage, inefficiency, improvement
  ideas, or any message that does not invoke the command.
disable-model-invocation: true
user-invocable: true
compatibility: Python 3 and a host that can run a shell.
---
Skill version: 1.4.0

# Let me cook

One invoke should end with nothing to change, or with one proven improvement waiting for a yes or a no. A yes deploys that exact change and checks it. A no leaves the target as it was and is remembered. Remove a repeating waste in how AI is used here by changing the cause that produces it, so the waste cannot happen again. Do not add a detector, a reminder, or a review step that lets the waste continue.

## Boundaries

Run only because the user invoked this command. Do not install a hook, a schedule, a watcher, or a log. This command reads evidence that already exists, then it ends.

Change how agents work: a skill, an instruction, a hook, or another local workflow file. A file of that kind stays in scope when it sits inside a product repository. Out of scope is that product's application source and product tests. Do not skip an agent file because the code beside it is product work. If the only worthy change is product work, record it as out of scope and stop.

The target you name is the file deploy will write. If you are not authorized to write the natural path, copy the file into the authorized scope, name that copy as the target with `begin --stand-in-for <natural path>`, and run the check on the copy. A stand-in run is a proof, never a change to the natural file: approve writes the copy only, and the natural path stays exactly as it was. Do not write the natural path, and do not stop only because the natural path is outside the scope.

If `LET_ME_COOK_SCOPE` is set, every target stays inside it. Never widen that scope. Never choose a credential, token, key, or secret file as a target. Never copy chat text or session log text into the ledger, an experiment, a candidate, or a reply; those places take a paraphrased one-line summary only. If you see a secret, skip that span. Do not print it, and do not write it into the ledger, the experiment, or your reply.

Do not push, send mail, open a pull request, call a paid API, or delete a file outside the experiment directory. Deploy is only the approve command below. Included quota may be spent when the investigation needs it. A new charge, a new key, a paid add-on, or a subscription is not authorized.

## State

The ledger, experiments, and rollback snapshots live in one state directory. `scripts/cook.py` beside this file resolves it: `$LET_ME_COOK_HOME` if set, otherwise `$XDG_STATE_HOME/let-me-cook`, otherwise `%LOCALAPPDATA%\let-me-cook` on Windows, otherwise `~/.local/state/let-me-cook`.

Run `python3` on `scripts/cook.py` by its path in the skill directory the host gave you. Do not depend on the current working directory. Keep the environment you were given. Clearing `LET_ME_COOK_HOME` or `LET_ME_COOK_SCOPE` writes the wrong ledger or escapes the authorized target.

A rejection is stored in `<state dir>/ledger.json`, as a row with `status: rejected`, the slug, and the reason. Run `scripts/cook.py path` to print the state directory, so `path` plus `/ledger.json` names that file.

Start with `list`. Use that ledger. Do not open a second one, and do not edit it by hand. A slug that `list` shows as rejected or rolled back is closed. Do not pursue it unless `gate` accepts new evidence that the recorded decision does not contain. `gate --slug <slug>` reads the ledger and exits 3 when the slug has a rejected or rolled-back row, printing the recorded id and summary. A reworded solution to the same problem is not new evidence. A `none` or `out-of-scope` row does not close a problem. It only records that one run stopped.

## What to read

Read only recent evidence of how agents work here: session logs from Claude Code, Pi, and Codex, plus firstmate task notes and skill probe results. Recent means one fixed window of 7 days by file modification time. `scripts/digest.py` owns the source paths and the window, so do not read older files or other places. Do not tour the archive, and do not build a standing collector.

Raw session logs are too large for a cheap model, and a worker that gets them falls back to keyword searches. So run `python3 <skill dir>/scripts/digest.py` first. It writes a read directory under the state directory and prints its path and the slices. Each slice has two files:

- `<slice>.digest`: the waste signals of each session, which are human turns, failed tool results, hook output, repeated calls, and the agent text a human reacted to. Every line keeps its source `path:line`. Routine calls are folded into counts.
- `<slice>.files`: the source files of that slice. One session never spans two slices.

### Who reads it

A handful of cheap workers read the digests, so the parent agent keeps its context for selecting and proving. Invoking this command authorizes one worker per slice and their included quota, so start them without asking.

Start each worker as a headless run of the harness's own command-line tool, with the cheap model fixed in that run's command, so the launch guarantees the model. An in-session subagent tool does not qualify, because it saves its transcript where the next run of this command reads it as evidence. For the same reason the headless run saves no session. It also gets read, shell, and write access up front, because a headless run cannot answer a permission prompt. Start all workers at once as background shell jobs, one per slice, with each run's output in its scratch path, then wait for all of them. For example:

- Pi: `pi -p --no-session --no-mcp --model openai-codex/gpt-6-luna --tools read,bash,write "<brief>"`.
- Codex: `codex exec --ephemeral --skip-git-repo-check -s workspace-write -C <read dir> -m gpt-6-luna "<brief>" < /dev/null`. Without `< /dev/null` a background job waits on stdin and returns nothing.

Once the workers start, confirm that each one runs on the cheap model. Read the model from what the run reports about itself, such as its start event or the model on its replies, not from the command you wrote. Stop a worker on any other model at once, because it spends the quota this design saves, then restart that slice correctly or read it yourself.

Each worker reads its whole `<slice>.digest`. It may open a source file from its `<slice>.files` at a cited line when the digest does not show enough. It writes its report to `<read dir>/<slice>.md`, and keeps any scratch work under `<read dir>/<slice>/`. Those two paths are the only places a worker writes. The report lists each repeating waste with a paraphrased summary, every occurrence as `path:line`, the count of separate sessions, the likely cause if the evidence shows it, and what the worker could not check. The worker's final message names the report path and gives one line per lead.

Each brief names the digest, the file list, the report path, the scratch path, and the secret rule from Boundaries. Workers do not run `scripts/cook.py` or pick a winner. If the harness cannot start a worker on a cheaper model, the parent reads the digests itself.

The parent reads every report file in full. A worker's lead is not evidence, because a cheap model can merge two different wastes or miss one. Before selecting, the parent opens the cited `path:line` spans in at least two separate session files and confirms the repeat and its cause itself. Then it deletes each `<slice>.digest` and `<read dir>/<slice>/` scratch folder, plus any folder a headless run still left in its harness's own session store, because they hold log excerpts, and keeps the reports and file lists. Stop once one waste is confirmed in two sessions, or the reports show nothing that repeats.

## What to select

Select at most one opportunity. It has to repeat, or the structure has to make it repeat.

Before you design a fix, name the root cause: the file, default, rule, ordering, or missing piece that makes agents produce the waste. Ask why the waste happens until the answer is something you can change, not an agent's choice in one session. The fix changes that cause, so the waste cannot occur. A fix that tells agents to notice, ignore, avoid, or recover from the waste treats a symptom, and a symptom fix is not an opportunity. For example, a hook flags every new brief before its model is set, and agents then ignore the flag. A sentence telling agents to ignore the flag is a symptom fix. Changing the hook so it checks the brief only once a model is set removes the cause.

If the cause is product work, which Boundaries puts out of scope, record it with `stop --status out-of-scope` and do not fall back to a symptom fix. A cause in an agent file you may not write still gets a stand-in copy, as Boundaries says.

A repeat is the same waste in at least two separate session files inside the 7-day window. Two mentions inside one session are one occurrence, not a repeat. A gain is small when the baseline check counts fewer than two affected occurrences, or when the fix changes only the single invocation that showed the waste. Drop a small gain.

If the best real gain is small, or you cannot show it with a check you can re-run, stop. Do not manufacture an opportunity so the run has a result.

Name the slug for the problem, not the solution, in lowercase words joined by hyphens. Run `gate --slug <slug>` before `begin`.

## How to prove it

1. Run `begin --slug <slug> --target <absolute-file> --summary <one line>` before any edit. Add `--stand-in-for <absolute-file>` when the target is a copy standing in for a path you may not write. Edit only inside the experiment directory it prints. The live target stays untouched until approve.
2. Write a check you can re-run. It must fail on the baseline for the waste you claim, and pass when that waste is gone. A check that only looks for a sentence you added is not evidence. The check must exercise the cause, for example by running the hook, script, or workflow that produced the waste. Build at least two candidate files under `candidates/`, each a different design that changes the cause. Run the same check on each. The measurement is the check's output, not an estimate.
3. Run the check on the baseline and keep its failing output word for word. Write one line on why the check measures the claimed waste and not merely your edit. Show the command, that failing output, and that line to the human before you run `propose`. That is a report, not a question, so do not wait for an answer. The decision package repeats all three.
4. Run `check <id>`. If it does not match, stop. Do not propose, and do not repair the live file.
5. Write `evidence.json` inside the experiment directory. Run `propose --help` and use those keys, including `check_command`, `baseline_failure`, and `fairness`. Then run `propose <id> evidence.json`. The winner is the candidate the check supports.

If the comparison shows no gain, run `drop <id> --reason <one line>`. That is not a rejection. Rejection is only the human's word. Then run `stop --status none --reason <one line>`.

If you found nothing that clears the bar, run `stop --status none --reason <one line>`. If the only candidate is product work, use `--status out-of-scope`.

A stop still reports what the run learned, so the human can act on it: the strongest confirmed repeat with two `path:line` citations, its root cause, and what blocked a fix. Without that report, the next run repeats the same investigation.

A decision word applies only after `propose` has succeeded. Do not deploy in the same action as the package unless the invoking message already used that word for this run.

## Done

This run is done when the ledger has a `none`, `out-of-scope`, `rejected`, or `deployed` decision, and you have read the live target back after a reject or a deploy. A deployed change is done only when `verify` prints `match=yes` and the rollback snapshot is still there. When the target is a stand-in copy, `verify` must also print `natural_match=yes`, and the run reports a proof, never a change to the natural path.

## Decision package

End a run that needs a human decision with only these fields:

- Opportunity: one sentence
- Root cause: what makes the waste happen, and how the winner changes it so the waste cannot occur
- Ledger id: the id `begin` printed
- Target: the live path, named as `natural path` or as `stand-in copy for <natural path>`
- Check: the command you re-ran, and why it is a fair test of the claimed waste
- Baseline failure: the check's failing output before the change
- Value: the comparison the check measured
- Risks: what can go wrong
- Rollback: `rollback <id>` after a deploy
- Decision: approve deploys this exact change; reject leaves the target unchanged

A stand-in run says so here in plain words: approve writes the copy, and the natural path stays exactly as it was.

Ask once for `approve` or `reject`, then wait. Those are the only decision words. "Looks good" is not a decision, and neither is silence. Any other reply is not a decision, so do not deploy, do not reject, and keep waiting for one of those two words.

On reject, run `reject <id> --reason <one line>`, then `verify <id>`, and read the live file. The live bytes must still match the baseline.

On approve, run `approve <id>`, then `verify <id>`, and read the live file. The live bytes must match the winner, and the rollback path must exist. Do not ask for another confirmation.
