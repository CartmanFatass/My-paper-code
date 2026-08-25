# DISH RBHR r06 finite contention repair and fresh P1 gate CM packet — 2026-08-23

```text
document_kind=code_manager_fresh_p1_contention_gate_cost_resource_invalidation
direction_id=degraded_incumbent_shadow_handover
exact_object_revision=DISH-RBHR-SCIENCE-20260822-06
portfolio_boundary=docs/session/PORTFOLIO_TO_ROOT_DISH_RBHR_R06_FINITE_CONTENTION_REPAIR_AND_FRESH_P1_GATE_20260823.md
technical_disposition=NARROW_CONTENTION_REPAIR_PRESENT|ONE_FRESH_P1_GATE_EXECUTED|FRESH_GATE_FAILED|P2_NOT_RELEASED
additional_actual_engineer_days=9
additional_hard_ceiling_engineer_days=11
cumulative_p1_actual_engineer_days=33
cumulative_p1_hard_ceiling_engineer_days=35
p2_forecast_engineer_days=MANAGED15|HIGH24
cumulative_p1_actual_plus_p2_high_forecast_days=57
total_residual_hard_ceiling_days=59
effective_concurrency=5.591645139192109
required_concurrency_min=6
parallel_overhead_fraction=0.4307059551986976
allowed_overhead_fraction_max=0.30
p2_released=false
future_lease_request_eligible=false
lease_issued=false
nonfixture_identity_or_activity=false
question_relevant_output=false
r05_or_sgsp_action=false
```

## Decision-level conclusion

The one authorized fresh exact result-blind P1 gate fails. Current bytes retain
the isolated eight-process CPU substrate and add only the authorized steady
contention repairs, but the fresh measurement yields effective concurrency
**5.591645139192109**, below six, and parallel overhead
**0.4307059551986976**, above 0.30. P2 remains unreleased and no automatic
continuation is inferred from the completed repair or unused ceiling.

All other fresh-gate predicates pass: eight distinct warmed processes, at most
eight cores and GPU0; projected ordinary CPU **175.16081064151723 h** and wall
**33.14065826747723 h**; projected hard CPU/wall; conservative high aggregate
RSS **6.61 GiB**, scratch **1.66 GiB**, durable **0.83 GiB** and total I/O
**68.14 GiB**; update integrity, Welford equivalence, same-identity successor
journal semantics and complete frozen task-plan inventories. The failed
concurrency and overhead predicates are exact and are not rounded or replaced
by the passing resource projections.

## Bounded contention repair applied

Only the addendum's existing CPU-process contention surfaces changed:

1. The frozen PPO update now materializes only the eight policy heads actually
   consumed by its loss. The complete recurrent action ABI still calls the
   unchanged full-head method, including prediction-cholesky and all FLEX
   outputs. Omitted update-only tensors had no loss consumer and therefore no
   gradient or optimizer transition; removing their temporary allocation
   reduces per-process allocator/cache pressure without changing model,
   optimizer, recurrence, sample, epoch, minibatch or checkpoint semantics.
2. Static 4,096-fragment, return/value and 512-row service-Q indices are
   allocated once per update instead of rebuilt in every minibatch.
3. The exact serialized checkpoint is scanned once. Its checkpoint digest is
   retained, and the MODEL/OPTIMIZER receipt domains bind that digest instead
   of rescanning the full checkpoint bytes twice. Sole-checkpoint and resume
   bytes are unchanged.
4. The existing topology audit showed hard compact/spread placement reducing
   throughput on this 8-core/16-logical AMD host, so the accepted substrate
   retains OS placement, one Torch intra-op/inter-op thread per process and
   high process priority. No new core, GPU or substrate was introduced.

The source compiled before the gate. That syntax check was not a performance
measurement. The gate function then executed exactly once under this addendum;
an earlier direct-script invocation stopped at import before entering the gate
and created no measurement or artifact.

## Exact fresh result-blind gate

The self-audit warmed the single-process worker, measured three steady updates,
warmed all eight spawned workers with one complete TEST-native update apiece,
then timed exactly one second eight-update batch. It also executed the retained
scalar Welford oracle and same-identity cross-process journal audit. No result
or partial scientific value exists in the receipt.

