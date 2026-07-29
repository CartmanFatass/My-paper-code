DESIGN_ASSERTION_CONTRACT_CLARIFICATION

result_contract_status=IDENTIFIED_AND_FROZEN
algorithm_id=CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_FAST_ANCHOR_ATTRIBUTION_G50
source_id=CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_FAST_ANCHOR_ATTRIBUTION_G50_P0
schema_version=2

reference_arm=FAST_ANCHOR_THEN_SINGLE_IMMEDIATE
null_arm=SINGLE_IMMEDIATE_FROM_INITIALIZATION

phase_A_reference_contract=G40_COMMON_NATIVE6_FAST_ANCHOR_V1
phase_A_reference_source_commit=97a8b237e0cec6c2713dd2a710d324040fa3dfc2
phase_A_reference_interpretation=B_COMPLETE_HISTORICAL_FAST_ANCHOR_PACKAGE

phase_B_contract=G49_SINGLE_IMMEDIATE
phase_B_formal_source_commit=8ecb01fd3ac0debf1b792e4e51293e07974d633b
phase_B_aligned_implementation_commit=9edddc845d88191bbfbd6c2ec779551edbbcb78a
phase_B_alignment_stage_commit=b56288597c6c91f784fb5f0fcc36ec5ef92de452
phase_B_formal_branch=DUPLICATED_IMMEDIATE_SINGLE_CHANNEL_EXACTLY_COLLAPSIBLE_G49

The result-bearing contract is recoverable without adding a metric or changing an estimand:

G40 supplies the exact phase-A graph, baseline-conditioned actor objective, module inventory, one-Adam-step-per-PPO-pass exposure and historical source authority.

G49 supplies the exact baseline-free, single-normalized-immediate phase-B objective and final-only reduced checkpoint semantics.

G48 supplies the fixed/random capacity-6/8/12 evaluation cells, whole-episode paired confidence construction, absolute-access gates, component contrasts and five-branch statistical selector.

The only G50 treatment is phase-A actor credit:

reference:
    normalized [r_t - stopgrad(b_I^old(xi_t))]
    plus the matched G40 immediate-baseline fitting package

null:
    G49 centered/population-RMS-normalized r_t
    plus the same immediate-baseline module, target, fitting loss and Adam exposure
    as a shadow-only matched control

Both arms delete all phase-A-only modules and all phase-A optimizer state at the common boundary, then train with the identical G49 single-immediate objective and fresh empty actor Adam states in phase B. The historical G40 runner confirms that the common anchor uses one Adam over actor/log_std plus the shared two-output baseline, with one optimizer step per PPO pass; the anchor Adam is discarded after phase A.

Frozen computational scope:

H=48
K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false

nonformal_phase_A_updates_per_arm=10
nonformal_phase_B_updates_per_arm=10
nonformal_total_real_transitions=22272
nonformal_total_optimizer_steps=80

formal_replicates=3
formal_phase_A_updates_per_arm=100
formal_phase_B_updates_per_arm=100
formal_total_real_transitions=626688
formal_total_optimizer_steps=2400

nonformal_wall_clock_cap_seconds=1200
formal_wall_clock_cap_seconds=28800

The optimizer totals decompose as:

nonformal:
    phase_A=40
    phase_B=40
    total=80

formal:
    phase_A=1200
    phase_B=1200
    total=2400

No evaluation optimizer step is permitted.

EVALUATION_CELLS_AND_ESTIMANDS

formal_replicate_order=0|1|2
arm_order=FAST_ANCHOR_THEN_SINGLE_IMMEDIATE|SINGLE_IMMEDIATE_FROM_INITIALIZATION
capacity_order=6|8|12

cell_order=
FINAL_FIXED_DETERMINISTIC|
FINAL_FIXED_STOCHASTIC|
FINAL_RANDOM_DETERMINISTIC|
FINAL_RANDOM_STOCHASTIC

cells_per_arm_capacity=4
formal_evaluation_cells=72
nonformal_evaluation_cells=24

formal_episodes_per_cell=48
nonformal_episodes_per_cell=6
checkpoint_selection=final_only
evaluation_optimizer_steps=0

This is the exact four-cell G48 statistical evaluation inventory, applied to the two G50 final phase-B checkpoints. Formal random-process cells contain:

LRJT=16 episodes
LJRT=16 episodes
JLRT=16 episodes

Nonformal random cells contain 2|2|2. The registered random process is the bounded G34-P0 one-each-of-L/R/J/T family; fixed cells use its registered fixed-process mate.

For every replicate, capacity, cell and episode:

both arms use the same episode ID;

