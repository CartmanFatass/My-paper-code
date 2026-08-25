# DISH RBHR r06 post-S2 current-byte residual cost/resource rebase CM assessment — 2026-08-23

```text
document_kind=code_manager_read_only_post_s2_residual_cost_resource_rebase
direction_id=degraded_incumbent_shadow_handover
exact_object_revision=DISH-RBHR-SCIENCE-20260822-06
portfolio_request=docs/session/PORTFOLIO_TO_ROOT_DISH_RBHR_R06_POST_S2_CURRENT_BYTE_RESIDUAL_COST_REBASE_20260823.md
assessment_disposition=PROCESS_REPAIR_TECHNICALLY_FEASIBLE_BUT_ORDINARY_CPU_AT_RISK|FINITE_TWO_STAGE_RESIDUAL_ENVELOPE_AVAILABLE
gross_architecture_engineer_days=LOW19|CENTRAL32|HIGH52
remaining_residual_engineer_days=LOW20|CENTRAL36|HIGH59
separate_sunk_actual_engineer_days=20
current_engineering_authority=NONE_ASSESSMENT_ONLY
future_lease_request_eligible=false
compute_class=none
source_test_or_runtime_action=false
sealed_master_or_identity_activity=false
question_relevant_output=false
r05_or_sgsp_action=false
```

## Decision-level conclusion

The current R06 science, native/data-plane flows, deterministic task graph and
most atomic-lifecycle contracts remain valuable. The production thread-pool
substrate and its S1/S2 concurrency evidence must be replaced. A bounded
isolated-process repair remains technically feasible, but the S2
`10.672341100056656`-second one-core update rebases training work to about
364.28 core-hours before nontraining work. That already exceeds the unchanged
320-core-hour ordinary target. The residual scope must therefore include an
explicit per-worker CPU/performance repair and measurement family; process
isolation alone is not enough.

On current evidence the remaining work is **20 / 36 / 59 experienced-engineer-
days** low/central/high. This is a fresh residual estimate from current
interfaces, salvage and newly observed process-resource risk. It is not
`19/32/52 - 20`, and the separate 20 sunk S1/S2 days are neither added to nor
subtracted from the forward envelope.

No current implementation is authorized by this assessment. A finite two-
stage forward envelope is available for Portfolio consideration; absent such
an exact decision, engineering remains no-current and may be revisited when an
isolated-process/per-worker CPU design is funded.

## Current-byte retain/adapt/replace/discard map

| Disposition | Current bytes/evidence | Exact technical treatment |
|---|---|---|
| **Retain** | Frozen R06 contract, population/address law, native C++ host/ABI, 32-lane TRAIN resets, recurrent policy/trainer, per-job persistent state, sole checkpoints, five-arm paired-mask evaluator, first-valid REAL/SHAM runner, metric store, 24-by-6,990 reducer/inference and result firewall | These are unchanged-science production flows. Process workers must call them without altering coordinates, stochastic order, optimizer semantics, paired lineage or complete-result rules. |
| **Retain** | `complete_stage_plan`: 120 block-arm training tasks, 3,600 evaluation tasks, 216 fork tasks and frozen stage barriers | The task/dependency graph is correct and independent of thread versus process transport. |
| **Adapt** | `TaskJournal`, ordered task-digest collector, stage-atomic global frontier and same-identity successor rules | Preserve schemas and ordering, but replace thread-local locks/observations with cross-process exclusive creation, process-safe file ownership, worker PID/generation binding and controller recovery after abrupt process exit. |
| **Adapt** | `R06ProductionDataPlane.execute_scheduled`, scheduled-receipt cache and training persist-to-journal recovery | Move construction into isolated worker processes; bind each worker to one exact block-arm job and process-local native/model cache; remove assumptions that Python objects, checkpoint caches or Torch global state are shared in memory. |
| **Adapt** | Exact CLI and resource guard | Add spawn-safe worker bootstrap, total-core assignment, child exit/receipt reconciliation, continuous process-group CPU/RSS/I/O observation and expiry checks. Preserve the existing loader and complete-result firewall boundary. |
| **Replace** | `ThreadPoolExecutor`, shared in-process `R06ProductionDataPlane`, thread-local active-count concurrency metric and global Torch thread configuration | Use isolated spawned processes with one explicitly budgeted core each (or another measured allocation totaling at most eight). Effective concurrency must be measured from completed native/PyTorch work, not live worker count. |
| **Discard for production acceptance** | S1 sleeping-fixture concurrency 8 and 0.2764% normalized coordination result | Retain only as journal mechanics evidence. S2's real native/PyTorch result supersedes it for throughput/resource eligibility. |
| **Discard for launch/eligibility** | Current thread scheduler, withdrawn 24-hour lease, superseded request and prior `lease_request_issuable=true` conclusion | Durable provenance only. None may launch, authorize identity activity or support a future request. |

