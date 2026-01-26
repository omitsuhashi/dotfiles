#!/usr/bin/env bash
set -euo pipefail

# Run make targets only if they exist.
# Order (assumption): fmt -> lint -> test -> build
targets=(build lint test)

# If no Makefile, skip (request: "if command exists")
if [[ ! -f Makefile && ! -f makefile && ! -f GNUmakefile ]]; then
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
  if make -rRqn "$t" >/dev/null 2>&1; then
    existing+=("$t")
  fi
done

if [[ ${#existing[@]} -eq 0 ]]; then
  echo "skip: no matching make targets (fmt/lint/test/build)"
  exit 0
fi

for t in "${existing[@]}"; do
  echo "==> make $t"
  make "$t"
done

