1. REGISTERED_RESULT_CONFORMANCE

Registered branch confirmed without modification:

MIXED_UNDERPOWERED_HISTORY_PROXY_COHERENCE_G37

The formal package is mechanically valid and conclusion-bearing:

formal=true
operational_valid=true
operational_errors=[]
replicates=3
capacities=6|8|12
cells=36
episodes=4608
real_transitions=221184
training_transitions=0
optimizer_steps=0
bootstrap_resamples=10000
H=48
K_search=0

The exact formal G36 joint-donor package was read rather than rerun; the exact G35 CS final checkpoints, source ledgers, episode identities, factorized tapes, action streams, lifecycle transitions, 48-step traces, same-source preflight, artifact digests and first-match branch were independently revalidated. The preceding code-science audit returned AUDIT_DISPOSITION=ALIGNED.

The conclusion-bearing result is:

Quantity	CI95 / value	Registered interpretation
Fixed utility, capacity 6	[0.901574, 0.932878, 0.951614]	access floor passes
Fixed utility, capacity 8	[0.888893, 0.928577, 0.949323]	LCB misses 0.90; no confident failure
Fixed utility, capacity 12	[0.889193, 0.927286, 0.946804]	LCB misses 0.90; no confident failure
Random utility, capacity 6	[0.900718, 0.933511, 0.952022]	access floor passes
Random utility, capacity 8	[0.885488, 0.926627, 0.947792]	LCB misses 0.90; no confident failure
Random utility, capacity 12	[0.890537, 0.926921, 0.945684]	LCB misses 0.90; no confident failure
Fixed stochastic pooled	[0.847873, 0.873239, 0.886657]	passes 0.80
Random stochastic pooled	[0.852128, 0.878716, 0.892775]	passes 0.80
Minimum fixed/random replicate mean	0.892938 / 0.891882	both pass 0.85
Primary joint − factorized	[0.006391, 0.021599, 0.051536]	positive direction; UCB misses noninferiority by 0.001536
Largest component UCB	0.090066	diagnostic only

Accordingly:

source_valid=true
g36_reference_valid=true
factorized_access_pass=false
factorized_access_confident_fail=false
coherence_noninferior=false
material_coherence_loss=false

Neither conclusion-bearing branch fired. The mixed branch is therefore immutable.

2. SCIENTIFIC_DISPOSITION
scientific_disposition=
MIXED_DIRECTIONAL_FACTORIZATION_COST_RETAIN_G36_CLOSE_G37_P0
Exact proposition added beyond G36

G37 adds one narrow, statistically supported observation:

For the exact formal G35 CS final checkpoints, exact G36 donor bank, registered G32/G34 source family, capacities 6/8/12, H=48, and frozen G37 four-column factorization law, the G36 joint donor has a positive average utility advantage over the factorized donor on the equal-capacity-weighted random deterministic primary estimand.

The primary interval:

Δ
coh
	​

=U
joint
	​

−U
factorized
	​

∈[0.006391, 0.051536]

lies entirely above zero. Thus strict zero average effect under this frozen primary estimand is not retained. The median effect is approximately 0.0216.

That directional result does not close either registered scientific decision:

It does not establish factorized-donor noninferiority because the UCB is 0.05153553 > 0.05.

It does not establish a material coherence benefit because the LCB is 0.00639057 < 0.05.

It does not establish factorized absolute access because capacity-8 and capacity-12 deterministic LCBs miss 0.90.

It does not establish confident access failure because every corresponding utility UCB remains well above 0.90.

Binding interpretation

The exact scientific update is:

supported:
a directional checkpoint-level cost of the complete G37 factorization

not supported:
factorized marginal sufficiency
joint-donor coherence as materially load-bearing
factorized access or confident no-access

The accepted usable algorithm boundary therefore remains G36, not G37:

The actual target history bundle may be replaced by the internally coherent, active-count-conditioned G36 donor generator.

The G37 factorized generator is neither accepted as a deployment reduction nor rejected as unusable.

Smallest retained and retired units

Retained:

G36’s actual-history sensor-substitution result remains fully intact.

