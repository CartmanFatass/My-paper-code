1. REGISTERED_RESULT_CONFORMANCE

Registered branch confirmed without modification:

CURRENT_STATE_REDUCTION_SUFFICIENT_G35

The formal evidence package is mechanically closed:

schema 2, formal=true, operational_valid=true, and no operational errors;

one CPU-only run with no retry, resume, fallback, or mixed backend;

three paired replicates and two freshly trained arms;

460,800 training transitions, 608,256 evaluation transitions, 1,069,056 total real transitions, and 3,600 optimizer steps;

99 evaluation cells and 12,672 evaluation episodes;

zero evaluation optimizer steps;

exact REC/CS parameter, initialization, checkpoint, exposure, replay, lifecycle, trace, and manifest-digest closure;

the correction-only code-science recheck returned ALIGNED;

the registered first-match selector was independently reproduced.

Both arms satisfy the complete common-access contract. The conclusion-bearing comparison is:

Estimand	CI95
Pooled REC − CS	[-0.0173505, -0.0081213, 0.0007130]
Capacity 6	[-0.0145298, -0.0105536, -0.0066404]
Capacity 8	[-0.0193356, -0.0086535, 0.0030353]
Capacity 12	[-0.0180017, -0.0052486, 0.0054082]

All four upper bounds are not merely below the frozen 0.05 materiality margin; they are at most 0.00541. The current-state arm also has positive learned gain, held-out stochastic access, and a minimum random deterministic replicate mean of 0.94103.

The frozen first-match order requires the current-state-sufficient branch to precede any recurrent-advantage or mixed interpretation once CS accesses and all pooled and capacity-specific upper bounds are at most 0.05.

2. SCIENTIFIC_DISPOSITION
scientific_disposition=
SUPPORTED_RETAINED_USABLE_CONFIGURED_CAPACITY_BOUNDED_RANDOM_PROCESS_CURRENT_STATE_CONTINUOUS_ROSTER_G35
Exact proposition added beyond G34

G34 showed that a previously trained recurrent checkpoint transported from the fixed G32 schedule to the bounded random G34-P0 process family. G35 now establishes the stronger reduction:

In CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_P0, a freshly trained actor that carries no learned neural state across primitive steps or lifecycle boundaries is sufficient under the registered access contract and is noninferior to the matched learned-state-carry actor by the frozen 0.05 margin.

The domain is exact:

training only on the G32 capacity-8 fixed process;

evaluation on paired fixed and G34-P0 random processes at configured capacities 6, 8, and 12;

horizon H=48;

three fresh paired replicates;

100 fast updates and 100 realized-return-to-go updates per arm;

eight environments per update and two PPO passes;

identical actor tensors, initialization, critic, action distribution, active-set aggregation, anonymous routing, action prefix, G31 credit, environment interactions, optimizer exposure, source ledgers, and stochastic action streams;

one nonserialized treatment constant:

c
REC
	​

=1,c
CS
	​

=0;

primary paired estimand:

Δ
rec
	​

=U
REC
	​

−U
CS
	​

;

a 10,000-resample whole-episode hierarchical bootstrap over paired replicate blocks and episode identities.

The CS arm is not an information-deprived ablation. It retains:

current capabilities and anonymous presentation priority;

current load and target mix;

raw log1p(active_count);

lifecycle age;

two previous actions;

true normalized physical time;

active masks and the active-fraction autoregressive prefix;

the same centralized critic and G31 credit.

Its only removed object is learned cross-step actor storage. Internally it still uses the same gated cell and parameter tensors, but its carried hidden state is exactly zero.

What is now supported

Empirical current-state sufficiency. A fully informed current-state actor is sufficient for fixed and bounded-random continuous-roster control in G35-P0.

Configured-capacity and process transport without neural carry. Learned cross-step state is not required to obtain access at capacities 6/8/12 or under the registered random L/R/J/T processes.

