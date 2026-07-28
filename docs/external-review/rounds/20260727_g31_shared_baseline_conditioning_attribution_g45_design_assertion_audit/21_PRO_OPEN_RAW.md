1. REGISTERED_DESIGN_CONFORMANCE
REGISTERED_DESIGN_CONFORMANCE=
CONFORMS_AFTER_EXACT_ACTUAL_DIRECTION_VS_SCALAR_SHADOW_SEPARATION

source_id=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHARED_BASELINE_CONDITIONING_ATTRIBUTION_G45_P0

design_audit_compute=0
H=48
K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false

The prerequisite scientific boundary is closed:

G44_formal_branch=
INDEPENDENT_CHANNEL_SCALE_ADVANTAGE_G44

accepted_post_anchor_route=
COMMON_NATIVE6_FAST_ANCHOR
→ NATIVE6_G31_EQUAL_MEAN_INDEPENDENT_SCALE_NO_SLOW

remaining_conclusion_bearing_iterations=3

G44 validly established that independent relative scaling of the immediate and realized-successor credit channels is load-bearing against the globally credit-norm-matched pooled-scale null. The retained route still contains realized-successor targeting, immediate/successor decomposition, the shared true-current-state two-output baseline, separate centering, independent per-channel scaling, and the literal equal-channel gradient mean. The active state records G45 as the scheduled boundary with three conclusion-bearing iterations remaining.

Required interpretation of NO_READ

The draft is scientifically admissible only under this exact distinction:

NO_READ means:
    no baseline output enters the actual actor-credit residual
    no baseline output coordinates enter the actual actor-credit direction

NO_READ does not mean:
    no baseline computation anywhere

The no-read arm is explicitly allowed to retain:

the baseline module’s ordinary target-fitting losses and Adam exposure; and

one local, detached scalar norm obtained from a baseline-read counterfactual on that arm’s own pre-update state and trajectory.

Thus, the no-read arm may use baseline outputs to establish a nuisance-control magnitude, but not to construct its actual residual rows or gradient direction. This narrowing is already implicit in the submitted claim ceiling, which retains the baseline module and local counterfactual scalar norm.

If “zero baseline-output reads” were interpreted as zero influence on both direction and scalar magnitude, the proposed scale matching would contradict that interpretation. Under the direction-versus-scalar separation above, the comparison has one result-changing treatment and is identifiable.

Additional structural precondition

The shared two-output baseline module must be parameter- and activation-disjoint from the native-six actor and log_std:

actor_parameter ∩ baseline_parameter = ∅
actor_forward_activation ∩ baseline_hidden_activation = ∅

“Shared” means shared by the immediate and successor baseline outputs—not a trainable trunk shared with the actor. Baseline losses may be stepped by the same accepted actor/head optimizer, but no baseline-loss gradient may enter an actor parameter. Otherwise the no-read arm would retain a second actor-conditioning route and the comparison would be invalid.

2. DESIGN_SCIENTIFIC_DISPOSITION
DESIGN_SCIENTIFIC_DISPOSITION=
IDENTIFIABLE_LOCAL_COUNTERFACTUAL_NORM_MATCHED_SHARED_BASELINE_CONDITIONING_G45_DESIGN
Exact arms
reference_arm=
NATIVE6_G31_INDEPENDENT_SCALE_BASELINE_READ

null_arm=
NATIVE6_G31_INDEPENDENT_SCALE_BASELINE_SHADOW_NO_READ

Both arms retain the complete accepted G44 post-anchor structure:

accepted G40 common fast anchor
accepted G41 no-slow projection
native-six no-carry actor
log_std
shared two-output true-current-state baseline module
immediate and realized-successor target construction
separate per-channel centering
independent per-channel RMS scaling
literal equal-channel gradient mean
common entropy rule
accepted PPO and Adam exposure
G32/G34 source family
final-only checkpoints

The only intended treatment is whether the actor-credit residual direction reads the baseline outputs. This is exactly the component left open after G44.

Exact pre-update data

For one complete branch update, let the frozen ordered primitive-step row set be:

num_envs=8
H=48
n=384
normalization_unit=one team-level row per primitive step

Both arms use the same row inventory before active-factor broadcast. Rows may not be duplicated or weighted by active-agent count or action-token count.

For channel k∈{I,S}, define the accepted targets:

y
t
I
	​

=r
t
	​

,y
t
S
	​

=G
t+1
	​

,

where G
t+1
	​

 uses the exact accepted G44/G31 realized-successor construction, terminal handling, and finite-precision order.

Before either PPO pass or optimizer step, each arm evaluates its own shared baseline module on the stored accepted true-current-state input:

b
t
I
	​

=b
I
	​

(ξ
t
	​

),b
t
S
	​

=b
S
	​

(ξ
t
	​

).

These baseline outputs are detached and frozen for actor-credit construction across both PPO passes. Baseline target-fitting losses continue under the exact inherited rule, but an update to the baseline parameters after PPO pass one must not retroactively change the already frozen actor-credit residual rows for pass two.

Frozen residual laws
Reference arm
x
t
I,R
	​

=y
t
I
	​

−stopgrad(b
t
I
	​

),
x
t
S,R
	​

