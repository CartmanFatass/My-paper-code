# DISH-CONTROL-LOW-LR-B04 result intake — 2026-09-06

Card `DISH_CONTROL_LOW_LR_B04_SCIENCE_CARD_20260906.md` (B/EXPLORE, opened by the archived
post-witness Convergence decision, `PRO_FINAL`, intake `DISH_POST_WITNESS_CONVERGENCE_INTAKE_20260906.md`);
CM record `DISH_CONTROL_LOW_LR_B04_CM_RECORD_20260906.md`; launch sha
`ef23d927045e449a0aa831e6a94a99d976e91924`; evidence `control_low_lr_b04_20260906/` (shared item,
CONTROL and LOW_LR summaries, `low_lr/paired.json`, recorded resets, receipts, timings, launch
script, task log). Direction Manager: the Claude research hub. Predictions scored in §4.

## 1. Execution facts (observation)

- Node `wsl_4070`, worktree `dish-b04-ef23d92` at the launch sha, single Torch thread, FP32
  learner, float64 native; one detached chain (`agent-task dish_b04_chain_20260906`, 22:16:45Z,
  exit 0, 432 s). Memory admission passed before the shared item and before each arm (≈14.6 GiB
  available).
- **Shared item S = 15.84 s** (focused check `7 passed` in 8.37 s; `shared` mode 6.55 s
  prepublication): one initializer call (seed-89 master `665c8d87…`), parameter L2 norm
  `38.26126788822669` (equal to the local test's reading), Welford counts 0/0/0, constructed
  optimizer rates `[3e-4, 3e-4]`; four recorded resets (`shared/resets.json`); the four-row
  zero-update raw-interface reference: **617 / 312 / 279 / 367, mean 393.75**, all four rows
  complete to 1,200 ticks, no legal transfer, hard events only `invalid_commit` 0/42/38/0, zero
  training counters, parameter norm unchanged after the episodes.
- **CONTROL (3e-4)**: `COMPLETE`, 16 updates, 512 optimizer steps, 65,536 ordinary transitions,
  22,044 service-label-eligible, `/usr/bin/time` 3:30.07 (210 s), prepublication 209.79 s, CPU
  216.2 s, peak RSS 616 MB; `learning_rates` read back `[3e-4, 3e-4]` at every one of the 16
  updates; all losses and gradient norms finite; L2 displacement 8.62 (relative 0.2253); training
  hard events `invalid_commit` 3,251, `separation_breach` 2; 34 training terminals; 0 training
  legal transfers.
- **LOW_LR (3e-5)**: `COMPLETE`, 16 updates, 512 steps, 65,536 transitions, 15,616 eligible,
  3:26.49 (206 s), prepublication 206.16 s, CPU 212.6 s, peak RSS 651 MB; `learning_rates`
  `[3e-5, 3e-5]` at every update; all finite; L2 displacement 1.91 (relative 0.0500); training
  hard events `invalid_commit` 2,234, `separation_breach` 2; 34 terminals; 0 legal transfers.
- Charge against the card: S 15.84 + 210.07 + 206.49 = **432.4 s** of the 3,600 s object cap;
  each arm plus S/2 ≈ 218 s of 1,800 s. No stop, no retry, no exception; both `.stderr` empty.
- Acceptance checks: both arms consumed the same shared bytes (norms equal), the four recorded
  resets equal the recomputed `_reset_row` rows (asserted in `run_arm`), the selected rate acted
  on both optimizer parameter groups at all sixteen updates in both arms (per-update read-back),
  configurations differ only in `arm` and `learning_rate`; the paired publication joined the
  twelve rows by coordinate key with sources `new:zero_update:raw`, `new:CONTROL:update16`,
  `new:LOW_LR:update16`. Valid, complete B/EXPLORE result.

## 2. Frozen rule applied verbatim and the observed readout

`Delta_LR = (1/4) Σ_r (J_LOW_LR,16,r − J_CONTROL,16,r)`; `D_CONTROL,new` and `D_LOW_LR,new`
against the seed-89 zero-update rows; scale ±24; seven-row reading.

| Condition (speed 4, slot 0, block 0) | `J_0` (raw init) | CONTROL | LOW_LR | LOW_LR − CONTROL | CONTROL − `J_0` | LOW_LR − `J_0` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| TARGET_VISUAL_MASK / K8 | 617 | 92 | 760 | **+668** | −525 | +143 |
| TARGET_VISUAL_MASK / K4_TO_K12 | 312 | 151 | 150 | −1 | −161 | −162 |
| TERRAIN_RELAY_MASK / K8 | 279 | 148 | 275 | +127 | −131 | −4 |
| TERRAIN_RELAY_MASK / K4_TO_K12 | 367 | 225 | 162 | −63 | −142 | −205 |
| **mean** | **393.75** | **154.0** | **336.75** | **Delta_LR = +182.75** | **D_CONTROL,new = −239.75** | **D_LOW_LR,new = −57.0** |

Companions. CONTROL's TARGET/K8 row **terminated natively at tick 684 (`separation_below_15`,
final separation 13.98) with one `separation_breach` and 26 `invalid_commit`; its 516 unexecuted
ticks count zero**, so its 92 is a terminated row, not a 1,200-tick service count. Every other
row of both arms and all reference rows ran the full 1,200 ticks. LOW_LR's four rows carry
23/4/0/11 `invalid_commit` and no other hard event; CONTROL's carry 26/64/89/50 and the one
separation breach. Energy per completed row is 288–292 k for LOW_LR and 288–289 k for CONTROL's
three complete rows (165 k for the terminated row); reference rows 258–281 k. **No legal
transfer occurred in any of the twelve evaluation episodes or in either arm's training** (the
source question stays unestimated; incumbent-only reading). Training curves: per-update service
30,846 (CONTROL) versus 26,412 (LOW_LR) summed over the 16 updates, both non-monotone with
similar shape (peaks at updates 1–2 and 10–11, troughs at 5–6 and 13–14); last four updates
840/583/794/762 versus 513/289/858/654; last loss 218.7 versus 244.8, last gradient norm 16.6
versus 29.4; LOW_LR's gradient norms are larger through updates 1–10 (up to 468) while its
displacement is 4.5 × smaller. Lower training loss or energy is not read as service.

