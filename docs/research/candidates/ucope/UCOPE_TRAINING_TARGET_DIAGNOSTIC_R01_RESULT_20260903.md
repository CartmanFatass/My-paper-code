# UCOPE-A-TRAINING-TARGET-DIAGNOSTIC-R01 — result (2026-09-03)

- Direction: `ucope`
- Object id: `UCOPE-A-TRAINING-TARGET-DIAGNOSTIC-R01`
- Evidence class: **A/RECON — diagnostic.** Outcome-free; no scientific arm trained at ladder
  scale, no polarity, no B object consumed, no published record altered.
- Card (frozen 2026-09-02, before any measurement): `UCOPE_TRAINING_TARGET_DIAGNOSTIC_R01_CARD_20260902.md`
- Prediction on record (owner, 2026-09-02, compliance note D.10; card section 8): **M2.**
- Runner: `scripts/run_ucope_training_target_diagnostic_r01.py`
- Unit checks: `tests/experiments/candidates/ucope/test_training_target_diagnostic_r01.py` — `13 passed in 0.37s`
- Record (gitignored): `temp/directions/ucope/exp/training_target_diagnostic_r01_20260903/diagnostic.json`

## 0. Headline

**Branch reached: `D1 — OBJECTIVE_FIXED_POINT_DIFFERS`**, on `max d_objective = 0.222610 > epsilon = 0.10`,
with `D4` ruled out first (all six oracle-tail root re-solves reproduce the oracle root vector).

**The prediction on record is contradicted by the rule's own wording.** The prediction was M2 —
"the objective's own optimum is still beta* and the learners do not reach it". The rule assigns
`D1`, whose registered reading is "the frozen tail objective's own optimum is **not** `beta*`".

The picture underneath is mixed and section 6 says so in full: pooled over all six folds the
objective's optimum **is** statistically `beta*`, so the objective is not mis-specified and the
`D1` condition is met by per-policy sampling error; and separately, the learners are an order of
magnitude further from their own objective's optimum than that error — which is the phenomenon the
prediction described. The frozen rule cannot express that combination, and that is itself a finding.

## 1. Launch conditions and topology

| Fact | Value |
| --- | --- |
| Launch commit sha (HEAD at launch) | `d2b4c25420e958b1c8ffcbce1f99989172ee3f5b` |
| Resource admission (before any measurement) | `available_physical_bytes = effective_available_bytes = 12,285,509,632` (11.44 GiB), `passed: true`, floor `4,294,967,296` |
| Preflight receipt | `temp/directions/ucope/exp/training_target_diagnostic_r01_20260903/preflight.json` |
| Interpreter | `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`, Python 3.10.20, torch 2.7.0+cpu, CPU |
| Topology | `torch_intraop_threads = 4`, `torch_interop_threads = 1`, `deterministic_algorithms = true` |
| Wall / CPU | `28.397 s` / `35.312 s` |
| Published run read | `temp/directions/ucope/exp/exposure_ladder_r02_rung2_20260902/complete` (final checkpoints only) |
| Populations | freshly generated from the frozen host, three B1 seeds, 5,120 episodes per context |

## 2. X1 — the tail objective's exact optimum and the learner's stationarity

Tail design per policy: 10,240 PROBE rows of the complementary fold, basis `(1, b, k, b*k, k^2)`,
target `row.tail_return`. Solved exactly in float64. `beta* = (0.31, 0.60, 1.35, -1.08, -0.891)`.

| Seed | Fold | `beta_tail_star` | `d_objective` | `kappa_tail` | `lambda_min` | `g_star` | `g` at optimum |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `00` | 0 | (0.214489, 0.630125, 1.566774, −1.168852, −0.996194) | **0.216774** | 716.655 | 2.6574e-03 | 5.5463e-02 | 5.57e-15 |
| `00` | 1 | (0.277044, 0.625734, 1.518532, −1.140558, −1.010805) | 0.168532 | 714.822 | 2.6528e-03 | 1.5842e-02 | 4.86e-15 |
| `01` | 0 | (0.253281, 0.639127, 1.530732, −1.143080, −1.013606) | 0.180732 | 717.261 | 2.6642e-03 | 8.5812e-03 | 4.85e-15 |
| `01` | 1 | (0.370108, 0.566081, 1.304708, −1.133316, −0.899669) | 0.060108 | 714.483 | 2.6585e-03 | 1.8260e-02 | 2.99e-15 |
| `02` | 0 | (0.396574, 0.513318, 1.177574, −0.963684, −0.839783) | 0.172426 | 736.646 | 2.6056e-03 | 1.1309e-02 | 2.86e-15 |
| `02` | 1 | (0.322147, 0.611400, 1.127390, −1.056341, −0.692131) | **0.222610** | 721.144 | 2.6278e-03 | 3.6744e-02 | 4.81e-15 |