Cross-column donor coherence or multivariate distributional consistency remains a live explanation.

Marginally in-support factorized filling remains a live but unresolved reduction.

Current load/mix, capabilities, active-set aggregation, active count, mask, within-step prefix and no-carry actor remain retained.

Lifecycle ownership, JOIN/LEAVE/REJOIN semantics, terminal deletion and survivor continuity remain retained.

The centralized critic and its true-time input remain retained.

G31 realized-future-tail credit remains training provenance, not a mechanism resolved by G37.

Configured capacities 6/8/12, H=48, and the bounded G34 process scope remain the complete claim domain.

Fresh retraining may adapt to six-coordinate or factorized inputs; G37 does not test that hypothesis.

Retired only in the smallest statistical sense:

The exact point-null that G36 joint-donor and G37 factorized-donor executions have zero average difference on the frozen pooled random deterministic primary estimand.

This does not warrant a new FAILED_CLOSED mechanism entry. The scientifically important alternatives—factorized sufficiency and materially load-bearing coherence—both remain unresolved.

G37-P0 closure

The exact G37-P0 evidence package is closed. Its frozen mixed branch explicitly preserves both explanations and forbids rescue by changing seeds, margin, donor law, episode count, checkpoint or evidence volume. The project’s durable result semantics likewise require mixed results to preserve uncertainty rather than be rescued through post-result budget or threshold changes.

3. COUNTEREXAMPLES_AND_EXCLUSIONS
Why the positive primary interval does not select coherence

The primary interval is directionally positive but straddles the materiality boundary:

LCB = 0.00639057
UCB = 0.05153553
margin = 0.05

It excludes exact zero average loss under the frozen resampling plan, but it is compatible with both:

a small, practically nonmaterial factorization cost; and

a material cost just above five utility points.

The experiment was designed to distinguish those cases through the complete interval, not the median or lower bound alone.

Why the deterministic access misses matter

Capacity 8 and 12 miss the deterministic 0.90 LCB under both fixed and random processes. The misses are approximately:

capacity 8 fixed   0.01111 below floor
capacity 8 random  0.01451 below floor
capacity 12 fixed  0.01081 below floor
capacity 12 random 0.00946 below floor

Yet their UCBs range from roughly 0.946 to 0.949, so this is uncertainty around absolute access, not confident no-access. Capacity 6 barely passes both deterministic floors. No monotone capacity law should be fitted from three configured capacities and overlapping intervals.

Why stochastic and replicate gates do not rescue access

The stochastic gates use a lower 0.80 floor and pool capacities. The minimum-replicate gate uses a 0.85 mean floor. Their passage shows that factorization did not cause catastrophic or broadly unstable collapse, but neither gate substitutes for the stricter capacity-specific deterministic 0.90 requirement. The frozen selector correctly leaves factorized_access_pass=false.

Diagnostic component intervals

At least one component interval has UCB 0.090066, meaning a locally material loss remains plausible. But no component LCB exceeded 0.05; otherwise material_coherence_loss would have been true. Those intervals indicate heterogeneity across utility, event-window, process-segment or action-mode quantities, but the design explicitly made them non-rescuing diagnostics. They cannot select the load-bearing branch after the primary predicates remain unresolved.

Strongest remaining alternate explanations

Finite checkpoint-replicate uncertainty. The hierarchy contains only three independently trained checkpoint replicates. Episode resampling cannot manufacture additional checkpoint-level variation. That can explain why capacity-specific LCBs remain below access and why the primary interval narrowly crosses 0.05. It does not authorize adding replicates to G37-P0 after seeing the result.

Multivariate distribution shift. Each factorized column has the exact G36 active-count-conditioned empirical marginal and legal support, but the resulting four-column tuples need not belong to the joint source distribution. A performance loss can therefore reflect generic neural sensitivity to unseen cross-coordinate combinations rather than semantic use of lifecycle coherence. The design identified this limitation in advance.

Checkpoint specialization. The exact checkpoints were trained with target-coherent fields and then shown by G36 to tolerate a coherent donor. They were never trained under independent column factorization. Their positive average loss may therefore reflect learned correlation-sensitive weights rather than a capability requirement.

