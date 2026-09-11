# B01 formal01 incomplete-attempt intake

Formal01 did not produce the frozen B comparison. It terminated by SIGSEGV after ten logged
training rounds per arm, before midpoint/final checkpoints or primary JSON publication.
Preserve its training-progress and cost facts as an incomplete attempt, with no performance
polarity. This does not consume the B object or reopen any historical VNFC result.

## Evidence and rule applied

DM read the complete CM `VNFC_N7_DIRECT_RETURN_B01_FORMAL01_TECHNICAL_STATUS_20260905.md`
and all retained text/JSON evidence under `evidence/b01_formal_20260905_01/` at `b804b1ca6`:
run log, logged exposure, external time, memory receipt, runtime/kernel identities and fault
symbol/disassembly. The two retained initial checkpoints are evidence of initial publication;
DM did not execute them. The controlling card is `VNFC_N7_DIRECT_RETURN_B01_SCIENCE_CARD_20260905.md`;
the preceding execution selection is `VNFC_N7_DIRECT_RETURN_B01_CHECK02_INTAKE_AND_FORMAL_SELECTION_20260905.md`.
The exact accepted source remains `33e08f440c2117dcfd9457d825f42fef7b38ccd7`.

Evidence spec 11.8.7 states: "Report observed exception, exit, missing output and counts
immediately. Root-cause attribution requires direct evidence, but reproducing and uniquely
locating every historical cause is not a universal prerequisite for later work. Repair or
check a defect that threatens reward, information access, comparison, training or the primary
measurement." It also states: "A damaged primary measurement cannot support its dependent
performance claim; independently trustworthy narrower facts remain reportable."

This attempt lacks the requested terminal comparison and primary records, so it cannot support
the card's five performance contrasts. A process crash is not evidence that either algorithm
is ineffective. Completed-update logs remain readable at their narrower ceiling. The original
check01 HMAC failure, check02 success, E01 engineering stop and historical learner losses all
retain their original meaning. No direction/Portfolio disposition follows.

## Actual invocation, counts and publication boundary

Task `vnfc_b01_formal_33e08f440_20260905_01` ran on `wsl_4070`, detached cwd
`/home/wu/hmasd-worktrees/vnfc_b01_formal_33e08f440_01`, with the selected formal namespace,
training seed 2026090501 and evaluation seed 2026090502. Fresh same-node memory admission
passed at **15,406,366,720 bytes** both physical and effective available. Tracker observed
terminal exit 139 and inactive tmux; DM acknowledged that terminal notification.

External complete chain: **87.86 wall seconds**, **79.31 user + .94 system = 80.25 CPU seconds**;
maximum RSS 780,008 KiB. `whole_time.txt` records "Command terminated by signal 11". Its trailing
"Exit status: 0" does not supersede signal termination and the supervisor's exit 139. The
supervisor's 88 seconds is rounded elapsed time. This was not expiration of the 2700-second cap.

DM independently parsed the twenty completed-update JSON log rows. Each arm records consecutive
rounds 1 through 10, **1920 joint training transitions and 320 optimizer steps**. With the
unchanged six decisions per episode, these imply **320 completed training episodes per arm**.
The last logged relative parameter movement is MAPR .1491831934 and DIRECT .1476987924.
DIRECT's residual output parameter norm is .1830907134. These are progress lower bounds:
the following round may have performed unlogged work. No complete exposure total is claimed.

DM also read the accepted `experiment.py` execution order: fixed BCRH and the initial evaluation
of both arms return before round-one collection. Thus reaching training implies 64 BCRH and
64 initial evaluation episodes per arm returned. Their endpoint values were held in process
memory and not published. The resulting **832 episodes / 199,680 ticks** lower bound is an
inference from control flow and logged training, not an episode-row reconciliation or recoverable
primary readout. It cannot be used to infer favorable or unfavorable return.

The existing runner wrote/read two initial checkpoints, retained with the raw evidence. There
is no midpoint/final checkpoint, summary, training curve JSON, training-episode JSON or evaluation
JSON. Do not reconstruct missing final policies, replay initial policies to manufacture the
comparison, or substitute the non-target check02 results. No scientific valid-result brief or
prediction score is available; the owner's prediction remains not taken (unattended).

## Fault observation and remaining investment

The kernel record and actual executable's ELF mapping/disassembly place the observed instruction
at `subtype_dealloc+0x34`, an object/GC-link write. This is a fault site, not a demonstrated Python,
Torch, native-memory or hardware cause. The run supplied no Python/native call stack or object
identity. WSL reported a crash capture; no usable dump had been recovered in CM's first return.
The formal native library byte digest equals check02's. No dependency or source substitution
occurred. This neither proves a shared cause with check01 nor rules one out.

The formal cumulative cap is unchanged: **2700 - 87.86 = 2612.14 seconds remaining**. A technical
failure grants no fresh 2700-second allocation. Check01/check02's measured 25.61 wall / 25.79 CPU
seconds and prior incompletely timed diagnostics remain separately visible engineering costs.
The earlier 282.611-second complete formal projection was conditional, not actual completion
or a guarantee of stability. Later attempted work must report its actual cumulative use.

DM selected one short existing-capture read, restricted to this process/time and relevant WSL
paths, with an approximately 120-second search bound. CM's return `f9c37993f`,
`VNFC_N7_DIRECT_RETURN_B01_EXISTING_CORE_READ_20260905.md`, records completion from
00:04:41Z to 00:06:02Z. This inspected existing evidence without a model, rollout, build,
runtime replay or source change. Its administrative elapsed time is not a new formal allocation.

