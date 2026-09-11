# N3 DISH B01 C04 seed 11 — technical collection

The exact accepted seed 11 invocation is technically complete on its observed no-trigger path.
Native learner work, actual nonzero exposure, all sixteen declared evaluation rows, and final
checkpoint/summary publication exist. This is an engineering conclusion, not the three-seed FTS
classification, a source-value estimate, or a decision to launch the remaining seeds.

## Bound execution and original evidence

Source: `e0541d0cb3e9e63731c72f4dacb10b44d268fd39`.
Node: `wsl_4070` via `hmasd-wsl-node`.
Cwd: `/home/wu/hmasd-worktrees/dish-b01-c04-e0541d0c`.
Task: `dish_b01_c04_seed11_e0541d0c_a1`; supervisor PID 112219.
Frozen command and fresh admission are recorded in
`N3_DISH_B01_C04_LAUNCH_INTAKE_20260904.md` and the accepted-launch section of the CM return.
No command, source, seed, comparator, endpoint, precision or stop condition changed during execution.

The tracker reported FINISHED, exit 0, tmux inactive; CM read the existing exit witness and
artifacts after that notice. Original log start is `2026-09-05T08:12:03+08:00`, terminal
`2026-09-05T08:30:22+08:00`, supervisor duration **1099 seconds**. The log is
`/home/wu/.agent-tasks/dish_b01_c04_seed11_e0541d0c_a1/task.log`; wrapper and terminal witnesses
remain beside it. Original artifacts remain unchanged under cwd-relative
`temp/directions/degraded_incumbent_shadow_handover/exp/n3_b01_c04_20260904/seed11_a1/`.

Local copies under CM worktree
`C:/Projects/HMASD-worktrees/cm-n3-dish-c04-20260904/temp/directions/degraded_incumbent_shadow_handover/exp/n3_b01_c04_20260904/`:

- `seed11_a1/summary.json` — original published JSON.
- `seed11_a1/checkpoint.pt` — **2,070,711 bytes**, original published checkpoint.
- `seed11_a1/task.log` and `seed11_a1/runner.sh` — supervisor evidence copies.
- `seed11_a1_admission.json` — original receipt, outside the output child.

The original summary bytes are also copied to the tracked sibling
`N3_DISH_B01_C04_SEED11_SUMMARY_20260904.json` for DM/remote-reader access.

## Direct technical checks

CM used a bounded read-only Python stdin command in the recorded remote cwd, with
`/home/wu/.venvs/hmasd/bin/python`, to parse the existing JSON and load the existing checkpoint
with `torch.load(..., map_location='cpu', weights_only=False)`. It instantiated no learner/model,
created no RNG master, and ran no training, evaluation, tests or new result invocation.
The check enumerated checkpoint tensors, optimizer step values, panel Cartesian tuples and final
parameter norm. It observed:

| Quantity | Observation |
| --- | --- |
| Summary learner updates | 64 |
| Summary native training transitions | 262,144 |
| Summary optimizer steps | 2,048 |
| Checkpoint update | 64 |
| Model tensor count / all finite | 50 / true |
| Optimizer state count / all finite | 36 / true |
| Distinct optimizer step values | `[2048.0]` |
| Actor Welford count | 1,048,576 |
| Critic Welford count | 262,144 |
| Snapshot Welford count | 0 |
| Evaluation rows | 16, exact prescribed Cartesian tuples |
| Prefix ticks | 19,200 = 16 x 1,200 |
| Triggered rows | 0 |
| Branch consequence ticks | 0 |

The checkpoint keys are `evaluation_checkpoint`, `model`, `optimizer`, `update`, `welford`.
The summary counts agree with the completed 64-update production loop and checkpoint counters;
they are not inferred from process exit alone. Zero snapshot-normalizer count is reported as
observed state, not evidence that a source intervention ran.

Panel membership equals packages `{TARGET_VISUAL_MASK,TERRAIN_RELAY_MASK}` x schedules
`{K8,K4_TO_K12}` x speeds `{4,8}` x within-speed slots `{0,3}`, with sixteen distinct rows and
each `triggered=false`. The runner's no-trigger path exhausts 1,200 ticks and retains its row;
therefore there are no actual branch receipts, future branch tapes, energy/hard-event comparisons,
or 100-tick endpoints to inspect in this seed. These quantities are conditional on a trigger,
not missing instrumentation on this no-trigger path. No aggregate result rule was invoked.
The summary's zero differences and true `shadow_nonharm` are empty-support reducer values;
they are not observed source equality or a nonharm result. `usable_trigger_support=false`.

## Actual exposure and resources

Actual published float64 exposure:

- Initial parameter norm: **38.19731474061207**.
- Final parameter norm: **41.78517869974931**.
- Relative total L2 displacement: **0.42465718774783356**, finite and nonzero.
- Maximum per-tensor displacement ratio: **1.2535341627432597e+300**, finite.
- Optimizer steps: **2048**.

CM recomputed the final norm from loaded checkpoint tensors in float64 and obtained exactly
**41.78517869974931**, matching the summary. The initial norm and displacement are original
runner observations; CM did not regenerate initialization or rerun a learner to repeat them.
The very large per-tensor ratio is interpreted only as the implementation's descriptive field:
`study.py:_parameter_exposure` divides by `max(initial_tensor_norm, 1e-300)`, while initialization
zeros biases. It is dominated by the zero-reference denominator and is not an infinity, a failed
finite-state check, a meaningful relative percentage for such tensors, or a scientific threshold.
The raw field is retained without altering the post-observation calculation.

Runner wall **1068.1102725170058 seconds**; supervisor wall **1099 seconds**. Both are below
the 1800-second cap and the generated per-arm projection 1474.544745605439 seconds. Runner peak
RSS **628,801,536 bytes**, `resources_unmeasured=false`. Supervisor wall also includes startup
and final publication overhead beyond the runner's timed section. These are direct observations,
not a throughput claim or a new measured cost law used to change queued budgets.

Fresh node receipt at `2026-09-05T00:12:03.356900Z` reported physical and effective available
memory **12,531,122,176 bytes** each, floor **4,294,967,296**, all pass flags true. The initial
admission does not purport to measure continuous available memory; peak RSS is the runner's
separate process-lifetime measurement. Scratch size was not instrumented; no resource claim is made.

## Coverage, risk and next boundary

The real learner-to-no-trigger-panel-to-checkpoint/summary publication path has now completed once.
This removes the specific uncertainty about whether that runtime path can publish these artifacts.
The automated end-to-end test still does not cover the complete `_run` publication path with
formal constants; **retain that open engineering item on results**. The scientific triggered
branch path has no real-seed observation yet; its earlier TEST conformance evidence remains a
bounded engineering check, not source-value evidence. Initial-checkpoint bytes are not separately
published, so the collection did not independently recompute total displacement from two artifacts.

No failure was classified, no repair was attempted after these question-relevant outputs,
and no seed/row/threshold was changed. Seeds 29 and 47 remain queued for DM selection based only
on technical completeness. No inference about their future support or effects is made here.
DM applies the unchanged card to the eventual complete three-seed set; CM returns this seed's
technical completeness and preserves all original evidence. Collection adds no §4 machinery.
