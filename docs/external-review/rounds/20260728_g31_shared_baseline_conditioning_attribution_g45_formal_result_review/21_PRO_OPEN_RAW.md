1. REGISTERED_RESULT_CONFORMANCE
REGISTERED_FORMAL_BRANCH=
SHADOW_BASELINE_NO_ACTOR_READ_SUFFICIENT_G45

scientific_acceptance=ACCEPT
valid_iteration_cost=1

formal_source_commit=
d2502f4d1732601aa1249a1df7627690d51a9954

aligned_source_commit=
a42da997712d9c941ac9a6ca08992f4c5de033a2

alignment_stage_commit=
40840069c4cfe0baad67e2800d13bbee872844b0

The registered branch is accepted without rescue, downgrade, or relabelling.

The formal package is mechanically complete and target-bound:

formal=true
status=COMPLETE
operational_valid=true
operational_errors=[]
source_valid=true

backend=ContinuousRosterToyBatch_CPU_CPP
python_fallback=false
process_workers=2
native_threads_per_worker=1
torch_threads_per_worker=1

replicates=3
arms=2
branch_updates_per_arm_per_replicate=100
PPO_passes=2

training_transitions=230400
evaluation_transitions=165888
total_real_transitions=396288
optimizer_steps=1200

evaluation_cells=72
episodes_per_cell=48
bootstrap_resamples=10000

K_search=0
hypothetical_transitions=0
checkpoint_selection=final_only

The source commit, repaired aligned implementation, alignment stage, same-source preflight, authorization boundary, final-only checkpoints, and formal artifact digests are bound in the review package. The independent correction recheck is exactly AUDIT_DISPOSITION=ALIGNED.

Registered predicates
read_access_pass=true
read_access_confident_fail=false

no_read_access_pass=true
no_read_access_confident_fail=false

no_read_noninferior=true
material_baseline_conditioning_advantage=false
treatment_activation_valid=true

The primary sign convention is:

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

The primary formal CI95 is:

[−0.00307723,−0.00144968,0.00106994]
	​


The capacity-specific random-deterministic intervals are:

Capacity	READ − NO_READ CI95
6	[-0.00301949, -0.00155019, 0.00077374]
8	[-0.00409015, -0.00204845, 0.00123583]
12	[-0.00316592, -0.00067913, 0.00118761]

Both arms independently pass all fixed/random deterministic, stochastic, event-window, process-segment, transport, and minimum-replicate access predicates. Every registered comparison UCB is below the frozen 0.05 noninferiority margin; the largest displayed component UCB is below 0.008.

The treatment was not vacuous. The formal training evidence reconstructs, for all required replicates, nonzero centered baseline variation, non-collinear READ versus counterfactual NO_READ directions, and live immediate-output, successor-output, and shared-trunk baseline gradients in both arms.

2. SCIENTIFIC_DISPOSITION
SCIENTIFIC_DISPOSITION=
SUPPORTED_RETAINED_NO_BASELINE_SUBTRACTION_WITH_SHADOW_NORM_G45
Exact supported proposition

Within G45-P0, after the accepted common native-six fast anchor and G41 no-slow projection, state-conditioned subtraction of the shared true-current-state baseline outputs from the immediate and realized-successor actor-credit residuals is removable. The target-only NO_READ actor-credit direction preserves the complete fixed/random capacity-6/8/12 access contract and is noninferior by the frozen 0.05 margin when baseline target fitting, baseline optimizer exposure, and the local baseline-read counterfactual scalar credit norm are retained as matched shadow controls.

The conclusion is bounded to:

actor=native_six_no_carry
common_anchor=accepted_G40_fast_anchor
post_anchor_slow_critic=absent

credit_targets=
immediate_reward
plus
realized_successor_tail

channel_centering=separate
channel_scaling=independent_per_channel
channel_composition=literal_equal_mean_0.5

baseline_module=retained_and_shadow_trained
baseline_true_state_inputs=retained
baseline_output_read_into_actual_residual=absent_in_NO_READ
baseline_output_read_into_actual_direction=absent_in_NO_READ
baseline_read_counterfactual_scalar_norm=retained

optimizer=registered_Adam
branch_updates=100
H=48
capacities=6|8|12
source=G32_fixed_plus_G34_P0_bounded_random

