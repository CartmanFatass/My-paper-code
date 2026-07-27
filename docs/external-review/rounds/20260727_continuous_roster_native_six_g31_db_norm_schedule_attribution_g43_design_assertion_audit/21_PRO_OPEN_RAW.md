1. REGISTERED_DESIGN_CONFORMANCE
REGISTERED_DESIGN_CONFORMANCE=
CONFORMS_AFTER_EXACT_SCALAR_SCHEDULE_FREEZE_BELOW

source_id=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_DB_NORM_SCHEDULE_ATTRIBUTION_G43_P0

reference_source_commit=
a6c3c2971ee74e76a453995c3a7c12627bb8f02c

design_audit_compute=0
H=48
K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false

The prerequisite scientific boundary is closed:

G42_formal_branch=
SCALE_MATCHED_NO_DIRECTION_BALANCE_SUFFICIENT_G42

accepted_post_anchor_route=
COMMON_NATIVE6_FAST_ANCHOR
→ NATIVE6_G31_RAW_SUM_SCALE_MATCHED_NO_SLOW

G42_retained_unresolved_component=
DB_DERIVED_SCALAR_GLOBAL_NORM_SCHEDULE

Formal G42 established that the direction-balanced vector direction can be replaced by the raw-sum direction while retaining the registered per-pass scalar norm. It explicitly left the scalar norm schedule unresolved and scheduled this exact G43 design audit.

The proposed G43 comparison is scientifically identifiable. At a fixed model state and stored trajectory, both arms use the same raw actor-gradient direction:

r=g
I
	​

+g
S
	​

.

They differ only in the scalar multiplying that direction:

d
DBNORM
	​

=
∥r∥
2
	​

∥d
DB
	​

∥
2
	​

	​

r

versus:

d
MEAN
	​

=
2
1
	​

r.

The actor-gradient norms therefore must not be equalized: their difference is the registered treatment. “Matched scale” in this audit means that both scalar laws are completely predeclared and every other source of gradient scaling, parameter exposure, baseline learning, optimizer state, source data, and evaluation evidence is held fixed. Equalizing the two norms would erase G43’s scientific treatment.

The fixed coefficient 1/2 is admissible because the two channels have already been formed and independently normalized; it is the literal equal-channel arithmetic mean. It is not selected from data and may not be searched, tuned, screened, or replaced after observing evidence. The question expressly freezes this coefficient and confines the claim to that exact null.

2. DESIGN_SCIENTIFIC_DISPOSITION
DESIGN_SCIENTIFIC_DISPOSITION=
IDENTIFIABLE_FIXED_EQUAL_MEAN_DB_NORM_SCHEDULE_ATTRIBUTION_G43_DESIGN
Exact arms
reference_arm=
NATIVE6_G31_RAW_SUM_DB_NORM_NO_SLOW

null_arm=
NATIVE6_G31_EQUAL_MEAN_NO_SHADOW_NO_SLOW

For each arm, update, PPO pass, and frozen actor-plus-log_std parameter order, compute the same two channel gradients:

g
I
	​

=∇
θ
	​

L
PPO
	​

(A
I
),g
S
	​

=∇
θ
	​

L
PPO
	​

(A
S
),

where:

A
t
I
	​

=r
t
	​

−stopgrad(b
I
	​

(ξ
t
	​

)),
A
t
S
	​

=G
t+1
	​

−stopgrad(b
S
	​

(ξ
t
	​

)),
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

The immediate and successor advantages retain the accepted independent channel normalization, zero-variance handling, PPO clipping, likelihood factorization, entropy semantics, active-factor denominator, and parameter order. Targets and normalized advantages are computed once from the complete real trajectory and reused across both PPO passes.

Reference schedule

Let:

r=g
I
	​

+g
S
	​

,m
DB
	​

=∥DB
G31
	​

(g
I
	​

,g
S
	​

)∥
2
	​

.

The reference arm uses:

d
DBNORM
	​

=
⎩
⎨
⎧
	​

0,
m
DB
	​

∥r∥
2
	​

r
	​

,
	​

m
DB
	​

=0,
m
DB
	​

>0 ∧ ∥r∥
2
	​

>0.
	​


The norm is computed in float64 over one frozen global flattening of actor-plus-log_std parameters. The DB vector is a pure shadow calculation: only its detached scalar norm may enter the applied reference gradient.

