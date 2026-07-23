# 第 6 轮结论性迭代：动态 agent 数量的可用基线成立

## 本轮科学问题与决策

前五轮说明，复杂的 EHC/roster 机制即使会影响动作，也未必能在冻结的 PPO
预算下形成稳定能力。因此新的八轮研究链先降低目标：暂时冻结异步技能周期，不要求
机制优势，只检验一个共享策略能否在同一回合中面对 agent 离开、重返、新加入和终止
离开，并迁移到训练中未见的 agent 数量。

本轮算法 `OPEN_ROSTER_DIRECT_MVP_G5` 使用共享成员编码器、每个生命周期自有的
recurrent hidden state、活跃集合求和与 `log1p(N)` 上下文，以及只对当前活跃成员执行的
自回归 primitive policy。模型参数形状不依赖 roster 容量；容量只用于批处理 padding。
本轮只问绝对可用性，不设置任何算法比较优势门槛。

## 环境、运行条件与预算

训练使用三个 80 步动态 roster：`3→2→4→3`、`4→2→6→4`、
`5→3→7→5`，容量为 10。held-out 使用 `6→2→8→4` 和
`7→4→9→6`，容量为 12。每条轨迹都包含临时离开、重返、真实新加入和终止离开。
环境仍是 Generic-SHORT 外部任务；skill controller、EHC、内在奖励和异步技能周期
均未进入算法或环境。

```text
source_commit=4b38eae5abbaeccbab6d53e3eb8f50bd28b957a9
run=logs/formal_open_roster_direct_g5_cpu_20260723_4b38eae_r1
backend=cpu
torch=2.7.0+cpu
torch_threads=1
formal=true
replicates=3
updates_per_replicate=250
environments_per_update=8
horizon=80
ppo_passes=4
evaluation_episodes_per_cell=128
bootstrap_repetitions=10000
```

固定 Luna-low 实验子代理以前台单次方式完成 `train → evaluate → analyze`，三个
阶段退出码均为 0，没有重启，机械运行耗时约 1576 秒。

## 证据闭合

Project Manager 在实验结束后独立检查并重算结果：

- 3 个 replicate 均完成 250 次更新、160,000 个 environment steps 和 1,000 个
  optimizer steps，总计 480,000 步与 3,000 次优化；
- 3 对 zero/final checkpoint 全部存在；
- 24 个评估 cell 完整覆盖 3 个 replicate、zero/final、IID/held-out 以及
  deterministic/stochastic，每个 cell 恰有 128 个 episode；
- 所有更新有限，replay 最大误差严格为 0，生命周期契约全部通过；
- 训练和评估均为 CPU 单线程，source commit 一致；
- 五个 roster profile 的构造性最优策略 utility 均为 1；
- `operational_valid=true`、错误列表为空，独立重算的 first-match 与分析文件一致。

## 正式结果

| 指标 | 正式值 |
|---|---:|
| IID deterministic utility CI95 | [0.9985352, 0.9994303, 1.0000000] |
| Held-out deterministic utility CI95 | [0.9828880, 0.9939927, 1.0000000] |
| Held-out 各 replicate 均值 | [1.0000000, 0.9828880, 0.9990900] |
| Held-out 最低 replicate 均值 | 0.9828880 |
| Held-out stochastic utility 均值 | 0.9737068 |
| Held-out final-minus-zero CI95 | [0.4828880, 0.5434274, 0.6483043] |

所有冻结门槛均通过：IID 与 held-out 的 CI95 下界都高于 0.90，最差 replicate
高于 0.85，随机动作采样均值高于 0.80，训练相对初始 checkpoint 的增益下界大于
0。因此登记分支为：

```text
USABLE_OPEN_ROSTER_DIRECT_G5
```

## 对科学决策的影响

- 项目已经得到第一个可用的动态 agent 数量算法测试版。一个共享 checkpoint 能处理
  回合内 roster 变化，并从训练最大活跃数 7 迁移到 held-out 最大活跃数 9。
- 训练容量 10 与评估容量 12 不同而性能保持接近 1，支持“padding 容量不是模型参数”
  的实现与接口判断。
- 这说明起步阶段无需同时引入异步 skill lifetime 或 EHC，直接 recurrent active-set
  policy 已足以建立可工作的动态 roster 基线。
- 本轮不能证明它优于其他算法，也不能证明它能外推到任意大的 agent 数量。当前的
  活跃 embedding 求和会随 N 增长，可能在更远尺度失稳。
- 固定在 20/40/60 的成员事件仍可能形成时间模式捷径；本轮没有验证不同事件时刻、
  不同事件次数或更剧烈 count jump。

## 下一边界与迭代计数

G5 按原合同永久闭合作为成功结果，不重跑、不调门槛、不用后续结果改写。本轮消耗新链
8 次中的第 1 次，尚余 7 次。下一步是零训练的
`OPEN_ROSTER_ZERO_SHOT_SCALE_G6_DERIVATION`：定义如何用冻结的 G5 checkpoint
分离“更大未见 agent 数量”与“未见 membership 事件时刻”的外推能力，再决定是否需要
最小的 count-normalized 算法修正。异步技能周期继续冻结。

```text
conclusion_bearing_iterations_consumed_total=6
new_chain_iterations_consumed=1
iterations_remaining=7
next_boundary=OPEN_ROSTER_ZERO_SHOT_SCALE_G6_DERIVATION
```
