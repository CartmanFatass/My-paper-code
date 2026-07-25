# 第 24 轮算法迭代报告

## 本轮科学问题

此前 G31 已证明：在一个预先配置好的最大容量内，实际 active agent 数量可在 episode 中加入、离开、重入并变化；但 critic 参数形状和部分输入仍可能绑定最大 slot 数。本轮 G32 检验更严格的问题：只在容量 8 上训练得到的同一 checkpoint，能否不重训、无评估优化步骤地直接运行在容量 6、8 和 12 的动态 roster 环境中。

同时，本轮设置了一个精确 padding 对照：容量 8 与容量 12 运行完全相同的 `4→3→6→5` active-member 过程，容量 12 仅多四个永不 active 的槽位。若算法真正与最大容量解绑，所有共同 active 成员的 observation、value、action、reward、hidden state 和生命周期都应完全一致。

## 环境、运行条件与预算

- 环境：不含 UAV 物理量的连续服务 toy；训练容量为 8，评估容量为 6、8、12。
- roster：训练包含三种动态过程；评估包含训练过程、容量 6/12 held-out 过程以及容量 8/12 精确 padding 配对。
- 算法：G31 的 realized-future-tail + direction-balanced actor 更新，配合 G32 的固定宽度 critic state 和 `log1p(active_count)`；最大容量不进入参数形状或环境坐标归一化。
- 训练：3 个 replicate；每个 replicate 100 次 fast update、100 次 return-to-go update、8 个并行环境、2 次 PPO pass。
- 评估：每个注册 cell 128 个 episode；共 30 个 cell、3,840 个 utility 观测；10,000 次层次 bootstrap。
- checkpoint：每个 replicate 的 zero/final checkpoint，共 6 个；只在容量 8 训练，容量 6/12 严格加载同一状态字典，评估 optimizer step 为 0。
- 平台：本机 AMD CPU，`torch 2.7.0+cpu`，单线程；无 CUDA、后端混合或跨后端比较。
- 正式源码提交：`fbce3609b11353634d1b4acb20cb27372de40bf2`。
- 正式运行目录：`logs/formal_runtime_capacity_g32_cpu_20260725_fbce360_r1`。

## 证据闭合

固定实验操作员自然完成 `train → evaluate → analyze`，三个命令退出码均为 0。三个 manifest/result 文件存在并绑定相同 source commit、正式授权 token、CPU 后端与单线程条件。分析器返回 `status=COMPLETE`、`formal=true`、`operational_valid=true`、`operational_errors=[]`。

所有训练更新有限；三个 replicate 均有非零参数漂移和非零 actor 行为变化；生命周期、replay、checkpoint、seed、cell inventory 和状态不变性检查全部通过。评估前后模型状态完全一致，证明 held-out 结果没有通过额外训练获得。

PM 使用冻结的 first-match 函数重新计算 predicate inputs，所得分支与分析文件完全一致。

## 注册结果

首匹配结果为：

`USABLE_RUNTIME_CAPACITY_G32`

| 指标 | 正式结果 | 冻结门槛 |
|---|---:|---:|
| 容量 8 utility CI95 | `[0.95025, 0.95520, 0.95910]` | LCB `≥0.90` |
| 容量 8 learned-gain CI95 | `[0.34652, 0.54171, 0.66433]` | LCB `>0` |
| 容量 6 utility CI95 | `[0.93757, 0.94355, 0.94802]` | LCB `≥0.90` |
| 容量 12 utility CI95 | `[0.94832, 0.94981, 0.95128]` | LCB `≥0.90` |
| held-out gain CI95 | `[0.36581, 0.53720, 0.64719]` | LCB `>0` |
| 最差 held-out replicate | `0.94284` | `≥0.85` |
| held-out stochastic mean | `0.87591` | `≥0.80` |

三个 mapping diagnostic 的相关系数均高于 `0.9898`，MAE 均低于 `0.0166`。容量 8/12 padding 配对中，observation、value、action、reward 和 hidden 的最大误差全部为精确 `0.0`，生命周期完全相等，inactive padding 也为精确零。

## 对科学决策的影响

本轮把“动态 agent 数量”分成了两个层次，并对其中两个已完成层次给出正式支持：

1. G31：在固定最大容量内，active agent 数量可在运行中变化；
2. G32：同一 checkpoint 可跨不同最大容量 6/8/12 使用，无需重训或评估期优化。

因此，当前算法已经有一个较稳定的、与固定 agent 数量和固定 checkpoint 容量解绑的 toy 测试版。成功来自结构性解绑：critic 参数不接收 raw padded mask，环境输入不再除以最大容量，生命周期状态按成员所有权管理；不是通过扩大模型、改变奖励或调低阈值获得。

但 G32 的每个环境实例在一条 trajectory 内仍使用固定 tensor 宽度。它没有证明运行到一半时把容器从容量 6 扩到 12、再缩到 8，同时继续携带共同成员的 recurrent hidden state。这个更窄的边界是下一项最有信息量的算法问题。

## 本轮不支持的结论

- 不支持“任意容量均可零样本泛化”；正式证据只覆盖注册的 6/8/12 family。
- 不支持“单条 trajectory 内 tensor 容量可实时扩缩”；当前只在不同固定容量实例之间复用 checkpoint。
- 不支持 UAV 通信、能量、充电轮换或临时失灵场景中的算法优势；两项既有 UAV source 仍因 source non-identifiable 关闭。
- 不支持 G32 对 G31 的独立性能增益；G32 的主张是容量解绑和保持可用性，而不是超越 G31。
- 不支持改变奖励、阈值、seed、预算或结果优先级来扩大结论。

## 下一边界

用户已要求将另一科研项目中的“双审计”经验吸收进 HMASD。下一步先重规划为 Pro 辅助、PM 单一验收的两阶段断言安全流程：冻结前由 Pro 审科学设计是否可判别、是否遗漏承载性决定；实现集成后由同一类 Pro 直接读取远程固定提交，审代码是否实例化科学契约以及是否引入替代解释。它们不是两个审批人，也不审风格、覆盖率或兼容性。

新流程落地后的第一个候选为 `LIVE_RUNTIME_CAPACITY_REBIND_CONTINUOUS_ROSTER_G33_DERIVATION`：先零计算推导单条 trajectory 内 runtime tensor 容量扩缩时，member-key、hidden state、RNG、packing 与 action factorization 必须满足的条件，再决定是否值得原型和正式迭代。

第 24 轮消耗 1 次有效结论性迭代；二十轮自动研究链剩余 13 次。