The frozen design expressly distinguishes removal of baseline coordinates from the actual residual and direction from complete removal of baseline computation. NO_READ retains the same baseline module, target-fitting losses, Adam exposure, and one detached local scalar norm derived from a READ counterfactual.

Accepted post-anchor route

The retained route becomes:

COMMON_NATIVE6_FAST_ANCHOR
→ NATIVE6_G31_INDEPENDENT_SCALE_BASELINE_SHADOW_NO_READ

It retains:

realized-successor target
immediate/successor decomposition
separate channel centering
independent per-channel scaling
literal equal-channel gradient mean
shadow-trained shared two-output baseline
local baseline-read counterfactual scalar norm

It continues to delete:

standalone slow critic
slow-critic return loss and optimizer
direction-balanced vector composition
DB-derived scalar norm schedule
all DB shadow computation
baseline subtraction from the actual actor-credit residual
baseline coordinates from the actual actor-credit direction
Smallest failed-closed unit

Retire exactly:

Under G45-P0, state-conditioned subtraction of the shared true-current-state baseline outputs into the actor-credit residual or direction is required for access or supplies a material utility advantage greater than 0.05 over the exact shadow-trained, scale-matched NO_READ null.

This does not retire:

the baseline module;

its true-current-state input;

its target-fitting objective;

its local scalar norm schedule;

all action-independent baselines;

baseline conditioning under another source, optimizer, target, normalization law, or budget.

Result type

The two arms have the same actor class, observations, action distribution, reward, environment, and deployment interface. Their environment-level optimal-policy sets are therefore identical. G45 concerns a finite-sample training estimator/control-variate effect—not policy-class expressivity or execution-time access to centralized information.

3. COUNTEREXAMPLES_AND_EXCLUSIONS
3.1 NO_READ is not baseline-free

The accepted NO_READ arm still uses baseline outputs through two shadow paths:

baseline target fitting and Adam exposure
local READ-counterfactual scalar credit norm

Therefore G45 does not support:

baseline module deletion
true-state baseline-input deletion
baseline optimizer deletion
baseline checkpoint-field deletion
all centralized training information is redundant

A structural no-baseline claim requires at least one further separating boundary.

3.2 Noninferiority is not exact equality or NO_READ superiority

The pooled and capacity-specific intervals all cross zero. Their centers favor NO_READ slightly, but no superiority predicate was registered.

The accepted statement is:

baseline subtraction is materially removable under margin 0.05

not:

the two estimators are exactly equal
NO_READ is conclusively better
baseline subtraction has literally zero effect

The evidence remains compatible with a small READ benefit below approximately 0.0013 on the primary capacity contrasts, and with small diagnostic component effects below the registered materiality boundary.

3.3 Independent channel scaling may absorb much of the baseline function

G44 established that independent relative scaling is load-bearing. In G45, both arms separately center and independently RMS-normalize the immediate and successor channels. A constant baseline offset cancels exactly under centering, and much of a state-dependent amplitude effect can be removed by independent scaling.

G45 therefore does not show that action-independent baselines are generally useless. It shows that, inside the already accepted independent-scale pipeline, their state-conditioned directional subtraction adds no registered material value.

3.4 The baseline treatment was nevertheless real

The result cannot be dismissed as a vacuous constant-baseline comparison. Formal admission required:

centered baseline RMS > 1e-6
READ vs reference NO_READ direction distance > 1e-6
positive finite credit norms
one active pass in each replicate 0|1|2

Named immediate-output, successor-output, and shared-trunk gradients were also live.

3.5 The scalar norm schedule remains unresolved

The NO_READ direction is rescaled to the norm of its own local baseline-conditioned counterfactual. Thus a baseline-dependent scalar learning-rate schedule remains in the actor-credit path.

A source-local advantage could still be carried entirely by:

m
B
	​

=∥v
READ-counterfactual
	​

∥
2
	​

,

even though the corresponding baseline-conditioned vector direction is unnecessary.

G45 does not identify whether that scalar schedule is removable.

3.6 Prior boundaries remain intact

G31: realized-future-tail credit remains supported on the exact paired G17/G18 source.

G40: the complete G31 branch remains materially superior to the exact TEAM-GAE1 null after the common anchor.

