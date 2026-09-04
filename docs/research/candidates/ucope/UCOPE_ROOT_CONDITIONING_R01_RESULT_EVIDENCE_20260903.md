# UCOPE root-conditioning R01 — result (2026-09-03)

Executed 2026-09-03 by Claude Code (Fable 5.1) against the object frozen in
`UCOPE_ROOT_CONDITIONING_R01_CARD_20260903.md` under owner decision D.16 (commit `f56546867`),
with the branch statistic amended to `C_root` before launch by owner decision D.18 (commit
`298ca67e2`; card section 13) and both predictions recorded before the run (card section 14).

**Question.** With the tail stage held fixed, does whitening the root design close the root
learner's gap, and does that reach competence?

**Claim ceiling: `B/EXPLORE`.** A direct observation on the actually observed panel of 3 seeds x 2
folds of one arm on one frozen eight-context host. Nothing here establishes acquisition polarity,
COUNT/RAW polarity, stable superiority, a seed-population effect, anything about `FT-XF-FLEX`, or
anything about variable `k`, variable `N`, MARL/UAV, transfer, safety, deployment, flight, energy or
real-world QoS. `C_root` is **not** the direction's competence predicate; the full `C_even` is
reported alongside it throughout, and under `C_even` no learner arm exceeds 3 of 6.

| Fact | Value |
| --- | --- |
| Science object | `UCOPE-B-EXPLORE-ROOT-CONDITIONING-R01` |
| Evidence class | `B/EXPLORE` |
| Branch statistic | **`C_root`** (card section 13, amended before launch) |
| Launch commit sha (HEAD at launch) | `104aca5914f34dda49e5011a3f3e2e113002a8c0` |
| Bound source inventory | 16 files, aggregate `8097b019e5c1bbeb386e91e9006908389e5760475256548e1afdc3f755738c99`; **clean** — the first clean inventory in this chain, the runner having been committed before the run |
| Arm under test | `FT-XF-BC` root stage, on one fixed `WHITENED-10X` tail per policy |
| Rows | `n = 81,920` tail rows and `163,840` root rows per policy, at the competence card's index law |
| Budget | `lr 3e-3`, batch 256, 1,600 tail updates (once per policy) and 3,200 root updates per arm |
| Interpreter / libraries | `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`, Python 3.10.20, torch 2.7.0+cpu, CPU |
| Machine | `Windows-10-10.0.26200-SP0`, 16 logical CPUs |
| Topology (recorded, not gating) | `torch_intraop_threads = 4`, `torch_interop_threads = 1`, `deterministic_algorithms = true`, 1 process |
| Result root (gitignored) | `temp/directions/ucope/exp/root_conditioning_r01_20260903/complete` |
| Branch published | **`R'-B — WHITENED_ROOT_MAJORITY_CEILING_CLEAN`**, `complete: true`, nothing quarantined |

---

## 1. Launch conditions

Still gating, and all satisfied: the central 4 GiB physical and effective memory admission
immediately before the workload; the §4 integrity items — group-disjoint folds, the odd-training /
even-held-out separation, no read of B1 or audit runtime rows, fresh counter-addressed data at
`i = OFFSET + j`, `OFFSET = 1,000,000`, `j = 0 .. 40,959`, **root whitening from training rows
only**, and **the tail-reproduction check at `1e-6`**; the §5.2 nonzero counts reconciled exactly;
one machine-generated exposure line; §6.2 quarantine on learner-side failure (not triggered).
Recorded and never gating: working-tree cleanliness (clean here), the absence of a dedicated
A/RECON performance assessment, execution topology, and the direction's acquisition and COUNT/RAW
sequencing locks.

**Resource admission**, receipt at
`temp/directions/ucope/exp/root_conditioning_r01_20260903/preflight.json`:

| Field | Value |
| --- | --- |
| `available_physical_bytes` | `15,324,450,816` (14.27 GiB) |
| `effective_available_bytes` | `15,324,450,816` (14.27 GiB) |
| `minimum_available_bytes` | `4,294,967,296` |
| `physical_floor_pass` / `effective_floor_pass` / `passed` | `true` / `true` / `true` |
| `measurement_source` / `assessed_at` | `GlobalMemoryStatusEx` / `2026-09-03T15:56:52.120340Z` |

