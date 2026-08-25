1. REGISTERED_DESIGN_CONFORMANCE
REGISTERED_DESIGN_CONFORMANCE=
CONFORMS_AFTER_GLOBAL_CREDIT_NORM_MATCHED_CLAIM_NARROWING

source_id=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_CHANNEL_SCALE_NORMALIZATION_ATTRIBUTION_G44_P0

design_audit_compute=0
H=48
K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false

The prerequisite boundary is closed:

G43_formal_branch=
EQUAL_MEAN_RAW_SUM_SUFFICIENT_G43

accepted_post_anchor_route=
COMMON_NATIVE6_FAST_ANCHOR
→ NATIVE6_G31_EQUAL_MEAN_NO_SHADOW_NO_SLOW

G43_retained_unresolved_component=
INDEPENDENT_PER_CHANNEL_SCALE_NORMALIZATION

G43 established that the literal no-shadow equal-channel mean preserves access and is noninferior to the DB-derived dynamic norm schedule. The retained post-anchor route still contains the realized-successor target, immediate/successor decomposition, shared true-current-state baseline, independent channel normalization, literal equal-channel mean, and common fast anchor. Four conclusion-bearing iterations remain.

Necessary narrowing of the submitted assertion

A direct comparison of

2
1
	​

(g
I
IND
	​

+g
S
IND
	​

)

against

2
1
	​

(g
I
POOL
	​

+g
S
POOL
	​

)

would generally change two objects simultaneously:

the relative weighting and direction of the immediate and successor credit gradients;

the global magnitude of the credit-bearing actor update.

The second difference is an effective actor learning-rate schedule. Under Adam it changes first and second moments, epsilon sensitivity, subsequent coordinatewise steps, and the actor-to-baseline update ratio. G43 explicitly treated scalar-gradient history as potentially causal rather than negligible.

The question requires actor-step scale matching and directs rejection when scale cannot be matched while changing only the channel-scale rule.

G44 is therefore identifiable only under this narrower proposition:

G44 tests whether independent relative channel scaling is removable in favor of a pooled-scale direction while retaining, as a nuisance control, the local counterfactual independent-scale global credit-gradient norm.

This does not yet test complete deletion of every independent-scale computation. Without this narrowing, the draft comparison is non-identifying.

2. DESIGN_SCIENTIFIC_DISPOSITION
DESIGN_SCIENTIFIC_DISPOSITION=
IDENTIFIABLE_GLOBAL_CREDIT_NORM_MATCHED_CHANNEL_SCALE_ATTRIBUTION_G44_DESIGN
Exact arms
reference_arm=
NATIVE6_G31_EQUAL_MEAN_INDEPENDENT_SCALE

null_arm=
NATIVE6_G31_EQUAL_MEAN_POOLED_SCALE

Both arms retain exactly:

accepted G40 common fast anchor
accepted G41 no-slow projection
native-six actor
log_std
shared immediate/successor two-output baseline
immediate reward target
realized-successor target
separate channel centering
literal equal-channel mean
PPO clipping and likelihood semantics
common entropy regularization
actor/head parameter inventory
Adam hyperparameters and optimizer-step exposure
G32/G34 source and paired RNG ownership
final-only checkpoint selection

Neither arm may compute a DB vector, DB norm, or DB shadow. G43 already closed the local need for that machinery and accepted the no-shadow equal-channel route.

Normalization unit

For one branch update:

num_envs=8
H=48
normalization_rows=384
normalization_unit=one team-level primitive-step row
normalization_before_active-factor broadcast=true
active-count weighting=false

Both channels use the same ordered set T of 384 primitive-step rows. A residual is represented once per environment step—not once per active agent or autoregressive action factor.

Residuals and retained centering

For j∈T, define detached residuals:

x
j
I
	​

=r
j
	​

−stopgrad(b
I
	​

(ξ
j
	​

)),
x
j
S
	​

=G
j+1
	​

−stopgrad(b
S
	​

(ξ
j
	​

)),

with:

G
H
	​

=0,G
t
	​

=r
t
	​

+0.99G
t+1
	​

.

Retain separate channel means:

μ
I
	​

=
n
1
	​

j
∑
	​

x
j
I
	​

,μ
S
	​

=
n
1
	​

j
∑
	​

x
j
S
	​

,

and centered rows:

c
j
I
	​

=x
j
I
	​

−μ
I
	​

,c
j
S
	​

=x
j
S
	​

−μ
S
	​

.

The pooled arm must not introduce a pooled mean. Separate centering is identical in both arms and is outside the treatment.

Frozen scale operator

Let Scale
43
	​

 denote the exact accepted G43 finite-precision scale operator, including:

dtype
reduction order
population/sample convention
epsilon, if any
zero-denominator behavior

The reference arm must use that operator byte-for-byte; G44 may not replace it.

