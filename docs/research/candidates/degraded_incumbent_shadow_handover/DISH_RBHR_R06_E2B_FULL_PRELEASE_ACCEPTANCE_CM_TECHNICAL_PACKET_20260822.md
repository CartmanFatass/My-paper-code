# DISH RBHR r06 E2B full prelease acceptance CM technical packet — 2026-08-22

```text
document_kind=code_manager_e2b_full_prelease_acceptance_technical_packet
direction_id=degraded_incumbent_shadow_handover
exact_object_revision=DISH-RBHR-SCIENCE-20260822-06
portfolio_boundary=docs/session/PORTFOLIO_TO_ROOT_DISH_RBHR_R06_FINITE_E2A_E2B_ENGINEERING_EXPANSION_20260822.md
technical_disposition=E2B_COMPLETE|CURRENT_BYTE_TECHNICAL_AND_RESOURCE_ACCEPTANCE|LEASE_REQUEST_ISSUABLE
e1_actual_engineer_days=48
pre_expansion_e2_actual_engineer_days=8
e2a_actual_engineer_days=23
e2b_actual_engineer_days=19
cumulative_e2_actual_engineer_days=50
cumulative_total_actual_engineer_days=98
e2b_hard_ceiling_engineer_days=29
cumulative_e2_hard_ceiling_engineer_days=72
cumulative_total_hard_ceiling_engineer_days=120
lease_request_issuable=true
lease_issued=false
question_relevant_output=false
nonfixture_identity_or_activity=false
r05_action=false
```

## Decision-level conclusion

E2B is complete at its 19-day managed allocation and below every finite cap.
The current bytes pass independent TEST acceptance across the integrated
surfaces, the exact full-panel CLI completes the entire 256,513-unit inventory
over two same-identity failure-atomic TEST slices, all ordinary and hard
resource gates pass current-byte result-blind measurement, and the exact
production lease request validates against its acceptance receipt and source
hashes.

The prepared request is technically eligible for a separate Operational-Root
lease decision. No lease was issued and no nonfixture master, identity,
coordinate, tape, model, checkpoint, training rollout, evaluation trajectory,
fork, inference result, branch value or partial value was created. The
production panel remains wholly unexecuted.

## Independent integrated acceptance

The focused independent suite passed `14/14` tests:

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q \
  tests/experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/test_r06_conformance.py \
  tests/experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/test_r06_e2b_integration.py
