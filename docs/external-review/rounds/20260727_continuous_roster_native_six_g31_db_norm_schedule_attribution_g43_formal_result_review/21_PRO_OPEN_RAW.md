1. REGISTERED_RESULT_CONFORMANCE
REGISTERED_FORMAL_BRANCH=
EQUAL_MEAN_RAW_SUM_SUFFICIENT_G43

scientific_acceptance=ACCEPT
valid_iteration_cost=1

formal_source_commit=
bb42840ab1479abde7f3485006bfbbee981a73cf

aligned_implementation_commit=
45e16f71d171228135b6444bee1678b157d79abe

alignment_stage_commit=
889c0b4e3d68a8d74f811ae9ecfe7b5213abfa76

The registered branch is accepted without rescue, downgrade, or relabelling. The committed evidence identifies an operationally valid formal package, exact execution and alignment provenance, and an archived AUDIT_DISPOSITION=ALIGNED.

The mechanically frozen inventory is:

formal=true
status=COMPLETE
operational_valid=true
operational_errors={}

backend=ContinuousRosterToyBatch_CPU_CPP
python_fallback=false
cpu_budget=2
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

The fixed two-process launch changes execution transport only: worker outputs are isolated, deterministically merged by preassigned index, and constrained to one native/PyTorch thread per worker. The scientific source, seeds, branch formulas, evidence volume, and confidence unit remain unchanged.

The registered result predicates are:

dbnorm_access_pass=true
dbnorm_access_confident_fail=false

mean_access_pass=true
mean_access_confident_fail=false

mean_noninferior=true
treatment_activation_valid=true
material_dbnorm_advantage=false

The primary sign convention is:

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

The formal intervals are:

Contrast	CI95
Equal-capacity pooled primary	[-0.01122548, -0.00215076, 0.00407002]
Capacity 6	[-0.00684008, -0.00101355, 0.00359780]
Capacity 8	[-0.01170109, -0.00236798, 0.00473064]
Capacity 12	[-0.01473798, -0.00297130, 0.00379189]

Both arms pass the complete absolute-access contract, and every registered primary and component upper confidence bound satisfies the frozen 0.05 noninferiority margin. The first-match branch is therefore exactly EQUAL_MEAN_RAW_SUM_SUFFICIENT_G43.

Transport note: direct GitHub Contents reads of the three listed runtime JSON paths returned 404 at the review-stage commit. The frozen question and committed evidence note independently reproduce their source identities, completion state, inventory, branch predicates, and registered intervals. I therefore treat this as connector transport unavailability, not a scientific ambiguity or permission to substitute another path.

2. SCIENTIFIC_DISPOSITION
SCIENTIFIC_DISPOSITION=
SUPPORTED_RETAINED_FIXED_EQUAL_MEAN_NO_SHADOW_POST_ANCHOR_G31_COMPOSITION_G43
Exact supported proposition

In CONTINUOUS_ROSTER_NATIVE_SIX_G31_DB_NORM_SCHEDULE_ATTRIBUTION_G43_P0, after the accepted common native-six fast anchor and the G41 no-slow projection, the literal no-shadow equal-channel actor-gradient mean

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

preserves the complete fixed/random capacity-6/8/12 access contract and is noninferior by the frozen 0.05 margin to the G42 reference that applies the DB-derived per-pass global norm to the same raw-sum direction.

The comparison is bounded to:

common_anchor=accepted_G40_fast_anchor
actor=native_six_no_carry
post_anchor_slow_critic=absent

immediate_target=retained
realized_successor_target=retained
shared_true_state_two_output_baseline=retained
independent_channel_normalization=retained

reference_schedule=DB_derived_dynamic_global_norm
null_schedule=fixed_literal_coefficient_0.5
optimizer=registered_Adam

H=48
source=G32_fixed_plus_G34_P0_bounded_random
configured_capacities=6|8|12
branch_updates=100

The G43 design froze actor scale as the treatment: the MEAN arm was not rescaled to match the reference, its coefficient was not tunable, and it could not read the DB vector, DB norm, composer, shadow state, or a hidden proxy.

Accepted post-anchor route

The smallest retained route is now:

COMMON_NATIVE6_FAST_ANCHOR
→ NATIVE6_G31_EQUAL_MEAN_NO_SHADOW_NO_SLOW

Its post-anchor actor update retains:

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

independent channel normalization, and:

d
actor
	​

=
2
1
	​