Simplified usable test version. The retained continuous-roster toy algorithm can now be represented as:

current member encoding
+ active-set aggregation
+ log active count
+ within-step autoregressive prefix
+ fully informed current fields
+ G31 training credit
- learned cross-step actor carry

Lifecycle correctness remains meaningful. Even with zero neural carry, membership still controls active masks, actor likelihood ownership, lifecycle age, previous-action state, fresh initialization, temporary freeze/restore, terminal deletion, and survivor continuity.

Smallest retired unit

Retire this exact proposition:

In G35-P0, learned per-lifecycle actor hidden-state carry is required for access or supplies a material finite-budget utility advantage greater than 0.05 over a fully informed current-state actor.

The evidence is stronger than merely failing to prove a five-point gain. The pooled upper bound permits at most a 0.000713 REC advantage, and the largest capacity-specific upper bound is 0.005408. At capacity 6, the entire interval is negative, favoring CS.

Do not retire recurrence globally. The source was explicitly designed so that current load and target mix determine an access-level action; it cannot prove that a task containing hidden, persistent, or creator-to-successor information is recurrence-free. The design contract itself states that task-level recurrence necessity is not identifiable here.

3. COUNTEREXAMPLES_AND_EXCLUSIONS
Strongest remaining explanation

The strongest explanation is now:

G35-P0 is sufficiently Markov and information-rich that a direct current-state controller has both a shorter optimization path and all information needed for the registered action; learned recurrence adds temporal parameter coupling without adding task-relevant information.

The source exposes current load and target mix, and its exact constructive action is:

a
i
(0)
	​

=2load
t
	​

−1,a
i
(1)
	​

=2target_mix
t
	​

−1.

The design also supplied an explicit no-carry representational witness whose minimum one-step utility over the complete load/mix support is 0.94048, above the 0.90 access floor. Thus CS success is not surprising and cannot be interpreted as a general theorem against memory.

Exact interpretation of the REC-minus-CS intervals

Pooled interval. The median is negative (−0.00812), but the interval ends slightly above zero (0.000713). Therefore:

the formal evidence does not establish overall CS superiority at the 95% level;

it excludes any material REC advantage remotely near the registered 0.05 threshold;

small effects in either direction remain compatible with the evidence.

The pooled interval width is approximately 0.01806.

Capacity 6. The entire interval is negative. In that cell family, CS exceeds REC by approximately 0.00664 to 0.01453 utility. This is a local result, not a monotonic capacity trend.

Capacities 8 and 12. Both intervals cross zero. They exclude REC advantages above approximately 0.00304 and 0.00541, respectively, but do not establish which arm is exactly better.

The capacity-specific interval widths are approximately 0.00789, 0.02237, and 0.02341. Their signs do not justify a fitted capacity trend from only three configured capacities.

Finite-budget explanation

The result is conditional on the registered budget. A recurrent arm may have:

a harder optimization problem;

extra path dependence through stored state;

more sensitivity to stochastic trajectories;

interference between the direct current-state mapping and temporal state.

That can explain the negative medians without implying that recurrence is intrinsically harmful. The valid negative cannot be rescued by increasing the budget on this same frozen claim, but a structurally different source in which relevant information is absent from the current observation may reactivate recurrence.

Retained hypotheses and boundaries

Retained:

true normalized time as an available actor and critic field;

lifecycle age and previous actions as actor fields;

active-set aggregation, raw log-count, anonymous routing, and the within-step action prefix;

active-mask and lifecycle-state semantics;

configured-capacity transport across 6/8/12;

bounded G34-P0 process transport;

G31 realized-future-tail credit as the common training estimator;

recurrence as a legal explanation in sources requiring genuinely hidden sequential state.

Not identified by G35:

whether true time, lifecycle age, or previous actions are individually load-bearing;

whether the accepted CS checkpoint can operate after those history proxies are removed;

