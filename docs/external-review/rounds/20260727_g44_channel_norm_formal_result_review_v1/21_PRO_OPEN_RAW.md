1. REGISTERED_RESULT_CONFORMANCE
REGISTERED_FORMAL_BRANCH=
INDEPENDENT_CHANNEL_SCALE_ADVANTAGE_G44

scientific_acceptance=ACCEPT
valid_iteration_cost=1

formal_source_commit=
96e35ddf55de71e56c6bcace4746c408909480dd

aligned_source_commit=
1a6e046801ab3d83830d4c9f6e9724c8c47659da

alignment_stage_commit=
b55578a8e57f444895da59efe9268ebe31edf511

The registered branch is accepted without rescue, downgrade, or relabelling. The formal package is complete and operationally valid, uses the required CPU/C++ backend with no Python fallback, binds the exact aligned implementation and correction-recheck stage, and contains the frozen three-replicate, 396,288-transition, 1,200-optimizer-step inventory.

formal=true
status=COMPLETE
operational_valid=true
operational_errors=[]

source_valid=true
treatment_activation_valid=true

independent_access_pass=true
independent_access_confident_fail=false

pooled_access_pass=false
pooled_access_confident_fail=true

pooled_noninferior=false
material_independent_advantage=true

No higher-precedence branch fired. The source and registered reference arm are valid; the pooled arm confidently fails access; and the material-advantage predicate is independently satisfied. The resulting first-match branch is therefore exactly:

INDEPENDENT_CHANNEL_SCALE_ADVANTAGE_G44
Absolute-access separation

The independent-scale arm passes every inherited access predicate. Its deterministic fixed-process utility LCBs are approximately 0.9582, 0.9713, and 0.9646 at capacities 6, 8, and 12; its corresponding random-process LCBs are 0.9632, 0.9721, and 0.9661. All event-window, process-segment, stochastic, transport, and minimum-replicate gates also pass.

The pooled-scale arm fails broadly rather than at one isolated diagnostic:

Gate	Capacity 6	Capacity 8	Capacity 12
Fixed deterministic utility LCB	0.8556	0.8476	0.8027
Random deterministic utility LCB	0.8595	0.8510	0.7965
Random event-window LCB	0.7851	0.7558	0.6638
Random process-segment LCB	0.7886	0.7639	0.6672

Its fixed and random stochastic pooled LCBs are also below 0.80, and its minimum fixed/random replicate means are approximately 0.8348 and 0.8355, below the registered 0.85 floor.

Registered comparative result

The sign convention is:

Δ
scale
	​

=U
INDEPENDENT
	​

−U
POOLED
	​

.

The formal primary interval is:

Δ
scale
	​

∈[0.09243883, 0.11293004, 0.13779361]
	​


and the capacity-specific intervals are:

Capacity	Independent − pooled CI95
6	[0.08692653, 0.09689438, 0.10838352]
8	[0.08096092, 0.10447315, 0.12605436]
12	[0.10996276, 0.13776535, 0.17842150]

The pooled primary LCB exceeds the materiality threshold 0.05, and every capacity-specific LCB is strictly positive. Several fixed, stochastic, event-window, and process-segment component intervals are also entirely positive.

2. SCIENTIFIC_DISPOSITION
SCIENTIFIC_DISPOSITION=
SUPPORTED_RETAINED_INDEPENDENT_RELATIVE_CHANNEL_SCALING_G44
Strongest supported proposition

Within G44-P0, after the accepted native-six common fast anchor and G41 no-slow projection, independently scaling the separately centered immediate and realized-successor credit channels supplies a source-local finite-budget access and material-utility advantage over a common pooled-scale channel geometry, even when the pooled arm’s global credit-gradient norm is matched to its own independent-scale counterfactual on every PPO pass.

This conclusion is bounded to:

actor=native_six_no_carry
common_anchor=accepted_G40_fast_anchor
post_anchor_slow_critic=absent
DB_vector_and_norm=absent

credit_targets=
immediate_reward
plus
realized_successor_tail

