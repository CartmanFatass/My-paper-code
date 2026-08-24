# DISH RBHR r06 scheduler-repair cost and feasibility CM assessment — 2026-08-23

```text
document_kind=code_manager_read_only_scheduler_repair_cost_feasibility_assessment
direction_id=degraded_incumbent_shadow_handover
exact_object_revision=DISH-RBHR-SCIENCE-20260822-06
portfolio_request=docs/session/PORTFOLIO_TO_ROOT_DISH_RBHR_R06_SCHEDULER_REPAIR_COST_DECOMPOSITION_20260823.md
assessment_disposition=TECHNICALLY_FEASIBLE_CONDITIONAL_ON_PRICED_REAL_SCHEDULER_AND_FRESH_ACCEPTANCE
total_engineer_days=LOW19|CENTRAL32|HIGH52
compute_class=none
source_or_test_edit=false
runtime_or_probe=false
lease_request_or_lease=false
sealed_master_or_identity_activity=false
question_relevant_output=false
r05_action=false
```

## Decision-level conclusion

The unchanged-science scheduler repair is technically feasible. A bounded
eight-core process scheduler can exploit the 120 independent `(block, arm)`
training jobs while keeping all 1,024 updates within each job strictly ordered,
then schedule checkpoint-bound evaluation batches and their dependent
REAL/SHAM/metric work. The complete repair, independent acceptance, exact
parallel-command resource remeasurement and future request preparation are
estimated at **19 / 32 / 52 experienced-engineer-days** low/central/high.

This is an assessment, not implementation or runtime acceptance. Feasibility
depends on actually constructing and measuring the priced scheduler. Merely
setting `workers=8` or dividing serial work by eight remains invalid.

## Cost decomposition

| Work family | Low | Central | High | Included work |
|---|---:|---:|---:|---|
| Scheduler implementation | 6 | 10 | 16 | Fixed pool of at most eight process workers; deterministic block-arm job queue; explicit total-core budget; per-worker native/model cache; dependency-aware TRAIN→checkpoint→evaluation/fork scheduling; ordered receipt collector; CLI integration and shutdown. |
| Failure-atomic coordination | 4 | 7 | 12 | Claim/commit boundary for each completed batch; create-only job generations; parent/hash validation; out-of-order receipt reorder buffer; crash/restart without duplicate optimizer updates or fork execution; aggregate resource guard and atomic global frontier. |
| Independent plus end-to-end acceptance | 5 | 8 | 13 | Deterministic equivalence against the serial TEST oracle; update/checkpoint byte and order checks; worker-death injection at every commit boundary; same-identity successor slices; complete 256,513-unit TEST CLI; result-firewall and no-partial-value checks. |
| Exact parallel-command resource remeasurement | 3 | 5 | 8 | Cold and warm exact command; worker-width sweep bounded by eight total cores; continuously sampled process-group RSS; CPU/wall, scratch/durable and read/write totals; oversubscription audit; full-panel projection from the accepted real width. |
| Future lease preparation | 1 | 2 | 3 | Bind the newly accepted source/receipt/resource bytes, exact scheduler width and command; validate immutable inventory and one-identity envelope; specify a sufficiently long validity interval. No issuance included. |
| **Total** | **19** | **32** | **52** | Scope-accounted experienced-engineer-day equivalents. |

The high case remains bounded engineering rather than a substrate rewrite. It
covers Windows process-spawn and handle-lifecycle friction, PyTorch/native
thread oversubscription repair, an additional atomic-frontier iteration and a
second full acceptance/measurement pass. It does not include science changes,
panel shrink, GPU work, more than eight cores, or replacement identity logic.

## Priced scheduler design

The cost estimate assumes the following concrete design rather than an
unimplemented concurrency declaration:

1. **Eight-core total budget.** The controller starts at most eight worker
   processes. Each worker's PyTorch intra-op/native thread count is set so the
   process-group total never exceeds eight cores; for the ordinary design this
   is one execution core per worker. Nested eight-thread training inside eight
   workers is forbidden.
2. **Training job is the ownership unit.** Each of 120 `(block, arm)` jobs owns
   one native state, recurrent state, model, optimizer, Welford state and sole
   checkpoint. Its 1,024 updates remain sequential. Different jobs may execute
   concurrently because RNG addresses and checkpoint identities are already
   block-arm addressed.
