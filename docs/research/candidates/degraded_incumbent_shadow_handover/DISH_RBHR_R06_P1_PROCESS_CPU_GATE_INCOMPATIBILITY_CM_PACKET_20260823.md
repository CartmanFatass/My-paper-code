# DISH RBHR r06 P1 process/CPU gate incompatibility CM packet — 2026-08-23

```text
document_kind=code_manager_p1_atomic_process_cpu_gate_incompatibility
direction_id=degraded_incumbent_shadow_handover
exact_object_revision=DISH-RBHR-SCIENCE-20260822-06
portfolio_boundary=docs/session/PORTFOLIO_TO_ROOT_DISH_RBHR_R06_FINITE_P1_P2_PROCESS_CPU_REPAIR_20260823.md
technical_disposition=P1_CONSTRUCTION_PRESENT|P1_RELEASE_GATE_FAILED|ATOMIC_CONCURRENCY_AND_OVERHEAD_INCOMPATIBILITY
p1_actual_engineer_days=24
p1_managed_engineer_days=21
p1_hard_ceiling_engineer_days=35
p2_forecast_engineer_days=MANAGED15|HIGH24
p1_actual_plus_p2_high_forecast_days=48
total_residual_hard_ceiling_days=59
effective_concurrency=5.851119531933833
required_concurrency_min=6
parallel_overhead_fraction=0.3672597109558533
allowed_overhead_fraction_max=0.30
p2_released=false
future_lease_request_eligible=false
lease_issued=false
nonfixture_identity_or_activity=false
question_relevant_output=false
r05_or_sgsp_action=false
```

## Decision-level conclusion

P1 stops at an exact technical/resource invalidation. The isolated spawn-
process scheduler, process-safe journal path and CPU repair are current-byte
implemented, and the CPU repair materially improves the comparable persistent
update. Nevertheless, the final result-blind eight-process measurement
achieves effective concurrency **5.8511**, below the required six, and
parallel makespan overhead **36.73%**, above the allowed 30%. P2 therefore is
not released.

No production command, request, lease, sealed master, nonfixture master,
identity, coordinate, model, checkpoint, training, evaluation, fork,
inference, result or partial-value path was entered. R05 and SGSP remain
untouched. The withdrawn lease remains unlaunchable.

## P1 construction completed before the stop

The current source replaces the prohibited production thread pool with a
spawn-based `ProcessPoolExecutor` boundary. Each child:

- imports and constructs its own data-plane runtime through a fixed
  module/function worker specification;
- sets `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`, Torch intra-op=1 and
  inter-op=1;
- owns one process-local native/model/optimizer cache and one exact scheduled
  task at a time;
- writes only its identity-bound task journal and coordinate-addressed receipt
  bytes; and
- returns task index, ordered digest and PID to the controller.

The controller uses at most eight spawned processes, eight total physical-core
budget, GPU0, frozen stage plans and sorted task-digest commit. Task-journal
files remain create/replace atomic and are readable by a later process with the
same identity. The spawn-safe production lease worker entry point revalidates
the exact future request/lease before constructing a worker data plane; P1 did
not invoke that production entry point.

### Per-worker CPU repair

The main repair replaces row-by-row Python Welford updates with the exact
parallel-variance merge law. A result-blind scalar oracle over 4,096-by-54
deterministic rows agrees in count and within `1e-12` mean / `1e-8` M2
tolerances. Checkpoint technical hashing was reduced to one serialized
checkpoint plus domain-separated hashes, and redundant immediate checkpoint
reserialization was removed. Model, optimizer, recurrence, PPO epochs,
minibatches, samples and checkpoint bytes remain frozen.

This lowers the steady one-process comparable update from the prior
10.672341100056656 seconds to a three-run median of
**3.6649988000281155 seconds**, comfortably below the approximately 8.93-
second ordinary-CPU threshold identified by the residual rebase.

## Exact final result-blind process measurement

The measurement warmed every spawned worker with one complete TEST-native
4,096-transition update, then timed a second complete update concurrently in
eight distinct child processes. This excludes one-time Torch optimizer/import
initialization while retaining the exact steady production update path.