channel_centering=separate
channel_composition=literal_equal_mean_0.5
reference_scale=independent_per_channel
null_scale=common_pooled
pooled_global_credit_norm=locally_matched

optimizer=registered_Adam
branch_updates=100
H=48
capacities=6|8|12
source=G32_fixed_plus_G34_P0_bounded_random

The G44 design deliberately held the credit-bearing global gradient norm fixed and left common entropy and baseline gradients unchanged. The identified treatment is therefore the relative weighting and direction created by independent channel scaling, not a larger actor step.

Accepted post-anchor route

The retained route is:

COMMON_NATIVE6_FAST_ANCHOR
→ NATIVE6_G31_EQUAL_MEAN_INDEPENDENT_SCALE_NO_SLOW

It retains:

realized-successor target
immediate/successor decomposition
shared true-current-state two-output baseline
separate channel centering
independent per-channel scaling
literal equal-channel gradient mean

It continues to delete:

standalone slow critic
slow-critic return loss and Adam state
direction-balanced vector composition
DB-derived scalar norm schedule
all post-anchor DB shadow computation
Exact increment beyond G40–G43

G40 supports the complete G31 branch package over TEAM-GAE1.

G41 deletes the standalone slow critic.

G42 deletes the DB angular direction.

G43 deletes the DB-derived scalar norm schedule.

G44 now identifies independent relative channel scaling as a retained, load-bearing component of the remaining package.

Consequently, the G40 advantage cannot be attributed to the deleted slow critic or either part of direction balancing. It can, however, be attributed in part to the remaining normalization geometry: when the two semantically different credit streams are forced through one common scale, access collapses across fixed and random processes and all configured capacities.

Smallest failed-closed unit

Retire exactly:

POOLED_CHANNEL_SCALE_SUFFICIENCY_G44_P0

or, in prose:

Under G44-P0, replacing independent relative channel scaling with the exact globally credit-norm-matched pooled-scale null preserves neither the registered access contract nor material utility.

This does not retire every common normalization law, every alternative channel weighting, or every pooled estimator. It closes only the exact registered pooled relative-scaling comparator.

3. COUNTEREXAMPLES_AND_EXCLUSIONS
Not a source or benchmark failure

The source is valid and the independent-scale reference arm passes every absolute gate. Pooled failure therefore cannot be attributed to an inaccessible benchmark, an unusable actor class, or lack of source support. It is an identified failure of the exact pooled-scale comparator.

The result concerns relative conditioning, not the numerical pooled RMS itself

After the pooled arm is rescaled to the local independent-counterfactual global credit norm, any positive common denominator contributes only a common scalar before the norm match. Its absolute value is therefore largely cancelled. The result identifies the loss of relative immediate-versus-successor channel conditioning, not a unique defect of one square-root formula. The frozen design explicitly limited the claim to relative channel geometry.

A different predeclared relative-weighting law could still succeed. G44 does not rank or reject:

another fixed channel ratio
a different independently normalized robust scale
a source-independent schedule
a separately audited learned mixture
another optimizer-aware comparator
Finite-budget Adam conditioning remains part of the conclusion

Even with matched pre-Adam global credit norm, changing relative channel geometry changes coordinatewise gradients and therefore Adam’s subsequent first- and second-moment trajectories. The result supports a finite-budget optimization-conditioning advantage under the frozen Adam configuration; it does not prove asymptotic or optimizer-independent necessity.

Interaction with the retained package remains open

Independent scaling may be load-bearing because of interaction with:

realized-successor targets
immediate/successor decomposition
separate channel centering
shared true-state baseline conditioning
the common fast anchor

G44 does not establish that independent scaling alone would be sufficient from random initialization, under another target, or without the shared baselines.

The formal training evidence also shows a large source-local disparity between immediate- and successor-channel scales in many updates. Independent scaling may therefore be balancing two credit streams with very different numerical units rather than expressing a universal MARL principle. The train artifact nevertheless confirms that treatment activation was real in every required replicate and that both arms’ normalization evidence was reconstructed.

