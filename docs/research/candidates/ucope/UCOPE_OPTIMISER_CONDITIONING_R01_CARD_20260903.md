# UCOPE-B-EXPLORE-OPTIMISER-CONDITIONING-R01 — card

- Direction: `ucope`
- Object id: `UCOPE-B-EXPLORE-OPTIMISER-CONDITIONING-R01`
- Evidence class: **`B/EXPLORE`**
- Written: 2026-09-03, **before** anything is run. Owner decision D.12 (commit `815296414`),
  following the accepted training-target diagnostic (compliance note D.11, commit `187941bf6`).
- Frozen by: this card. It awaits the owner's prediction (section 9) before launch.
- Predecessors it reads, and only for already-published numbers:
  `UCOPE_TRAINING_TARGET_DIAGNOSTIC_R01_RESULT_20260903.md` and the R02 rung-2 checkpoints, which is
  what `ladder.validate_complete` already reads. No published record is altered.

## 1. Question

On the **linear** tail objective — `FT-XF-BC`, the one arm whose trained model *is* the frozen
5-term Bellman function `(1, b, k, b*k, k^2)` — the accepted diagnostic measured a large gap between
where the learner stops and where its own per-policy objective is minimised:

| policy (seed / fold) | `d_learned` | `g_learned / g_star` | `d_objective` |
| --- | --- | --- | --- |
| `00` / 0 | 1.953026 | 1.84 | 0.216774 |
| `00` / 1 | 1.725694 | 20.98 | 0.168532 |
| `01` / 0 | **2.380056** | **107.78** | 0.180732 |
| `01` / 1 | 1.950627 | 3.79 | 0.060108 |
| `02` / 0 | 1.623135 | 16.49 | 0.172426 |
| `02` / 1 | **0.951506** | 2.25 | 0.222610 |

with a design whose Gram condition number is `714.483`–`736.646` and smallest eigenvalue
`2.6e-03`, at `n = 10,240` rows per policy.

**Does whitening the design close that gap at the published budget, and does the exact solve reach
it?**

## 2. What is fixed, and what the single declared axis is

Fixed: the frozen host, the counter-addressed RNG, the three B1 seeds
`ucope-scout-r01-b1-fresh-{00,01,02}`, both group-disjoint folds, 5,120 episodes per context, batch
256, the `FT-XF-BC` initialisation `build_arm("FT-XF-BC", seed, fold)`, the frozen `_step` loop
(AdamW, `betas (0.9, 0.999)`, `eps 1e-8`, `weight_decay 0.0`, `clip_grad_norm_(..., 1.0)`), and the
frozen cyclic batch schedule `_cyclic_batch`. Six policies, exactly the ladder's.

