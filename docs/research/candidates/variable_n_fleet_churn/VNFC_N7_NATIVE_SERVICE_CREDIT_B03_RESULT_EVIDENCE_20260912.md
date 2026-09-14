# B03 incomplete-attempt evidence — 2026-09-12

The single fresh INTERVAL/TERMINAL training pair exited with signal 11 after both
arms logged round 35. It has no final recovery comparison and no scientific score.
Partial progress and measured cost are retained. This is not a complete B result.

## Bound inputs and rule applied verbatim

Object: [B03 card](VNFC_N7_NATIVE_SERVICE_CREDIT_B03_SCIENCE_CARD_20260912.md), selected
by Portfolio response `6c32ade3216c374ecf2f5179b15d559729cd45c9` section 6 and Root's
2026-09-12 continuation. Repair/source acceptance was integrated by Root at main
`70cce4323` / `91c16cb06`; that accepted finite engineering dependency is historical
provenance, not evidence that this full training invocation succeeded.

Exact scientific source: `b93329b3c44ea9d0cf5622c00f5ca6eea0740dac`.
Exact command/input record: `f72f0d8634a365518a24c4fad7166bdda7ea1c68`.
Staging record: `d35b0a110b7b7078397765540b730d3334aba74b`.
Fresh training/evaluation seeds: `2026091201` / `2026091202`; namespace
`VNFC-N7-NATIVE-SERVICE-CREDIT-B03-20260912`. CPU float64, one computation thread,
original configured interpreter and native environment. One accepted pair, zero retries.

The frozen primary is final round-64 paired mean INTERVAL−TERMINAL R_fail_60 over
all 64 worlds, read with full J, intact/zone tradeoffs, own-initial and fixed BCRH
comparisons. The card rule applies verbatim: "Invalid primary limits only its
dependent claim; credible partial facts remain. All outcomes end this allocation."
Evidence specification §11.8.7: "A damaged primary measurement cannot support its
dependent performance claim; independently trustworthy narrower facts remain reportable."
No final score survives, so no usable, mixed, small or adverse performance branch
can be assigned. The named one-invocation allocation ends; B has no consumption state.

## Acceptance, observation and terminal receipt

[Launch](evidence/b03_credit_20260912_01/launch.json) was accepted once at
`2026-09-12T13:53:09.244627+00:00`. Bare supervisor handle
`vnfc-b03-credit-20260912-01` owns tmux session `agent_vnfc-b03-credit-20260912-01`.
Detached source checkout: `/home/wu/hmasd-worktrees/vnfc-b03-credit-20260912-01`.
Its output is `temp/directions/variable_n_fleet_churn/exp/b03_credit_20260912_01`;
supervisor records are `/home/wu/.agent-tasks/vnfc-b03-credit-20260912-01`.

The exact command joined fresh admission and the timed scientific invocation with
`&&`. [Admission](evidence/b03_credit_20260912_01/memory.json) passed at
`2026-09-12T13:53:09.878166Z`: physical/effective available 15,623,073,792 bytes,
required 4,294,967,296 bytes, measured from `/proc/meminfo`.

[Monitor receipts](evidence/b03_credit_20260912_01/monitor_receipts.json) distinguish
accepted MONITOR_ADD delivery from actual goal adoption. The live Monitor called
get_goal, found none and created an unbudgeted unfinished goal retaining this handle.
Two initial not_found observations were temporary observation loss. Root then routed
running pid 3374208 / tmux active, and the one requested DM reconciliation observed
the same running process. No relaunch followed. The cause of the transient observation
loss is not established; a naming defect is not asserted from these receipts.

Root routed Monitor's terminal notice: failed, exit 139, pid 3374208, tmux inactive,
terminal `2026-09-12T21:54:54+08:00`, supervisor duration 105 seconds. The collected
[outer timer](evidence/b03_credit_20260912_01/collected/outer_time.txt) explicitly says
"Command terminated by signal 11": **104.89 seconds**, peak RSS **780,784 KiB =
799,522,816 bytes**. Its `%x` field prints 0 despite signal termination; it does not
override the signal line and supervisor exit 139. This is not a 600-second timeout.
Monitor goal completion remains a separate direct Root receipt, not inferred here.

## Preserved artifacts and direct progress

[Raw archive](evidence/b03_credit_20260912_01/raw_collection.tar.gz): 5,532,089 bytes,
SHA256 `a9b98b58d6b0051f8f5055e8d8b261e6c8a87e9d253de5db14d0aea156e9e9fa`.
Remote and local digests match. [Readback](evidence/b03_credit_20260912_01/archive_readback.json)
records all 13 readable member streams, sizes and hashes: four initial/midpoint
checkpoints, native library, admission/timer and six supervisor files. Collection
read their bytes without loading a checkpoint, native library, model or environment.
The [collection receipt](evidence/b03_credit_20260912_01/terminal_collection.json)
retains the full log and output inventory. Small text members are also available
under `evidence/b03_credit_20260912_01/collected/`.

Both initial checkpoints are 722,421 bytes; both midpoint checkpoints are 2,169,211
bytes. There are no final checkpoints, `summary.json`, `training_episodes.json`,
`evaluation_episodes.json` or `training_curves.json`. The latter documents are only
published after both learners complete. Midpoint model bytes do not supply missing
scores or authorize a new evaluation.

