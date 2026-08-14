#
# Executes commands at the start of an interactive session.
#
# Authors:
#   Sorin Ionescu <sorin.ionescu@gmail.com>
#

# Make Homebrew-provided completion functions visible before Prezto runs compinit.
if [[ -d /opt/homebrew/share/zsh/site-functions ]]; then
  fpath=(/opt/homebrew/share/zsh/site-functions $fpath)
fi

_dotfiles_source_if_file() {
  local file="$1"
  [[ -f "$file" ]] || return 0
  source "$file"
}

_dotfiles_path_prepend_if_dir() {
  local dir="$1"
  path=(${path:#$dir})
  [[ -d "$dir" ]] || {
    export PATH
    return 0
  }
  path=("$dir" ${path:#$dir})
  export PATH
}

_dotfiles_path_append_if_dir() {
  local dir="$1"
  path=(${path:#$dir})
  [[ -d "$dir" ]] || {
    export PATH
    return 0
  }
  path=(${path:#$dir} "$dir")
  export PATH
}

# Source Prezto.
if [[ -s "${ZDOTDIR:-$HOME}/.zprezto/init.zsh" ]]; then
  source "${ZDOTDIR:-$HOME}/.zprezto/init.zsh"
fi

# Customize to your needs...
_dotfiles_source_if_file "/Users/omitsuhashi/google-cloud-sdk/path.zsh.inc"

# The next line updates PATH for the Google Cloud SDK.
# The next line enables shell command completion for gcloud.
_dotfiles_source_if_file "/Users/omitsuhashi/google-cloud-sdk/completion.zsh.inc"

# Added by LM Studio CLI (lms)
_dotfiles_path_append_if_dir "/Users/omitsuhashi/.lmstudio/bin"

# pnpm
export PNPM_HOME="/Users/omitsuhashi/Library/pnpm"
_dotfiles_path_prepend_if_dir "$PNPM_HOME"
# pnpm end

# Added by Antigravity
_dotfiles_path_prepend_if_dir "/Users/omitsuhashi/.antigravity/antigravity/bin"

# Remove all git worktrees except current working directory.
# Missing/broken worktree paths are pruned so one bad entry cannot stop the loop.
wt-clean() {
  local wt current
  current="$(pwd -P 2>/dev/null || pwd)"

  git worktree list --porcelain \
    | awk '/^worktree /{print substr($0, 10)}' \
    | while IFS= read -r wt; do
        [ -n "$wt" ] || continue
        [ "$wt" = "$current" ] && continue

        if [ ! -e "$wt" ]; then
          printf 'wt-clean: pruning missing worktree %s\n' "$wt" >&2
          git worktree prune -v || true
          continue
        fi

        if ! git worktree remove -f -- "$wt" 2>/dev/null; then
          printf 'wt-clean: remove failed for %s; pruning\n' "$wt" >&2
          git worktree prune -v || true
        fi
      done
}

# Remove all local branches except main and develop.
branch-clean() {
  local branch

  git switch main || return 1

  git for-each-ref --format='%(refname:short)' refs/heads/ \
    | while IFS= read -r branch; do
        case "$branch" in
          main|develop) ;;
          *) git branch -D -- "$branch" ;;
        esac
      done
}

# Open one localhost-bound SSH local port forward in the foreground.
ssh-tunnel() {
  if (( $# != 3 )); then
    print -u2 -- 'usage: ssh-tunnel <ssh-host> <target-ipv4> <local-port>:<target-port>'
    return 2
  fi

  local ssh_host="$1"
  local target_ipv4="$2"
  local port_mapping="$3"
  local local_port target_port octet
  local -a ipv4_octets

  if [[ -z "$ssh_host" || "$ssh_host" == -* ]]; then
    print -u2 -- "ssh-tunnel: invalid SSH destination: $ssh_host"
    return 2
  fi

  if [[ "$target_ipv4" != <->.<->.<->.<-> ]]; then
    print -u2 -- "ssh-tunnel: invalid target IPv4 address: $target_ipv4"
    return 2
  fi

  ipv4_octets=("${(@s:.:)target_ipv4}")
  for octet in "${ipv4_octets[@]}"; do
    if (( ${#octet} > 3 )); then
      print -u2 -- "ssh-tunnel: invalid target IPv4 address: $target_ipv4"
      return 2
    fi
    if (( 10#$octet > 255 )); then
      print -u2 -- "ssh-tunnel: invalid target IPv4 address: $target_ipv4"
      return 2
    fi
  done

  if [[ "$port_mapping" != <->:<-> ]]; then
    print -u2 -- "ssh-tunnel: invalid port mapping: $port_mapping"
    return 2
  fi

  local_port="${port_mapping%%:*}"
  target_port="${port_mapping#*:}"
  if (( ${#local_port} > 5 || ${#target_port} > 5 )); then
    print -u2 -- "ssh-tunnel: invalid port mapping: $port_mapping"
    return 2
  fi
  if (( 10#$local_port < 1 || 10#$local_port > 65535 \
    || 10#$target_port < 1 || 10#$target_port > 65535 )); then
    print -u2 -- "ssh-tunnel: invalid port mapping: $port_mapping"
    return 2
  fi

  ssh -N \
    -o ExitOnForwardFailure=yes \
    -L "127.0.0.1:${local_port}:${target_ipv4}:${target_port}" \
    "$ssh_host"
}

# bun completions
_dotfiles_source_if_file "/Users/omitsuhashi/.bun/_bun"

# bun
export BUN_INSTALL="$HOME/.bun"
_dotfiles_path_prepend_if_dir "$BUN_INSTALL/bin"

# Hermes Agent — ensure ~/.local/bin is on PATH
export PATH="$HOME/.local/bin:$PATH"
