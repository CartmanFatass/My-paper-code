# DISH retained-prefix A01 — result evidence

Date: 2026-09-05 PDT. Object `DISH-PREFIX-TRIGGER-FUNNEL-A01`, **A / RECON**.
Result: **A01-PREFIX-FUNNEL-OBSERVED**. All sixteen rows reproduce the original prefix
reference; each has **PREPARATION_SUPPORT_GAP**, missing stage **snapshot_delivery**.

## E0 — question, original rule and bounded reading

This diagnostic asks where the handover exposure chain stops on the retained seed-11
checkpoint and original B01 sixteen rows. It adds no learning, source intervention,
policy change or new independent learner seed.

The card's complete-object rule applies verbatim:

> The complete object result is **A01-PREFIX-FUNNEL-OBSERVED** when all sixteen rows and required
> measurements are complete and the original no-trigger/prefix-count reference is reproduced.

All sixteen ordered original tuples match, with 1,200 inspected and completed ticks per
row, 19,200 total and zero triggers. For every row the first-absent-stage reading passes
live renewal, prepare proposal and latch presence, then stops at **snapshot delivery**.
The later no-commit/no-intent branches are not substituted for that ordered label.
Underlying counts remain visible; the label does not imply that later gates would pass.

This establishes a measurement fact on one retained checkpoint: preparation proposals
and latching occurred, but common-source support and snapshot delivery were never
observed. It narrows the missing exposure upstream of an actual handover. It does not
show a remedy, shadow-state value, source equality, general policy competence, physical
impossibility, native-host defect, or algorithm effect. B01 remains valid FTS-B0; the
five-service-tick source MEI is still unidentifiable.

## Counts, timing and exposure

| Quantity | Complete observation |
| --- | ---: |
| Original ordered rows / triggered | 16 / 0 |
| Inspected / completed prefix ticks | 19,200 / 19,200 |
| Live prepared inputs / terminal padding | 19,200 / 0 |
| Live renewal opportunities | 2,720 |
| Owner prepare proposals / commit proposals | 2,234 / 1,131 |
| Live prepared latch / live completion latch occupancy | 19,132 / 19,148 |
| Prepare with existing prepared latch | 2,218 |
| Commit with existing prepared latch | 1,131 |
| Common-source support | 0 |
| Snapshot / readiness deliveries and accepted-state occupancy | all 0 |
| Version-ready / its renewal-latch-commit conjunctions | all 0 |
| Emitted / prepared pending intents, all margin/certificate partitions | all 0 |
| Application-valid / CAS / invalid-commit increments | all 0 |
| Native service ticks | 0 |
| New training transitions / learner updates / optimizer steps | 0 / 0 / 0 |
| Actual parameter displacement in each of sixteen rows | 0 |

Every row has at least one prepare proposal and latch. Ten rows have commit proposals;
six have none, but the earlier snapshot-delivery stage is absent in all sixteen. Maximum
warmup ranges 1,193–1,199 ticks. These occupancy and proposal counts have different
denominators and are not probabilities of success. Detailed row counts are in the CM
collection table and raw summary.

Each row's first terminal event occurs only at completion of action tick 1,199 / native
tick 1,200; there is no early-terminal padding explanation for this observed absence.
First-terminal batteries remain positive, 51,853.90409100452–64,523.99873586311. No
physical cause is inferred from those endpoints. Both recorded source-exists flags at
that boundary are zero on every row. Common-source occupancy is directly zero across
the full observed prefix; the endpoint flags alone are not a separately instrumented
time series of each individual source receiver.

Each reason histogram is `{0: 1200}`. Reason zero means no recorded nonzero application
reason here, not a successful application. Missing-stage first-occurrence values are
explicitly null; they are complete absence measurements, not missing instrumentation.

Retained parameter norm is 41.78517869974931 before/after each row and all sixteen
measured L2/relative displacements are exactly zero. Inherited B01 exposure remains
2,048 optimizer steps, initial norm 38.19731474061207, final norm 41.78517869974931,
relative displacement 0.42465718774783356. Zero new exposure is correct for this A object.

## Source, receipts, artifacts and resource use

- Diagnostic source `bfe4952beeff9cff237d5b16325c02e5c0c08664`; original R06/B01 source
  surface unchanged from `e0541d0cb3e9e63731c72f4dacb10b44d268fd39`.
