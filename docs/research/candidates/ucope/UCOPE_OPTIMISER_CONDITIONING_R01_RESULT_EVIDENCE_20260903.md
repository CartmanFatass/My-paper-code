# UCOPE optimiser-and-conditioning R01 — result (2026-09-03)

Executed 2026-09-03 by Claude Code (Fable 5.1) against the object frozen in
`UCOPE_OPTIMISER_CONDITIONING_R01_CARD_20260903.md` under owner decision D.12 (commit
`815296414`), with both predictions recorded before the run (compliance note D.12, commit
`66198aa32`; card section 11).

**Question.** On the linear `FT-XF-BC` tail objective, does whitening the design close the learner's
gap to its own per-policy optimum, and does the exact solve reach it?

**Claim ceiling: `B/EXPLORE`.** A direct observation on the actually observed panel of 3 seeds x 2
folds on one arm. Nothing here establishes competence, acquisition polarity, COUNT/RAW polarity,
stable superiority, a seed-population effect, anything about `FT-XF-FLEX`, or anything about
variable `k`, variable `N`, MARL/UAV, transfer, safety, deployment or real-world QoS. Closing
`d_learned` is not competence.

| Fact | Value |
| --- | --- |
| Science object | `UCOPE-B-EXPLORE-OPTIMISER-CONDITIONING-R01` |
| Evidence class | `B/EXPLORE` |
| Launch commit sha (HEAD at launch) | `adbc42b515cc068e2437c2ed702edfd615a0bebf` |
| Bound source inventory | 14 files, aggregate `cd924be23817cdf9b90dddcb4e500af69c7dd5de00475a61ca1d8dbb17666440`; **not clean** — one entry, `?? scripts/run_ucope_optimiser_conditioning_r01.py`, the runner itself, untracked at launch and committed with this document. Recorded, not gating (§11.4) |
| Arm under test | `FT-XF-BC` (the only arm whose trained model *is* the frozen 5-term linear function) |
| Interpreter / libraries | `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`, Python 3.10.20, torch 2.7.0+cpu, CPU |
| Machine | `Windows-10-10.0.26200-SP0`, 16 logical CPUs |
| Topology (recorded, not gating) | `torch_intraop_threads = 4`, `torch_interop_threads = 1`, `deterministic_algorithms = true`, 1 process |
| Result root (gitignored) | `temp/directions/ucope/exp/optimiser_conditioning_r01_20260903/complete` |
| Branch published | **`O-B — CONDITIONING_MOSTLY_CLOSES_IT`**, `complete: true`, nothing quarantined |

---

## 1. Launch conditions

Still gating for this object, and all satisfied: the central 4 GiB admission; the §4 integrity items
including **whitening from the training rows only**; the §5.2 nonzero counts; one machine-generated
exposure line; §6.2 quarantine on learner-side failure. Recorded and never gating: working-tree
cleanliness of the bound source inventory, the absence of a dedicated A/RECON performance
assessment, execution topology, and the exact-oracle competence predicate.

**Resource admission**, run immediately before any RNG master, model or optimizer existed; receipt
at `temp/directions/ucope/exp/optimiser_conditioning_r01_20260903/preflight.json`:

| Field | Value |
| --- | --- |
| `available_physical_bytes` | `12,220,616,704` (11.38 GiB) |
| `effective_available_bytes` | `12,220,616,704` (11.38 GiB) |
| `minimum_available_bytes` | `4,294,967,296` |
| `physical_floor_pass` / `effective_floor_pass` / `passed` | `true` / `true` / `true` |

## 2. Command actually run

```
git rev-parse HEAD
  -> adbc42b515cc068e2437c2ed702edfd615a0bebf

C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/run_ucope_optimiser_conditioning_r01.py run \
  --output-root temp/directions/ucope/exp/optimiser_conditioning_r01_20260903 --thread-cap 4
  -> {"branch": "O-B", "label": "CONDITIONING_MOSTLY_CLOSES_IT",
      "path": ".../optimiser_conditioning_r01_20260903/complete/run-record.json"}
```