=y
t
S
	​

−stopgrad(b
t
S
	​

).
No-read arm
x
t
I,N
	​

=y
t
I
	​

,
x
t
S,N
	​

=y
t
S
	​

.

For each arm a∈{R,N} and each channel:

c
t
k,a
	​

=x
t
k,a
	​

−
n
1
	​

j
∑
	​

x
j
k,a
	​

,
s
k
a
	​

=
n
1
	​

t
∑
	​

(c
t
k,a
	​

)
2
	​

,
z
t
k,a
	​

={
0,
c
t
k,a
	​

/s
k
a
	​

,
	​

s
k
a
	​

=0,
s
k
a
	​

>0.
	​


The exact accepted G44 dtype, reduction order, RMS convention, zero rule, row ordering, and no-epsilon semantics are inherited unchanged.

What baseline subtraction actually changes

Separate centering gives the useful identity:

c
t
k,R
	​

=(y
t
k
	​

−
y
	​

k
)−(b
t
k
	​

−
b
k
),

whereas:

c
t
k,N
	​

=y
t
k
	​

−
y
	​

k
.

Therefore a constant baseline offset cancels completely. G45 tests only the state-varying, centered baseline prediction:

b
t
k
	​

=b
t
k
	​

−
b
k
.

This prevents a calibration intercept from being mislabeled as useful centralized conditioning.

Credit-gradient construction

For each arm, use the exact accepted likelihood-surrogate, clipping, action-factor denominator, autoregressive ownership, and frozen parameter order to construct:

p
I
a
	​

=∇
θ
	​

L
PPO
	​

(z
I
a
	​

),
p
S
a
	​

=∇
θ
	​

L
PPO
	​

(z
S
a
	​

).

The raw credit-bearing actor gradient is:

v
a
raw
	​

=
2
1
	​

(p
I
a
	​

+p
S
a
	​

).

The exact inherited entropy term remains outside the credit-gradient norm gate and is added once under the accepted G44 ownership and coefficient rule. Baseline parameters are excluded from every actor-credit norm.

Reference arm update

The reference arm uses:

v
R
	​

=v
R
raw
	​

.
No-read arm local scale control

On the no-read arm’s own current pre-update model and trajectory, compute a baseline-read counterfactual using that arm’s own baseline outputs:

v
R,cf
N
	​

.

Only its detached scalar norm may be used:

m
cf
N
	​

=
	​

v
R,cf
N
	​

	​

2
	​

.

The assigned no-read credit gradient is:

v
N
	​

=
⎩
⎨
⎧
	​

0,
m
cf
N
	​

∥v
N
raw
	​

∥
2
	​

v
N
raw
	​

	​

,
	​

m
cf
N
	​

=0,
m
cf
N
	​

>0∧∥v
N
raw
	​

∥
2
	​

>0.
	​


If:

m
cf
N
	​

>0and∥v
N
raw
	​

∥
2
	​

=0,

the package is operationally invalid before either arm takes an optimizer step. No channel fallback, epsilon direction, perturbation, or priority rule is permitted.

This matches effective actor-credit scale without copying baseline-conditioned vector coordinates into the no-read direction.

Baseline shadow training

Both arms retain the same baseline graph and target-fitting objective:

same true-current-state input tensor and field order
same two output heads
same targets and reductions
same parameter order
same optimizer group
same Adam hyperparameters
same number of optimizer steps
same final checkpoint inventory

On the first paired update, before either arm steps:

baseline_parameter_bytes_equal=true
baseline_Adam_states_equal=true
baseline_targets_equal=true
baseline_losses_equal=true
baseline_gradients_equal=true

After policies and trajectories diverge, later baseline losses may differ as a downstream consequence of the treatment.

Optimal-policy and claim interpretation

The two arms have the same actor class, observations, action distribution, reward, environment, and deployment interface. Hence their environment-level optimal policy sets are identical:

Π
R
⋆
	​

=Π
N
⋆
	​

.

Baseline subtraction changes only the finite-sample training estimator. A positive G45 result would therefore support a training-time control-variate or gradient-conditioning advantage, not a larger policy class or execution-time access to centralized state.

3. IDENTIFICATION_FAILURES_AND_COUNTEREXAMPLES
3.1 Total “no-read” overclaim

The no-read arm still uses baseline outputs for:

baseline target fitting
local baseline-read counterfactual scalar norm

It does not support a claim that the baseline module or centralized input is structurally absent.

Closure: distinguish actual residual/direction reads from the permitted scalar shadow.

3.2 Shared actor/baseline parameters

If the baseline loss updates actor parameters through a shared trunk, the no-read arm retains baseline conditioning through parameter updates.

Closure: actor/log-std and baseline parameter sets must be disjoint, and baseline losses must have exact zero gradients with respect to every actor parameter.

3.3 Baseline output used by the actual no-read direction

A hidden use of b
I
	​

 or b
S
	​

 in no-read centering, scaling, normalized advantages, channel weighting, clipping, or assigned vector would invalidate the null.

Required actual-path counters:

baseline_read_into_actual_actor_residual=0
baseline_read_into_actual_actor_credit_direction=0
baseline_read_into_action_or_logprob=0
baseline_read_into_checkpoint_selection=0
baseline_read_into_evaluation_metric=0

Permitted separately:

baseline_read_into_local_counterfactual_scalar_norm=true
baseline_read_into_shadow_target_fitting=true
3.4 Cross-arm scale authority

Scaling the no-read arm using the reference arm’s later-diverging credit norm would make one policy control the other policy’s update.

Closure: actual no-read updates use only their own local baseline-read counterfactual norm. Reference-arm data are used only for treatment-activation evidence.

3.5 Recomputing baseline-conditioned actor residuals between PPO passes

If baseline predictions are recomputed after the first baseline update, the treatment changes between PPO passes and becomes entangled with baseline optimizer order.

Closure: the actor-credit baseline outputs, residual rows, channel means, and channel RMS values are frozen once from the complete pre-update trajectory and reused for both passes. Actor gradients and the scalar norm gate are recomputed per pass because the actor changes.

3.6 Constant or affine baseline vacuity

A constant baseline is removed exactly by channel centering. More generally, a baseline that only produces an affine transformation subsequently cancelled by independent scaling may leave the actor-credit direction unchanged.

Closure: require actual unit-direction separation, not merely nonzero baseline values.

3.7 Treatment activation

On the reference arm’s own pre-update state, define centered baseline outputs:

b
t
I
	​

=b
t
I
	​

−
b
I
,
b
t
S
	​

=b
t
S
	​

−
b
S
.

Define:

q
B
	​

=max(RMS(
b
I
),RMS(
b
S
)).

Construct on that same reference state:

v
R,ref
	​

,v
N,cf
R
	​

.

When both are nonzero, define:

q
dir
	​

=
	​

∥v
R,ref
	​

∥
2
	​

v
R,ref
	​

	​

−
∥v
N,cf
R
	​

∥
2
	​

v
N,cf
R
	​

	​

	​

2
	​

.

A pass counts as treatment-active only when:

q_B > 1e-6
q_direction > 1e-6
reference_credit_norm > 0
reference_no_read_counterfactual_credit_norm > 0

Required scope:

nonformal:
    at least one treatment-active pass

formal:
    at least one treatment-active pass
    in each accepted-anchor replicate 0|1|2

The actual no-read arm supplies no activation evidence:

evidence_source_arm=BASELINE_READ
reference_no_read_counterfactual=true
no_read_arm_evidence_read_count=0
3.8 Baseline variation without gradient effect

A baseline may have large centered RMS but remain orthogonal to the score-function geometry, producing no direction change.

Closure: q
B
	​

 and q
dir
	​

 must both pass. Baseline-output variation alone is not conclusion-bearing evidence.

3.9 Action-dependent or future-dependent baseline

A baseline that reads a current sampled action, current action token, post-action state, reward, future event, or realized return at prediction time is not an action-independent state control variate.

Closure: the baseline prediction path uses only the exact accepted pre-action true-current-state input. Target values may enter the detached baseline loss but not the baseline prediction input or action forward path.

3.10 Global scale confound

Baseline subtraction can change both actor-credit direction and global norm.

Closure: match the no-read arm’s global credit norm to its local read counterfactual. Do not match the total gradient after the entropy term, and do not match post-Adam parameter deltas.

3.11 Baseline-loss or entropy contamination

The following remain outside the treatment:

baseline targets and reductions
baseline gradients and Adam exposure
entropy coefficient and inherited ownership
actor/baseline parameter inventory

No baseline parameter may be included in the actor-credit norm. No entropy vector may be rescaled by the credit-norm gate.

3.12 Finite-budget versus asymptotic interpretation

For an unclipped exact-expectation policy gradient, an action-independent baseline is an unbiased control variate. In this experiment, clipping, finite paired batches, channel centering/scaling, and Adam can make it materially affect finite-budget learning.

A positive result would support:

finite-budget estimator conditioning

not:

execution-time centralized information necessity
asymptotic policy-class necessity
global task-level baseline necessity
3.13 Source and transfer limits

G45 remains bounded to the accepted G44 domain:

H=48
configured capacities=6|8|12
G32 fixed training source
G34-P0 bounded fixed/random evaluation source
registered event-count/order/profile family
accepted common fast anchors
registered Adam and branch budget

It cannot establish arbitrary process, capacity, horizon, recurrence, UAV, lifetime, or intrinsic-reward claims. G44 itself was explicitly bounded to this source and finite-budget optimizer setting.

3.14 Smallest branch witnesses
Outcome	Smallest valid witness
Operational invalidity	Baseline and actor share parameters; baseline enters no-read actual residual/direction; positive counterfactual norm with zero no-read direction; treatment inactive in a required replicate; baseline predictions are recomputed between PPO passes; unequal target-fitting or Adam exposure
Source/reference failure	Source invalid, or the accepted READ reference arm confidently fails an inherited access predicate
No-read sufficiency	Both arms pass access and every READ-minus-NO_READ primary/component UCB is <=0.05
Baseline-conditioning advantage	READ passes access and NO_READ confidently fails, or the pooled primary LCB is >0.05 with every capacity-specific primary LCB >0
Mixed/underpowered	Every remaining operationally valid numerical pattern
4. CDC_PORTFOLIO_LEDGER_EDITS

This is a zero-compute design freeze. It changes no scientific status. Status changes require a conclusion-bearing result, not a design review.

CONJECTURES.md
EDIT=NONE

G44 remains the latest conclusion-bearing update. Shared-baseline conditioning stays unresolved within the retained G31 package. The repository currently records the accepted G44 route and explicitly schedules this G45 boundary.

RESEARCH_DIRECTION_LEDGER.md
STATUS_EDIT=NONE

Retain OPEN_UNTESTED, mechanically narrowed to:

Markdown
| G44 accepted independent-scale branch 中 shared true-current-state baseline
对 actor-credit direction 的局部必要性 | `OPEN_UNTESTED` | 保持 accepted
anchors、G41 no-slow projection、realized-tail、immediate/successor
decomposition、separate centering、independent scaling、literal equal mean、
source、PPO 与 Adam exposure 不变；比较 baseline-conditioned actor residual
与 shadow-trained no-actual-read residual，并以 no-read arm 自身的
baseline-read counterfactual global credit norm 匹配 actor-credit step。 |
G45 design 已冻结；该边界不检验 baseline module、true-state input 或
counterfactual scalar shadow 的结构删除，尚无 conclusion-bearing result。 |

The existing ledger already records G44 as SUPPORTED_RETAINED, the pooled-scale null as failed closed, and G45 as the next action.

IDEA_PORTFOLIO.md
SCIENTIFIC_ROW_EDIT=NONE

After mechanical archival only:

completed_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHARED_BASELINE_CONDITIONING_ATTRIBUTION_G45_DESIGN_ASSERTION_AUDIT

design_disposition=
IDENTIFIABLE_LOCAL_COUNTERFACTUAL_NORM_MATCHED_SHARED_BASELINE_CONDITIONING_G45_DESIGN

valid_result_disposition=CONTINUE

next_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHARED_BASELINE_CONDITIONING_ATTRIBUTION_G45_CODE_SCIENCE_ALIGNMENT_AUDIT

conclusion_bearing_iterations_consumed=34
iterations_remaining=3

G44’s recorded portfolio retains baseline conditioning while preserving target, decomposition, centering, common-anchor, broader transport, recurrence, and non-G33 UAV questions separately.

CURRENT_WORK.md

After mechanical archival only:

last_completed_assignment_id=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHARED_BASELINE_CONDITIONING_ATTRIBUTION_G45_DESIGN_ASSERTION_AUDIT

active_assignment_id=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHARED_BASELINE_CONDITIONING_ATTRIBUTION_G45_CODE_SCIENCE_ALIGNMENT_AUDIT

next_boundary=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHARED_BASELINE_CONDITIONING_ATTRIBUTION_G45_CODE_SCIENCE_ALIGNMENT_AUDIT

g45_design_disposition=
IDENTIFIABLE_LOCAL_COUNTERFACTUAL_NORM_MATCHED_SHARED_BASELINE_CONDITIONING_G45_DESIGN

g45_reference_arm=
NATIVE6_G31_INDEPENDENT_SCALE_BASELINE_READ

g45_null_arm=
NATIVE6_G31_INDEPENDENT_SCALE_BASELINE_SHADOW_NO_READ

g45_primary_treatment=
state_conditioned_baseline_subtraction_into_actor_credit_direction

g45_retained_nuisance_controls=
shadow_baseline_target_fitting|
local_baseline_read_counterfactual_credit_norm

g45_design_compute=0
conclusion_bearing_iterations_consumed=34
iterations_remaining=3

The current active record already identifies G45 as the active assignment with three iterations remaining.

ALGORITHM_PRINCIPLES.md
EDIT=NONE

G45 applies existing mechanism-matched comparator, optimizer-exposure, replacement-before-accumulation, and narrow-result principles. It does not yet establish a new cross-experiment rule.

5. DESIGN_VALID_DISPOSITION
DESIGN_VALID_DISPOSITION=CONTINUE

conclusion_bearing_iteration_cost=0
conclusion_bearing_iterations_consumed=34
remaining_conclusion_bearing_iterations=3

The comparison is identifiable under the exact direction-versus-scalar-shadow boundary above. The balance is not exhausted, and a bounded G45 realization/audit candidate exists. The role contract therefore requires continuation with one scheduled action while retaining the rest of the portfolio.

Direction	State after this design audit	Advancement or reactivation condition
Independent relative channel scaling	Supported and retained	Preserve in G45
Shared baseline subtraction into actor-credit direction	Live; G45 realization/audit scheduled	Exact READ versus shadow-NO_READ comparison
Complete structural removal of baseline module or centralized input	Live, not adjudicated by G45	Requires a later no-shadow/no-module design if G45 first supports direction removal
Separate channel centering	Live, unscheduled	Hold targets, baseline, scaling, and composition fixed
Realized-successor target	Live, unscheduled	Change only target authority under matched downstream processing
Immediate/successor decomposition	Live, unscheduled	Preserve information, baseline capacity, normalization, and update scale
Common fast anchor	Live, unscheduled	Match initial function, interactions, and optimizer exposure
Broader process/horizon/capacity	Live, unscheduled	Change one source axis at a time
Identifiable non-G33 UAV transport	Parked	Requires a feasible, load-bearing, support-valid, source-identifiable source
Recurrence/EHC	Parked	Requires task-relevant sequential information absent from current observations
C-BASE/C-COORD	Live outside this local reduction	Requires a representation-fixed access or coordination separation
Asynchronous skill lifetime/intrinsic reward	OUT_OF_SCOPE_FROZEN	Later explicit scope transition
G33 lineage	Permanently frozen	No reactivation in this chain

Scheduling G45 does not make shared-baseline conditioning the unique scientific direction.

6. CURRENT_SCHEDULED_ACTION_IF_CONTINUE
current_scheduled_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHARED_BASELINE_CONDITIONING_ATTRIBUTION_G45_CODE_SCIENCE_ALIGNMENT_AUDIT

That audit becomes eligible only after Code Project Manager independently realizes and technically accepts one exact pushed implementation of the frozen G45 object.

Its sole scientific question is:

Does the accepted implementation preserve the exact G44 independent-scale route; keep the baseline graph, target fitting, parameters, Adam exposure, entropy, source, and confidence plan matched; remove baseline outputs only from the no-read arm’s actual actor-credit residual and direction; use only a local detached baseline-read counterfactual norm as the permitted scalar shadow; and fail closed on shared parameters, baseline leakage, stale/recomputed residuals, cancellation, liveness, treatment-vacuity, provenance, pairing, evidence, or first-match mismatches?

This disposition authorizes no implementation, Git activity, proof execution, nonformal run, or formal run.

7. EXECUTABLE_DESIGN_BOUNDARY
7.1 Provenance and branch start

Freeze the exact accepted chain:

accepted_G40_common_fast_anchor_replicates=0|1|2
accepted_G41_projection=no_slow
accepted_G44_formal_source_commit=
96e35ddf55de71e56c6bcace4746c408909480dd

accepted_G44_aligned_source_commit=
1a6e046801ab3d83830d4c9f6e9724c8c47659da

accepted_G44_alignment_stage_commit=
b55578a8e57f444895da59efe9268ebe31edf511

For every replicate:

Strict-validate the accepted anchor manifest identity and complete-state digest.

Apply the exact accepted no-slow projection.

Clone retained model state bitwise into READ and NO_READ arms.

Create empty, separately owned actor/head Adam states.

Require zero shared parameter, buffer, gradient, or optimizer storage.

Consume no model RNG during projection.

7.2 Exact graph inventory

Both arms contain exactly:

native-six actor
log_std
shared immediate/successor two-output baseline module
no learned actor carry
no standalone slow critic
no DB composer, DB norm, or DB shadow

Before treatment, require equality of:

semantic state keys
tensor shapes
trainable masks
parameter counts
initial bytes
optimizer parameter-group order
baseline input and output schema

Additional structural invariants:

actor_and_baseline_parameter_storage_disjoint=true
baseline_loss_gradient_into_actor_parameter_count=0
actor_loss_gradient_into_baseline_parameter_count=0

The second zero follows from detached baseline outputs in the actor residual.

7.3 Frozen target and prediction evidence

For each update and arm, serialize and bind:

primitive_row_count=384
primitive_row_mask_digest
episode_id_digest
true_current_state_input_digest
immediate_target_digest
successor_target_digest
immediate_baseline_output_digest
successor_baseline_output_digest

The baseline predictions used by actor credit are produced before either arm’s first PPO step and are frozen across both passes.

Every arm record must carry its own baseline outputs and targets. A reference-only evidence package is insufficient after the arms diverge.

7.4 Actual residual and normalization evidence

For every arm and channel, bind:

residual_law_id
residual_mean
centered_sum_square
RMS_scale
normalized_row_digest
normalization_row_count=384
normalization_mask_digest

Required route identities:

READ:
    residual_law=target_minus_detached_baseline

NO_READ:
    residual_law=target_only

Both routes use separate channel centering and independent scale. No pooled scale, active-count weighting, epsilon, row exclusion, or between-pass normalization recomputation is permitted.

7.5 Exact credit-gradient and scalar-control plans
READ arm
read_credit_gradient =
0.5 * (
    immediate_PPO_gradient(read_normalized_immediate)
    +
    successor_PPO_gradient(read_normalized_successor)
)
NO_READ arm
no_read_raw_credit_gradient =
0.5 * (
    immediate_PPO_gradient(no_read_normalized_immediate)
    +
    successor_PPO_gradient(no_read_normalized_successor)
)

On the NO_READ arm’s local current state, compute:

baseline_read_counterfactual_credit_gradient

solely to obtain:

baseline_read_counterfactual_credit_norm

Then assign the raw no-read direction at that norm.

The norm-match gate is:

	​

∥v
N
	​

∥
2
	​

−m
cf
N
	​

	​

≤10
−8
+10
−6
m
cf
N
	​

.

The exact-zero rules are:

m_cf=0:
    assigned NO_READ credit gradient=exact zero
    baseline and entropy updates continue
    Adam exposure continues

m_cf>0 and ||NO_READ raw credit gradient||=0:
    INVALID before either optimizer step
7.6 Baseline-shadow dependency certificate

The NO_READ arm must record:

actual_residual_baseline_read_count=0
actual_direction_baseline_coordinate_read_count=0

counterfactual_baseline_scalar_shadow=true
counterfactual_shadow_output_type=one_detached_scalar_credit_norm
counterfactual_vector_serialized=false
counterfactual_vector_coordinate_use_outside_norm=0
counterfactual_gradient_assignment_count=0
counterfactual_optimizer_state_count=0
counterfactual_RNG_consumption=0
counterfactual_model_mutation_count=0

baseline_target_fitting_retained=true
baseline_action_or_logprob_read_count=0
baseline_checkpoint_selection_read_count=0
baseline_evaluation_metric_read_count=0

A serialized declaration is insufficient. The later alignment audit must reconstruct dependencies from the actual computation graph and call paths.

7.7 First paired-batch audit

Before either arm’s first optimizer step:

actor_bytes_equal=true
log_std_bytes_equal=true
baseline_bytes_equal=true
actor_head_Adam_states_empty_and_separate=true
stored_trajectories_equal=true
targets_equal=true
baseline_outputs_equal=true
baseline_losses_equal=true
baseline_gradients_equal=true
entropy_rule_equal=true

The only permitted difference is:

READ actual actor residual subtracts baseline
NO_READ actual actor residual does not

The local scalar counterfactual is a nuisance control, not a second direction.

7.8 Learning-signal and treatment-activation gates

Every PPO pass must serialize finite gradient evidence for both arms.

Require:

all immediate and successor channel gradients finite
each arm's combined credit gradient finite
each registered actor group finite in both channel rows
each actor group live in at least one channel on treatment-counting passes

immediate baseline-output loss gradient finite and >1e-12
successor baseline-output loss gradient finite and >1e-12
shared baseline trunk live under the union of the two losses

Reference-arm activation evidence serializes:

centered_immediate_baseline_RMS
centered_successor_baseline_RMS
q_baseline=max(centered RMS values)

reference_READ_credit_norm
reference_NO_READ_counterfactual_credit_norm
reference_credit_dot_product
q_direction

evidence_source_arm=BASELINE_READ
reference_no_read_counterfactual=true
no_read_arm_evidence_read_count=0

A pass is active only when:

q_baseline > 1e-6
q_direction > 1e-6
reference_READ_credit_norm > 0
reference_NO_READ_counterfactual_credit_norm > 0

Package gates:

nonformal:
    at least one active pass

formal:
    at least one active pass in each replicate 0|1|2

A stored passed=true flag cannot substitute for reconstruction from baseline-output and credit-gradient evidence.

7.9 Pairing and seed ownership

Freeze:

branch_ledger_seed_base=10451000
branch_action_seed_base=10452000
branch_gradient_probe_seed_base=10453000

evaluation_base_ledger_seed_base=10454000
evaluation_process_seed_base=10455000
evaluation_action_seed_base=10456000

bootstrap_seed=10457045
nonformal_seed_offset=900000

For formal replicate r, add r once to every nonbootstrap base. For nonformal work, add 900000 to every seed, including the bootstrap seed.

Shared across arms:

anchor identity
episode IDs
source ledgers
membership process
member-owned action-noise tensors
evaluation ledgers
evaluation action noise
bootstrap plan

Arm-owned:

model state after clone
baseline state after clone
actor/head Adam state

Both complete trajectories are materialized and validated before either arm updates.

Freeze branch execution order after paired collection:

BASELINE_READ
then
BASELINE_SHADOW_NO_READ

A proof-sized order-swap guard must take zero diagnostic optimizer steps and establish that execution order cannot alter the mate’s stored trajectory, targets, baseline predictions, RNG, or initial optimizer state.

7.10 Training exposure

Per arm and replicate:

branch_updates=100
environments_per_update=8
PPO_passes=2
checkpoint_selection=final_only
episode_exclusions=none

The exact accepted G44 Adam class, hyperparameters, parameter groups, and order remain unchanged.

Required:

one actor/head Adam step per PPO pass
no optimizer reset between branch updates
no gradient clipping
no new minibatch split
no global actor-plus-baseline norm operation
7.11 Evaluation source and cells

For each arm, replicate, and capacity 6|8|12, evaluate:

FINAL_FIXED_DET
FINAL_FIXED_STOCH
FINAL_RANDOM_DET
FINAL_RANDOM_STOCH

No zero or anchor evaluation cell is added.

Formal support per replicate/capacity:

episodes_per_cell=48
unique_random_time_tuples=48
event_orders=16|16|16
capacity_8_profiles=16|16|16

Nonformal uses six episodes per cell, with 2|2|2 order/profile balance where applicable.

Evaluation performs zero optimizer steps. Baseline outputs may not enter action generation, checkpoint selection, reward, utility, or any conclusion-bearing evaluation metric.

7.12 Absolute-access gates

For each arm a:

fixed deterministic utility LCB per capacity >=0.90
fixed stochastic pooled LCB >=0.80
minimum fixed deterministic replicate mean >=0.85

random deterministic utility LCB per capacity >=0.90
random event-window LCB per capacity >=0.85
random process-segment LCB per capacity >=0.85
random-minus-fixed LCB per capacity >=-0.05
random stochastic pooled LCB >=0.80
minimum random deterministic replicate mean >=0.85

All non-strict equalities pass. ACCESS_CONFIDENT_FAIL uses the exact upper-confidence-bound duals inherited from G44. The registered G44 thresholds are part of its formal evidence boundary.

7.13 Estimands and comparison gates

For paired final random-deterministic episodes:

Δ
baseline,C,r,e
	​

=U
C,r,e
READ
	​

−U
C,r,e
NO_READ
	​

.

Primary:

Δ
baseline
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
baseline,C,r,e
	​

]
	​


