---
name: write-a-skill
description: Write, revise, shorten, fix, or audit a skill, an instruction file, or a worker prompt the user owns, starting from evidence in past transcripts, and show that the change improves agent behavior. Use whenever the user asks to create a skill (global or project), change what a skill says or when it loads, remove a stale part, check a skill after its tool changed, turn a repeated correction into a skill, or improve the prompt variables file. Load it together with global-skill-sync, which covers only where skills live.
---
Skill version: 1.0.4

A skill earns its place when agents behave better with it than without it. I want skill text that states the intent and leaves the model room to reach it its own way, unless the skill describes a fixed workflow. Every change starts from evidence of how the skill behaves today and ends with evidence that the change helped.

Read `variables.md` beside this file first. It lists the variables that move agent behavior, how sure we are of each one, and the setting that works here.

1. **Find the failures in history.** Run `scripts/history.py corrections <skill>` for my corrections soon after the skill loaded, and `scripts/history.py misses <skill> --about '<topic regex>'` for corrections on its topic in sessions where it never loaded. For a new skill, run only `misses`. Open each hit that looks real at its `file:line`, and write one line per failure: what the agent did and what I wanted. If history has nothing, ask me for two or three real prompts. To pick which skill to improve, `scripts/history.py sweep` ranks them all.
2. **Turn failures into probes.** Add each failure to the skill's `probes.json` as a prompt that should load the skill, with a `look_for` regex when the failure was in behavior and not in loading. Add prompts near the topic that must not load it. Run `scripts/probe.py <skill> --file <its probes.json> --label before` to measure the installed text.
3. **Diagnose with the variables.** Name the variable behind each failure and the setting `variables.md` gives for it. When no variable fits, add the failure to `variables.md` as a new hunch.
4. **Change the skill.** Change only what the diagnosis points to. Write the description as the trigger, in my words. Keep only sentences that carry what the agent cannot find, a limit only I can set, the proof of done, or a fix for a failure you reproduced. When you rewrite or shorten, list every behavior the old text produced and keep each one.
5. **Prove it.** Run `scripts/probe.py <skill> --draft <edited skill folder> --label after` on the target model, which swaps in only your edited folder. Land the change only when every probe that passed before still passes and the probes for the failures you targeted now pass. Loading is not deterministic, so rerun a probe that flips with `--runs 3` before you trust it.
6. **Record the evidence.** Add one dated line to each variable you relied on, with the before and after numbers and the path of the saved result, and move its level when the rule in `variables.md` says so. When a result goes against an observed variable, mark it shaky and tell me.

Scale the work to the change: a one-line fix needs one history query and the probes it touches, and a new skill or a rewrite gets the whole loop. Probes spend my Claude quota, so check `quota-axi` before a large batch and report the cost.
