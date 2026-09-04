# UCOPE-A-INSTRUMENTATION-TAIL-AGREEMENT-COMPETENCE-CHECK-R01 — card

- Direction: `ucope`
- Object id: `UCOPE-A-INSTRUMENTATION-TAIL-AGREEMENT-COMPETENCE-CHECK-R01`
- Evidence class: **A/RECON — instrumentation check.** Outcome-free, unit-scale, no training
  of any scientific arm, no learning-rate axis, no polarity. It consumes no B object and
  creates no retry budget for one.
- Written: 2026-09-02, **before** the check was run.
- Frozen by: this card. The tests named in §5 *are* the check.
- Reads: the frozen implementation under
  `experiments/candidates/ucope/competence_first_scout_r01/`, the ladder runner
  `scripts/run_ucope_exposure_ladder_rung1.py`, and — only for the confirmatory rows marked
  (D) below — the published rung-1/rung-2 evaluation rows and checkpoints, which are exactly
  the fields `evaluation.validate_policy_evaluation` and `ladder.validate_complete` already
  read. No published record or document of R01 is altered by this object.

## 1. Question

Do the tail-agreement and competence measurements measure what they claim, on **both** ladder
arms (`FT-XF-FLEX`, `FT-XF-BC`)? Two anomalies motivate the check:

- **(a)** `FT-XF-BC` recorded `minimum_tail_agreement` exactly `0.000000` in every row at both
  rungs (24 rows at rung 1, 30 rows at rung 2).
- **(b)** each `FT-XF-FLEX` policy's `minimum_tail_agreement` is constant across its four
  (rung 1) / five (rung 2) checkpoints.

An instrumentation defect and a genuine learning outcome can produce the same recorded
number. This object separates them.

## 2. What is measured

Four measurement groups, all through the *exact* code path the ladder runner uses
(`training.train_policy` calls `evaluation.evaluate_policy` on every checkpoint; the runner
calls `exposure_line` on the final checkpoints).

**M1 — tail agreement.** `evaluation.evaluate_policy` computes, per context,
`agreement = sum over count=0..6 of mass(count) * [selected_period == optimal_tail(K_EVAL, belief(count))]`
and records the **minimum over the eight contexts** as `minimum_tail_agreement`.
M1 drives synthetic tail policies whose true agreement is known in closed form through
`evaluate_policy` on both arms and compares.

**M2 — competence predicate components.** `competence_pass = all_finite and all_unique and
oracle_root_match and max_regret <= 1/50 and minimum_tail_agreement >= 19/20`
(`experiments/candidates/ucope/competence_first_scout_r01/evaluation.py:124`). M2 checks each
component separately — regret, tail agreement, the exact-oracle root vector — and checks that
the predicate can return `True` at all, on both arms, for a policy that is exactly optimal.

**M3 — per-coordinate Bellman displacement statistic.**
`scripts/run_ucope_exposure_ladder_rung1.py:372 exposure_line`. M3 establishes numerically
**which tensors it reads for `FT-XF-FLEX`**: whether the paired 64x64 residual is included in
`parameter_displacement_l2` / `initialisation_scale_l2`, and whether it is included in
`beta_displacement_l2` / `beta_max_abs_coordinate_move`; and what that does to the cross-arm
comparability of the R01 reading rule's `m = min` over all rows.

**M4 — the two anomalies.** M4 tests two structural explanations end to end:
for **(b)**, that for every `FT-*` arm `training.train_policy` runs the whole tail loop to
completion *before* the first root update and never touches the tail module again, so every
checkpoint of one policy necessarily carries a byte-identical tail model; for **(a)**, that
period 8 is never oracle-optimal at any belief, and that on the four `SEVERED` contexts the
belief is 1/2 for every count, so agreement there is 0 or 1 — hence a policy that never
selects period 4 records exactly `0.000000`.

## 3. Levels used for M1, and one honest substitution

The true agreement levels reachable on the frozen host are the **exactly computable
rationals** below. Each is computed in the check by an independent reference implementation
written from `oracle.py`'s definitions in `Fraction` arithmetic — not by calling
`audit_policy_choices` or `evaluate_policy`.

