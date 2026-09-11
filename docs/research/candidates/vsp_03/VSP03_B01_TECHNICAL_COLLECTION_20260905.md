# VSP03 B01 technical collection

**The selected first invocation completed and its required measurements are technically accepted.**
One seed pair ran once, with all40tick episodes, 256 joint updates, all three prescribed
evaluation points, fixed F, the eight-case check and final publication/readback. No successor,
seed replacement or scientific disposition is made here. DM owns interpretation.

## Exact execution and artifacts

Launch source: `2c7d7ae08f978aa63d58468f3de1adb372f1339a`, pushed branch
`codex/cm-vsp03-b01-20260905`; contract commit `7e817627e` is its parent. Node `wsl_4070`, SSH
`hmasd-wsl-node`, cwd `/home/wu/hmasd-worktrees/vsp03-b01-seed1-r01`, verified detached at that SHA.
Exact argv, preflight and supervisor command are frozen in
`VSP03_B01_TECHNICAL_ACCEPTANCE_20260905.md`. Existing `agent-task` accepted
`vsp03-b01-seed1-r01-20260905`; PID1704022, exit0, status finished, tmux inactive.
Tracker `/root/tracker_tl_experiments` acknowledged adoption and directly reported termination
to CM/DM. CM independently read that same supervisor terminal status during collection.

Remote primary output root:
`/home/wu/hmasd-worktrees/vsp03-b01-seed1-r01/temp/directions/vsp_03/exp/vsp03_b01_seed1_r01/`.
Receipt is its sibling `vsp03_b01_seed1_r01_memory.json`.
Supervisor evidence is `/home/wu/.agent-tasks/vsp03-b01-seed1-r01-20260905/`.
SCP collection preserves all outputs locally under
`C:/Projects/HMASD-worktrees/cm-vsp03-b01-20260905/temp/directions/vsp_03/exp/vsp03_b01_seed1_r01/`:

- `summary.json`, `focused_check.json`;
- `T_endpoint_32.json`, `T_endpoint_64.json`, `T_endpoint_128.json`, and corresponding G files;
- `F_endpoint_128.json`, `T_curve.jsonl`, `G_curve.jsonl`;
- `T_final.pt`, `G_final.pt`;
- collected `task.log`, `supervisor_exit_code.txt`, `supervisor_status.txt`;
- `collection_checks.json`, CM's read-only artifact-check result, generated after completion.

The receipt is also copied to the local sibling path. These scratch artifacts are not Git-tracked;
this committed record makes the accepted remote and local evidence recoverable. No evidence was
deleted or restarted. An initial ordinary-shell Git fetch stalled before preparation; its Git
process was stopped, and configured `zsh -lic` fetch/checkout then succeeded. That shell printed
gitstatus initialization and existing repository auto-GC warnings, but returned exit0 and the
required SHA. No scientific process had been accepted then. No repository GC repair was attempted.

## Runtime and complete cost

Actual-node admission at `2026-09-05T23:54:37.480263Z` passed physical/effective available memory,
both15,388,168,192 bytes, against4,294,967,296 bytes. Measurement source `/proc/meminfo`;
cgroup values were null in the existing receipt, not independently measured limits.
Supervisor started23:54:37Z and ended23:54:40Z (node log renders UTC+08).

Runner import-through-publication/readback wall was **2.364870157005498s**, below the complete
1800s cap; supervisor duration3s includes preflight/start/exit overhead and second resolution.
Main-process OS peak RSS was **484,868,096bytes (462.40625MiB)**. Source sets BLAS/OpenMP and
Torch intra/inter-op compute threads to one and uses CPU float32. No live thread census or
aggregate CPU measurement was taken; this is not a measured CPU-seconds or accelerator claim.
Single-invocation sequential wall is the study critical path; no summed parallel speedup claim.

| Measured cost term | T seconds | G seconds |
| --- | ---: | ---: |
| Initialization I | 0.5020376380 | 0.0034664720 |
| Mean full training batch C(128,40) | 0.0037041082 | 0.0035967217 |
| Mean full evaluation batch E(128,40) | 0.0026402642 | 0.0069991854 |
| O: curves/endpoints/states/other arm bookkeeping | 0.0352849610 | 0.0347501130 |
| I+128C+10E+O, complete measured arm wall | 1.0378510870 | 0.5685888210 |

