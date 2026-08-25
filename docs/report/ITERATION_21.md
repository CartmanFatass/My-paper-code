# 第 21 轮算法迭代报告

## 本轮科学问题

本轮检验 G31 的核心判断：在保留 G30 的全 actor、双通道梯度方向单位化与等权合成规则时，把后继通道的目标从学习得到的一步价值估计，替换为“排除当前奖励的、已实现折扣未来回报”，能否在全新随机种子下同时保住即时动态 roster 能力，并稳定学会延迟电池轮换与突发服务分配。

## 算法与实验环境

- 算法：`RETURN_TO_GO_DIRECTION_BALANCED_G31`。
- 训练目标：后继 actor/baseline 使用 detached realized future tail；slow critic 仍拟合包含当前奖励的完整折扣回报。
- 环境：G17 连续即时服务 roster 与 G18 延迟电池 roster 两个 toy 环境；本轮没有运行 UAV 环境。
- 平台：本机 AMD CPU，`torch 2.7.0+cpu`，单线程；Python 为 `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`。
- 三个全新 replicate，不恢复 G30 或 G31 screen checkpoint。
- G17 每个 replicate 使用 `100` 次 fast 更新和 `100` 次 return-to-go 更新；G18 使用 `100/300` 次；每次 8 个环境、2 次 PPO pass。
- G17 每个 domain、每个 replicate 评估 128 个 episode；G18 每个 replicate 评估 3 种 slot layout；bootstrap 10,000 次。
- 正式源码提交：`03bedada8b4aaa83d39d5b25e80d14505fa01b22`。
- 运行目录：`logs/formal_return_to_go_g31_cpu_20260724_03bedad_r1`。

## 证据闭合

训练、评估与分析均成功完成。正式证据包含 6 个训练结果、12 个 zero/final checkpoint 和 21 个评估 cell。源码、正式 token、配置、随机种子、阶段次数和 CPU 单线程身份完全一致。所有 replay 误差、梯度方向合成误差和终止 future-tail 误差均为 0，return-to-go 目标有限；生命周期、inactive action、参数所有权、exact-zero residual 与每次 Adam 只前进一步也全部通过。PM 再次运行冻结 artifact 验证器得到空错误集，并用冻结的首匹配函数独立重算出与文件相同的结果分支。

## 注册结果

首匹配结果为：

`USABLE_RETURN_TO_GO_DIRECTION_BALANCED_G31`

G17 即时动态 roster 全部通过：

- IID utility CI95：`[0.95739, 0.96056, 0.96530]`；
- held-out utility CI95：`[0.95136, 0.95660, 0.96190]`；
- gain CI95：`[0.38030, 0.48865, 0.60404]`；
- 最差单 episode：`0.92510`；
- effort/mix 最低相关系数：`0.98530/0.99472`；
- effort/mix 最大 MAE：`0.01903/0.01179`。

G18 延迟服务也全部通过：

- utility CI95：`[0.97776, 0.98367, 0.98683]`；
- 相对 zero checkpoint 的 gain CI95：`[0.16144, 0.23739, 0.27685]`；
- spike utility CI95：`[0.95969, 0.96843, 0.98508]`；
- rotating effort share CI95：`[0.96224, 0.97091, 0.98685]`；
- 最低 replicate utility：`0.97761`。

## 对科学决策的影响

本轮首次得到一个在相同模型与训练预算下，同时通过即时和延迟动态 roster 两类 toy 环境的统一算法版本。G31 在三个 fresh seed 上稳定保住 G17，并把 G30 未通过的 G18 spike utility 下界从 `0.87611` 提升到 `0.95969`。这说明 G30 的剩余问题并非必须依赖 UAV 电池字段或人为 spike 标记；至少在当前成对来源上，后继 credit 的目标估计是可分离且关键的算法因素。

因此，G31 已满足“先获得一个可用算法测试版”的阶段目标，并符合从 toy 晋级重型 UAV 验证的条件。下一步不再继续调 toy seed、预算或门槛，而是检查相同环境无关 credit 规则能否在 UAV 的突增通信、充电轮换和临时脱离/失灵条件下保持作用。

## 本轮不支持的结论

- 尚未证明 G31 在 UAV 通信、运动、充电站几何或真实部署上有效。
- 尚未证明未来 team reward 已被严格归因到某一个 agent 的当前动作。
- 尚未排除更长、更随机回报序列中的 Monte Carlo 方差问题。
- 尚未证明对任意 agent 数量、任意生命周期或任意任务分布普适。
- 不允许通过更换 seed、增加预算、降低门槛或重跑 G31 来扩大本轮结论。

## 下一边界

下一步为 `RETURN_TO_GO_DIRECTION_BALANCED_G31_UAV_PROMOTION_DEFINITION`：只设计并实现把已冻结 G31 credit/梯度规则接入现有 UAV 动态服务 roster 证据源的最小边界，先做 proof-sized 非正式运行，再决定是否消耗下一轮正式迭代。当前自动研究授权剩余 6 轮。