G41: the standalone post-anchor slow critic remains exactly removable.

G42: DB angular reorientation remains removable under its exact scale-matched comparator.

G43: the DB-derived scalar norm remains removable in favor of the literal equal mean.

G44: independent relative channel scaling remains load-bearing against the exact globally norm-matched pooled-scale null.

G45: only baseline subtraction into the actual actor-credit residual/direction is additionally removed.

G45 does not show that TEAM-GAE1 would succeed if supplied with another baseline, nor does it rewrite the G17/G18 evidence.

3.7 Source, process, capacity, and horizon remain bounded

The result remains restricted to:

H=48
configured capacities=6|8|12
G32 capacity-8 fixed training source
G34-P0 bounded fixed/random evaluation family
one each of L/R/J/T
three registered event orders
accepted common anchors
registered Adam and finite branch budget

It does not establish arbitrary:

active count or configured capacity;

within-trajectory maximum-capacity changes;

event count, type, spacing, or ordering;

repeated unbounded leave/rejoin;

roster-process law;

horizon;

optimizer or update budget.

3.8 History, recurrence, and UAV exclusions

Both arms use the same native-six current-state, no-carry actor. G45 supplies no new evidence about recurrence on partially observed sources.

It also contains no UAV evidence. UAV G1/G2 remain source-non-identifiable; identifiable non-G33 UAV transport remains parked behind a feasible and load-bearing source; G33 remains permanently frozen. The current portfolio explicitly preserves those boundaries.

4. CDC_PORTFOLIO_LEDGER_EDITS
CONJECTURES.md

Replace the C-CONTINUOUS-ROSTER status line with:

Markdown
- Status: supported and retained at G45 as a usable native-six-coordinate,
  no-carry, post-anchor no-slow/no-DB, literal-equal-mean,
  independent-channel-scale, shadow-baseline/no-actor-read G31-credit,
  configured-capacity bounded-random-process continuous-roster test version
  for the registered H=48, capacity-6/8/12 toy family.

Insert after the G44 evidence paragraph:

Markdown
- Formal shared-baseline-conditioning evidence: G45 compares the accepted
  baseline-conditioned READ actor-credit direction against a shadow-trained
  NO_READ arm that uses target-only immediate/successor residuals while
  retaining the same baseline module, losses, Adam exposure and one local
  READ-counterfactual scalar norm. Both arms pass all absolute-access gates.
  READ-minus-NO_READ pooled CI95 is
  [-0.00307723, -0.00144968, 0.00106994]; capacity-6/8/12 UCBs are
  0.00077374, 0.00123583 and 0.00118761. NO_READ noninferiority holds,
  treatment activation is valid and material baseline-conditioning advantage
  is false.

Replace the accepted post-anchor boundary with:

Markdown
- Accepted post-anchor training boundary:
  `COMMON_NATIVE6_FAST_ANCHOR →
  NATIVE6_G31_INDEPENDENT_SCALE_BASELINE_SHADOW_NO_READ`.
  Retain realized-successor/immediate decomposition, separate centering,
  independent per-channel scaling, literal equal-channel composition,
  shadow-baseline target fitting and the local baseline-read counterfactual
  scalar norm. Delete baseline subtraction from the actual actor-credit
  residual and baseline coordinates from the actual actor-credit direction.

Append to the retired-alternatives paragraph:

Markdown
- G45 local closure: shared true-current-state baseline subtraction into the
  actor-credit residual/direction is neither access-required nor materially
  advantageous by more than 0.05 over the exact shadow-trained, locally
  norm-matched NO_READ null. This does not close the baseline module,
  true-state baseline inputs, target fitting or the baseline-derived scalar
  norm schedule.

Replace the strongest remaining training-explanations paragraph with:

Markdown
- Strongest remaining training explanations: the accepted route still uses a
  baseline-derived local scalar norm schedule, baseline target fitting,
  realized-successor targeting, immediate/successor decomposition, separate
  centering, independent relative scaling and the common fast anchor. G45
  removes only state-conditioned baseline coordinates from the actual
  actor-credit direction.

For C-CREDIT, replace the status line with:

Markdown
- Status: supported retained on the registered G17/G18 family and shared-anchor
  G40-P0 branch, narrowed locally by G41--G45: the standalone slow critic, all
  DB composition and shared-baseline subtraction into the actor-credit
  direction are removable from the retained post-anchor route.

