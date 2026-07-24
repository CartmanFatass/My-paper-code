# 第 10 轮：高频动态成员变更鲁棒性

## 本轮科学问题与决策

第 9 轮已经得到可用的前缀归一化动态 roster 策略，但此前每个 episode
只有三次成员变更。本轮检验同一个策略在更频繁、更贴近任务负载的成员
变更下是否仍然可用。这里不重新训练，也不调整第 9 轮模型；因此结果直接
回答已学策略的迁移能力，而不是新训练预算能否补救失败。

正式结果为 `ROBUST_HIGH_FREQUENCY_CHURN_G9`。这支持当前算法在本轮规定的
八次成员编辑、重复临时离开/回归、新成员加入和终止离开下保持稳定。

## 算法、环境与运行条件

- 源码 commit：`ff7461fd2b0f3cfb7ad13a5f6f2730eb6bac3d99`
- 正式 artifact：
  `logs/formal_high_frequency_churn_g9_cpu_20260723_ff7461f_r1`
- 算法：第 9 轮的 active-sum、log-count、active-fraction-prefix 策略
- checkpoint：第 9 轮三个 update-250 终态，逐一精确导入
- 新训练：无；optimizer steps 为 0
- 环境：Generic-SHORT，horizon 80，容量 20，最大同时活跃成员数不超过 16
- 三类 roster：重复离开/回归、负载边界附近变更、混合高频变更
- 每类均有 8 个成员编辑事件
- 正式评估：3 个 replicate × 3 个 domain × deterministic/stochastic，共
  18 cells；每 cell 128 episodes
- 运行设备：本机 AMD CPU，PyTorch 2.7.0+cpu，单线程；没有 CUDA 对照或回退

## 证据闭合

训练、评估和分析三个命令均正常退出。3 个导入 checkpoint 的模型状态与
来源完全相同；18 个评估 cell 的模型状态均未变化。2,304 个 utility 值、
episode 数量和 cell 唯一性完整，序列化均值可独立复算。

三种环境的构造性控制器都达到 utility 1.0；成员数量轨迹、实际 wave 需求、
八次事件数量以及生命周期隐藏状态冻结/恢复检查全部通过。Analyzer 报告
`operational_valid=true` 且无错误。我按冻结的 first-match 顺序独立复算，
仍得到 `ROBUST_HIGH_FREQUENCY_CHURN_G9`。

预启动时曾有一个子代理工具在约 1.3 秒后超时，未生成任何 artifact，也没有
残留进程。随后在全新的非正式 run root 上仅修正前台工具超时，算法、参数、
预算与门槛完全不变；这不是科学迭代或实验重跑。

## 正式结果

| 域 | deterministic utility CI95 |
|---|---|
| repeated rejoin | [0.9309692, 0.9556274, 1.0000000] |
| load proximal | [0.9294434, 0.9545492, 1.0000000] |
| mixed churn | [0.9299316, 0.9543050, 1.0000000] |

Mixed-churn 的三个 replicate 均值为
`[0.9299316, 1.0000000, 0.9329834]`，最差值为 `0.9299316`；stochastic mean
为 `0.9099933`。它们分别通过预先冻结的 0.90、0.85 和 0.80 门槛。

## 对科学判断的影响

本轮排除了“第 9 轮策略只记住一次缩减—扩张—缩减模板”和“隐藏状态只能
正确冻结/恢复一次”这两个最直接反例。当前可用测试版不仅能处理未见过的
成员数量和事件时间，也能处理本轮定义的重复、负载邻近成员变更。

但本轮不证明：

- 任意事件次数或任意事件时刻都稳定；
- 活跃成员数超过 16 时仍能承受同样高频 churn；
- 第 8 轮的 N<=40 规模成功与本轮高频 churn 成功会自动组合；
- 异步技能周期、技能选择或 EHC 已得到解决；这些仍冻结在当前主线之外；
- 当前算法相对其他算法具有优势。本链的目标仍是先获得可用算法。

## 下一轮

下一边界是 `SCALE_CHURN_COMPOSITION_G10`：继续冻结同一批第 9 轮 checkpoint，
零训练地把较大活跃成员数与八次高频 roster 变更放进同一 episode。它用于
检验两个单独成功是否真正组合；第 10 轮消耗 1 次结论性迭代，授权链剩余
7 次。
