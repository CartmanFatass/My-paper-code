# RISP G-init R01 post-26 phase-stratified cost and hot-path EM intake

```text
artifact_kind=SAME_DIRECTION_EM_TECHNICAL_INTAKE
direction_id=renewal_indexed_score_plasticity
exact_object_revision=RISP-G-INIT-REACH-R01-FULL-PANEL|RISP-G-INIT-REACH-SCIENCE-20260821-01
source_cm=temp/handoffs/code_manager_to_root/RISP_G_INIT_REACH_R01_POST_26_PHASE_STRATIFIED_COST_AND_HOT_PATH_CM_RETURN_20260823.md
source_cm_sha256=aba3ffd6879818b42a01e99f2f39b16b73bccabb8a697ade5b44b303193595bd
scientific_result=NONE
partial_value_exposed=false
```

## Intake

The old finite mixed-phase full-panel forecast is withdrawn. The only measured
production batches are the 13 committed TRAIN batches. The exact remaining
structure is six TRAIN units in three two-worker batches followed by 320 EVAL
units in 160 two-worker batches. Every EVAL timing/resource class is
`UNMEASURED`; therefore no finite complete-panel low, managed or high CPU/wall
forecast is supported.

The current implementation is only partially native. C++ owns the batched
environment host, while Python still owns the interactive/event layer and
PyTorch owns the frozen float64 forward/replay/autograd/AdamW path. EVAL avoids
the TRAIN backward/optimizer loop, so TRAIN latency cannot be transferred to
EVAL. Current proof-grade sampling/transcendental necessity remains
scientifically unestablished; the prospective
`HMASD-MARL-FP32-BASELINE-V1` standard does not retroactively change R01.

## Direction decision boundary

```text
prior_413_CPUh_9.388d_forecast=WITHDRAWN
prior_585.580_CPUh_14.468d_forecast=WITHDRAWN
remaining_train_cost=PHASE_LOCAL_DECOMPOSITION_ONLY|ALL_CASES_EXCEED_CONSUMED_32CPUH_ACCOUNT
remaining_eval_cost=UNMEASURED|NO_TRAIN_COST_TRANSFER
full_panel_cost=NOT_FORECASTABLE
current_frontier=26/352|BLINDED|UNCHANGED
current_activity_authority=NONE
portfolio_action=WITHHOLD_TRANCHE_CPU_EXPANSION_LEASE_OPERATOR_AND_ACCOUNT_RESET
science=UNCHANGED|NO_POSITIVE_NEGATIVE_RESULT_OR_DIRECTION_FAILURE
```

The CM return's suggested later EVAL measurement is an unissued future
engineering boundary, not current authority. The earlier task-scoped recovery
owner completed its static contract repair; no live recovery, instrumentation,
benchmark or runtime assignment follows from this intake. Portfolio must make
a separate value/resource decision before any new RISP measurement or a
science-bearing ordinary-precision successor revision.

SGSP, RCLE, DISH and VQFP are unchanged. No source, build, test, benchmark,
runtime, lease, Operator, frontier/result/partial, provider or Git action was
taken.