Equal-mean null

The null uses exactly:

d
MEAN
	​

=
2
1
	​

(g
I
	​

+g
S
	​

)
	​


with the same fixed global parameter order.

It performs:

DB_vector_reads=0
DB_norm_reads=0
DB_composer_calls=0
DB_shadow_computation=0
learned_or_tunable_channel_weights=0

The 1/2 coefficient is a literal constant. It may not be replaced by a learning rate, scheduler, empirical mean norm, running statistic, fitted scale, per-group coefficient, or selected candidate.

What G43 identifies

The treatment is:

DB-derived dynamic scalar coefficient
versus
fixed equal-channel coefficient 1/2

while preserving the same raw-sum direction.

A positive reduction branch may support only:

Under G43-P0, the DB-derived scalar global-norm schedule is removable in favor of the fixed equal-channel mean.

A positive reference-schedule branch may support only:

Under the frozen anchors, source, Adam state evolution, and finite branch budget, the DB-derived scalar norm schedule supplies an access or material-utility advantage over the exact 1/2 equal-channel mean.

A reference-schedule advantage must be described as an optimizer-scale or actor-to-baseline learning-geometry effect. It may not be relabelled as evidence that angular conflict resolution is necessary: G42 already failed-closed that exact angular claim.

Retained, deleted, and added objects
Object	G43 treatment
Accepted G40 common fast anchors	Retain read-only
G41 no-slow projection	Retain exactly
Native-six actor and log_std	Retain exactly
Immediate and realized-successor targets	Retain exactly
Shared true-state two-output baseline	Retain exactly
Independent channel normalization	Retain exactly
PPO and likelihood semantics	Retain exactly
Actor/head parameter inventory	Retain exactly
Adam hyperparameters and step count	Retain exactly
Raw-sum actor-gradient direction	Same in both formulas
DB-derived scalar norm schedule	Reference treatment
Fixed coefficient 1/2	Null treatment
Trainable parameters	Add none
Observation, reward, source, or checkpoint field	Add none
Standalone slow critic	Absent in both arms
3. IDENTIFICATION_FAILURES_AND_COUNTEREXAMPLES
3.1 Actor scale is the treatment

The two actor gradients are deliberately not norm-matched:

∥d
DBNORM
	​

∥
2
	​

=m
DB
	​

,
∥d
MEAN
	​

∥
2
	​

=
2
1
	​

∥g
I
	​

+g
S
	​

∥
2
	​

.

A realization that rescales d_MEAN to the DB norm, adapts its 1/2, or changes the learning rate to compensate would reproduce G42 or introduce a second schedule. It would not instantiate G43.

What must remain matched is:

gradient direction before scalar multiplication
channel targets and normalization
actor/head graph
baseline gradients
optimizer hyperparameters
optimizer-step exposure
source and trajectory law
evaluation and confidence unit
3.2 The equal mean is one exact null, not all simple schedules

A failure of 1/2(g_I+g_S) would not establish that every no-shadow scalar law fails. Alternatives such as another fixed coefficient, a source-independent scheduler, or a non-DB running scale remain scientifically distinct and are not rescued or rejected by G43.

Conversely, an equal-mean pass supports deletion only relative to this exact reference schedule and finite budget.

3.3 Adam makes scalar history causally meaningful

Under Adam, a time-varying scalar affects:

first moments;

second moments;

the role of optimizer epsilon;

subsequent coordinatewise parameter changes;

the actor-to-shared-baseline learning-rate ratio.

This is not a nuisance to match away. It is the mechanism G43 tests. A positive DB-norm result therefore supports a finite-budget optimization schedule, not an information or policy-capacity advantage.

No post-Adam parameter-delta matching is permitted. Such matching would add an optimizer-dependent controller and erase the registered scalar-schedule treatment.

3.4 Zero and cancellation semantics

For finite g
I
	​

,g
S
	​

, define:

r=g
I
	​

+g
S
	​

.

Freeze these cases:

Condition	Reference arm	Equal-mean arm	Disposition
m
DB
	​

=0, r

=0	Exact zero actor gradient	r/2	Valid, maximally active scalar treatment
m
DB
	​

