#!/usr/bin/env bash
# config-sync: stage explicit ~/configs paths, review, commit, and push
set -euo pipefail

CONFIGS_DIR="${HOME}/configs"

usage() {
  printf 'Usage: %s "<commit message>" <intended-path> [<intended-path> ...]\n' "$0" >&2
}

if (( $# < 2 )); then
  usage
  echo "Refusing to continue: provide a commit message and at least one intended path." >&2
  exit 1
fi

commit_msg=$1
shift
intended_paths=("$@")

if [[ -z $commit_msg ]]; then
  echo "Refusing to continue: commit message must not be empty." >&2
  exit 1
fi

cd "$CONFIGS_DIR"

if [[ -n $(git diff --cached --name-only) ]]; then
  echo "Refusing to continue: the index already contains staged changes." >&2
  echo "Review or unstage them before using this helper." >&2
  git status --short >&2
  exit 1
fi

for path in "${intended_paths[@]}"; do
  if [[ -z $path || $path == /* || $path == . || $path == .. || $path == ../* || $path == */../* || $path == */.. || $path == .git || $path == .git/* ]]; then
    printf 'Refusing unsafe path: %q\n' "$path" >&2
    exit 1
  fi
done

git add -- "${intended_paths[@]}"

if git diff --cached --quiet; then
  echo "Nothing staged from the intended paths; no commit created."
  exit 0
fi

echo "=== Staged diff ==="
git diff --cached --check
git diff --cached

echo "=== Repository status ==="
git status --short

git commit -m "$commit_msg"

echo "=== Pushing current branch ==="
git push

echo "=== Done ==="
