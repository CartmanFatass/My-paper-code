# UCOPE paid acquisition B01 — result (2026-09-03)

Executed 2026-09-03 by Claude Code (Fable 5.1) against
`UCOPE_PAID_ACQUISITION_B01_CARD_20260903.md`, opened under the owner decision on D.22 option (a) —
spec **§11.1, competence recorded, not required** — intaken as D.23, with both predictions recorded
in the card's section 12 before launch.

**Question.** Does the learner pay the probe cost exactly where information is worth buying — at
`LINKED-p17_20-c9_100`, the unique context of eight whose oracle net acquisition is positive — and
does the information it buys leave it better off than not having paid?

**Claim ceiling: `B/EXPLORE`.** 3 seeds x 2 folds of one arm on one frozen eight-context host.
Nothing here establishes COUNT/RAW polarity, stable superiority, a seed-population effect, anything
about `FT-XF-FLEX`, or anything about variable `k`, variable `N`, MARL/UAV, transfer, safety,
deployment, flight, energy or real-world QoS. `A_paid` is a competence-free predicate frozen for this
object; it is **not** the direction's competence criterion, and the competence record is carried
throughout so that no reader can mistake one for the other.

| Fact | Value |
| --- | --- |
| Science object | `UCOPE-B-EXPLORE-PAID-ACQUISITION-B01` |
| Evidence class | `B/EXPLORE` |
| Branch statistic | **`A_paid`** — the frozen `acquisition_pass` with its `competence_pass` conjunct removed and nothing else changed |
| Competence policy | **recorded, not required** (`MARL_EMPIRICAL_EVIDENCE_SPEC.md#11.1`) |
| Launch commit sha (HEAD at launch) | `ceaae3a7e84cf2339d18a5f2eea59435386021da` |
| Bound source inventory | 18 files, aggregate `0c51969b0c6888ba688ec8c52d3f192498de0f89611cc94e834d4dfb943fe7a1`; **clean** |
| Arms | `MARGIN-AWARE-TREATMENT`, `EXACT-REFERENCE`, on the same draw |
| Index law | offset **`2,000,000`**, reused from the remedies object, multiple of 20, disjoint from `0..5,119`, `0..319` and `1,000,000..1,081,919` |
| Odd/even separation | hinge witness `(5, 9)`, both in `K_train`; `held_out_periods_used_in_training = []` |
| Interpreter / libraries | `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`, Python 3.10.20, torch 2.7.0+cpu, CPU |
| Machine | `Windows-10-10.0.26200-SP0`, 16 logical CPUs |
| Execution | **1 process, `torch_intraop_threads = 1`**, `torch_interop_threads = 1`, `deterministic_algorithms = true` |
| Result root (gitignored) | `temp/directions/ucope/exp/paid_acquisition_b01_20260903/complete` |
| Branch published | **`PA-B — PAID_ACQUISITION_MAJORITY`**, `complete: true`, nothing quarantined |

---

## 1. Launch conditions

Still gating, all satisfied: the central 4 GiB physical and effective memory admission immediately
before the workload; the §4 integrity items — group-disjoint folds, the odd-training /
even-held-out separation, no read of B1 or audit runtime rows, counter-addressed data at
`i = 2,000,000 + j`, whitening from training rows only per stage, and **the tail-reproduction check
at `1e-6`**; the §5.2 nonzero counts reconciled exactly; one machine-generated exposure line; §6.2
quarantine on learner-side failure (not triggered). Recorded and never gating: source-inventory
cleanliness (clean), the absence of a dedicated A/RECON performance assessment, execution topology,
**resource telemetry and the declared concurrent load**, **the competence record**, and the
direction's own sequencing locks.

**Resource admission**, written to the output root before any model or optimizer existed, by the
command the card names:

| Field | Value |
| --- | --- |
| `available_physical_bytes` | `14,990,376,960` (13.96 GiB) |
| `effective_available_bytes` | `14,990,376,960` (13.96 GiB) |
| `minimum_available_bytes` | `4,294,967,296` |
| `physical_floor_pass` / `effective_floor_pass` / `passed` | `true` / `true` / `true` |
| `measurement_source` / `assessed_at` | `GlobalMemoryStatusEx` / `2026-09-03T20:40:44.755327Z` |