No architectural or observation conclusion

Both arms use the same native-six actor, observations, action distribution, active-set aggregation, prefix, and parameter inventory. G44 supplies no new evidence about actor expressivity, recurrence, history fields, or deployment observation reduction.

Prior boundaries remain intact

G31: realized-tail credit remains supported on its registered G17/G18 paired source.

G40: TEAM-GAE1 remains failed-closed under G40-P0.

G41: the standalone slow critic remains removable.

G42: angular direction balancing remains removable under its exact scale-matched comparator.

G43: the DB-derived scalar norm schedule remains removable.

G44: independent relative channel scaling is retained against the exact pooled null.

G44 cannot retroactively show that G17/G18 require the same normalization mechanism or that every ordinary credit estimator fails.

Process, capacity, and horizon exclusions

The result remains bounded to:

H=48
configured capacities=6|8|12
G32 fixed process
G34-P0 bounded random process
one each of L/R/J/T
three registered event orders

It does not establish transport to arbitrary event counts, repeated unbounded leave/rejoin, other configured capacities, within-trajectory capacity changes, other horizons, or arbitrary process laws.

History, recurrence, and UAV exclusions

Both arms are no-carry current-state policies. G44 says nothing about recurrence on partially observed sources. It also contains no UAV evidence: UAV G1/G2 remain source-non-identifiable, identifiable non-G33 UAV transport remains parked, and G33 remains permanently frozen. The current conjecture and direction ledgers preserve these boundaries.

4. CDC_PORTFOLIO_LEDGER_EDITS
CONJECTURES.md

Replace the C-CONTINUOUS-ROSTER status line with:

Markdown
- Status: supported and retained at G44 as a usable native-six-coordinate,
  no-carry, post-anchor no-slow-critic, no-DB, literal-equal-mean,
  independent-channel-scale G31-credit configured-capacity bounded-random-
  process continuous-roster test version for the registered H=48,
  capacity-6/8/12 toy family.

Insert after the G43 scalar-schedule evidence:

Markdown
- Formal channel-scale evidence: G44 compares the accepted independently
  centered-and-scaled immediate/successor credit channels against an exact
  pooled-scale null whose global credit-gradient norm is locally matched to its
  own independent-scale counterfactual. The independent arm passes every
  absolute-access gate; the pooled arm confidently fails. Independent-minus-
  pooled pooled CI95 is
  [0.09243883, 0.11293004, 0.13779361], with capacity-6/8/12 CI95
  [0.08692653, 0.09689438, 0.10838352],
  [0.08096092, 0.10447315, 0.12605436], and
  [0.10996276, 0.13776535, 0.17842150].

Replace the accepted post-anchor boundary with:

Markdown
- Accepted post-anchor training boundary:
  `COMMON_NATIVE6_FAST_ANCHOR →
  NATIVE6_G31_EQUAL_MEAN_INDEPENDENT_SCALE_NO_SLOW`.
  Retain the native-six actor, realized-successor/immediate decomposition,
  shared true-current-state two-output baseline, separate centering,
  independent per-channel scaling and literal equal-channel gradient mean.
  Delete the standalone slow critic and all post-anchor direction-balance
  vector, norm and shadow computation.

Append to the retired-alternatives paragraph:

Markdown
- G44 local closure: the exact globally credit-norm-matched pooled relative
  channel-scale null is not access-sufficient and is materially worse than
  independent relative scaling inside G44-P0. This closes only that exact
  pooled comparator; it does not establish that every pooled/common
  normalization, channel ratio or optimizer fails.

Replace the strongest remaining training-explanations paragraph with:

Markdown
- Strongest remaining training explanations: the accepted route still depends
  on realized-successor targeting, immediate/successor decomposition, separate
  channel centering, shared true-current-state baseline conditioning and the
  common fast anchor. G44 identifies independent relative scale conditioning
  as load-bearing but does not separate those remaining components or their
  interactions.

Replace the exclusions paragraph with:

Markdown
- Exclusions: exact-RMS universality, every alternative channel weighting,
  optimizer-independent necessity, realized-tail or decomposition necessity,
  baseline or separate-centering necessity, common-anchor necessity, arbitrary
  capacity/process/horizon, recurrence, UAV usability, asynchronous skill
  lifetime, intrinsic-reward advantage and complete-algorithm superiority
  remain unsupported.

For C-CREDIT, replace the status line with:

Markdown
- Status: supported retained on the registered G17/G18 family and shared-anchor
  G40-P0 branch, with G41--G44 narrowing the local load-bearing unit to
  realized-tail/decomposed credit, shared-baseline conditioning, separate
  centering, independent relative channel scaling and literal equal-channel
  composition.

Append:

Markdown
- G44 update: independent relative channel scaling is load-bearing against the
  exact globally credit-norm-matched pooled-scale null. The reference arm
  passes all access gates; the pooled arm confidently fails, and the pooled
  independent-minus-pooled LCB is 0.09243883 against the 0.05 materiality
  margin. This is source-local finite-budget credit-conditioning evidence, not
  universal normalization or temporal-credit necessity.

No status change is warranted for C-REC, C-BASE, C-BENCH, or C-COORD. The existing ledger requires updating only the smallest implicated unit.

RESEARCH_DIRECTION_LEDGER.md

Add this exact mechanical block near the existing G40–G43 updates:

## G44 formal result update (mechanically recorded from External Pro)

g44_row=continuous-roster native-six realized-tail/decomposed credit with
independent relative channel scaling and literal equal-mean post-anchor route

g44_row_status=SUPPORTED_RETAINED

g44_row_evidence=
docs/research/cdc/EVIDENCE_NOTES/20260727_CONTINUOUS_ROSTER_NATIVE_SIX_G31_CHANNEL_SCALE_NORMALIZATION_ATTRIBUTION_G44_FORMAL_RESULT_96E35DD.md
|docs/external-review/rounds/20260727_g44_channel_norm_formal_result_review_v1/21_PRO_OPEN_RAW.md

g44_row_claim_ceiling=registered G44-P0 only; no universal channel-normalization,
credit, recurrence, process, horizon, capacity, UAV or G33 claim

g44_scientific_route=
COMMON_NATIVE6_FAST_ANCHOR_to_NATIVE6_G31_EQUAL_MEAN_INDEPENDENT_SCALE_NO_SLOW

g44_supported_unit=
independent_relative_immediate_successor_channel_scaling_under_matched_global_credit_norm

g44_failed_closed=
globally_credit_norm_matched_pooled_relative_channel_scale_access_or_noninferiority_inside_G44_P0

g44_primary_ci95=[0.09243883,0.11293004,0.13779361]

g44_capacity_ci95_6=[0.08692653,0.09689438,0.10838352]
g44_capacity_ci95_8=[0.08096092,0.10447315,0.12605436]
g44_capacity_ci95_12=[0.10996276,0.13776535,0.17842150]

g44_next_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHARED_BASELINE_CONDITIONING_ATTRIBUTION_G45_DESIGN_ASSERTION_AUDIT

g44_valid_result_disposition=CONTINUE
g44_conclusion_bearing_iterations_consumed=34
g44_iterations_remaining=3

Add under SUPPORTED_RETAINED:

Markdown
| 连续动态 roster 的 native-six、realized-tail/decomposed credit、independent-channel-scale post-anchor 路线 | `SUPPORTED_RETAINED` | G41 删除 standalone slow critic，G42/G43 删除全部 post-anchor DB composition；G44 中 independent-scale arm 通过全部 access，而 globally credit-norm-matched pooled arm confident fail。Independent-minus-pooled pooled CI95 为 [0.09243883, 0.11293004, 0.13779361]，三个 capacity 的 LCB 均大于 0.08。当前 route 为 `COMMON_NATIVE6_FAST_ANCHOR → NATIVE6_G31_EQUAL_MEAN_INDEPENDENT_SCALE_NO_SLOW`。 | 不能推出 exact RMS 普适最优、所有 common scale 都失败、其他 optimizer/budget、realized-tail、decomposition、baseline、centering 或 common anchor 必要；不能外推任意 process/capacity/horizon、UAV、skill lifetime 或 intrinsic reward。 | [G44 正式结果](EVIDENCE_NOTES/20260727_CONTINUOUS_ROSTER_NATIVE_SIX_G31_CHANNEL_SCALE_NORMALIZATION_ATTRIBUTION_G44_FORMAL_RESULT_96E35DD.md) |