=0, r=0	Exact zero	Exact zero	Valid but treatment inactive for this pass
m
DB
	​

>0, ∥r∥=0	Undefined accepted formula	Zero	INVALID before either optimizer step
Nonfinite channel, raw sum, norm, scale, or assigned gradient	—	—	INVALID before either optimizer step

A zero actor gradient does not skip learning exposure. Both actor/head Adam optimizers advance exactly once per PPO pass, the shared-baseline losses still update, and no stale gradient may survive. Adam momentum may still move actor parameters after a zero current gradient; that is part of the frozen optimizer semantics.

3.5 Treatment-vacuity gate

Define:

m
MEAN
	​

=
2
1
	​

∥r∥
2
	​

.

For the reference arm’s pre-update state, define the relative schedule difference:

q=
⎩
⎨
⎧
	​

0,
max(m
DB
	​

,m
MEAN
	​

)
∣m
DB
	​

−m
MEAN
	​

∣
	​

,
	​

m
DB
	​

=m
MEAN
	​

=0,
otherwise.
	​


Every valid reference-arm PPO-pass record must serialize:

db_norm
raw_sum_norm
equal_mean_norm
dbnorm_scale
relative_schedule_difference=q
zero_db_norm
zero_raw_sum

Required activation:

nonformal:
    at least one valid q > 1e-6

formal:
    at least one valid q > 1e-6
    in each accepted-anchor replicate 0, 1, and 2

If a formal replicate never activates the scalar treatment, the package is operationally invalid. It may not support schedule removability merely because the two formulas happened to coincide.

The null path itself may not compute m
DB
	​

 to satisfy this gate. Treatment activation is reconstructed from the reference-arm evidence.

3.6 Channel and baseline liveness

For every PPO pass in both arms:

||g_I||_2 > 1e-12
||g_S||_2 > 1e-12
all channel-gradient values finite

exact registered actor-group inventory present
every actor group finite in both channel rows
every actor group live in at least one channel

immediate-baseline output gradient finite and >1e-12
successor-baseline output gradient finite and >1e-12

A globally live raw sum may not conceal an actor group dead in both channels. A live actor may not conceal a dead baseline output.

3.7 Baseline-learning mismatch

The scalar treatment applies only to actor-plus-log_std gradients.

The immediate and successor baseline:

targets;

losses;

gradients;

parameter order;

optimizer group;

Adam steps

remain unchanged. No global gradient clipping, cross-parameter normalization, or joint norm operation may allow the actor scalar to directly rescale baseline gradients.

On the first paired branch batch, before either arm updates:

channel_gradients_between_arms=bitwise_equal
baseline_gradients_between_arms=bitwise_equal
baseline_parameters=bitwise_equal
baseline_Adam_state=bitwise_equal

After the actor policies diverge, later baseline differences caused through different real trajectories are legitimate downstream treatment effects.

3.8 Shadow-computation leakage

The reference arm may calculate the DB vector only to obtain its scalar norm. That calculation must:

consume_no_RNG=true
create_no_optimizer_state=true
mutate_no_model_or_buffer=true
write_no_gradient_into_parameters=true
affect_no_checkpoint_selection=true
affect_no_evaluation_metric=true

The equal-mean arm must have no reachable code path to the DB composer, its norm, a serialized DB scale, or a hidden proxy. A lower wall-clock cost in the mean arm is descriptive only and cannot enter the branch selector.

3.9 Paired-source and update-order confounding

Both complete branch trajectories must be materialized and validated before either arm updates. The arms share:

accepted anchor
episode identities
source ledgers
membership/process signatures
member-owned action-noise tensors
evaluation ledgers
evaluation action noise
bootstrap plan

Model tensors and Adam states remain arm-owned and storage-disjoint. A proof-sized order-swap guard must show that executing the reference update first cannot alter the null’s stored input, RNG, targets, or initial optimizer state.

3.10 Common-anchor and source limits

G43 begins from accepted G40 fast anchors. It does not identify:

the necessity of that fast phase;

performance from random initialization;

another branch-update budget;

another optimizer;

another source family.

Formal G42 was bounded to H=48, capacities 6|8|12, and the registered fixed plus bounded-random process family. G43 inherits exactly that domain.

3.11 Other retained G31 components

Both arms retain:

