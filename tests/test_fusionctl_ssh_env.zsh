#!/bin/zsh

set -euo pipefail

repo_root="${0:A:h:h}"
sut="$repo_root/zshenv.d/fusionctl.zsh"
test_home="$(mktemp -d)"
trap 'rm -rf "$test_home"' EXIT

mkdir -p "$test_home/scripts"
print -r -- '#!/bin/sh' 'exit 0' > "$test_home/scripts/fusionctl"
chmod +x "$test_home/scripts/fusionctl"

HOME="$test_home"
PATH='/usr/bin:/bin'
source "$sut"

[[ "$(command -v fusionctl)" == "$test_home/scripts/fusionctl" ]]
[[ "$path[1]" == "$test_home/scripts" ]]
[[ "$path[2]" == '/Applications/VMware Fusion.app/Contents/Public' ]]

source "$sut"

scripts_count=0
vmware_count=0
for dir in $path; do
  [[ "$dir" == "$test_home/scripts" ]] && (( ++scripts_count ))
  [[ "$dir" == '/Applications/VMware Fusion.app/Contents/Public' ]] \
    && (( ++vmware_count ))
done

(( scripts_count == 1 ))
(( vmware_count == 1 ))

print -r -- 'PASS: fusionctl SSH environment'
