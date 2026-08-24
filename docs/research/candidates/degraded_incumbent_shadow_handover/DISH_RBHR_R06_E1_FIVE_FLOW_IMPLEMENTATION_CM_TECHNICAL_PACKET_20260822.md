# DISH RBHR r06 E1 five-flow implementation CM technical packet — 2026-08-22

```text
document_kind=code_manager_e1_five_flow_implementation_technical_packet
direction_id=degraded_incumbent_shadow_handover
exact_object_revision=DISH-RBHR-SCIENCE-20260822-06
portfolio_boundary=docs/session/PORTFOLIO_TO_ROOT_DISH_RBHR_R06_FINITE_TWO_STAGE_ENGINEERING_EXPANSION_20260822.md
technical_disposition=E1_COMPLETE|ALL_FIVE_FLOW_LOCAL_FAMILIES_ACCEPTED
e1_actual_engineer_days=48
e1_hard_ceiling_engineer_days=76
remaining_e2_forecast_engineer_days=CENTRAL25|HIGH41
total_forecast_engineer_days=CENTRAL73|HIGH89
hard_total_ceiling_engineer_days=117
e2_release_gate_technical_fact=SATISFIED
question_relevant_output=false
identity_or_activity=false
r05_action=false
```

## Decision-level conclusion

E1 is complete for all five required unchanged-science production families.
The current source supplies master-addressed 32-lane TRAIN reset rows, a native
batched recurrent policy/persistent 1,024-update trainer, checkpoint-loaded
five-arm paired-mask evaluation, a first-application-valid native REAL/SHAM
runner, and the complete 24-by-6,990 reducer with master-addressed 99,999-
resample joint inference.

The deterministic flow-local receipt accepts every family and the r06-only
native ABI. It created no scientific master, identity, coordinate, tape,
model, checkpoint, training, evaluation, inference matrix, branch result,
partial value, or question-relevant output. No E2 cross-flow integration,
independent TEST acceptance, resource remeasurement, lease-request preparation
or lease action occurred.

## Completed flow families and flow-local evidence

| E1 family | Implemented source | Flow-local self-audit fact |
|---|---|---|
| 32-lane TRAIN reset | `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_train_reset.py` | Exactly 32 consecutive lanes, eight regime/schedule cells, four lanes per cell; master-addressed Omega permutation, identity law, common physical rows and arm-slot binding are source-bound. |
| Native recurrent persistent trainer | `production_recurrent_trainer.py`, `production_training_engine.py`, `production_backend.py`, native C++ | Exactly 32 lanes x 128 ticks = 4,096 transitions/update and 1,024 persistent updates; native selected reset, physical-copy recurrence/promotion, master-addressed Xavier/policy draws, native passive-label clone and sole checkpoint boundary are source-bound. |
| Five-arm mask-on/off evaluator | `production_evaluator.py` | Exactly 11,520 base tapes x two paired mask views x five independently checkpointed arms = 115,200 unique episodes; native batch width is 32 and the paired views retain common physical randomness. |
| First-valid REAL/SHAM runner | `production_real_sham.py`, native C++ | Nonmutating native application predicate precedes clone; only first-valid unconsumed rows fork; REAL/SHAM transaction telemetry is byte-identical and both branches run exactly 100 ticks on paired future physical addresses. |
| Complete reducer/inference | `production_reducer.py`, `production_inference.py` | All 6,990 unique estimands bind one of ten frozen source families for each of 24 blocks; duplicates and incomplete matrices fail closed; production bootstrap uses the future master and all 99,999 common block-resample vectors. |

Controlling flow-local receipt:

```text
runtime/benchmarks/dish_rbhr_r06_e1_flow_local_self_audits_20260822.json
sha256=9ea4b9dcef2e9e1fa277106952760392c4bd456a2c0e0a38ac9d66e90bbc4af5
all_five_families_flow_local_accepted=true
question_relevant_output=false
```

The receipt additionally records native ABI version 1, reset input 144 bytes,
step input 4,640 bytes, state 5,616 bytes and step output 2,496 bytes. The
nonmutating first-application predicate, passive-label shapes and paired-mask
common-randomness fixture all pass. These are flow-local deterministic E1
checks, not E2 independent TEST acceptance.

## Current source identities

