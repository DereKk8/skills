---
name: hunk-review
description: Interacts with live Hunk diff review sessions via CLI. Inspects review focus, navigates files, hunks, and exact lines, reloads session contents, adds inline review comments, and paints attention marks on character ranges. Use when the user has a Hunk session running or wants to review diffs interactively.
---
Skill version: 1.0.0

When I ask you to walk me through or comment on a diff in my running Hunk window, drive it only through `hunk session` commands (`hunk session --help` lists them, and the file that `hunk skill path` prints is the full reference for the installed version), never `hunk diff` or `hunk show`, because those open an interactive viewer that blocks your shell, then tell the story in the order that explains it best, move my view to the code before each note, note only what I would not spot myself, and ask before you restart the daemon or clear my own notes.