Append:

Markdown
- G45 update: READ and shadow-trained NO_READ both pass access.
  READ-minus-NO_READ pooled CI95 is
  [-0.00307723, -0.00144968, 0.00106994], and every registered comparison
  passes the 0.05 NO_READ-noninferiority rule. The retained local credit unit is
  realized-tail/decomposed credit, separate centering, independent scaling,
  literal equal-channel composition, and a still-unresolved shadow-baseline
  scalar norm schedule.
C-REC_EDIT=NONE
C-BASE_EDIT=NONE
C-BENCH_EDIT=NONE
C-COORD_EDIT=NONE
ALGORITHM_PRINCIPLES_EDIT=NONE

The current conjecture already records the G44 route and leaves baseline conditioning as the scheduled unresolved component; G45 updates only that smallest unit.

RESEARCH_DIRECTION_LEDGER.md

Replace the current G45 OPEN_UNTESTED block with:

g45_row=continuous-roster native-six realized-tail/decomposed credit with
independent scaling and shadow-baseline/no-actor-read post-anchor route

g45_row_status=SUPPORTED_RETAINED

g45_row_evidence=
docs/external-review/rounds/20260728_g31_shared_baseline_conditioning_attribution_g45_formal_result_review/formal_evidence/analysis_result.json
|docs/external-review/rounds/20260728_g31_shared_baseline_conditioning_attribution_g45_formal_result_review/21_PRO_OPEN_RAW.md

g45_row_claim_ceiling=registered G45-P0 only; baseline module, true-state
baseline input, target fitting and local counterfactual scalar norm remain
retained; no universal credit, recurrence, process, horizon, capacity, UAV or
G33 claim

g45_scientific_route=
COMMON_NATIVE6_FAST_ANCHOR_to_NATIVE6_G31_INDEPENDENT_SCALE_BASELINE_SHADOW_NO_READ

g45_supported_unit=
target_only_actor_credit_direction_with_shadow_baseline_norm_control

g45_failed_closed=
shared_true_state_baseline_subtraction_required_for_access_or_material_advantage_inside_G45_P0

g45_primary_ci95=[-0.00307723,-0.00144968,0.00106994]

g45_capacity_ci95_6=[-0.00301949,-0.00155019,0.00077374]
g45_capacity_ci95_8=[-0.00409015,-0.00204845,0.00123583]
g45_capacity_ci95_12=[-0.00316592,-0.00067913,0.00118761]

g45_next_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_BASELINE_SHADOW_NORM_SCHEDULE_ATTRIBUTION_G46_DESIGN_ASSERTION_AUDIT

g45_valid_result_disposition=CONTINUE
g45_conclusion_bearing_iterations_consumed=35
g45_iterations_remaining=2

Add under FAILED_CLOSED:

Markdown
| G45-P0 中 shared true-current-state baseline subtraction 对 actor-credit
direction 的 access 必要性或相对 shadow-trained NO_READ 的 >0.05 material
advantage | `FAILED_CLOSED` | READ 与 NO_READ 均通过完整 access；
READ-minus-NO_READ pooled CI95 为
[-0.00307723, -0.00144968, 0.00106994]，全部 component UCB 低于 0.008，
NO_READ noninferiority 成立，material baseline-conditioning advantage 为
false。 | “baseline module 可删除”“true-state baseline input 无用”“所有
action-independent baseline 都无效”“两臂精确相等”。 |

Add under OPEN_UNTESTED:

Markdown
| G45 accepted NO_READ route 中 baseline-derived local scalar credit-norm
schedule 的局部必要性 | `OPEN_UNTESTED` | 保持 accepted anchors、G41
no-slow projection、target-only actor residuals、realized-tail/decomposition、
separate centering、independent scaling、literal equal mean、shadow baseline
target fitting、source 与 Adam exposure 不变；比较 baseline-derived local
counterfactual norm schedule 与不读取 baseline norm 的 literal raw
equal-mean credit step。 | G45 只删除 baseline-conditioned vector direction；
scalar shadow remains. Current scheduled action is G46 design assertion audit. |

The ledger’s existing G45 row is currently OPEN_UNTESTED; this formal result is the authority that changes it.

