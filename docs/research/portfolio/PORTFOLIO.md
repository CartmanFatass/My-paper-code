# 科研 Portfolio 报告

> OWNER_DIRECT 2026-09-14：各方向完成手中任务与实验后暂停并写handoff；不停止已接受的运行/审查，不启动后继实验或补位。[当前指令](decisions/2026-09-14-owner-pause-after-inflight.md)。三个席位保持，科学CONTINUE等既有处置与这次运行暂停分别记录。


当前目标为三个占用与预留席位。Portfolio 按 [当前决策协议](../../project/PORTFOLIO_DECISION_PROTOCOL.md)
作方向层面的最终综合判断；DM 负责创新、实验、实现、证据报告和执行，普通实验不逐项申请批准。
中央 Clerk 已退休，DM 平等协调，Root 是用户入口。以下是已发布证据和当前登记的摘要，
实时席位、实际 producer 与同会话请求顺序以 [共享登记表](../../../.codex/hmasd-dm-sessions.toml) 为准。

## 当前方向与空缺

| 方向 | 已知科学位置 | 当前工作与席位 |
| --- | --- | --- |
| [RCLE](../candidates/roster_consistent_latent_exploration/DIRECTION.md) | B13真实学习与nearest收益保留，sampled对greedy−0.019784；modal512行已测结局相同、恢复利益/损害和B11缺失保留。完整151行Portfolio判断接受新独立实例仍有价值，当前选择可逆PARK。 | 已应用PARK并释放1席；不CLOSE/RECAST，不新增fit。[完整裁决与回应](../candidates/roster_consistent_latent_exploration/pro_packets/20260914_post_b13_portfolio_direction/INTAKE.md)、[PARK知识与原始资产](../candidates/roster_consistent_latent_exploration/PARK.md)已保全。原DM已完成本次唯一空缺接续及直接交接，无RCLE科学producer；源码和558文件恢复已保全，历史四个被拒删除路径作为清理例外保留。 |
| [ACVC](../candidates/acvc/DIRECTION.md) | 六个原始fixed1024完整程序的F-C均值+.096377354920J、区间[.074826981257,.117927728584]；F-dwell+.064088940259J、[.035375804426,.092802076092]，两下界均>.01。df5两项97.5%边际区间的同时覆盖仅在预设iid-normal模型下成立；实际神经训练校准未建立，全部反证保留。 | 占用1席，科学CONTINUE / MEDIUM / recasts2；当前工作已完成并按所有者指令暂停。[最终handoff](../candidates/acvc/ACVC_OWNER_PAUSE_HANDOFF_20260914.md)发布于cccd8068f9fa7398591b4c76e4e6c3df00b5f893。六原始单元/7296回合/12288更新、完整74行科学审查和144行Portfolio决定均已接收并逐项回应，已释放完成的对话。所选未来1024/4096 B未建卡、未抽种子、未写源码、未启动。原生1733.09s，完整支持/provider/agent费用UNKNOWN；原始档案保全，远端清理完成，本地被策略拒绝的测试清理保留。 |
| [MGTAP](../candidates/metric_ground_transport_allocation/DIRECTION.md) | 固定1e-4新8253配对完成：COND−DENSE−0.025924927546066238 J，COND_ADVERSE，条件世界SE0.0027978641，2正/30负；前次8252正向及更早混合结果保留。这次未再出现有用正向，不是普遍不可复现、稳定劣势或事前两种子确认。 | 占用1席，科学CONTINUE/DENSE默认保留；当前工作全部收尾，现已按所有者指令暂停。[最终handoff](../candidates/metric_ground_transport_allocation/MGTAP_OWNER_PAUSE_HANDOFF_20260914.md)发布于fa7edbb339c6b9d9d33b22c93dd2ae68a58d1240。完整181行独立审查494dbefe0已读取并逐项回应，未见需改判或补跑缺陷；收窄复现措辞，明确机制解释不是新增普通B的门槛。实际2拟合/178.86s/exit0，证据及checkpoint完整保留，两轮远端目录已核验回收，无native/monitor/provider遗留。后续取舍仅保留供明确恢复时讨论；不PARK、不释放席位、不新增实验/咨询。 |
| [FOLR](../candidates/vap_folr_core/DIRECTION.md) | A-G增强B01完整：G−0.966484375，A4.329921875，d=+5.29640625，AUGMENTED_ABOVE_MEI；DM低置信度Generic胜预测错误。每臂1次训练/128条件评价，不声称稳定排名或持久记忆因果收益；旧替换BANK B02/B03负结果分别保留。 | 占用1席，科学CONTINUE/MEDIUM保持，依所有者指示收尾后暂停。两臂5000/4969/128均完成并已保全/回收；native3975.48s、CPU3972.96s、study17377s，完整支持成本未知。只剩当前结果独立复核与实质回应、最终[交接](../candidates/vap_folr_core/HANDOFF_20260914_OWNER_PAUSE.md)。同一复核已于20:46:33UTC一次接收，原Transport正在观察完整答复；此前队列遗漏已解决；无后继实验、空缺或新方向。 |