14 passed
```

The suite independently covers the complete deterministic population and
native ABI, no-lease refusal, exact inventory, all fifteen first-match branches
and common-anchor intersections, complete witness/support denominators and
`d_h`/`d_a` predicates, idempotent atomic metric resume and divergent shard
rejection, refusal to expose incomplete metrics, lease-loader fail-closed
behavior, failure-before-receipt frontier atomicity, same-identity successor
resume, all-stage completion and the complete-result firewall.

The exact production CLI surface was then run with an explicit TEST-only
loader and no scientific master. Slice one sealed all 11,520 population units;
slice two resumed generation 1 and completed the remaining 244,993 units. The
final frontier records:

```text
completed_units=256513
stage=COMPLETE
slice_generation=1
same_identity=true
partial_values_exposed=false
component_chain_sha256=ac17b3fbf75bf4eaca2eb67dfdfb07eed328a36db34c33002e29787b276ba0e0
```

This is a structural TEST lifecycle, not an empirical panel, inference output
or candidate identity. It establishes that the exact CLI, loader interface,
native-batch executor, atomic frontier and result firewall compose end to end.

## Current-byte resource evidence

The acceptance harness measured the current native 32-lane rollout, one
native-connected 4,096-transition persistent update, analyzer cost, lifecycle
bytes and process resources, then applied the frozen complete-panel inventory:

| Resource | Current-byte result-blind projection | Ordinary / hard gate | Disposition |
|---|---:|---:|---|
| CPU | 265.1801 core-hours | 320 / 560 core-hours | Pass ordinary and hard |
| Wall at eight workers | 33.1476 hours | 65 / 110 hours | Pass ordinary and hard |
| Aggregate RSS, conservative eight-process bound | 2.203 GiB | 40 GiB hard | Pass |
| Scratch | 0.664 GiB | 120 GiB hard | Pass |
| Durable | 0.331 GiB | 16 GiB hard | Pass |
| Total I/O | 34.067 GiB | 400 GiB hard | Pass |

Measured native throughput was 12,865.425 lane-ticks/second and the complete
4,096-transition update took 7.3242 seconds. The projection is:

```text
676116480/current_native_lane_ticks_per_second
+ 122880*current_native_connected_4096_update_seconds
+ current_analyzer_seconds_per_estimand*6990
```

It contains no candidate scanner, admission search or question-relevant row.
The CLI resource guard now observes CPU, wall, current process RSS, separate
scratch/durable paths and cumulative read/write bytes before every atomic
batch. Ordinary ceilings remain scheduling targets; every hard ceiling remains
fail-closed.

Controlling current-byte acceptance receipt:

```text
runtime/benchmarks/dish_rbhr_r06_e2b_technical_resource_acceptance_20260822.json
sha256=786f740571d48b8c23ab53f6bd5c9b91f1a8258cd0de9e7d9208321b07e544cc
technical_acceptance=true
lease_request_preparation_eligible=true
fixture_only=true
question_relevant_output=false
```

That receipt is the controlling current-byte source-hash manifest for the
native host, production data plane, executor, loader, metrics, inference,
REAL/SHAM, trainer, CLI and independent tests.

## Exact lease request and validator

Prepared request:

```text
runtime/lease_requests/dish_rbhr_r06_full_panel_lease_request_20260822.json
sha256=1868ec27ca9d854842352646753a0d0ddfde1648598330d0dd766e54a122bdd8
```

Validator receipt:

```text
runtime/benchmarks/dish_rbhr_r06_lease_request_validation_20260822.json
sha256=d7343e30f5e1460d97836cc82fb896610c45c6ab8d420f5b678f617d1f50a063
lease_request_issuable=true
lease_issued=false
identity_materialized=false
question_relevant_output=false
```

The request binds the exact object and component, current acceptance bytes,
all production source/test/CLI hashes, the indivisible inventory, one fresh
nonreplaceable identity, no partial-value exposure, the exact production
loader/command template, eight workers/cores, GPU0, and the immutable ordinary
and hard resource ceilings. Any byte change makes the current validator fail
closed and requires fresh CM reacceptance before Root may issue a lease.

Operational Root alone may issue the separate lease and bind the single fresh
blinded master/identity/run root. The request contains no master or identity
material and does not authorize execution by itself.

## Engineer-day accounting

E2B accounts for 19 experienced-engineer-day equivalents, exactly its managed
allocation and 10 below its 29-day hard ceiling. Cumulative E2 is therefore
`8 + 23 + 19 = 50`, below the 72-day hard cap. With E1 fixed at 48, cumulative
construction is `98`, below 120. No substage capacity transferred, and the old
closed E2/total caps were not reused or replenished.

## Invalidation checks

Every E2B invalidation predicate is false:

- science revision, treatment, comparators, thresholds, arms, first-match
  branches, inference families, coordinate law, population and claim remain
  byte-bound and unchanged;
- inventories remain 11,520 base tapes, 120 persistent 1,024-update jobs,
  503,316,480 training transitions, 115,200 paired-mask five-arm episodes,
  6,912 claim-tape first-valid REAL/SHAM rows, 6,990 estimands and 99,999 joint
  resamples;
- native recurrence/promotion, persistent hidden/model/optimizer/Welford
  state, sole checkpoints, paired mask randomness, first-valid REAL/SHAM
  ordering, complete support denominators, common-anchor inference and the
  result firewall remain intact;
- the single-future-identity rule remains intact; no nonfixture identity
  exists, no replacement path was introduced and successor slices bind the
  same identity;
- current-byte resource evidence passes both ordinary CPU/wall targets and all
  hard CPU/wall/RSS/scratch/durable/I/O ceilings; and
- no Python environment/rollout fallback, panel shrink, substrate replacement,
  r05 action, provider action, Git action, deployment or flight occurred.

There is no technical incompatibility, science-bearing ambiguity or resource
boundary in this E2B return.

## Four-layer translation

```text
observed_fact=Current bytes pass 14/14 independent tests, exact two-slice TEST CLI completion, complete-result firewall acceptance and resource projections of 265.1801 CPUh, 33.1476 wall h, 2.203 GiB RSS, 0.664 GiB scratch, 0.331 GiB durable and 34.067 GiB I/O; the exact request validator returns lease_request_issuable=true.
local_action_fence=This packet prepares and validates one request only; it does not issue a lease or authorize any master/identity/coordinate/tape/model/checkpoint/training/evaluation/fork/inference/result/partial value, replacement identity, r05 action, provider or Git operation.
scientific_stage_continuation=The immutable Pro-closed complete r06 empirical panel is technically and resource-ready for a separate Operational-Root lease under its unchanged one-identity/result-blind envelope.
continuation_owner=Operational Root for the exact lease decision and, only after issuance, the same DISH CM for the indivisible production panel; Portfolio receives this decision-level technical return.
root_decision_class=E2B_TECHNICAL_RESOURCE_ACCEPTANCE_COMPLETE|LEASE_REQUEST_ISSUABLE|ROOT_LEASE_DECISION_REQUIRED|NO_LEASE_ISSUED.
applies_to=DISH-RBHR-SCIENCE-20260822-06 complete E2B prelease acceptance and exact prepared request only.
does_not_imply=Lease issuance|empirical activity|scientific result|claim interpretation|partial-panel permission|replacement identity|r05 revival.
```