**The tail-reproduction gate: `0.000000e+00`, bitwise, in all six policies.** The card flagged in
advance that the published `MARGIN-AWARE` vectors were produced at four threads while this object
runs single-threaded, and that float32 reduction order could therefore make the difference nonzero;
it set the gate at the `1e-6` tolerance for that reason. **The risk did not materialise** — the
re-trained treatment tail is bit-identical to the published one at one thread as at four. The
treatment is provably the learner the card names.

**Whitening contract**, per stage and policy, before any optimizer:

| Policy | tail `kappa` | tail `lambda_min(G)` | tail `max abs(LL^T − G)` | root `kappa` | root `lambda_min(G)` | root `max abs(LL^T − G)` |
| --- | --- | --- | --- | --- | --- | --- |
| seed 00 fold 0 | 727.849 | 2.613580e-03 | 5.551e-17 | 5014.086 | 3.083845e-04 | 2.776e-17 |
| seed 00 fold 1 | 733.581 | 2.593057e-03 | 0.000e+00 | 5014.086 | 3.083845e-04 | 2.776e-17 |
| seed 01 fold 0 | 726.616 | 2.619013e-03 | 0.000e+00 | 5014.086 | 3.083845e-04 | 2.776e-17 |
| seed 01 fold 1 | 728.647 | 2.609311e-03 | 0.000e+00 | 5014.086 | 3.083845e-04 | 2.776e-17 |
| seed 02 fold 0 | 722.896 | 2.628212e-03 | 0.000e+00 | 5014.086 | 3.083845e-04 | 2.776e-17 |
| seed 02 fold 1 | 726.855 | 2.615258e-03 | 5.551e-17 | 5014.086 | 3.083845e-04 | 2.776e-17 |

Contract: `max abs(LL^T − G) <= 1e-10` and `lambda_min(G) > 1e-6`. Every value clears it by seven
orders of magnitude or more.

## 2. Commands actually run

```
git rev-parse HEAD
  -> ceaae3a7e84cf2339d18a5f2eea59435386021da

C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe scripts/run_ucope_paid_acquisition_b01.py run \
  --output-root temp/directions/ucope/exp/paid_acquisition_b01_20260903 --thread-cap 1 \
  --concurrent-load "two directions concurrently by owner instruction: this object (1 process, torch threads 1) and E2 (2 four-thread runs); recorded as a one-off, observational only"
  -> {"branch": "PA-B", "label": "PAID_ACQUISITION_MAJORITY",
      "treatment_count": 5, "reference_count": 6,
      "path": ".../paid_acquisition_b01_20260903/complete/run-record.json"}
```

Launched detached via `Start-Process -WindowStyle Hidden` so no tool timeout could reach it; pid
`10440`, started `2026-09-03T13:39:54` local, exited `20:42:39Z`, run-record written `13:41:48`
local — about 64 s after the preflight receipt.

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q \
  tests/experiments/candidates/ucope/test_paid_acquisition_b01_runner.py \
  tests/experiments/candidates/ucope/test_paid_acquisition_b01_card.py \
  --basetemp C:/Projects/HMASD/temp/pytest_ucope_paid_acq_run02
  -> 50 passed in 14.60s
