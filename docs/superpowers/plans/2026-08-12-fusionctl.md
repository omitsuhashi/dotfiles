# fusionctl Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a host-side `fusionctl` command that discovers VMware Fusion VMX files and safely lists, checks, starts, queries, and soft-stops an exactly selected VM over an existing SSH route.

**Architecture:** A dependency-free Zsh script owns VM discovery, exact target resolution, running-state parsing, and the five subcommands. A standalone Zsh test uses temporary VM bundles and a fake `vmrun`, while an operations document explains host installation and non-interactive SSH `PATH` verification.

**Tech Stack:** macOS Zsh, VMware Fusion `vmrun`, POSIX/macOS command-line utilities, standalone Zsh tests

## Global Constraints

- Implement the operational logic only in `scripts/fusionctl`; do not add VM-control logic to `zprofile` or `zshrc`.
- Discover VMX files below `${FUSIONCTL_VM_ROOT:-$HOME/Virtual Machines.localized}`.
- Resolve a target only by exact discovered VMX path or exact case-sensitive display name; duplicate names must fail and print their full paths.
- Never select the first discovery result implicitly and never accept a path outside the configured root.
- Use `vmrun` by command name because the Fusion host already exposes it in the SSH command environment.
- Use `vmrun -T fusion start "$vmx" nogui`; never start with GUI mode.
- Use `vmrun -T fusion stop "$vmx" soft`; never retry or escalate to `hard`.
- Use `vmrun -T fusion getGuestIPAddress "$vmx" -wait` only for a running VM.
- Treat repeated `start` and `stop` requests as successful no-ops when the requested state already holds.
- Send normal results to stdout and diagnostics to stderr. Exit `0` for success/idempotence, `1` for operational failure, and `2` for usage/configuration/selection errors.
- Do not use `eval`, external package dependencies, Fusion REST APIs, or guest SSH.
- Unit tests must not start, stop, or otherwise operate a real VM.

## File Structure

- Create `scripts/fusionctl`: standalone host-side CLI and all command behavior.
- Create `tests/test_fusionctl.zsh`: temporary-filesystem test harness and fake `vmrun` contract tests.
- Create `docs/fusionctl.md`: installation, SSH invocation, configuration, and verification instructions.
- Keep `linker.sh` unchanged: its existing `scripts/*` loop already links `scripts/fusionctl` into `$HOME/scripts`.

---

### Task 1: VM discovery, running-state parsing, and `list`

**Files:**
- Create: `scripts/fusionctl`
- Create: `tests/test_fusionctl.zsh`

**Interfaces:**
- Consumes: `FUSIONCTL_VM_ROOT`, `HOME`, `PATH`, and `vmrun -T fusion list`.
- Produces: global arrays `VM_NAMES`, `VM_PATHS`, and `RUNNING_PATHS`; functions `discover_vms()`, `load_running_vms()`, `is_running(path)`; CLI `fusionctl list`.

- [ ] **Step 1: Write the failing discovery/list test harness**

Create `tests/test_fusionctl.zsh` with a fake `vmrun` and one test covering deterministic output, spaces, and both running states:

