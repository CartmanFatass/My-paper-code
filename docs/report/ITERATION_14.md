# 第 14 轮：逐 episode 随机成员过程

## 本轮问题和决定

第 13 轮把可用规模扩展到 N=80，但每个 domain 的所有 episode 仍重复同一条人工 count
schedule。本轮检验一个更直接的替代解释：策略是否只是适应了少数固定成员轨迹，而非
真正能处理新的 roster 过程。

正式结果为 `ROBUST_RANDOMIZED_ROSTER_PROCESS_G13`。每个正式 episode 都使用不同的
初始人数与成员键、事件时间、受影响成员和批量幅度，三个随机过程域及稳定性门槛全部
通过。因此，当前算法的可用性不再只依赖 G9–G12 的几条固定 schedule。

## 算法、环境和预算

- 源码 commit：`e3ffabb5e7d6207546c035552f7ed678af841e17`
- 正式目录：`logs/formal_random_roster_g13_cpu_20260723_e3ffabb_r1`
- 模型：G8 的三个 update-250 终态 checkpoint；新训练为 0
- 表示：active embedding sum、log-count、active-fraction prefix
- 每个 episode：三组 temporary leave→rejoin→terminal leave→fresh join，共 12 events
- 随机 moderate：capacity 48，初始 N=12–32，声明范围 N=4–40
- 随机 wide：capacity 96，初始 N=24–56，声明范围 N=8–64
- 随机 ultra：capacity 96，初始 N=40–72，声明范围 N=12–80
- 评估：3 replicates × 3 domains × deterministic/stochastic × 48 episodes，
  共 18 cells、864 个 utility 值
- 设备：AMD CPU、PyTorch 2.7.0+cpu、单线程

## 证据闭合

训练导入、评估、分析均正常退出。144 个 domain/episode source-control key 和 profile
name 均唯一；每条记录包含并可复算完整 event signature、roster schedule、wave demand
和构造性结果。四类成员操作全部出现，12-event 计数、utility=1 与 lifecycle 状态控制
全部通过。

18 个行为单元唯一完整，864 个数组值闭合，三个 checkpoint 拷贝差异为 0，所有模型
状态精确不变。独立按 random-moderate→random-wide→random-ultra→稳定性→成功的
first-match 顺序复算，得到相同结果。

## 正式结果

| 随机过程域 | deterministic utility CI95 |
|---|---|
| moderate | [0.9249674, 0.9501330, 0.9994876] |
| wide | [0.9270833, 0.9518954, 0.9995663] |
| ultra | [0.9283854, 0.9527840, 0.9996279] |

Ultra 三个 replicate 均值为
`[0.9283854, 0.9996279, 0.9303385]`，最低为 `0.9283854`；stochastic mean 为
`0.8892955`。全部通过冻结门槛。

## 科学影响与限制

本轮排除了“固定 count schedule 记忆”这一直接反例。当前测试版已经具备：动态参数
形状、N≤80 的零训练迁移、槽位布局不变性、高频 churn、规模×churn 组合，以及逐
episode 随机 roster 过程上的绝对可用性。这已经构成较稳定的动态 agent 数量算法
测试版，而非只是一组接口单元测试。

仍不能推出：

- 任意 roster 随机过程或任意 N 都稳定；
- 同一事务中的大规模终止与冷启动替换已被覆盖；
- 事件发生在未注册的任务关键相位时仍可用；
- 异步技能周期、技能控制器或比较优势已建立。

## 下一轮

G13 把 terminal leave 与 fresh join 放在相邻但不同的事务中。下一边界为
`ATOMIC_COHORT_REPLACEMENT_G14`：在同一 membership transaction 中随机终止一批
成员并加入同等数量的新成员，使 N 保持不变但身份和 recurrent state 大幅换代。这会
直接测试冷启动 cohort 与原子 roster edit，而不是重复普通 count 变化。

本轮消耗 1 次结论性迭代，剩余 3 次。
