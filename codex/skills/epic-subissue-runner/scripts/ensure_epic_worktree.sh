#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE' >&2
ensure_epic_worktree.sh <epic-issue-number-or-url-or-owner/repo#N>

Creates (or reuses) a local clone + git worktree for the given epic issue.
Prints the worktree path to STDOUT (so callers can capture it).

If the epic body specifies a doc submodule pin (SubmodulePins / DependsOn),
this script pins the doc submodule commit and commits the pointer update in
this epic branch.

ENV (optional):
  CODEX_WORKSPACE_ROOT=<dir>   # default: $HOME/repos/the3 if exists, else $HOME/repos, else $HOME/work
  WT_ROOT=<dir>                # default: $CODEX_WORKSPACE_ROOT/wt
USAGE
}

die(){ echo "ERROR: $*" >&2; exit 2; }

normalize_repo_full() {
  # input: https://github.com/owner/repo(.git)? or git@github.com:owner/repo(.git)?
  local u="$1"
  u="$(printf '%s' "$u" | sed -E 's#^(https?://github\.com/|git@github\.com:)##; s#\.git$##')"
  u="$(printf '%s' "$u" | sed -E 's#^([^/]+/[^/]+).*$#\\1#')"
  printf '%s' "$u"
}

extract_section() {
  local body="$1"
  local heading="$2"
  printf '%s\n' "$body" | awk -v h="$heading" '
    BEGIN{in=0}
    $0 ~ "^##[[:space:]]*"h"([[:space:]]|$)" {in=1; next}
    in && $0 ~ "^##[[:space:]]+" {exit}
    in {print}
  '
}