realized-successor target
immediate/successor decomposition
shared-baseline conditioning
true-current-state baseline inputs
per-channel normalization
common fast anchor

Neither G43 outcome may attribute necessity or redundancy to any of them.

3.12 Smallest branch witnesses
Outcome	Smallest valid witness
Invalid	Mean path reads DB state; coefficient differs from literal 1/2; nonfinite gradients; accepted positive-norm/raw-sum cancellation; dead actor/baseline group; treatment inactive in a required replicate; unequal optimizer exposure
Source/reference failure	Source invalid, or the accepted DBNORM reference arm confidently fails an inherited absolute-access predicate
Equal-mean sufficiency	Both arms access and every DBNORM-minus-MEAN primary/component UCB is <=0.05
DB-norm advantage	Reference arm accesses and MEAN confidently fails, or pooled LCB is >0.05 with every capacity-specific primary LCB >0
Mixed/underpowered	Every remaining valid numerical pattern
4. CDC_PORTFOLIO_LEDGER_EDITS

This is a zero-compute design freeze. It changes no scientific status.

CONJECTURES.md
EDIT=NONE

G42 already records that angular direction balancing is locally removable while the DB-derived scalar norm schedule and the other G31 components remain open. G43 has produced no result evidence yet.

RESEARCH_DIRECTION_LEDGER.md
STATUS_EDIT=NONE

Retain:

DB_derived_scalar_norm_schedule=OPEN_UNTESTED

The mechanically narrowed wording may be:

Markdown
| G42 accepted raw-sum branch 中 DB-derived scalar global-norm schedule 的局部必要性 | `OPEN_UNTESTED` | 在相同 accepted anchors、G41 no-slow projection、raw-sum direction、G31 targets、shared baseline、channel normalization、source 与 Adam exposure 下，比较 DB-derived norm schedule 与 literal `0.5*(g_I+g_S)`。 | G43 design 已冻结；尚无 conclusion-bearing result。 |

The ledger already records G42’s retained scalar schedule and schedules this exact G43 audit.

IDEA_PORTFOLIO.md
SCIENTIFIC_ROW_EDIT=NONE

After mechanical archival only:

completed_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_DB_NORM_SCHEDULE_ATTRIBUTION_G43_DESIGN_ASSERTION_AUDIT

design_disposition=
IDENTIFIABLE_FIXED_EQUAL_MEAN_DB_NORM_SCHEDULE_ATTRIBUTION_G43_DESIGN

valid_result_disposition=CONTINUE

next_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_DB_NORM_SCHEDULE_ATTRIBUTION_G43_CODE_SCIENCE_ALIGNMENT_AUDIT

conclusion_bearing_iterations_consumed=32
iterations_remaining=5
CURRENT_WORK.md
last_completed_assignment_id=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_DB_NORM_SCHEDULE_ATTRIBUTION_G43_DESIGN_ASSERTION_AUDIT

active_assignment_id=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_DB_NORM_SCHEDULE_ATTRIBUTION_G43_CODE_SCIENCE_ALIGNMENT_AUDIT

next_boundary=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_DB_NORM_SCHEDULE_ATTRIBUTION_G43_CODE_SCIENCE_ALIGNMENT_AUDIT

g43_design_disposition=
IDENTIFIABLE_FIXED_EQUAL_MEAN_DB_NORM_SCHEDULE_ATTRIBUTION_G43_DESIGN

g43_reference_arm=
NATIVE6_G31_RAW_SUM_DB_NORM_NO_SLOW

g43_null_arm=
NATIVE6_G31_EQUAL_MEAN_NO_SHADOW_NO_SLOW

g43_primary_treatment=
DB_derived_dynamic_global_norm_vs_literal_equal_channel_mean_one_half

g43_design_compute=0
conclusion_bearing_iterations_consumed=32
iterations_remaining=5

The current active record confirms that G42 consumed iteration 32, left five conclusion-bearing iterations, and selected this G43 design boundary.

ALGORITHM_PRINCIPLES.md
EDIT=NONE

G43 applies the existing matched-comparator, one-action-at-a-time, and replacement-before-accumulation rules. It does not establish a new cross-experiment principle.

5. DESIGN_VALID_DISPOSITION
DESIGN_VALID_DISPOSITION=CONTINUE