Independent-scale reference
s
I
	​

=Scale
43
	​

(c
I
),s
S
	​

=Scale
43
	​

(c
S
),
z
I
IND
	​

=Z
43
	​

(c
I
,s
I
	​

),z
S
IND
	​

=Z
43
	​

(c
S
,s
S
	​

).
Pooled-scale null

Apply the same accepted scale law to the concatenation of the two separately centered rows:

s
P
	​

=Scale
43
	​

([c
I
;c
S
]).

In exact population-RMS arithmetic this is:

s
P
	​

=
2n
∑
j
	​

(c
j
I
	​

)
2
+∑
j
	​

(c
j
S
	​

)
2
	​

	​

.

Then:

z
I
POOL
	​

=Z
43
	​

(c
I
,s
P
	​

),z
S
POOL
	​

=Z
43
	​

(c
S
,s
P
	​

).

No learned weighting, running statistic, per-group scale, maximum-scale rule, arithmetic mean of channel scales, active-count weighting, or coefficient search is permitted.

Credit-gradient construction

Separate the actor update into:

p
I
	​

(z
I
	​

): the clipped PPO likelihood-surrogate gradient for the immediate channel;

p
S
	​

(z
S
	​

): the clipped PPO likelihood-surrogate gradient for the successor channel;

g
E
	​

: the inherited common entropy-gradient contribution.

This is an algebraic decomposition of the accepted G43 equal-mean objective; the reference arm must pass a direct equivalence gate against the accepted G43 actor update.

The independent credit gradient is:

v
IND
	​

=
2
1
	​

[p
I
	​

(z
I
IND
	​

)+p
S
	​

(z
S
IND
	​

)].

The raw pooled credit gradient is:

v
POOL
	​

=
2
1
	​

[p
I
	​

(z
I
POOL
	​

)+p
S
	​

(z
S
POOL
	​

)].
Required credit-step scale matching

For the pooled arm’s own current pre-update state and trajectory, compute a shadow independent-scale counterfactual:

v
IND,cf
POOL
	​

.

Only its detached scalar norm may be used:

m
cf
	​

=
	​

v
IND,cf
POOL
	​

	​

2
	​

.

The pooled assigned credit gradient is:

v
POOL
	​

=
⎩
⎨
⎧
	​

0,
m
cf
	​

∥
v
POOL
	​

∥
2
	​

v
POOL
	​

	​

,
	​

m
cf
	​

=0,
m
cf
	​

>0∧∥
v
POOL
	​

∥
2
	​

>0.
	​


Total actor gradients are:

d
IND
	​

=v
IND
	​

+g
E
	​

,
d
POOL
	​

=v
POOL
	​

+g
E
	​

.

The common entropy gradient is added unchanged after credit-norm control. It must not be included in the rescaled vector. Rescaling the complete actor gradient would change the effective entropy coefficient and introduce a second treatment.

Matching the credit-bearing actor-gradient norm is the smallest valid scale control. Differences in the total gradient norm caused solely by the changed angle between the matched credit vector and the identical entropy vector are downstream geometric consequences of the intended treatment.

Important algebraic interpretation

For any positive pooled denominator, both pooled channel likelihood gradients share a common scalar. After local credit-norm matching, that common scalar cancels from the assigned direction. G44 therefore does not uniquely validate the numerical value of s
P
	​

.

The actual causal distinction is:

independent relative channel weighting
versus
one common channel scale / equal centered-channel weighting

The pooled RMS remains frozen as the exact registered null and as a zero/support check, but the scientific claim is about relative channel scaling, not the intrinsic merit of one particular positive pooled denominator.

Shadow boundary

The pooled arm’s local independent-scale counterfactual may:

compute one detached scalar credit-gradient norm

It must not:

supply vector coordinates to the assigned gradient
change pooled normalized advantages
alter separate centering
create optimizer state
write parameter gradients
consume RNG
mutate model or buffer state
affect checkpoint selection
affect evaluation or result selection

Accordingly, a pooled-sufficiency result can support only:

Independent relative channel scaling is removable under G44-P0 while the counterfactual independent-scale global credit-norm schedule is retained.

It cannot yet support complete deletion of independent-scale shadow computation.

Claim ceilings

A reduction branch may support only:

Independent relative per-channel scale normalization is removable in favor of
the globally credit-norm-matched pooled-scale direction under G44-P0.

A positive reference branch may support only:

Independent relative channel scaling supplies a source-local finite-budget
access or material-utility advantage over the exact globally credit-norm-matched
pooled-scale null.

Neither result may establish the necessity or redundancy of:

realized-successor targeting
immediate/successor decomposition
separate channel centering
shared-baseline conditioning
true-current-state baseline inputs
literal equal-channel composition
common fast anchor
recurrence
broader process/capacity/horizon transport
UAV mechanisms
G33
3. IDENTIFICATION_FAILURES_AND_COUNTEREXAMPLES
3.1 Unmatched global credit scale