Add under FAILED_CLOSED:

Markdown
| G44-P0 中 globally credit-norm-matched pooled relative channel scaling 的 access sufficiency 或相对 independent scaling 的 0.05 noninferiority | `FAILED_CLOSED` | Independent arm 通过全部 access；pooled arm 在 fixed/random utility、event window、process segment、stochastic 与 minimum-replicate gates 上 confident fail。Independent-minus-pooled primary LCB 为 0.09243883，且所有 capacity LCB 严格为正。 | “所有 pooled/common normalization 都无效”“某一 pooled RMS 数值本身导致失败”“所有 source 都需要 independent scaling”。 | [G44 正式结果](EVIDENCE_NOTES/20260727_CONTINUOUS_ROSTER_NATIVE_SIX_G31_CHANNEL_SCALE_NORMALIZATION_ATTRIBUTION_G44_FORMAL_RESULT_96E35DD.md) |

Delete or supersede the former open G44 channel-scale row, and add:

Markdown
| G44 accepted independent-scale branch 中 shared true-current-state baseline 对 actor credit 的局部必要性 | `OPEN_UNTESTED` | 保持 accepted anchors、G41 no-slow projection、realized-tail、decomposition、separate centering、independent scaling、literal equal mean、source 与 Adam exposure 不变；比较 actor 使用 baseline-conditioned residuals 与 baseline module shadow-trained 但 actor 不读取 baseline outputs 的 matched null。 | G44 证明 relative scaling load-bearing，但 shared baseline conditioning 尚未获得 component-level comparator。当前 scheduled action 为 G45 design assertion audit。 |

All broader process, horizon, capacity, recurrence, UAV, lifetime, and intrinsic-reward entries remain unchanged. The current ledger expressly requires SUPPORTED_RETAINED, FAILED_CLOSED, and OPEN_UNTESTED to be applied only to their smallest exact units.

IDEA_PORTFOLIO.md

Replace C-CONTINUOUS-ROSTER with:

Markdown
| C-CONTINUOUS-ROSTER | supported retained at G44: native-six no-carry, post-anchor no-slow/no-DB, literal-equal-mean independent-channel-scale G31-credit configured-capacity bounded-process test version | G40 supports the complete G31 package over TEAM_GAE1; G41--G43 remove the standalone slow critic and all DB composition; G44 shows the independent-scale arm passes all access while the globally credit-norm-matched pooled arm confidently fails. Independent-minus-pooled CI95 is [0.09243883, 0.11293004, 0.13779361]. | Retain `COMMON_NATIVE6_FAST_ANCHOR → NATIVE6_G31_EQUAL_MEAN_INDEPENDENT_SCALE_NO_SLOW`. Next isolate shared-baseline conditioning. Broader transport and identifiable non-G33 UAV remain live or parked. |

Replace C-CREDIT with:

Markdown
| C-CREDIT | supported on G17/G18 and shared-anchor G40-P0; independent relative channel scaling retained by G44 | G41--G43 remove the standalone slow critic and DB composition, but G44 rejects the globally credit-norm-matched pooled-scale replacement. The retained local unit is realized-tail/decomposed credit, shared-baseline conditioning, separate centering, independent relative channel scaling and literal equal-channel mean. | Schedule shared-baseline actor-conditioning attribution next. Preserve target, decomposition, centering, common-anchor, process-transport and source-specific questions as separate live directions. |

Append:

## G44 formal result update

g44_continuous_roster_status=
supported retained at G44: native-six no-carry, post-anchor no-slow/no-DB,
literal-equal-mean independent-channel-scale G31-credit configured-capacity
bounded-process test version

