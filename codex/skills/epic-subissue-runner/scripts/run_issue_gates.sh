#!/usr/bin/env bash
set -euo pipefail

dir="."
if [[ "${1:-}" == "--dir" ]]; then
  dir="${2:-}"
  [[ -n "$dir" ]] || { echo "usage: $0 [--dir <path>]" >&2; exit 2; }
fi

# Ensure submodules are ready (doc/ as submodule etc.)
if [[ -f "$dir/.gitmodules" ]]; then
  git -C "$dir" submodule sync --recursive >/dev/null || true
  git -C "$dir" submodule update --init --recursive
fi

# Run make targets only if they exist.
# Order (assumption): fmt -> lint -> test -> build
targets=(build lint test)

# If no Makefile, skip (request: "if command exists")
if [[ ! -f "$dir/Makefile" && ! -f "$dir/makefile" && ! -f "$dir/GNUmakefile" ]]; then
  echo "skip: no Makefile"
  exit 0
fi

if ! command -v make >/dev/null 2>&1; then
  echo "skip: make not found"
  exit 0
fi

existing=()
for t in "${targets[@]}"; do
  # -rR disables built-in rules/vars to avoid false positives from implicit rules
  # -q: question mode, -n: dry-run (no execution). If target is unknown -> non-zero.
  if make -C "$dir" -rRqn "$t" >/dev/null 2>&1; then
    existing+=("$t")
  fi
done

if [[ ${#existing[@]} -eq 0 ]]; then
  echo "skip: no matching make targets (fmt/lint/test/build)"
  exit 0
fi

for t in "${existing[@]}"; do
  echo "==> make $t"
  make -C "$dir" "$t"
done
