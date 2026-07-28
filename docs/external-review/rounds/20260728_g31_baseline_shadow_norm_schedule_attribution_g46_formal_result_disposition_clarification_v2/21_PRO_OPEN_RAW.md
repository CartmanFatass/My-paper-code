# Pro raw response

REGISTERED_RESULT_CONFORMANCE
REGISTERED_FORMAL_BRANCH=
RAW_NO_BASELINE_SHADOW_NORM_SUFFICIENT_G46

scientific_acceptance=ACCEPT
valid_iteration_cost=1

formal_source_commit=
af7d6b1f1ad55f24e25202b39414203677a7813b

aligned_source_commit=
ef3a2fa273d1506c2bc88f50db8e06810e946809

alignment_stage_commit=
d073d13317c09980863a700f6241573dd6709cdf

The registered branch is accepted without rescue, relabelling, seed expansion, threshold change, or evidence-volume change.

The formal package is mechanically complete and target-bound:

formal=true
status=COMPLETE
operational_valid=true
operational_errors=[]
alignment_disposition=ALIGNED

backend=ContinuousRosterToyBatch_CPU_CPP
python_fallback=false
process_workers=2
worker_start_method=spawn
native_and_torch_threads_per_worker=1
deterministic_merge=preassigned_index_not_completion_order

replicates=3
arms=2
branch_updates_per_arm=100
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

The exact source, aligned implementation, alignment stage, same-source preflight, final checkpoint inventory, and fixed formal inventory are bound in the evidence note and code-science index.

The registered predicates are:

source_valid=true
treatment_activation_valid=true

SHADOW_NORM_access_pass=true
SHADOW_NORM_access_confident_fail=false

RAW_NORM_access_pass=true
RAW_NORM_access_confident_fail=false

raw_noninferior=true
material_shadow_norm_advantage=false

The sign convention is:

Δ
shadow norm
	​

=U
SHADOW_NORM
	​

−U
RAW_NORM
	​

.

The primary CI95 is:

[−0.0004228799, 0.0021094173, 0.0066980410]
	​


The capacity-specific random-deterministic intervals are:

Capacity	SHADOW_NORM − RAW_NORM CI95
6	[-0.0004973679, 0.0019354286, 0.0056411082]
8	[-0.0008021310, 0.0021935522, 0.0077412759]
12	[-0.0002107238, 0.0021713662, 0.0065407719]

Both arms pass access, the registered RAW noninferiority predicate is true, treatment activation is valid, and material shadow-norm advantage is false. The first-match result is therefore exactly RAW_NO_BASELINE_SHADOW_NORM_SUFFICIENT_G46.

The earlier archived response consisted solely of AUDIT_DISPOSITION=MISMATCH; under the present user-authorized v2 fence it is a nonconforming transport artifact, not a G46 scientific disposition.

SCIENTIFIC_DISPOSITION
SCIENTIFIC_DISPOSITION=
SUPPORTED_RETAINED_RAW_NORM_NO_BASELINE_ACTOR_READ_G46
Exact supported proposition

Within G46-P0, after the accepted native-six common fast anchor and the G41 no-slow projection, the baseline-derived dynamic scalar credit-norm schedule is removable. The literal, unrescaled equal-mean credit gradient preserves the complete registered fixed/random capacity-6/8/12 access contract and is noninferior by the frozen 0.05 margin.

The result is bounded to:

actor=native_six_no_carry
common_anchor=accepted_G40_fast_anchor
standalone_slow_critic=absent

actual_actor_credit_residuals=
immediate_reward
plus
realized_successor_tail

channel_centering=separate
channel_scaling=independent_per_channel
channel_composition=literal_0.5*(g_I+g_S)

actual_actor_baseline_read_residual=0
actual_actor_baseline_read_direction=0
actual_actor_baseline_read_scalar_norm=0

baseline_module=retained_as_shadow
baseline_target_fitting=retained
baseline_optimizer_exposure=retained

optimizer=registered_Adam
branch_updates=100
H=48
capacities=6|8|12
source=G32_fixed_plus_G34_P0_bounded_random

The G46 contract binds both actual actor-credit paths to target-only residuals. The reference arm changes only the scalar norm using a local baseline-conditioned counterfactual, while the RAW arm uses the literal unrescaled 0.5*(g_I+g_S) and has zero baseline reads into residual, direction, or scalar norm.

