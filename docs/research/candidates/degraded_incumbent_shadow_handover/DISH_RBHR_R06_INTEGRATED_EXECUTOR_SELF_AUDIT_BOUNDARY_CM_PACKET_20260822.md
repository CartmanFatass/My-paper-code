# DISH RBHR r06 integrated-executor self-audit boundary — 2026-08-22

```text
document_kind=code_manager_prelease_self_audit_boundary
direction_id=degraded_incumbent_shadow_handover
exact_object_revision=DISH-RBHR-SCIENCE-20260822-06
technical_disposition=LEASE_NOT_READY
lease_request_issuable=false
science_ambiguity=none
resource_boundary=none
identity_or_activity=false
```

The integrated stage/frontier/resource-guard module and exact CLI now exist,
and eight conformance tests pass. Current-byte cost remains within the envelope
at 302.2183 CPUh, 52.2630 wall h, 2.5871 GiB RSS, 0.6631 GiB scratch,
0.3305 GiB durable and 34.0670 GiB I/O.

Before freezing a lease request, CM self-audit followed the CLI's
`--lease-loader` dependency end to end. It found no concrete
`production_lease.py`, `load_root_lease`, or `R06ProductionDataPlane`. The CLI
therefore cannot validate a Root lease, materialize the one identity, generate
the production training/evaluation/fork units, or drive the integrated
executor. The earlier superficial `issuable=true` receipt is superseded and
must not be used.

Controlling receipt:
`runtime/benchmarks/dish_rbhr_r06_full_panel_prelease_validation_final_20260822.json`
with SHA-256
`53504948855d510081825ad6874f671b431a42af56b3fa27f62833c33f79ccfb`.

Implemented but not sufficient:

- `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_full_panel.py`
- `tools/experiments/run_dish_rbhr_r06_full_panel.py`
- `runtime/benchmarks/dish_rbhr_r06_production_lease_readiness_20260822.json`
  (resource evidence only; SHA-256
  `b9aa40bccbf8ea45f245e76e67a42403f33cc0fce7d91d8a8f813e586b10b44e`).

```text
observed_fact=Integrated orchestration/CLI source exists and resource gates pass, but no concrete lease loader or production data plane exists; the CLI cannot execute the panel and lease_request_issuable=false.
local_action_fence=Do not issue a lease or create an R06 master/identity/coordinate against these bytes.
does_not_imply=Science defect|resource failure|Portfolio allocation change|permission for partial activity.
scientific_stage_continuation=Immutable R06 empirical investment remains live; unchanged-science engineering must implement and validate the concrete lease/data plane.
continuation_owner=Operational Root and same DISH CM for the remaining concrete production data plane.
root_decision_class=PRELEASE_TECHNICAL_INCOMPATIBILITY|NO_LEASE_ISSUANCE.
```
