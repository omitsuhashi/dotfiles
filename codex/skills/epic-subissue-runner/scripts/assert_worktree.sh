#!/usr/bin/env bash
set -euo pipefail

git rev-parse --show-toplevel >/dev/null 2>&1 || {
  echo "ERROR: not in a git repository" >&2
  exit 2
}

top="$(git rev-parse --show-toplevel)"
# current path must be registered as a worktree
if ! git worktree list --porcelain | awk '$1=="worktree"{print $2}' | grep -Fxq "$top"; then
  echo "ERROR: not inside a git worktree. Start Codex from your epic worktree directory." >&2
  exit 3
fi

# prevent committing on default branch
default_branch="$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}')"
default_branch="${default_branch:-main}"
current_branch="$(git branch --show-current)"

if [[ -z "$current_branch" ]]; then
  echo "ERROR: detached HEAD. Use a branch in your epic worktree." >&2
  exit 4
fi

if [[ "$current_branch" == "$default_branch" ]]; then
  echo "ERROR: on default branch ($default_branch). Switch to epic worktree branch before running." >&2
  exit 5
fi

echo "OK: worktree=$top branch=$current_branch (default=$default_branch)"

