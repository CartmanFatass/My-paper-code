# P01 — ACE / Asynchronous MAPPO

论文：*Asynchronous Multi-Agent Reinforcement Learning for Efficient Real-Time Multi-Robot Cooperative Exploration*，AAMAS 2023
原文：[本地 PDF](../papers/P01_ACE_AAMAS2023.pdf) · [会议 PDF](https://www.ifaamas.org/Proceedings/aamas2023/pdfs/p1108.pdf)
代码：[官方仓库](https://github.com/yang-xy20/async_mappo) · 本地 `../code/P01_ACE_async_mappo`

## 一句话结论

ACE 是八篇中唯一同时给出异步动作执行和机器人丢失压力测试的工作，但它解决的是固定 roster 上的异步决策与跨配置泛化；其代码没有实现时长正确的 SMDP return，也没有运行时动态增删 collector 维度。因此应吸收事件化执行壳，不应直接吸收其训练 return 或把它称为已解绑 `N`。

## 机制拆解

ACE 把每个机器人建模为独立到期的决策者。环境仍按基础时间步推进，但只有执行周期结束的智能体重新采样动作；尚未到期的智能体继续执行旧动作。策略侧用局部特征提取器和跨智能体注意力编码其他成员，避免让参数量随团队规模线性增长。

代码中的关键链路是：

- `onpolicy/utils/util.py::AsynchControl` 为每个 `(env, agent)` 保存剩余周期和活动标志；
- `onpolicy/runner/shared/gridworld_runner.py` 累积一个宏动作周期内的奖励，只在该智能体到期时写入异步 buffer；
- `onpolicy/utils/shared_buffer.py` 用每个智能体自己的 `update_step` 保存不同长度的事件序列；
- `onpolicy/algorithms/utils/invariant.py` 提供以其他成员为集合的注意力编码器。

## 对 `N` 的实际支持

论文在测试中让三机器人团队损失一台、两机器人团队损失一台，说明共享策略和集合式关系编码具有一定的 survivor robustness。这是有价值的直接压力证据。

但代码的 `AsynchControl`、buffer、runner 和若干网络层都由启动时的 `num_agents` 分配固定形状；`MIXBase` 还按固定成员数拆分通道并逐成员循环。也就是说：

- 支持：在另一个固定 `N` 配置中复用共享权重，或用屏蔽/重新配置模拟丢失；
- 不支持：episode 内 join、leave、充电离场、归队时动态改变存储形状；
- 未证明：掉队后 survivor recurrent state 与新成员初始化语义保持正确。

所以 ACE 提供的是“固定容量接口上的丢失鲁棒性证据”，不是完整的 open-roster contract。

## 对 `k / T_i` 的实际支持

执行层确实允许各智能体在不同基础时刻重新决策，但训练层没有保存实际持续时长 `T_i`。`SharedReplayBuffer.compute_returns` 仍按每条已存事件只乘一次 `gamma`，未使用 `gamma ** T_i`；周期内奖励也未按基础步进行显式折扣。因此宏事件长短不同时，价值目标并不满足 HMASD 要求的 SMDP 语义。

此外，`shared_buffer.py` 的异步插入路径有若干 `self.masks[step + 1] = ...` 一类整时间片赋值，而不是明确索引到 `(env, agent)`；迁移前必须将其视为待验证的原型代码，不能照搬。

## HMASD 吸收边界

| 判定 | 机制 | 原因 |
|---|---|---|
| ABSORB | 每智能体独立 readiness / 到期事件和周期奖励累积的执行壳 | 直接对应共享检查钟 `k0` 下的不同 `T_i` |
| CONDITIONAL | 活跃成员集合上的交叉注意力 | 需移除固定通道拆分、显式成员位置和固定 buffer 形状 |
| DIAGNOSTIC | 训练中正常、测试中随机掉队的 survivor 压力测试 | 可成为 episode 内 leave 的最小行为检查 |
| DO_NOT_ABSORB | 当前 return / GAE 实现 | 缺少 `gamma^T_i` 和事件时长字段 |
| DO_NOT_ABSORB | 将固定 `num_agents` mask 当作动态 roster | 无法表达新成员加入、离开后回归及 survivor hidden continuity |

## 最小后续因果门

若未来激活变 `k`，先仅复用事件化执行概念，并用手工轨迹证明
`R_e = sum_r gamma^r r_{t+r}`、bootstrap 使用 `gamma^T_i`。若未来激活变 `N`，ACE 只作为掉队压力 arm；collector 必须另行采用 active-only ragged roster 或等价的严格 mask contract。本报告不授权实现或实验。
