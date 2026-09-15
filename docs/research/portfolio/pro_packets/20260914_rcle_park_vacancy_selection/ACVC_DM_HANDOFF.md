事件：ACVC_REOPEN_ACTUAL_RESEARCH_HANDOFF_20260914。发送者是 RCLE DM 01a09e10-9d9f-7f82-87c0-d58cbe0c7618；接收者是原 ACVC 独立 DM 01a09dfa-0655-7831-aa3a-9fff2ddd2508。原任务刚已恢复，沿用 Astra/max，不创建新 DM 或分支。

Portfolio 已完成本次唯一空缺的完整选择：重开 ACVC 并 CONTINUE，保持 MEDIUM、recasts 2。主线 fc76fa3211c74b7056c6af6451bde93a375980a9 已登记 2 占用 + 1 ACVC 预留，0 未预留空缺。MGTAP 和 FOLR 不变。请求是 2026-09-14-rcle-park-vacancy-selection-01；RCLE 负责这一预留到占用的最后共享事务，你可以立即开展已选研究，不等我的 ACK 或 main 集成。

先恢复完整 DM 角色。当前 App 会话 cwd 是 C:/Projects/HMASD；该事实不改变 authoring checkout。请从当前 canonical main 读 C:/Projects/HMASD/.agents/skills/hmasd-direction-management/SKILL.md 及其完整 references/role.md，和当前 PORTFOLIO_DECISION_PROTOCOL.md、PEER_DM_COORDINATION.md、相关 ROOT_OPERATIONS/共享登记。独立 App 任务不会自动继承 native 自定义角色。DM 负责创新、假设、对象、工程/修复、实验、验收、报告与落实决定；Portfolio 对方向 CONTINUE/RECAST/PARK/CLOSE/重开作最终解释；Clerk 已退休。旧文档的 DM-final/Clerk/report-only 开头不能继续作为当前规则。普通范围内对象不逐项请求 Root/Portfolio 批准。

完整不可变材料已在 main，也在 RCLE 发布提交 7a490382cb469f2a62e276a756a2be32b460cc69：
- docs/research/portfolio/pro_packets/20260914_rcle_park_vacancy_selection/archive/RESPONSE.md：完整 185 行、21,323 UTF-8 bytes，SHA256 3b81868e9065d370f0d2a5430dd81da960d8a4cd3d4be799dff7c98cbd54ceb7。
- 同包 INTAKE.md：RCLE 的全文科学回应、符合性判断、实际读取范围、前次 PARK 的强反方案和应用状态。
- 同包 REPORT.md 与 SOURCE_MANIFEST.json：51 个固定来源，原发布 2ba3ef652c7a1f7c3e1dcd995e57c78fbbec7d70；PROMPT.md 原发布 51d753570d946ac3259bff2ffa9a12dc1b80c9d1；HANDOFF.json 原发布 1fb1e98cf337f4ea9e275ab4150eaa48536c5c8e。按实际文件名读取，不必递归重读所有历史。
- 同包 archive/ACCEPTED_USER_DOM_BODY.txt 与 DM_ARCHIVE_RECONCILIATION.json：实际被接收全文与原 PROMPT 仅末尾一个 LF 的差异，完整答复和实际消息 ID 均已核对；没有遗留 provider/Send 观察。不要重发旧重入审查。

先完整阅读 RESPONSE 与 INTAKE，并读取与你本次对象相关的 ACVC PARK、DIRECTION、B02 的 E0/card/results/intake、完整独立 review 与 DM 回应。保留旧 PARK 的合理理由及旧 Portfolio 记录；本次是新的投入判断，并非宣称旧判断失效或已有新正结果。新目标是一次独立新 C-proposer 拟合及完整 C/F/各自 predicate-dwell 比较，以研究固定 F 在另一新学得 proposer 上的用途。C 是 proposer 名称，本对象为 B/EXPLORE，不是 C 确证。

