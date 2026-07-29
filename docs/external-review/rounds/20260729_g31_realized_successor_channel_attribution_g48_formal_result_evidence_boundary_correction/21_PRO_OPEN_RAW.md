CORRECTED_EVIDENCE_CONFORMANCE

CORRECTED_EVIDENCE_CONFORMANCE=CONFORMS

IMMUTABLE_RESULT_RECORD
formal_source_commit=
4abbee66d43ffd592d65624121121bc0109882ab

aligned_implementation_commit=
d96f8f29367b55b5ea655b984631d6064877e237

alignment_stage_commit=
617414f9a175f044eecfbfec4e4b170c6990b47f

immutable_formal_branch=
DUPLICATED_IMMEDIATE_CREDIT_SUFFICIENT_G48

SCIENTIFIC_DISPOSITION=
SUPPORTED_RETAINED_DUPLICATED_IMMEDIATE_POST_ANCHOR_CREDIT_SUFFICIENCY_G48

The corrected note now supplies every field identified as missing in the prior review: the immutable analysis branch; operational, source, activation and arm-access predicates; noninferiority and material-advantage predicates; primary, per-capacity and every registered component CI95; thresholds; configuration; seed block; terminal manifest digests; the analysis digest; and all six final-checkpoint digests. These are copied from the existing formal artifacts without rerunning, recomputing, filtering, relabelling or rewriting them.

First-match reproduction
operational_valid=true
source_valid=true
treatment_activation_valid=true

reference_access_pass=true
reference_access_confident_fail=false

null_access_pass=true
null_access_confident_fail=false

duplicated_immediate_noninferior=true
material_realized_successor_advantage=false

Therefore:

The invalid branch does not fire.

The source/reference-failure branch does not fire.

Both arms pass access and duplicated-immediate noninferiority is true.

The frozen selector stops at DUPLICATED_IMMEDIATE_CREDIT_SUFFICIENT_G48.

The result is not inferred from the copied branch label alone: the copied predicates and confidence intervals independently reproduce the same first-match selection. The G48 index identifies the exact reference and null arms, the zero-successor-read boundary, the paired confidence plan and the immutable branch order.

Formal inventory and seed law
arms=
NATIVE6_G31_IMMEDIATE_REALIZED_SUCCESSOR
NATIVE6_G31_DUPLICATED_IMMEDIATE

replicates=3
branch_updates_per_arm=100
environments_per_update=8
PPO_passes=2

training_transitions=230400
evaluation_transitions=165888
total_real_transitions=396288
optimizer_steps=1200

evaluation_cells=72
episodes_per_cell=48
bootstrap_resamples=10000

H=48
K_search=0
hypothetical_transitions=0
checkpoint_selection=final_only

branch_ledger_seed=10481000
branch_action_seed=10482000
branch_gradient_probe_seed=10483000
evaluation_ledger_seed=10484000
evaluation_process_seed=10485000
evaluation_action_seed=10486000
bootstrap_seed=10487048

The backend was the required CPU C++ implementation with no Python fallback, two workers and one thread per worker.

Registered statistical result

The estimand is:

Δ
succ
	​

=U
IMMEDIATE+SUCCESSOR
	​

−U
DUPLICATED IMMEDIATE
	​

.
Contrast	Reference minus null CI95
Equal-capacity pooled primary	[-0.0099297350, -0.0031302390, 0.0006496391]
Capacity 6	[-0.0030475732, -0.0000237678, 0.0032257702]
Capacity 8	[-0.0117158886, -0.0034464184, 0.0011528930]
Capacity 12	[-0.0148397661, -0.0059030163, -0.0006160106]

Every registered component UCB is below approximately 0.004003, far beneath the frozen 0.05 noninferiority margin. Both arms satisfy the complete absolute-access contract.

Strongest supported proposition

Under the exact post-anchor G48-P0 source, initialization, Adam exposure and formal evidence inventory, the complete realized-successor channel package is removable in favor of the registered duplicated-immediate null. The duplicated-immediate arm preserves fixed/random capacity-6/8/12 access and is noninferior to the immediate-plus-realized-successor reference by the frozen 0.05 margin.

The treatment includes the successor target’s effects on gradient direction, global credit magnitude, Adam moments and later trajectories; it is not merely a test of whether the normalized target rows differ. The duplicated-immediate construction is mathematically immediate-only while retaining two separately materialized channel losses and the registered two-channel bookkeeping.