Without the local norm control, pooled scaling changes both relative channel geometry and effective actor learning rate. A result could then be caused by Adam moment magnitude rather than channel-scale structure.

Closure: match the pooled arm’s credit-gradient norm to its own local independent-scale counterfactual on every PPO pass.

3.2 Cross-arm scale authority

Using the reference arm’s norm to scale the later-diverging pooled arm would make one arm’s current state control the other arm’s update and would conflate treatment with cross-arm policy divergence.

Closure: actual pooled updates use only the pooled arm’s local counterfactual. The reference arm is used only for treatment-activation evidence.

3.3 Full-removal overclaim

Because the pooled arm retains a scalar independent-scale counterfactual, a positive pooled branch cannot establish:

all independent normalization computation can be deleted

It establishes only removal of independent relative channel weighting. A later no-shadow schedule comparison would be scientifically distinct.

3.4 Pooled mean instead of pooled scale

Centering the concatenated residuals around one joint mean would change both location and scale.

Closure: μ
I
	​

 and μ
S
	​

 remain separate. Pool only the centered second-moment statistic.

3.5 Active-count or action-token weighting

If residuals are duplicated per active action factor before scale calculation, high-roster steps receive extra weight and membership process becomes part of the treatment.

Closure: one team-level residual per primitive step, before active-factor broadcast.

3.6 Pooled-scale numerical law is not the main estimand

After credit-norm matching, any positive common denominator generates the same pooled credit direction under the frozen PPO surrogate. The exact pooled RMS is therefore not itself load-bearing except for zero and validity semantics.

Consequence: any positive result must be described as evidence about independent relative channel conditioning, not evidence that the particular pooled RMS formula is uniquely superior.

3.7 Scale difference without directional treatment

The fact that s
I
	​


=s
S
	​

 does not ensure a changed assigned actor direction. The two channel gradients may be collinear, one channel may be locally zero, or their weighted combinations may remain parallel.

A denominator-only activation gate could therefore certify a vacuous comparison.

3.8 Treatment-activation evidence

Using only the independent-scale reference arm’s pre-update residuals, define:

q
scale
	​

=
⎩
⎨
⎧
	​

0,
max(s
I
	​

,s
S
	​

)
∣s
I
	​

−s
S
	​

∣
	​

,
	​

s
I
	​

=s
S
	​

=0,
otherwise.
	​


On that same reference state construct:

v
IND,ref
	​

,
v
POOL,cf
	​

.

When both are nonzero, define:

q
dir
	​

=
	​

∥v
IND,ref
	​

∥
2
	​

v
IND,ref
	​

	​

−
∥
v
POOL,cf
	​

∥
2
	​

v
POOL,cf
	​

	​

	​

2
	​

.

A PPO pass counts as treatment-active only when:

q_scale > 1e-6
q_direction > 1e-6
reference credit norm > 0
reference pooled-counterfactual credit norm > 0

Required package activation:

nonformal:
    at least one treatment-active pass

formal:
    at least one treatment-active pass
    in each accepted-anchor replicate 0|1|2

The later-diverging pooled arm supplies no activation evidence:

evidence_source_arm=INDEPENDENT_SCALE
pooled_arm_evidence_read_count=0
reference_pooled_counterfactual=true

The analyzer must reconstruct both q statistics from serialized reference-arm rows; a stored pass Boolean is insufficient.

3.9 Zero and cancellation semantics
Condition	Required behavior
Both centered channels and both credit gradients are zero	Both arms submit exact-zero credit gradients; common entropy and baseline updates continue; treatment inactive
One centered channel is zero	Its normalized row remains exact zero; valid, but treatment counts only if both activation predicates pass
Local independent counterfactual norm m
cf
	​

=0	Pooled assigned credit gradient is exact zero
m
cf
	​

>0 but pooled raw credit gradient is zero	INVALID before either optimizer step
Any nonfinite residual, mean, scale, normalized row, gradient, norm, or scalar	INVALID before either optimizer step

No fallback channel, epsilon direction, perturbation, or priority rule is permitted.

3.10 Learning-signal liveness

Before the first optimizer step and on every treatment-counting pass require:

immediate likelihood-surrogate gradient finite and globally live
successor likelihood-surrogate gradient finite and globally live

exact registered actor-group inventory present
every actor group finite in both channel rows
every actor group live in at least one channel

immediate baseline-output gradient finite and >1e-12
successor baseline-output gradient finite and >1e-12

Non-counting zero passes may occur only under the frozen exact-zero semantics and may not supply treatment evidence.

3.11 Baseline and entropy contamination

The treatment applies only to detached actor credit advantages.

These objects remain bitwise or reconstruction-equivalent:

baseline targets
baseline losses
baseline parameter order
baseline gradients
baseline Adam exposure
entropy coefficient
entropy gradient