### The fixed tail reproduced exactly

The gating integrity item of card section 3 required the re-trained `WHITENED-10X` tail to match the
competence run's recorded coefficients to `max abs difference <= 1e-6`. **Observed in all six
policies: `0.000000e+00`.** The re-training is bit-identical, which is what card section 3 predicted
and what makes the three root arms provably sit on the competence object's tail.

### The root whitening contract

Measured per policy, before any optimizer existed, and identical in all six as card section 4
predicted from the structural fold-invariance of the root Gram:

| Quantity | Contract | Observed (all six policies) |
| --- | --- | --- |
| `kappa(G_root)` | — | **5014.086** |
| `lambda_min(G_root)` | `> 1e-6` | **3.083845e-04** |
| `max abs(L L^T - G)` | `<= 1e-10` | **2.776e-17** |

The tail contract was checked too and cleared identically to the competence run.

## 2. Commands actually run

```
git rev-parse HEAD
  -> 104aca5914f34dda49e5011a3f3e2e113002a8c0

C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/run_ucope_root_conditioning_r01.py run \
  --output-root temp/directions/ucope/exp/root_conditioning_r01_20260903 --thread-cap 4
  -> {"branch": "R'-B", "label": "WHITENED_ROOT_MAJORITY_CEILING_CLEAN",
      "exact_root_competent": 6, "whitened_root_competent": 5, "raw_root_competent": 1,
      "path": ".../root_conditioning_r01_20260903/complete/run-record.json"}
```

Unit checks — the inherited constants, the single shared implementation path, the tail-reproduction
reference and its two refusals, tail determinism and raw recovery, the one shared root problem, the
fold-invariance of the root Gram, `C_root` against `C_even` on every component, the per-context
breakdown against `evaluation.evaluate_policy`, all five amended branches in their stated order, an
end-to-end miniature run, and a perturbed reference producing a §6.2 quarantine:

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q \
  tests/experiments/candidates/ucope/test_root_conditioning_r01.py \
  --basetemp C:/Projects/HMASD/temp/pytest_ucope_root_cond_02
  -> 23 passed in 6.74s