Unit checks for the object's own machinery — batch indexing against the frozen
`training._cyclic_batch`, the whitening contract and its refusal, the reparameterisation algebra,
the exact solve, and all five branches in their stated order:
`tests/experiments/candidates/ucope/test_optimiser_conditioning_r01.py`, **14 passed**.

## 3. Work accounting — declared versus actual

| Quantity | Declared | Actual |
| --- | --- | --- |
| Policies | 6 (3 seeds x 2 folds) | 6 |
| Training arms | 2 per policy (`RAW`, `WHITENED`) | 12 runs |
| Episodes generated | 122,880 | 122,880 |
| Tail rows fitted | 10,240 per policy | 61,440 |
| Tail optimizer updates | 1,600 x 12 = 19,200 | 19,200 |
| Tail example exposures | 19,200 x 256 = 4,915,200 | 4,915,200 |
| Exact solves (`EXACT-SOLVE`) | 6 | 6 |
| Non-finite events | 0 | 0 |
| Gradient clipping events | — | 1,148 of 19,200 (5.98 %) |
| Wall / CPU | — | `23.943 s` / `30.500 s` |

Every §5.2 count is nonzero and reconciles exactly. The card's budget was "under 10 minutes"; the
run took 24 seconds.

## 4. The whitening integrity item, checked and recorded before any training

Computed from the training rows only — the same `_canonical_rows(population, fold=fold, tail=True)`
the learner trains on — at float64, and checked before any optimizer existed.

| Seed | Fold | `kappa` | `lambda_min(G)` | `max abs(L L^T - G)` | tolerance | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| `00` | 0 | 716.655 | 2.657409e-03 | 0.000e+00 | 1e-10 | pass |
| `00` | 1 | 714.821 | 2.652845e-03 | 5.551e-17 | 1e-10 | pass |
| `01` | 0 | 717.261 | 2.664207e-03 | 0.000e+00 | 1e-10 | pass |
| `01` | 1 | 714.483 | 2.658456e-03 | 5.551e-17 | 1e-10 | pass |
| `02` | 0 | 736.646 | 2.605638e-03 | 0.000e+00 | 1e-10 | pass |
| `02` | 1 | 721.144 | 2.627766e-03 | 5.551e-17 | 1e-10 | pass |

Every reconstruction residual is at or below `5.551e-17` — three to four orders of magnitude below
the `O(kappa * eps_fp64) ~= 1.6e-13` the card predicted and seven orders below the `1e-10` ceiling,
and `lambda_min` is three orders above the `1e-6` floor. The move to float64 with a
condition-number-derived tolerance did exactly what it was meant to do: the numerical contract that
quarantined the whitening discriminator at `9.12e-06`–`9.69e-06` against a `3.81e-06` FP32 ceiling
is not close to binding here.

## 5. `d_objective` — for the record, not a branch

| Seed | Fold | `beta_tail_star` | `d_objective` | `g_star` |
| --- | --- | --- | --- | --- |
| `00` | 0 | (0.214489, 0.630125, 1.566774, −1.168853, −0.996194) | 0.216774 | 5.546346e-02 |
| `00` | 1 | — | 0.168532 | 1.584245e-02 |
| `01` | 0 | — | 0.180732 | 8.581194e-03 |
| `01` | 1 | — | 0.060108 | 1.826036e-02 |
| `02` | 0 | — | 0.172426 | 1.130948e-02 |
| `02` | 1 | — | 0.222610 | 3.674431e-02 |

These reproduce the accepted diagnostic's values to every printed digit, which is the expected
consequence of whitening being a bijective reparameterisation: it cannot move the objective's
optimum, only the trajectory. The gradient at the exact solve is `1.7e-15`–`5.5e-15`.

## 6. `d_learned` per arm per policy, at both budgets