No actor norm may include baseline parameters, and no baseline loss may enter the matched credit norm.

3.12 PPO-pass recomputation

Residuals, channel means, scales, and normalized advantages are computed once from the complete stored trajectory and reused across both PPO passes.

Actor likelihood gradients and the local scalar norm control are recomputed on each pass because actor parameters change after pass one.

Recomputing residual means or scales between PPO passes is forbidden.

3.13 Adam consequences

Even with matched pre-Adam credit norms, different relative channel geometry changes coordinatewise gradient distributions and therefore later Adam moments.

That is an intended consequence of the treatment. Matching post-Adam parameter deltas would add an optimizer controller and destroy causal identification.

3.14 Common-anchor limitation

G44 begins from accepted G40 common fast anchors. It does not test:

independent vs pooled scaling from random initialization
removal of the common fast phase
another optimizer
another branch-update budget
another source family
3.15 Source and transport limits

G44 inherits:

H=48
configured capacities=6|8|12
G32 fixed source
G34-P0 bounded random source
one each of L/R/J/T
three registered legal event orders

It cannot establish arbitrary process laws, active counts, capacities, event patterns, horizons, recurrence necessity, UAV transport, asynchronous skill lifetime, or intrinsic-reward benefit. The non-G33 UAV direction remains parked behind source identifiability, while G33 remains frozen.

Smallest branch witnesses
Outcome	Minimal valid witness
Invalid	Pooled mean replaces separate centering; active-token weighting; pooled arm reads reference vector coordinates; positive local reference norm with zero pooled direction; dead actor/baseline group; treatment inactive in a required replicate; unequal optimizer exposure
Source/reference failure	Source invalid or independent-scale reference arm confidently fails an inherited absolute-access predicate
Pooled sufficiency	Both arms access and every IND-minus-POOL primary/component UCB is <=0.05
Independent-scale advantage	Reference accesses and POOL confidently fails, or pooled primary LCB is >0.05 with all capacity-specific LCBs positive
Mixed/underpowered	Every remaining operationally valid numerical pattern
4. CDC_PORTFOLIO_LEDGER_EDITS

This is a zero-compute design freeze. It changes no scientific status.

CONJECTURES.md
EDIT=NONE

G43 already records the accepted fixed-equal-mean route and preserves independent channel normalization, realized-tail targeting, decomposition, shared-baseline conditioning, and the common anchor as unresolved components.

RESEARCH_DIRECTION_LEDGER.md
STATUS_EDIT=NONE

Retain:

independent_per_channel_scale_normalization=OPEN_UNTESTED

Mechanically narrow its text to:

Markdown
| G43 accepted equal-mean branch 中 independent relative channel-scale
normalization 的局部必要性 | `OPEN_UNTESTED` | 保持 accepted anchors、G41
no-slow projection、realized-tail、immediate/successor decomposition、shared
true-state baseline、separate channel centering、literal equal mean、source 与
Adam exposure 不变；比较 independent relative scaling 与 pooled relative
scaling，并用每个 arm 自身的 counterfactual independent-scale global
credit-gradient norm 匹配 credit-step scale。 | G44 design 已冻结；该边界不检验
完全删除 independent-scale shadow，尚无 conclusion-bearing result。 |

No broader process, horizon, capacity, recurrence, UAV, lifetime, or intrinsic-reward row changes.

IDEA_PORTFOLIO.md
SCIENTIFIC_ROW_EDIT=NONE

After mechanical archival only:

completed_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_CHANNEL_SCALE_NORMALIZATION_ATTRIBUTION_G44_DESIGN_ASSERTION_AUDIT

design_disposition=
IDENTIFIABLE_GLOBAL_CREDIT_NORM_MATCHED_CHANNEL_SCALE_ATTRIBUTION_G44_DESIGN

valid_result_disposition=CONTINUE

next_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_CHANNEL_SCALE_NORMALIZATION_ATTRIBUTION_G44_CODE_SCIENCE_ALIGNMENT_AUDIT

conclusion_bearing_iterations_consumed=33
iterations_remaining=4
CURRENT_WORK.md

After mechanical archival only:

last_completed_assignment_id=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_CHANNEL_SCALE_NORMALIZATION_ATTRIBUTION_G44_DESIGN_ASSERTION_AUDIT

active_assignment_id=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_CHANNEL_SCALE_NORMALIZATION_ATTRIBUTION_G44_CODE_SCIENCE_ALIGNMENT_AUDIT

next_boundary=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_CHANNEL_SCALE_NORMALIZATION_ATTRIBUTION_G44_CODE_SCIENCE_ALIGNMENT_AUDIT

g44_design_disposition=
IDENTIFIABLE_GLOBAL_CREDIT_NORM_MATCHED_CHANNEL_SCALE_ATTRIBUTION_G44_DESIGN