```text
experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/native/rbhr_r06_production_backend.cpp=a86ce19c009cf8a2e65de72ea70b81b5db5e2bc48ab539ce01bcff605d45606e
experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_backend.py=5b649804ead996605b15df07ef3c5e4dbff17453226679b5439208862fb19dc0
experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_evaluator.py=035364bdb8cc36a9d5b24a695c3af3b46455a00b6dca78766d698cbcc65c63db
experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_inference.py=24e665ce6ed559e54a4292de065b4d9cf1bc1550eceee34271d7775d3a08227d
experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_preactivity.py=91593ce5e1a218b78b60f473398cf0f065bdcf28d583213d90f755bd18b77f51
experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_real_sham.py=77a6969e22df25961784acecd268c2d141ca2a06fdf4b2eb6ee15dd5bde4bf98
experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_recurrent_trainer.py=a651e0ffb07de56aea97d3a725f94e515749fb380946e8355872dc61c1e0e566
experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_reducer.py=3eb06a62159205c6c6470e467a8f000877dc78b73b98233943d53e3671a567e6
experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_train_reset.py=4f8e8d63ef5b0c396ffe3deaf63f6a426688930be9412aad18c476955ef572c3
experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_training_engine.py=8b84c7c5192be7f555b7335718021c1542c67eeef442b6ffea23df0dc30e3a27
experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_e1.py=8cf6911c08f62013ad7340235a49eed84a670f0fc9ce96e209d4a59c74bdb6ae
tools/experiments/run_dish_rbhr_r06_e1_self_audits.py=91319122235f935a030e9f761f17da6b6f374809c5fd291cc94c0dd09fcb988b
```

The receipt is the authoritative current-byte source-hash manifest. The list
above is duplicated only to make this decision packet self-contained.

## Engineer-day accounting and remaining forecast

E1 uses **48 scope-accounted experienced-engineer-day equivalents**, matching
the central five-flow decomposition: TRAIN reset 5, recurrent persistent
trainer 14, evaluator 12, REAL/SHAM 7 and reducer/inference 10. This is the
finite engineering-envelope accounting unit; no external human time ledger or
empirical runtime is represented by it.

E1 is therefore 28 days below its 76-day hard ceiling. The unchanged remaining
E2 forecast is 25 central / 41 high engineer-days. With E1 actual fixed at 48,
the remaining total forecast is 73 central / 89 high, below the 117-day hard
total ceiling. Unused E1 capacity is not transferred to E2.

## Invalidation checks

All E1 invalidation predicates remain false:

- no treatment, comparator, threshold, branch, checkpoint law, coordinate,
  population, inference family or claim changed;
- exact inventories remain 11,520 base tapes, 120 training jobs, 1,024 updates
  per job, 503,316,480 training transitions, 115,200 evaluation episodes,
  6,912 potential REAL/SHAM forks, 6,990 estimands and 99,999 joint resamples;
- one future fresh blinded nonreplaceable r06 identity remains the sole
  production identity; none exists now and no replacement path was added;
- native recurrence, persistent optimizer/Welford/hidden state, paired
  mask-on/off physical randomness, first-valid REAL/SHAM suborder, complete
  reduction, result blindness and fail-closed completeness are retained;
- no Python environment or rollout fallback, panel shrink, partial value,
  substrate replacement or r05 reuse/action was introduced; and
- prior ordinary `320 CPUh / 65 wall h` and hard resource envelopes remain the
  controlling forecast. E1 performed no resource remeasurement; current-byte
  full-chain remeasurement remains explicitly in E2.

## Expected E2 risks, not E1 invalidations

The following remain deliberately unestablished until conditional E2:

1. cross-flow binding of these five families into the existing full-panel
   frontier/executor and result firewall;
2. independent TEST acceptance of master/reset, recurrent resume, arm/mask
   pairing, fork lineage, complete reducer and bootstrap equivalence;
3. end-to-end result-blind failure-atomic reacceptance and same-identity
   successor-slice recovery;
4. current-byte CPU/wall/RSS/scratch/durable/I/O remeasurement; and
5. exact lease-request preparation and final `lease_request_issuable` ruling.

Those are the already-budgeted E2 scope, not permission to issue a lease or
instantiate activity now. A newly observed science, inventory, identity,
atomicity, substrate or resource incompatibility in E2 still returns before
any lease or identity action.

## Four-layer translation

```text
observed_fact=All five E1 source families and deterministic flow-local self-audits are complete; E1 accounting is 48 days, remaining E2 forecast is 25/41 and total forecast is 73/89, with no invalidation.
local_action_fence=No E2 work, lease request, lease, master, identity, coordinate, tape, model, checkpoint, training, evaluation, inference output, partial value, provider, Git, deployment, flight or r05 action occurred or is authorized by this packet.
scientific_stage_continuation=The immutable Pro-closed r06 complete panel remains empirically allocated and result-blind; conditional E2 may proceed only under Operational Root after this gate, still before every lease or identity action.
continuation_owner=Operational Root for conditional E2 release; same DISH CM for E2 engineering; Portfolio receives any invalidation and the final decision-level E2 return.
root_decision_class=E1_GATE_TECHNICALLY_SATISFIED|CONDITIONAL_E2_MAY_BE_RELEASED_WITHOUT_NEW_PORTFOLIO_VOTE|NO_LEASE.
applies_to=DISH-RBHR-SCIENCE-20260822-06 E1 five-flow implementation and flow-local self-audit only.
does_not_imply=E2 completion|independent TEST acceptance|resource remeasurement|lease-request eligibility|lease authority|identity/activity|scientific result|claim expansion|r05 revival.
```
