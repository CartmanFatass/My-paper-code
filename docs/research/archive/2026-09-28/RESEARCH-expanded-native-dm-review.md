# Expanded native DM questions: completed independent review

Completed 2026-09-28 UTC. Root: `01a0e560-4333-7b03-8ff3-759a4add1d9a`.
Reviewer: native `/root/round_question_review`, registered
`hmasd-research-critic`, originally created with `fork_turns=none`. This was a
bounded follow-up in its independent review context, not a new result direction.
It read original evidence before the proponents' new notebooks, then received
their concrete design/cost revisions. It was not blinded. No reviewer-run fit or
result episode occurred. Completion of this review is not engineering clearance
or proof that any proposed batch was accepted.

## Selection Object And Provenance

The owner removed the fixed Codex DM/research-track count ceiling and requested
more proactive research. This creates no quota and does not override actual node
resources, existing pauses or the Claude peer's ownership. Owner-control source:
`192dd1df1`; new assignments and initial complete plan: `3c1a02ad2`,
[pinned plan](https://github.com/CartmanFatass/My-paper-code/blob/3c1a02ad2/docs/research/RESEARCH.md#current-research-plan).
Existing A/B work remained selected; C's source-based reserve judgment was not
reversed. The revised D/E/F choices below supersede their initial proposals only.

- D, `uav_geometric_generalization`: initial P/G/V used eight transformed recurrent
  lanes and action averaging, plus a speed-matched control; det/stoch plus H@10
  gave 112 episodes/336k steps, 0 fits, estimated 1-3 CPU node-hours plus engineering.
  The DM's simpler P/C alternative uses a single fixed episode transformation
  chosen from legal spawn positions, with NE chosen from already exposed c06
  direction evidence. P/C det/stoch plus H@10 gives 80 episodes/240k steps.
  Its notebook was an uncommitted owned draft at the review boundary; exact
  execution inputs must subsequently be published. [Append-only notebook](../../candidates/uav_geometric_generalization/NOTES.md).
- E, `uav_active_sensing`: the initial H/P/A proposal was 16 new worlds, 48
  episodes/144k steps, 0 fits. The direct native-J learning alternative is one
  480k-step fit, with initialization, endpoint and H/P/A evaluated in the same
  16 new worlds, 80 evaluation episodes/240k steps. Both alternatives and their
  costs were published at `0651e7982`; no rule-positive prerequisite was proposed.
  [Append-only notebook](../../candidates/uav_active_sensing/NOTES.md).
- F, `uav_radio_placement`: H is the original geometric reference, G strengthens
  its k-means optimization with eight fixed initializations, and R uses finite
  native-radio spatial search. Eight new worlds, 24 episodes/72k steps, 0 fits,
  at most 81.6k radio queries. The selected scope and L0 were published at
  `b1c3b8c2f`. [Append-only notebook](../../candidates/uav_radio_placement/NOTES.md).

The Claude peer's response-probe evidence was updated during review:
`ee02de596` contains the complete Pro answer; `6dfbc9731` adopted corrections and
declared the probe; `b97318be1` temporarily withdrew its paired rotated-world
closed-loop Block 2. Root clarified at `59a77f2c8` that D's P/C comparison on the
original worlds does not supply that paired-world estimand. The peer independently
reinstated Block 2 at `cef84927c`. No Root assignment takes over that probe,
representation fit or the relational goal decoder.

## Complete Reviewer Return

The following is the substantive native final return in full. File links are
made repository-relative; the review text and dissent are preserved.

**结论**
D 选简化后的 P/C；E 改为直接学习比较；F 保留 H/G/R。三项各买一次完整观察，不串成“规则阳性后才准学习”的流程。

本审查未继承 Root/DM 完整对话，但接收了选题和后续设计摘要，因此不是盲审。判断依据是原始源码、完整结果和技术失败记录，再与新 NOTES 对照。

**证据判断**
SET 的 c00→c06 确有学习收益，但只有一条完整恢复训练轨迹；两个新种子都缺终点，不是算法阴性。[原始终止记录](../../../../runs/energy_relay_baselines/b01_set_a01/seed-26092731/terminal-observation.json)

B03 中 Hungarian 相对固定一一分配仅增加约 .0068 QoS，相对独立最近点却增加 .324。这要求保留强普通对照，不能用失败分配器制造机会。[原始结果](../../../../runs/energy_relay_benchmark/b03_stake_a01/stake-sizing/summary.json) B05 的均值收益伴随严重风险尾部，B02 学习值函数又输给普通规划器；它们反对用代理分数代替完整收益，不反对新的学习尝试。

**D：Revise，选择 P/C**
值得测的是：**利用已曝光方向偏置的固定坐标规范化，能否使同一个冻结 c06 更有用？** 这比八路动作平均更直接，避免动作抵消、随机采样降噪和八路历史维护的混淆。

带固定 ID 的出生网格并不满足 D4 分布对称；NE 又是根据开发证据选择的。因此这是预先固定的部署包，不是一般几何泛化或对称性定理。[出生代码](../../../../envs/pettingzoo/relay/routed_core.py#L1115)

选择 P/C 各确定性和一次随机部署，加 H_central@10：16 新世界、80 完整回合、≤240k 步、0 fit。完整 J/QoS/风险改善才支持保留包装；阴性只限制这个包装，不能否定表示学习。H 是强普通替代，不是信息上界。

它**不替代 Claude 撤回的旋转物理世界 Block 2**，也不接管其开环探针或表示学习。无需因此加臂。40–100 分钟节点墙钟仍是估计，工程成本另计。

**E：Revise，直接购买一次学习比较**
选择最新的 **L 初始化、L 端点、H/P/A 同批评估**，取消独立先跑 H/P/A。理由不是需要一个神经网络，而是当前值得问：**经验能否学会信息获取的后续服务价值，超过固定公共先验巡查和信息量/路程规则？**

共同合法 BS/survey 记忆、候选地理、一个 scout、30 步时钟和运动保护，使 P/A 成为实质普通替代。L 直接选择服务或巡查，不只是修正 A 的评分；用原生 J 学习，禁止信息奖励、真值标签或隐藏世界预测。这不要求普通规则先证明阳性。

成本明确：1 fit、480k 原生步、160 完整训练回合、16k 宏决策、1600 次更新；80 评估回合/240k 步，总计 ≤720k。2–4 节点小时尚非实测，采集、工程和失败风险都是真实成本。训练单位仍为 **n=1**。

结果用途明确：L 的完整收益若超过初始化及强普通程序，支持这一有限经验学习包；只有 P/A 有收益，则普通搜索已解释观察；发现更多用户但 J/服务不改善，则该采集策略没有付清代价。任何结果都不证明纯信息中介，也不自动购买修补或第二个种子。

关键实现语义是有限 H3000 终点：宏奖励累积原生团队 J，不能通过 time-limit bootstrap 接入终点以后的价值。它属于正确性检查，不是额外实验门槛。

**F：Retain，选择 H/G/R**
原生服务确实耦合接入带宽分摊、关联和回传瓶颈，几何聚类没有直接优化这些量。[原生服务计算](../../../../envs/pettingzoo/relay/energy_aware.py#L966) G 的多初值几何求解是必要的强简单替代，H 保留已有能力锚。

8 新世界、24 完整回合、≤72k 步、0 fit、≤81.6k 无线查询足以第一次检验完整用途。约 1.43 worker-hour 的历史外推不含全部工程和竞争成本。R-G 是目标、搜索和可动支持的包差异，不是单独替换目标公式的因果效应，也不是最优性比较。

R 同时胜过 G/H 的完整收益才支持使用；G 已解释收益则无需归功无线优化；静态得分提高而原生结果变差，就保留该方法的失败，不自动追加时间预测或补能修补。返回/充电成员仍参与无线图，不能按 F 模式删除它们。

**整合**
D/F 的当前问题用零拟合完整部署即可回答；E 的强化问题需要真实学习。F 与 A 都涉及联合几何，但分别检验静态目标构造和完整时序计划；E 改变合法信息获取动作，不重复 B 的静态信息权比较，也不接管 Claude 的解码器。

科研速度应来自直接完整比较和比例适当的实现检查，不来自增加诊断层，也不来自把三个问题全部改写成便宜规则排行。

**MATERIAL_DISSENT: no。** 当前 P/C、直接 native-J 学习 E、H/G/R 已消除选题上的实质异议；不存在对原 P/G/V 或独立先跑 E 三规则批次的背书。

## Root Disposition

Root adopts all three final recommendations. D and F were sent the resolved scope
through native child messages; E received a native follow-up for the single direct
learning study. No child must wait for this archive or another routine Root ACK.
Each owns L0, implementation, proportionate independent engineering review,
published exact inputs, actual admission, same-handle collection, complete reading
and its own publication. New material disputes or out-of-question pivots return
to Root; normal implementation and publication do not.

One scientific clarification: the review's sentence that "only P/A have gains"
is read as support for those tested ordinary search packages, not causal proof
that information alone explains the gain. Likewise, no empirical loss localizes
all remaining loss to another mechanism. Complete native J, service, risk tails,
runtime and adverse worlds retain priority over intermediate scores.

Together with already selected A/B, the prospective scientific exposure is one
fit and at most 1.68M native team steps: A 72k, B 576k, D 240k, E 720k, F 72k.
This is the sum of declared comparisons, not a new allowance or proof of execution;
engineering checks and the peer's independently owned work are separate. E's
480k training steps are included, not added again. Model/radio queries and total
engineering/collection costs remain separately reported by their owners.

At this selection boundary only B had reported an accepted result operation;
selection, code publication and independent scientific review do not substitute
for terminal evidence. Root will use long native waits, read material returns
and choose continuation, reframing or stop from evidence. Prior technical failures,
adverse results, PPC/FSD pauses and G33's frozen contract remain unchanged.
