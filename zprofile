# install Prezto
# https://github.com/sorin-ionescu/prezto

export LSCOLORS=gxfxcxdxbxegedabagacad
export LC_ALL='en_US.UTF-8'
export LANG='en_US.UTF-8'

export LDFLAGS="-L/usr/local/opt/openssl/lib"
export CPPFLAGS="-I/usr/local/opt/openssl/include"

export HDF5_DIR=/opt/homebrew/opt/hdf5
export TOOL_DIR=$HOME/.tool

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

# pipenv
export PIPENV_VENV_IN_PROJECT=true

# direnv
eval "$(direnv hook zsh)"

# rvenv
eval "$(rbenv init - zsh)"

# jenv
eval export PATH="/Users/omitsuhashi/.jenv/shims:${PATH}"
export JENV_SHELL=zsh
export JENV_LOADED=1
unset JAVA_HOME
unset JDK_HOME
source '/opt/homebrew/Cellar/jenv/0.5.6/libexec/libexec/../completions/jenv.zsh'
jenv rehash 2>/dev/null
jenv refresh-plugins
jenv() {
  type typeset &> /dev/null && typeset command
  command="$1"
  if [ "$#" -gt 0 ]; then
    shift
  fi

  case "$command" in
  enable-plugin|rehash|shell|shell-options)
    eval `jenv "sh-$command" "$@"`;;
  *)
    command jenv "$command" "$@";;
  esac
}

# openjdk
export PATH="/opt/homebrew/opt/openjdk/bin:$PATH"

# dart
export PATH="$PATH":"$HOME/.pub-cache/bin"

# golang
export GOPATH=$HOME/go
export GOBIN=$GOPATH/bin
export PATH="$PATH:$GOBIN"

# rust
export PATH="$PATH:$HOME/.cargo/bin"

# flutter
export PATH="$PATH:$HOME/.tools/flutter/bin"