Retraining adaptation. A freshly trained actor that never receives the four history coordinates—or receives only constants that can be algebraically removed—may learn the direct current load/mix solution without any donor apparatus. G37 is a zero-training checkpoint intervention and cannot reject this explanation.

Explicit exclusions

G37 does not establish:

donor coherence as materially necessary;

marginal donor columns as sufficient;

individual necessity or redundancy of time, age, previous-action-0 or previous-action-1;

deletion of actor coordinates 6:10;

arbitrary independent noise robustness;

removal of within-column roster structure;

global task memorylessness;

history independence after retraining;

critic-time redundancy;

G31-credit redundancy;

arbitrary capacities, horizons, counts or process laws;

UAV transport;

asynchronous skill lifetime;

intrinsic-reward value.

G33 and every full-ledger/static-preposition derivative remain abandoned and cannot be selected or renamed.

4. CDC_PORTFOLIO_LEDGER_EDITS
4.1 Replace the complete C-CONTINUOUS-ROSTER block in CONJECTURES.md
Markdown
## C-CONTINUOUS-ROSTER — Continuous control under dynamic membership

- Status: supported and retained at the G36 boundary as a usable
  actual-history-sensor-substituted, configured-capacity,
  bounded-random-process continuous dynamic-roster test version for the
  registered 48-step capacity-6/8/12 toy family. G37 does not extend this
  accepted boundary.
- Claim: a capacity-shape-independent no-carry actor trained only at capacity 8
  remains usable at configured capacities 6, 8 and 12 across the fixed G32
  process and bounded G34-P0 random process. For the exact formal G35 CS final
  checkpoints, the actor's actual true-time, lifecycle-age and previous-action
  sensor bundle may be replaced by the frozen G36 active-count-conditioned,
  internally coherent source-valid donor generator.
- Retained actual actor information: capability, anonymous priority, current
  load and target mix, raw log1p(active_count), active mask and active-fraction
  autoregressive prefix.
- Retained surrogate interface: the four actor coordinates for age, two
  previous actions and time remain present. The accepted deployment boundary
  populates them through the exact coherent G36 donor law; this is sensor
  substitution rather than ten-to-six-dimensional architectural deletion.
- Formal immediate/delayed evidence: G31 passes the paired G17/G18 utility,
  spike-allocation, rotation, learned-gain and fresh-seed stability gates.
- Formal configured-capacity evidence: G32 supports strict-loadable
  capacity-6/8/12 deployment and exact common-active padding invariance.
- Formal bounded-process evidence: G34 supports zero-training transport from the
  fixed 12/24/36 process to its registered one-each-of-L/R/J/T random process.
- Formal current-state evidence: G35 freshly trains matched REC and CS arms.
  Both access; pooled REC-minus-CS CI95 is
  [-0.0173505, -0.0081213, 0.0007130], and every capacity-specific UCB is at
  most 0.0054082 against the 0.05 margin.
- Formal actual-history substitution evidence: G36 replaces actor time, age and
  previous-action fields with an independent coherent donor bundle. All
  fixed/random capacity-6/8/12 access gates pass. Primary
  registered-minus-substitution CI95 is
  [-0.0024790, 0.0001048, 0.0035749], and the largest component UCB is
  0.0075287.
- Formal coherence evidence: G37 independently samples and permutes each donor
  column while preserving every column's complete active-count-conditioned
  empirical marginal. Its primary joint-minus-factorized CI95 is
  [0.0063906, 0.0215989, 0.0515355]. This supports a directional factorization
  cost and rejects exact zero average effect on the frozen primary estimand, but
  neither noninferiority nor >0.05 material loss closes. Capacity-8/12 fixed
  and random deterministic access LCBs miss 0.90, while no confident-access-
  failure predicate fires. The terminal branch is
  MIXED_UNDERPOWERED_HISTORY_PROXY_COHERENCE_G37.
- Accepted deployment boundary: retain the coherent G36 donor generator.
  The G37 factorized generator is neither accepted nor confidently rejected.
