# Retired Native Round-Two Execution Plan

Historical-only snapshot, retired 2026-09-28. It does not authorize new work or
alter accepted operations, direction ownership, pauses or evidence.

Source revision: `a0d9d67fb67265a2ee24b75733928f04508173eb`. The selected plan was published at
`457cd15d49f512b1e30de04609cf69582ce56649` and remained substantively unchanged
through this snapshot. Relative links below are rebased; the complete selection
question, amendments, independent answer and Root disposition remain in
[the selection archive](RESEARCH-native-round2-selection.md).
Current result integration and method recommendation are in
[RESEARCH](../../RESEARCH.md#current-research-plan). Each direction retains its
full result reading, independent disposition and cost in its own NOTES.

## Current research plan

**Owner已启动新一轮研究（2026-09-28）。** 按已发布方法选择两项可改变后续研究判断的完整比较，
由新建原生DM承担；前轮已完成DM不复用。选题的同一次独立科学审查已读完，两个实质问题已修改：
主动感知增加普通固定探测频率对照，信息归因不以“不显著”或微不足道的算术简化来偏好站点0。
完整原问题、修改、答复、Root采纳及被替代的前轮计划见[本轮选题记录](RESEARCH-native-round2-selection.md)。
这是已选研究，正在各自的声明/实现/工程检查流程；是否已接受、完整收集和科学读完，以方向NOTES及原生记录为准。

| 研究问题与负责方向 | 完整比较与预计成本 | 结果将改变什么 |
| --- | --- | --- |
| A：同合法信息下，学习何时及往何处探测，能否提供超出普通策略的完整用途？ `uav_active_sensing`，新DM `/root/dm_sensing_round2` | 所有臂共享固定P_BS规划支持，明确区分推断与真实见过BS。初始服务/探测概率各.5，探测后条件选择256目标；仍有可用服务UAV、返航margin、6..29合法用户限制和30步承诺。1fit/480k训练；16新H3000世界同场H/L0、L1、A、R50，64评价回合/192k步，约70–95节点分钟。H/L0仅在零gate及确定性tie→service的逐决策恒等核验后共用一次评价，不算额外复制。 | L1须面对适用的普通服务、按新鲜度探测A及未调参的“服务/探测交替”R50，而不只胜初始化。阳性支持单实例when-and-where学习包；充分执行仍无益削弱该有限包的用途；稀薄执行限制解释，但不丢弃inactive世界或自动放宽gate。不是类别平衡、纯时机或旧失败原因的归因。 |
| B：站点代数推断相对同样启用中继的简单合法锚点，是否增加决策内容，改变普通参照？ `uav_information_value`，新DM `/root/dm_information_round2` | P_BS、直接站点0的S0_BS、真实观测记忆H_BS；共同32新世界28100301–28100332、H3000，0fit/96回合/288k步，约27–40节点分钟。真实见过BS永久优先，保持共同重规划/持有动作时序；分别记录输入、生成/分配中继、提交命令与实际移动。 | P–S0主要总J对比连同服务/风险决定几何变换的条件性用途及未来参照。S0有利可支持该替代；两者均胜H但差异仍宽则保留未决，不宣称等价或仅因更简单就偏好S0。保留P历史替换限制和新面板的前瞻风险规则，不自动补世界或安全修补。 |

合计计划**1fit、480k训练步、480k评价步**，160个完整评价回合；约97–135节点分钟只是基于既有运行的估计，
工程、排队、复核、读数及当前竞争另计，非时间上限。精确配置/种子/评价与实际成本由各DM在NOTES前瞻绑定和报告；
本轮是探索，不是独立训练种子间的确认。A固定使用既有P_BS资产，不等待或按B结果调参；B保留被A使用的旧控制器字节。

**Root如何判断信息增益。** 看完整结果是否改变学习包的投入、普通参照或解释边界，而非仅看正分数/实验数量。
设计阶段的R50对照和B未决分支已真实改变比较/取舍；结果仍可能无判别力，也不能因方法被采用就宣称科研效率已提高。
前轮7批/640轨迹/1.92M原生步/1fit的完整结论与风险保留；未复活解析I/C、固定NE、旧257类或roster私有历史前提。
Root负责跨题判断；DM独立执行、读完、发表及考虑有价值的续题，一次结果不产生自动修补配额或逐fit审批。

优先使用配置节点并做新鲜实际资源准入，真实训练和评价都占资源；Claude的 `energy_relay_benchmark` B05 fit及其既定面板保持原身份，
不重跑、迁移或复制SW研究。PPC/FSD暂停、G33冻结和其他方向归属保持。原生子DM保持turn并对同一handle长等待，
Root用native `wait_agent`等待实质返回；不把启动/接受当作结果。现有方法见[方法复核与采纳](RESEARCH-method-workflow-review.md)，
无需新增常设角色、skill、pilot或逐批科学审查。当前地址见[任务路由](../../RESEARCH.md#session-routing)。
