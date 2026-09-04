# UCOPE-B-EXPLORE-THREE-WITNESS-HINGE-R01 — science card

- Direction: `ucope`
- Object id: `UCOPE-B-EXPLORE-THREE-WITNESS-HINGE-R01`
- Evidence class: **B/EXPLORE**
- Frozen: 2026-09-04, before this object's implementation, test, cost projection, or result run
- Direction authority: owner decision D.25 on 2026-09-03 queued the three-witness hinge as the next
  UCOPE object; this card fixes its object-tier wording under the unattended delegation.

## 1. Question and claim ceiling

On the already observed draw, does covering all three exact training-support witnesses of the
three held-out decision directions remove the two tail-agreement residuals that a one-witness hinge
left, beyond what can be obtained merely by tripling the total hinge dose?

The maximum claim is a preliminary mechanism observation on six policies of the frozen finite
renewal host: an oracle-signed three-witness training loss did or did not improve held-out tail
decisions over a dose-matched one-witness null on these rows. It is not a stable-superiority,
seed-population, deployable-objective, paid-acquisition, COUNT/RAW, generic UCOPE, variable-`k`,
variable-`N`, MARL/UAV, transfer, safety, flight, energy, or real-world QoS claim.

## 2. Prior observation and live explanations

`UCOPE-B-EXPLORE-TAIL-MARGIN-REMEDIES-R01` observed branch `M-B`. Its `(5,9)` training-support
witness made the corresponding held-out `(6,8)` count-0 gap positive in 6 of 6 policies, but its two
remaining agreement failures landed exactly on the uncovered `(2,4)` and `(4,6)` directions. Their
exact training-support witnesses are `(1,5)` and `(3,7)`.

The treatment explanation is **direction coverage**: all three held-out directions must have a
training-support margin term. The strongest same-data, same-information live null is **hinge dose**:
three units of penalty on the already used `(5,9)` direction may be enough without covering the
other two. Other live explanations are draw-specific exact-objective error, optimizer variation,
root-target movement caused by tail bias, and three-seed heterogeneity. The paired exact solve is
reported as a reference, not as an empirical comparator and not as an arm.

## 3. Frozen population, information, and common learner

- Seeds: `ucope-scout-r01-b1-fresh-00`, `-01`, `-02`; folds `0,1`, group-disjoint as in the accepted
  UCOPE chain. The owner's prediction slot is not a seed slot.
- Draw: the deterministic counter-addressed rows at offset `2,000,000`, with 40,960 episodes per
  context and 81,920 tail rows per policy. Both arms share exactly the same rows. This reuse is
  deliberate: B/EXPLORE is adaptive, and this object asks whether the named intervention removes the
  already localized residual on those rows. No previous runtime artifact is read.
- Training support: `K_train={1,3,5,7,9}`. Evaluation support: `K_eval={2,4,6,8}`. No even period may
  enter a hinge construction, training design, target, selection, or tuning operation.
- Common learner: frozen `FT-XF-BC`, FP32 AdamW, learning rate `0.003`, batch 256, whitened tail from
  training rows only, 1,600 tail updates, and the root stage held at `WHITENED-ROOT-10X` for 3,200
  updates. Initial parameters, cyclic batches, clipping, root target construction, evaluator, and
  sampled diagnostic are paired arm-by-arm and unchanged.
- Execution: one process, one intra-op thread, deterministic algorithms enabled. The live arm order
  is fixed as comparator then treatment for every seed/fold; no result is inspected between arms.

Reusing the draw and frozen oracle sign makes this the smallest causal mechanism check on the
observed residual. It also lowers the claim ceiling: it does not test a fresh draw or an objective
that could be deployed without oracle knowledge.

## 4. Treatment and strongest comparator

For a training belief `b` and witness pair `(a,c)`, define

```text
d_(a,c)(b) = z(b,a) - z(b,c)
s_(a,c)(b) = sign(d_(a,c)(b) . beta*)
L_(a,c)    = mean_rows max(0, 0.024022 - s_(a,c)(b) d_(a,c)(b) . beta)
```

`beta*` is the frozen oracle tail vector already recorded by the direction. The sign is computed
before optimization from the pair's two **odd training-support** basis rows. It is never inferred
from a learned policy or from an even held-out period. None of the enumerated training beliefs has a
zero oracle witness gap. The signed definition is necessary: the preferred side of `(1,5)` and
`(3,7)` changes with belief, while `(5,9)` is positive throughout the frozen panel.

