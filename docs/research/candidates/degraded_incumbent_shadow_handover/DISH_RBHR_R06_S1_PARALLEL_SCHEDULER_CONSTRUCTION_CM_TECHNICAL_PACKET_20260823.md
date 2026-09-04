# DISH RBHR r06 S1 parallel scheduler construction CM technical packet — 2026-08-23

```text
document_kind=code_manager_s1_parallel_scheduler_construction_self_audit_packet
direction_id=degraded_incumbent_shadow_handover
exact_object_revision=DISH-RBHR-SCIENCE-20260822-06
portfolio_boundary=docs/session/PORTFOLIO_TO_ROOT_DISH_RBHR_R06_FINITE_TWO_STAGE_SCHEDULER_REPAIR_20260823.md
technical_disposition=S1_COMPLETE|REAL_SCHEDULER_AND_ATOMIC_COORDINATION_CONSTRUCTED|RESULT_BLIND_SELF_AUDIT_ACCEPTED
s1_actual_engineer_days=17
s1_managed_engineer_days=17
s1_hard_ceiling_engineer_days=28
s2_remaining_forecast_engineer_days=MANAGED15|HIGH24
total_s1_actual_plus_s2_forecast_engineer_days=MANAGED32|HIGH41
overall_hard_ceiling_engineer_days=52
s2_release_gate_technical_fact=SATISFIED
production_compute=false
lease_request_or_lease=false
nonfixture_identity_or_activity=false
question_relevant_output=false
r05_action=false
```

## Decision-level conclusion

S1 is complete at its 17-day managed allocation. Current source now contains
and wires a real deterministic scheduler bounded to 6–8 workers, at most eight
total CPU cores and GPU0. It owns 120 independent block-arm training tasks,
keeps all 1,024 updates within each task ordered, releases evaluation only
after sole checkpoint completion, preserves evaluation-before-fork-before-
inference dependencies, collects out-of-order worker completions into ordered
task digests, and advances the global frontier only after a complete stage.

Each task has an identity-bound atomic journal. The data plane adds an
idempotent scheduled-receipt cache and an exact training recovery seam for the
persisted-state-to-journal crash window. A new scheduler instance resumes the
same task and identity from the durable journal without repeating committed
work. The production executor selects the scheduler only for the real R06 data
plane; existing serial TEST fixtures remain isolated.

The result-blind self-audit accepts every construction surface, observes eight
concurrent workers, and prices measured coordination overhead at 0.2764% of
the immutable 7.324149699998088-second update—below the 30% S1 gate. No
production loader, request, lease, sealed master, nonfixture identity,
coordinate, model, checkpoint or activity was created.

## Constructed scheduler and atomic coordination

### Deterministic job and dependency graph

`production_scheduler.py` constructs exact complete stage plans:

| Stage | Scheduled tasks | Unit coverage | Execution dependency |
|---|---:|---:|---|
| Population | 360 native width-32 tasks | 11,520 | First stage |
| Training | 120 block-arm tasks | 122,880 ordered updates | After population |
| Evaluation | 3,600 native width-32 tasks | 115,200 episodes | After every update-1,024 sole checkpoint exists |
| Fork | 216 width-32 sealing tasks | 6,912 claim rows | After evaluation has atomically persisted paired first-valid receipts |
| Inference | 1 complete task | 24-by-6,990 plus 99,999 resamples | After complete metric/fork inventories |

Workers may finish independently, but task digests are returned in frozen
task-index order. The full-panel executor chains those ordered digests and
atomically advances one complete stage. The scientific inventory and result
firewall remain unchanged; task digests are technical lifecycle identities,
not scientific observables.

### Core and thread policy

The scheduler refuses fewer than six or more than eight workers, more than
eight total cores, workers exceeding the core count, or any GPU. Before
parallel stages the production data plane sets PyTorch intra-op and inter-op
threads to one, preventing nested `8 workers × 8 threads` oversubscription.
Native host calls and frozen PyTorch kernels remain the compute surfaces; no
serial Python environment/rollout fallback was introduced.

### Failure atomicity and successor mechanics

Each scheduled task owns a create/replace atomic journal bound to the exact
identity, stage, task index, start, total units and width. The journal accepts
only the next consecutive unit frontier and cumulative receipt-chain hash.
After a worker failure, the successor scheduler validates the same identity
and resumes the first uncommitted unit.

The data plane's scheduled-receipt cache makes already returned batches
idempotent. For the narrower window where a training update's native,
recurrent and checkpoint bytes are durable but its scheduled receipt is not,
`_recover_training_receipt` accepts only the exact `update + 1` persistent
frontier and reconstructs the receipt from those same bytes. A later or
ambiguous frontier fails closed. Evaluation/fork receipts remain deterministic
and coordinate-addressed; the global frontier never exposes an incomplete
stage or partial result.

