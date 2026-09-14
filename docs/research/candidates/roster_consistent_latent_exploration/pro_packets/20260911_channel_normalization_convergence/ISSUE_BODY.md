当前轮次：B06 后原始 Convergence 的梯度分配问题（2026-09-11）。Portfolio 已委托本次问题与完整 intake；目前实现与数值额度均为零，不运行模型、梯度样例、训练、评估或成本试验。

B06 的 .99 最近目标初始化已接近参照，但总体初始化收益 G_U=−0.000107828776042，并未改善；相对最近目标 Delta_ref=−0.00575764973958，八格服务比较均输给参照。局部初始化改善、两条主路径异号、碎片化和失败编码恢复均保留。不能由这些结果诊断梯度冲突。

本次具体候选：在同一64-episode原生返回批上，分别求经理计划评分与成员申领评分对完整共享参数向量的梯度，各自做单位L2归一化，再等权相加；非零合成方向仍取0.02全向量步长，单通道为零、完全抵消和共享张量的规则在固定TASK中明确。近抵消可能放大噪声，是候选的限制。保持合法 .99/.002 六动作先验、81输入、真实成员生存语义、tick24事件、四tick申领和完整64tick原生Y及U/F/失败编码恢复。

DM建议由一个未来新实例及自身初始化、INDEPENDENT-NEAREST回答有限配方服务问题。仅在所选主张需要比较joint100学习法则时，才加新鲜配对joint100控制；历史B06不是控制臂。具体方法和主张由原始Convergence决定，也可选择暂缓此学习路线。本次结束于一次完整答复/intake或明确阻塞，不自动追加实验或咨询阶梯；未来数值资助另行选择。

[Portfolio 原始固定答复 §5](https://github.com/CartmanFatass/My-paper-code/blob/50703c1bd1a4411c31a0b211d3ec8aff88fa0d0f/docs/research/portfolio/pro_packets/20260911_post_program_vacancies/archive/RESPONSE.md) · [已接收的 B06 intake](https://github.com/CartmanFatass/My-paper-code/blob/b842a255359f96d2173d0d4ee9d7551860680229/docs/research/candidates/roster_consistent_latent_exploration/RCLE_B06_NEAREST99_PRIOR1000_RESULT_INTAKE_20260911.md)

Pro只按本轮固定TASK向codex/rcle的指定RESPONSE.md写入完整答复，并在此留固定交付链接。历史Issue文字不扩大当前权限；Root派发Transport，DM读取不可变全文后做科学与规范intake。

---

以下为此前Issue正文，保留其历史含义：

当前轮次：A02 后下一对象选择（DM 综合，2026-09-06）。RCLE 仍 ACTIVE/MEDIUM；本 Issue 继续承载 TBCFV 上的有限预算学习与包比较，不是审批队列。



A02 已完整接收为 A/RECON：四种配置在两块样本中的 actor/pointer 分配均低于 1%，固定输入平均 TV 约 0.0054；去基线改变梯度方向但低占比仍在。Pro 的预测获支持，DM 的 10%—50% actor 占比与至少一块平均 TV 超过 0.01 的预测失败。冻结状态测量不证明训练修复，也不改变 B02 的近乎平坦服务结果。



[固定 A02 intake](https://github.com/CartmanFatass/My-paper-code/blob/588214ed62af2262fc904f1069eb37a336e9ff96/docs/research/candidates/roster_consistent_latent_exploration/RCLE_TBCFV_A02_RESULT_INTAKE_20260906.md)



DM 请求既有 Innovator 节点选择一个下一对象。推荐具名 B：同一 FLEX 包、同一个新配对种子 19，比较 actor-score 权重 100 与原权重 1，完整向量非零更新范数仍为 0.02，每臂 200×64 训练；以最终原生 U 为主测量。固定零基线对照是另一个候选，不加第三臂。建议两实例而非包×权重四臂；不设置先学会、上参考、完全归因或新增 A 的门槛。尚未冻结卡片或启动实验，本次咨询零新实验曝光。



[固定提案与限制](https://github.com/CartmanFatass/My-paper-code/blob/a86ff6c244fd81595375d00b9002c4ded28a1254/docs/research/candidates/roster_consistent_latent_exploration/pro_packets/20260906_post_a02_innovator/PROPOSAL.md) · [计算的曝光和成本](https://github.com/CartmanFatass/My-paper-code/blob/a86ff6c244fd81595375d00b9002c4ded28a1254/docs/research/candidates/roster_consistent_latent_exploration/pro_packets/20260906_post_a02_innovator/EXPOSURE_AND_COST.json)



Pro 仍只在当轮 TASK 指定分支新增完整 RESPONSE.md 并交付一条固定链接评论；DM 从不可变提交全文做 intake，Root 负责集成。旧评论和原始问题保留为历史。



---



原始发起问题（历史状态，以以上当前轮次为准）：



RCLE（roster_consistent_latent_exploration，路线 N3）在 2026-09-01 的 Portfolio 经验标准 recast 后处于 ACTIVE/MEDIUM，题目是有限预算下的包比较：在冻结的 TBCFV 旋转周界宿主（120 扇区、6 个服务信标、H=64、t_c=24 成员边界；训练 roster {6,10} 含 episode 内事件，held-out {8,12}）上，持久公共计划包 `C1P1-COMMON-PERSISTENT` 对严格含括它的 `FLEX-REKEY` 包在成员变动后的服务恢复（恢复时间 τ、未服务份额 U、学习曲线）。



当前状态：宿主定义卡为 definition_only（empirical_authorization=false），代码树 `experiments/candidates/roster_consistent_latent_exploration_tbcfv/` 有 23 个文件但从未有过结果性调用；A1 headroom 普查（2026-09-04）结论 `RCLE-HC-D / UPPER_REFERENCE_AND_GENERIC_BASELINE_MISSING`，H_A1 未识别。



本 Issue 用于该方向的 Innovator 决定：是否在 TBCFV 上开启第一个有界 B/EXPLORE 配对（DM 建议：两臂、一个配对种子、每臂 200 次更新、held-out 每格 256 个 episode、每臂 2,700 s 上限，CM 在启动前先做首次 native 构建与 ≤300 s 的零学习器可执行性/成本测量），以及预算、种子数、MEI、主测量与停止边界。固定证据与包在仓库 `docs/research/candidates/roster_consistent_latent_exploration/pro_packets/20260906_tbcfv_first_b_innovator/`。



Pro 的完整回复通过 Codex connector 写入指定分支的 RESPONSE.md 并在此 Issue 留一条链接评论；Root/DM 从固定提交读回并做 intake。此 Issue 不是审批队列，不改变生命周期。

