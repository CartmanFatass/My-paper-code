# RCLE TBCFV 首个 B Innovator 决定简报 — 2026-09-06

**一句话**：Pro（PRO_FINAL，本节点首次绑定）在冻结的 TBCFV 宿主上开启第一个有界 B/EXPLORE 配对 `RCLE-TBCFV-B01-PERSIST-VS-FLEX`：C1P1-COMMON-PERSISTENT 对 FLEX-REKEY，一个配对训练种子，每臂 200 次更新 × 64 个训练 episode，只用最终 checkpoint，held-out 每格 256 个 episode。每臂硬上限 2,700 s，整对含构建、测量、参考行与发布合计 5,400 s。

## 理由

含括关系（FLEX 把两个更新头归零即得处理策略）从未在有限学习预算下被问过恢复性能；一次真正可比的学习观察比先补上参考、调优通用基线或机制解释更直接地决定下一小笔投入。最强反对意见不是旧结果的负号，而是新比较可能几乎没学到东西：固定步长 0.0005 × 200 次更新的路径长度上界只有 0.1；两臂都不改善时低曝光、优化困难和恢复指标饱和都是活解释。

## 对象要点

- 主测量：恢复时间 τ（边界后连续四 tick 无未服务的首个偏移，否则记 40），**只在 ACTIVE_CONTINUATION 的 8→12 与 12→8 两格上等权比较**；其余六格与八格均值作伴随描述。伴随 U（边界后 40 tick 平均未服务）与学习曲线（每次更新的 Y 汇总，全部 200 点保留，每 25 次展示）。
- MEI：τ 4 个 tick、U 绝对 0.05，用于解释而非显著性门槛；不套用原 C 的 0.02 非劣界或 72 尾规则。
- 训练律不变：stopped-gradient score 项、actor log-prob、64 episode 联合 loss、每 block 一次 backward、固定步长 plain SGD、八个 per-cell baseline 0.95/0.05；没有 Adam 和回报归一化，也不新增。
- 附一行零学习器参考 INDEPENDENT-NEAREST（每次 claim 选最近信标，并列取小编号），同一 2,048 个 held-out scenario，只评估一次；用于分辨「两臂都饱和」与「相对差小」。
- CM 准备：在 wsl_4070 首次 native 构建；一次 ≤300 s 的零学习器可执行性/成本测量（≤8 格 × 一个 8-episode batch，独立准备样本）；写一个薄的两臂单种子适配入口，复用 host/model/package/loss/update，不走旧 20-block 全景与证书链。
- 读法五行：Δτ ≈ +4 且 U 无 MEI 级损失 → 值得一个独立种子；Δτ ≈ −4 或 U 实质损失 → 降低支持，清楚的反向结果也可复现一次；带内 → 不主张差异；路径相反/τ-U 交易/几乎全 40 → 混合；主比较受损 → 只留窄事实。

## Pro 更正的三条 DM 表述

「other-agent partial observability」不是本宿主的绑定结构（应为成员数变化后的协调恢复）；「各自优化器/归一化状态」应落实为实际存在的 baseline 状态；脚本参考「秒级成本」无实测依据、不采用。

## 执行

DM 冻结 B01 卡与 CM 目标（Grok 实现薄入口与构建，枢纽审阅），operator 在 wsl_4070 先做构建与可执行性测量，再依次启动两臂与参考行。详情：`docs/research/candidates/roster_consistent_latent_exploration/RCLE_TBCFV_FIRST_B_INNOVATOR_INTAKE_20260906.md`；原文 `pro_packets/20260906_tbcfv_first_b_innovator_r02/archive/RESPONSE.md`（提交 35e3b7b1）。
