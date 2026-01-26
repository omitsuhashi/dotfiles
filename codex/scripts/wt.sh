#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || { echo "Run inside a git repo"; exit 1; })"
WT_ROOT="${WT_ROOT:-"$REPO_ROOT/../wt"}"

usage() {
  cat <<'USAGE'
wt - git worktree orchestrator

USAGE:
  wt new <task_id> [--agent A] [--base origin/main] [--paths p1,p2,...] [--draft] [--title "PR title"] [--body "PR body"]
  wt ls
  wt rm  <task_id|path>      # PR merge後の撤収
  wt sync <task_id>          # main追従 (rebase)
  wt pr   <task_id> [--ready]# PR作成 or Draft→Ready
  wt gc                      # 孤児worktreeの掃除(安全)

ENV:
  WT_ROOT=<dir>  # default: repo/../wt

NOTES:
  - ブランチ命名: feat/<agent>/<task_id>
  - ディレクトリ: $WT_ROOT/<task_id>
USAGE
}

die(){ echo "ERR: $*" >&2; exit 1; }

wt_mkdir(){ mkdir -p "$WT_ROOT"; }

branch_of() {
  local task="$1" agent="${2:-"agent"}"
  echo "feat/${agent}/${task}"
}

path_of(){ echo "$WT_ROOT/$1"; }

ensure_clean_repo(){
  git -C "$REPO_ROOT" fetch --all --prune
}

cmd_ls(){
  git worktree list
}

cmd_new(){
  [[ $# -ge 1 ]] || die "task_id is required"
  local task="$1"; shift
  local agent="agent"
  local base="origin/main"
  local paths=""
  local draft="no"
  local pr_title="feat: $task"
  local pr_body="Automated by wt for task $task"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --agent) agent="$2"; shift 2;;
      --base)  base="$2"; shift 2;;
      --paths) paths="$2"; shift 2;;
      --draft) draft="yes"; shift;;
      --title) pr_title="$2"; shift 2;;
      --body)  pr_body="$2"; shift 2;;
      *) die "unknown option: $1";;
    esac
  done

  wt_mkdir
  ensure_clean_repo

  local br; br="$(branch_of "$task" "$agent")"
  local wt_dir; wt_dir="$(path_of "$task")"

  # 作成
  git -C "$REPO_ROOT" worktree add -b "$br" "$wt_dir" "$base"

  # sparse-checkout (任意)
  if [[ -n "$paths" ]]; then
    git -C "$wt_dir" sparse-checkout init --cone
    IFS=',' read -ra arr <<< "$paths"
    git -C "$wt_dir" sparse-checkout set "${arr[@]}"
  fi

  # 初回コミット(空でない場合のみ)
  pushd "$wt_dir" >/dev/null
  if [[ -n "$(git status --porcelain)" ]]; then
    git add -A
    git commit -m "chore: initial changes for $task"
  fi
  popd >/dev/null

  # PR（オプション）
  if [[ "$draft" == "yes" ]]; then
    git -C "$wt_dir" push -u origin "$br"
    gh pr create --repo "$(git -C "$REPO_ROOT" config --get remote.origin.url)" \
      --title "$pr_title" --body "$pr_body" --head "$br" --base main --draft
  fi

  echo "OK: worktree created at $wt_dir (branch=$br)"
}

cmd_rm(){
  [[ $# -ge 1 ]] || die "task_id or path is required"
  local target="$1"

  local wt_dir
  if [[ -d "$target" ]]; then wt_dir="$target"; else wt_dir="$(path_of "$target")"; fi
  [[ -d "$wt_dir" ]] || die "not found: $wt_dir"

  # 安全: 未pushコミットがあれば警告
  if git -C "$wt_dir" rev-parse --abbrev-ref @{u} &>/dev/null; then
    :
  else
    echo "WARN: no upstream set; ensure you've pushed your commits." >&2
  fi

  git -C "$REPO_ROOT" worktree remove "$wt_dir"
  echo "OK: removed worktree $wt_dir"
}

cmd_sync(){
  [[ $# -ge 1 ]] || die "task_id is required"
  local task="$1"; shift
  local wt_dir; wt_dir="$(path_of "$task")"
  [[ -d "$wt_dir" ]] || die "not found: $wt_dir"

  git -C "$wt_dir" fetch origin
  git -C "$wt_dir" rebase origin/main || {
    echo "Rebase had conflicts. Resolve in $wt_dir, then 'git rebase --continue' and push." >&2
    exit 2
  }
  echo "OK: rebased $task onto origin/main"
}

cmd_pr(){
  [[ $# -ge 1 ]] || die "task_id is required"
  local task="$1"; shift
  local ready="no"
  local wt_dir; wt_dir="$(path_of "$task")"
  [[ -d "$wt_dir" ]] || die "not found: $wt_dir"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --ready) ready="yes"; shift;;
      *) die "unknown option: $1";;
    esac
  done

  local br; br="$(git -C "$wt_dir" rev-parse --abbrev-ref HEAD)"
  git -C "$wt_dir" push -u origin "$br"

  if gh pr view --json number &>/dev/null; then
    if [[ "$ready" == "yes" ]]; then
      gh pr ready || true
      echo "OK: PR is Ready for Review"
    else
      echo "OK: PR already exists"
    fi
  else
    gh pr create --title "$br" --body "Automated PR for $task" --base main --head "$br" --draft
    echo "OK: Draft PR created"
  fi
}

cmd_gc(){
  # 参照が壊れたworktreeやローカルonlyブランチの掃除（破壊なし）
  git -C "$REPO_ROOT" worktree prune
  echo "OK: pruned stale worktrees"
}

main(){
  local cmd="${1:-}"; shift || true
  case "$cmd" in
    new)  cmd_new "$@";;
    ls)   cmd_ls  "$@";;
    rm)   cmd_rm  "$@";;
    sync) cmd_sync"$@";;
    pr)   cmd_pr  "$@";;
    gc)   cmd_gc  "$@";;
    ""|-h|--help) usage;;
    *) usage; exit 1;;
  esac
}

main "$@"