Imports/setup measured0.6698968100s; shared eight-case check0.0624245910s. F batch times and
remaining shared publication are retained in summary/terminal wall. O is the arm-wall residual,
not a separately isolated disk benchmark. First normal batches supplied initial partial estimates
while E/O stayed explicitly unknown; every such batch was retained. No pilot or timing rerun.

## Actual exposure

| Quantity | T | G |
| --- | ---: | ---: |
| Actor / critic parameters | 1314 / 257 | 1314 / 257 |
| Training episodes / ticks | 16384 / 655360 | 16384 / 655360 |
| Joint optimizer steps / backward calls | 128 / 128 | 128 / 128 |
| Valid training decisions / gradient rows | 53473 / 53473 | 42139 / 42139 |
| Training actor forwards, including loss forward | 1272 | 1226 |
| Training critic forwards | 128 | 128 |
| Evaluation episodes / ticks | 1280 / 51200 | 1280 / 51200 |
| Evaluation decision rows / actor forwards | 4892 / 90 | 6263 / 90 |
| Initial total parameter L2 / RMS | 6.427330494 / 0.162159562 | 5.939346313 / 0.149847865 |
| First total displacement / initial-L2 ratio | 0.017058313 / 0.002654028 | 0.017058399 / 0.002872100 |
| Final total displacement / initial-L2 ratio | 2.616672277 / 0.407116497 | 3.095903397 / 0.521253221 |

Actor/critic-specific norms and first/final displacements remain in summary. Final direct-b
coefficients read from saved states are T2.2572817802 and G0.0886396989; all coefficients remain
trainable. F executes1024episodes/40960ticks/3959decision rows, zero model forwards/updates.
The check executes8episodes/320ticks/32decision and gradient rows, one actor/critic forward and
backward, zero optimizer steps. It clears check gradients before actual learning.

Whole actual count is2learner constructions,36360started/completed episodes,1454400ticks,
110758decision rows,2422rollout actor forwards and256joint steps. Loss forwards are separately
reported above. One selected configuration and one independent training pair; no best endpoint.

## Fixed endpoint observations

| Update | Episodes per arm | T mean return | G mean return | T-G | Conditional paired-episode SE |
| --- | ---: | ---: | ---: | ---: | ---: |
| 32 | 128 | 0.365390625 | -0.2 | 0.565390625 | 0.0446985064 |
| 64 | 128 | 0.367187500 | -0.2 | 0.567187500 | 0.0444654573 |
| **128 main** | **1024** | **0.3755859375** | **0.3755859375** | **0** | **0** |

At the main endpoint F also returns0.3755859375. All1024complete per-episode records compare
equal among T,G,F (including submission times, native components and event counts); this is a
direct observation on these sampled episodes, not a claim of global policy equivalence.
Each main arm/reference has success0.482421875, attempt0.951171875, failed attempt0.46875,
non-submission0.048828125, mean waiting11.85546875ticks.565episodes submitted after departure
and re-entry, with conditional mean return0.4039469027. These are descriptive diagnostics.
G's two early greedy evaluations had no submissions. No earlier endpoint replaces update128.
One trained pair cannot estimate training-seed variability; the episode SE is conditional.

## Technical checks and limits

Independent source review and five focused non-rollout tests are recorded in source acceptance.
The selected runtime eight-case check passed initial/read-before-update latch, armed interval,
departure/re-entry, first/last service failure, final opportunity, no submission, integer rewards,
finite gradients, zero check optimizer steps and JSON publication/readback. Its exact expected
integer returns were `[186,182,-14,-14,158,-40,186,182]`.

CM read all copied endpoint rows with standard-library JSON and independently recomputed each
integer reward, division, waiting/submission relation, failed-attempt count, endpoint means and
paired differences. All matched. Episode IDs are0..127 or0..1023 as prescribed; all128curve
update records per arm are present, each reports128episodes, and their decision counts sum to
the arm exposure. Summary total episodes/ticks/steps match the frozen plan. F submitted only
with b=1. Final state readback with `torch.load(weights_only=True,map_location='cpu')` found
11tensors/1571finite float32 parameters per arm. The runner itself had already compared saved
state tensors to live state during its timed publication. This collection constructs no model,
generates no new rollout and performs no new optimizer step.

No missing required measurement or concrete semantic defect was found. This acceptance covers
the selected implementation and observed invocation, not baseline competence certification,
stable superiority, learning necessity, cross-host bit identity, historical event authentication
or any MARL-specific consequence. Next step is DM intake of the preserved fixed observations.