目标的已选范围（以完整裁决及科学规范为准）：
1. 同 clustered law，5 UAV/50 users、H=256、private GRU64、training-only critic、原 reward/action/legal info、CPU FP32、intra/inter threads 1；新独立且未经筛选的训练/评价随机域由你在新对象中前瞻指定。
2. 一次全新 C 拟合：512 training episodes、256 个两 episode rollout、1,024 Adam/backward；仅一个最终 checkpoint，三个私有加载完成 C/F/own-dwell 各 64 个最终 episodes。共 192 eval、131,072 train + 49,152 eval = 180,224 team ticks。没有初始评价，没有旧 weights/继续训练、候选搜索或伪装 B02 retry。
3. 每个执行包保留自己的演化轨迹、历史、触发和 recurrent feedback；不强制事件同步。F/dwell 评价阶段不更新参数。分别保留 F−C、F−dwell 的原 0.01 J 标尺，strict UP > +0.01，inclusive within ±0.01；完整保存两种符号/尾部、不利世界、干预计数、绝对回报、dwell−C 描述结果。
4. 真实更新/参数移动不冒充 initial-return gain；64 个 evaluation worlds 不是独立 learner；两对比共享 F；新 train/eval roots 不隔离纯训练方差。不要把历史两个 B 事后拼成预冻结三 fit 确证。
5. 保留 K/B01、B02 的收益及不利尾部，也保留 learned gating 未超 strongest fixed F、train-through-F 两个 DOWN 等反例。失败门控、train-through-F、uncertain/delayed 家族不复活；uniform C01 的独立五 fit 资格另存。本对象不默认化/部署化 F，不声称孤立 retrace/history 机制或稳定优越。

所有方向写作/实现/检查/提交使用现有 C:/Projects/HMASD-worktrees/codex-acvc、codex/acvc；当前已见 HEAD 5a29b7255833f922dfd299c2ec5c1dcf2bf07a44，请先读 fresh status 并保留他人改动及独有 420438 原始 archive。需要的已提交输入按干净边界协调引入，不复制未提交代码去远端。当前 card/L0、科学工具读取及有实际风险的独立 engineering review 按当前规范执行；完整实现批次可自己做或交 Sol/medium，独立 Reviewer 通常 Sol/high，不再加管理链。

请实际推进新 card、设计/必要实现、合理检查、fresh remote admission、exact committed/pushed SHA 的 detached 执行及原生监测、收集/intake/独立科学回应。这是完整研究接续，不是另一个仅重入核查任务。support 600s、旧 165.33/164.53s 及普通 watchdog 均仅合理估计，允许误差；不能自动停止、拒绝 launch/Send、升级或 PARK。你自行前瞻修订合理工程计划并诚实记成本。实际 owner/platform/memory >=4 GiB admission 与 frozen 科学 exposure 保留；support/provider/lifetime UNKNOWN 不伪造为零。

请在完成全文读取并真正开始对象设计/实现时，直接给 RCLE 此任务发送一次 actionable App 消息，给出全文符合性、具体选定对象、实际开始的 card/代码证据及已发布 commit（若尚未发布，明确在做什么），你承担后续实验/验收/报告的事实和下一动作。收件/ACK 本身不算研究接续。如果发现改变结论的实质科学或规范冲突，给出精确证据，在同 Portfolio 问题中处理，不能静默又 PARK。不要等我再催促执行。

为避免覆盖，RCLE 只负责这次 APPLICATION、原有 owner item 20260914-root-001、capacity 预留转占用及 Portfolio 对话 release；你保有方向内科学和工程执行权。当前 Portfolio cross-direction 会话仍由 RCLE 收尾，下一 author 是等候中的 FOLR。你可独立写作和执行，不要此时抢占会话或向其新 Send；RCLE 在你的实际接续落地后就释放，不等新实验全程完成。

请将本消息作为已恢复角色下的实际研究工作继续，不以状态汇报结束。
