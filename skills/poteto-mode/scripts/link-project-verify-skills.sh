#!/usr/bin/env bash
set -u

usage() {
  echo "Usage: $0 [--check] <repo-root>" >&2
  exit 2
}

check=0
if [[ "${1:-}" == --check ]]; then
  check=1
  shift
fi
[[ $# -eq 1 && -d "$1" ]] || usage
repo_root="$(cd -- "$1" && pwd -P)"

shopt -s nullglob
skills=("$repo_root"/.cursor/skills/verify-*/)
if [[ ${#skills[@]} -eq 0 ]]; then
  echo "No project .cursor/skills/verify-* skills found in $repo_root."
  exit 0
fi
for path in "$repo_root/.cursor" "$repo_root/.cursor/skills"; do
  if [[ -L "$path" || ( -e "$path" && ! -d "$path" ) ]]; then
    printf 'invalid: %s must be a real directory\n' "$path" >&2
    exit 1
  fi
done

failed=0
claude_ready=1
agents_ready=1

ensure_directory() {
  local path=$1 label=$2
  if [[ -L "$path" ]]; then
    printf 'conflict: %s is a symlink; leaving it unchanged\n' "$label" >&2
    return 1
  fi
  if [[ -e "$path" ]]; then
    if [[ -d "$path" ]]; then
      return 0
    fi
    printf 'conflict: %s exists but is not a directory; leaving it unchanged\n' "$label" >&2
    return 1
  fi
  if [[ $check -eq 1 ]]; then
    printf 'missing: %s\n' "$label" >&2
    return 1
  fi
  if mkdir -- "$path"; then
    return 0
  fi
  printf 'error: could not create %s\n' "$label" >&2
  return 1
}

if ! ensure_directory "$repo_root/.claude" '.claude'; then
  claude_ready=0
  failed=1
fi
if [[ $claude_ready -eq 1 ]] && ! ensure_directory "$repo_root/.claude/skills" '.claude/skills'; then
  claude_ready=0
  failed=1
fi
if ! ensure_directory "$repo_root/.agents" '.agents'; then
  agents_ready=0
  failed=1
fi
if [[ $agents_ready -eq 1 ]] && ! ensure_directory "$repo_root/.agents/skills" '.agents/skills'; then
  agents_ready=0
  failed=1
fi

link_skill() {
  local destination=$1 relative_target=$2 label=$3
  if [[ -L "$destination" ]]; then
    local actual
    actual="$(readlink -- "$destination")"
    if [[ "$actual" == "$relative_target" ]]; then
      printf 'ok: %s -> %s\n' "$label" "$actual"
      return 0
    fi
    printf 'conflict: %s points to %s, expected %s; leaving it unchanged\n' "$label" "$actual" "$relative_target" >&2
    failed=1
    return 1
  fi
  if [[ -e "$destination" ]]; then
    printf 'conflict: %s already exists and is not the expected symlink; leaving it unchanged\n' "$label" >&2
    failed=1
    return 1
  fi
  if [[ $check -eq 1 ]]; then
    printf 'missing: %s -> %s\n' "$label" "$relative_target" >&2
    failed=1
    return 1
  fi
  if ln -sT -- "$relative_target" "$destination"; then
    printf 'linked: %s -> %s\n' "$label" "$relative_target"
  else
    printf 'error: could not create %s\n' "$label" >&2
    failed=1
    return 1
  fi
}

for skill_path in "${skills[@]}"; do
  skill_path=${skill_path%/}
  skill_name=${skill_path##*/}
  if [[ -L "$skill_path" || ! -d "$skill_path" || ! -f "$skill_path/SKILL.md" ]]; then
    printf 'invalid: %s must be a real directory containing SKILL.md\n' "$skill_path" >&2
    failed=1
    continue
  fi
  relative_target="../../.cursor/skills/$skill_name"
  if [[ $claude_ready -eq 1 ]]; then
    link_skill "$repo_root/.claude/skills/$skill_name" "$relative_target" ".claude/skills/$skill_name" || true
  fi
  if [[ $agents_ready -eq 1 ]]; then
    link_skill "$repo_root/.agents/skills/$skill_name" "$relative_target" ".agents/skills/$skill_name" || true
  fi
done

exit "$failed"