```

## 3. Work accounting — declared versus actual

| Quantity | Declared | Actual |
| --- | --- | --- |
| Policies | 6 (3 seeds x 2 folds) | 6 |
| Tails trained | 1 per policy, shared by three arms | 6 |
| Root arms trained | 2 per policy | 12 |
| Episodes generated | `40,960 x 8 x 3 = 983,040` | 983,040 |
| Tail rows fitted | 81,920 per policy | 491,520 |
| Root rows fitted | 163,840 per policy | 983,040 |
| Tail optimizer updates | `1,600 x 6 = 9,600` | 9,600 |
| Root optimizer updates | `3,200 x 12 = 38,400` | 38,400 |
| Tail example exposures | `9,600 x 256 = 2,457,600` | 2,457,600 |
| Root example exposures | `38,400 x 256 = 9,830,400` | 9,830,400 |
| Exact solves | 3 per policy (exact tail, root on learned targets, root on exact-tail targets) | 18 |
| Exact policy evaluations | `8 x 3 arms x 6 policies = 144` | 144 |
| Sampled evaluation episodes | `64 x 8 x 3 x 6 = 9,216` | 9,216 |
| Sampled evaluation transitions | — | 26,496 |
| Non-finite events | 0 | 0 |
| Gradient clipping events | — | 2,382 of 48,000 (4.96 %) |
| Wall / CPU | under 10 minutes | **`98.620 s`** / `109.984 s` |

Every §5.2 count is nonzero and reconciles exactly.

## 4. `C_root` — the branch statistic — per arm and per policy

`C_root` = `all_scores_finite AND all_choices_unique AND exact_eight_context_oracle_root_vector AND
max_expected_regret <= 1/50`, evaluated in the frozen exact rational arithmetic.

| Policy | `WHITENED-ROOT-10X` | `RAW-ROOT-10X` | `EXACT-ROOT-SOLVE` |
| --- | --- | --- | --- |
| seed 00 fold 0 | **pass** | **pass** | **pass** |
| seed 00 fold 1 | **pass** | fail | **pass** |
| seed 01 fold 0 | **pass** | fail | **pass** |
| seed 01 fold 1 | **pass** | fail | **pass** |
| seed 02 fold 0 | fail | fail | **pass** |
| seed 02 fold 1 | **pass** | fail | **pass** |
| **count** | **5 of 6** | **1 of 6** | **6 of 6** |

Component by component, the two decisive ones:

| Component | `WHITENED-ROOT-10X` | `RAW-ROOT-10X` | `EXACT-ROOT-SOLVE` |
| --- | --- | --- | --- |
| `exact_eight_context_oracle_root_vector` | 5 of 6 | **1 of 6** | 6 of 6 |
| `max_expected_regret <= 0.02` | 5 of 6 | **1 of 6** | 6 of 6 |
| `all_scores_finite`, `all_choices_unique` | 6 of 6 | 6 of 6 | 6 of 6 |

Max expected regret per policy — `WHITENED-ROOT-10X`: `0.003155, 0.003155, 0.000000, 0.000000,
0.033103, 0.000000`; `RAW-ROOT-10X`: `0.003155, 0.070609, 0.021437, 0.021437, 0.048000, 0.021437`;
`EXACT-ROOT-SOLVE`: `0.003155, 0.003155, 0.000000, 0.000000, 0.004540, 0.000000`. The raw root
misses the `0.02` gate by a hair in three policies (`0.021437`), which is the signature of one wrong
root action rather than a diffuse error.

## 5. The full `C_even`, reported as required

`C_even` adds the purely tail-determined `min_forced_PROBE_tail_agreement >= 19/20`, whose six
values are fixed by the shared tail at `0.611559, 0.611559, 1.000000, 1.000000, 0.520727, 1.000000`
and are therefore **identical across all three arms of a policy** (verified: one distinct value per
policy).

| Arm | `C_even` flags | count |
| --- | --- | --- |
| `WHITENED-ROOT-10X` | `[false, false, true, true, false, true]` | **3 of 6** |
| `RAW-ROOT-10X` | `[false, false, false, false, false, false]` | 0 of 6 |
| `EXACT-ROOT-SOLVE` | `[false, false, true, true, false, true]` | **3 of 6** |

Two things follow, both of which the card predicted in writing before the run.

1. **`WHITENED-ROOT-10X` reproduced the competence object exactly.** Its `C_even` flags are the
   competence run's `WHITENED-10X` flags, `[false, false, true, true, false, true]`, and its root
   `d_learned` values are that run's numbers to the digit (`0.207066, 0.294404, 0.271799, 0.101065,
   0.083938, 0.027560`). The bit-reproduction check of card section 8 **passed**; no discrepancy to
   report.
2. **The ceiling is capped at 3 of 6 under `C_even`**, exactly as card section 8 argued from
   already-published numbers: with one tail fixed, no arm — including the closed-form ceiling — can
   exceed the three policies whose tail clears the agreement gate. Under the **un-amended** rule the
   branch would have been `R-D` with probability 1. The amendment was necessary, and the run now
   demonstrates its necessity rather than merely arguing it.

## 6. `d_objective_root`, `d_learned_root`, gradient ratios

`d_objective_root = max abs(beta_root_star - beta_root_star_exact_tail)` measures how far the
*learned* tail's residual moves the root optimum — the direct test of mechanism (ii)(a).

| Policy | `d_objective_root` | root-target displacement `max abs` |
| --- | --- | --- |
| seed 00 fold 0 | 0.013723 | 0.017473 |
| seed 00 fold 1 | 0.028351 | 0.020390 |
| seed 01 fold 0 | 0.025548 | 0.006855 |
| seed 01 fold 1 | 0.011406 | 0.021375 |
| seed 02 fold 0 | **0.057571** | 0.013518 |
| seed 02 fold 1 | 0.008835 | 0.019080 |
| **median / max** | **0.019636 / 0.057571** | 0.006855 – 0.021375 |

**All six are inside `eps_L = 0.10`.** Target-carrying displaces the root optimum, but by well under
the tolerance, and — decisively — the ceiling solved on the carried targets is competent under
`C_root` in all six. Mechanism (ii)(a) is **not** what binds at this `n`.

`d_learned_root = max abs(beta_root_arm - beta_root_star)` against `eps_L = 0.10`:

| Policy | `WHITENED-ROOT-10X` | `RAW-ROOT-10X` |
| --- | --- | --- |
| seed 00 fold 0 | 0.207066 | 0.326054 |
| seed 00 fold 1 | 0.294404 | 1.301747 |
| seed 01 fold 0 | 0.271799 | 0.676441 |
| seed 01 fold 1 | 0.101065 | 0.207126 |
| seed 02 fold 0 | 0.083938 | 0.775756 |
| seed 02 fold 1 | 0.027560 | 1.033983 |
| **median** | **0.154066** | **0.726098** |
| **within `eps_L`** | 2 of 6 | 0 of 6 |

Whitening cuts the median root gap by **4.7x**. Note the honest tension: `WHITENED-ROOT-10X` clears
`C_root` in 5 of 6 while clearing `eps_L` in only 2 of 6 — `eps_L` is a parameter-space tolerance
and `C_root` a decision predicate, and on this problem the decisions are correct well before the
coefficients are.

Gradient ratios `g_learned / g_star` on the root objective, with `g_star` the infinity-norm gradient
at the exact-tail root optimum (`1.398e-02, 8.847e-03, 1.151e-03, 5.920e-03, 6.442e-03, 4.233e-03`)
— `WHITENED-ROOT-10X`: `0.4344, 1.5808, 14.9927, 4.8949, 2.0862, 1.1276`; `RAW-ROOT-10X`: `0.7559,
1.6765, 26.2867, 4.9361, 2.1070, 3.6594`. Descriptive and deciding nothing: `g_star` is taken at a
point that is not this objective's optimum, so the ratio mixes the learner's residual with the
target displacement, and the `14.99` / `26.29` pair is an artefact of that policy's unusually small
denominator (`1.151e-03`).

## 7. Per-context breakdown, and what the raw root actually gets wrong

The breakdown is machine-generated into the run record and cross-checked against
`evaluation.evaluate_policy` at `1e-12` on both the maximum regret and the minimum agreement. At the
target context `LINKED-p17_20-c9_100`, whose oracle action is `PROBE`:

| Policy | `WHITENED-ROOT-10X` | `RAW-ROOT-10X` | `EXACT-ROOT-SOLVE` |
| --- | --- | --- | --- |
| seed 00 fold 0 | PROBE | PROBE | PROBE |
| seed 00 fold 1 | PROBE | PROBE | PROBE |
| seed 01 fold 0 | PROBE | **IMMEDIATE** | PROBE |
| seed 01 fold 1 | PROBE | **IMMEDIATE** | PROBE |
| seed 02 fold 0 | PROBE | PROBE | PROBE |
| seed 02 fold 1 | PROBE | **IMMEDIATE** | PROBE |

**The raw root's characteristic error is refusing to probe at the target context** — three of its
six policies, each costing regret `0.021437`, just over the `0.02` gate. The whitened root chooses
`PROBE` there in all six, and so does the ceiling. Contexts with a mismatched root action: whitened
`0, 0, 0, 0, 1, 0`; raw `0, 3, 1, 1, 2, 1`.

The single whitened-root failure, seed 02 fold 0, mismatches at `LINKED-p17_20-c7_50` — the target
context's cost twin — with `max_regret = 0.033103`; the ceiling on the same targets gets that
context right with regret `0.004540`, so this failure is the **learner**, not the problem.

## 8. Exposure line

Machine-generated over the two learner arms; `EXACT-ROOT-SOLVE` has no optimizer trajectory and is
excluded. Per-coordinate displacement of the recovered raw root vector from the frozen root
initialisation of the same seed and fold:

| Arm | min | median | max |
| --- | --- | --- | --- |
| `WHITENED-ROOT-10X` | 0.818056 | 1.142266 | 1.955352 |
| `RAW-ROOT-10X` | 0.670694 | 0.884900 | 1.523858 |

The raw per-coordinate ceiling at this budget is `3,200 x 3e-3 = 9.6`, far above every observed
move, so **no arm is step-budget-bound**. Clipping at the frozen norm `1.0`: the shared tail 801 of
9,600 (8.34 %); `WHITENED-ROOT-10X` root 1,054 of 19,200 (5.49 %); `RAW-ROOT-10X` root 527 of 19,200
(2.74 %) — whitening again roughly doubles the clipping rate.

## 9. The rule applied verbatim, in its stated order

The card's section 13 (the amended rule), quoted, with the deciding numbers.

> - **`R'-A — WHITENED_ROOT_COMPETENT`.** `WHITENED-ROOT-10X` satisfies `C_root` in **all six**
>   policies.

