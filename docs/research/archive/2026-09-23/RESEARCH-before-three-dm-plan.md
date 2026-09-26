# Historical plan — before the three-DM allocation

Retired 2026-09-23. Source revision: `c13350a7ce9ddbcf0c55acacae03fa93a9e140fd`. Historical plan only.
The accepted Pro question and its answer target remain in [current RESEARCH](../../RESEARCH.md); they are not retired here.

## Current research plan

**当前科学安排（owner，2026-09-23 新授权）。** 本任务持续担任项目管理者。研究重点是有限数据和计算下有用的联合技能与完整 UAV 服务；可变 k、可变 N 分别研究，普通学习改进也有独立价值。
负结果进入下一次判断：先问它约束了哪个假说，哪些问题仍有可改变决策的实验，再自主推进选中的工作。
不要求坚持旧网络、旧方向名，也不要求先做完所有便宜诊断才准许训练。

| 项目优先事项 | 当前动作与依据 |
| --- | --- |
| 保留可重复的策略包优势，检验有用技能的学习 | 人数 B10 已完成：保留开局标签的均值更高，但存在明显局部服务损失；这削弱持续重分配是均值收益必要条件的解释，不证明技能学习无用。技能 DM 的 D/G/P 共同学习继续原合同，避免再并行复制一个交互预测辅助配方。 |
| 从容量诊断转向实际学习 | Root 正在复盘一个具体候选：普通 SET 在 N6 与 N8 下各训练 360k，在共同 N8/N6 面板比较服务与专门化代价；预计 2 fits / 64k final eval。容量 B01 给出真实资格缺口而非可达最优界；该比较检验直接训练是否改变服务，尚未批准为固定实验。完整建议返回后由 Root 在当前授权内选择、登记并推进，无须再次等待 owner 选题。 |
| 收回已产生的科学信息 | 聚合 E 原进程已完成；Root 已收回并核验原生输出。既有观察失败及缺失 checkout 与科学阴性分开；不增加一次训练来替代丢失的观察。 |
| 以机会成本管理其他方向 | 旧 dense、duration、S7 辅助预测、固定容量配方的结论继续约束各自做法；DM 可以结合全项目证据转向有区别的学习问题，不默认让所有归档方向重新运行。 |