- Retired alternatives: within the registered family, usable deployment does
  not require capacity-shaped learned parameters, capacity-specific retraining,
  checkpoint adapters, the exact fixed 12/24/36 schedule, atomic R+J, learned
  per-lifecycle actor carry, or acquisition of the target episode's actual
  time/age/previous-action bundle. G37 additionally retires only the exact
  zero-average-effect point null for its primary joint-minus-factorized
  estimand.
- Lifecycle boundary: active masks, likelihood ownership, environment lifecycle
  state, fresh initialization, temporary leave/rejoin, terminal deletion and
  survivor continuity remain part of the runtime contract.
- Scope: H=48; configured capacity is fixed within a trajectory and belongs to
  6/8/12; G34-P0 contains one each of L/R/J/T and three legal event orders; G36
  and G37 use their exact frozen donor distributions.
- Strongest remaining explanations: G37 may expose generic multivariate
  distribution-shift sensitivity or specialization of checkpoints trained on
  coherent inputs. Whether a freshly trained six-coordinate actor can delete
  the entire surrogate interface remains open.
- Critic and credit boundary: the critic retains true time, and the checkpoints
  retain G31 training provenance. G37 performs zero training and supplies no
  credit-comparator evidence.
- UAV boundary: temporary-service-loss G1 and charge-rotation G2 remain source
  non-identifiable. G33 and all derivatives remain abandoned by user
  instruction.
- Exclusions: arbitrary capacity/process/horizon, arbitrary filler robustness,
  architectural coordinate deletion, globally memoryless control, UAV
  usability, asynchronous skill lifetime, intrinsic-reward advantage,
  complete-algorithm superiority and G31-credit redundancy remain unsupported.
4.2 Append this bullet to C-REC
Markdown
- G37 update: the mixed factorization result does not reopen G35's rejection of
  learned actor carry or G36's rejection of actual target-history acquisition.
  Its positive primary contrast concerns the distribution of four execution-time
  nuisance coordinates for exact frozen CS checkpoints; it is not recurrence
  evidence. Cross-column donor coherence remains unresolved, and fresh
  six-coordinate retraining is the relevant architectural discriminator.

No C-CREDIT status change is warranted. G37 performs zero optimization and changes no credit estimator.

4.3 Replace the affected IDEA_PORTFOLIO.md rows
Markdown
| C-CONTINUOUS-ROSTER | supported retained at G36; G37 factorized reduction mixed and closed | G31/G32/G34/G35/G36 form the accepted configured-capacity, bounded-process, no-carry, actual-history-sensor-substituted test version. G37 yields a positive primary joint-minus-factorized CI95 [0.0063906, 0.0215989, 0.0515355], but capacity-8/12 deterministic access LCBs miss 0.90 and neither sufficiency nor material-coherence predicates close. | Retain the coherent G36 donor boundary. Do not extend G37-P0 by seeds or evidence volume. Next action: test fresh architectural deletion of coordinates 6:10 rather than further post-training donor-factorization peeling. |
| C-REC | sufficient in exact memory sources; learned carry and actual target-history acquisition remain closed in G35/G36-P0 | G37 does not reinstate recurrence. Its mixed result concerns exact-checkpoint sensitivity to factorized nuisance inputs, not cross-step neural state. | Reactivate recurrence only on an identified source containing task-relevant information absent from current observations and a matched material recurrent advantage. |

Replace the terminal block with:

completed_action=CONTINUOUS_ROSTER_HISTORY_PROXY_COHERENCE_G37_FORMAL_ITERATION_28
source_family=CONTINUOUS_ROSTER_HISTORY_PROXY_COHERENCE_G37_P0
formal_disposition=MIXED_UNDERPOWERED_HISTORY_PROXY_COHERENCE_G37
scientific_disposition=MIXED_DIRECTIONAL_FACTORIZATION_COST_RETAIN_G36_CLOSE_G37_P0
next_action=CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_DESIGN_ASSERTION_AUDIT
authorization_status=active_twenty_iteration_toy_first_uav_promotion_chain
conclusion_bearing_iterations_consumed=28
iterations_remaining=9

