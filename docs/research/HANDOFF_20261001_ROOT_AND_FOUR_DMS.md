# 本轮研究交接：Root 与四位 DM（2026-10-01）

> **状态：整理中，尚未完成交接。** 当前已接受的研究和已开始的选题评估继续完成，
> 不启动下一轮实验。最终状态由 Root 在四位 DM 完成各自部分后更新。

<!-- ROOT_OVERVIEW_BEGIN -->
## Root 总览

Owner 本次要求：完成这一轮，不打断正在进行的工作，然后写一个独立 handoff；
Root 负责总览，四位 DM 各自撰写负责部分，方便后续继续。本文件按该明确请求建立，
不替代原始 NOTES、运行证据或 RESEARCH 当前状态。

本轮边界是完成已接受的 S7 C/H/F 比较及三份已经开始的后续选题评估。
三个较早完成的研究已经发表、独立判读和清理。后续候选尚未选定；
即使建议可行，也不据此启动下一轮。交接完成后，本 Root 及这四位 DM 停在交接边界，
等待 owner 明确继续。状态询问、阅读 handoff 或工作流修改本身不恢复研究。
Claude 的独立授权、FSD/PPC 暂停、G33 冻结和 Milan 数据依赖保持原范围。

### 四位 DM 与本轮责任

| DM | 本轮结果性研究 | 当前交接事项 |
| --- | --- | --- |
| /root/dm_fleet_transmission | S7 C/H/F：预测信息是否改善完整服务控制 | 原操作继续至完整读出、独立判读、发表和清理 |
| /root/dm_fleet_adaptation | B10：联合本地运动与发射控制学习 | 已关闭；完成静默与下一次观测问题的资料及成本评估 |
| /root/dm_parent_adaptation | RF information B01：付费信息包与普通先验控制 | 已关闭；完成整体 U32_FULL/P_PRIOR 候选的独立评估 |
| /root/dm_user_waiting | RF uncertainty B01：U32 与同测量信息的 P | 已关闭；完成策略参数搜索与等投入普通校准候选的资料及成本评估 |

四个现有会话均未被 owner 归档。后续若仍未归档，可按 RESEARCH 路由复用；
若 owner 已归档完成会话，创建新的 DM 并继承其已发表证据，不恢复归档会话。
Oracle、Scout 和 Reviewer 是辅助工作，不计为第五个 DM。

### 已经改变的判断

- **U32 有条件的目标收益成立，等待代价必须同时保留。** 对 P 的 payload-J 增量
  为 +.007529588，32 世界中 26 正、6 负；服务数量增量仍未确定。平均年龄、
  最差用户年龄和最长未服务间隔均恶化，存在目标收益为正但连续排除长达
  129/127 tick 的闭合间隔。该结果不证明共同测量包值得购买。
- **普通 P 的 FULL 信息包没有挣回完整成本。** 对 P_PRIOR 的 payload-J 为
  −.015929915，32 世界均为负，其中一例近乎持平。部分等待改善与严重反例并存；
  不能将这一效应与另一面板的 U32−P 相加得到 U32_FULL−P_PRIOR。
- **B10 两个联合学习实例均未形成超出强参照的增量。** 对实际 INIT90 的 J
  为 −.0229865/−.0261492，并低于 P0、Bstar、Hdirect 的所列强组合。训练真实激活，
  保留既有 P0/HIDDEN/普通控制能力以及 CJ 的即时正例；不据此断言一般不可学习，
  也未识别各次失败的共同原因。
- **S7 的判断待完整结果。** 部分进度不作科学结论。由负责 DM 在下文写入完整结果
  和独立判读后，Root 再整合本项。

三个已完成研究的被清理目标合计释放 **6,550,663,168 allocated bytes（约 6.10 GiB）**；
这是各自实际清理目标的净下降，不能称为整台机器的空闲空间变化。S7 本轮清理尚未计入。
各研究保留必要的单份正面、负面和失败证据，详见各 DM 部分。

### 下一轮候选和实际审阅状态

当前只有三个资料评估中的候选问题，没有新实验被选定：

1. RF 完整 U32_FULL 对 P_PRIOR 包比较，补足两项既有比较不能相减回答的用途问题。
2. 本地静默的即时收益与下一次被遮蔽观测之间，合法保留信息或不同观测合同是否有用。
3. 完整回合参数搜索是否能使小幅上下文策略发展超过等投入全局校准及已有强参照。

最终建议、完整成本、是否建议购买及反对理由由各负责 DM 在对应部分保留。
候选名称和空余算力均不构成执行授权。

模型来源已作纠正：RF 早期资料建议来自原 age_control_interface Scout，
实际为 Luna/medium；先前把它称为 Astra Max Oracle 是 Root 的错误。
原建议和来源纠正已分别保存于
[RF 原始建议与更正](candidates/uav_radio_information_cost/NOTES.md#b02-original-opportunity-advice)。
新的 /root/oracle_rf_integrated 已核对实际运行是 Astra/max，正在进行独立科学评估；
另两位 Oracle 实际运行同样已核对为 Astra/max。旧建议保留为资料，不替代这次独立评估。

### 继续时先恢复什么

以 [RESEARCH 当前状态](RESEARCH.md) 和各 DM 下列精确证据为入口。工作区是
/home/fires/hmasd-wsl 的 main；节点和解释器取自 .codex/hmasd-compute.toml。
保持原始输入和操作身份，已结束的 worker、reader 和观察句柄不重启。
新研究须在 owner 明确继续后，重新作科学投入选择、前瞻声明、精确输入发表和实际节点准入。

各 DM 负责其方向目录及 NOTES；共享 Git 索引/提交仍串行且只提交明确拥有的路径。
恢复时检查当前他方改动，不从本文件复制旧版 RESEARCH 覆盖共享文件。
本文件各 DM 部分由本人撰写；Root 在全部完成后更新总览和交接状态。

**Root 最后核对：待本轮全部结果、三份完整建议、四份 DM 交接和终态清理齐备后填写。**
<!-- ROOT_OVERVIEW_END -->

<!-- DM_FLEET_TRANSMISSION_BEGIN -->
## DM：机群发射控制与 S7 预测用途

待 /root/dm_fleet_transmission 完成当前研究后本人填写。
<!-- DM_FLEET_TRANSMISSION_END -->

<!-- DM_FLEET_ADAPTATION_BEGIN -->
## DM：机群策略发展与本地联合控制

待 /root/dm_fleet_adaptation 完成当前资料评估后本人填写。
<!-- DM_FLEET_ADAPTATION_END -->

<!-- DM_PARENT_ADAPTATION_BEGIN -->
## DM：父策略发展与无线信息成本

待 /root/dm_parent_adaptation 完成当前资料评估后本人填写。
<!-- DM_PARENT_ADAPTATION_END -->

<!-- DM_USER_WAITING_BEGIN -->
## DM：用户等待、无线不确定性与后续策略发展候选

待 /root/dm_user_waiting 完成当前资料评估后本人填写。
<!-- DM_USER_WAITING_END -->
