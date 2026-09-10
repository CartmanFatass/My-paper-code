# CBSC native fatal P36 capability result

**COMMAND_NOT_ACCEPTED / NO_DIAGNOSTIC_RUN.** An installed native debugger is
available, but a method satisfying P36's complete debugger-plus-inferior
termination requirement was not established. This is neither debugger absence,
an observed escape, an installed-binary defect nor a scientific negative.
No diagnostic candidate process was launched.

## Authority and applied acceptance

P36 assignment `69365047a640b5447552740ab8f02ecc068f5329`,
[exact handoff](../../portfolio/handoffs/2026-09-08-p36-cbsc-native-fatal-context.md).
Entry checkout `53b90c2ccd211b6e05f8b082599d8946534c16b2`, branch `codex/cbsc`,
`C:/Projects/HMASD-worktrees/dm-cbsc-next-20260906`. Existing P32 mapping and
scientific source `d2753be86c12bfa63c404ac2cac513b914371115` were not altered.

Applied P36 acceptance sentence, verbatim:

> static command/termination review verifies debugger
> and inferior are enclosed by the complete<=120s cap (TERM115s+5s grace), without
> continuing after the first captured fatal event.

That whole-invocation requirement remains unmet by the established command
facts. DM independently reviewed the retained inventory and relevant source
ranges, accepted this no-run disposition and declined to freeze a speculative
full-run card/literal. No P36 diagnostic runtime allowance was consumed.

## Capability and actual cost

One remote inventory invocation performed the fixed `command -v gdb` and
`command -v lldb` lookups, then one selected GDB no-init batch version/help call.
It found `/usr/bin/gdb`: GNU GDB15.1, Ubuntu15.1-1ubuntu1~24.04.1,
x86_64-linux-gnu. No lldb path was returned; no alternate tool was pursued.
Relevant help covered signal stop/nopass, bounded backtrace, instruction/register
output, quit and startup/fork behavior. This establishes capability to express
the capture, not a tested target launch or ptrace containment observation.

Exit0. Remote GNU-time wall0.10s; locally measured SSH subprocess wall
0.8279999999795109s. Whole local command tool wall1.0688061s includes control-script
startup/receipt work. All are below the30s inventory bound, distinct from the
unexecuted prospective120s diagnostic cap. No target admission, scientific output
root, model, optimizer, evaluation, target import, test inferior, package operation
or setup was performed. Target/process-learning exposure is0; there is no native
fatal instruction, stack, register result or durable learner prefix for P36.

## Precise missing termination fact

The [CM capability/termination handoff](CBSC_B05_NATIVE_FATAL_P36_ROOT_HANDOFF_20260908.md)
contains exact inventory argv and versioned GDB15.1 source references. Its static
chain is: child enters a separate process group before tracing/exec; launched
inferior EXITKILL is requested during post-startup initialization. Established
post-startup EXITKILL and graceful debugger TERM/quit support later termination,
but do not prove containment during the earlier separate-pgrp startup interval
if forced KILL is needed. No live escape was observed or inferred as fact.

The exact missing requirement is **creation-through-KILL containment of both
debugger and inferior inside the one115+5s envelope**. No conforming method was
established from available command/help/source evidence. This work adds no new
source, wrapper, runtime test or setup; it does not categorically exclude every
possible wrapper. No further probe, source retrieval, test or delegation follows
this returned gap. A separately specified continuation must supply the missing
method rather than treating debugger-only timeout as complete containment.

## Retained evidence and return

Raw capability artifacts remain in
`temp/directions/capability_bound_semantic_currentness/exp/b05_native_fatal_p36_20260908_control/`
in the authoring checkout: `inventory_command.json`, `inventory.stdout`,
`inventory.stderr`, `inventory_result.json` and the locally retrieved versioned
source files named by the handoff. No source/code/test path was edited.

P28 incomplete RAW and P32 Python-frame context remain separate, unchanged
observations; no shared corrupting writer or cause is assigned. CBSC and FRRIE
exposure/causes are independent. Root integrates the explicit evidence paths;
DM owns the no-run intake, brief, audit and concrete next task request. No
STRUCT, retry, source repair, seed change, installation or diagnostic extension.
