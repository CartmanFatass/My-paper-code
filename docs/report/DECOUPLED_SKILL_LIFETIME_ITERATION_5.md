# 解耦技能生命周期第 5 轮：预测相位不等于行为技能边界

日期：2026-07-24

## 本轮结论

第 5 次结论性迭代得到精确 PASS：

`PASS_PREDICTIVE_PHASE_SKILL_LIFETIME_CONFOUND`

本轮没有运行代码、原型、训练或实验。它回答的是实现前的语义问题：如果一个状态既负责当前受控行为，又负责预测下一 active observation 的 transition phase，那么该状态的每次变化能否直接解释为“技能生命周期边界”？答案是否定的。

## 决定性反例

冻结 source 保留两个等概率脚本：

- `23` 的 cue rows 为 `0,2,5`；
- `32` 的 cue rows 为 `0,3,5`。

在 active age 1 之后，两个脚本都只显示了 `C_0=1,C_1=0`，因此脚本后验仍为各 `1/2`。下一 active row 是否出现 cue 的概率是：

`P(D_1=1)=1/2`。

沿 script 32 到 active age 2，当前合法观察是 no-cue：`C_2=0`。这条当前观察排除了 script 23，并确定下一 active row age 3 必有 cue，所以：

`P(D_2=1|S=32,age2)=1`。

然而 script 32 在 age 1 与 age 2 的当前 regime 都是 `B`。完整 current controlled behavior 没有变化。精确签名因此是：

```text
current_behavior_TV=0
predictive_phase_TV=1/2
I_extra=1
phase_only_boundary_count>=1
```

## 为什么这会破坏 monolithic skill 语义

若一个 monolithic predictive state 要同时精确表示当前行为与下一 cue 相位，它必须区分上述两个 history，因为同一个 decoder class 不可能同时输出 Bernoulli `1/2` 和 Bernoulli `1`。

因此该状态必须在 script 32 的 age-2 no-cue 行切换 class；但当前行为仍是 `B`。这次切换发生在第一个长度为 3 的恒定行为 segment 内，是纯粹的信息/预测相位更新，而不是真实行为技能切换。

把每个 predictive-state change 都计为技能边界，会把一个真实行为生命周期错误切成多个 apparent lifetime。

## 可行的科学修正

本轮只证明两个科学对象必须分开解释：

- `b`：当前 controlled-behavior class；
- `p`：预测 next-active transition law 所需的 phase。

在决定性 history 上，合法 online update 是：

```text
p: script_uncertain -> script32_next_cue_certain
b: B -> B
```

`p` 更新，但 `b` 不变，因此行为技能生命周期不重置。这个结果支持研究 behavioral/predictive-phase factorization，却没有预选任何网络结构、损失函数或训练方法。

## 排除的捷径

本轮没有使用：

- active age、全局时钟或 `t mod k`；
- script oracle；
- future cue；
- membership history；
- identity、role、task、reward、goal、success 或 progress；
- natural action memory；
- nuisance bit。

Temporary absence 被 next-active 语义跳过，并冻结 lifecycle state，因此不会制造或消除反例。G8 recurrence 仍是完整外部策略比较器；本轮不声称 recurrence 表达不足。

## 结论边界

本轮仅证明：在冻结有限 source 上，generic predictive phase 可以在 current behavior 不变时更新，所以 monolithic predictive-state transition 不能普遍当作行为技能生命周期边界。

它不证明：

- 可学习的 factorization；
- 最优架构或训练目标；
- learned transition timing；
- primitive-policy 收益；
- recurrence 不足；
- 任意 horizon closure；
- optimization、value、robustness 或 transport 收益；
- 最终 HMASD 集成。

第 5 次结论性迭代已消耗，剩余 5 次。结果必须先回到同一注册 GPT-5.6 Pro 对话，由外部科学裁决选择第 6 次行动。
