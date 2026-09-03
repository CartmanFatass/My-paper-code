# UCOPE-A-TAIL-MARGIN-TARGET-CONTEXT-R01 — card

- Direction: `ucope`
- Object id: `UCOPE-A-TAIL-MARGIN-TARGET-CONTEXT-R01`
- Evidence class: **`A/RECON`** for part 1 (sections 3–7, computed here); part 2 (sections 8–12)
  registers a **follow-on `B/EXPLORE` object that is NOT run and NOT frozen by this card's
  execution** — it awaits the owner's prediction and decision.
- Written: 2026-09-03, under owner decision D.18 (commit `298ca67e2`), after the accepted
  root-conditioning object (branch `R'-B`) and the D.17 correction that the binding failure is the
  tail's decision margin at the target context.
- **Part 1 has been computed and is outcome-free. Part 2 is not run.**

## 1. Question

Three objects have now removed everything except one thing.

| Object | Branch | What it removed |
| --- | --- | --- |
| Training-target diagnostic R01 | `D1` | the tail objective is right; per-policy variance was the problem |
| Optimiser-and-conditioning R01 | `O-B` | tail conditioning is the dominant cause |
| Competence (whitened) R01 | `C-C` | with both handled the two-stage exact solve is competent 6 of 6 and the whitened learner 3 of 6 |
| Root-conditioning R01 | `R'-B` | root conditioning was real and largely removable: `C_root` 1 of 6 raw to 5 of 6 whitened, ceiling 6 of 6, `d_objective_root` inside `eps_L` everywhere |

What remains is a single component of `C_even`: `min_forced_PROBE_tail_agreement >= 19/20`, which
depends on the **tail model alone** and fails in exactly three of the six policies, at
`0.611559, 0.611559, 0.520727`. No root treatment can touch it. **Why does the held-out tail
decision fail there, and what would fix it?**

## 2. Claim ceiling

**Part 1 is `A/RECON`: reconnaissance.** It computes closed-form geometry from the frozen basis, the
frozen oracle and coefficient vectors already published by the competence object. It trains nothing,
samples nothing and evaluates no policy; it establishes no polarity, no competence and no
comparison, and it consumes no `B` budget. Its own runner is asserted by test to contain no call to
`optimizer_for`, `train_stage`, `_step`, `execute_policy_episode` or `evaluate_policy`.

**Part 2, if the owner registers it, would be `B/EXPLORE`** on 3 seeds x 2 folds of one arm on one
frozen eight-context host, and could not establish acquisition polarity, COUNT/RAW polarity, stable
superiority, a seed-population effect, anything about `FT-XF-FLEX`, or anything about variable `k`,
variable `N`, MARL/UAV, transfer, safety, deployment, flight, energy or real-world QoS.

## 3. Part 1 — method, and why it is exact rather than approximate

The tail score is **linear** in the coefficients: `Q(b, k) = z(b, k) . beta` with the frozen
5-term basis `z = (1, b, k, b*k, k^2)`, `k = period/9`. Three consequences make the whole of part 1
closed-form:

- The **top-two gap** at a belief is `(z_top - z_runner) . beta`, itself linear in `beta`.
- The **flip radius** — the smallest `L2` coefficient perturbation that can change the argmax — is
  `min over competitors of (score_top - score_competitor) / ||z_top - z_competitor||`. It is a
  worst-case (adversarially directed) quantity.
- The **directional derivative** of the gap along any direction `d` is exactly `(z_top - z_comp) . d`,
  and `gap(beta* + e) = gap(beta*) + (z_top - z_comp) . e` **exactly**, with no truncation. So the
  "predicted" gap at a published coefficient error is not a linearisation; it is the value.