Positive values favor baseline-conditioned actor credit.

materiality_and_noninferiority_margin=0.05

Registered component contrasts:

fixed deterministic utility per capacity
random deterministic utility per capacity
fixed stochastic utility pooled across capacities
random stochastic utility pooled across capacities
random event-window utility per capacity
random process-segment utility per capacity
random-minus-fixed transport per capacity

NO_READ_NONINFERIOR requires every primary and component UCB to be <=0.05.

MATERIAL_BASELINE_CONDITIONING_ADVANTAGE requires:

LCB
95
	​

(Δ
baseline
	​

)>0.05

and:

LCB
95
	​

(Δ
baseline,C
	​

)>0∀C∈{6,8,12}.
7.14 Confidence construction

Freeze:

bootstrap_seed=10457045
nonformal_resamples=250
formal_resamples=10000
confidence_interval=95_percentile
episode_exclusions=none

Use one hierarchical paired plan for every absolute and comparative quantity:

Resample accepted-anchor replicate blocks.

Within each selected replicate and capacity, resample complete episode IDs.

Retain both arms and all fixed/random and deterministic/stochastic mates.

Never independently resample members, primitive steps, event windows, credit channels, or action factors.

Weight capacities 6, 8, and 12 equally.

7.15 Frozen first-match table
Priority	Terminal branch	Exact predicate
1	INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHARED_BASELINE_CONDITIONING_ATTRIBUTION_G45	Any provenance, graph-disjointness, target, residual, baseline-shadow, scale-match, liveness, activation, zero/cancellation, optimizer, RNG, source-trace, checkpoint, confidence, inventory, or authority invariant fails
2	SOURCE_OR_REFERENCE_ACCESS_FAILURE_G45	Operationally valid and source invalid, or the accepted READ reference confidently fails an inherited access predicate
3	SHADOW_BASELINE_NO_ACTOR_READ_SUFFICIENT_G45	Both arms pass access and every READ-minus-NO_READ primary/component UCB is <=0.05
4	SHARED_TRUE_STATE_BASELINE_CONDITIONING_ADVANTAGE_G45	READ passes access and either NO_READ confidently fails or MATERIAL_BASELINE_CONDITIONING_ADVANTAGE=true
5	MIXED_UNDERPOWERED_SHARED_BASELINE_CONDITIONING_G45	Every remaining operationally valid numerical pattern