**Reading.** Two rows of the table apply at once and are reported together:

- Row 2, relative signal with `D_LOW_LR,new ≤ −24`: `Delta_LR = +182.75 ≥ +24` with no adverse
  LOW_LR companion (fewer hard events, no termination, energy within the completed-row range),
  and `D_LOW_LR,new = −57.0 ≤ −24`, so the low-rate arm shows **only a smaller loss against
  CONTROL, not recovery of the initialization**; the reference's advantage (393.75 against
  336.75) is listed alongside.
- Row 4, mixed row signs: the four differences are +668, −1, +127, −63. The mean is dominated by
  one condition (TARGET/K8) where CONTROL terminated early; on TARGET/K4_TO_K12 the arms are
  equal, on TERRAIN/K8 LOW_LR retains its initialization while CONTROL loses 131, and on
  TERRAIN/K4_TO_K12 LOW_LR is 63 below CONTROL and 205 below the initialization. The card's
  row-4 clause therefore also applies: **no useful learning-rate advantage is established across
  the four conditions at this exposure**; the condition differences are kept; no automatic
  further rate reduction, longer training, better checkpoint or seed-adding follows.
- Row 6 (no evaluation legal transfer): the comparison stands as incumbent-only.

Stated plainly: on seed 89 the CONTROL learner again fell far below its own zero-update
controller (−239.75, the same description as seed 73's −245.75), and CONTROL's TERRAIN/K8 and
TARGET/K8 rows are its worst as on seed 73 (TERRAIN rows) with the addition of a separation
termination; the tenfold smaller rate moved the parameters 4.5 × less and left the controller
much nearer its initialization on two conditions, but it is still 57 mean ticks below it and
is worse than CONTROL on one condition. The witness's shared before/after loss repeated on this
instance for CONTROL; for LOW_LR the loss is smaller but present.

Not inferred: that 3e-5 is a good learning rate, that the loss is caused by the learning rate
(the object measured the total effect of the rate hyperparameter including AdamW's weight-decay
scaling; the parameter displacement shrank by 4.5 ×, not 10 ×), any general stability claim, any
relay or handover competence, any source or SHADOW-COPY conclusion, or equivalence between the
arms on the three non-terminated rows. Two rows favouring LOW_LR by more than the scale and one
row against it on one seed are not a seed-level claim; the zero-update reference remains an
ancillary measurement, not a tuned baseline.

## 3. What the observation adds to the direction's record

- Second training instance (seed 89) of the corrected-boundary CONTROL learner: final mean
  154.0 against its own initialization 393.75; with seed 73 (460.5 against 706.25) this is two
  instances of the same before/after description at 16 updates, with different absolute levels
  (seed 89's initialization serves far less than seed 73's, 393.75 versus 706.25: the raw
  zero-update controller's service is seed-dependent).
- One early native termination by separation breach in a CONTROL evaluation row on the corrected
  boundary (the first evaluation-row termination recorded in B02/B03/witness/B04); its row is
  kept as a terminated row.
- The learning-rate plumbing fact is now runtime-verified: the initializer-payload rate persisted
  through all sixteen construct-then-restore cycles in both arms.

## 4. Predictions scored

- **DM primary** (`D_CONTROL,new ≤ −24`, and `Delta_LR` inside ±24 or mixed across rows):
  the first half held clearly (−239.75); the second half held only in its "mixed rows" form
  (signs +, −, +, −) while the mean, +182.75, is far outside the band. Partly correct.
- **DM competing** (`Delta_LR ≥ +24` with `D_LOW_LR,new` inside ±24): the first half held, the
  second failed (−57.0). Wrong.
- **Node**: no numerical prediction; every row treated as a serious outcome. Nothing to score.
- **Owner**: not taken (unattended).

## 5. Decisions this intake produces (object tier, delegated)

Options: (a) accept the pair, the reference and the recorded resets as a valid complete
B/EXPLORE result read under rows 2, 4 and 6 of the card, and put the successor to
`em:dish:convergence` with this record; (b) buy a second independent paired seed of the same
comparison now (row 1 allows "one or two later seeds may be considered from the full record",
not pre-bought); (c) quarantine CONTROL's terminated row and rerun it. Recommendation: (a). A
second seed is a direction-tier selection under this card's wording and the mixed-row clause;
the terminated row is a valid native outcome (the card forbids row filtering by termination).
**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**

Successor question for the node (direction tier): after two training instances in which the
CONTROL learner ends far below its own zero-update controller, and one instance in which a
tenfold smaller AdamW rate leaves a smaller but still present loss with mixed rows, what is the
next object: a second independent seed of the LR pair; a different learner-side change (for
example a shorter or differently scheduled exposure, or an evaluation of intermediate
checkpoints on this seed); a return to the RETAIN/COPY/SHADOW source question on a controller
that does not degrade; or park. Packet `pro_packets/20260906_post_b04_convergence/`.

Records: brief `owner/briefs/degraded_incumbent_shadow_handover/2026-09-06_B04-low-LR-result.md`;
ledger rows; DIRECTION addendum; Portfolio row.
