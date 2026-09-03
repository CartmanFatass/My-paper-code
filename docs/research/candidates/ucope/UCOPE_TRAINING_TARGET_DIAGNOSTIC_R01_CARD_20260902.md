# UCOPE-A-TRAINING-TARGET-DIAGNOSTIC-R01 — card

- Direction: `ucope`
- Object id: `UCOPE-A-TRAINING-TARGET-DIAGNOSTIC-R01`
- Evidence class: **A/RECON — diagnostic.** Outcome-free, unit-scale. No scientific arm is trained
  at ladder scale, no polarity is produced, no B object is consumed, and no published record is
  altered.
- Written: 2026-09-02. **Not run.** It awaits the owner's prediction (section 7) before launch.
- Reads: the frozen implementation under
  `experiments/candidates/ucope/competence_first_scout_r01/`, freshly generated populations from
  the same frozen host, and the final tail/root parameters in the published R02 checkpoints — which
  is what `ladder.validate_complete` already reads.

## 1. Question

The exposure ladder is closed. Both R02 rungs returned `R2-D NEITHER_ARM_MOVED`, and across a
ten-fold change of learning rate traded against a ten-fold change of update count — `steps x lr`
equal to `0.96` at both rungs — each arm's least-moving coordinate moved by **less than one percent**
between the two schedules (`FT-XF-FLEX` 0.108116 → 0.107457; `FT-XF-BC` 0.250245 → 0.249392, set by
the same policy and stage at both rungs).

At the same time, the instrumentation check
`UCOPE-A-INSTRUMENTATION-TAIL-AGREEMENT-COMPETENCE-CHECK-R01` established that the frozen 5-term
tail basis represents the true expected tail return **exactly**, at
`beta* = (0.31, 0.60, 1.35, -1.08, -0.891)`, and that a policy carrying those coefficients is
recorded as fully competent on both arms. It also recovered each published `FT-XF-BC` tail model from
its own recorded scores and found `max |beta - beta*| > 0.5` for every policy.

**So: why does the learned `beta` settle far from an optimum its own basis can represent exactly, and
why does an order-of-magnitude change of schedule not move it?**

## 2. Candidate mechanisms, written out from the code

**M1 — the objective's own fixed point is not `beta*`.**
The tail head is fit by MSE against `row.tail_return` (`host.py:150`), a realized return, with
`row.belief_short` the exact posterior for the displayed count (`host.py:148`–`149`).
`host.py:199 expected_tail_mean` shows that `E[tail_return | belief, period]` equals the oracle's
`expected_tail`, which lies exactly in the span of `(1, b, k, b*k, k^2)`. The *population* optimum
should therefore be `beta*`. Whether the **empirical** optimum on the actual finite design is
`beta*` is not established: it depends on the design's rank and on the realized belief/period
support.

**M2 — optimization shortfall on an ill-conditioned design.**
`training.py:_step` runs AdamW at a fixed learning rate with `clip_grad_norm_(..., 1.0)`, and
`training.py:_cyclic_batch` takes each batch as a **contiguous cyclic window** of a row list sorted
by `(episode_index, context_id)` — never shuffled, and with the behaviour period a deterministic
function of the episode index (`host.py:49 behavior_stratum`, offset `index % 10`). The tail Gram
over `(1, b, k, b*k, k^2)` has strongly correlated columns; the whitening discriminator R01 measured
condition numbers of `7.2e2` (tail) and `5.0e3` (root) on this design family. A slow eigendirection
then needs roughly `kappa` times the travel of a fast one, while the per-coordinate travel budget is
`steps x lr = 0.48` at the tail stage of **both** rungs. On this account the learner is converging
correctly but far too slowly along one direction, and the two rungs are the same budget in disguise
— which is exactly the invariance the ladder observed.

**M3 — the root's frozen target package.**
For every `FT-*` arm the tail is frozen and `frozen_targets = _root_targets(root_rows, tail)` is
materialised once, before the root loop (`training.py:228`–`231`). In `_root_targets`, a PROBE row's
target is `probe_primitive + max over K_TRAIN of Q_tail(k, belief)` — the **odd** training periods
`{1,3,5,7,9}` — while the competence predicate `C_even` ranks the tail over the **even** periods
`K_eval = {2,4,6,8}`. So the root's own fixed point is defined by (a) the *learned* tail rather than
the true one, and (b) a maximisation over a different period set from the one it is judged on.

