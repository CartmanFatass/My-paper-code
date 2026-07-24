# 第 15 轮：原子 cohort 身份替换

## 本轮问题和决定

第 14 轮的随机 roster 过程把离开和加入放在不同事务中，策略会短暂观察到较小的中间
roster。本轮把大批 terminal leave 与等量 fresh join 合并成同一个 membership
transaction，并让总人数始终不变。这样 count、log-count 都无法提示变化，测试重点只剩
身份换代、终止 lifecycle 和新成员 recurrent state 冷启动。

正式结果为 `ROBUST_ATOMIC_COHORT_REPLACEMENT_G14`。三个规模域与稳定性门槛全部
通过，说明当前算法不仅能处理人数变化，也能在人数完全相同时承受显著成员身份替换。

## 算法、环境和预算

- 源码 commit：`b709fd5fc9cb423110d5edc24067e0030e05cbab`
- 正式目录：`logs/formal_atomic_replacement_g14_cpu_20260723_b709fd5_r1`
- 模型：G8 的三个 update-250 终态 checkpoint；optimizer steps 为 0
- 每个 episode：在 t=9、24、32、40、49、64 执行 6 次原子 replacement
- moderate：capacity 64，N=12–20，每次替换 2–6 人
- wide：capacity 144，N=32–48，每次替换 6–14 人
- ultra：capacity 192，N=64–80，每次替换 10–18 人
- 评估：3 replicates × 3 domains × deterministic/stochastic × 32 episodes，
  共 18 cells、576 个 utility 值
- 设备：AMD CPU、PyTorch 2.7.0+cpu、单线程

## 证据闭合

96 个 domain/episode profile 均唯一。每条 event signature 都包含正数个 terminally_left
和 joined key，二者数量严格相等，并且没有 temporary leave/rejoin；整条 roster size
序列保持常数。构造性 utility=1、wave demand、terminal 后永久失活与新成员零 hidden
state 全部闭合。

三个 checkpoint 拷贝差异为 0，18 个 cell 唯一，576 个值完整，模型状态精确不变。
独立复算 first-match 得到与 analyzer 相同的
`ROBUST_ATOMIC_COHORT_REPLACEMENT_G14`。

## 正式结果

| 原子替换域 | deterministic utility CI95 |
|---|---|
| moderate | [0.9230957, 0.9516602, 1.0000000] |
| wide | [0.9257813, 0.9525405, 0.9999556] |
| ultra | [0.9291992, 0.9541194, 0.9998093] |

Ultra 三个 replicate 均值为
`[0.9291992, 0.9998093, 0.9333496]`，最低为 `0.9291992`；stochastic mean 为
`0.8951629`。全部高于冻结门槛。

## 科学影响与限制

结果排除了“必须先看到人数下降、再看到人数恢复，策略才能适应新成员”的解释。即使
N 完全不变，当前 active-set recurrent policy 也能在每次 wave 前接受大批 cold-start
成员并保持任务可用。这强化了其作为动态 agent 数量/身份算法测试版的实际意义。

仍不能推出：

- 同一事务同时发生身份换代和大幅 count jump 时仍稳定；
- 任意 cohort 比例、容量或 N>80 都稳定；
- 任务关键相位之外的原子事件均安全；
- 异步技能周期或比较优势已被验证。

## 下一轮

下一边界为 `ATOMIC_COUNT_SHOCK_G15`：在同一事务中使用不等量的 terminal 和 fresh
join cohort，使 roster 在低/高人数间大幅跳变，同时发生身份冷启动。它组合了已分别
通过的 count transport 与 atomic replacement，是最终综合测试前最近的交互反例。

本轮消耗 1 次结论性迭代，剩余 2 次。