3. **Dependency-aware downstream queue.** Evaluation work becomes runnable
   only after its exact block-arm checkpoint reaches update 1,024. A
   STRUCTURED claim batch atomically seals its first-valid REAL/SHAM receipts
   before its evaluation receipt is globally committed. Metric/inference work
   begins only after complete required inventories exist.
4. **Deterministic global commit order.** Workers may finish out of order, but
   a controller-side reorder buffer commits receipts in frozen stage/index
   order. A worker completion is not a global frontier advance until all
   durable component hashes for that batch validate.
5. **Same-identity failure recovery.** Worker-local generations are
   create-only and parent-bound. After failure, the controller reuses accepted
   completed bytes, discards only uncommitted temporary bytes and resumes the
   same job/identity. It never repeats a committed optimizer update or
   REAL/SHAM fork.

The low case assumes these mechanisms fit the existing data-plane boundaries.
The central case includes moderate restructuring of the executor and
per-job persistence. The high case includes a dedicated coordinator journal
and repair of one cross-process checkpoint/metric-store interaction.

## Explicit resource model

The immutable measured input is:

```text
persistent_update_wall_seconds=7.324149699998088
updates_per_job=1024
training_jobs=120
training_updates=122880
serial_training_wall_hours=249.99764309326807
single_job_training_wall_hours=2.0833136924439007
nontraining_measured_core_hours=15.182386322885742
```

Concurrency is priced only through the scheduler above. The training model is

```text
training_wall = 249.99764309326807 / effective_training_concurrency
                * (1 + training_scheduler_overhead)
```

The nontraining model is

```text
nontraining_wall = 15.182386322885742 / effective_nontraining_concurrency
                   * (1 + nontraining_scheduler_overhead)
```

and a fixed coordination allowance covers startup, final drains and atomic
stage transitions.

| Scenario | Effective TRAIN concurrency | TRAIN overhead | Effective nontraining concurrency | Nontraining overhead | Fixed coordination | Projected complete wall |
|---|---:|---:|---:|---:|---:|---:|
| Low | 8 | 5% | 8 | 10% | 1 h | 35.90 h |
| Central | 7 | 15% | 6 | 20% | 2 h | 46.11 h |
| High | 6 | 30% | 4 | 35% | 4 h | 63.29 h |

These are assessment projections, not accepted resource evidence. They make
concurrency and overhead explicit and keep even the high modeled wall below
the unchanged 65-hour ordinary target. Exact parallel-command measurement may
move any scenario.

CPU concurrency reduces wall, not work. Applying scheduler/coordination CPU
overheads of 3% / 8% / 20% to the measured 265.1800294161538 core-hour
component estimate yields approximately 273.14 / 286.39 / 318.22 core-hours,
all below the 320-hour ordinary target. Conservative aggregate estimates for
the other resources are:

| Resource | Low | Central | High | Hard ceiling |
|---|---:|---:|---:|---:|
| Aggregate RSS | 2.75 GiB | 3.86 GiB | 6.61 GiB | 40 GiB |
| Scratch | 0.73 GiB | 1.00 GiB | 1.66 GiB | 120 GiB |
| Durable | 0.37 GiB | 0.50 GiB | 0.83 GiB | 16 GiB |
| Total I/O | 37.48 GiB | 45.99 GiB | 68.14 GiB | 400 GiB |

These use explicit multipliers over the prior result-blind component estimates:
RSS `1.25x / 1.75x / 3.0x`, storage `1.1x / 1.5x / 2.5x`, and I/O
`1.1x / 1.35x / 2.0x`. They price process duplication, atomic temporary bytes,
reorder buffering and checkpoint replay. They do not replace the required
process-group measurements.

## Future lease-validity rule

Let `B` be the later independently accepted complete-run wall bound of the
exact parallel command, including its measured scheduler overhead, successor-
slice restart allowance and final result sealing. A future lease must satisfy:

```text
lease_validity_hours >= B + max(6 hours, 0.20 * B)
lease_validity_hours > B
```

The lease starts no earlier than the intended production launch window and its
expiry check must be enforced by the loader and before every successor slice.
No fixed duration from this assessment substitutes for the later measured
`B`. For illustration only, the central 46.11-hour assessment would require at
least 55.34 hours; the high 63.29-hour assessment would require at least 75.95
hours. The withdrawn 24-hour lease cannot satisfy the rule.

## Critical path and safe parallelism

The central 32 engineer-days have an approximately 29-day technical critical
path:

