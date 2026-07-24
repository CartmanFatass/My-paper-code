# 解耦技能生命周期第 2 轮：排他慢通道的全区间反证

## 本轮科学问题

S1 证明：如果预测器同时能读取不受约束的 fast recurrent state `h`，那么只惩罚
slow state `z` 的写入无法识别记忆所有权。外部 GPT-5.6 Pro 因此选择新的
`C-ALPSC` 合同：primitive controller 可以继续拥有 `h`，但慢预测通道内，`z` 必须是
唯一跨 active-step 记忆。writer 只能读取当前通用局部观测、旧 `z` 和新 writer RNG；
decoder 只能读取写入后的 `z`。

本轮 `S2_EXCLUSIVE_SLOW_CHANNEL_IDENTIFIABILITY_DERIVATION` 继续使用完全不变的
S1 有限 source，不写代码、不运行实验。冻结门槛要求 cue writer 在完整区间
`0 < beta < (1/2)ln 3` 内始终唯一最优，并严格击败所有固定 age、周期、membership、
post-hoc 和随机混合 null。

## 排他通道与完整枚举

推导排除了 `h`、age、全局/局部时钟、动作、active-set/membership 历史、当前 cue 的
decoder 直通和任何辅助 RNN。候选 cue writer 在每个 7 步生命周期中仍精确写入 2 次，
预测 NLL 为

`H = ln 4 -(3/4)ln 3`，

所以总目标为 `H+(2/7)beta`。边界 precision/recall 均为 1，完整生命周期仍为
`{2,3}`，构造性 ALPSC 与 G8 策略均有 `U*=1`。

证据列出了 post-join ages 1–6 的全部 64 个 fixed-age bitmask，并对每个 mask 的
全部二值 candidate map 给出有限精确计数公式；所有 period/phase 都映射到这 64 个
mask，membership-event-only 的 8 个映射和 post-hoc null 也被覆盖。条件熵凹性证明
任何 stochastic mixture 不能优于其最佳 deterministic extreme point。

## 决定性反例：优化后的 never-write decoder

排他通道消除了 S1 的 recurrent leak，但 `NEVER_WRITE_AFTER_JOIN` 仍是合法结构 null。
它把 structural join 的 `z=B` 保持到结束，并针对聚合分布拟合最优 decoder。

两种脚本平均后，regime 与 `z` 同向的比例为 `9/14`，反向为 `5/14`。经过
`3/4` 的 target channel 后：

`P(Y=z | z)=4/7`。

因此 never-write 的最佳 NLL 不是受限的 `p_z` 值，而是

`L_NW = h(4/7) = ln 7 -(4/7)ln 4 -(3/7)ln 3`。

它与 cue writer 在以下内部点相交：

`beta_star = (7/2)ln 7 -(11/2)ln 4 +(9/8)ln 3`。

该点严格大于 0，并严格小于 `(1/2)ln 3`。后一个结论可由精确整数不等式证明：
`7^7<2^20`、`3^5<2^8`，所以 `7^28*3^5<2^88=4^44`。

于是：

- `0<beta<beta_star`：这个 never-write null 较差；
- `beta=beta_star`：两者并列，唯一性和严格 `Delta_SC>0` 失败；
- `beta_star<beta<(1/2)ln 3`：never-write 严格更优。

该 null 只读取 structural `z`，没有 `h`、cue、age、clock、action 或任何辅助状态，
因此不是 side-channel leak。

## 泄漏门槛核验

六个禁止泄漏都被构造性复现：fast `h` 或辅助 RNN 可零写入达到 `H`；age/clock 加 cue
pattern 可重建 regime；由 `h` 选择的 action 可把 bit 送入 decoder；直接 cue bypass
使 ages 3 和 6 的延迟两次写入达到同一 NLL；可恢复时间的 active-set 历史属于 clock
leak。这些只证明排他条件必要，不是本轮决定性合法 null。

first-match 有效终态为：

`NO_IDENTIFIABLE_EXCLUSIVE_SLOW_CHANNEL`

合同和枚举有效，也没有合法侧信道；失败发生在第三分支，因为完整冻结 beta 区间内存在
合法 never-write 交点和优势区间。

## 最小科学结论

本轮否决的是**精确 C-ALPSC 目标与完整冻结区间**。它说明：排除替代 temporal channel
是识别记忆所有权的必要条件，但不是充分条件。即使 decoder 只能读取 `z`，优化 decoder
后仍会出现 rate–distortion tradeoff：较粗糙的零写入状态可以用略高预测误差换取更低写入
代价，并在区间上部成为全局最优。

本轮没有证明排他预测通道、稀疏分段或个体生命周期普遍不可行。不能在本地缩窄 beta
区间、强制 decoder 使用 `p_z`、限制 never-write、换 source、写代码或运行实验来救援；
这些都会改变冻结科学合同，必须返回同一 Pro 对话重新选择。

本有效负结论消耗第 2 次结论性迭代；剩余 8 次。迭代 3 尚未选择。