## S1 self-audit evidence

Controlling receipt:

```text
runtime/benchmarks/dish_rbhr_r06_s1_scheduler_self_audit_20260823.json
sha256=4376c6b9ed08a440813ce84ef5223413c59a958cc31b2d48728c3cd9ab425ae7
all_construction_checks=true
max_observed_concurrency=8
cores=8
gpu=0
scheduler_overhead_fraction=0.0027638865366830965
fixture_only=true
production_compute=false
question_relevant_output=false
```

The fixture launched eight journaled tasks concurrently. It injected a worker
failure after three committed updates, observed exactly three retained journal
commits, then constructed a new scheduler instance with the same TEST identity
and completed exactly eight. It also verifies complete plan cardinalities,
ordered collection, production executor wiring, data-plane crash-window
recovery and the no-partial-value manifest.

The overhead calculation separates the short fixture's 0.100-second synthetic
unit from measured journal/coordination time, then normalizes the observed
0.0202432 coordination seconds per unit against the frozen measured
7.324149699998088-second persistent update. This is an S1 construction
self-audit, not the exact parallel-command resource measurement reserved for
S2.

The pre-existing focused conformance/integration suite remains green:

```text
14 passed
```

The receipt is the controlling current-byte hash manifest for
`production_scheduler.py`, `production_data_plane.py`,
`production_full_panel.py` and `production_s1.py`.

## Cost accounting and S2 forecast

S1 accounts for 17 experienced-engineer-day equivalents, exactly its managed
allocation and 11 below its non-transferable 28-day hard ceiling. Remaining S2
is forecast at 15 managed / 24 high days. Therefore S1 actual plus S2 forecast
is 32 managed / 41 high, below the 52-day overall hard ceiling. Unused S1
capacity does not enlarge S2.

S2 remains responsible for independent scheduler acceptance, exact end-to-end
result-blind reacceptance, actual parallel-command CPU/wall/RSS/scratch/durable/
I/O measurement, establishment of accepted complete-run bound `B`, and future
request preparation under the rule `validity >= B + max(6h, 20% B)` and
strictly greater than `B`. No planning or fixture timing substitutes for S2's
actual result-blind measurement.

## S1 release-gate and invalidation checks

Every S1 release predicate is satisfied:

- S1 is complete at 17 days, at most 28;
- S2 high forecast is 24 days and total actual-plus-high forecast is 41, at
  most 52;
- the scheduler supports and the fixture observes concurrency 8, at least 6;
- observed coordination overhead normalized to the measured update is 0.2764%,
  below 30%;
- total cores are at most eight and GPU is zero; and
- all frozen semantics and resource assumptions remain intact.

Every invalidation predicate is false. Science revision, indivisible
256,513-unit panel, one future nonreplaceable identity, deterministic RNG and
commit order, persistent per-job model/optimizer/recurrent state, sole
checkpoints, paired mask/fork lineage, complete witness/support/reducer,
result blindness, no-partial-value firewall and immutable resource ceilings
are unchanged. No alternate substrate, panel shrink, replacement identity,
Python environment fallback, R05 action, provider action, Git action,
deployment or flight occurred.

S2 may reveal a technical/resource incompatibility if actual production-path
concurrency is below six, overhead exceeds 30%, or any ordinary/hard resource
bound fails. Those remain measurement risks, not current S1 invalidations.

## Four-layer translation

```text
observed_fact=A deterministic 6–8-worker/<=8-core/GPU0 R06 scheduler, ordered task collector, per-task failure-atomic journal, idempotent data-plane receipt cache and same-identity successor seam are current-byte constructed; result-blind self-audit observes concurrency 8 and 0.2764% measured-update-normalized coordination overhead.
local_action_fence=S1 construction/self-audit only: no S2 exact resource measurement or future request preparation, production compute, request/lease, sealed master, nonfixture identity/coordinate/model/checkpoint/activity/result/partial value, R05, provider or Git action occurred.
scientific_stage_continuation=The immutable complete R06 panel remains empirically allocated; conditional S2 may proceed under Operational Root because every exact S1 release predicate is satisfied.
continuation_owner=Operational Root for conditional S2 release; same DISH CM for S2; Portfolio receives any S2 invalidation and the final current-byte technical/resource return.
root_decision_class=S1_GATE_TECHNICALLY_SATISFIED|CONDITIONAL_S2_MAY_PROCEED|NO_LEASE.
applies_to=DISH-RBHR-SCIENCE-20260822-06 real scheduler and atomic coordination construction/self-audit only.
does_not_imply=S2 acceptance|accepted complete-run bound B|future request eligibility|lease issuance|empirical activity|scientific result|R05 revival.
```