whether ordinary GAE can replace G31 credit;

asymptotic equivalence between recurrent and feedforward policy classes;

arbitrary capacities, horizons, event counts, repeated leave/rejoin, or process laws;

live in-trajectory tensor-width rebinding;

UAV transport;

asynchronous skill lifetime;

intrinsic-reward value;

comparative superiority on another task family.

G33 and its full-ledger/static-preposition derivatives remain abandoned by direct user instruction and are not legal successors.

4. CDC_PORTFOLIO_LEDGER_EDITS
4.1 Replace the complete C-CONTINUOUS-ROSTER block in CONJECTURES.md

The current block ends with G34 and still lists the current-state explanation as unresolved. Replace it with:

Markdown
## C-CONTINUOUS-ROSTER — Continuous control under dynamic membership

- Status: supported and retained as a usable fully informed current-state,
  configured-capacity, bounded-random-process continuous dynamic-roster test
  version for the registered 48-step capacity-6/8/12 toy family. A finite
  packing capacity is selected before each trajectory.
- Claim: a capacity-shape-independent actor can be trained only at capacity 8
  and remain usable at configured capacities 6, 8 and 12 across the fixed G32
  process and bounded held-out G34-P0 random process without carrying learned
  neural state across primitive steps or lifecycle boundaries.
- Retained actor information: current capability, anonymous priority, current
  load and target mix, raw log1p(active_count), lifecycle age, two previous
  actions, true normalized time and the active-fraction autoregressive prefix.
- Formal immediate/delayed evidence: G31 passes the paired G17/G18 utility,
  spike-allocation, rotation, gain and fresh-seed stability gates.
- Formal configured-capacity evidence: G32 strict-loads the same capacity-8
  recurrent checkpoints at capacities 6, 8 and 12 and establishes exact
  common-active padding invariance.
- Formal bounded-process evidence: G34 transports those checkpoints without
  retraining from the fixed 12/24/36 process to one each of L/R/J/T at random
  held-out times and orders, with all registered access, event-window, segment,
  learned-gain and stochastic gates passing.
- Formal current-state reduction evidence: G35 freshly trains parameter-,
  information-, credit- and exposure-matched REC and CS arms. Both access the
  fixed and random capacity-6/8/12 cells. REC-minus-CS pooled CI95 is
  [-0.0173505, -0.0081213, 0.0007130]; capacity-6/8/12 upper bounds are
  -0.0066404, 0.0030353 and 0.0054082, all below the frozen 0.05 margin.
  Current-state reduction is therefore sufficient in G35-P0.
- Retired alternatives: within the registered family, usable deployment does
  not require capacity-shaped learned parameters, capacity-specific retraining,
  checkpoint adapters, the exact fixed 12/24/36 schedule, atomic R+J, or
  learned per-lifecycle actor hidden-state carry. The exact claim that carry
  supplies a material >0.05 finite-budget advantage in G35-P0 is closed.
- Lifecycle boundary: active masks, likelihood ownership, fresh initialization,
  temporary freeze/rejoin, terminal deletion, lifecycle age, previous-action
  state and survivor continuity remain part of the environment/runtime
  contract. G35 removes only learned actor carry.
- Scope: H=48; configured capacity is fixed within a trajectory and belongs to
  6/8/12; G34-P0 contains one each of L/R/J/T, three legal event orders and the
  registered cohort magnitudes. This is not arbitrary process-law transport.
- Strongest remaining explanation: current load and target mix directly define
  an access-level action. The retained true-time, age and previous-action fields
  may also act as history or schedule proxies; their necessity is unresolved.
- Credit boundary: both G35 arms use identical G31 realized-future-tail credit,
  so G35 does not establish that estimator's necessity or redundancy.
- UAV boundary: temporary-service-loss G1 and charge-rotation G2 remain source
  non-identifiable. G33 and all derivatives remain abandoned by user
  instruction.