- Original seed-11 checkpoint: 2,070,711 bytes; pre/post input SHA256
  `0020137d98e23f06a71048daf5906d7835545fd38cc8a1399bbeee15e11df4fa`.
- Node `wsl_4070`; cwd `/home/wu/hmasd-worktrees/dish-prefix-a01-bfe4952b`;
  task `dish_prefix_funnel_a01_seed11_a1`, PID 1610547, existing exit witness 0.
- Start `2026-09-05T09:15:15Z`, terminal `09:17:20Z`; logged supervisor wall **125 seconds**.
  Runner wall **115.94635876399116 seconds**, peak RSS **369,057,792 bytes**,
  `resources_unmeasured=false`; scratch was not measured. Both wall observations fit
  the prospective 450-second projection / 600-second cap. The whole replay path is charged
  once to A01; no source-arm multiplier or new-throughput claim is used.
- Fresh admission assessed `2026-09-05T09:15:15.165793Z`, physical/effective available
  each **12,650,926,080 bytes**, both floor flags and passed true, floor 4,294,967,296.
- Original output: cwd-relative
  `temp/directions/degraded_incumbent_shadow_handover/exp/n3_prefix_funnel_a01_20260904/a1/summary.json`;
  separate receipt sibling `a1_admission.json`; witnesses in
  `/home/wu/.agent-tasks/dish_prefix_funnel_a01_seed11_a1/`.
- Collected originals are under the same relative output root in
  `C:/Projects/HMASD-worktrees/cm-n3-dish-funnel-a01-20260904`, with `a1/task.log`.
- Tracked raw summary `DISH_PREFIX_TRIGGER_FUNNEL_A01_SUMMARY_20260905.json` and
  `DISH_PREFIX_TRIGGER_FUNNEL_A01_COLLECTION_20260905.md` are pushed at
  `a6ff9d7489e5187a3c95b026283b458350a0d7c9`. Raw summary is **240,765 bytes**, SHA256
  `ba7d3b25cd59e2c69b815c63adc9b0865838a8b386c8bf21840c5e9ed2ca07f1`.

## Independent intake checks and engineering limits

DM compared original JSON bytes with the committed Git blob, reconstructed all sixteen
ordered tuples, recomputed the row labels and complete-object reference rule, summed
counts, and checked per-row inspection/completion/live counts, proposal bounds, reason
totals, presence-versus-first-occurrence consistency, timing offsets and zero parameter
movement. All agree with the card and CM collection. CM checked finite JSON, retained
input digest, raw artifact preservation and technical completeness without rerunning a
policy or native step. Direct facts are separated from explanations of their absence.

No scientific, precision, RNG, checkpoint or side-effect deviation was observed. Three
new files add 315 non-test lines, runner 66, conservative orchestration 89/315 = 28.3%;
scope section-4 additions none, no section-5 breach. Independent review and four focused
tests cover the measurement conventions. The reproduced missing pytest scratch parent
was fixed command-only before the actual toy publication smoke; no scientific attempt
was repaired or replaced. Full-size A01 publication has now completed.

Nonzero downstream intent/margin/application paths were not exposed by this actual
checkpoint. Synthetic tests remain engineering evidence only. This diagnostic does not
resolve B01's open full automated publication-path coverage or supply its unobserved
source forks. No A/B consumption state or direction disposition is created.

## Predictions, support, contradiction and next discriminator

The DM predicted reference reproduction with preparation support absent on most rows;
both match the complete measurement (16/16 rows missing snapshot delivery). Owner
prediction remains **not taken (unattended)**. The earlier B01 prediction remains separately
scored. One observed stage occurrence was the A card's event-resolution MEI: prepare,
commit and latch occurrences exceed it, while delivery remains absent. This is not a
return effect size. Tuned same-information B01 headroom remains absent; zero service on
this checkpoint does not estimate headroom against a competent upper reference.

Strongest support is repeated preparation/latch presence with no common source or
snapshot delivery, despite complete live prefixes. Strongest limit is one checkpoint
and no intervention on the absent stage. Radio/geometry support, source admission,
normalization/action competence and later protocol constraints remain live explanations.
The next useful discriminator qualifies the host's ground-source observation/admission
path over the same recorded source before investing in more training or altering physics.
