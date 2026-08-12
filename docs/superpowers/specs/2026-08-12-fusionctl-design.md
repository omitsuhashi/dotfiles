# fusionctl design specification

Date: 2026-08-12

## Purpose

Provide a small host-side CLI for controlling existing VMware Fusion virtual
machines from a work PC through SSH. The normal entry point is one remote
command, for example:

```sh
ssh fusion-host fusionctl start Ubuntu
```

The CLI removes the need to repeat the VMX path and the four `vmrun` command
forms. It does not replace the existing SSH configuration or provide guest SSH
access.

## Scope

The first version supports these commands:

```text
fusionctl list
fusionctl start <name-or-vmx-path>
fusionctl status <name-or-vmx-path>
fusionctl ip <name-or-vmx-path>
fusionctl stop <name-or-vmx-path>
```

`fusionctl` runs on the Fusion host. The caller reaches it through an existing
SSH host alias. The host must already satisfy these prerequisites:

- `vmrun` is executable by command name in the SSH command environment.
- `fusionctl` is installed in the non-interactive SSH `PATH`.
- The SSH user can read the VM bundles and operate them with `vmrun`.

Provisioning VMs, changing VM configuration, guest SSH, snapshots, suspend,
hard power-off, and exposing the Fusion REST API are outside this version.

## Artifact placement

The implementation is a standalone Zsh script at `scripts/fusionctl`. It is
not implemented as a shell alias or function and no VM-control logic is added
to `zprofile` or `zshrc`.

The repository's existing `linker.sh` mechanism exposes scripts under
`$HOME/scripts`. Installation must additionally ensure that the resulting
`fusionctl` command is visible in the actual non-interactive SSH `PATH`; this
is verified with:

```sh
ssh fusion-host 'command -v fusionctl && command -v vmrun'
```

The concrete symlink destination is selected from the host's measured SSH
`PATH`, rather than assuming that an interactive-shell `PATH` also applies to
remote commands.

## VM discovery

The scan root is:

```text
${FUSIONCTL_VM_ROOT:-$HOME/Virtual Machines.localized}
```

All regular files ending in `.vmx` below that root are candidates. Results are
sorted deterministically by display name and then full path.

For a VMX inside a `.vmwarevm` bundle, the display name is the bundle basename
with the `.vmwarevm` suffix removed. A VMX not contained in such a bundle uses
its `.vmx` basename without the suffix. Discovery never means "operate on the
first result"; every mutating command performs exact target resolution.

The root must exist and be readable. Otherwise, `fusionctl` exits with a
configuration error and reports the resolved root.

## Target resolution

For commands requiring a target, all remaining command-line words are joined
with a single space. This permits both quoted local execution and natural SSH
usage with names containing spaces:

```sh
fusionctl start 'Ubuntu 24.04'
ssh fusion-host fusionctl start Ubuntu 24.04
```

The resulting target is resolved in this order:

1. Exact full-path match against a discovered VMX path.
2. Exact, case-sensitive display-name match.

Prefix, substring, case-insensitive, and fuzzy matches are not accepted. If no
candidate matches, the command fails and suggests `fusionctl list`. If more
than one candidate has the same display name, the command fails and prints the
matching full paths; the caller must then supply a full path.

Only paths discovered under the configured scan root are accepted. Supplying
an arbitrary existing VMX path outside that root does not bypass this boundary.

## Running-state model

`vmrun -T fusion list` is the authoritative source for currently running VMs.
Its first summary line is ignored and each remaining line is treated as a VMX
path. A discovered VM is `running` only when its full path exactly equals one
of those lines; otherwise it is `stopped`.

No substring or basename comparison is used. This avoids treating two VMs with
similar names as the same machine.

## Command behavior

### `list`

Print every discovered VM, including stopped VMs, as tab-separated columns:

```text
NAME    STATE    PATH
Ubuntu running  /Users/example/Virtual Machines.localized/Ubuntu.vmwarevm/Ubuntu.vmx
Kali    stopped  /Users/example/Virtual Machines.localized/Kali.vmwarevm/Kali.vmx
```