The two live arms are:

1. **`DOSE-MATCHED-SINGLE`** — `MSE + 3 * L_(5,9)`. This is the strongest competent null: same
   data, oracle information, optimizer exposure, and maximum hinge coefficient as the treatment,
   with all dose concentrated on the direction already constrained by the accepted predecessor.
2. **`THREE-WITNESS`** — `MSE + L_(1,5) + L_(3,7) + L_(5,9)`. Each witness receives the predecessor's
   frozen weight `1.0`; the three-term sum, rather than an average, dose-matches the comparator.

The margin `0.024022`, the three weights, and the signs are not tuned. The historical one-witness
weight-1 result is a recorded baseline only and is not silently promoted into a paired comparator.

## 5. Trace from event to native consequence

The environment event is a forced diagnostic PROBE. The acting root policy owns the buy/no-buy
choice; the tail policy owns the effective-period choice after the belief update. It observes the
same belief and odd-period training rows in both arms. The only changed credit path is the signed
hinge gradient on the tail coefficients. Those coefficients build the frozen root targets, so any
root-action movement is a native downstream consequence and is measured, not attributed away.
The native consequence is held-out even-period tail agreement, root action, regret, and paid-probe
value under the existing exact evaluator. No membership, slot-identity, join/leave, censoring,
replacement, or semi-Markov-time question is part of this fixed-population host.

## 6. Observables and estimand

The primary observable per arm-policy is
`min_forced_PROBE_tail_agreement` on `K_eval`, with pass threshold `>=19/20`. Let `P_T` and `P_C` be
the sets of passing seed/fold policies for `THREE-WITNESS` and `DOSE-MATCHED-SINGLE`; let `N_T` and
`N_C` be their sizes. The primary paired estimand is `N_T-N_C`, qualified by whether
`P_C subseteq P_T`; per-policy agreement differences are reported without aggregation claims.

Also required:

- the full frozen `C_even` components and counts, root-action vector, maximum regret, and `C_root`;
- signed learned and oracle gaps for `(2,4)`, `(4,6)`, and `(6,8)` at every evaluation belief;
- per-witness hinge activation and final signed margin, training MSE, `d_learned_tail`,
  `d_learned_root`, and `d_objective`;
- exact-reference agreement and `C_even` on the same rows;
- nonzero environment-transition, update, and evaluation counts; launch SHA; wall time and peak RSS
  when measured; and one machine-generated exposure line.

Resource telemetry may be missing and then is marked `resources_unmeasured`. Missing learner-side
measurements, policies, counts, or required gaps quarantine the attempt and produce no scientific
branch.

## 7. Frozen result rule

Apply the following branches in order after all six policies and both arms are complete:

1. **`TW-A — COVERAGE_CLOSES_COMPETENCE`.** `N_T=6`, `N_C<6`, and `THREE-WITNESS` has `C_even=6/6`.
   Reading: witness coverage, beyond equal hinge dose, closes the observed tail and complete
   competence predicates on this panel.
2. **`TW-B — COVERAGE_CLOSES_TAIL_ONLY`.** `N_T=6`, `N_C<6`, and `THREE-WITNESS` has `C_even<6/6`.
   Reading: witness coverage closes the tail obstruction beyond dose, while root/value-bias or
   another non-tail component remains.
3. **`TW-C — DOSE_SUFFICIENT`.** `N_T=6` and `N_C=6`.
   Reading: the tail closes, but direction coverage is not identified because concentrating the
   same total dose on one witness also closes it.
4. **`TW-D — COVERAGE_PARTIAL`.** `N_T>N_C`, `N_T<6`, and `P_C subseteq P_T`.
   Reading: coverage adds held-out decisions without breaking a comparator pass, but the dose is
   insufficient or another tail residual survives.
5. **`TW-E — NO_COVERAGE_GAIN`.** `P_T=P_C` and `N_T<6`.
   Reading: adding the two missing witness directions changes no agreement decision over the
   dose-matched null on this panel.
6. **`TW-F — TRADEOFF_OR_UNCLEAR`.** Every other complete combination, including loss of a
   comparator pass or different pass sets at equal counts. Report the exact movements and infer no
   clean coverage effect.

Only `TW-A` and `TW-B` support the narrow statement that coverage, rather than dose alone, closes
the observed tail residual. No branch changes either direction lock or Portfolio state.

## 8. Predictions on record