Part (b) is closed form, and **was computed while writing this card** so that the reading rule is
fixed with it disclosed: substituting `max over K_TRAIN` for `max over K_EVAL` in the *true* value
shifts the informed value by at most `0.003713`, and preserves the sign of net acquisition at all
four `LINKED` contexts — at the target context `LINKED-p17_20-c9_100` the implied net is `+0.025151`
against the oracle's `+0.021437`; at `LINKED-p13_20-c9_100` it is `-0.023182` against `-0.020079`.
The odd/even substitution alone therefore does **not** make the oracle root vector unreachable, and
if anything widens the target context's margin. What remains untested in M3 is part (a): how much
tail error the root inherits, given that all twelve published policies chose `IMMEDIATE` in all
eight contexts while the oracle chooses `PROBE` at exactly one.

**M4 — fold coupling and training order.**
`training.py:_canonical_rows` trains the tail on the **complementary** fold's rows
(`wanted = 1 - fold`) and only on `behavior_action == "PROBE"` rows, and the root on its own fold.
The tail is trained to completion first and never updated again, so the root is fit to targets built
by a model that never saw the root's data and cannot be corrected by it. This is a small effect if
the folds are exchangeable, and it is cheap to size.

## 3. Differentiating measurements

All operate on freshly generated populations from the frozen host and on parameters read from the
published checkpoints. None trains a scientific arm; none produces polarity.

**X1 — the tail objective's exact optimum and the learner's stationarity.** *(linear algebra, no
learner; ~2 min.)* Assemble the exact tail design from one seed's population, solve the normal
equations for `beta_tail_star`, and report:
`d_objective = max |beta_tail_star - beta*|`; the Gram condition number `kappa_tail` and its smallest
eigenvalue; and the infinity-norm gradient of the frozen tail loss evaluated at `beta*` (`g_star`)
and at each published final tail `beta` (`g_learned`).
→ Separates **M1** from **M2**: if `beta_tail_star` *is* `beta*`, the objective is right and the
learner stopped short; if not, the learner is converging correctly to a different place.

**X2 — the root target package, three ways.** *(linear algebra; ~2 min.)* Rebuild the root's frozen
targets from (a) the exact oracle tail, (b) `beta_tail_star`, and (c) each published tail; solve the
root normal equations for each; read off the implied root action vector and whether it equals the
oracle's `{7 x IMMEDIATE, PROBE at LINKED-p17_20-c9_100}`.
→ Separates **M3(a)** — the root inherits tail error — from a root-side defect: if (a) and (b)
produce the oracle vector and (c) does not, the root is fine and the tail is the whole story.

**X3 — optimization versus objective.** *(unit-scale; ~5–10 min; run only if X1 shows `d_objective`
small and `g_learned` large.)* From one published policy's tail parameters, continue the **same**
`_step` loop with the same optimizer for ten times the rung-2 tail budget, and separately take the
exact normal-equation solve; report where each lands relative to `beta_tail_star`.
→ Distinguishes "needs more of the same steps" from "will not get there in this parameterisation and
schedule at any practical budget".

**X4 — fold coupling.** *(linear algebra; ~1 min.)* Recompute `beta_tail_star` on the tail's own fold
and on the root's fold and compare.
→ Sizes **M4**; expected to be small, and worth knowing before it is invoked as an explanation.

## 4. Reading rule — written before any of these are run

Thresholds fixed here. `epsilon = 0.10` on max-absolute coefficient distance: `beta*`'s coordinates
range from `0.31` to `1.35`, and the published learners sit more than `0.5` away, so `0.10` is well
inside "essentially converged" and well below the observed gap. `g` ratio threshold `10`.

Branches, evaluated in this order; exactly one applies.

- **D4 — `TARGET_PACKAGE_CEILING`.** X2(a) — the root re-solve with the **exact oracle tail** — does
  not reproduce the oracle root vector. Reading: the frozen target package cannot express the
  oracle's root decision at all, and no amount of learning inside it can. Next: a named object that
  changes the target package, not the learner.
- **D1 — `OBJECTIVE_FIXED_POINT_DIFFERS`.** `d_objective > epsilon`. Reading: the frozen tail
  objective's own optimum is not `beta*`; the learner is converging correctly to the wrong place, and
  every exposure result to date is consistent with a correct optimizer on a mis-specified objective.
  Next: an object that changes the objective or the training support, never the exposure.
