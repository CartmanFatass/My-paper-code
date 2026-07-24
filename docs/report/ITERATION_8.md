# 第 8 轮结论性迭代：原始 roster 表示不能稳定外推到 N>16

## 本轮科学问题与决策

第 6、7 轮已经证明，同一组 G5 checkpoint 在未见成员数量与事件时刻下可稳定迁移到
N=16。本轮故意越过代码声明的 N=16 表示范围，在不训练、不改参数、不裁剪 count
特征的前提下，检验它能否继续用于 N=20、24、28、40 的 roster。

这一步先诊断再修复。若原 checkpoint 本身能够通过，就没有必要过早更换聚合方式；若
失败，则失败位置可以决定是否进入尺度归一化算法。

## 环境、运行条件与证据预算

```text
source_commit=19ea4d915ee4bdd03e81c913570d66f0ad00974d
run=logs/formal_beyond_declared_count_g7_cpu_20260723_19ea4d9_r1
checkpoint_source_commit=4b38eae5abbaeccbab6d53e3eb8f50bd28b957a9
backend=cpu
torch=2.7.0+cpu
torch_threads=1
formal=true
imported_replicates=3
optimizer_steps=0
evaluation_cells=18
evaluation_episodes_per_cell=128
bootstrap_repetitions=10000
maximum_active_count=40
maximum_count_feature=1.3107280023564027
```

三个压力域分别覆盖：刚超过声明范围的 `moderate_beyond`、最高到 N=40 的
`far_beyond`，以及更大数量和未见事件时刻同时出现的 `joint`。任务仍是同一
Generic-SHORT，奖励、动作、观察字段、生命周期、波次需求和 G5 模型均未改变。

固定 Luna-low 实验子代理以前台单次方式完成
`train（仅导入）→ evaluate → analyze`，三个阶段退出码均为 0，没有重启或恢复。

## 证据闭合

Project Manager 独立检查并重算：

- 三个 checkpoint 均为已关闭 G5 的 update-250 final，来源、正式授权 token、CPU
  条件和登记结果完全匹配；
- 18 个 cell 覆盖 3 个 replicate、3 个压力域和 deterministic/stochastic，共
  2,304 个 episode；
- 每个指标数组均有 128 个位于 `[0,1]` 的有限值，外部均值复算与存档最大差异为
  `6.67e-16`；
- 所有 cell 的模型参数最大差异严格为 0，optimizer steps 也严格为 0；
- 七个构造性控制 profile 的 utility 均为 1，roster trace、实际波次需求、成员事件、
  lifecycle 状态和 terminal destruction 全部精确；
- `operational_valid=true`、错误列表为空，独立 first-match 与存档分支一致。

## 正式结果

| 指标 | 正式值 | 登记门槛 |
|---|---:|---:|
| Moderate deterministic utility CI95 | [0.8590299, 0.9346962, 0.9864063] | LCB ≥ 0.90 |
| Far deterministic utility CI95 | [0.8089696, 0.8922767, 0.9669230] | LCB ≥ 0.90 |
| Joint deterministic utility CI95 | [0.8377266, 0.9154998, 0.9789795] | LCB ≥ 0.90 |
| Joint 各 replicate 均值 | [0.9789795, 0.8377266, 0.9297932] | 最低值 ≥ 0.85 |
| Joint stochastic utility 均值 | 0.8873766 | ≥ 0.80 |

首个 moderate 下界已经低于 0.90，因此首匹配结果为：

```text
NO_MODERATE_BEYOND_COUNT_G7
```

虽然 pooled 均值仍然较高，但 replicate 1 在 moderate、far、joint 中分别只有
0.8590、0.8090、0.8377，说明结果不是稳定的任意规模泛化。所有 deterministic
persistent score 仍为 1.0；损失完全来自 short-duty 分配，且随 N 增大而恶化。

## 对科学决策的影响

- G5/G6 在 N≤16 的可用结论保持不变；本轮没有重跑、调门槛或重新解释它们。
- 原始 `active embedding sum + log1p(N)/log1p(16)` 表示不再被视为可稳定外推到
  N=40 的算法。
- 失败不是成员生命周期或持久职责崩溃，而是大 roster 下短任务协调出现明显的
  seed 间分化。
- 现有证据同时允许两个解释：active embedding 求和随 N 放大，或者 count 特征越过
  1 后导致分布外输入；本轮不能把二者强行归因成唯一机制。
- 下一轮先做小型、非结论性的组件筛选，再冻结一个尺度归一化表示并重新训练；不会
  通过修改 G7 checkpoint、预算或门槛来“救”本轮失败。
- 异步技能周期、skill controller、EHC、内在奖励和比较优势继续冻结在 scope 外。

## 下一边界与迭代计数

G7 作为有效失败结果永久关闭。12 轮新链已经完成 3 轮，剩余 9 轮；下一边界是
`SCALE_NORMALIZED_OPEN_ROSTER_G8_DERIVATION`，目标是得到在同一动态 roster 任务上
对 N 更稳定的最小表示，而不是增加代码兼容层或扩大测试仪式。

```text
conclusion_bearing_iterations_consumed_total=8
new_chain_iterations_consumed=3
iterations_remaining=9
next_boundary=SCALE_NORMALIZED_OPEN_ROSTER_G8_DERIVATION
```
