# UCOPE-B-EXPLORE-PAID-ACQUISITION-B01 — card

- Direction: `ucope`
- Object id: `UCOPE-B-EXPLORE-PAID-ACQUISITION-B01`
- Evidence class of **this card**: **`A/RECON`** — it is a specification, written before any run of
  this object, and it computes nothing about any learner. The object it registers would be
  **`B/EXPLORE`**.
- Written: 2026-09-03 under the owner decision on D.22, **option (a)**: open the paid-acquisition
  object under spec §11.1 with **competence recorded, not required**.
- **Not run.** No output root exists, no learner has been trained for this object, and no acquisition
  quantity has been computed. The card awaits the two predictions in section 12.

## 1. The question, in one sentence

**Does the learner pay the probe cost exactly where information is worth buying — at the single
context of eight whose oracle net acquisition is positive — and does the information it then buys
leave it better off than not having paid?**

**Claim ceiling: `B/EXPLORE`.** On 3 seeds x 2 folds of one arm on one frozen eight-context host. The
object could not establish COUNT/RAW polarity, stable superiority, a seed-population effect, anything
about `FT-XF-FLEX`, or anything about variable `k`, variable `N`, MARL/UAV, transfer, safety,
deployment, flight, energy or real-world QoS. A positive outcome would be a statement about these six
policies under this criterion, not an acquisition claim for the direction.

## 2. Why the object can be opened now, and what §11.1 changes

Every prior object in this chain treated acquisition as unreachable, because the frozen code makes it
conditional on competence twice over:

1. `evaluation.enforce_conditional_acquisition` **suppresses** the acquisition fields —
   `target_delta_acquisition` and `direct_probe_component` set to `None`, `acquisition_pass` set to
   `false` — unless **both folds of a seed** are competent at the final root update.
2. The predicate `acquisition_pass` itself carries `competence_pass` as one of its conjuncts.

Under the published record that is not merely strict, it is **empty**. The best learner in the chain
so far, the `MARGIN-AWARE` arm of the remedies object, has `C_even` flags
`[true, false, false, true, true, false]` by `(seed, fold)`, so seed 00 is `(T, F)`, seed 01 is
`(F, T)` and seed 02 is `(T, F)`: **no seed has both folds competent**, and the frozen conditional
exposure would return `acquisition_pass = false` and `target_delta_acquisition = None` for every one
of the six policies, whatever those policies actually do about paying.

The owner decision on D.22, option (a), opens the object under spec **§11.1 with competence recorded,
not required**. This card therefore defines a **competence-free** branch statistic (section 4) and
carries the competence record and the frozen conditional `acquisition_pass` as **recorded fields that
never gate** (section 6). Nothing in the frozen code is modified: `enforce_conditional_acquisition` is
still called and its output still published, beside — not instead of — the object's own statistic.

## 3. The frozen acquisition arithmetic — outcome-free, from the oracle alone

Computed from `oracle.build_oracle()` and the frozen contract. No learner is involved and no draw is
read. `baseline` is the best immediate (no-probe) value at belief `1/2`; `probe_value` is the value of
paying and then playing the informed tail optimally; `direct_probe` is what paying costs;
`net_acquisition = probe_value − baseline`.

| Context | oracle action | baseline | probe_value | direct_probe | net_acquisition |
| --- | --- | --- | --- | --- | --- |
| `LINKED-p13_20-c9_100` | IMMEDIATE | 0.794000 | 0.773921 | −0.050000 | −0.020079 |
| `LINKED-p13_20-c7_50` | IMMEDIATE | 0.794000 | 0.723921 | −0.100000 | −0.070079 |
| **`LINKED-p17_20-c9_100`** | **PROBE** | 0.794000 | **0.815437** | **−0.050000** | **+0.021437** |
| `LINKED-p17_20-c7_50` | IMMEDIATE | 0.794000 | 0.765437 | −0.100000 | −0.028563 |
| `SEVERED-p13_20-c9_100` | IMMEDIATE | 0.794000 | 0.744000 | −0.050000 | −0.050000 |
| `SEVERED-p13_20-c7_50` | IMMEDIATE | 0.794000 | 0.694000 | −0.100000 | −0.100000 |
| `SEVERED-p17_20-c9_100` | IMMEDIATE | 0.794000 | 0.744000 | −0.050000 | −0.050000 |
| `SEVERED-p17_20-c7_50` | IMMEDIATE | 0.794000 | 0.694000 | −0.100000 | −0.100000 |

