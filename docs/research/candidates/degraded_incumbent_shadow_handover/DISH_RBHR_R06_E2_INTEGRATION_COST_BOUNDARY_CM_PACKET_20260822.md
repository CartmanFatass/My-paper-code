# DISH RBHR r06 E2 integration and cost boundary — 2026-08-22

```text
document_kind=code_manager_e2_integration_cost_boundary
direction_id=degraded_incumbent_shadow_handover
exact_object_revision=DISH-RBHR-SCIENCE-20260822-06
source_boundary=docs/session/PORTFOLIO_TO_ROOT_DISH_RBHR_R06_FINITE_TWO_STAGE_ENGINEERING_EXPANSION_20260822.md
technical_disposition=E2_INTEGRATION_INCOMPLETE|COST_FORECAST_EXCEEDS_E2_HARD_CEILING
e2_actual_scope_accounted_engineer_days=8
remaining_e2_forecast_engineer_days=LOW28|CENTRAL42|HIGH64
e2_completion_forecast_engineer_days=LOW36|CENTRAL50|HIGH72
e2_hard_ceiling_engineer_days=41
total_completion_forecast_engineer_days=LOW84|CENTRAL98|HIGH120
hard_total_ceiling_engineer_days=117
lease_request_issuable=false
science_bearing_ambiguity=none
identity_or_activity=false
r05_action=false
```

## Decision-level conclusion

E2 must return before further work. Current-byte integration found that E1's
accepted flow-local source families do not yet form a production data plane or
an end-to-end reducible panel. The remaining central/high E2 completion
forecast is 50/72 scope-accounted engineer-days including the 8 already used,
above the protected 41-day E2 ceiling. The high total forecast is 120 days,
above the non-replenishable 117-day total ceiling.

This is an engineering integration/cost fact, not a science defect or empirical
result. No current-byte resource ruling is possible because the exact full
chain is absent. No lease request was prepared: a request binding bytes that
cannot yet produce the complete result would be a false-positive lease surface.

## Exact current-byte boundary

The result-blind validator establishes these absent production surfaces:

1. concrete `R06ProductionDataPlane` connecting the five E1 families;
2. `production_lease.py` and fail-closed `load_root_lease`;
3. failure-atomic native-batch orchestration in `FullPanelExecutor` rather than
   per-unit frontier advancement ahead of 32-wide evaluation/fork batches;
4. production raw-metric ingestion into all 6,990 block-estimand rows;
5. complete recovery-witness `drop`, `maintain`, witness-gain and continuity
   rows under the frozen 200-tick/event-window definitions;
6. STRUCTURED/FLEX first-valid trigger support with exact `d_h` and `d_a`
   behavior-changing diagnostics;
7. complete fifteen-branch payload after interval/common-anchor schedule and
   regime intersections;
8. failure-atomic metric storage/resume across one identity; and
9. an exact current-byte lease request, which is correctly absent while the
   preceding surfaces remain unaccepted.

Controlling validator receipt:

```text
runtime/benchmarks/dish_rbhr_r06_e2_integration_boundary_20260822.json
sha256=14c525e5dc2797b582714c5b14f7926b82703a343db919a8a58144ecf923574b
lease_request_issuable=false
question_relevant_output=false
```

Validator source:

`temp/handoffs/code_manager_to_root/validate_dish_rbhr_r06_e2_integration_boundary_20260822.py`

The receipt also confirms that no master, identity, coordinate, model,
checkpoint, training, evaluation, inference, partial value, provider, Git or
r05 action occurred.

## Bounded E2 work completed before the stop

The 8-day scope-accounted E2 repair established reusable integration pieces:

- evaluator checkpoint binding is now exact for all 24 blocks by five arms,
  not one checkpoint per arm across blocks;
- native state/output snapshots and selected-lane reset support exist for
  same-job persistent resume and 1,200-tick lane renewal;
- mask-on versus mask-off intervention control is separate from the
  `PAIR_SHARED` RNG address, preserving paired physical randomness;
- production bootstrap block indices use the future master under the frozen
  99,999-resample address law rather than the TEST key; and
- `production_estimands.py` maps a complete frozen block-metric dictionary to
  all 6,990 identities with exact benefit orientation, energy ratios and phase
  differences.