Equality rules:

absolute-floor equality                       = pass
random-minus-fixed LCB = -0.05                = pass
UCB(READ-NO_READ) = 0.05                      = noninferior pass
LCB(READ-NO_READ) > 0.05                      = strict advantage
capacity-specific LCB > 0                     = strict
centered baseline RMS = 1e-6                  = inactive
unit-direction distance = 1e-6                = inactive
credit-norm error exactly at tolerance        = pass

No baseline calibration score, prediction MSE, gradient variance diagnostic, training curve, event stratum, or wall-clock result may rescue or relabel an earlier branch.

7.16 Smallest evidence inventory

The G44 inventory remains the smallest defensible conclusion-bearing inventory because:

three accepted anchors are the independent trained-state unit;

48 episodes preserve exact 16/16/16 process-order and capacity-8 profile balance;

100 post-anchor updates preserve the accepted finite-budget boundary;

the allow-listed evidence contains no precision analysis supporting fewer replicates or episodes.

Nonformal
replicates=1
branch_updates_per_arm=10
num_envs=8
PPO_passes=2

evaluation_cells=24
episodes_per_cell=6
bootstrap_resamples=250

training_transitions=7680
evaluation_transitions=6912
total_real_transitions=14592
optimizer_steps=40
Formal
replicates=3
branch_updates_per_arm=100
num_envs=8
PPO_passes=2

