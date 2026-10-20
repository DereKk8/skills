# Vendored skills

Vendored skills keep their upstream bytes, so they carry no `Skill version:` line. Their pin here is the version. `scripts/check-skills.sh` accepts a skill with no version line only when this file names it in a `- \`name\`` entry.

## pstack verification skills

Commit SHA: e43c7ee26e0038c6c1fa8380dd34ce86ff94cb2a
Commit date: 2026-10-04T00:06:48Z
Upstream: https://github.com/cursor/plugins (path `pstack/skills/`)
License: `LICENSES/pstack-MIT.txt` (MIT, copyright (c) 2026 Lauren Tan)

- `create-verification-skill`
- `maintain-verification-skill`
- `principle-prove-it-works`
- `principle-sequence-verifiable-units`
- `principle-test-behavior-not-implementation`

Local deviation, recorded so a re-sync can re-apply it. It changed `create-verification-skill/` (SKILL.md and `references/feature-map-example/`) and `maintain-verification-skill/SKILL.md`. Create adds an `Attack scenarios` H2 to each feature file and a `Report` section to the generated skill. Maintain checks for that section and runs its scenarios. All other vendored files match the pin.

`poteto-mode` is not vendored. Upstream's `pstack/skills/poteto-mode/` is a broad methodology skill. This repo's `skills/poteto-mode/` is a routing skill with the same name and different content.

Re-sync: `scripts/update-pstack.sh <40-character-SHA-or-main>`. It replaces each vendored directory whole, which removes the deviation above. Review its printed diff, re-apply the deviation from git history, then update this list.

## no-mistakes

Tag: v1.84.0
Upstream: https://github.com/kunchenguid/no-mistakes (path `skills/`)

- `no-mistakes`

The file matches the upstream tag byte for byte. Update it by replacing the file with the same path at the new tag, then change the tag above.
