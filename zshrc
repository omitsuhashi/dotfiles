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

# Source Prezto.
if [[ -s "${ZDOTDIR:-$HOME}/.zprezto/init.zsh" ]]; then
  source "${ZDOTDIR:-$HOME}/.zprezto/init.zsh"
fi

# Customize to your needs...
source "/Users/omitsuhashi/google-cloud-sdk/path.zsh.inc"

# The next line updates PATH for the Google Cloud SDK.
if [ -f '/Users/omitsuhashi/google-cloud-sdk/path.zsh.inc' ]; then . '/Users/omitsuhashi/google-cloud-sdk/path.zsh.inc'; fi

# The next line enables shell command completion for gcloud.
if [ -f '/Users/omitsuhashi/google-cloud-sdk/completion.zsh.inc' ]; then . '/Users/omitsuhashi/google-cloud-sdk/completion.zsh.inc'; fi

# Added by LM Studio CLI (lms)
export PATH="$PATH:/Users/omitsuhashi/.lmstudio/bin"

# pnpm
export PNPM_HOME="/Users/omitsuhashi/Library/pnpm"
case ":$PATH:" in
  *":$PNPM_HOME:"*) ;;
  *) export PATH="$PNPM_HOME:$PATH" ;;
esac
# pnpm end

# Added by Antigravity
export PATH="/Users/omitsuhashi/.antigravity/antigravity/bin:$PATH"

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
[ -s "/Users/omitsuhashi/.bun/_bun" ] && source "/Users/omitsuhashi/.bun/_bun"

# bun
export BUN_INSTALL="$HOME/.bun"
export PATH="$BUN_INSTALL/bin:$PATH"
