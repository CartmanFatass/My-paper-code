# 第 20 轮算法迭代报告

## 本轮科学问题

本轮检验 G30 的核心猜想：把即时通道和后继通道的全 actor 梯度分别做全局单位化，再等权合成，是否能在不同随机种子下同时保持 G17 的即时动态 roster 能力，并稳定学会 G18 的延迟电池轮换服务。

## 算法与实验环境

- 算法：`DIRECTION_BALANCED_FULL_ACTOR_G30`。
- 两个 toy 环境：G17 连续服务 roster 与 G18 延迟电池 roster；本轮未运行 UAV 环境。
- 运行平台：本机 AMD CPU，`torch 2.7.0+cpu`，单线程；Python 为 `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`。
- 三个全新 replicate，不从 G28、G29 或 G30 screen checkpoint 恢复。
- 每个 G17 replicate 使用 `100` 次 fast 更新和 `100` 次 direction-balanced 更新；每个 G18 replicate 使用 `100/300` 次；每次 8 个环境、2 次 PPO pass。
- G17 每个 domain、每个 replicate 评估 128 个 episode；G18 每个 replicate 评估 3 种 slot layout；bootstrap 10,000 次。
- 正式源提交：`1e4fbb735107b2a924bb3fd4f682c251ab62fb72`。
- 运行目录：`logs/formal_direction_balanced_g30_cpu_20260724_1e4fbb7_r1`。

## 证据闭合

训练、评估和分析均完成，正式标记与 CPU 单线程条件正确。证据包含 6 个训练结果、12 个 zero/final checkpoint 和 21 个评估 cell。所有 replay 误差与方向合成 identity 误差均为 0，最小即时方向点积为正，Adam 每次只推进一步；生命周期、参数所有权、inactive action 与 exact-zero residual 均通过。PM 用冻结函数独立重算出的首匹配分支与 artifact 一致。

## 注册结果

首匹配结果为：

`NO_DELAYED_ACCESS_DIRECTION_BALANCED_G30`

G17 全部通过：

- IID utility CI95：`[0.94011, 0.95000, 0.95634]`；
- held-out utility CI95：`[0.94011, 0.94442, 0.95089]`；
- gain CI95：`[0.33645, 0.39343, 0.44536]`；
- 最差单 episode：`0.89821`；
- effort/mix 最低相关系数：`0.98445/0.99371`。

G18 的总体学习也较强：

- utility CI95：`[0.95872, 0.96449, 0.97364]`；
- 相对 zero checkpoint 的 gain CI95：`[0.23698, 0.24839, 0.26258]`；
- rotating effort share CI95：`[0.87067, 0.88924, 0.90926]`；
- 最低 replicate utility：`0.95870`。

决定性失败项是 spike utility：CI95 为 `[0.87611, 0.89346, 0.92093]`，其下界低于冻结门槛 `0.90`。三个 replicate 的 spike 均值约为 `0.87611`、`0.88323` 和 `0.92106`。

## 对科学判断的影响

本轮排除了“G30 只是单 seed 偶然保持 G17”的解释：它在三个 fresh seed 上稳定保留了 G17，并且 G18 总 utility、总体 gain、轮换机制和 replicate 总体稳定性都通过。与此同时，它没有稳定解决最关键的短时突发服务：两个 replicate 的 spike 表现明显低于要求。

因此，当前证据支持“等权全局方向平衡能解决大部分跨通道冲突”，但不支持“已经得到可用的延迟动态 roster 算法”。失败已从广义表示或总体延迟学习，收缩到 spike 时刻的 credit/动作分配稳定性。

## 本轮不支持的结论

- 不得用 spike 均值或置信区间上界替代冻结的下界门槛。
- 不得更换 seed、增加预算、降低 `0.90` 门槛或重跑 G30 来救援。
- 本轮未证明 UAV 通信、运动、充电站几何或真实部署鲁棒性。
- 本轮也未证明对任意 agent 数量、任意延迟机制或任意任务分布普适。

## 下一边界

G30 正式关闭。下一步为 `G31_DELAYED_SPIKE_CREDIT_ALLOCATION_DERIVATION`：先用零计算推导区分“总体延迟效用已学会但 spike 分配不稳”的最小算法机制，再决定一个 bounded toy discriminator。剩余自动结论性迭代为 7 轮。
