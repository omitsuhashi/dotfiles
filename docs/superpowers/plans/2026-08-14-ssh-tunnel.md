# SSH Tunnel Helper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a validated `ssh-tunnel` Zsh helper that opens one localhost-bound SSH local forward from three concise arguments.

**Architecture:** Keep the public interface as one interactive function in `zshrc`, matching the repository's existing helper pattern. A focused Zsh regression test replaces `ssh` with a stub so argument construction, validation, and exit-status propagation are verified without opening a network connection.

**Tech Stack:** Zsh, OpenSSH command-line interface, shell regression tests

## Global Constraints

- Interface: `ssh-tunnel <ssh-host> <target-ipv4> <local-port>:<target-port>`.
- Bind the local listener only to `127.0.0.1`.
- Support exactly one IPv4 target and one TCP port mapping per invocation.
- Run `ssh` in the foreground and preserve its exit status.
- Invalid input must return status 2 before invoking `ssh`.
- Bound numeric field lengths before Zsh arithmetic to prevent overflow or truncation warnings.
- Do not add background management, multiple mappings, IPv6, remote forwards, SOCKS proxies, or public listener addresses.

---

### Task 1: Implement and verify `ssh-tunnel`

**Files:**
- Create: `tests/test_ssh_tunnel.zsh`
- Modify: `zshrc:64-104`
- Verify: `docs/superpowers/specs/2026-08-14-ssh-tunnel-design.md`

**Interfaces:**
- Consumes: an OpenSSH-compatible `ssh` command and a configured destination such as `local.kali`.
- Produces: `ssh-tunnel <ssh-host> <target-ipv4> <local-port>:<target-port>`, returning status 2 for invalid input and otherwise returning the `ssh` exit status.

- [x] **Step 1: Write the failing regression test**

Create `tests/test_ssh_tunnel.zsh`:

```zsh
#!/bin/zsh

set -u

repo_root="${0:A:h:h}"
ZDOTDIR="$repo_root/tests/no-zdotdir"
source "$repo_root/zshrc"

typeset -ga captured_ssh_args
typeset -gi ssh_calls=0
typeset -gi stub_ssh_status=0

ssh() {
  (( ssh_calls += 1 ))
  captured_ssh_args=("$@")
  return "$stub_ssh_status"
}

fail() {
  print -u2 -- "$1"
  exit 1
}

assert_eq() {
  local label="$1"
  local expected="$2"
  local actual="$3"
  [[ "$actual" == "$expected" ]] \
    || fail "$label: expected '$expected', got '$actual'"
}

typeset error_file
error_file="$(mktemp "${TMPDIR:-/tmp}/test_ssh_tunnel.XXXXXX")" || exit 1
trap 'rm -f -- "$error_file"' EXIT

run_invalid() {
  local label="$1"
  shift
  local result=0
  ssh_calls=0

  ssh-tunnel "$@" >/dev/null 2>"$error_file" || result=$?

  assert_eq "$label status" 2 "$result"
  assert_eq "$label ssh calls" 0 "$ssh_calls"
}

typeset result=0
ssh-tunnel local.kali 10.48.157.47 8080:80 || result=$?
assert_eq "valid status" 0 "$result"
assert_eq "valid ssh calls" 1 "$ssh_calls"

typeset -a expected_ssh_args=(
  -N
  -o ExitOnForwardFailure=yes
  -L 127.0.0.1:8080:10.48.157.47:80
  local.kali
)
assert_eq "ssh argument count" "${#expected_ssh_args}" "${#captured_ssh_args}"
for (( argument_index = 1; argument_index <= ${#expected_ssh_args}; argument_index++ )); do
  assert_eq \
    "ssh argument $argument_index" \
    "${expected_ssh_args[$argument_index]}" \
    "${captured_ssh_args[$argument_index]}"
done

run_invalid "missing arguments"
assert_eq \
  "usage message" \
  "usage: ssh-tunnel <ssh-host> <target-ipv4> <local-port>:<target-port>" \
  "$(<"$error_file")"
run_invalid "extra argument" local.kali 10.48.157.47 8080:80 extra
run_invalid "empty ssh host" "" 10.48.157.47 8080:80
run_invalid "option-like ssh host" -V 10.48.157.47 8080:80
run_invalid "short IPv4" local.kali 10.48.157 8080:80
run_invalid "non-decimal IPv4" local.kali 10.48.x.47 8080:80
run_invalid "out-of-range IPv4" local.kali 10.48.157.256 8080:80
run_invalid "oversized IPv4 octet" local.kali 99999999999999999999.1.1.1 8080:80
assert_eq \
  "oversized IPv4 error" \
  "ssh-tunnel: invalid target IPv4 address: 99999999999999999999.1.1.1" \
  "$(<"$error_file")"
run_invalid "missing separator" local.kali 10.48.157.47 8080
run_invalid "extra separator" local.kali 10.48.157.47 8080:80:443
run_invalid "zero local port" local.kali 10.48.157.47 0:80
run_invalid "large local port" local.kali 10.48.157.47 65536:80
run_invalid "oversized local port" local.kali 10.48.157.47 99999999999999999999:80
assert_eq \
  "oversized local port error" \
  "ssh-tunnel: invalid port mapping: 99999999999999999999:80" \
  "$(<"$error_file")"
run_invalid "zero target port" local.kali 10.48.157.47 8080:0
run_invalid "large target port" local.kali 10.48.157.47 8080:65536
run_invalid "oversized target port" local.kali 10.48.157.47 8080:99999999999999999999
assert_eq \
  "oversized target port error" \
  "ssh-tunnel: invalid port mapping: 8080:99999999999999999999" \
  "$(<"$error_file")"
run_invalid "non-decimal port" local.kali 10.48.157.47 http:80

stub_ssh_status=23
ssh_calls=0
result=0
ssh-tunnel local.kali 10.48.157.47 8080:80 >/dev/null 2>&1 || result=$?
assert_eq "ssh status propagation" 23 "$result"
assert_eq "status propagation ssh calls" 1 "$ssh_calls"
```

