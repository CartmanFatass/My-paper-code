# G35 Prelaunch Evidence Note

```text
document_kind=pm_prelaunch_runtime_evidence
algorithm_id=CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35
source_id=CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_P0
implementation_code_commit=42b9f85a7820ec5f4a3a7507d3a4e644b27fbc56
pm_technical_acceptance=accepted
scientific_interpretation=none
formal_compute_started=false
```

## Proof and integration evidence

The PM code check passed 14 G35-focused tests and 79 tests across the changed
shared G19-through-G35 policy surface. Syntax compilation passed for the shared
policy, G35 source, runner and focused tests.

The registered Experiment Operator then held exactly one bounded nonformal CPU
exercise:

```text
run_root=logs/nonformal_continuous_roster_reactive_reduction_g35_cpu_20260726_42b9f85_pm1
source_commit=42b9f85a7820ec5f4a3a7507d3a4e644b27fbc56
formal=false
authorization_token=absent
preflight_root=absent
exit_codes=train:0,evaluate:0,analyze:0
train_wall_time_seconds=49.3190127
evaluation_wall_time_seconds=6.9291847
analysis_wall_time_seconds=0.2012777
total_wall_time_seconds=56.4494751
backend=cpu
torch=2.7.0+cpu
torch_threads=1
replicates=1
arms=2
cells=33
training_transitions=15360
evaluation_transitions=12672
total_real_transitions=28032
optimizer_steps=120
operational_valid=true
branch=NONFORMAL_CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_EXERCISE_COMPLETE
```

PM reread the three terminal JSON artifacts and mechanically verified source
identity, CPU one-thread runtime, both arm gradient/lifecycle/replay predicates,
exact optimizer exposure, three capacity inventories, all 33 cells, zero
evaluation updates, checkpoint before/after identity and the empty operational
error list. PM did not rerun the experiment.

## Formal capacity projection

The frozen projection uses the separately measured stages:

```text
T_projected_formal=1.25*(30*T_train_nf+48*T_eval_nf+40*T_analysis_nf)
T_projected_formal_seconds=2275.2779432502575
T_projected_formal_minutes=37.92129905417096
T_projected_formal_hours=0.6320216509028493
formal_wall_clock_cap_seconds=28800
prelaunch_capacity_status=EXECUTABLE_WITHIN_BOUND
```

The formal inventory remains 460,800 training transitions, 608,256 evaluation
transitions, 1,069,056 total real transitions, 3,600 optimizer steps and 10,000
paired hierarchical bootstrap resamples. `H=48`, `K_search=0`, hypothetical
transitions are zero, and no nested rollout or replanning exists.

This note authorizes no formal run. The exact accepted implementation and
commit-bound code-science index must first pass the single zero-compute
`CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_CODE_SCIENCE_ALIGNMENT_AUDIT`.
