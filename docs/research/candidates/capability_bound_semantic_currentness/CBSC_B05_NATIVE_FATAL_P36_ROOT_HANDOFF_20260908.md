# CBSC native fatal P36: capability and termination finding

**COMMAND_NOT_ACCEPTED / NO_DIAGNOSTIC_RUN.** Installed debugger capability is
established; whole-invocation containment is not.
No diagnostic launch is accepted by this record. GDB15.1 can express the selected
first-stop instruction/native-stack/register capture, but the ordinary outer
timeout does not by itself cover every inferior startup phase. No target process,
import, installation, test inferior, source edit or diagnostic invocation occurred.

## Assignment and installed capability

P36 assignment `69365047a640b5447552740ab8f02ecc068f5329`,
[Portfolio handoff](../../portfolio/handoffs/2026-09-08-p36-cbsc-native-fatal-context.md).
Authoring checkout `C:/Projects/HMASD-worktrees/dm-cbsc-next-20260906`,
`codex/cbsc`, entry clean at `53b90c2ccd211b6e05f8b082599d8946534c16b2`.
P32 source/call-path mapping and named retained evidence are reused.

One bounded remote no-init inventory/version/help command found `/usr/bin/gdb`:
GNU GDB (Ubuntu15.1-1ubuntu1~24.04.1)15.1, configured x86_64-linux-gnu. The fixed
lldb lookup returned no path; no alternative was installed or explored. GDB help
covered signal stop/nopass, bounded backtrace, instruction examination, register
listing, quit and startup/fork options. Command exit0, remote wall0.10s, complete
SSH subprocess wall0.8279999999795109s, within the30s inventory bound. These are
capability facts, not ptrace/inferior runtime observations.

Exact inventory argv (already executed once; retained here as evidence):

```json
{
  "argv": [
    "ssh",
    "-o",
    "BatchMode=yes",
    "-o",
    "ConnectTimeout=10",
    "hmasd-wsl-node",
    "/usr/bin/time -f inventory_wall_seconds=%e /usr/bin/timeout --signal=TERM --kill-after=2s 25s /usr/bin/env -u BASH_ENV -u ENV /bin/bash --noprofile --norc -c 'command -v gdb || true\ncommand -v lldb || true\nif command -v gdb >/dev/null 2>&1; then\n  gdb --nx --nh --batch -ex \"show version\" -ex \"help handle\" -ex \"help info registers\" -ex \"help backtrace\" -ex \"help x\" -ex \"help quit\" -ex \"help set startup-with-shell\" -ex \"help set detach-on-fork\" -ex \"help set follow-fork-mode\"\nelif command -v lldb >/dev/null 2>&1; then\n  lldb --no-lldbinit --version\n  lldb --no-lldbinit --batch -o \"help process launch\" -o \"help process kill\" -o \"help thread backtrace\" -o \"help register read\" -o \"help disassemble\" -o \"help quit\"\nelse\n  /usr/bin/printf '\"'\"'NO_INSTALLED_GDB_OR_LLDB\\n'\"'\"'\nfi'"
  ],
  "complete_bound_seconds": 30
}
```

Raw evidence in the authoring checkout:
`temp/directions/capability_bound_semantic_currentness/exp/b05_native_fatal_p36_20260908_control/`
(`inventory_command.json`, `inventory.stdout`, `inventory.stderr`,
`inventory_result.json`). Source references below were read on the local control
plane; they did not invoke the node's target or add a package operation.

## Static containment finding

GDB15.1 upstream sources were retrieved from the versioned sourceware mirror:

- [fork-child.c](https://raw.githubusercontent.com/RTEMS/sourceware-mirror-binutils-gdb/gdb-15.1-release/gdb/fork-child.c),
  `postfork_child_hook`, lines103-109: the child enters a separate process group
  even when no new terminal session is created.
- [nat/fork-inferior.c](https://raw.githubusercontent.com/RTEMS/sourceware-mirror-binutils-gdb/gdb-15.1-release/gdb/nat/fork-inferior.c):
  the child calls that hook before `traceme_fun` and exec.
- [inf-ptrace.c](https://raw.githubusercontent.com/RTEMS/sourceware-mirror-binutils-gdb/gdb-15.1-release/gdb/inf-ptrace.c):
  `create_inferior` completes startup before `post_startup_inferior`.
- [linux-nat.c](https://raw.githubusercontent.com/RTEMS/sourceware-mirror-binutils-gdb/gdb-15.1-release/gdb/linux-nat.c):
  `linux_nat_ptrace_options` requests `PTRACE_O_EXITKILL` for launched, non-attached
  inferiors; `post_startup_inferior` applies these options.
- [nat/linux-ptrace.c](https://raw.githubusercontent.com/RTEMS/sourceware-mirror-binutils-gdb/gdb-15.1-release/gdb/nat/linux-ptrace.c):
  supported options are tested and applied through event-reporting setup.

Therefore a launched tracee with EXITKILL established has a debugger-death kill
path. This does not prove containment during the earlier interval after the child
has left the timeout process group but before EXITKILL is established. A KILL of
only the debugger cannot be presented as an all-phases inferior bound from these
facts. Graceful GDB quit/kill behavior also does not alone settle that forced-KILL
interval. No live scheduling claim or measured escape is asserted: this is a
specific missing static termination fact. The installed Ubuntu binary was not
reproduced from these upstream sources, and kernel ptrace behavior was not probed.

The P36 assignment explicitly charges debugger startup and inferior startup to
the same120s envelope, so the interval cannot silently be excluded from acceptance.
No conforming command-only closure was established from the available evidence.
This preparation adds no source, wrapper, runtime containment test or setup; it
does not assert that every possible new wrapper is categorically forbidden.

## Preserved prospective question and unresolved handoff

Scientific source remains `d2753be86c12bfa63c404ac2cac513b914371115`, existing cwd
`/home/wu/hmasd-worktrees/cbsc-opportunity-credit-b05-20260907`, RAW seed21223 and
P17 system312 lexical interpreter. Original B1_RUN/public information/host/credit/
optimizer, CPUFP32/Torch1,48x8 schedule/768Adam ceiling,0/48 evaluations, RAW rules
and publication remain fixed. P28 and P32 are separate observations and do not
identify a shared writer or cause.

The intended capture remains at most32 current-thread native frames, one
instruction at the stopped PC and a bounded named general-register set, followed
by kill/quit with no continue. Normal ASLR must be preserved with
`set disable-randomization off`; no startup shell, auto-loaded scripts, debuginfo
downloads, locals/full frames or broad memory reads. This describes the selected
observation, not an executable launch payload. No diagnostic handle was accepted.

The concrete unresolved need is containment covering the separate-pgrp inferior
from creation through debugger startup, capture and forced termination under the
one115+5s envelope, supported within the existing command-only scope. Until that
is established, no Root-ready launch literal or diagnostic-runtime acceptance is
claimed. DM independently inspected the inventory and source ranges and accepted
COMMAND_NOT_ACCEPTED / NO_DIAGNOSTIC_RUN. No speculative full-run card or literal
was frozen. Return the creation-through-KILL containment requirement through
DM/Root; no installation, probe, patch, launch or reuse of an old allowance occurs.
