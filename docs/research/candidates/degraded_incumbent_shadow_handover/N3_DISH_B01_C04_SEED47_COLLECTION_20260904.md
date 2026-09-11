# N3 DISH B01 C04 seed 47 — technical collection

The final original seed 47 is technically complete on the observed no-trigger path. All required
learner counts, actual finite nonzero exposure, exact sixteen-row evaluation and checkpoint/summary
publication exist. No three-seed FTS rule, scientific polarity or successor is selected by CM.

## Bound execution and artifacts

Source remains `e0541d0cb3e9e63731c72f4dacb10b44d268fd39`; the remote worktree is clean.
Node `wsl_4070`, cwd `/home/wu/hmasd-worktrees/dish-b01-c04-e0541d0c`.
Task `dish_b01_c04_seed47_e0541d0c_a1`, PID 1101576; existing exit witness **0**.
Log start `2026-09-05T09:12:59+08:00`, terminal `2026-09-05T09:30:19+08:00`, actual logged
supervisor duration **1040 seconds**. Tracker's later uptime 1075 seconds is not execution wall.
Original log/wrapper/status/exit remain under
`/home/wu/.agent-tasks/dish_b01_c04_seed47_e0541d0c_a1/`.

Original output cwd-relative:
`temp/directions/degraded_incumbent_shadow_handover/exp/n3_b01_c04_20260904/seed47_a1/`;
admission is sibling `seed47_a1_admission.json`, outside output. Verbatim invocation is in the
seed 29 DM intake and accepted seed 47 section of the CM return; no invocation change occurred.

Local original copies are under
`C:/Projects/HMASD-worktrees/cm-n3-dish-c04-20260904/temp/directions/degraded_incumbent_shadow_handover/exp/n3_b01_c04_20260904/`:
`seed47_a1/summary.json`, `seed47_a1/checkpoint.pt`, `seed47_a1/task.log`,
`seed47_a1/runner.sh`, and `seed47_a1_admission.json`.
Tracked sibling `N3_DISH_B01_C04_SEED47_SUMMARY_20260904.json` copies the original summary bytes.
No remote artifact was rewritten.

## Direct collection checks

After tracker terminal notice, CM used remote Python stdin to parse existing JSON and CPU-load
the existing checkpoint, enumerate finite tensors/optimizer counters, compare panel tuples and
recompute final norm in float64. This is the same bounded read path as seeds 11/29; it creates
no learner, model, scientific RNG master or result and executes no tests/evaluation.

| Quantity | Direct observation |
| --- | --- |
| Learner updates / checkpoint update | 64 / 64 |
| Training transitions | 262,144 |
| Optimizer steps / distinct checkpoint step values | 2,048 / `[2048.0]` |
| Model tensors / all finite | 50 / true |
| Optimizer states / all finite | 36 / true |
| Welford actor / snapshot / critic counts | 1,048,576 / 0 / 262,144 |
| Exact prescribed Cartesian rows | 16 |
| Triggered rows / branch ticks | 0 / 0 |
| Prefix ticks | 19,200 = 16 x 1,200 |
| Checkpoint size | 2,070,711 bytes |
| Initial parameter norm | 38.193747358754344 |
| Final parameter norm | 41.7205655228189 |
| Relative total L2 displacement | 0.4196544358013136 |
| Maximum per-tensor displacement ratio | 1.1524722211249414e+300 |

The float64 norm recomputed from loaded final checkpoint is exactly **41.7205655228189**,
matching the summary. Total displacement is finite and nonzero. Initial norm/displacement are
original runner observations, not independently regenerated initialization. As already disclosed,
the finite large per-tensor ratio reflects the `max(initial_tensor_norm,1e-300)` denominator for
initially zero tensors; it is not a meaningful percentage for zero-reference tensors or a
nonfinite learner failure. Its formula/raw value are preserved after observation.

The sixteen unique tuples equal packages `{TARGET_VISUAL_MASK,TERRAIN_RELAY_MASK}` x schedules
`{K8,K4_TO_K12}` x speeds `{4,8}` x within-speed slots `{0,3}`. Every row is `triggered=false`;
each prefix reaches the 1,200-tick no-trigger ceiling. Conditional three-branch receipts/tapes,
100-tick service/tail, energy and hard-event comparisons therefore do not exist and are not
missing instrumentation on this path. Empty-support difference zeros and `shadow_nonharm=true`
are reducer defaults, not observed source equality/nonharm. Usable support is false.

## Resources and remaining limits

Runner wall **995.6141687410054 seconds**, supervisor wall **1040 seconds**, peak RSS
**640,073,728 bytes**, `resources_unmeasured=false`. Both walls fit the unchanged 1800-second cap
and 1474.544745605439-second per-arm projection. They do not replace the frozen cost law or create
a throughput claim. Scratch usage was not measured. Supervisor duration includes overhead outside
the runner's timed section.

Admission captured `2026-09-05T01:12:59.650750Z`, assessed `01:12:59.651164Z` via `/proc/meminfo`:
physical and effective available memory each **13,040,766,976 bytes**, minimum **4,294,967,296**,
both floor flags and passed true, empty failure reasons. This is start admission, not continuous
available-memory monitoring; peak RSS is separately measured by the runner.

Checkpoint and summary publication are complete. The learner-to-no-trigger-publication route has
now been observed for all three original seeds. Full automated `_run` publication-path coverage
remains an **open engineering item**, and no real scientific triggered branch has been observed.
Existing TEST conformance is not source-value evidence. Initial checkpoint bytes are not separately
published, limiting independent two-checkpoint displacement recomputation during collection.
No new defect classification, repair, repeated suite, seed replacement or successor was needed or
authorized. All three existing seed collections are available for DM's unchanged complete-card
intake. Section-4 additions: none; CM has no live process to observe at this boundary.