```zsh
#!/bin/zsh

set -u

repo_root="${0:A:h:h}"
sut="$repo_root/scripts/fusionctl"
test_root="$(mktemp -d)"
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
chmod +x "$fake_bin/vmrun"

typeset output
typeset -i status

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
  output="$(
    FUSIONCTL_VM_ROOT="$vm_root" \
    FUSIONCTL_TEST_RUNNING_FILE="$running_file" \
    FUSIONCTL_TEST_VMRUN_LOG="$vmrun_log" \
    PATH="$fake_bin:/usr/bin:/bin" \
    "$sut" "$@" 2>&1
  )"
  status=$?
}

run_cli list
expected=$'NAME\tSTATE\tPATH\n'\
$'Kali\tstopped\t'"$vm_root/Kali.vmwarevm/Kali.vmx"$'\n'\
$'Standalone\tstopped\t'"$vm_root/Standalone.vmx"$'\n'\
$'Ubuntu 24.04\trunning\t'"$vm_root/Ubuntu 24.04.vmwarevm/Ubuntu 24.04.vmx"
assert_eq 0 "$status" "list exit status"
assert_eq "$expected" "$output" "list output"

empty_root="$test_root/empty-root"
mkdir -p "$empty_root"
output="$(
  FUSIONCTL_VM_ROOT="$empty_root" \
  FUSIONCTL_TEST_RUNNING_FILE="$running_file" \
  FUSIONCTL_TEST_VMRUN_LOG="$vmrun_log" \
  PATH="$fake_bin:/usr/bin:/bin" \
  "$sut" list 2>&1
)"
status=$?
assert_eq 0 "$status" "empty list exit status"
assert_eq $'NAME\tSTATE\tPATH' "$output" "empty list header"

print -r -- "PASS: fusionctl"
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```sh
zsh tests/test_fusionctl.zsh
```

Expected: FAIL with `scripts/fusionctl: no such file or directory` and a non-zero exit.

- [ ] **Step 3: Implement discovery and `list` minimally**

Create `scripts/fusionctl`:

```zsh
#!/bin/zsh

set -u
set -o pipefail

typeset -gr VM_ROOT="${FUSIONCTL_VM_ROOT:-$HOME/Virtual Machines.localized}"
typeset -ga VM_NAMES=()
typeset -ga VM_PATHS=()
typeset -ga RUNNING_PATHS=()

usage() {
  print -u2 -- 'usage: fusionctl list'
}

error() {
  print -u2 -- "fusionctl: $*"
}

validate_environment() {
  if ! command -v vmrun >/dev/null 2>&1; then
    error 'vmrun is not available in PATH'
    return 2
  fi
  if [[ ! -d "$VM_ROOT" || ! -r "$VM_ROOT" ]]; then
    error "VM root is not a readable directory: $VM_ROOT"
    return 2
  fi
}