Five of six exceed `epsilon = 0.10`; the maximum is `0.222610`. The Gram condition number is
`714.5`–`736.6` throughout, matching the `7.2e2` the whitening discriminator measured on the same
design family. The gradient at the solved optimum is `~5e-15`, confirming the solver.

Published final tail parameters, from the R02 rung-2 checkpoints:

| Seed | Fold | Arm | `d_learned` (to `beta_tail_star`) | `d` to `beta*` | `g_learned` | `g_learned / g_star` |
| --- | --- | --- | --- | --- | --- | --- |
| `00` | 0 | `FT-XF-BC` | 1.953026 | 1.736252 | 1.0202e-01 | 1.84 |
| `00` | 1 | `FT-XF-BC` | 1.725694 | 1.605889 | 3.3233e-01 | 20.98 |
| `01` | 0 | `FT-XF-BC` | **2.380056** | 2.316976 | 9.2487e-01 | **107.78** |
| `01` | 1 | `FT-XF-BC` | 1.950627 | 1.995920 | 6.9173e-02 | 3.79 |
| `02` | 0 | `FT-XF-BC` | 1.623135 | 1.795561 | 1.8653e-01 | 16.49 |
| `02` | 1 | `FT-XF-BC` | 0.951506 | 1.174116 | 8.2613e-02 | 2.25 |
| `00` | 0 | `FT-XF-FLEX` | 2.011380 | 1.922528 | 1.6987e-01 | 3.06 |
| `00` | 1 | `FT-XF-FLEX` | 1.991749 | 1.931191 | 2.5809e-01 | 16.29 |
| `01` | 0 | `FT-XF-FLEX` | 1.992068 | 1.928989 | 2.3665e+00 | 275.78 |
| `01` | 1 | `FT-XF-FLEX` | 1.372013 | 1.417305 | 1.4474e+00 | 79.26 |
| `02` | 0 | `FT-XF-FLEX` | 1.456057 | 1.507274 | 3.3378e+00 | 295.14 |
| `02` | 1 | `FT-XF-FLEX` | 0.966377 | 0.954977 | 1.4950e+00 | 40.69 |

`FT-XF-FLEX` rows are **descriptive only**: that arm's trained model is `beta` *plus* a paired
residual, so its `beta` alone is not its model and its objective's optimum in `beta` is not defined
independently of the residual. The reading rule's `beta` comparisons are evaluated on `FT-XF-BC`,
the only arm whose trained model is exactly the 5-term linear function (deviation 1).

## 3. X2 — the root target package, rebuilt three ways

Root design per policy: 20,480 rows of the policy's own fold. PROBE targets rebuilt exactly as the
frozen package does — `probe_primitive + max over K_TRAIN of Q_tail(k, belief)` — from three tail
sources, then solved exactly and read for the implied root action vector. Oracle vector:
seven `IMMEDIATE` and `PROBE` at `LINKED-p17_20-c9_100`.

