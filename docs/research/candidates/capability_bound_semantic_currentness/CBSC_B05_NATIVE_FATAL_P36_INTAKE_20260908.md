# CBSC P36 capability and no-run intake — 2026-09-08

Claim: the remote node has an installed debugger that can express the intended native capture, but this preparation did not establish the complete debugger-and-inferior termination bound required to launch it.
Binding structure: **systems / information flow**. This is runtime diagnostic preparation; no effect arising from multi-agent partial observability or non-stationarity is tested.

**CAPABILITY_PRESENT / COMMAND_NOT_ACCEPTED / NO_DIAGNOSTIC_RUN.** Accept the
read-only capability record and return the specific missing termination fact.
No native diagnostic card, executable launch literal or accepted handle was frozen.

## Authority, question and checked evidence

[P36](../../portfolio/handoffs/2026-09-08-p36-cbsc-native-fatal-context.md) at
`69365047a640b5447552740ab8f02ecc068f5329` allocated bounded installed-debugger
inventory/version/help, followed conditionally by one native capture only after
command acceptance. This intake covers the completed preparation, not a new
learning object. Its A/RECON record is the named inventory and static measurement
path; the conditional diagnostic never reached a prospective freeze.

The DM checked the complete [CM E0](CBSC_B05_NATIVE_FATAL_P36_RESULT_EVIDENCE_20260908.md)
and [capability/termination handoff](CBSC_B05_NATIVE_FATAL_P36_ROOT_HANDOFF_20260908.md)
at `b7163b57197dfc91771a624d6c74f00b263aa13d` against P36, the retained exact
inventory argv, stdout, stderr and result JSON, and the relevant retained GDB15.1
source ranges. The source review covered child process-group creation, tracing/
exec ordering and post-startup EXITKILL setup. It did not rerun the inventory,
launch a test inferior, import the target or reproduce the installed binary.

Applied P36 acceptance sentence, verbatim:

> static command/termination review verifies debugger
> and inferior are enclosed by the complete<=120s cap (TERM115s+5s grace), without
> continuing after the first captured fatal event.

This explicit allocation requirement is unmet. [Evidence-spec](../../specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md) sections 4, 5.1 and
11.8 distinguish credible observation from a learner result and proportional
engineering acceptance from scientific polarity. This is no new general launch
condition, and neither a debugger failure nor a scientific negative is inferred.

## Observation, counts and receipts

One bounded inventory session on `hmasd-wsl-node` found `/usr/bin/gdb`, GNU GDB
15.1, Ubuntu `15.1-1ubuntu1~24.04.1`, configured `x86_64-linux-gnu`. The selected
no-init batch help covered signal stop/nopass, backtrace, instruction/register
output, quit and startup/fork behavior. The fixed lldb lookup returned no path;
this is not an exhaustive machine-wide absence claim.

| Quantity | Retained observation or limit |
| --- | --- |
| Capability sessions / selected GDB version-help calls | 1 / 1; exit 0 |
| Remote inventory GNU-time wall | 0.10 s |
| Local SSH subprocess wall | 0.8279999999795109 s |
| Whole local command-tool wall | 1.0688061 s, including control-script work |
| Inventory bound | 30 s; met |
| Diagnostic target launches / imports / test inferiors | 0 / 0 / 0 |
| Target model / optimizer / evaluation / outputs | 0 / 0 / 0 / 0 |
| New independent training seeds / complete RAW-STRUCT pairs | 0 / 0 |
| Native fatal instruction / stack / registers | No diagnostic observation |
| Prospective diagnostic cap | 115 s + 5 s; unspent, no accepted command |

The timing layers overlap and must not be added. Source inspection occurred on
the local control plane; its full wall/CPU cost was not measured. Aggregate CPU,
peak RSS, scratch and complete preparation critical path are
`resources_unmeasured`. These omissions do not invalidate the retained inventory.
No fresh result-bearing admission was needed or performed because no diagnostic
target was launched. The GDB metadata process is not a learner invocation.

Raw evidence remains in the authoring checkout under
`temp/directions/capability_bound_semantic_currentness/exp/b05_native_fatal_p36_20260908_control/`:
`inventory_command.json`, `inventory.stdout`, `inventory.stderr`,
`inventory_result.json` and the versioned source files named in the CM handoff.
There is no diagnostic output root or accepted experiment handle for Root to
observe, and no terminal collection remains outstanding.

## Bounded interpretation and remaining fact

