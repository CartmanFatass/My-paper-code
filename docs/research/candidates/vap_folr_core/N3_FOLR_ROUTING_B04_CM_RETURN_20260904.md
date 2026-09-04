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
