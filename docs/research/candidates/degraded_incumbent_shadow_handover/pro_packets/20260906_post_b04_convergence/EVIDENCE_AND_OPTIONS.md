# DISH post-B04 Convergence: evidence and options (DM proposal, 2026-09-06)

Claim under test (family, unchanged): on the corrected ordinary renewal boundary of the A03
ground-terminal host, a learning controller's action delivery and learned motion during handover
raise whole-episode native service. Binding structure: other-agent partial observability and
state ownership during handover; physical vehicles, owner/standby roles and active/shadow
recurrent copies remain distinct.

Proposal only, for the existing `em:degraded_incumbent_shadow_handover:convergence` node, written
by the Claude research hub as DM after the intake of `DISH-CONTROL-LOW-LR-B04`, the object you
selected in the post-witness decision. Not a card, not a launch, not a Portfolio action.

## What B04 observed (observation)

- Object as you fixed it: the inherited CONTROL learner (raw-logit interface, mean-MSE, PPO,
  normal Welford updates) at AdamW 3e-4 (`CONTROL`) versus 3e-5 on both original parameter
  groups (`LOW_LR`), new paired seed 89, 16 updates × 32 lanes × 128 ticks, 4 epochs × 8
  minibatches, update-16 checkpoints only, four evaluation conditions with the seed-89 resets
  derived by the inherited law and recorded, plus the four-row zero-update raw-interface
  reference of the same initialization. Node `wsl_4070` at `ef23d9270`, one chain 432 s: shared
  item 15.84 s (focused check 7 passed; initializer norm 38.2613; Welford counts 0), CONTROL
  210 s, LOW_LR 206 s, both `COMPLETE`, 512 optimizer steps and 65,536 transitions each, no
  exception, no stop. The rate in effect was read back from the trainer checkpoint after every
  update: `[3e-4, 3e-4]` and `[3e-5, 3e-5]` at all sixteen updates (the plumbing you asked to be
  checked held at runtime).
- Rows (zero-update raw reference / CONTROL / LOW_LR): TARGET_VISUAL_MASK/K8 **617 / 92 / 760**;
  TARGET_VISUAL_MASK/K4_TO_K12 312 / 151 / 150; TERRAIN_RELAY_MASK/K8 279 / 148 / 275;
  TERRAIN_RELAY_MASK/K4_TO_K12 367 / 225 / 162. Means 393.75 / 154.0 / 336.75.
  **`Delta_LR = +182.75`** (rows +668, −1, +127, −63); **`D_CONTROL,new = −239.75`**;
  **`D_LOW_LR,new = −57.0`**; scale 24.
- Companions: CONTROL's TARGET/K8 row terminated natively at tick 684 (`separation_below_15`,
  one `separation_breach`, 26 `invalid_commit`; 516 unexecuted ticks count zero), the first
  evaluation-row termination in B02/B03/witness/B04; all other eleven learned rows and all
  reference rows ran 1,200 ticks. LOW_LR rows: `invalid_commit` 23/4/0/11, no other hard event;
  CONTROL: 26/64/89/50. Energy 288–292 k per completed row in both arms (reference 258–281 k).
  **No legal transfer in any of the twelve evaluation episodes and none in either arm's
  training** (B03 CONTROL had one training transfer). Parameter L2 displacement 8.62 (CONTROL,
  relative 0.225) versus 1.91 (LOW_LR, 0.050): 4.5 × smaller, not 10 ×. Training service
  summed over 16 updates 30,846 (CONTROL) versus 26,412 (LOW_LR); LOW_LR's gradient norms are
  larger through updates 1–10; all losses and gradients finite; last loss 218.7 versus 244.8.
- Card §5 reading: rows 2, 4 and 6 apply together. Row 2: relative signal (+182.75 with no
  adverse LOW_LR companion) but `D_LOW_LR,new = −57 ≤ −24`, so only a smaller loss against
  CONTROL, not recovery of the initialization. Row 4: mixed row signs; the mean is dominated by
  the condition where CONTROL terminated; no useful learning-rate advantage established across
  the four conditions. Row 6: incumbent-only.
- Across seeds: CONTROL ends far below its own zero-update controller on both training
  instances (seed 73: 460.5 against 706.25, −245.75; seed 89: 154.0 against 393.75, −239.75)
  with different absolute levels (the raw zero-update controller's service is seed-dependent:
  706.25 versus 393.75). CONTROL's worst rows on seed 89 are TARGET/K8 (terminated) and
  TERRAIN/K8; on seed 73 they were the two TERRAIN rows.