Launch conditions (spec §11.4): the central 4 GiB admission was taken before the computation
(`14,193,020,928` bytes physical and effective, `2026-09-03T16:10:00.154705Z`, passed). No §5.2
counts apply, because nothing is trained or sampled; no exposure line applies, because there is no
optimizer trajectory. Runner:
`scripts/run_ucope_tail_margin_geometry_r01.py`; unit checks
`tests/experiments/candidates/ucope/test_tail_margin_geometry_r01.py`, **13 passed**. Record
(gitignored): `temp/directions/ucope/exp/tail_margin_geometry_r01_20260903b/margin-geometry.json`,
wall `0.331 s`. (An earlier invocation at `..._20260903` produced identical geometry without the
section 6 identity block; the `b` record is the one cited here.)

Published vectors are read from the competence object's run record, which is gitignored — so **every
number this card relies on is quoted in full below**, and the card, not the record, is the durable
artifact.

## 4. Where the held-out decision is tight — at `beta*`, before any learner

The frozen basis reproduces the oracle's exact tail values everywhere (`max` deviation `2.220e-16`),
and its argmax equals the oracle period at all 56 (context, belief) cells. Per context, the minimum
flip radius over the seven forced-PROBE beliefs:

| Context | min flip radius (`L2`) | min top-two gap | ratio to the tightest |
| --- | --- | --- | --- |
| **`LINKED-p17_20-c9_100`** (target) | **0.019485** | **0.008007** | **1.00** |
| `LINKED-p17_20-c7_50` | **0.019485** | **0.008007** | **1.00** |
| `LINKED-p13_20-c9_100` | 0.033361 | 0.013711 | 1.71 |
| `LINKED-p13_20-c7_50` | 0.033361 | 0.013711 | 1.71 |
| `SEVERED-p13_20-c9_100` | 0.114195 | 0.040000 | 5.86 |
| `SEVERED-p13_20-c7_50` | 0.114195 | 0.040000 | 5.86 |
| `SEVERED-p17_20-c9_100` | 0.114195 | 0.040000 | 5.86 |
| `SEVERED-p17_20-c7_50` | 0.114195 | 0.040000 | 5.86 |

**Honest correction to the phrase "the target context".** The tail basis contains **no cost term**,
so the tail geometry cannot depend on the probe cost. The target context ties *exactly* with its
cost twin `LINKED-p17_20-c7_50`, and its rank of 1 in the fragility ordering is a tie-break, not a
separation. The fragile object is the **belief stratum `(LINKED, p = 17/20)`**, which two of the
eight contexts share. Everything below should be read as a statement about that stratum.

Inside the target stratum, cell by cell at `beta*`:

| count | belief | mass | oracle `k` | runner-up | top-two gap | flip radius |
| --- | --- | --- | --- | --- | --- | --- |
| **0** | 0.000030 | 0.188580 | 6 | 8 | **0.008007** | **0.019485** |
| **1** | 0.000969 | 0.199861 | 6 | 8 | **0.008233** | **0.020033** |
| **2** | 0.030201 | 0.090832 | 6 | 8 | 0.015248 | 0.037100 |
| 3 | 0.500000 | 0.041453 | 4 | 6 | 0.040000 | 0.114195 |
| 4 | 0.969799 | 0.090832 | 2 | 4 | 0.064752 | 0.188679 |
| 5 | 0.999031 | 0.199861 | 2 | 4 | 0.071767 | 0.206644 |
| 6 | 0.999970 | 0.188580 | 2 | 4 | 0.071993 | 0.207213 |

**Why this stratum is the fragile one.** At `p = 17/20` a `LINKED` context is very informative, so
the posterior after a forced PROBE is pushed to the extremes: `b ~ 3e-05` at count 0 and
`b ~ 0.99997` at count 6, and the two extreme-low cells carry `0.388441` of the mass between them.
At `b -> 0` the true tail values of `k = 6` and `k = 8` are nearly equal — a gap of `0.008007`, five
times tighter than the `0.040000` that a `SEVERED` context (belief pinned at `1/2`) shows at every
count — while carrying **ten times** the mass a `SEVERED` cell has at its own tightest point. Low
reliability (`p = 13/20`) spreads the posterior and keeps the gap at `0.013711`. So the fragility is
an interaction: **the most informative link produces the most extreme beliefs, and at extreme
beliefs the held-out periods are hardest to tell apart, and that is exactly where the mass is.**