```

## 3. Work accounting — declared versus actual

| Quantity | Declared | Actual |
| --- | --- | --- |
| Policies x arms | 6 x 2 | 12 |
| Episodes generated | `40,960 x 8 x 3 = 983,040` | 983,040 |
| Tail rows fitted | 81,920 per policy | 491,520 |
| Root rows fitted | 163,840 per policy | 983,040 |
| Tail optimizer updates | `1,600 x 6 = 9,600` | 9,600 |
| Root optimizer updates | `3,200 x 6 = 19,200` | 19,200 |
| Tail / root example exposures | `x 256` | 2,457,600 / 4,915,200 |
| Hinge rows built | `6 x 81,920` | 491,520 |
| Exact solves | 3 per policy | 18 |
| Acquisition audits | 2 per policy | 12 |
| Exact policy evaluations | `8 x 12` | 96 |
| Sampled evaluation episodes / transitions | `64 x 8 x 12` | 6,144 / 16,512 |
| Non-finite events | 0 | 0 |
| Gradient clipping events | — | 1,839 of 28,800 (6.39 %) |
| Wall / CPU | under 30 minutes | **`61.827 s`** / `61.516 s` |

Every §5.2 count is nonzero and reconciles exactly. Single-threaded execution was **not** slower
than the four-thread comparable: the remedies object needed `181.865 s` for roughly six times this
workload, and this object's `61.827 s` for a sixth of it is the same order — consistent with the
repository's measured note that at this model size one thread is competitive with several.

## 4. The branch statistic — `A_paid`, four conjuncts per policy per arm

`A_paid` = `root_action(TARGET) == "PROBE"` **AND** `target_delta_acquisition > 0` **AND**
`direct_probe_component < 0` **AND** `root_action(cell) == "IMMEDIATE"` for every other cell.

### `MARGIN-AWARE-TREATMENT`

| Policy | pays at target | `delta > 0` | `cost < 0` | refuses elsewhere | `A_paid` |
| --- | --- | --- | --- | --- | --- |
| seed 00 fold 0 | true | true | true | true | **pass** |
| seed 00 fold 1 | true | true | true | true | **pass** |
| seed 01 fold 0 | true | true | true | true | **pass** |
| seed 01 fold 1 | true | true | true | true | **pass** |
| seed 02 fold 0 | true | true | true | true | **pass** |
| seed 02 fold 1 | **false** | **false** | true | true | **fail** |
| **count** | | | | | **5 of 6** |

### `EXACT-REFERENCE`

All six policies: `true, true, true, true` — **6 of 6**.

### The acquisition numbers behind conjunct 2

`learned_value(TARGET) = target_delta_acquisition + 0.794`; the oracle pays `0.815437`, a net
`+0.021437` over the `0.794` baseline; `shortfall = 0.021437 − delta`.

| Policy | treatment `delta` | treatment value | treatment shortfall | reference `delta` | reference shortfall |
| --- | --- | --- | --- | --- | --- |
| seed 00 fold 0 | +0.021437 | 0.815437 | 0.000000 | +0.021437 | 0.000000 |
| seed 00 fold 1 | +0.021437 | 0.815437 | 0.000000 | +0.018282 | 0.003155 |
| seed 01 fold 0 | +0.021437 | 0.815437 | 0.000000 | +0.018282 | 0.003155 |
| seed 01 fold 1 | +0.021437 | 0.815437 | 0.000000 | +0.021437 | 0.000000 |
| seed 02 fold 0 | +0.021437 | 0.815437 | 0.000000 | +0.021437 | 0.000000 |
| seed 02 fold 1 | **+0.000000** | **0.794000** | **0.021437** | +0.018282 | 0.003155 |

Three things this table settles.

- **Where the treatment pays, it captures the entire available gain.** In all five passing policies
  `delta` is exactly `+0.021437` and the shortfall exactly `0.000000`: the learner does not merely
  probe, it then plays the informed tail optimally on the held-out support at the target context.
- **The single failure is a refusal, not a mispricing.** Seed 02 fold 1 chose `IMMEDIATE` in all
  eight contexts, so its value at the target is exactly the `0.794` baseline and its shortfall is the
  whole `+0.021437`. Conjunct 2 fails there only as the arithmetic consequence of conjunct 1 failing:
  a policy that does not pay cannot have a positive delta.
- **The reference is not perfect either, and its imperfection is small.** Three of its six policies
  give up `0.003155` — the cost of the count-0 tail flips the tail-margin object measured at this
  offset — but `0.003155 < 0.021437`, so conjunct 2 still holds and it passes 6 of 6.

## 5. Competence, carried as a recorded field and never as a gate

**These fields decide nothing.** They are recorded because §11.1 requires it.

| Policy | treatment `C_even` | treatment agreement gate | treatment min agreement | treatment `A_paid` | reference `C_even` | reference `A_paid` |
| --- | --- | --- | --- | --- | --- | --- |
| seed 00 fold 0 | pass | pass | 1.000000 | pass | pass | pass |
| seed 00 fold 1 | **fail** | **fail** | 0.788446 | **pass** | fail | pass |
| seed 01 fold 0 | **fail** | **fail** | 0.788446 | **pass** | fail | pass |
| seed 01 fold 1 | pass | pass | 1.000000 | pass | pass | pass |
| seed 02 fold 0 | pass | pass | 1.000000 | pass | pass | pass |
| seed 02 fold 1 | fail | pass | 1.000000 | fail | fail | pass |
| **count** | **3 of 6** | **4 of 6** | | **5 of 6** | **3 of 6** | **6 of 6** |

The treatment's competence record **reproduces the published remedies record exactly**: `C_even`
flags `[true, false, false, true, true, false]`, agreement-gate flags
`[true, false, false, true, true, true]`, and count-0 margin gaps `+0.013707, +0.032587, +0.017488,
+0.027708, +0.030653, +0.024024`, each equal to its published value to the digit.

**Two policies satisfy `A_paid` while failing `C_even`** — seed 00 fold 1 and seed 01 fold 0, both
failing competence on the tail-agreement gate at `LINKED-p13_20` (`0.788446 < 0.95`), a stratum with
nothing to do with paying. That is precisely the case §11.1 was opened for, and it is now measured
rather than argued.

**The frozen conditional predicate, recorded beside `A_paid`.** `enforce_conditional_acquisition`
returned, for **all twelve** arm-policies of both arms: `acquisition_pass = false`,
`target_delta_acquisition = null`, `direct_probe_component = null`,
`suppressed_by_conditional_exposure = true`. No seed has both folds competent in either arm, so the
frozen path would have produced **no acquisition measurement at all** — including for the exact
reference, which pays correctly in 6 of 6. The card predicted exactly this; it is the concrete
vindication of opening the object under §11.1, and it is why the frozen `acquisition_pass` is
reported here as a recorded field and not as a finding.

## 6. `d_learned`, `d_objective`, exposure line

| Policy | treatment `d_learned_tail` | treatment `d_learned_root` | `d_objective` |
| --- | --- | --- | --- |
| seed 00 fold 0 | 0.069542 | 0.299801 | 0.018030 |
| seed 00 fold 1 | 0.260552 | 0.060653 | 0.038322 |
| seed 01 fold 0 | 0.205830 | 0.213414 | **0.180023** |
| seed 01 fold 1 | 0.129944 | 0.334460 | 0.020161 |
| seed 02 fold 0 | 0.201334 | 0.074973 | 0.015001 |
| seed 02 fold 1 | 0.150201 | 0.026696 | 0.041029 |

Against `eps_L = 0.10`: the treatment tail clears it in 1 of 6 and the root in 2 of 6 — and yet
`A_paid` holds in 5 of 6. As the root-conditioning object also found, on this problem the decisions
are correct well before the coefficients are, and `eps_L` is a parameter-space tolerance, not a
behavioural one. `EXACT-REFERENCE` has `d_learned = 0` by construction. Every value here equals the
published remedies `MARGIN-AWARE` number, as bitwise reproduction requires.

**Exposure line**, over the treatment arm only; `EXACT-REFERENCE` has no optimizer trajectory and is
excluded:

| Stage | min | median | max | raw per-coordinate ceiling |
| --- | --- | --- | --- | --- |
| tail | 1.423938 | 1.904952 | 2.142148 | `1,600 x 3e-3 = 4.8` |
| root | 0.902597 | 1.145174 | 1.808281 | `3,200 x 3e-3 = 9.6` |

Global min `0.902597`, max `2.142148`: the learner moves in its budget in all 12 rows and no stage is
step-budget-bound. Clipping at the frozen norm `1.0`: tail 793 of 9,600 (8.26 %), root 1,046 of
19,200 (5.45 %) — again identical to the published remedies figures.

## 7. Resource telemetry and concurrent load (recorded, never gating)

The declared concurrent load, recorded verbatim in the run record:

> two directions concurrently by owner instruction: this object (1 process, torch threads 1) and E2
> (2 four-thread runs); recorded as a one-off, observational only

This object kept its own process count at **one**, with one intra-op thread, as the card requires.

**The machine-side telemetry capture failed and is therefore unmeasured.** The runner invoked
`scripts/hmasd_resource_preflight.py capture` without the `--out` argument that subcommand requires,
so it returned a usage error, and the record carries `capture: null` with
`capture_error: "hmasd_resource_preflight.py capture: error: the following arguments are required:
--out"`. Under §11.4 a failed measurement sets the observation unmeasured and downgrades; it never
annuls, and it is not a gate. The **gating** admission — the central 4 GiB check — succeeded and is
in section 1. The run was not re-run to fix this: the object is consumed. The defect is in the
runner's telemetry helper only and touches no computed quantity.

