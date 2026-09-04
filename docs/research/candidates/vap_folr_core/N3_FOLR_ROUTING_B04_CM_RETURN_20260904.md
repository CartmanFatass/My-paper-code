# N3/FOLR B04 engineering return

## Prospective engineering contract

Implement the B04 card at `a5449da0d72094a7e1fbf3be3104f49fb6dd1a11`:
observe paired STALE_LOAD sampled-return AUC differences between TYPED and GENERIC;
RESET is the information cut and evaluation-only LATCH is the simpler legal control.
Technical acceptance establishes the actual host/learner/output chain, never mechanism value.

Owned paths: `experiments/candidates/vap_folr_core/n3_routing_b04/`, mirrored tests,
`scripts/run_folr_n3_routing_b04.py`, and this report. CM checkout is
`C:/Projects/HMASD-worktrees/cm-n3-folr-b04-20260904`, branch
`codex/cm-n3-folr-b04-20260904`. Unrelated primary-worktree changes remain untouched.
The implementer owns only the new learning module in its separate worktree; B3 source is reused unchanged.

Engineering scope specification section 4 additions: **none**. No card line requests
distributed execution, new orchestration, retries, resume, guards, registries, validators,
compatibility shims, extra telemetry or repeated smoke tests. Existing host metadata is inherited.

The host always executes three transitions with q0 leaving and distinct q1 joining while
`owner_t@0` continues. Differentiable owner/obsolete candidates remain learner-owned;
the host owns detached lifecycle state and terminal reward. Only sampled native reward
enters REINFORCE. No direct-label learning, writer gate or historical manifest pipeline.
The detached frozen writer is identical for each seed's routing arms. LATCH stores the
initial survivor bit in two owner channels and recovers it from the surviving host record;
it applies the same frozen writer's learned readout to the delivered payload.

Protected numerical/data contract: CPU float32; Adam 0.025, default stated betas/epsilon,
zero weight decay; 96041–96043; 128 writer updates and 128 per routing arm; 64 balanced
episodes per update; evaluation 0–128 every 16, 256 per regime. Routing arms share
initialization, data and action-uniform tapes. Evaluation streams are separate and fixed
across curve points. Save final model and optimizer state only; no resume or model selection.
Cross-OS bit equality is outside the estimand. Actual displacement norms use float64.

Acceptance: one admitted toy smoke reaches final checkpoints, plain evaluation rows,
complete training/evaluation curves and summary; reading-rule tests pin the card's branches.
Full expected counts are 98,304 train episodes, 1,536 learner updates, 49,920 eval episodes,
148,224 complete episodes and 444,672 primitive transitions. Policy calls and diagnostic
forwards are counted separately. Existing B3 learner-publication orchestrators are not called.

Execution is prospectively portable Windows/Linux CPU and remote-first on `wsl_4070` using
the configured Python and a detached exact-SHA worktree under `/home/wu/hmasd-worktrees/`.
Runtime output lives under `temp/directions/vap_folr_core/exp/n3_routing_b04_<attempt>/`.
Every learner invocation receives fresh node-local `admit-memory` immediately beforehand,
joined to the runner command by `&&` inside `agent-task`. No live run is migrated or duplicated.

Before full launch, measure train/evaluation wall per episode on the smoke and project each
three-seed phase and routing arm; charge the entire shared writer to every routing arm.
Do not launch if any projected phase/charged arm exceeds 600 s or the full invocation exceeds
2,400 s. Stop at completion or the whole-invocation wall cap; reproduce a failing step before
classifying a failure. No seed/treatment/threshold changes after question-relevant output.

Publication coverage is initially open until the one end-to-end smoke reaches the actual
final output path. Prior B3 calibration absence is not a post-learner failure in this new path.

## Frozen technical invocation

Execution node `wsl_4070`; cwd
`/home/wu/hmasd-worktrees/cm-n3-folr-b04-20260904-a1` (detached at the first CM implementation commit).
Supervisor task `n3-folr-b04-smoke-20260904-a1`. The exact command after `cd` is:

```sh
/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/vap_folr_core/exp/n3_routing_b04_smoke_20260904_a1/resource_admission.json && B04_SMOKE_OUTPUT=/home/wu/hmasd-worktrees/cm-n3-folr-b04-20260904-a1/temp/directions/vap_folr_core/exp/n3_routing_b04_smoke_20260904_a1 /home/wu/.venvs/hmasd/bin/python -m pytest -q -p no:cacheprovider tests/experiments/candidates/vap_folr_core/n3_routing_b04/test_b04.py
```

