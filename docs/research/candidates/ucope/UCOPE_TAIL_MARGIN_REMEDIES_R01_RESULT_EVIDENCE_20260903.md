# UCOPE tail-margin remedies R01 — result (2026-09-03)

Executed 2026-09-03 by Claude Code (Fable 5.1) against part 2 of
`UCOPE_TAIL_MARGIN_R01_CARD_20260903.md` (sections 8–12), registered and predicted under owner
decision D.20 (commit `da8e02301`), with both predictions recorded before the run (card section 13).

**Question.** The held-out tail decision fails only in the `(LINKED, p = 17/20)` belief stratum,
where the true top-two gap is `0.008007`. Which remedy — more data, more optimisation, or a
margin-aware objective — moves the learner's projection back inside it?

**Claim ceiling: `B/EXPLORE`.** 3 seeds x 2 folds of one arm on one frozen eight-context host.
Nothing here establishes acquisition polarity, COUNT/RAW polarity, stable superiority, a
seed-population effect, anything about `FT-XF-FLEX`, or anything about variable `k`, variable `N`,
MARL/UAV, transfer, safety, deployment, flight, energy or real-world QoS. The branch statistic is
one component of `C_even`; the full `C_even` is reported for every arm and policy, and **no arm
reaches 6 of 6 on it**.

| Fact | Value |
| --- | --- |
| Science object | `UCOPE-B-EXPLORE-TAIL-MARGIN-REMEDIES-R01` |
| Evidence class | `B/EXPLORE` |
| Branch statistic | `min_forced_PROBE_tail_agreement >= 19/20`, per policy |
| Launch commit sha (HEAD at launch) | `cba112c729a796b14c5fa0a42d5713aafbcbbd16` |
| Bound source inventory | 16 files, aggregate `8097b019e5c1bbeb386e91e9006908389e5760475256548e1afdc3f755738c99`; **clean** |
| Arms | `LARGER-N`, `BUDGET-100X`, `MARGIN-AWARE`; root stage held at `WHITENED-ROOT-10X` |
| Index law | fresh offset **`2,000,000`**, a multiple of 20, disjoint from `0..5,119`, `0..319` and `1,000,000..1,081,919` |
| Odd/even separation | hinge witness `(5, 9)`, both in `K_train`; `held_out_periods_used_in_training = []` |
| Interpreter / libraries | `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`, Python 3.10.20, torch 2.7.0+cpu, CPU |
| Machine | `Windows-10-10.0.26200-SP0`, 16 logical CPUs |
| Topology (recorded, not gating) | `torch_intraop_threads = 4`, `torch_interop_threads = 1`, `deterministic_algorithms = true`, 1 process |
| Result root (gitignored) | `temp/directions/ucope/exp/tail_margin_remedies_r01_20260903/complete` |
| Branch published | **`M-B — MARGIN_MAJORITY`** (arm at majority: `MARGIN-AWARE`), `complete: true`, nothing quarantined |

---

## 1. Launch conditions

Still gating, all satisfied: the central 4 GiB admission (`13,576,851,456` bytes physical and
effective, `2026-09-03T16:25:22.596899Z`, `GlobalMemoryStatusEx`, passed); the §4 integrity items —
group-disjoint folds, **the odd-training / even-held-out separation**, no read of B1 or audit
runtime rows, fresh counter-addressed data at offset `2,000,000`, whitening from training rows only
per stage; the §5.2 nonzero counts reconciled exactly; one machine-generated exposure line; §6.2
quarantine on learner-side failure (not triggered). Recorded and never gating: source-inventory
cleanliness (clean), the absence of an A/RECON performance assessment, execution topology, and the
direction's sequencing locks.

**The separation, asserted rather than assumed.** The hinge reads only periods `{5, 9}`, both in
`K_train = {1,3,5,7,9}`; the run record carries
`held_out_periods_used_in_training = []` and `hinge_witness_inside_training_support = true`, and the
test suite spies on every `tail_basis` call the hinge construction makes and asserts the period set
is exactly `{5, 9}` and disjoint from `K_eval`. The generated training rows themselves carry only
`K_train` behaviour periods.