conclusion_bearing_iteration_cost=0
conclusion_bearing_iterations_consumed=32
remaining_conclusion_bearing_iterations=5

The G43 comparison is identifying under the exact scalar-only contract above. The active balance is not exhausted, and this exact in-scope candidate remains executable beneath the evidence ceiling.

The preserved portfolio is unchanged:

Direction	State after G43 design audit
DB-derived scalar norm schedule	Live; G43 realization/audit scheduled
Realized-successor target attribution	Live, unscheduled
Immediate/successor decomposition	Live, unscheduled
Shared-baseline conditioning	Live, unscheduled
Per-channel normalization	Live, unscheduled
Common fast-anchor simplification	Live, unscheduled
Broader process/horizon/capacity	Live, unscheduled
Identifiable non-G33 UAV transport	Parked behind source identifiability
Recurrence/EHC	Parked behind a genuinely hidden-information source
C-BASE/C-COORD	Live outside this local reduction
Asynchronous skill lifetime/intrinsic reward	OUT_OF_SCOPE_FROZEN
G33 lineage	Permanently frozen

Scheduling G43 does not make scalar scheduling the unique scientific direction and retires none of the unselected portfolio. External Pro must preserve those directions while scheduling one resource-consuming action.

6. CURRENT_SCHEDULED_ACTION_IF_CONTINUE
current_scheduled_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_DB_NORM_SCHEDULE_ATTRIBUTION_G43_CODE_SCIENCE_ALIGNMENT_AUDIT

This boundary becomes eligible only after Code Project Manager independently realizes and technically accepts one exact pushed implementation of the G43 contract.

Its sole scientific question will be:

Does the accepted realization preserve the exact G42 scale-matched raw-sum reference, instantiate the literal no-shadow 0.5(g_I+g_S) arm, change no other graph, target, baseline, optimizer, source, exposure, evidence, or confidence field, and fail closed on zero/cancellation, dead-gradient, provenance, treatment-vacuity, and hidden-DB-dependency paths?

This response does not authorize realization, Git activity, proof execution, nonformal compute, or formal compute.

7. EXECUTABLE_DESIGN_BOUNDARY
7.1 Provenance and branch start

Freeze:

accepted_G40_anchor_replicates=0|1|2
accepted_G40_source_commit=97a8b237e0cec6c2713dd2a710d324040fa3dfc2
accepted_G41_projection_source_commit=a5f63c349228fc2bba7843647e0ae4c34361c1c9
accepted_G42_reference_source_commit=a6c3c2971ee74e76a453995c3a7c12627bb8f02c
accepted_G42_aligned_source_commit=6b8ea82d8fdbc76c14a414ff2b042a126f945dfb
accepted_G42_alignment_stage=309858dca06af66f13857f94773bcef37527d821

For each replicate:

Strict-validate the accepted G40 manifest entry and complete anchor digest.

Apply the accepted G41 no-slow projection.

Clone retained state bitwise into the DBNORM and MEAN arms.

Create empty, separate actor/head Adam states.

Require zero shared parameter, buffer, gradient, or optimizer storage.

Consume no model RNG during projection.

Both arms contain exactly:

native-six actor
log_std
shared immediate/successor two-output baseline
no learned actor carry
no standalone slow critic

Semantic keys, tensor shapes, trainable masks, parameter counts, initial bytes, and optimizer parameter order must match.

7.2 Channel construction

For every complete real branch trajectory:

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

,S
t
	​

=G
t+1
	​

.

Then:

A
t
I
	​

=r
t
	​

−stopgrad(b
I
	​

(ξ
t
	​

)),
A
t
S
	​

=S
t
	​

−stopgrad(b
S
	​

(ξ
t
	​

)).

Each channel is normalized once before both PPO passes. No target, baseline prediction, or normalized advantage is recomputed between passes.

The two complete actor-plus-log_std channel gradients are generated separately:

g
I
	​

,g
S
	​

.

Shared-baseline losses remain outside the actor-gradient composition.

7.3 Exact assigned gradients
DBNORM arm
r = g_I + g_S
d_DB = exact registered G31 direction-balanced composition
m_DB = float64_global_norm(d_DB)

Then apply the inherited G42 rule:

m_DB == 0:
    assigned_actor_gradient = exact_zero