`d_learned = max abs(beta_arm − beta_tail_star)`, with the whitened arm's parameters mapped back to
raw coordinates by `beta = L^-T beta_tilde`. `EXACT-SOLVE` is `0` by construction and trains nothing.

| Seed | Fold | `RAW-BASE` | `WHITENED-BASE` | `RAW-10X` | `WHITENED-10X` |
| --- | --- | --- | --- | --- | --- |
| `00` | 0 | 1.962464 | 0.443187 | 1.679417 | **0.066387** |
| `00` | 1 | 1.727622 | 0.191550 | 1.190367 | **0.038564** |
| `01` | 0 | **2.398713** | **1.183038** | 1.337028 | **0.010220** |
| `01` | 1 | 1.954234 | **0.062445** | 1.618013 | **0.079964** |
| `02` | 0 | 1.628449 | 0.504468 | 1.089411 | **0.043541** |
| `02` | 1 | 0.951967 | 0.212877 | **0.674283** | **0.019356** |
| **median** | | **1.840928** | **0.328032** | 1.263698 | 0.041053 |

Bold marks the extreme of each column, plus every value below `eps_L = 0.10`.

Gradient ratios `g_learned / g_star`, computed in **raw** coordinates for both arms so they are
comparable — recorded, descriptive, deciding nothing:

| Seed | Fold | `RAW-BASE` | `WHITENED-BASE` | `RAW-10X` | `WHITENED-10X` |
| --- | --- | --- | --- | --- | --- |
| `00` | 0 | 1.51 | 18.49 | 0.34 | 0.08 |
| `00` | 1 | 21.41 | 20.38 | 1.08 | 0.28 |
| `01` | 0 | 104.24 | 281.86 | 0.85 | 0.17 |
| `01` | 1 | 4.27 | 0.40 | 0.92 | 0.20 |
| `02` | 0 | 16.25 | 19.02 | 1.26 | 0.22 |
| `02` | 1 | 2.04 | 15.54 | 0.12 | 0.05 |

Note that a whitened-base ratio can exceed the raw one (`281.86` at `01`/0) while its `d_learned` is
half the raw arm's: the raw-coordinate gradient is dominated by the design's fast directions, so it
is a poor proxy for distance on an ill-conditioned design. That is a reason the branch statistic is
`d_learned` and not the gradient.

Clipping events per 1,600 updates: raw `0`–`159`, whitened `0`–`407`. The whitened arm clips more
often, as expected — the clip acts on a norm measured in whitened coordinates (card section 2).

## 7. The exposure line (a launch condition, §11.4)

Per-coordinate displacement of the recovered Bellman vector from the exact deterministic
initialisation of the same seed and fold. `EXACT-SOLVE` has no optimizer trajectory and is excluded,
as the card states.

| Arm | rows | min `max_abs_coordinate_move` | max |
| --- | --- | --- | --- |
| `RAW-BASE` | 6 | 0.250245 | 0.495109 |
| `WHITENED-BASE` | 6 | 1.164076 | 2.039941 |
| `RAW-10X` | 6 | 0.602027 | 1.599347 |
| `WHITENED-10X` | 6 | 1.290966 | 2.080848 |

`learner_can_move_in_its_budget = true` (minimum over all 24 rows is `0.250245 > 0`).

This table carries the mechanism in one line. AdamW's per-step per-coordinate move is bounded by
approximately the learning rate, so the raw arm's per-coordinate travel ceiling at the base budget is
`160 x 3e-3 = 0.48` — and `RAW-BASE`'s observed moves are `0.250`–`0.495`, sitting exactly at that
ceiling. The distance from the frozen initialisation to `beta_tail_star` is `1.276`–`2.088`, so the
raw arm at the base budget **arithmetically cannot** arrive, whatever else is true. The whitened arm
at the same 160 steps moves the recovered vector by `1.164`–`2.040`, two to four times the raw
ceiling, because the recovery `beta = L^-T beta_tilde` amplifies the whitened step along the design's
slow directions by up to `1/sqrt(lambda_min) ~= 19.6`. Conditioning does not merely reorder the
descent; it changes how far the same budget can travel in the coordinates that matter.