g44_reference_arm=
NATIVE6_G31_EQUAL_MEAN_INDEPENDENT_SCALE

g44_null_arm=
NATIVE6_G31_EQUAL_MEAN_POOLED_SCALE

g44_primary_treatment=
independent_relative_channel_scaling_vs_pooled_relative_scaling

g44_retained_nuisance_control=
local_counterfactual_independent_scale_global_credit_gradient_norm

g44_design_compute=0
conclusion_bearing_iterations_consumed=33
iterations_remaining=4

The active record places G44 at the current design boundary after accepted iteration 33.

ALGORITHM_PRINCIPLES.md
EDIT=NONE

G44 applies the existing mechanism-matched comparator, optimizer-exposure, replacement-before-accumulation, and narrow-result rules.

5. DESIGN_VALID_DISPOSITION
DESIGN_VALID_DISPOSITION=CONTINUE

conclusion_bearing_iteration_cost=0
conclusion_bearing_iterations_consumed=33
remaining_conclusion_bearing_iterations=4

The globally credit-norm-matched design is identifying and remains within the active evidence-complexity boundary. The balance is not exhausted, and an exact in-scope realization/audit candidate exists.

Direction	State after G44 design audit
Independent relative channel scaling	Live; G44 realization/audit scheduled
Complete removal of independent-scale shadow norm	Live, but not adjudicated by G44
Separate channel centering	Live, unscheduled
Realized-successor target attribution	Live, unscheduled
Immediate/successor decomposition	Live, unscheduled
Shared-baseline conditioning	Live, unscheduled
Common fast-anchor simplification	Live, unscheduled
Broader process/horizon/capacity	Live, unscheduled
Identifiable non-G33 UAV transport	Parked behind source identifiability
Recurrence/EHC	Parked behind a genuinely hidden-information source
C-BASE/C-COORD	Live outside this local reduction
Asynchronous skill lifetime/intrinsic reward	OUT_OF_SCOPE_FROZEN
G33 lineage	Permanently frozen

Scheduling G44 does not make channel scaling the unique scientific direction and retires none of the unselected portfolio. The role contract requires one scheduled action while preserving all other viable directions.

6. CURRENT_SCHEDULED_ACTION_IF_CONTINUE
current_scheduled_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_CHANNEL_SCALE_NORMALIZATION_ATTRIBUTION_G44_CODE_SCIENCE_ALIGNMENT_AUDIT

This boundary becomes eligible only after Code Project Manager independently realizes and technically accepts one exact pushed implementation of the frozen G44 contract.

Its sole scientific question is:

Does the accepted implementation preserve the exact G43 fixed-equal-mean no-shadow route, retain separate channel centering and all targets/baselines, instantiate the concatenated pooled scale law, match the credit-bearing actor norm using only a scalar local independent-scale counterfactual, preserve common entropy and baseline updates, reconstruct treatment activation exclusively from reference-arm pre-update evidence, and fail closed on zero/cancellation, liveness, provenance, pairing, optimizer, evidence, and confidence mismatches?

This response authorizes no implementation, Git activity, proof execution, nonformal compute, or formal compute.

7. EXECUTABLE_DESIGN_BOUNDARY
7.1 Provenance

Freeze:

accepted_G40_anchor_replicates=0|1|2
accepted_G40_source_commit=
97a8b237e0cec6c2713dd2a710d324040fa3dfc2

accepted_G41_projection_source_commit=
a5f63c349228fc2bba7843647e0ae4c34361c1c9

accepted_G42_reference_source_commit=
a6c3c2971ee74e76a453995c3a7c12627bb8f02c

accepted_G42_aligned_source_commit=
6b8ea82d8fdbc76c14a414ff2b042a126f945dfb

accepted_G42_alignment_stage=
309858dca06af66f13857f94773bcef37527d821

accepted_G43_formal_source_commit=
bb42840ab1479abde7f3485006bfbbee981a73cf

accepted_G43_aligned_source_commit=
45e16f71d171228135b6444bee1678b157d79abe

accepted_G43_alignment_stage=
889c0b4e3d68a8d74f811ae9ecfe7b5213abfa76

The G43 index and formal evidence bind these accepted identities and the final no-shadow route.

For each replicate:

Strict-validate the accepted G40 anchor manifest entry and complete-state digest.

Apply the accepted G41 no-slow projection.

Clone retained state bitwise into IND and POOL arms.

Create empty, separately owned actor/head Adam states.

Require zero shared parameter, buffer, gradient, or optimizer storage.

Consume no model RNG during projection.

7.2 Exact branch graphs

Both arms contain exactly:

native-six actor
log_std
shared immediate/successor two-output baseline
no learned actor carry
no standalone slow critic
no DB composer
no DB norm
no DB shadow

Before treatment they require identical:

semantic state keys
tensor shapes
trainable masks
parameter counts
initial bytes
actor/head optimizer parameter order

No arm-specific parameter, learned scale, running statistic, scheduler, or auxiliary head is permitted.

7.3 Frozen normalization evidence

Every update serializes and binds:

normalization_row_count=384
normalization_unit=primitive_team_step
normalization_before_active_factor_broadcast=true
active_count_weighting=false

immediate_mean
successor_mean
immediate_centered_sum_square
successor_centered_sum_square
immediate_scale
successor_scale
pooled_scale
normalization_mask_digest
accepted_scale_operator_identity

The validator recomputes these values rather than trusting a pass flag.

7.4 Exact actor-gradient plans
IND arm
z_I = accepted_normalize(centered_I, scale_I)
z_S = accepted_normalize(centered_S, scale_S)

independent_raw_credit_gradient =
0.5 * (
    immediate_likelihood_surrogate_gradient(z_I)
    + successor_likelihood_surrogate_gradient(z_S)
)
POOL arm
pooled_scale =
accepted_scale_operator(concat(centered_I, centered_S))

z_I = accepted_normalize(centered_I, pooled_scale)
z_S = accepted_normalize(centered_S, pooled_scale)

pooled_raw_credit_gradient =
0.5 * (
    immediate_likelihood_surrogate_gradient(z_I)
    + successor_likelihood_surrogate_gradient(z_S)
)

The pooled arm then computes its own local independent-scale counterfactual solely for its detached global credit norm and rescales the pooled raw credit direction to that norm.

7.5 Shadow-dependency certificate

The pooled arm records:

counterfactual_independent_scale_shadow=true
shadow_output_type=one_detached_scalar_credit_norm

shadow_vector_serialized=false
shadow_vector_coordinate_use_outside_norm=0
shadow_gradient_assignment_count=0
shadow_optimizer_state_count=0
shadow_RNG_consumption=0
shadow_model_mutation_count=0
shadow_checkpoint_selection_reads=0
shadow_evaluation_reads=0

independent_scale_read_into_pooled_normalized_advantages=0
independent_scale_read_into_pooled_credit_direction=0

A serialized declaration is insufficient; the later code-science audit must reconstruct these dependencies from actual call paths and parameter flows.

7.6 Credit-norm gate

For every pooled-arm PPO pass:

m
cf
	​

=
	​

v
IND,cf
POOL
	​

	​

2
	​

.

Require:

∣∥v
POOL
	​

∥
2
	​

−m
cf
	​

∣≤10
−8
+10
−6
m
cf
	​

.

Zero/cancellation rules:

m_cf=0:
    pooled assigned credit gradient=exact_zero

m_cf>0 and pooled_raw_credit_norm=0:
    INVALID before either optimizer step

The common entropy gradient is added after this gate and must be identical in both arms.

7.7 First paired-batch audit

Before either first update:

actor_bytes_equal=true
log_std_bytes_equal=true
shared_baseline_bytes_equal=true
actor_head_Adam_states_empty_and_separate=true
stored_trajectories_equal=true

unnormalized_residual_rows_equal=true
channel_means_equal=true
baseline_gradients_equal=true
common_entropy_gradient_equal=true

local_independent_counterfactual_norms_equal=true

The only permitted initial difference is the relative channel-scale rule and the resulting norm-matched credit direction.

7.8 Liveness and treatment activation

Every treatment-counting pass binds the exact registered actor-group inventory and requires:

immediate surrogate gradient finite and globally live
successor surrogate gradient finite and globally live

every actor group finite in both channel rows
every actor group live in at least one channel

immediate baseline-output gradient finite and >1e-12
successor baseline-output gradient finite and >1e-12

Reference-arm activation evidence serializes:

s_I
s_S
s_P
q_scale
independent_credit_norm
pooled_counterfactual_credit_norm
q_direction

evidence_source_arm=INDEPENDENT_SCALE
pooled_arm_evidence_read_count=0
reference_pooled_counterfactual=true

Package gates:

nonformal:
    at least one pass with
    q_scale > 1e-6
    and q_direction > 1e-6

formal:
    at least one such pass
    in each replicate 0|1|2
7.9 Optimizer exposure

Freeze the accepted G43 actor/head optimizer:

optimizer=Adam
beta1=0.9
beta2=0.999
eps=1e-8
weight_decay=0
learning_rate=1e-3

gradient_clipping=none
minibatches=none
PPO_passes=2
one_actor_head_Adam_step_per_pass=true

Residuals, means, scales, and normalized advantages are computed once before both PPO passes.

Likelihood-surrogate gradients and the local credit-norm control are recomputed on each pass.

Baseline gradients are excluded from the credit norm and remain unchanged.

7.10 Seed ownership

Freeze:

branch_ledger_seed_base=10441000
branch_action_seed_base=10442000
branch_gradient_probe_seed_base=10443000

