# HA-CTSE Current Work

Updated: 2026-07-15

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
- **Local overnight authorization:** the user permits a longer local CUDA run
  overnight when the next causal gate is registered and requires it. R35 used
  that authorization and has reached its registered terminal result.
- **Default review handoff:** once a tracked question is committed and pushed,
  Codex automatically submits it in the existing `HMASD Algorithm Consultation`
  browser conversation with the `Pro` model, archives the raw response, and
  continues only the accepted registered branch. Do not create duplicate review
  conversations.

## Current Objective

- Active objective: implement and run `EXP-20260715-r38-cts-access` from the
  single contract in `memory/ExpRecord.md`. R37 is retired; do not return to the
  Alice-Bob access family.

## Next Actions

- Immediate next action: implement the CTS environment, ordinary constant-code
  recurrent MAPPO configuration, and the single local runner/analyzer described
  in `docs/superpowers/plans/2026-07-15-r38-cts-access-gate.md`.

## Immediate Constraints

- Do not refit, retune, or sweep the frozen R28-G0 scorer.
- Do not launch the blocked R28-G1 cloud package or repeat the identical local
  smoke.
- Do not rerun the fixed HMASD baseline or R25 arm0/arm2 references without
  explicit user approval.
- Keep the old `q_d/q_D` reward paths and default-off `q_A` disabled. Do not add
  team reward, communication-intrinsic mechanisms, kappa/hazard, or DADS before
  the post-R33 failure review selects and registers one new causal edge.
- Do not reinterpret forced R27 capacity as natural use or a team-level claim.
- Keep R29 diagnostic-only. Its online `real_reward` path and variants that
  alter only prior, window, aggregation, coefficient, normalization, or clip
  are retired.
- Do not tune or enlarge duration candidates, restore a duration head or
  duration entropy floor, or use duration as a skill-semantic input in the
  active core.
- R30 uses no keep entropy, edit/switch penalty, forced maximum lifetime, or
  positive lifetime reward. Long survival must be learned from delayed task
  advantage rather than paid for directly.
- Do not use environment potential/progress shaping in Alice--Bob sparse
  exploration claims, and do not count shaped progress as algorithmic intrinsic
  reward. The completed 64K shaped pair remains mechanism-only evidence.
- Do not customize intrinsic reward to a benchmark. Any future intrinsic term
  must keep one environment-agnostic mathematical form and input contract and
  must not consume task identities, goals, contacts, phases, success predicates,
  distances, or external reward.
- Do not inject another individual-skill reward; the R29/R31/R32 individual
  action/effect lines are retired.
- Do not launch R31 reward, its 160K pair, an identical-batch append, or any
  R31 coefficient/window/prior/posterior/null/threshold variant.
- Do not integrate R32 into normal training. Permanently prohibit direct IFEPG
  rescue by learning-rate, update-count, window, replica, effect, threshold,
  seed, reward/scorer/value objective, or parameter-scope changes.
- R33 may update only `FixedClockAREditPolicy.skill_head`. Keep the low policy,
  keep head/shared high trunk, critics, OPT/bridge, posteriors, team latents,
  `q_d/q_D`, task reward, and environment shaping outside its objective.
- Do not rescue R33 with temperature, more updates, score clipping, another
  pair permutation, new team latent, `q_D`, team reward, seed expansion, or
  normal-trainer integration.
- Do not let `real_modes > sham` alone count as R34 mode creation; the real arm
  must also clear the frozen-source anchor. Do not use teammate motion, reward,
  action, age, agent ID, or task fields to define focal mode labels.
- Do not change R34 K, descriptor, clustering, optimizer exposure, parameter
  scope, window, seed, or thresholds after its result. A downstream
  frozen-selector or coverage failure does not erase an M1 codebook pass.
- R34 did not pass M1. Do not rerun or rescue it with another label balance,
  clustering family, replay epoch count, recurrent/FiLM scope, source seed,
  threshold, normal-trainer objective, or sham comparison.
- R35 is a baseline reset, not a new skill algorithm. Do not compare a trained
  arm with a frozen arm, initialize from the trained R30 checkpoint, inject an
  auxiliary reward, or treat two zero-access arms as noninferiority. A single
  320K seed cannot establish general hierarchy value or HMASD/S7 parity.
- R36's exact direct-cell episodic novelty is retired. Do not rescue it with a
  different grid, count window, formula, coefficient, seed, budget, RND/ICM
  relabeling, or a lower access gate. Coverage is not collection access.
- R37 may expose only current active plate/target identity to the treatment
  actor. Do not add clocks, contacts, collection/progress state, reward fields,
  shaping, oracle actions, skills, hierarchy, intrinsic reward, or a second
  algorithm route. A valid R37 failure retires this sparse Alice--Bob access
  gate rather than authorizing retuning or expansion.
- R37 is now retired by that valid-FAIL branch. Do not rerun it, lower its cycle
  floor, expand its budget/seeds, change its horizon/contact geometry, or treat
  passed M2/M3 as an overall PASS.

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
- `memory/LTM/R29_ACTOR_DENSITY_RATIO_FAILURE_REVIEW_20260714.md` — accepted
  R29 retirement and next causal edge.
- `docs/research/R30_FIXED_CLOCK_AR_EDIT_DESIGN_20260714.md` — accepted temporal
  controller and implementation boundary.
- `docs/external-review/gpt5_6_pro/20260714_fixed_clock_keep_set/` — raw external
  response and controller disposition.
- `docs/external-review/gpt5_6_pro/20260714_r30_algorithm_code_review/` — raw
  `MODIFY R30` review and accepted controller disposition.
- `docs/external-review/gpt5_6_pro/20260714_r30_sparse_exploration_review/` —
  current result boundary and manual review entry for the next intrinsic route.
- `docs/external-review/gpt5_6_pro/20260714_r31_cfei_gate_result/` — raw R31
  result review, corrected failure interpretation, and accepted R32 gate.
- `docs/external-review/gpt5_6_pro/20260714_r32_ifepg_gate_result/` — manual
  review entry, raw response, and controller disposition for R32/R33.
- `memory/LTM/R29_R33_EFFECT_COMPOSITION_FAILURE_REVIEW_20260714.md` —
  cross-round failure and baseline matrix after the valid R33 failure.
- `memory/LTM/R35_R37_SPARSE_ACCESS_FAILURE_REVIEW_20260715.md` — current
  cross-round access failure and replacement-benchmark boundary.
- `docs/external-review/gpt5_6_pro/20260714_r33_irsc_gate_result/` — tracked
  result-review question for the single post-R33 causal edge.
- `docs/external-review/gpt5_6_pro/20260715_r34_bhmd_gate_result/` — tracked
  R34 result audit, rejected first R35 route, and correction entry.
- `docs/external-review/gpt5_6_pro/20260715_r36_aem_access_result/` — tracked
  R36 valid-failure and Alice--Bob access-instrument review entry.
- `docs/external-review/gpt5_6_pro/20260715_r37_actor_visible_identity_access_result/`
  — tracked R37 result audit and replacement-benchmark request.
- `memory/LTM/external_reviews/` — raw external-review evidence and index.