evaluation_cells=72
episodes_per_cell=48
bootstrap_resamples=10000

training_transitions=230400
evaluation_transitions=165888
total_real_transitions=396288
optimizer_steps=1200
7.17 Complexity and wall-clock boundary
H=48
K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
per_episode_complexity=O(H)

nonformal_wall_clock<=1200_seconds
formal_wall_clock<=28800_seconds

Freeze the conservative projection:

T
projected,formal
	​

=1.25(30T
train,nf
	​

+24T
evaluate,nf
	​

+40T
analyze,nf
	​

).

A cap violation is:

NON_EXECUTABLE_EVIDENCE_DESIGN

with zero scientific iteration cost—not a G45 result. The project policy requires the 20-minute nonformal and eight-hour formal ceilings and forbids nested or horizon-growing search.

7.18 Scientific versus implementation-only choices

Scientifically frozen:

provenance
graph and parameter disjointness
target and baseline prediction timing
READ and NO_READ residual laws
separate centering and independent scaling
local counterfactual credit-norm control
permitted scalar shadow and prohibited vector reads
baseline target-fitting identity
entropy isolation
zero/cancellation rules
liveness and activation gates
pairing and seed ownership
training and evaluation inventory
access and comparison gates
confidence unit
first-match order
evidence ceilings

