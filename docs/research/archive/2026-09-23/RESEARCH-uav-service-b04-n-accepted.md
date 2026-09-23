# Superseded service-risk B04 standing and plan, 2026-09-23

Retired from RESEARCH.md at main `2c16014b9635ed01f03214bcd859fa30328425cb` when N was fully accepted and the fixed R operation was admitted. Historical statements below are preserved; current standing is in RESEARCH.md. This retirement does not alter the fixed comparison, lead or owner controls.

## Previous standing

| `uav_service_auxiliary` | 在 S7 完整共同学习中，怎样把服务改善转成包含返航风险的净收益？ | exploring | Codex DM (independent session) | 文献第 1 项；直接 DM task `01a0c9af-d5cd-7d70-b5e8-9db2c598ad4e`，host `local`，`gpt-6-astra` / `max`；checkout `/home/fires/.codex/worktrees/d319/hmasd-wsl`，branch `codex/uav-service-predictive-control`。固定 B03 D/S/G×两块六 fits、两次共同端点回放全部完整验收，source `73be55261b9f5e8f8fe26fdec6558b87ad088fcb`。两块最终 S−D J **+24.585407 / −16.825601**，G−D **+117.896434 / −24.945921**，S−G **−93.311027 / +8.120320**；收益均未复现，G服务增加但成本取舍转坏，保留负尾部。共同回放中G首块两类MSE最高、第二块最低，均不能代替原生用途。按已覆盖该分支的完整Pro建议关闭当前配方，0追加/确认，无旧操作待收。B04 已前瞻固定并通过独立审查与实际4070节点8项检查：新原生N与真实返航成本加强R，训练成本系数2/4，最终均按原生系数2评价；2 fits/360k train/192k eval上限。N已原生准入运行并登记观察，R为固定第二臂；尚无B04科学结果。[前瞻与L0](candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b04-prospective-direct-service-and-return-risk-learning)；[N原生运行](candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b04-n-admitted-after-native-cuda-checks)。方向与lead不变。6 fits累计769.038846 runner min，零更新共同回放另1.693106 min。[完整结果与判断](candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b03-second-common-replay-accepted-and-current-recipe-closed)；[G2验收](candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b03-second-block-g-accepted-and-fixed-common-replay-bound)。 |

## Previous plan

| **DM3：服务收益与风险控制** | G 的服务提升在 S7 两块都出现，返航约束成本改善没有复现；下一问题是怎样把服务转成完整用途。 | **B04已固定并开始**：原生N与训练时额外扣除 `2×真实返航约束成本` 的R，共同新种子914021；两层原生回报/优势均变化，原生评价系数仍为2。每臂180k，**2 fits / 360k train / 192k eval上限**；开发937001–8在0/10/20/30，最终938001–32只读更新30。独立审查和实际CUDA检查已通过，N原生运行、R为固定第二臂。看原生J、QoS、返航成本、电量低尾与逐世界损失；不选最佳checkpoint或调系数。原分项critic只保留为有理由时的替代。[前瞻与运行](candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b04-n-admitted-after-native-cuda-checks)。 |