fixed/random process mates use the same registered source identity;

deterministic/stochastic mates retain their registered pairing;

source ledgers, lifecycle/event schedules, reward law and member-owned action-noise tensors are paired;

evaluation noise is paired;

neither arm updates during evaluation.

The paired bootstrap must keep all these mates together.

Primary estimand

For each final random-deterministic paired episode:

Δ
anchor,C,r,e
	​

=U
C,r,e
FAST→SINGLE
	​

−U
C,r,e
SINGLE→SINGLE
	​

.

The pooled primary is:

Δ
anchor
	​

=
3
1
	​

C∈{6,8,12}
∑
	​

E
r,e
	​

[Δ
anchor,C,r,e
	​

].
positive_direction=favors_FAST_ANCHOR_THEN_SINGLE_IMMEDIATE
materiality_and_noninferiority_margin=0.05
capacity_weights=1/3|1/3|1/3
Registered comparative components

Each comparative quantity is reference minus null:

fixed_deterministic_utility_capacity_6
fixed_deterministic_utility_capacity_8
fixed_deterministic_utility_capacity_12

random_deterministic_utility_capacity_6
random_deterministic_utility_capacity_8
random_deterministic_utility_capacity_12

fixed_stochastic_utility_equal_capacity_pooled
random_stochastic_utility_equal_capacity_pooled

random_event_window_capacity_6
random_event_window_capacity_8
random_event_window_capacity_12

random_process_segment_capacity_6
random_process_segment_capacity_8
random_process_segment_capacity_12

random_minus_fixed_transport_capacity_6
random_minus_fixed_transport_capacity_8
random_minus_fixed_transport_capacity_12

The transport contrast is the difference-in-differences:

Δ
transport,C
	​

=(U
REF,C
random,det
	​

−U
REF,C
fixed,det
	​

)−(U
NULL,C
random,det
	​

−U
NULL,C
fixed,det
	​

).

These are the exact G48 component classes, with only the arm identities and primary treatment replaced by G50’s phase-A comparison.

ACCESS_GATES

Source and treatment validity

Before a conclusion-bearing branch can be selected:

source_valid=true
phase_A_objective_contract_valid=true
phase_A_treatment_activation_valid=true
phase_A_graph_and_optimizer_match_valid=true
phase_A_to_phase_B_projection_valid=true
phase_B_G49_route_valid=true
pairing_valid=true
seed_inventory_valid=true
checkpoint_inventory_valid=true
confidence_plan_valid=true

The source must retain:

training_capacity=8
evaluation_capacities=6|8|12
H=48
G32 fixed training process
G34-P0 fixed/random evaluation family
unchanged external reward
ContinuousRosterToyBatch_CPU_CPP backend
python_fallback=false
Phase-A reference and null read predicates

Reference actor advantage:

A
t
F
	​

=stopgrad(r
t
	​

−b
I
old
	​

(ξ
t
	​

)).

Null actor target:

x
t
I
	​

=r
t
	​

,

with one 384-row population-centering/RMS-normalization pass and exact-zero scale mapped to zeros.

Required null baseline read counts:

baseline_read_into_null_actor_advantage=0
baseline_read_into_null_actor_gradient=0
baseline_read_into_null_action_or_logprob=0
baseline_read_into_null_checkpoint_selection=0
baseline_read_into_null_evaluation=0
baseline_read_into_null_result_selection=0

The baseline module, reward target, immediate-baseline MSE and baseline optimizer exposure remain matched shadow controls in both arms.

Required matched-shadow evidence on the registered paired pre-update boundary:

baseline_target_bytes_equal=true
baseline_output_bytes_equal_before_treatment=true
baseline_MSE_loss_bytes_equal=true
baseline_parameter_gradient_bytes_equal=true
baseline_Adam_configuration_equal=true
baseline_storage_disjoint=true

The historical slow-critic and successor-baseline objectives are zero-step liveness diagnostics only; they may not add an optimizer step or enter either actor objective.

Forced phase-A activation gate

Let g
F
	​

 be the reference actor-plus-log_std PPO gradient using normalized r_t-b_I^old, and g
I
	​

 be the G49 single-immediate counterfactual gradient on the same reference-owned pre-update model and trajectory. Common entropy and baseline-loss gradients are excluded from both diagnostic vectors.

q
A
	​

=
⎩
⎨
⎧
	​

INVALID,
0,
max(∥g
F
	​

∥
2
	​

,∥g
I
	​

∥
2
	​

)
∥g
F
	​

−g
I
	​

∥
2
	​

	​

,
	​

g
F
	​

 or g