The header is always printed. An empty scan is successful and prints only the
header.

### `status`

Resolve the target and print exactly one of:

```text
running
stopped
```

Both states return success. Selection or `vmrun` failures return a non-zero
status.

### `start`

If the VM is already running, print `already running: <name>` and return
success without calling `vmrun start`.

Otherwise execute:

```sh
vmrun -T fusion start "$vmx" nogui
```

`nogui` is mandatory. A successful `vmrun` exit is reported as
`started: <name>`. No Fusion GUI or guest SSH session is opened.

### `ip`

If the VM is stopped, fail immediately and tell the caller to start it.
Otherwise execute:

```sh
vmrun -T fusion getGuestIPAddress "$vmx" -wait
```

The IP address from `vmrun` is written to standard output unchanged. VMware
Tools availability and `vmrun -wait` timing remain VMware responsibilities;
the user can interrupt the wait with Ctrl+C.

### `stop`

If the VM is already stopped, print `already stopped: <name>` and return
success without calling `vmrun stop`.

Otherwise execute:

```sh
vmrun -T fusion stop "$vmx" soft
```

`soft` is mandatory. A successful `vmrun` exit is reported as
`stopped: <name>`. The wrapper never retries with `hard`; forced power-off must
be a separate, explicit manual action.

## Output and exit status

- Normal results go to standard output.
- Usage, configuration, selection, and `vmrun` errors go to standard error.
- Exit `0`: requested operation succeeded or its idempotent state already held.
- Exit `1`: an external operation such as `vmrun` failed.
- Exit `2`: usage, configuration, or target-selection error.

The script propagates enough context to identify the failed operation and VM,
but does not hide `vmrun` diagnostics.

## Safety properties

- Paths and names are always passed as quoted arguments; no `eval` is used.
- Mutating commands require an exact, unique discovered target.
- Running-state checks compare exact full paths.
- Start is always headless with `nogui`.
- Stop is always graceful with `soft`; there is no automatic escalation.
- Repeated start and stop calls are idempotent.
- Existing SSH routes and guest access remain separate from VM power control.

## Verification strategy

Add `tests/test_fusionctl.zsh`, following the repository's existing standalone
Zsh test style. Tests create temporary `.vmwarevm` bundles and place a fake
`vmrun` first in `PATH`. The fake records arguments and provides controlled
`list` and IP responses without touching a real VM.

The automated suite covers:

- discovery and deterministic listing of running and stopped VMs;
- names and paths containing spaces;
- exact status matching;
- `start` uses `-T fusion`, `nogui`, and the resolved VMX path;
- `stop` uses `-T fusion`, `soft`, and the resolved VMX path;
- start/stop idempotence avoids unnecessary mutating calls;
- IP lookup requires a running VM and uses `-wait`;
- missing, unknown, and duplicate names fail safely;
- arbitrary paths outside the scan root are rejected;
- operation with a minimal SSH-like `PATH` containing `vmrun` and required
  system utilities;
- Zsh syntax validation with `zsh -n scripts/fusionctl`.

After automated tests pass, host verification proceeds in increasing-risk
order:

1. Confirm `command -v fusionctl` and `command -v vmrun` through the same SSH
   command path the user will use.
2. Run `fusionctl list` and compare discovered VMX paths with the Fusion host.
3. Run `status` and `ip` against an already-running VM where available.
4. Perform real `start` and `stop` only with an explicitly selected disposable
   or approved VM.

Real-host VM state changes are not part of the unit test suite.

## Primary technical reference

The command forms are based on *Using VMware Fusion Pro 13*, pp. 161-175:

<https://techdocs2-prod.adobecqms.net/content/dam/broadcom/techdocs/us/en/pdf/vmware/desktop-hypervisors/fusion/vmware-fusion-pro-13.pdf>

The guide defines `vmrun -T fusion`, `list`, `start <vmx> [gui|nogui]`,
`stop <vmx> [hard|soft]`, and `getGuestIPAddress <vmx> [-wait]`.
