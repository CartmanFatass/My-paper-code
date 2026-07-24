# 解耦技能生命周期第 1 轮：C-ALPSW 可识别性反证

## 本轮科学问题与冻结边界

外部 GPT-5.6 Pro 选择了 `C-ALPSW`：每个 agent 生命周期拥有一个快速 recurrent
状态 `h` 和一个只在内生边界稀疏写入的连续慢状态 `z`。写入器只能学习通用观测与
membership 动态，不得读取外部奖励、任务字段、身份、角色、成功或进度信息。

本轮唯一行动是 `S1_ALPSW_IDENTIFIABILITY_DERIVATION`。它不写算法代码、不运行
实验，只回答一个先决问题：在冻结的预测描述长度目标下，是否存在非空写入代价区间，
使非退化 sparse writer 唯一优于 always-write、never-write、固定周期、
membership-event-only 和事后分段 null，同时 G8 recurrent 控制器仍能达到最优行为。

## 精确有限构造

推导构造了 3 个匿名生命周期、21 个 active transition。每个生命周期独立采样初始二值
regime，以及 `{2,3}` 或 `{3,2}` 两种 active-step 段长脚本；因此完整生命周期精确包含
两种长度 2 和 3。全局 membership 表同时包含临时 leave/rejoin、一个 genuine join 和
terminal leave。临时缺席不推进 active-step 时钟，并冻结状态与 RNG。

每个新段首行给出通用二值 cue，其余行不再给出 regime。下一通用观测位以精确概率
`3/4` 匹配当前 regime、以 `1/4` 相反。正确记忆 regime 时，每步预测 NLL 为

`H = ln 4 - (3/4) ln 3`。

意图中的 sparse writer 在每个 7 步生命周期只进行 2 次 learned write，边界 precision
和 recall 都为 1，目标为 `H + (2/7)β`。构造性 ALPSW 策略和构造性 G8 recurrent
策略都能精确记住 regime 并获得 `U*=1`。

## 决定性反证

冻结合同同时把未受容量约束、未受复杂度惩罚的快速 recurrent 状态 `h` 提供给预测
解码器。因此，never-write null 可以在 cue 出现时只更新 `h`，完全不写 `z`，仍在每个
active row 达到同一个熵下界 `H`，且 learned-write cost 为 0。

更一般地，对任何有限在线过程，recurrent 状态都可以编码有限合法历史或相应的预测充分
统计量，并输出对原 writer 内部随机性边缘化后的预测分布。log-sum 不等式保证其预测
NLL 不高于原 sparse writer。于是：

- `β>0`：零写入 recurrence 严格优于任何正写入率的 writer；
- `β=0`：两者至少并列，非退化 writer 不唯一；
- `β<0`：always-write 因更多写入获得更低目标，仍不选择 sparse writer。

所以不存在任何满足条件的开放 `β` 区间。对完整 C-ALPSW 参数类，`β≥0` 时
`Delta_ID(β)=0`；若强制使用意图中的两次写入构造，则 `β>0` 时
`Delta_ID(β)=-(2/7)β<0`。

## 逐项核验

- 精确有理 transition/observation law：通过；
- 在线 filtration 与禁止信息：通过；
- independent lifecycle change points：通过；
- temporary leave/rejoin、genuine join、terminal leave：通过；
- 五个结构 null 的解析最优值：通过；
- 两种完整 active-step lifetime：通过，精确为 2 和 3；
- ALPSW 与 G8 构造性效用：通过，均为 1；
- lifecycle key、active 顺序、inactive padding、缺席插入不变性：mismatch 全为 0；
- 非空写入代价区间：失败，区间为空；
- 算法代码、原型、CPU/GPU 或正式实验：均未执行。

first-match 有效终态为：

`NO_ONLINE_IDENTIFIABLE_SLOW_STATE`

较低优先级的 `NULL_EQUIVALENT_PREDICTIVE_WRITE` 也有 never-write 等价证据，但不能覆盖
更早的“无可识别区间”终态。

## 最小科学结论

本轮否决的是**当前冻结的 C-ALPSW 预测目标**：当 fast recurrent state 不受瓶颈或
复杂度约束且也进入预测器时，该目标无法识别慢状态的独立因果所有权。

本轮没有证明 predictive state、稀疏分段、个体生命周期或 task-blind latent dynamics
无用，也没有证明 G8 在优化、样本效率或迁移上等价。任何加入 fast-state 信息瓶颈、
复杂度代价、不同 decoder filtration 或新因果目标的修正都会改变科学合同，必须先回到
同一 GPT-5.6 Pro 对话，不能在本地用调 `β`、改 latent width 或换 source 难度救援。

本有效负结论消耗授权链第 1 次结论性迭代；剩余 9 次。下一步仅是把精确证明和最小反驳
命题提交回同一 Pro 对话，由 Pro 重新执行 CDC 并选择一个后续行动。