- **DM:** `TW-B`. Predicted `N_T=6`, `N_C=4`, with `THREE-WITNESS C_even` at 4 or 5 of 6. Rationale:
  the predecessor's two tail failures land exactly on the two newly covered directions, while its
  separate seed-02/fold-1 root refusal shows that a tail closure need not close the full predicate.
- **Owner:** `not taken (unattended)`.

## 9. Budget, cost law, exposure, and stop rule

This is a two-arm paired sweep. Each arm has six policies, 983,040 shared generated episodes,
9,600 tail updates, 19,200 root updates, 2,457,600 tail example exposures, and 4,915,200 root
example exposures when the full shared generation is conservatively charged to each arm.

The runner's prospective cost law must be emitted by its non-result `project-cost` command:

```text
projected_arm_seconds = 3 * 61.827
                      * max(environment_episodes / 983040,
                            optimizer_updates / 28800,
                            policies / 6)
```

`61.827 s` is the measured nearest-neighbour paid-acquisition path with the same rows and exactly
one learner arm at these tail/root update counts; factor 3 is the fixed machine-load and
implementation allowance. The frozen projection is therefore **185.481 s per arm**. The
machine-time cap is **600 s per arm**; it applies independently, and neither arm launches if its
machine-generated projection exceeds it.

Nominal clipped-gradient path budgets are `1600*0.003=4.8` per tail coordinate and
`3200*0.003=9.6` per root coordinate. Deterministic initial maximum-coordinate scales span
`0.719230..0.983295` for the tail and `0.591251..0.863498` for the root, so nominal budget/initial
scale spans `4.88..6.67` and `11.12..16.24`, respectively. The result must replace this prospective
line with actual per-policy raw-coordinate displacement and initialisation-scale ratios; zero
movement refuses the B result.

There is one result-bearing invocation. It stops after one complete `summary.json`, or immediately
on a §4 integrity breach, failed fresh 4 GiB physical/effective memory admission, nonzero-count
failure, nonfinite learner event, or missing required learner measurement. There is no scientific
rerun, early stopping, arm dropping, post-result tuning, or replacement seed. A reproduced
implementation defect may be repaired outcome-blind at a new SHA as a fresh attempt; it has no
polarity and does not consume this B object.

## 10. Launch contract and engineering scope

Before the result invocation: implement the smallest disposable research runner, run its one smoke
and rule test set once after editing, emit and record the cost projection, commit and push the card,
runner and tests, run that same focused test set once before launch, then take one fresh central
`admit-memory` receipt immediately before the detached invocation. The summary lives under
`temp/directions/ucope/exp/three_witness_hinge_r01_20260904/` and records the launch SHA and exact
argv. The run is detached from the agent process.

Protected semantics: the counter-addressed rows, folds, FP32 learner, AdamW state/update order,
whitening, initialization, cyclic batches, clipping, root targets, evaluation, RNG, numerical
precision, and side effects outside the named scratch root. Technical success can establish only
that the assignment ran and its measurements are complete; it cannot establish mechanism value.

**Engineering-scope §4 line: this object needs none of the prohibited machinery.** In particular it
adds no scheduler/queue, resume/retry, checkpoint orchestration, tamper evidence, provenance guard,
incident tree, schema validator, registry, telemetry beyond wall/peak RSS, compatibility shim, or
repeated smoke loop. New research code stays below 2,000 lines, the runner below 600, orchestration
below 30 percent, and the tests are one under-60-second toy smoke plus rule/hinge-semantics tests.

## 11. Object-tier design decision

Options considered before implementation:

- (a) add the two missing witness terms and compare only with the historical one-witness result;
- (b) use oracle-signed terms at every training belief and run a live `3x` dose-matched one-witness
  comparator on the same rows;
- (c) move immediately to a fresh draw and accept draw variation in the first mechanism check.

Recommendation: **(b)**. It preserves the exact training/held-out boundary, handles the genuine
belief-dependent sign reversal, and distinguishes witness coverage from total regularizer dose.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (b).** This is reversible object
wording inside the owner-selected queued object; it changes no direction or Portfolio state.

## 12. Non-goals

Do not alter the paid-acquisition or COUNT/RAW locks, diagnose the single paid-acquisition root
refusal, introduce a fresh draw, tune margin/weight, add learner capacity or budget, change the root
treatment, evaluate another function class, retrofit historical runners, or infer a population or
deployment claim. A valid negative closes at most this oracle-signed three-witness intervention on
the observed draw.