[下方当前复盘](#portfolio-review-2026-09-23-scientific-management-and-next-learning-investment)列出下一笔训练的理由、最强替代解释与成本。
已完成的旧计划见 [本次变更前快照](../../archive/2026-09-23/RESEARCH-before-scientific-management.md)。
[文献提案](../../designs/LITERATURE_RESEARCH_PLAN_20260922.md)作为科学参考，不能替代冻结合同、真实比较或 DM 判断。

| 研究问题 | 当前优先次序与第一个比较 | 证据如何约束投入 |
| --- | --- | --- |
| **普通局部信息组织** | B01 已完成并归档当前 dense 配方，0 追加 fit。 | S1 固定 k/N、同信息完整共同学习的两个 fits 中，dense 在三个预写面板的平均 J 均较低，且实测成本更高；每臂一个训练实例，不建立表示类总体排名。没有选中修补或后继比较。[最终判断](../../candidates/local_observation_encoding/NOTES.md#2026-09-22--dm-decision-archive-the-tested-dense-recipe)；[退役的初始计划](../../archive/2026-09-22/RESEARCH.md)。 |
| **技能周期与有限学习** | B01 三臂完成，关闭本次 S1/cap=10 普通分解／AR 配方，0 追加 fit。 | 新时长选择确实执行，事件与高层优化量增加；两种可变臂终点均低于固定，AR 后段胜分解不足以满足既定保留条件。每臂一个训练实例，不否定更广周期问题；长于十步的承诺另需实际团队时钟、支持与相应固定参照，尚未选中该比较。[结果与判断](../../candidates/joint_duration_skill_learning/NOTES.md#b01-complete-three-arm-result-and-closure-of-the-cap-10-recipe--2026-09-22)；[退役的初始计划](../../archive/2026-09-22/RESEARCH_02.md)。 |
| 事实预测辅助 | 独立近邻：同一个实际训练的事实 readout，detach 对辅助梯度进入 actor/GRU。 | 两臂都有预测头；最终看完整回报，不能用更低 MSE 代替用途。先选一个后果/窗口，不叠加规划、通信、duration。 |
| 技能规模与实际重组 | 分别选择有依据的较小标签集合，或固定 k 下真实 partner-skill 重组曝光，对普通匹配训练。 | 标签组合数不是样本复杂度；保留正常搭配收益。技能可辨认不等于有任务互补性，冻结标签探针不是新共同学习的阳性门槛。 |
| **N 数量泛化** | B10完整验收，结束本次开局技能复用诊断；保留原包和明确局部代价的部署替代，0追加fit、无已选后继。 | 平均J与覆盖在N4/6/8均提高，但有13个覆盖损失世界与N4质量代价，不能由正合并均值推广统一替换。干预改变全部48世界执行；削弱持续采用新标签是本批均值优势必要条件的解释，保留具体世界中在线重选的服务价值。训练重复仍为1；不认证flat、不推导技能训练无用或省算力，后继须有区别明确的事前预测。[完整证据与决定](../../candidates/agent_count_generalization/NOTES.md#2026-09-23--b10-complete-opening-assignment-replay-improves-means-with-consequential-local-losses)；[退役实现计划](../../archive/2026-09-23/RESEARCH-agent-count-b10-complete.md)。 |
| 运行中成员变化、cross-play、异质能力 | 三个独立备选问题：服务连续性/区间信用，独立 population 混编，能力条件化共享。 | 分别继承 VNFC、CPCP、FOLR/ACPS 等证据；先明确真实任务和合法接口。技术失败、未执行和科学不利分别处理，不合成笼统“适应性”。 |
| **UAV 端到端服务预测 / 文献第 1 项** | B03六格和两次固定共同端点回放均已完整验收，关闭当前配方；无下一批、运行中操作或待收Pro。 | 1.08M train/576k eval/42k physical facts，6 fits共769.038846 runner min；两次回放零新fits/更新/环境步，另1.693106 min。S−D、G−D两块均反号；G服务提升重现而成本下降不重现，MSE优势也不能挽回原生结果。按既定分支不追加第三块、重调、较早终点、长训练或确认；未来重开须有新的科学理由，不能从两块推总体无效或稳定排名。[完整解释和成本](../../candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b03-second-common-replay-accepted-and-current-recipe-closed)；[退役的运行中计划](../../archive/2026-09-23/RESEARCH-uav-service-b03-complete.md)。 |
| **技能条件化的信息聚合 / 文献第 3 项** | B01 三臂原生进程均完成；Root 已收回遗留 E 输出，原 DM 最终方向记录尚待完成。 | P 的 J45=.159861，低于 O 的 .509137，服务分量与实测成本均不利，削弱当前池化配方的投入理由。收齐 E 后比较 E−O、P−O、E−P 与成本，再作三臂判断；不把 32 个世界当训练重复，不识别实体筛选机制或技能语义对齐。[P 结果与固定接续](../../candidates/goal_conditioned_entity_aggregation/NOTES.md#2026-09-22--b01-p-complete-and-read-e-remains-the-fixed-third-arm)；[E 启动](../../candidates/goal_conditioned_entity_aggregation/NOTES.md#2026-09-22--b01-e-accepted)。 |
| **负载与关键成员泛化 / 文献第 6 项** | B01 已完整核验并结束当前诊断路线，0 新 fits / 80k eval / 160 episodes，5.911021 command min；无后继或待收操作。 | 五格平均 H6 原生 J/覆盖优势保留；容量放宽时 SET 在 N4 恢复更多用户与 J、H6 在 N8 更多，D4=−.020377、D8=+.023481，原两-N统一预测失败。资格、截断及质量组成解释这些固定路径的转换；同 N 高度抵消，同 K 残差不识别纯 N。按既有 Pro 混合结果/信息价值分支停止，不追加没有明确学习用途的 balanced-c fits 或异质接口。[完整证据与决定](../../candidates/load_critical_member_generalization/NOTES.md#2026-09-23--b01-complete-useful-package-levels-mixed-capacity-response-route-closure)；[退役的运行中计划](../../archive/2026-09-23/RESEARCH-load-capacity-b01-complete.md)。 |
| 支持方法与条件候选 | 真实行为漂移下的经验复用/critic，任务相关 discovery，普通物理模型及学习修正，通信、尾部服务、实体/角色动作，事件终止/时钟课程。 | 只为具体待估未来量或真实服务后果选择。普通方法已解决就保留；行动接口、目标和信息权限改变单独解释，不列为前一个配方失败后的自动续集。[候选全集](../../archive/2026-09-21/RESEARCH.md#potential-research-directions-2026-09-21)。 |

**普通编码比较的当前结论。** 已读完冻结 J45、15/30/45 面板、原生服务分量及实际成本。
已测试 dense 包没有兑现原生收益/成本预测；完整 Pro 咨询后结束此配方投入。训练种子差异和其他表示机会仍未解决，
旧 dense 配方没有追加比较。owner 现已选择第 3 项的技能聚合位置问题，按新 NOTES/Pro 判断其区别与成本；
这不是旧 dense 配方的阳性翻案，也不为穷尽可能解释自动追加实验。
完整 HMASD 表示比较不能承担“层次结构胜过 flat MARL”的结论，后者另需能学好的同信息 flat 参照。
实际 horizon、种子和 fits 由选中后的 prospective note 声明，本页没有接受批次。

**周期比较的判读。** 策略类确实包含固定方案时，最优值不降低；有限训练仍受探索、估计和优化影响。
联合式只赢分解式但输固定 k，不支持增加实际复杂度；两种可变方式都有效而无可靠彼此增量，则保留简单方式。
只改变时长统计、熵或局部信用不构成服务增益。没有有用增量和具体新区别，就停止所测配方。
S1 只能检验自身覆盖/连接后果；S7 研究需要其真实服务机制，不能因 S1 阴性就自动换宿主制造机会。

研究依据在本页的[背景与共享认识](#研究背景与共享认识)中统一维护；必要正确性修复在相关新比较中共享。
完整答复、推导和原始结果留在方向 notebook / claim / runs 与日期归档。每次有新结果，重新选择下一笔有信息价值的投入，
不承诺遍历整个候选清单；并行强度不构成科学方向配额或自动补位规则。