IDEA_PORTFOLIO.md

Replace C-CONTINUOUS-ROSTER with:

Markdown
| C-CONTINUOUS-ROSTER | supported retained at G45: native-six no-carry,
post-anchor no-slow/no-DB, literal-equal-mean independent-scale,
shadow-baseline/no-actor-read G31-credit configured-capacity bounded-process
test version | G40 supports the complete G31 package; G41--G43 remove the slow
critic and DB composition; G44 retains independent channel scaling; G45 shows
READ and shadow-trained NO_READ both access, with READ-minus-NO_READ CI95
[-0.00307723, -0.00144968, 0.00106994]. | Retain
`COMMON_NATIVE6_FAST_ANCHOR →
NATIVE6_G31_INDEPENDENT_SCALE_BASELINE_SHADOW_NO_READ`. Next isolate the
remaining baseline-derived scalar norm schedule. Broader transport and
identifiable non-G33 UAV remain live or parked. |

Replace C-CREDIT with:

Markdown
| C-CREDIT | supported on G17/G18 and shared-anchor G40-P0; baseline
subtraction into actor-credit direction locally reduced by G45 | G44 retains
independent relative scaling, but G45 shows that state-conditioned baseline
coordinates need not enter the actor-credit residual or direction. The
retained local unit is realized-tail/decomposed credit, separate centering,
independent scaling, literal equal mean and a baseline-derived shadow scalar
norm schedule. | Schedule scalar-shadow attribution next. Preserve target,
decomposition, centering, common-anchor, transport and source-specific
questions separately. |

Append:

## G45 formal result update

g45_formal_branch=SHADOW_BASELINE_NO_ACTOR_READ_SUFFICIENT_G45

g45_scientific_disposition=
SUPPORTED_RETAINED_NO_BASELINE_SUBTRACTION_WITH_SHADOW_NORM_G45

g45_scientific_route=
COMMON_NATIVE6_FAST_ANCHOR_to_NATIVE6_G31_INDEPENDENT_SCALE_BASELINE_SHADOW_NO_READ

g45_failed_closed=
shared_true_state_baseline_subtraction_required_for_access_or_material_advantage_G45_P0

g45_next_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_BASELINE_SHADOW_NORM_SCHEDULE_ATTRIBUTION_G46_DESIGN_ASSERTION_AUDIT

Replace the terminal block with:

completed_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHARED_BASELINE_CONDITIONING_ATTRIBUTION_G45_FORMAL_ITERATION_35

source_family=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHARED_BASELINE_CONDITIONING_ATTRIBUTION_G45_P0

formal_disposition=
SHADOW_BASELINE_NO_ACTOR_READ_SUFFICIENT_G45

scientific_disposition=
SUPPORTED_RETAINED_NO_BASELINE_SUBTRACTION_WITH_SHADOW_NORM_G45

valid_result_disposition=CONTINUE

next_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_BASELINE_SHADOW_NORM_SCHEDULE_ATTRIBUTION_G46_DESIGN_ASSERTION_AUDIT

authorization_status=
active_twenty_iteration_toy_first_uav_promotion_chain

conclusion_bearing_iterations_consumed=35
iterations_remaining=2
CURRENT_WORK.md

Apply only the following mechanical active-state update:

last_completed_assignment_id=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHARED_BASELINE_CONDITIONING_ATTRIBUTION_G45_FORMAL_ITERATION_35_VALID

active_assignment_id=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_BASELINE_SHADOW_NORM_SCHEDULE_ATTRIBUTION_G46_DESIGN_ASSERTION_AUDIT

next_boundary=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_BASELINE_SHADOW_NORM_SCHEDULE_ATTRIBUTION_G46_DESIGN_ASSERTION_AUDIT

g45_formal_source_commit=
d2502f4d1732601aa1249a1df7627690d51a9954

g45_aligned_source_commit=
a42da997712d9c941ac9a6ca08992f4c5de033a2

g45_alignment_stage_commit=
40840069c4cfe0baad67e2800d13bbee872844b0

g45_formal_branch=
SHADOW_BASELINE_NO_ACTOR_READ_SUFFICIENT_G45

g45_scientific_disposition=
SUPPORTED_RETAINED_NO_BASELINE_SUBTRACTION_WITH_SHADOW_NORM_G45

