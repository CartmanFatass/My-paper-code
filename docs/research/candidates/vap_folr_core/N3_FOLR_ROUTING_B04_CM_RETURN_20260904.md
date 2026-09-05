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

## Completed observation and technical acceptance

**The full implementation and observation exist and are technically accepted.** The one full
task finished with exit 0, supervisor PID **97387**, at **2026-09-04T22:09:13Z**, supervisor
duration **43 s**. The shared tracker subsequently observed the terminal state at
22:09:55Z (tracker record commit `e914ee039fa6a36fd0c00ed77ebb59cda1eff70b`). The DM handed
the accepted process to that tracker; CM released routine polling and collected only after
the terminal handoff. No duplicate launch, repair or rerun occurred.

Full admission at **2026-09-04T22:08:30.583381Z** measured both physical and effective available
memory **12,932,308,992 bytes**. Learner wall **40.371824955997 s** and peak RSS
**484,229,120 bytes** were measured. Actual wall by three-seed phase, including train and
evaluation: WRITER **8.502901867999753 s**, TYPED **10.483885985959205 s**, GENERIC
**10.186610095966898 s**, RESET **10.03539999393979 s**, LATCH **0.350390626990702 s**.
With the full writer charged to each routing arm, actual measured phase totals are
**18.98678785395896**, **18.689511963966652**, and **18.538301861939544 s** respectively.
These observed walls fit the recorded limits. RSS is the learner process high-water mark;
it is not a whole-node resource census. No throughput or resource-comparison claim is made.

Actual totals match the card: **98,304 training episodes**, **1,536 updates**, **49,920
evaluation episodes**, **148,224 complete episodes**, **444,672 primitive transitions**.
The summary retains phase/seed/arm counts, batched policy-call counts by role, individual
terminal decisions, and separately counted counterfactual kernel rows. WAIT transitions
are not counted as learned policy calls. All 12 learners reached update 128.

| Seed | TYPED STALE AUC | GENERIC STALE AUC | Difference | TYPED final STALE | GENERIC final STALE | RESET final STALE | LATCH final STALE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 96041 | 0.87158203125 | 0.86962890625 | 0.001953125 | 0.9921875 | 0.9921875 | 0.5078125 | 1.0 |
| 96042 | 0.898681640625 | 0.89892578125 | -0.000244140625 | 0.9921875 | 0.9921875 | 0.50390625 | 0.99609375 |
| 96043 | 0.867431640625 | 0.861328125 | 0.006103515625 | 0.98046875 | 0.98046875 | 0.5078125 | 1.0 |

The recorded first-matching card rule is **`B04_WITHIN_MEI`**, because mean STALE AUC difference
is **0.0026041666666666665**, whose absolute value is below 0.05. CLEAN AUC differences are
**0.000732421875**, **-0.0009765625**, **0.001953125**; final CLEAN gaps are **0.00390625**,
**0**, **0**. All final STALE gaps are zero. Seed-mean final STALE return is **0.98828125**
for both TYPED and GENERIC, **0.5065104166666666** for RESET, and **0.9986979166666666** for
LATCH. Every final writer sampled return is 1.0. Independent descriptive flags are
`writer_weak=false` and `simple_control_headroom=false`. These are recorded arithmetic facts;
scientific interpretation and the next object remain with the DM.

Collection independently read all **12 final model/optimizer checkpoints**, **15 plain final
evaluation files containing 6,912 rows**, complete training curves at updates 1–128 and
evaluation curves at 0,16,…,128. Checks reconstructed final row rewards and expected reward
probabilities, normalized AUC from each curve, final parameter norms from saved tensors,
and frozen writer equality across arms. All checkpoint tensors were finite CPU float32;
every present Adam state had step 128. Each learner had nonzero measured parameter
displacement. Complete float64 initial/final/displacement norms, component accuracies,
final obsolete-flip TVs and all expected-reward-probability curves are in `summary.json`.
The full endpoint and publication path are now observed; there is no open B04 publication
coverage item. No runtime verifier or second learner smoke was needed for collection.

Complete original bytes remain at the remote output root in the frozen command above.
The complete local copy is:

`C:/Projects/HMASD-worktrees/cm-n3-folr-b04-20260904/temp/directions/vap_folr_core/exp/n3_routing_b04_full_20260904_a1/`

It contains `summary.json`, `resource_admission.json`, copied `supervisor.log`,
`seed_<seed>/{writer,TYPED,GENERIC,RESET}/final.pt`, each phase's
`final_evaluation.jsonl` (including LATCH), and local `collection_check.json` from the
offline arithmetic/readability check. The smoke's complete artifacts and supervisor log
are retained in the sibling `n3_routing_b04_smoke_20260904_a1/` directory.
No original result bytes were edited. The source remains exactly the launch SHA; only this
report changes afterward. CM checkout is clean after its report commit and push.

Limitations: one fixed CPU configuration and three seeds; no cross-host bit-equivalence,
throughput, generic optimality or mechanism-necessity conclusion. Technical checks establish
conformance, not scientific truth. Next step: DM intake of the accepted result and Root
integration of the explicitly owned commits. The owner-item boundary read returned no
pending owner instructions.
