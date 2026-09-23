# Retired DM3 preparation text — 2026-09-23

Superseded owned standing and plan from main `9c732a4d0faa5be84ac62240b691dba81acebad5`; current state is in RESEARCH.md. This archive changes no other direction or control.

| `uav_service_auxiliary` | 面向控制用途的预测小模块：事实预测监督与任务后果监督怎样影响 S7 完整服务收益？ | exploring | Codex DM (independent session) | 文献第 1 项；直接 DM task `01a0c9af-d5cd-7d70-b5e8-9db2c598ad4e`，host `local`，`gpt-6-astra` / `max`；checkout `/home/fires/.codex/worktrees/d319/hmasd-wsl`，branch `codex/uav-service-predictive-control`。固定 B03 D/S/G×两块六 fits、两次共同端点回放全部完整验收，source `73be55261b9f5e8f8fe26fdec6558b87ad088fcb`。两块最终 S−D J **+24.585407 / −16.825601**，G−D **+117.896434 / −24.945921**，S−G **−93.311027 / +8.120320**；收益均未复现，G服务增加但成本取舍转坏，保留负尾部。共同回放中G首块两类MSE最高、第二块最低，均不能代替原生用途。按已覆盖该分支的完整Pro建议关闭当前配方，0追加/确认，无旧操作待收。Root 将本 DM 的新准备聚焦于直接服务—风险学习，原 checkout 已从已发表分支恢复，原任务已解除归档并接受接续请求，native active；新批次的定稿与准入尚未确认，见[现行计划](#current-research-plan)。方向与lead不变。6 fits累计769.038846 runner min，零更新共同回放另1.693106 min。[完整结果与判断](candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b03-second-common-replay-accepted-and-current-recipe-closed)；[G2验收](candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b03-second-block-g-accepted-and-fixed-common-replay-bound)。 |

| **DM3：服务收益与风险控制** | G 的服务提升在 S7 两块都出现，返航约束成本改善没有复现；下一问题是怎样把服务转成完整用途。 | **先定稿直接服务—风险学习比较**：普通原生 actor 更新，对比以预定系数加强真实返航/约束成本惩罚，保持其他信息、动作、曝光及原生评价目标。明确这是训练目标干预。初步 **2 fits、每臂180k**，权重尺度、接线、最终世界与完整成本尚需前瞻固定；看原生 J、QoS、返航成本、电量低尾及世界损失。原分项 critic 候选保留为有理由时的替代，不同时铺开两包。 |

B03 完整证据保留；原任务已解除归档并收到同一接续请求，新 turn `01a0ce7a-7b15-7880-aed4-3cfcb7fed3b5` 为 inProgress。
