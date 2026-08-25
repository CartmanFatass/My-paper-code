# DISH RBHR r06 E2A integrated data-plane CM technical packet — 2026-08-22

```text
document_kind=code_manager_e2a_integrated_data_plane_technical_packet
direction_id=degraded_incumbent_shadow_handover
exact_object_revision=DISH-RBHR-SCIENCE-20260822-06
portfolio_boundary=docs/session/PORTFOLIO_TO_ROOT_DISH_RBHR_R06_FINITE_E2A_E2B_ENGINEERING_EXPANSION_20260822.md
technical_disposition=E2A_COMPLETE|ALL_FIRST_EIGHT_PRODUCTION_SURFACES_PRESENT|LOCAL_SELF_AUDIT_ACCEPTED
already_accounted_e1_engineer_days=48
already_accounted_e2_engineer_days=8
e2a_actual_additional_engineer_days=23
cumulative_e2_actual_engineer_days=31
cumulative_total_actual_engineer_days=79
remaining_e2b_forecast_engineer_days=MANAGED19|HIGH29
cumulative_e2_completion_forecast_engineer_days=MANAGED50|HIGH60
cumulative_total_completion_forecast_engineer_days=MANAGED98|HIGH108
e2a_hard_additional_ceiling_days=35
cumulative_e2_hard_ceiling_days=72
cumulative_total_hard_ceiling_days=120
e2b_release_gate_technical_fact=SATISFIED
lease_request_issuable=false
question_relevant_output=false
identity_or_activity=false
r05_action=false
```

## Decision-level conclusion

E2A is complete within its finite envelope. The current r06 source now binds
the five E1 flows through a concrete single-identity production data plane, a
fail-closed Root-lease loader that creates no request, native-batch atomic
orchestration, atomic metric persistence/resume, raw metric-to-6,990 ingestion,
complete first-valid recovery-witness and behavior-changing `d_h`/`d_a`
support rows, and the complete ordered fifteen-branch payload.

The local result-blind receipt accepts all eight required E2A surfaces. It
compiled and loaded the source-keyed native ABI, exercised only synthetic
structural persistence, complete-key mapping and branch-reachability fixtures,
and exposed no partial or question-relevant value. It did not instantiate an
r06 master, identity, coordinate, tape, model, checkpoint, training rollout,
evaluation trajectory or production inference. No lease request was prepared
and no lease was issued.

## Eight required E2A surfaces

| Required surface | Current source and local acceptance fact |
|---|---|
| Concrete r06 production data plane | `production_data_plane.py` binds population, 32-lane persistent TRAIN, five-arm paired evaluation, first-valid REAL/SHAM receipts, complete metric ingestion, inference and the result firewall under one lease-bound master/identity. |
| Production lease-loader, no request | `production_lease.py` validates exact Root-authored request and lease bytes, immutable resource shape and single identity before materializing a master. Its manifest records `request_created=false`, `lease_issued=false`, `master_materialized=false`. |
| Failure-atomic native-batch orchestration | `production_full_panel.py` obtains the complete receipt inventory for a batch and advances/replaces the sealed frontier only afterward; evaluation and fork widths are 32 and training advances one complete 4,096-transition update. |
| Failure-atomic metric persistence/resume | `production_metrics.py` uses binding-checked atomic shard replacement, idempotent same-byte replay, divergent replacement rejection and complete-block-only exposure. The local store/resume fixture passed and an incomplete store was refused. |
| Raw metric to 6,990 ingestion | The required block-key inventory maps in exact manifest order through `production_estimands.py`; the local structural fixture assembled exactly 6,990 unique rows. Production inference still refuses anything other than a complete finite 24-by-6,990 matrix. |
| Complete witness/support rows | Claim-only STRUCTURED first-valid observers persist one receipt for each of 6,912 claim tapes, including no-trigger rows, paired 100-tick REAL/SHAM service/energy/hard-event telemetry, and complete cell denominators. |
| Behavior-changing `d_h`/`d_a` rows | At the nonmutating first-valid predicate, the production collector records `d_h = ||h_shadow-h_incumbent||/sqrt(128)` and `d_a = ||a_promoted-a_retained||/6`; support requires both at least `1e-3`, with explicit zero-denominator behavior. |
| Complete fifteen-branch payload | `complete_branch_payload` requires all protocol/support predicates and all three anchor-speed rows for each of the six regime/schedule cells, applies frozen first-match classification, then schedule/regime common-anchor intersections. The local fixture reaches every one of the 15 catalog branches. |

Controlling result-blind local receipt:

```text
runtime/benchmarks/dish_rbhr_r06_e2a_local_self_audit_20260822.json
sha256=100af8d900bb1b81e080f00d8d4e7cb3120792c5f602c204efa7b3765e159b14
all_eight_surface_checks=true
fixture_only=true
question_relevant_output=false
partial_values_exposed=false
```

The accepted native artifact is SHA-256
`de26610daf9d8458e568594becf361c230b41c8bc95e56d0c743dccbeaede252`
from native source SHA-256
`a86ce19c009cf8a2e65de72ea70b81b5db5e2bc48ab539ce01bcff605d45606e`.
ABI version 1 and the reset/step/state/output/fork/passive-label/protocol sizes
remain accepted. The receipt is the controlling current-byte source-hash
manifest for the ten E2A/E1-bound production modules.