Implementation-only:

file and class names
tensor storage
vectorization and batching
serialization layout
telemetry organization
CPU process count within the inherited deterministic boundary
native-kernel organization
proof-test file placement
post-collection execution order subject to the order-swap invariant
8. CHINESE_SUMMARY
G45设计裁决=
IDENTIFIABLE_LOCAL_COUNTERFACTUAL_NORM_MATCHED_SHARED_BASELINE_CONDITIONING_G45_DESIGN

DESIGN_VALID_DISPOSITION=CONTINUE

本轮结论性迭代成本=0
已消耗结论性轮次=34
剩余结论性轮次=3
G45 真正比较什么

当前 G44 接受路线是：

COMMON_NATIVE6_FAST_ANCHOR
→ NATIVE6_G31_EQUAL_MEAN_INDEPENDENT_SCALE_NO_SLOW

继续保留：

realized-successor target
immediate/successor decomposition
shared true-state two-output baseline
separate centering
independent channel scaling
literal equal-channel mean

G45 比较：

READ:
    actor credit residual 减去 baseline prediction

NO_READ:
    actor credit residual 不读取 baseline prediction
    baseline module 仍按完全相同规则训练
“NO_READ” 的精确含义

NO_READ 不是完全删除 baseline。

它仍允许：

baseline target-fitting loss
baseline Adam exposure
本地 baseline-read counterfactual 的一个 detached scalar norm

