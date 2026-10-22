# Vendored skills

Vendored skills keep their upstream bytes, so they carry no `Skill version:` line. Their pin here is the version. `scripts/check-skills.sh` accepts a skill with no version line only when this file names it in a `- \`name\`` entry.

## pstack verification skills

Commit SHA: d457567332aa6989e753ea289f30ea2bfbc80bc0
Commit date: 2026-10-19T05:35:26Z
Upstream: https://github.com/cursor/plugins (path `pstack/skills/`)
License: `LICENSES/pstack-MIT.txt` (MIT, copyright (c) 2026 Lauren Tan)

- `create-verification-skill`
- `maintain-verification-skill`
- `principle-prove-it-works`
- `principle-sequence-verifiable-units`
- `principle-test-behavior-not-implementation`

Local deviation, recorded so a re-sync can re-apply it. It changed `create-verification-skill/` (SKILL.md and `references/feature-map-example/`) and `maintain-verification-skill/SKILL.md`. Create adds an `Attack scenarios` H2 to each feature file and a `Report` section to the generated skill. Maintain checks for that section and runs its scenarios. All other vendored files match the pin. Re-applied over upstream d457567 (pstack 0.15.28) on 2026-10-19: upstream's seed-data and stand-in sentences from cursor/plugins#573 are kept inside the deviated paragraphs of `create-verification-skill/SKILL.md`.

`poteto-mode` is not vendored. Upstream's `pstack/skills/poteto-mode/` is a broad methodology skill. This repo's `skills/poteto-mode/` is a routing skill with the same name and different content.

Re-sync: `scripts/update-pstack.sh <40-character-SHA-or-main>`. It replaces each vendored directory whole, which removes the deviation above. Review its printed diff, re-apply the deviation from git history, then update this list.

## no-mistakes

Tag: v1.84.0
Upstream: https://github.com/kunchenguid/no-mistakes (path `skills/`)

- `no-mistakes`

The file matches the upstream tag byte for byte. Update it by replacing the file with the same path at the new tag, then change the tag above.