evaluation_base_ledger_seed_base=10444000
evaluation_process_seed_base=10445000
evaluation_action_seed_base=10446000

bootstrap_seed=10447044
nonformal_seed_offset=900000

For formal replicate r, add r exactly once to every nonbootstrap base. For nonformal work, additionally add 900000 to every seed, including the bootstrap seed.

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
actor/head Adam state

Both complete trajectories are materialized and validated before either arm updates.

Freeze update order after paired collection:

INDEPENDENT_SCALE then POOLED_SCALE

A proof-sized order-swap guard must establish that order cannot alter the mate’s stored inputs, RNG, targets, or initial optimizer state.

7.11 Evaluation inventory

For every arm, replicate, and capacity 6|8|12, evaluate:

FINAL_FIXED_DET
FINAL_FIXED_STOCH
FINAL_RANDOM_DET
FINAL_RANDOM_STOCH

No zero or anchor evaluation cell is added.

Formal support per replicate/capacity:

episodes_per_cell=48
unique_random_time_tuples=48

LRJT=16
LJRT=16
JLRT=16

At capacity 8, the three registered process profiles also occur 16/16/16.

Evaluation performs zero optimizer steps and fails closed on checkpoint, source, episode, trace, lifecycle, action-noise, or cell mismatch.

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

All non-strict equalities pass. ACCESS_CONFIDENT_FAIL uses the exact upper-confidence-bound duals.

7.13 Estimands

For paired final random-deterministic episodes:

Δ
scale,C,r,e
	​

=U
C,r,e
IND
	​

−U
C,r,e
POOL
	​

.

Primary:

Δ
scale
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
scale,C,r,e
	​

]
	​


Positive values favor independent relative scaling.

materiality_and_noninferiority_margin=0.05

Registered component contrasts:

fixed deterministic utility per capacity
random deterministic utility per capacity
fixed stochastic utility pooled across capacities
random stochastic utility pooled across capacities
random event-window utility per capacity
random process-segment utility per capacity
random-minus-fixed transport per capacity

POOL_NONINFERIOR requires every primary and component UCB to be <=0.05.

MATERIAL_INDEPENDENT_SCALE_ADVANTAGE requires:

LCB
95
	​

(Δ
scale
	​

)>0.05

and:

LCB
95
	​

(Δ
scale,C
	​

)>0∀C∈{6,8,12}.
7.14 Confidence construction
bootstrap_seed=10447044
nonformal_resamples=250
formal_resamples=10000
confidence_interval=95_percentile
episode_exclusions=none

One paired hierarchical plan is reused for every absolute and comparative quantity:

Resample the three accepted-anchor replicate blocks.

Within each selected replicate and capacity, resample all 48 whole episode IDs.

Retain both arms and every fixed/random and deterministic/stochastic mate.

Never independently resample members, primitive steps, events, credit channels, or action factors.

Weight capacities 6, 8, and 12 equally.

7.15 Frozen first-match table
Priority	Terminal branch	Exact predicate
1	INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_CHANNEL_SCALE_ATTRIBUTION_G44	Any provenance, graph, centering, row unit, scale law, shadow dependency, norm-match, liveness, treatment-activation, zero/cancellation, optimizer, RNG, source-trace, checkpoint, confidence, inventory, or authority invariant fails
2	SOURCE_OR_REFERENCE_ACCESS_FAILURE_G44	Operationally valid and source invalid, or the independent-scale reference confidently fails an inherited access predicate
3	POOLED_CHANNEL_SCALE_SUFFICIENT_G44	Both arms pass access and every IND-minus-POOL primary/component UCB is <=0.05
4	INDEPENDENT_CHANNEL_SCALE_ADVANTAGE_G44	Reference passes access and either POOL confidently fails or MATERIAL_INDEPENDENT_SCALE_ADVANTAGE=true
5	MIXED_UNDERPOWERED_CHANNEL_SCALE_ATTRIBUTION_G44	Every remaining operationally valid numerical pattern

Equality rules:

absolute-floor equality             = pass
random-minus-fixed LCB = -0.05      = pass
UCB(IND-POOL) = 0.05                = noninferior pass
LCB(IND-POOL) > 0.05                = strict advantage
q_scale = 1e-6                      = inactive
q_direction = 1e-6                  = inactive
credit-norm error at tolerance      = pass

No scale histogram, optimizer-moment diagnostic, training curve, event stratum, or wall-clock result may rescue or relabel an earlier branch.

7.16 Smallest evidence inventory

The G43 inventory remains the smallest defensible conclusion-bearing inventory:

three accepted-anchor replicates provide independent trained-state variation;

48 episodes preserve exact 16/16/16 order and capacity-8 profile balance;

100 branch updates preserve the accepted finite-budget boundary;

the allow-listed G43 evidence contains no precision analysis supporting a smaller inventory.

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