Accepted post-anchor route

The smallest retained route is now:

COMMON_NATIVE6_FAST_ANCHOR
→ NATIVE6_G31_NO_BASELINE_ACTOR_READ_RAW_NORM

It retains:

immediate reward target
realized-successor target
immediate/successor decomposition
separate channel centering
independent per-channel RMS scaling
literal equal-channel mean
common entropy
shadow baseline target fitting

It deletes from the actual actor-credit path:

standalone slow critic
direction-balanced vector composition
DB-derived scalar norm
all DB shadow computation
baseline-conditioned residual subtraction
baseline-conditioned direction
baseline-derived scalar norm schedule
Smallest failed-closed unit

Retire exactly:

Under G46-P0, the local baseline-derived dynamic scalar credit-norm schedule is required for access or supplies a material utility advantage greater than 0.05 over the literal RAW equal-mean norm.

The formal primary UCB is approximately 0.00670, and the largest capacity-specific UCB is approximately 0.00774, both far below the registered 0.05 margin. This closes the exact scalar-schedule claim, not every possible baseline or every adaptive learning-rate schedule.

Combined implication of G45 and G46

G45 removed baseline-conditioned coordinates from the actor-credit residual and direction while retaining a scalar shadow. G46 now removes that remaining scalar influence.

Therefore, within the accepted post-anchor route:

baseline_output influence on actual actor credit=zero

The shared baseline module still exists and is still optimized, but its outputs no longer causally determine the actor’s residual, direction, scalar magnitude, action, or registered evaluation result. That makes structural deletion of the remaining shadow module a live exact-reduction question; it does not itself complete that deletion.

COUNTEREXAMPLES_AND_EXCLUSIONS
Noninferiority is not exact equality or RAW superiority

The pooled and capacity-specific intervals cross zero. G46 does not establish:

SHADOW_NORM and RAW_NORM are bitwise or statistically identical
RAW_NORM is significantly superior
the baseline-derived norm has literally zero effect

The evidence remains compatible with a small SHADOW_NORM advantage below approximately 0.00775 on the registered capacity contrasts. The correct conclusion is material removability under the 0.05 margin.

The baseline module is not yet structurally deleted

Both arms retain:

shared two-output baseline parameters
true-current-state baseline inputs
baseline target-fitting losses
baseline Adam exposure
baseline checkpoint fields

The RAW arm does not read their outputs into actor credit, but G46 did not compare a baseline-bearing graph against a graph in which the baseline module and its optimizer state were absent.

Accordingly, G46 does not yet support:

baseline module exactly removable
true-current-state baseline inputs structurally unnecessary
baseline optimizer and checkpoint keys deletable
all centralized training information redundant

Those are eligible for an exact dependency reduction, not implied automatically by statistical noninferiority.

The result is conditional on the retained credit geometry

G46 preserves:

realized-successor targets
immediate/successor decomposition
separate centering
independent relative scaling
literal equal-channel composition

G44 established that independent relative channel scaling is load-bearing against the registered pooled-scale null. G46 therefore cannot be used to replace independent scaling or collapse the two credit streams into an ordinary shared-team estimator.

The literal raw norm is one exact comparator

The supported null is the unrescaled gradient:

v
RAW
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

G46 does not establish that:

every fixed coefficient is sufficient;

every adaptive schedule is redundant;

a raw unaveraged sum is equivalent under the same Adam learning rate;

another optimizer or branch budget would yield the same result;

a learned or per-group scale is unnecessary.

Finite-budget and optimizer scope

A scalar schedule changes Adam moment histories and actor-to-baseline learning geometry. G46 shows that the specific baseline-derived scalar schedule is unnecessary under the frozen Adam configuration, accepted anchors, and 100-update branch budget. It does not prove optimizer-independent or asymptotic equivalence.

Prior boundaries remain intact

G31: realized-future-tail credit remains supported on the registered paired G17/G18 source.

G40: the complete G31 package remains materially better than the exact TEAM-GAE1 branch after the common fast anchor.

G41: the standalone slow critic remains exactly removable.

G42: DB angular direction balancing remains locally removable.

G43: the DB-derived global norm remains removable.

G44: independent relative channel scaling remains load-bearing.

