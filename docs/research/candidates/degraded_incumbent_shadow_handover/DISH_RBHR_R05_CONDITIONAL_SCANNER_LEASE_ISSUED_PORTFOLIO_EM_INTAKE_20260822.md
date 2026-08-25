# DISH RBHR r05 conditional scanner lease-issued Portfolio-EM intake — 2026-08-22

```text
document_kind=portfolio_em_operational_lease_milestone_intake
owner=Dedicated Portfolio successor session 01a02b11-f3da-7022-b821-a33f9c7e0bac acting locally as same-direction DISH Portfolio EM
direction_id=degraded_incumbent_shadow_handover
exact_object_revision=DISH-RBHR-SCIENCE-20260821-05
source_packet=docs/session/ROOT_TO_PORTFOLIO_DISH_CONDITIONAL_SCANNER_LEASE_ISSUED_20260822.md
source_packet_sha256=d489e0028f2d553772298e6262781c5c18741e5b62d65c3c6c1daa805cab33a3
request_path=temp/handoffs/code_manager_to_root/DISH_RBHR_R05_CONDITIONAL_SCANNER_ROOT_LEASE_REQUEST_20260822.json
request_sha256=72c2559c8207187f1dfc9c711d46a66e6aecca2ad26bd44109af69077489a447
lease_path=runtime/leases/dish_rbhr_r05_conditional_scanner_lease_20260822.json
lease_sha256=34de1ce458d25b3828b0dc6696c505ef6d51f1ea72c4a847cc9212e776e6f67a
validation_artifact=runtime/benchmarks/dish_rbhr_r05_conditional_scanner_lease_validation_20260822.json
validation_sha256=a392ea8ae105d9e04a45907933d58423da153ca369087e22e1cf13e60ef03736
lease_id=DISH-RBHR-R05-CONDITIONAL-SCANNER-20260822-01
lease_window=2026-08-22T22:10:47.483102Z..2026-08-23T22:10:47.483102Z
lease_status=ACTIVE
lease_binding_valid=true
cm_technical_acceptance_reperformed=false
root_lease_decision_reperformed=false
science_bearing_ambiguity=none
question_relevant_output=none
portfolio_allocation_changed=false
uav_classification_changed=false
```

## Portfolio intake

Accept the exact CM validation and Operational-Root lease issuance without
re-performing technical acceptance or the Root resource decision. The issued
lease matches the approved request, binds one blinded nonreplaceable master,
one identity and the sole coordinate, and authorizes only the frozen scanner
and accepted-tape installation path. The TEST validation confirms the
request/guards/resume path and creates no production identity or activity.

At the exact issuance validation boundary, the lease is active but no master,
identity or coordinate has yet been materialized. Scanner execution is
authorized and starting under the same CM. Scientific activity begins only
when that CM actually materializes the one nonfixture master/identity/
coordinate; lease issuance by itself is not a result or gate observation.

All six high gates remain unestablished pending the scanner's complete
inventory/resource return. No full-panel model, optimizer, checkpoint,
training, evaluation, fork, bootstrap, branch, result or partial-value path is
authorized.

```text
observed_fact=Operational Root issued and validated the exact active conditional scanner-only lease; its binding passed while master_materialized=false, and scanner-only execution is now authorized under the same CM.
local_action_fence=Only one blinded nonreplaceable master/identity/sole coordinate plus frozen scanner and accepted-tape installation are authorized; halt before rejection 10451148 or any unchanged ceiling; no full-panel/model/training/evaluation/result/partial-value/provider/Git action.
applies_to=DISH-RBHR-R05 conditional candidate-scanner resource subphase only.
does_not_imply=Master already materialized|scientific activity already observed|gate pass|preactivity acceptance|full-panel lease|scientific result|allocation or UAV-classification change|direction completion.
scientific_stage_continuation=DISH remains empirical and the sole current direct-UAV empirical; the scanner subphase resolves the last resource fact for its unchanged full panel.
continuation_owner=Same DISH CM for guarded scanner execution and exact return; Operational Root for lease/resource enforcement; same-direction Portfolio EM for any exact science ambiguity or later complete result.
root_decision_class=conditional scanner resource lease applied; technical scanner outcome pending.
portfolio_disposition=LEASE_ISSUANCE_INTAKEN|NO_NEW_PORTFOLIO_DECISION
```

