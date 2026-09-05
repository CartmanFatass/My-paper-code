# 两类、六族、九路线：修订提案

日期：2026-09-04
状态：`PRO_FINAL / OWNER_DIRECT / ROOT_INTEGRATED`；所有者随后批准推进自动研究，见
[采用与恢复记录](2026-09-04-adopt-nine-routes-and-resume.md)。以下提案正文保留审阅时语境。
来源：[所有者复制的完整 6 Pro 回复](../../../external-review/2026-09-04-two-line-consolidation-6pro/OWNER_FOLLOWUP_02_RESPONSE.md)
证据参考：`b35eadf954a0bc56f3291f3b3d2b9ece0748e4a9`

## 本次修正

两条线用于分类，不设“每类只留一个”名额。保留不同科学问题，通过机制族共享管理、
已兼容的环境、基线和诊断，减少重复工作。九路线是目前的地图，不是新的数量上限。
此前只保留 FSD、FRRIE 的建议已被这份修订撤回；Root 从未应用那份 PARK 清单。

## 建议采用的研究地图

| 分类 | 机制族 | 路线及来源 | 本轮投资位置与边界 |
| --- | --- | --- | --- |
| 灵活 agent 数量 | 集合与关系表示 | N1 关系归纳与学习效率：FRRIE | 保留 contact-active R128 R02；当前只覆盖已见 N，不声称 churn 或未见人数迁移 |
| 灵活 agent 数量 | 成员变化后的恢复 | N2 恢复动作：VNFC | 保留因果 one-deviation R03；second-recast 与既有最低排序保留，不恢复宽 K 搜索 |
| 灵活 agent 数量 | 成员变化后的恢复 | N3 状态保留、重建与迁移：RCLE、FOLR、DISH、VSP-02 | 一条同族探索议程；分别隔离记忆状态、状态来源、optimizer state，不恢复四套独立管理链 |
| 灵活 agent 数量 | 成员变化后的恢复 | N4 旧信息有效性：CBSC | 保留原 host 的 online B1；r06 技术失败，r07 未创建；不要求先接入统一 N host |
| 灵活 agent 数量 | 资源配置与几何 | N5 配置结构与 FREE：MGTAP | 保留小型 B 探索空间；具体新对象与成本待定义，两个旧 C 不恢复 |
| 灵活 skill duration | 中断与续约 | K1 中断时机：FSD、VSP-03 | 保留 E3，10/18 有效、8 格未启动；事件规则属于以后具名控制，不加进现有 E3 |
| 灵活 skill duration | 中断与续约 | K2 动作边界学习：CRTO | 保留 RAW-only 252..264 trace；处理远端依赖，不把诊断当 residual 胜出或挑 checkpoint |
| 灵活 skill duration | 信息获取与续约 | K3 付费获取：UCOPE | 保留 root／数值审计与机制探索；工程 scope blocker 仍须解决，不等待接入续约 host |
| 灵活 skill duration | duration 表示与价值共享 | K4 跨时长共享、组合与负迁移：SCDMP、VSP-C1 | 中期前瞻问题；尚无新冻结对象，旧 D6 家族的 PARK 不解除 |

六个现有入口：**FRRIE R02、FSD E3、VNFC R03、CBSC online B1、CRTO trace、UCOPE audit**。
另给 **N3 状态恢复、N5 配置几何**形成有界问题的探索空间；**K4** 保留前瞻研究位置。
“保留投资”不等于“现在可以运行”，也不等于九条常驻 DM。原有执行暂停与资源准入保持。
N1–N5、K1–K4 是路线标签，不是运行排序；VNFC 的 second-recast 不因归组清零。

## 其余来源的明确去处

下面八个来源作为可调用储备或保留原有停止边界，不再各建完整研究链：

| 来源 | 保留价值与限制 |
| --- | --- |
| ACVC | 合法历史的正动作价值、second-recast 与证书边界保留；不自动重开旧 learner／证书搜索 |
| EOCIV-Lite | receiver-addressed 家族继续 PARK；保留相对收益与初始化信号，不转成普遍负结论 |
| RECCT-Lite | target intervention 储备；需要 consequence-distinct 干预，不继承 EOCIV 极性 |
| EC4G-R1 | receipt-content 控制储备；无效 aggregation 不成为有效 learner 证据 |
| Scope-1s | 信息切断控制；信息集差异不冒充同信息优势 |
| Orbit | 角色与有效性控制；保留已有 PARKED 状态 |
| EGRCR | 当前 factorization 家族 PARK 与既有重入边界保持；不抹去局部正 utility 差 |
| APFI | 独立 population-flow 问题和已有 PARKED 状态保留；不按 churn 名称强行并入 N 算法 |

这里是提案中的管理与投资去向，尚未把这些描述批量写成新的 Portfolio 生命周期。
SCDMP 同时出现在 K4 的前瞻议程和旧 D6 的停止边界中；两者不可混同。
共覆盖全部 22 个历史来源，保留来源 ID、卡片、证据路径、无效尝试与 Pro 绑定。

## 哪些共享能产生实际增益

1. **N2/N3/N4**共同区分：恢复动作选错、内部状态丢失、旧状态失效。每次只改变一个干预位置；
   RESET 通常是信息切断控制，同信息效率比较器要另列。
2. **K1/K2**共享兼容的中断成本、错误继续／错误中断计数和原生回报评价；简单事件规则、
   policy gap、residual、RAW 保持具名。不要为统一接口先建设大平台。
3. **CRTO/UCOPE**共享决策边界诊断：局部排序改善是否反而恶化有成本的上游动作。
   这是待检验的共同解释，不是已证明的共同病因。

优先衡量下一步能区分什么、每个有效结果用了多少同节点计算、还能复用什么。
已有卡片和 readiness 影响可执行顺序，不能替代科学价值。未测成本保持未知；
共享能节省多少训练必须实测，不预先记作收益。

## 初步成果与 UAV 边界

- UCOPE：3 seeds × 2 folds 中 5/6 策略取得约 +0.021437 净获取值；完整能力尚未全部通过。
- FOLR：KEEP 约 0.852、RESET 0.5，显示记忆使用；简单 latch 约 0.970，未证明 typed-memory 优越。
- VNFC、CBSC：分别有受限因果／控制见证和精确协议价值；均不等于通用 learner 优势。
- FSD：真实 D2 路径已实现，但 E2 是 NEITHER，E3 未完成；FRRIE 的新 R02 尚无结果。

按现行 spec，B 可以直接在 UAV learner 上开展，不以 toy 胜出、定理或 headroom 数值作门槛。
已有材料不能直接宣称正式 C-BENCH／C-TRANSFER 成功；需其对应的冻结公平比较、
独立重复、胜任控制与不确定性证据。此次没有冻结或启动任何 UAV 对象。

## 审阅点

建议采用上述组织地图与投资位置，再逐项写入 Portfolio；不自动恢复实验。
所有者已直接确定两类与同族归组的目标，并要求这份扩展回复回来后共同审阅。
本文件据此保留为可核对的修订提案，不把“已手动复制回复”冒称逐项生命周期批准。

Scope: none.