G45: baseline subtraction into the actual actor-credit direction remains removable.

G46: the remaining baseline-derived scalar norm schedule is removable.

G46 does not show that TEAM-GAE1 would access the source, nor does it rewrite G31’s G17/G18 causal evidence.

Source, process, capacity, and horizon exclusions

The result is restricted to:

H=48
configured capacities=6|8|12
capacity-8 fixed-process training
G34-P0 bounded fixed/random evaluation
one each of L/R/J/T
three registered legal event orders
accepted common anchors
registered Adam and finite branch budget

It does not establish arbitrary:

configured capacity or active count;

within-trajectory maximum-capacity changes;

event count, type, timing, or ordering;

repeated unbounded leave/rejoin;

process laws;

horizons;

optimizers or update budgets.

History, recurrence, and UAV exclusions

Both arms use the same current-state, no-carry actor. G46 provides no new evidence about recurrence where task-relevant information is absent from current observations.

It also contains no UAV evidence. G1/G2 remain source-non-identifiable, identifiable non-G33 UAV transport remains parked, and G33 remains permanently frozen. The existing ledger preserves these directions rather than treating toy evidence as UAV transport.

CDC_PORTFOLIO_LEDGER_EDITS

These are exact scientific recording instructions only. They do not authorize repository mutation.

CONJECTURES.md

Replace the C-CONTINUOUS-ROSTER status line with:

Markdown
- Status: supported and retained at G46 as a usable native-six-coordinate,
  no-carry, post-anchor no-slow/no-DB, target-only, literal-raw-norm,
  independently scaled G31-credit continuous dynamic-roster test version for
  the registered H=48, capacity-6/8/12 bounded-process family. The shared
  baseline module remains shadow-trained but has no output read into actual
  actor-credit residual, direction or scalar norm.

Add after the G44 paragraph:

Markdown
- Formal G45 actor-direction evidence: target-only NO_READ actor credit passes
  the complete access contract and is noninferior to baseline-conditioned READ
  when the local baseline-read counterfactual scalar norm remains matched.
  Baseline subtraction into the actual actor-credit residual and direction is
  therefore locally removable; the baseline module and scalar shadow remained.
- Formal G46 scalar-schedule evidence: G46 compares that accepted
  baseline-shadow-norm route against the literal unrescaled target-only
  equal-mean gradient. Both arms pass access, RAW noninferiority is true and
  material shadow-norm advantage is false. SHADOW-minus-RAW pooled CI95 is
  [-0.0004228799, 0.0021094173, 0.0066980410]; capacity-6/8/12 UCBs are
  0.0056411082, 0.0077412759 and 0.0065407719.

Replace the accepted post-anchor boundary with:

Markdown
- Accepted post-anchor training boundary:
  `COMMON_NATIVE6_FAST_ANCHOR →
  NATIVE6_G31_NO_BASELINE_ACTOR_READ_RAW_NORM`.
  Retain immediate/realized-successor decomposition, separate centering,
  independent per-channel scaling, literal equal-channel composition and
  common entropy. The baseline module remains only as a matched shadow:
  baseline outputs do not enter the actual actor-credit residual, direction or
  scalar norm.

Append to the retired alternatives:

Markdown
- G45--G46 local closure: neither state-conditioned baseline subtraction nor
  the baseline-derived dynamic scalar norm is access-required or materially
  advantageous by more than 0.05 inside the registered P0 boundaries. This
  does not yet establish exact structural removal of the baseline module,
  target-fitting losses, true-state inputs or baseline optimizer/checkpoint
  state.

Replace the strongest remaining training-explanations paragraph with:

Markdown
- Strongest remaining training explanations: realized-successor targeting,
  immediate/successor decomposition, separate centering, independent relative
  scaling and the common fast anchor remain causally unresolved. The retained
  baseline module is now a candidate decorative shadow rather than an
  identified actor-credit mechanism.

For C-CREDIT, replace the status line with:

Markdown
- Status: supported retained for the registered G17/G18 family and the
  shared-anchor G40-P0 branch, narrowed locally by G41--G46. The retained
  post-anchor credit unit is immediate/realized-successor decomposition,
  separate centering, independent relative scaling and literal equal-channel
  composition; neither the slow critic, DB composition nor baseline-output
  influence on actor credit remains supported as load-bearing.