Replace the final continuous-roster paragraph with:

Markdown
Formal G32 supports capacity-6/8/12 strict-load and padding invariance. G34
supports fixed-to-bounded-random process transport. G35 closes learned actor
carry as required or materially advantageous, and G36 shows that the exact G35
CS checkpoints do not need the target episode's actual time/age/previous-action
sensors when supplied with the coherent G36 donor. Formal G37 factorizes the
four donor columns. Its primary joint-minus-factorized CI95 is
[0.0063906, 0.0215989, 0.0515355], establishing a directional average
factorization cost but resolving neither the 0.05 materiality decision nor
capacity-8/12 deterministic access. G37-P0 closes mixed without
evidence-volume rescue; the accepted boundary remains G36. The next scientific
action is `CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_DESIGN_ASSERTION_AUDIT`,
which tests fresh architectural deletion rather than continued exact-checkpoint
proxy perturbation.
4.4 Update RESEARCH_DIRECTION_LEDGER.md

Replace the supported continuous-roster row with:

Markdown
| 连续动态 roster 的跨容量、随机过程、current-state 与实际历史传感替代 | `SUPPORTED_RETAINED` | G31/G32/G34/G35/G36 在已登记 H=48、capacity 6/8/12 toy family 中形成当前可用测试版：G35 关闭 learned actor carry，G36 支持以内部一致的 source-valid donor 替代目标真实 time/age/previous-action sensors。G37 的完整四列 factorization 产生正向平均损失，但正式分支为 mixed，未扩展接受边界。 | 不能推出四列 factorized donor 已足够、joint coherence 具有 >0.05 material necessity、十维到六维结构删除、任意 filler、全局 memoryless、任意容量/过程/horizon、UAV transport 或 G31 credit 冗余。 | [G36 正式结果](EVIDENCE_NOTES/20260726_CONTINUOUS_ROSTER_HISTORY_PROXY_FREE_CS_G36_FORMAL_RESULT.md)；[G37 正式结果](EVIDENCE_NOTES/20260726_CONTINUOUS_ROSTER_HISTORY_PROXY_COHERENCE_G37_FORMAL_RESULT.md)；[第 28 轮报告](../../report/ITERATION_28.md) |

Replace the open coherence row with:

Markdown
| G36 donor 的跨列 coherence 与 factorized marginal sufficiency | `OPEN_UNTESTED` | G37 primary joint-minus-factorized CI95 为 [0.0063906, 0.0215989, 0.0515355]，方向上支持 joint donor 较好；但 UCB 略高于 0.05，LCB 远低于 0.05，且 capacity-8/12 deterministic access LCB 未过 0.90。 | G37-P0 已按 mixed 分支关闭，禁止通过扩 seed、episode 或证据量救援。现有证据既不能接受 factorized donor，也不能把 coherence 写成 materially load-bearing。 |

Add this open direction:

Markdown
| fresh six-coordinate actor 的结构删除与重新训练适应 | `OPEN_UNTESTED` | 在保持 current load/mix、capability、active set、prefix、critic、G31 credit、G32/G34 source 与 paired exposure 时，重新训练一个可精确折叠为六输入的 no-carry actor，是否保持 fixed/random capacity-6/8/12 access 并对完整十输入 CS 非劣。 | G35/G36/G37 都使用十输入 checkpoint；G37 的 mixed loss 可能只是 coherent-input checkpoint 对 factorized joint OOD 的敏感性，不能回答重新训练后的结构删除。 |

Replace longitudinal summary item 5 with:

Markdown
5. G32 支持 capacity-6/8/12 strict-load，G34 支持固定过程到有界随机
   roster process transport，G35 关闭 learned actor carry，G36 支持用内部一致
   donor 替代目标真实 history sensors。G37 破坏 donor 四列的 shared snapshot
   与 shared row alignment 后，得到正向但跨越 0.05 materiality 边界的 primary
   interval，同时 capacity-8/12 deterministic access 未闭合；正式结论为 mixed。
   因此 G36 仍是接受边界，G37-P0 不扩证据救援。下一边界改为 fresh
   six-coordinate actor 的结构删除，而不是继续细分 donor proxy。

