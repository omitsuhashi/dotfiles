#!/bin/zsh

set -u

repo_root="${0:A:h:h}"
sut="$repo_root/scripts/fusionctl"
test_root="$(mktemp -d)"
test_root="${test_root:A}"
trap 'rm -rf "$test_root"' EXIT

fake_bin="$test_root/bin"
vm_root="$test_root/Virtual Machines.localized"
running_file="$test_root/running-vms"
vmrun_log="$test_root/vmrun.log"

mkdir -p "$fake_bin" \
  "$vm_root/Kali.vmwarevm" \
  "$vm_root/Ubuntu 24.04.vmwarevm"
: > "$vm_root/Kali.vmwarevm/Kali.vmx"
: > "$vm_root/Standalone.vmx"
: > "$vm_root/Ubuntu 24.04.vmwarevm/Ubuntu 24.04.vmx"
print -rl -- \
  "$vm_root/Ubuntu 24.04.vmwarevm/Ubuntu 24.04.vmx" \
  "$vm_root/Kali.vmwarevm/Kali.vmx.backup" > "$running_file"
: > "$vmrun_log"

cat > "$fake_bin/vmrun" <<'FAKE_VMRUN'
#!/bin/zsh
{
  print -r -- BEGIN
  for arg in "$@"; do
    print -r -- "$arg"
  done
  print -r -- END
} >> "$FUSIONCTL_TEST_VMRUN_LOG"

command_name="${3-}"
if [[ "${FUSIONCTL_TEST_FAIL_COMMAND:-}" == "$command_name" ]]; then
  print -u2 -- "fake vmrun failure: $command_name"
  exit 9
fi

case "$command_name" in
  list)
    typeset -a running=()
    if [[ -s "$FUSIONCTL_TEST_RUNNING_FILE" ]]; then
      running=("${(@f)$(<"$FUSIONCTL_TEST_RUNNING_FILE")}")
    fi
    print -r -- "Total running VMs: ${#running}"
    (( ${#running} == 0 )) || print -rl -- "${running[@]}"
    ;;
  getGuestIPAddress)
    print -r -- "${FUSIONCTL_TEST_IP:-192.0.2.10}"
    ;;
  start|stop)
    ;;
  *)
    print -u2 -- "unexpected fake vmrun command: $command_name"
    exit 64
    ;;
esac
FAKE_VMRUN

cat > "$fake_bin/find" <<'FAKE_FIND'
#!/bin/zsh

if [[ "${FUSIONCTL_TEST_FIND_FAIL:-0}" == 1 ]]; then
  print -rn -- "$FUSIONCTL_TEST_PARTIAL_VMX"$'\0'
  print -u2 -- 'fake find failure'
  exit 7
fi

exec /usr/bin/find "$@"
FAKE_FIND
chmod +x "$fake_bin/vmrun" "$fake_bin/find"

typeset output
typeset -i result
typeset -i discovery_failure=0

fail() {
  print -u2 -- "FAIL: $1"
  exit 1
}

assert_eq() {
  local expected="$1"
  local actual="$2"
  local context="$3"
  [[ "$actual" == "$expected" ]] || fail "$context\nexpected: ${(qqq)expected}\nactual:   ${(qqq)actual}"
}

assert_contains() {
  local haystack="$1"
  local needle="$2"
  local context="$3"
  [[ "$haystack" == *"$needle"* ]] || fail "$context: missing ${(qqq)needle}"
}

assert_not_contains() {
  local haystack="$1"
  local needle="$2"
  local context="$3"
  [[ "$haystack" != *"$needle"* ]] || fail "$context: unexpectedly found ${(qqq)needle}"
}

run_cli() {
  run_cli_from_root "$vm_root" "$repo_root" "$@"
}

run_cli_from_root() {
  local configured_root="$1"
  local working_directory="$2"
  shift 2

  output="$(
    cd "$working_directory" || exit 99
    FUSIONCTL_VM_ROOT="$configured_root" \
    FUSIONCTL_TEST_RUNNING_FILE="$running_file" \
    FUSIONCTL_TEST_VMRUN_LOG="$vmrun_log" \
    FUSIONCTL_TEST_FIND_FAIL="$discovery_failure" \
    FUSIONCTL_TEST_PARTIAL_VMX="$vm_root/Kali.vmwarevm/Kali.vmx" \
    PATH="$fake_bin:/usr/bin:/bin" \
    "$sut" "$@" 2>&1
  )"
  result=$?
}

run_cli list
expected=$'NAME\tSTATE\tPATH\n'\
$'Kali\tstopped\t'"$vm_root/Kali.vmwarevm/Kali.vmx"$'\n'\
$'Standalone\tstopped\t'"$vm_root/Standalone.vmx"$'\n'\
$'Ubuntu 24.04\trunning\t'"$vm_root/Ubuntu 24.04.vmwarevm/Ubuntu 24.04.vmx"
assert_eq 0 "$result" "list exit status"
assert_eq "$expected" "$output" "list output"

