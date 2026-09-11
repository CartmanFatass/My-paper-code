# N3 DISH B01 C04 seed 11 — result evidence

Date: 2026-09-04. Class: **B / EXPLORE**. One valid complete seed observation; the three-seed
comparison is incomplete and has no aggregate `FTS-*` branch. A/B have no consumption state.
Card: `DISH_FIRST_TRIGGER_SOURCE_SCOUT_B01_SCIENCE_CARD_20260904.md`, with the prospective
description supplement at `271489d1`; launch selection `551fd251f`.

## Observation and bounded reading

After 64 real native learner updates, seed 11 produced **zero first-valid triggers in all sixteen
declared evaluation rows**. All rows exhausted their 1,200-tick prefixes. No RETAIN, COPY or SHADOW
consequence branch was materialized, so this seed does not estimate source value, source equality,
nonharm, or a five-tick MEI contrast. It supplies an observed trigger-support failure on this
one checkpoint/panel at this exposure, not a failure of the source mechanism or N3 route.

The raw summary retains `delta_copy=0`, `delta_shadow=0`, `delta_shadow_worst20=0` and
`shadow_nonharm=true`. These are empty-support reducer values. They are not sampled equal returns
or observed nonharm and are not used as such. `usable_trigger_support=false` is the applicable
support reading.

## Rule applied verbatim

The card says: "A seed has **usable trigger support** when at least four of sixteen rows trigger
and the triggered set contains both packages."

Observed `trigger_count=0` fails that definition. Both packages were evaluated; neither supplied
a triggered row. The aggregate rule's input instruction is: "Apply the following branches in
order to three complete seed summaries:". Only seed 11 is complete, so no aggregate branch is
applied. In particular, the three-seed `FTS-B0` verdict is not assigned early and the empty-support
zeros cannot select `FTS-BC` or `FTS-BN`.

No-trigger rows are explicitly valid under card section 5; zero conditional branch measurements
are expected here, not missing learner instrumentation. Seeds 29 and 47 remain required under
the unchanged card, with no efficacy/trigger-based early stop.

## Counts and exposure

| Quantity | Observation | Card |
| --- | ---: | ---: |
| Completed independent learner seeds | 1 (11) | 3 (11,29,47) for aggregate |
| Native training transitions | 262,144 | 64 x 4,096 |
| Learner updates | 64 | 64 |
| Optimizer minibatch steps | 2,048 | 64 x 32 |
| Evaluation rows / distinct tuples | 16 / 16 | 16 / 16 |
| Evaluation prefix ticks | 19,200 | 16 x 1,200 when no trigger |
| Triggered rows / branch consequence ticks | 0 / 0 | conditional on first-valid trigger |
| Checkpoint update | 64 | 64 |
| Model tensors / finite | 50 / all | finite |
| Optimizer states / finite | 36 / all | finite |
| Optimizer step values | all 2,048 | 2,048 |

The panel is exactly two packages x K8/K4_TO_K12 x speeds 4/8 x within-speed slots 0/3, block 0,
degradation on. DM independently reconstructed these sixteen tuples and the zero-trigger total
from the original JSON, and checked 19,200 prefix ticks against the exhaustive no-trigger law.
CM read the existing checkpoint without instantiating a model or running the learner again.
Actor/critic/snapshot Welford counts were 1,048,576 / 262,144 / 0.

Actual float64 exposure: initial parameter norm **38.19731474061207**, final norm
**41.78517869974931**, total relative L2 displacement **0.42465718774783356**. CM independently
recomputed the final norm from checkpoint tensors and matched it exactly. Initial checkpoint
bytes are not separately published, so the initial norm/displacement remain original runner
observations rather than a two-artifact independent reconstruction.

Raw maximum per-tensor displacement ratio **1.2535341627432597e300** is retained. The code divides
by `max(initial_tensor_norm,1e-300)` and initializes biases to zero; this ratio is dominated by a
zero reference, not a meaningful relative percentage. All inspected model/optimizer values and
the total displacement are finite. No post-result formula change or numerical-failure claim is
made. The usable total exposure shows nonzero learning movement, not checkpoint competence.

## Receipts, cost and artifacts

- Exact source: `e0541d0cb3e9e63731c72f4dacb10b44d268fd39`.
- Node: `wsl_4070`, SSH `hmasd-wsl-node`, CPU/one Torch thread, carded FP32 learner/float64 native.
- Cwd: `/home/wu/hmasd-worktrees/dish-b01-c04-e0541d0c`.
- Supervisor: `dish_b01_c04_seed11_e0541d0c_a1`, PID 112219, exit 0.
- Start/terminal: `2026-09-05T00:12:03Z` / `2026-09-05T00:30:22Z`; supervisor wall **1099 s**.
- Runner wall: **1068.1102725170058 s**; peak RSS **628,801,536 bytes**;
  `resources_unmeasured=false`. Charge the complete runner wall to each source arm; even the
  conservative supervisor charge is below the **1,800 s** cap and **1,474.544745605439 s** projection.
- Admission at `2026-09-05T00:12:03.356900Z`: physical and effective available memory each
  **12,531,122,176 bytes**, against **4,294,967,296**, all pass flags true.
- Receipt: cwd-relative `temp/directions/degraded_incumbent_shadow_handover/exp/n3_b01_c04_20260904/seed11_a1_admission.json`.
- Raw root: cwd-relative `temp/directions/degraded_incumbent_shadow_handover/exp/n3_b01_c04_20260904/seed11_a1/`.
- Log and supervisor witnesses: `/home/wu/.agent-tasks/dish_b01_c04_seed11_e0541d0c_a1/`.

CM collected `summary.json`, the **2,070,711-byte** `checkpoint.pt`, task log/wrapper and receipt
under the same relative root in `C:/Projects/HMASD-worktrees/cm-n3-dish-c04-20260904`.
Original remote artifacts remain unchanged. The raw summary is tracked as
`N3_DISH_B01_C04_SEED11_SUMMARY_20260904.json`; collection record is
`N3_DISH_B01_C04_SEED11_COLLECTION_20260904.md`, pushed at
`17018ec74592c0b29254006006fac03f951e22c5`.

This buys one valid learner-seed observation. Training/verification preparation and earlier DISH
history are separate costs; no total-history or agent-token cost is inferred. The earlier static
runner projection remains the queued-seed cost law; measured seed 11 cost does not change their
budget or selection.

## Validity, limits and prediction

The real learner-to-no-trigger-evaluation-to-publication path completed. Counts, finite checkpoint,
actual exposure, exact panel and receipt match the card. No scientific/numerical/RNG/checkpoint/
side-effect deviation, section-4 addition, section-5 breach or invalid attempt was identified.
The automated smoke still does not cover full `_run` publication with real constants; retain this
open engineering item. A triggered scientific 100-tick branch remains unobserved, although its
TEST conformance path was previously checked. Exit 0 alone was not used to establish validity.

The original DM prediction of insufficient support is consistent with this one seed; its
three-seed prediction is not yet scored. Owner prediction item `20260904-dish-010` has no reply:
**not taken (unattended)**. Tuned B01 headroom remains absent.

Strongest support is the complete no-trigger census over all sixteen prescribed prefixes despite
nonzero training exposure. The limit against a broad negative is that neither source intervention
was exposed, only one learned checkpoint was sampled, and the cause of no trigger is unidentified.
Commit-head competence, physical opportunity and seed/budget/panel dependence remain live
explanations. The next discriminator is the unchanged remaining-seed panel, not an equality claim.
