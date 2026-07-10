# CSOG Gate-First Research Roadmap Implementation Plan

> **SUPERSEDED 2026-07-10. DO NOT EXECUTE.** The graph-first CSOG design was
> replaced by the user-approved IMOD-Direct design draft at
> `docs/superpowers/specs/2026-07-10-imod-direct-design.md`. Per the
> brainstorming written-spec review gate, no replacement implementation plan
> exists yet.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement linked phase plans task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and evaluate Causal Skill Operator Graph (CSOG) as a clean, gate-first HMASD+OPT successor without carrying the legacy algorithm's compatibility surface into the new research stack.

**Architecture:** CSOG lives in a new top-level `csog/` package and reuses only the environment contract and collection infrastructure. The legacy HA-CTSE policy is permitted only as a temporary source of real behavior for G0; old `Z`, `q_A`, `q_d`, `q_D`, duration-policy, and probe mechanisms do not enter the new package. Each phase produces a falsifiable artifact and later phases are planned in executable detail only after the prior gate passes.

**Tech Stack:** Python, PyTorch, NumPy, pytest, Gymnasium-compatible HMASD environments, NPZ/JSON experiment artifacts, cloud CUDA.

## Global Constraints

- Execute implementation in an isolated branch/worktree, with `codex/csog-radical` as the default branch name.
- Do not preserve legacy checkpoint, CLI, reward, probe, or configuration compatibility inside `csog/`.
- Reuse `ha_ctse_process.env_factory` and `ha_ctse_process.collectors` only as environment infrastructure until a separate environment package is justified.
- The deployed low-level actor is decentralized and has signature `pi_i(a_i | o_i, z_i)`.
- The deployed actor cannot read global state, the world model, the program graph, or raw communication indicators.
- Environment task reward remains external and is never relabeled as intrinsic.
- No intrinsic reward is computed from raw communication indicators.
- New reward paths are default-off and open only after real forced-intervention evidence passes the registered gate.
- `q_A`, `q_d`, and `q_D` reward paths remain absent from CSOG.
- Every CSOG mechanism supersedes a named legacy mechanism; CSOG is not an additional parallel reward stack.
- 160k and 320k runs are mechanism gates, not final performance verdicts.
- Approximately 1M-step matched multi-seed runs are required for the thesis-level task claim.
- Compute-bearing work defaults to cloud CUDA. A runner must fail if CUDA is unavailable; it must not fall back to CPU.
- Runtime artifacts live under `logs/<experiment-id>/`; no loose root-level logs, CSVs, JSON files, or checkpoints.
- Train, validation, and test windows are grouped by environment episode or trajectory. Adjacent windows never cross splits.
- All compared probes/models use equal capacity, optimization budget, validation-based early stopping, and device class.
- No phase launch is authorized by this roadmap alone.

---

## 1. Branch And Package Strategy

The implementation branch is intentionally allowed to break from the old algorithm. The clean ownership boundary is:

```text
csog/
  recognition.py          OPT online/target interaction representation
  trajectory.py           real trajectory contracts and storage
  dynamics_data.py        grouped windows, scaling, and diagnostic nulls
  world_model.py          distributional multi-horizon latent dynamics
  g0.py                   dynamics metrics and G0 disposition
  operators.py            reachable-effect candidates and codebook
  distillation.py         reward-off operator-conditioned behavior cloning
  interventions.py        real forced-operator protocols and evidence
  graph.py                sparse autoregressive program graph policy
  scheduler.py            asynchronous event-driven node execution
  rewards.py              gated operator progress channel only
  trainer.py              CSOG rollout/update/version-boundary orchestration
  checkpoint.py           CSOG-only checkpoint schema

scripts/
  export_csog_g0.py
  analyze_csog_g0.py
  run_csog_g0_cloud.sh
  ... phase-specific runners created only after their prerequisite gate opens

tests/csog/
  ... tests mirroring the focused modules above
```

Legacy code remains available for comparison but is not a dependency of the deployed CSOG stack. The one exception is `scripts/export_csog_g0.py`, which may load a healthy legacy policy checkpoint to generate real action/state trajectories. That adapter is diagnostic infrastructure and must not be imported by `csog/`.

## 2. Stage Dependency Graph

```text
Phase A: frozen OPT dynamics feasibility
  G0 PASS
     |
     v
Phase B1: reachable operator discovery
  G1 PASS
     |
     v
Phase B2: reward-off distillation + real forced execution
  G2 PASS
     |
     v
Phase C: sparse program graph + asynchronous scheduler, operator coefficient zero
  G3 PASS
     |
     v
Phase D: gated operator progress signal versus coefficient-zero control
  G4 PASS
     |
     v
Phase E: mature event/fixed/shared thesis matrix
  G5 PASS or bounded negative result
```

No downstream task result can compensate for an upstream gate failure.

## 3. Phase A: Dynamics Feasibility And G0

**Detailed executable plan:** `docs/superpowers/plans/2026-07-10-csog-phase-a-g0.md`

