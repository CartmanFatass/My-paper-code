# G35 Prelaunch Evidence Note

```text
document_kind=pm_prelaunch_runtime_evidence
algorithm_id=CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35
source_id=CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_P0
alignment_disposition=MISMATCH
repair_scope=exact_three_artifact_formal_preflight_validation_and_binding_only
implementation_code_commit=f626dfd8a345ef670e08e601344b67e28ffb3563
superseded_implementation_code_commit=42b9f85a7820ec5f4a3a7507d3a4e644b27fbc56
pm_technical_acceptance=accepted
scientific_interpretation=none
formal_compute_started=false
```

## Proof and integration evidence

The original accepted implementation passed 14 G35-focused tests and 79 tests
across the changed shared G19-through-G35 policy surface. Its later
implementation-post audit returned `MISMATCH` because formal admission trusted
a favorable analysis summary without validating and binding the exact bounded
nonformal training and evaluation artifacts.

The correction changes no arm, source, seed, credit rule, threshold, evidence
volume, estimand or first-match branch. It adds full three-artifact preflight
validation, exact frozen inventory checks, digest binding, stage-time projection
recomputation and formal artifact revalidation from the serialized absolute
preflight root. The corrected code passed 17 G35-focused tests and the complete
82-test G19-through-G35 shared regression. Syntax compilation passed for the
corrected runner and focused runner test.

The registered Experiment Operator then held exactly one bounded nonformal CPU
exercise:

```text
run_root=logs/nonformal_continuous_roster_reactive_reduction_g35_cpu_20260726_f626dfd_pm2
source_commit=f626dfd8a345ef670e08e601344b67e28ffb3563
formal=false
authorization_token=absent
preflight_root=absent
exit_codes=train:0,evaluate:0,analyze:0
train_wall_time_seconds=87.00778109999999
evaluation_wall_time_seconds=10.019150200000013
analysis_wall_time_seconds=0.18594130000008136
total_wall_time_seconds=97.2128726
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

PM independently reread the three terminal JSON artifacts without rerunning the
experiment. It verified exact source and runtime identity, equal frozen
configuration, both-arm parameter/gradient/lifecycle/replay predicates, exact
optimizer exposure, all three capacity inventories, all 33 cells, 264 episodes,
zero evaluation updates, checkpoint before/after identity and the empty
operational error list. It recomputed utility, minimum-step utility, all event
windows and all process segments from every serialized 48-step reward trace,
checked every 48-step roster trace, recomputed both manifest SHA-256 digests and
confirmed that `analysis_result.json` binds those exact files.

```text
training_manifest_sha256=a2f7b74d5ae1dc9f65b307d6a82e2d99e806026b20bb6fc90d661247f6010abf
evaluation_manifest_sha256=1866099d93e817b4a625dfeb4016a354ea18d1989dd429a872c9887e3e13b916
```

## Formal capacity projection

The frozen projection uses the separately measured stages:

```text
T_projected_formal=1.25*(30*T_train_nf+48*T_eval_nf+40*T_analysis_nf)
T_projected_formal_seconds=3873.237868250004
T_projected_formal_minutes=64.5539644708334
T_projected_formal_hours=1.0758994078472233
formal_wall_clock_cap_seconds=28800
prelaunch_capacity_status=EXECUTABLE_WITHIN_BOUND
```

The formal inventory remains 460,800 training transitions, 608,256 evaluation
transitions, 1,069,056 total real transitions, 3,600 optimizer steps and 10,000
paired hierarchical bootstrap resamples. `H=48`, `K_search=0`, hypothetical
transitions are zero, and no nested rollout or replanning exists.

This note authorizes no formal run. The exact accepted correction and
commit-bound code-science index must first pass the one permitted zero-compute
`CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_CODE_SCIENCE_ALIGNMENT_CORRECTION_RECHECK`.