Accepted post-anchor route
COMMON_NATIVE6_FAST_ANCHOR
→ NATIVE6_G31_DUPLICATED_IMMEDIATE

Retained:

native-six current-state actor
no learned actor carry
no slow critic
no baseline module
immediate reward target
two separately materialized immediate channels
separate per-channel centering
independent population-RMS normalization
literal 0.5 equal-channel composition
common entropy
registered actor Adam

Retired only inside G48-P0:

realized-successor target G_(t+1)
realized-successor channel gradient
its direction/magnitude contribution
its downstream Adam-conditioning contribution
its necessity for access
its >0.05 material advantage over duplicated immediate
COUNTEREXAMPLES_AND_EXCLUSIONS
Post-anchor sufficiency is not fresh end-to-end sufficiency

Both arms start from accepted common fast anchors. G48 does not prove that a newly initialized controller trained end to end with duplicated-immediate credit reaches the same result. The common anchor may already encode useful representation or behavior.

Duplicated immediate is not TEAM-GAE1

The null retains:

two separately materialized channel losses
separate centering
independent RMS normalization
literal equal-channel composition
the accepted post-anchor initialization
the registered PPO/Adam exposure

It is not ordinary shared-team GAE1. G48 therefore does not reverse G40’s TEAM-GAE1 failure or establish ordinary-credit equivalence.

No exact single-channel structural result

Because the two null channels and their gradients are bitwise equal,

2
1
	​

(g
I
1
	​

	​

+g
I
2
	​

	​

)=g
I
	​

.

Nevertheless, G48 formally tested the registered two-channel duplicated-immediate implementation. It does not itself prove that the second target tensor, second loss construction, second backward construction and associated artifact fields can be deleted bitwise without affecting the optimizer path.

No universal claim about future information

The null still observes every reward at its physical time. It removes the earlier-step realized-tail target, not later rewards from the training trajectory.

The result does not establish:

future consequences are universally irrelevant
delayed tasks never need temporal credit
all history or recurrence is redundant
all ordinary estimators are sufficient

It closes only the complete registered realized-successor channel package in the exact G48 post-anchor comparison.

No deployment-input conclusion

Both arms have the same native-six deployment actor and neither consumes G_(t+1) at deployment. G48 is a training-credit result, not a new deployment-information or policy-class result.

No superiority relabelling

The primary median and several component intervals favor the null numerically, and the capacity-12 primary interval is entirely below zero. No null-superiority branch was registered. The scientific result remains removability/noninferiority, not a claim that duplicated immediate is generally superior.

G44 is not retroactively invalidated

G44 supported independent relative scaling when two semantically distinct channels were present. G48 shows that the accepted route no longer needs the realized-successor channel. In the duplicated-immediate null, the two normalized channels are identical, so there is no nontrivial relative channel geometry. G48 does not rewrite the earlier G44 result; it changes which earlier mechanism is consumed by the smallest accepted route.

Scope exclusions

The result remains bounded to:

H=48
capacity-8 fixed-process training
fixed/random capacity-6/8/12 evaluation
three accepted anchor replicates
100 post-anchor updates per arm
registered Adam/PPO configuration
G34-P0 bounded process family

It establishes no arbitrary process, horizon, capacity, optimizer, task, UAV, asynchronous-skill-lifetime or intrinsic-reward claim. Recurrence remains live for sources containing task-relevant information absent from current observations. G33 remains permanently abandoned.

CDC_PORTFOLIO_LEDGER_EDITS

These are exact scientific recording instructions; they do not authorize repository mutation.

CONJECTURES.md

Replace the current C-CONTINUOUS-ROSTER status paragraph with:

Markdown
- Status: supported and retained at G48 as a usable native-six-coordinate,
  no-carry, post-anchor no-slow/no-DB/no-baseline, duplicated-immediate,
  separately centered and independently RMS-normalized continuous-roster
  training route for the registered H=48, capacity-6/8/12 bounded-process toy
  family.

Insert:

Markdown
- Formal realized-successor attribution evidence: G48 compares the accepted
  baseline-free immediate-plus-realized-successor reference against a
  duplicated-immediate null that never reads `G_(t+1)` into actor credit.
  Both arms pass the complete access contract. Reference-minus-null pooled
  CI95 is
  [-0.0099297350, -0.0031302390, 0.0006496391]; capacity-6/8/12 CI95 are
  [-0.0030475732, -0.0000237678, 0.0032257702],
  [-0.0117158886, -0.0034464184, 0.0011528930], and
  [-0.0148397661, -0.0059030163, -0.0006160106].
  Duplicated-immediate noninferiority holds and material
  realized-successor advantage is false.