I
	​

 contains a nonfinite value,
∥g
F
	​

∥
2
	​

=∥g
I
	​

∥
2
	​

=0,
max(∥g
F
	​

∥
2
	​

,∥g
I
	​

∥
2
	​

)>0.
	​

activation_tolerance=1e-6
treatment_active=q_A>1e-6
q_A_exactly_1e-6=inactive
reference_only_activation_evidence=true
actual_null_activation_evidence_read_count=0

Required activation inventory:

nonformal:
    at least one treatment-active phase-A pass

formal:
    at least one treatment-active phase-A pass in each replicate 0|1|2

Required liveness:

gradient_live_tolerance=1e-12

all registered actor-group gradients finite under both objectives
each registered actor group live in at least one objective
common entropy gradient bytes equal

historical zero-step diagnostics:
    centralized slow critic finite/live
    immediate-baseline path finite/live
    successor-baseline path finite/live
    diagnostic_optimizer_steps=0

The G40 source defines the registered actor groups and the 1e-12 liveness threshold; its first-batch audit also verifies the slow-critic and two baseline paths without taking diagnostic optimizer steps.

Absolute access gates

For each arm a:

Fixed deterministic

For each capacity C∈{6,8,12}:

LCB
95
	​

(U
C
a,fixed,det
	​

)≥0.90.
Fixed stochastic
LCB
95
	​

(U
a,fixed,stoch
)≥0.80,

with equal capacity weighting.

minimum_fixed_deterministic_replicate_mean>=0.85
Random deterministic

For every capacity:

LCB
95
	​

(U
C
a,random,det
	​

)≥0.90,
LCB
95
	​

(E
C
a,random,det
	​

)≥0.85,
LCB
95
	​

(P
C
a,random,det
	​

)≥0.85,
LCB
95
	​

(U
C
a,random,det
	​

−U
C
a,fixed,det
	​

)≥−0.05.
Random stochastic
LCB
95
	​

(U
a,random,stoch
)≥0.80,

with equal capacity weighting.

minimum_random_deterministic_replicate_mean>=0.85

All equalities at these floors pass. These are the exact access predicates frozen for G48 and inherited unchanged by G50.

Confident null-access failure

The null confidently fails if any CI-based access quantity has:

UCB < corresponding_access_floor

using strict inequality.

For either minimum-replicate gate:

maximum_null_replicate_mean < 0.85

A null that fails ordinary access but does not meet this confident-failure dual cannot select the anchor-advantage branch solely from access.

Comparative gates
fresh_single_immediate_noninferior=
    reference_access_pass
    and null_access_pass
    and every registered reference-minus-null
        primary/component UCB <= 0.05

material_common_fast_anchor_advantage=
    reference_access_pass
    and (
        null_access_confident_fail
        or (
            primary_delta_anchor_LCB > 0.05
            and capacity_6_random_deterministic_LCB > 0
            and capacity_8_random_deterministic_LCB > 0
            and capacity_12_random_deterministic_LCB > 0
        )
    )

Equality rules:

access LCB exactly at floor=pass
random-minus-fixed LCB exactly -0.05=pass
reference-minus-null UCB exactly 0.05=noninferior pass

primary LCB exactly 0.05=not material
capacity-specific primary LCB exactly 0=not strict advantage

gradient norm exactly 1e-12=not live
q_A exactly 1e-6=inactive

CONFIDENCE_AND_BOOTSTRAP

confidence_method=paired_hierarchical_percentile_bootstrap

formal_bootstrap_resamples=10000
nonformal_bootstrap_resamples=250

formal_bootstrap_seed=10511050
nonformal_bootstrap_seed=11411050

quantiles=0.025|0.50|0.975
quantile_method=linear
confidence_level=95_percent

capacity_weights=1/3|1/3|1/3
episode_exclusions=none

The complete G50 seed block remains:

initialization_seed_base=10501000

phase_A_ledger_seed_base=10502000
phase_A_action_seed_base=10503000
phase_A_gradient_probe_seed_base=10504000

phase_B_ledger_seed_base=10505000
phase_B_action_seed_base=10506000
phase_B_gradient_probe_seed_base=10507000

evaluation_ledger_seed_base=10508000
evaluation_process_seed_base=10509000
evaluation_action_seed_base=10510000

bootstrap_seed=10511050
nonformal_seed_offset=900000

For formal replicate r, add r exactly once to every non-bootstrap base. For nonformal execution, add 900000 exactly once to every seed, including the bootstrap seed.

For every formal bootstrap draw:

Resample the three initialization-replicate blocks with replacement.

