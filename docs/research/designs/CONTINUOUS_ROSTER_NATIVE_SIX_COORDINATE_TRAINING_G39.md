# Continuous Roster Native Six-Coordinate Training G39

```text
document_kind=pm_code_realization
algorithm_id=CONTINUOUS_ROSTER_NATIVE_SIX_COORDINATE_TRAINING_G39
source_id=CONTINUOUS_ROSTER_NATIVE_SIX_COORDINATE_TRAINING_G39_P0
external_pro_disposition=IDENTIFIABLE_FUNCTION_MATCHED_NATIVE_SIX_TRAINING_G39_DESIGN
scientific_authority=external_pro
implementation_authority=project_manager
implementation_status=pending_exact_realization_and_pm_technical_acceptance
formal_compute_status=not_eligible_before_external_pro_alignment_and_same_source_preflight
training=paired_CONST10_FOLD6_vs_Native6_CS
```

## Controlling contract

The exact scientific contract is the External-Pro response in
`docs/external-review/rounds/20260727_continuous_roster_native_six_coordinate_training_g39_design_assertion_audit/21_PRO_OPEN_RAW.md`.
This record is only the PM implementation pointer; the raw response controls if
any shorthand here is incomplete.

G39 compares two fresh, paired, no-carry training parameterizations with the
same six-coordinate policy-function class:

- `CONST10_FOLD6` preserves the accepted G38 ten-coordinate affine entries,
  internally appends `(1/2,1/2,1/2,24/47)`, and is folded before evaluation.
- `NATIVE6_CS` has exactly `Linear(6,32)` and `Linear(6,2)` raw-input maps from
  initialization and never contains a filler, constant column or fold.

The intended treatment is exactly the absence from `NATIVE6_CS` of 136
constant-column weights, their independent Adam moments and the post-training
fold. Actor information, function class, downstream graph, critic, G31 credit,
source, reward, lifecycle, action distribution, training interactions, PPO
passes, optimizer-step counts and checkpoint rule remain matched. G39 cannot
establish task-level history necessity or native-six inexpressivity.

## Function-matched initialization

For each replicate, initialize `CONST10_FOLD6` once and deterministically derive
`NATIVE6_CS`; independent native initialization is forbidden. For each of the
two raw-input affines, freeze:

```text
W_native = W_const[:,0:6]
b_native = b_const + W_const[:,6:10] @ c
c = [1/2,1/2,1/2,24/47]
```

Copy every unaffected actor, critic, baseline and log-standard-deviation tensor
bitwise. Before training, the folded CONST zero checkpoint and native zero
checkpoint must be bitwise equal, their complete first paired 8-episode,
48-step trajectory must match, both Adam states must be empty and separate,
and the frozen live-gradient and analytic reparameterization identities in the
raw contract must pass. The 136 extra CONST scalars must have a genuine nonzero
gradient under at least one registered objective.

Both arms collect and validate their paired trajectories before either update.
They receive only source coordinates `0:6`; CONST appends constants internally.
No model, optimizer, tensor, buffer or RNG state may be shared between arms.

## Frozen evidence

```text
H=48
K_search=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
per_episode_complexity=O(H)
optimizer=Adam(beta1=0.9,beta2=0.999,eps=1e-8,weight_decay=0)
learning_rate=1e-3
ppo_passes=2
checkpoint_selection=final_only
formal_replicates=3
training_capacity=8
fast_updates_per_arm_per_replicate=100
return_to_go_updates_per_arm_per_replicate=100
environments_per_update=8
evaluation_capacities=6|8|12
evaluation_episodes_per_cell=64
formal_total_cells=90
formal_training_transitions=460800
formal_evaluation_transitions=276480
formal_total_real_transitions=737280
formal_optimizer_steps=3600
bootstrap_resamples=10000
episode_exclusions=none
```

The formal evaluation uses 64 unique G34 time tuples per replicate/capacity,
retains one each of L/R/J/T, preserves only LRJT/LJRT/JLRT with rotating
22/21/21 counts, and uses the same base ledger and action stream for both arms.
The whole-episode hierarchical bootstrap resamples the three paired replicate
blocks and all 64 paired episode IDs, weights capacities equally and reuses one
plan for every absolute and paired estimand. The bootstrap seed is `10398039`.

The bounded nonformal package uses one replicate, ten fast and ten
return-to-go updates per arm, eight environments, two PPO passes, 30 cells, six
episodes per cell and 250 bootstrap resamples: 24,000 real transitions and 120
optimizer steps. It must finish within 1,200 seconds. Formal projection is
exactly `1.25 * (30*T_train_nf + 32*T_evaluate_nf + 40*T_analyze_nf)` and must
not exceed 28,800 seconds.

## Gates and first match

The primary paired estimand is `CONST10_FOLD6 - NATIVE6_CS` on final random
deterministic utility, positive in favor of the redundant constant route, with
margin `0.05`. All absolute access, confident-failure, learned-gain,
component, initialization, optimizer, source, pairing, trace and operational
predicates are exactly those in Sections 5--8 of the raw contract.

Apply the frozen first-match order without diagnostic rescue:

1. `INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_TRAINING_G39`
2. `SOURCE_OR_COMMON_ACCESS_FAILURE_G39`
3. `NATIVE_SIX_COORDINATE_TRAINING_SUFFICIENT_G39`
4. `CONSTANT_OVERPARAMETERIZED_TRAINING_ADVANTAGE_G39`
5. `MIXED_UNDERPOWERED_NATIVE_SIX_TRAINING_G39`

A native-six branch supports deleting the constant columns, their moments and
fold only inside G39-P0. A CONST branch supports only a finite-budget
optimization/access advantage for redundant constant parameterization under
the frozen Adam/source/budget; it does not support history necessity.

## Authority sequence

PM must technically accept one exact implementation and commit-bound
code-science index, push them, and route exactly one read-only
`CONTINUOUS_ROSTER_NATIVE_SIX_COORDINATE_TRAINING_G39_CODE_SCIENCE_ALIGNMENT_AUDIT`.
Only an External-Pro `ALIGNED` result permits the same-source bounded
nonformal preflight. Formal execution additionally requires its three artifact
digests and a dedicated G39 token bound to the aligned source commit and frozen
configuration.
