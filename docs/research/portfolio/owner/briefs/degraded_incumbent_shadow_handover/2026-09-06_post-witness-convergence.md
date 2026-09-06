# DISH 见证后 Convergence 决定简报 — 2026-09-06

**一句话**：Pro（PRO_FINAL）继续 RETAIN/COPY/SHADOW 议程，预测包支线保持结束；本轮只开一个新的 B/EXPLORE：**DISH-CONTROL-LOW-LR-B04**——继承的 CONTROL 学习器，AdamW 学习率 3e-4 对 3e-5，新配对种子 89，每臂 16 次更新，另含同一种子的四行零更新参考（raw 接口）。不冻结 Welford，不减 epoch，不重开包，不停车，不 RECAST。

## 理由

见证把此前未测的前提变成了有界事实：seed 73 的最终 CONTROL 比它自己的零更新控制器少 245.75 平均服务 tick。现在值得直接问“更小的优化器步长能否在同样交互与更新次数下改善原生服务”。**这个事实提供动机，但没有诊断学习率过大；选的是一个性能假设，不是已定位原因的修复。** 归一化、参数移动、PPO 都不能被说成损失的唯一来源。

## Pro 对 DM 的更正

- 两个零更新视图相同，不证明从未提出 prepare/commit，也不证明两视图内部动作历史相同（summary 没有逐 tick 提案计数）；“接口无处作用”只能留作推断，不为它买复现，也不据此认为 raw 与 sigmoid 在学习时可互换。
- DM 首选的“冻结 Welford”不选：它干预一个部件但不识别历史损失的原因，会同时改变有效输入、饱和、动作、采样数据与梯度；不是必做的前置诊断。减到一个 epoch 会把优化步从 512 减到 128，为保留更新次数不选。
- 不先买单独的“第二个 CONTROL 种子”：新 B 的 CONTROL 臂加它自己的零更新参考已经能报告前后损失是否重复。

## 对象要点

- 两臂只差学习率（3e-5 作用于 AdamW 的**全部**原参数组，含其解耦权重衰减的缩放；是学习率超参数的总效果）；其余目标、裁剪、采样、PPO/replay、标签/mask、归一化规则全同。
- 种子 89：master = sha256("DISH-CONTROL-LOW-LR-B04/seed/89")；两臂同一初始参数与初始空 Welford；四个评估 reset 按继承坐标法则为 seed 89 导出并记录（不是 seed 73 的相位）。
- 主量 Delta_LR = 四行 (LOW_LR − CONTROL) 均值；附属 D_CONTROL,new 与 D_LOW_LR,new 相对本种子初始四行；尺度 +24；七行读法。任何结果都不自动授权另一个 LR、冻结 Welford、重开包或改 Portfolio。
- 成本：每臂 ≤ 1,800 s，两臂合计 ≤ 3,600 s（含共享初始化、四行参考、聚焦检查、构建/加载与发布）；不采用 DM 的约 410 s 为投影；不买校准实验。
- 验收要点：所选学习率在每次更新都真正作用于全部参数组，checkpoint/状态恢复或 trainer 重建不得把 LOW_LR 重设回 3e-4；这是 CM 目标的核心检查（r06 代码有三处写死 lr=3e-4，薄入口须在每个构造/恢复点设定，且不改 r06 源码）。

## 执行

DM 取学习率通路的只读代码图后冻结卡片 `DISH_CONTROL_LOW_LR_B04_SCIENCE_CARD_20260906.md` 与 CM 目标；Grok Build 实现薄入口，枢纽审阅，operator 在 wsl_4070 启动。详情：`docs/research/candidates/degraded_incumbent_shadow_handover/DISH_POST_WITNESS_CONVERGENCE_INTAKE_20260906.md`；完整答复：`pro_packets/20260906_post_witness_convergence/archive/RESPONSE.md`（提交 27730bf75）。