g45_retired_unit=
shared_true_state_baseline_subtraction_required_for_access_or_material_advantage_inside_G45_P0

g45_retained_boundary=
baseline_shadow_target_fitting|
baseline_read_counterfactual_scalar_norm|
realized_successor_target|
decomposition|
separate_centering|
independent_scaling|
literal_equal_mean|
common_fast_anchor

g45_selected_successor=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_BASELINE_SHADOW_NORM_SCHEDULE_ATTRIBUTION_G46_DESIGN_ASSERTION_AUDIT

conclusion_bearing_iterations_consumed=35
iterations_remaining=2
toy_first_chain_iterations_remaining=2

No new operational file, report, principle, or authorization record is scientifically required by this disposition.

5. PORTFOLIO_DELTA_AND_VALID_RESULT_DISPOSITION
VALID_RESULT_DISPOSITION=CONTINUE

conclusion_bearing_iterations_consumed=35
remaining_conclusion_bearing_iterations=2

The balance is not exhausted, and an exact in-scope component-attribution candidate remains. Therefore neither terminal disposition applies. External Pro must schedule one action while preserving the rest of the portfolio.

Direction	State after G45	Advancement or reactivation condition
Target-only NO_READ actor-credit direction	Supported and retained	Use as current post-anchor route
Baseline subtraction into actor direction	Failed closed in G45-P0	A distinct identified source/comparator—not G45 tuning
Baseline-derived scalar norm schedule	Live; scheduled	G46 exact scalar-schedule attribution
Baseline target fitting/module structural removal	Live, not yet adjudicated	Eligible for zero-trajectory deletion proof only after scalar path is removed
Independent relative channel scaling	Supported and retained	Preserve in G46
Separate channel centering	Live, unscheduled	Hold targets, scaling, composition, and scalar schedule fixed
Realized-successor target	Live, unscheduled	Change only target authority under matched downstream processing
Immediate/successor decomposition	Live, unscheduled	Preserve information, normalization, and update scale
Common fast anchor	Live, unscheduled	Match initial function, interactions, and optimizer exposure
Broader process/horizon/capacity	Live, unscheduled	Change one source axis at a time
Identifiable non-G33 UAV transport	Parked	Feasible, load-bearing, support-valid, source-identifiable source
Recurrence/EHC	Parked	Task-relevant information absent from current observations
C-BASE/C-COORD	Live outside this reduction	Representation-fixed access or coordination separation
Asynchronous skill lifetime/intrinsic reward	OUT_OF_SCOPE_FROZEN	Later explicit scope transition
G33 lineage	Permanently frozen	No reactivation in this chain

Scheduling G46 is an attribution boundary. It does not assert that scalar scheduling is the only worthwhile scientific direction.

6. CURRENT_SCHEDULED_ACTION_IF_CONTINUE
current_scheduled_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_BASELINE_SHADOW_NORM_SCHEDULE_ATTRIBUTION_G46_DESIGN_ASSERTION_AUDIT
Scientific rationale

G45 removes the baseline-conditioned vector direction, but its successful NO_READ arm still computes a baseline-conditioned counterfactual to obtain the scalar norm of every actor-credit update.

That scalar is now the closest remaining specialized baseline path:

baseline outputs
→ local READ counterfactual
→ one detached global credit norm
→ NO_READ raw direction rescaling

Testing it next is cheaper and more discriminating than changing:

realized-successor targets;

decomposition;

separate centering;

independent scaling;

the common anchor;

the process family;

UAV source semantics.

A raw-norm sufficiency result would eliminate every baseline-output read from the actor-credit update. Because actor and baseline parameters are disjoint and baseline outputs already do not affect action generation, checkpoint selection, or evaluation, that result would make a subsequent structural baseline-module deletion eligible for a zero-trajectory dependency proof.

A positive reference result would instead identify the scalar schedule—not baseline-conditioned direction—as the remaining source-local baseline contribution.

7. EXECUTABLE_SCIENTIFIC_BOUNDARY
next_boundary=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_BASELINE_SHADOW_NORM_SCHEDULE_ATTRIBUTION_G46_DESIGN_ASSERTION_AUDIT

review_mode=DESIGN_ASSERTION_AUDIT
design_audit_compute=0
Exact G46 question