## 8. The rule applied verbatim, in its stated order

The card's section 8, quoted, with the deciding numbers.

> - **`PA-A — PAID_ACQUISITION_POSITIVE`.** `MARGIN-AWARE-TREATMENT` satisfies `A_paid` in **all six**
>   policies.

Not satisfied. The treatment satisfies `A_paid` in **5** of 6
(`[true, true, true, true, true, false]`).

> - **`PA-B — PAID_ACQUISITION_MAJORITY`.** Not `PA-A`, but `MARGIN-AWARE-TREATMENT` satisfies
>   `A_paid` in **at least four** of six **and** `EXACT-REFERENCE` satisfies it in all six.

**Satisfied.** `5 >= 4`, the majority threshold fixed before data, and `EXACT-REFERENCE` satisfies
`A_paid` in **6 of 6** (`[true, true, true, true, true, true]`). **This is the published branch.**

> Reading: the behaviour is present and the residual is the learner's, not the problem's; the gap
> between the arm and the reference is the next object's subject.

The later branches were not reached: `PA-C` requires the treatment below four, `PA-D` requires the
reference short of all six, and `PA-E` is the residue.

**Branch published: `PA-B — PAID_ACQUISITION_MAJORITY`.**

The reading is confirmed sharply. The residual is a single policy, seed 02 fold 1, and it is the
*same* policy whose root action vector the root-conditioning object recorded as its one
oracle-root mismatch: on this draw that policy's root refuses to probe at the target context, which
costs it exactly the oracle net acquisition `0.021437` — the number that has recurred as a regret
throughout this chain and is here identified as what it always was, the price of not paying.