The smoke test executes the runner with `--smoke --seeds 96041 --output-root <B04_SMOKE_OUTPUT>`.
It uses two updates, batch 64, three evaluation points and the formal 256 episodes per regime.
The single pytest invocation owns the only smoke and checks its actual output. No model is
created before that admitted runner invocation. Its completion bound is 60 seconds for the
runner, and five minutes for the focused suite. Stop on the first failing step; no automatic retry.

Static checks: three new Python files parse; the six reading-rule/count/cost tests pass locally
in 0.10 seconds. They launch no learner. No B3 source or unrelated path has changed.

## Technical acceptance and recorded cost before full launch

Implementation SHA **`0f83132fb3484f8366eaaa5863559d203f0cb369`** is committed and pushed.
Independent reviewer found no material defect: 506 research-code lines, runner 178 lines,
approximately 23–26% orchestration, no section 4 additions. CM inspected the integrated diff.

Remote smoke task `n3-folr-b04-smoke-20260904-a1` finished with exit 0, supervisor PID 82693.
The seven-test suite passed in **4.69 s**; learner wall was **2.382219321 s**, peak RSS
**483,033,088 bytes**. Actual smoke activity: 512 training episodes, 8 updates, 5,888
evaluation episodes, 6,400 complete episodes and 19,200 primitive transitions.
At `2026-09-04T22:06:11.717379Z`, node admission measured physical and effective available
memory of **12,773,167,104 bytes**, both above 4 GiB. The output contains four readable final
checkpoints with optimizer states, five plain evaluation files and the final summary.
Smoke checks compare frozen writer tensors, native reward rows, probability normalization,
zero obsolete-flip TV for TYPED/RESET, actual counts and nonzero parameter displacement.

**Per-arm cost projection:** measured smoke coefficients below use the runner's law
`train_episodes * seconds_per_train_episode + eval_episodes * seconds_per_eval_episode`.
Each routing phase has 24,576 train and 13,824 evaluation episodes across three seeds;
the writer has 24,576 train and 6,912 evaluation episodes. LATCH has 1,536 eval episodes.
Final flip diagnostics are included in evaluation wall; their separately recorded subtime
must not be added again. Checkpoint/publication and process startup overhead are outside
this episode law; observed smoke total wall remains recorded above.

| Phase | Train s/episode | Eval s/episode | Projected phase s | Arm s including full shared writer |
| --- | ---: | ---: | ---: | ---: |
| WRITER | 0.0005884640781346206 | 0.00031719232812103354 | 16.65452655620902 | — |
| TYPED | 0.0002527308749904478 | 0.00025939302409009696 | 9.796963148786745 | 26.451489704995765 |
| GENERIC | 0.00027637393753821016 | 0.00025631476563129735 | 10.335461209026107 | 26.989987765235128 |
| RESET | 0.0002827966640666091 | 0.00026871563867321885 | 10.664735805119562 | 27.319262361328583 |
| LATCH | 0 | 0.000239170589850346 | 0.36736602601013146 | evaluation only |

Total projected invocation: **47.819052745151566 s**. All projected phases and charged arms
fit 600 s; the invocation fits 2,400 s. No arm is dropped. This is a budget projection,
not a throughput claim or runtime resource disposition.

**Post-learner path coverage:** the one smoke reached the actual final publication path with
formal batch size 64 and evaluation size 256, all three routing arms and final LATCH. It
exercises the full path at two updates, not the formal 128-update endpoint; full-endpoint
execution coverage remains an open engineering item until the full run completes.
No post-learner failure has occurred in B04.

One remote preparation correction occurred before any learner: a fetch without the declared
login/interactive network shell made no progress for 82 s and was terminated explicitly.
The same branch fetch through configured `zsh -lic` then succeeded in the five-second
preparation command. This is an observed invocation difference; no source repair, learner
retry or scientific root duplication occurred. Shell startup printed unrelated gitstatus
initialization messages but fetch/worktree creation exited 0.

## Frozen full invocation

Launch source remains `0f83132fb3484f8366eaaa5863559d203f0cb369`; the subsequent report-only
commit changes no execution bytes. Node `wsl_4070`, detached cwd
`/home/wu/hmasd-worktrees/cm-n3-folr-b04-20260904-a1`, task
`n3-folr-b04-full-20260904-a1`. Exact command after `cd`:

```sh
/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/vap_folr_core/exp/n3_routing_b04_full_20260904_a1/resource_admission.json && timeout 2400s /home/wu/.venvs/hmasd/bin/python scripts/run_folr_n3_routing_b04.py --seeds 96041 96042 96043 --output-root temp/directions/vap_folr_core/exp/n3_routing_b04_full_20260904_a1
```

One accepted process will be handed to the DM for the shared tracker. No duplicate observer,
new heartbeat, restart or migration is added. Completion/timeout/failure is the stop condition.
