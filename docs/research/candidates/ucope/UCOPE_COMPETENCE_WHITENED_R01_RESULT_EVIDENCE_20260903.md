# UCOPE competence (whitened learner) R01 — result (2026-09-03)

Executed 2026-09-03 by Claude Code (Fable 5.1) against the object frozen in
`UCOPE_COMPETENCE_WHITENED_R01_CARD_20260903.md` under owner decision D.14 (commit `bc35a9abd`),
with both predictions recorded before the run (compliance note D.14, commit `953e5e310`; card
section 11) and with `n = 81,920` tail rows per policy fixed in the card's section 3 before any
learner existed.

**Question.** With conditioning and sample-size variance both handled, does the whitened linear
`FT-XF-BC` learner reach competence on this host?

**Claim ceiling: `B/EXPLORE`.** A direct observation on the actually observed panel of 3 seeds x 2
folds of one arm on one frozen eight-context host. Nothing here establishes acquisition polarity,
COUNT/RAW polarity, stable superiority, a seed-population effect, anything about `FT-XF-FLEX`, or
anything about variable `k`, variable `N`, MARL/UAV, transfer, safety, deployment, flight, energy or
real-world QoS. Three competent policies out of six are **not** a competence claim about the
direction, and the `EXACT-SOLVE` ceiling is not a learner.

| Fact | Value |
| --- | --- |
| Science object | `UCOPE-B-EXPLORE-COMPETENCE-WHITENED-R01` |
| Evidence class | `B/EXPLORE` |
| Launch commit sha (HEAD at launch) | `19eeb9338e43f3b8fc9e93cfe4ec8d500dcabfba` |
| Bound source inventory | 15 files, aggregate `18b3a1f585a040dbaf65d5f21cba878c3685d298040c4ebd644be054ab7ba772`; **not clean** — one entry, `?? scripts/run_ucope_competence_whitened_r01.py`, the runner itself, untracked at launch and committed as `b21fb61f5`. Recorded, not gating (§11.4) |
| Arm under test | `FT-XF-BC` (the only arm whose trained model *is* the frozen 5-term linear function) |
| Rows | `n = 81,920` tail rows and `163,840` root rows per policy, at the card's fresh index law |
| Budget | `lr 3e-3`, batch 256, **1,600 tail and 3,200 root updates** (ten times the frozen rung-1 budget) |
| Interpreter / libraries | `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`, Python 3.10.20, torch 2.7.0+cpu, CPU |
| Machine | `Windows-10-10.0.26200-SP0`, 16 logical CPUs |
| Topology (recorded, not gating) | `torch_intraop_threads = 4`, `torch_interop_threads = 1`, `deterministic_algorithms = true`, 1 process |
| Result root (gitignored) | `temp/directions/ucope/exp/competence_whitened_r01_20260903/complete` |
| Branch published | **`C-C — CEILING_COMPETENT_LEARNER_NOT`**, `complete: true`, nothing quarantined |

---

## 1. Launch conditions

Still gating for this object, and all satisfied: the central 4 GiB physical and effective memory
admission immediately before the workload; the §4 integrity items — group-disjoint folds, the
odd-training / even-held-out separation, no read of B1 or audit runtime rows, fresh
counter-addressed data at the index law of card section 3, and **whitening from training rows only,
per stage**; the §5.2 nonzero counts reconciled exactly; one machine-generated exposure line; §6.2
quarantine on learner-side failure (not triggered). Recorded and never gating: working-tree
cleanliness of the bound source inventory, the absence of a dedicated A/RECON performance
assessment, execution topology, and the direction's acquisition and COUNT/RAW sequencing locks.

**Resource admission**, run before any RNG master, model or optimizer existed; receipt at
`temp/directions/ucope/exp/competence_whitened_r01_20260903/preflight.json`:

| Field | Value |
| --- | --- |
| `available_physical_bytes` | `12,714,844,160` (11.84 GiB) |
| `effective_available_bytes` | `12,714,844,160` (11.84 GiB) |
| `minimum_available_bytes` | `4,294,967,296` |
| `physical_floor_pass` / `effective_floor_pass` / `passed` | `true` / `true` / `true` |
| `measurement_source` / `assessed_at` | `GlobalMemoryStatusEx` / `2026-09-03T10:30:34.481794Z` |