## 9. Verdicts on the recorded predictions

**Owner — "`PA-B`: the treatment arm satisfies `A_paid` in 4 or 5 of 6 policies, the exact reference
in 6 of 6."**

*By the rule's wording:* **borne out.** The branch is `PA-B`; the treatment is 5 of 6, inside the
stated range; the reference is 6 of 6, exactly as stated.

*By the numbers:* borne out on every quantity it named, with no over- or under-statement.

**Reviewer — "`PA-B`, treatment 5 of 6 and reference 6 of 6, the one treatment failure being a policy
whose root refuses to pay at the target context (the root object's 5-of-6 oracle-root match carried
forward), not a failed conjunct 2; the reference's count-0 flips at this offset cost it less than the
`+0.021437` net acquisition, so conjunct 2 holds for it in all six."**

*By the rule's wording:* **borne out.** `PA-B`, treatment exactly 5 of 6, reference exactly 6 of 6.

*By the numbers:* borne out on four of its five specific claims, and **precisely wrong in its literal
wording on the fifth**, in a way worth recording.

- Right: the branch, and both counts, exactly.
- Right: the failure is **a policy whose root refuses to pay at the target context** — seed 02 fold 1
  chose `IMMEDIATE` in all eight contexts, and its `oracle_root_match` is false, the same 5-of-6
  oracle-root pattern the root-conditioning object recorded.
- Right, quantitatively: **the reference's count-0 flips cost it less than the net acquisition.** The
  three reference policies with a negative count-0 gap (`−0.002267`, `−0.003461`, `−0.002090`) give up
  exactly `0.003155`, and `0.003155 < 0.021437`, so conjunct 2 holds and the reference passes 6 of 6 —
  the mechanism and the magnitude both as predicted.
- **Wrong as written: "not a failed conjunct 2."** Conjunct 2 *did* fail in that policy, with
  `delta = +0.000000`. The reviewer's causal claim is nonetheless correct: a policy that does not pay
  has `learned_value(TARGET) = baseline` identically, so conjunct 2 fails as an arithmetic consequence
  of conjunct 1 and not as an independent mispricing. The prediction identified the cause correctly
  and mis-stated which conjuncts would register it.

**Both predictions are borne out at the branch and at both counts.** This is the second consecutive
object whose prediction survives contact with the numbers, and the first in which both parties
converged on the same branch and the same counts in advance.

## 10. Deviations from the card

1. **The exact reference builds its root targets at float64**, matching the competence object's
   two-stage ceiling, while the treatment builds them at float32 through the frozen scorer arithmetic,
   matching the remedies arm it reproduces. The two paths were measured to agree to `O(1e-7)` in the
   competence object, against acquisition effects of `0.003155` and `0.021437` here — four orders
   below the signal.