typeset -a root_regression_failures=()

run_cli_from_root 'Virtual Machines.localized/../Virtual Machines.localized' "$test_root" list
if [[ "$result" != 0 || "$output" != "$expected" ]]; then
  root_regression_failures+=("relative root did not produce canonical paths and state")
fi

symlink_root="$test_root/vm-root-link"
ln -s "$vm_root" "$symlink_root"
run_cli_from_root "$symlink_root" "$repo_root" list
if [[ "$result" != 0 || "$output" != "$expected" ]]; then
  root_regression_failures+=("symlink root was not traversed canonically")
fi

trailing_bundle="$vm_root/Trailing Display.vmwarevm"
mkdir -p "$trailing_bundle"
: > "$trailing_bundle/internal-config.vmx"
trailing_expected=$'NAME\tSTATE\tPATH\n'\
$'Kali\tstopped\t'"$vm_root/Kali.vmwarevm/Kali.vmx"$'\n'\
$'Standalone\tstopped\t'"$vm_root/Standalone.vmx"$'\n'\
$'Trailing Display\tstopped\t'"$trailing_bundle/internal-config.vmx"$'\n'\
$'Ubuntu 24.04\trunning\t'"$vm_root/Ubuntu 24.04.vmwarevm/Ubuntu 24.04.vmx"
run_cli_from_root "$vm_root/" "$repo_root" list
if [[ "$result" != 0 || "$output" != "$trailing_expected" ]]; then
  root_regression_failures+=("trailing slash changed discovered names, paths, or state")
fi

bundle_root="$test_root/Bundle Root.vmwarevm"
mkdir -p "$bundle_root"
: > "$bundle_root/internal-config.vmx"
print -r -- "$bundle_root/internal-config.vmx" >> "$running_file"
bundle_expected=$'NAME\tSTATE\tPATH\n'\
$'Bundle Root\trunning\t'"$bundle_root/internal-config.vmx"
run_cli_from_root "$bundle_root/" "$repo_root" list
if [[ "$result" != 0 || "$output" != "$bundle_expected" ]]; then
  root_regression_failures+=("bundle root was not recognized as the VM display-name ancestor")
fi

if (( ${#root_regression_failures} > 0 )); then
  fail "VM root normalization regressions:\n${(F)root_regression_failures}"
fi

discovery_failure=1
run_cli list
assert_eq 1 "$result" "discovery command failure exit status"
assert_contains "$output" 'fusionctl: VM discovery failed' "discovery command failure diagnostic"
assert_not_contains "$output" $'NAME\tSTATE\tPATH' "discovery command failure output"
discovery_failure=0

empty_root="$test_root/empty-root"
mkdir -p "$empty_root"
output="$(
  FUSIONCTL_VM_ROOT="$empty_root" \
  FUSIONCTL_TEST_RUNNING_FILE="$running_file" \
  FUSIONCTL_TEST_VMRUN_LOG="$vmrun_log" \
  PATH="$fake_bin:/usr/bin:/bin" \
  "$sut" list 2>&1
)"
result=$?
assert_eq 0 "$result" "empty list exit status"
assert_eq $'NAME\tSTATE\tPATH' "$output" "empty list header"

run_cli status Ubuntu 24.04
assert_eq 0 "$result" "status with unquoted SSH-style words"
assert_eq running "$output" "running status"

run_cli status "$vm_root/Kali.vmwarevm/Kali.vmx"
assert_eq 0 "$result" "status by exact full path"
assert_eq stopped "$output" "stopped status"

run_cli status Ubuntu
assert_eq 2 "$result" "unknown name exit status"
assert_contains "$output" 'unknown VM: Ubuntu' "unknown name diagnostic"
assert_contains "$output" 'fusionctl list' "unknown name hint"

outside_vmx="$test_root/Outside.vmwarevm/Outside.vmx"
mkdir -p "${outside_vmx:h}"
: > "$outside_vmx"
run_cli status "$outside_vmx"
assert_eq 2 "$result" "outside path exit status"
assert_contains "$output" 'unknown VM:' "outside path rejection"

mkdir -p "$vm_root/one/Duplicate.vmwarevm" "$vm_root/two/Duplicate.vmwarevm"
: > "$vm_root/one/Duplicate.vmwarevm/one.vmx"
: > "$vm_root/two/Duplicate.vmwarevm/two.vmx"
run_cli status Duplicate
assert_eq 2 "$result" "duplicate name exit status"
assert_contains "$output" 'ambiguous VM name: Duplicate' "duplicate diagnostic"
assert_contains "$output" "$vm_root/one/Duplicate.vmwarevm/one.vmx" "first duplicate path"
assert_contains "$output" "$vm_root/two/Duplicate.vmwarevm/two.vmx" "second duplicate path"

run_cli status
assert_eq 2 "$result" "missing target exit status"
assert_contains "$output" 'usage:' "missing target usage"

run_cli list unexpected
assert_eq 2 "$result" "extra list argument exit status"
assert_contains "$output" 'usage:' "extra list argument usage"

run_cli destroy Kali
assert_eq 2 "$result" "unknown command exit status"
assert_contains "$output" 'usage:' "unknown command usage"

output="$(
  FUSIONCTL_VM_ROOT="$test_root/missing-root" \
  FUSIONCTL_TEST_RUNNING_FILE="$running_file" \
  FUSIONCTL_TEST_VMRUN_LOG="$vmrun_log" \
  PATH="$fake_bin:/usr/bin:/bin" \
  "$sut" list 2>&1
)"
result=$?
assert_eq 2 "$result" "missing root exit status"
assert_contains "$output" 'VM root is not a readable directory:' "missing root diagnostic"

output="$(FUSIONCTL_VM_ROOT="$vm_root" PATH="/usr/bin:/bin" "$sut" list 2>&1)"
result=$?
assert_eq 2 "$result" "missing vmrun exit status"
assert_contains "$output" 'vmrun is not available in PATH' "missing vmrun diagnostic"

output="$(
  FUSIONCTL_VM_ROOT="$vm_root" \
  FUSIONCTL_TEST_RUNNING_FILE="$running_file" \
  FUSIONCTL_TEST_VMRUN_LOG="$vmrun_log" \
  FUSIONCTL_TEST_FAIL_COMMAND=list \
  PATH="$fake_bin:/usr/bin:/bin" \
  "$sut" list 2>&1
)"
result=$?
assert_eq 1 "$result" "vmrun list failure exit status"
assert_contains "$output" 'fake vmrun failure: list' "vmrun list diagnostic preservation"
assert_contains "$output" 'vmrun list failed' "vmrun list failure context"