Three facts this fixes before data:

- **`LINKED-p17_20-c9_100` is the unique context where paying pays.** It is the only one with
  `net_acquisition > 0` and the only one whose oracle action is `PROBE`. It is also the fragile belief
  stratum the tail-margin object identified, and the `TARGET_CONTEXT_ID` the frozen contract names.
- **The exact margin of the whole question is `+0.021437`** (`17149681/800000000`). This is the same
  number that has recurred through the chain as the regret of a learner that chooses `IMMEDIATE` at
  the target context — because refusing to pay there costs exactly the oracle net acquisition.
- **`direct_probe` is negative in every context** (`−1/20` at the target). Paying is always a real
  cost; the question is only ever whether the information bought exceeds it.

**Frozen constants**, machine-checked against the code by
`tests/experiments/candidates/ucope/test_paid_acquisition_b01_card.py`:

| Constant | Value |
| --- | --- |
| `TARGET_CONTEXT_ID` | `LINKED-p17_20-c9_100` |
| `oracle_baseline_at_target` | `397/500` |
| `oracle_probe_value_at_target` | `652349681/800000000` |
| `oracle_direct_probe_at_target` | `-1/20` |
| `oracle_net_acquisition_at_target` | `17149681/800000000` |
| `oracle_probe_context_count` | `1` |
| `oracle_baseline_period` | `4` |
| `held_out_support` | `2,4,6,8` |
| `hinge_margin` | `0.024022` |
| `hinge_weight` | `1.0` |
| `hinge_witness_pair` | `5,9` |
| `tail_updates` | `1600` |
| `root_updates` | `3200` |
| `tail_rows_per_policy` | `81920` |
| `episodes_per_context` | `40960` |
| `learning_rate` | `0.003` |
| `batch_size` | `256` |
| `draw_offset` | `2000000` |
| `tail_reproduction_tolerance` | `1e-6` |
| `eps_L` | `0.10` |
| `majority_threshold` | `4` |
| `policies` | `6` |
| `thread_cap` | `1` |

## 4. The branch statistic — `A_paid`, competence-free

Per policy, on the even held-out support `K_eval = {2,4,6,8}` at the final root update, using
`evaluation.audit_policy_choices` exactly as the frozen code computes it:

> **`A_paid`** = `root_action(TARGET) == "PROBE"`
> **AND** `target_delta_acquisition > 0`
> **AND** `direct_probe_component < 0`
> **AND** `root_action(cell) == "IMMEDIATE"` for every other cell.

This is the frozen `acquisition_pass` **with its `competence_pass` conjunct removed and nothing else
changed**. That single removal is what the owner decision on D.22 option (a) authorises; every other
term, and the arithmetic behind each, is the frozen one.

Two properties are fixed here so the object's content is not mistaken:

- Conjuncts 1 and 4 together are exactly `oracle_root_match` against the frozen eight-context vector,
  because that vector is `PROBE` at the target and `IMMEDIATE` everywhere else (section 3). Conjunct 3
  is a constant of the host (`−0.05 < 0`) and is reported so the conjunction is visible in full, not
  because it can vary.
- Conjunct 2 carries the object's actual question. `target_delta_acquisition` is
  `learned_value(TARGET) − 0.794`, where `learned_value(TARGET) = learned_tail_value +
  direct_probe(cost)` under the policy's **own** held-out tail choices. So a policy can pay at the
  right context and still fail `A_paid`: **paying is not enough — the acquired information must be
  worth more than it cost.** That is the difference between this object and a root-action check, and it
  is why the object is worth running.

## 5. Arms

Two, on the **same draw**, so the reference is paired with the treatment policy by policy.

