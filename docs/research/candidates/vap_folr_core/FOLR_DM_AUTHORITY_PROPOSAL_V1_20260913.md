# FOLR 方向研究管理员扩权建议 v1

建议将 DM 的端到端责任落实为连续执行权：一项已授权对象从实现、运行到
collection、验收、intake 和范围内的下一步，由同一 DM 执行并承担判断责任。
Root 接收变化和执行依赖，不逐步签发许可。

本文件是 Root 指派的建议稿，不修改治理规范、FOLR card、科学含义、caps 或
生命周期，不新增 Pro 请求或实验。现行规则已支持下列多数权限；建议重点是
消除实际流程中重复等待 ACK 的行为。读取的当前控制版本为
`7357fdb884e07a939c0b7d92534139b1f0a1bc83` 的 ROOT_OPERATIONS.md。

## 1. 当前 FOLR 的具体边界

Portfolio 已完整决定 F，来源为 `9e37525139abc18ab6b9dcd393a21e5a24f12e26`，
[conformance intake](pro_packets/20260913_retained_reference_investment/INTAKE.md)
已接受。该投资问题已经关闭，当前没有待批准的 Portfolio 请求。

新的 Generic64 已在固定源 `5dce539ed54afd4334d09db9dcd94df38c52c2fc` 上通过
独立高风险审查、必要检查和远端新鲜准入，并由 native Monitor 接管。
[运行与技术记录](retained_reference_use_b01_781301/TECHNICAL_ACCEPTANCE.md)
发布于 `67275c9e684461b34148f7214e0c6ef1b7840ac3`。它完成且技术可信后，DM
直接执行已拨款的固定 BANK128 新 panel，不因 Generic 得分重新询问 Portfolio。
Generic 不完整则不运行 BANK；BANK 失败则保留 Generic 的可信事实而不给出差值。

五项 caps 保持 Generic2700s、BANK300s、native 合计3000s、support1200s、完整
invoked4200s。旧 BANK→Generic 决定及旧 Generic 无终点历史保持原样。
本次 F 没有续投、retry、额外 panel、新 BANK 训练或下一次咨询的预付额度。
FOLR 仍为 ACTIVE/MEDIUM；有限额度结束不自动停止方向。

## 2. 建议明确由 DM 连续完成的动作

| 动作 | DM 自主执行的范围及实际约束 |
| --- | --- |
| 对象与输入 | 在已接受机制、对象/梯级授权及剩余预算内选择普通 object-tier 选项；记录 card、预测、未筛选 seed、比较器、曝光和停止规则。冻结科学含义的变更按原决策梯级处理。 |
| 实现与工程修复 | 在所属 checkout/路径内实现、修复 runner、序列化、发布和必要 Transport helper；完成 L0、自查、比例合适的检查及适用的独立高风险审查，DM 作技术接受。无需 Root 重跑或签收后才继续。暂不创建 CM/Implementer。 |
| 发布与启动 | 按显式路径 commit/push，固定 source/command/input 摘要、节点、工作目录、输出和 handle；在真实节点逐次准入后 detached 启动。一次失败或换 SHA 不产生新的科学调用额度，接受不确定时先核对同一 handle。 |
| 监控与顺序执行 | 复用 DM 的原生 Monitor，收到直接 MONITOR_ADOPTED 后停止 DM 日常轮询；完整 Generic 验收后直接执行本次已授权 BANK128，随后交同一 Monitor。依赖由实际终点决定。 |
| Collection 与技术接受 | 收取 native 输出、计数、checkpoint、退出/计时/资源事实，核对 card 的主测量、完整调用和失败边界；必要且在已授权范围内的提取、格式和证据发布修复由 DM 完成。不得用修复名义补跑科学样本。 |
| 科学 intake 与范围内继续 | 区分技术合规与科学结果，应用原规则、保留反例/未知成本和条件性不确定性；选择已有 object-tier 授权覆盖的下一动作，发布英文 intake、中文 brief 和审计。已决定 F 无需再次咨询。 |
| Proper-node authoring/Transport | 真有新问题且范围固定时，DM 直接整理、发布、绑定并通过自己的 Transport 发送，读取完整答复并核对；不先索取 Root ACK。单一 Portfolio binding 的真实写者冲突仍需协调。 |
| 保留与清理 | collection 时列出精确 inventory，保留唯一证据，创建者清理自己的测试 scratch；已授权清理按指定路径执行并核验。共享/活跃 checkout 保持，Root 对 main 集成与留存完成情况作确认并接受回收。 |

这些动作沿用既有科学预算、fresh admission 和独立审查的实际要求。审查意见是
DM 接受工作的证据；不能把“Reviewer 已返回”或“Root 尚未整合”变成额外科学审批。
权限应和责任一并落在 DM，材料和结果直接返回 DM，无中转审批链。

