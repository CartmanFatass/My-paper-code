# RISP G-init r01 post-26 resource-cost decomposition EM intake — corrected 2026-08-23

```text
document_kind=direction_resource_assessment_scientific_intake
owner=direction:renewal_indexed_score_plasticity
exact_object_revision=RISP-G-INIT-REACH-R01-FULL-PANEL|RISP-G-INIT-REACH-SCIENCE-20260821-01
cm_resource_return=temp/handoffs/code_manager_to_root/RISP_G_INIT_REACH_R01_POST_26_RESOURCE_COST_DECOMPOSITION_CM_RETURN_20260823.md
cm_resource_return_sha256=d285485294d11653e23c7559580a05aafc6538a802fc02e90cf42a1d28870f96
observed_frontier=BLINDED_26_OF_352
science_bearing_ambiguity=none
question_relevant_output=none
partial_values_exposed=false
science_change=false
em_scientific_disposition=R01_REMAINS_PRO_CLOSED_UNCHANGED|RESOURCE_FORECAST_TECHNICALLY_NONDECISIVE
em_portfolio_recommendation=WITHHOLD_RISP_TRANCHE_AND_CPU_EXPANSION_PENDING_PHASE_STRATIFIED_CURRENT_PATH_REACCEPTANCE
empirical_or_lease_authority=false
```

## Corrected decision

The same-direction EM preserves exact R01 science but withholds any resource
tranche or CPU expansion from the current decomposition.

The CM correctly audited the cumulative `32.9642578125 CPUh` account and
correctly found that the prior 32-CPUh ceiling stops the runner before workers.
Its complete-panel forecast is not decision-valid, however. The frozen unit
plan is `32 TRAIN` followed by `320 EVAL`; the blinded frontier `26/352`
therefore leaves only six TRAIN units and all 320 EVAL units. The decomposition
applied cost observed from 13 completed TRAIN batches to all 163 remaining
mixed-phase batches. Evaluation is `torch.no_grad()` and contains no 512-update
backward/optimizer loop, so the managed `413.321 CPUh / 9.388 d` and empirical
high `585.580 CPUh / 14.468 d` are not estimates of the actual remaining panel.

No one-slice tranche is scientifically or economically justified from that
mis-stratified forecast. A corrected technical return must separate the three
remaining two-unit TRAIN batches from the 160 EVAL batches, use phase-specific
current-byte evidence, identify unmeasured quantities rather than assigning
TRAIN cost, and disclose the dominant Python/Torch versus C++/parallel hot
path. Only then can Portfolio compare a finite tranche or full completion with
opportunity cost.

```text
observed_fact=CURRENT_26_UNITS_ARE_TRAIN_PHASE|REMAINING_6_TRAIN_PLUS_320_EVAL|CM_EXTRAPOLATED_TRAIN_BATCH_COST_TO_ALL_REMAINING_BATCHES
scientific_interpretation=NO_RISP_RESULT|R01_PRO_CLOSED_SCIENCE_UNCHANGED
portfolio_recommendation=NO_CURRENT_TRANCHE_CPU_EXPANSION_OR_LEASE_FROM_THIS_RETURN|REQUEST_PHASE_STRATIFIED_TECHNICAL_REPAIR
local_fence=NO_ACCOUNT_RESET|NO_PANEL_CHANGE|NO_RUNTIME_OR_BENCHMARK_WITH_PRODUCTION_COORDINATE|NO_FRONTIER_RESULT_PARTIAL_PROVIDER_GIT_DEPLOYMENT_FLIGHT
continuation_owner=WORKFLOW_RECOVERY_MANAGER_FOR_SYSTEMIC_CONTRACT_CAUSE|OPERATIONAL_ROOT_AND_RISP_CM_FOR_LATER_CORRECTED_TECHNICAL_RETURN|PORTFOLIO_FOR_ANY_RESOURCE_DECISION
```