| Tail source | folds reproducing the oracle root vector |
| --- | --- |
| (a) exact oracle tail | **6 of 6** |
| (b) `beta_tail_star` (the objective's own optimum) | 4 of 6 — fails at seed `01`, both folds |
| (c) published `FT-XF-BC` tail | **0 of 6** |
| (c) published `FT-XF-FLEX` tail | 1 of 6 (seed `02`, fold 1) |

Two things follow directly. First, **the frozen target package is not a ceiling**: given a correct
tail, the odd/even substitution (`max over K_TRAIN` in the target versus `K_eval` in the criterion)
still yields the oracle root vector at every seed and fold, which is why `D4` did not fire and is
consistent with the closed-form gap of at most `0.003713` quoted in the card. Second, the published
policies' root failures are **inherited tail error**: with the published tails the implied root
vector is wrong everywhere, and the failures are not uniform — `FT-XF-BC` under-probes in two folds
(no `PROBE` at all) and over-probes in the rest, once selecting `PROBE` in all eight contexts.

Notably, even the objective's own optimum loses the oracle root vector in 2 of 6 folds, so the
margin between the target-context `PROBE` value and the baseline is thin enough that per-policy
estimation error alone can flip it.

## 4. X4 — fold coupling

`beta_tail_star` recomputed on the fold the tail trains on versus the fold the root trains on:

| Seed | max abs difference |
| --- | --- |
| `00` | 0.062555 |
| `01` | 0.226024 |
| `02` | 0.147653 |

The same order as `d_objective` itself (0.060–0.223). Fold coupling is therefore not a separate
mechanism at this sample size — it is the same per-policy estimation variance seen twice.

## 5. X3 — not run

The card runs X3 only if X1 shows `d_objective` small and `g_learned` large. `d_objective` is
`0.222610 > epsilon`, so the trigger did not fire and X3 did not run. This is the card's own
condition, applied as written; the runner records `x3_triggered: false`.

## 6. The reading rule applied verbatim

Card section 4, branches evaluated in the stated order with the thresholds frozen there
(`epsilon = 0.10`, gradient ratio `10`).

1. **`D4 — TARGET_PACKAGE_CEILING`**: fires if X2(a) does not reproduce the oracle root vector.
   X2(a) reproduces it in **6 of 6** folds. **Does not fire.**
2. **`D1 — OBJECTIVE_FIXED_POINT_DIFFERS`**: fires if `d_objective > epsilon`.
   `max d_objective = 0.222610 > 0.10`. **Fires.**

Branch: **`D1`**. Its registered reading, verbatim: *"the frozen tail objective's own optimum is not
`beta*`; the learner is converging correctly to the wrong place, and every exposure result to date is
consistent with a correct optimizer on a mis-specified objective."*

**Verdict on the prediction on record: contradicted.** The prediction was M2 — "the objective's own
optimum is still `beta*` and the learners do not reach it". `D2` (`OPTIMIZATION_SHORTFALL`) is the
branch that would have supported it, and the rule did not reach `D2`, because `D1`'s condition is
tested first and is met. Under either reading of the card's singular `g_learned > 10 * g_star`
(as "for all six linear-arm policies", which is how it was applied, or as "for any"), the branch is
still `D1`, because `D1` precedes `D2` in the stated order — so the ambiguity noted in deviation 2
is not deciding here.

**What the branch does not capture, stated because the numbers require it.** Two observations sit
alongside the branch and neither changes it:

- *The objective is not mis-specified; the `D1` condition is met by per-policy sampling error.* A
  post-hoc descriptive supplement (deviation 3), pooling all six designs into one 61,440-row fit,
  gives `beta_pooled = (0.305074, 0.598557, 1.371487, −1.101781, −0.908709)`, a distance to `beta*`
  of `0.021781` — inside `epsilon` — with all five coordinates within `1.22` standard errors of
  `beta*` (residual sigma `0.401674`, standard errors `0.0077`–`0.0240`). So the *population*
  optimum of the frozen tail objective is `beta*`, exactly as the instrumentation check's algebra
  said it must be; what X1 measured is that at the `n = 10,240` each policy actually sees, on a
  design with `kappa ≈ 717`, the *empirical* optimum sits `0.06`–`0.22` away per coordinate. That
  is an estimator-variance effect, and the ill-conditioning that mechanism M2 blames for slow
  optimisation is the same ill-conditioning that inflates this variance.
- *The learners are separately, and much further, from their own objective's optimum.* `d_learned`
  for the linear arm is `0.951`–`2.380`, roughly ten times `d_objective`, with gradient ratios up to
  `107.78`. The `D1` reading's second clause — "the learner is converging correctly" — is therefore
  **not** supported by X1's own numbers. The learner is not at the empirical optimum, not at the
  pooled optimum, and not at `beta*`.

So the prediction's *mechanism as the rule defines it* is contradicted, while the *phenomenon* the
prediction describes — learners far from the optimum — is corroborated and is larger than the effect
that decided the branch. The frozen five-branch rule has no branch for "the objective's optimum is
right in population but noisy per policy, **and** the learner is far from both", which is what the
data show. That gap in the rule is recorded here rather than patched.

## 7. Deviations

1. **The rule's `beta` comparisons were evaluated on `FT-XF-BC` only.** The card names "each
   published final tail `beta`" without saying how to treat `FT-XF-FLEX`, whose trained model is
   `beta` plus a 4,865-coordinate residual and for which an optimum in `beta` alone is not defined.
   `FT-XF-BC` — the arm whose model *is* the 5-term linear function — carries the rule; FLEX is
   reported descriptively in section 2. This choice is recorded in the runner as `LINEAR_ARM`.
2. **The card's `g_learned > 10 * g_star` is singular and was applied as "for all six linear-arm
   policies"** (the conservative reading; 3 of 6 ratios exceed 10). As section 6 notes, the branch is
   `D1` under either quantifier, so this is not deciding.
3. **A post-hoc descriptive supplement was computed after the frozen measurements** — the pooled
   61,440-row solve, the residual standard deviation and the analytic standard errors — and is
   recorded at `temp/directions/ucope/exp/training_target_diagnostic_r01_20260903/supplementary.json`.
   It is not part of the frozen measurement set, it decides nothing, and it did not change the
   branch. It is reported because without it the `D1` reading would be misleading.
4. **The runner imports four private helpers from the frozen `training.py`** (`_canonical_rows`,
   `_cyclic_batch`, `_step`, `_tail_batch`) deliberately, so that the row selection, the batch
   schedule and the optimizer step are the frozen code paths rather than re-implementations.
5. **The resource admission ran before *all* measurements**, not only before the one that trains.
   This is stricter than the instruction and costs nothing.
6. **X3 did not run**, because X1 did not call for it. That is the card's condition, not a choice.
7. **The per-policy standard errors in the supplement assume i.i.d. residuals.** Observation: the
   per-policy `max |z|` against `beta*` is `2.97`–`4.99` while the pooled `max |z|` is `1.22`.
   Inference, not measured here: the host draws each episode's marks from a counter-addressed stream
   keyed on `(namespace, seed, episode_index)` and evaluates all eight contexts at the same episode
   index, so rows within an episode are not independent and the i.i.d. standard errors are
   optimistic; the per-policy `z` values should be read as upper bounds on significance. The pooled
   statement does not depend on this.

## 8. Could not verify

- Whether the per-policy departures of `beta_tail_star` from `beta*` are significant under the true
  correlation structure of the host's draws. Not measured; see deviation 7.
- Whether more optimizer steps would close `d_learned`. X3 is the measurement for that and the
  card's trigger did not fire, so the question is open with numbers attached but no test.
- Anything about the *root* learner's own optimisation. X2 solved the root exactly; it did not
  examine how the trained root moves.
- `FT-XF-FLEX`'s objective optimum. Its model class includes the residual and no fixed point was
  computed for it; its rows in section 2 are descriptive.
- Anything about the whitening discriminator, which is owner-held and was neither read nor run.
- Anything outside this frozen eight-context host: no acquisition or COUNT/RAW polarity, no
  conditioning attribution, no stable superiority, no seed-population claim, and nothing about
  variable `k`, variable `N`, MARL/UAV, transfer, safety, deployment or real-world QoS.

## 9. What this means for the direction's next object — options, not a decision

Stated for the owner to choose among; this document decides none of them.

1. **An estimator-variance object.** The pooled fit reaches `beta*` and the per-policy fit does not,
   at `kappa ≈ 717`. An object that raises the per-policy tail sample (more episodes per context, or
   fitting the tail on both folds where the §4 integrity items allow it) would test whether
   `d_objective` collapses as `1/sqrt(n)` predicts, and would say whether the direction's competence
   criterion is reachable at any practical sample size on this host.
2. **An optimiser/conditioning object — the prediction's mechanism, now with numbers.** `d_learned`
   of `0.951`–`2.380` at `kappa ≈ 717` is a large, concrete shortfall. The X3 measurement is already
   written and was not triggered; a named object could run it directly (continue the frozen loop for
   ten times the budget, against the exact solve) and settle whether more of the same steps ever
   suffice. This is where the quarantined whitening discriminator's question returns.
3. **A reading-rule object.** The frozen five branches cannot express the combination the data show.
   A successor rule would separate "population optimum" from "empirical optimum at the policy's own
   sample size" and would test the learner against the latter, not against `beta*`.
4. **A margin object.** X2 shows that even the objective's own optimum loses the oracle root vector
   in 2 of 6 folds, so the target context's `PROBE`-versus-baseline margin of `0.021437` is thin
   relative to per-policy estimation error. The margin-scaled competence falsifier already held in
   reserve by the review addresses exactly this.
5. **Stop spending on the ladder family.** The ladder is closed, the instrument is verified, and the
   remaining questions are about the estimator and the criterion rather than about exposure.