**Whitening contract**, per stage, before any optimizer, at both sample sizes:

| Stage | `n` | `kappa` | `lambda_min(G)` | `max abs(LL^T - G)` | contract |
| --- | --- | --- | --- | --- | --- |
| tail | 163,840 (`LARGER-N`) | 726.832 | 2.617063e-03 | 5.551e-17 | `<= 1e-10`, `> 1e-6` |
| tail | 81,920 (other two) | 727.849 | 2.613580e-03 | 5.551e-17 | same |
| root | 327,680 / 163,840 | 5014.086 | 3.083845e-04 | 2.776e-17 | same |

## 2. Commands actually run

```
git rev-parse HEAD
  -> cba112c729a796b14c5fa0a42d5713aafbcbbd16

C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/run_ucope_tail_margin_remedies_r01.py run \
  --output-root temp/directions/ucope/exp/tail_margin_remedies_r01_20260903 --thread-cap 4
  -> {"branch": "M-B", "label": "MARGIN_MAJORITY",
      "agreement_counts": {"LARGER-N": 2, "BUDGET-100X": 2, "MARGIN-AWARE": 4},
      "c_even_counts": {"LARGER-N": 2, "BUDGET-100X": 2, "MARGIN-AWARE": 3},
      "path": ".../tail_margin_remedies_r01_20260903/complete/run-record.json"}
```

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q \
  tests/experiments/candidates/ucope/test_tail_margin_remedies_r01.py \
  --basetemp C:/Projects/HMASD/temp/pytest_ucope_remedies_01
  -> 21 passed in 31.23s