Within each selected replicate and capacity, resample 48 whole episode IDs with replacement.

Retain both arms and every fixed/random and deterministic/stochastic mate for each sampled episode.

Preserve the paired lifecycle/process ledger, reward source and action-noise mate.

Never resample agents, primitive steps, events, phases, channels or action factors independently.

Nonformal uses the same plan with one replicate block and six whole episodes per cell.

One realized bootstrap index plan must be reused across every absolute-access and comparative quantity. The G48 contract freezes this exact paired hierarchical construction and the 2.5/50/97.5 linear quantiles.

Confidence quantities participating in a gate are exactly:

absolute per arm:
    fixed_deterministic_utility_capacity_6_ci95
    fixed_deterministic_utility_capacity_8_ci95
    fixed_deterministic_utility_capacity_12_ci95
    fixed_stochastic_utility_ci95

    random_deterministic_utility_capacity_6_ci95
    random_deterministic_utility_capacity_8_ci95
    random_deterministic_utility_capacity_12_ci95

    random_event_window_capacity_6_ci95
    random_event_window_capacity_8_ci95
    random_event_window_capacity_12_ci95

    random_process_segment_capacity_6_ci95
    random_process_segment_capacity_8_ci95
    random_process_segment_capacity_12_ci95

    random_minus_fixed_transport_capacity_6_ci95
    random_minus_fixed_transport_capacity_8_ci95
    random_minus_fixed_transport_capacity_12_ci95

    random_stochastic_utility_ci95

comparative:
    reference_minus_null_primary_ci95
    reference_minus_null_capacity_6_ci95
    reference_minus_null_capacity_8_ci95
    reference_minus_null_capacity_12_ci95

    all registered fixed/random deterministic,
    fixed/random stochastic,
    event-window,
    process-segment,
    and transport component CI95 values

Minimum-replicate gates use the actual replicate means, not independently resampled agent- or step-level observations.

FIRST_MATCH_ORDER_AND_TOKENS

The analyzer must use this exact first-match order:

1. INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_FAST_ANCHOR_ATTRIBUTION_G50

2. SOURCE_OR_REFERENCE_ACCESS_FAILURE_G50

3. FRESH_SINGLE_IMMEDIATE_TRAINING_SUFFICIENT_G50

4. COMMON_FAST_ANCHOR_FINITE_BUDGET_ADVANTAGE_G50

5. MIXED_UNDERPOWERED_COMMON_FAST_ANCHOR_ATTRIBUTION_G50
1. INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_FAST_ANCHOR_ATTRIBUTION_G50

Select first if any of the following fails:

provenance:
    G40 phase-A source/objective/package identity
    G49 phase-B source/alignment/branch identity
    G50 source/alignment identity
    schema or algorithm/source ID

initialization:
    actor/log_std/full phase-A package initial byte equality
    parameter names/order/masks
    storage disjointness
    zero projection RNG consumption

phase_A:
    complete interpretation-B graph
    matched immediate-baseline shadow package
    optimizer groups/hyperparameters/order
    one optimizer step per PPO pass
    q_A activation scope
    actor-group liveness
    zero-step historical diagnostic liveness
    null baseline no-read predicates

pairing:
    both trajectories materialized before either update
    exogenous ledger/action-noise ownership
    fixed reference-then-null update order
    reverse-order zero-step invariance

phase_boundary:
    all phase-A Adam state discarded
    phase-A-only modules/buffers deleted
    no baseline/critic state enters phase B
    fresh empty disjoint phase-B Adam
    projection consumes zero RNG and zero optimizer steps

phase_B:
    exact G49 single-immediate target/normalization/loss/entropy route
    no second credit channel
    no baseline or slow critic
    final-only checkpoint selection

inventory:
    updates, environments, PPO passes
    transitions and optimizer steps
    evaluation cells/episodes/profile balance
    seed block

artifacts:
    required manifests and final checkpoints
    exact schemas and digests
    reload validation
    no missing, extra, intermediate or forged checkpoint

confidence:
    exact bootstrap seed, unit, grouping, resample count
    capacity weighting and quantile method
    finite interval values
    every registered absolute/comparative quantity reconstructed

authority:
    formal flag, token, same-source preflight
    independent ALIGNED implementation/stage
    fresh run root and C++ backend

Nonfinite target, gradient, loss, timing, metric or confidence evidence also selects this branch.

2. SOURCE_OR_REFERENCE_ACCESS_FAILURE_G50

Select when the package is operationally valid, but either:

source_valid=false

or the reference arm fails any absolute-access predicate.

Reference failure has precedence over both conclusion-bearing comparison branches.

