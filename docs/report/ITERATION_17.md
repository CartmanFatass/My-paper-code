# 第 17 轮：异质动态 roster 部署混合与整链结论

## 本轮科学问题与决策

此前各轮分别证明了串行随机 membership 编辑、人数不变的原子身份替换，以及同时包含身份
替换和人数冲击的原子事务。最后一个风险是：策略可能只在这些机制被分成独立实验包时稳定，
而部署时如果每个 episode 都可能来自不同过程族，性能会下降。

本轮用全新种子，在每个规模域内平衡混合三种过程，每种各 12 个 profile。正式结果为
`USABLE_DYNAMIC_ROSTER_DEPLOYMENT_G16`。这完成了当前 12 轮自动研究链，并将 G8 的
prefix-normalized direct recurrent policy 接受为一个可用的动态 agent 数量算法测试版。

## 算法、环境和预算

- 源码 commit：`1745ab9c155e7a58ba0689380f3a77866b3503b5`
- 正式目录：`logs/formal_deployment_mixture_g16_cpu_20260723_1745ab9_r1`
- 模型：G8 的 3 个 update-250 终态 checkpoint；optimizer steps 为 0
- 三种 episode 模式：serial random、atomic equal、atomic shock
- 每个规模域：36 个 episode，每种模式各 12 个
- capacity：moderate 128、wide 192、ultra 224；有效人数上界分别为 40、64、80
- 评估：3 replicates × 3 domains × deterministic/stochastic × 36 episodes，
  共 18 cells、648 个 utility 值
- 设备：AMD CPU、PyTorch 2.7.0+cpu、单线程

## 证据闭合

108 个 source profile 全部唯一。每个规模域均精确包含 12 个 serial-random、12 个
atomic-equal 和 12 个 atomic-shock profile。事件数只允许 6 或 12，三种模式各自的操作、
人数和 lifecycle 约束均无错误；四种 membership 操作、构造性 utility=1、roster 轨迹、
wave demand 和 cold-start/terminal 状态全部闭合。

3 个 checkpoint 复制误差为 0，18 个 evaluation cell 的模型状态精确不变。正式来源、
CPU 环境、授权 token、648 个效用值和 first-match 分支均独立复核通过。

## 正式结果

| 部署混合域 | deterministic utility CI95 |
|---|---|
| moderate | [0.9253538, 0.9520621, 0.9998431] |
| wide | [0.9231771, 0.9513158, 0.9995639] |
| ultra | [0.9251302, 0.9525272, 0.9997258] |

Ultra 三个 replicate 均值为
`[0.9251302, 0.9997258, 0.9327257]`，最低为 `0.9251302`；stochastic mean
为 `0.8928564`。全部高于冻结门槛。

## 整条研究链对算法决策的影响

当前可用测试版不再绑定固定 agent 数量，也不要求预先知道 episode 将采用哪种 roster
变化机制。其核心是：对 active set 做求和聚合，保留 log1p 人数坐标，并把 actor 的动作前缀
改为 active-fraction 表示，同时让 recurrent hidden state 由成员 lifecycle 独立拥有。

12 轮中最重要的科学修正来自第 7–8 轮：原始 raw-prefix 表示在超出训练人数后确实失败，
而 active-fraction prefix 的小改动修复了尺度外推；后续各轮则逐步排除了高频 churn、布局、
N=80、随机过程、原子替换和组合冲击等最近反例。最终异质混合确认这些支持并非依赖独立
实验包。

## 结论边界

可以声称：已有一个在注册环境族中、N≤80、可处理运行时成员变化的可用算法测试版。

不能声称：对任意 roster 过程或 N>80 普遍鲁棒；异步技能周期、内在奖励、样本效率和相对
其他算法的优势仍未研究。它们需要新的研究目标，而不是当前结果的自动外推。

本轮消耗最后 1 次结论性迭代；本链剩余 0 次，自动推进在完整闭合处结束。