但禁止 baseline output 进入：

实际 actor residual
实际 actor credit direction
action / logprob
checkpoint selection
evaluation metric

所以 G45 只归因 baseline 对 actor-credit 方向的状态条件化作用；还不能直接删除 baseline module 或 true-state input。

为什么需要 credit-norm 匹配

减去 baseline 会同时改变：

credit gradient direction
credit gradient global magnitude

若不控制 magnitude，结果可能只是不同 actor learning-rate schedule。

因此 NO_READ arm 使用自己当前状态下的 READ counterfactual，只读取其 scalar norm，再把自身无 baseline 的 raw direction 匹配到这个 norm。

counterfactual vector 坐标不能进入实际更新。

baseline 真正进入的是 centered variation

因为每条 channel 都随后中心化：

c
READ
=c
target
−(b−
b
ˉ
),

常数 baseline offset 会完全消失。

Treatment activation 必须同时满足：

至少一个 centered baseline output RMS > 1e-6
READ 与 NO_READ counterfactual unit direction 距离 > 1e-6
两条 credit direction norm 均为正

每个 formal replicate 0|1|2 至少出现一次，否则 comparison 因 treatment vacuous 而进入 INVALID。

结果解释上限

若 NO_READ 通过，只能说明：

baseline subtraction 可从 actor-credit direction 中删除
但 baseline module、target fitting 和 scalar norm shadow 仍保留

