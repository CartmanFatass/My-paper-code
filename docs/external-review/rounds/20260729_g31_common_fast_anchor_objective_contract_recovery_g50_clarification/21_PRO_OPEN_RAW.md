DESIGN_ASSERTION_CONFORMANCE

design_assertion_result=CONTRACT_IDENTIFIED
historical_interpretation=B
design_compute=0
scientific_iteration_cost=0

accepted_historical_source_commit=
97a8b237e0cec6c2713dd2a710d324040fa3dfc2

historical_algorithm=
CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40

historical_phase=
COMMON_NATIVE6_FAST_ANCHOR

One authoritative historical contract is identifiable.

accepted_common_fast_anchor_objective is not an actor-only gradient extracted onto the later G49 actor graph. It is the complete historical G40 common-anchor training package realized by:

ha_ctse_process/continuous_roster_native_six_credit_reduction_g40.py
    ::G40NativeSixPolicy
    ::G40NativeSixPolicy.actor_credit_parameters
    ::compute_credit_targets
    ::_policy_loss_from_normalized_advantage
    ::_entropy
    ::pre_common_gradient_audit
    ::optimize_common_fast_anchor_update

scripts/run_continuous_roster_native_six_credit_reduction_g40.py
    ::_optimizer
    ::_configuration
    ::_train_replicate

The formal evidence and fixture bind that package to source commit 97a8b237..., 100 common-anchor updates, two PPO passes, and exactly 200 common-anchor optimizer steps for formal replicate 0.

The package includes the native-six actor and log_std plus the shared two-output credit-baseline module in the same phase-A optimizer. The slow critic and successor-baseline target path remain present as zero-step first-batch diagnostics, but neither receives a separate common-anchor optimizer step.

OBJECTIVE_CONTRACT_IDENTITY

phase_A_reference_interpretation=
B_COMPLETE_HISTORICAL_FAST_ANCHOR_TRAINING_PACKAGE

objective_contract_id=
G40_COMMON_NATIVE6_FAST_ANCHOR_V1

source_commit=
97a8b237e0cec6c2713dd2a710d324040fa3dfc2

authoritative_reference_update_symbol=
ha_ctse_process.continuous_roster_native_six_credit_reduction_g40.optimize_common_fast_anchor_update

authoritative_reference_model_symbol=
ha_ctse_process.continuous_roster_native_six_credit_reduction_g40.G40NativeSixPolicy

authoritative_runner_symbol=
scripts.run_continuous_roster_native_six_credit_reduction_g40._train_replicate

The historical identity is B because the common-anchor optimizer is constructed from:

Python
Run
anchor.actor_credit_parameters()

and actor_credit_parameters() is:

full_actor_parameters
+
all credit_baselines parameters

rather than actor/log_std alone.

The baseline is the exact accepted shared module:

Linear(critic_state_dim, hidden_dim)
→ Tanh
→ Linear(hidden_dim, 2)

with immediate and successor output coordinates. Its complete state is carried into the accepted anchor checkpoint.

Interpretation A is rejected because it would omit an actually optimized module, its loss, its Adam moments, and its effect on the accepted common-anchor checkpoint. That would construct a new actor-only objective rather than recover the historical anchor.

PHASE_A_TARGET_AND_ADVANTAGE_EQUATIONS

Reference: complete historical G40 fast-anchor package

For a stored phase-A trajectory, define the immediate baseline recorded before the update as b
I
old
	​

(ξ
t
	​

). The historical reference advantage is:

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

The fixed normalized advantage is:

A
F
=normalize_advantage(A
F
),

where the normalization authority is the exact historical symbol imported and invoked by G40 at source commit 97a8b237.... It is called once per complete trajectory before the two PPO passes and is not recomputed between passes. No G49 normalization is substituted for this reference transform.

For active actor factor i, define:

ρ
t,i
	​

=exp(logπ
θ
	​

(a
t,i
	​

∣x
t
	​

)−logπ
old
	​

(a
t,i
	​

∣x
t
	​

)).

The policy loss is:

L
PPO
F
	​

=−E
t
	​

[
n
t
active
	​

1
	​

i∈A
t
	​

∑
	​

min(ρ
t,i
	​

A
t
F
	​

,clip(ρ
t,i
	​

,1−PPO_CLIP,1+PPO_CLIP)
A
t
F
	​

)].

