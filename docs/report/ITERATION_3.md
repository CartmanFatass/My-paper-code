# 第 3 轮结论性迭代：G2 TEAM_REC 足够

## 本轮科学问题与运行前决策

本轮检验：当 creator 的 per-member recurrent state 已因终止离开而删除时，
event-held state 是否能比 persistent TEAM_REC 更好地把私有 bit 传递给匿名
successor。主估计量冻结为 `G_team=U_EHC-U_TEAM_REC`，DUM 提供链路空控制，
访问、source identifiability 和 first-match 优先级均在运行前冻结。

## 实验环境与证据闭合

```text
source_commit=9a72dc6a0f776aa3e6dfa96d86f5265f12717ace
run=logs/formal_cross_lifecycle_handoff_g2_cpu_20260723_9a72dc6_r1
backend=cpu
torch=2.7.0+cpu
torch_threads=1
formal=true
replicates=5
updates_per_arm_replicate=160
optimizer_steps_per_arm_replicate=640
```

固定的 Luna-low experiment operator 在前台完成 train/evaluate/analyze，三阶段
退出码均为 0。Project Manager 重新验证了 15 个最终 checkpoint、60 个评估
文件（15,360 条记录）、640 条 held-out snapshot 因果审计及 source controls；
源码、后端和线程合同一致，无临时或 latest 残留。

## 登记结果

| 指标 | 均值 | CI95 |
|---|---:|---:|
| TEAM_REC utility | 1.0 | [1.0, 1.0] |
| DUM utility | 0.5 | [0.5, 0.5] |
| EHC utility | 1.0 | [1.0, 1.0] |
| `G_team` | 0.0 | [0.0, 0.0] |
| `G_link` | 0.5 | [0.5, 0.5] |
| mark-flip action TV | 1.0 | [1.0, 1.0] |
| mark-flip utility drop | 1.0 | [1.0, 1.0] |

EHC 相对 DUM 学到了完全有效、可干预的跨生命周期链路；但是 TEAM_REC 同样
达到 1.0，主估计量精确为 0。first-match 第 6 步因此登记：

```text
TEAM_REC_SUFFICIENT_HANDOFF_G2
```

## 对科学决策的影响

- 单个全局 bit 的生命周期 handoff 仍可完全约化为一个 persistent team state；
  “跨生命周期持久化”本身不足以证明 event-indexed 机制的优势。
- 结果没有否定 EHC 链路：`G_link=0.5` 且两个干预后果均为 1.0，说明链路真实
  参与行为，只是没有优于 TEAM_REC。
- 2/5 个 EHC replicate 学到 `m=-b`，其余学到 `m=b`，但所有行为指标都完美。
  因而原始 `P(m=b)` 受任意标签符号影响，未来必须改用每 replicate 内标签
  置换不变的自然 mediation 指标。
- C-EHC 进一步收窄为“可变数量、事件索引的 standing commitment roster”；
  C-COORD 成为当前更贴近最终 MARL 目标的方向，即异步编辑时的互补分配。
- 精确 G2 永久关闭，不重跑、不调参、不改名、不救援。
- 本轮消耗第 3 次结论性迭代，当前剩余 2 次。

## 本轮不能支持的结论

本轮不能证明 EHC 普遍无用，也不能证明任意有限 recurrence 都不需要结构化
外部状态。它只表明这个单记录、被动 bit-reproduction source 无法区分 EHC 与
TEAM_REC；`G_link` 的正结果也不能越过 first-match 顺序改写主结论。

## 下一边界

执行 `ASYNC_COMMITMENT_ROSTER_G3_INFORMATION_GATE`。它是零训练、非正式、
不消耗迭代的 source gate：同时存在多个生命周期所有的 standing commitment，
每次只有部分匿名成员编辑，外部价值取决于 retained/new commitments 的互补性；
ROSTER_EDITOR 与 TEAM_REC_ORACLE 都必须作为构造性解释，独立/no-roster 与
shuffled-roster 作为 null。只有 gate 通过后才决定是否冻结可学习的 G3 合同。
