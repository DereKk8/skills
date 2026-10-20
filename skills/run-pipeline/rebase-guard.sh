#!/usr/bin/env bash
# rebase-guard.sh — deterministic diagnosis of the no-mistakes rebase step.
#
# The pipeline's rebase step sometimes rebases onto a STALE merge-base and replays
# the base branch's commits onto the feature branch with new SHAs. Same content,
# divergent history -> GitHub reports the PR `dirty` with FALSE conflicts.
#
# This script decides — with git patch-id equivalence, not judgement — whether the
# feature branch is CLEAN, STALE (needs rebase), DUPLICATED (rebase misfired), or has
# a REAL conflict. It prints a single VERDICT line and an exact remedy. With --fix it
# performs the safe remedy automatically.
#
# Usage:
#   rebase-guard.sh [--base <branch>] [--feature <branch>] [--fix]
#   Defaults: base=dev, feature=current branch.
#
# Exit codes: 0 CLEAN | 10 STALE | 20 DUPLICATED | 30 REAL_CONFLICT | 2 usage/error
set -euo pipefail

BASE="dev"
FEATURE=""
FIX=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --base) BASE="$2"; shift 2 ;;
    --feature) FEATURE="$2"; shift 2 ;;
    --fix) FIX=1; shift ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
[[ -z "$FEATURE" ]] && FEATURE="$(git rev-parse --abbrev-ref HEAD)"
[[ "$FEATURE" == "HEAD" ]] && { echo "detached HEAD; pass --feature" >&2; exit 2; }

echo "== rebase-guard: base=$BASE feature=$FEATURE =="
git fetch -q origin "$BASE" "$FEATURE" 2>/dev/null || git fetch -q origin "$BASE" || true
BASEREF="origin/$BASE"
# Prefer the remote feature head (that's what the PR actually is); fall back to local.
if git rev-parse -q --verify "origin/$FEATURE" >/dev/null; then
  PRHEAD="origin/$FEATURE"
else
  PRHEAD="$FEATURE"
fi

# Patch-id equivalence (the deterministic core):
#   dup           = base commits re-applied into the feature branch (duplication bug)
#   base_missing  = base commits ABSENT from the feature branch (staleness)
dup=$(git cherry "$BASEREF" "$PRHEAD" 2>/dev/null | grep -c '^-' || true)
base_missing=$(git cherry "$PRHEAD" "$BASEREF" 2>/dev/null | grep -c '^+' || true)
ahead=$(git rev-list --count "$BASEREF..$PRHEAD")

# Real-conflict probe: merge-tree exits non-zero and lists conflicts if a true
# 3-way merge of feature into base would conflict.
conflict=0
if ! git merge-tree --write-tree "$BASEREF" "$PRHEAD" >/tmp/rg_mt.$$ 2>/dev/null; then
  conflict=1
fi
rm -f /tmp/rg_mt.$$

echo "   commits ahead of base : $ahead"
echo "   duplicated base commits: $dup   (patch-id matches already in $BASE)"
echo "   base commits missing   : $base_missing   (staleness)"
echo "   real merge conflict    : $([[ $conflict -eq 1 ]] && echo yes || echo no)"

# ---- Verdict ---------------------------------------------------------------
if [[ $conflict -eq 1 && $dup -eq 0 ]]; then
  echo "VERDICT: REAL_CONFLICT"
  echo "RECOMMEND: genuine conflict with $BASE. Do NOT skip rebase. Rebase and resolve by hand:"
  echo "  git rebase $BASEREF $FEATURE   # resolve conflicts, then force-push"
  exit 30
fi

if [[ $dup -gt 0 ]]; then
  echo "VERDICT: DUPLICATED"
  echo "RECOMMEND: the rebase step misfired ($dup base commits re-applied). Collapse to one"
  echo "           clean commit on the CURRENT base tip, then rerun with --skip=ci,rebase."
  if [[ $base_missing -gt 0 ]]; then
    echo "NOTE: base also has $base_missing commit(s) the branch lacks — a plain reset --soft would"
    echo "      REVERT them. A real rebase is required first:"
    echo "  git rebase $BASEREF $FEATURE   # brings base changes in; resolve any real conflicts"
    echo "  then re-run this guard with --fix."
    exit 20
  fi
  if [[ $FIX -eq 1 ]]; then
    echo "-- applying safe collapse (tree is preserved byte-for-byte; only history is linearized) --"
    msg="$(git log -1 --format='%s' "$PRHEAD")"
    git checkout -q "$FEATURE"
    git reset --hard -q "$PRHEAD"      # ensure local == real PR head
    git reset --soft -q "$BASEREF"     # reparent identical tree onto current base
    git commit -q -m "$msg"
    echo "collapsed -> $(git rev-parse --short HEAD) (parent $(git rev-parse --short HEAD^) = $BASE)"
    echo "PUSH: git push --force-with-lease origin $FEATURE"
    echo "RERUN: no-mistakes rerun --skip=ci,rebase"
  else
    echo "FIX: re-run with --fix to collapse automatically, or manually:"
    echo "  git reset --hard $PRHEAD && git reset --soft $BASEREF && git commit && git push --force-with-lease"
  fi
  exit 20
fi

if [[ $base_missing -gt 0 ]]; then
  echo "VERDICT: STALE"
  echo "RECOMMEND: branch is behind $BASE by $base_missing commit(s), no duplication. Rebase is"
  echo "           NEEDED — do NOT skip it. Let the pipeline rebase, or: git rebase $BASEREF $FEATURE"
  exit 10
fi

echo "VERDICT: CLEAN"
echo "RECOMMEND: branch is current with $BASE and free of duplicates. Do nothing; do NOT skip rebase."
exit 0
