# metric_ground_transport_allocation · native_ground_geometry_b01 · P75 · 2026-09-09

## 问题

在固定五 UAV 原生速度控制中，保留全部同样输入和原生奖励的 typed relation-residual (`REL`)，是否比等分支参数量的同信息 dense residual (`DENSE`) 带来更高的完整原生回报？

## 结果一句话

技术 collection 完整、两次提交均 exit 0；两主种子的 REL−DENSE 分别为 `-0.04468252516448091` 和 `-0.003243683445650989`，聚合 `Delta=-0.02396310430506595`，低于 `-0.01`，按冻结规则为 **`REL_ADVERSE`**。

## 结果边界

这是该 REL package 在本原生任务和固定训练暴露下相对 DENSE 的完整不利 B/EXPLORE 观察。它不证明 DENSE 的稳定总体优势、度量因果、等价性、收敛、部署价值、地面基站价值或任何仓库/UAV 效果。H 只是固定零速度诊断，不能证明 learned comparator 的一般能力。

## 成本与证据

两次 native process wall 为 `353.71 s`、`368.12 s`，离线 aggregate 为 `0.81 s`；合计 `722.64 s`，研究关键路径为 `899.395664691925 s`。两次 admission 的 physical/effective 可用内存均通过 4 GiB；完整 counts、checkpoint、episode/rollout、supervisor 和文件哈希保存在 P75 技术 collection JSON 中。aggregate CPU、峰值 RSS 与 activation memory 未测量。

## 预测核对

原卡预测为聚合差异较小或落在 `0.01` 关注尺度内；实际结果在不利方向越过该尺度。无人值守下 owner prediction slot 标记为 `not taken`，不虚构 owner 回复或预测分数。

## 下一步

P75 allocation 已消耗。建议结束本次 allocation，不追加相同 REL/DENSE pair、seed、重试、调参、额外评估、profiler 或 UAV 验证。若方向要继续，需由 `em:metric_ground_transport_allocation:convergence` 决定是否暂存/关闭该 actor family，或另行提出保持原生 reward/action/history 与同信息 competent comparator 的实质不同几何问题；本 intake 不作方向层选择，也不授权新运行或 Pro Send。
