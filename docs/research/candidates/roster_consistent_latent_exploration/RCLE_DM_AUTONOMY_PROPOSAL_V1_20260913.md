# RCLE 方向研究管理员扩权建议 v1 — 2026-09-13

**建议稿，未改变任何 grant、card、Pro 决定或治理规则。** 本稿响应 Root 当前的方向管理员建议任务。建议把已存在的一次委托执行到底，减少逐步确认；科学/投资边界仍按现行层级。它不是新增研究授权，也不是新的 Pro 请求。

## RCLE 的三个实际边界

1. [B08 结果与 intake](RCLE_B08_JOINT_QUOTA_PHASE_INTAKE_20260912.md)：一项真实 fit 完成256更新，G_U=+.048152669，但 D_g=−.533040365、D_n=−.370141602，两主路径和全部八格服务都落后规则。结果、成本与保全/清理已经完成。旧900/900/1800限额结束，没有预算结转；这不释放 ACTIVE 方向槽位。
2. [post-B08 HOLD](pro_packets/20260913_post_b08_development/INTAKE.md) 只约束 exact joint-quota-phase/256-update Adam/final256 原样配方，旧 equal-unit/.99-prior/FLEX/final1000 HOLD 另行保留。[最新 Convergence intake](pro_packets/20260913_greedy_anchored_continuation/INTAKE.md) 仅保留 epsilon .1 exact-greedy log-prior 加既有 scorer 的候选问题，明确是 close-call，没有选择 fit、seed、card 或 cap。不能把“方向 ACTIVE”或“保留候选”写成已购实验。
3. 当前只有一项新的 [finite-investment 问题](pro_packets/20260913_greedy_anchored_investment/INVESTMENT_QUESTION.md) 在准备：拟议一项 seed29/256更新 B，新初始化、final、greedy、nearest 四角色，共18,432 episodes，拟议180秒 native/600秒 support/780秒 invoked 合计。源材料306cabf5923b44bbfa486fae7313b5fea8666613已发布；此稿撰写时 REQUEST 及22项固定引用核查已准备，尚未 bind 或 Send。推荐购买未应用，当前 grant 仍 NONE。它决定是否购买一次有明确服务后果的观察，不是对已批准运行索取 ACK。此稿不额外发送它或重复它。

上述事实来自本方向自己的 DIRECTION、最新 intake 和当前 handoff；主控 Portfolio 的简写只作协调快照。独立训练单位仍是一项 fit，已有正学习、巨大规则差距、新先验能力未知和完整成本 UNKNOWN 均保留。

## 建议直接覆盖的对象级执行权

现行 AGENTS 的2026-09-13条款和 ROOT_OPERATIONS 已明确：card、Pro 决定或 finite grant 固定了对象、输入、比较器与 cap，DM 自行准入并启动/收集/接受，无需新的 Portfolio 或 Root ACK。建议 v1 把下面的完整链作为一条委托在 handoff 中写清，避免每步重新解释：

| DM 可直接执行 | 边界 |
| --- | --- |
| 固定普通 seed/语义地址、文件名、命令及科学卡执行细节 | 只补足已选机制内的对象级细节；不改变冻结问题、比较器、RNG含义、endpoint、允许 fit 数或 cap。C冻结后不得重写。 |
| 直接实现、自检、修复以及安排必要独立高风险 Reviewer | 在所属源码/测试/文档与§4—5工程预算内；保留保护语义，Review用于技术接受，不是投资重投票。 |
| 显式 pathspec commit/push、准确源码 staging、实际目标节点资源准入 | 保留并发编辑；Root继续拥有main/index集成。准入是当前资源事实，不能由先前receipt代替。 |
| 对已定对象 detached launch，交给本DM native Monitor，收集完整输出 | 按精确 card/grant；确认MONITOR_ADOPTED后不重复轮询。失败/未知接受先核对，不能自动换源再fit。 |
| 技术接受、科学intake、预测核对、中文brief及已委托对象级结果分支 | 保留所有结果和依赖局限；不把n1变成稳定优势，不把错误/遥测缺失当科学负面。 |
| 可逆的同义实现修复、传输修复和原请求恢复 | 已证明未接受才可修复同一次发送；可能接受则仅观察/核对。新源码的结果-bearing调用仍是新launch，须在明确允许的调用数内。 |
| 保全及已授权清理 | 先留唯一证据/源码，只移除已列明的终止对象；Root确认集成/保留并接受回收，不删shared/live工作区或证据根。 |

**建议明确的增量**：每个接受的有限分配，在同一记录中写明“授权包括卡片执行绑定→实现/检查→准入→启动/monitor→intake/保全”，并指明授权结束的那个具体分配。把这些常规步骤全部留给同一DM；Root收到事件后集成和协调，不再为每一步发续行动词。本文只建议这种表述，不扩展任何现有调用数、允许变体或 cap。