## 8. The reading rule applied verbatim, in its stated order

Card section 6, thresholds frozen there: `eps_L = 0.10`, `rho = 5` on the median.

1. **`O-A — CONDITIONING_CLOSES_IT`**: fires if `WHITENED-BASE` has `d_learned < eps_L` for **all
   six** policies. Observed: one of six (`01`/1, `0.062445`); the other five are `0.191550`,
   `0.212877`, `0.443187`, `0.504468`, `1.183038`. **Does not fire.**
2. **`O-B — CONDITIONING_MOSTLY_CLOSES_IT`**: fires if the median `d_learned` of `WHITENED-BASE` is
   at most `1/rho` of `RAW-BASE`'s **and** `WHITENED-10X` has `d_learned < eps_L` for all six.
   Observed: median `1.840928 → 0.328032`, a reduction factor of **`5.612037 >= 5`**, so the
   reduction condition is met; and `WHITENED-10X` is `0.010220`, `0.019356`, `0.038564`, `0.043541`,
   `0.066387`, `0.079964` — **all six below `0.10`**. **Fires.**

Branch: **`O-B`**. Its registered reading, verbatim: *"mechanism (i) with a rate qualifier —
conditioning is the dominant cause and the budget is a secondary one."*

One further number, which the rule does not use but which sharpens the reading: `RAW-10X` is
`0.674283`–`1.679417`, so **none** of the six policies closes on budget alone. Ten times the
published budget without whitening leaves the gap essentially intact (median `1.840928 → 1.263698`,
a factor of `1.46`), while whitening at one tenth of that budget already achieves `5.61`. The two
factors are not substitutes: on this design whitening is necessary, and given whitening the extra
budget is also necessary.

## 9. Verdict on each prediction

**Owner — `O-A` (conditioning is the cause; whitening closes `d_learned` at the base budget):
CONTRADICTED**, both by the rule's wording and by the numbers. The rule assigns `O-B`, not `O-A`,
because `O-A` requires all six policies below `eps_L` at the base budget and only one is. By the
numbers the shortfall is a factor of `11.8` at the worst policy (`1.183038` against `0.10`). The
prediction's *direction* is right — conditioning is the dominant cause, which is what `O-B` says —
but its *strength* is not: the base budget is not enough even in whitened coordinates.

**Reviewer — `O-B` (whitening removes most of the gap, the clip and the unshuffled cyclic windows
leave a residual that only the 10x budget closes): SUPPORTED**, by the rule's wording — the branch
is exactly `O-B` — and by the numbers: whitening removes `82.2 %` of the median gap at the base
budget (`1.840928 → 0.328032`), and the residual is closed only at `1,600` updates, where all six
policies land below `eps_L`.

One qualification is owed to the reviewer's stated causal attribution. `O-B` establishes that a
residual remains after whitening at the base budget and that ten times the budget closes it. It does
**not** establish that the clip and the unshuffled cyclic windows are what leave that residual: this
object never varied the clip or the batch order, and section 7 offers a simpler sufficient
explanation — at 160 steps even the whitened arm is close to its own travel ceiling for the distance
it must cover. Attributing the residual specifically to the clip or the schedule would need an
object that varies them, and that is not what ran.

## 10. Deviations

1. **The whitened design is materialised at float64 and cast to float32** to enter the frozen
   `_step` loop, whose scorer requires FP32 (`model.py:91`). The Gram, the Cholesky, the contract
   check, the recovery `beta = L^-T beta_tilde` and every reported statistic are float64, as carded;
   only the batch tensors cross into FP32, exactly as the published path's do.
