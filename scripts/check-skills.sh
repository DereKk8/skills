#!/usr/bin/env bash
# Check the skill catalog: layout, names, version lines, version rises, and path rules.
# Run it with BASE=HEAD before a commit (it then sees pending edits), and in CI with BASE=origin/<base>.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"
base="${BASE:-origin/main}"
errors=0
fail() { echo "FAIL: $*" >&2; errors=$((errors + 1)); }

git rev-parse --verify -q "$base" >/dev/null || { echo "Base ref $base not found; fetch it or set BASE." >&2; exit 1; }
# Compare against the fork point, so a base that advanced on its own does not count as a change here.
fork="$(git merge-base "$base" HEAD)"

# Print the version on the line right after the frontmatter of a SKILL.md read from stdin.
version_of() {
  awk '
    NR == 1 { if ($0 != "---") exit; next }
    !closed && $0 == "---" { closed = 1; if ((getline nxt) > 0 && nxt ~ /^Skill version: [0-9]+\.[0-9]+\.[0-9]+$/) { sub(/^Skill version: /, "", nxt); print nxt } exit }
  '
}

# A top-level folder is runtime-owned when git ignores it and tracks nothing under it.
runtime_owned() {
  [[ -z "$(git ls-files -- "$1")" ]] && git check-ignore -q -- "$1"
}

if [[ -n "$(git ls-files -s skills | awk '$1 == "120000"')" ]]; then
  fail "tracked symlink under skills/"
fi

vendored_names="$(sed -n 's/^- `\([^`]*\)`.*/\1/p' VENDORED.md)"
changed_names="$(git diff --name-only "$fork" -- skills; git ls-files --others --exclude-standard -- skills)"

# Succeeds when the changed-path list has a path under the given folder.
changed_under() {
  awk -v prefix="$1/" 'index($0, prefix) == 1 { found = 1 } END { exit !found }' <<<"$changed_names"
}

# Every entry under skills/, including dot-prefixed names such as ..hidden.
while IFS= read -r -d '' entry; do
  if [[ -L "$entry" ]]; then fail "$entry is a symlink"; continue; fi
  runtime_owned "$entry" && continue
  if [[ ! -d "$entry" ]]; then fail "$entry is not a skill folder"; continue; fi
  if [[ -n "$(find "$entry" -type l)" ]]; then fail "symlink inside $entry"; fi
  if [[ -n "$(find "$entry" -mindepth 2 -name SKILL.md)" ]]; then fail "nested SKILL.md under $entry"; fi

  name="$(basename "$entry")"
  file="$entry/SKILL.md"
  [[ -f "$file" ]] || { fail "$name has no SKILL.md"; continue; }

  fm_name="$(sed -n '2,/^---$/p' "$file" | sed -n 's/^name: *//p' | head -1 | tr -d "\"'")"
  [[ "$fm_name" == "$name" ]] || fail "$file frontmatter name '$fm_name' != folder '$name'"

  version="$(version_of < "$file")"
  if [[ -z "$version" ]]; then
    grep -qxF "$name" <<<"$vendored_names" || fail "$name has no 'Skill version:' line right after the frontmatter and no VENDORED.md entry"
    continue
  fi

  # Any change under the folder (SKILL.md, scripts, references, probes), committed or pending, needs a raised version.
  changed_under "$entry" || continue
  base_version="$(git show "$fork:$file" 2>/dev/null | version_of || true)"
  base_version="${base_version:-0.0.0}"
  highest="$(printf '%s\n%s\n' "$base_version" "$version" | sort -V | tail -1)"
  [[ "$version" != "$base_version" && "$highest" == "$version" ]] || fail "$name changed but version $version does not rise above $base_version"
done < <(find skills -mindepth 1 -maxdepth 1 -print0)

# Path rules: no reference to the old configs paths, and no category-folder route to a skill.
if git grep -n -e 'configs/'"skills" -e 'configs/'"pstack" -- . ':!scripts/check-skills.sh'; then
  fail "tracked files still reference the old configs skill or pstack paths"
fi
if hits="$(git grep -nE '(^|[^A-Za-z0-9_./-])(engineering|tools|thinking|meta)/[A-Za-z0-9_.-]+' -- skills || true)" && [[ -n "$hits" ]]; then
  fail "skill text routes to a removed category folder:"$'\n'"$hits"
fi

if (( errors > 0 )); then
  echo "$errors check(s) failed." >&2
  exit 1
fi
echo "Skill catalog checks passed."
