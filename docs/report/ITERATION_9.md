# 第 9 轮结论性迭代：prefix 归一化得到可用的 N≤40 动态 roster 算法

## 本轮科学问题与决策

第 8 轮表明，原 G5 checkpoint 在 N>16 时出现明显 seed 分化，短任务分配随规模恶化。
非正式八组合筛选随后发现，最小且表现最好的修复不是把所有表示都归一化，而是只把
自回归动作前缀从原始计数改为当前 roster 的比例：

```text
原输入=[IDLE_count, PERSIST_count, SHORT_count]
新输入=原输入/N
```

active embedding 仍求和，环境与模型仍使用原 `log1p` count 坐标，参数形状不变。本轮
从新随机种子训练三个模型，检验这个单一算法变化能否在 IID、held-out 和 N=40 压力域
同时达到绝对可用门槛。

## 环境、运行条件与证据预算

```text
source_commit=fcce714c296c55f3dcb5a0c0ee11090b393c26ba
run=logs/formal_open_roster_prefix_g8_cpu_20260723_fcce714_r1
backend=cpu
torch=2.7.0+cpu
torch_threads=1
formal=true
replicates=3
updates_per_replicate=250
environments_per_update=8
ppo_passes=4
evaluation_episodes_per_cell=128
evaluation_cells=33
bootstrap_repetitions=10000
```

训练仍只使用 G5 的三个 profile，最大训练 N=7。33 个评估 cell 包含三个 zero-checkpoint
joint 基线，以及三个 final checkpoint 在五个域的 deterministic/stochastic 结果。没有
恢复或改造 G5/G7 checkpoint。

固定 Luna-low 实验子代理以前台单次方式完成 `train → evaluate → analyze`，三个阶段
退出码均为 0，没有重启。

## 证据闭合

Project Manager 独立检查并重算：

- 三个 replicate 均完成 250 updates、1,000 optimizer steps，更新有限，lifecycle 精确，
  replay 最大误差严格为 0；
- 33 个 cell 清单完整，共 4,224 个 utility 值；每个数组恰有 128 个 `[0,1]` 有限值；
- 外部均值复算与存档最大差异为 `5.55e-16`；
- 所有评估 cell 的模型参数最大漂移严格为 0；
- 12 个 source-control profile 的构造性 utility 均为 1，原 count 特征在 N=40 时可达
  1.3107，但始终有限，任务与生命周期保持不变；
- `operational_valid=true`、错误列表为空，独立 first-match 与存档分支一致。

## 正式结果

| 指标 | 正式值 | 门槛 |
|---|---:|---:|
| IID deterministic utility CI95 | [0.9432373, 0.9705811, 1.0000000] | LCB ≥ 0.90 |
| Held-out deterministic utility CI95 | [0.9469604, 0.9669189, 1.0000000] | LCB ≥ 0.90 |
| Moderate deterministic utility CI95 | [0.9321289, 0.9544279, 0.9989648] | LCB ≥ 0.90 |
| Far deterministic utility CI95 | [0.9302979, 0.9531218, 0.9987087] | LCB ≥ 0.90 |
| Joint deterministic utility CI95 | [0.9299927, 0.9534098, 1.0000000] | LCB ≥ 0.90 |
| Joint 各 replicate 均值 | [0.9299927, 1.0000000, 0.9302368] | 最低值 ≥ 0.85 |
| Joint stochastic utility 均值 | 0.8994221 | ≥ 0.80 |
| Joint final-minus-zero CI95 | [0.1707176, 0.4429891, 0.6406480] | LCB > 0 |

全部门槛通过，登记结果为：

```text
USABLE_PREFIX_NORMALIZED_OPEN_ROSTER_G8
```

## 对科学决策的影响

- 项目现在有一个正式通过的动态 agent 数量算法测试版：一个共享、参数形状与 N 无关的
  recurrent policy，训练只见到 N≤7，却在登记任务上稳定迁移到 N=40。
- 仅归一化动作前缀就足以恢复这一范围的稳定性；active embedding 求和和超过 1 的原
  count 坐标仍然存在，因此它们不是本任务 N=40 可用性的必然阻碍。
- 这不等于证明 G7 的唯一失败原因就是 raw prefix。正式 G8 使用新训练 seeds，唯一归因
  仍需更强的匹配实验；当前目标是得到可用算法，不为唯一机制追加昂贵证明。
- G7 的失败保持有效：冻结的 raw-prefix checkpoint 不能被本轮成功倒改成通过。
- 成功范围只到已登记的 N=40、三次成员事件和 Generic-SHORT；尚未证明高频 churn、
  任意 N、比较优势、异步技能周期或 EHC 能力。

## 下一边界与迭代计数

G8 作为成功结果关闭，不重跑、不调门槛。12 轮新链已经完成 4 轮，剩余 8 轮。下一轮
冻结三个 G8 final checkpoint，不做 optimizer step，只增加 episode 内的成员加入、离开、
重入频率，并把部分事件放到任务负载附近，检验 lifecycle 编辑是否能真正组合。

```text
conclusion_bearing_iterations_consumed_total=9
new_chain_iterations_consumed=4
iterations_remaining=8
next_boundary=HIGH_FREQUENCY_ROSTER_CHURN_G9_DERIVATION
```