Replace the accepted post-anchor boundary with:

Markdown
- Accepted post-anchor training boundary:
  `COMMON_NATIVE6_FAST_ANCHOR →
  NATIVE6_G31_DUPLICATED_IMMEDIATE`.
  Retain the native-six actor, immediate reward credit, separate channel
  centering, independent population-RMS normalization, literal equal-channel
  composition and common entropy. Delete the complete realized-successor
  channel package from the retained post-anchor route.

Append to the retired-alternatives paragraph:

Markdown
- G48 local closure: the complete realized-successor channel package is not
  required for access and supplies no >0.05 material advantage over the exact
  duplicated-immediate null inside G48-P0. This does not establish fresh
  end-to-end immediate-only sufficiency, TEAM-GAE1 sufficiency, exact
  single-channel structural equivalence or universal future-information
  redundancy.

Replace the strongest remaining training-explanations paragraph with:

Markdown
- Strongest remaining training explanations: the accepted route still depends
  on the common fast anchor, immediate-target centering/RMS normalization,
  literal immediate-gradient composition and the frozen Adam/PPO exposure.
  Exact collapse of the duplicated two-channel bookkeeping to one channel and
  fresh end-to-end training of the fully simplified route remain untested.

Under C-CREDIT, append:

Markdown
- G48 update: the complete realized-successor channel package is locally
  removable from the accepted post-anchor route. This does not rewrite G31's
  paired G17/G18 result or G40's package-level advantage over TEAM-GAE1,
  because the G48 null is a normalized duplicated-immediate estimator rather
  than TEAM-GAE1. The smallest retained post-anchor credit object is now the
  normalized immediate channel under the registered common-anchor and Adam
  boundary.

The current conjecture file still describes the G43/G44 route and identifies the larger G31 package as retained, so G48 requires consolidation to the smaller accepted route.

IDEA_PORTFOLIO.md

Replace the C-CONTINUOUS-ROSTER row with:

Markdown
| C-CONTINUOUS-ROSTER | supported retained at G48: native-six no-carry,
post-anchor no-slow/no-DB/no-baseline, duplicated-immediate,
independently normalized bounded-process route | Both G48 arms pass access;
reference-minus-null pooled CI95 is
[-0.0099297350, -0.0031302390, 0.0006496391], every registered component UCB
is below 0.004003, duplicated-immediate noninferiority holds and material
realized-successor advantage is false. | Retain
`COMMON_NATIVE6_FAST_ANCHOR → NATIVE6_G31_DUPLICATED_IMMEDIATE`.
Future work requires new user authority: exact single-channel structural
collapse, fresh end-to-end simplified training, broader transport or an
identifiable non-G33 UAV source. |

Replace the C-CREDIT row with:

Markdown
| C-CREDIT | G31/G40 package-level evidence remains supported, while the
complete realized-successor channel is locally removable in G48-P0 | G48
shows that the normalized duplicated-immediate post-anchor route preserves
access and is noninferior. This isolates the earlier G40 advantage away from
the realized-successor channel itself; it does not make TEAM-GAE1 sufficient
or invalidate G31 on G17/G18. | Preserve immediate normalization, common
anchor and optimizer conditioning as live explanations. Exact one-channel
deduplication and fresh end-to-end immediate-only training require a later
grant. |

Append:

## G48 formal result update

g48_formal_source_commit=
4abbee66d43ffd592d65624121121bc0109882ab

g48_formal_branch=
DUPLICATED_IMMEDIATE_CREDIT_SUFFICIENT_G48

g48_scientific_disposition=
SUPPORTED_RETAINED_DUPLICATED_IMMEDIATE_POST_ANCHOR_CREDIT_SUFFICIENCY_G48

g48_scientific_route=
COMMON_NATIVE6_FAST_ANCHOR_to_NATIVE6_G31_DUPLICATED_IMMEDIATE

g48_supported_unit=
duplicated_immediate_post_anchor_access_and_0.05_noninferiority

g48_failed_closed=
complete_realized_successor_channel_package_required_for_access_or_material_advantage_inside_G48_P0

g48_primary_ci95=
[-0.009929735010121536,-0.003130239010674661,0.0006496391334839275]