The **single declared axis is the coordinate system the optimiser works in**: raw versus whitened.
Everything else that differs between arms is either the same loop at a longer budget (X3's 10x) or
an outcome-free closed-form reference (the exact solve).

**Whitening leaves the objective's optimum unchanged.** `Z_tilde = Z L^-T` with `G = Z^T Z / n =
L L^T` is a bijective linear reparameterisation, so the least-squares optimum in `beta` is *exactly*
the same vector in both arms and `d_objective` cannot move. Only the optimiser's trajectory changes.
Two consequences are recorded, not hidden: AdamW is not affine-invariant, which is the whole point;
and `clip_grad_norm_(..., 1.0)` then clips a norm measured in the whitened coordinates, which is a
different constraint from the raw one.

## 3. Arms

1. **`RAW-BASE`** — the published path. Raw design, frozen `_step` loop, **rung-1 budget**: 160 tail
   updates at `lr 3e-3`, batch 256, from the frozen initialisation.
2. **`WHITENED-BASE`** — identical loop, identical budget, identical initialisation (mapped through
   `L^T`), on the whitened design.
3. **`EXACT-SOLVE`** — the normal-equation solution in float64. Outcome-free reference; `d_learned`
   is `0` by construction and it trains nothing. It exists to show the ceiling is reachable and to
   supply `beta_tail_star` per policy.

Plus the diagnostic's X3 extension on the two training arms:

4. **`RAW-10X`** and 5. **`WHITENED-10X`** — the same loops continued to **1,600** tail updates
   (ten times the base budget), everything else unchanged.

`RAW-BASE`'s `d_learned` at the rung-1 budget has **not** been computed by any prior object; the
table in section 1 is from the R02 **rung-2** finals (1,600 updates at `lr 3e-4`). So arm 1's base
number is genuinely unseen when this rule is fixed, and so is every whitened number. That is stated
here rather than discovered later.

### Whitening, and its numerical contract

`G` is computed **from the training rows only** — the same `_canonical_rows(population, fold=fold,
tail=True)` the learner trains on, which are the complementary fold's PROBE rows. No held-out row,
no other fold, no other seed, and no evaluation row enters `G`. This is a §4 integrity item for this
object, and a launch condition: a whitening fitted on anything else refuses the launch.

The transform is computed and applied at **float64**, with a Cholesky contract checked before any
optimizer step:

- `max |L L^T - G| <= 1e-10` (absolute), and
- `lambda_min(G) > 1e-6`.

How the tolerance follows from the published numbers: standard error analysis puts the Cholesky
reconstruction error at `O(kappa * eps)`, and with the measured `kappa ~= 717` and
`eps_fp64 = 2.22e-16` that is `~1.6e-13`. The ceiling of `1e-10` is roughly 600x that headroom —
tight enough to refuse a genuine numerical failure, loose enough not to repeat the mistake that
quarantined the whitening discriminator, whose `16 * eps_fp32 = 3.81e-06` ceiling was calibrated at
40-episode technical scale and was exceeded by `2.4`–`2.5x` (`9.12e-06`–`9.69e-06`) at science
scale. `lambda_min(G) > 1e-6` is four orders below the observed `2.6e-03`, so it refuses a
rank-deficient design without being brittle.

## 4. Mechanisms

**(i) Conditioning is the cause.** The learner's shortfall is a property of the coordinate system:
AdamW's per-coordinate normalisation does not fix a rotation, so on a Gram with `kappa ~= 717` the
slow eigendirection needs roughly `kappa` times the travel of the fast one, while the per-coordinate
budget is `steps x lr = 0.48` at the tail stage of both published rungs. Prediction under (i):
**`WHITENED-BASE` closes `d_learned` at the base budget**, because in whitened coordinates every
direction has the same curvature and 160 steps suffice.

**(ii) The optimiser or the batch schedule is the cause.** The shortfall comes from the step rule
and the data order rather than from the geometry: batches are contiguous cyclic windows of a list
sorted by `(episode_index, context_id)` and never shuffled (`training.py:_cyclic_batch`), with the
behaviour period a deterministic function of the episode index (`host.py:49`), and the gradient is
clipped to norm `1.0` on 26–30 % of steps in the published runs. Prediction under (ii): **whitening
does not close it at the base budget**, and only the 10x extension — or nothing short of the exact
solve — does.

## 5. Differentiating measurement

For each of the six policies and each training arm, at the base budget and at 10x:

- **`d_learned` = `max |beta_arm - beta_tail_star|`**, where `beta_tail_star` is arm 3's exact solve
  on that policy's own training rows. This is the branch statistic.
- **`g_learned / g_star`**, the infinity-norm full-data gradient of the frozen objective at the
  arm's parameters over the same at `beta*`. Recorded, descriptive, deciding nothing — as in the
  diagnostic.
- **`d_objective` = `max |beta_tail_star - beta*|`** per policy, for the record. It cannot move
  between arms (section 2) and is not a branch.
- The whitening's realised `max |L L^T - G|` and `lambda_min(G)` per policy, and `kappa` per policy.
- One machine-generated **exposure line** over arms 1, 2, 4 and 5: per-coordinate displacement of
  the recovered `beta` from the frozen initialisation of the same seed and fold. Arm 3 has no
  optimizer trajectory and is excluded, which is stated in the record.

## 6. Reading rule — written before data, branches ordered by effect size

Thresholds, and how each follows from the published numbers:

- **`eps_L = 0.10`** for "closed". It is the same `epsilon` already frozen and applied in the
  training-target diagnostic, so it is not a new choice; and against today's `d_learned` of
  `0.951506`–`2.380056` it means the gap has been cut by at least a factor of `9.5` at the best
  policy and `23.8` at the worst. Applied as: **all six** policies below `eps_L`.
- **`rho = 5`** for "materially reduced", on the **median** `d_learned` across the six policies of
  the whitened arm against the raw arm at the same budget. Today's six `d_learned` values span a
  max/min ratio of `2.50`, so a factor-5 median reduction is outside anything the seed-and-fold
  scatter alone produces; and `1.838161 / 5 = 0.368`, still comfortably above `eps_L`, so `rho`
  names a genuinely intermediate effect that neither "closed" nor "no effect" can reach.

Branches, evaluated in this order — largest effect first; exactly one applies.

- **`O-A — CONDITIONING_CLOSES_IT`.** `WHITENED-BASE` has `d_learned < eps_L` for all six policies.
  Reading: mechanism (i). At the published budget, the entire learner shortfall on the linear arm is
  a coordinate-system effect; the exposure ladder's `R2-D` readings were reading a geometry problem.
- **`O-B — CONDITIONING_MOSTLY_CLOSES_IT`.** Not `O-A`, but the median `d_learned` of
  `WHITENED-BASE` is at most `1/rho` of `RAW-BASE`'s, **and** `WHITENED-10X` has `d_learned < eps_L`
  for all six. Reading: mechanism (i) with a rate qualifier — conditioning is the dominant cause and
  the budget is a secondary one.
- **`O-C — BUDGET_CLOSES_IT_NOT_CONDITIONING`.** `RAW-10X` has `d_learned < eps_L` for all six,
  while `WHITENED-BASE` does not reach the `rho` reduction. Reading: mechanism (ii). Geometry is not
  the binding constraint; the published budget simply was not enough, and the ladder's schedule
  invariance needs another explanation.
- **`O-D — NEITHER_CLOSES_IT`.** Neither `RAW-10X` nor `WHITENED-10X` has `d_learned < eps_L` for
  all six, while `EXACT-SOLVE` reaches the optimum by construction. Reading: the frozen `_step`
  package cannot reach its own objective's optimum on this design at ten times the published budget
  in either coordinate system. Neither mechanism as written is sufficient.
- **`O-E — UNCLEAR`.** Any other combination. Reading: report every number, name what is
  unexplained, and propose no successor object on the strength of an `O-E`.

Descriptive and deciding nothing: the gradient ratios, `d_objective`, the per-policy `kappa`, the
whitening residuals, the exposure line, and any per-seed spread. At three seeds no arm-comparison
polarity, stable-superiority or seed-population claim is available.

## 7. Launch conditions (spec §11.4) and claim ceiling

This is a `B/EXPLORE` object, so what may hold its launch is exactly:

- the central 4 GiB physical and effective memory admission, immediately before the workload;
- the §4 integrity items — group-disjoint folds, the odd-training / even-held-out separation, no
  read of B1 or audit runtime rows, fresh counter-addressed data, **and the whitening-from-training-
  rows-only requirement of section 3**;
- the §5.2 nonzero transition / update / evaluation counts, reconciled exactly;
- one machine-generated exposure line (section 5).

Recorded and never gating, as for the ladder: working-tree cleanliness of the bound source
inventory, the absence of a dedicated A/RECON performance assessment, resource telemetry (a failed
measurement sets `resources_unmeasured` and downgrades, it never annuls), and the exact-oracle
competence predicate. Learner-side instrumentation failure still quarantines under §6.2.

**Claim ceiling.** "On this exact finite eight-context host, on the linear `FT-XF-BC` tail objective,
with three seeds and two folds, whitening the design did / did not bring the frozen optimizer within
`eps_L` of its own objective's optimum at the published budget." This object says **nothing** about
competence, acquisition polarity, COUNT/RAW polarity, stable superiority, seed populations, the
`FT-XF-FLEX` arm (whose model includes a residual and whose optimum in `beta` is not defined), or
about variable `k`, variable `N`, MARL/UAV, transfer, safety, deployment, flight, energy or
real-world QoS. Closing `d_learned` is **not** competence: `d_objective` of `0.060`–`0.223` sits
between the objective's optimum and `beta*`, and X2 of the diagnostic showed that even the exact
optimum loses the oracle root vector in 2 of 6 folds.

## 8. Budget

Under **10 minutes** of wall time. Population generation for three seeds is `~15 s`; the six exact
solves and the whitening factorisations are milliseconds each; the training arms total
`6 policies x 2 arms x (160 + 1,600) = 21,120` steps of a 5-parameter linear model at batch 256,
which the published runs put at roughly `1.5 ms` per step, so `~35 s`. One resource preflight
immediately before the workload. Outputs under
`temp/directions/ucope/exp/optimiser_conditioning_r01_<date>/`.

## 9. What each branch means for the direction — including for the held discriminator

- **`O-A`** would identify the binding constraint precisely and cheaply, and would make a whitened
  variant of the tail fit the natural next object. It would also **answer the question the
  quarantined whitening discriminator `UCOPE-B-EXPLORE-FT-XF-BC-INVERTIBLE-CONDITIONING-DISCRIMINATOR-R01`
  was built to ask**, at a fraction of its cost and without its FP32 tolerance, which is why that
  object's result document is annotated to point here. Whether the discriminator is then repaired,
  superseded or retired stays an owner decision.
- **`O-B`** would say conditioning is dominant but not sufficient, and would put a joint
  conditioning-plus-budget object next — still answering the discriminator's question in the
  affirmative but with a rate caveat.
- **`O-C`** would clear conditioning of blame and move the direction to the batch schedule and the
  step rule: unshuffled cyclic windows and a clip that fires on a quarter of steps. It would also
  weaken the case for repairing the discriminator at all, since its question would have been
  answered negatively.
- **`O-D`** would be the most consequential: the frozen `_step` package cannot reach its own
  optimum on this design at ten times the published budget in either coordinate system, which would
  make the learner package — not the exposure, not the geometry — the direction's binding
  constraint, and would call the whole `FT-XF-BC` arm into question as an instrument.
- **`O-E`** would leave the question open with numbers attached and would argue against further
  spending on this family until a better hypothesis exists.

No branch supports `PARK`, promotion, retirement or a lifecycle change on its own.

## 10. Prediction requested from the owner

Please pick one before the run.

- **Option (i) — conditioning.** Whitening closes `d_learned` below `eps_L` at the base budget on
  all six policies, so the shortfall was a coordinate-system effect all along.
- **Option (ii) — optimiser or batch schedule.** Whitening does not close it at the base budget, and
  only the ten-fold extension or the exact solve reaches the optimum.
- **Option "both, in stated proportions".** Whitening produces a large but incomplete reduction —
  at least the factor `rho = 5` in the median — and the extension finishes the job; please state the
  proportion you expect between the two.
- **Option "neither / unclear".** Neither the whitened base nor the ten-fold extension closes it,
  or the picture is mixed enough that `O-E` is the honest outcome.

## 11. Predictions on record (added 2026-09-03; card body and reading rule unchanged)

Two predictions were recorded on 2026-09-03 (compliance note D.12, commit `66198aa32`), before the
object ran.

Owner:

> O-A (conditioning is the cause; whitening closes d_learned at the base budget)

Reviewer:

> O-B (whitening removes most of the gap, the clip and the unshuffled cyclic windows leave a
> residual that only the 10x budget closes)

This section records the predictions only. Nothing in sections 1-10 is altered: the arms, the
whitening contract, the measurements, the five branches and the thresholds `eps_L = 0.10` and
`rho = 5` stand exactly as frozen on 2026-09-03, and the branch is decided by those numbers alone.
Each prediction is judged afterwards, in the rule's own wording and against the numbers, in
`UCOPE_OPTIMISER_CONDITIONING_R01_RESULT_EVIDENCE_20260903.md`.
