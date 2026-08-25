# DISH RBHR r06 lease prelaunch technical/resource incompatibility CM packet — 2026-08-22

```text
document_kind=code_manager_prelaunch_technical_resource_incompatibility
direction_id=degraded_incumbent_shadow_handover
exact_object_revision=DISH-RBHR-SCIENCE-20260822-06
lease=runtime/leases/dish_rbhr_r06_full_panel_lease_20260822.json
request=runtime/lease_requests/dish_rbhr_r06_full_panel_lease_request_20260822.json
identity_sha256=a816403058202e2847e53469b728fba349c7881adae60196ce0bdf6db2eba1ec
lease_chain_sha256=b208c467b7c878346cec31fd037222ffdb9a4c72d8e173f2855a3dec0164caa8
technical_disposition=ATOMIC_PRELAUNCH_TECHNICAL_RESOURCE_INCOMPATIBILITY
production_command_launched=false
load_root_lease_called=false
master_materialized=false
run_root_created=false
question_relevant_output=false
partial_value=false
r05_action=false
```

## Decision-level conclusion

The issued lease must not be launched. Prelaunch reconciliation of the exact
accepted measurement with the exact current executor exposed a material
technical/resource incompatibility: the production CLI has no eight-worker
execution mechanism, while the accepted wall estimate divided a sequential
component sum by eight. The measured persistent update is 7.3241497 seconds;
the current executor runs all 122,880 training updates synchronously one at a
time, so training wall alone projects to 249.9977 hours. That exceeds the
immutable 110-hour hard wall ceiling before evaluation, forks or inference.

Independently, the exact lease validity interval is 24 hours, shorter even than
the prior optimistic eight-worker wall projection of 33.1476 hours. The
shortfall is 9.1476 hours. Therefore neither the current serial executor nor
the earlier optimistic projection can complete within this lease.

No production loader or command was invoked. The sealed master was not opened
through the loader, no run root/frontier was created, and no identity activity,
model, checkpoint, training, evaluation, fork, inference, result or partial
value exists.

## Exact observed technical facts

The controlling source is synchronous:

- `R06ProductionDataPlane.preferred_batch("TRAINING", ...)` returns one;
- `_training_batch` rejects any `count != 1` and performs one complete
  4,096-transition update;
- `FullPanelExecutor.run_slice` calls `execute_units` inline and contains no
  worker pool, subprocess group or concurrent job scheduler; and
- the production CLI constructs one executor/data plane and calls one
  synchronous `run_slice`.

The current-byte acceptance receipt measured:

```text
full_4096_update_seconds=7.324149699998088
training_updates=122880
sequential_training_wall_hours=7.324149699998088*122880/3600=249.99764309326807
hard_wall_hours=110
```

The prior receipt's 33.14750367701922-hour wall number was computed as total
projected core-hours divided by eight. That division is unsupported by the
current executor. Its `workers=8` lease field is a ceiling/shape declaration,
not an implemented scheduler.

The exact lease records:

```text
issued_at=2026-08-23T02:20:42.164371Z
expires_utc=2026-08-24T02:20:42.168372Z
validity_hours=24.0000011114
prior_optimistic_wall_hours=33.14750367701922
optimistic_validity_shortfall_hours=9.1475025656
```

This incompatibility is established entirely from result-blind resource and
source/interface facts. It contains no question-relevant interpretation.

## Prior eligibility correction

The earlier E2B packet and request validator established source/hash,
inventory, atomic-resume and component resource facts, but their
`lease_request_issuable=true` conclusion is superseded for the current command
by this prelaunch finding. The exact request and issued lease remain durable
provenance; they are not safe execution authority for the current serial
executor.

The smallest unchanged-science repair is:

1. implement deterministic failure-atomic scheduling across at most eight
   independent block-arm training jobs and evaluation batches while preserving
   master-addressed order, sole checkpoints, paired mask/fork lineage and the
   one-identity frontier;
2. independently reaccept same-identity crash/resume and complete receipt order
   under that real scheduler;
3. remeasure actual aggregate CPU/wall/RSS/scratch/durable/I/O on the exact
   parallel command without dividing by an unimplemented worker count; and
4. prepare a fresh current-byte request and Root lease whose validity exceeds
   the accepted complete-run wall bound.

This is engineering repair under unchanged science. It neither rejects nor
alters the R06 panel. Operational Root owns withdrawal/replacement or extension
of the unstarted lease and any renewed engineering envelope.

## Four-layer translation

```text
observed_fact=The exact current executor is synchronous with TRAIN batch count one; measured update wall implies 249.9977 training hours alone against the 110-hour hard wall ceiling, and the 24-hour issued lease is shorter even than the unsupported optimistic 33.1476-hour projection.
local_action_fence=Do not launch runtime/leases/dish_rbhr_r06_full_panel_lease_20260822.json or open its sealed master through the production loader; no production action occurred.
scientific_stage_continuation=The immutable complete R06 panel remains empirically allocated; unchanged-science parallel scheduler repair, independent reacceptance and a correctly sized Root lease may continue without altering science.
continuation_owner=Operational Root for lease disposition and exact renewed CM engineering envelope; same DISH CM for unchanged-science scheduler repair if authorized; Portfolio receives this decision-level incompatibility.
root_decision_class=ATOMIC_SAME_IDENTITY_PRELAUNCH_TECHNICAL_RESOURCE_INCOMPATIBILITY|LEASE_RESOURCE_REPAIR_REQUIRED|NO_SCIENCE_CHANGE.
applies_to=Current bytes, exact issued R06 lease and exact production CLI only.
does_not_imply=Scientific ambiguity|panel shrink|replacement identity|partial result|R05 revival|provider|Git.
```