Append:

Markdown
- G46 update: the exact baseline-derived scalar credit-norm schedule is
  removable. Both SHADOW_NORM and literal RAW_NORM access; SHADOW-minus-RAW
  pooled CI95 is [-0.0004228799, 0.0021094173, 0.0066980410], RAW
  noninferiority holds and material shadow-norm advantage is false. Structural
  deletion of the still-trained baseline module remains a separate exact
  dependency question.
C-REC_EDIT=NONE
C-BASE_EDIT=NONE
C-BENCH_EDIT=NONE
C-COORD_EDIT=NONE
ALGORITHM_PRINCIPLES_EDIT=NONE

The principles require updating only the smallest implicated unit and forbid broad retirement from one local result.

RESEARCH_DIRECTION_LEDGER.md

Supersede the stale G45 design-only row with:

g45_row_status=SUPPORTED_RETAINED
g45_scientific_route=
COMMON_NATIVE6_FAST_ANCHOR_to_NATIVE6_G31_INDEPENDENT_SCALE_BASELINE_SHADOW_NO_READ

g45_failed_closed=
shared_true_state_baseline_subtraction_required_for_access_or_material_advantage_inside_G45_P0

g45_retained_open=
baseline_derived_local_scalar_norm_schedule|baseline_shadow_module|
realized_successor_target|decomposition|separate_centering|
independent_scaling|common_fast_anchor

Add the exact G46 block:

g46_row=
continuous-roster native-six target-only literal-raw-norm post-anchor route

g46_row_status=SUPPORTED_RETAINED

g46_row_evidence=
docs/research/cdc/EVIDENCE_NOTES/20260728_CONTINUOUS_ROSTER_NATIVE_SIX_G31_BASELINE_SHADOW_NORM_ATTRIBUTION_G46_FORMAL_RESULT_AF7D6B1.md
|docs/external-review/rounds/20260728_g31_baseline_shadow_norm_schedule_attribution_g46_formal_result_disposition_clarification_v2/21_PRO_OPEN_RAW.md

g46_row_claim_ceiling=
registered G46-P0 only; baseline module and target-fitting exposure remain as
shadow controls; no universal credit, optimizer, process, capacity, horizon,
recurrence, UAV or G33 claim

g46_scientific_route=
COMMON_NATIVE6_FAST_ANCHOR_to_NATIVE6_G31_NO_BASELINE_ACTOR_READ_RAW_NORM

g46_supported_unit=
literal_raw_equal_mean_credit_norm_without_any_baseline_output_actor_read

g46_failed_closed=
baseline_derived_dynamic_scalar_credit_norm_required_for_access_or_material_advantage_inside_G46_P0

g46_primary_ci95=
[-0.0004228799079499559,0.0021094173361041147,0.006698041015233213]

g46_capacity_ci95_6=
[-0.0004973678887284012,0.0019354286384837916,0.005641108195372586]

g46_capacity_ci95_8=
[-0.0008021309699993385,0.0021935522016206174,0.007741275860189576]

g46_capacity_ci95_12=
[-0.0002107237611699419,0.0021713662325489836,0.006540771929473869]

g46_next_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHADOW_BASELINE_MODULE_REDUCTION_G47_DESIGN_ASSERTION_AUDIT

g46_conclusion_bearing_iterations_consumed=36
g46_iterations_remaining=1

Add under FAILED_CLOSED:

Markdown
| G46-P0 中 baseline-derived dynamic scalar credit-norm schedule 对 access 的
必要性或相对 literal RAW norm 的 >0.05 material advantage |
`FAILED_CLOSED` | SHADOW_NORM 与 RAW_NORM 均通过 access；RAW
noninferiority 成立，material shadow-norm advantage 为 false；
SHADOW-minus-RAW pooled CI95 为
[-0.0004228799, 0.0021094173, 0.0066980410]。 |
不得误写为“baseline module 已删除”“所有 baseline 都无效”“所有
adaptive scalar schedule 都无效”或“两臂精确相等”。 |

Add under OPEN_UNTESTED:

Markdown
| G46 accepted RAW route 中 shadow baseline module、target-fitting losses、
true-state input、optimizer state 与 checkpoint fields 的结构必要性 |
`OPEN_UNTESTED` | G46 已关闭 baseline output 对实际 actor residual、
direction 与 scalar norm 的全部读取；baseline parameters 与 actor
parameters 分离。下一最小问题是零轨迹依赖证明能否在不改变 actor update、
Adam state、action 或 trace 的情况下删除完整 shadow baseline module。 |
当前 scheduled action 为 G47 design assertion audit。 |

The current ledger explicitly distinguishes supported, failed-closed, and open units and requires status changes only from an External-Pro scientific disposition.

IDEA_PORTFOLIO.md

Replace C-CONTINUOUS-ROSTER with:

Markdown
| C-CONTINUOUS-ROSTER | supported retained at G46: native-six no-carry,
post-anchor no-slow/no-DB, target-only literal-raw-norm independently scaled
G31-credit bounded-process test version | G41--G43 remove the slow critic and
DB composition; G44 retains independent channel scaling; G45 removes baseline
subtraction from actor direction; G46 removes the remaining baseline-derived
scalar norm. Both G46 arms access and SHADOW-minus-RAW CI95 is
[-0.0004228799, 0.0021094173, 0.0066980410]. | Retain
`COMMON_NATIVE6_FAST_ANCHOR →
NATIVE6_G31_NO_BASELINE_ACTOR_READ_RAW_NORM`. Next test exact structural
removal of the now-decorative shadow baseline module. Broader transport and
identifiable non-G33 UAV remain live or parked. |

Replace C-CREDIT with:

Markdown
| C-CREDIT | supported on G17/G18 and shared-anchor G40-P0; post-anchor
baseline-output influence locally removed by G45--G46 | The retained local
unit is immediate/realized-successor decomposition, separate centering,
independent relative scaling and literal equal-channel composition. The
baseline module remains shadow-trained but no longer supplies actor residual,
direction or norm. | Schedule exact shadow-baseline structural reduction.
Preserve target, decomposition, centering, scaling, common-anchor and
source-transfer questions separately. |

Append:

## G46 formal result update

g46_formal_branch=
RAW_NO_BASELINE_SHADOW_NORM_SUFFICIENT_G46

g46_scientific_disposition=
SUPPORTED_RETAINED_RAW_NORM_NO_BASELINE_ACTOR_READ_G46

g46_scientific_route=
COMMON_NATIVE6_FAST_ANCHOR_to_NATIVE6_G31_NO_BASELINE_ACTOR_READ_RAW_NORM

g46_failed_closed=
baseline_derived_dynamic_scalar_credit_norm_required_for_access_or_material_advantage_G46_P0

g46_next_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHADOW_BASELINE_MODULE_REDUCTION_G47_DESIGN_ASSERTION_AUDIT

Replace the active terminal block with:

completed_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_BASELINE_SHADOW_NORM_SCHEDULE_ATTRIBUTION_G46_FORMAL_ITERATION_36

source_family=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_BASELINE_SHADOW_NORM_SCHEDULE_ATTRIBUTION_G46_P0

formal_disposition=
RAW_NO_BASELINE_SHADOW_NORM_SUFFICIENT_G46

scientific_disposition=
SUPPORTED_RETAINED_RAW_NORM_NO_BASELINE_ACTOR_READ_G46

next_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHADOW_BASELINE_MODULE_REDUCTION_G47_DESIGN_ASSERTION_AUDIT

conclusion_bearing_iterations_consumed=36
iterations_remaining=1
PORTFOLIO_DELTA_AND_VALID_RESULT_DISPOSITION
VALID_RESULT_DISPOSITION=CONTINUE
conclusion_bearing_iterations_consumed=36
remaining_conclusion_bearing_iterations=1

The balance arithmetic is an inference from the allow-listed state: G44 recorded 34 consumed and three remaining; G45 is bound as an accepted formal prerequisite in the G46 index; accepting the present G46 formal result consumes one further iteration.

An exact, cheaper in-scope reduction remains: the shadow baseline module is still trained but has no registered causal path into actor credit, action selection, checkpoint selection, or evaluation. The result therefore does not meet either terminal condition.

