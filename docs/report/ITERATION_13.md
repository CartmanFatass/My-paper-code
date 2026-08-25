# 第 13 轮：动态 roster 零训练扩展到 N=80

## 本轮问题和决定

第 12 轮证明了算法不依赖低编号、连续槽位或接近活跃人数的 padding，但已有正式规模
证据仍止于 N=40。本轮不重新训练模型，只把八次成员变更的活跃规模提升到 48、64 和
80，检验第 9 轮学到的前缀归一化策略是否真正跨越原有规模范围。

正式结果为 `ROBUST_ULTRA_SCALE_OPEN_ROSTER_G12`。三个规模域及跨 seed/stochastic
稳定性门槛全部通过。当前动态 agent 数量算法测试版的明确可用边界因此从 N≤40 扩展到
本轮注册的 N≤80。

## 算法、环境和预算

- 源码 commit：`21046fcf9a67cd7503266284c02896ae85dafd62`
- 正式目录：`logs/formal_ultra_scale_g12_cpu_20260723_21046fc_r1`
- 模型：G8 的三个 update-250 终态 checkpoint
- 新训练：无，optimizer steps 为 0
- 表示：active embedding sum、log-count、active-fraction autoregressive prefix
- 环境：Generic-SHORT，horizon 80；三个 profile 的最大 N 为 48、64、80，均有八次
  temporary leave/rejoin/join/terminal leave 组合
- 容量：64、80、96
- 评估：3 replicates × 3 domains × deterministic/stochastic，共 18 cells；
  每 cell 64 episodes，共 1,152 个 utility 值
- 设备：AMD CPU、PyTorch 2.7.0+cpu、单线程；无 CUDA 比较或回退

## 证据闭合

检查点导入、评估、分析均正常退出。三个 checkpoint 文件存在，拷贝最大差异均为 0；
18 个 cell 唯一且完整，所有模型状态保持精确不变，每个 persistent、short 和 utility
数组均为 64 项且序列化均值可复算。

三个 source profile 都通过精确 roster schedule、实际 wave demand、八次事件事务、
lifecycle 隐状态冻结/恢复和构造性 utility=1 控制。独立按 edge→far→ultra→稳定性→
成功的 first-match 顺序复算，得到与 analyzer 相同的分支。

## 正式结果

| 最大活跃 N | deterministic utility CI95 |
|---|---|
| 48 | [0.9251709, 0.9513819, 0.9996535] |
| 64 | [0.9230957, 0.9499752, 0.9987292] |
| 80 | [0.9270020, 0.9523218, 0.9997878] |

N=80 的三个 replicate 均值为
`[0.9270020, 0.9997878, 0.9301758]`，最低值为 `0.9270020`；stochastic mean 为
`0.8973560`。所有值都通过预先冻结的绝对可用性与稳定性门槛。

## 科学影响与限制

结果说明 G8 的关键修正——对 autoregressive action prefix 使用活跃比例——不仅修复
了 N=16 之后的退化，而且在不重新训练的情况下迁移到了训练规模数倍的 N=80。结合
槽位不变性结果，当前实现已经是一个可使用、参数形状不依赖 agent 数、能处理 episode
内动态加入/离开并跨较大规模迁移的算法测试版。

仍不能推出：

- 任意 N 或 N>80 都稳定；
- 任意随机的成员事件时序、方向和幅度都稳定；
- 当前三条人工 profile 之外的 roster 过程已被覆盖；
- 异步技能周期、技能控制器、EHC 或比较优势已得到支持。

## 下一轮

继续单纯提高 N 的信息增益已经下降。更直接的反例是“策略只适应了少数人工固定的
count schedule”。下一边界为 `RANDOMIZED_ROSTER_PROCESS_G13`：每个 episode 独立
生成合法的成员事件时间、方向、规模和 roster 轨迹，同时保持任务、构造性可解性和
冻结 checkpoint 不变。

本轮消耗 1 次结论性迭代，剩余 4 次。
