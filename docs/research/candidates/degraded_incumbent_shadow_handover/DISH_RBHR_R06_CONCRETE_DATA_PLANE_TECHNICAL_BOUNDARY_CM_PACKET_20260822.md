# DISH RBHR r06 concrete data-plane technical boundary — 2026-08-22

```text
document_kind=code_manager_prelease_technical_boundary
direction_id=degraded_incumbent_shadow_handover
exact_object_revision=DISH-RBHR-SCIENCE-20260822-06
lease_request_issuable=false
identity_or_activity=false
science_ambiguity=none
```

Exact end-to-end intake of the proposed `production_lease.py` revealed that a
lease loader cannot legitimately manufacture the missing data plane from the
accepted modules. The remaining absence is algorithmic production plumbing,
not merely a loader class:

- no master-addressed TRAIN reset-row generator exists for all 32 lanes and
  episode waves;
- no native-to-policy recurrent action loop feeds the persistent trainer while
  preserving per-job hidden/model/optimizer state;
- no checkpoint-loaded five-arm evaluator executes every mask-on/off tape;
- no first-application-valid fork detector supplies paired REAL/SHAM rows; and
- no production reducer maps those rows into the complete `[24,6990]` matrix.

Creating a loader whose unit methods emit opaque counters, delegate these
operations back to the lease authority, or raise at runtime would satisfy the
surface-name validator but would not execute the scientific panel. CM therefore
refuses to create that false-positive module or a lease request. The final
controlling validator remains
`runtime/benchmarks/dish_rbhr_r06_full_panel_prelease_validation_final_20260822.json`
(`53504948855d510081825ad6874f671b431a42af56b3fa27f62833c33f79ccfb`),
with `lease_request_issuable=false`.

```text
observed_fact=Current modules cannot supply the concrete production unit payloads required by FullPanelExecutor; a lease-loader wrapper alone would fail at the first production unit or fake completion.
local_action_fence=No lease request, lease, identity, master, coordinate or activity against these bytes.
does_not_imply=Science defect|resource failure|allocation reversal.
scientific_stage_continuation=The immutable invested panel remains live, but requires implementation and TEST acceptance of the five named production data flows before lease readiness.
continuation_owner=Operational Root and same DISH CM for a larger bounded concrete data-plane implementation assignment.
root_decision_class=PRELEASE_TECHNICAL_INCOMPATIBILITY|NO_LEASE_ISSUANCE.
```