m_DB > 0 and ||r|| > 0:
    assigned_actor_gradient = m_DB * r / ||r||

m_DB > 0 and ||r|| == 0:
    INVALID before optimizer step

The applied norm must satisfy the inherited tolerance:

∣∥d
DBNORM
	​

∥
2
	​

−m
DB
	​

∣≤10
−8
+10
−6
∣m
DB
	​

∣.
MEAN arm

Use exactly:

r = g_I + g_S
assigned_actor_gradient = 0.5 * r

Required invariants:

literal_coefficient=0.5
coefficient_trainable=false
coefficient_configurable=false
coefficient_search_count=0

DB_vector_read_count=0
DB_norm_read_count=0
DB_composer_call_count=0
shadow_DB_state_count=0
fallback_channel_count=0
per_group_scale_count=0

The mean gradient must equal the frozen fixed-order 0.5*(g_I+g_S) construction bitwise, or under one predeclared proof-sized finite tolerance if bitwise equality is impossible on the accepted CPU kernel.

7.4 Initial equality and direct-treatment audit

On the first paired branch batch, before either arm updates:

actor_and_log_std_bytes_equal=true
shared_baseline_bytes_equal=true
actor_head_Adam_states_empty_and_separate=true
stored_trajectory_identity_equal=true

g_I_between_arms=bitwise_equal
g_S_between_arms=bitwise_equal
baseline_gradients_between_arms=bitwise_equal

At that point:

d
DBNORM
	​

∥d
MEAN
	​

∥g
I
	​

+g
S
	​


whenever the relevant vector is nonzero. Any non-collinearity is operational invalidity because it means a second directional treatment entered G43.

7.5 Gradient and schedule-activation evidence

Every PPO-pass record must bind:

exact registered actor-group inventory
global immediate-channel norm
global successor-channel norm
per-group immediate/successor norms and finiteness
immediate-baseline output gradient
successor-baseline output gradient
raw-sum norm
DB-derived norm
equal-mean norm
DBNORM assigned norm
MEAN assigned norm
relative_schedule_difference
all zero/cancellation flags
absence of DB dependency in MEAN

Define:

q=
max(m
DB
	​

,
2
1
	​

∥r∥
2
	​

)
∣m
DB
	​

−
2
1
	​

∥r∥
2
	​

∣
	​


when the denominator is positive; otherwise record undefined_noncounting_zero_step.

Conclusion evidence requires:

nonformal:
    at least one q > 1e-6

formal:
    at least one q > 1e-6
    in each replicate 0|1|2

A serialized pass flag is insufficient; the analyzer must reconstruct the gate from every update record.

7.6 Optimizer exposure

In both arms, preserve the accepted G42 actor/head optimizer:

same optimizer class and hyperparameters
same parameter groups and order
same branch updates
same PPO passes
one actor/head Adam step per PPO pass
no optimizer reset within the branch
no gradient clipping or new cross-parameter norm operation

The scalar schedule affects actor-plus-log_std gradients only. Immediate- and successor-baseline gradients are assigned unchanged.

At a registered zero actor-gradient pass:

actor_gradient_tensors=exact_zero
baseline_gradients=retained
Adam_step_exposure=retained
stale_gradient_reuse=forbidden
7.7 Seed ownership and paired training

Freeze:

branch_ledger_seed_base=10431000
branch_action_seed_base=10432000
branch_gradient_probe_seed_base=10433000

evaluation_base_ledger_seed_base=10434000
evaluation_process_seed_base=10435000
evaluation_action_seed_base=10436000

bootstrap_seed=10437043
nonformal_seed_offset=900000

For formal replicate r, add r once to each nonbootstrap base. For nonformal work, add 900000 to every seed, including the bootstrap seed.

Shared across arms:

anchor identity
episode identity
source ledger
membership process
member-owned action noise
evaluation ledger
evaluation action noise
bootstrap plan

Arm-owned:

model state after clone
actor/head Adam state

Per arm and replicate:

branch_updates=100
environments_per_update=8
PPO_passes=2
checkpoint_selection=final_only
episode_exclusions=none

Both complete trajectories are materialized and validated before either update. Freeze branch execution order as:

DBNORM then MEAN

after paired collection, with one proof-sized order-swap guard.

7.8 Evaluation cells and source support

