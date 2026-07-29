# 第 38 轮：G49 duplicated-immediate 单通道折叠

## 运行边界

- 环境：toy env，`ContinuousRosterToyBatch_CPU_CPP`，不是 UAV。
- formal source commit：`8ecb01fd3ac0debf1b792e4e51293e07974d633b`。
- 对齐实现：`9edddc845d88191bbfbd6c2ec779551edbbcb78a`。
- 对齐阶段：`b56288597c6c91f784fb5f0fcc36ec5ef92de452`。
- formal run：`logs/formal_continuous_roster_native_six_g31_duplicated_immediate_single_channel_collapse_g49_cpu_20260729_8ecb01f_r1`。

## 机械结果

同源 nonformal preflight 已先完成且有效；随后 formal train、evaluate、analyze
均退出码 0，终端 artifact 齐全，分析器通过，`formal_statistical_run=false`，本轮为
proof-sized 结论承载运行。记录的 `D_SC=0`，结果分支为
`DUPLICATED_IMMEDIATE_SINGLE_CHANNEL_EXACTLY_COLLAPSIBLE_G49`。

本轮使用 384 个真实 transitions、两次 PPO pass、每臂两次 actor Adam step，未使用
bootstrap；其余 G48 保护语义和 C++ toy backend 保持冻结。

## 迭代余额

本轮消耗 1 个结论承载迭代：`conclusion_bearing_iterations_consumed=38`，
`iterations_remaining=9`。后续仍按用户授权自动推进；若下一边界需要新的代码或外审，
先完成对应机械验收，禁止把未授权计算当作迭代。

## 证据

- [G49 formal evidence note](../research/cdc/EVIDENCE_NOTES/20260729_G48_DUPLICATED_IMMEDIATE_SINGLE_CHANNEL_COLLAPSE_G49_FORMAL_RESULT.md)
- [G49 design alignment raw](../external-review/rounds/20260729_g48_duplicated_immediate_single_channel_collapse_code_science_alignment_audit/21_PRO_OPEN_RAW.md)
- [G49 correction recheck raw](../external-review/rounds/20260729_g48_duplicated_immediate_single_channel_collapse_code_science_alignment_correction_recheck/21_PRO_OPEN_RAW.md)
- [G49 formal analysis](../../logs/formal_continuous_roster_native_six_g31_duplicated_immediate_single_channel_collapse_g49_cpu_20260729_8ecb01f_r1/analysis_result.json)