**The arithmetic closes exactly.** A flip at counts 0 and 1 costs `0.188580 + 0.199861 = 0.388441` of
agreement, and `1 - 0.611559 = 0.388441`. Adding count 2 costs `0.479273`, and
`1 - 0.520727 = 0.479273`. The two observed failing agreements are *exactly* "counts 0 and 1 flipped"
and "counts 0, 1 and 2 flipped". Nothing else is happening.

## 5. Where the published tails sit — the flip is exact, not statistical

`||beta - beta*||` for the published vectors, and the projection of that error onto the count-0
decision direction. A cell flips **iff** `gap + (z_top - z_comp) . (beta - beta*) < 0`, i.e. iff the
projection is below `-0.008007`.

| Policy | vector | `\|\|error\|\|_2` | projection at count 0 | resulting gap | flipped? |
| --- | --- | --- | --- | --- | --- |
| seed 00 fold 0 | `EXACT-SOLVE` | 0.017641 | −0.002286 | +0.005721 | no |
| seed 00 fold 0 | `WHITENED-10X` | 0.136005 | **−0.008340** | **−0.000333** | **yes** |
| seed 00 fold 1 | `EXACT-SOLVE` | 0.066658 | −0.003625 | +0.004382 | no |
| seed 00 fold 1 | `WHITENED-10X` | 0.122529 | **−0.014219** | **−0.006212** | **yes** |
| seed 01 fold 0 | `EXACT-SOLVE` | 0.036184 | +0.006493 | +0.014501 | no |
| seed 01 fold 0 | `WHITENED-10X` | 0.084184 | +0.015591 | +0.023598 | no |
| seed 01 fold 1 | `EXACT-SOLVE` | 0.029996 | −0.002244 | +0.005763 | no |
| seed 01 fold 1 | `WHITENED-10X` | 0.046835 | +0.003783 | +0.011790 | no |
| seed 02 fold 0 | `EXACT-SOLVE` | 0.062741 | +0.000120 | +0.008128 | no |
| seed 02 fold 0 | `WHITENED-10X` | 0.301723 | **−0.017780** | **−0.009773** | **yes** |
| seed 02 fold 1 | `EXACT-SOLVE` | 0.018482 | −0.003945 | +0.004062 | no |
| seed 02 fold 1 | `WHITENED-10X` | 0.029900 | −0.000271 | +0.007736 | no |

Four readings, all outcome-free:

1. **The norm alone does not decide it.** `seed 01 fold 0`'s learned tail has `||error|| = 0.084184`,
   more than four times the flip radius `0.019485`, and does not flip, because its error points the
   *helpful* way (`+0.015591`). The flip radius is a worst-case bound; the **projection** is the
   quantity that decides.
2. **The margin is razor-thin where it fails.** `seed 00 fold 0` lands at `−0.000333` — a gap
   `0.000333` on the wrong side out of an original `0.008007`, i.e. **4.2 %** past the edge.
   `seed 00 fold 1` is `77.6 %` past; `seed 02 fold 0` is `122 %` past.
3. **The exact solves never flip.** Their projections span `−0.003945 .. +0.006493`, all inside
   `+-0.008007`, so the *objective* at `n = 81,920` is already safe. The failure is entirely the
   learner residual, which is what `C-C` said and what `R'-B` left standing.
4. **Every flip anywhere is a low-belief cell in a `LINKED` context.** Across all 56 cells and all
   six published tails, the flipped cells are exactly:

   | Policy | flipped cells | total |
   | --- | --- | --- |
   | seed 00 fold 0 | `LINKED-p17_20-*` counts 0, 1 | 4 |
   | seed 00 fold 1 | `LINKED-p17_20-*` counts 0, 1; `LINKED-p13_20-*` count 0 | 6 |
   | seed 01 fold 0 / fold 1 | none | 0 |
   | seed 02 fold 0 | `LINKED-p17_20-*` counts 0, 1, 2; `LINKED-p13_20-*` count 0 | 8 |
   | seed 02 fold 1 | none | 0 |

   No `SEVERED` context ever flips, and no count from 3 to 6 ever flips. The `LINKED-p13_20`
   flips at count 0 cost only `0.038629` of mass, leaving agreement `0.961371`, still above the
   gate — which is why the gate fails **only** in the `p = 17/20` stratum.