```text
single_process_steady_update_median_seconds=3.3999508999986574
eight_process_batch_wall_seconds=4.86433000001125
effective_concurrency=8*3.3999508999986574/4.86433000001125
                     =5.591645139192109
parallel_overhead=4.86433000001125/3.3999508999986574-1
                 =0.4307059551986976
parallel_worker_update_seconds=
  4.591953400056809|4.84853740001563|4.7215593999717385|4.84438120003324|
  4.635080700041726|4.634553599986248|4.652176399948075|4.861855400027707
median_parallel_worker_update_seconds=4.686867899959907
```

The single-worker repair improves the previous 3.6649988000281155-second
steady measurement to 3.3999508999986574 seconds. Simultaneous workers also
improve in absolute makespan from 5.011005199979991 to 4.86433000001125
seconds. The single-worker improvement is larger, however, so the exact
relative concurrency and overhead gates regress and remain unsatisfied. This
is a host-level all-core scaling fact, not evidence about the immutable R06
science or panel.

## Current-byte artifacts

```text
benchmark=runtime/benchmarks/dish_rbhr_r06_p1_fresh_contention_gate_20260823.json
benchmark_sha256=9e9ac66ab505d49b98481974eaa2c9370bd382861757b884167e564c7154ce29
source_sha256.production_training_engine.py=995b6642c4f4ca2a16fea061ffebc66e75f072c650a69c460dfbfa5f0f73f70b
source_sha256.production_p1.py=0d4dcc6c2245042271ee4e0a2754ebc943c23397a583dbd5c774c518f6789ed2
source_sha256.production_scheduler.py=8544fb0c456281217c1f8d02430b8e1c3f07ba1c0d3c9d6258998bdb26f7d62a
source_sha256.production_lease.py=82f912f30db966d2e3a4894920b7222bbcb93d4c04c4a23d4e13fc00e69f2fb4
source_sha256.production_data_plane.py=ee422d2294ebc92939662ff52a6c25eca335c9f8cf925c24a0b1c44421b58da8
```

## Cost, invariant and fence disposition

The narrow repair and one fresh gate consume nine additional experienced-
engineer-day equivalents. Cumulative P1 is therefore **33**, within 35; adding
the unchanged P2 high forecast of 24 gives **57**, within 59. Cost and every
non-concurrency resource predicate pass, but they cannot override either exact
performance-gate failure.

The Pro-closed R06 object, indivisible 256,513-unit panel, one future
nonreplaceable identity, deterministic order, persistent model/optimizer/
recurrent state, sole checkpoints, paired mask/fork lineage, complete reducer
and inference, result blindness, failure atomicity and no-partial-value
firewall remain unchanged. No P2, complete-command resource measurement,
bound B, request preparation, lease request, lease, withdrawn-lease restore,
sealed master, nonfixture master/identity/coordinate/model/checkpoint/activity,
question-relevant result, partial value, R05, SGSP, provider, Git, deployment
or flight action occurred.

## Four-layer translation

```text
observed_fact=Authorized contention-only current-byte repair improves absolute single and eight-process update wall, but the one fresh exact TEST gate returns effective concurrency5.591645139192109<6 and overhead0.4307059551986976>0.30; every other gate including cost and projected resources passes.
local_action_fence=Return before P2 and do not repeat the one fresh gate, enter complete-command measurement/bound-B/request/lease/nonfixture activity, or launch any withdrawn lease.
scientific_stage_continuation=Immutable R06 remains empirically allocated, but this addendum is exhausted; only Portfolio may decide any later technical/resource continuation.
continuation_owner=Operational Root for exact relay; Portfolio for the required fresh-gate pass/fail intake and any later finite decision.
root_decision_class=FRESH_P1_TECHNICAL_RESOURCE_INCOMPATIBILITY|CONCURRENCY_AND_OVERHEAD_GATE_FAILED|P2_NOT_RELEASED|NO_SCIENCE_CHANGE.
applies_to=DISH-RBHR-SCIENCE-20260822-06 current CPU-process contention repair and the single fresh result-blind P1 gate only.
does_not_imply=Science ambiguity|panel shrink|replacement identity|P2 release|lease eligibility|partial result|R05, SGSP, RISP or RCLE change.
```
