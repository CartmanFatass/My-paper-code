# 解耦技能生命周期第 4 轮：时域二阶受控状态与递归闭包

## 本轮科学问题

S3 已证明：完整的一步外部 intervention-kernel 向量可以精确识别两个状态类，并用最少两次 learned installation 得到 `{2,3}` 的 active-step lifetime。但这仍留下一个具体漏洞：两个 history 的**立即**受控预测完全相同，不代表它们的延迟受控未来也相同；而且一个只会总结当前预测、却不能由自身状态递归更新的 partition，也不能算真正的生命周期状态。

外部 GPT-5.6 Pro 因此选择 `C-ALSCPS` 与纯推导任务 `S4_HORIZON2_SEQUENTIAL_CONTROLLED_STATE_DERIVATION`。本轮不写算法代码、不运行 CPU/GPU、不启动实验或 Monitor。

## 构造：一步无信息、两步有信息

S4 保留 S3 的匿名三生命周期 source、脚本 `23/32`、21 个 active rows、temporary leave/rejoin、structural join、nuisance `N` 和完整 lifetimes `{2,3}`。

在每个合法 history 上，外部完整枚举四个 open-loop binary plan：`00,01,10,11`。plan 不依赖 `h`、`z`、历史、身份或自然策略，不进入 writer，也不修改自然生命周期。

branch 的第一个观测始终是公平比特：

`Y1 ~ Bernoulli(1/2)`。

第二个观测取决于 plan parity `u0 XOR u1` 与当前 regime `R` 是否相同：相同则 `P(Y2=1)=3/4`，不同则为 `1/4`。

于是：

- 只看 `Y1`，所有 regime 和 plan 都完全相同，`one_step_TV=0`，`K_1=1`；
- 对每个完整 plan，看联合序列 `(Y1,Y2)`，两种 regime 的 total variation 都是 `1/2`。

匹配 regime/plan parity 时，四个联合概率是 `(1/8,3/8,1/8,3/8)`；另一 regime 是 `(3/8,1/8,3/8,1/8)`。序列 Bayes floor 为

`L_2_star=ln2 + H`，其中 `H=ln4-(3/4)ln3`。

这给出了明确的一步 myopia 反例：立即受控 projection 合并了 history，但延迟受控 future 必须区分它们。

## Update congruence

S4 不只要求预测充分，还要求 quotient 可以由一个共同的 online 函数更新：

`F(class(z_old),O_now) -> class(z_new)`。

候选在 cue 上设置 `z=X`，非 cue 保持 `z`。任何处于同一 quotient class、看到同一合法 observation 的 history 都进入同一个 next class，不依赖被合并 history 的隐藏代表或更早记忆。因此 update-congruence mismatch 为 0。

这排除了另一类伪状态：如果一个 partition 的成员在同一新观测下需要不同 next class，它即使能总结当前预测，也不是可持续递归更新的 lifecycle state。

## 最小写入证明

模型继续按 `(E_2,q,K_2)` 字典序比较：先要求 horizon-2 excess 为 0，再最小化写入率，最后最小化合并等价 latent 后的 sequence-kernel 数。

C-ALSCPS 在 join 时结构性设置 `z=B`，只在两个 post-join cue 上写入当前 `R`，其他行保持，decoder 读取 `(z,plan)`。它得到：

- `E_2=0`；
- `q=2/7`；
- `K_2=2`；
- update mismatch 0；
- boundary precision/recall 1；
- complete lifetimes `{2,3}`。

严格 proper sequence log score 使 `E_2=0` 等价于每个正概率 history 和 plan 上的 KL 都为 0。因为两种 regime 的 horizon-2 kernel 对每个 plan 都相差 TV `1/2`，任何充分模型必须在实际 regime change 行 decode 前切换 class。两种脚本的第一个 change 分别在 age 2 或 3，第二个都在 age 5，所以每个生命周期至少写两次：

`q>=2/7`。

达到等号时不能在其他行正概率写入；合并所有 sequence-equivalent subdivision 后只能有两个 class，独立 nuisance `N` 被删除。

## 完整 null 核验

- **One-step quotient**：只有公平 `Y1`，`K_1=1`，无法拟合延迟 kernel，因此 `E_2>0`。
- **Never-write**：保留 `z=B`，延迟预测最佳概率为 `4/7` 或 `3/7`，所以 `L_2=ln2+h(4/7)`，excess `h(4/7)-H>0`。
- **Always-write**：可充分但 `q=6/7`。
- **全部 64 个 fixed-age mask**：充分 mask 必须同时包含 `{2,3,5}`；仅 8 个 superset 可能充分，而且 `q>=3/7`。其余 56 个漏掉必需 change。
- **周期 schedule**：有限 horizon 下仍归入上述 mask。
- **8 个 membership mapping**：不写 ordinary row 会漏掉内部 change；写 ordinary row 的率高于 `2/7`。
- **post-hoc**：未来 branch outcome 不能回写已安装状态或改变更早预测。
- **随机 writer/mixture**：零期望 excess 要求几乎处处精确，无法把两次必要 class change 平均掉。
- **nuisance-only**：不区分 sequence kernel；冗余 nuisance subdivision 合并。
- **identical-kernel negative**：正确得到 `K_2=1,q=0` 和无非平凡 lifetime。

由 fast `h` 选择 plan 属于 natural-plan-as-memory leak；writer 提前读取 `Y1/Y2` 属于 future-outcome leak，二者均被拒绝。

## Adaptive-plan 审计与递归基线

结论性查询集是四个 open-loop plan。即使额外审计一个由 `Y1` 决定第二 action 的 deterministic rule，`Y1` 与 regime 独立，所以 plan mixture 权重也与 regime 无关。每个实现的 `Y1` 条件下，延迟概率仍是 `3/4` 对 `1/4`，不会把一步 projection 变得有信息，也不会消除 horizon-2 区分。

C-ALSCPS 选择 `A=z`；G8 把 `R` 存入 `h` 并选择 `A=h`。二者 audit utility 都是 1，utility 不进入 sequential-state supervision。G8 仍是最强 simpler explanation。

## 结论边界

按 first-match 顺序，source/target 和 online order 有效，plan 没有记忆或未来泄漏，一步 projection 正确坍缩、horizon-2 kernel 正确分离，quotient 也满足 update congruence 与唯一最小写入。因此有效终态是：

`PASS_ALSCPS_FUTURE_CLOSED_DERIVATION`。

最小支持命题：在这个冻结有限 source 上，可以精确识别一个 update-congruent、horizon-2 sufficient、minimum-transition 的 agent-local state，其 active-step lifetimes 为 `{2,3}`。

本轮没有证明任意 horizon 闭包、learned recovery、skill semantics、普通 recurrence 不足、优化或样本效率优势、primitive-policy mediation、自然价值、鲁棒性、transfer 或最终算法集成。

本 PASS 消耗第 4 次结论性迭代；剩余 6 次。迭代 5 尚未选择，结果必须先返回同一 GPT-5.6 Pro 对话。