[g
I
	​

+g
S
	​

].

It no longer requires:

standalone slow critic
slow-critic loss or Adam state
direction-balanced vector composition
DB-derived scalar norm
shadow DB computation
Increment beyond G40–G42

G40 established that the complete G31 branch package materially outperformed the exact TEAM-GAE1 null after a shared anchor.

G41 proved the standalone post-anchor slow critic exactly removable.

G42 proved the direction-balanced vector direction removable while retaining its scalar norm.

G43 proves that the remaining DB-derived scalar norm schedule is also removable in favor of the fixed equal-channel mean.

The combined G42–G43 result therefore closes the need for the complete post-anchor direction-balancing computation in this source. It does not retrospectively rewrite G31’s G17/G18 evidence or G40’s rejection of TEAM-GAE1. Historical results remain bounded to their own source and comparator.

Smallest retired unit

Retire exactly:

In G43-P0, the DB-derived per-pass scalar global-norm schedule is required for access or supplies a finite-budget material advantage greater than 0.05 over the literal equal-channel mean.

This retirement includes the remaining need to execute the DB composer as a post-anchor shadow calculation.

Smallest retained credit unit

The currently retained post-anchor training unit is:

realized-successor target
immediate/successor decomposition
shared true-current-state two-output baseline
independent per-channel normalization
fixed equal-channel mean

G40’s package-level advantage can no longer be attributed to the standalone slow critic, angular direction balancing, or the DB-derived scalar norm schedule. At least one of the remaining components—or their interaction under the common anchor and finite Adam budget—must explain the difference from TEAM-GAE1.

3. COUNTEREXAMPLES_AND_EXCLUSIONS
Noninferiority is not exact equality or MEAN superiority

The pooled and all capacity-specific intervals cross zero. G43 therefore does not establish exact equality, and it does not establish statistically confident superiority of the equal-mean arm.

The intervals permit a small DBNORM benefit, but the largest reported primary/capacity upper bound is only about 0.00473, far below the registered 0.05 materiality boundary. Conversely, their negative centers are consistent with a small MEAN benefit, but no superiority branch was registered. The exact conclusion is material removability and noninferiority, not equality or dominance.

The exact coefficient is 1/2

G43 validates one predeclared no-shadow null:

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

It does not prove that:

every fixed coefficient works;

a raw unaveraged sum works under the same Adam learning rate;

any arbitrary scalar scheduler is equivalent;

1/2 is globally or asymptotically optimal.

A different coefficient, learned weight, running scale, optimizer-specific correction, or per-group schedule is a different scientific comparator. It cannot be treated as a rescue or automatic extension of G43.

Finite-budget Adam dependence remains

Changing a per-pass scalar affects Adam’s first and second moments, optimizer epsilon, subsequent coordinatewise updates, and the actor-to-baseline learning-rate ratio. G43 shows that the DB-derived schedule adds no registered material value under the frozen anchors, Adam configuration, branch budget, and source. It does not establish optimizer-independent or asymptotic redundancy. The design explicitly treated these optimizer-history effects as part of the scalar-schedule intervention.

No source or common-access failure

Both DBNORM and MEAN pass absolute access. The higher-precedence SOURCE_OR_REFERENCE_ACCESS_FAILURE_G43 branch did not fire. G43 is therefore an identified component reduction, not a comparison between two inaccessible policies and not evidence that the G32/G34 source is defective.

Remaining G31 components are not adjudicated

G43 does not change:

realized-successor target
immediate/successor decomposition
shared-baseline conditioning
true-current-state baseline inputs
independent per-channel normalization
common fast anchor

It cannot establish that any one of these is necessary or redundant. A later comparator must change one component only and retain the accepted fixed-equal-mean route.

Prior boundaries remain intact

G31: realized-future-tail credit remains supported on its exact paired G17/G18 source.

G40: the exact TEAM-GAE1 branch remains failed-closed in G40-P0.

G41: the standalone post-anchor slow critic remains exactly removable.

G42: angular direction balancing remains failed-closed as a material requirement in G42-P0.

G43: only the DB-derived scalar norm schedule is additionally closed.

G43 does not imply that TEAM-GAE1 would succeed merely by changing its actor-gradient coefficient, nor that direction balancing is redundant on G17/G18 or another source.

History and recurrence are not implicated

Both G43 arms use the same native-six, no-carry actor and the same current information. The result does not support:

global task memorylessness;