Not satisfied. `WHITENED-ROOT-10X` satisfies `C_root` in **5** of 6
(`[true, true, true, true, false, true]`).

> - **`R'-B — WHITENED_ROOT_MAJORITY_CEILING_CLEAN`.** Not `R'-A`, but `WHITENED-ROOT-10X` satisfies
>   `C_root` in **at least four** of six **and** `EXACT-ROOT-SOLVE` satisfies it in all six.

**Satisfied.** `5 >= 4`, and `EXACT-ROOT-SOLVE` satisfies `C_root` in **6 of 6**. **This is the
published branch.**

> Reading: mechanism (i) substantially, with a residual the ceiling does not share.

The later branches were not reached: `R'-C` requires the whitened root in fewer than four, `R'-D`
requires the ceiling not competent in all six, and `R'-E` is the residue.

**Branch published: `R'-B — WHITENED_ROOT_MAJORITY_CEILING_CLEAN`.**

Mechanism (i) — root conditioning binds — is the reading. The supporting numbers: the raw root
satisfies `C_root` in 1 of 6 and the whitened root in 5 of 6 on the *same* targets, the *same*
initialisation and the *same* budget, differing only in the coordinate system; the median root gap
falls 4.7x; and mechanism (ii)(a) is ruled out on its own frozen measurement, `d_objective_root`
being inside `eps_L` in all six with a ceiling competent in all six. The residual — one policy, seed
02 fold 0 — is (ii)(b)-shaped and is what the card calls the arm-to-ceiling gap.