- **D2 — `OPTIMIZATION_SHORTFALL`.** `d_objective <= epsilon`, `max |beta_published - beta_tail_star|
  > epsilon`, and `g_learned > 10 * g_star`. Reading: the objective's optimum is `beta*` and the
  optimizer stops far short of stationarity. Report `kappa_tail`. Next: a conditioning or solver
  object — which is what the whitening discriminator was for — rather than more steps. X3 then says
  whether more of the same steps would ever suffice.
- **D3 — `TAIL_CONVERGED_ROOT_INHERITS`.** `d_objective <= epsilon` and
  `max |beta_published - beta_tail_star| <= epsilon` (the tail is at its own optimum), while X2(c)
  fails to give the oracle root vector and X2(a)/(b) succeed. Reading: the tail is doing its job and
  the failure is entirely the root's inherited target error. Next: an object on the root target
  package and the tail-before-root freeze.
- **D5 — `NONE_OF_THESE`.** Any other combination. Reading: the four mechanisms as written do not
  account for the observation; the result document says so, reports every number, and names what is
  still unexplained. No new object is proposed on the strength of a `D5`.

Descriptive and deciding nothing: `kappa_root`, the per-fold `beta_tail_star` difference from X4, the
`K_TRAIN` versus `K_EVAL` informed-value gaps already quoted in section 2, and any per-seed spread.

## 5. Budget

Under 20 minutes of compute in total: X1, X2 and X4 are linear algebra on already-generated
populations (under 10 minutes together, including population generation); X3 is a single unit-scale
optimizer loop on one policy's tail rows (under 10 minutes) and runs only if X1 calls for it. One
resource preflight immediately before the run, as for every result-bearing invocation. No new
scientific arm, no ladder-scale training, no new checkpoints under any published run root.

## 6. What each outcome would mean for the direction

- **D4** would retire the current target package as the direction's frozen object: the ladder, the
  discriminator and the competence criterion would all have been measuring a learner that could not
  have succeeded. That is a redesign, and an outcome-informed one, so it would be a new object.
- **D1** would move the direction's binding constraint from *exposure* and *conditioning* to
  *objective specification*, and would explain the ladder's schedule-invariance directly: a correct
  optimizer on a fixed wrong target does not care how the budget is split.
- **D2** would revive the conditioning question that the quarantined whitening discriminator R01 was
  built to ask, and would give it a concrete number (`kappa_tail`) and a concrete failure mode to
  target. It would also make the ladder's `R2-D` readings intelligible rather than merely
  uninformative.
- **D3** would localise the failure to the root, and would make the tail-before-root freeze — not the
  representation, not the exposure — the direction's next object.
- **D5** would leave the direction with an unexplained observation, which is a legitimate and
  reportable outcome, and would argue against spending further budget on the ladder family until a
  better hypothesis exists.

None of these outcomes establishes acquisition polarity, COUNT/RAW polarity, stable superiority, a
seed-population claim, or anything about variable `k`, variable `N`, MARL/UAV, transfer, safety,
deployment or real-world QoS. This is a diagnostic on one frozen eight-context host.

## 7. Prediction requested from the owner

Please pick one before the run, so the diagnostic is a test rather than a fishing trip.

- **Option M1 — the objective's fixed point.** The frozen tail MSE objective's own optimum on the
  realized design is not `beta*`, so the learner is converging correctly to a different vector and no
  schedule change can help.
- **Option M2 — optimization shortfall.** The optimum is `beta*`, but AdamW at a clipped gradient on
  a Gram matrix with condition number in the hundreds cannot traverse the slow direction inside a
  `steps x lr = 0.48` per-coordinate budget, which is identical at both rungs and explains the
  schedule-invariance.
- **Option M3 — the root's frozen target package.** The tail is close to fine and the root fails
  because its once-materialised targets are built from the learned tail (and maximised over the odd
  training periods), so the root inherits and amplifies tail error it can never correct.
- **Option M4 — fold coupling and order.** The tail is trained on the complementary fold's PROBE rows
  and frozen before the root ever runs, so the root is fit against a model that never saw its data.
- **Option "none of these".** The mechanisms as written do not cover it, and the diagnostic should
  report `D5` rather than force a fit.