The active-token denominator, clipping operation and averaging are the exact _policy_loss_from_normalized_advantage path.

The current immediate-baseline fitting loss is:

L
b
I
	​

	​

=MSE(b
I
	​

(ξ
t
	​

),stopgrad(r
t
	​

)).

The entropy statistic is:

H(π
θ
	​

)=E
t
	​

[
n
t
active
	​

1
	​

i∈A
t
	​

∑
	​

H(π
θ,i
	​

)].

The actual historical common-anchor loss is:

L
FAST
	​

=L
PPO
F
	​

+VALUE_COEFFICIENTL
b
I
	​

	​

−ENTROPY_COEFFICIENTH(π
θ
	​

)
	​


using the exact PPO_CLIP, VALUE_COEFFICIENT and ENTROPY_COEFFICIENT symbols imported by the G40 source. The baseline loss and actor loss are backpropagated together through one optimizer.

Reference diagnostic targets with zero optimization

The complete historical first-batch package also constructs:

G
t
	​

=r
t
	​

+0.991
¬terminal
t
	​

	​

G
t+1
	​

,G
H
	​

=0,

and:

S
t
	​

=1
¬terminal
t
	​

	​

G
t+1
	​

.

It checks finite live gradients for:

L
V
	​

=MSE(V(ξ
t
	​

),G
t
	​

),
L
b
I
	​

	​

=MSE(b
I
	​

(ξ
t
	​

),r
t
	​

),
L
b
S
	​

	​

=MSE(b
S
	​

(ξ
t
	​

),S
t
	​

).

These slow-critic and successor-baseline objectives are diagnostic only during common-anchor phase A: they receive zero optimizer steps. The actual common-anchor update contains no slow-critic loss and no successor-baseline loss term.

G50 null under interpretation B

The null’s actor-credit target remains the frozen G49 single-immediate target:

x
t
I
	​

=r
t
	​

,

with the exact G49 one-row normalization:

μ
I
	​

=
384
1
	​

t
∑
	​

r
t
	​

,c
t
	​

=r
t
	​

−μ
I
	​

,
s
I
	​

=
384
1
	​

t
∑
	​

c
t
2
	​

	​

,
z
t
I
	​