实际为3占用、0预留、0空缺。ACVC已完成当前对象及完整Portfolio回应并释放对话，现已暂停；MGTAP也已完成当前对象及完整审查并暂停，FOLR继续收尾其在手工作。所有后继实验和补位依直接所有者暂停指令停止新增。
第四方向限制的历史效力保留；当前额外适用所有者暂停指令：仅收尾在手工作，不新增研究或补位。旧报告的 UCOPE/LCAC/ACVC 工作集和
RCLE/MGTAP/FOLR 归档表已经过期，不能用来判断现在是否“开始后直接结束”。

RCLE B13 完整审查固定于d45d4bc6ea2012b93d1d044402268520be5eea9a，DM 实质回应和后续方向取舍报告见
afb647d0ddf7522ad0e0e99162a54403ede21c43；此前 E01 审查、前次 CONTINUE 理由及全部反证保留。MGTAP 当前科学卡/重入依据见
3594eafe28ed91b2558fcc064e46ea714edd2e1c；FOLR 的完整裁决、修正及实际应用见
4776103de4f55beaee610c52506112651bfaed04。这里引用已有 DM 结论，不新增跨方向的数值排序。

## PARK及已归档方向的知识入口

| 方向 | 保留知识与当前限制 |
| --- | --- |
| [RCLE](../candidates/roster_consistent_latent_exploration/PARK.md) | 新Portfolio可逆PARK已应用，B10/B12固定先验、B11缺失、E01旧面板、B13新法则分开保留；完整原始归档、恢复向量和新实例复开反方案保全。原DM仍执行已登记的空缺交接，不占科研席位。 |
| [DISH](../candidates/degraded_incumbent_shadow_handover/PARK.md) | 保留 B09 −35.25、REPLACE 与 BYPASS 边界；旧 Portfolio 补位建议未应用；前次裁决选择继续 FOLR；本次 RCLE 空缺已由新完整裁决选给 ACVC，旧 DISH 建议不应用。 |
| [UCOPE](../candidates/ucope/PARK.md) | 保留 reactive renewal 的结果、反证和重新研究条件；当前未占用席位。 |
| [LCAC](../candidates/learned_counterfactual_agent_credit/PARK.md) | 保留 B03 负结果及基线/学习证据；当前未占用席位。 |
| [ACVC](../candidates/acvc/PARK.md) | 原PARK知识与全部反证保留；后续复开并完成六程序C01，最新完整Portfolio仍CONTINUE，当前依所有者指令运行暂停；未再次PARK、未释放席位。 |

其他方向见 [Research map](../RESEARCH_MAP.md)。历史决定保留原始出处；当前 owner 挑战和
Portfolio 的新决定前瞻应用，不擅自重写结果或批量重启旧方向。

## 当前交接与成本口径

ACVC五个历史clustered开发学习程序native1114.44s，六个新fixed1024 C01单元native1733.09s，已知子集合计2847.53s。各科学对象/暴露/快照保持独立，费用相加不构成统计合并。C01本身6144训练/1152评估/12288更新/1867776team ticks，CPU1732.73s。完整支持、provider、agent、维护及方向生命周期成本UNKNOWN。

FOLR 请求2026-09-14-folr-portfolio-direction-reconciliation-01已完成并应用 CONTINUE；
完整答复保全于4776103de4f55beaee610c52506112651bfaed04。RCLE 请求
2026-09-14-rcle-e01-direction-decision-01完整答复已按一次 Send 归档，20,895字节/SHA256 7c7476fca152aec673c7ff0974ae182c0ef30c091e230a4ba7039ac71f06a416；CONTINUE 于5f4abd6f应用，B13随后实际完成，完整证据见c58ec2fb4。此前 RCLE CONTINUE 请求已结清并执行为B13；后续完整方向裁决现已可逆PARK并形成一个真实空缺，当前补位完整裁决已落实为原ACVC DM的实际B03对象工作，同一个预留已转为占用；Portfolio会话已释放，并已向下一作者FOLR直接交付本次完整应用与全局事实。
旧6aa7836e会话答复已由552f0dce7904e35206b8e32f9180ab85aee822ad保全，其 DISH 建议未应用。
新的 Portfolio 决定须基于实际读取的固定权限、全局上下文、完整结果/反证/审查和 DM 回应。

support600s 与普通 wall 规划是允许误差的参考，不是自动停止、Send 或升级条件。
实际 owner/平台资源边界和冻结科学端点仍适用；未知费用保留 UNKNOWN，不变成0或 PARK 理由。
Heartbeat 登记仍为 MISSING，不能声称定时恢复已运行。当前依赖真实 producer 和直接消息交接。
