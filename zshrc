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
wt-clean() {
  git worktree list --porcelain \
    | awk '/^worktree /{print $2}' \
    | while IFS= read -r wt; do
        if [ "$wt" != "$(pwd)" ]; then
          git worktree remove -f "$wt"
        fi
      done
}

# bun completions
_dotfiles_source_if_file "/Users/omitsuhashi/.bun/_bun"

# bun
export BUN_INSTALL="$HOME/.bun"
_dotfiles_path_prepend_if_dir "$BUN_INSTALL/bin"
