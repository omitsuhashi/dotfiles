# fusionctl

`fusionctl` discovers existing VMware Fusion VMX files and controls an exactly
selected VM. It runs on the Fusion host and is called from a work PC through
the existing `local.omitsuhashi` SSH route.

## Install on the Fusion host

From the dotfiles checkout on the Fusion host:

```sh
cd "$HOME/dotfiles"
install_dir=$HOME/scripts
fusionctl_path=$install_dir/fusionctl
expected_target=$PWD/scripts/fusionctl

test -x "$expected_target" || {
  printf "missing or non-executable source: %s\n" "$expected_target" >&2
  exit 1
}
mkdir -p "$install_dir" || exit 1

if test -L "$fusionctl_path"; then
  current_target=$(readlink "$fusionctl_path") || exit 1
  if test "$current_target" = "$expected_target"; then
    printf "already installed: %s -> %s\n" \
      "$fusionctl_path" "$current_target"
  else
    printf "refusing to replace existing symlink:\n" >&2
    ls -ld "$fusionctl_path" >&2
    exit 1
  fi
elif test -e "$fusionctl_path"; then
  printf "refusing to replace existing path:\n" >&2
  ls -ld "$fusionctl_path" >&2
  exit 1
else
  ln -s "$expected_target" "$fusionctl_path" || exit 1
  printf "installed: %s -> %s\n" "$fusionctl_path" "$expected_target"
fi
```

This install is intentionally specific to `fusionctl`; do not invoke
`linker.sh` to install this command because its generic script-link loop may
replace an unrelated path with the same name. A missing destination is
created, the exact expected symlink is accepted as already installed, and any
normal file or differently targeted symlink is displayed and refused.

The SSH command form starts a non-login, non-interactive Zsh. It does not read
`.zprofile` or `.zshrc`, so expose both `fusionctl` and `vmrun` from the
lightweight, repository-managed `zshenv.d/fusionctl.zsh` snippet. Install a
copy in the Fusion host's private configuration directory, then add only a
guarded source line to its existing `.zshenv`; do not replace that file or
source the full `.zprofile`:

```sh
ssh local.omitsuhashi zsh -s <<'REMOTE'
set -eu

source_snippet="$HOME/dotfiles/zshenv.d/fusionctl.zsh"
install_dir="$HOME/.config/fusionctl"
installed_snippet="$install_dir/zshenv.zsh"
zshenv_path="$HOME/.zshenv"
source_line='[[ -r "$HOME/.config/fusionctl/zshenv.zsh" ]] && source "$HOME/.config/fusionctl/zshenv.zsh"'

test -r "$source_snippet" || {
  printf "missing or unreadable snippet: %s\n" "$source_snippet" >&2
  exit 1
}

mkdir -p "$install_dir"
install -m 0644 "$source_snippet" "$installed_snippet"

touch "$zshenv_path"
if grep -Fqx -- "$source_line" "$zshenv_path"; then
  printf "already configured: %s\n" "$zshenv_path"
else
  printf '\n%s\n' "$source_line" >> "$zshenv_path"
  printf "configured: %s\n" "$zshenv_path"
fi
REMOTE
```

The snippet only prepends `$HOME/scripts` and VMware Fusion's public command
directory. Existing `.zshenv` setup, such as Cargo initialization, remains in
place. The installed copy is Fusion-host-specific and is intentionally not
linked by `linker.sh` on every machine. Re-run the installation after updating
the repository copy.

Verify both prerequisites in the command environment used by non-interactive
SSH. This check exits non-zero as soon as either command is unavailable:

```sh
ssh local.omitsuhashi '
  printf "PATH=%s\n" "$PATH"
  command -v fusionctl || exit 1
  command -v vmrun || exit 1
'
```

Do not add VM operation functions to shell startup files. Calling
`$HOME/scripts/fusionctl` directly is not a complete workaround when `vmrun`
is also absent from the SSH command PATH.

## Commands

Keep `list` as a fixed quoted remote command:

```zsh
ssh local.omitsuhashi 'fusionctl list'
```

For every command taking a target, define this helper in the local Zsh session.
`printf %q` quotes each remote argument, and the resulting remote command is
passed to `ssh` as one argument:

```zsh
fusionctl_ssh() {
  if (( $# < 2 )); then
    print -u2 -- 'usage: fusionctl_ssh <host> <command> [target]'
    return 2
  fi

  local host="$1"
  local remote_command
  shift
  printf -v remote_command '%q ' fusionctl "$@"
  ssh "$host" "${remote_command% }"
}
```

Use the helper for names and exact VMX paths, including targets containing
spaces or shell metacharacters:

```zsh
fusionctl_ssh local.omitsuhashi status 'Ubuntu 24.04'
fusionctl_ssh local.omitsuhashi start 'Ubuntu 24.04'
fusionctl_ssh local.omitsuhashi ip 'Ubuntu 24.04'
fusionctl_ssh local.omitsuhashi stop 'Ubuntu 24.04'
fusionctl_ssh local.omitsuhashi status \
  '/Users/example/VMs/Lab; echo not-a-command.vmwarevm/Lab.vmx'
```

Use the exact VMX path shown by `list` when display names are duplicated.

## VM discovery root

The default is `$HOME/Virtual Machines.localized`. Override it for one remote
command when necessary:

```sh
ssh local.omitsuhashi 'FUSIONCTL_VM_ROOT="$HOME/VMs" fusionctl list'
```

## Safety behavior

- `start` is always `nogui` and does nothing if the VM is already running.
- `stop` is always `soft` and never escalates to `hard`.
- `ip` requires a running VM and VMware Tools.
- Names are exact and case-sensitive; unknown and duplicate names fail.
- VMX paths outside the discovery root are rejected.

## Local verification

```sh
zsh -n scripts/fusionctl zshenv.d/fusionctl.zsh \
  tests/test_fusionctl.zsh tests/test_fusionctl_ssh_env.zsh
zsh tests/test_fusionctl.zsh
zsh tests/test_fusionctl_ssh_env.zsh
zsh tests/test_capture_audio.zsh
git diff --check
```

After defining `fusionctl_ssh`, check its quoting locally without a network
connection. Here `ssh` only captures its arguments; the test-only `eval`
simulates the remote Zsh parsing the one captured command against a fake
`fusionctl`:

```zsh
(
  set -eu
  check_dir="$(mktemp -d)"
  trap 'rm -rf "$check_dir"' EXIT
  typeset -a ssh_args=() fusionctl_args=()

  ssh() { ssh_args=("$@") }
  fusionctl() { fusionctl_args=("$@") }

  marker="$check_dir/injected"
  target="VM name; touch $marker; \$(touch $marker.subshell) & echo unsafe"
  fusionctl_ssh local.omitsuhashi status "$target"

  (( ${#ssh_args} == 2 ))
  eval "${ssh_args[2]}"
  (( ${#fusionctl_args} == 2 ))
  [[ "${fusionctl_args[1]}" == status ]]
  [[ "${fusionctl_args[2]}" == "$target" ]]
  [[ ! -e "$marker" && ! -e "$marker.subshell" ]]
  print -r -- 'PASS: SSH target remained one data argument'
)
```

Real VM state changes require an explicitly selected approved VM and are not
performed by the automated tests.