3. FRESH_SINGLE_IMMEDIATE_TRAINING_SUFFICIENT_G50

Select when:

reference_access_pass=true
null_access_pass=true
fresh_single_immediate_noninferior=true

where noninferiority requires every registered reference-minus-null primary and component UCB to be <=0.05.

This supports only exact finite-budget G50-P0 sufficiency under the forced phase boundary and Adam reset.

4. COMMON_FAST_ANCHOR_FINITE_BUDGET_ADVANTAGE_G50

Select when:

reference_access_pass=true

and either:

null_access_confident_fail=true

or:

primary_delta_anchor_LCB>0.05
and every capacity-specific random-deterministic LCB>0

This supports only a source-local finite-budget curriculum/optimization-path advantage.

5. MIXED_UNDERPOWERED_COMMON_FAST_ANCHOR_ATTRIBUTION_G50

Select for every remaining operationally valid pattern.

No training diagnostic, phase-A loss statistic, target correlation, wall-clock value, individual process stratum or favorable component may rescue or relabel an earlier branch. This selector is the G48 five-branch contract with the treatment-specific G50 tokens and predicates.

EQUALITY_AND_ARTIFACT_RULES

Numeric and byte-equality rules

Exact byte equality is required for:

pre-anchor actor/log_std state
phase-A baseline module initial state
parameter names, order and masks
Adam parameter order, counters, exp_avg and exp_avg_sq where equality is required
RNG states before/after zero-RNG operations
source ledgers and process signatures
member-owned action-noise tensors
seed records
checkpoint identity fields
artifact digests
bootstrap index plan
phase-B fresh-empty Adam records

The two arms are allowed to diverge in actor state after phase-A treatment begins; only paired exogenous authority remains equal thereafter.

Numeric tolerances:

phase_A_q_A_activation:
    strict >1e-6

gradient_liveness:
    strict >1e-12

G40 replay/log-probability/value/baseline/prefix/hidden checks:
    <=1e-6

G40 initial forward pre-tanh comparison:
    <=1e-7

token/joint log-probability comparisons:
    <=1e-6

GAE/return algebra identity:
    <=1e-6

access and comparative thresholds:
    as specified in ACCESS_GATES

The G40 implementation defines GAE_IDENTITY_TOLERANCE=1e-6, FORWARD_TOLERANCE=1e-7, LOG_PROB_TOLERANCE=1e-6 and the 1e-12 gradient-live threshold.

Terminal artifact schema
schema_version=2

train_manifest=train_manifest.json
evaluation_manifest=evaluation_manifest.json
analysis_result=analysis_result.json
checkpoint_directory=checkpoints

Exactly six final checkpoints are required:

checkpoints/replicate_0_fast_anchor_then_single_immediate_final.pt
checkpoints/replicate_0_single_immediate_from_initialization_final.pt

checkpoints/replicate_1_fast_anchor_then_single_immediate_final.pt
checkpoints/replicate_1_single_immediate_from_initialization_final.pt

checkpoints/replicate_2_fast_anchor_then_single_immediate_final.pt
checkpoints/replicate_2_single_immediate_from_initialization_final.pt

No zero checkpoint, phase-A checkpoint, intermediate phase-B checkpoint or selected-best checkpoint belongs to the terminal conclusion-bearing inventory.

Each checkpoint must bind exactly:

schema_version
algorithm_id
source_id
source_commit
formal=true
replicate
arm
kind=final_only

phase_A_objective_contract_id=G40_COMMON_NATIVE6_FAST_ANCHOR_V1
phase_A_source_commit=97a8b237e0cec6c2713dd2a710d324040fa3dfc2
completed_phase_A_updates=100

phase_B_source_commit=8ecb01fd3ac0debf1b792e4e51293e07974d633b
phase_B_formal_branch=DUPLICATED_IMMEDIATE_SINGLE_CHANNEL_EXACTLY_COLLAPSIBLE_G49
completed_phase_B_updates=100

configuration
seed_block
actor_state
log_std
phase_B_actor_Adam_state

phase_A_state_disposal_certificate
phase_B_single_immediate_route_certificate
source/process/lifecycle provenance

A final checkpoint must contain no:

phase_A baseline parameters
phase_A slow-critic parameters
phase_A optimizer state
phase_A auxiliary buffers
phase-A checkpoint-selection state
second immediate channel
realized-successor channel
intermediate checkpoint marker
Manifest and digest binding

train_manifest.json must bind:

status=COMPLETE
formal=true
schema_version=2
algorithm/source/source_commit
exact configuration and seed block
G40/G49 predecessor identities
phase-A activation/liveness evidence by replicate
phase-A optimizer exposure and disposal evidence
phase-B fresh-Adam and route evidence
training transition and optimizer-step inventory
six-checkpoint inventory with SHA-256
backend/runtime identity
stage wall time
preflight artifact digests

evaluation_manifest.json must bind:

status=COMPLETE
formal=true
same source/configuration/seeds
exact 72-cell inventory
48 episodes per cell
process-profile and paired episode/action-noise digests
zero evaluation optimizer steps
all absolute and paired episode-level summaries
training_manifest_sha256
six checkpoint SHA-256 values
stage wall time

analysis_result.json must bind:

status=COMPLETE
formal=true
operational_valid
operational_errors

source_valid
treatment_activation_valid
reference_access_pass
reference_access_confident_fail
null_access_pass
null_access_confident_fail

fresh_single_immediate_noninferior
material_common_fast_anchor_advantage

all absolute CI95 values
all comparative CI95 values
threshold record
first_match_priority
result_branch

training_manifest_digest
evaluation_manifest_digest
stage wall time

The G48 formal evidence uses schema version 2, three terminal manifests, six final checkpoints, explicit manifest/analysis digests and exact branch/metric reconstruction; G50 inherits that result-bearing artifact class.

Analyzer reconstruction

The analyzer must:

Reload and validate the train and evaluation manifests and all six final checkpoints.

Recompute the exact configuration, seed block, threshold record and inventory.

Reconstruct every absolute-access predicate from serialized episode-level evidence.

Reconstruct the paired bootstrap using the serialized bootstrap index plan.

Recompute all comparative CIs and branch booleans.

Apply the five branches in frozen order.

Require the stored branch to equal the recomputed first match.

Reject a favorable stored branch, Boolean or CI that is inconsistent with the underlying paired evidence.

Bind the exact train/evaluation artifact digests into analysis_result.json.

Missing, extra, forged, wrong-route, wrong-seed, wrong-cell, wrong-checkpoint or digest-substituted evidence routes to the invalid branch rather than a conclusion-bearing branch.

FORMAL_ADMISSION_AND_RUNNER_INTERFACE

authorization_token=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_FAST_ANCHOR_ATTRIBUTION_G50_FORMAL_AUTHORIZATION_V1

alignment_audit_id=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_FAST_ANCHOR_ATTRIBUTION_G50_CODE_SCIENCE_ALIGNMENT_AUDIT

nonformal_completion_branch=
NONFORMAL_CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_FAST_ANCHOR_ATTRIBUTION_G50_EXERCISE_COMPLETE
Required immutable predecessor identities
accepted_phase_A_source_commit=
97a8b237e0cec6c2713dd2a710d324040fa3dfc2

accepted_phase_A_algorithm=
CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40

accepted_phase_A_contract=
G40_COMMON_NATIVE6_FAST_ANCHOR_V1

accepted_phase_A_formal_root=
logs/formal_continuous_roster_native_six_credit_reduction_g40_cpu_20260727_97a8b23_r1

accepted_phase_A_checkpoint_identity=
common_native6_fast_anchor|
completed_anchor_updates=100|
optimizer_steps=200

The G40 formal evidence and fixture bind this source, root, checkpoint kind, updates and optimizer-step count. The accepted anchor is objective authority only: G50 must initialize both arms freshly from the G50 initialization seed and must not load the historical anchor checkpoint as either arm’s starting state.

accepted_phase_B_source_commit=
8ecb01fd3ac0debf1b792e4e51293e07974d633b

accepted_phase_B_aligned_implementation_commit=
9edddc845d88191bbfbd6c2ec779551edbbcb78a

accepted_phase_B_alignment_stage_commit=
b56288597c6c91f784fb5f0fcc36ec5ef92de452

accepted_phase_B_branch=
DUPLICATED_IMMEDIATE_SINGLE_CHANNEL_EXACTLY_COLLAPSIBLE_G49
Future G50 source and alignment binding

Before formal admission, the runner must contain exact non-null constants:

ALIGNED_IMPLEMENTATION_COMMIT=<exact future G50 implementation commit>
ALIGNMENT_STAGE_COMMIT=<exact independent G50 alignment stage commit>

Formal train requires:

--source-commit == ALIGNED_IMPLEMENTATION_COMMIT
--alignment-disposition ALIGNED
--aligned-source-commit == ALIGNED_IMPLEMENTATION_COMMIT
--alignment-stage-commit == ALIGNMENT_STAGE_COMMIT

All commit identities must be lowercase 40-character SHA-1 strings.