**Index law, as carded.** Episodes at `i = OFFSET + j`, `OFFSET = 1,000,000`, `j = 0 .. 40,959`.
`OFFSET % 20 == 0`, so the 10-episode behaviour stratum and the 20-episode fold alternation start in
the phase they have at index 0; the published ranges `0..5,119` and `0..319` are disjoint from it,
and every host draw is counter-addressed on `(namespace, seed, episode_index, counter)`. The runner
re-asserted fold balance, behaviour-stratum balance and `K_train` period support and balance on the
fresh range for each seed before any design was built.

**Whitening contract, checked per stage before any optimizer step existed** (float64):

| Policy | tail `kappa` | tail `lambda_min(G)` | tail `max abs(LL^T - G)` | root `kappa` | root `lambda_min(G)` | root `max abs(LL^T - G)` |
| --- | --- | --- | --- | --- | --- | --- |
| seed 00 fold 0 | 726.199 | 2.620428e-03 | 0.000e+00 | 5014.086 | 3.083845e-04 | 2.776e-17 |
| seed 00 fold 1 | 724.061 | 2.620676e-03 | 5.551e-17 | 5014.086 | 3.083845e-04 | 2.776e-17 |
| seed 01 fold 0 | 721.061 | 2.644066e-03 | 0.000e+00 | 5014.086 | 3.083845e-04 | 2.776e-17 |
| seed 01 fold 1 | 732.927 | 2.599248e-03 | 5.551e-17 | 5014.086 | 3.083845e-04 | 2.776e-17 |
| seed 02 fold 0 | 729.342 | 2.603292e-03 | 0.000e+00 | 5014.086 | 3.083845e-04 | 2.776e-17 |
| seed 02 fold 1 | 722.165 | 2.638062e-03 | 5.551e-17 | 5014.086 | 3.083845e-04 | 2.776e-17 |

Every value clears the frozen contract by orders of magnitude: the reconstruction error is at most
`5.551e-17` against the `1e-10` tolerance, and `lambda_min` at least `3.08e-04` against `1e-06`.
The tail `kappa` values sit exactly where the `n` selection recorded them (`726.199` at seed 00 fold
0), confirming again that `n` bought variance and not conditioning. The **root** design is
substantially worse conditioned than the tail — `kappa = 5014.086`, identical across all six
policies because the root design's rows are a fixed multiset of eight context vectors crossed with
the behaviour strata — which is a fact this chain had never measured, every previous object having
examined the tail head only.

## 2. Commands actually run

```
git rev-parse HEAD
  -> 19eeb9338e43f3b8fc9e93cfe4ec8d500dcabfba

C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/run_ucope_competence_whitened_r01.py run \
  --output-root temp/directions/ucope/exp/competence_whitened_r01_20260903 --thread-cap 4
  -> {"branch": "C-C", "label": "CEILING_COMPETENT_LEARNER_NOT",
      "exact_competent": 6, "whitened_competent": 3, "raw_competent": 0,
      "path": ".../competence_whitened_r01_20260903/complete/run-record.json"}
```

Unit checks for the object's own machinery — the carded constants, the index law, the canonical
`(episode_index, context_id)` row order, the batch windows against the frozen
`training._cyclic_batch`, the 9-dimensional feature construction against `model.x_features`, both
designs against the `n` selection's, both root-target precisions against the frozen scorer
arithmetic and the `n` selection's package, the whitening contract, its refusal on a rank-deficient
design, the reparameterisation recovery identity, and all five branches in their stated order, plus
one end-to-end miniature run:

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q \
  tests/experiments/candidates/ucope/test_competence_whitened_r01.py \
  --basetemp C:/Projects/HMASD/temp/pytest_ucope_competence_whitened_r01b
  -> 31 passed in 6.64s
