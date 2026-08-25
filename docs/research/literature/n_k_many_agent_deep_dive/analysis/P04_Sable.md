# P04 — Sable

论文：*Sable: a Performant, Efficient and Scalable Sequence Model for MARL*，ICML 2025
原文：[本地 PDF](../papers/P04_Sable_ICML2025.pdf) · [PMLR PDF](https://raw.githubusercontent.com/mlresearch/v267/main/assets/mahjoub25a/mahjoub25a.pdf)
代码：[维护版 Mava](https://github.com/instadeepai/Mava) · 本地稀疏检出 `../code/P04_Sable_Mava`

## 一句话结论

Sable 明确属于 many-agent 研究：它在超过 1,000 个智能体时保持近线性内存增长，是很强的 coordinator scaling reference。但其 retention 序列把同步时间和固定顺序的 `N` 个成员展平，网络与 mask 显式依赖 `n_agents`；它没有解绑运行时 `N`，也没有解绑技能周期 `k`。

## 机制拆解

Sable 将 RetNet 的 retention 机制改造成 MARL 序列模型。它把一个 batch 中的时间和智能体轴组织为长序列，在同一环境时刻建模成员间依赖，在跨时刻方向保留递归记忆；相较 Transformer 的全注意力，retention 可用 recurrent/chunkwise 形式把内存增长压到近线性。

本地只检出了相关 Mava 子树。关键文件包括：

- `mava/networks/retention.py`：parallel、recurrent、chunkwise retention；
- `mava/networks/sable_network.py`：Sable encoder/decoder 与隐状态；
- `mava/networks/utils/sable/`：mask、衰减矩阵和序列整理；
- `mava/systems/sable/`：learner、executor 与配置。

## 对 many-agent 的真实贡献

论文在 Neom 等环境把规模扩展到 32、512、1,024 甚至更多智能体，并比较 MAT 的显存爆炸；Sable 的主要贡献是让长 joint sequence 在显存和吞吐上可执行。这个结论对 HMASD 的价值是：如果 full-set/MAT coordinator 随 `N` 成为瓶颈，Sable 是一个强的容量对照。

不过“能运行 1,000 个智能体”与“能在同一 episode 动态改变 active roster”是两个问题。大规模任务中的每次运行仍采用固定成员数和稳定顺序；论文也没有充电离场、掉队、join/rejoin 的状态语义。

## 对 `N` 与 `k` 的代码边界

实现中 `n_agents` 被写入 mask、chunk 衰减和序列切片，例如按 `::n_agents` 取时间边界、按 `n_agents` 重复衰减块，以及用 `C // n_agents` 解释 chunk。改变 `N` 会改变序列位置与衰减结构，通常需要新配置/重编译；成员中途离开还会使后续 token 的相位和隐状态归属发生歧义。

Sable 中的 retention decay 只是表示记忆的衰减参数，不等于 RL 折扣 `gamma`，更不等于技能实际持续期 `T_i`。整个 rollout 仍是同步 timestep，因此不能用它证明变 `k`。

## HMASD 吸收边界

| 判定 | 机制 | 原因 |
|---|---|---|
| DIAGNOSTIC | 1,000+ agent 的显存/吞吐曲线 | 提供 many-agent coordinator 的强容量基线 |
| CONDITIONAL | retention 作为固定 `M` slot coordinator | 当 Field-Slot 表示门先通过后，固定槽序列可能受益于长时记忆 |
| DO_NOT_ABSORB | 直接以 `T*N` 展平成员序列来解绑 `N` | 固定 `n_agents`、顺序和同步时间假设过强 |
| DO_NOT_ABSORB | 将 retention decay 当成 `T_i`/SMDP 处理 | 概念和 credit 语义均不同 |

## 最小后续因果门

Sable 不应进入当前 N/k 第一因果边。只有 Field-Slot 的表示充分性和固定 `M` coordinator 需求成立后，才可把 retention 与 attention/MAT 作为相同 slot 输入上的容量比较；该比较只能回答效率与记忆，不回答动态 roster 或技能周期。本报告不授权实现或实验。