**Scientific question:** Can a frozen OPT interaction state support action-conditioned, calibrated multi-step prediction on real, non-collapsed policy behavior?

**Implementation boundary:** Build a standalone diagnostic stack. Do not modify PPO, policy architecture, rewards, skill assignment, or legacy training code.

**Primary artifacts:**

- frozen encoder hash and real episode trajectory shards;
- grouped train/validation/test manifest;
- equal-budget real-action and action-shuffle ensembles;
- persistence baseline;
- H10/H20/H50 held-out error and uncertainty calibration report;
- machine-readable `PASS` or `FAIL` G0 disposition.

**Data-validity precondition:** The gate is not read unless trajectories come from a documented healthy checkpoint, contain real environment transitions, have episode-separated splits, and show non-degenerate action and latent variation.

**G0 criterion:**

- real-action model beats persistence at H10, H20, and H50;
- real-action model beats the same-capacity action-shuffle model at H10, H20, and H50;
- H50 error is at least 10% below the stronger of those two nulls;
- pooled held-out uncertainty/error Spearman rho across H10/H20/H50 is at least 0.3.

**Estimated CUDA cost:** 15-30 minutes for trajectory collection plus 1-2 hours for the equal-budget ensembles. Use one cloud GPU; implementation tests remain short CPU unit tests.

**Decision:**

- `PASS`: freeze the G0 dataset/report and write the executable Phase B1 plan.
- `FAIL`: archive the negative result and stop CSOG operator/graph implementation. A materially changed recognition or dynamics mechanism requires a new design disposition before another G0.
- `INVALID`: repair only the data/instrument defect, preserving the registered model/null/gate definitions.
- `MIXED`: treat as `FAIL` for progression; do not average away a failed horizon or calibration condition.

## 4. Phase B1: Reachable Operator Discovery And G1

**Entry condition:** G0 is `PASS` on real behavior.

**Scientific question:** Does the current policy's real behavior contain at least three stable, context-matched, reachable H50 effect families?

**Implementation scope:**

- fit the online/target OPT encoder lifecycle with a fixed discovery-cycle target;
- construct real effect windows `e_t^H = h_{t+H} - h_t`;
- exclude high-uncertainty and representation-drift windows;
- discover candidates from real supported effects only;
- audit agent, phase, duration, and history leakage;
- promote/retire codebook entries at a slow boundary.

**Prohibited in this phase:** actor conditioning changes, operator reward, graph policy, graph reward, q_A/q_d/q_D, model-imagined effect prototypes.

**G1 criterion:** At least three supported operators, normalized usage entropy at least 0.8, no operator above 50% usage, and held-out H50 between/within effect ratio at least 1.2.

**Estimated CUDA cost:** offline analysis on the G0 corpus, expected 1-2 hours after the first calibrated implementation.

**Decision:**

- `PASS`: freeze codebook version 1 and write the Phase B2 executable plan.
- `FAIL`: stop graph work. If reachable effects exist but do not support a graph-ready codebook, evaluate the already-approved Effect-Addressed Skill Codebook fallback.

## 5. Phase B2: Reward-Off Distillation, Intervention, And G2

**Entry condition:** G1 is `PASS` with a frozen codebook.

**Scientific question:** Can decentralized actors execute operator identities, rather than merely receive diverse labels?

**Implementation scope:**

- add `pi_i(a_i | o_i, z_i)` with no global, graph, model, or communication input;
- assign stopped-gradient operator labels to real high-confidence windows;
- distill observed actions with supervised loss only;
- run matched active/inactive distillation arms with all intrinsic reward coefficients zero;
- collect real forced-operator interventions from matched initial contexts;
- run behavior-only held-out separability against pre/history/duration/agent nulls.

**Prohibited in this phase:** operator progress reward, team graph, composition reward, graph PPO, model-imagined action targets.

**G2 criterion:** Real forced H50 between/within at least 1.2, H50 ratio not below H10, behavior-only residual at least 0.05, positive fraction at least 0.60, and the real variant above every registered null.

**Estimated CUDA cost:** 1.5-2 hours per 160k arm; 3-4 hours serial for the matched pair, plus intervention analysis.

**Decision:**

- `PASS`: freeze executor and codebook versions; write the Phase C executable plan.
- `FAIL`: do not increase a reward coefficient. Distinguish discovery failure from actor-capacity failure, then either revise the executor mechanism under a new design or retire CSOG.

## 6. Phase C: Program Graph, Scheduler, And G3

**Entry condition:** G2 is `PASS` on real forced execution.

**Scientific question:** Does sparse graph structure add real joint effect semantics beyond independent operator marginals?

**Implementation scope:**

- sparse autoregressive node and bounded-edge generation;
- one active node and at most one pending successor per agent;
- generic `enable`, `inhibit`, `co-activate`, and `none` edges;
- local event-driven replanning and explicit close reasons;
- graph PPO using external return only;
- operator-progress coefficient fixed to zero;
- joint-versus-marginal model and all graph structure nulls;
- real node/edge ablation interventions.

