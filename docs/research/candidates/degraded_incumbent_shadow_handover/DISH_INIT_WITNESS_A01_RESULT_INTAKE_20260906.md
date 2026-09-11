# DISH-INIT-WITNESS-A01 result intake — 2026-09-06

Card `DISH_INIT_WITNESS_A01_SCIENCE_CARD_20260906.md` (A/RECON, selected by the post-B03
Convergence response at `f85016d76`, `PRO_FINAL`); CM record
`DISH_INIT_WITNESS_A01_CM_RECORD_20260906.md`; launch sha `3c0ed5c87f91ec0e4692aa7dd0214f83482b4418`;
evidence `init_witness_a01_20260906/` (summary, receipt, timings, logs, launch script). Direction
Manager: the Claude research hub. Predictions scored in §4.

## 1. Execution facts (observation)

- Node `wsl_4070`, worktree `dish-witness-3c0ed5c` at the launch sha, single CPU thread, FP32
  policy / float64 native, unchanged host `GROUND-TERMINAL-LINEAR-CLEARANCE-A03` and corrected
  boundary.
- Attempt r1 (`agent-task dish_witness_a01_20260906`, 20:52Z) stopped in the focused check
  (1 failed, 4 passed, 5.8 s): the node worktree's cone sparse-checkout omits `docs/`, so the
  frozen evidence input `b03_forecast_package_20260906/{control,forecast_package}/summary.json`
  was not on disk. No preflight, model, native state or episode ran; no exposure. The committed
  evidence folder was staged into the sparse surface (bytes unchanged, HEAD unchanged) and the
  object relaunched once as r2 with a fresh output root.
- Attempt r2 (`agent-task dish_witness_a01_20260906_r2`, 20:58:44Z, exit 0): focused check
  5 passed in 4.58 s, `C = 4.981 s`; memory admission passed (15.67 GB available); formal run
  `COMPLETE`, 8 of 8 episodes, `prepublication_wall_seconds` 10.953, CPU 10.948 s, peak self RSS
  473 MB, `/usr/bin/time` wall 11.25 s. **Whole-item charge 4.981 + 11.25 = 16.23 s of the 120 s
  cap**; allowance was 115.019 s.