Can a conclusion-bearing matched post-anchor comparison be frozen between:

NATIVE6_G31_NO_READ_BASELINE_SHADOW_NORM — the accepted G45 route, whose actual immediate and successor residuals are target-only but whose raw equal-mean credit direction is rescaled to the norm of a local baseline-conditioned counterfactual; and

NATIVE6_G31_NO_BASELINE_ACTOR_READ_RAW_NORM — the identical target-only route using the literal unrescaled equal-mean credit gradient, with no baseline-output read into residual, direction, or scalar norm?

Both arms retain identical:

accepted G40 common fast anchors
G41 no-slow projection
native-six actor and log_std
immediate and realized-successor targets
separate channel centering
independent per-channel RMS scaling
literal 0.5*(g_I+g_S)
common entropy
baseline module and target-fitting losses
baseline parameter/Adam exposure
source ledgers and action streams
PPO passes and optimizer-step exposure
evaluation and confidence plan
final-only checkpoints

The only treatment is:

baseline-derived dynamic scalar credit-norm schedule
versus
literal raw equal-mean credit-gradient norm
Frozen actor-credit laws

For both arms, construct target-only residuals:

x
t
I
	​

=r
t
	​

,x
t
S
	​

=G
t+1
	​

,

then apply the accepted separate centering and independent scaling and form:

v
raw
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

).
Reference arm

On its own current pre-update state and trajectory, compute the detached baseline-conditioned counterfactual norm:

m
B
	​

=∥v
READ,cf
	​

∥
2
	​

.

Assign:

v
REF
	​

=
⎩
⎨
⎧
	​

0,
m
B
	​

∥v
raw
	​

∥
2
	​

v
raw
	​

	​

,
	​

m
B
	​

=0,
m
B
	​

>0∧∥v
raw
	​

∥
2
	​

>0.
	​

Raw-norm null

Assign exactly:

v
RAW
	​

=v
raw
	​

	​


with:

baseline_read_into_actual_residual=0
baseline_read_into_actual_direction=0
baseline_read_into_actual_scalar_norm=0
baseline_counterfactual_calls=0
learned_or_tunable_scale=0

Common entropy is added once after these credit-gradient rules and is never rescaled.

Zero and cancellation semantics
Condition	Reference	RAW null	Result
m
B
	​

=0,∥v
raw
	​

∥>0	Exact zero credit gradient	Raw gradient	Valid scalar treatment
m
B
	​

=0,∥v
raw
	​

∥=0	Exact zero	Exact zero	Valid but inactive
m
B
	​

>0,∥v
raw
	​

∥=0	Undefined norm-matched direction	Exact zero	INVALID before either optimizer
Any nonfinite residual, gradient, norm, or assigned row	—	—	INVALID

Zero credit gradients do not skip baseline updates, entropy, or actor/head Adam exposure.

Treatment activation

Using only the reference arm’s own pre-update state, define:

m
raw
	​

=∥v
raw
	​

∥
2
	​

,
q
norm
	​

=
⎩
⎨
⎧
	​

0,
max(m
B
	​

,m
raw
	​

)
∣m
B
	​

−m
raw
	​

∣
	​

,
	​

m
B
	​

=m
raw
	​

=0,
otherwise.
	​


Require:

nonformal:
    at least one valid q_norm > 1e-6

formal:
    at least one valid q_norm > 1e-6
    in each accepted-anchor replicate 0|1|2

When both assigned credit gradients are nonzero, their unit directions must agree under one frozen proof tolerance. Any directional discrepancy is invalid because G46 is a scalar-schedule attribution.

Primary estimand
Δ
shadow_norm
	​

=U
SHADOW_NORM
	​

−U
RAW_NORM
	​

.
materiality_and_noninferiority_margin=0.05

Positive values favor the baseline-derived scalar schedule.

Claim ceilings

A raw-norm sufficiency result may support only:

The baseline-derived scalar credit-norm schedule is removable from the actor-credit path under G46-P0 while the baseline module, target fitting, parameters, and optimizer exposure remain as matched shadow controls.

It may not yet claim structural baseline-module deletion.

A positive reference result may support only:

The local baseline-derived scalar norm schedule supplies a source-local finite-budget access or material-utility advantage over the exact literal raw-norm null.

