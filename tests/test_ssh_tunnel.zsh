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