1. **`MARGIN-AWARE-TREATMENT`** — the whitened `MARGIN-AWARE` tail learner **exactly as run in the
   remedies object**: whitening from the training rows only at float64 under the unchanged Cholesky
   contract (`max abs(LL^T − G) <= 1e-10`, `lambda_min(G) > 1e-6`); the training-support hinge on the
   `(5, 9)` witness pair with **`m = 0.024022`** and **weight `1.0`** relative to the MSE term, as a
   batch mean; the ten-fold budget of **1,600 tail updates**, `lr 3e-3`, batch 256; **`n = 81,920`**
   tail rows per policy (`m = 40,960` episodes per context); and the root stage held at
   `WHITENED-ROOT-10X` with 3,200 root updates. *The D.22 text writes the hinge margin as `0.024`; the
   value actually run, and therefore the value frozen here, is `0.024022`.*
2. **`EXACT-REFERENCE`** — the exact two-stage solve on the same rows: the tail normal equations solved
   exactly, its coefficients fed through the frozen root target package, the root solved exactly.
   Outcome-free reference, no optimizer trajectory, excluded from the exposure line.

**Draw offset: `2,000,000` — the remedies object's draw, reused, not a fresh one.** Reasons, in order
of weight:

1. **The recorded competence field must be about the same learners.** Section 6 carries the
   `MARGIN-AWARE` competence record as a recorded field; that record is a property of the policies
   trained on the `2,000,000` draw. On a fresh draw it would describe different policies and the
   recorded field would be a non sequitur.
2. **The card requires the reference to be the exact solve on the same draw.** Pairing treatment and
   reference policy by policy is only meaningful on one draw, and comparing either against the
   published competence record requires that draw to be `2,000,000`.
3. **The rows are already a known prefix.** The remedies run generated `m = 81,920` episodes per
   context and used the first `40,960` for `MARGIN-AWARE`; this object needs exactly that prefix, at
   the same counter-addressed indices `i = 2,000,000 + j`, so no new index range is consumed and the
   offset stays disjoint from `0..5,119`, `0..319` and `1,000,000..1,081,919`.

**Tail-reproduction integrity item (gating).** The re-trained `MARGIN-AWARE` tail must reproduce the
remedies object's published per-policy coefficients to `max abs difference <= 1e-6` — the same
tolerance and construction the root-conditioning object used, where it observed `0.000000e+00`. A
failure means the treatment is not the learner this card names, so the object has not run its declared
assignment and **quarantines under §6.2**; it is not re-run with changes.

**One risk this card fixes in advance rather than discovering afterwards.** Section 9 requires
`torch.set_num_threads(1)`, while the published `MARGIN-AWARE` vectors were produced at four threads.
Intra-op thread count can change float32 reduction order, so the reproduction difference may be nonzero
where the root object saw exactly zero. The gate is therefore the `1e-6` tolerance, not bitwise
equality, and the observed difference is recorded per policy whatever it is. If it exceeds `1e-6` the
object quarantines rather than proceeding on a learner it cannot identify.

## 6. Competence, carried as a recorded field and never as a gate

The run record must carry, per arm, a `competence_record` block containing:

- **`c_even_count` and `c_even_flags`** — the frozen five-component predicate, per policy;
- **`agreement_gate_count` and `agreement_gate_flags`** — `min_forced_PROBE_tail_agreement >= 19/20`,
  per policy;
- **`margin_sign_per_policy`** — the sign of the count-0 `(6,8)` top-two gap in the target stratum, per
  policy;
- **`frozen_conditional_acquisition`** — the output of `enforce_conditional_acquisition`
  (`acquisition_pass`, `target_delta_acquisition`, `direct_probe_component`) exactly as the frozen code
  returns it, so the difference between the frozen conditional predicate and this object's `A_paid` is
  visible on the page rather than argued.