- [x] **Step 2: Run the focused test and confirm it fails for the missing helper**

Run:

```bash
zsh -f tests/test_ssh_tunnel.zsh
```

Expected: exit status 1 after `ssh-tunnel` is reported as an unknown command; no real SSH connection is attempted because the test defines an `ssh` stub.

- [x] **Step 3: Add the minimal validated function**

Add this function after `branch-clean` in `zshrc`:

```zsh
# Open one localhost-bound SSH local port forward in the foreground.
ssh-tunnel() {
  if (( $# != 3 )); then
    print -u2 -- 'usage: ssh-tunnel <ssh-host> <target-ipv4> <local-port>:<target-port>'
    return 2
  fi

  local ssh_host="$1"
  local target_ipv4="$2"
  local port_mapping="$3"
  local local_port target_port octet
  local -a ipv4_octets

  if [[ -z "$ssh_host" || "$ssh_host" == -* ]]; then
    print -u2 -- "ssh-tunnel: invalid SSH destination: $ssh_host"
    return 2
  fi

  if [[ "$target_ipv4" != <->.<->.<->.<-> ]]; then
    print -u2 -- "ssh-tunnel: invalid target IPv4 address: $target_ipv4"
    return 2
  fi

  ipv4_octets=("${(@s:.:)target_ipv4}")
  for octet in "${ipv4_octets[@]}"; do
    if (( ${#octet} > 3 )); then
      print -u2 -- "ssh-tunnel: invalid target IPv4 address: $target_ipv4"
      return 2
    fi
    if (( 10#$octet > 255 )); then
      print -u2 -- "ssh-tunnel: invalid target IPv4 address: $target_ipv4"
      return 2
    fi
  done

  if [[ "$port_mapping" != <->:<-> ]]; then
    print -u2 -- "ssh-tunnel: invalid port mapping: $port_mapping"
    return 2
  fi

  local_port="${port_mapping%%:*}"
  target_port="${port_mapping#*:}"
  if (( ${#local_port} > 5 || ${#target_port} > 5 )); then
    print -u2 -- "ssh-tunnel: invalid port mapping: $port_mapping"
    return 2
  fi
  if (( 10#$local_port < 1 || 10#$local_port > 65535 \
    || 10#$target_port < 1 || 10#$target_port > 65535 )); then
    print -u2 -- "ssh-tunnel: invalid port mapping: $port_mapping"
    return 2
  fi

  ssh -N \
    -o ExitOnForwardFailure=yes \
    -L "127.0.0.1:${local_port}:${target_ipv4}:${target_port}" \
    "$ssh_host"
}
```

- [x] **Step 4: Run the focused test and syntax checks**

Run:

```bash
zsh -f tests/test_ssh_tunnel.zsh
zsh -n zshrc tests/test_ssh_tunnel.zsh
```

Expected: both commands exit 0 with no output.

- [x] **Step 5: Run the full local regression suite and diff checks**

Run:

```bash
for test_file in tests/test_*.zsh; do zsh -f "$test_file" || exit; done
git diff --check
git status --short
```

Expected: every test exits 0; `git diff --check` prints nothing; only the implementation plan, `zshrc`, and `tests/test_ssh_tunnel.zsh` are modified or untracked.

- [x] **Step 6: Commit the implementation**

```bash
git add docs/superpowers/plans/2026-08-14-ssh-tunnel.md zshrc tests/test_ssh_tunnel.zsh
git commit -m "Add validated SSH tunnel helper"
```
