# B01 formal01 incomplete execution and targeted failure observations

Formal01 terminated by SIGSEGV before the frozen comparison and primary publication completed.
This is an incomplete B attempt, not an algorithm-negative result, a completed B observation,
or a cap exceedance. No retry, new seed, source change or further result-bearing invocation
has followed. The unchanged source remains independently reviewed; actual long-path stability
is now an unresolved dependency of obtaining the trained policies and primary comparison.

## Actual invocation and investment

DM selection `cd41628b7`, integrated as `972992e1a`, selected the exact command in the technical
acceptance. Source `33e08f440c2117dcfd9457d825f42fef7b38ccd7`; configured `wsl_4070`;
task `vnfc_b01_formal_33e08f440_20260905_01`; detached cwd
`/home/wu/hmasd-worktrees/vnfc_b01_formal_33e08f440_01`; output parent
`temp/directions/variable_n_fleet_churn/b01_formal_20260905_01`.
Fresh memory admission passed; exact raw available bytes are in the retained `memory.json`.
The formal training/evaluation masters2026090501/2026090502 and formal namespace were used.

Supervisor terminal: exit139, tmux inactive,88s rounded elapsed. External `/usr/bin/time`:
**87.86s wall**,79.31user+.94system=**80.25 CPU-s**, maximum RSS780,008KiB.
It explicitly records `Command terminated by signal 11`. Its trailing `Exit status: 0`
does not override signal termination or the supervisor's139. The2700s timeout did not expire.

The selected cumulative formal investment has spent87.86s, leaving **2612.14s** of the2700s
total if DM selects another formal attempt. Failure does not allocate a fresh2700s. The prior
282.611s conditional projection was not a guaranteed bound or proof of runtime stability.
Prior checks25.61 measured wall/25.79 CPU-s and the separately recorded diagnostics remain
engineering preparation costs; their evidence and incomplete measurement boundaries are retained.

## Trustworthy progress and missing primary result

The full stdout log has20 completed-update rows: ten rounds for each arm, each192 transitions
and32 optimizer steps. Tool-produced `logged_exposure.json` summarizes these direct log facts.

| Logged completed work | Each learner |
| --- | ---: |
| Rounds | 10 |
| Complete training episodes implied by fixed32/round | 320 |
| Joint training transitions | 1920 |
| Optimizer steps | 320 |

These are lower bounds; the log does not reveal how far any next round proceeded. Last logged
relative parameter movement is MAPR .1491831934 and DIRECT .1476987924. Movement is observed;
return improvement, final policy quality and complete selected training are not.

Execution order places fixed BCRH64 episodes/384 calls and each arm's64 initial evaluation
episodes before training. Reaching round1 therefore implies those calls returned. Their endpoint
values were retained only in process memory and never published; they are **not readable primary
evidence**. Source-implied completed episode count is at least640 training +192 initial/reference
evaluation =832, or199,680 native ticks. This is a control-flow lower bound, not an independent
episode-row reconciliation. No final complete exposure total is claimed.

Output contains only `MAPR_initial.pt`, `DIRECT_initial.pt` and `b01_native.so`. The two initial
checkpoints were written/read back by the existing runner before training and are retained here.
No midpoint/final checkpoint, summary.json, training_curves.json, training_episodes.json or
evaluation_episodes.json was published. None of the five frozen final-minus-initial/comparator
contrasts is available. Do not replay initial checkpoints to manufacture a complete comparison,
resume from absent trained state, or substitute check02 non-target outcomes.

## Read-only targeted diagnosis

The kernel reported a Python thread1703953 segfault and WSL CaptureCrash associated it with
process1702677, signal11, the configured Python executable. Its instruction pointer was
`0x57824a33f4e4`; executable text mapping began `0x57824a1e1000`. The ELF executable LOAD segment
has virtual offset0x145000, yielding symbol address0x2a34e4. `addr2line`/`objdump` on this actual
executable identify **`subtype_dealloc+0x34`**, an object/GC-link write instruction. Raw kernel
and disassembly evidence is retained. This is a fault site, not root-cause attribution: it does
not prove a Python bug, native corruption, a Torch bug or hardware failure. No Python/native
call stack or crashing object identity is available from the run log.

Linux core_pattern is `|/wsl-capture-crash %t %E %p %s`; no conventional `core*` file was found
at the execution cwd, and the handler pathname was not a readable Linux file. WSL reported
capturing the crash, but this task has not recovered a usable dump. No core evidence was deleted.

The formal native library SHA256 is
`1e72526547c0709e2fbc8feb3101a09f0d9896d3e09ba52ce6e0e4ede3f1f5d8`, identical to the successful
check02 library. Compiler: Ubuntu c++13.3.0. Actual Python executable SHA256:
`ca420bd4614ae7757b4cd4938b3c663e98d2b631bda518610071d9a4ca0b509e`.
No dependency substitution occurred. Check01's HMAC exception remains unexplained and may or
may not share a cause; the observations do not establish a connection.

All new diagnosis above was inspection of existing logs, executable metadata and disassembly;
no model, native simulation, formal replay or new timing task was launched. The segfault itself
has not been reproduced. Full-history root-cause proof is not a prerequisite, but the live
execution stability dependency now requires a targeted disposition before assuming the primary
measurement can be obtained.

## Minimal next options for DM selection

1. **Recommended: one bounded fault-observation task.** First attempt to recover the already
   reported WSL crash capture for a Python/native stack; this changes no scientific computation.
   If that capture is unavailable, explicitly select a small non-target longer-path diagnostic
   on the same N7/native/PPO path with Python faulthandler enabled and a fixed bound, sufficient
   to distinguish initialization/world generation, native stepping and learner update at a crash.
   Freeze its non-target inputs, counts and cap before execution; do not treat it as a formal
   result or a new mandatory general check. No such invocation is authorized by this report.
2. Select an unchanged formal fresh attempt with fault observation enabled, explicitly accounting
   for87.86s spent and2612.14s remaining. This could produce the frozen result, but without a stack
   it currently risks another poorly localized failure. No automatic retry follows this option.
3. Hold the result attempt at the present boundary if no useful bounded diagnosis fits the
   remaining investment. This is an engineering hold with incomplete primary evidence, not a
   direction disposition or negative scientific interpretation.

There is no evidence-backed HMAC replacement, dependency upgrade, dtype/device switch or native
algorithm patch to propose. If a subsequent stack identifies a concrete dependency, return that
specific repair and ownership boundary. Do not change seeds, arms, training exposure or checkpoint
selection in response to partial target progress. Root/DM receive this complete technical return
for object-tier selection; the scientific card and historical contrary evidence stay intact.

Raw evidence: `evidence/b01_formal_20260905_01/` contains run log, receipt, external time,
logged exposure, runtime/kernel identity, fault symbol disassembly and both initial checkpoints.
Remote originals and the native library remain at the exact execution location above.