For the treatment arm these are already known from the published remedies run and the object must
reproduce them: `c_even_flags = [true, false, false, true, true, false]` (**3 of 6**),
`agreement_gate_flags = [true, false, false, true, true, true]` (**4 of 6**), and the margin sign
**positive in 6 of 6** policies (`+0.013707, +0.032587, +0.017488, +0.027708, +0.030653, +0.024024`).
Under `enforce_conditional_acquisition` no seed has both folds competent, so
`frozen_conditional_acquisition.acquisition_pass` is expected `false` in all six with the two value
fields `null` — recorded, and **not** a finding about acquisition.

**None of these fields appears in the reading rule of section 8.** They are recorded because §11.1
requires competence to be recorded, and because a reader must be able to see that the object's result,
positive or negative, is not a competence result in disguise.

## 7. Measurements

Per arm and per policy:

- **`A_paid`**, with its four conjuncts reported separately so a failure names its own cause. **This is
  the branch statistic.**
- `target_delta_acquisition` (float) and the learned value it implies,
  `learned_value(TARGET) = target_delta_acquisition + 0.794`, against the oracle `0.815437`.
- `direct_probe_component`, and the root action vector over all eight contexts.
- The **acquisition shortfall** `oracle_net_acquisition − target_delta_acquisition`
  (`+0.021437 − delta`), for the record: it says how much of the available gain the policy captured.
- The competence record of section 6.
- `d_learned_tail`, `d_learned_root` and `d_objective` against `eps_L = 0.10`, carried unchanged.
- The whitening contract numbers per stage (`kappa`, `lambda_min(G)`, `max abs(LL^T − G)`).
- The tail-reproduction difference against the published vectors.
- One machine-generated **exposure line** over the treatment arm's two stages; `EXACT-REFERENCE` has no
  optimizer trajectory and is excluded.

## 8. Reading rule — written before data, branches ordered by effect size

Thresholds, all fixed here and none of them new: `A_paid` as defined in section 4, with `>` and `<`
strict and `oracle_root_match` an exact equality against the frozen eight-context vector; **"majority"
is at least 4 of 6** policies, carried unchanged from every prior object in this chain; `eps_L = 0.10`.
Competence introduces no threshold, because it does not appear.

Branches, in the style of the remedies object's `M-A .. M-E`, evaluated in this order; exactly one
applies.

- **`PA-A — PAID_ACQUISITION_POSITIVE`.** `MARGIN-AWARE-TREATMENT` satisfies `A_paid` in **all six**
  policies. Reading: on this host the learner buys information exactly where it pays, and profits by
  doing so. This is the strongest outcome the object admits.
- **`PA-B — PAID_ACQUISITION_MAJORITY`.** Not `PA-A`, but `MARGIN-AWARE-TREATMENT` satisfies `A_paid`
  in **at least four** of six **and** `EXACT-REFERENCE` satisfies it in all six. Reading: the behaviour
  is present and the residual is the learner's, not the problem's; the gap between the arm and the
  reference is the next object's subject.
- **`PA-C — REFERENCE_ONLY`.** `EXACT-REFERENCE` satisfies `A_paid` in all six and
  `MARGIN-AWARE-TREATMENT` in fewer than four. Reading: paying correctly is reachable on this draw, and
  the **learner** is what fails to reach it.
- **`PA-D — REFERENCE_NOT_POSITIVE`.** `EXACT-REFERENCE` does not satisfy `A_paid` in all six. Reading:
  the exact optimum on this draw does not itself buy information profitably, so the object is a
  statement about the draw and the criterion, not about any learner. The failing conjunct says which.
- **`PA-E — UNCLEAR`.** Any other combination. Report every number, name what is unexplained, propose no
  successor on the strength of a `PA-E`.

Descriptive and deciding nothing: the competence record in every form, the frozen conditional
`acquisition_pass`, the acquisition shortfall, `d_learned_tail`, `d_learned_root`, `d_objective`, the
whitening numbers, the reproduction difference and the exposure line. At three seeds no arm-comparison
polarity, stable-superiority or seed-population claim is available, so `EXACT-REFERENCE` is a reference
and never a comparator for a claim.

## 9. Launch conditions (spec §11.4) and budget

