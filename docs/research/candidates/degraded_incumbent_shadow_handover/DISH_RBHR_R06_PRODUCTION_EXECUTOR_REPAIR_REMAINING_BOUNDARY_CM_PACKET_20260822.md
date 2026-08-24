# DISH RBHR r06 production-executor repair remaining boundary — 2026-08-22

```text
document_kind=code_manager_unchanged_science_repair_boundary
direction_id=degraded_incumbent_shadow_handover
exact_object_revision=DISH-RBHR-SCIENCE-20260822-06
technical_disposition=PARTIAL_REPAIR_ACCEPTED|LEASE_NOT_READY
lease_request_issuable=false
science_bearing_ambiguity=none
resource_boundary=none
identity_or_activity=false
```

The unchanged-science repair now supplies four previously absent production
families:

- lease-bound nonfixture native reset rows in
  `production_backend.open_production_batch`;
- a private persistent model/optimizer engine carrying exact checkpoint bytes
  through updates, with the sole evaluation checkpoint only at update 1,024;
- create-only production lifecycle open/resume with identity-bound parent
  generations; and
- complete `[24,6990]` production max-t inference plus a create-only complete-
  result firewall rejecting incomplete inventory.

Seven R06 conformance tests still pass. The repaired prelease validator observes
those four surfaces and narrows the incompatibility to exactly two absent
families: the integrated complete full-panel module and its exact resource-
guarded CLI. Those surfaces must connect persistent policies to all 115,200
mask-on/off evaluations, first-application-valid REAL/SHAM forks, reducer rows,
atomic same-identity successor slices and the final firewall. Until they exist
and receive current-byte acceptance, a Root lease request is not issuable.

## Current repair artifacts

```text
experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_backend.py=213ef10269219ea909b0b0dd4001f6363f2f1e2215239f55c6b1cd7cba0f6b75
experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_training.py=7e76e9e8ccd1e1ea641478081a1470849c1b211ce7252c7b073b20ab5fb98af3
experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_training_engine.py=703220f02acf0348f2255c8aef49874672c99990497e89c30cd5df02bce05755
experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_lifecycle.py=e37222ae8ac44ed99dc001172641fff004ff4637ba677bc24326dc71c85249fa
experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_inference.py=3b947c99e7a52240213b4e7eb96c201e9b9fcd90c55f30ed72d1ec72d4501ee7
temp/handoffs/code_manager_to_root/validate_dish_rbhr_r06_full_panel_prelease_20260822.py=18eb103aff69ff4caad731c5379dde248f8763067afe976a9a9c4da066e9d168
runtime/benchmarks/dish_rbhr_r06_full_panel_prelease_validation_repair_20260822.json=715b96b40d2558ece4b33ef3c0dd2a3a3830e33ae14bb84787e6667bc56a228d
```

```text
observed_fact=Lease-bound native reset, persistent trainer, atomic lifecycle/resume and complete inference/firewall are now present; exact full-panel orchestration and resource-guarded CLI remain absent, so lease_request_issuable=false.
local_action_fence=Do not issue a lease or create an R06 identity against these bytes.
applies_to=R06 current-byte production lease readiness only.
does_not_imply=Science defect|resource failure|allocation reversal|permission for partial activity.
scientific_stage_continuation=The unchanged invested panel remains live; same-CM engineering may complete the final two orchestration families without Portfolio science change.
continuation_owner=Operational Root and same DISH CM for the remaining integrated executor/CLI repair.
root_decision_class=PRELEASE_TECHNICAL_INCOMPATIBILITY_NARROWED|NO_LEASE_ISSUANCE.
```