Standard-library analysis of all 70 flushed progress rows produced
[partial counts](evidence/b03_credit_20260912_01/partial_counts.json). Each arm has
exactly rounds 1–35, each reporting 192 joint transitions and 32 optimizer steps.

| Arm | Logged rounds | Joint transitions | Optimizer steps | Last parameter displacement / initial L2 |
| --- | ---: | ---: | ---: | ---: |
| INTERVAL | 35 | 6,720 | 1,120 | .2504465494391335 |
| TERMINAL | 35 | 6,720 | 1,120 | .24154357326557027 |
| Combined | 70 arm-rounds | 13,440 | 2,240 | not a performance comparison |

Each arm has 89,090 parameters. INTERVAL's last norm/displacement is
34.732846945409094 / 8.344043913146654; TERMINAL's is
34.66886085672971 / 8.047426434022773. Nonzero movement is a learner-execution fact,
not return improvement or support for a treatment advantage.

The bound `variable_n_fleet_churn_n7_direct_b01/experiment.py` logs only after each
collection/update. It performs both initial and midpoint checkpoint/evaluation paths
before entering rounds 33–35. Combined with 32 training episodes per arm-round and
six joint decisions per episode, this implies **at least 2,240 complete training
episodes, 256 learned-policy evaluations, 64 reference episodes and 2,240 backward
calls**. Total complete-episode lower bound: **2,560**, or **614,400 native ticks**;
the fixed reference accounts for 384 complete BCRH calls. These are source-order
inferences, not readback of absent episode/counter/gradient arrays. Unprinted partial
work is unknown. The planned 4,544 episodes / 1,090,560 ticks / 4,096 optimizer calls
must not replace observed incomplete exposure.

## Bounded technical diagnosis and limits

The one newly saved core was inventoried by exact launch/terminal interval:
[core inventory](evidence/b03_credit_20260912_01/core_inventory.json), 641,089,536 bytes,
mtime `2026-09-12T13:54:54.055109+00:00`. Its full absolute path remains in that record
and the cleanup inventory. It is outside the execution checkout and is retained.

One read of its first 12 native frames used GDB with auto-loading/debuginfod disabled
and a 10-second outer bound: [raw receipt](evidence/b03_credit_20260912_01/core_top_stack.json),
2.141 seconds. No inferior ran and no numerical fixture was added. The core header
identifies `scripts/run_vnfc_native_service_credit_b03.py` and signal SIGSEGV. The top
frame is address zero, followed by Python evaluation, `gen_iternext`,
`PySequence_Tuple` and call frames. GDB also reports an executable-match warning,
libcuda build-id mismatch, unavailable relative native-library symbols and an
unsupported `info proc cmdline` request. This stack is provisional localization; it
does not identify a Python source line, offending write, faulty component or shared
cause with B02. No broader core/allocator search or new test follows in this allocation.

The 256/256 stored-input boundary check still establishes its exact finite contract,
including expected mean and backward behavior on that fixture. B03 is direct contrary
evidence to any broader inference that this alternative makes full native training
reliable. The original writer was never established. Neither this crash nor an old
Fraction/padding observation establishes a common root cause. Full primary-publication
acceptance fails; this is an engineering failure with no scientific polarity.

## Cost, deviations and preservation boundary

Native wall 104.89 seconds is below the pair-wide 600-second cap. Per-arm native cost
and aggregate CPU work were not published. No timeout, precision/comparator change,
new diagnostic framework or Engineering Scope §5 breach is observed; source is unchanged
from the committed launch binding. [Support accounting](evidence/b03_credit_20260912_01/support_costs.json)
separates selected non-nested command-wall receipts from missing preparation, routing,
intake/publication/cleanup and complete elapsed critical path. Its recorded sum is
40.316923 seconds; this is not complete support wall. Full 300-second support and
900-second combined conformance is unestablished, not a measured breach or a scientific
failure classification. Missing clocks are not zero. No valid-result cost denominator
exists, and the unused arithmetic does not authorize another scientific invocation.
The earlier 3.177215865-second maintenance check stays in its separate engineering account.

[Cleanup inventory](evidence/b03_credit_20260912_01/cleanup_inventory.json) names two
terminal detached checkouts: this B03 root and the owned-mean check root
`/home/wu/hmasd-worktrees/vnfc-owned-mean-20260912`. The exact remote maintenance receipt is now preserved with its digest in
[cleanup preservation](evidence/b03_credit_20260912_01/cleanup_preservation.json). Root
confirms integration and retention; the DM then reclaims those scoped checkouts and
verifies disk plus Git-registration absence.
The external B03 core and small supervisor history remain; the shared Windows
`C:/Projects/HMASD-worktrees/codex-vnfc` authoring checkout is still used for this return.
Owned test scratch is already absent. No evidence root is deleted in this intake.


Closeout update: Root integrated and retained this evidence at main `7125f368b`
(with source/input/staging `efa676ac2` / `60ba92104` / `57da33f0c`). The execution
record's [actual cleanup section](VNFC_N7_NATIVE_SERVICE_CREDIT_B03_EXECUTION_20260912.md#root-acceptance-and-actual-cleanup--2026-09-12)
supersedes the pending inventory above: both named detached checkouts are absent on
disk and from Git registration. The raw archive, exact maintenance receipt, external
core, supervisor history, B01/B02 evidence and shared authoring checkout are retained.
No new scientific or diagnostic invocation occurred.
