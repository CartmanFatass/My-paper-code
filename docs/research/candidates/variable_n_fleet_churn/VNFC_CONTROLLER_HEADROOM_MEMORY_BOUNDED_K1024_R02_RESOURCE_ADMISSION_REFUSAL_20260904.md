# VNFC memory-bounded K=1024 R02 — resource admission refusal

- Object: `VNFC-CONTROLLER-HEADROOM-A-RECON-MEMORY-BOUNDED-K1024-R02`
- Evidence class: `A/RECON`
- Launch candidate SHA: `21a65bd8d120563e201e3bb4b30d47ea58379247`
- Refused at: `2026-09-04T12:10:55.099046Z`
- Disposition recorded: `2026-09-04T12:13:37Z`
- Status: `BLOCKED_RESOURCE_ADMISSION`
- Scientific polarity: none

## Direct prelaunch facts

The final focused prelaunch suite ran on the pushed launch candidate:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider `
  --basetemp C:/Projects/HMASD-worktrees/codex-vnfc-controller-headroom-20260904/temp/directions/variable_n_fleet_churn/test/controller_headroom_mb1024_prelaunch_21a65bd8 `
  tests/experiments/candidates/variable_n_fleet_churn_headroom/test_controller_headroom.py
```

It passed `17 passed, 1 warning in 12.94s`. No code or scientific input changed afterward.

Immediately afterward, the mandatory central admission was invoked exactly once:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe `
  scripts/hmasd_resource_preflight.py admit-memory `
  --out temp/directions/variable_n_fleet_churn/exp/controller_headroom_mb1024_r02/attempt_01_preflight.json
```

The receipt directly reports:

- measurement source: `GlobalMemoryStatusEx`;
- physical available: `3,986,948,096` bytes;
- effective available: `3,986,948,096` bytes;
- required minimum: `4,294,967,296` bytes;
- physical pass: `false`;
- effective pass: `false`;
- overall pass: `false`; and
- failure reason: `available physical memory is below 4 GiB`.

The intended result root
`temp/directions/variable_n_fleet_churn/exp/controller_headroom_mb1024_r02/attempt_01_result`
does not exist. A Python-process query found zero runner processes targeting it. No RNG master,
target fixture, model, optimizer, scientific output, stdout/stderr log, or result process was
created. The object has no observation or polarity.

The earlier memory-bounded saturation pilot remains technically admitted. This refusal measures
only transient host availability for the result invocation; it neither contradicts the pilot's
191,859,553-byte conservative process high water nor changes the frozen 723.80-second projection.

## Fresh admission after the first pressure change

UCOPE completed without a runner. At `2026-09-04T12:16:10Z`, a read-only operating-system query
reported 5,040,775,168 free physical bytes, making one official retry reasonable rather than a
rapid blind poll. A distinct fresh receipt was therefore requested at
`temp/directions/variable_n_fleet_churn/exp/controller_headroom_mb1024_r02/attempt_02_preflight.json`.

The authoritative `GlobalMemoryStatusEx` measurement at `2026-09-04T12:16:21Z` reported physical
and effective availability of 4,101,500,928 bytes. Both remained below 4,294,967,296; both floor
flags and `passed` were false. The short-lived discrepancy with the earlier read-only observation
is host pressure variation, not a measurement failure and not evidence about this object.

No result root or process was created. The clean wait remains controlling until another meaningful
pressure change, such as completion of active FSD work, makes one later official admission
reasonable. No rapid polling is permitted.

## Decisions this refusal produces

Options:

- (a) wait at the clean resource boundary until active FSD/UCOPE pressure changes and free memory
  is plausibly at least 4 GiB, then make one new fresh central admission using a new receipt and
  launch only if it passes;
- (b) launch below the mandatory threshold;
- (c) kill or suspend unrelated work to manufacture capacity; or
- (d) convert the resource refusal into K=1024 or VNFC scientific polarity.

Recommendation: **(a)**. It preserves the accepted object and all evidence, respects actual host
capacity, and is reversible. Option (b) violates the mandatory launch condition, (c) exceeds this
direction's authority and would disrupt other work, and (d) violates the scientific/engineering
boundary.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Provenance:
`OWNER_DELEGATED`, with Root's 2026-09-04 capacity coordination. Do not poll rapidly. No human
approval is required once a meaningful pressure change makes a new check reasonable. The next
fresh receipt must have a distinct path; the refused receipt remains historical evidence.

This is an object-tier wait, not a Direction- or Portfolio-tier lifecycle decision. No MAPR or Pro
handoff is opened at this boundary.

## Prospective `REMOTE_FIRST` invocation route

Root changed runtime routing at `2026-09-04T13:10:46Z`. Because no local scientific process was
ever accepted, no target root exists, and portability is declared before any target output, the
unchanged sole R02 invocation is prospectively portable and now `REMOTE_FIRST`.

The direction must remain at this clean boundary until Root explicitly marks
`.codex/hmasd-compute.toml` active. Then the launch uses a detached remote worktree at the exact
pushed commit containing this route and exactly one remote `agent-task` command. That command must
perform the remote `admit-memory` and, only on its success, the exact frozen runner invocation in
one accepted remote payload. The remote receipt, interpreter, argv, root, SHA, acceptance fact,
PID/process fact, and terminal result must be recorded.

The failed local `attempt_01_preflight.json` and `attempt_02_preflight.json` receipts do not admit a
remote invocation. Local execution is forbidden unless remote acceptance is definitively absent,
portability remains declared before output, and a distinct new local admission passes. An uncertain
remote acceptance state is a hard no-duplicate boundary: consult authoritative remote state and do
not send or launch again blindly.

This changes only the execution host. Population, seed, bytes, treatment, comparators, numerical
and RNG semantics, result rule, stop rule, exposure, claim ceiling, and one-invocation limit remain
unchanged. It is Root capacity coordination, not new scientific polarity or a MAPR/Direction
decision.