Direction	State after G46	Advancement or reactivation condition
Literal RAW target-only post-anchor route	Supported and retained	Use as current accepted route
Baseline-derived scalar norm schedule	Failed closed in G46-P0	Distinct source or scientifically different comparator
Shadow baseline module structural necessity	Live; scheduled	G47 exact dependency/removal audit
Realized-successor target	Live, unscheduled	Matched target-authority comparator
Immediate/successor decomposition	Live, unscheduled	Preserve total information and normalization
Separate channel centering	Live, unscheduled	Hold targets, scaling and composition fixed
Independent relative channel scaling	Supported and retained	Preserve in G47
Common fast anchor	Live, unscheduled	Match initial function, interactions and exposure
Broader process/horizon/capacity	Live, unscheduled	Change one source axis at a time
Identifiable non-G33 UAV transport	Parked	Feasible, load-bearing, support-valid, identifiable source
Recurrence/EHC	Parked	Task-relevant information absent from current observations
Asynchronous skill lifetime/intrinsic reward	OUT_OF_SCOPE_FROZEN	Later explicit scope transition
G33 lineage	Permanently frozen	No reactivation

Scheduling one action does not make it scientifically unique; the role contract requires retaining other viable directions with reactivation conditions.

CURRENT_SCHEDULED_ACTION_IF_CONTINUE
current_scheduled_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHADOW_BASELINE_MODULE_REDUCTION_G47_DESIGN_ASSERTION_AUDIT
Scientific rationale

G46 removes the final baseline-output influence on the actor-credit path:

baseline read into actual residual=0
baseline read into actual direction=0
baseline read into actual scalar norm=0

The retained baseline module now performs only its own shadow target fitting. Because actor and baseline parameters are disjoint, the actor uses target-only credit, and there is no global gradient clipping or joint norm operation, the baseline module is a candidate causally disconnected component.

An exact structural-deletion audit is cheaper and more discriminating than immediately changing the realized-successor target, decomposition, independent scaling, common anchor, process family, or UAV source. It can potentially delete:

shared two-output baseline module
true-current-state baseline input
baseline target losses
baseline optimizer parameters and Adam state
baseline checkpoint fields

without consuming the remaining conclusion-bearing iteration if exact disconnection can be proved.

EXECUTABLE_SCIENTIFIC_BOUNDARY
next_boundary=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHADOW_BASELINE_MODULE_REDUCTION_G47_DESIGN_ASSERTION_AUDIT

review_mode=DESIGN_ASSERTION_AUDIT
design_audit_compute=0
Exact G47 question

Can an exact causal-disconnection reduction be frozen between:

NATIVE6_G31_RAW_NORM_SHADOW_BASELINE — the accepted G46 RAW route, retaining the shared two-output baseline module, true-state input, target-fitting losses, optimizer parameters/state, and checkpoint fields although no baseline output enters actor credit; and

NATIVE6_G31_RAW_NORM_NO_BASELINE_MODULE — the identical actor-credit route with the entire baseline module and all baseline-only training/checkpoint state removed?

Only intended treatment

Delete exactly:

credit_baselines module
true-current-state baseline-only input path
immediate baseline target-fitting loss
successor baseline target-fitting loss
baseline parameters
baseline Adam moments and optimizer membership
baseline checkpoint keys and output schema

Retain exactly:

accepted G40 common fast anchor
G41 no-slow projection
native-six actor and log_std
target-only immediate residual
target-only realized-successor residual
separate channel centering
independent per-channel RMS scaling
literal 0.5*(g_I+g_S)
common entropy
source ledgers and action streams
PPO passes and actor optimizer exposure
final actor checkpoint rule

No replacement baseline, critic, learned scale, constant filler, optimizer compensation, or utility threshold is permitted.

Primary identification invariant

The intended result is exact equivalence, not statistical noninferiority.

Define D
G47
	​

 as the maximum of:

actor/log_std parameter difference
actor Adam-state difference
pre-tanh/action/log-probability difference
reward/roster/lifecycle trace difference
final actor-checkpoint difference

under the same stored trajectory and actor update.

Exact removability requires:

baseline_parameter_read_into_actor_gradient=0
baseline_parameter_read_into_entropy=0
baseline_parameter_read_into_action_or_logprob=0
baseline_parameter_read_into_checkpoint_selection=0
baseline_parameter_read_into_evaluation=0

actor_updates=bitwise_equal
actor_Adam_states=bitwise_equal
actions_and_registered_traces=equal_under_frozen_existing_tolerances

