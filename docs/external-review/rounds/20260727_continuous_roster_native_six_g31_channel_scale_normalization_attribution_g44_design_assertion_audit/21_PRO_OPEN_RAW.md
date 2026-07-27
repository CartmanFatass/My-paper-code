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

Formal G43 established that a literal no-shadow equal-channel gradient mean preserves access and is noninferior to the DB-derived dynamic norm schedule. The accepted route retains the realized-successor target, immediate/successor decomposition, shared true-current-state baseline, independent channel normalization, literal equal-channel mean, and common fast anchor. Four conclusion-bearing iterations remain.

Necessary correction to the draft assertion

A direct comparison of:

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

against:

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

would generally change two quantities simultaneously:

the relative weighting/direction of the immediate and successor channel gradients; and

the global magnitude of the resulting credit-bearing actor gradient.

The second difference is an effective actor learning-rate schedule. It is especially result-changing under Adam because it modifies first moments, second moments, epsilon sensitivity, and the actor-to-baseline update ratio. G43’s accepted disposition explicitly preserves finite-budget Adam effects as part of a scalar-schedule treatment rather than treating them as negligible.

The G44 question itself requires actor-step scale matching and says the design must be rejected if scale cannot be matched while changing only the channel-scale rule.

Therefore the scientifically identifiable G44 object is narrower than the unqualified phrase “independent normalization is removable”:

G44 tests whether relative independent per-channel scaling is removable in favor of a pooled-scale direction while retaining the counterfactual independent-scale global credit-gradient norm schedule as a nuisance control.

This preserves one treatment: relative channel-scale geometry. It does not yet test deletion of every independent-scale computation.

That narrowing is required for conformance; without it, the comparison is non-identifying.

2. DESIGN_SCIENTIFIC_DISPOSITION
DESIGN_SCIENTIFIC_DISPOSITION=
IDENTIFIABLE_GLOBAL_CREDIT_NORM_MATCHED_CHANNEL_SCALE_ATTRIBUTION_G44_DESIGN
Exact arms
reference_arm=
NATIVE6_G31_EQUAL_MEAN_INDEPENDENT_SCALE

null_arm=
NATIVE6_G31_EQUAL_MEAN_POOLED_SCALE

Both arms retain the accepted G43 post-anchor graph:

native-six actor
log_std
shared immediate/successor two-output baseline
no learned actor carry
no standalone slow critic
literal equal-channel gradient mean

They begin from the same accepted G40 common fast-anchor replicate after the accepted G41 no-slow projection. G43 established that the post-anchor route no longer requires any DB vector, DB norm, or DB shadow computation; G44 must not reintroduce one.

Exact normalization unit

For one complete branch update, let:

num_envs=8
H=48
n=384 primitive-step rows

The normalization unit is the team-level primitive-step row before broadcasting its advantage to active autoregressive action factors.

The scale statistics must not:

duplicate a row once per active member;

weight a row by active count;

use action-token counts;

exclude a terminal step;

independently mask the two credit channels.

Both channels use the same ordered row set T of size n.

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

Retain distinct channel means:

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

The pooled arm must not introduce a pooled mean. Separate centering remains identical between arms and is outside the treatment.

All means and scales are detached from actor and baseline optimization.

Scale operator

Let R(c) denote the exact population-RMS scale law:

R(c)=
n
1
	​

j
∑
	​

c
j
2
	​

	​

.

The implementation must preserve the accepted G43 finite-precision reduction order and zero-variance convention for the reference arm. The pooled computation applies that same law to the concatenated, separately centered rows.

Independent-scale reference
s
I
	​

=R(c
I
),s
S
	​

=R(c
S
).

Define:

