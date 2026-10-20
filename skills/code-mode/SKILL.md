---
name: code-mode
description: Decide when one script that calls your tools or commands beats direct tool calls, and keep its output small. Use before a tree scan, bulk read, pagination loop, transcript or row sampling, or a batch of status commands.
---
Skill version: 1.0.1

# Code mode
Code-mode is a capability, not one specific tool: a single call runs a script, the script calls your other tools or commands, and only the script output comes back to you.
When code-mode has a concrete advantage, use the first form you have:
- A code-mode, programmatic tool-calling, or code-execution tool.
- Otherwise, one shell or script call that runs the whole loop and prints only the result.

Before calling code-mode, compare it with the best direct path. Name the advantage: less model-visible data, fewer model turns, lower tool latency, or necessary access to deferred tools. Compare with server-side filters, one shell command, and native parallel calls. Do not credit code-mode for savings the inner command already provides. If there is no advantage, call the tool directly. Keep reasoning, approvals, and user-steered trials outside scripts.

Prefer code-mode for mechanical work with a concrete advantage:
- Compose dependent calls, bounded pagination, and deterministic branches without returning every intermediate result.
- Run independent I/O concurrently when direct calls cannot provide equivalent concurrency.
- Discover deferred tools and read their schemas before you call them.
- Scan a tree for counts, paths, or matching lines. Return that table from the script.
- Sample or summarize many transcripts, pages, Notion rows, or database rows. Return only the fields you will use.
- Read past a truncated page. Loop the offset or read the file in the script, and print only the needed lines.
- Run several read-only status commands before a decision. Return one small object. Crew state, peek, diff stats, and task show fit this case.
- Filter long tool results to the evidence needed for the next decision. Use a new call for each user-steered trial.
- Follow project wait protocols. Do not replace a blocking wait with repeated sleep-and-status turns.

Script output rules:
- Keep script output under about 10K tokens, because longer tool output is often cut in the middle.
- Print counts or sizes before content, so a filter that matches nothing or everything is visible.
- Check command exit codes, tool error flags, and intermediate truncation; report failures and partial results.
- Bound total returned output. Deduplicate excerpts and keep source paths for omitted details.
- Use native parallel calls when they provide the same concurrency and result size.

Do not use code-mode for these jobs:
- Wrapping directly available calls without discovery, computation, composition, or output reduction.
- One `write` or `edit` of text the user already gave you, or that you already composed. A script that only writes a finished report is a `write`. Do not paste content into a write that you have not read.
- Dumping whole files or whole command output back to yourself. If you can issue parallel tool calls, use them instead of batching reads in a script.
- Spawn, send, lease claim, commit, push, or dispatch. The user may correct that step on the next message.
- A judgment or a short reply when the needed facts are already in the conversation.
- One small command.
- Any turn after the current user message. A message or wake event that arrives later is its own turn. A read-only status script inside that turn is still allowed.

For a script that sends many records to a cheap decision model, load the `jev-codemode` skill.