discover_vms() {
  local vmx dir bundle name record
  local -a records=()

  VM_NAMES=()
  VM_PATHS=()

  while IFS= read -r -d $'\0' vmx; do
    dir="${vmx:h}"
    bundle=''
    while [[ "$dir" == "$VM_ROOT"/* ]]; do
      if [[ "${dir:t}" == *.vmwarevm ]]; then
        bundle="$dir"
        break
      fi
      dir="${dir:h}"
    done

    if [[ -n "$bundle" ]]; then
      name="${bundle:t:r}"
    else
      name="${vmx:t:r}"
    fi

    if [[ "$name" == *$'\t'* || "$name" == *$'\n'* || "$vmx" == *$'\t'* || "$vmx" == *$'\n'* ]]; then
      error "unsupported tab or newline in VM name/path: $vmx"
      return 2
    fi
    records+=("$name"$'\t'"$vmx")
  done < <(find "$VM_ROOT" -type f -name '*.vmx' -print0)

  records=("${(@o)records}")
  for record in "${records[@]}"; do
    VM_NAMES+=("${record%%$'\t'*}")
    VM_PATHS+=("${record#*$'\t'}")
  done
}

load_running_vms() {
  local output line
  local -a lines=()
  local -i index

  output="$(vmrun -T fusion list)" || {
    error 'vmrun list failed'
    return 1
  }
  lines=("${(@f)output}")
  RUNNING_PATHS=()
  for (( index = 2; index <= ${#lines}; index++ )); do
    line="${lines[index]}"
    [[ -z "$line" ]] || RUNNING_PATHS+=("$line")
  done
}

is_running() {
  local expected="$1"
  local running
  for running in "${RUNNING_PATHS[@]}"; do
    [[ "$running" == "$expected" ]] && return 0
  done
  return 1
}

command_list() {
  local -i index
  local state

  load_running_vms || return $?
  printf 'NAME\tSTATE\tPATH\n'
  for (( index = 1; index <= ${#VM_PATHS}; index++ )); do
    state=stopped
    is_running "${VM_PATHS[index]}" && state=running
    printf '%s\t%s\t%s\n' "${VM_NAMES[index]}" "$state" "${VM_PATHS[index]}"
  done
}

main() {
  if [[ "${1-}" != list || $# -ne 1 ]]; then
    usage
    return 2
  fi
  validate_environment || return $?
  discover_vms || return $?
  command_list
}

main "$@"
```

Make the script executable:

```sh
chmod +x scripts/fusionctl tests/test_fusionctl.zsh
```

- [ ] **Step 4: Run focused syntax and list tests**

Run:

```sh
zsh -n scripts/fusionctl tests/test_fusionctl.zsh
zsh tests/test_fusionctl.zsh
```

Expected: both commands exit `0`; the test prints `PASS: fusionctl`.

- [ ] **Step 5: Commit the discovery/list slice**

```sh
git add scripts/fusionctl tests/test_fusionctl.zsh
git commit -m "Add fusionctl VM discovery and listing"
```

---

### Task 2: Exact target resolution and `status`

**Files:**
- Modify: `scripts/fusionctl`
- Modify: `tests/test_fusionctl.zsh`

**Interfaces:**
- Consumes: populated `VM_NAMES`, `VM_PATHS`, and `RUNNING_PATHS` from Task 1.
- Produces: globals `RESOLVED_NAME`, `RESOLVED_PATH`; function `resolve_target(words...)`; CLI `fusionctl status <name-or-vmx-path>`.

- [ ] **Step 1: Add failing target-resolution/status tests**

Insert these cases before the final `PASS` line in `tests/test_fusionctl.zsh`:

```zsh
run_cli status Ubuntu 24.04
assert_eq 0 "$status" "status with unquoted SSH-style words"
assert_eq running "$output" "running status"

run_cli status "$vm_root/Kali.vmwarevm/Kali.vmx"
assert_eq 0 "$status" "status by exact full path"
assert_eq stopped "$output" "stopped status"

run_cli status Ubuntu
assert_eq 2 "$status" "unknown name exit status"
assert_contains "$output" 'unknown VM: Ubuntu' "unknown name diagnostic"
assert_contains "$output" 'fusionctl list' "unknown name hint"

outside_vmx="$test_root/Outside.vmwarevm/Outside.vmx"
mkdir -p "${outside_vmx:h}"
: > "$outside_vmx"
run_cli status "$outside_vmx"
assert_eq 2 "$status" "outside path exit status"
assert_contains "$output" 'unknown VM:' "outside path rejection"

mkdir -p "$vm_root/one/Duplicate.vmwarevm" "$vm_root/two/Duplicate.vmwarevm"
: > "$vm_root/one/Duplicate.vmwarevm/one.vmx"
: > "$vm_root/two/Duplicate.vmwarevm/two.vmx"
run_cli status Duplicate
assert_eq 2 "$status" "duplicate name exit status"
assert_contains "$output" 'ambiguous VM name: Duplicate' "duplicate diagnostic"
assert_contains "$output" "$vm_root/one/Duplicate.vmwarevm/one.vmx" "first duplicate path"
assert_contains "$output" "$vm_root/two/Duplicate.vmwarevm/two.vmx" "second duplicate path"

run_cli status
assert_eq 2 "$status" "missing target exit status"
assert_contains "$output" 'usage:' "missing target usage"

run_cli list unexpected
assert_eq 2 "$status" "extra list argument exit status"
assert_contains "$output" 'usage:' "extra list argument usage"

run_cli destroy Kali
assert_eq 2 "$status" "unknown command exit status"
assert_contains "$output" 'usage:' "unknown command usage"

output="$(
  FUSIONCTL_VM_ROOT="$test_root/missing-root" \
  FUSIONCTL_TEST_RUNNING_FILE="$running_file" \
  FUSIONCTL_TEST_VMRUN_LOG="$vmrun_log" \
  PATH="$fake_bin:/usr/bin:/bin" \
  "$sut" list 2>&1
)"
status=$?
assert_eq 2 "$status" "missing root exit status"
assert_contains "$output" 'VM root is not a readable directory:' "missing root diagnostic"

output="$(FUSIONCTL_VM_ROOT="$vm_root" PATH="/usr/bin:/bin" "$sut" list 2>&1)"
status=$?
assert_eq 2 "$status" "missing vmrun exit status"
assert_contains "$output" 'vmrun is not available in PATH' "missing vmrun diagnostic"

output="$(
  FUSIONCTL_VM_ROOT="$vm_root" \
  FUSIONCTL_TEST_RUNNING_FILE="$running_file" \
  FUSIONCTL_TEST_VMRUN_LOG="$vmrun_log" \
  FUSIONCTL_TEST_FAIL_COMMAND=list \
  PATH="$fake_bin:/usr/bin:/bin" \
  "$sut" list 2>&1
)"
status=$?
assert_eq 1 "$status" "vmrun list failure exit status"
assert_contains "$output" 'fake vmrun failure: list' "vmrun list diagnostic preservation"
assert_contains "$output" 'vmrun list failed' "vmrun list failure context"
```

- [ ] **Step 2: Run the tests to verify the new cases fail**

Run:

```sh
zsh tests/test_fusionctl.zsh
```

Expected: FAIL at the first `status` assertion because only `list` is implemented.

- [ ] **Step 3: Implement exact resolution and `status`**

Add these globals after the arrays in `scripts/fusionctl`:

```zsh
typeset -g RESOLVED_NAME=''
typeset -g RESOLVED_PATH=''
```

Replace `usage()` with:

```zsh
usage() {
  print -u2 -- 'usage: fusionctl list'
  print -u2 -- '       fusionctl start <name-or-vmx-path>'
  print -u2 -- '       fusionctl status <name-or-vmx-path>'
  print -u2 -- '       fusionctl ip <name-or-vmx-path>'
  print -u2 -- '       fusionctl stop <name-or-vmx-path>'
}
```

Add target resolution and status:

```zsh
resolve_target() {
  local target="${(j: :)@}"
  local -a matches=()
  local -i index

  if [[ -z "$target" ]]; then
    usage
    return 2
  fi

  for (( index = 1; index <= ${#VM_PATHS}; index++ )); do
    if [[ "${VM_PATHS[index]}" == "$target" ]]; then
      RESOLVED_NAME="${VM_NAMES[index]}"
      RESOLVED_PATH="${VM_PATHS[index]}"
      return 0
    fi
  done

  for (( index = 1; index <= ${#VM_NAMES}; index++ )); do
    [[ "${VM_NAMES[index]}" == "$target" ]] && matches+=("$index")
  done

  if (( ${#matches} == 0 )); then
    error "unknown VM: $target; run fusionctl list"
    return 2
  fi
  if (( ${#matches} > 1 )); then
    error "ambiguous VM name: $target"
    for index in "${matches[@]}"; do
      print -u2 -- "  ${VM_PATHS[index]}"
    done
    return 2
  fi

  index="${matches[1]}"
  RESOLVED_NAME="${VM_NAMES[index]}"
  RESOLVED_PATH="${VM_PATHS[index]}"
}

command_status() {
  load_running_vms || return $?
  if is_running "$RESOLVED_PATH"; then
    print -r -- running
  else
    print -r -- stopped
  fi
}
```

Replace `main()` with command validation and dispatch that preserves all
remaining target words:

```zsh
main() {
  local command="${1-}"
  [[ -n "$command" ]] || {
    usage
    return 2
  }
  shift

  case "$command" in
    list)
      (( $# == 0 )) || {
        usage
        return 2
      }
      ;;
    start|status|ip|stop)
      (( $# > 0 )) || {
        usage
        return 2
      }
      ;;
    *)
      usage
      return 2
      ;;
  esac

  validate_environment || return $?
  discover_vms || return $?

  case "$command" in
    list)
      command_list
      ;;
    status)
      resolve_target "$@" || return $?
      command_status
      ;;
    *)
      error "command is not implemented: $command"
      return 2
      ;;
  esac
}
```

- [ ] **Step 4: Run status and regression tests**

Run:

```sh
zsh -n scripts/fusionctl tests/test_fusionctl.zsh
zsh tests/test_fusionctl.zsh
```

Expected: syntax checks and all list/status assertions pass.

- [ ] **Step 5: Commit exact selection and status**

```sh
git add scripts/fusionctl tests/test_fusionctl.zsh
git commit -m "Add exact fusionctl target status"
```

---

### Task 3: Idempotent start/stop and running-only IP lookup

**Files:**
- Modify: `scripts/fusionctl`
- Modify: `tests/test_fusionctl.zsh`

**Interfaces:**
- Consumes: `RESOLVED_NAME`, `RESOLVED_PATH`, `load_running_vms()`, and `is_running(path)`.
- Produces: functions `command_start()`, `command_stop()`, `command_ip()`; CLI `start`, `stop`, and `ip` behaviors.

- [ ] **Step 1: Add failing operation tests**

Insert these cases before the final `PASS` line in `tests/test_fusionctl.zsh`:

```zsh
: > "$vmrun_log"
run_cli start Ubuntu 24.04
assert_eq 0 "$status" "idempotent start exit status"
assert_eq 'already running: Ubuntu 24.04' "$output" "idempotent start output"
log="$(<"$vmrun_log")"
assert_not_contains "$log" $'\nstart\n' "idempotent start must not mutate"

: > "$vmrun_log"
run_cli start Kali
assert_eq 0 "$status" "start exit status"
assert_eq 'started: Kali' "$output" "start output"
log="$(<"$vmrun_log")"
assert_contains "$log" $'\nstart\n' "start command"
assert_contains "$log" $'\nnogui\n' "headless mode"
assert_contains "$log" $'\n'"$vm_root/Kali.vmwarevm/Kali.vmx"$'\n' "start VMX path"

: > "$vmrun_log"
run_cli stop Kali
assert_eq 0 "$status" "idempotent stop exit status"
assert_eq 'already stopped: Kali' "$output" "idempotent stop output"
log="$(<"$vmrun_log")"
assert_not_contains "$log" $'\nstop\n' "idempotent stop must not mutate"

: > "$vmrun_log"
run_cli stop Ubuntu 24.04
assert_eq 0 "$status" "stop exit status"
assert_eq 'stopped: Ubuntu 24.04' "$output" "stop output"
log="$(<"$vmrun_log")"
assert_contains "$log" $'\nstop\n' "stop command"
assert_contains "$log" $'\nsoft\n' "soft stop mode"
assert_not_contains "$log" $'\nhard\n' "no hard stop"

: > "$vmrun_log"
FUSIONCTL_TEST_IP=198.51.100.7 run_cli ip Ubuntu 24.04
assert_eq 0 "$status" "IP exit status"
assert_eq 198.51.100.7 "$output" "IP output"
log="$(<"$vmrun_log")"
assert_contains "$log" $'\ngetGuestIPAddress\n' "IP command"
assert_contains "$log" $'\n-wait\n' "IP wait flag"

run_cli ip Kali
assert_eq 1 "$status" "stopped VM IP exit status"
assert_contains "$output" 'VM is stopped: Kali' "stopped VM IP diagnostic"

output="$(
  FUSIONCTL_VM_ROOT="$vm_root" \
  FUSIONCTL_TEST_RUNNING_FILE="$running_file" \
  FUSIONCTL_TEST_VMRUN_LOG="$vmrun_log" \
  FUSIONCTL_TEST_FAIL_COMMAND=start \
  PATH="$fake_bin:/usr/bin:/bin" \
  "$sut" start Kali 2>&1
)"
status=$?
assert_eq 1 "$status" "vmrun failure normalization"
assert_contains "$output" 'vmrun start failed: Kali' "vmrun failure context"
assert_contains "$output" 'fake vmrun failure: start' "vmrun diagnostic preservation"
```

- [ ] **Step 2: Run the tests to verify operation commands fail**

Run:

```sh
zsh tests/test_fusionctl.zsh
```

Expected: FAIL because `start`, `stop`, and `ip` still report “command is not implemented”.

- [ ] **Step 3: Implement start, stop, and IP commands**

Add these functions to `scripts/fusionctl`:

```zsh
command_start() {
  load_running_vms || return $?
  if is_running "$RESOLVED_PATH"; then
    print -r -- "already running: $RESOLVED_NAME"
    return 0
  fi
  vmrun -T fusion start "$RESOLVED_PATH" nogui || {
    error "vmrun start failed: $RESOLVED_NAME"
    return 1
  }
  print -r -- "started: $RESOLVED_NAME"
}

command_stop() {
  load_running_vms || return $?
  if ! is_running "$RESOLVED_PATH"; then
    print -r -- "already stopped: $RESOLVED_NAME"
    return 0
  fi
  vmrun -T fusion stop "$RESOLVED_PATH" soft || {
    error "vmrun stop failed: $RESOLVED_NAME"
    return 1
  }
  print -r -- "stopped: $RESOLVED_NAME"
}

command_ip() {
  load_running_vms || return $?
  if ! is_running "$RESOLVED_PATH"; then
    error "VM is stopped: $RESOLVED_NAME; run fusionctl start $RESOLVED_NAME"
    return 1
  fi
  vmrun -T fusion getGuestIPAddress "$RESOLVED_PATH" -wait || {
    error "vmrun getGuestIPAddress failed: $RESOLVED_NAME"
    return 1
  }
}
```

Replace the `main()` dispatch case with:

```zsh
  case "$command" in
    list)
      command_list
      ;;
    start|status|ip|stop)
      resolve_target "$@" || return $?
      case "$command" in
        start) command_start ;;
        status) command_status ;;
        ip) command_ip ;;
        stop) command_stop ;;
      esac
      ;;
  esac
```

- [ ] **Step 4: Run all operation and regression tests**

Run:

```sh
zsh -n scripts/fusionctl tests/test_fusionctl.zsh
zsh tests/test_fusionctl.zsh
```

Expected: all tests pass and the fake log proves `nogui`, `soft`, exact paths,
`-wait`, and idempotence.

- [ ] **Step 5: Commit VM operations**

```sh
git add scripts/fusionctl tests/test_fusionctl.zsh
git commit -m "Add safe fusionctl VM operations"
```

---

### Task 4: Host installation guide and final verification

**Files:**
- Create: `docs/fusionctl.md`
- Verify: `scripts/fusionctl`
- Verify: `tests/test_fusionctl.zsh`

**Interfaces:**
- Consumes: the complete `fusionctl` CLI and existing `linker.sh` script-linking behavior.
- Produces: repeatable Fusion-host installation and SSH verification instructions.

- [ ] **Step 1: Write the operational documentation**

Create `docs/fusionctl.md`:

````markdown
# fusionctl

`fusionctl` discovers existing VMware Fusion VMX files and controls an exactly
selected VM. It runs on the Fusion host and is called from a work PC through
the existing SSH route. Replace `fusion-host` below with that established SSH
host alias.

## Install on the Fusion host

From the dotfiles checkout on the Fusion host:

```sh
cd "$HOME/dotfiles"
./linker.sh
```

This creates `$HOME/scripts/fusionctl`. Verify the command environment used by
non-interactive SSH:

```sh
ssh fusion-host 'printf "PATH=%s\n" "$PATH"; command -v vmrun; command -v fusionctl'
```

If `vmrun` is found but `fusionctl` is not, link `fusionctl` beside the
already-working `vmrun` command, provided that directory is user-writable:

```sh
ssh fusion-host '
  vmrun_path=$(command -v vmrun) || exit 1
  bin_dir=${vmrun_path%/*}
  test -w "$bin_dir" || {
    printf "not writable: %s\n" "$bin_dir" >&2
    exit 1
  }
  ln -sfn "$HOME/scripts/fusionctl" "$bin_dir/fusionctl"
  command -v fusionctl
'
```

Do not add VM operation functions to shell startup files. If the `vmrun`
directory is not writable, choose an administrator-approved directory already
shown in the remote `PATH`, or invoke `$HOME/scripts/fusionctl` explicitly.

## Commands

```sh
ssh fusion-host fusionctl list
ssh fusion-host fusionctl status Ubuntu
ssh fusion-host fusionctl start Ubuntu
ssh fusion-host fusionctl ip Ubuntu
ssh fusion-host fusionctl stop Ubuntu
```

Names containing spaces can be sent as separate SSH command words because
`fusionctl` joins all words after the subcommand:

```sh
ssh fusion-host fusionctl start Ubuntu 24.04
```

Use the exact VMX path shown by `list` when display names are duplicated.

## VM discovery root

The default is `$HOME/Virtual Machines.localized`. Override it for one remote
command when necessary:

```sh
ssh fusion-host 'FUSIONCTL_VM_ROOT="$HOME/VMs" fusionctl list'
```

## Safety behavior

- `start` is always `nogui` and does nothing if the VM is already running.
- `stop` is always `soft` and never escalates to `hard`.
- `ip` requires a running VM and VMware Tools.
- Names are exact and case-sensitive; unknown and duplicate names fail.
- VMX paths outside the discovery root are rejected.

## Local verification

```sh
zsh -n scripts/fusionctl tests/test_fusionctl.zsh
zsh tests/test_fusionctl.zsh
git diff --check
```

Real VM state changes require an explicitly selected approved VM and are not
performed by the automated tests.
````

- [ ] **Step 2: Verify installation behavior without changing a real host**

Run `linker.sh` with an isolated temporary `HOME` and confirm the symlink:

```sh
tmp_home="$(mktemp -d)"
HOME="$tmp_home" zsh ./linker.sh
test -L "$tmp_home/scripts/fusionctl"
test "$(readlink "$tmp_home/scripts/fusionctl")" = "$PWD/scripts/fusionctl"
rm -rf "$tmp_home"
```

Expected: all commands exit `0`. The removal targets only the path returned by
`mktemp -d`.

- [ ] **Step 3: Run the complete local verification gate**

Run:

```sh
zsh -n scripts/fusionctl tests/test_fusionctl.zsh
zsh tests/test_fusionctl.zsh
git diff --check
git status --short
```

Expected: syntax checks exit `0`, tests print `PASS: fusionctl`, diff check is
clean, and status shows only the three intended implementation files before
commit.

- [ ] **Step 4: Commit documentation and final verified state**

```sh
git add docs/fusionctl.md
git commit -m "Document fusionctl host setup"
```

- [ ] **Step 5: Perform read-only host preflight before any real VM mutation**

Run with the user's established Fusion-host alias:

```sh
ssh fusion-host 'command -v fusionctl; command -v vmrun; fusionctl list'
```

Expected: both commands resolve to executable paths and `list` prints the
header plus the host's discovered VMs. Record the exact output. Do not run
`start` or `stop` until the user selects the VM whose state may be changed.
