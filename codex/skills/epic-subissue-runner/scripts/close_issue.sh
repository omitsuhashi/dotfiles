#!/usr/bin/env bash
set -euo pipefail

issue_ref="${1:-}"
if [[ -z "$issue_ref" ]]; then
  echo "usage: $0 <issue-number-or-url-or-owner/repo#N>" >&2
  exit 2
fi

# If already closed, be idempotent.
state="$(gh issue view "$issue_ref" --json state -q '.state' 2>/dev/null || true)"
if [[ "$state" == "CLOSED" ]]; then
  exit 0
fi

branch="$(git branch --show-current 2>/dev/null || true)"
head="$(git rev-parse --short HEAD 2>/dev/null || true)"
comment="Done in ${branch:-unknown} @ ${head:-unknown}."

# Close as completed (status=完了)
gh issue close "$issue_ref" -r completed -c "$comment"