g44_formal_branch=INDEPENDENT_CHANNEL_SCALE_ADVANTAGE_G44

g44_scientific_disposition=
SUPPORTED_RETAINED_INDEPENDENT_RELATIVE_CHANNEL_SCALING_G44

g44_scientific_route=
COMMON_NATIVE6_FAST_ANCHOR_to_NATIVE6_G31_EQUAL_MEAN_INDEPENDENT_SCALE_NO_SLOW

g44_failed_closed=
globally_credit_norm_matched_pooled_relative_channel_scale_sufficiency_G44_P0

g44_next_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHARED_BASELINE_CONDITIONING_ATTRIBUTION_G45_DESIGN_ASSERTION_AUDIT

Replace the terminal block with:

completed_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_CHANNEL_SCALE_NORMALIZATION_ATTRIBUTION_G44_FORMAL_ITERATION_34

source_family=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_CHANNEL_SCALE_NORMALIZATION_ATTRIBUTION_G44_P0

formal_disposition=
INDEPENDENT_CHANNEL_SCALE_ADVANTAGE_G44

scientific_disposition=
SUPPORTED_RETAINED_INDEPENDENT_RELATIVE_CHANNEL_SCALING_G44

valid_result_disposition=CONTINUE

next_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHARED_BASELINE_CONDITIONING_ATTRIBUTION_G45_DESIGN_ASSERTION_AUDIT

authorization_status=
active_twenty_iteration_toy_first_uav_promotion_chain

conclusion_bearing_iterations_consumed=34
iterations_remaining=3
5. PORTFOLIO_DELTA_AND_VALID_RESULT_DISPOSITION
VALID_RESULT_DISPOSITION=CONTINUE

conclusion_bearing_iterations_consumed=34
remaining_conclusion_bearing_iterations=3

The balance is not exhausted and an exact in-scope component-attribution candidate remains. CLOSE_NO_EXECUTABLE_CANDIDATE and COMPLETE_BALANCE_EXHAUSTED therefore do not apply. The External-Pro charter requires one scheduled action while preserving all other viable directions.

Direction	State after G44	Advancement or reactivation condition
Independent relative channel scaling	Supported and retained	Use in the accepted post-anchor route
Exact pooled relative scale null	Failed closed in G44-P0	Distinct source or scientifically different comparator, not tuning G44
Shared true-state baseline conditioning	Live; scheduled	G45 matched baseline-read versus shadow-no-read audit
Separate channel centering	Live, unscheduled	Hold scaling, targets, baseline and equal mean fixed
Realized-successor target	Live, unscheduled	Change target only under matched decomposition and normalization
Immediate/successor decomposition	Live, unscheduled	Preserve total information, baseline capacity and update scale
Common fast anchor	Live, unscheduled	Match initialization, interactions and optimizer exposure
Broader process/horizon/capacity	Live, unscheduled	Change one source axis at a time
Identifiable non-G33 UAV transport	Parked	Requires feasible, load-bearing, support-valid, source-identifiable source
Recurrence/EHC	Parked	Requires task-relevant information absent from current observations
C-BASE/C-COORD	Live outside this reduction	Requires representation-fixed access or coordination separation
Asynchronous skill lifetime/intrinsic reward	OUT_OF_SCOPE_FROZEN	Later explicit scope transition
G33 lineage	Permanently frozen	No reactivation in this chain
6. CURRENT_SCHEDULED_ACTION_IF_CONTINUE
current_scheduled_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHARED_BASELINE_CONDITIONING_ATTRIBUTION_G45_DESIGN_ASSERTION_AUDIT
Scientific rationale

G44 shows that relative channel scaling is genuinely load-bearing; the next question should not weaken or replace it. The nearest remaining specialized information path is the shared two-output baseline’s state-dependent subtraction from the actor credit channels.

This is the cheapest high-information successor because it can preserve:

realized-successor and immediate targets
their decomposition
separate centering
independent channel scaling
literal equal mean
actor and source
common anchor
Adam/PPO exposure

