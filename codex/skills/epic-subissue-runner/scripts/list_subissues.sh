#!/usr/bin/env bash
set -euo pipefail

epic="${1:-}"
if [[ -z "$epic" ]]; then
  echo "usage: $0 <epic-issue-number-or-url-or-owner/repo#N>" >&2
  exit 2
fi

# ---- 1) GitHub Sub-issues API (primary) ----
url="$(gh issue view "$epic" --json url -q '.url')"
num="$(gh issue view "$epic" --json number -q '.number')"
owner_repo="$(printf '%s' "$url" | sed -E 's|https?://github\.com/([^/]+/[^/]+)/issues/.*|\1|')"
owner="${owner_repo%/*}"
repo="${owner_repo#*/}"

subissues="$(
  gh api -H "Accept: application/vnd.github+json" \
    "repos/${owner}/${repo}/issues/${num}/sub_issues" \
    --paginate --jq '.[] | select(.state=="open") | .html_url' 2>/dev/null || true
)"

if [[ -n "$subissues" ]]; then
  printf '%s\n' "$subissues"
  exit 0
fi

# ---- 2) Fallback: unchecked task list items in the epic body ----
body="$(gh issue view "$epic" --json body -q '.body')"
printf '%s\n' "$body" \
  | awk 'match($0,/^[[:space:]]*[-*+] \[ \] /){print}' \
  | (grep -Eo 'https?://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/issues/[0-9]+|([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)?#[0-9]+' || true) \
  | awk '!seen[$0]++'