1. scheduler skeleton, worker/core policy, job graph and production adapters — 10 days;
2. atomic coordinator/reorder journal — 7 days, with about 3 days overlapping
   late scheduler adapters;
3. independent and end-to-end acceptance — 8 days;
4. exact parallel resource remeasurement and width selection — 5 days; and
5. future request preparation/validation — 2 days.

Safe engineering parallelism is limited. Worker-process adapters and
controller journaling can proceed in parallel after the job/receipt interfaces
freeze. Deterministic equivalence fixtures can be prepared alongside late
implementation. Resource measurement cannot begin until scheduler and atomic
acceptance are complete, and request preparation cannot finish until the
measurement bytes are final. Multiple engineers must not independently alter
the frontier, checkpoint or metric-commit contract.

## Reusable versus R06-specific work

Approximately 55–65% of the central implementation/coordination work is
reusable within DISH:

- bounded process pool and total-core enforcement;
- worker health, shutdown and process-group resource observation;
- create-only generations, parent/hash checks and ordered receipt commit;
- same-identity successor-slice mechanics; and
- cold/warm resource-measurement harnesses.

The remaining 35–45% is R06-specific:

- 120 block-arm persistent training-job identities and sole checkpoints;
- update-1,024 dependency release into the five-arm evaluation plan;
- paired mask-on/off batch grouping;
- first-valid STRUCTURED claim-tape REAL/SHAM fork suborder;
- 6,912 fork receipts, complete witness/support denominators and 24-by-6,990
  metric/inference barriers; and
- R06 result-firewall and exact lease-request inventory.

Reuse means only within the DISH engineering family. It grants no shared-code
mutation authority and cannot alter another direction's scheduler semantics.

## Uncertainty and invalidation conditions

Primary cost/resource uncertainties are Windows process startup and file-handle
behavior; PyTorch intra-op and native-library thread oversubscription; model and
optimizer copy-on-spawn cost; checkpoint fsync contention; out-of-order worker
completion; process-group RSS observability; and whether evaluation/fork
dependency granularity requires smaller durable commits than currently
assumed.

The estimate must be revisited if any of these occurs:

- the measured 4,096-transition update changes materially from
  7.324149699998088 seconds on the exact scheduler host;
- accepted effective training concurrency is below six or scheduler overhead
  exceeds 30%;
- aggregate CPU crosses 320 ordinary or 560 hard core-hours, complete wall
  crosses 65 ordinary or 110 hard hours, or any RSS/storage/I/O hard ceiling is
  projected to fail;
- correctness requires more than eight total cores, GPU use, a different
  native host/substrate or a serial Python environment/rollout path;
- deterministic RNG/receipt ordering, persistent optimizer state, sole
  checkpoints, paired mask/fork lineage, complete reducer, result blindness or
  failure atomicity cannot be retained; or
- science, inventory, panel, one-identity semantics, claim or result firewall
  would have to change.

The first three are engineering/resource re-estimation triggers. The latter
three are exact technical or science/resource invalidations returned before
any future lease or identity action.

## Four-layer translation

```text
observed_fact=Read-only current-source/resource analysis prices the unchanged-science real scheduler, atomic coordination, acceptance, remeasurement and future request preparation at 19/32/52 engineer-days; explicit priced concurrency projects 35.90/46.11/63.29 wall hours but remains unaccepted until real parallel-command measurement.
local_action_fence=Assessment only: no source/test edit, implementation, probe, runtime, request, lease, sealed master, identity/coordinate/model/checkpoint/activity/result/partial value, R05, provider or Git action occurred.
scientific_stage_continuation=The immutable indivisible R06 panel remains empirically allocated; Portfolio may decide whether to authorize this finite unchanged-science scheduler-repair envelope.
continuation_owner=Operational Root for exact relay; Portfolio for the engineering-cost decision; same DISH CM only under a later exact implementation envelope.
root_decision_class=READ_ONLY_SCHEDULER_REPAIR_COST_FEASIBILITY_RETURN|PORTFOLIO_RESOURCE_DECISION_REQUIRED|NO_LEASE.
applies_to=DISH-RBHR-SCIENCE-20260822-06 scheduler repair, atomic acceptance, resource remeasurement and future request preparation only.
does_not_imply=Implementation authority|accepted resource bound|lease request|lease issuance|science change|panel shrink|replacement identity|R05 revival.
```