Do not modify ALGORITHM_PRINCIPLES.md. G37 is a local mixed result, not a new cross-experiment rule.

5. ONE_NEXT_ACTION
CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_DESIGN_ASSERTION_AUDIT
Decision

Do not extend G37 with more replicates, episodes or bootstrap draws. Its first-match contract explicitly closes the mixed package without seed or evidence-volume rescue.

Do not immediately perform another partial donor intervention such as “shared snapshot but independent rows” or “independent snapshots but shared permutation.” Such probes would localize an artificial surrogate’s correlations while still leaving the deployment architecture at ten coordinates plus donor machinery.

The selected successor instead tests the strongest remaining practical explanation:

The G37 loss may be checkpoint specialization to coherent ten-coordinate inputs; after fresh training, the four nuisance coordinates and the complete donor generator may be structurally removable.

Why this is the cheapest decision-changing successor

The design audit itself requires zero compute.

It can delete four actor inputs and the entire donor generator, rather than merely simplify one donor correlation.

It directly tests the retraining explanation left open by G37.

It reuses the identified G32/G34 source family rather than risking another source-identifiability failure.

It holds G31 credit fixed, avoiding a simultaneous representation/credit confound.

It is more decision-relevant than expanding capacity or process support before the accepted actor interface is settled.

It does not reactivate G33.

The action follows the project preference for replacement and simplification over continued module or apparatus accumulation.

6. EXECUTABLE_SCIENTIFIC_BOUNDARY
next_boundary=
CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_DESIGN_ASSERTION_AUDIT
One exact design-audit question

Can a conclusion-bearing fresh paired comparison be frozen between:

FULL10_CS — the G35-style no-carry actor receiving the ten registered actor coordinates, including actual lifecycle age, two previous actions and normalized time; and

FOLD6_CS — an otherwise parameter-, initialization-, critic-, credit-, source-, interaction- and optimizer-exposure-matched no-carry actor whose coordinates 6:10 are clamped during all training and evaluation to the fixed vector

c=(
2
1
	​

,
2
1
	​

,
2
1
	​

,
47
24
	​

),

and whose trained constant-coordinate affine contributions are then exactly folded into every affected bias so that the final deployment actor consumes only coordinates 0:6;

with both arms trained on the unchanged G32 capacity-8 fixed source and evaluated on the unchanged G34-P0 fixed/random capacity-6/8/12 family?

The audit must decide whether the folded six-coordinate actor retains every registered access gate and is noninferior to FULL10_CS by a frozen 0.05 margin, or whether actual history-coordinate information supplies a material finite-budget advantage after fresh matched training.

Why this comparison is identifying

The treatment separates:

fresh access to four history-shaped actor fields
                 versus
fresh training with no varying information in those fields

It does not repeat G37’s post-training multivariate OOD intervention.

The design audit must prove that:

both training arms use the same serialized graph and parameter count;

the constant-input arm has a live gradient path before folding;

all occurrences of coordinates 6:10 enter through foldable affine paths;

after training, folding those constant contributions into biases produces a six-coordinate actor with exactly equivalent pre-tanh means, action distributions and values;

no donor bank or surrogate tape remains in the folded deployment path.

If exact folding is impossible in the accepted graph, the proposed comparison must be rejected rather than approximated.

Inherited scientific boundary
H=48
training_source=unchanged_G32_capacity8_fixed_process
evaluation_source=unchanged_G34_P0_fixed_and_random_capacity6_8_12
actor_carry=CS_zero
critic=unchanged_true_current_state
credit=unchanged_G31_realized_future_tail
reward=unchanged
action_distribution=unchanged
active_set_log_count_mask_prefix=unchanged
fresh_paired_training=true
checkpoint_selection=final_only
G33_reactivation=forbidden

The primary estimand to be frozen is directionally:

Δ
info
	​

=U
FULL10_CS
	​

−U
FOLD6_CS
	​