```

## 3. Work accounting — declared versus actual

| Quantity | Declared | Actual |
| --- | --- | --- |
| Policies x arms | 6 x 3 | 18 |
| Episodes generated | `81,920 x 8 x 3 = 1,966,080` | 1,966,080 |
| Tail rows fitted | 163,840 (`LARGER-N`) / 81,920 (other two) per policy | 1,966,080 |
| Root rows fitted | 327,680 / 163,840 per policy | 3,932,160 |
| Tail optimizer updates | `6 x (1,600 + 16,000 + 1,600) = 115,200` | 115,200 |
| Root optimizer updates | `18 x 3,200 = 57,600` | 57,600 |
| Tail example exposures | `115,200 x 256` | 29,491,200 |
| Root example exposures | `57,600 x 256` | 14,745,600 |
| Hinge rows built | `6 x 81,920` (`MARGIN-AWARE` only) | 491,520 |
| Exact solves | 2 per arm-policy (tail reference, root) | 36 |
| Exact policy evaluations | `8 x 18` | 144 |
| Sampled evaluation episodes / transitions | `64 x 8 x 18` | 9,216 / 25,728 |
| Non-finite events | 0 | 0 |
| Gradient clipping events | — | 5,522 of 172,800 (3.20 %) |
| Wall / CPU | under 25 minutes | **`181.865 s`** / `208.766 s` |

Every §5.2 count is nonzero and reconciles exactly.

## 4. The branch statistic — the agreement gate, per arm and per policy

Gate: `min_forced_PROBE_tail_agreement >= 19/20 = 0.95`.

| Policy | `LARGER-N` | `BUDGET-100X` | `MARGIN-AWARE` |
| --- | --- | --- | --- |
| seed 00 fold 0 | 0.520727 fail | 0.520727 fail | **1.000000 pass** |
| seed 00 fold 1 | 0.611559 fail | 0.611559 fail | 0.788446 fail |
| seed 01 fold 0 | 0.000000 fail | 0.000000 fail | 0.788446 fail |
| seed 01 fold 1 | **1.000000 pass** | **1.000000 pass** | **1.000000 pass** |
| seed 02 fold 0 | **1.000000 pass** | **1.000000 pass** | **1.000000 pass** |
| seed 02 fold 1 | 0.520727 fail | 0.520727 fail | **1.000000 pass** |
| **count** | **2 of 6** | **2 of 6** | **4 of 6** |

`LARGER-N` and `BUDGET-100X` have **identical** flags and near-identical agreements. Ten times the
tail budget (16,000 updates against 1,600) and double the sample size each leave the gate exactly
where it was.

## 5. The margin — what each arm did to the count-0 gap

The card's frozen quantity: the `(6,8)` top-two gap at count 0 of the target stratum, which is
`truth_gap + projection` exactly, with `truth_gap = 0.008007`. Baseline (published run, offset
`1,000,000`): `-0.000333, -0.006212, +0.023598, +0.011790, -0.009773, +0.007736`, negative in
policies 0, 1 and 4.

| Policy | `LARGER-N` | `BUDGET-100X` | `MARGIN-AWARE` |
| --- | --- | --- | --- |
| seed 00 fold 0 | −0.010320 | −0.010729 | **+0.013707** |
| seed 00 fold 1 | −0.001806 | −0.001128 | **+0.032587** |
| seed 01 fold 0 | −0.015716 | −0.017154 | **+0.017488** |
| seed 01 fold 1 | +0.025032 | +0.025226 | **+0.027708** |
| seed 02 fold 0 | +0.017720 | +0.017450 | **+0.030653** |
| seed 02 fold 1 | −0.020268 | −0.020407 | **+0.024024** |
| **positive** | 2 of 6 | 2 of 6 | **6 of 6** |

**`MARGIN-AWARE` turned the count-0 gap positive in all six policies**, including all three where
the baseline is negative — it satisfies the card's "strictly improves the margin" definition and is
the only arm that does. Its projections are `+0.005699 .. +0.024580`, all above the
`-0.008007` threshold with room to spare. `BUDGET-100X` moved the count-0 gap by at most `0.0014`
relative to `LARGER-N`: **ten times the optimisation budget is worth about one thousandth of the
margin.**

**The hinge did exactly what the geometry said it would, and no more.** `MARGIN-AWARE` flips no cell
at all in the `(LINKED, p = 17/20)` stratum in any policy. Its two remaining failures bind
**elsewhere**, and precisely:

| Policy | binding context | agreement | flipped cell | decision pair | `K_train` witness |
| --- | --- | --- | --- | --- | --- |
| seed 00 fold 1 | `LINKED-p13_20-*` | 0.788446 | count 4 (mass 0.211554), oracle `k=2`, selected `k=4` | `(2, 4)` | `(1, 5)` |
| seed 01 fold 0 | `LINKED-p13_20-*` | 0.788446 | count 2 (mass 0.211554), oracle `k=6`, selected `k=4` | `(4, 6)` | `(3, 7)` |

The hinge constrained the `(5, 9)` witness, i.e. **one** of the three held-out decision directions —
the `(6, 8)` one the card's part 1 identified. Both residual failures are on the **other two**
directions, `(2, 4)` and `(4, 6)`, which the hinge never touched. `1 - 0.211554 = 0.788446` closes
the arithmetic exactly, as it did in part 1.

## 6. The full `C_even`, and its components

| Arm | `C_even` flags | count |
| --- | --- | --- |
| `LARGER-N` | `[false, false, false, true, true, false]` | 2 of 6 |
| `BUDGET-100X` | `[false, false, false, true, true, false]` | 2 of 6 |
| `MARGIN-AWARE` | `[true, false, false, true, true, false]` | **3 of 6** |

**No arm reaches 6 of 6 on `C_even`**, and none exceeds the published baseline of 3 of 6;
`MARGIN-AWARE` ties it. The one place where `MARGIN-AWARE`'s agreement pass does not become a
`C_even` pass is **seed 02 fold 1**: agreement `1.000000`, but `oracle_root_match = false` and
`max_regret = 0.021437`, one root action wrong. The hinge changed the tail, the tail changed the
frozen root targets, and the root action moved with them — the value-bias channel arriving on the
root side. `C_root` (the root-stage diagnostic from the previous object) is satisfied in **5 of 6 for all
three arms**, but not in the same policies: `LARGER-N` and `BUDGET-100X` fail it at seed 01 fold 0,
`MARGIN-AWARE` at seed 02 fold 1.

## 7. `d_learned`, `d_objective`, and the value bias of `MARGIN-AWARE`

| Arm | `d_learned_tail` median (min–max) | `d_objective` median (min–max) | `d_learned_root` median |
| --- | --- | --- | --- |
| `LARGER-N` | 0.146370 (0.084986–0.364801) | 0.033588 (0.019692–0.065914) | 0.152283 |
| `BUDGET-100X` | 0.148261 (0.096617–0.245863) | 0.029241 (0.015001–**0.180023**) | 0.144227 |
| `MARGIN-AWARE` | 0.175767 (0.069542–0.260552) | 0.029241 (0.015001–**0.180023**) | 0.144194 |

**The value bias of `MARGIN-AWARE` is small.** Excess training MSE over that policy's own exact
solve: ratios `1.0003, 1.0039, 1.0049, 1.0041, 1.0022, 1.0021` — at most **0.49 %**, against
`1.0007 .. 1.0070` for `LARGER-N` and `1.0009 .. 1.0043` for `BUDGET-100X`. So the hinge is not
buying its margin by wrecking the fit; on this problem it is nearly free in squared error. Its
maximum held-out value error against `beta*` spans `0.006193 .. 0.066169` (best and worst of all
three arms), and its `d_learned_tail` median is the largest of the three — the hinge does move the
coefficients further from the least-squares optimum, in the decision-relevant direction, which is
the intent.

## 8. Exposure line

Per-coordinate displacement of the recovered raw Bellman vectors from the frozen initialisation,
per arm and stage; global min `0.902597`, max `2.142148`, so the learner can move in its budget in
all 36 rows.

| Arm | tail min / median / max | root min / median / max |
| --- | --- | --- |
| `LARGER-N` | 1.346087 / 1.886275 / 2.124581 | 0.902842 / 1.142769 / 1.808274 |
| `BUDGET-100X` | 1.345612 / 1.884761 / 2.123598 | 0.902614 / 1.145215 / 1.808277 |
| `MARGIN-AWARE` | 1.423938 / 1.904952 / 2.142148 | 0.902597 / 1.145174 / 1.808281 |

Clipping at the frozen norm `1.0`: `LARGER-N` tail 795 of 9,600 (8.28 %); `BUDGET-100X` tail 797 of
**96,000** (0.83 %) — the extra budget is spent almost entirely in an unclipped regime, which is why
it changes so little; `MARGIN-AWARE` tail 793 of 9,600 (8.26 %). Root clipping is 1,044 / 1,047 /
1,046 of 19,200 each — indistinguishable across arms, as expected since the root treatment is held
fixed.

## 9. The rule applied verbatim, in its stated order

The card's section 9, quoted, with the deciding numbers.

> - **`M-A — MARGIN_CLOSED`.** Some arm reaches agreement `>= 19/20` in **all six** policies.

Not satisfied. Counts are `LARGER-N` 2, `BUDGET-100X` 2, `MARGIN-AWARE` **4**; none is 6.

> - **`M-B — MARGIN_MAJORITY`.** Not `M-A`, but some arm reaches **at least four** of six.

**Satisfied.** `MARGIN-AWARE` reaches **4 of 6**, and `4 >= 4`, the majority threshold fixed before
data. **This is the published branch**, with `MARGIN-AWARE` the arm at majority.

> Reading: the margin is the obstruction and the named arm removes it partially; the residual
> policies are the next subject.

The later branches were not reached: `M-C` requires no arm at four, `M-D` requires no arm above the
baseline and no margin improvement, `M-E` is the residue.

**Branch published: `M-B — MARGIN_MAJORITY`.**

The reading is confirmed in an unusually specific way: the residual is not diffuse. `MARGIN-AWARE`
removed the obstruction completely on the direction the hinge constrains — 6 of 6 positive count-0
gaps, no flip anywhere in the target stratum — and the two policies it does not close fail on the
two held-out decision directions the hinge does not constrain.

## 10. Verdicts on the recorded predictions

**Owner — "MARGIN-AWARE reaches 6 of 6 on the agreement gate and BUDGET-100X does not".**

*By the rule's wording:* **not borne out.** It is a conjunction; its second clause holds
(`BUDGET-100X` reaches 2 of 6, not 6) but its first does not (`MARGIN-AWARE` reaches **4 of 6**), so
the prediction as stated is false.

*By the numbers:* right about the ranking and the mechanism, wrong about the level.
`MARGIN-AWARE` is the only arm that moved anything, it is the arm at majority, and it closed the
count-0 gap in **6 of 6** policies — on the *margin* the owner's "6 of 6" is exactly right; it is on
the *agreement gate* that it falls to 4, and it falls there for a reason the prediction could not
have contained: the gate is a minimum over eight contexts and three held-out decision directions,
and the hinge constrains one direction.

**Reviewer — "MARGIN-AWARE 6 of 6, BUDGET-100X 5 of 6, LARGER-N 3 of 6".**

*By the rule's wording:* **not borne out.** All three counts are wrong: observed 4, 2, 2 against
predicted 6, 5, 3.

*By the numbers:* the weak ordering `MARGIN-AWARE > BUDGET-100X >= LARGER-N` survives (`4 > 2 = 2`),
and every arm was over-predicted. The specific miss worth recording is `BUDGET-100X` vs `LARGER-N`:
the reviewer separated them by two policies (5 against 3) and they came out **identical** — same
flags, same failing policies, count-0 gaps differing by at most `0.0014`. Ten times the tail budget
and double the sample size are, on this measurement, the same intervention: none.

**Neither prediction is borne out.** Both were directionally right that `MARGIN-AWARE` would lead.

## 11. Deviations from the card

1. **The hinge is a batch mean, not a sum.** The card writes "sum over rows"; the implementation uses
   the mean, so that the fixed weight `1.0` is commensurate with `mse_loss`, which is also a mean —
   which is what the card's own phrase "hinge weight fixed at `1.0` **relative to the MSE term**"
   requires. A sum would have made the effective weight scale with the batch size (256x).
2. **`training._step` is replaced by a local `step_with_hinge` for all three arms**, because the
   frozen step computes MSE only. It is asserted by test to be **bit-for-bit identical** to
   `training._step` — same parameters and same activity counters — when the hinge is absent, so the
   two hinge-free arms run the frozen step's arithmetic.
3. **The rule's baseline is unpaired with this object's rows.** The baseline count-0 gaps come from
   the published run at offset `1,000,000`; this object draws fresh rows at `2,000,000` as the card
   requires. The comparison is therefore across different draws, and the draw matters: the **exact
   solve** at the new rows itself flips count 0 in **3 of 6** policies at `n = 81,920`
   (`+0.005166, -0.002267, -0.003461, +0.006372, +0.008148, -0.002090`) and **1 of 6** at
   `n = 163,840`, whereas at the old rows it never flipped. Recorded; the rule was applied exactly as
   written, and the exact-solve reference is in the record per arm and policy so the objective's own
   contribution is visible.
4. **One draw is materially worse.** `d_objective` reaches `0.180023` at seed 01 fold 0 for the two
   `n = 81,920` arms — about four times anything seen at the old offset — which is why that policy is
   the worst for every arm (`LARGER-N` and `BUDGET-100X` reach agreement `0.000000` there, with all
   eight contexts below the gate).
5. **The bound source inventory does not include this runner.** It is inherited from the
   root-conditioning object's inventory function, so the aggregate is identical to that object's
   (`8097b019...`, 16 files) and covers the frozen package, the competence runner, the n selection and
   the root runner, but not `run_ucope_tail_margin_remedies_r01.py`. The runner was committed as
   `cba112c72` before the run and the tree was clean at launch. Recorded, not gating (§11.4).
6. **Rows are built as flat numeric columns** permuted into the frozen canonical order rather than as
   `Episode` dataclasses through `training.train_policy`; the frozen `build_arm`, `optimizer_for` and
   `evaluate_policy` are unmodified, batch windows pinned to `training._cyclic_batch`, and no
   checkpoints are written.
7. **The three arms use different `n`**, so each has its own tail Gram, its own exact solve and its
   own reference; `LARGER-N`'s reference is not the other two arms'.

## 12. Could not verify

- **Whether a hinge on all three witness pairs would close the remaining two policies.** Section 5
  names `(1, 5)` and `(3, 7)` as the untouched witnesses and the failures land exactly on their
  held-out directions, but the three-witness variant was not run and is not claimed.
- **Whether seed 02 fold 1's root-action regression under `MARGIN-AWARE` is caused by the hinge.**
  The mechanism is plausible — the hinge moved the tail, the frozen root targets moved with it — but
  a single policy at three seeds supports no causal claim.
- **Whether `LARGER-N == BUDGET-100X` is general.** They were identical on this draw. That is an
  observation about six policies at one offset, not a claim that budget and sample size never matter.
- **Whether the unpaired baseline changes the branch.** The rule is applied as written; a paired
  re-run at the published offset was not performed and would be a different scientific object.
- **`FT-XF-FLEX` / `MT-XF-FLEX`**, other hosts, other `m`, other hinge weights: not run. `m` and the
  weight were fixed in the card and not tuned.
- **Reproduction.** One run, one machine. No re-run and no cross-machine check.
- **No dedicated A/RECON performance assessment** exists for this workload; `181.865 s` is an
  observation, not an admitted budget.

## 13. Interpretation boundary — the acquisition lock and COUNT/RAW

**This object opens neither lock and proposes no decision.** As the card's section 11 states for
`M-B`, a majority is not the ladder's `B_COMPETENT` rule and is not a population claim.

- **The COUNT/RAW lock stays.** Its precondition is that competence exists. Under the direction's
  actual predicate `C_even`, the best arm reaches **3 of 6**, equal to — not better than — the
  published baseline. Made visible as the owner asked: **no arm reaches 6 of 6 on `C_even`**, so
  nothing here meets the precondition.
- **The acquisition lock stays.** Acquisition polarity is outside this object's claim ceiling, and no
  arm supplies the competent policies an acquisition evaluation would need.
- **What the branch does establish**, and hands forward: the margin is the right lever. A hinge on a
  training-support witness pair, costing at most `0.49 %` of training MSE and touching no held-out
  period, moved the count-0 gap positive in 6 of 6 policies where doubling `n` and multiplying the
  budget by ten moved it in none. The residual is not diffuse — it is the two held-out decision
  directions the hinge did not constrain.
- **Option A (owner's to take or leave): a three-witness hinge object.** Constrain `(1,5)`, `(3,7)`
  and `(5,9)` together, which by the part 1 identity controls all three held-out decision directions
  `(2,4)`, `(4,6)` and `(6,8)`. Section 5 predicts this addresses both residual failures; it would be
  a new frozen card with its own prediction, not a re-run of this one.
- **Option B (owner's to take or leave): an object on draw variance.** Deviations 3 and 4 show the
  objective itself crossing the gap at these rows, which the published offset did not. That is a
  statement about how much of the criterion's difficulty is sampling, and it bears on the
  margin-scaled falsifier the review holds in reserve.
- **Option C: do nothing.** `M-B` supports no `PARK`, promotion, retirement or lifecycle change on
  its own, and none is proposed.

An outcome-informed rewrite of this card would be a **different scientific object**; this one is
consumed by a valid completed assignment and is not to be re-run with changes.