**Prohibited in this phase:** active operator intrinsic reward, composition reward, q_A, q_D, sampled duration policy, graph commitments crossing PPO policy versions.

**G3 criterion:** Joint held-out NLL at least 10% below individual marginals, better than every graph null, and real node/edge intervention between/within at least 1.2 in the predicted direction.

**Estimated CUDA cost:** 2.5-3 hours per 320k run; 5-6 hours for two seeds; 10-12 hours including matched graph-off controls.

**Decision:**

- `PASS`: freeze graph/scheduler semantics and write the Phase D executable plan.
- `FAIL` with G2 retained: keep the individual operator contribution and drop the team-graph claim.

## 7. Phase D: Gated Operator Progress And G4

**Entry condition:** G3 is `PASS`; G2 remains above threshold on the current executor.

**Scientific question:** Does a calibrated operator-progress channel improve execution without damaging task behavior or semantics?

**Implementation scope:**

- implement `r_op = confidence_gate * clip(gamma * Phi_k(h_{t+1}) - Phi_k(h_t))`;
- source `Phi_k`, support, and uncertainty from a pre-rollout frozen snapshot;
- inject the channel only into the focal low-level executor;
- log external and operator channels separately;
- compare coefficient-zero and active arms with identical architecture and compute;
- verify exact zero outside support and after node close.

**Prohibited in this phase:** graph intrinsic reward, environment reward relabeling, raw communication reward features, q_A/q_d/q_D, counterfactual graph baseline.

**G4 criterion:** G2 remains above threshold, final 320k coverage is not more than 10% relatively below coefficient-zero control, and two seeds agree in effect direction.

**Estimated CUDA cost:** two arms by two seeds at 320k, approximately 10-12 hours serial.

**Decision:**

- `PASS`: freeze the reward contract and write the Phase E executable plan.
- `FAIL`: retain CSOG as a reward-off operator/graph contribution if G2/G3 stand; retire the operator-progress reward claim.

## 8. Phase E: Mature Thesis Matrix And G5

**Entry condition:** G0-G4 all pass.

**Scientific question:** Do event-driven operator composition and asynchronous lifetime produce mature task benefits beyond fixed/shared controls?

**Minimum matched matrix:**

- CSOG event-driven scheduler;
- CSOG fixed lifetime;
- CSOG shared/synchronous lifetime;
- CSOG graph-off individual-operator control;
- best established HMASD control under matched environment, seed, budget, and evaluation protocol.

**G5 criterion:** Approximately 1M-step multi-seed evidence beats the best fixed/shared CSOG control, reaches `coverage_eq1_step_fraction >= 0.5`, and maintains a low failed/zero-service episode fraction.

**Estimated CUDA cost:** 7-8 hours per 1M run. A five-arm, three-seed matrix is approximately 105-120 GPU-hours before parallelism; reduce only by a pre-registered sequential design, never by dropping the decisive controls after seeing results.

**Decision:**

- `PASS`: support the full causal-operator, structural-composition, and endogenous-temporality claim within the tested environment scope.
- operator/graph mechanism passes but task utility fails: report a mechanism contribution, not a task-performance victory.
- mixed seeds or unstable controls: no thesis-level performance claim.

## 9. Mechanism Retirement Ledger

| Legacy mechanism | CSOG replacement | Earliest phase it may exist |
| --- | --- | --- |
| sampled team label `Z` | executable graph `G` | Phase C after G2 |
| q_A actionability reward | graph intent directly contains assignment | retired from branch start |
| q_d label-recovery reward | gated operator progress | Phase D after G3 |
| q_D team discriminator/reward | graph-versus-marginal composition evidence | diagnostic in Phase C, never reward |
| parallel independent assignment | sparse autoregressive graph | Phase C after G2 |
| sampled duration policy | event-triggered close semantics | Phase C after G2 |
| old intrinsic stack | no parallel equivalent | retired from branch start |

## 10. Controller Checkpoint After Every Phase

Before writing or executing the next phase plan, the controller must report:

- **Situation:** exact artifacts, seeds, device class, and completion state.
- **Meaning:** factual gate evidence separated from interpretation.
- **Next plan:** pass/fail/invalid/mixed branch and its only authorized next action.
- **Recommendation:** continue, stop, repair the instrument, or select the fallback.
- **Core MARL impact:** reward, actor/critic, optimizer/loss, collector, environment, latent semantics, graph, or diagnostic-only.
- **Open gates:** exact unmet threshold, null, intervention, or review decision.

## 11. Roadmap Completion Definition

The roadmap is complete when one of these terminal states is documented:

1. G5 passes with mature matched multi-seed evidence.
2. A gate fails and CSOG is archived as a bounded negative result.
3. G2 passes but G3 fails, yielding an individual causal-operator contribution without a graph claim.
4. G3 passes but G4/G5 fails, yielding a reward-off mechanism contribution without a task-performance claim.

Stopping at a failed gate is a valid research outcome and does not authorize adding compensating mechanisms.