The presence of baseline losses in the reference arm must not alter actor parameters through parameter ordering, shared storage, global clipping, joint normalization, optimizer-wide scheduling, or checkpoint selection.

Ordered outcomes
1. INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHADOW_BASELINE_MODULE_REDUCTION_G47

2. UNREGISTERED_SHADOW_BASELINE_COUPLING_G47

3. SHADOW_BASELINE_MODULE_EXACTLY_REMOVABLE_G47

4. NUMERICALLY_UNRESOLVED_SHADOW_BASELINE_MODULE_REDUCTION_G47

No utility margin, bootstrap interval, or formal statistical run may substitute for the exact dependency claim.

Claim ceilings

A removable result may support only:

The shadow two-output baseline module, its true-state-only input, target-fitting losses, optimizer state, and checkpoint fields are structurally removable from the accepted post-anchor G46 RAW route.

It may not establish that:

baselines are unnecessary for TEAM-GAE1 or another estimator;

realized-successor targeting is removable;

independent scaling is removable;

centralized critics are universally unnecessary;

other sources or optimizers do not benefit from baselines.

A coupling result may support only:

The accepted implementation contains an unregistered numerical or causal baseline coupling that prevents exact deletion.

It may not establish task-level baseline necessity until that coupling is identified.

Evidence and complexity ceiling

Seek a zero-trajectory static and optimizer-factorization proof first.

If a dynamic witness is indispensable, freeze at most:

one accepted G46 RAW branch-start state
one 8-episode × 48-step stored batch
real_transitions<=384
PPO_passes=2
hypothetical_transitions=0
bootstrap_resamples=0
formal_statistical_run=forbidden
wall_clock<=1200_seconds

H=48
K_search=0
nested_rollout=false
replanning=false

The same stored trajectory must feed both update paths; duplicated environment interaction is unnecessary.

This boundary authorizes no implementation or proof execution.

中文简报
G46正式分支=
RAW_NO_BASELINE_SHADOW_NORM_SUFFICIENT_G46

科学裁决=
SUPPORTED_RETAINED_RAW_NORM_NO_BASELINE_ACTOR_READ_G46

已消耗结论性轮次=36
剩余结论性轮次=1
G46 证明了什么

G46 比较：

SHADOW_NORM:
    target-only actor-credit direction
    × local baseline-conditioned counterfactual norm

RAW_NORM:
    literal 0.5*(g_I+g_S)
    baseline output 对 residual / direction / scalar norm 全部零读取

两臂都通过完整 access，正式主区间为：

SHADOW_NORM - RAW_NORM CI95
=
[-0.0004228799, 0.0021094173, 0.0066980410]

三个 capacity 的 UCB 都低于 0.00775，远低于 0.05 margin。

因此，在 G46-P0 中：

baseline-derived dynamic scalar norm schedule 可以从 actor-credit 路径删除。

当前接受 route
COMMON_NATIVE6_FAST_ANCHOR
→ NATIVE6_G31_NO_BASELINE_ACTOR_READ_RAW_NORM

actor-credit 仍保留：

immediate target
realized-successor target
separate centering
independent scaling
literal equal-channel mean

actor-credit 已不再读取：

baseline residual subtraction
baseline direction
baseline scalar norm
不能误写为
baseline module 已经结构删除
true-state baseline input 在所有训练中无用
所有 adaptive scale 都无用
RAW 显著优于 SHADOW
两臂精确相等
TEAM_GAE1 已经足够
UAV transport 已成立

baseline module 目前仍作为 shadow 训练，并保留自己的 loss、Adam state 和 checkpoint fields。

下一动作
CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHADOW_BASELINE_MODULE_REDUCTION_G47_DESIGN_ASSERTION_AUDIT

G47 将检验能否通过零轨迹依赖证明，精确删除：

shared baseline module
true-state baseline-only input
baseline losses
baseline optimizer state
baseline checkpoint fields

同时要求 actor 参数、actor Adam、动作和完整 trace 保持精确等价。

realized-tail、decomposition、separate centering、independent scaling、common anchor、broader process/horizon/capacity、可识别非 G33 UAV 与 recurrence/EHC 等方向继续保持 live 或 parked。G33 永久冻结。本裁决不授权实现或计算。
