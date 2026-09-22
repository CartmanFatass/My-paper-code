# Retired UAV-service running standing and replication plan — 2026-09-22

Source revision: `a48ef628a40ed1200c42140dd2d6e42c8979faa9`.
This preserves the UAV-service standing and plan superseded by the complete four-fit
comparison and bounded keep/revise decision. The final accepted operation has been collected,
verified and read; no unresolved operation or Pro target is moved. The full question, Pro
answer, prospective bindings and interpretations remain in the append-only direction NOTES.
Other directions retain their own current records. Evidence links below are pinned to the
source revision.

[Complete source index](https://github.com/CartmanFatass/My-paper-code/blob/a48ef628a40ed1200c42140dd2d6e42c8979faa9/docs/research/RESEARCH.md)

## Previous UAV-service standing

| Direction | Question | State | Lead runtime | Standing and next step |
| --- | --- | --- | --- | --- |
| `uav_service_auxiliary` | 未来事实端到端服务监督能否帮助 HMASD 学会接入、回传与能源约束下的协作？ | exploring | Codex DM (independent session) | 直接 DM task `01a0c6f0-31e1-7510-bee7-4f0f8b62d821`，host `local`；checkout `/home/fires/.codex/worktrees/a335/hmasd-wsl`，branch `codex/uav-service-auxiliary`。S7-S2 v3/reward v2/arm C，固定 k=10/N=8；B01 单训练对完整核验，固定终点 joint−detach J 差 +159.537455、QoS 差 +0.038796、返航约束代价差 -0.034002；2 fits 合计 297.90 runner min，仍为探索观察。完整 Pro 阅读后选择恰好一对科学配方不变的 B02，seed 910137，种子入口修正经独立审查，输入 `30401722b`。B02 detach 已完整核验 180k transitions，终点 J=-670.393733、QoS=0.140231、共同事实 MSE=0.00415098；第 20 次更新后 J 明显回落。训练仅 1 个充电 UAV 时间步，评估无充电／切断／耗尽事件。joint 已在 `wsl_4070` 准入运行，事实哈希与初始模型指纹和 detach 一致，配对判断待完整终点。4 计划 fits 全已启动：3 完成、1 运行；已完成 runner wall 合计 414.28 min，另有 15/16 秒训练前拒绝。无自动第三对或已选确认，G33 冻结。[B02 核验与解释](https://github.com/CartmanFatass/My-paper-code/blob/a48ef628a40ed1200c42140dd2d6e42c8979faa9/docs/research/candidates/uav_service_auxiliary/NOTES.md#b02-detach-complete-and-original-joint-remains--2026-09-22-0359-pdt)；[joint 启动证据](https://github.com/CartmanFatass/My-paper-code/blob/a48ef628a40ed1200c42140dd2d6e42c8979faa9/runs/uav_service_auxiliary/b02_joint_910137_a01/launch-manifest.json)。 |

## Superseded UAV-service replication plan

| 研究问题 | 当前优先次序与第一个比较 | 证据如何约束投入 |
| --- | --- | --- |
| **UAV 端到端服务预测** | S7 首对已完成；Pro 后选择的唯一 B02 复现对（seed 910137）中，detach 已完整核验，joint 正在运行。 | 固定 k/N、W10 事实 QoS 头 detach 对进入 actor/GRU 的梯度；B02 detach 后段 J 回落且 MSE 降低，继续按预定 rollout-30 原生终点读完整两臂，单独报告两对，不能按 MSE 或早期 checkpoint 选结果。复现失败或不足以改变投资默认结束当前配方支出，无自动第三对或立即确认；保留成本与事件曝光边界，G33 冻结。[固定判读与核验](https://github.com/CartmanFatass/My-paper-code/blob/a48ef628a40ed1200c42140dd2d6e42c8979faa9/docs/research/candidates/uav_service_auxiliary/NOTES.md#b02-detach-complete-and-original-joint-remains--2026-09-22-0359-pdt)。 |