,

with positive values favoring the four varying history fields.

The design audit must freeze mutually exclusive branches for:

operational invalidity
source/common-access failure
six-coordinate architectural reduction sufficiency
material full-information finite-budget advantage
mixed/underpowered evidence

A positive six-coordinate branch may support only the exact fresh-trained folded architecture in this source family. A negative branch may support only a finite-budget advantage for the four varying inputs; it may not establish task-level history necessity.

Complexity boundary
design_audit_compute=0
H=48
K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false

Any later realization must remain at or below the already accepted G35 matched-training envelope:

formal_real_transitions<=1069056
formal_optimizer_steps<=3600
nonformal_wall_clock<=1200_seconds
formal_train_evaluate_analyze_wall_clock<=28800_seconds

The design audit must freeze the smallest exact inventory within those ceilings before implementation. File names, tensor storage, vectorization, serialization, batching, telemetry and proof-sized test organization remain implementation-only.

This disposition authorizes no implementation or compute.

7. 中文简报

本轮正式分支必须原样接受：

MIXED_UNDERPOWERED_HISTORY_PROXY_COHERENCE_G37

科学裁决是：

MIXED_DIRECTIONAL_FACTORIZATION_COST_RETAIN_G36_CLOSE_G37_P0
G37 真正增加了什么

G37 将 G36 donor 的四列完全独立抽取和独立打乱。主差值是：

joint donor - factorized donor
CI95 = [0.00639, 0.02160, 0.05154]

这个区间完全大于零，因此可以说：

完整 factorization 对这些 exact checkpoints 产生了方向明确的平均损失。

但不能说 coherence 已经 materially load-bearing，因为：

LCB = 0.00639 < 0.05

也不能说 factorized donor 已经 noninferior，因为：

UCB = 0.05154 > 0.05
绝对 access 也没有闭合

Factorized deterministic utility：

Capacity	Fixed LCB	Random LCB	结论
6	0.90157	0.90072	通过
8	0.88889	0.88549	未通过，但不是 confident fail
12	0.88919	0.89054	未通过，但不是 confident fail

stochastic pooled 与 minimum-replicate 门槛通过，只说明没有广泛崩溃；它们不能替代 capacity-specific deterministic 0.90 门槛。

当前准确结论

G36 仍是接受的部署边界：使用内部 coherent donor。

G37 factorized donor 既没有被接受，也没有被确认否定。

joint coherence 是否带来超过 0.05 的价值仍然开放。

每列 marginal support 是否已经足够也仍然开放。

G37-P0 按 mixed 分支关闭，不能通过追加 seed、episode 或 bootstrap 救援。

G35/G36 已关闭的 learned carry 与目标真实 history acquisition 不会被 G37 重新打开。

当前进度位置
阶段	状态
G32：跨配置容量	支持
G34：有界随机 roster process	支持
G35：删除 learned actor carry	支持
G36：替代目标真实 history sensors	支持
G37：删除 donor 跨列 coherence	mixed，未闭合
剩余正式迭代	9
唯一下一动作
CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_DESIGN_ASSERTION_AUDIT

不再继续拆分 donor coherence，也不扩 G37 证据量。下一步直接检查更有价值的结构问题：

fresh training 后，是否可以把四个 history-shaped 输入和 donor generator 一起从部署 actor 中删除？

拟议比较使用相同图和参数量训练两个 no-carry arm：

FULL10_CS 使用完整十维输入；

FOLD6_CS 在训练期间将四个 history 坐标固定为一个冻结常量，训练结束后把常量列的作用精确折叠进 bias，形成真正的六输入 actor。

这能区分：

G37 只是旧 checkpoint 对 factorized joint OOD 敏感；

四个历史字段在 fresh matched training 中确实提供有限预算价值。

设计审计本身零计算，H=48、K_search=0、无 hypothetical rollout；任何后续正式实现不得超过 G35 已接受的 1,069,056 real transitions、3,600 optimizer steps和八小时上限。

G33 及其衍生线继续保持用户放弃、禁止复活。本裁决不授权代码、Git 或计算。
