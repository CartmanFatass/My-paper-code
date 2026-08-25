# 第 11 轮：大规模成员数与高频变更的组合

## 本轮问题和决定

第 9 轮证明同一策略可迁移到活跃成员数 40，第 10 轮证明它可处理八次高频
成员变更，但这两个结论来自不同 episode。本轮把大规模 roster 与高频 churn
放进同一个 episode，检验两种鲁棒性是否会互相干扰。

正式结果为 `ROBUST_SCALE_CHURN_COMPOSITION_G10`。因此，对本轮注册的 12–40
活跃成员数和八次事件组合，当前前缀归一化策略仍是可用的。

## 算法、环境和预算

- 源码 commit：`e66a202673ea91711d9d122d1807e9597e3dba43`
- 正式目录：`logs/formal_scale_churn_g10_cpu_20260723_e66a202_r1`
- 模型：第 9 轮三个 update-250 终态 checkpoint
- 新训练：无，optimizer steps 为 0
- 表示：active embedding sum、log-count、active-fraction autoregressive prefix
- 环境：Generic-SHORT，horizon 80，容量 32 或 48
- profile：moderate scale churn（N=12–24）、far scale churn（N=16–40）、
  mixed churn（N=12–40）；每个 profile 8 次成员编辑
- 评估：3 replicates × 3 domains × deterministic/stochastic，共 18 cells；
  每 cell 128 episodes
- 设备：AMD CPU、PyTorch 2.7.0+cpu、单线程，无 CUDA 比较或回退

## 证据闭合

训练导入、评估、分析均正常退出。3 个 checkpoint 拷贝完全一致，18 个 cell
唯一且完整，共 2,304 个 utility 值；所有 cell 都保持模型状态不变，数组长度
和序列化均值可复算。三个构造性控制器均达到 utility 1.0，大容量成员轨迹、
wave 需求、事件数量和临时离开期间的隐藏状态冻结/恢复全部通过。

Analyzer 报告 `operational_valid=true`、无错误。我按原有 moderate→far→mixed
→stability→success 顺序独立复算，得到相同分支。

预启动的第一次非正式运行在任何 artifact 产生前暴露了 thin runner 的项目根
导入错误。修复仅为 CLI `sys.path` 初始化，随后全部聚焦测试和新的非正式
full path 通过；科学参数与门槛未改变，这个操作错误不消耗迭代。

## 正式结果

| 域 | deterministic utility CI95 |
|---|---|
| moderate scale churn | [0.9296265, 0.9544881, 1.0000000] |
| far scale churn | [0.9245605, 0.9515991, 1.0000000] |
| mixed churn | [0.9272461, 0.9527860, 0.9994103] |

Mixed 三个 replicate 均值为
`[0.9272461, 0.9994103, 0.9317017]`，最差为 `0.9272461`；stochastic mean
为 `0.8963305`。全部通过冻结门槛。

## 科学影响与限制

本轮排除了“规模成功与 churn 成功只能分别成立、组合后会崩溃”的直接反例。
到目前为止，同一套 checkpoint 已覆盖：未见成员数、未见事件时间、N=40、
八次高频变更，以及 N=40 与八次变更的组合。这已经是一个较稳定、可运行的
动态 agent 数量算法测试版。

仍不能推出：

- 任意 N 或 N>40 都可用；
- 任意数量、任意密度的成员事件都稳定；
- 生命周期 key 的编号、连续性和 padding 容量完全无关；
- 异步技能周期、技能选择或 EHC 已得到支持；
- 相对其他算法具有比较优势。

## 下一轮

下一边界为 `SLOT_LAYOUT_INVARIANCE_G11`。它冻结现有 checkpoint，在相同逻辑
episode 上成对改变 lifecycle key 的排列、稀疏位置和 padding 容量，检验当前
成功是否依赖低编号连续 slot。这比继续提高 N 更直接地检验“解绑固定 agent
数量/布局”。本轮消耗 1 次结论性迭代，剩余 6 次。
