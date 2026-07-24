# 第 18 轮：动态 roster 连续服务与即时信用对齐

## 本轮科学问题与决策

本轮检验一个比此前离散 toy 更接近连续控制、但仍足够轻量的问题：同一套参数规模不依赖在线 agent 数量的策略，能否在 episode 内发生离队、归队、新加入和永久离开时，根据当前通信负载与服务配比，学会连续分配服务动作。

此前多组非正式实验表明，单纯增加训练量、缩小探索方差、加入当前观测残差或采用人数课程都只会学到近似常数动作。关键修正是把 actor 信用与本环境的即时服务目标对齐：使用 `gamma=0`，不再把之后独立重新采样的需求误归因给当前动作。正式结果为 `USABLE_ONE_STEP_CONTINUOUS_ROSTER_G17`。

## 算法、环境与预算

- 源码 commit：`91f6cbb58dfacd7e30462828aeb301d9c96df9dd`
- 正式目录：`logs/formal_continuous_service_roster_g17_cpu_20260724_91f6cbb_r1`
- 环境：48 步连续服务 toy；第 12、24、36 步发生 roster 变化
- 训练人数轨迹：`4→3→6→5`、`5→3→7→6`、`6→4→8→6`
- 留出人数轨迹：`3→2→5→4`、`6→3→8→5`
- 动作：每个 active agent 两个连续坐标，分别控制服务努力程度与服务混合比例
- 表示：active-set 求和、`log1p(active_count)`、成员 lifecycle 独立 GRU 状态、active-fraction 动作前缀
- 算法修正：启用当前观测线性残差；actor credit 使用 `gamma=0`
- 训练：3 个独立 replicate，每个 100 updates、每次 8 个环境、2 次 PPO pass
- 评估：每个域 128 episodes；10,000 次层次 bootstrap
- 设备：AMD CPU、PyTorch 2.7.0+cpu、单线程；未进行 CPU/CUDA 对比

## 证据闭合

训练、评估和分析均完整结束。6 个 checkpoint 引用全部存在，15 个 evaluation cells 共 1,920 个 utility 值，10 个构造性 source control 全部闭合。所有 roster 轨迹与生命周期规则一致，构造性动作可达到近似 1 的逐步效用；teacher replay 的 log-probability、joint log-probability、value、hidden state、prefix 和 inactive likelihood 最大误差均为 0。

Project Manager 独立复算冻结的 first-match 分支，与分析器结果完全一致。没有通过降低门槛、改变 seed、增加预算或重命名结果进行救援。

## 正式结果

| 指标 | 正式结果 |
|---|---|
| IID deterministic utility CI95 | `[0.9486910, 0.9513964, 0.9539132]` |
| held-out deterministic utility CI95 | `[0.9372598, 0.9431133, 0.9474355]` |
| held-out final-minus-zero CI95 | `[0.3017123, 0.5464017, 0.7473721]` |
| 最低 held-out replicate 均值 | `0.9366205` |
| held-out stochastic mean | `0.8380883` |
| 最低 effort / mix correlation | `0.9637707 / 0.9904294` |
| 最大 effort / mix MAE | `0.0261737 / 0.0185482` |

所有正式门槛均通过，因此接受当前 G17 作为“即时连续服务目标下可用的动态 roster 控制器”。

## 对算法决策的影响

这轮最重要的进展不是简单增加一个网络模块，而是定位到信用窗口与任务因果窗口的错位：长 GAE 把无关未来需求混入当前动作的优势估计，导致策略收敛到平均常数；对齐后，同一小型策略即可稳定学习当前负载和服务配比，并迁移到未参与训练的人数轨迹。

保留的算法核心是：参数形状不绑定在线 agent 数量、active-set 聚合、成员生命周期状态和归一化动作前缀。新增的当前观测残差很小，只提供直接条件路径；它本身在错误信用下并不能学习，说明正向结果不能归因于单纯增加容量。

## 结论边界与下一轮

可以声称：在注册的即时服务 toy 中，已经得到一个能处理运行中 agent 数量变化的可用连续控制测试版。

不能声称：它已经解决 UAV 的移动、通信、能耗、充电轮换或长时域规划；也不能声称相对其他算法具有优势。特别是 `gamma=0` 只适合当前动作立即产生被计分结果的来源，不能直接搬到具有未来电量与位置后果的 UAV 环境。

下一轮先在轻量 toy 中构造“当前努力改变后续服务可用性”的最小反例，推导带电量/充电状态时的信用传递方式，再决定是否值得推广到重型 UAV。第 18 轮已消耗 1 次结论性迭代，本次 10 轮自动链剩余 9 次。