recurrence redundancy on partially observed tasks;

removal of environment lifecycle state;

deletion of the true-current-state inputs to the shared baseline.

Ordinary/team recurrence remains a retained simpler explanation for sources where task-relevant information is absent from current observations.

Process, capacity, and horizon remain bounded

The result is restricted to:

H=48
configured capacities=6|8|12
G32 fixed process
G34-P0 bounded random process
one each of L/R/J/T
three registered event orders

It does not establish arbitrary:

active count or configured capacity;

within-trajectory maximum-capacity change;

event count, event type, order, or spacing;

repeated unbounded leave/rejoin;

roster-process law;

horizon.

Those remain separate live transport questions and must be varied one axis at a time.

UAV and frozen-scope exclusions

G43 contains no UAV evidence. UAV temporary-service-loss G1 and charge-rotation G2 remain SOURCE_NOT_IDENTIFIABLE; identifiable non-G33 UAV transport remains parked until a source is physically feasible, target-behavior load-bearing, policy-support valid, and source-identifiable. G33 and its full-ledger/static-preposition lineage remain permanently frozen. Asynchronous skill lifetime and environment-agnostic intrinsic reward remain outside the active membership stage.

4. CDC_PORTFOLIO_LEDGER_EDITS
4.1 CONJECTURES.md

Retain all earlier evidence, then amend C-CONTINUOUS-ROSTER as follows.

Replace its status line with:

Markdown
- Status: supported and retained at G43 as a usable native-six-coordinate,
  no-carry, post-anchor no-slow-critic, no-shadow fixed-equal-mean G31-credit,
  configured-capacity, bounded-random-process continuous dynamic-roster test
  version for the registered H=48, capacity-6/8/12 toy family.

Insert after the G42 evidence:

Markdown
- Formal scalar-schedule evidence: G43 compares the accepted G42 raw-sum
  direction with its DB-derived per-pass global norm against the literal
  no-shadow equal-channel mean `0.5*(g_I+g_S)`. Both arms pass every absolute
  access gate. DBNORM-minus-MEAN pooled CI95 is
  [-0.01122548, -0.00215076, 0.00407002]; capacity-6/8/12 UCBs are
  0.00359780, 0.00473064 and 0.00379189. MEAN is noninferior by 0.05,
  treatment activation is valid and material DBNORM advantage is false.

Replace the accepted-boundary paragraph with:

Markdown
- Accepted post-anchor training boundary:
  `COMMON_NATIVE6_FAST_ANCHOR →
  NATIVE6_G31_EQUAL_MEAN_NO_SHADOW_NO_SLOW`. Retain the native-six actor,
  shared immediate/successor baseline, realized-successor targets, independent
  channel normalization and literal equal-channel gradient mean. Delete the
  standalone slow critic and all post-anchor DB vector, DB norm and shadow
  computation.

Append to the retired-alternatives paragraph:

Markdown
  Inside G43-P0, the DB-derived scalar global-norm schedule is additionally
  closed as an access requirement or source of a >0.05 material advantage over
  the literal equal-channel mean. Together with G42, this removes the complete
  post-anchor direction-balancing computation from the accepted route. It does
  not close direction balancing on G17/G18 or every adaptive scalar schedule.

Replace the strongest-remaining-training-explanations paragraph with:

Markdown
- Strongest remaining training explanations: the accepted route still uses a
  realized-successor target, immediate/successor decomposition, a shared
  true-current-state two-output baseline, independent per-channel
  normalization and a common fast anchor. G40 supports that remaining package
  against TEAM_GAE1, but no one retained component is yet individually
  identified.

Replace the exclusions paragraph with:

Markdown
- Exclusions: arbitrary fixed coefficients, optimizer-independent equivalence,
  realized-tail or decomposition redundancy, shared-baseline or centralized-
  information reduction, channel-normalization redundancy, common-anchor
  redundancy, arbitrary capacity/process/horizon, UAV usability, asynchronous
  skill lifetime, intrinsic-reward advantage and complete-algorithm
  superiority remain unsupported.

For C-CREDIT, replace its status line with:

Markdown
- Status: supported retained for the registered G17/G18 paired toy family and
  the shared-anchor G40-P0 branch, narrowed locally by G41--G43: the standalone
  slow critic, direction-balanced vector and DB-derived scalar norm are
  removable from the post-anchor continuous-roster route.

Append:

Markdown
- G43 update: both the DBNORM and literal equal-mean arms pass access.
  DBNORM-minus-MEAN pooled CI95 is
  [-0.01122548, -0.00215076, 0.00407002], all registered comparisons satisfy
  the 0.05 noninferiority margin and material DBNORM advantage is false. The
  retained local credit unit is therefore realized-tail/decomposed credit,
  shared-baseline conditioning, independent channel normalization and a fixed
  equal-channel mean.
- Interpretation boundary: G43 closes neither every adaptive scalar rule nor
  any retained target, decomposition, baseline, normalization or anchor
  component.

No status edit is warranted for C-REC, C-BASE, C-COORD, or C-BENCH. The current conjecture ledger still records the package-level G40 evidence and the G41 reduction, so G43 must update only the smallest additional component.

4.2 RESEARCH_DIRECTION_LEDGER.md

Replace the supported continuous-roster row with:

Markdown
| 连续动态 roster 的原生六坐标、realized-tail/decomposed credit、fixed equal-mean post-anchor 路线 | `SUPPORTED_RETAINED` | G39 支持 native-six 训练；G40 支持共同 fast anchor 后的 G31 package；G41 精确删除 standalone slow critic；G42 删除 DB angular vector；G43 进一步证明 literal `0.5*(g_I+g_S)` 在不读取 DB vector、norm 或 shadow 的情况下仍通过 fixed/random capacity-6/8/12 全部 access。DBNORM-minus-MEAN pooled CI95 为 [-0.01122548, -0.00215076, 0.00407002]，MEAN noninferiority 成立且 material DBNORM advantage 为 false。当前 route 为 `COMMON_NATIVE6_FAST_ANCHOR → NATIVE6_G31_EQUAL_MEAN_NO_SHADOW_NO_SLOW`。 | 不能推出其他固定系数、其他 optimizer/budget、realized-tail、decomposition、shared baseline、independent channel normalization 或 common anchor 可删除；不能外推任意 capacity/process/horizon、UAV、skill lifetime 或 intrinsic reward。 | [G43 正式结果](EVIDENCE_NOTES/20260727_CONTINUOUS_ROSTER_NATIVE_SIX_G31_DB_NORM_SCHEDULE_ATTRIBUTION_G43_FORMAL_RESULT_BB42840.md)；第 33 轮报告 |

Add under FAILED_CLOSED:

Markdown
| G43-P0 中 DB-derived per-pass scalar global-norm schedule 对 access 的必要性或相对 literal equal mean 的 >0.05 material advantage | `FAILED_CLOSED` | DBNORM 与 MEAN 均通过 access；DBNORM-minus-MEAN pooled CI95 为 [-0.01122548, -0.00215076, 0.00407002]，三个 capacity UCB 均 <=0.004731，MEAN noninferiority 成立，material DBNORM advantage 为 false。 | “所有 adaptive scale schedule 都无用”“任意 fixed coefficient 都足够”“G17/G18 不需要 direction balancing”“两臂精确相等”。 | [G43 正式结果](EVIDENCE_NOTES/20260727_CONTINUOUS_ROSTER_NATIVE_SIX_G31_DB_NORM_SCHEDULE_ATTRIBUTION_G43_FORMAL_RESULT_BB42840.md)；第 33 轮报告 |

Delete the open G43 scalar-norm row and add:

Markdown
| G43 accepted equal-mean branch 中 independent per-channel scale normalization 的局部必要性 | `OPEN_UNTESTED` | 保持 accepted anchors、G41 no-slow projection、realized-tail、immediate/successor decomposition、shared true-state baseline、separate channel centering、literal equal mean、source、trajectories 与 Adam exposure 不变，只比较独立 channel scale 与一个预登记 pooled channel scale。 | G43 删除了 DB scalar schedule，但两条 credit channel 仍分别归一化；尚无 matched comparator。当前 scheduled action 为 G44 design assertion audit。 |

Retain as live or parked:

realized-successor target attribution;

decomposition attribution;

shared-baseline conditioning;

common-fast-anchor simplification;

broader process/horizon/capacity;

identifiable non-G33 UAV transport;

recurrence/EHC;

asynchronous lifetime and intrinsic reward under their existing statuses.

4.3 IDEA_PORTFOLIO.md

Replace C-CONTINUOUS-ROSTER with:

Markdown
| C-CONTINUOUS-ROSTER | supported retained at G43: native-six no-carry, post-anchor no-slow, no-shadow fixed-equal-mean G31-credit configured-capacity bounded-process test version | G40 supports the complete G31 package over TEAM_GAE1; G41 deletes the standalone slow critic; G42 deletes angular DB composition; G43 shows both DBNORM and literal equal-mean arms access, with DBNORM-minus-MEAN CI95 [-0.01122548, -0.00215076, 0.00407002] and every registered comparison noninferior by 0.05. | Retain `COMMON_NATIVE6_FAST_ANCHOR → NATIVE6_G31_EQUAL_MEAN_NO_SHADOW_NO_SLOW`. Next isolate independent per-channel scale normalization. Broader transport and non-G33 UAV remain live or parked. |

Replace C-CREDIT with:

Markdown
| C-CREDIT | supported on G17/G18 and shared-anchor G40-P0; slow critic and all post-anchor DB composition locally reduced by G41--G43 | G40 rejects TEAM_GAE1, but G41 removes the standalone slow critic, G42 removes DB angular direction and G43 removes the DB-derived scalar norm. The retained local unit is realized-tail/decomposed credit, shared-baseline conditioning, independent channel normalization and literal equal-channel mean. | Schedule channel-scale-normalization attribution next. Preserve the other component questions, G17/G18 evidence and every source-specific claim ceiling. |

Replace the terminal block with:

completed_action=CONTINUOUS_ROSTER_NATIVE_SIX_G31_DB_NORM_SCHEDULE_ATTRIBUTION_G43_FORMAL_ITERATION_33
source_family=CONTINUOUS_ROSTER_NATIVE_SIX_G31_DB_NORM_SCHEDULE_ATTRIBUTION_G43_P0
formal_disposition=EQUAL_MEAN_RAW_SUM_SUFFICIENT_G43
scientific_disposition=SUPPORTED_RETAINED_FIXED_EQUAL_MEAN_NO_SHADOW_POST_ANCHOR_G31_COMPOSITION_G43
valid_result_disposition=CONTINUE
next_action=CONTINUOUS_ROSTER_NATIVE_SIX_G31_CHANNEL_SCALE_NORMALIZATION_ATTRIBUTION_G44_DESIGN_ASSERTION_AUDIT
authorization_status=active_twenty_iteration_toy_first_uav_promotion_chain
conclusion_bearing_iterations_consumed=33
iterations_remaining=4

Before G43, the frozen G43 design recorded 32 consumed iterations and five remaining; acceptance of this valid formal result consumes one additional iteration.

4.4 ALGORITHM_PRINCIPLES.md
EDIT=NONE

G43 is a bounded local simplification already governed by the matched-comparator, replacement-before-accumulation, and narrow-result rules. It does not establish a new cross-experiment principle.

5. PORTFOLIO_DELTA_AND_VALID_RESULT_DISPOSITION
VALID_RESULT_DISPOSITION=CONTINUE

conclusion_bearing_iterations_consumed=33
remaining_conclusion_bearing_iterations=4

The balance is not exhausted, and an executable in-scope component-attribution candidate remains. Therefore neither terminal disposition applies. The External-Pro contract requires one scheduled resource-consuming action while retaining the remaining viable directions.

Direction	State after G43	Advancement or reactivation condition
Fixed-equal-mean no-shadow G31 route	Supported and retained	Use as the post-anchor basis
DB angular vector	FAILED_CLOSED in G42-P0	A distinct identified source/comparator, not tuning G42
DB-derived scalar norm schedule	FAILED_CLOSED in G43-P0	A distinct source, optimizer, or predeclared comparator
Independent channel-scale normalization	Live; currently scheduled	G44 matched independent-versus-pooled scale audit
Realized-successor target	Live, unscheduled	Change only the successor target after normalization attribution
Immediate/successor decomposition	Live, unscheduled	Preserve total reward information, baseline capacity and scale
Shared-baseline conditioning	Live, unscheduled	Hold targets, normalization and equal-mean composition fixed
Common fast anchor	Live, unscheduled	Match total interactions, optimizer exposure and initial function
Broader process/horizon/capacity	Live, unscheduled	Change one source axis at a time
Identifiable non-G33 UAV transport	Parked	Feasible, load-bearing, policy-support-valid, source-identifiable source
Recurrence/EHC	Parked	Relevant sequential information absent from current observations
C-BASE/C-COORD	Live outside this reduction	Representation-fixed access or coordination separation
Asynchronous skill lifetime/intrinsic reward	OUT_OF_SCOPE_FROZEN	Later explicit scope transition
G33 lineage	Permanently frozen	No reactivation in this chain