while changing only whether the actor credit reads the baseline predictions.

A reduction result could remove centralized true-state conditioning from the actor-credit path. A positive result would identify that conditioning as another load-bearing member of the residual G40 package. This is more discriminating than immediately changing the realized-tail target and substantially cheaper than changing the common anchor, process family, horizon, capacity, or UAV source.

Scheduling G45 does not make baseline conditioning the unique live scientific direction.

7. EXECUTABLE_SCIENTIFIC_BOUNDARY
next_boundary=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHARED_BASELINE_CONDITIONING_ATTRIBUTION_G45_DESIGN_ASSERTION_AUDIT

review_mode=DESIGN_ASSERTION_AUDIT
design_audit_compute=0
Exact G45 question

Can a conclusion-bearing matched post-anchor comparison be frozen between:

NATIVE6_G31_INDEPENDENT_SCALE_BASELINE_READ — the accepted G44 route, whose immediate and successor actor-credit residuals subtract their shared true-current-state baseline outputs; and

NATIVE6_G31_INDEPENDENT_SCALE_BASELINE_SHADOW_NO_READ — the identical route with the same baseline module, inputs, target-fitting losses, parameters, optimizer group, Adam exposure, and checkpoint inventory, but with zero baseline-output reads into the actor-credit residuals?

The only intended treatment is:

state-conditioned baseline subtraction into actor credit
versus
no actor read of those baseline outputs
Frozen residual laws

Reference:

x
t
I,READ
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
x
t
S,READ
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

)).

No-read null:

x
t
I,NO_READ
	​

=r
t
	​

,
x
t
S,NO_READ
	​

=G
t+1
	​

.

Both arms then use the same frozen pipeline:

separate channel centering
independent per-channel RMS scaling
literal 0.5*(g_I+g_S)
common entropy added once
two persistent PPO passes
Baseline inventory and shadow isolation

Both arms retain byte-identical:

shared two-output baseline graph
true-current-state baseline inputs
baseline targets
baseline losses
baseline parameter order
baseline Adam state and exposure

In the no-read arm:

baseline_read_into_actor_residual=0
baseline_read_into_actor_gradient_direction=0
baseline_read_into_action_or_logprob=0
baseline_read_into_checkpoint_selection=0
baseline_read_into_evaluation_metric=0

The baseline remains shadow-trained only to match capacity and optimizer exposure.

Credit-step scale control

Baseline subtraction can change both direction and global actor-credit norm. To isolate conditioning rather than effective learning rate, the no-read arm must match its credit-gradient norm to a local baseline-read counterfactual computed on its own pre-update model and trajectory.

Only the detached scalar norm may be used. The counterfactual vector cannot be assigned, serialized as an actor interface, or affect the no-read direction.

Common entropy and baseline gradients are added or applied unchanged after the credit-norm gate.

Treatment activation

Using only the reference arm’s pre-update state, construct:

reference baseline-conditioned credit direction
no-baseline-read counterfactual credit direction

Require both:

at least one baseline output has centered RMS > 1e-6
unit-direction distance > 1e-6

and positive finite credit norms.

Required scope:

nonformal:
    at least one treatment-active pass

formal:
    at least one treatment-active pass
    in each accepted-anchor replicate 0|1|2

The actual no-read arm supplies no activation evidence.

Primary estimand
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
materiality_and_noninferiority_margin=0.05

Positive values favor actor use of the shared true-state baseline.

Claim ceilings

A no-read sufficiency result may support only:

State-conditioned baseline subtraction is removable from the actor-credit direction under G45-P0 while the baseline module, its target fitting, optimizer exposure, and local counterfactual scalar norm remain retained as matched controls.

It may not establish that the baseline module or centralized true-state information can already be deleted structurally.

A positive reference result may support only:

Shared true-current-state baseline conditioning supplies a source-local finite-budget access or material-utility advantage over the exact shadow-trained no-actor-read null.

Neither result may establish the necessity or redundancy of realized-tail targeting, decomposition, separate centering, independent scaling, the common anchor, recurrence, UAV mechanisms, or G33.