Backend and process policy
formal=true
environment_backend=ContinuousRosterToyBatch_CPU_CPP_required
environment_python_fallback=false

cpu_budget=2
process_workers=2

OMP_NUM_THREADS=1
MKL_NUM_THREADS=1
OPENBLAS_NUM_THREADS=1
NUMEXPR_NUM_THREADS=1
torch_intraop_threads=1

worker_start_method=spawn
deterministic_merge=preassigned_index_not_completion_order

This matches the G48 statistical formal runtime class.

Run-root contract

The runner accepts an explicit --run-root. It must be absent or empty before train.

Canonical path patterns:

nonformal:
logs/nonformal_continuous_roster_native_six_g31_common_fast_anchor_attribution_g50_cpu_<YYYYMMDD>_<source7>_r1

formal:
logs/formal_continuous_roster_native_six_g31_common_fast_anchor_attribution_g50_cpu_<YYYYMMDD>_<source7>_r1

All train/evaluate/analyze stages for one run use the same root.

Command-level interface

The result-bearing runner is:

scripts/run_continuous_roster_native_six_g31_common_fast_anchor_attribution_g50.py

Required stages:

train
evaluate
analyze
exercise
readiness-smoke
readiness-train
readiness-validate
readiness-reload
readiness-evaluate
readiness-analyze

Formal train interface:

python scripts/run_continuous_roster_native_six_g31_common_fast_anchor_attribution_g50.py \
  train \
  --run-root <fresh_formal_root> \
  --source-commit <exact_G50_source_commit> \
  --formal \
  --authorization-token CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_FAST_ANCHOR_ATTRIBUTION_G50_FORMAL_AUTHORIZATION_V1 \
  --accepted-anchor-root logs/formal_continuous_roster_native_six_credit_reduction_g40_cpu_20260727_97a8b23_r1 \
  --preflight-root <fresh_same_source_nonformal_root> \
  --alignment-disposition ALIGNED \
  --aligned-source-commit <exact_G50_source_commit> \
  --alignment-stage-commit <exact_G50_alignment_stage_commit> \
  --cpu-budget 2 \
  --process-workers 2

Evaluation and analysis:

python ...g50.py evaluate --run-root <same_formal_root>
python ...g50.py analyze  --run-root <same_formal_root>

Nonformal exercise requires:

--run-root
--source-commit
--accepted-anchor-root

and forbids:

--formal
--authorization-token
--preflight-root
--alignment-disposition
--aligned-source-commit
--alignment-stage-commit
Same-source preflight requirements

Before any formal environment interaction, formal train must reload and validate:

<preflight_root>/train_manifest.json
<preflight_root>/evaluation_manifest.json
<preflight_root>/analysis_result.json

Required nonformal inventory:

formal=false
replicates=1
arms=2
phase_A_updates_per_arm=10
phase_B_updates_per_arm=10
environments_per_update=8
PPO_passes=2

evaluation_cells=24
episodes_per_cell=6

total_real_transitions=22272
optimizer_steps=80
bootstrap_resamples=250

The preflight branch is operational only and cannot authorize a scientific conclusion. It must equal the frozen nonformal completion token.

The formal manifests must bind the three preflight artifact SHA-256 digests.

Stage times must be finite and nonnegative. The frozen formal projection is:

T
projection
	​

=1.25(30T
train
	​

+24T
evaluate
	​

+40T
analyze
	​

)≤28800 seconds.

The multipliers are the exact formal/nonformal ratios:

training=460800/15360=30
evaluation=165888/6912=24
bootstrap-analysis=10000/250=40
Fail-closed admission conditions

Formal train fails before collection if any of these is wrong:

authorization token
source commit
alignment disposition
aligned implementation commit
alignment stage commit

historical G40 objective source/root/manifest identity
G49 phase-B source/alignment/branch identity

same-source preflight source or formal flag
preflight manifests, schemas or digests
preflight inventory, branch or operational validity
wall-clock projection

fresh run root
backend identity or Python fallback
cpu/process/thread configuration
configuration, seed block or evidence ceiling

Formal authority permits no evaluation or analysis to bypass an absent or invalid train manifest. This section defines an interface only; it does not authorize a G50 formal execution.

CODE_PM_COMPLETION_CONDITION

The smallest technical completion condition is:

1. One Code-PM-accepted G50 source commit implements the exact two-phase
   interpretation-B training contract and the complete result contract above.

2. A static configuration certificate reconstructs:
   arms, phases, modules, optimizer groups, seeds, cells, episodes,
   transition/optimizer counts, thresholds, bootstrap plan and branch order.