Scheduling G44 is an attribution choice, not a claim that it is the only scientifically worthwhile direction.

6. CURRENT_SCHEDULED_ACTION_IF_CONTINUE
current_scheduled_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_CHANNEL_SCALE_NORMALIZATION_ATTRIBUTION_G44_DESIGN_ASSERTION_AUDIT
Scientific rationale

After G43, no post-anchor DB calculation remains. The closest specialized object is now the independent scale normalization of the immediate and realized-successor channels.

This is the cheapest and most discriminating next action because it can preserve:

common anchors
native-six actor
no-slow graph
realized-successor target
immediate/successor decomposition
shared baseline and its true-state inputs
separate channel centering
literal equal-channel mean
source and paired RNG
Adam and PPO exposure

while changing only whether the two centered channels receive separate scale denominators or one shared pooled denominator.

It is more local and reversible than changing the realized-tail target, collapsing the decomposition, deleting the shared baseline, removing the common anchor, expanding the process family, or designing another UAV source.

A reduction result would simplify the retained G31 package further. A positive independent-scale result would identify the first remaining component of the G40 package as source-locally load-bearing.

7. EXECUTABLE_SCIENTIFIC_BOUNDARY
next_boundary=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_CHANNEL_SCALE_NORMALIZATION_ATTRIBUTION_G44_DESIGN_ASSERTION_AUDIT

review_mode=DESIGN_ASSERTION_AUDIT
design_audit_compute=0
Exact G44 design question

Can a conclusion-bearing matched post-anchor comparison be frozen between:

NATIVE6_G31_EQUAL_MEAN_INDEPENDENT_SCALE_NO_SLOW — the accepted G43 route, which independently centers and scales the immediate and realized-successor residual channels before applying the literal equal-channel gradient mean; and

NATIVE6_G31_EQUAL_MEAN_POOLED_SCALE_NO_SLOW — the identical route that retains separate per-channel centering but divides both centered channels by one fixed-law pooled scale before applying the same literal equal-channel gradient mean?

The only intended treatment is:

separate per-channel scale denominators
versus
one shared pooled scale denominator
Frozen normalization laws

Let the unnormalized detached residual rows over the same valid primitive-step unit be:

x
I
	​

=r−b
I
	​

(ξ),x
S
	​

=G
t+1
	​

−b
S
	​

(ξ).

Retain separate centering:

c
I
	​

=x
I
	​

−mean(x
I
	​

),c
S
	​

=x
S
	​

−mean(x
S
	​

).
Accepted independent-scale arm

Using the exact accepted finite-precision RMS/zero-variance helper:

s
I
	​

=RMS(c
I
	​

),s
S
	​

=RMS(c
S
	​

),
z
I
IND
	​

=Z(c
I
	​

,s
I
	​

),z
S
IND
	​

=Z(c
S
	​

,s
S
	​

),

where Z retains the exact accepted zero-denominator rule.

Pooled-scale null

Define the single pooled denominator over the concatenated centered rows:

s
P
	​

=
2n
∑c
I
2
	​

+∑c
S
2
	​

	​

	​

.

Then:

z
I
POOL
	​

=Z(c
I
	​

,s
P
	​

),z
S
POOL
	​

=Z(c
S
	​

,s
P
	​

).

Both arms construct their channel PPO gradients using the same likelihood, clipping, entropy, active-factor denominator and fixed parameter order, then apply:

d
actor
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

Neither arm may compute a DB vector, DB norm, learned coefficient, running scheduler, per-group scale, or post-Adam correction.

Zero and invalidity rules
s_I=s_S=0:
    both arms submit exact-zero actor channel gradients
    baseline updates and Adam exposure continue
    treatment inactive for that pass

one channel scale=0 and the other>0:
    the zero centered channel remains exact zero
    the nonzero channel follows its registered arm denominator
    valid treatment

s_P=0 while either centered channel is nonzero:
    INVALID before optimizer step

nonfinite residual, center, scale, normalized row or gradient:
    INVALID before optimizer step
Treatment-activation gate

Treatment activation must be reconstructed from the independent-scale reference arm’s pre-update residuals, not from the later-diverging pooled arm.

Define:

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


Require:

nonformal:
    at least one valid q_scale > 1e-6