Frozen first-match branches
1. INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHARED_BASELINE_CONDITIONING_ATTRIBUTION_G45

2. SOURCE_OR_REFERENCE_ACCESS_FAILURE_G45

3. SHADOW_BASELINE_NO_ACTOR_READ_SUFFICIENT_G45

4. SHARED_TRUE_STATE_BASELINE_CONDITIONING_ADVANTAGE_G45

5. MIXED_UNDERPOWERED_SHARED_BASELINE_CONDITIONING_G45

The sufficiency branch requires both arms to pass the complete inherited access contract and every READ-minus-NO_READ primary/component UCB to be <=0.05.

The advantage branch requires reference access and either confident no-read failure or:

LCB
95
	​

(Δ
baseline
	​

)>0.05

with every capacity-specific primary LCB strictly positive.

Evidence-complexity ceiling
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

These are ceilings, not default evidence volumes or compute authorization. The G45 design audit must freeze the smallest inventory consistent with three accepted-anchor replicates, exact process/profile balance, whole-episode paired confidence, and the inherited absolute-access gates.

This disposition authorizes no implementation, Git operation, nonformal run, or formal run.

8. 中文简报
G44正式分支=
INDEPENDENT_CHANNEL_SCALE_ADVANTAGE_G44

科学裁决=
SUPPORTED_RETAINED_INDEPENDENT_RELATIVE_CHANNEL_SCALING_G44

有效结果 disposition=
CONTINUE

已消耗结论性轮次=34
剩余结论性轮次=3
G44 证明了什么

G44 比较：

IND:
    immediate / successor 分别中心化、分别缩放

POOL:
    仍分别中心化
    但两条 channel 共用 pooled scale
    并把全局 credit-gradient norm 匹配到自己状态下的 IND counterfactual

因此，两臂不是因为 actor step 大小不同而分开；真正 treatment 是 immediate 与 successor 的相对 channel weighting。

正式结果：

IND access pass=true
POOL access pass=false
POOL confident fail=true

IND - POOL pooled CI95
=
[0.09243883, 0.11293004, 0.13779361]

三个 capacity 的 LCB 都高于 0.08。POOL 还同时失败于 fixed/random utility、event window、process segment、stochastic 和 minimum-replicate gates。

所以，在 G44-P0 中，independent relative channel scaling 是 load-bearing；精确 pooled relative-scale null 失败关闭。

不能误写为
所有 pooled normalization 都失败
某一个 pooled RMS 数值本身导致失败
independent RMS 在所有 source/optimizer 中普适最优
G17/G18 已经单独证明同一 normalization 必要
所有任务都不需要 recurrence
UAV transport 已经成立

G44 是当前 source、anchor、Adam 和有限预算下的 component attribution。

当前接受 route
COMMON_NATIVE6_FAST_ANCHOR
→ NATIVE6_G31_EQUAL_MEAN_INDEPENDENT_SCALE_NO_SLOW

已经删除：

standalone slow critic
DB angular vector
DB scalar norm
全部 post-anchor DB shadow

继续保留：

realized-successor target
immediate/successor decomposition
shared true-state two-output baseline
separate channel centering
independent channel scaling
literal equal-channel mean
下一动作
CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHARED_BASELINE_CONDITIONING_ATTRIBUTION_G45_DESIGN_ASSERTION_AUDIT

G45 将保持 target、decomposition、centering、independent scaling、equal mean、source 和 Adam exposure 不变，只比较：

actor credit 读取 baseline-conditioned residual
versus
baseline module 同样训练，但 actor 完全不读取 baseline output

为了不混入 actor learning-rate 差异，no-read arm 的 credit-gradient norm 将匹配其本地 baseline-read counterfactual norm；baseline 和 entropy updates 保持不变。

其他 realized-tail、decomposition、separate centering、common anchor、broader process/horizon/capacity、可识别非 G33 UAV 与 recurrence/EHC 方向继续保持 live 或 parked。G33 永久冻结。本裁决不授权代码或计算。