No retained byte grants authority to reuse R05, SGSP, another direction's
runtime, or the withdrawn sealed master.

## Gross-to-residual bridge

The earlier 19/32/52 estimate priced a greenfield process scheduler around the
then-assumed 7.324149699998088-second update. Current bytes salvage the job
graph and much atomic/data-plane logic, but S2 adds an ordinary-CPU risk that
the gross estimate did not price.

| Work family | Gross low/central/high | Current-byte remaining low/central/high | Bridge |
|---|---:|---:|---|
| Isolated-process scheduler implementation | 6 / 10 / 16 | 5 / 9 / 15 | Retain deterministic task plans and CLI/executor entry interfaces; replace thread transport, shared data plane and worker lifecycle. |
| Failure-atomic coordination | 4 / 7 / 12 | 3 / 6 / 10 | Retain journal schemas, ordered digests and stage frontier; add cross-process ownership, abrupt-exit and persist/cache reconciliation. |
| Per-worker CPU/performance rebase and repair | included only as generic measurement risk | 3 / 6 / 10 | New explicit family caused by 10.6723411-second one-core result and predicted ordinary CPU failure. |
| Independent plus end-to-end acceptance | 5 / 8 / 13 | 5 / 8 / 13 | Thread acceptance does not accept the replacement process substrate; no credit. |
| Exact process-command resource remeasurement | 3 / 5 / 8 | 3 / 5 / 8 | Still wholly required for process-group CPU/wall/RSS/scratch/durable/I/O and bound `B`. |
| Future request preparation | 1 / 2 / 3 | 1 / 2 / 3 | Still wholly required after final accepted bytes and `B`; no current request is eligible. |
| **Total** | **19 / 32 / 52** | **20 / 36 / 59** | Salvage reduces scheduler/atomic work by 2/4/7 days, while the newly explicit CPU/performance family adds 3/6/10. |

This bridge is a bottom-up reassessment, not an accounting formula. The 20
days already spent on S1/S2 are recorded separately as sunk evidence-producing
work. They do not supply remaining authority, automatically lower residual
cost, or mechanically create a cumulative `39/68/111` decision number.

## Salvage: R06-specific versus reusable within DISH

### R06-specific salvage

Approximately 70–80% of the R06-specific experiment/data-plane bytes are
retained: population/addressing, 120 job identities, update order, persistent
state, checkpoint law, evaluation grouping, fork lineage, witness/support
rows, reducer/inference and firewall. The process repair changes how these
objects are scheduled, not what they mean.

The R06-specific adaptation is concentrated in worker bootstrap and
dependencies: block-arm job ownership, update-1,024 checkpoint release,
STRUCTURED claim evaluation/fork atomicity, complete metric barriers and exact
result sealing. None of this can be replaced by a generic unordered map.

### Reusable within DISH