2. **The telemetry capture failed** (section 7): `hmasd_resource_preflight.py capture` was invoked
   without its required `--out`. Recorded, never gating, not re-run.
3. **A launch-mechanics retry, which produced no artifact.** The first `Start-Process` invocation
   passed `--concurrent-load` unquoted, so PowerShell split the value on spaces and `argparse`
   rejected the trailing words. That failure occurred **before** `run_object` was entered: no output
   root was created, no preflight was taken, no RNG master, model or optimizer existed, and nothing
   was written anywhere. It is a shell-quoting error in the launch command, not a §6.2 event and not
   an incomplete attempt; the create-once guard was untouched and the relaunch two minutes later is
   the only execution of this object.
4. **Rows are built as flat numeric columns** permuted into the frozen canonical
   `(episode_index, context_id)` order rather than as `Episode` dataclasses through
   `training.train_policy`; the frozen `build_arm`, `optimizer_for`, `audit_policy_choices`,
   `enforce_conditional_acquisition` and `evaluate_policy` are used unmodified, and no checkpoints are
   written, so the checkpoint cadence and cold-resume seam are not exercised.
5. **The bound source inventory** is inherited from the remedies object's and extended with the
   remedies runner and this runner — 18 files, aggregate
   `0c51969b0c6888ba688ec8c52d3f192498de0f89611cc94e834d4dfb943fe7a1`, **clean** at launch.

No other deviation. The arms, the draw, the budget, the seeds, the folds, the hinge constants, the
thresholds and the branch order are exactly as carded.

## 11. Could not verify

- **Whether seed 02 fold 1's refusal is a property of that policy or of the draw.** One failing
  policy out of six at three seeds is not a population claim, and `EXACT-REFERENCE` is a reference,
  never a comparator for a claim.
- **Whether the treatment would pay correctly at another offset.** The draw was reused deliberately
  (card section 5) so the competence record and the reference are paired; that choice buys pairing and
  forgoes independence, and no second draw was taken.
- **The machine's memory and CPU state during the run.** The telemetry capture failed (section 7), so
  the concurrent load is recorded only as the declaration quoted there, not as a measurement. Nothing
  in the object depends on it.
- **Whether single-threaded execution is generally reproducible against four-threaded runs.** It was
  here, bitwise, on this workload. That is one observation on one machine, not a portability claim.
- **`FT-XF-FLEX` / `MT-XF-FLEX`**, other hosts, other hinge constants, the three-witness hinge: not
  run.
- **Reproduction.** One run, one machine, no re-run.
- **No dedicated A/RECON performance assessment** exists for this workload; `61.827 s` is an
  observation, not an admitted budget.

## 12. Interpretation boundary — the acquisition lock and COUNT/RAW

**This object opens neither lock and proposes no decision.**

- **`PAID_ACQUISITION_STATUS`.** The direction can now record that paid acquisition has been
  *measured*, on six policies of one arm, under a competence-free predicate frozen before data: the
  treatment pays correctly and profitably in **5 of 6**, the exact reference in **6 of 6**. As the
  card states for `PA-B`, that is not the same as satisfying the acquisition lock, whose own wording
  ties it to competence. Whether to relax that wording is an owner decision this card does not
  pre-empt.
- **`COUNT_RAW_STATUS` stays exactly where it is.** Its precondition is competence, which this object
  records and does not test. Under `C_even` the treatment is 3 of 6 and the reference 3 of 6 —
  unchanged from the published remedies record.
- **What the branch establishes, and hands forward.** Paid acquisition is not the direction's
  obstruction: where the learner pays, it captures the *entire* available gain (`shortfall = 0.000000`
  in all five passing policies). The residual is one policy's root refusal, worth exactly `0.021437`,
  and it is the same policy the root-conditioning object flagged. The arm-to-reference gap named by
  `PA-B` is therefore a single, localised, already-identified root-action failure.
- **Option A (owner's to take or leave):** an object on that one root refusal, which is now the whole
  of the arm-to-reference gap.
- **Option B (owner's to take or leave):** the three-witness hinge, still the parallel follow-up the
  card named in its section 11, untouched by this result.
- **Option C: do nothing.** `PA-B` supports no `PARK`, promotion, retirement or lifecycle change on
  its own, and none is proposed.

An outcome-informed rewrite of this card would be a **different scientific object**; this one is
consumed by a valid completed assignment and is not to be re-run with changes.