## 6. The identity that makes a margin-aware remedy legal

The frozen §4 integrity item separates **training support** `K_train = {1,3,5,7,9}` from **held-out
support** `K_eval = {2,4,6,8}`. A margin-aware objective that penalised the held-out top-two gap
directly would train on held-out periods and destroy that separation, invalidating every evaluation
in the direction. It is not available.

It is not needed. For the frozen basis, at **any** belief,

> `z(b, j) - z(b, j+2) == ( z(b, j-1) - z(b, j+3) ) / 2`, exactly.

The first two coordinates cancel and the remaining three are affine and quadratic in `k` over an
evenly spaced pair. Every held-out decision direction therefore has a **`K_train` witness**:

| held-out pair | witness pair in `K_train` | relation |
| --- | --- | --- |
| `(2, 4)` | `(1, 5)` | held-out direction = witness / 2 |
| `(4, 6)` | `(3, 7)` | held-out direction = witness / 2 |
| **`(6, 8)`** | **`(5, 9)`** | held-out direction = witness / 2 |

Verified over all `8 x 7 x 3 = 168` (context, belief, pair) cells: maximum deviation
`1.110e-16`, and `||z(b,5) - z(b,9)|| = 2 ||z(b,6) - z(b,8)||` to the same precision. **A penalty on
the `(5, 9)` gap at the training beliefs controls the held-out `(6, 8)` margin exactly, at a factor
of two, without any held-out period entering training.** This is what makes arm `MARGIN-AWARE` in
section 8 a legal object rather than a leak.

## 7. What part 1 does and does not establish

Establishes, as arithmetic: the fragile object is the belief stratum `(LINKED, p = 17/20)`, not a
single context and not the cost; the tightest cell is count 0 with a true gap of `0.008007` and a
flip radius of `0.019485`; the three observed agreement failures are exactly the cells whose
projections cross that gap; the objective at `n = 81,920` is already safe and the learner residual is
not; and each held-out decision direction has an exact training-support witness.

Establishes nothing about: whether any remedy works, the polarity of any comparison, competence,
`FT-XF-FLEX`, other `n`, other hosts, or the direction's scientific claim. Part 1 **is not** a
result about a learner.

## 8. Part 2 — the follow-on `B/EXPLORE` object, its arms and their predicted effects

**Not run, and not registered as consumed by this card.** Proposed id
`UCOPE-B-EXPLORE-TAIL-MARGIN-REMEDIES-R01`, `B/EXPLORE`, three seeds, both group-disjoint folds,
the frozen `FT-XF-BC` arm, the whitened tail treatment carried unchanged from the competence object,
the same index law with a **fresh disjoint offset** (`OFFSET = 2,000,000`, a multiple of 20, disjoint
from `0..5,119`, `0..319` and `1,000,000..1,081,919`), and the root stage held at
`WHITENED-ROOT-10X`, which `R'-B` showed is not what binds.

**Baseline to beat, from the published run**: agreement `>= 19/20` in **3 of 6** policies; count-0
target-stratum gaps `−0.000333, −0.006212, +0.023598, +0.011790, −0.009773, +0.007736`.

