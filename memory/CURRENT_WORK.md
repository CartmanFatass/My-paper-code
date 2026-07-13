# HA-CTSE Current Work

Updated: 2026-07-13

Purpose: the single mandatory first read. Keep only controller ownership, the
current objective, next actions, immediate constraints, and pointers. Evidence
and history live in their owning files.

## Controller Handoff

- **Active controller:** Codex on branch `aggressive`. Codex and Claude Code
  alternate; only one controller may modify the repository at a time.
- **Workflow authority:** `AGENTS.md`. Retired delegated-agent, Superpowers,
  routing, review-package, and lifecycle files are provenance only.
- **Versioning:** Git only; no application-layer hashes or checksums.
- **Project boundary:** IMOD is separate and is not evidence for HMASD. Its
  operational conventions may be consulted without importing its algorithms or
  experiment parameters.
- **Shared GPU scheduling:** Codex task
  `019f5aca-bde7-70b3-8c94-24584136c2c9` is the IMOD/HMASD lease controller.
  Formal cloud jobs must be registered there from an exact committed contract.

## Current Objective

Resolve the causal edge `distinct z_i -> naturally expressed, behaviorally
differentiated skills`.

- R27-G2 established forced persistent conditional capacity and a local effect;
  R26 remains the natural observational negative. This does not establish
  natural selection, reward usefulness, cooperation, credit, or task gain.
- R28-G0 `PASS_TARGET_NULLS` froze the only accepted scorer.
- R28-G1 implementation smoke completed with `FAIL_SUPPORT_OOD`: the exact
  update/checkpoint path worked, but the frozen support guard stopped R28 reward
  injection before scoring.

## Next Actions

1. Diagnose the completed run at
   `logs/r28_g1_engineering_smoke_20260713_212008/real_reward`: 81 structural
   rows, four in support, OOD fraction 0.9506, one support kill, and zero R28
   reward-applied steps.
2. Add only the minimum support-distance diagnostic needed to identify the
   dominant standardized feature residuals. Do not change the frozen scorer,
   features, variance floor, thresholds, reward scale, or guard.
3. If the diagnostic identifies a feature-construction mismatch, repair that
   bug and repeat the exact smoke once. If the feature construction is correct,
   block G1 as a natural-support mismatch and take the registered failure-review
   branch before proposing another target.

## Immediate Constraints

- Do not refit, retune, or sweep the frozen R28-G0 scorer.
- Do not execute the R28 cloud runner's `topology`, `run`, `evidence`, `analyze`,
  or `all` modes without separate formal authorization and matching topology
  validation through the shared scheduler.
- Do not rerun the fixed HMASD baseline or R25 arm0/arm2 references without
  explicit user approval.
- Keep the old `q_d/q_D` reward paths and default-off `q_A` disabled. Do not add
  team reward, communication-intrinsic mechanisms, kappa/hazard, or DADS while
  the individual-differentiation gate is open.
- Do not reinterpret forced R27 capacity as natural use or a team-level claim.

## Pointers

- `memory/ALGORITHM_PRINCIPLES.md` — binding research contract.
- `memory/IMPLEMENTATION_PLAN.md` — active R28 implementation boundary.
- `memory/ExpRecord.md` — formal experiment contracts, evidence, and decisions.
- `docs/research/R28_G1_CAUSAL_SKILL_FORCING_REWARD_DESIGN_20260713.md` — frozen
  R28-G0/G1 design.
- `docs/research/R27_G2_FORCED_Z_TRAJECTORY_EFFECT_DESIGN_20260712.md` — frozen
  R27-G2 design.
- `memory/LTM/IMPLEMENTATION_PLAN_ARCHIVE_20260713.md` and
  `memory/LTM/EXPERIMENT_ARCHIVE.md` — superseded/completed detail.
- `memory/LTM/external_reviews/` — raw external-review evidence and index.