For every arm, replicate, and capacity 6|8|12, evaluate:

FINAL_FIXED_DET
FINAL_FIXED_STOCH
FINAL_RANDOM_DET
FINAL_RANDOM_STOCH

No zero or anchor cell is added.

Formal support per replicate/capacity:

episodes_per_cell=48
unique_random_time_tuples=48
LRJT=16
LJRT=16
JLRT=16

At capacity 8, the three registered process profiles also occur 16/16/16.

Evaluation performs zero optimizer steps and fails closed on checkpoint, source, episode, trace, lifecycle, action-noise, or cell mismatch.

7.9 Absolute-access predicates

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

7.10 Primary and component estimands

For paired final random-deterministic episodes:

Δ
norm,C,r,e
	​

=U
C,r,e
DBNORM
	​

−U
C,r,e
MEAN
	​

.

Primary:

Δ
norm
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
norm,C,r,e
	​

]
	​


Positive values favor the DB-derived scalar schedule.

Freeze:

materiality_and_noninferiority_margin=0.05

Registered component contrasts:

fixed deterministic utility, per capacity;

random deterministic utility, per capacity;

fixed stochastic utility, equal-capacity pooled;

random stochastic utility, equal-capacity pooled;

random event-window utility, per capacity;

random process-segment utility, per capacity;

random-minus-fixed transport, per capacity.

MEAN_NONINFERIOR requires every primary and component UCB to be <=0.05.

MATERIAL_DBNORM_ADVANTAGE requires:

LCB
95
	​

(Δ
norm
	​

)>0.05

and:

LCB
95
	​

(Δ
norm,C
	​

)>0∀C∈{6,8,12}.
7.11 Confidence construction

Freeze:

bootstrap_seed=10437043
nonformal_resamples=250
formal_resamples=10000
confidence_interval=95_percentile
episode_exclusions=none

Use one hierarchical paired plan for all absolute and comparative quantities:

Resample the three accepted-anchor replicate blocks.

Within each selected replicate and capacity, resample all 48 whole episode IDs.

Retain both arms and every fixed/random and deterministic/stochastic mate.

Never independently resample members, time steps, events, gradient channels, or action factors.

Weight capacities 6, 8, and 12 equally.

7.12 Frozen first-match table
Priority	Terminal branch	Exact predicate
1	INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_DB_NORM_ATTRIBUTION_G43	Any provenance, graph, no-shadow dependency, coefficient, gradient, liveness, scalar-treatment activation, zero/cancellation, optimizer, RNG, source-trace, checkpoint, confidence, inventory, or authority invariant fails
2	SOURCE_OR_REFERENCE_ACCESS_FAILURE_G43	Operationally valid and source invalid, or the accepted DBNORM reference arm confidently fails absolute access
3	EQUAL_MEAN_RAW_SUM_SUFFICIENT_G43	Reference access passes, MEAN access passes, and every DBNORM-minus-MEAN primary/component UCB is <=0.05
4	DB_DERIVED_NORM_SCHEDULE_ADVANTAGE_G43	Reference access passes and either MEAN confidently fails or MATERIAL_DBNORM_ADVANTAGE=true
5	MIXED_UNDERPOWERED_DB_NORM_ATTRIBUTION_G43	Every remaining valid numerical pattern

Equality semantics:

absolute-floor equality               = pass
random-minus-fixed LCB = -0.05        = pass
UCB(DBNORM-MEAN) = 0.05               = noninferior pass
LCB(DBNORM-MEAN) > 0.05               = strict advantage
relative schedule difference = 1e-6  = inactive

No scale histogram, Adam moment diagnostic, training curve, event stratum, or wall-clock result may rescue or relabel an earlier branch.

7.13 Smallest evidence inventory

The G42 inventory remains the smallest defensible conclusion-bearing inventory:

48 episodes preserve exact 16/16/16 process-order and capacity-8 profile balance.

Three accepted-anchor replicates are the unit of independent trained-state variation.

The accepted finite-budget route uses 100 branch updates; reducing that number would change the G42-derived training-budget boundary rather than merely reduce evidence volume.

The allow-listed evidence contains no precision result that justifies fewer episodes or replicates. G42 used the same inventory for its valid component-attribution conclusion.

Nonformal
accepted_anchor_replicates=1
branch_updates_per_arm=10
environments_per_update=8
PPO_passes=2