- Exclusions: arbitrary capacity, repeated or arbitrary membership processes,
  random horizon, history-proxy-free robustness, UAV usability, asynchronous
  skill lifetime, intrinsic-reward advantage, complete-algorithm superiority
  and general recurrence or G31-credit redundancy remain unsupported.
4.2 Replace the complete C-REC block in CONJECTURES.md

The existing block still describes the G34 recurrence question as unresolved. Replace it with:

Markdown
## C-REC — Ordinary recurrence is sufficient

- Status: selected as a sufficient capability in the exact G1/G2 memory
  sources, but learned actor-state carry is rejected as load-bearing in the
  fully informed G35-P0 continuous-roster source.
- Memory-source claim: a matched recurrent MARL controller can represent useful
  persistence without an explicit event-held commitment when access and
  training are adequate.
- Continuous-roster result: G35 freshly compares parameter-identical REC and CS
  arms under identical current information, G31 credit, source, capacity,
  interactions and optimizer exposure. Both access; the pooled REC-minus-CS
  CI95 is [-0.0173505, -0.0081213, 0.0007130], and every capacity-specific UCB
  is at most 0.0054082 against the 0.05 materiality margin.
- Smallest retired unit: learned cross-step actor carry is neither required for
  access nor materially advantageous in G35-P0. This does not retire recurrence
  on sources containing task-relevant information absent from current
  observations.
- Retained lifecycle distinction: zero learned carry does not delete active
  masks, lifecycle age, previous-action state, temporary freeze/rejoin,
  fresh-state initialization, terminal deletion or survivor continuity.
- Reactivation condition: an identified source in which a fully informed
  current-state policy lacks relevant sequential information, followed by a
  matched comparison showing a material recurrent advantage. More seeds,
  budget or threshold changes on G35-P0 are not reactivation evidence.
4.3 Add this bullet to C-CREDIT
Markdown
- G35 update: both REC and CS use identical G31 realized-future-tail targets,
  direction-balanced actor updates, critics and optimizer exposure. Current-state
  sufficiency therefore isolates actor carry only; it supplies no evidence that
  G31 credit is necessary or replaceable in this source. The G31 credit claim
  remains supported only by its registered paired G17/G18 evidence.

No other conjecture block changes.

4.4 Replace the affected rows in IDEA_PORTFOLIO.md

The current rows and terminal block still point to G35 as unresolved. Replace them with:

Markdown
| C-CONTINUOUS-ROSTER | supported retained: fully informed current-state configured-capacity bounded-random-process continuous-roster test version | G31 closes the paired immediate/delayed toy contract; G32 adds strict-loadable capacity-6/8/12 transport; G34 adds bounded random-process transport; G35 shows that a fresh no-carry current-state arm accesses the same fixed/random capacity-6/8/12 family and is noninferior to REC by the 0.05 margin. | Next action: test whether the accepted CS checkpoints depend on retained history-proxy inputs. Arbitrary processes, horizons, history-proxy-free robustness, UAV transport and G31-credit necessity remain open. |
| C-REC | sufficient in exact memory sources; learned actor carry closed as load-bearing in G35-P0 | Both G35 arms access. REC-minus-CS pooled CI95 is [-0.0173505, -0.0081213, 0.0007130], and every capacity-specific UCB is <=0.0054082. | Reactivate actor carry only on an identified source with task-relevant information absent from current observations and a matched material advantage; do not rescue G35-P0. |
| C-CREDIT | supported on paired toys; necessity unresolved outside them | G35 holds G31 credit fixed in both arms, so its current-state result isolates representation and does not compare credit estimators. | Reactivate only through a representation-, information- and exposure-matched credit-only comparison. |

Replace the terminal block with:

completed_action=CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_FORMAL_ITERATION_26
source_family=CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_P0
formal_disposition=CURRENT_STATE_REDUCTION_SUFFICIENT_G35
scientific_disposition=SUPPORTED_RETAINED_USABLE_CONFIGURED_CAPACITY_BOUNDED_RANDOM_PROCESS_CURRENT_STATE_CONTINUOUS_ROSTER_G35
next_action=CONTINUOUS_ROSTER_HISTORY_PROXY_FREE_CS_G36_DESIGN_ASSERTION_AUDIT
authorization_status=active_twenty_iteration_toy_first_uav_promotion_chain
conclusion_bearing_iterations_consumed=26
iterations_remaining=11

Replace the final G32/G34 paragraph with:

Markdown
Formal G32 supports one capacity-8-trained recurrent checkpoint at configured
capacities 6, 8 and 12 with exact padding invariance. Formal G34 transports
those checkpoints without retraining from the fixed 12/24/36 process to the
registered four-event random-process family. Formal G35 then freshly trains
parameter-, information-, credit- and exposure-matched REC and CS arms and
selects `CURRENT_STATE_REDUCTION_SUFFICIENT_G35`: both access, while every
pooled and capacity-specific REC-minus-CS upper bound is below 0.00541 against
the 0.05 materiality margin. Learned actor carry is therefore closed as
load-bearing in G35-P0, but true time, lifecycle age, previous actions and G31
credit remain retained, unseparated inputs or training mechanisms. The next
scientific action is
`CONTINUOUS_ROSTER_HISTORY_PROXY_FREE_CS_G36_DESIGN_ASSERTION_AUDIT`.
4.5 Update RESEARCH_DIRECTION_LEDGER.md

Replace the supported continuous-roster row with:

Markdown
| 连续动态 roster 的跨容量、随机过程与 current-state 化简 | `SUPPORTED_RETAINED` | G31/G32/G34/G35 在已登记 48-step toy family 中形成可用测试版：capacity-8 训练模型可在配置容量 6/8/12 与固定/有界随机 roster process 上保持 access；G35 进一步表明，在保留 true time、age、previous action、active-set、prefix 与 G31 credit 时，不携带 learned cross-step hidden 的 CS arm 已充分，REC 的 >0.05 material advantage 在 P0 内被关闭。 | 不能推出 history-proxy-free、time-free、任意容量/过程/horizon、UAV transport、技能生命周期、内在奖励增益、G31 credit 冗余或全局 recurrence 无用。 | [G34 正式结果](EVIDENCE_NOTES/20260726_CONTINUOUS_ROSTER_RANDOM_PROCESS_G34_FORMAL_RESULT.md)；[G35 正式结果](EVIDENCE_NOTES/20260726_CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_FORMAL_RESULT.md)；[第 26 轮报告](../../report/ITERATION_26.md) |

Add under 已失败并关闭的精确方向:

Markdown
| G35-P0 中 learned actor hidden carry 的必要性或 >0.05 material advantage | `FAILED_CLOSED` | fully informed CS 与 REC 均达到 access；REC-minus-CS pooled CI95 为 [-0.0173505, -0.0081213, 0.0007130]，每个 capacity 的 UCB 均 <=0.0054082。该 source、预算与架构下，learned carry 不是 load-bearing。 | “所有任务都不需要 recurrence”“REC 在所有设置都更差”或“G31 credit 不需要”。 | [G35 正式结果](EVIDENCE_NOTES/20260726_CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_FORMAL_RESULT.md)；[第 26 轮报告](../../report/ITERATION_26.md) |

Replace the UAV-transport row with:

Markdown
| G35 current-state continuous-roster controller 向非 G33、可识别 UAV source 的 transport | `OPEN_UNTESTED` | 在物理可行、目标行为 load-bearing 且 source-identifiable 的非 G33 UAV source 上，fully informed current-state representation、bounded-process transport 与 G31 credit 是否保持可用。 | UAV G1/G2 在 learned training 前因 source 不可识别关闭；G33 被用户放弃；尚无可判别的 UAV transport 结果。 |