Z(c,s)={
0,
c/s,
	​

s=0,
s>0.
	​


Then:

z
I
IND
	​

=Z(c
I
,s
I
	​

),z
S
IND
	​

=Z(c
S
,s
S
	​

).
Pooled-scale null

Freeze one pooled denominator:

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

=
2
s
I
2
	​

+s
S
2
	​

	​

	​

	​


and:

z
I
POOL
	​

=Z(c
I
,s
P
	​

),z
S
POOL
	​

=Z(c
S
,s
P
	​

).

This is equal channel weighting. There is no sample-count weighting, learned mixture, maximum scale, arithmetic mean of standard deviations, running statistic, or selected candidate.

Credit-gradient construction

To keep the common entropy regularizer outside the scale treatment, decompose the actor gradient mathematically into:

p
I
	​

(z
I
	​

): clipped PPO likelihood-surrogate gradient for the immediate channel;

p
S
	​

(z
S
	​

): clipped PPO likelihood-surrogate gradient for the successor channel;

g
E
	​

: the inherited common entropy-gradient contribution, added exactly once.

This is algebraically identical to the accepted equal mean when the same entropy term appears in both channel objectives.

Define the reference credit gradient:

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

Define the raw pooled credit gradient:

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
Required actor-step scale control

For the pooled arm’s own pre-update model, trajectory, residuals, and PPO pass, compute a shadow independent-scale counterfactual:

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

The pooled arm receives:

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


The total actor gradients are:

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

Thus:

the common entropy contribution is bitwise identical and is never rescaled;

the credit-bearing actor-gradient norm is matched;

only the direction induced by independent versus pooled relative scaling differs.

Matching the total gradient after adding entropy would rescale or geometrically distort the common entropy term and would introduce a second causal difference. The frozen scale gate therefore applies to the credit-bearing actor component; the common entropy gradient must be bitwise equal.

Shadow boundary

The pooled arm’s independent-scale counterfactual:

may:
    compute one scalar global credit-gradient norm

must_not:
    supply vector coordinates to the assigned gradient
    alter channel centering
    alter pooled normalized advantages
    create optimizer state
    write parameter gradients
    consume RNG
    mutate model or buffer state
    affect checkpoint selection
    affect evaluation or branch selection
    be serialized as a trainable interface

A pooled-sufficiency result can therefore support only:

Independent relative channel scaling is removable under G44-P0 while the counterfactual independent-scale global credit-gradient norm schedule is retained.

It cannot yet support complete deletion of independent-scale shadow computation.

Claim ceilings

A reduction result may support only:

Independent relative per-channel scale normalization is removable in favor of
pooled relative scaling under G44-P0 when the independent-scale global
credit-gradient norm schedule is retained as a scalar nuisance control.

A positive independent-scale result may support only:

Independent relative channel scaling supplies a source-local finite-budget
access or material-utility advantage over the exact globally norm-matched
pooled-scale null.

Neither outcome may establish the necessity or redundancy of:

realized-successor targeting;

immediate/successor decomposition;

separate channel centering;

shared-baseline conditioning;

true-current-state baseline inputs;

literal equal-channel composition;

the common fast anchor;

recurrence;

broader process, capacity, or horizon transport;

UAV mechanisms;

G33.

3. IDENTIFICATION_FAILURES_AND_COUNTEREXAMPLES
3.1 Unmatched global actor scale

Without the scalar norm control, the pooled arm changes both relative channel weighting and effective actor learning rate.

A performance difference could then be caused by:

smaller or larger actor updates;

different Adam moment magnitudes;

different epsilon sensitivity;

a changed actor-to-baseline learning-rate ratio.

That would not identify independent channel scaling.

Frozen closure: match the global norm of the credit-bearing actor component on every PPO pass while preserving the common entropy and baseline gradients unchanged.

3.2 Full-removal overclaim

Because the pooled arm retains a scalar counterfactual independent-scale norm, a pooled pass does not yet justify:

all independent-scale computation can be deleted

It justifies deletion of independent relative weighting.

A later no-shadow norm-schedule question would be scientifically distinct. G44 must not silently claim that later result.

3.3 Pooled mean instead of pooled scale

Computing one mean over the concatenation [x
I
	​

,x
S
	​

] would alter channel centering as well as scale.

Frozen closure: retain μ
I
	​

 and μ
S
	​

 separately. Pool only the two centered second moments.

3.4 Active-count weighting

If advantages are duplicated once per active action factor before scale estimation, high-roster steps receive more statistical weight. Membership process and normalization would become confounded.

Frozen closure: compute every scale on exactly one team residual per primitive step, before autoregressive broadcast.

3.5 Common positive scaling is not the scientific treatment

When both channels use one positive denominator, that denominator is a common scalar multiplier on the likelihood-surrogate gradients. After credit-norm matching, its absolute magnitude is a nuisance.

The actual G44 treatment is the ratio:

s
S
	​

s
I
	​

	​


versus a shared denominator, not the absolute value of s
P
	​

.

A positive result must therefore be interpreted as a relative channel-conditioning effect.

3.6 Scale difference without gradient-direction difference

A difference between s
I
	​

 and s
S
	​

 does not guarantee that the assigned actor direction changes. For example:

one channel gradient may be zero;

the two channel gradients may be collinear;

their weighted combinations may have the same unit direction.

A denominator-only activation gate could therefore certify a vacuous treatment.

Frozen closure: require both a scale-statistic difference and an actor-direction difference under a reference-state counterfactual.

3.7 Treatment-activation evidence

Using the independent-scale reference arm’s own pre-update state, compute:

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
otherwise,
	​


and construct on that same state:

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

A pass counts as treatment-active only when:

q_scale > 1e-6
q_dir   > 1e-6
reference credit norm > 0
pooled counterfactual credit norm > 0

Required package-level activation:

nonformal:
    at least one active pass

formal:
    at least one active pass
    in each accepted-anchor replicate 0|1|2

The actual pooled arm supplies no activation evidence:

evidence_source_arm=INDEPENDENT_SCALE
pooled_arm_evidence_read_count=0
reference_pooled_counterfactual=true

A forged pass flag is insufficient; the analyzer must reconstruct both q values from serialized reference-arm rows.

3.8 Zero-variance cases

Freeze these cases:

Condition	Independent arm	Pooled arm	Status
s
I
	​

=s
S
	​

=0	Both normalized credit rows zero	Both normalized credit rows zero	Valid; treatment inactive
s
I
	​

=0, s
S
	​

>0 or vice versa	Zero channel remains zero	Zero centered channel remains zero	Valid; activation still requires q
dir
	​

>10
−6

s
P
	​

=0 while either centered row is nonzero	—	Undefined/inconsistent pooled scale	INVALID before either optimizer
Any nonfinite residual, mean, scale, normalized row, gradient, norm, or scalar	—	—	INVALID

A zero credit-gradient step does not remove optimizer exposure:

actor_credit_gradient=exact_zero
common_entropy_gradient=retained
baseline_gradients=retained
actor_head_Adam_step=retained
stale_gradient_reuse=forbidden
3.9 Norm-match cancellation

Freeze:

m_cf=0:
    pooled assigned credit gradient=exact_zero
    valid but treatment inactive for that pass

m_cf>0 and ||pooled_raw_credit_gradient||=0:
    INVALID before either optimizer step

No fallback channel, epsilon direction, perturbation, or priority rule is permitted.

3.10 Dead actor or baseline group

Before the first optimizer step and in every serialized PPO-pass record:

immediate credit gradient finite and globally live
successor credit gradient finite and globally live

exact registered actor-group inventory present
every actor group finite in both channel rows
every actor group live in at least one channel

immediate-baseline output gradient finite and >1e-12
successor-baseline output gradient finite and >1e-12

Global liveness may not conceal a dead unaffected actor group or a dead baseline output.

3.11 Baseline and entropy contamination

The scale treatment applies only to detached actor advantages.

The following must remain identical:

baseline targets
baseline losses
baseline parameter order
baseline gradients
baseline Adam exposure
common entropy coefficient
common entropy gradient

No actor norm operation may include baseline parameters. No baseline loss may enter the actor norm used for matching.

3.12 PPO pass and normalization recomputation

Advantages, means, and scales are computed once from the complete stored trajectory before the two PPO passes.

They are reused across both passes.

Actor gradients and the scalar norm control are recomputed at each pass because the actor changes after pass one. Recomputing residual means or scales between passes would change the treatment and is forbidden.

3.13 Adam consequences

Even after matching pre-Adam credit-gradient norms, independent and pooled scaling can create different coordinate distributions and therefore different Adam moment trajectories.

That is the intended downstream consequence of changing relative channel geometry. Post-Adam parameter-delta matching would add another optimizer controller and erase the causal treatment.

3.14 Common-anchor limitation

G44 begins from accepted G40 common fast anchors. It does not test:

independent or pooled normalization from random initialization;

removal of the common fast phase;

another optimizer;

another branch-update budget;

another source family.

3.15 Source and transfer limits

G44 inherits:

H=48
configured capacities=6|8|12
G32 fixed source
G34-P0 bounded random source
one each of L/R/J/T
three legal event orders

It does not establish arbitrary process laws, active counts, capacities, event patterns, horizons, recurrence requirements, UAV transfer, asynchronous skill lifetime, or intrinsic-reward benefit. Those directions remain separately live, parked, or out of scope.

Smallest branch witnesses
Outcome	Smallest valid witness
Invalid	Pooled mean replaces separate centering; scale uses active-token weighting; pooled arm reads reference vector coordinates; positive reference norm with zero pooled direction; dead actor/baseline group; treatment inactive in a required replicate; unequal Adam exposure
Source/reference failure	Source invalid or independent-scale reference arm confidently fails an inherited absolute-access predicate
Pooled sufficiency	Both arms access and every IND-minus-POOL primary/component UCB is <=0.05
Independent-scale advantage	Reference accesses and pooled arm confidently fails, or pooled primary LCB exceeds 0.05 with all capacity-specific LCBs positive
Mixed/underpowered	Every remaining operationally valid numerical pattern
4. CDC_PORTFOLIO_LEDGER_EDITS

This is a zero-compute design freeze. It changes no scientific status.

CONJECTURES.md
EDIT=NONE

G43 already records the accepted fixed-equal-mean route and leaves independent per-channel normalization, realized-tail targeting, decomposition, baseline conditioning, and the common anchor unresolved.

RESEARCH_DIRECTION_LEDGER.md
STATUS_EDIT=NONE

Retain:

G43 accepted equal-mean branch 中 independent per-channel scale normalization
的局部必要性=OPEN_UNTESTED

Mechanically narrow its text to:

Markdown
| G43 accepted equal-mean branch 中 independent relative channel-scale
normalization 的局部必要性 | `OPEN_UNTESTED` | 保持 accepted anchors、G41
no-slow projection、realized-tail、immediate/successor decomposition、shared
true-state baseline、separate channel centering、literal equal mean、source 与
Adam exposure 不变；比较 independent relative scaling 与 pooled scaling，并以
每个 arm 自身的 counterfactual independent-scale global credit-gradient norm
匹配 actor-step scale。 | G44 design 已冻结；该边界不检验完全删除 independent
scale shadow，尚无 conclusion-bearing result。 |

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
counterfactual_independent_scale_global_credit_gradient_norm_schedule

g44_design_compute=0
conclusion_bearing_iterations_consumed=33
iterations_remaining=4

The active record already places G44 at the current design boundary after accepted iteration 33.

ALGORITHM_PRINCIPLES.md
EDIT=NONE

G44 applies the existing rules requiring a mechanism-matched comparator, matched optimizer exposure, replacement before accumulation, and narrow result semantics.

5. DESIGN_VALID_DISPOSITION
DESIGN_VALID_DISPOSITION=CONTINUE

conclusion_bearing_iteration_cost=0
conclusion_bearing_iterations_consumed=33
remaining_conclusion_bearing_iterations=4

The globally credit-norm-matched design is identifying and remains within the active evidence-complexity boundary. The balance is not exhausted, and an exact in-scope realization/audit candidate exists.

The preserved portfolio remains:

Direction	State after G44 design audit
Independent relative channel scaling	Live; G44 realization/audit scheduled
Complete removal of independent-scale shadow norm	Live but not adjudicated by G44
Realized-successor target attribution	Live, unscheduled
Immediate/successor decomposition	Live, unscheduled
Shared-baseline conditioning	Live, unscheduled
Separate channel centering	Live, unscheduled
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

Its sole scientific question will be:

Does the accepted implementation preserve the exact G43 fixed-equal-mean no-shadow route, retain separate channel centering and all targets/baselines, instantiate the concatenated pooled RMS law, match the credit-bearing actor norm using only a scalar local independent-scale counterfactual, preserve the common entropy and baseline updates, reconstruct treatment activation exclusively from reference-arm pre-update evidence, and fail closed on zero/cancellation, liveness, provenance, pairing, optimizer, evidence, and confidence mismatches?

This response authorizes no implementation, Git activity, proof execution, nonformal compute, or formal compute.

7. EXECUTABLE_DESIGN_BOUNDARY
7.1 Provenance

Freeze:

accepted_G40_anchor_replicates=0|1|2
accepted_G40_source_commit=97a8b237e0cec6c2713dd2a710d324040fa3dfc2

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

The G43 index and evidence bind these accepted source identities and the final no-shadow route.

For each replicate:

Strict-validate the accepted G40 anchor manifest entry and complete state digest.

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

Required equality before treatment:

semantic state keys
tensor shapes
trainable masks
parameter counts
initial bytes
actor/head optimizer parameter order

No arm-specific parameter, learned scale, scheduler, running statistic, or auxiliary head is permitted.

7.3 Frozen channel statistics

For every update:

normalization_rows=8*48=384
normalization_unit=one_team_row_per_primitive_step
normalization_before_active_factor_broadcast=true
active_count_weighting=false
episode_exclusions=none

Both arms must serialize:

immediate_mean
successor_mean
immediate_centered_sum_square
successor_centered_sum_square
immediate_scale
successor_scale
pooled_scale
normalization_row_count
normalization_mask_digest

The analyzer recomputes all statistics rather than trusting a pass Boolean.

7.4 Exact credit plans
Independent arm
z_I = centered_I / scale_I
z_S = centered_S / scale_S
credit_gradient = 0.5*(ppo_gradient(z_I)+ppo_gradient(z_S))
Pooled arm
pooled_scale =
sqrt((sum(centered_I^2)+sum(centered_S^2))/(2*n))

z_I = centered_I / pooled_scale
z_S = centered_S / pooled_scale

pooled_raw_credit_gradient =
0.5*(ppo_gradient(z_I)+ppo_gradient(z_S))

The pooled arm separately computes the independent-scale counterfactual on its own current state solely to obtain:

counterfactual_independent_credit_norm

Its assigned credit gradient is the pooled raw direction with that norm.

7.5 Shadow-dependency certificate

The pooled arm must record:

counterfactual_scale_shadow=true
shadow_output_type=one_detached_scalar_norm

shadow_vector_serialized=false
shadow_vector_coordinate_use_outside_norm=0
shadow_gradient_assignment_count=0
shadow_optimizer_state_count=0
shadow_RNG_consumption=0
shadow_model_mutation_count=0
shadow_checkpoint_selection_reads=0
shadow_evaluation_reads=0

A serialized record is insufficient; the future code-science audit must reconstruct the dependency from the actual graph and call paths.

7.6 Credit norm gate

For every pooled PPO pass:

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

Zero rules:

m_cf=0:
    pooled assigned credit gradient=exact_zero

m_cf>0 and pooled_raw_credit_norm=0:
    INVALID before optimizer step

The common entropy gradient is added after this gate and must be bitwise identical between arms.

7.7 Liveness and activation

Every PPO pass must bind the exact registered actor-group inventory.

Require:

immediate surrogate gradient finite and globally live
successor surrogate gradient finite and globally live

every actor group finite in both channel rows
every actor group live in at least one channel

immediate baseline-output gradient finite and >1e-12
successor baseline-output gradient finite and >1e-12

Reference-arm activation evidence must serialize and reconstruct:

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

Package requirements:

nonformal:
    at least one pass with
    q_scale>1e-6 and q_direction>1e-6

formal:
    at least one such pass
    in every replicate 0|1|2
7.8 Optimizer exposure

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

The immediate and successor residuals, means, scales, and normalized advantages are computed once before both passes.

The PPO actor gradients and scalar norm control are recomputed on each pass.

Baseline gradients are not included in the credit-gradient norm.

7.9 Seed ownership

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

A proof-sized order-swap guard must show no mate input, RNG, target, or optimizer state changes.

7.10 Evaluation inventory

For each arm, replicate, and capacity 6|8|12, evaluate:

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

7.11 Absolute-access gates

For each arm a:

Fixed source

For every capacity:

LCB
95
	​

(U
C
a,fixed,det
	​

)≥0.90.

Also:

LCB
95
	​

(U
a,fixed,stoch
)≥0.80,

with equal capacity weighting, and:

minimum fixed deterministic replicate mean >=0.85
Random source

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

Also:

LCB
95
	​

(U
a,random,stoch
)≥0.80,

and:

minimum random deterministic replicate mean >=0.85

All non-strict equalities pass. ACCESS_CONFIDENT_FAIL uses the exact UCB duals.

7.12 Estimands

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


Positive values favor independent relative channel scaling.

Freeze:

materiality_and_noninferiority_margin=0.05

Registered components:

fixed deterministic utility, per capacity;

random deterministic utility, per capacity;

fixed stochastic utility, equal-capacity pooled;

random stochastic utility, equal-capacity pooled;

random event-window utility, per capacity;

random process-segment utility, per capacity;

random-minus-fixed transport, per capacity.

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
7.13 Confidence construction

Freeze:

bootstrap_seed=10447044
nonformal_resamples=250
formal_resamples=10000
confidence_interval=95_percentile
episode_exclusions=none

One hierarchical paired plan is reused for every absolute and comparative quantity:

Resample the three accepted-anchor replicate blocks.

Within each selected replicate and capacity, resample all 48 whole episode IDs.

Retain both arms and every fixed/random and deterministic/stochastic mate.

Never independently resample members, time steps, events, channels, or action factors.

Weight capacities 6, 8, and 12 equally.

7.14 Frozen first-match table
Priority	Terminal branch	Exact predicate
1	INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_CHANNEL_SCALE_ATTRIBUTION_G44	Any provenance, graph, centering, normalization-unit, shadow-dependency, norm-match, liveness, activation, zero/cancellation, optimizer, RNG, source-trace, checkpoint, confidence, inventory, or authority invariant fails
2	SOURCE_OR_REFERENCE_ACCESS_FAILURE_G44	Operationally valid and source invalid, or the independent-scale reference confidently fails an inherited access predicate
3	POOLED_CHANNEL_SCALE_SUFFICIENT_G44	Both arms pass access and every IND-minus-POOL primary/component UCB is <=0.05
4	INDEPENDENT_CHANNEL_SCALE_ADVANTAGE_G44	Reference access passes and either POOL confidently fails or MATERIAL_INDEPENDENT_SCALE_ADVANTAGE=true
5	MIXED_UNDERPOWERED_CHANNEL_SCALE_ATTRIBUTION_G44	Every remaining valid numerical pattern

Equality rules:

absolute-floor equality             = pass
random-minus-fixed LCB = -0.05      = pass
UCB(IND-POOL) = 0.05                = noninferior pass
LCB(IND-POOL) > 0.05                = strict advantage
q_scale = 1e-6                      = inactive
q_direction = 1e-6                  = inactive
credit-norm error at tolerance      = pass

No scale histogram, optimizer-moment diagnostic, training curve, event stratum, or wall-clock result may rescue or relabel an earlier branch.

7.15 Evidence inventory

The G43 inventory remains the smallest defensible conclusion-bearing inventory:

three accepted-anchor replicates provide independent trained-state variation;

48 episodes provide exact 16/16/16 order and capacity-8 profile balance;

100 branch updates preserve the accepted finite-budget boundary;

the allow-listed evidence contains no precision analysis supporting a smaller inventory.

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
7.16 Complexity and wall-clock boundary
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

with zero scientific iteration cost, not a G44 result. The hard policy requires the 20-minute nonformal and eight-hour formal limits and forbids nested or horizon-growing search.

7.17 Implementation-only choices

Scientifically frozen:

provenance
normalization row unit
separate centering
independent and pooled scale laws
credit-gradient norm control
common entropy isolation
shadow dependency ceiling
zero/cancellation rules
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
native kernel organization
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

最终 actor gradient 的：

相对 channel weighting
全局 gradient magnitude

都会变化。

在 Adam 下，全局 magnitude 会改变一阶/二阶 moments、epsilon 作用和 actor/baseline 的相对学习速度。因此不匹配 actor-step scale 时，无法把结果只归因于 independent channel scaling。

G44 精确比较

Reference：

immediate 和 successor 分别中心化
分别用自己的 RMS scale
0.5 × (g_I + g_S)

POOL：

仍分别中心化
共用一个 pooled RMS scale
0.5 × (g_I + g_S)

但 POOL 的 credit-gradient 全局 norm 必须匹配其自身状态下的 independent-scale counterfactual norm。

共同 entropy gradient 不参与 rescale，baseline gradients 也完全不变。

所以 G44 真正检验的是：

immediate 和 successor 的相对独立缩放是否重要，而不是谁用了更大的 actor learning step。

Pooled scale
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

.

其中：

n=8×48=384 primitive-step rows

不能按 active agent 数重复或加权。

两条 channel 仍各自中心化；只 pooling 二阶 scale，不 pooling mean。

Treatment activation

仅使用 reference arm 的 pre-update 数据：

q_scale > 1e-6
并且
q_direction > 1e-6

每个 formal replicate 至少出现一次，才能证明处理真正改变了 matched actor direction。

仅有 s_I != s_S 不够；若两种组合的 actor direction 仍相同，实验就是 vacuous。

Claim ceiling

若 POOL 通过，只能说明：

relative independent channel scaling
在保留 independent-derived global credit norm schedule 时可删除

不能说明 independent scale shadow 已完全删除。

若 IND 获胜，只能说明该 relative scaling 在 G44-P0、当前 Adam 和有限预算下有优势。

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