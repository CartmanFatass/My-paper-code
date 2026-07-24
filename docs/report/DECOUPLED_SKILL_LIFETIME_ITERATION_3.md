# 解耦技能生命周期第 3 轮：受控预测状态的精确可识别性

## 本轮科学问题

前两轮分别否决了两种目标：S1 中，不受约束的 fast recurrence `h` 可以吸收 slow state；S2 中，即使 slow decoder 只能读取 `z`，固定 `beta` 的预测误差—写入率加权仍允许较粗的 never-write 状态在区间上部胜出。

外部 GPT-5.6 Pro 因此选择新的 `C-ALCPS` 合同。本轮不再用 `beta` 交换预测精度和写入次数，而是先要求**精确受控预测充分性**，再按字典序最小化 learned write 数和 decoder-distinct state 数量。整个 S3 只做有限源精确推导，不写算法代码、不运行 CPU/GPU、不启动实验或 Monitor。

## 受控查询为什么提供新信息

S3 保留 S1/S2 的匿名三生命周期 source、脚本 `23/32`、21 个 active rows、temporary leave/rejoin、fresh join、右删失和 `{2,3}` 生命周期。额外加入一个完全独立的 nuisance bit `N`，用来检验状态是否错误地记忆无关观测。

在每个合法 active history 上，外部枚举查询 `u∈{0,1}`。它不是自然策略选出的 action，不依赖 `h`、`z`、历史或身份，也不会跨步保存。target law 是：

- `u=R` 时，`P(Y=1)=3/4`；
- `u≠R` 时，`P(Y=1)=1/4`。

因此每个固定查询下，两种 regime 的 Bernoulli kernel 的 total variation 都是 `1/2`。但如果把 `u` 均匀边缘化并从 decoder 中删掉，两种 regime 都变成 `P(Y=1)=1/2`，区分度严格为 0。

这说明 load-bearing 信息不是 action marginal，而是完整的外部 intervention-kernel 向量：

- `R=0` 对应 `(3/4,1/4)`；
- `R=1` 对应 `(1/4,3/4)`。

## 新的字典序科学标准

对任意模型定义：

1. `E_ctrl`：相对受控 Bayes floor 的预测 excess；
2. `q`：每个 active row 的 learned state installation rate；
3. `K`：合并 decoder-equivalent latent 后，不同受控 kernel 的数量。

模型按 `(E_ctrl,q,K)` 字典序比较。也就是说，任何正预测 excess 都不能再用“少写几次”来补偿；只有 `E_ctrl=0` 的模型之间才比较写入率，再比较状态数量。这正面切断了 S2 never-write 反例利用的 rate–distortion 交换。

## C-ALCPS 候选与下界证明

候选在 genuine join 时结构性设置 `z=B`，在两个 post-join cue 上写入当前 `R`，其他行保持不变，并忽略 nuisance `N`。decoder 只读取 `(z,u)`。

它在每一行都有 `z=R`，因此：

- `E_ctrl=0`；
- `q=2/7`；
- 合并等价状态后 `K=2`；
- boundary precision/recall 都是 1；
- 完整 active-step lifetimes 是 `{2,3}`。

关键下界来自严格 proper log score。`E_ctrl=0` 意味着每个正概率 history 和每个查询上的 KL 都必须为 0，所以 decoder-visible state 必须区分两种不同的受控 kernel。脚本 `23` 在 active age 2 第一次换 regime，脚本 `32` 在 age 3 第一次换 regime，两者都在 age 5 换回。每个 change row 在 decode 前都必须从旧 kernel class 切到新 class，因此任何充分模型都必须在两个真实 post-join change 上各安装一次状态：

`q≥2/7`。

达到等号时不能再在其他行正概率写入。合并所有相同受控 kernel 的 latent subdivision 后，只剩两类；独立 nuisance `N` 改变不了 kernel，所以被 quotient 自动删除。

## 完整 null 与泄漏核验

- **Never-write**：保留 `z=B`，最优受控 decoder 仍只有 `4/7` 与 `3/7` 的软化概率，NLL 为 `h(4/7)>H`，所以 `E_ctrl>0`，在字典序第一项就失败。
- **Always-write**：可以充分，但 `q=6/7`。
- **全部 64 个 fixed-age mask**：要同时覆盖两种脚本，必须包含 ages `{2,3,5}`。只有这 8 个 superset 可能充分，而且至少写 3 次；其余 56 个缺少必需 change row，预测不充分。
- **周期 schedule**：在有限 horizon 内仍只是上述 age subset，不能更优。
- **membership-event-only**：membership event 与 `B,S` 独立，不能标出每个生命周期的两个内部 regime change。
- **post-hoc segmentation**：读取未来违反 online order；限制回合法 filtration 后仍受 `q≥2/7` 下界约束。
- **随机 writer/mixture**：期望 KL 为 0 要求每个正质量分量几乎处处充分；混合不能把必要的两次 class change 平均掉。
- **nuisance-only state**：不区分受控 kernel；冗余记录 `N` 的 subdivision 在 quotient 后合并。

另有两个关键反例：去掉 `u` 的 `ACTION_MARGINAL_NULL` 正确得到单一 kernel 和无非平凡 lifetime；让 fast `h` 选择自然 action 会把 action label 变成记忆侧信道，因此不能作为 intervention query。

## 递归基线与不变量

构造性 C-ALCPS 策略选择 `A=z`，G8 recurrence 把 `R` 存在 `h` 中并选择 `A=h`；二者 audit utility 都是 1。外部 utility 不进入 writer、loss、target、decoder 或 boundary decision。

对 lifecycle key 重命名、active-member permutation、inactive padding、temporary-absence insertion、query label 连同 kernel 列交换、latent `0↔1` 重命名，mismatch 全部为 0。G8 仍是完整行为 comparator 和最强 simpler explanation。

## 结论与边界

按预声明 first-match 顺序，合同无算术或 filtration 错误，query 没有侧信道，受控 source 可识别，也不存在同等或更优的不同最小写入 schedule。因此本轮有效终态是：

`PASS_ALCPS_CONTROLLED_STATE_DERIVATION`。

这证明的最小命题是：在冻结有限 source 上，可以用完整外部 action-interventional predictive law 的 coarsest minimum-transition quotient，精确识别一个具有 `{2,3}` active-step lifetime 的 agent-local state。

它**没有**证明该状态已经是 learned skill，也没有证明普通 recurrence 不足、C-ALCPS 更易优化、更省样本、具有自然因果中介、提高 held-out return、增强鲁棒性或能迁移到最终 HMASD 算法。上述问题都必须由后续 Pro 选择的新证据合同回答。

本有效 PASS 消耗第 3 次结论性迭代；剩余 7 次。迭代 4 尚未选择。结果必须先返回同一 GPT-5.6 Pro 对话。
