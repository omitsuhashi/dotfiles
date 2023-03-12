#!/bin/zsh
if [ ! -e ~/.ssh ]; then
  mkdir ~/.ssh
fi

ln -sf ~/dotfiles/ideavimrc ~/.ideavimrc
ln -sf ~/dotfiles/zprofile ~/.zprofile
ln -sf ~/dotfiles/zshrc ~/.zshrc
ln -sf ~/dotfiles/xvimrc ~/.xvimrc
ln -sfn ~/dotfiles/vim ~/.vim