Approximately 45–55% of the current scheduler/atomic implementation is
salvageable into a process scheduler: task plan concepts, task-journal schema,
ordered digest collection, global stage commit, same-identity successor rules
and result-blind resource seams. Once process-safe, the following should be
reusable within DISH:

- spawn-safe bounded worker pool and total-core budget;
- process PID/generation lifecycle and abrupt-exit reconciliation;
- create-only task progress plus ordered controller commit;
- process-group CPU/RSS/I/O observation; and
- exact-command cold/warm measurement and future lease-validity derivation.

Thread-local locks, in-memory caches, live-thread concurrency counts and shared
Torch runtime state have no production salvage. Reuse remains within DISH and
does not authorize shared-component changes or cross-direction transfer.

## 10.672341100056656-second comparability and process-resource rebase

The S2 single-update value is directly comparable only to a future worker that
uses the same current source, interpreter/backend, native TEST seam, Torch
intra-op/inter-op threads set to one and one budgeted CPU core. It is the best
current conservative process-worker baseline because the replacement design
also requires isolated one-core workers.

It is **not** interchangeable with the earlier 7.324149699998088-second value.
That earlier measurement preceded the real scheduler policy and did not prove
one-core process comparability. Mixing 7.324 seconds for CPU work with
10.672 seconds for concurrency would recreate the invalid resource model.

Using the S2-comparable value:

```text
single_job_wall = 10.672341100056656 * 1024 / 3600
                = approximately 3.03569 hours
serial_training_core_hours = 10.672341100056656 * 122880 / 3600
                           = approximately 364.2826 core-hours
```

Concurrency can reduce wall but cannot reduce those core-hours. Adding the
prior 15.1824 nontraining component estimate gives approximately 379.47
core-hours before process/journal overhead: above the 320-hour ordinary target,
though below the 560-hour hard ceiling. To fit 320 hours while reserving the
same nontraining work and no scheduler overhead, the persistent update must be
about 8.93 seconds or faster. Real overhead requires a lower threshold.

Accordingly, the replacement must measure and, if necessary, optimize the
per-worker update itself—batch formation, duplicate tensor conversion,
checkpoint serialization frequency, Torch kernel/thread configuration and
native/Python handoff—without changing PPO, recurrence, samples, update count
or scientific semantics.

Assessment scenarios for training wall, before nontraining work, are:

| Effective process concurrency | Training wall at 10.6723411 s/update | Gate implication |
|---:|---:|---|
| 8 | 45.54 h ideal, before overhead | CPU ordinary still fails unless per-update work improves; wall has room. |
| 7 | 52.04 h ideal, before overhead | Little ordinary wall room after nontraining and drains. |
| 6 | 60.71 h ideal, before overhead | Ordinary 65-hour wall is unlikely after other stages; hard 110 may remain feasible. |

These are analysis projections, not runtime evidence. A future process
measurement must report actual process-group CPU time, complete wall,
continuously sampled aggregate RSS, scratch/durable bytes and total I/O. It may
not infer CPU from wall or divide by worker count.

## Finite staged forward envelope

If Portfolio chooses current investment, the smallest finite envelope is:

### P1 — isolated-process substrate plus CPU repair

```text
scope=PROCESS_WORKER_SCHEDULER_ADAPTATION|PROCESS_SAFE_ATOMIC_COORDINATION|PER_WORKER_CPU_PERFORMANCE_REBASE_AND_REPAIR|RESULT_BLIND_SELF_AUDIT
engineer_days=LOW11|MANAGED21|HARD35
```

P1 must return before further work unless current bytes implement the process
worker boundary, preserve all frozen semantics, observe result-blind effective
concurrency at least six and overhead at most 30%, and project both ordinary
CPU/wall and every hard resource gate as satisfiable. A one-core comparable
update that remains above the ordinary CPU budget is a P1 resource boundary,
not permission to continue optimistically.

### P2 — conditional final acceptance, measurement and request preparation

