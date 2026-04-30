# install Prezto
# https://github.com/sorin-ionescu/prezto

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

if command -v xcrun >/dev/null 2>&1; then
  export SDKROOT="$(xcrun --show-sdk-path)"
fi

export LSCOLORS=gxfxcxdxbxegedabagacad
export LC_ALL='en_US.UTF-8'
export LANG='en_US.UTF-8'

if [[ -d /usr/local/opt/openssl/lib ]]; then
  export LDFLAGS="-L/usr/local/opt/openssl/lib"
fi
if [[ -d /usr/local/opt/openssl/include ]]; then
  export CPPFLAGS="-I/usr/local/opt/openssl/include"
fi

if [[ -d /opt/homebrew/opt/hdf5 ]]; then
  export HDF5_DIR=/opt/homebrew/opt/hdf5
else
  unset HDF5_DIR
fi
export TOOL_DIR=$HOME/.tool

# alias
alias tf='terraform'
alias start-pg='brew services start postgresql@17'
alias stop-pg='brew services stop postgresql@17'
alias git-diff='git diff main...HEAD > combined_changes.patch'

# brew
if [[ "$(uname -m)" == 'arm64' && -x /opt/homebrew/bin/brew ]]; then
  eval "$(/opt/homebrew/bin/brew shellenv)"
fi

# Drop stale nodenv entries if they were inherited from a parent process.
path=(${path:#$HOME/.nodenv/bin} ${path:#$HOME/.nodenv/shims})
export PATH

# direnv
if command -v direnv >/dev/null 2>&1; then
  eval "$(direnv hook zsh)"
fi

# openjdk
_dotfiles_path_prepend_if_dir "/opt/homebrew/opt/openjdk/bin"

# dart
_dotfiles_path_append_if_dir "$HOME/.pub-cache/bin"

# golang
export GOPATH=$HOME/go
export GOBIN=$GOPATH/bin
_dotfiles_path_append_if_dir "$GOBIN"

# rust
_dotfiles_path_append_if_dir "$HOME/.cargo/bin"

# flutter
_dotfiles_path_append_if_dir "$HOME/.tools/flutter/bin"

# libpq
# TODO remove this and related packages
if [[ -d /opt/homebrew/opt/libpq/lib ]]; then
  export LDFLAGS="-L/opt/homebrew/opt/libpq/lib"
fi
if [[ -d /opt/homebrew/opt/libpq/include ]]; then
  export CPPFLAGS="-I/opt/homebrew/opt/libpq/include"
fi
if [[ -d /opt/homebrew/opt/libpq/lib/pkgconfig ]]; then
  export PKG_CONFIG_PATH="/opt/homebrew/opt/libpq/lib/pkgconfig"
fi
_dotfiles_path_prepend_if_dir "/opt/homebrew/opt/libpq/bin"

# llvm
if [[ -d /opt/homebrew/opt/llvm/lib ]]; then
  export LDFLAGS="-L/opt/homebrew/opt/llvm/lib"
fi
if [[ -d /opt/homebrew/opt/llvm/include ]]; then
  export CPPFLAGS="-I/opt/homebrew/opt/llvm/include"
fi
_dotfiles_path_prepend_if_dir "/opt/homebrew/opt/llvm/bin"

export PATH

# Added by OrbStack: command-line tools and integration
# This won't be added again if you remove it.
_dotfiles_source_if_file "$HOME/.orbstack/shell/init.zsh"

# Setting PATH for Python 3.12
# The original version is saved in .zprofile.pysave
_dotfiles_path_prepend_if_dir "/Library/Frameworks/Python.framework/Versions/3.12/bin"
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
_dotfiles_path_prepend_if_dir "$HOME/scripts"
export PATH

# flutter
_dotfiles_path_prepend_if_dir "$HOME/flutter/bin"

# ffmpeg
if [[ -d /opt/homebrew/opt/ffmpeg@7/lib ]]; then
  export DYLD_LIBRARY_PATH="/opt/homebrew/opt/ffmpeg@7/lib:$DYLD_LIBRARY_PATH"
fi
_dotfiles_path_prepend_if_dir "/opt/homebrew/opt/ffmpeg@7/bin"

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

# nvm
export NVM_DIR="$HOME/.nvm"
_dotfiles_source_if_file "/opt/homebrew/opt/nvm/nvm.sh"  # This loads nvm
_dotfiles_source_if_file "/opt/homebrew/opt/nvm/etc/bash_completion.d/nvm"  # This loads nvm bash_completion
if command -v nvm >/dev/null 2>&1; then
  nvm use --silent default >/dev/null 2>&1 || true
fi