```

## 3. Work accounting — declared versus actual

| Quantity | Declared | Actual |
| --- | --- | --- |
| Policies | 6 (3 seeds x 2 folds) | 6 |
| Training arms | 2 per policy (`WHITENED-10X`, `RAW-10X`) | 12 runs |
| Episodes generated | `40,960 x 8 x 3 = 983,040` | 983,040 |
| Tail rows fitted | 81,920 per policy | 491,520 |
| Root rows fitted | 163,840 per policy | 983,040 |
| Tail optimizer updates | `1,600 x 12 = 19,200` | 19,200 |
| Root optimizer updates | `3,200 x 12 = 38,400` | 38,400 |
| Tail example exposures | `19,200 x 256 = 4,915,200` | 4,915,200 |
| Root example exposures | `38,400 x 256 = 9,830,400` | 9,830,400 |
| Exact solves (`EXACT-SOLVE`) | 12 (tail and root, 6 policies) | 12 |
| Exact policy evaluations | `8 contexts x 3 arms x 6 policies = 144` | 144 |
| Sampled evaluation episodes | `64 x 8 x 3 x 6 = 9,216` | 9,216 |
| Sampled evaluation transitions | — | 25,344 |
| Non-finite events | 0 | 0 |
| Gradient clipping events | — | 2,732 of 57,600 (4.74 %) |
| Wall / CPU | under 15 minutes | `110.970 s` / `126.078 s` |

Every §5.2 count is nonzero and reconciles exactly with the declaration.

## 4. The competence predicate, per arm and per policy

`C_even` is the frozen predicate, unchanged: `all_scores_finite AND all_choices_unique AND
exact_eight_context_oracle_root_vector AND max_expected_regret <= 1/50 AND
min_forced_PROBE_tail_agreement >= 19/20`, on even held-out support `K_eval = {2,4,6,8}` at the
final root update. Gates: regret `<= 0.02`, agreement `>= 0.95`. Its five components:

### `WHITENED-10X`

| Policy | finite | unique | oracle root | max regret | min tail agreement | `C_even` |
| --- | --- | --- | --- | --- | --- | --- |
| seed 00 fold 0 | true | true | true | 0.003155 | **0.611559** | **fail** |
| seed 00 fold 1 | true | true | true | 0.003155 | **0.611559** | **fail** |
| seed 01 fold 0 | true | true | true | 0.000000 | 1.000000 | **pass** |
| seed 01 fold 1 | true | true | true | 0.000000 | 1.000000 | **pass** |
| seed 02 fold 0 | true | true | **false** | **0.033103** | **0.520727** | **fail** |
| seed 02 fold 1 | true | true | true | 0.000000 | 1.000000 | **pass** |

**3 of 6 competent.** The binding component is the **forced-PROBE tail agreement**: it fails in all
three failures, whereas the oracle root vector fails once and the regret gate once, both in the same
policy (seed 02 fold 0). No policy fails on finiteness or uniqueness.

### `RAW-10X` (control; never a comparator for a claim)

| Policy | finite | unique | oracle root | max regret | min tail agreement | `C_even` |
| --- | --- | --- | --- | --- | --- | --- |
| seed 00 fold 0 | true | true | false | 0.021437 | 0.000000 | fail |
| seed 00 fold 1 | true | true | false | 0.098532 | 0.000000 | fail |
| seed 01 fold 0 | true | true | false | 0.021437 | 0.000000 | fail |
| seed 01 fold 1 | true | true | false | 0.021437 | 0.000000 | fail |
| seed 02 fold 0 | true | true | true | 0.048000 | 0.000000 | fail |
| seed 02 fold 1 | true | true | false | 0.021437 | 0.000000 | fail |

**0 of 6 competent**, every one of them failing the agreement gate outright at `0.000000`.

### `EXACT-SOLVE` (ceiling; outcome-free, no optimizer trajectory)

All six policies: finite `true`, unique `true`, oracle root `true`, max regret `0.000000`, min tail
agreement `1.000000` — **6 of 6 competent**, every component at its perfect value.

## 5. `d_learned`, `d_objective`, and the gradient ratios

`d_learned = max abs(beta_arm - beta_star_policy)` against `eps_L = 0.10`, per stage;
`d_objective = max abs(beta_tail_star - beta*)`, which cannot differ between arms.

| Policy | `d_objective` | `d_learned` tail W | `d_learned` tail R | `d_learned` root W | `d_learned` root R |
| --- | --- | --- | --- | --- | --- |
| seed 00 fold 0 | 0.011638 | 0.095253 | 1.510012 | 0.207066 | 0.327753 |
| seed 00 fold 1 | 0.046433 | 0.052249 | 1.095268 | 0.294404 | 1.318556 |
| seed 01 fold 0 | 0.030209 | 0.034964 | 1.206325 | 0.271799 | 0.669768 |
| seed 01 fold 1 | 0.023380 | 0.029579 | 1.593731 | 0.101065 | 0.327380 |
| seed 02 fold 0 | 0.037303 | 0.183077 | 1.203085 | 0.083938 | 0.774985 |
| seed 02 fold 1 | 0.013271 | 0.027485 | 0.877095 | 0.027560 | 1.021626 |
| **median** | — | **0.043607** | **1.204705** | **0.154066** | **0.722377** |
| **within `eps_L`** | 6 of 6 `<= 0.10` | **5 of 6** | **0 of 6** | **2 of 6** | **0 of 6** |

`d_objective` reproduces the `n` selection's per-policy values exactly (`0.011638, 0.046433,
0.030209, 0.023380, 0.037303, 0.013271`), which is an independent confirmation that the run drew the
same rows the selection did.

Gradient ratios `g_learned / g_star` in raw coordinates, where `g_star` is the tail objective's
infinity-norm gradient at `beta*` (`0.017030, 0.005515, 0.003400, 0.004648, 0.006732, 0.003559`):

| Policy | `WHITENED-10X` | `RAW-10X` |
| --- | --- | --- |
| seed 00 fold 0 | 1.104990 | 0.451407 |
| seed 00 fold 1 | 2.742960 | 4.466211 |
| seed 01 fold 0 | 0.549143 | 2.105910 |
| seed 01 fold 1 | 3.316532 | 6.473777 |
| seed 02 fold 0 | 0.754227 | 1.368204 |
| seed 02 fold 1 | 1.697742 | 5.652467 |

These are **descriptive and decide nothing**, for the reason section 6 of the conditioning result
gives: `g_star` is the gradient at a point that is not the empirical optimum, so the ratio mixes the
learner's residual with the sampling offset between `beta*` and `beta_tail_star`, and at these
magnitudes (`3e-3` to `1.7e-2`) it is dominated by the latter.

## 6. Whitening numbers and the exposure line

Whitening numbers are in section 1. The **exposure line** is machine-generated over the two learner
arms; the `EXACT-SOLVE` arm has no optimizer trajectory and is excluded by construction. It reports,
per arm and stage, the per-coordinate displacement of the recovered raw Bellman vector from the exact
deterministic initialisation of the same seed and fold.

| Arm / stage | min `max abs` coordinate move | median | max |
| --- | --- | --- | --- |
| `WHITENED-10X` tail | 1.478948 | 1.855126 | 2.034672 |
| `WHITENED-10X` root | 0.818056 | 1.142267 | 1.955352 |
| `RAW-10X` tail | 0.629338 | 1.011536 | 1.613547 |
| `RAW-10X` root | 0.583103 | 0.877235 | 1.523629 |

Global minimum `0.583103`, global maximum `2.034672`; the learner can move in its budget in every one
of the 24 rows, so the launch condition on the exposure line is satisfied. The raw per-coordinate
ceiling at this budget is `1,600 x 3e-3 = 4.8` on the tail and `3,200 x 3e-3 = 9.6` on the root,
against observed maxima of `2.034672` and `1.955352` — so, unlike the base-budget conditioning run
where the raw arm sat exactly at its ceiling, **no arm is step-budget-bound here**. The whitened arm moves further than the raw arm in every stage (median
`1.855` vs `1.012` on the tail), which is the expected consequence of `norm(L^-1) ~ 1/sqrt(lambda_min)`
mapping a bounded whitened step onto a larger raw displacement.

Gradient clipping, at the frozen norm `1.0`:

| Arm | tail clips / 9,600 | root clips / 19,200 |
| --- | --- | --- |
| `WHITENED-10X` | 801 (8.34 %) | 1,054 (5.49 %) |
| `RAW-10X` | 352 (3.67 %) | 525 (2.73 %) |

Whitening roughly **doubles** the clipping rate on both stages, consistent with the conditioning
object's observation that the clip acts in whitened norm.

## 7. The rule applied verbatim, in its stated order

The card's section 7, quoted, with the deciding numbers.

> - **`C-A — WHITENED_LEARNER_COMPETENT`.** `WHITENED-10X` satisfies `C_even` in **all six**
>   policies.

Not satisfied. `WHITENED-10X` satisfies `C_even` in **3** of 6 policies
(`[false, false, true, true, false, true]`).

> - **`C-B — WHITENED_MAJORITY_CEILING_CLEAN`.** Not `C-A`, but `WHITENED-10X` is competent in **at
>   least four** of six **and** `EXACT-SOLVE` is competent in all six.

Not satisfied. The second conjunct holds — `EXACT-SOLVE` is competent in all six — but the first
does not: **3 < 4**, the majority threshold fixed in the card as "at least 4 of 6".

> - **`C-C — CEILING_COMPETENT_LEARNER_NOT`.** `EXACT-SOLVE` competent in all six, `WHITENED-10X`
>   competent in fewer than four.

**Satisfied.** `EXACT-SOLVE` competent in **6 of 6**; `WHITENED-10X` competent in **3**, which is
fewer than four. **This is the published branch.**

> Reading: mechanism (ii). The objective, the geometry and the sample size are all sufficient and the
> **learner** is the binding constraint; the root learner, the clip and the batch order are the named
> suspects.

The later branches were not reached: `C-D` requires `EXACT-SOLVE` not competent in all six (it is
competent in all six), and `C-E` is the residue of the four named branches.

**Branch published: `C-C — CEILING_COMPETENT_LEARNER_NOT`.**

## 8. Verdict on the recorded predictions

**Owner — "unclear (an exploration run without a calibration point)".** As the card states, the
owner's prediction is "unclear" and therefore **carries no verdict**. Recorded without one.

**Reviewer — "C-B (a majority of folds competent but not all six, because the competence predicate
is tight and the whitened learner's residual to the exact solve will cross it in at least one
fold)".**

*By the rule's wording:* **not borne out.** The rule's `C-B` requires `WHITENED-10X` competent in at
least four of six; it is competent in three. The branch is `C-C`.

*By the numbers:* partly right and partly wrong, and the split is informative.

- Right: "**not all six**" — 3 of 6, not 6 of 6.
- Right: "**the competence predicate is tight**" and "**the whitened learner's residual to the exact
  solve will cross it**" — the residual does cross it, and it crosses on exactly the component the
  reviewer's word "tight" points at. Five of six policies have tail `d_learned <= eps_L = 0.10`, and
  two of those five (seed 00, both folds, at `0.095253` and `0.052249`) still fail `C_even` on the
  agreement gate. Being inside `eps_L` does **not** imply clearing the predicate.
- Right about direction, wrong about degree: "in **at least one** fold" understates it — the residual
  crossed the predicate in **three** folds, which is what moved the branch from `C-B` to `C-C`.
- Wrong: "**a majority of folds competent**". Three of six is exactly half, not a majority under the
  card's threshold of at least four.

## 9. Post-hoc descriptive supplement — which context binds (decides nothing)

Not part of the run record and not part of the rule; a recomputation from the recorded `beta_tail`
values, reported because branch `C-C` names the learner as the next subject and this localises it.
`minimum_tail_agreement` is a minimum over eight contexts. For each `WHITENED-10X` failure the
binding context is the same one:

| Policy | min agreement | binding context | contexts below 0.95 |
| --- | --- | --- | --- |
| seed 00 fold 0 | 0.611559 | `LINKED-p17_20-c9_100` | 2 of 8 |
| seed 00 fold 1 | 0.611559 | `LINKED-p17_20-c9_100` | 2 of 8 |
| seed 02 fold 0 | 0.520727 | `LINKED-p17_20-c9_100` | 2 of 8 |

`LINKED-p17_20-c9_100` is the direction's `TARGET_CONTEXT_ID`. Every `RAW-10X` failure instead binds
at `SEVERED-p13_20-c9_100` with agreement exactly `0.000000`, and 6-to-8 of its eight contexts fall
below the gate — the all-or-nothing behaviour of the `SEVERED` contexts (belief pinned at `1/2`)
recorded in the instrumentation check. Seed 00's two folds produce the *identical* agreement
`0.611559` despite training on complementary row sets; this is a coincidence of the discrete argmax
pattern over `K_eval`, not a shared quantity, and is noted only so it is not read as a bug.

## 10. Deviations from the card

1. **Two precisions for the root target package.** The card names one package
   (`probe_primitive + max over K_TRAIN of Q_tail`). The two learner arms compute it through the
   frozen FP32 scorer arithmetic `(z * beta).sum(-1)`, matching `training._root_targets`; the
   `EXACT-SOLVE` ceiling computes it at float64 in the `n` selection's exact term order, so the
   ceiling is bit-identical to the arithmetic that fixed `n`. The two agree to
   `9.247e-08 .. 1.412e-07` at the exact tail solution (recorded per policy in the run record as
   `root_target_precision_max_abs_difference`).
2. **The whitened design is materialised at float64 and cast to float32** before the frozen `_step`,
   because the frozen scorer refuses non-FP32 inputs. The Cholesky factorisation, the contract check
   and the recovery `beta = solve(L^T, beta_tilde)` are all float64.
3. **Rows are built as flat numeric columns**, permuted into the frozen canonical
   `(episode_index, context_id)` order, rather than constructed as `Episode` dataclasses and passed
   through `training.train_policy`. The frozen `_step`, `build_arm`, `optimizer_for` and
   `evaluate_policy` are used unmodified, and the batch windows are pinned to
   `training._cyclic_batch` by test. Consequences: no checkpoints are written, so the declared
   checkpoint cadence and the cold-resume seam are not exercised, and evaluation happens once at the
   final root update rather than at a cadence — which is what the card asks for.
4. **The bound source inventory was not clean at launch**: one entry,
   `?? scripts/run_ucope_competence_whitened_r01.py`, the runner itself. Recorded, not gating under
   §11.4; committed as `b21fb61f5`.
5. **Section 9 is a post-hoc descriptive recomputation** performed after the branch was fixed. It
   changes no number in the run record and decides nothing.

No other deviation. The arms, the `n`, the budget, the seeds, the folds, the thresholds and the
branch order are exactly as carded.

## 11. Could not verify

- **Which of the three named suspects binds.** `C-C`'s reading names the root learner's own
  optimisation, the gradient clip at norm `1.0`, and the unshuffled cyclic batch order. This object
  varied none of them, so it localises the obstruction to the learner without decomposing it. Two
  numbers here are suggestive and no more: the root design's `kappa = 5014.086` is seven times the
  tail's, and the root `d_learned` clears `eps_L` in only 2 of 6 policies against the tail's 5 of 6.
- **What residual would suffice.** The `EXACT-SOLVE` ceiling reaches agreement `1.000000` in all six,
  so the gate is reachable at the optimum; the largest `d_learned` that still clears it is not
  measured, and cannot be read off six points.
- **Whether 3 of 6 is a property of the panel or of these seeds.** At three seeds no
  arm-comparison polarity, stable-superiority or seed-population claim is available. `RAW-10X` is a
  control, never a comparator.
- **`FT-XF-FLEX` and `MT-XF-FLEX`** were not run; nothing here transfers to them.
- **Reproduction.** The run was executed once. No re-run, no second machine, no bit-identity check
  across processes was attempted, and none is claimed.
- **No dedicated A/RECON performance assessment** exists for this workload; the `110.970 s` wall is
  an observation, not an admitted performance budget.

## 12. Interpretation boundary — the acquisition lock and COUNT/RAW

The direction records `PAID_ACQUISITION_STATUS=UNEVALUATED_LOCKED` and
`COUNT_RAW_STATUS=LOCKED_UNTIL_COMPETENCE`. Under the section-11 recast those are the direction's own
sequencing choice, recorded and not §11 gates. **This object opens neither lock, and this document
proposes no decision.** What `C-C` places in front of the owner, as options:

- **The COUNT/RAW lock's stated precondition is not met.** Its condition is that competence exists.
  No learner arm is competent on the panel: `WHITENED-10X` is competent in 3 of 6 policies, which is
  not the ladder's `B_COMPETENT` rule and not a majority under this card's own threshold, and
  `RAW-10X` in none. The `EXACT-SOLVE` ceiling is competent in all six but is a closed-form
  reference, not a learner, so it cannot satisfy a precondition about what a learner achieves. The
  lock stays exactly where it is.
- **The acquisition lock likewise stays.** Acquisition polarity is out of this object's claim ceiling
  and no arm supplies the competent policies an acquisition evaluation would need.
- **Option A (owner's to take or leave): register a root-learner object.** `C-C` names the root
  learner as the one component the chain has only ever solved exactly. Two measurements here point at
  it: the root design's condition number (`5014.086`, seven times the tail's) and the root
  `d_learned` clearing `eps_L` in only 2 of 6 policies. Such an object would be a new frozen card,
  not a re-run of this one.
- **Option B (owner's to take or leave): register a tail-agreement object on the binding context.**
  Section 9 shows every `WHITENED-10X` failure binding at `LINKED-p17_20-c9_100`, the
  `TARGET_CONTEXT_ID`, with 2 of 8 contexts below the gate — while `d_learned` is inside `eps_L`.
  That is a statement about the *margin* between an `eps_L`-close parameter vector and the predicate's
  agreement gate, and it connects directly to the margin-scaled falsifier the review holds in
  reserve.
- **Option C: do nothing.** `C-C` supports no `PARK`, promotion, retirement or lifecycle change on
  its own, and none is proposed.

An outcome-informed rewrite of this card would be a **different scientific object**; this one is
consumed by a valid completed assignment and is not to be re-run with changes.
