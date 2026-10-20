# Notes verification map

This directory is the maintained source for verifying the user-facing behavior of Notes. Read the index before driving the app, then use the matching feature file as the recipe.

## Baseline preconditions

- Launch Notes at `http://127.0.0.1:4173` with a disposable data directory.
- Set `NOTES_DATA_DIR=/tmp/notes-verify-$RUN_ID` so concurrent runs do not share state.
- Seed notes titled `Quarterly plan` and `Grocery list`.
- Put `control-notes` and the `notes` CLI on `PATH`.
- Run `control-notes doctor` and require the expected URL, data directory, and build revision.
- Never drive an instance that was not started by this verification run.

## Driving conventions

- Start every recipe from the baseline state unless its preconditions say otherwise.
- Prefer ARIA roles and accessible names over CSS selectors or DOM position.
- Treat every command as literal. Keep quoted names and flags unchanged.
- Run browser actions through `control-notes browser`.
- Run terminal actions through `control-notes cli -- <command>`.
- Restore seeded data after a mutation. Do not remove proof artifacts during cleanup.

## Proof and skip reporting

- Capture the user action and the resulting state, not only the final screen.
- UI proof includes an ARIA snapshot and a screenshot with the app identity visible.
- CLI proof includes the command, stdout, stderr, and exit code.
- Mutation proof includes a read-only second view of the stored value.
- Record the feature ID and entry point used with every artifact.
- Report an unreachable path with the attempted command and the unmet precondition.
- Do not report a skipped entry point as verified through a different path.
- Report each attack scenario tried as `attack: <scenario> | how: <command> | result: <observed>`, and say whether the safe expected result held.
- A report with no attack lines is not a pass. A broken safe result is a found bug, not a skipped step.

## Feature entry contract

Each feature file starts with an H1 title and one paragraph describing the user-visible behavior. It then uses exactly five H2 sections in this order.

1. `Sub-features` lists short IDs with one line for each behavior.
2. `How to get to it (user POV)` lists every user entry point.
3. `Driving it with <harness>` starts with `Preconditions:` and uses labeled bullets that pair each user action with an exact command and observable result.
4. `Attack scenarios` lists realistic ways the feature could break, most likely and most damaging first. Each bullet names who triggers it and how it really happens, the exact command that tries it, the safe expected result, and the past bug it came from when there is one. Keep only scenarios a real user, operator, or real failure could cause, such as a retry after a timeout, a double submit, a network drop mid-save, or two tabs at once. Notes holds no secrets or payments, so theoretical attacks stay out.
5. `Gotchas` lists traps that can waste or invalidate a verification run.

Keep implementation details out of the map. Name only user paths, stable handles, required state, commands, and observable proof.

## Features

- [Create a note](./create-note.md) covers browser and CLI creation, cancellation, persistence, double saves, and cleanup.
- [Search notes](./search.md) covers toolbar, keyboard, and CLI search with matching, empty, clear, and stale-result states.
