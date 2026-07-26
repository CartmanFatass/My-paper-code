# Continuous Roster Six-Coordinate CS G38

```text
document_kind=pm_code_realization
algorithm_id=CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38
source_id=CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_P0
external_pro_disposition=IDENTIFIABLE_FRESH_FOLDED_SIX_COORDINATE_CS_G38_DESIGN
scientific_authority=external_pro
implementation_authority=project_manager
implementation_status=pm_accepted_after_15_G38_and_50_combined_G34_G35_G38_tests
formal_compute_status=not_eligible_before_external_pro_alignment_and_same_source_preflight
training=fresh_paired_FULL10_CS_vs_FOLD6_CS
```

## Frozen contract

The scientific contract is the exact External-Pro response in
`docs/external-review/rounds/20260726_continuous_roster_six_coordinate_cs_g38_design_assertion_audit/21_PRO_OPEN_RAW.md`.
This record is only the PM implementation pointer; the raw response controls if
any shorthand below is incomplete.

G38 compares two freshly trained, no-carry actors with one common serialized
ten-coordinate graph and byte-identical initialization. `FULL10_CS` receives
the registered ten actor coordinates. `FOLD6_CS` may read only source
coordinates `0:6`, writes `(1/2,1/2,1/2,24/47)` directly into active rows
`6:10`, and leaves inactive rows zero. It may never inspect the corresponding
real source values during collection, replay, gradient audit, PPO, zero/final
evaluation or fold verification.

The common actor has exactly two raw-observation affine entries:

- `member_input: Linear(10,32)` before the remaining member encoder;
- `current_readout: Linear(10,2)` added to the pre-tanh action mean.

No other actor, critic, normalization, gate, residual, context, routing,
prefix, baseline or credit path may consume the raw ten-coordinate observation.
The critic retains the unchanged true-current-state input, and both arms retain
the G31 realized-future-tail credit, source, reward, lifecycle, action
distribution, active-set aggregation, routing, prefix and zero learned carry.

## Exact folding boundary

Both ten-coordinate matrices remain fully trainable in both arms. The forced
first paired batch must show finite live gradients for all inherited trainable
groups and for every removable column of both raw-input affines under at least
one registered fast or return-to-go objective, with maximum absolute gradient
strictly greater than `1e-12`.

After training the final and zero FOLD6 checkpoints, split each permitted
affine into retained and constant columns and apply exactly:

```text
member_input.weight = member_input.weight[:, 0:6]
member_input.bias = member_input.bias + member_input.weight[:, 6:10] @ c
current_readout.weight = current_readout.weight[:, 0:6]
current_readout.bias = current_readout.bias + current_readout.weight[:, 6:10] @ c
c = [1/2, 1/2, 1/2, 24/47]
```

The implementation must use the pre-fold weights when computing each bias
update, remove exactly 136 actor weights, perform no optimizer step after the
fold, and copy every other tensor unchanged. The deployed folded actor consumes
only six coordinates and retains no donor, proxy, filler or source-history
reader.

For every conclusion-bearing FOLD6 zero/final cell, the pre-fold constant-input
model and folded six-input model run in lockstep on one environment trajectory.
The exact bitwise and tolerance gates in the raw contract apply to log standard
deviation, critic/value, pre-tanh means, actions, prefix sums, token likelihood,
inactive zeros, rewards, summaries, roster sizes, membership edits and lifecycle
validity. A fold failure is operational invalidity and cannot be approximated.

## Frozen exposure and evidence

```text
H=48
K_search=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
per_episode_complexity=O(H)
formal_replicates=3
training_capacity=8
fast_updates_per_arm_per_replicate=100
return_to_go_updates_per_arm_per_replicate=100
environments_per_update=8
ppo_passes=2
learning_rate=1e-3
optimizer=Adam(beta1=0.9,beta2=0.999,eps=1e-8,weight_decay=0)
checkpoint_selection=final_only
evaluation_capacities=6|8|12
evaluation_cells_per_arm_capacity=5
evaluation_episodes_per_cell=128
formal_total_cells=90
formal_training_transitions=460800
formal_evaluation_transitions=552960
formal_total_real_transitions=1013760
formal_optimizer_steps=3600
bootstrap_resamples=10000
confidence_interval=95_percent_percentile
episode_exclusions=none
```

Each arm/replicate/capacity evaluates exactly `ZERO_RANDOM_DET`,
`FINAL_FIXED_DET`, `FINAL_FIXED_STOCH`, `FINAL_RANDOM_DET` and
`FINAL_RANDOM_STOCH`. Training collects both paired trajectories before either
arm updates. The whole-episode hierarchical bootstrap resamples three paired
replicate blocks and all 128 episode IDs within each selected replicate and
capacity, retains every paired mate, weights capacities equally, and reuses one
plan for all absolute and paired estimands.

The formal seed bases are `10381000` through `10387000` for model, training
ledger, training action, evaluation base ledger, evaluation process,
evaluation action and initial gradient probe respectively. Add the replicate
once. The bootstrap seed is `10388038`. Nonformal adds `900000` to every seed,
including bootstrap.

The bounded nonformal package uses one replicate, ten fast and ten return-to-go
updates per arm, eight environments, two PPO passes, 30 cells, eight episodes
per cell and 250 bootstrap resamples: 26,880 real transitions and 120 optimizer
steps. It must finish within 1,200 seconds. Formal projection is exactly
`1.25 * (30*T_train_nf + 48*T_evaluate_nf + 40*T_analyze_nf)` and must not
exceed 28,800 seconds.

## Gates and first-match result

All absolute access, confident-failure, gain, component noninferiority,
fold-equivalence, source, pairing, trace and operational predicates are exactly
those in Sections 4--7 of the raw contract. The primary paired estimand is
`FULL10_CS - FOLD6_CS` on final random deterministic utility, positive in favor
of access to the four varying fields, with margin `0.05`.

Apply the frozen first-match order without diagnostic rescue:

1. `INVALID_CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38`
2. `SOURCE_OR_COMMON_ACCESS_FAILURE_G38`
3. `SIX_COORDINATE_ARCHITECTURAL_REDUCTION_SUFFICIENT_G38`
4. `FULL_INFORMATION_FINITE_BUDGET_ADVANTAGE_G38`
5. `MIXED_UNDERPOWERED_SIX_COORDINATE_G38`

A positive reduction branch supports only the exact freshly trained folded
six-coordinate deployment actor in G38-P0. A full-information branch supports
only a finite-budget capability or material utility advantage for the varying
four-field bundle. Neither establishes task-level history necessity, native
six-input training equivalence, individual-field necessity, critic-time
redundancy, recurrence necessity or transport outside the registered source.

## Authority sequence

PM must technically accept one exact implementation plus a commit-bound
`CODE_SCIENCE_INDEX.md`, push it, and route exactly one read-only
`CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_CODE_SCIENCE_ALIGNMENT_AUDIT`.
Only an External-Pro `ALIGNED` result permits one exact same-source-commit
bounded nonformal preflight. Formal execution then additionally requires the
preflight and the token
`CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_FORMAL_AUTHORIZATION_V1`.
