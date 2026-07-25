# 第 23 轮算法迭代报告

## 本轮科学问题

本轮没有先比较 learned policy，而是先检验冻结的 UAV 充电轮换 G2 是否具备可解释算法差异的来源条件：在 8 架物理 UAV、两个单容量充电站以及运行中 `ACTIVE / CHARGE_ABSENT / TERMINAL` 服务 roster 变化下，掌握完整冻结规则的 constructive 轮换控制器，能否既保持足够高的绝对服务效用，又显著优于不主动轮换的控制器。

只有这两个条件同时成立，后续 `FIXED_MASK_REC` 与 `PREFIX_NORMALIZED_OPEN_ROSTER` 的差异才可以解释为生命周期/roster 算法效应。

## 环境、运行条件与预算

- 场景：S7-S3 风格的 8 架物理 UAV、2 个充电站、每站同时服务 1 架 UAV，episode 长度 1,500 步。
- 生命周期：服务侧 `ACTIVE / CHARGE_ABSENT / TERMINAL`；离开服务的 UAV 仍按冻结的物理、排队和充电规则演化，电量达到 0.80 后在下一 pre-action 边界重新加入。
- 来源 profile：`IID`、`LOW_ENERGY`、`SYNCHRONIZED_PRESSURE`。
- 控制对：`CONSTRUCTIVE_CHARGE_ROTATION` 与 `NO_PROACTIVE_ROTATION`；共享同一环境、初始能量排列与随机性。
- 来源证据：3 个 replicate、每个 profile/控制器 128 个 episode，共 2,304 行 source-control 记录；10,000 次配对层次 bootstrap。
- 若来源通过，原计划训练 2 个 learned arm，每个 replicate 128 updates、8 个并行环境、4 次 PPO pass；本轮来源未通过，因此这些训练没有启动。
- 平台：本机 AMD CPU，`torch 2.7.0+cpu`，单线程；没有 CUDA、后端混用或 CPU/CUDA 对比。
- 正式源码提交：`8350263ef73b15f10b6d2bcac2583687aad7cade`。
- 正式运行目录：`logs/formal_uav_charge_rotation_g2_cpu_20260724_8350263_r1`。

正式过程曾按同一 source commit、授权 token、run root 和不可变分块身份续行。最终 `train -> evaluate -> analyze` 均以退出码 0 结束；续行没有改变 seed、预算、阈值或添加重复样本。

## 证据闭合

冻结 validator 通过。`formal=true`、`conclusion_bearing=true`、`operational_valid=true`、`operational_errors=[]`。2,304 行来源记录及其 complete/binding 引用闭合；训练清单状态为 `TRAIN_SKIPPED_SOURCE_NON_IDENTIFIABLE`，learned training row、checkpoint 和 evaluation row 均为 0。分析器明确记录 `learned_gates_evaluated=false`。

PM 使用冻结的 first-match 规则复核：在 operational-valid 后，`source_identifiable=false` 必须先于所有 learned access/gain 分支返回来源不可识别。分析文件和独立 validator 均得到相同分支。

## 注册结果

首匹配结果为：

`SOURCE_NON_IDENTIFIABLE_UAV_CHARGE_ROTATION_G2`

constructive 控制器的绝对效用 `Phi` 为：

| Profile | mean | CI95 |
|---|---:|---:|
| IID | 0.24667 | `[0.21189, 0.27981]` |
| LOW_ENERGY | 0.09827 | `[0.05005, 0.14200]` |
| SYNCHRONIZED_PRESSURE | 0.11206 | `[0.07483, 0.14770]` |

三者均远低于冻结的绝对可行性线 `0.90`，所以 `constructive_feasibility_pass=false`。

另一方面，`constructive - no_rotation` 的 CI95 下界分别为 `0.79105`、`0.90834` 和 `0.83339`，因此 `load_bearing_pass=true`：主动轮换确实比完全不轮换重要，但当前 constructive 本身仍不能提供可用服务。其运行中还出现 11 次 cutoff 与 8 次 depletion，导致完整支持条件不通过。

## 对科学决策的影响

本轮把两个问题分开了：充电轮换是负载承载机制，但冻结的 source/controller 对不是一个可用于比较 learned 算法的可行 benchmark。若直接训练，任一 learned arm 的高低都可能主要反映“是否偶然修正了一个低质量控制器/来源”，不能归因于动态 roster 表示或 G31 的 return-to-go 信用规则。

因此永久关闭这一精确 G2 来源，不降低 `0.90`、不增强 constructive、不改变能量 profile、seed、预算或结果顺序，也不补跑 learned arms。此前 G31 在 G17/G18 成对 toy 上的正式可用结论保持不变；本轮没有初始化 G31 或其 comparator，所以没有产生 UAV 算法优劣证据。

两次连续 UAV source-first 尝试都在 learned training 前关闭，说明当前最高收益不是继续设计重型 UAV 控制对，而是回到轻量 toy，把可用连续 roster 算法尚未覆盖的数量泛化边界分离清楚，再仅把有希望且来源可识别的方向晋级 UAV。

## 本轮不支持的结论

- 不支持“G31 在 UAV 上失败”或“固定 mask 优于 open roster”；两个 learned arm 均未训练。
- 不支持“充电轮换不重要”；它相对不轮换的优势很大，失败的是绝对可行性和完整支持。
- 不支持通过调低阈值、改控制器、加预算或重跑来救回这一精确来源。
- 不支持把 C++ UAV 内核的性能结果解释为本轮科学证据；该内核在正式进程结束后才编译，并未参与此 run。
- 不支持对突增通信需求、临时失灵或任意 UAV 数量作新的结论。

## 下一边界

下一步为 `CAPACITY_INVARIANT_CONTINUOUS_ROSTER_G32_DERIVATION`。它在现有 toy 环境中先区分两种能力：当前 G31 已证明同一固定容量内 active agent 数量会在 episode 中变化；尚未证明同一 checkpoint 可跨不同最大 slot 容量工作。零计算推导将检查 raw padded mask、容量归一化坐标和 critic 参数形状是否仍绑定最大容量，并冻结一个最小、环境无关的 discriminator。只有 bounded toy 证据有希望时才进入下一次正式迭代或 UAV 晋级。

第 23 轮消耗 1 次有效结论性迭代；十轮自动研究链剩余 4 次。