Add under 尚未验证的方向:

Markdown
| G35 CS checkpoint 的 history-proxy-free 执行 | `OPEN_UNTESTED` | 在不改变 checkpoint、current load/mix、capability、active set、prefix、critic、source 或 action stream 时，neutralize actor 的 true time、lifecycle age 与 previous-action fields 后，CS 是否仍保持 access 与注册 noninferiority。 | G35 只删除 learned hidden carry；三个 history-proxy fields 均被保留，尚不能把 current-state sufficiency 写成纯即时 demand mapping。 |

Replace longitudinal summary item 5 with:

Markdown
5. G32 支持 capacity-6/8/12 strict-load，G34 支持固定过程到有界随机
   roster process 的零训练 transport。G35 通过 fresh paired REC/CS 比较支持
   fully informed current-state reduction，并在 P0 内关闭 learned actor hidden
   carry 的必要性或 >0.05 advantage。该结果仍保留 true time、age、previous
   action 与 G31 credit；下一边界检查 accepted CS checkpoint 是否依赖这些
   history-proxy inputs。

No change is warranted to ALGORITHM_PRINCIPLES.md: G35 is a bounded local simplification result, not a new cross-experiment law.

5. ONE_NEXT_ACTION
CONTINUOUS_ROSTER_HISTORY_PROXY_FREE_CS_G36_DESIGN_ASSERTION_AUDIT
Scientific distinction

G35 has resolved the learned-carry question. The remaining ambiguity inside the accepted current-state controller is:

instantaneous current load/mix and active-set mapping
versus
dependence on retained true time, lifecycle age and previous-action proxies

The next action should not retrain another recurrent model. It should first determine whether the accepted G35 CS checkpoints themselves rely on those three history-bearing inputs.

Why this is the cheapest discriminating action

No training is initially required. It can reuse the exact three formal G35 CS final checkpoints.

It targets the nearest remaining shortcut. G34 found true-time rotation load-bearing for its historical recurrent checkpoint, while G35 retained true time, age, and previous actions in both arms.

It is cheaper than a G31 credit comparison. Credit remains independently supported on G17/G18 and was not implicated by the G35 result.

It is cheaper and cleaner than another UAV source. Two UAV sources failed source identification, and G33 is permanently excluded.

It is more discriminating than extending capacity or process support. Further transport on the same source would not tell whether the accepted controller is genuinely instantaneous or is using clock/history proxies.

Its outcomes change a concrete decision.

A pass permits a simpler deployment interface and strengthens the direct-mapping interpretation.

A confident failure retains the three-field history-proxy bundle as load-bearing for the accepted checkpoint and closes that reduction without retraining rescue.

This is a zero-compute design audit, not an implementation or evaluation authorization.

6. EXECUTABLE_SCIENTIFIC_BOUNDARY
next_boundary=
CONTINUOUS_ROSTER_HISTORY_PROXY_FREE_CS_G36_DESIGN_ASSERTION_AUDIT
One smallest exact audit question

Can a conclusion-bearing, zero-training paired evaluation be frozen for the exact formal G35 CS final checkpoints that compares their registered execution with an actor-only history-proxy-free execution in which lifecycle age, both previous-action coordinates, and normalized absolute time carry no episode- or lifecycle-history information, while preserving current capabilities, anonymous priority, current load, current target mix, raw log active count, active masks, autoregressive prefix, centralized critic, checkpoint tensors, G32/G34 fixed and random sources, configured capacities 6/8/12, episode identities, member-owned action streams, reward, access gates, and zero optimizer exposure?

The audit must decide whether the claim is only checkpoint-level dependence or can support a deployment-input reduction; freeze the exact information-destroying transform, the paired estimand, a noninferiority margin, fixed/random deterministic and stochastic gates, whole-episode confidence unit, first-match branches, and the smallest evaluation inventory before any realization.

