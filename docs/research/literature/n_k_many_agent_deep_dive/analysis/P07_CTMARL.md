# P07 — Continuous-Time Value Iteration for MARL

论文：*Continuous-Time Value Iteration for Multi-Agent Reinforcement Learning*，ICLR 2026
原文：[本地 PDF](../papers/P07_CTMARL_ICLR2026.pdf) · [arXiv PDF](https://arxiv.org/pdf/2509.09135)
代码：[官方仓库](https://github.com/Wangxuefeng1024/Continuous-Time-Value-Iteration-for-Multi-Agent-Reinforcement-Learning) · 本地 `../code/P07_CTMARL`

## 一句话结论

这篇论文对“真实时间间隔必须进入价值语义”提供了有力连续时间对照，但不是 HMASD 的直接算法候选：它让所有智能体共享同一个随机 `Delta t`，使用固定 `N` 的联合状态、PINN/HJB 和模型化 dynamics。可吸收的是 duration-aware invariant 和压力测试思路，不应迁移整套 VIP/VGI。

## 机制拆解

论文把离散 Bellman recursion 改写为连续时间 HJB 条件，用 PINN 逼近价值函数，并用 Value Gradient Iteration (VGI) 沿轨迹传播价值梯度。实验把 MPE 与 Multi-Agent MuJoCo 改成随机积分步长，覆盖最多 6 个智能体和 113 维状态；目标是证明算法在任意或不固定时间间隔下比离散时间基线更稳。

代码中：

- `algo/multi_main.py` 从 Dirichlet 分布生成全局 `delta_ts`，所有智能体在某一步共享同一值；
- `algo/vip/agent.py::choose_action` 把该标量复制给每个智能体并拼到局部观测；
- VGI target 显式使用 `gamma_dt = exp(log(gamma) * dt)`；
- continuous return helper 使用 `reward * dt + gamma^dt * future_return`，对应连续 reward rate 的积分近似；
- 每个智能体各有一套 policy/value/dynamics/reward 网络，而 value/dynamics 输入输出依赖展平的联合维度。

## 对 `k / T_i` 的价值与边界

论文明确表明固定一步折扣在随机时间间隔下会产生偏差，并通过随机 `Delta t` 测试这种鲁棒性。这支持 HMASD 的基本不变量：事件持续时间必须成为 return、critic 和可能的 policy/recurrent input 的一等数据。

但它的 `Delta t` 是一次联合环境步的全局标量，不是每个智能体的不同 `T_i`；也没有异步事件序列、agent-centric GAE 或宏动作自然终止。连续 reward rate 的 `r * dt` 还不能直接替换 HMASD 离散基础步的
`sum_r gamma^r reward_(t+r)`，两者必须由环境 reward contract 区分。

## 对 `N` 和实现成熟度的限制

联合 state/action 维度和每智能体网络列表都由固定 `n_agents` 构造，计算量会随 `N` 和联合状态快速增长。论文没有动态 roster 或跨 `N` 权重复用证据。

仓库更适合论文原型阅读而非直接依赖：例如 `compute_discounted_returns` 把 `n_agents` 局部写成 `1`，而注释宣称返回 `[T, n_agents]`；`soft_update_target_value_net` 对 Python list 调用 `.parameters()`。这些可复核的接口问题意味着即使只复现实验，也应先修正和验证代码，而不是作为 HMASD 生产实现基础。

## HMASD 吸收边界

| 判定 | 机制 | 原因 |
|---|---|---|
| ABSORB | `Delta t` 必须进入折扣/价值目标这一不变量 | 与 `gamma^T_i` 的 SMDP contract 同方向 |
| DIAGNOSTIC | 随机时间间隔训练/测试矩阵 | 可检验固定周期策略对未见时长的退化 |
| CONDITIONAL | 把 elapsed/control duration 作为策略输入 | 需先证明不泄露未来持续期，并与事件 owner 一致 |
| DO_NOT_ABSORB | PINN + HJB + VGI + learned dynamics 整栈 | 与当前 PPO 路线、计算规模和因果问题不匹配 |
| DO_NOT_ABSORB | 全员共享 `Delta t` 作为变 `T_i` 证据 | 没有每智能体异步性 |

## 最小后续因果门

固定 `N` 下用外生异质 `T_i` 构造可解析短轨迹，比较标准一步折扣与 duration-correct SMDP return；再做 seen/unseen 时长压力测试。ACAC 应是实现主参考，本篇只提供连续时间语义对照。本报告不授权实现或实验。