formal:
    at least one valid q_scale > 1e-6
    in every accepted-anchor replicate 0|1|2

A reference replicate in which the two denominators never differ cannot support channel-scale attribution.

Claim ceilings

A reduction branch may support only:

Independent per-channel scale normalization is removable in favor of the registered pooled scale under G44-P0.

A positive independent-scale branch may support only:

Independent channel scaling supplies a source-local finite-budget access or material-utility advantage over the exact pooled-scale null.

Neither outcome may adjudicate:

separate channel centering;

realized-successor targeting;

immediate/successor decomposition;

shared-baseline conditioning;

common-anchor necessity;

recurrence;

process/capacity/horizon transport;

UAV mechanisms.

Primary estimand
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
materiality_and_noninferiority_margin=0.05

Positive values favor independent channel scaling.

Frozen first-match branches
1. INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_CHANNEL_SCALE_ATTRIBUTION_G44

2. SOURCE_OR_REFERENCE_ACCESS_FAILURE_G44

3. POOLED_CHANNEL_SCALE_SUFFICIENT_G44

4. INDEPENDENT_CHANNEL_SCALE_ADVANTAGE_G44

5. MIXED_UNDERPOWERED_CHANNEL_SCALE_ATTRIBUTION_G44

The pooled-scale sufficiency branch requires both arms to pass the complete inherited access contract and every IND-minus-POOL primary/component UCB to be <=0.05.

The independent-scale advantage branch requires reference access and either confident pooled-scale failure or:

LCB
95
	​

(Δ
scale
	​

)>0.05

with every capacity-specific primary lower bound strictly positive.

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

These are ceilings, not default evidence volume or compute authorization. The G44 design audit must choose the smallest conclusion-bearing inventory consistent with three independent anchor replicates, exact process/profile balance, whole-episode paired confidence, and the frozen access gates.

This disposition authorizes no implementation, Git operation, nonformal run, or formal run.

8. 中文简报
G43正式分支=
EQUAL_MEAN_RAW_SUM_SUFFICIENT_G43

科学裁决=
SUPPORTED_RETAINED_FIXED_EQUAL_MEAN_NO_SHADOW_POST_ANCHOR_G31_COMPOSITION_G43

有效结果 disposition=
CONTINUE

已消耗结论性轮次=33
剩余结论性轮次=4
G43 最强结论

G43 比较：

DBNORM:
    raw-sum direction × DB-derived dynamic norm

MEAN:
    0.5 × (immediate gradient + successor gradient)
    不读取 DB vector
    不读取 DB norm
    不运行 DB shadow

两臂都通过完整 access，MEAN 通过全部 0.05 noninferiority 门槛：

DBNORM - MEAN pooled CI95
=
[-0.01122548, -0.00215076, 0.00407002]

capacity 6/8/12 的 UCB 分别约为：

0.003598
0.004731
0.003792

因此，G43-P0 中 DB-derived scalar norm schedule 不是 access 所必需，也没有相对 literal equal mean 的 >0.05 material advantage。

不能误写为什么

这不是：

两臂精确相等
MEAN 显著优于 DBNORM
所有 adaptive scale 都无用
所有 source 都不需要 direction balancing

它只关闭 exact G43-P0 中的 DB-derived scalar schedule。

当前接受 route
COMMON_NATIVE6_FAST_ANCHOR
→ NATIVE6_G31_EQUAL_MEAN_NO_SHADOW_NO_SLOW

已经删除：

post-anchor standalone slow critic
DB angular vector
DB-derived scalar norm
全部 post-anchor DB shadow computation

仍然保留：

realized-successor target
immediate/successor decomposition
shared true-state baseline
independent per-channel normalization
literal equal-channel mean
common fast anchor
下一动作
CONTINUOUS_ROSTER_NATIVE_SIX_G31_CHANNEL_SCALE_NORMALIZATION_ATTRIBUTION_G44_DESIGN_ASSERTION_AUDIT

G44 只比较：

reference:
    immediate / successor 各自中心化并各自缩放

null:
    仍分别中心化
    但使用一个 pooled scale

两臂继续使用：

0.5 × (g_I + g_S)

不重新引入 DB，不改变 target、baseline、source、Adam、PPO 或证据单位。

其他 realized-tail、decomposition、baseline、common anchor、broader process/horizon/capacity、可识别非 G33 UAV 与 recurrence/EHC 方向继续保持 live 或 parked。G33 永久冻结。本裁决不授权代码或计算。