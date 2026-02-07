#!/bin/zsh
if [ ! -e ~/.ssh ]; then
  mkdir ~/.ssh
fi

ln -sf ~/dotfiles/ideavimrc ~/.ideavimrc
ln -sf ~/dotfiles/zprofile ~/.zprofile
ln -sf ~/dotfiles/zshrc ~/.zshrc
ln -sf ~/dotfiles/xvimrc ~/.xvimrc
ln -sfn ~/dotfiles/vim ~/.vim
ln -sf ~/dotfiles/git/gitconfig ~/.gitconfig
ln -sf ~/dotfiles/git/gitignore_global ~/.gitignore_global
ln -sf ~/dotfiles/git/gitmessage ~/.gitmessage
ln -sfn ~/dotfiles/codex ~/.codex
ln -sfn ~/dotfiles/agents ~/.agents