若 READ 获胜，只能说明：

shared true-current-state baseline conditioning
在 G45-P0、当前 source、Adam 与有限预算下具有 access 或 material advantage

不能推出：

deployment actor 需要 centralized state
所有任务都需要 baseline
realized-tail 或 decomposition 必要
recurrence 必要或不必要
UAV transport 已成立
正式分支
1 INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHARED_BASELINE_CONDITIONING_ATTRIBUTION_G45
2 SOURCE_OR_REFERENCE_ACCESS_FAILURE_G45
3 SHADOW_BASELINE_NO_ACTOR_READ_SUFFICIENT_G45
4 SHARED_TRUE_STATE_BASELINE_CONDITIONING_ADVANTAGE_G45
5 MIXED_UNDERPOWERED_SHARED_BASELINE_CONDITIONING_G45

主估计量：

Δ
baseline
	​

=U
READ
	​

−U
NO_READ
	​

.

margin：

0.05
证据上限
nonformal:
    14,592 real transitions
    40 optimizer steps
    24 cells
    250 bootstrap

formal:
    396,288 real transitions
    1,200 optimizer steps
    72 cells
    48 episodes/cell
    10,000 bootstrap

H=48
K_search=0
hypothetical transitions=0
CDC 与下一边界

本轮没有运行数据，因此：

CONJECTURES scientific status=不变
RESEARCH_DIRECTION_LEDGER status=OPEN_UNTESTED
IDEA_PORTFOLIO scientific rows=不变

下一边界仅为：

CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHARED_BASELINE_CONDITIONING_ATTRIBUTION_G45_CODE_SCIENCE_ALIGNMENT_AUDIT

separate centering、realized-successor target、decomposition、common anchor、broader process/horizon/capacity、可识别非 G33 UAV 与 recurrence/EHC 等方向继续保持 live 或 parked。G33 永久冻结。本裁决不授权实现、Git、nonformal 或 formal compute。