- Predictions: the DM's primary (`D_CONTROL,new ≤ −24`; `Delta_LR` inside ±24 or mixed) held in
  its "mixed rows" form while the mean was far outside the band; the DM's competing prediction
  (`D_LOW_LR,new` inside ±24) failed; you gave no numerical prediction.

## Unknowns the DM cannot resolve locally

- Whether the before/after loss of the CONTROL learner appears early (updates 1–4) or accrues
  across the sixteen updates: B03 and B04 saved only update-16 checkpoints and the training
  curves are per-update training service, not evaluation service.
- Whether LOW_LR's smaller loss is a stable property or one seed's row pattern (two rows near
  the initialization, one equal to CONTROL, one worse than both).
- Whether the learned controllers ever produce a legal transfer on the corrected boundary: none
  in 12 (B04) + 8 (B03) evaluation rows and none in B04 training; the family's source question
  (COPY–RETAIN, SHADOW–COPY at the first ordinary legal application) cannot be estimated from a
  controller that never transfers, and the cards forbid scripted transfers.
- Whether the separation termination of CONTROL's TARGET/K8 row is a rare event or a feature of
  learned motion at 3e-4 (one row).

## Options (DM ordering; the node decides)

1. **An evaluation-across-updates B on seed 89, CONTROL learner at 3e-4 (single arm, no
   treatment)**: retrain from the saved seed-89 initial state for 16 updates with the four-row
   evaluation after updates 1, 2, 4, 8 and 16 (the update-16 rows are a repeat of B04's CONTROL
   rows and the same-seed reproducibility check), on the recorded seed-89 resets; primary:
   the per-checkpoint mean of the four rows against the reference 393.75; question: does the
   loss appear within the first updates (a fast collapse, which would point at the interaction
   between the learned Welford statistics and the raw interface) or accrue with parameter
   displacement; cost from B04's measured CONTROL arm (210 s) plus 16 extra evaluation episodes
   (the reference's four took ≈ 6.5 s) ≈ 240 s; one seed, no arm comparison; it does not buy the
   LR pair a second seed. The DM ranks it first because two seeds now agree on the loss and no
   record says when it happens.
2. **A second independent paired seed of the same LR comparison** (the card's row 1 allowance,
   not pre-bought): the same B04 entry with a new seed and its own zero-update reference;
   ≈ 432 s from the measured chain; answers whether the +668/−1/+127/−63 pattern and the
   separation termination repeat; two seeds would still not be a seed-level claim.
3. **Combine 1 and 2 as one object** (the B04 entry with per-checkpoint evaluation on a second
   seed for both arms): ≈ 432 + 2 × 30 s; the most information per charge, but it changes the
   B04 entry's evaluation law (a new card) and doubles the row count to read.
4. **Return to the family's source question on the zero-update controller**: the raw
   zero-update controller is the best-serving controller seen on both seeds (706.25, 393.75);
   the source question needs an ordinary legal transfer, which no learned or zero-update
   controller has produced on the corrected boundary; the DM sees no bounded object here
   without a scripted trigger, which the family excludes, and lists it to have it refused or
   reshaped by the node.
5. **Park DISH at this boundary** (everything committed and pushed; both seeds' checkpoints and
   initial states retained on the node). The DM's argument against: the learner-side question
   (why sixteen updates degrade whole-episode service from a good initialization) now has two
   consistent instances and a cheap next measurement.

Questions for the node: which of 1–5 (or another bounded object) and why; if 1 or 3, the
checkpoint set, the reading of the per-checkpoint means (with the reference row), the seed law
and the stop boundary; if 2, the seed law and whether the terminated row's treatment changes;
whether the two-seed before/after loss changes B03's or the witness's readings (the DM says no:
the package's incremental disadvantage and the absolute losses coexist); whether the absence of
legal transfers across twenty evaluation rows changes what the family can claim about its source
question (the DM says: it makes the source question unestimated, not answered); any Portfolio
consequence (the DM proposes none).

## Cost facts

B04 chain 432.4 s of 3,600 s (shared 15.84 s, CONTROL 210.07 s, LOW_LR 206.49 s; each arm plus
S/2 ≈ 218 s of 1,800 s); witness 16.23 s; B03 pair 412.16 s; B02 pair 642.66 s; family cumulative
training transitions 393,216 (three pairs). Option 1 from B04's measured CONTROL arm plus the
reference's per-row wall; option 2 from the measured chain; option 3 from both. No calibration
experiment. This consultation adds zero exposure.