DM read that complete return and `existing_core_backtrace.txt`. The matching 651,046,912-byte
core remains at its original remote WSL crash-capture path cited in the return. GDB's main-thread
chain is `subtype_dealloc -> builtin_sum -> Python evaluation -> THPFunction_apply`; other
captured threads are waiting in autograd and CUDA polling. No environment native function is
active on this captured stack, which does not exclude earlier native corruption. GDB's
core/executable and libcuda build-ID warnings remain, and `py-bt` was unavailable. No exact
Python fault line or root cause is established. The source's exact-roster-mean/Fraction-sum path
is consistent with the chain, but remains an inference and does not justify replacing that mean.

## Decisions this intake produces

| Option | Work, value and limit | Recommendation |
| --- | --- | --- |
| A. One unchanged formal fresh attempt with Python fault-stack output enabled | Preserve the exact selected learning comparison and opportunity for a B result; observe available Python frames if the fault returns on the actual target path. Same 4544 episodes / 1,090,560 ticks / 2048 optimizer steps per arm. Previous complete conditional projection about 282.61s plus unmeasured fault-handler overhead, with a strict remaining-investment timeout. Completion is not guaranteed. | Recommended and selected |
| B. First create/run an eleven-round non-target diagnostic | Two arms × 11 rounds × 32 episodes, plus 64-episode evaluation at 0/5/11 and fixed BCRH64: 1152 total episodes / 276,480 ticks / 352 optimizer steps per arm. Stored-unit conditional estimate about 91.91s. New non-target trajectory may not reproduce; current CLI has only 2/64-round profiles, so a diagnostic entry would also need implementation. | Not selected |
| C. Require unique historical cause or hold all execution | Produces no new learning observation; no identified wrong metric/comparator or separate primary dependency currently requires this broader condition. | Not selected |

The decision value comparison is explicit: option B supplies no identified fault-observation
capability unavailable from A, while adding a new trajectory/configuration before the desired
result. The recovered stack already bounds the stage. CM states no specific primary-integrity
dependency requires B first; remaining uncertainty is surviving to final measurement, not a
demonstrated wrong reward or comparison. A's larger complete work directly answers the selected
learning question. This is not a presumption that diagnostics are cheap or that a successful
retry would locate the root cause. No exact proof, source repair, mean replacement, runtime
upgrade or new seed is silently selected.

**Owner-delegated decision (unattended, 2026-09-03 instruction): A.** Tier: object;
kind: selection; provenance: OWNER_DELEGATED; reversible: yes; owner flag: none.
The preceding read-only evidence collection is technical work within this intake. Current
owner reviews are empty. Root integrates the shared ledger and owner decision item, including
the previous failed attempt and this selected follow-up; no per-item reply is awaited. Portfolio
priority, recasts: 2 and lifecycle remain unchanged.

## Formal02 CM handoff

After this intake/card supplement is committed and pushed, run one fresh attempt from the
unchanged source `33e08f440c2117dcfd9457d825f42fef7b38ccd7`, on `wsl_4070`, detached cwd
`/home/wu/hmasd-worktrees/vnfc_b01_formal_33e08f440_02`, task
`vnfc_b01_formal_33e08f440_20260905_02`. Use new output root
`temp/directions/variable_n_fleet_churn/b01_formal_20260905_02/output`; preserve formal01.

The original card remains the scientific assignment: seeds 2026090501/2026090502, formal
namespace, two actual CPU binary64 learners, original information/action/RNG/optimizer semantics,
64 rounds × 32 full episodes per arm, initial/32/64 evaluation on 64 episodes and BCRH64 once.
This is a same-seed fresh attempt of the incomplete B, not another independent training seed.
No resume from initial checkpoints, truncation, best-checkpoint choice or outcome selection.

The only changed interpreter option is `-X faulthandler`, selected to emit available Python
thread stacks if a fatal fault occurs. Fault output may be incomplete in damaged state; its
overhead is not measured as zero and is included in the same external wall boundary. It does
not fix the fault. Card supplement names this one event-triggered diagnostic quantity; there
is no new telemetry framework, watchdog, periodic dump, worker, numerical change or retry loop.

Exact command, launched through the existing detached supervisor:

```sh
cd /home/wu/hmasd-worktrees/vnfc_b01_formal_33e08f440_02 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/variable_n_fleet_churn/b01_formal_20260905_02/memory.json && /usr/bin/time -v -o temp/directions/variable_n_fleet_churn/b01_formal_20260905_02/whole_time.txt timeout 2612s /home/wu/.venvs/hmasd/bin/python -X faulthandler scripts/run_vnfc_n7_direct_b01.py --profile formal --seed 2026090501 --eval-seed 2026090502 --launch-sha 33e08f440c2117dcfd9457d825f42fef7b38ccd7 --out temp/directions/variable_n_fleet_churn/b01_formal_20260905_02/output
```

The external 2612-second timeout fits the 2612.14-second remaining total; the runner's historical
2700 config field grants no extra time. Initialization/build, full learner/reference work and
publication remain one invocation. Fresh memory admission occurs on the node immediately before
it. No separate smoke, pytest, diagnostic run or automatic formal03 is selected. CM hands the
accepted handle directly to `/root/tracker_tl_experiments`, collects all terminal output/cost and
returns technical acceptance; DM owns the subsequent scientific intake. At selection, formal02
has not launched. A crash returns the observed dependency and any stack without automatic
repair/retry; a complete result retains every outcome under the unchanged card's interpretation.