The strongest support is direct installed version/help output: the debugger can
express the selected observation. The limiting static evidence is that upstream
GDB15.1 moves the child into a separate process group before tracing/exec, while
the cited launched-inferior EXITKILL setup occurs after startup. Established
EXITKILL supports debugger-death termination later; an ordinary timeout of the
debugger process group does not establish containment during the earlier window.
Graceful TERM/quit also does not establish the forced-KILL case there.

This is an unmet static fact, not an observed escaping inferior, an installed
Ubuntu binary defect or proof that every possible wrapper fails. The binary was
not reproduced from the cited upstream source, and kernel ptrace behavior was
not probed. The missing fact is **containment of both debugger and inferior from
creation through startup, capture, publication and forced termination inside the
same 115+5-second envelope**. No conforming method was established here.

No new claim is made about P28's incomplete RAW run or
[P32's eight Python frames](CBSC_B05_FIRST_FAULT_P32_INTAKE_20260908.md).
P28 retained 24 updates before its fault; P32 faulted during initial projection
before the training loop. Their differing progress remains a limitation on any
shared-cause story. P36 supplies no native PC, corrupting writer, patch target,
reward or representation effect. CBSC and FRRIE evidence remains separate.

No P36 diagnostic prediction was frozen or scored; the owner's prediction is
**not taken (unattended)**. P32's previously scored context prediction is not
scored again. B05's paired MEI 0.25 and absent matched tuned headroom remain;
the missing pair is still needed to read that MEI. Existing B04 RAW 12.0375 versus
REQUEST_ONLY 12.375 and absent STRUCT are unchanged. No accepted mechanism-level
science was added, so DIRECTION, recasts, C status, lifecycle, priority and UAV
entry remain unchanged.

This preparation needs **none** of [engineering-scope](../../../project/ENGINEERING_SCOPE_SPEC.md) section 4's added machinery.
It added no source, wrapper, package, runtime instrumentation or test; no section
5 budget breach occurred. The prospective native reporting remained unexecuted.
This was pure capability collection/static preparation with the same CM, not a
new coding assignment or a fourth model-comparison batch.

## Decisions this intake produces

1. **Object / technical:** (a) accept installed capability and the precise unmet
   bound as a no-run result; (b) infer debugger absence or a live containment
   failure; (c) accept the unsupported all-phases bound. Recommend/select **(a)**.
   Direct capability is reportable; the required complete bound is not established.
2. **Object / selection:** (a) end this preparation and return the containment
   need below for a separately specified continuation; (b) launch a target, probe,
   setup or source wrapper from this record; (c) silently exclude inferior startup
   from the cap. Recommend/select **(a)**. No additional work is released here.

Owner-delegated decision (unattended, 2026-09-03 instruction): (a) for both.
Both choices are reversible; owner flags **none**. Entry and intake owner review
queries returned []; relevant audit owner fields were empty. There is no new
card or direction decision requiring a duplicate P1/P2 item. The
[Chinese brief](../../portfolio/owner/briefs/capability_bound_semantic_currentness/2026-09-08_P36.md)
is this completed capability result's owner surface. A/B have no consumption
state; the conditional diagnostic was never invoked.

## Concrete downstream need

Return through Root to Portfolio a bounded engineering continuation to establish
the missing creation-through-forced-KILL containment method for the debugger and
inferior under P36's existing complete cap. The evidence supports retaining the
same source `d2753be86c12bfa63c404ac2cac513b914371115`, RAW seed 21223, prepared
system312 runtime, CPU FP32 with one Torch thread and original schedule. It selects no patch or
new runtime. A conforming command-only method may suffice; if establishing the
method requires a utility, source wrapper, runtime assessment or setup, that work
must be specified rather than silently added to this returned preparation.

The desired scientific observation remains one first-fatal native instruction
and bounded context, not a complete causal diagnosis. The unchanged possible
algorithm work is one arm x 48 x 8 training episodes, at most 768 Adam updates,
64 policy evaluations and 96 rule passes; the unaccepted diagnostic would add
debugger work and share one 120-second cap. Those are ceilings, not zero learner
exposure or a completion forecast. No extra validation or diagnostic invocation
is authorized by this intake.

Further technical investment is a Portfolio allocation question. Root receives
the exact missing fact, not a request to interpret the science or choose the next
research object. Native diagnosis is not a prerequisite for an independently
justified B path. The scientific next discriminator remains a complete fresh
RAW/STRUCT native-return pair; P36 adds no evidence for that comparison.