Neither outcome may adjudicate realized-tail targeting, decomposition, separate centering, independent scaling, the common anchor, recurrence, UAV mechanisms, or G33.

Frozen first-match branches
1. INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_BASELINE_SHADOW_NORM_ATTRIBUTION_G46

2. SOURCE_OR_REFERENCE_ACCESS_FAILURE_G46

3. RAW_NO_BASELINE_SHADOW_NORM_SUFFICIENT_G46

4. BASELINE_SHADOW_NORM_SCHEDULE_ADVANTAGE_G46

5. MIXED_UNDERPOWERED_BASELINE_SHADOW_NORM_ATTRIBUTION_G46

The sufficiency branch requires both arms to pass the inherited access contract and every reference-minus-raw primary/component UCB to be <=0.05.

The advantage branch requires reference access and either confident raw-arm failure or:

LCB
95
	​

(Δ
shadow_norm
	​

)>0.05

with every capacity-specific primary LCB strictly positive.

Evidence and complexity
H=48
K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false

nonformal_real_transitions<=14592
nonformal_optimizer_steps<=40
nonformal_wall_clock<=1200_seconds

formal_real_transitions<=396288
formal_optimizer_steps<=1200
formal_wall_clock<=28800_seconds

Use the inherited three accepted-anchor replicates, exact 16/16/16 process/profile balance, 48 whole episodes per cell, one paired hierarchical confidence plan, equal capacity weighting, no exclusions, and 10,000 formal bootstrap draws unless the design audit supplies a valid smaller conclusion-bearing inventory.

This disposition authorizes no implementation, Git operation, nonformal run, or formal run.

8. 中文简报
G45正式分支=
SHADOW_BASELINE_NO_ACTOR_READ_SUFFICIENT_G45

科学裁决=
SUPPORTED_RETAINED_NO_BASELINE_SUBTRACTION_WITH_SHADOW_NORM_G45

有效结果 disposition=
CONTINUE

已消耗结论性轮次=35
剩余结论性轮次=2
G45 证明了什么

G45 比较：

READ:
    immediate / successor residual 减去 true-state baseline prediction

NO_READ:
    actual actor residual 完全不读取 baseline output
    但 baseline module 仍训练
    并保留一个 local READ-counterfactual scalar norm

两臂都通过完整 access：

READ access pass=true
NO_READ access pass=true

正式主区间：

READ - NO_READ CI95
=
[-0.00307723, -0.00144968, 0.00106994]

三个 capacity 的 UCB 均小于 0.0013，所有 component UCB 均小于 0.008，远低于 0.05 margin。

因此，在 G45-P0 中：

baseline prediction 不需要进入 actor-credit residual 或 actor-credit direction。

不能误写为
baseline module 已经可以删除
true-state baseline input 已经无用
所有 action-independent baseline 都无效
NO_READ 显著优于 READ
两臂精确相等
所有 source / optimizer 都不需要 baseline

NO_READ 仍保留：

baseline target fitting
baseline Adam exposure
baseline-derived local scalar credit norm
当前接受 route
COMMON_NATIVE6_FAST_ANCHOR
→ NATIVE6_G31_INDEPENDENT_SCALE_BASELINE_SHADOW_NO_READ

仍然保留：

realized-successor target
immediate/successor decomposition
separate centering
independent scaling
literal equal-channel mean
shadow baseline training
baseline-derived scalar norm
下一动作
CONTINUOUS_ROSTER_NATIVE_SIX_G31_BASELINE_SHADOW_NORM_SCHEDULE_ATTRIBUTION_G46_DESIGN_ASSERTION_AUDIT

G46 只比较：

reference:
    target-only NO_READ direction
    × baseline-derived local counterfactual norm

null:
    target-only NO_READ direction
    × its literal raw equal-mean norm
    baseline output 对 actor residual / direction / scalar 全部零读取

若 raw-norm null 通过，就能删除 actor-credit 路径中的最后一个 baseline-output 读取；此后 baseline module 的结构删除可进入零轨迹依赖证明。

realized-tail、decomposition、separate centering、independent scaling、common anchor、broader process/horizon/capacity、可识别非 G33 UAV 与 recurrence/EHC 等方向继续保持 live 或 parked。G33 永久冻结。本裁决不授权代码或计算。
