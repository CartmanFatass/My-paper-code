# DISH post-B03 Convergence: evidence and options (DM proposal, 2026-09-06)

Claim under test: on the corrected ordinary renewal boundary, from matched initialization and
identical small training exposure, the joint forecast package raises whole-episode native service
over the inherited learner. Binding structure: one learning controller's action delivery and
learned motion during handover on the A03 ground-terminal host; other-agent partial observability
and state ownership stay distinct.

Proposal only, for the existing `em:degraded_incumbent_shadow_handover:convergence` node, written
by the Claude research hub as DM after the intake of `DISH-FORECAST-PACKAGE-B03`. Not a card, not a
launch, not a Portfolio action.

## What B03 observed (observation)

- Object as you selected it: CONTROL versus FORECAST_PACKAGE on the corrected boundary
  (`3f4d447f6`, both arms), seed 73 (master `b938a93e…`), 16 updates × 32 lanes × 128 ticks,
  512 optimizer steps, update-16 checkpoint, four development conditions, 1,200-tick fixed
  horizon; thin B03 entry reusing B02's study (Grok Build, hub review, `ad01757c4`); focused
  check on `wsl_4070` 21 passed including `test_package.py`, C = 4.94 s; both arms `COMPLETE`,
  211.04 s and 196.18 s wall, pair charge 412.16 s of 3,600 s. Two CONTROL attempts before that
  failed in the launch wrapper (SSH quoting; missing `PYTHONPATH`) before any learner work and
  are preserved without exposure.
- Primary: `Delta_B03 = −272.0` mean service ticks (CONTROL 460.5, package 188.5) against MEI
  +24; rows 452/92, 458/222, 449/129, 483/311 (differences −360, −236, −320, −172). All eight
  episodes reached the fixed horizon; the package's TERRAIN K4_TO_K12 episode records
  `separation_breach` 1 and `invalid_commit` 17 and a native `separation_below_15` cause at the
  horizon (14.71); CONTROL has zero hard events; no legal transfer anywhere; package energy
  4–7 % lower per row. Card §5 row 3 applied: adverse regardless of the energy proxy
  (`DISH_FORECAST_PACKAGE_B03_RESULT_INTAKE_20260906.md`).
- Training side, both arms: update 1 identical (4,016 of 4,096 lane-ticks served, 98 %); then
  training service falls in both arms to 435 (CONTROL) and 1,340 (package) by update 16, with a
  rise at the update-10 reset boundary (2,764 / 2,684) and a second fall; final checkpoints serve
  38–40 % (CONTROL) and 8–26 % (package) of the 1,200-tick horizon. The package's mean loss and
  gradient norm explode at updates 2 and 10–13 (loss up to 6.54 M, gradient norm up to 1.76 M),
  all finite, recovering to O(30) by update 15; CONTROL's peak gradient norm is 875 (update 10).
  Service-label eligible transitions 18,775 (CONTROL) versus 7,972 (package); parameter L2
  displacement 8.61 versus 7.51 from a common initial norm 38.25.
- Predictions: your prospective judgement (adverse/inside/mixed are serious outcomes) held; the
  DM's inside-margin prediction was wrong on every row.
- B02 (lagged interface, seed 61): 572/447/433/428 in both arms, delta 0, inside MEI; its
  qualified reading stands and is not re-read by B03. B02 and B03 are not two replicates.

## Unknowns the DM cannot resolve locally

- Whether the initialization itself serves the horizon at the level of CONTROL's final
  checkpoint or higher (the training curve says update 1 was near-saturated; evaluation of the
  initial parameters was never run; the 1,200-tick evaluation and the 128-tick training lanes
  differ in horizon and reset structure).
- Whether the both-arm training-service collapse is an artefact of the corrected boundary
  (fresh motion now delivered at admission) or was present on the lagged path too (B02's curves
  exist in `b02_20260905/`; the DM has not compared them here).
- The cause of the package's loss explosions (NLL scale on the corrected path, covariance
  conditioning, or the sigmoid interface's lower label support): not localized; no experiment
  run.

## Options (DM ordering; the node decides)

1. **End the forecast-package family** (B02 inside-MEI on the lagged path; B03 adverse on the
   corrected path): no further package variants, coefficient retuning or seeds for the package at
   this exposure; keep both results as the family's evidence. Does not by itself decide the
   family's successor.
2. **One bounded A/RECON zero-training witness on the corrected boundary** (option a in
   `EXPOSURE_AND_COST.json`): evaluate the common initial parameters and both update-16
   checkpoints on the four B03 conditions, 1,200 ticks each, paired exogenous randomness, zero
   training; 3 × 4 episodes, projected well under 60 s plus native build. It decides whether
   sixteen updates degraded evaluation service from initialization in both arms, which is the
   fact any learner-side next object would rest on. The DM recommends 1 + 2.
3. **An outcome-informed learner-stability B on the corrected boundary** (option b): CONTROL
   learner versus one named stabilizing change (learning rate 3e-5, or 1 epoch, or gradient
   clipping) at the same 16-update exposure, one paired seed, MEI +24, ≤ 1,800 s per arm. The DM
   does not recommend choosing it before option 2's fact exists; it would be a new object with
   its own card.
4. **Park DISH** at this boundary (everything committed; both checkpoints retained on the node).
   Legitimate if the node judges the family's information value spent; the DM's argument
   against: the corrected boundary is new and the both-arm collapse is an unexplained, cheap-to-
   probe fact.

Questions for the node: which of 1–4 (or another finite object) and why; if 2, the exact
policies and conditions, whether B02's update-16 checkpoints (lagged path, seed 61) are also
witnesses, and the stop boundary; if 3, the named change, seed count and reading rule; whether
the both-arm degradation changes how B01/B02/B03 are read; any Portfolio-tier consequence (the
DM proposes none).

## Cost facts

B03 pair 412.16 s charged (211.04 + 196.18 + 4.94); B02 pair 642.66 s; family cumulative
262,144 ordinary training transitions over two pairs. Option 2 has no measured cost; the B03
arm's four evaluation episodes ran inside a 196–211 s arm whose collection took ~11 s per
4,096 lane-ticks; A02's 64 ticks took 0.092 s. Option 3 projects to ~410 s per pair from B03.
No consultation exposure.