These are partial engineering repairs only. They create no partial panel or
lease readiness and do not satisfy the absent raw-metric/data-plane surfaces.

Current identities for the exact inspected surfaces are recorded in the
validator receipt, including:

```text
experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_backend.py=0d9617fb21e4f3a9acac7fe961a1a046ca1a7c12f40d451d2759fcec4d445a31
experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/native/rbhr_r06_production_backend.cpp=a86ce19c009cf8a2e65de72ea70b81b5db5e2bc48ab539ce01bcff605d45606e
experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_evaluator.py=f3b343f119135117348dbf8a3cb052bfe1061eefb03f87253b705f0eb51bfdf7
experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_recurrent_trainer.py=812beff7bf83184fc690863a8957773160cc870980d7924bee48561e57369df5
experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_inference.py=24e665ce6ed559e54a4292de065b4d9cf1bc1550eceee34271d7775d3a08227d
experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_reducer.py=3eb06a62159205c6c6470e467a8f000877dc78b73b98233943d53e3671a567e6
experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_estimands.py=b2b035404e842ca13c297fe6a28fcb9f56831c284aa49f7eee7cdd27fae35a92
experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_full_panel.py=584af36b3e0adc5db3456bd82e8dd59287e7aa823ff27ed1230813803630286f
```

## Remaining cost decomposition

The 28/42/64 remaining low/central/high estimate comprises:

| Remaining E2 family | Low | Central | High |
|---|---:|---:|---:|
| Concrete data plane, batch orchestration and atomic metric persistence | 7 | 10 | 15 |
| Exact witness/support/raw-metric production and 6,990-row ingestion | 8 | 13 | 20 |
| Independent TEST acceptance | 5 | 8 | 12 |
| End-to-end result-blind reacceptance | 3 | 5 | 8 |
| Current-byte resource remeasurement | 3 | 4 | 6 |
| Exact lease-request preparation and validator | 2 | 2 | 3 |
| **Remaining** | **28** | **42** | **64** |

Adding the 8 used E2 days yields 36/50/72. The low case fits 41, but the
central and high cases do not; the protected packet requires return before E2
would exceed 41, not optimistic continuation until a physical overrun. The
high total is 48 E1 + 72 E2 = 120, also above 117. Unused E1 capacity cannot
move into E2.

## Unestablished acceptance/resource facts

Because the integrated production chain does not exist, none of the following
may be inferred from earlier E1 flow-local or pre-E1 benchmark evidence:

- independent current-byte TEST acceptance;
- end-to-end failure-atomic complete-result acceptance;
- current-byte CPU/wall/RSS/scratch/durable/I/O measurements;
- `lease_request_issuable=true`; or
- empirical readiness, result, partial value or branch disposition.

The prior ordinary `320 CPUh / 65 wall h` and hard ceilings remain immutable
requirements, not current-byte measurements. No ceiling was observed to fail;
resource status is unestablished because the measurable chain is incomplete.

## Four-layer translation

```text
observed_fact=E2 integration exposes nine missing production surfaces; 8 E2 days are accounted, remaining work forecasts 28/42/64 and total E2 completion 36/50/72 against the protected 41-day ceiling; no question-relevant activity occurred.
local_action_fence=Stop E2 before further implementation, independent TEST, resource measurement or lease-request preparation under the current cap; do not issue a lease or create any master/identity/coordinate/activity/partial value.
scientific_stage_continuation=The immutable Pro-closed r06 panel remains scientifically unchanged and empirically allocated; this engineering cost return neither interprets nor rejects it.
continuation_owner=Operational Root for exact relay; Portfolio for any new engineering-cost envelope decision; same DISH CM only if an exact owner decision authorizes continuation.
root_decision_class=E2_COST_BOUNDARY|LEASE_REQUEST_NOT_ISSUABLE|PORTFOLIO_RESOURCE_DECISION_REQUIRED.
applies_to=DISH-RBHR-SCIENCE-20260822-06 E2 cross-flow integration and prelease acceptance only.
does_not_imply=Science ambiguity|portfolio reversal|runtime hard-ceiling failure|partial-panel permission|replacement identity|r05 revival|provider|Git|deployment|flight.
```
