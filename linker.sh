#!/bin/zsh

set -euo pipefail

DOTFILES_DIR="${0:A:h}"

ensure_dir() {
  mkdir -p "$1"
}

link_children_as_symlinks() {
  local src_dir="$1"
  local dest_dir="$2"
  local child

  [[ -d "$src_dir" ]] || return 0

  ensure_dir "$dest_dir"

  for child in "$src_dir"/*(N/); do
    ln -sfn "$child" "$dest_dir/${child:t}"
  done
}

ensure_dir "$HOME/.ssh"

ln -sf "$DOTFILES_DIR/ideavimrc" "$HOME/.ideavimrc"
ln -sf "$DOTFILES_DIR/zprofile" "$HOME/.zprofile"
ln -sf "$DOTFILES_DIR/zshrc" "$HOME/.zshrc"
ln -sf "$DOTFILES_DIR/xvimrc" "$HOME/.xvimrc"
ln -sfn "$DOTFILES_DIR/vim" "$HOME/.vim"
ln -sf "$DOTFILES_DIR/git/gitconfig" "$HOME/.gitconfig"
ln -sf "$DOTFILES_DIR/git/gitignore_global" "$HOME/.gitignore_global"
ln -sf "$DOTFILES_DIR/git/gitmessage" "$HOME/.gitmessage"

ensure_dir "$HOME/.codex"
ln -sf "$DOTFILES_DIR/agents/AGENTS.md" "$HOME/.codex/AGENTS.md"

link_children_as_symlinks "$DOTFILES_DIR/agents/skills" "$HOME/.codex/skills"
link_children_as_symlinks "$DOTFILES_DIR/agents/skills" "$HOME/.claude/skills"

ensure_dir "$HOME/scripts"

for script in "$DOTFILES_DIR"/scripts/*(N-.); do
  ln -sf "$script" "$HOME/scripts/${script:t}"
done
