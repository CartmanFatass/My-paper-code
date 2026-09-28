# Native round 3 selection and retired round 2 synthesis

Historical evidence only. This completed review and substantively superseded
project plan were retired on 2026-09-28. They do not change current pause,
leadership, accepted operations or execution admission.
The prior current plan is preserved from
`17ce44bfd14aca249ac66be824c8f721700852fd`; the reviewed new direction proposal
is at that same revision. Relative links below are rebased for this archive.
Current priorities belong in [RESEARCH](../../RESEARCH.md#current-research-plan).

## Portfolio review 2026-09-28 native-round3-selection

Conversation: independent native scientific review only; no Pro consultation.
Reviewer: `/root/round3_question_review`, fresh context.
Question owner: fresh native `/root/dm_persistent_service_round3`.
Root: `/root`, App thread `01a0e560-4333-7b03-8ff3-759a4add1d9a`.

### Context and options

The owner approved keeping the Root/native-DM division, applying the proposed
light changes, then advancing a new research round. Method prose was published
at `858e8cff5`: prioritize consequential question design and judge a round by
changes in understanding, ordinary references and investment, without new roles,
quotas, exposure gates or routine approval. Constitution sections 2/4/5 and the
current scientific, engineering and portfolio methods govern the work.

Relevant completed evidence: Energy I already selected station goals and carried
them between 60-step replans, but lost the direct comparison to strong P;
cooperative offline hold-ranking lost to P; sensing B02 had real exposure but
did not establish extra usefulness; information B03 strengthened a lawful ordinary
reference with adverse reserve tails. The declined transit-handoff proposal was
not executed. None diagnoses a general energy defect or exhausts planning.
The complete source-based reconstruction appears in the answer below and
[prospective NOTES at the reviewed SHA](https://github.com/CartmanFatass/My-paper-code/blob/17ce44bfd14aca249ac66be824c8f721700852fd/docs/research/candidates/uav_persistent_service/NOTES.md).

Decision asked: is executable finite return admission, recharge dwell and
redeployment worth one direct learned-versus-ordinary comparison on the UAV host?
The new estimand is complete finite service, not a renamed proactive station
trip, an indefinite sustainability guarantee or a new PPO method.

- Select the proposed L/O/P comparison: one fit, 64 H3000 training worlds and
  16 new common evaluation worlds per arm, 336k native steps and 640 updates.
  This can distinguish useful learned scheduling, ordinary-only value and no
  established package value. Actual opportunity and charging interruptions are
  read within the complete experiment, not certified by a required pilot.
- Revise the finite arithmetic/specification if the ordinary comparator is weak,
  without automatically buying another arm, fit, probe or review.
- Decline this investment if no competent finite ordinary comparison can be
  defined or if its information does not warrant the full cost. The broad
  scheduling question would remain unrefuted; no replacement quota applies.
- User-motion prediction was considered as an opportunity-cost alternative,
  but no second study was selected. Actual information B01 implements current
  user sources and BS memory, not the earlier proposed user-track memory.
  The current visibility/refresh regime and ordinary discovery results leave
  the near-term gain prediction insufficiently concrete. This is a priority
  judgment, not an executed negative result for prediction.

The same critic first reconstructed the original evidence and then read the
concrete design. Source feedback corrected an important interface issue before
the final answer: voluntary assignment eligibility must not masquerade as real
F modes, because P's inherited any-F fallback affects the entire fleet.
No second selection critic or Pro round was added.

### Answer

The complete final independent answer follows. Only link targets were rebased.

**Recommendation: revise O, then select the single bounded L/O/P study.** I dissent from launching the comparison exactly as published at `17ce44bfd14aca249ac66be824c8f721700852fd`. The objection is a correctable comparator problem, not a requirement for another diagnostic experiment.

This review inherited no Root/DM conversation. It was not blinded: the assignment supplied Root's framing, and index navigation exposed earlier interpretation excerpts. I reconstructed original configurations, native summaries and consequential controller/host interfaces before reading this complete DM proposal. I did not repeat remote NPZ audits, inspect every historical failure, or verify all proofs in the literature bridges. No experiments or record edits were performed.

The evidence supports the following diagnosis:

| Original comparison | Observation | Consequence |
| --- | --- | --- |
| Energy B01 I−H | J +145.243; QoS +.045360; eight joint improvements | Ordinary analytical planning had conditional usefulness against H. |
| Energy B02 I−P | J −136.696, descriptive interval [−430.812,157.419]; six joint losses | That advantage did not establish usefulness beyond competent P. I also used substantially more computation. |
| Cooperative B02 L−P | J −55.389; QoS −.016488 | The executed offline move/hold learner was adverse, without diagnosing the cause. |
| Sensing B02 | 3411 eligible training choices; L1 executed 139 probes; no demonstrated increment over ordinary alternatives | Global nonactivation no longer explains that package's result. |
| Information B03 | P_BS exceeded the simple anchor, with adverse reserve tails | Ordinary competence remains consequential; P_BS is a distinct information regime, not the present central P. |

These readings come from the original [energy outputs](../../../../runs/uav_energy_coordination/b02_i_vs_p_a01/summary.json), [planning output](../../../../runs/uav_cooperative_planning/b02_transit_value_a01/summary.json), [sensing output](../../../../runs/uav_active_sensing/b02_semantic_choice_a01/summary.json) and [information output](../../../../runs/uav_information_value/b03_anchor_content_a01/summary.json). They neither identify a charging defect nor exhaust finite scheduling opportunities. The handoff proposal was declined without execution.

The new interface is sufficiently distinct to investigate: I already chose station goals, but this proposal explicitly carries admission and finite dwell commitments through ordinary replanning. Its value would be empirical understanding and complete service performance, not a new PPO method.

**The consequential objection is O's deadline arithmetic.** Native margin subtracts both reserve and return-energy requirement. Under O's declared held-geometry approximation, `D = margin × capacity / power` is therefore time until F entry: an approximate departure deadline. The proposal subsequently subtracts travel time again in `D−tau`, both for ranking and station slack. That has no stated justification in the native contract. See the [margin definition](https://github.com/CartmanFatass/My-paper-code/blob/17ce44bfd14aca249ac66be824c8f721700852fd/envs/pettingzoo/relay/energy_aware.py#L1573) and [proposed O](https://github.com/CartmanFatass/My-paper-code/blob/17ce44bfd14aca249ac66be824c8f721700852fd/docs/research/candidates/uav_persistent_service/NOTES.md#L142).

For example, a competitor with `D=600`, `tau=100` nominally reaches the charger around time 700. O uses 500 as the occupancy limit. A candidate arriving at 100 could dwell 600 until that nominal arrival, yet the published rule permits only 300. A learner could beat this O through an ordinary arithmetic correction. Beating exact P as well would establish a useful package, but would not repair the weak same-interface comparison.

I recommend these bounded revisions:

1. Rank departure urgency using `D`. For station occupancy, use the other member's predicted arrival `D+tau`. If the intended criterion is restoring service before another departure, use that departure deadline and the candidate's redeployment travel explicitly. Keep these meanings separate.
2. Make O account for the known finite endpoint. At minimum, a predicted F deadline beyond H3000 should not itself justify discretionary recharge, and terminal dwell selection needs an explicit rule. L already receives remaining episode time.
3. State dwell consistently as **elapsed time after first geometric arrival**, including waiting and subsequent time outside capture. This buys continued docking commands, not guaranteed charging time or energy.

These corrections need arithmetic/specification work and ordinary correctness checks, not another fit, preliminary exposure screen or fourth arm. P alone does not substitute for a competent ordinary policy over the expanded interface.

The remaining interface is defensible. Separate commitment eligibility from real-F modes preserves the intended transit comparison. Native priority can interrupt charging, F can prevent release, and charging members remain radios. Full-battery release can also make different duration labels execute identically. Requested duration, actual dwell, allocated charging, net input and eventual service recovery therefore matter alongside complete endpoints. Sparse or aliased exposure would limit the reading; it would not automatically authorize repair.

The literature supports taking scheduling seriously, while strengthening the ordinary alternative. The [graph-monitoring paper](https://arxiv.org/html/2303.08935#S3) uses fixed latency and recharge assumptions; the [charging-schedule paper](https://arxiv.org/html/2409.00572#S2) assumes known durations and consecutive charging slots. Neither supplies an S7 guarantee or an RL advantage.

After correction, the smallest worthwhile observation remains the proposed complete study: **one fit, 64 training worlds, L/O/P on 16 fresh common worlds, 336,000 native steps and 640 optimizer updates**. Retain the final checkpoint and fixed deployment rule. Different outcomes would change investment:

- L improves complete J/service over corrected O and P with acceptable observed tails: price independent-training replication of this finite package.
- O improves over P without useful L increment: retain ordinary scheduling if its full cost warrants use; stop this learning recipe.
- Neither improves: stop this package without concluding that all scheduling is ineffective.
- Nonactivation, failed arrival, technical incompleteness or mixed utility/risk: preserve their distinct meanings; none supplies an automatic successor.

This is a worthwhile bounded purchase because it tests executable temporal commitments while avoiding the declined handoff design's repeated surrogate rollouts. It requires **zero forecast environment steps**, but up to **638,400 radio snapshots**, native execution, neural work and substantial implementation/readback. Historical P scaling gives roughly **2.45 worker-hours**, not a forecast or upper bound. Actual elapsed time, contention, engineering and retention costs remain unknown; four-worker admission is unresolved. Sixteen evaluation worlds remain conditional observations for one trained instance, not independent learning replication.

**MATERIAL_DISSENT: yes.** The disputed investment is launching the published L/O/P comparison with `D−tau` and no finite-horizon rule in O. Direct native margin semantics support correcting that comparator. I recommend selecting the bounded study after those corrections, without additional prerequisite experiments.

### Decision

Root, 2026-09-28: adopt the material objection and select the single study with
the bounded corrections, not the uncorrected `17ce44bfd` rule. The DM accepted
the objection and returned this exact revised ordinary rule before substantive
implementation:

- `D_i=max(0,margin_i)*160*3600/p_i` is approximate time to F entry. Rank
  dispatchable members by `D_i`, then lower observed load and index.
- For each free same-station competitor, `A_k=D_k+tau_in,k`;
  `A_next=min A_k`. These are nominal arrival times, not reserved slots.
- Choose the longest `d in {120,300,600}` satisfying
  `tau_in,i+d<=A_next` and
  `tau_in,i+d+10+tau_out,i<=R`, with `R=3000-t`.
  The second condition separately prices nominal travel from capture to the
  current base H1 service target and up to ten seconds for the next P replan.
  It is a held-target estimate, not guaranteed service restoration.
- No feasible duration means continue service. Initiate only if `D_i<R`
  and `D_i<=tau_in,i+d+30`. A deadline beyond the remaining horizon cannot
  itself motivate discretionary recharge.
- Dwell is elapsed time after first geometric arrival, including waiting and
  later time outside capture. Native F, allocation, full-battery/900-second
  release and terminal censoring retain their declared meanings.

This resolves the identified specification objection without claiming that O
is optimal or that all scheduling alternatives have been exhausted. Ordinary
correctness checks must implement the stated meanings; implementation and
high-risk engineering review remain with the DM, not another selection gate.
If a material inability to define/implement this competent comparison emerges,
it is returned as that concrete issue rather than silently self-cleared.

The selected cost, arms, seeds, horizon, final-checkpoint rule and single-fit
scope remain those in the prospective NOTES, absent a separately reasoned
prospective correction. No fourth arm, activation pilot, extra Pro/critic pass,
automatic fit, horizon extension or retry follows from this selection.
The DM owns the complete execution, independent result reading, publication and
evidence-preserving cleanup; Root owns the cross-question plan and waits for
substantive returns. Peer B05 remains untouched. No training/result execution
had begun at this selection boundary.

The useful methodological consequence here is concrete: source reconstruction
prevented relabeling old proactive returns as new, and the independent review
changed the comparator before spending the fit. This is not a causal estimate
of workflow efficiency or proof that the new study will be informative.
The complete dissent is retained above; its original form is not rewritten
into agreement.

## Superseded current plan from 17ce44bfd

The following is the prior current-plan section, preserved in full with rebased
links. Its then-current recommendation and next-selection status are historical.

**本轮两项完整比较已经运行结束，并有独立科学判读（2026-09-28）。** Root采纳两项有范围的结果取舍，
不追加原配方fit、评价世界或自动安全修补；方向发表、保全及终态清理由各DM完成，具体边界见各自NOTES和路由。
这不是较宽问题被否定，也不是把所有未解释现象都转成下一项实验。
原选题、两项实质修改及完整独立答复见[选题记录](RESEARCH-native-round2-selection.md)，
原执行计划已[按原文退役](RESEARCH-native-round2-complete.md)。

| 本轮问题 | 完整观察改变了什么 | 当前取舍与边界 |
| --- | --- | --- |
| 主动感知学习包：能否超过适用的普通策略？ | 1fit/480k训练、64完整评价回合/192k步。160个训练世界和16个评价世界都有合法决策机会；训练3411次eligible选择含1618次服务、1793次探测。L1实际在13/16评价世界执行139次探测，但L1-H/L0、L1-A、L1-R50总J分别+7.217、-17.474、+3.379，名义配对t95均跨零。不能再以全局未激活概括该包的结果。 | 未建立学习的额外用途，结束不变B02的投入；保留普通控制器及完整正反证据。弱目标分化和确定性部署集中是观察，不识别特定优化故障；一个训练实例不否定可学性、不证明等价。28173005/010等低储备尾部和共有P_BS限制继续有效。[完整结果](../../candidates/uav_active_sensing/NOTES.md)、[冻结读数](../../../../runs/uav_active_sensing/b02_semantic_choice_a01/reading.json)。 |
| 合法锚点内容：代数构造是否超出简单启用中继？ | 0fit/96完整评价回合/288k步。P-S0总J+132.787 [72.406,193.167]、QoS/步+.039149；S0-H本身也有收益，但只启用分支不足以解释P相对此普通替代的增量。 | P作为更强的条件性普通性能参照，S0保留为归因控制，H按既定风险规则保留默认。P相对S0四世界终点低储备+7，S0也有新增反例；不作风险占优、精确重构或纯几何中介结论。结束本项锚点归因投入。[完整读数与独立处置](../../candidates/uav_information_value/NOTES.md#2026-09-28---b03-independent-reading-and-comparator-disposition)。 |

本轮合计**1fit、480k训练步、480k评价步、160个评价回合**；加训练为320条完整H3000轨迹。
两项runner分别89.56和39.13分钟，合计128.69分钟；这是并行批次时长之和，不是用户等待时间或总科研工时。
另有1302步工程检查、两个单次优化器接线检查；准备、审查、收集、发表没有完整计时，不能算零成本。
Root核对compact结果的完整性及关键读数并读取两位独立结果critic的完整答复，复用各DM的科学判读，不再叠加同范围审查；
未自行重审全部远端raw。学习包保持单实例探索，世界间区间不是独立训练复制。

**当前方法建议：保持现有Root与原生DM分工，不再作结构性调整。**
本轮可核查的收益是比较与后续决定更明确：选题审查实际补入R50并纠正未决分支，
结果既升级了一个普通参照，也使一个有真实执行却未建立额外用途的有限配方获得有理由的停止决定。
这支持继续试用现有方法，不是新工作流导致更高信息增益或效率的因果证明，更不是论文级创新已经增加。
已有角色和skill足够；此次只完成研究计划收口，不修改治理、角色或方法，也不宣布新的研究批次。

Root下一次选题应把精力放在重要的未决问题、适用普通替代和不同结果会改变的研究取舍，
不把日常执行改成审批，也不把长期诊断或基线归因本身当作研究终点。DM保留挑战题目和选择方法的责任。
复盘看实际认识/参照/投入的改变，不设信息增益分数、固定新题数、正例门槛、修补配额或新增表单。
只有出现具体职责缺口、重复阻塞或反复无判别力的设计，才针对实际问题调整；运行中已经解决的网络准备问题保留事实，
不据此增加常设流程。旧方向不自动复活，下一项结果性研究仍须有具体问题及前瞻比较。

Claude的既有B05及其面板保持原身份和peer自主范围，当前结果见其NOTES，不由本轮收口迁移或复制。
PPC/FSD暂停、G33冻结及其他方向归属保持。后续已选研究仍按真实节点准入，子DM保持turn并长等待同一handle，
Root使用native `wait_agent`等待实质返回。方法依据见[已采纳方法](RESEARCH-method-workflow-review.md)，地址见[任务路由](../../RESEARCH.md#session-routing)。
