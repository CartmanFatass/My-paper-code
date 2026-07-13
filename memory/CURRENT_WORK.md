# HA-CTSE Current Work

Updated: 2026-07-14

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

Find an individual-skill target that is defined inside the natural on-policy
trajectory domain:

```text
on-policy state visitation
-> support-compatible, non-shortcut individual differentiation signal
```

- R27-G2 established forced persistent conditional capacity and a local effect;
  R26 remains the natural observational negative. This does not establish
  natural selection, reward usefulness, cooperation, credit, or task gain.
- R28-G0 `PASS_TARGET_NULLS` froze the only accepted scorer.
- Two exact R28-G1 one-update engineering smokes reproduced
  `FAIL_SUPPORT_OOD`: OOD `0.950617` and `0.9375`, one support kill each, and
  zero R28 reward-applied steps. The formal three-arm reward experiment never
  ran and has no scientific outcome.
- Feature/order/action/duration/distance parity is confirmed. The dominant
  residuals are all four temporal action standard deviations, consistent with
  a real forced-deterministic to natural-on-policy trajectory-domain shift.
- The frozen G1 launch package is therefore `BLOCKED_SUPPORT_OOD`; the completed
  cross-round review is
  `memory/LTM/R26_R27_R28_FAILURE_REVIEW_20260713.md`.
- The 64-reset paired transport diagnostic returned
  `FAIL_STOCHASTIC_SUPPORT_TRANSPORT`: deterministic OOD `0.068359` versus
  stochastic OOD `0.823242` across 1,024 paired windows per mode. Random action
  execution alone reproduces the action-std domain shift.
- The forced-deterministic R28-G0 scorer family is retired from online reward
  use. It must not be refit, widened, or carried into another reward package.
- R29-G0 passed at update25, update30, and final. Active action-information
  means are `0.017050`, `0.017990`, and `0.019208` nats; the inactive control is
  numerical zero and every active skill clears its floor. A support-native
  individual action-information target therefore exists on natural on-policy
  states; this does not yet establish reward usefulness or task gain.
- GPT-5.6 Pro modified the pointwise reward into R29-T10: fixed-skill recurrent
  replay over each complete natural lifetime, final-10-step density ratio, one
  endpoint reward, low GAE only. The pointwise online reward is retired.

## Next Actions

1. Complete the R29-T10 implementation and launch the authorized local paired
   run: one seed, two concurrent 16-env CUDA arms, +320K steps per arm.
2. Collect final task/R26 evidence and prepare the raw result/question ZIP for
   manual GPT-5.6 Pro review before choosing the next research route.

## Immediate Constraints

- Do not refit, retune, or sweep the frozen R28-G0 scorer.
- Do not launch the blocked R28-G1 cloud package or repeat the identical local
  smoke.
- Do not rerun the fixed HMASD baseline or R25 arm0/arm2 references without
  explicit user approval.
- Keep the old `q_d/q_D` reward paths and default-off `q_A` disabled. Do not add
  team reward, communication-intrinsic mechanisms, kappa/hazard, or DADS while
  the individual-differentiation gate is open.
- Do not reinterpret forced R27 capacity as natural use or a team-level claim.
- Keep R29 default-off and compare `probe_only` versus `real_reward` with the
  same source, seed, exposure, optimizer settings, and other rewards.

## Pointers

- `memory/ALGORITHM_PRINCIPLES.md` — binding research contract.
- `memory/IMPLEMENTATION_PLAN.md` — active transport implementation boundary.
- `memory/ExpRecord.md` — formal experiment contracts, evidence, and decisions.
- `docs/research/R28_G1_CAUSAL_SKILL_FORCING_REWARD_DESIGN_20260713.md` — frozen
  R28-G0/G1 design.
- `docs/research/R27_G2_FORCED_Z_TRAJECTORY_EFFECT_DESIGN_20260712.md` — frozen
  R27-G2 design.
- `memory/LTM/IMPLEMENTATION_PLAN_ARCHIVE_20260713.md` and
  `memory/LTM/EXPERIMENT_ARCHIVE.md` — superseded/completed detail.
- `memory/LTM/external_reviews/` — raw external-review evidence and index.