| Arm | What it changes | Predicted effect on the count-0 margin, from section 5 |
| --- | --- | --- |
| **`LARGER-N`** | `n = 163,840` tail rows per policy (double), same 10x budget (1,600 tail updates), same `lr` and batch | **Near zero.** The published exact solves already never flip (projections `−0.003945 .. +0.006493` inside `+-0.008007`), so the objective is not what crosses the gap. Doubling `n` scales the *sampling* term by about `1/sqrt(2)`, taking `||beta_exact - beta*||` from `0.017641 .. 0.066658` to roughly `0.012 .. 0.047` — still safe, and leaving the learner residual untouched. Predicted competent-by-agreement count: **3 of 6, unchanged.** |
| **`BUDGET-100X`** | whitened tail at **16,000 tail updates** (ten times the ten-fold budget) at `n = 81,920`, everything else frozen | **Proportional to how much of the residual the extra budget removes.** The three failing projections are `−0.008340, −0.014219, −0.017780` against a threshold of `−0.008007`, so they must shrink by **4.0 %, 43.7 % and 55.0 %** respectively. `O-B` measured that the first ten-fold step removed `82.2 %` of the median gap; if a second step removes even half that, all three clear. Predicted: **5 or 6 of 6**, with `seed 02 fold 0` — the one needing `55 %` — the doubtful one. |
| **`MARGIN-AWARE`** | whitened tail at the 10x budget with a hinge added to the tail loss on the **training-support** `(5, 9)` gap at the training beliefs: `sum over rows of max(0, m - (z(b,5) - z(b,9)) . beta)` with `m` fixed below | **Direct and bounded.** By section 6 the held-out `(6,8)` margin is exactly half the `(5,9)` margin, so enforcing `(z(b,5) - z(b,9)) . beta >= m` enforces a held-out gap of `>= m/2`. Setting `m = 2 x 0.012011 = 0.024022` — one and a half times the truth's own gap — makes a flip at count 0 impossible while the hinge is satisfied. Predicted: **6 of 6 on the agreement gate**, at the price of value bias: `d_learned_tail` and `d_objective` should *worsen*, and the root targets built from this tail move with it, so `C_root` and the root's `d_objective_root` must be re-reported. |

The hinge weight is the one free hyperparameter; it is fixed here at `1.0` relative to the MSE term,
with `m = 0.024022`, and neither is to be tuned after seeing data.

## 9. Part 2 — reading rule, ordered by effect size, thresholds fixed before data

Branch statistic: the frozen `C_even` component `min_forced_PROBE_tail_agreement >= 19/20`, per
policy, at the final root update, on the even held-out support. Thresholds, all fixed here:
the agreement gate `19/20` (frozen, unchanged); "majority" is **at least 4 of 6** policies; the
published baseline is **3 of 6**; "strictly improves the margin" means the count-0 target-stratum
gap becomes positive in a policy where the baseline has it negative.

- **`M-A — MARGIN_CLOSED`.** Some arm reaches agreement `>= 19/20` in **all six** policies. Reading:
  the tail margin was the whole remaining obstruction, and the named arm removes it. The full `C_even`
  must then be re-reported for that arm, because it is the first configuration in this chain that
  could be competent in six.
- **`M-B — MARGIN_MAJORITY`.** Not `M-A`, but some arm reaches **at least four** of six. Reading: the
  margin is the obstruction and the named arm removes it partially; the residual policies are the
  next subject.
- **`M-C — MARGIN_MOVED_NOT_CLOSED`.** No arm reaches four, but at least one arm **strictly improves
  the margin** in every policy where the baseline is negative, without turning any positive baseline
  negative. Reading: the mechanism is confirmed and the dose is insufficient.
- **`M-D — MARGIN_UNMOVED`.** No arm exceeds `3 of 6` and no arm strictly improves the margin.
  Reading: the tail margin is not reachable by budget, sample size or a training-support hinge on
  this host, which is a statement about the criterion's reachability and connects directly to the
  margin-scaled falsifier the review holds in reserve.
- **`M-E — UNCLEAR`.** Any other combination, including an arm that improves some policies and
  breaks others. Report every number, name what is unexplained, propose no successor.

Descriptive and deciding nothing: `d_learned_tail`, `d_objective`, `C_root`, the full `C_even`
counts, the root re-report, the per-context breakdown, the gradient ratios, the whitening numbers and
the exposure line. At three seeds no arm-comparison polarity, stable-superiority or seed-population
claim is available.