Inherited non-negotiable boundary
training=none
checkpoints=exact_formal_G35_CS_final_only
H=48
capacities=6|8|12
sources=unchanged_G32_fixed_and_G34_P0_random
reward=unchanged
critic=unchanged
current_load_and_target_mix=retained
capability_priority_active_count_mask_prefix=retained
G33_reactivation=forbidden

The result ceiling must remain:

pass: the frozen CS checkpoints do not require the tested history-proxy bundle for registered access;

fail: that bundle is load-bearing for those checkpoints;

not permitted: “all retrained policies require history” or “the task is globally memoryless.”

Complexity boundary
design_audit_compute=0
H=48
K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false

A later evaluation-only realization must remain O(H) per episode, below the 20-minute nonformal and eight-hour formal ceilings, and require no candidate search or simulated counterfactual trajectory. Even a conservative ceiling of three replicates × three capacities × four fixed/random deterministic/stochastic intervention cells × 128 episodes is only:

3×3×4×128×48=221,184

real transitions and zero optimizer steps. The design audit must freeze the smallest inventory at or below this bound. The governing complexity policy permits direct trajectories but forbids nested or horizon-growing search.

File names, tensor storage, vectorization, serialization, telemetry layout, and proof-sized test organization remain implementation-only. The intervention semantics, source, checkpoints, paired unit, margin, confidence construction, evidence volume, and branch order are scientific fields.

This disposition authorizes no implementation, Git action, nonformal/formal evaluation, monitoring, or successor child.

7. 中文简报

G35 的正式分支应原样接受：

CURRENT_STATE_REDUCTION_SUFFICIENT_G35

它在 G34 之上新增的最强结论是：

在完全保留 current load、target mix、capability、active count、true time、lifecycle age、previous actions、active-set aggregation、action prefix、centralized critic 和 G31 credit 的情况下，不跨 primitive step 携带 learned hidden state 的 CS arm，已经足以完成固定与随机 roster process、capacity 6/8/12 的注册任务。

这不是破坏性 ablation。REC 和 CS：

从相同参数初始化；

参数 key、shape、trainable mask 和数量相同；

使用相同 source、随机数、信息、critic、G31 credit、训练 transition 和 optimizer exposure；

唯一差别是：

REC: h_next = u
CS:  h_next = 0

正式结果中，两臂都通过 access。REC − CS 的 pooled CI95 是：

[-0.0173505, -0.0081213, 0.0007130]

capacity 6/8/12 的 UCB 分别是：

-0.0066404
 0.0030353
 0.0054082

全部远低于 0.05 materiality margin。因此在 G35-P0 内可以关闭：

learned actor hidden carry 是 access 所必需，或者能够带来大于 0.05 的有限预算优势。

但不能写成：

所有任务都不需要 recurrence；

REC 永远更差；

true time、age 或 previous actions 不需要；

G31 credit 不需要；

任意 capacity、process、horizon 或 UAV 都已解决。

尤其是，pooled interval 仍略微跨过零，所以不能声称 CS 在总体上显著优于 REC。只有 capacity 6 的区间完全为负。更准确的表述是：CS 足够，且没有可识别的 material REC advantage。

下一项科研动作是：

CONTINUOUS_ROSTER_HISTORY_PROXY_FREE_CS_G36_DESIGN_ASSERTION_AUDIT

它只问一个更小的问题：

已经成功的 G35 CS checkpoints 是否仍然依赖 true time、lifecycle age 和 previous actions，还是仅凭即时 load/mix 与 active-set 信息就能工作？

这是比重新训练 recurrence、重做 credit、扩展 capacity 或重新进入 UAV 更便宜的证据。设计审计本身零计算；任何后续实现都必须零训练、H=48、K_search=0、无 hypothetical rollout，并保持在 20 分钟/8 小时上限内。

G33 及其衍生线继续保持用户放弃、禁止复活。本裁决不授权代码或计算。
