# G34 Alignment-Correction Prelaunch Evidence Note

```text
document_kind=pm_prelaunch_runtime_evidence
algorithm_id=CONTINUOUS_ROSTER_RANDOM_PROCESS_G34
source_id=CONTINUOUS_ROSTER_RANDOM_PROCESS_G34_P0
alignment_disposition=MISMATCH
repair_scope=exact_checkpoint_digest_binding_and_trace_recomputation_only
implementation_code_commit=973589414a865cf79ef9f80a33a8feb2d4aabf40
artifact_schema_version=2
pm_technical_acceptance=accepted
scientific_interpretation=none
formal_compute_started=false
```

## Correction evidence

The repair changes no frozen process, checkpoint set, controller, diagnostic,
estimand, threshold, seed, evidence volume or first-match branch. It adds only:

- independent strict loading and digest comparison for every declared
  replicate/kind/capacity model cell;
- serialized 48-step reward and roster-size traces;
- recomputation of utility, minimum step, four event windows, five process
  segments and roster validity from those traces before analysis;
- wrong-checkpoint, summary, reward-trace and roster-trace tamper regressions.

The repaired code passed 18 G34-focused tests and 31 tests with both exact G32
upstream test files. The registered Experiment Operator then held exactly one
new bounded nonformal CPU exercise:

```text
run_root=logs/nonformal_continuous_roster_random_process_g34_cpu_20260726_9735894_pm2
checkpoint_root=logs/formal_runtime_capacity_g32_cpu_20260725_fbce360_r1
source_commit=973589414a865cf79ef9f80a33a8feb2d4aabf40
schema_version=2
formal=false
authorization_token=absent
exit_codes=TRAIN:0,EVALUATE:0,ANALYZE:0
measured_wall_time_seconds=7.1
backend=cpu
torch_threads=1
cells=20
episodes=80
real_transitions=3840
reward_trace_length_per_episode=48
roster_trace_length_per_episode=48
optimizer_steps=0
operational_valid=true
operational_errors=0
branch=NONFORMAL_CONTINUOUS_ROSTER_RANDOM_PROCESS_G34_EXERCISE_COMPLETE
```

PM reread both terminal JSON artifacts and verified the schema, source commit,
nonformal authority, CPU identity, exact cell/transition inventory, all 80 trace
pairs, roster predicates, checkpoint before/after identity and empty error list.

## Formal capacity projection

The formal inventory remains 368,640 real transitions, 96 times the measured
nonformal inventory. Linear projection from 7.1 seconds is 681.6 seconds. A 10x
allowance for serialization, 18 independent checkpoint loads, the registered
10,000-resample bootstrap and machine variance is 6,816 seconds, or 1.90 hours,
below the eight-hour cap.

```text
H=48
intrinsic_K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
projected_formal_wall_clock_upper_allowance_hours=1.90
formal_wall_clock_cap_hours=8
prelaunch_capacity_status=EXECUTABLE_WITHIN_BOUND
```

This note authorizes no formal run. The one permitted correction-only
code-science alignment recheck must first return `ALIGNED`.
