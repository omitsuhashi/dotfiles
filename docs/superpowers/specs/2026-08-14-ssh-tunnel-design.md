# SSH Tunnel Helper Design

## Context

The current workflow opens a foreground SSH local port forward with a command such as:

```zsh
ssh -N \
  -L 127.0.0.1:8080:10.48.157.47:80 \
  local.kali
```

The SSH destination, target IPv4 address, and port mapping change between uses. The helper should accept those values directly while preserving the current foreground lifecycle.

## Command Interface

Add an interactive Zsh function named `ssh-tunnel` to `zshrc`:

```text
ssh-tunnel <ssh-host> <target-ipv4> <local-port>:<target-port>
```

Example:

```zsh
ssh-tunnel local.kali 10.48.157.47 8080:80
```

The arguments are, in order:

1. An SSH destination accepted by `ssh`, such as the configured alias `local.kali`.
2. The complete target IPv4 address as seen from the SSH destination.
3. Exactly one local-to-target TCP port mapping.

## Behavior

For the example above, the function executes the equivalent of:

```zsh
ssh -N \
  -o ExitOnForwardFailure=yes \
  -L 127.0.0.1:8080:10.48.157.47:80 \
  local.kali
```

The local listener is always bound to `127.0.0.1`; exposing it on other interfaces is outside this helper's scope. The SSH process stays in the foreground and the user stops it with `Ctrl+C`. The function returns the `ssh` exit status.

`ExitOnForwardFailure=yes` makes the SSH session fail when the requested local forward cannot be established, such as when the local port is already occupied. It does not preflight whether the final target service will accept a later forwarded connection.

## Input Validation and Errors

The function validates all input before invoking `ssh`:

- Exactly three arguments are required. Otherwise it prints the usage string to standard error and returns status 2.
- The SSH destination must be non-empty and must not start with `-`, preventing it from being interpreted as another SSH option.
- The target must contain exactly four decimal IPv4 octets, each from 0 through 255.
- The mapping must contain exactly one `:` and two decimal ports, each from 1 through 65535.

Invalid IPv4 addresses and port mappings produce a concise error on standard error and return status 2. Connection and forwarding errors from a valid invocation are reported by `ssh` itself.

## Placement and Scope

The helper belongs in `zshrc` beside the existing interactive helper functions. A standalone script is unnecessary because use from other shells and non-interactive SSH commands is not required.

The initial version supports one IPv4 target and one TCP mapping per invocation. Background process management, multiple mappings, IPv6 targets, remote forwards, SOCKS proxies, and public listener addresses are intentionally excluded.

## Verification

Add a focused Zsh regression test that stubs `ssh` and verifies:

- A valid invocation produces the exact expected SSH arguments.
- The configured SSH destination is passed as the destination, not interpreted as an option.
- Missing or extra arguments are rejected without calling `ssh`.
- Malformed and out-of-range IPv4 octets are rejected.
- Malformed, zero, and out-of-range ports are rejected.
- The helper returns the exit status from the stubbed `ssh` command.

Run the focused test, the existing dotfiles tests, `zsh -n` on changed Zsh files, and `git diff --check`.

## Acceptance Criteria

- Running `ssh-tunnel local.kali 10.48.157.47 8080:80` creates only a localhost-bound `8080` forward to `10.48.157.47:80` through `local.kali`.
- The command remains attached to the terminal until it exits or the user presses `Ctrl+C`.
- Invalid user input fails before any SSH connection attempt.
- Existing Zsh helpers continue to behave unchanged.
