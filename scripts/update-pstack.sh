#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
upstream=https://github.com/cursor/plugins.git
requested="${1:-main}"

if [[ "$requested" == main ]]; then
  revision="$(git ls-remote --refs "$upstream" refs/heads/main | awk 'NR == 1 {print $1}')"
  [[ -n "$revision" ]] || { echo "Could not resolve cursor/plugins main" >&2; exit 1; }
elif [[ "$requested" =~ ^[0-9a-fA-F]{40}$ ]]; then
  revision="$requested"
else
  echo "Usage: $0 [main|<40-character-commit-SHA>]" >&2
  exit 2
fi

skills=(
  create-verification-skill
  maintain-verification-skill
  principle-prove-it-works
  principle-test-behavior-not-implementation
  principle-sequence-verifiable-units
  bro
)

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/repo" "$tmp/incoming"
git -C "$tmp/repo" init --quiet
git -C "$tmp/repo" fetch --quiet --depth=1 "$upstream" "$revision"
revision="$(git -C "$tmp/repo" rev-parse FETCH_HEAD)"
commit_epoch="$(git -C "$tmp/repo" show -s --format=%ct "$revision")"
commit_date="$(date -u -d "@$commit_epoch" +%Y-%m-%dT%H:%M:%SZ)"
upstream_paths=(pstack/LICENSE)
for skill in "${skills[@]}"; do
  upstream_paths+=("pstack/skills/$skill")
done
git -C "$tmp/repo" archive --format=tar "$revision" "${upstream_paths[@]}" | tar -xf - -C "$tmp/incoming"

printf 'Upstream diff for cursor/plugins %s (%s):\n' "$revision" "$commit_date"
for skill in "${skills[@]}"; do
  diff -ru "$repo_root/skills/$skill" "$tmp/incoming/pstack/skills/$skill" || true
done
diff -u "$repo_root/LICENSES/pstack-MIT.txt" "$tmp/incoming/pstack/LICENSE" || true

for skill in "${skills[@]}"; do
  if ! diff -qr "$repo_root/skills/$skill" "$tmp/incoming/pstack/skills/$skill" >/dev/null; then
    rm -rf "$repo_root/skills/$skill"
    cp -a "$tmp/incoming/pstack/skills/$skill" "$repo_root/skills/$skill"
  fi
done
cp -a "$tmp/incoming/pstack/LICENSE" "$repo_root/LICENSES/pstack-MIT.txt"

sed -i \
  -e "s/^Commit SHA: .*/Commit SHA: $revision/" \
  -e "s/^Commit date: .*/Commit date: $commit_date/" \
  "$repo_root/VENDORED.md"

printf 'Synced the vendored pstack skills and LICENSE from %s. Review the diff above and re-apply the deviations in VENDORED.md.\n' "$revision"
