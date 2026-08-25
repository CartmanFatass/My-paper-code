# P02 — Agent-Centric Actor-Critic (ACAC)

论文：*Agent-Centric Actor-Critic for Asynchronous Multi-Agent Reinforcement Learning*，ICML 2025
原文：[本地 PDF](../papers/P02_ACAC_ICML2025.pdf) · [PMLR PDF](https://raw.githubusercontent.com/mlresearch/v267/main/assets/jung25a/jung25a.pdf)
代码：[官方仓库](https://github.com/LGAI-Research/acac) · 本地 `../code/P02_ACAC`

## 一句话结论

ACAC 是当前短名单中对解绑 `k` 最有直接帮助的论文：它把每个智能体的有效宏事件历史单独编码，并让 `gamma` 按真实微时间流逝、让 `lambda` 按宏决策次数递推。它没有解绑 roster，因此应吸收 SMDP credit 语义和 agent-centric history，不能照搬固定 `n_agent` critic。

## 机制拆解

异步宏动作使不同智能体拥有不同长度、不同时间戳的轨迹。ACAC 不把“某智能体没有新决策”伪造成一个同步观测，而是：

1. 从联合环境轨迹中抽取每个智能体自己的有效宏事件序列；
2. 用共享或独立的历史编码器处理这些 agent-centric histories；
3. 在联合事件时刻，为每个智能体取其最近有效历史表示；
4. 用 attention centralized critic 聚合这些表示；
5. 把联合优势重新映射回每个智能体实际发生的决策事件上做 PPO。

代码中的核心位于 `acac/acac_marl/cores/acac/learner_acac.py`、`memory.py`、`models.py` 和 `envs_runner.py`。实现仍会为 minibatch 进行张量 padding，但先抽取有效事件再重组；这里的“without padding”应理解为不把缺失异步事件当成真实历史，而不是整个训练栈完全没有 padding。

## 对 `k / T_i` 的关键贡献

论文和代码都把两类时间指数分开：

```text
delta_l = R_l + gamma^(l_next-l) V_next - V_l
A_l     = sum_j lambda^j gamma^(l_j-l) delta_l_j
```

因此：

- `gamma` 的指数是实际经过的微时间，负责物理时间折扣；
- `lambda` 每跨过一个宏决策乘一次，负责 estimator 的事件深度；
- 每个智能体可有不同的事件时间戳与宏动作长度。

代码先构造 `gamma^t`，再用相邻联合事件之间的比值得到 `gamma^(Delta t)`；GAE 递推使用 `mac_discount * GAE_lambda`。这与 HMASD 候选中的 `gamma^T_i` 方向一致，且比 ACE 的标准一步 return 更可信。

需要注意：ACAC 的时间是宏动作自然结束产生的，不自动解决“不同技能周期需求如何学习”这一上层问题。对 HMASD，第一步仍应使用外生 `T_i`，而不是同时学习 timing policy。

## 对 `N` 的实际支持

环境和 controller 均在启动时固定 `env.n_agent`；centralized critic 的 token 数、agent 列表和经验结构都假定 roster 不变。attention 使参数共享更容易，但不能据此推断 episode 内 join/leave。

若迁移到 open roster，需要至少补上：active-only token packing、join 初始化、leave 后不 bootstrap、survivor hidden continuity、同一 PPO batch 中 roster 事件的有效性 mask，以及按活跃成员数稳定 critic/advantage 尺度。

## HMASD 吸收边界

| 判定 | 机制 | 原因 |
|---|---|---|
| ABSORB | 微时间折扣 `gamma^T_i` 与宏事件级 `lambda` 的分离 | 直接修复不同技能持续期下的 SMDP credit |
| ABSORB | 每智能体有效事件历史与“最近有效快照”聚合 | 避免把异步空档伪造成同步样本 |
| CONDITIONAL | attention centralized critic | 必须改为 active-only roster，并稳定随 `N` 变化的归一化和梯度尺度 |
| CONDITIONAL | 联合优势到各 agent 事件的映射 | 需证明与 HMASD 的 on-policy owner、mask、detach 和 bootstrap 边界一致 |
| DO_NOT_ABSORB | 固定 `n_agent` rollout/controller 外壳 | 不支持运行时成员变化 |

## 最小后续因果门

未来变 `k` 的第一个门只需在固定 `N` 下比较统一外生周期与异质外生 `T_i`，并用可解析短轨迹先验证 return/GAE。不得在同一首轮门中加入动态 roster、learned termination 或新 intrinsic reward。本报告不授权实现或实验。
