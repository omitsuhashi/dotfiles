# install Prezto
# https://github.com/sorin-ionescu/prezto

export SDKROOT=$(xcrun --show-sdk-path)

export LSCOLORS=gxfxcxdxbxegedabagacad
export LC_ALL='en_US.UTF-8'
export LANG='en_US.UTF-8'

export LDFLAGS="-L/usr/local/opt/openssl/lib"
export CPPFLAGS="-I/usr/local/opt/openssl/include"

export HDF5_DIR=/opt/homebrew/opt/hdf5
export TOOL_DIR=$HOME/.tool

# alias
alias tf='terraform'
alias start-pg='brew services start postgresql@17'
alias stop-pg='brew services stop postgresql@17'
alias git-diff='git diff main...HEAD > combined_changes.patch'


# brew
if [[ $(uname -m) == 'arm64' ]]; then
  eval "$(/opt/homebrew/bin/brew shellenv)"
fi

# nodenv
PATH="$HOME/.nodenv/bin:$PATH"
eval "$(nodenv init -)"

# direnv
eval "$(direnv hook zsh)"

# openjdk
PATH="/opt/homebrew/opt/openjdk/bin:$PATH"

# dart
PATH="$PATH":"$HOME/.pub-cache/bin"

# golang
export GOPATH=$HOME/go
export GOBIN=$GOPATH/bin
PATH="$PATH:$GOBIN"

# rust
PATH="$PATH:$HOME/.cargo/bin"

# flutter
PATH="$PATH:$HOME/.tools/flutter/bin"

# libpq
# TODO remove this and related packages
export LDFLAGS="-L/opt/homebrew/opt/libpq/lib"
export CPPFLAGS="-I/opt/homebrew/opt/libpq/include"
export PKG_CONFIG_PATH="/opt/homebrew/opt/libpq/lib/pkgconfig"
PATH="/opt/homebrew/opt/libpq/bin:$PATH"

# llvm
export LDFLAGS="-L/opt/homebrew/opt/llvm/lib"
export CPPFLAGS="-I/opt/homebrew/opt/llvm/include"
PATH="/opt/homebrew/opt/llvm/bin:$PATH"

export PATH

# Added by OrbStack: command-line tools and integration
# This won't be added again if you remove it.
source ~/.orbstack/shell/init.zsh 2>/dev/null || :

# Setting PATH for Python 3.12
# The original version is saved in .zprofile.pysave
PATH="/Library/Frameworks/Python.framework/Versions/3.12/bin:${PATH}"
export PATH

# hugging-face
# ollama
if [ -d "/Volumes/mac1st2tb/" ]; then
    export HF_HOME="/Volumes/mac1st2tb/huggingface"
    export OLLAMA_MODELS="/Volumes/mac1st2tb/ollama"
else
    export HF_HOME="$HOME"
fi

# scripts
PATH="$HOME/scripts:$PATH"
export PATH

# flutter
export PATH=$HOME/flutter/bin:$PATH

# ffmpeg
export DYLD_LIBRARY_PATH="/opt/homebrew/opt/ffmpeg@7/lib:$DYLD_LIBRARY_PATH"
export PATH="/opt/homebrew/opt/ffmpeg@7/bin:$PATH"

# codex
export CODEX_PROFILE=sandbox
gtr() {
  local branch="$1"; shift || true
  local wt gitdir_abs common_abs
  if [[ -z "$branch" ]]; then
    echo "usage: gtr <branch> [-- codex-args...]" >&2
    return 2
  fi

  wt="$(git gtr go "$branch" 2>/dev/null)" || {
    git gtr new "$branch" --yes || return 1
    wt="$(git gtr go "$branch")" || return 1
  }

  if [[ "$branch" =~ ^epic/([0-9]+)$ ]] \
    && [[ -x "$HOME/.codex/skills/epic-subissue-runner/scripts/ensure_epic_worktree.sh" ]]; then
    local epic_num="${BASH_REMATCH[1]}"
    local remote repo_full epic_ref
    remote="$(git -C "$wt" remote get-url origin 2>/dev/null || true)"
    if [[ -n "$remote" ]]; then
      repo_full="$(printf '%s' "$remote" | sed -E 's#^(https?://github\.com/|git@github\.com:)##; s#\.git$##; s#^([^/]+/[^/]+).*$#\1#')"
    fi
    if [[ -n "${repo_full:-}" ]]; then
      epic_ref="${repo_full}#${epic_num}"
    else
      epic_ref="${epic_num}"
    fi
    bash "$HOME/.codex/skills/epic-subissue-runner/scripts/ensure_epic_worktree.sh" "$epic_ref" >/dev/null || return 1
    wt="$(git gtr go "$branch")" || return 1
  fi

  gitdir_abs="$(cd "$wt" && cd "$(git rev-parse --git-dir)" && pwd -P)" || return 1
  common_abs="$(cd "$wt" && cd "$(git rev-parse --git-common-dir)" && pwd -P)" || return 1

  git gtr ai "$branch" --ai codex -- \
    --sandbox workspace-write \
    --add-dir "$wt" \
    --add-dir "$gitdir_abs" \
    --add-dir "$common_abs" \
    "$@"
}