## 仍须 proper node 的决定

- **对象层，DM站立委托**：既有机制/预算内的card wording、下一rung、treatment/comparator、删arm和cap内偏差，按未被owner接管的实际委托处理；列出选项、推荐、执行项和依据。若它改变已冻结科学意义，普通实现自主权不覆盖。
- **方向层，Convergence**：开/关对象家族、RECAST、consumed C 后的下一对象和C-BENCH提升；C冻结前按既有 Innovator 路由。现有B08 HOLD、候选A决定不能被DM“更高效率”地改写。
- **Portfolio层**：新增投资/调用预算、容量/priority、whole-direction生命周期、融合/分离、登记和vacancy replacement。当前B09因从未获得fit/card/cap选择，恰是一次新投资问题。若Portfolio buy并完整符合范围，后续实验变成上表对象级执行，不再发一轮投资请求。
- **明确冲突或owner接管**：冻结意义冲突、共享活跃writer、耗尽允许调用数、外部接受不确定，报告具体事实。只有依赖部分等待，独立已授权工作继续；不以本地建议替代未形成的方向/Portfolio决定。

建议每次准备 proper-node 问题只加一句“这次新观察会改变哪一个实际选择”。没有这个后果、或已有card/grant已回答，就不再发同类审批请求。科学菜单、重复ACK、因工具失败而改题以及为了维持活动外观而连续咨询，都不属于扩权。

## 审计：复用现有账本，不建新审批面

普通对象决策继续使用原字段：time、direction、tier、kind、options、chosen option、reversible、provenance、evidence、owner flag、owner。kind=selection才表示选运行/策略/arm/预算，其余为technical。没有owner回复就保持owner空白；不补写批准。下列为填写示例，不是已发生的审计行：

| 情境 | 选项与实际记录 |
| --- | --- |
| buy后的B09普通实现/准入/启动 | “按所选对象执行 / 返回具体完整性或资源缺口”；选执行时标Owner-delegated decision，并引用最终Portfolio intake、card和accepted handle。无需新Portfolio项。 |
| B09 Portfolio买/不买 | 选项只含单一有界分配与暂不分配；完整答复conformance后记PRO_FINAL / OWNER_DELEGATED和实际应用边界，P1 item保持异步。 |
| 发送效果不确定 | 记technical：原request observe/reconcile，不记科研失败，不加fit或新题；引用operation/paired IDs/immutable response或精确缺口。 |

只为新card、方向决定、close-call、重大dissent及Portfolio等原P1/P2时点使用owner CLI。候选A的close-call已在20260913-rcle-002；本建议稿不是一次实际扩权决定，不给它伪造auto_applied。未知成本/遥测仍在原intake；不增加profiler、审计实验、状态机或普遍gate。

## 回报：四行普通native消息，无ACK要求

建议在完成、实质阻塞、ACTIVE-idle这三个改变事件用一条可执行消息，内容为：

- **本次assignment和状态**：具体完成/未完成的对象或请求；方向生命周期另写清。
- **决定与边界**：由谁、哪一层、选了什么；grant/调用数剩余或无拨款；不用“完成”暗示停向。
- **证据与交付**：commit、card/intake、accepted handle或immutable response；最强支持/反对和具体未测项可合并一句。
- **下一动作或依赖**：DM将直接执行的下一步；Root仅需集成/解决哪个共享依赖，或明确哪个proper-node问题尚未形成决定。

这不是强制新schema，不需要新的envelope、ACK、台账服务或重复唤醒。例：“B09单一投资问题已一次发送，等待Portfolio完整决定；RCLE ACTIVE/MEDIUM、当前未启动fit。固定TASK/HANDOFF及operation见某commit。DM由自己的Transport接收全文并intake；Root仅整合资料，buy后DM自行准入和执行。”原请求不得因为这条回报再发一次。

ACTIVE-idle时先检查是否有已获授权的下一对象；有则同DM自行前进。若只有明确未决的新投资问题，就自主写完/发布/bind并通过原native Transport发送一次，随后继续独立工作或native wait。若没有非虚构的问题，返回“缺哪项实际选择/事实”的有界阻塞，而非等待Root逐步授予已存在的执行权。未变的wait timeout保持静默并继续等待。

## 本稿的应用状态

**PROPOSAL_ONLY。** 当前仍只有已接受的候选保留A和两个原样配方HOLD；当前投资问题尚未Send，无新grant/fit或规则修改。本稿只提交给Root汇总；若要改变治理规则，走现有适当权限并保留精确来源。原来已授权的单次finite-investment准备/发送任务继续其原路由，本稿不生成第二请求或扩大投资范围。