3. Synthetic zero-environment branch witnesses select each of the five
   first-match outcomes and test every equality boundary:
   access-floor equality, transport=-0.05, UCB=0.05,
   primary LCB=0.05, capacity LCB=0, q_A=1e-6.

4. Synthetic paired episode records prove:
   whole-episode paired hierarchical resampling,
   equal capacity weighting, mate retention and one shared bootstrap plan.

5. Artifact tamper guards reject:
   missing/extra manifests, wrong schema, wrong source/seed/cell/episode,
   wrong phase route, intermediate checkpoints, baseline residue in phase B,
   checkpoint or manifest digest substitution, and forged branch labels.

6. Formal-admission guards reject:
   wrong token, wrong source/alignment/stage, non-same-source preflight,
   wrong preflight inventory, invalid timing projection, stale root,
   wrong backend/fallback or process configuration.

7. All required technical tests are proof-sized:
   zero scientific real transitions,
   zero hypothetical transitions,
   zero optimizer steps,
   zero bootstrap resamples beyond synthetic index arithmetic.

The completion package may use synthetic metric dictionaries and synthetic episode IDs; it may not run the scientific G50 train/evaluate/analyze experiment under this clarification.

After Code Project Manager accepts one pushed implementation, External Pro must inspect that exact commit in a read-only code-science alignment audit. No nonformal or formal scientific execution precedes an ALIGNED disposition.

DISPOSITION=RESULT_CONTRACT_IDENTIFIED

NEXT_BOUNDARY

CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_FAST_ANCHOR_ATTRIBUTION_G50_CODE_SCIENCE_ALIGNMENT_AUDIT

The next audit asks only whether the accepted implementation instantiates:

the complete G40 interpretation-B phase-A reference package;

the matched shadow-baseline null and its zero actor-read boundary;

exact phase-A state disposal and phase-B G49 reset;

the frozen G50 evaluation, access, confidence and selector contract;

the exact terminal artifact and formal-admission interface above.

No implementation or compute is authorized by this clarification.

中文简报

G50结果合同=已识别
phase_A解释=B

本轮把 Code PM 缺失的 result-bearing runner 合同全部冻结。

正式比较：

reference:
    Phase A = 完整 G40 common fast-anchor package
    Phase B = G49 single immediate

null:
    Phase A = G49 single immediate
              + 完全匹配但对 actor 零读取的 immediate-baseline shadow package
    Phase B = 同一个 G49 single immediate

评估固定为：

3 replicates
2 arms
capacities 6/8/12
每个 arm/capacity 4 个 final cells：
    fixed deterministic
    fixed stochastic
    random deterministic
    random stochastic

48 episodes/cell
72 cells
final-only checkpoints

主估计量是：

U_FAST_ANCHOR_THEN_SINGLE
-
U_SINGLE_IMMEDIATE_FROM_INITIALIZATION

正值支持 common fast anchor。非劣与 material margin 均为 0.05。

绝对 access 门槛保持：

det utility LCB>=0.90
stochastic pooled LCB>=0.80
event-window LCB>=0.85
process-segment LCB>=0.85
random-fixed LCB>=-0.05
minimum replicate mean>=0.85

五个 first-match token 已精确冻结：

INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_FAST_ANCHOR_ATTRIBUTION_G50
SOURCE_OR_REFERENCE_ACCESS_FAILURE_G50
FRESH_SINGLE_IMMEDIATE_TRAINING_SUFFICIENT_G50
COMMON_FAST_ANCHOR_FINITE_BUDGET_ADVANTAGE_G50
MIXED_UNDERPOWERED_COMMON_FAST_ANCHOR_ATTRIBUTION_G50

置信区间使用 paired hierarchical whole-episode percentile bootstrap：

formal=10000 resamples
nonformal=250
quantiles=0.025/0.50/0.975
capacities 等权
不排除 episode

正式工件为：

train_manifest.json
evaluation_manifest.json
analysis_result.json
六个 replicate×arm final checkpoints
schema_version=2

正式 token 冻结为：

CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_FAST_ANCHOR_ATTRIBUTION_G50_FORMAL_AUTHORIZATION_V1

正式入口还必须满足：

独立 ALIGNED G50 commit/stage
same-source nonformal preflight
G40 objective authority
G49 phase-B authority
C++ backend、无 Python fallback
fresh run root
全部 manifest/checkpoint digest 绑定

本轮没有授权实现、Git、nonformal 或 formal compute。下一边界是 exact pushed G50 implementation 的 code-science alignment audit。

RESULT_CONTRACT_IDENTIFIED