: > "$vmrun_log"
run_cli start Ubuntu 24.04
assert_eq 0 "$result" "idempotent start exit status"
assert_eq 'already running: Ubuntu 24.04' "$output" "idempotent start output"
log="$(<"$vmrun_log")"
assert_not_contains "$log" $'\nstart\n' "idempotent start must not mutate"

: > "$vmrun_log"
run_cli start Kali
assert_eq 0 "$result" "start exit status"
assert_eq 'started: Kali' "$output" "start output"
log="$(<"$vmrun_log")"
assert_contains "$log" $'\nstart\n' "start command"
assert_contains "$log" $'\nnogui\n' "headless mode"
assert_contains "$log" $'\n'"$vm_root/Kali.vmwarevm/Kali.vmx"$'\n' "start VMX path"

: > "$vmrun_log"
run_cli stop Kali
assert_eq 0 "$result" "idempotent stop exit status"
assert_eq 'already stopped: Kali' "$output" "idempotent stop output"
log="$(<"$vmrun_log")"
assert_not_contains "$log" $'\nstop\n' "idempotent stop must not mutate"

: > "$vmrun_log"
run_cli stop Ubuntu 24.04
assert_eq 0 "$result" "stop exit status"
assert_eq 'stopped: Ubuntu 24.04' "$output" "stop output"
log="$(<"$vmrun_log")"
assert_contains "$log" $'\nstop\n' "stop command"
assert_contains "$log" $'\nsoft\n' "soft stop mode"
assert_not_contains "$log" $'\nhard\n' "no hard stop"

: > "$vmrun_log"
FUSIONCTL_TEST_IP=198.51.100.7 run_cli ip Ubuntu 24.04
assert_eq 0 "$result" "IP exit status"
assert_eq 198.51.100.7 "$output" "IP output"
log="$(<"$vmrun_log")"
assert_contains "$log" $'\ngetGuestIPAddress\n' "IP command"
assert_contains "$log" $'\n-wait\n' "IP wait flag"

run_cli ip Kali
assert_eq 1 "$result" "stopped VM IP exit status"
assert_contains "$output" 'VM is stopped: Kali' "stopped VM IP diagnostic"

output="$(
  FUSIONCTL_VM_ROOT="$vm_root" \
  FUSIONCTL_TEST_RUNNING_FILE="$running_file" \
  FUSIONCTL_TEST_VMRUN_LOG="$vmrun_log" \
  FUSIONCTL_TEST_FAIL_COMMAND=start \
  PATH="$fake_bin:/usr/bin:/bin" \
  "$sut" start Kali 2>&1
)"
result=$?
assert_eq 1 "$result" "vmrun failure normalization"
assert_contains "$output" 'vmrun start failed: Kali' "vmrun failure context"
assert_contains "$output" 'fake vmrun failure: start' "vmrun diagnostic preservation"

print -r -- "PASS: fusionctl"