Still gating: the central 4 GiB physical and effective memory admission immediately before the
workload, with the receipt written under the output root; the §4 integrity items — group-disjoint
folds, the odd-training / even-held-out separation (the hinge reads only `K_train` periods `5` and
`9`), no read of B1 or audit runtime rows, counter-addressed data at `i = 2,000,000 + j`, whitening
from training rows only per stage, and the **tail-reproduction check at `1e-6`** of section 5; the §5.2
nonzero counts reconciled exactly; one machine-generated exposure line. Recorded and never gating:
source-inventory cleanliness, the absence of a dedicated A/RECON performance assessment, execution
topology, resource telemetry, **the competence record of section 6**, and the direction's own
sequencing locks. Learner-side instrumentation failure quarantines under §6.2.

**Execution: a single process with `torch.set_num_threads(1)`**, deterministic algorithms on, as the
D.22 decision specifies. See the reproduction-tolerance note in section 5 for the one consequence this
has.

**Budget: under 30 minutes wall.** Generating `40,960 x 8 x 3 = 983,040` episodes cost about `70 s` at
four threads in the two measured runs and is the dominant term; the treatment is
`6 x (1,600 + 3,200) = 28,800` optimizer steps on 5- and 7-parameter models at batch 256; the six exact
solves and the Cholesky factorisations are milliseconds; the evaluations are 8 contexts x 2 arms x 6
policies with the frozen sampled diagnostic. Single-threaded execution is expected to widen the wall
time by a small multiple and stays far inside 30 minutes. Outputs under
`temp/directions/ucope/exp/paid_acquisition_b01_<date>/`.

## 10. What each branch would mean for the acquisition lock and COUNT/RAW

The direction records `PAID_ACQUISITION_STATUS=UNEVALUATED_LOCKED` and
`COUNT_RAW_STATUS=LOCKED_UNTIL_COMPETENCE`. Under the section-11 recast those are the direction's own
sequencing choice, recorded and not §11 gates. **This card opens neither, and no branch below opens
either; each says only what would be placed in front of the owner.**

- **`PA-A`** would be the direction's first measured paid-acquisition behaviour, and would move
  `PAID_ACQUISITION_STATUS` from `UNEVALUATED` to *evaluated on six policies under a competence-free
  predicate* — which is not the same as satisfying the acquisition lock, whose own wording ties it to
  competence. Whether to relax that wording is an owner decision this card does not pre-empt.
- **`PA-B`** would establish the behaviour with a residual, and make the arm-to-reference gap the next
  object.
- **`PA-C`** would keep both locks and make the learner the next subject, as `C-C` and `R'-B` each did
  in their turn.
- **`PA-D`** would keep both locks and turn the question to the draw and the criterion.
- **`PA-E`** would keep both locks and propose nothing.

`COUNT_RAW_STATUS` is untouched by every branch: its precondition is competence, which this object
records and does not test. No branch supports `PARK`, promotion, retirement or a lifecycle change on
its own.

## 11. Parallel follow-up, noted once and deliberately not an arm

The remedies object closed on `M-B` with its two residual failures landing on the `(2,4)` and `(4,6)`
held-out decision directions, whose `K_train` witnesses `(1, 5)` and `(3, 7)` the single-pair hinge
never constrained. A **three-witness hinge** object is the obvious successor there. It is **not an arm
of this object and not a variable here**: this card fixes the treatment learner as the one actually
run, so that the acquisition question is asked of a learner whose competence record is already
published. The two objects are parallel, and neither is a precondition of the other.

## 12. Predictions requested from the owner and the reviewer

To be filled in before launch. Nothing in sections 1 to 11 may change when they are recorded.

**Owner:**

> _(empty — to be recorded before the run)_

**Reviewer:**

> _(empty — to be recorded before the run)_

## 13. Deviations

_(empty — no run has taken place. This section exists so the result document has a place to carry
deviations from this card, and so that its emptiness here is on the record.)_

## 14. Could not verify

_(empty — no run has taken place. This section exists so the result document has a place to carry what
could not be verified, and so that its emptiness here is on the record.)_