```text
scope=INDEPENDENT_PROCESS_SCHEDULER_ACCEPTANCE|EXACT_END_TO_END_RESULT_BLIND_CLI|ACTUAL_PROCESS_GROUP_RESOURCE_REMEASUREMENT|ACCEPTED_BOUND_B|FUTURE_REQUEST_PREPARATION_AND_VALIDATION
engineer_days=LOW9|MANAGED15|HARD24
release_gate=P1_COMPLETE|P1_ACTUAL_LE35|P2_FORECAST_LE24|TOTAL_ACTUAL_PLUS_FORECAST_LE59|EFFECTIVE_CONCURRENCY_GE6|OVERHEAD_LE30PCT|CORES_LE8|GPU0|ORDINARY_AND_HARD_GATES_PROJECTED_SATISFIABLE|ALL_INVARIANTS
```

The total finite residual envelope is 20 managed-low / 36 central / 59 high as
specified above; P1 and P2 capacities are non-transferable. A future lease may
be prepared only after P2 establishes complete-run bound `B`, and must satisfy
`validity >= B + max(6h, 20% B)` and `validity > B`.

This assessment creates no P1/P2 authority. Without an exact Portfolio
decision applying P1, current engineering is **no-current**. Revisit when
Portfolio explicitly funds the isolated-process plus per-worker CPU repair, or
when a new result-blind measurement/substrate fact materially changes the
10.672-second resource rebase.

## Exact invalidations and fences

Current exact invalidations are:

- the thread scheduler's effective concurrency is 2.8553, below six;
- its parallel makespan overhead is 180.18%, above 30%;
- the 10.6723411-second comparable one-core update projects ordinary CPU above
  320 hours before process overhead; and
- no accepted complete-command resource bound `B` exists, so no future request
  is eligible and no lease duration can be instantiated.

Further process work must stop and return if concurrency remains below six,
overhead exceeds 30%, total cores exceed eight, any GPU is required, ordinary
CPU exceeds 320 hours, ordinary wall exceeds 65 hours, any hard ceiling fails,
or process isolation changes deterministic order, persistent optimizer/model/
recurrent state, sole checkpoints, paired mask/fork lineage, complete reducer,
result blindness, failure atomicity, one-identity semantics or the immutable
panel/science.

The withdrawn lease remains unlaunchable. No source/test edit or execution,
implementation, runtime/probe, production command, request/lease, sealed
master, nonfixture identity/coordinate/model/checkpoint/activity/result/partial
value, R05, SGSP, provider, Git, deployment or flight action occurred in this
assessment.

## Four-layer translation

```text
observed_fact=Current bytes retain most R06 flows and part of the atomic scheduler architecture, but thread transport is nonproduction and the comparable 10.6723411s one-core update projects approximately 364.28 training core-hours; residual isolated-process plus CPU-repair work is re-estimated at 20/36/59 days, with 20 sunk S1/S2 days recorded separately.
local_action_fence=Assessment only and no-current until a new exact owner decision; do not execute or edit current scheduler, restore the withdrawn lease, prepare a request or access any master/identity/activity/partial path.
scientific_stage_continuation=The immutable complete R06 panel remains empirically allocated; a finite P1 then conditional P2 unchanged-science process/CPU repair is available for Portfolio selection without changing science.
continuation_owner=Operational Root for exact relay; Portfolio for current-investment versus no-current/revisit decision; same DISH CM only under a later exact P1 envelope.
root_decision_class=POST_S2_READ_ONLY_RESIDUAL_COST_RESOURCE_REBASE|FINITE_P1_P2_OPTION_AVAILABLE|CURRENT_NO_ENGINEERING_AUTHORITY|NO_LEASE.
applies_to=DISH-RBHR-SCIENCE-20260822-06 current-byte process-scheduler residual and resource feasibility only.
does_not_imply=Implementation authority|accepted resource bound B|request eligibility|lease issuance|science change|panel shrink|replacement identity|R05 or SGSP action.
```