## 3. 仍需 proper node 或跨方向协调的事项

| 实际变化 | 决定/协调者 | FOLR 示例 |
| --- | --- | --- |
| 新投资、追加/转移 cap、容量、优先级、生命周期、融合/分离或注册 | `portfolio:cross_direction`；方向 DM 著作及完整 intake，Root 执行跨方向映射 | F 之外再训练一个 Generic、增加 BANK panel、请求追加费用或 PARK 整个 FOLR。不得把已拨款 BANK128重新包装为投资请求。 |
| 新开/关闭对象族、recast、消费 C 后的下一对象、提升 C-BENCH | 原 `em:vap_folr_core:convergence`；冻结 C 前按原规则 Innovator | 改变已选定的 reference-use 科学问题或转入新的机制族；旧已归档用途题不重复发送。 |
| 实际共享写者、运行时/设备冲突、跨方向资源依赖、main/index 集成 | Root 与受影响 DM 协调执行；科学选择仍由 proper node 决定 | Portfolio binding 已有未决 Send，或共享运行时需要串行修改。方向本身继续独立可做的工作。 |
| 答复与 owner/spec 的具体冲突，或冻结含义需更改 | 返回原决定节点；显式规范更改走 AGENTS §4.7 | 不能以“完整答复”默许破坏固定 cap，也不能把 Transport 故障判成科学否定。 |

Root 可按已定优先级排程、整合和解除真实依赖；优先级和生命周期的新选择仍按
Portfolio 梯级。共享资源暂不可用不是 PARK。只有当前所有者的直接覆盖指令，或
完整合规 proper-node 决定，改变相应科学/投资边界。接受效果不确定时停止重复
Send/launch，继续同一请求或 handle 的事实核对。

## 4. 最小审计与主动回报

1. **已有 card/执行记录是单一事实入口。** 保留问题、来源、固定 SHA/输入、
   比较器/RNG、曝光/caps、handle、准入、Monitor 归属和终态证据。Git 发布是
   可恢复边界；无需新增 ACK 字段、审批表或逐工具操作日志。
2. **真正的自动决策写一行既有 audit。** 列选项、推荐、实际选择、tier、
   provenance、证据和 owner flag；普通操作不重复建立决策。P1/P2 仅用于已有
   owner-item 规则指定的新 card、方向选择、重要异议、close call、第二次 recast
   和 Portfolio 项，owner 异步介入不成为等待条件。
3. **结果在一个 intake 中闭合。** 引用原 reading rule，记录独立单位/计数、
   技术接受与科学上限、支持和反证、预测核对、未知/失败工作及决定的下一步。
   有效结果附六标题、600字以内中文 brief；不完整结果保留可信窄事实，不能补造
   主比较。SHA 和明细留在英文记录。
4. **每个变化主动回报一次。** bounded assignment 完成、实质冲突/阻塞、进入
   ACTIVE-idle 时，DM 直接发原生 action message：assignment、状态、证据/commit、
   下一动作或具体依赖。受理/归属有实质变化的启动可在同一交接中报告。无需状态
   中转或未变化 keepalive；无独立工作时 native long wait，终态到来立即处理。
5. **Root 审计只列未决项。** 此刻 FOLR 未决的是 Generic 的终态和技术接受，随后
   才能运行 BANK128；不存在 F 再审批。Root 整合已发布结果和实际依赖，保持
   ACTIVE 方向链的责任归属；DM 在本次额度耗尽后按现有授权形成下一有界问题。

## 5. 建议采纳方式与本稿实际执行

建议 Root 将以上连续执行边界作为研究管理员默认行为，并在派工和回报中只列
真实的新决定或依赖。无需为本次 Generic→BANK 链增加一次流程批准。若要进一步
授予跨方向资金或治理变更权限，应明确写出范围并走现有授权途径；本建议不推定
这些新权限已经生效。

本稿仅发布建议及一条技术审计，未执行建议性规范更改、未新增请求、未移动
任何 cap/seed/比较器。当前科学 card、F 决定和运行中的 Generic 保持原绑定。
下一步仍是接收 Monitor 终态、DM collection/技术接受及依赖满足后的 BANK128。

依据：AGENTS §§2–6；[ROOT_OPERATIONS.md](../../../project/ROOT_OPERATIONS.md)
Current control、Complete deliverables、Execution inputs、Integration and cleanup；
[ENGINEERING_SCOPE_SPEC.md](../../../project/ENGINEERING_SCOPE_SPEC.md) §7；
[当前 science card](FOLR_RETAINED_REFERENCE_USE_B01_SCIENCE_CARD_20260913.md)。