```text
single_process_steady_update_median_seconds=3.6649988000281155
eight_process_batch_wall_seconds=5.011005199979991
effective_concurrency=8*3.6649988000281155/5.011005199979991
                     =5.851119531933833
parallel_overhead=5.011005199979991/3.6649988000281155-1
                 =0.3672597109558533
parallel_worker_update_seconds=
  4.989061600062996|4.953460999997333|4.976713599986397|4.936944399960339|
  4.994593300041743|5.008728799992241|4.843661700026132|4.8986677000066265
```

All eight workers returned finite losses/gradient norms, exact 4,096-
transition inventories and checkpoint-resume acceptance. Separate process-
journal self-audit completed one task in one process, reopened the same
identity/journal in a different PID, and returned the identical terminal task
digest without reexecution. Every population/training/evaluation/fork/
inference task-plan cardinality remains exact.

The process count, total-core and GPU gates pass. The ordinary CPU/wall
projection also passes after the CPU repair: median parallel worker update
wall is about 4.965 seconds, projecting roughly 169.5 training core-hours and
about 184.7 core-hours including the prior nontraining component; modeled
complete wall is roughly 33.5 hours. These are P1 result-blind projections,
not P2 complete-command resource acceptance.

## Why the gate still fails

Process isolation removes the thread/GIL substrate failure and improves
effective concurrency from 2.8553 to 5.8511. The remaining shortfall is host-
level steady-update contention across eight independent Torch/native workers.
It is small in absolute terms but exact: concurrency is 0.1489 below six and
overhead is 6.73 percentage points above 30%. The owner packet requires stop
on either predicate and does not authorize rounding, optimistic selection or
P2 measurement. Both predicates therefore invalidate release.

The smallest possible continuation would be a new owner decision for a narrow
process-contention repair—process placement/topology, allocator/cache pressure
and steady checkpoint/digest contention—followed by a fresh independent P1
measurement. Unused P1 or P2 capacity does not automatically grant that
authority after this return.

## Cost and invariant disposition

P1 uses 24 scope-accounted experienced-engineer-day equivalents, above its
21-day managed target but below its nonreplenishable 35-day hard ceiling. P2
remains forecast at 15 managed / 24 high; P1 actual plus P2 high would be 48,
below 59. Those cost predicates pass, but cannot override the concurrency and
overhead failures.

No immutable scientific or technical semantic changed. The indivisible
256,513-unit panel, one future nonreplaceable identity, deterministic order,
persistent model/optimizer/recurrent state, sole checkpoints, paired mask/fork
lineage, complete reducer/inference, result blindness, failure atomicity,
no-partial-value firewall and resource ceilings remain intact. No science,
inventory, identity, substrate beyond CPU processes, R05, SGSP, provider, Git,
deployment or flight action occurred.

Complete-command CPU/wall/RSS/scratch/durable/I/O acceptance, bound `B`, future
validity duration and request eligibility remain unknown because exact P1
failure prohibits P2.

## Four-layer translation

```text
observed_fact=Current bytes implement isolated spawn workers and reduce steady comparable update wall to 3.6650s, but final eight-process TEST measurement yields effective concurrency5.8511<6 and overhead36.73%>30%; CPU/wall projections and other construction invariants pass.
local_action_fence=Stop before P2, complete-command resource measurement or request preparation; do not launch the current scheduler or any withdrawn lease. No nonfixture or partial activity occurred.
scientific_stage_continuation=The immutable complete R06 panel remains empirically allocated; only a later exact owner decision may authorize a narrow unchanged-science process-contention repair and fresh P1 gate.
continuation_owner=Operational Root for exact relay; Portfolio for any new finite engineering/resource decision; same DISH CM only under a later exact envelope.
root_decision_class=ATOMIC_P1_TECHNICAL_RESOURCE_INCOMPATIBILITY|CONCURRENCY_AND_OVERHEAD_GATE_FAILED|P2_NOT_RELEASED|FUTURE_REQUEST_NOT_ELIGIBLE|NO_SCIENCE_CHANGE.
applies_to=DISH-RBHR-SCIENCE-20260822-06 current isolated-process scheduler and P1 result-blind process/CPU self-audit only.
does_not_imply=Scientific ambiguity|panel shrink|replacement identity|lease eligibility|partial result|R05 or SGSP action.
```
