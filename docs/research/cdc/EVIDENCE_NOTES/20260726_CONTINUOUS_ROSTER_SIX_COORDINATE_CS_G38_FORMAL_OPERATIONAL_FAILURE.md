# G38 formal operational failure

```text
algorithm_id=CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38
assignment_id=CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_FORMAL_ITERATION_29
run_root=logs/formal_continuous_roster_six_coordinate_cs_g38_cpu_20260726_0fd5f73_r1
source_commit=0fd5f73cc783d5056fdd8019e820965e522c7977
terminal=ERROR
analyzer_status=INVALID
operational_valid=false
result_branch=INVALID_CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38
iteration_cost=0
retry_resume_restart=none
```

## Bound execution

The registered Experiment Operator executed the authorized CPU-only formal
train, evaluate and analyze commands exactly once. All three commands exited
zero, and all terminal artifacts and 18 checkpoint files are present. The
serialized bindings independently checked by PM are:

```text
formal=true
backend=cpu
torch=2.7.0+cpu
torch_threads=1
authorization_token=CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_FORMAL_AUTHORIZATION_V1
alignment_disposition=ALIGNED
aligned_source_commit=0fd5f73cc783d5056fdd8019e820965e522c7977
preflight_root=C:/Users/fires/OneDrive/文档/HMASD-new/logs/nonformal_continuous_roster_six_coordinate_cs_g38_cpu_20260726_0fd5f73_r1
preflight_artifact_digests=train_evaluate_analyze_exact_match
replicates=3
arms=2
evaluation_cells=90
evaluation_episodes_per_cell=128
training_transitions=460800
evaluation_transitions=552960
total_real_transitions=1013760
optimizer_steps=3600
bootstrap_resamples=10000
K_search=0
train_seconds=1505.2007505000001
evaluate_seconds=122.4055260999994
analyze_seconds=2.9470029000003706
total_seconds=1630.5532795
```

## Exact operational defect

The analyzer rejected 34 of the 45 conclusion-bearing FOLD6 cells with
`G38 fold-equivalence mismatch`. Eleven FOLD6 cells passed. Every exact field
passed in every cell: log standard deviation, critic tensors, value output,
inactive actions and likelihoods, roster sizes, membership edits, lifecycle and
zero hidden carry.

The maxima across all 45 FOLD6 cells were:

```text
pre_tanh_mean=7.152557373046875e-07
actions=6.183981895446777e-07
prefix_action_sums=2.2649765014648438e-06
token_log_probability=3.814697265625e-06
reward_trace=4.106918257695824e-07
summary=1.637992121938936e-07
```

Only accumulated prefix-action error exceeded its unchanged `1e-6` limit.
The pre-fold ten-wide affine and folded six-wide affine used different floating
reduction orders despite the exact algebraic bias fold. This is an operational
implementation defect, not a scientific branch result. It may be repaired only
under the frozen constant, graph, fold equations, tolerances, seeds, budgets,
RNG, inventory and first-match semantics.

PM authorized no retry, resume, restart, alternate backend or result salvage.
The failed run remains read-only and consumes zero conclusion-bearing
iterations. The autonomous balance remains 28 consumed and 9 remaining.
