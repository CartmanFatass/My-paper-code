# 第 7 轮结论性迭代：冻结 checkpoint 可零样本迁移到 N=16 与新事件时刻

## 本轮科学问题与决策

第 6 轮已经得到可用的动态 roster 测试版，但训练最大活跃数为 7，held-out 最大为
9，而且所有 membership 事件都发生在 20/40/60。本轮不训练新模型，而是冻结三个
G5 final checkpoint，分别检验：

- `count_scale`：事件时刻不变，活跃数扩展到 16；
- `event_time`：数量保持在原 held-out 范围，事件改到未见的安全时刻；
- `joint`：更大数量与新事件时刻同时出现。

这样能在改算法之前区分“只会邻近 count 插值”“记住固定事件时钟”和“二者不能组合”
三个反例。N 最大仍为 16，因此完全保留 G5 的 `log1p(N)/log1p(16)` 观察语义。

## 环境、运行条件与证据预算

```text
source_commit=909ced01ee58e2690fd7cd0ec2da214e99203af5
run=logs/formal_open_roster_zero_shot_g6_cpu_20260723_909ced0_r1
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
```

固定 Luna-low 实验子代理以前台单次方式完成
`train(仅导入) → evaluate → analyze`，三个阶段退出码均为 0，没有重启。所谓
`train` 阶段只验证并复制 G5 checkpoint，没有调用 optimizer。

## 证据闭合

Project Manager 独立检查并重算：

- 三个导入 checkpoint 均来自已关闭的 G5，严格加载为 update 250，G5 source、正式
  authorization token、CPU 条件与登记分支全部匹配；
- 18 个 cell 恰好覆盖 3 个 replicate、3 个 stress domain 与 deterministic/
  stochastic，共 2,304 个 episode；
- 每个指标数组恰有 128 个有限且位于 `[0,1]` 的值，外部均值复算与 NumPy 存档的
  最大差异仅约 `1.23e-15`；
- 所有 cell 的 model-state 最大差异严格为 0，optimizer steps 也严格为 0；
- 八个 source-control profile 的构造性 utility 均为 1，roster trace、实际 wave
  demand、membership event、lifecycle 状态和 terminal destruction 全部精确；
- `operational_valid=true`、错误列表为空，独立 first-match 与存档分支相同。

## 正式结果

| 指标 | 正式值 |
|---|---:|
| Count-scale deterministic utility CI95 | [0.9294811, 0.9728004, 0.9990977] |
| Event-time deterministic utility CI95 | [0.9854642, 0.9951547, 1.0000000] |
| Joint deterministic utility CI95 | [0.9358802, 0.9763486, 0.9999524] |
| Joint 各 replicate 均值 | [0.9999524, 0.9358802, 0.9932133] |
| Joint 最低 replicate 均值 | 0.9358802 |
| Joint stochastic utility 均值 | 0.9501188 |

三类 deterministic CI95 下界均高于 0.90；最差 joint replicate 高于 0.85；
joint stochastic 均值高于 0.80。登记分支为：

```text
ROBUST_ZERO_SHOT_OPEN_ROSTER_G6
```

## 对科学决策的影响

- G5 的成功不只是从训练 N=7 到邻近 N=8/9 的局部插值；冻结 checkpoint 在 N=16
  仍达到 count-scale 均值 0.9728。
- 未见 membership 事件时刻几乎不影响能力，event-time 均值为 0.9952，因此固定
  20/40/60 时钟不是当前成功的必要捷径。
- 更大 N 与新事件时刻可以组合，joint 均值为 0.9763，且没有任何参数更新。
- count-scale/joint 的下界低于 event-time，下一个更可能的薄弱点是数值尺度，而不是
  lifecycle 事件时间。
- 结果恰好停在代码声明的 N=16 count-feature 上限，不能外推为任意 N，也不能证明
  active embedding 求和在更大 roster 上仍稳定。
- 异步技能周期、skill controller、EHC 和算法比较优势仍不在本轮 scope。

## 下一边界与迭代计数

G6 作为独立成功结果关闭，不重跑、不调门槛。用户授权的 12 轮新链已完成 2 轮，尚余
10 轮。第 8 轮先进行 `BEYOND_DECLARED_COUNT_G7_DERIVATION`：继续冻结 G5
checkpoint，定义 N>16 的分段零训练 stress。只有观察到尺度失败后，才引入 mean/count
归一化等算法修正，避免把诊断与修复混在同一轮。

```text
conclusion_bearing_iterations_consumed_total=7
new_chain_iterations_consumed=2
iterations_remaining=10
next_boundary=BEYOND_DECLARED_COUNT_G7_DERIVATION
```
