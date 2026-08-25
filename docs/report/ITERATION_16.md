# 第 16 轮：原子身份替换与人数冲击组合

## 本轮科学问题与决策

第 12 轮已经证明人数可迁移到 N=80，第 15 轮已经证明在人数不变时可以承受同一事务中的
大批身份替换，但这两项结果并不自动保证二者同时发生时仍然稳定。本轮让每个 membership
事务同时终止一批旧成员、加入一批从未出现的新成员，并让两批人数严格不等，从而使 active
roster 在低人数和高人数区间之间立即跳变。

正式结果为 `ROBUST_ATOMIC_COUNT_SHOCK_G15`。三个规模域及稳定性门槛全部通过，说明当前
prefix-normalized recurrent policy 能在同一个时间步同时吸收人数归一化变化和大量新成员的
hidden-state 冷启动。

## 算法、环境和预算

- 源码 commit：`68fa0d6e3f45596e108d858fb7c7a4d1df8e95fe`
- 正式目录：`logs/formal_atomic_count_shock_g15_cpu_20260723_68fa0d6_r1`
- 模型：G8 的 3 个 update-250 终态 checkpoint；optimizer steps 为 0
- 每个 episode：在 t=9、24、32、40、49、64 执行 6 次原子人数冲击
- moderate：capacity 128，低区间 12–16，高区间 24–32
- wide：capacity 192，低区间 28–32，高区间 52–64
- ultra：capacity 224，低区间 40–48，高区间 72–80
- 评估：3 replicates × 3 domains × deterministic/stochastic × 24 episodes，
  共 18 cells、432 个 utility 值
- 设备：AMD CPU、PyTorch 2.7.0+cpu、单线程

## 证据闭合

72 个 profile 全部唯一，共包含 432 个原子事务。每个事务都同时具有正数个 terminal leave
和 fresh join，二者数量严格不等；没有 temporary leave、rejoin 或人数区间错误。roster
轨迹、wave demand、构造性 utility=1、终止成员永久失活和新成员零 hidden state 均通过。

3 个 checkpoint 的复制误差为 0，18 个 evaluation cell 的模型状态精确不变，正式证据
来源、CPU 环境、授权 token、cell 和 utility 清单完整。独立 first-match 复算与 analyzer
一致，得到 `ROBUST_ATOMIC_COUNT_SHOCK_G15`。

## 正式结果

| 组合压力域 | deterministic utility CI95 |
|---|---|
| moderate | [0.9188949, 0.9496082, 0.9992658] |
| wide | [0.9166667, 0.9487374, 0.9995326] |
| ultra | [0.9225260, 0.9517546, 0.9994696] |

Ultra 三个 replicate 均值为
`[0.9225260, 0.9994696, 0.9332682]`，最低为 `0.9225260`；stochastic mean
为 `0.8936155`。全部高于冻结门槛。

## 对算法判断的影响与限制

本轮排除了“人数迁移与身份冷启动只能分别成立、二者组合会破坏策略”的最近反例。至此，
当前测试版已分别或组合覆盖 N=80、随机 episode 过程、高频 churn、槽位布局变化、等量原子
替换和不等量原子人数冲击，已经形成相对稳定的动态 agent 数量算法基线。

仍不能推出任意 roster 生成过程、任意容量、N>80、异步技能周期或相对其他算法的优势。
最后一轮不会扩大这些结论，而是用全新种子把已支持的不同 roster 机制放入同一部署混合，
检查当前稳定结论是否依赖各轮独立固定的压力分布。

本轮消耗 1 次结论性迭代，剩余 1 次。