## 10. Verdict on the recorded predictions

**Owner — "none (exploration run)".** No prediction, therefore **no verdict**. Recorded without one.

**Reviewer — "R'-B (the whitened root improves the regret and oracle-root components but not in all
six)".**

*By the rule's wording:* **borne out.** The published branch is `R'-B`.

*By the numbers:* borne out in the specific components the reviewer named, and in the right
direction and degree.

- "**improves the regret ... component**": `max_expected_regret <= 0.02` holds in **1 of 6** raw
  policies and **5 of 6** whitened.
- "**and oracle-root**": the exact eight-context oracle root vector is recovered in **1 of 6** raw
  and **5 of 6** whitened.
- "**but not in all six**": exactly one policy, seed 02 fold 0, fails — on both named components
  (`oracle_root_match` false, `max_regret = 0.033103`).
- Not stated by the reviewer but consistent with it: the ceiling is clean in all six, which is the
  second conjunct `R'-B` needs and which distinguishes `R'-B` from `R'-D`.

This is the first prediction in the chain to be borne out both by wording and by mechanism.

## 11. Deviations from the card

1. **The ceiling is solved on the FP32 targets the learners see**, not on FP64 targets, so that all
   three arms solve literally the same root problem — which is what card section 4 requires
   ("solving the *same* root problem and differ **only** in how the root design is
   coordinatised"). The FP64 target vector is used only to compute
   `beta_root_star_exact_tail` for `d_objective_root`; the two target vectors differ by
   `0.006855 .. 0.021375` per policy, recorded, and that difference is the measured quantity, not an
   error.
2. **`d_objective_root` compares an FP32-target solve with an FP64-target solve.** The target
   precision component of that comparison is `O(1e-7)` (measured in the competence object) against
   effects of `0.008835 .. 0.057571`, so it is four to five orders below the signal.
3. **Rows are built as flat numeric columns** permuted into the frozen canonical
   `(episode_index, context_id)` order rather than as `Episode` dataclasses through
   `training.train_policy`; the frozen `_step`, `build_arm`, `optimizer_for` and `evaluate_policy`
   are used unmodified and the batch windows are pinned to `training._cyclic_batch` by test. No
   checkpoints are written, so the checkpoint cadence and cold-resume seam are not exercised.
4. **The exact tail solve is computed but never trained or evaluated.** It exists only as the
   reference for `d_objective_root`; this object's ceiling deliberately inherits the *learned* tail,
   which is what lets it discriminate mechanism (ii)(a).
5. **Improvement over the competence object, not a deviation:** the per-context breakdown is
   machine-generated into the run record and cross-checked against the frozen evaluation, rather
   than recomputed after the fact as the competence result had to.
6. **Test-only:** the miniature end-to-end test neutralises `_configure_topology`, because
   `torch.set_num_interop_threads` cannot be called after parallel work has started in a shared
   pytest process. Execution topology is recorded-not-gating and the real run set it normally
   (`torch_interop_threads = 1`). The same limitation makes the competence object's miniature test
   fail when the whole `ucope` suite runs in one process; that runner is left untouched pending an
   owner decision on a fail-soft.

## 12. Could not verify

- **Whether seed 02 fold 0 is special or noise.** One failing policy out of six, at three seeds, is
  not a population claim and not a stable-superiority claim. `RAW-ROOT-10X` is a control and never a
  comparator.
- **Which sub-mechanism produces the residual.** `R'-B`'s residual is (ii)(b)-shaped but the clip at
  norm `1.0` and the unshuffled cyclic batch order were not varied here, so the arm-to-ceiling gap is
  named, not decomposed.
- **Why `C_root` is cleared long before `eps_L` is.** 5 of 6 on the predicate against 2 of 6 within
  the parameter tolerance is recorded as an observation; no claim is made about the general relation
  between the two.
- **Anything about the agreement gate.** It is tail-determined, unchanged at `0.611559, 0.611559,
  1.0, 1.0, 0.520727, 1.0`, and untouched by any root treatment. That is the subject of
  `UCOPE-A-TAIL-MARGIN-TARGET-CONTEXT-R01`.
- **`FT-XF-FLEX` / `MT-XF-FLEX`**, other `n`, other budgets, other hosts: not run.
- **Reproduction across machines.** The run was executed once on one machine. The tail reproduced
  bit-exactly *within* this machine, which is evidence of determinism, not of portability.
- **No dedicated A/RECON performance assessment** exists for this workload; `98.620 s` is an
  observation, not an admitted budget.

## 13. Interpretation boundary — the acquisition lock and COUNT/RAW

**This object opens neither lock, and proposes no decision.** As card section 10 states for `R'-B`,
a majority is not the ladder's `B_COMPETENT` rule and not a population claim.

- **COUNT/RAW stays locked.** Its precondition is that competence exists. Under the direction's
  actual competence predicate `C_even`, `WHITENED-ROOT-10X` reaches 3 of 6 — unchanged from the
  competence object, because the root was never what stopped the other three. `C_root` is a
  root-stage diagnostic frozen for this object, not the direction's criterion, and 5 of 6 on it is
  not competence.
- **The acquisition lock stays.** Acquisition polarity is outside this object's claim ceiling.
- **What the branch does establish**, and hands forward: root conditioning was a real and largely
  removable obstruction (1 of 6 to 5 of 6 on `C_root`), the two-stage target construction is sound at
  this `n` (`d_objective_root` inside `eps_L` in all six, ceiling clean in all six), and the
  remaining root residual is a single policy.
- **What now blocks competence is the tail**, specifically its decision margin at the target
  context — the D.17 correction, recorded in card section 13 and carried by
  `UCOPE_TAIL_MARGIN_R01_CARD_20260903.md`.

An outcome-informed rewrite of this card would be a **different scientific object**; this one is
consumed by a valid completed assignment and is not to be re-run with changes.