| synthetic tail policy | `SEVERED` | `LINKED` p=13/20 | `LINKED` p=17/20 |
| --- | --- | --- | --- |
| always period 8 | 0 | 0 | 0 |
| always period 2 | 0 | 48928580/128000000 = 0.382255 | 61346980/128000000 = 0.479273 |
| always period 6 | 0 | 48928580/128000000 = 0.382255 | 61346980/128000000 = 0.479273 |
| always period 4 | 1 | 30142840/128000000 = 0.235491 | 5306040/128000000 = 0.041453 |
| exact-oracle beta | 1 | 1 | 1 |

The task asked for a level of exactly **1/2**. It is not attainable on this host: the seven
count masses are binomial and no subset of them sums to 1/2. The check proves that by
exhaustive enumeration of all 128 subsets for each of the four `LINKED` contexts rather than
asserting it. The substitution is `0.479273` — the closest attainable value — plus the two
further intermediates above. This is a deliberate, stated deviation, recorded again in the
result document.

## 4. Pass condition

The check **passes** if and only if all of:

1. **M1** For all five synthetic tail policies, on both arms, over all eight contexts, the
   agreement `evaluate_policy` records equals the independent reference exactly
   (|delta| <= 1e-12), including the two extreme levels 0 and 1.
2. **M2** With exactly-optimal root **and** tail coefficients, both arms record
   `competence_pass = True`, `max_regret = 0.0`, `minimum_tail_agreement = 1.0` and
   `oracle_root_match = True`; for every synthetic policy all four reported components equal
   the independent reference; and the exact (`Fraction`) predicate in `evaluate_policy`
   agrees with the float predicate in `validate_policy_evaluation`.
3. **M3** For controlled parameter displacements every field of `exposure_line` equals the
   hand-computed value; the residual is demonstrably inside the aggregate statistic and
   demonstrably outside the beta statistic; and the arm-dependent initialisation scale is
   quantified.
4. **M4** Both structural explanations are demonstrated, not asserted: FT checkpoints carry
   an identical tail model within a policy while the MT arm's do not (the sensitivity
   control); and recomputing agreement from the published `tail_periods` with the independent
   reference reproduces the published `minimum_tail_agreement` on every row of both rungs (D).

## 5. Where the check lives

`tests/experiments/candidates/ucope/test_instrumentation_check_r01.py`, run with an explicit
`--basetemp`. Rows marked (D) skip if the untracked run directories are absent; every other
row is hermetic.

## 6. What a fail means

- **A fail in M1 or M2** means `minimum_tail_agreement`, `max_regret`, `oracle_root_match` or
  `competence_pass` do not mean what the R01 result documents say they mean. The R01 rung-1
  and rung-2 result documents would then receive a dated note naming the affected field; the
  ladder's competence observations would be evidence about the instrument rather than about
  the learners; and the runner defect would be fixed, with its own test, before any R02
  object is registered. Because competence is recorded and never gating, no published
  *decision* would change — the recorded observation would.
- **A fail in M3** means the exposure line — which **is** a launch condition under §11.4 —
  misstates displacement. That would put the R01 reading-rule outcome (`R1-C` at both rungs)
  in question, and would be reported as a defect in a gating item.
- **A fail in M4** means the anomalies have some other cause and this check has not explained
  them; the result document then says so and names what is still unexplained.
- **A pass** means the recorded numbers are correct measurements of the policies that were
  trained, and that anomalies (a) and (b) are properties of those policies and of the frozen
  training schedule, not of the instrument. It does **not** make `FT-XF-BC` competent, and it
  licences no claim about the learners beyond what R01 already records.

## 7. Post-run note (added 2026-09-02, after the check ran)

The card body above is the pre-run artifact and is left unedited. Two of its statements were
corrected by the check itself and are recorded in
`UCOPE_INSTRUMENTATION_CHECK_R01_RESULT_20260902.md` section 5: (i) the closest *attainable
recorded minimum* to 1/2 is `0.520727`, not `0.479273` — the latter is attainable per context
but never as a minimum; the check uses a belief-threshold policy to reach it. (ii) The
explanation offered in section 2 for anomaly (a) via convexity of the learned BC tail is false:
the published second differences are negative. The check replaced it with a coefficient
recovery from the recorded scores, which reaches the same conclusion for a verified reason.