g48_conclusion_bearing_iterations_consumed=37
g48_iterations_remaining=0
g48_next_action=NONE_BALANCE_EXHAUSTED

Set the portfolio terminal-disposition field to the single token declared in Section 5. The current portfolio still identifies G40/G44 as the latest retained route and G45 as the pending action, so those stale active-route fields must be superseded.

RESEARCH_DIRECTION_LEDGER.md

Supersede the stale G45 design-only active marker with:

## G48 formal result update

g48_row=
continuous-roster native-six duplicated-immediate post-anchor credit route

g48_row_status=SUPPORTED_RETAINED

g48_row_evidence=
docs/research/cdc/EVIDENCE_NOTES/20260729_G31_REALIZED_SUCCESSOR_CHANNEL_ATTRIBUTION_G48_FORMAL_RESULT.md
|docs/external-review/rounds/20260729_g31_realized_successor_channel_attribution_g48_formal_result_evidence_boundary_correction/21_PRO_OPEN_RAW.md

g48_row_claim_ceiling=
exact post-anchor G48-P0 source, accepted anchors, H48, capacity-6/8/12
fixed/random process family, registered Adam exposure and duplicated-immediate
two-channel null; no fresh-training, TEAM-GAE1, arbitrary-task, UAV or
universal-future-information claim

g48_scientific_route=
COMMON_NATIVE6_FAST_ANCHOR_to_NATIVE6_G31_DUPLICATED_IMMEDIATE

g48_supported_unit=
duplicated_immediate_access_and_noninferiority_inside_G48_P0

g48_failed_closed=
complete_realized_successor_channel_package_necessity_or_material_advantage_inside_G48_P0

g48_primary_ci95=
[-0.009929735010121536,-0.003130239010674661,0.0006496391334839275]

g48_capacity_ci95_6=
[-0.003047573242081267,-0.000023767837701393361,0.003225770189697182]

g48_capacity_ci95_8=
[-0.011715888608560947,-0.0034464183754958928,0.0011528930163752981]

g48_capacity_ci95_12=
[-0.014839766149231546,-0.005903016317533048,-0.0006160106466084341]

g48_conclusion_bearing_iterations_consumed=37
g48_iterations_remaining=0
g48_next_action=NONE_BALANCE_EXHAUSTED

Add under FAILED_CLOSED:

Markdown
| G48-P0 中 complete realized-successor channel package 对 access 的必要性
或相对 duplicated-immediate null 的 >0.05 material advantage |
`FAILED_CLOSED` | Reference 与 null 均通过完整 access；reference-minus-null
pooled CI95 为
[-0.0099297350, -0.0031302390, 0.0006496391]，全部 component UCB
低于 0.004003，duplicated-immediate noninferiority 成立，material
realized-successor advantage 为 false。 | 不得写成“TEAM-GAE1 已充分”
“所有 delayed credit 都无用”“fresh immediate-only training 已成立”
或“所有任务不需要未来信息”。 |

Preserve under OPEN_UNTESTED:

Markdown
| G48 duplicated-immediate route 的 exact single-channel structural collapse |
`OPEN_UNTESTED` | 两条 immediate target、normalized row 和 channel
gradient 在冻结 null 中逐字节相等，但尚未完成删除第二 channel loss、
backward construction 与 artifact schema 的 exact optimizer-equivalence
证明。 | 仅在新的用户授权与余额下复活；优先零轨迹依赖证明。 |

| 从随机初始化开始的 fully simplified immediate-only/no-baseline training |
`OPEN_UNTESTED` | G48 是 accepted-common-anchor 之后的比较，不能回答完全
移除历史训练路径后是否仍可学习。 | 需要 function-、source-、
interaction- 与 optimizer-exposure-matched fresh-training contract。 |

The ledger defines status changes at the smallest supported or refuted unit; G48 therefore supports the duplicated-immediate route and closes only the exact realized-successor package claim.

PORTFOLIO_DELTA_AND_VALID_RESULT_DISPOSITION

VALID_RESULT_DISPOSITION=COMPLETE_BALANCE_EXHAUSTED

Before scientific acceptance of G48, the grant had 36 consumed conclusion-bearing iterations and one remaining. The G48 evidence record specifies a cost of one upon External-Pro acceptance. Acceptance therefore yields:

conclusion_bearing_iterations_consumed=37
remaining_conclusion_bearing_iterations=0

Balance exhaustion has precedence over candidate availability, and terminal balance completion carries no scheduled action.

The preserved portfolio is:

Direction	Terminal state	Reactivation condition
G48 duplicated-immediate post-anchor route	Supported and retained	Reusable only inside its registered source/anchor/optimizer boundary
Complete realized-successor channel necessity	Failed closed in G48-P0	A distinct identified source or comparator—not more G48 seeds or budget
Exact single-channel collapse	Live, unscheduled	New grant; exact graph/gradient/Adam equivalence proof
Fresh end-to-end simplified training	Live, unscheduled	New grant; matched fresh initialization and exposure
Immediate centering/RMS normalization	Retained, not isolated	Matched normalization ablation under new authority
G44 relative scaling result	Supported in its earlier two-distinct-channel boundary	Reactivate when a future route again retains distinct channels
Common fast anchor	Live, unscheduled	Fresh branch-start comparison
Broader process/horizon/capacity	Live, unscheduled	Change one source axis at a time
Identifiable non-G33 UAV transport	Parked	Physically feasible, load-bearing, support-valid source
Recurrence/EHC	Parked	Source with relevant information absent from current observation
Asynchronous skill lifetime/intrinsic reward	OUT_OF_SCOPE_FROZEN	Explicit later scope transition
G33 lineage	Permanently frozen	No reactivation
CURRENT_SCHEDULED_ACTION_IF_CONTINUE
current_scheduled_action=NONE
reason=conclusion_bearing_balance_exhausted

No implementation, evidence disclosure, design audit, proof execution, nonformal run or formal run is scheduled by this disposition.

EXECUTABLE_SCIENTIFIC_BOUNDARY
active_grant_next_boundary=NONE
remaining_conclusion_bearing_iterations=0

H=48
K_search=0
hypothetical_transitions=0
new_real_transitions=0
new_optimizer_steps=0
new_bootstrap_resamples=0

The terminal accepted scientific boundary is:

source=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_REALIZED_SUCCESSOR_CHANNEL_ATTRIBUTION_G48_P0

accepted_route=
COMMON_NATIVE6_FAST_ANCHOR
→ NATIVE6_G31_DUPLICATED_IMMEDIATE

retired_local_unit=
complete_realized_successor_channel_package_necessity_or_material_advantage

claim_ceiling=
post-anchor, source-local, finite-budget duplicated-immediate sufficiency only

No successor is active within the exhausted grant.

For preservation only—not as a scheduled action—the smallest future reactivation question is:

Can the two byte-identical duplicated-immediate channels, second channel loss, second backward construction and associated artifact fields be structurally collapsed to one immediate channel while preserving the actor gradient, Adam state, actions and final actor checkpoint exactly?

That question requires a new user-authorized balance. File organization, tensor layout, serialization and proof-test placement would be implementation-only; the exact gradient/Adam equivalence would be scientific. No such work is authorized here.

中文简报
修正证据边界=完整
G48不可变分支=DUPLICATED_IMMEDIATE_CREDIT_SUFFICIENT_G48

修正后的 evidence note 已经提供：

analysis branch
source / activation / access predicates
noninferiority 与 material-advantage predicates
primary、capacity 与全部 component CI
thresholds
formal inventory
seed block
train/evaluation/analysis digests
六个 final checkpoint digests

因此可以完整重放 first-match：

operational valid
source valid
reference access pass
null access pass
duplicated-immediate noninferior
material successor advantage=false

正式主区间为：

reference - duplicated immediate
=
[-0.0099297350, -0.0031302390, 0.0006496391]

全部 component UCB 低于约 0.004003，远低于 0.05 margin。

最强结论是：

在 exact G48-P0 post-anchor 边界内，完整 realized-successor channel
package 可以由 duplicated-immediate null 替代；它不再是 access 所必需，
也没有 >0.05 material advantage。

当前最小路线是：

COMMON_NATIVE6_FAST_ANCHOR
→ NATIVE6_G31_DUPLICATED_IMMEDIATE

这不能写成：

TEAM-GAE1 已充分
fresh end-to-end immediate-only training 已成立
所有 delayed credit 都无用
所有任务都不需要未来信息或 recurrence
null 显著优于 reference
UAV transport 已成立

G48 接受后，结论性余额从 1 降为 0。因此当前 grant 终止，不再调度任何动作。Exact single-channel collapse、fresh simplified training、broader process/horizon/capacity、可识别非 G33 UAV transport 与 hidden-information recurrence 均保留为未来新授权下的 live 或 parked 方向；G33 永久冻结。