- Initialization: `reconstructed_from_master` (no saved zero-update snapshot exists; one
  initializer call), `initial_model_norm` 38.24996300787587 = the B03 check value
  (`norm_matches` true), `update` 0, Welford counts actor/snapshot/critic 0/0/0, helper
  objects model + optimizer; 8 policy constructions / 8 checkpoint loads (one per episode, as
  B03's `run_arm` does); zero-training counters all 0; parameter norm after every episode
  equals the initial norm.
- Inputs: the recorded `evaluation_rows[].reset` of the two B03 summaries (verified identical
  across arms and equal to the recomputed `_reset_row`), four conditions in B03's order.

## 2. Frozen rule applied verbatim and the observed readout

`D_a = (1/4) Σ_r (J_a,16,r − J_a,0,r)`, reused rows from the accepted B03 summaries.

| Condition (speed 4, slot 0, block 0) | J_0 CONTROL view | J_16 CONTROL | diff | J_0 PACKAGE view | J_16 PACKAGE | diff |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| TARGET_VISUAL_MASK / K8 | 467 | 452 | −15 | 467 | 92 | −375 |
| TARGET_VISUAL_MASK / K4_TO_K12 | 478 | 458 | −20 | 478 | 222 | −256 |
| TERRAIN_RELAY_MASK / K8 | 942 | 449 | −493 | 942 | 129 | −813 |
| TERRAIN_RELAY_MASK / K4_TO_K12 | 938 | 483 | −455 | 938 | 311 | −627 |
| **mean** | **706.25** | **460.5** | **D_C = −245.75** | **706.25** | **188.5** | **D_P = −517.75** |

All eight new episodes reached the 1,200-tick horizon (`fixed_horizon`), zero hard events in all
seven classes, zero legal transfers (service entirely before any transfer), energy 277,817 to
282,598 per row. Descriptive scale 24 ticks. Pattern (card §4 table): **row 1, `D_C ≤ −24`**, and
the package also drops, so the reading is a **shared conditional before/after loss**: on this
seed and panel both recorded update-16 controllers serve far below their own-interface
zero-update views (CONTROL by 35 %, the package by 73 % of the initial view mean). The two
TARGET rows of CONTROL are inside the band (−15, −20); the two TERRAIN rows carry the loss
(−493, −455).

**Independent fact at its own ceiling (observation).** The two zero-update views produced
identical rows on every condition: the same service ticks, the same energy to all printed
digits, the same terminal facts. The raw-logit and sigmoid service interfaces made no
difference to any evaluation outcome at initialization. Inference (labelled, not measured):
the service-probability input enters native decisions only around prepare/commit and
transfer, and none of those occurred in any zero-update episode (zero hard events, zero
transfers), so the interface value had nothing to act on; this does not transfer to the trained
controllers, whose package arm did attempt commits (B03: `invalid_commit` 17). The card's DM
prediction that the views would differ materially was wrong.

## 3. Reading under the card's rule

- **What the panel now supports.** "Sixteen updates degraded whole-episode evaluation service
  in both arms" is now an observation *conditional on this seed, this initialization and this
  panel*: the common initialization serves 706 mean ticks with no hard events, the trained
  CONTROL 460.5 and the trained package 188.5. This is the fact the response asked for before any
  learner-side proposal; it is not a general "learning harms" claim, provides no training
  replicate and attributes the loss to no component (PPO, learning rate, NLL, normalization,
  recurrent state, Welford statistics are all inside the before/after contrast).
- **What it motivates (card §4 row 1).** Concrete motivation for a *named* learner-stability B on
  the corrected boundary; it does not prove the learning rate too large or PPO wrong. Because
  the package also drops, the two arms are reported as one shared conditional loss, not as two
  seeds. Per the response, no outcome automatically buys a learner B, restores package
  investment or changes Portfolio: the successor is a direction-tier question for
  `em:dish:convergence`.
- **Ceiling.** The zero-update views are the same parameters under the empty normalization state
  (variance 1, clamp ±10) and fresh recurrent state; the trained controllers carry learned
  Welford statistics and parameters. The contrast is the complete controller state formed by
  training. Nothing here re-reads B03's package-adverse conclusion (unchanged), B02, B01 or
  A01–A05.
- **Cost.** 16.23 s of 120 s; 9,600 evaluation ticks; zero training work; the r1 attempt cost
  5.8 s of focused check and no exposure.

## 4. Predictions scored

- DM: predicted row 2 (`D_C > −24`, `D_P ≤ −24`) and materially different zero-update views.
  **Wrong on both**: `D_C = −245.75` (row 1) and the views were identical.
- Node (Pro): none numeric; the response listed every row as a serious outcome.
- Owner: not taken (unattended).

## 5. Decisions this intake produces

1. **Object tier, `OWNER_DELEGATED`**: accept r2 as the valid, complete A/RECON result (all
   inputs bound and verified, eight complete episodes, zero training counters, reused rows
   joined by coordinate). Options considered: (a) accept as complete; (b) quarantine pending a
   reproduction of the identical-views fact; (c) rerun with a different initialization.
   Selected (a): the identical views are an observation with a code-supported explanation
   labelled as inference, not a defect in the frozen path; (b) would add a reproduction the
   claim does not depend on (§8, diagnosis by reproduction); (c) is a different object.
   `Owner-delegated decision (unattended, 2026-09-03 instruction): (a)`.
2. **Direction tier**: the successor question (a named learner-stability B on the corrected
   boundary, or another finite object, or park) goes to `em:dish:convergence` as the
   post-witness Convergence request, with this intake, the witness summary and the B03 records
   as evidence; the DM proposes its options there. Nothing is launched meanwhile.
3. Records: ledger rows, DIRECTION addendum, Portfolio row, owner brief
   `owner/briefs/degraded_incumbent_shadow_handover/2026-09-06_init-witness-A01-result.md`,
   EXPERIMENT_TRACKING row.
