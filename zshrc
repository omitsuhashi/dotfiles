#
# Executes commands at the start of an interactive session.
#
# Authors:
#   Sorin Ionescu <sorin.ionescu@gmail.com>
#

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