evaluation_arms=2
capacities=3
cells_per_arm_capacity=4
episodes_per_cell=6
bootstrap_resamples=250
training_transitions=7680
evaluation_transitions=6912
total_real_transitions=14592
optimizer_steps=40
Formal
accepted_anchor_replicates=3
branch_updates_per_arm=100
environments_per_update=8
PPO_passes=2

evaluation_cells=72
episodes_per_cell=48
bootstrap_resamples=10000
training_transitions=230400
evaluation_transitions=165888
total_real_transitions=396288
optimizer_steps=1200
7.14 Complexity and wall-clock boundary
H=48
K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
per_episode_complexity=O(H)

nonformal_wall_clock<=1200_seconds
formal_wall_clock<=28800_seconds

Freeze the same conservative projection:

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

with zero scientific iteration cost. It is not a G43 schedule result. The evidence policy requires these 20-minute and eight-hour ceilings and forbids nested or horizon-growing search.

7.15 Scientific versus implementation-only choices

Scientifically frozen:

provenance
branch graphs
literal coefficient 1/2
absence of DB shadow in MEAN
channel construction
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
batching/vectorization
serialization layout
telemetry organization
CPU kernel organization
proof-test file placement
execution order after paired collection, subject to the frozen order-swap invariant
8. 中文简报
G43设计裁决=
IDENTIFIABLE_FIXED_EQUAL_MEAN_DB_NORM_SCHEDULE_ATTRIBUTION_G43_DESIGN

DESIGN_VALID_DISPOSITION=CONTINUE

本轮结论性迭代成本=0
已消耗结论性轮次=32
剩余结论性轮次=5
G43 真正比较什么

G42 已经证明：

DB 的向量方向重排可以删除

但 G42 的 accepted route 仍然运行 DB operator，以取得每一步的标量范数：

m
DB
	​

=∥d
DB
	​

∥
2
	​

.

G43 比较：

reference:
    raw-sum direction × DB-derived scalar norm

null:
    0.5 × (immediate gradient + successor gradient)
    不读取 DB vector
    不读取 DB norm
    不运行 DB shadow

两臂方向相同；唯一 treatment 是 actor gradient 的标量 schedule。

不能再把两臂 norm 匹配，因为 norm 差异就是 G43 要检验的对象。

零梯度和抵消
DB norm=0, raw sum!=0:
    reference actor gradient=0
    MEAN actor gradient=0.5*raw_sum
    有效 treatment

DB norm=0, raw sum=0:
    两臂 actor gradient 都为0
    当前 pass 不计 treatment activation

DB norm>0, raw sum=0:
    accepted formula 无法定义
    optimizer step 前 INVALID

即使 actor 当前 gradient 为零，也必须继续 baseline 更新和 Adam step exposure。

Treatment activation

每个 formal replicate 至少要有一次：

max(m
DB
	​

,0.5∥g
I
	​

+g
S
	​

∥)
∣m
DB
	​

−0.5∥g
I
	​

+g
S
	​

∥∣
	​

>10
−6
.

否则该 replicate 的 scalar treatment 实际未发生，整个 conclusion package 进入 INVALID，不能把“没有处理差异”解释为 schedule 可删除。

正式分支
1 INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_DB_NORM_ATTRIBUTION_G43
2 SOURCE_OR_REFERENCE_ACCESS_FAILURE_G43
3 EQUAL_MEAN_RAW_SUM_SUFFICIENT_G43
4 DB_DERIVED_NORM_SCHEDULE_ADVANTAGE_G43
5 MIXED_UNDERPOWERED_DB_NORM_ATTRIBUTION_G43

主估计量：

Δ
norm
	​

=U
DBNORM
	​

−U
MEAN
	​

.

margin：

0.05
最小证据上限
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

CONTINUOUS_ROSTER_NATIVE_SIX_G31_DB_NORM_SCHEDULE_ATTRIBUTION_G43_CODE_SCIENCE_ALIGNMENT_AUDIT

其他 G31 components、common fast anchor、broader process/horizon/capacity、可识别非 G33 UAV、recurrence/EHC 等方向继续保持 live 或 parked。G33 永久冻结。本裁决不授权实现、Git、nonformal 或 formal compute。