## Failure-atomic lifecycle and result firewall

The production object is inert at import. Only a later active Root lease may
construct it. A training update resumes only from matching native-state,
recurrent-state and persistent model/optimizer bytes; any incomplete triplet
fails closed. Checkpoint evaluation requires all 120 block-arm sole
checkpoints at update 1,024. Evaluation persists first-valid CLAIM/DEGRADED
REAL/SHAM receipts by their immutable claim coordinate; the later FORK frontier
seals those existing paired receipts and never reruns a branch after a crash.
Metric shards are identity-bound and create/replace atomic. The inference entry
point accepts only the complete 24-by-6,990 matrix and complete branch-predicate
inventory, and the public result remains behind the existing complete-result
firewall.

## Engineer-day accounting and E2B forecast

E2A accounts for 23 additional experienced-engineer-day equivalents, at its
managed target and 12 below its 35-day hard ceiling. Added to the already
charged E2=8, cumulative E2 actual is 31; with E1 fixed at 48, cumulative
construction actual is 79.

Remaining E2B is unchanged at 19 managed / 29 high days. Therefore cumulative
E2 completion forecasts are 50 managed / 60 high, below 72, and cumulative
construction forecasts are 98 managed / 108 high, below 120. No unused E2A
capacity transfers to E2B. This accounting is the same finite
scope-accounted experienced-engineer-day unit used by E1 and the protected
cost boundary; it is not elapsed human time or empirical runtime.

## Remaining E2B work and risks

The following are deliberately unestablished and remain only in conditional
E2B:

1. independent TEST acceptance of cross-flow recurrence, persistence, paired
   mask evaluation, first-valid fork lineage, complete metric/inference
   ingestion and result-firewall recovery;
2. end-to-end result-blind reacceptance of the exact production CLI and
   failure-atomic successor-slice lifecycle;
3. current-byte CPU/wall/RSS/scratch/durable/I/O measurement and full-panel
   projections against the immutable ordinary and hard ceilings; and
4. exact Root lease-request preparation and the final
   `lease_request_issuable` ruling.

Production-only paths remain unexecuted by the E2A fence, so empirical runtime
and measured bottlenecks are still unknown. These are E2B acceptance/resource
facts, not E2A gaps or science ambiguities. `lease_request_issuable` correctly
remains false until E2B completes.

## Invalidation checks

Every E2A invalidation predicate is false:

- no treatment, comparator, threshold, arm, branch, inference family,
  coordinate law, population, panel, claim or science revision changed;
- exact inventories remain 11,520 base tapes, 120 training jobs, 1,024 updates
  per job, 503,316,480 training transitions, 115,200 evaluation episodes,
  6,912 claim-tape fork rows, 6,990 estimands and 99,999 joint resamples;
- the one-future-identity rule remains intact; no identity exists, no
  replacement path was added and no partial panel can be exposed;
- native host recurrence, persistent hidden/model/optimizer state, paired
  mask randomness, first-application-valid REAL/SHAM order, complete
  witness/support denominators, common-anchor inference and atomicity are
  preserved;
- no Python environment/rollout fallback, panel shrink, substrate replacement,
  provider, Git, deployment, flight or r05 action occurred; and
- ordinary `320 CPUh / 65 wall h` and hard `560 CPUh / 110 wall h / 40 GiB RSS
  / 120 GiB scratch / 16 GiB durable / 400 GiB I/O`, at no more than eight
  workers/cores and GPU0, remain immutable. E2A made no resource ruling.

## Four-layer translation

```text
observed_fact=All first eight E2A production surfaces are current-byte present and accepted by a result-blind local fixture; E2A actual is 23 additional days, cumulative E2/total actual is 31/79, remaining E2B forecast is 19/29, and no invalidation or question-relevant activity occurred.
local_action_fence=No E2B independent acceptance, resource measurement or lease-request preparation occurred; no lease may be issued and no r06 master/identity/coordinate/tape/model/checkpoint/training/evaluation/inference/activity/partial value, r05 action, provider or Git operation is authorized by this packet.
scientific_stage_continuation=The immutable Pro-closed complete r06 panel remains empirically allocated and result-blind; conditional E2B may proceed under Operational Root because this exact E2A gate is satisfied.
continuation_owner=Operational Root for conditional E2B release; same DISH CM for E2B; Portfolio receives any later invalidation and the final E2B decision-level return.
root_decision_class=E2A_GATE_TECHNICALLY_SATISFIED|CONDITIONAL_E2B_MAY_BE_RELEASED_WITHOUT_NEW_PORTFOLIO_VOTE|NO_LEASE.
applies_to=DISH-RBHR-SCIENCE-20260822-06 E2A first eight production surfaces and result-blind local self-audit only.
does_not_imply=E2B completion|independent TEST acceptance|current-byte resource acceptance|lease-request eligibility|lease authority|identity/activity|scientific result|claim expansion|r05 revival.
```