extract_doc_pin_from_body() {
  # stdout: pin string or empty
  local body="$1"

  local pins doc_pin deps
  pins="$(extract_section "$body" "SubmodulePins" || true)"
  doc_pin="$(
    printf '%s\n' "$pins" \
      | sed -nE \
        's/^[[:space:]]*([-*][[:space:]]*)?doc[[:space:]]*=[[:space:]]*([^[:space:]].*)$/\2/p;
         s/^[[:space:]]*([-*][[:space:]]*)?doc[[:space:]]*:[[:space:]]*([^[:space:]].*)$/\2/p' \
      | head -n1
  )"
  if [[ -n "$doc_pin" ]]; then
    printf '%s' "$doc_pin"
    return 0
  fi

  deps="$(extract_section "$body" "DependsOn" || true)"
  mapfile -t dep_urls < <(
    printf '%s\n' "$deps" \
      | sed -nE 's/^[[:space:]]*[-*]?[[:space:]]*(https?:\/\/github\.com\/[^[:space:]]+\/(issues|pull)\/[0-9]+).*/\1/p'
  )
  if (( ${#dep_urls[@]} == 0 )); then
    return 0
  fi
  if (( ${#dep_urls[@]} > 1 )); then
    die "multiple DependsOn URLs found; specify exactly one doc pin via ## SubmodulePins (doc=...)"
  fi
  printf 'url:%s' "${dep_urls[0]}"
}

resolve_doc_target() {
  # input: pin string (issue:123 / pr:456 / branch:xxx / sha:... / url:https://...)
  # stdout: "kind value"
  local pin="$1"

  pin="$(printf '%s' "$pin" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')"

  if [[ "$pin" =~ ^url:(https?://.+)$ ]]; then
    local url="${BASH_REMATCH[1]}"
    if [[ "$url" =~ /issues/([0-9]+)$ ]]; then
      echo "issue ${BASH_REMATCH[1]}"; return 0
    fi
    if [[ "$url" =~ /pull/([0-9]+)$ ]]; then
      echo "pr ${BASH_REMATCH[1]}"; return 0
    fi
    die "unsupported url pin: $url"
  fi

  if [[ "$pin" =~ ^https?:// ]]; then
    resolve_doc_target "url:$pin"; return 0
  fi

  if [[ "$pin" =~ ^issue:([0-9]+)$ ]]; then echo "issue ${BASH_REMATCH[1]}"; return 0; fi
  if [[ "$pin" =~ ^pr:([0-9]+)$ ]]; then echo "pr ${BASH_REMATCH[1]}"; return 0; fi
  if [[ "$pin" =~ ^sha:([0-9a-fA-F]{7,40})$ ]]; then echo "sha ${BASH_REMATCH[1]}"; return 0; fi
  if [[ "$pin" =~ ^branch:(.+)$ ]]; then echo "branch ${BASH_REMATCH[1]}"; return 0; fi

  if [[ "$pin" =~ ^[0-9]+$ ]]; then echo "issue $pin"; return 0; fi
  if [[ "$pin" =~ ^epic/[0-9]+$ ]]; then echo "branch $pin"; return 0; fi

  echo "branch $pin"
}

pin_doc_submodule_from_epic() {
  local wt_dir="$1"
  local epic_ref="$2"

  [[ -f "$wt_dir/.gitmodules" ]] || return 0

  local doc_url
  doc_url="$(git -C "$wt_dir" config -f .gitmodules --get submodule.doc.url 2>/dev/null || true)"
  [[ -n "$doc_url" ]] || return 0
  [[ -d "$wt_dir/doc" ]] || return 0

  local body pin
  body="$(gh issue view "$epic_ref" --json body -q '.body')"
  pin="$(extract_doc_pin_from_body "$body" || true)"
  [[ -n "$pin" ]] || return 0

  if [[ "$pin" =~ ^url:(https?://.+)$ ]]; then
    local pin_repo
    pin_repo="$(normalize_repo_full "${BASH_REMATCH[1]}")"
    local doc_repo
    doc_repo="$(normalize_repo_full "$doc_url")"
    if [[ "$pin_repo" != "$doc_repo" ]]; then
      die "DependsOn repo does not match doc submodule: $pin_repo != $doc_repo"
    fi
  fi

  local kind value
  read -r kind value < <(resolve_doc_target "$pin")

  local doc_dir="$wt_dir/doc"
  if [[ -n "$(git -C "$doc_dir" status --porcelain)" ]]; then
    die "doc submodule has local changes; commit/stash before pinning (path=$doc_dir)"
  fi

  git -C "$doc_dir" fetch --all --prune >/dev/null

  local target_sha desc
  case "$kind" in
    issue)
      local branch="epic/$value"
      if ! git -C "$doc_dir" fetch origin "$branch" >/dev/null 2>&1; then
        die "doc branch not found on origin: $branch (create it on GitHub first)"
      fi
      target_sha="$(git -C "$doc_dir" rev-parse FETCH_HEAD)"
      desc="issue#$value($branch)"
      ;;
    pr)
      if ! git -C "$doc_dir" fetch origin "refs/pull/$value/head" >/dev/null 2>&1; then
        die "failed to fetch PR head: pr#$value"
      fi
      target_sha="$(git -C "$doc_dir" rev-parse FETCH_HEAD)"
      desc="pr#$value"
      ;;
    branch)
      if ! git -C "$doc_dir" fetch origin "$value" >/dev/null 2>&1; then
        die "doc branch not found on origin: $value (create it on GitHub first)"
      fi
      target_sha="$(git -C "$doc_dir" rev-parse FETCH_HEAD)"
      desc="branch:$value"
      ;;
    sha)
      if ! git -C "$doc_dir" cat-file -e "$value^{commit}" >/dev/null 2>&1; then
        die "doc sha not found locally after fetch --all: $value"
      fi
      target_sha="$value"
      desc="sha:$value"
      ;;
    *)
      die "unsupported doc pin kind: $kind"
      ;;
  esac

  git -C "$doc_dir" checkout --detach "$target_sha" >/dev/null
  git -C "$wt_dir" add doc
  if ! git -C "$wt_dir" diff --cached --quiet; then
    git -C "$wt_dir" commit -m "chore(doc): pin submodule to $desc (${target_sha:0:7})" >/dev/null
  fi
}

epic_ref="${1:-}"
[[ -n "$epic_ref" ]] || { usage; exit 2; }

command -v gh >/dev/null 2>&1 || die "`gh` not found"
command -v git >/dev/null 2>&1 || die "`git` not found"
gh auth status >/dev/null 2>&1 || die "`gh` not authenticated (run: gh auth login)"

WORKSPACE_ROOT="${CODEX_WORKSPACE_ROOT:-}"
if [[ -z "$WORKSPACE_ROOT" ]]; then
  if [[ -d "$HOME/repos/the3" ]]; then
    WORKSPACE_ROOT="$HOME/repos/the3"
  elif [[ -d "$HOME/repos" ]]; then
    WORKSPACE_ROOT="$HOME/repos"
  else
    WORKSPACE_ROOT="$HOME/work"
  fi
fi
WT_ROOT="${WT_ROOT:-"$WORKSPACE_ROOT/wt"}"

# Resolve epic to owner/repo + issue number
url="$(gh issue view "$epic_ref" --json url -q '.url')"
num="$(gh issue view "$epic_ref" --json number -q '.number')"
owner_repo="$(printf '%s' "$url" | sed -E 's|https?://github\.com/([^/]+/[^/]+)/issues/.*|\1|')"
owner="${owner_repo%/*}"
repo="${owner_repo#*/}"
repo_full="${owner}/${repo}"

branch="epic/${num}"
wt_dir="${WT_ROOT}/${owner}-${repo}/epic-${num}"

# Candidate base repo dir:
base_dir=""

# 1) If we are already inside the right repo, reuse it.
if git rev-parse --show-toplevel >/dev/null 2>&1; then
  top="$(git rev-parse --show-toplevel)"
  remote="$(git -C "$top" remote get-url origin 2>/dev/null || true)"
  if [[ -n "$remote" ]]; then
    norm="$(normalize_repo_full "$remote")"
    if [[ "$norm" == "$repo_full" ]]; then
      base_dir="$top"
    fi
  fi
fi

# 2) Typical locations under workspace root.
if [[ -z "$base_dir" ]]; then
  for cand in \
    "$WORKSPACE_ROOT/$repo" \
    "$WORKSPACE_ROOT/$owner/$repo" \
    "$WORKSPACE_ROOT/src/$repo"
  do
    if [[ -d "$cand/.git" ]]; then
      base_dir="$cand"
      break
    fi
  done
fi

# 3) Clone if missing.
if [[ -z "$base_dir" ]]; then
  base_dir="$WORKSPACE_ROOT/$repo"
  mkdir -p "$(dirname "$base_dir")"
  gh repo clone "$repo_full" "$base_dir" >/dev/null
fi

# Refresh refs + detect default branch
git -C "$base_dir" fetch --all --prune >/dev/null
default_branch="$(git -C "$base_dir" remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}')"
default_branch="${default_branch:-main}"

# Prune stale worktrees (idempotent)
git -C "$base_dir" worktree prune >/dev/null || true

# Branch must exist on origin (branch creation happens on GitHub)
if ! git -C "$base_dir" show-ref --verify --quiet "refs/remotes/origin/$branch"; then
  die "epic branch not found on origin: $branch (create it on GitHub first)"
fi

# If branch already checked out somewhere, reuse that worktree path.
existing_wt="$(
  git -C "$base_dir" worktree list --porcelain \
    | awk -v target="refs/heads/$branch" '
        $1=="worktree"{wt=$2}
        $1=="branch" && $2==target {print wt}
      ' \
    | head -n1
)"
if [[ -n "$existing_wt" ]]; then
  wt_dir="$existing_wt"
else
  # Guard: if directory exists but is not registered as a worktree, refuse.
  if [[ -d "$wt_dir" ]]; then
    if ! git -C "$base_dir" worktree list --porcelain | awk '$1=="worktree"{print $2}' | grep -Fxq "$wt_dir"; then
      die "path exists but is not a registered worktree: $wt_dir"
    fi
  else
    mkdir -p "$(dirname "$wt_dir")"
  fi

  # Create or attach the worktree.
  if git -C "$base_dir" show-ref --verify --quiet "refs/heads/$branch"; then
    git -C "$base_dir" worktree add "$wt_dir" "$branch" >/dev/null
  else
    git -C "$base_dir" worktree add -b "$branch" "$wt_dir" "origin/$branch" >/dev/null
  fi
fi

# Ensure submodules (doc/ etc.)
if [[ -f "$wt_dir/.gitmodules" ]]; then
  git -C "$wt_dir" submodule sync --recursive >/dev/null || true
  git -C "$wt_dir" submodule update --init --recursive
fi

# Pin doc submodule if epic requests it
pin_doc_submodule_from_epic "$wt_dir" "$epic_ref"

echo "$wt_dir"
