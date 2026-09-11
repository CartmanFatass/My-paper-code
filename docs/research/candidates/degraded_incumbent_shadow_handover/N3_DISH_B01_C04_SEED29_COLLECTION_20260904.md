# N3 DISH B01 C04 seed 29 — technical collection

Seed 29 is technically complete on its observed no-trigger path. Existing checkpoint, actual
nonzero exposure, all sixteen prescribed evaluation rows and final publication were directly
checked. No scientific aggregate, source-effect estimate or seed 47 launch is assigned here.

## Execution and evidence

- Source `e0541d0cb3e9e63731c72f4dacb10b44d268fd39`, node `wsl_4070`.
- Cwd `/home/wu/hmasd-worktrees/dish-b01-c04-e0541d0c`.
- Task `dish_b01_c04_seed29_e0541d0c_a1`, supervisor PID 607075, exit witness **0**.
- Log start `2026-09-05T08:47:14+08:00`; terminal `2026-09-05T09:04:11+08:00`;
  actual logged supervisor duration **1017 seconds**. Tracker's later uptime 1104 seconds
  includes time after termination and is not the run duration.
- Log `/home/wu/.agent-tasks/dish_b01_c04_seed29_e0541d0c_a1/task.log`; wrapper/status/exit
  witnesses beside it. Original source and remote artifacts were preserved.
- Original output cwd-relative
  `temp/directions/degraded_incumbent_shadow_handover/exp/n3_b01_c04_20260904/seed29_a1/`.

CM collected after the tracker's terminal notice, using the same bounded existing-artifact
read path as seed 11: remote Python stdin, JSON parse and CPU `torch.load` of the existing
checkpoint; tensor finiteness, optimizer step values, tuple-set panel membership and float64
final norm checks. No model/learner construction, RNG master, test, new evaluation, source change
or result invocation occurred. Invocation/admission command is preserved verbatim in the seed 11
DM intake and accepted seed 29 section of the CM return.

Local originals copied under
`C:/Projects/HMASD-worktrees/cm-n3-dish-c04-20260904/temp/directions/degraded_incumbent_shadow_handover/exp/n3_b01_c04_20260904/`:
`seed29_a1/summary.json`, `seed29_a1/checkpoint.pt`, `seed29_a1/task.log`,
`seed29_a1/runner.sh`, and `seed29_a1_admission.json` outside the child.
The sibling tracked `N3_DISH_B01_C04_SEED29_SUMMARY_20260904.json` copies the original summary.

## Direct counts and exposure

| Quantity | Observation |
| --- | --- |
| Learner updates / checkpoint update | 64 / 64 |
| Training transitions | 262,144 |
| Optimizer steps / distinct checkpoint step values | 2,048 / `[2048.0]` |
| Model tensor count / all finite | 50 / true |
| Optimizer state count / all finite | 36 / true |
| Welford counts actor / snapshot / critic | 1,048,576 / 0 / 262,144 |
| Panel membership | Exact 16 distinct frozen Cartesian rows |
| Prefix ticks | 19,200 = 16 x 1,200 |
| Trigger count / branch ticks | 0 / 0 |
| Published checkpoint bytes | 2,070,711 |
| Initial parameter norm | 38.286447586375616 |
| Final parameter norm | 41.81658102299228 |
| Relative total L2 displacement | 0.419585027483137 |
| Maximum per-tensor displacement ratio | 1.0764195675299437e+300 |

Loaded checkpoint final norm recomputed in float64 is exactly **41.81658102299228**, matching
the summary. Actual total exposure is finite and nonzero. Initial norm/displacement remain original
runner measurements; initialization was not regenerated. As recorded for seed 11, the finite large
maximum per-tensor ratio uses `max(initial_tensor_norm, 1e-300)` with initially zero biases;
it is a zero-reference-scale diagnostic, not an infinity or a meaningful percentage for those
tensors. The raw observation and calculation were not altered after output.

The tuple set exactly matches both packages, K8/K4_TO_K12, speeds 4/8 and within-speed slots 0/3.
Each row is `triggered=false`, and each prescribed prefix completes its 1,200-tick ceiling.
There are therefore no actual three-branch receipts/tapes, energy/hard-event comparisons or
100-tick endpoints in this seed. Those conditional data are not missing on a legitimate no-trigger
path. Raw zero contrasts and `shadow_nonharm=true` are empty-support reducer defaults, not observed
source equality or nonharm. `usable_trigger_support=false`. The three-seed FTS rule was not run.

## Resources, publication and limits

Runner wall **977.5005878610027 seconds**; logged supervisor wall **1017 seconds**; measured
peak RSS **628,461,568 bytes**, `resources_unmeasured=false`. Both walls are below the frozen
1800-second cap and unchanged 1474.544745605439-second per-arm projection. Runtime measurements
do not alter the cost law or queued budget. Scratch usage was not instrumented; no resource claim
is made. Startup/publication overhead is included in supervisor duration beyond runner timing.

Fresh receipt captured `2026-09-05T00:47:14.317386Z`, assessed `00:47:14.317661Z`, source
`/proc/meminfo`: physical and effective available memory each **15,432,970,240 bytes**,
minimum **4,294,967,296 bytes**, physical/effective/pass flags true, no failure reasons.
Admission is a start reading, not continuous available-memory telemetry. Receipt is outside output.

Existing summary and checkpoint were both successfully published. This is a second direct
observation of learner-to-no-trigger-panel-to-publication completion. Full automated `_run`
publication-path coverage remains an **open engineering item**, and no real scientific triggered
branch has yet been observed; the prior TEST branch evidence retains its limited scope. Initial
checkpoint bytes are not separately published, so collection did not independently recompute
displacement from two checkpoints. No new failure classification or repair was necessary.

DM may inspect this technical completeness to select unchanged queued seed 47. Nothing here
selects based on trigger support, effect, MEI or a source comparison. Scientific interpretation
and the eventual aggregate belong to DM; seed 47 is not launched by this collection.
Section-4 machinery added: none.