2. **The training arms index precomputed full-row tensors** rather than rebuilding each batch from
   `Episode` rows. `_cyclic_indices` reproduces `training._cyclic_batch`'s arithmetic and is pinned
   to it by a test at updates `0, 1, 3, 7, 159, 1599`, so the batch schedule is the frozen one.
3. **Arms 4 and 5 are the base loops continued, implemented as one 1,600-step run per arm
   snapshotted at 160**, not as two separate runs. Deterministic and identical in trajectory to a
   restart-from-snapshot, and cheaper; the card's wording ("continued to 1,600") is satisfied.
4. **The bound source inventory was not clean at launch**: one entry, `?? scripts/run_ucope_optimiser_conditioning_r01.py`
   — the runner itself, untracked at the moment of the run and committed alongside this document.
   Working-tree cleanliness is recorded and not gating under §11.4. The 14-file inventory with
   per-file digests and the aggregate is in the record.
5. **Gradient ratios are computed in raw coordinates for both arms**, so the two arms are
   comparable. The whitened arm's gradient in its own coordinates is not reported; section 6 explains
   why the ratio is descriptive only.
6. **`EXACT-SOLVE` is excluded from the exposure line**, as the card specifies: it has no optimizer
   trajectory.

## 11. Could not verify

- Whether the residual left by whitening at the base budget is caused by the gradient clip or by the
  unshuffled cyclic batch order specifically. Neither was varied; see section 9.
- Whether some budget between `160` and `1,600` updates suffices in whitened coordinates. Only the
  two carded budgets were measured.
- Anything about `FT-XF-FLEX`. Its model includes a 4,865-coordinate residual, its optimum in `beta`
  alone is undefined, and it was not run.
- Whether closing `d_learned` produces competence. It cannot follow from this object: `d_objective`
  is unchanged at `0.060`–`0.223`, and the diagnostic showed that even the exact optimum loses the
  oracle root vector in 2 of 6 folds.
- Anything about the whitening discriminator itself, which is owner-held, quarantined, and was
  neither read nor run here.
- Anything outside this frozen eight-context host and this one arm.

## 12. What the branch means for the direction — options for the owner, not a decision

`O-B` says the learner's failure to reach its own objective's optimum is dominantly a
coordinate-system effect, with a budget component that only shows up once the geometry is fixed.
The exposure ladder's `R2-D` readings were, on this arm, reading a geometry problem.

1. **A whitened tail-fit object.** Replace the raw tail fit with the whitened one inside the frozen
   learner and re-run the competence criterion. This is the direct successor and the cheapest test of
   whether the direction's competence question was ever about exposure at all. Note it will not move
   `d_objective`, so the sample-size question from the diagnostic remains separate.
2. **A joint conditioning-plus-budget object.** `O-B`'s registered reading names the budget as a
   secondary cause; an object that sweeps the budget in whitened coordinates would locate the knee
   between `160` and `1,600` and put a number on "how much budget conditioning buys back".
3. **A clip-and-schedule object.** Section 9's qualification is a real gap: nothing here separates
   the clip from the batch order. If the owner wants the reviewer's causal claim tested rather than
   inferred, this is the object that does it.
4. **For the held discriminator `UCOPE-B-EXPLORE-FT-XF-BC-INVERTIBLE-CONDITIONING-DISCRIMINATOR-R01`:**
   its scientific question — is conditioning what keeps the `FT-XF-BC` learner from its target — has
   now been answered **yes, dominantly**, at 24 seconds of compute, with an FP64 contract that passed
   by seven orders of magnitude where its FP32 ceiling failed by a factor of `2.4`–`2.5`. The options
   are to retire it as superseded, to repair its tolerance and run it anyway as an independent
   confirmation, or to leave it quarantined and unconsumed. This document takes none of those steps
   and its quarantine is untouched.
5. **Stop here.** `O-B` is a clean, cheap, interpretable answer; the direction could bank it and
   spend the next budget on the competence criterion rather than on the optimizer.

No branch of this object supports `PARK`, promotion, retirement or any lifecycle change on its own.
