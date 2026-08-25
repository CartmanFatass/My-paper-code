# G38 formal result evidence

```text
algorithm_id=CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38
source_id=CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_P0
assignment_id=CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_FORMAL_ITERATION_29_REPAIRED_ATTEMPT_2
run_root=logs/formal_continuous_roster_six_coordinate_cs_g38_cpu_20260726_ea93b15_r2
source_commit=ea93b15eabf68c35ba8e459ca8527e56d2988db8
formal=true
status=COMPLETE
operational_valid=true
operational_errors=[]
registered_branch=SIX_COORDINATE_ARCHITECTURAL_REDUCTION_SUFFICIENT_G38
iteration=29
iteration_cost=1
scientific_interpretation=SUPPORTED_RETAINED_FRESH_FOLDED_SIX_COORDINATE_CONFIGURED_CAPACITY_BOUNDED_PROCESS_CONTINUOUS_ROSTER_G38
valid_result_disposition=CONTINUE
next_action=CONTINUOUS_ROSTER_NATIVE_SIX_COORDINATE_TRAINING_G39_DESIGN_ASSERTION_AUDIT
```

## Identity and repaired boundary

The valid execution uses the PM-accepted fold-kernel repair commit, the exact
`ALIGNED` correction recheck, the repaired-source bounded preflight and the
frozen G38 V1 formal token. The earlier `0fd5f73` formal attempt remains a
separate read-only operational-invalid run with zero iteration cost. It was not
resumed, reused or salvaged.

```text
backend=cpu
torch=2.7.0+cpu
torch_threads=1
authorization_token=CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_FORMAL_AUTHORIZATION_V1
alignment_disposition=ALIGNED
aligned_source_commit=ea93b15eabf68c35ba8e459ca8527e56d2988db8
preflight_root=C:/Users/fires/OneDrive/文档/HMASD-new/logs/nonformal_continuous_roster_six_coordinate_cs_g38_cpu_20260726_ea93b15_r1
train_exit_code=0
evaluate_exit_code=0
analyze_exit_code=0
train_seconds=2088.4485000999994
evaluate_seconds=153.51740570000402
analyze_seconds=7.996405400001095
total_seconds=2249.9623112000045
```

## Frozen inventory

```text
replicates=3
arms=2
training_capacity=8
evaluation_capacities=6|8|12
evaluation_cells=90
evaluation_episodes_per_cell=128
H=48
training_transitions=460800
evaluation_transitions=552960
total_real_transitions=1013760
optimizer_steps=3600
bootstrap_resamples=10000
K_search=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
```

PM independently reran the registered training/evaluation identity validator,
checked both terminal artifact digests and recomputed the first-match selector.
The error list was empty and the recomputed branch exactly matched the stored
branch. All 45 conclusion-bearing FOLD6 cells passed their fold-equivalence
gate. Every maximum error was exactly zero for pre-tanh means, actions,
prefix-action sums, token log probabilities, reward traces and summaries.

## Registered predicates

```text
source_valid=true
full_access_pass=true
fold_access_pass=true
full_access_confident_fail=false
fold_access_confident_fail=false
fold_equivalence_pass=true
six_coordinate_noninferior=true
material_info_advantage=false
full_information_advantage_subpredicate=null
FULL10_minus_FOLD6_primary_CI95=[-0.01008620876485097,-0.0031272915109353447,0.008414676838030393]
```

The registered first-match branch is therefore immutable:

```text
SIX_COORDINATE_ARCHITECTURAL_REDUCTION_SUFFICIENT_G38
```

External Pro accepts this branch inside G38-P0: the final true six-coordinate
deployment actor is sufficient under the registered configured-capacity and
bounded-process family, while learned carry, actual actor-history access,
donor/filler machinery and ten-coordinate deployment are not load-bearing.
The result does not establish native-six training equivalence, individual field
redundancy, critic-time or G31-credit redundancy, global memorylessness, UAV
transport or arbitrary process/capacity/horizon generalization. The current
scheduled action tests only the redundant constant-column training geometry;
other live and parked portfolio directions remain preserved.