={
0,
c
t
	​

/s
I
	​

,
	​

s
I
	​

=0,
s
I
	​

>0.
	​


There is no epsilon, row exclusion, active-count weighting or running statistic. Its actor-credit gradient is g
I
	​

, with the same common entropy contribution added once. The G49 route has exactly one target, one normalization, one loss and one gradient construction.

Because interpretation B is authoritative, the null must additionally retain the same G40 immediate-baseline module, reward target, MSE loss and optimizer exposure as a shadow control. Its baseline output has zero reads into:

null actor advantage
null actor gradient direction
null action or log-probability
checkpoint selection
evaluation
result selection

Thus the sole phase-A treatment is:

reference actor credit:
    normalized (r_t - stopgrad(b_I_old))

null actor credit:
    independently centered/RMS-normalized r_t

The immediate-baseline fitting package is common to both arms rather than part of the treatment.

PHASE_A_MODULE_AND_MASK_INVENTORY

phase_A_model_class=
G40NativeSixPolicy

phase_A_complete_graph_equal_across_arms=true
phase_A_initial_state_bytes_equal=true
phase_A_storage_disjoint=true
Optimizer-owned trainable inventory in both arms

Actor/log_std groups:

policy.member_encoder.*
policy.context_encoder.*

policy.actor_rnn.weight_ih
policy.actor_rnn.weight_hh
policy.actor_rnn.bias_ih
policy.actor_rnn.bias_hh

policy.action_mean.*
current_readout.*
log_std

Shared baseline:

credit_baselines.0.weight
credit_baselines.0.bias
credit_baselines.2.weight
credit_baselines.2.bias

These comprise the exact actor_credit_parameters() sequence and must have identical keys, shapes, trainable masks, initialization bytes and optimizer order in both G50 arms. The registered actor-group decomposition is explicitly member encoder, context encoder, gated-cell input/recurrent weights and biases, action head, current readout and log_std.

Present but not phase-A optimized
slow_critic.*
policy.critic.*
policy.delayed_residual.*

Rules:

slow_critic remains in the complete historical phase-A model state but is excluded from the common-anchor optimizer.

It may be temporarily enabled only for the zero-step first-batch liveness diagnostic and must then have its prior mask restored.

policy.critic and policy.delayed_residual are excluded from the full-actor parameter sequence.

No slow-critic, successor-baseline or other auxiliary optimizer exists in phase A.

Baseline-row treatment

All parameters of the shared two-output baseline are optimizer-owned. The actual phase-A loss fits only the immediate output. There is no dedicated successor-output phase-A loss; successor-output liveness is checked only by the zero-step diagnostic.

The null arm must retain this exact module and immediate-loss exposure as a storage-disjoint shadow. It may not replace it with a private trunk, frozen dummy, zero filler or separately parameterized baseline.

PHASE_A_OPTIMIZER_GROUPS_AND_STEPS

phase_A_optimizer_count_per_arm=1
phase_A_optimizer_class=Adam
phase_A_parameter_groups_per_optimizer=1

phase_A_optimizer_parameters=
full_actor_parameters|
log_std|
all_credit_baselines_parameters

learning_rate=1e-3
beta1=0.9
beta2=0.999
eps=1e-8
weight_decay=0
amsgrad=false

gradient_clipping=false
minibatches=false
optimizer_reset_within_phase_A=false

The historical runner constructs one Adam over anchor.actor_credit_parameters(). It performs one optimizer.step() per PPO pass and no auxiliary optimizer step. The slow critic has no common-anchor optimizer.

Therefore:

phase_A_optimizer_steps_per_arm_per_update=2
phase_A_optimizer_steps_per_arm_per_PPO_pass=1
auxiliary_optimizer_steps_per_PPO_pass=0

The formal accepted G40 anchor had:

anchor_updates=100
PPO_passes=2
common_anchor_optimizer_steps=200

which is independently bound by the archived fixture.

Exact G50 optimizer ceilings implied by B

Nonformal:

2 arms×(10
A
	​

+10
B
	​

) updates×2 passes×1 step/pass=80.

Formal:

3 replicates×2 arms×(100
A
	​

+100
B
	​

) updates×2 passes×1 step/pass=2400.

Thus:

nonformal_optimizer_steps=80
formal_optimizer_steps=2400

Interpretation B does not increase those ceilings because the baseline parameters are updated inside the same Adam step as the actor rather than by an auxiliary optimizer. The G40 runner’s historical inventory likewise counts one anchor step per pass and two separate steps per branch pass only after the anchor has ended.

PHASE_A_PROJECTION_AND_RESET

After the final phase-A update in each G50 arm:

discard_phase_A_Adam_state=true
delete_phase_A_optimizer_object=true
carry_phase_A_Adam_moments_into_phase_B=false
projection_optimizer_steps=0
projection_RNG_consumption=0

The historical G40 runner explicitly discards the nonempty anchor Adam before creating post-anchor branch optimizers.

For G50, project only:

native-six actor parameters
log_std
completed_phase_A_update_count
initialization/source/objective provenance

Delete from both arms before phase B:

credit_baselines module and all parameters
slow_critic module and state
policy.critic state
policy.delayed_residual state
all phase-A-only buffers and diagnostics
all phase-A optimizer state

No baseline, critic, constant, compatibility head or filler field may survive the projection.

Both arms then instantiate the exact G49 single-immediate phase-B graph and receive:

fresh empty separately owned Adam
identical actor/log_std parameter order
lr=1e-3
betas=(0.9,0.999)
eps=1e-8
weight_decay=0
amsgrad=false

Phase B uses the frozen G49 objective in both arms for 10 nonformal or 100 formal updates. The phase boundary may preserve different actor bytes caused by the phase-A treatment, but no optimizer or auxiliary-module state may mediate that difference.

EVIDENCE_CEILING_AND_NONCOMPUTE

clarification_evidence=
Git-visible allow-listed historical evidence only

real_environment_transitions=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
optimizer_steps=0
bootstrap_resamples=0

implementation=false
nonformal_compute=false
formal_compute=false

The identified contract is supported jointly by:

the G40 design and code-science index;

the exact G40 source and runner symbols;

the accepted formal evidence note;

the immutable common-anchor fixture handoff;

G49’s frozen single-immediate route;

the prior G50 seed, phase-reset, activation and evidence ceilings.

No historical variant was averaged, and no objective was reconstructed from preference.

G50 seeds and offsets now fully bound
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

For formal replicate r∈{0,1,2}, add r exactly once to every non-bootstrap seed. For nonformal work, add 900000 exactly once to every seed, including the bootstrap seed.

Forced-first-batch gates now fully bound

Let g
F
	​

 be the reference actor-plus-log_std gradient of the historical G40 PPO term using normalized r−b
I
old
	​

, excluding common entropy and baseline-loss gradients.

Let g
I
	​

 be the counterfactual G49 single-immediate actor-plus-log_std gradient on the same pre-update model and trajectory, also excluding common entropy.

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

 is nonfinite,
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


Required:

q_A>1e-6
equality_at_1e-6=inactive

all actor groups finite under both objectives
each actor group live in at least one objective
common entropy gradient bytes equal

reference-only activation evidence
actual null activation-evidence read count=0

B-specific matched-shadow gates:

baseline target bytes equal
baseline output bytes equal before treatment
baseline MSE loss bytes equal
baseline parameter-gradient bytes equal
baseline Adam state bytes equal after every phase-A pass

baseline read into null actor objective=0
baseline read into null action/logprob=0
baseline read into null checkpoint/evaluation/result=0

The zero-step historical diagnostics must also show finite live actor groups, slow-critic path, immediate-baseline path and successor-baseline path, with zero diagnostic optimizer steps.

Activation scope remains:

nonformal:
    at least one active phase-A pass

formal:
    at least one active phase-A pass in each replicate 0|1|2
Real-transition ceilings remain unchanged
nonformal_total_real_transitions=22272
formal_total_real_transitions=626688

nonformal_wall_clock_cap_seconds=1200
formal_wall_clock_cap_seconds=28800

H=48
K_search=0
nested_rollout=false
replanning=false

Only the optimizer ambiguity was unresolved; B fixes its value to 80/2400.

DISPOSITION=CONTRACT_IDENTIFIED_B

NEXT_BOUNDARY

next_boundary=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_FAST_ANCHOR_ATTRIBUTION_G50_CODE_SCIENCE_ALIGNMENT_AUDIT

This boundary applies only after Code Project Manager independently realizes and technically accepts the exact interpretation-B G50 implementation.

The alignment audit must verify that:

both phase-A arms instantiate the complete G40 common-anchor graph and one-step-per-pass optimizer package;

the immediate-baseline package is byte-matched and shadow-only for the null actor;

the sole phase-A treatment is historical baseline-conditioned fast actor credit versus G49 single-immediate actor credit;

every phase-A auxiliary state is deleted before phase B;

the 80/2400 optimizer ceilings, seeds, q
A
	​

 activation, phase reset and prior G50 first-match contract are exact.

This clarification authorizes no implementation or compute.

中文简报

G50_fast_anchor_contract=B

历史 common fast anchor 不是只抽出一条 actor gradient 的 A，而是完整的 G40 phase-A package：

native-six actor + log_std
+
shared two-output credit baseline
+
immediate baseline MSE
+
一个共同 Adam optimizer

正式历史 source 是：

97a8b237e0cec6c2713dd2a710d324040fa3dfc2

Reference phase A 的 actor advantage 是：

r
t
	​

−stopgrad(b
I
old
	​

(ξ
t
	​

)),

只 normalization 一次，两次 PPO pass 复用。实际 loss 是：

PPO immediate-residual loss
+ VALUE_COEFFICIENT * MSE(immediate baseline, reward)
- ENTROPY_COEFFICIENT * entropy

一个 Adam 同时拥有 actor、log_std 和完整 credit_baselines 参数。每个 PPO pass 只有一次 optimizer.step()；slow critic 和 successor-baseline loss 只做零步数 liveness diagnostic，不做 phase-A 更新。

因此 G50 的完整匹配必须让 null 也保留相同 baseline module、loss 和 Adam exposure，但 baseline output 对 null actor gradient、action、checkpoint 和 evaluation 全部零读取。唯一 treatment 是：

reference:
    normalized (reward - old immediate baseline)

null:
    G49 normalized raw reward

Phase A 结束后，两臂都删除 baseline、critic、全部 phase-A optimizer state，只投影 actor/log_std，然后用 fresh empty Adam 进入相同的 G49 phase B。

精确 optimizer 预算现已确定：

nonformal=80
formal=2400

Transition 预算保持：

nonformal=22272
formal=626688

下一边界是 Code PM 独立实现并技术接受之后的 G50 code-science alignment audit。本轮不授权代码或计算。

CONTRACT_IDENTIFIED_B