with zero scientific iteration cost—not a G44 scientific result. The evidence policy requires the 20-minute nonformal and eight-hour formal limits and forbids nested or horizon-growing search.

7.18 Scientific versus implementation-only choices

Scientifically frozen:

provenance
normalization row unit
separate centering
accepted independent scale law
pooled scale law
local counterfactual credit-norm control
common entropy isolation
shadow dependency ceiling
zero/cancellation semantics
liveness and activation gates
optimizer exposure
seed ownership
evaluation inventory
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
CPU process count
native-kernel organization
proof-test file placement
post-collection execution order subject to the order-swap invariant
8. 中文简报
G44设计裁决=
IDENTIFIABLE_GLOBAL_CREDIT_NORM_MATCHED_CHANNEL_SCALE_ATTRIBUTION_G44_DESIGN

DESIGN_VALID_DISPOSITION=CONTINUE

本轮结论性迭代成本=0
已消耗结论性轮次=33
剩余结论性轮次=4
为什么不能直接比较两个原始 normalization

若直接比较：

immediate / successor 各自缩放
versus
两条 channel 共用一个 pooled scale

最终 actor credit gradient 的两项都会变化：

相对 channel weighting / direction
全局 gradient magnitude

在 Adam 下，全局 magnitude 会改变一阶和二阶 moments、epsilon 作用以及 actor 与 baseline 的相对学习速度。因此不做 scale control 时，无法把结果只归因于 independent channel scaling。

G44 精确比较

Reference：

immediate 和 successor 分别中心化
分别使用自己的 accepted scale
固定 equal mean

POOL：

仍分别中心化
共用一个 pooled scale
固定 equal mean

POOL 的 credit-gradient 全局 norm，必须匹配其自身当前状态下的 independent-scale counterfactual norm。

不能使用 reference arm 的后期 norm 控制 pooled arm，否则会把 branch divergence 引入 treatment。

共同 entropy gradient 不参与缩放，baseline gradients 也完全不变。

所以 G44 真正检验的是：

immediate 和 successor 的相对独立缩放是否重要，而不是哪一臂使用了更大的 actor credit step。

Pooled scale

在理想 population-RMS 表达中：

s
P
	​

=
2n
∑(c
I
2
	​

)+∑(c
S
2
	​

)
	​

	​

,n=8×48=384.

实际实现必须复用 accepted G43 scale operator 的 dtype、reduction order、epsilon 和 zero rule。

不能按 active-agent 数重复或加权 residual。

两条 channel 仍分别中心化；只 pooling scale，不 pooling mean。

一个重要解释边界

在 positive pooled scale 下，两个 channel 都乘同一个正标量；随后又匹配全局 credit norm，因此该 pooled scale 的绝对数值会从最终 assigned direction 中消掉。

所以 G44 实际归因的是：

independent relative channel weighting
versus
common-scale equal centered-channel weighting

不是“某一个 pooled RMS 数值本身优越”。

Treatment activation

仅使用 reference arm 的 pre-update evidence：

q_scale > 1e-6
并且
q_direction > 1e-6

每个 formal replicate 至少出现一次。

仅有 s_I != s_S 不够；若两种 normalization 产生相同 actor credit direction，实验仍是 vacuous。

Claim ceiling

若 POOL 通过，只能说明：

independent relative channel scaling
在保留 local independent-derived global credit norm schedule 时可删除

不能说明 independent-scale shadow 已完全删除。

若 IND 获胜，只能说明 relative independent scaling 在 G44-P0、当前 Adam 与有限预算下具有局部优势。

正式分支
1 INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_CHANNEL_SCALE_ATTRIBUTION_G44
2 SOURCE_OR_REFERENCE_ACCESS_FAILURE_G44
3 POOLED_CHANNEL_SCALE_SUFFICIENT_G44
4 INDEPENDENT_CHANNEL_SCALE_ADVANTAGE_G44
5 MIXED_UNDERPOWERED_CHANNEL_SCALE_ATTRIBUTION_G44

主估计量：

Δ
scale
	​

=U
IND
	​

−U
POOL
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

本轮没有计算结果，因此：

CONJECTURES scientific status=不变
RESEARCH_DIRECTION_LEDGER status=OPEN_UNTESTED
IDEA_PORTFOLIO scientific rows=不变

下一边界仅为：

CONTINUOUS_ROSTER_NATIVE_SIX_G31_CHANNEL_SCALE_NORMALIZATION_ATTRIBUTION_G44_CODE_SCIENCE_ALIGNMENT_AUDIT

realized-tail、decomposition、baseline conditioning、separate centering、common fast anchor、broader process/horizon/capacity、可识别非 G33 UAV、recurrence/EHC 等方向继续保持 live 或 parked。G33 永久冻结。本裁决不授权实现、Git、nonformal 或 formal compute。