## 10. Part 2 — launch conditions (§11.4) and budget

Still gating: the central 4 GiB admission immediately before the workload; the §4 integrity items —
group-disjoint folds, **the odd-training / even-held-out separation** (which section 6 is what makes
`MARGIN-AWARE` compatible with), no read of B1 or audit runtime rows, fresh counter-addressed data at
the disjoint offset, whitening from training rows only per stage; the §5.2 nonzero counts reconciled
exactly; one machine-generated exposure line. Recorded and never gating: source-inventory
cleanliness, the absence of an A/RECON performance assessment, execution topology, resource
telemetry, and the direction's sequencing locks. Learner-side instrumentation failure quarantines
under §6.2.

**Budget: under 25 minutes.** From the two measured runs (the competence object did 983,040 episodes,
19,200 tail and 38,400 root updates in `110.970 s`; the root object did the same generation, 9,600
tail and 38,400 root updates in `98.620 s`): `LARGER-N` needs `1,966,080` episodes (about `140 s`)
plus 1,600 tail and 3,200 root updates per policy; `BUDGET-100X` and `MARGIN-AWARE` share the
`983,040`-episode generation (about `70 s`) and need `16,000 + 1,600 = 17,600` tail updates and
`6,400` root updates per policy. Total roughly `6 x 21,000 = 126,000` optimizer steps on 5- and
7-parameter models at batch 256, plus 18 exact solves and 18 evaluations. Outputs under
`temp/directions/ucope/exp/tail_margin_remedies_r01_<date>/`.

## 11. What each branch would mean for the acquisition lock and COUNT/RAW

The direction records `PAID_ACQUISITION_STATUS=UNEVALUATED_LOCKED` and
`COUNT_RAW_STATUS=LOCKED_UNTIL_COMPETENCE`. Under the section-11 recast those are the direction's own
sequencing choice, recorded and not §11 gates. **This card opens neither, and part 1 cannot: it is
reconnaissance.**

- **`M-A`** would, for the first time in the direction, put a learner in reach of `C_even` in all six
  policies — the COUNT/RAW lock's stated precondition. Whether to open the lock, and whether the
  acquisition evaluation is then a separate named object on the competent policies, are owner
  decisions this card does not pre-empt. The full `C_even` would have to be re-reported for the
  named arm before any such step, because agreement is only one of five components.
- **`M-B`** would leave the precondition partially met; a majority is not the ladder's `B_COMPETENT`
  rule. The honest next step would be the residual policies, not an unlock.
- **`M-C`** would keep both locks and make the dose — budget, hinge weight or `m` — the next object.
- **`M-D`** would keep both locks and turn the question to the **criterion**: an agreement gate of
  `19/20` on a stratum whose true top-two gap is `0.008007` may be asking for a coefficient accuracy
  no learner reaches on this host, which is a statement about the margin and the criterion together.
- **`M-E`** would keep both locks and propose nothing.

No branch supports `PARK`, promotion, retirement or a lifecycle change on its own.

## 12. Prediction requested from the owner

Please pick one before part 2 is registered and run.

- **Option `LARGER-N`.** More data closes it: the remaining flips are a sampling effect and doubling
  `n` removes them.
- **Option `BUDGET-100X`.** More optimisation closes it: the residual is the learner's, and a second
  ten-fold step shrinks the decision-direction projection below `0.008007` in all three failing
  policies.
- **Option `MARGIN-AWARE`.** Only a change of objective closes it: uniform squared error does not
  care where the decision boundary is, and the training-support hinge of section 6 is what puts the
  margin into the loss.
- **Option "unclear".** No single arm closes it cleanly and `M-C`, `M-D` or `M-E` is the honest
  result.

Please also say whether part 2 is to be registered as
`UCOPE-B-EXPLORE-TAIL-MARGIN-REMEDIES-R01` as written, or amended first.
