# install Prezto
# https://github.com/sorin-ionescu/prezto

export LSCOLORS=gxfxcxdxbxegedabagacad
export LC_ALL='en_US.UTF-8'
export LANG='en_US.UTF-8'

export HDF5_DIR=/opt/homebrew/opt/hdf5

# brew
if [[ $(uname -m) == 'arm64' ]]; then
  eval "$(/opt/homebrew/bin/brew shellenv)"
fi

# nodenv
export PATH="$HOME/.nodenv/bin:$PATH"
eval "$(nodenv init -)"

# pyenv
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

# direnv
eval "$(direnv hook zsh)"

# openjdk
export PATH="/opt/homebrew/opt/openjdk/bin:$PATH"

# golang
export PATH="/usr/local/go/bin:$PATH"

# rust
export PATH="$HOME/.cargo/bin:$PATH"

# dart
export PATH="$PATH":"$HOME/.pub-cache/bin"

# golang
export GOPATH=$HOME/go
export GOBIN=$GOPATH/bin
export PATH="$PATH:$GOBIN"

