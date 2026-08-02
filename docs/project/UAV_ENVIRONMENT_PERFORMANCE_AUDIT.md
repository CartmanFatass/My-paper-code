# UAV 环境性能审计与轻量实现边界

```text
status=PM_ACCEPTED_ENGINEERING_BOUNDARY
algorithm_iteration_environment=toy_default
uav_environment_role=promoted_candidate_validation_only
reviewed_uav_wrapper_commit=b125efd205e302666aea78b286d6857f8ecf9286
reviewed_s7_core_commit=a2908ba578b27f5b5ce783a659ea3cfedb0c8f09
formal_result_semantics_change=false
communication_snapshot_status=PM_ACCEPTED_ISOLATED_IMPLEMENTATION
communication_snapshot_benchmark_improvement_pct=20.3186
observation_view_reuse_status=PM_ACCEPTED_ISOLATED_IMPLEMENTATION
combined_wrapper_benchmark_improvement_pct=32.3707
graph_radio_reuse_status=PM_ACCEPTED_ISOLATED_IMPLEMENTATION
topology_copy_removal_status=PM_ACCEPTED_ISOLATED_IMPLEMENTATION
final_three_fast_paths_benchmark_improvement_pct=36.6627
discarded_base_view_status=PM_ACCEPTED_ISOLATED_IMPLEMENTATION
fdma_frontend_sinr_reuse_status=PM_ACCEPTED_ISOLATED_IMPLEMENTATION
intra_sinr_cache_validation_reuse_status=PM_ACCEPTED_ISOLATED_IMPLEMENTATION
latest_incremental_benchmark_improvement_pct=15.953851
directional_path_loss_reuse_status=PM_ACCEPTED_ISOLATED_IMPLEMENTATION
directional_path_loss_reuse_benchmark_improvement_pct=7.554426
directional_path_loss_reuse_exact_transition_and_rng=true
```

## 结论

S7/S1-like UAV 环境存在可观的纯执行冗余。首选修复不是简化通信
物理模型，也不是立即把公式改写为不同归约顺序的全向量化，而是：

1. 复用同一步已经生成的原始观测；
2. 控制源筛选不构造或跨进程传输未使用的完整 actor/critic view；
3. 将相同几何、用户位置和可用性状态下的路损、SINR 与定向链路容量
   缓存扩展到整个环境 step，而不是只在一次 widest-path 调用内生效。

这三项均为执行实现，不改变通信参数、路径损耗公式、FDMA、干扰、连接、
路由、吞吐、reward、observation 定义、RNG 或任何科学 gate。

算法发现仍默认使用 toy env。本文件只约束以后被 PM 晋升到 UAV 环境的
候选；UAV 性能工程不得阻塞 toy 算法迭代。

## 已观察的冗余

### 观测路径

一个低优先级、单进程、单线程、非正式诊断得到：

- steady learned step：`24` 次 `_get_observation`；最后 8 次与
  `scenario7.step()` 已返回的 raw observation 字节级相等；
- steady controller-shaped step：`32` 次；控制器实际只使用物理位置和
  active mask；
- 从 step 119 跨入 loss onset 120：`23` 次，且旧 raw 与跨界后观测不等。

因此只允许在 service mask 未变化时复用 raw；onset、rejoin、充电/失效导致
的可用性变化必须重算。

### 通信路径

- `_compute_interference_radius()` 只依赖固定通信参数，却在每次 SINR
  计算中重复执行对数和幂运算。
- 每步 8 UAV × 30 users 的 `sinr_matrix` 构造中，同一 UAV-user 路损既作为
  desired link 又被多个目标 UAV 当作 interference link 重算。
- UAV-UAV、UAV-BS 的路损、定向 SINR 和容量随后又被连接判定、widest-path、
  packet flow、吞吐/安全量和局部观测重复请求。
- 现有 `_routing_link_capacity_cache` 只覆盖一次
  `_compute_routing_paths_widest()`，函数返回即删除；同一步后续 packet flow
  因而重新计算同一条边。
- Scenario 7 已对 access SINR 做严格位置/可用性匹配后复用，证明项目已有
  正确的 fail-closed 缓存模式；backhaul 尚未获得等价范围的缓存。

## 最小实现顺序

### A. 观测与控制 fast path

- `current_view()` 接受同一步 raw observation，仅在 cache identity 匹配时
  做匿名化 repack，不再次调用基础观测构造。
- `step()` 返回 mask-change 事实；steady step 复用 raw，lifecycle 边界重算。
- controller worker 直接读取当前物理位置和 active mask。控制筛选响应只回传
  QoS、done、executed mask 与 next active mask，不构造完整 policy view。

### B. 整步通信快照

在 `_update_channel_state()` 后建立一个环境内部通信快照。identity 至少包含
精确副本或 generation-guarded 等价物：

- UAV、user、ground-BS positions；
- battery/service 不可用 mask；
- 会影响通信计算的冻结配置。

payload 包含一次性标量求值生成的 A2G、A2A、UAV-BS 路损，access SINR，
定向 backhaul SINR 与容量。第一版保留当前标量函数和干扰累加次序，只复用
结果，不改变浮点归约。

以下情况必须失效或绕过快照：用户/UAV 移动、service onset/rejoin、充电或
电量状态改变可用性、reset，以及 backhaul action guard 临时写入 proposed
position 的试探计算。试探位置只能走原标量 fallback，不能污染当前状态快照。

### C. 可选后续优化

只有 A/B 仍不足且 exact-equality evidence 已闭合时，才考虑批量距离矩阵或
全向量化通信公式。它们可能改变浮点归约顺序，不属于第一修复。

## Proof-sized 验收

1. 同 seed/action 的 baseline 与 fast path 在 steady、onset、rejoin、充电可用性
   变化和 proposed-position guard 上逐项完全一致：SINR、connections、UAV/BS
   adjacency、routing paths/capacities、packet metrics、QoS、reward、observation、
   state、RNG state。
2. 持久 instrumentation 只检查高风险边界；性能调用计数用测试内 spy，不写入
   正式 schema。
3. 运行一个短的单环境与一个小 vector-env nonformal benchmark。三次中位数
   至少改善 20% 才保留跨文件通信缓存；该性能门槛不是科学 result gate。
4. 只运行 UAV 环境聚焦测试和一个 bounded nonformal exercise；不启动正式
   训练，不运行广泛兼容套件。

## 实现与验收（2026-07-23）

本轮实现 A 类 observation/control 复用和 B 类整步通信快照。实现位于隔离分支
`codex/uav-env-fastpath`，不会改变正在运行的 G1 正式实验所绑定的源码。

- `uav_temp_loss_g1.py` 在 service mask 不变时直接复用 `scenario7.step()` 已生成的 raw
  observations 与 `next_state`，只执行匿名 owner repack；onset/rejoin 强制完整重建。
- controller worker 直接读取当前 active mask 与物理位置来生成动作，不再在动作前构造一个未使用的
  actor/critic view；step 后仍返回原有完整 view，因此不改变进程协议或估计量。
- `envs.pettingzoo.relay.routed_core` 为每次权威 `_update_channel_state()` 建立精确状态快照，复用 UAV-user
  路损、定向 link SINR 与 capacity；干扰半径和噪声线性值按其参数签名复用。
- 快照逐项校验 UAV/user/ground-BS 坐标、不可用 mask 和通信配置。位置试探、配置变化、
  服务退出或恢复均走原标量路径；试探结果不写入快照，恢复原状态后仍可命中原快照。
- 原标量公式、干扰源遍历与 `np.sum` 顺序保持不变；没有批量化或浮点归约重排。
- Scenario 7 的 graph potential、widest backhaul 与 end-to-end rate 复用同一步已经验证的
  不可用 mask、access SINR 和定向 backhaul SINR；保留原有标量 fallback 作为精确对照。
- 每步只保留一个只读的上一时刻 routing 外层快照；route records 由现有构造器整体替换，
  因此不再深拷贝其不可变旧值。训练/评估可视化仍消费每个 agent 的 `reward_info` topology，
  所以接口被保留，但 connections/routing snapshots 每步只构造一次并由所有 agent 共享；
  adapter 对权威 `state_info` 的输出也保持不变。
- `scenario7_energy_aware_test.py` 的 39 项聚焦测试全部通过；其中包含五步缓存/未缓存结构化
  证据与 RNG 完全一致、精确位置/配置/不可用 mask 失效，以及试探不污染检查。
- 临时离队环境聚焦测试文件的 16 项测试全部通过，包括 leave-before-action、S7-S1 保护配置、
  持久 vector worker 以及新增的 step/view 精确对照。
- 新增的四阶段稳态/onset/rejoin/稳态对照逐元素验证 observation、critic state、位置、reward、
  QoS 和 executed mask；复用版只在无 lifecycle 变化的阶段读取 step 已生成输入。

低优先级、CPU 单线程、单环境 S7-S1 短基准对缓存与显式禁用缓存各运行三组，每组 3 step，
交替运行顺序并逐组核对最终 SINR、connections 和 routing paths 完全一致：

```text
cached_seconds=[0.5609561, 0.5128088, 0.5559196]
uncached_seconds=[0.6888934, 0.7572745, 0.6976778]
cached_median_seconds=0.5559196
uncached_median_seconds=0.6976778
median_improvement=20.3186%
engineering_keep_threshold=20%
decision=KEEP
```

该门槛只决定是否保留性能实现，不产生或改变任何科学结论。

在通信快照已启用的条件下，单独开启 observation/view 复用的三组 3-step 中位耗时从
`0.6674345s` 降至 `0.6077971s`，额外改善 `8.9353%`。最终默认 fast path 与同时禁用两项
优化的标量路径进行三组配对，逐组核对完整 transition 证据完全一致：

```text
fast_seconds=[0.5265045, 0.5715126, 0.6938764]
scalar_seconds=[0.8957733, 0.8450665, 0.7667238]
fast_median_seconds=0.5715126
scalar_median_seconds=0.8450665
combined_median_improvement=32.3707%
```

第三组以六个独立 seed 各执行 3 step，并交替先后顺序，对默认 fast path 与同时禁用
communication snapshot、observation/view reuse、graph radio reuse 的同版本标量路径配对。
两侧仍共享安全的拓扑复制移除，所以该数字不把删除深拷贝的收益混入对照；每一步完整
transition 逐元素完全一致：

```text
fast_seconds=[0.1458677, 0.1832531, 0.1710015, 0.1837777, 0.1890255, 0.1469248]
scalar_seconds=[0.2414106, 0.3011241, 0.2428631, 0.2844198, 0.2975021, 0.2748946]
fast_median_seconds=0.177127300
scalar_median_seconds=0.279657200
combined_median_improvement=36.662707%
exact_transition_match=true
focused_tests=55_passed
```

同一 warmed steady step 的定向剖析用于定位而非 gate：Python 调用数从 `238374` 降至
`157745`，观测耗时从约 `0.260s` 降至约 `0.150s`；其中 `copy.deepcopy` 已从热点中消失，
graph potential 从约 `0.096s` 降至约 `0.025s`。这些剖析值只说明下一热点位置，验收仍由
上述 exact transition 对照和聚焦测试承担。

## 调度

原 G1 正式流水线已在两次前台两小时超时后以操作性 `ERROR` 终止，没有有效结果，
也未消耗结论性迭代。三项已验收 fast path 已集成到 `aggressive`；算法循环回到 toy env。
G1 不自动重跑，只有新的 toy 证据再次达到 PM promotion 边界时才考虑 heavy UAV 计算。

### 被拒绝的 worker 整段控制器 rollout

第二个 Scout 提议把 source-screen 控制器的逐步 pipe 往返融合到 worker 内。PM 实现了短暂
原型，并对 `constructive` 与 `no_reallocation` 都以逐步 worker 作为独立 oracle，QoS 轨迹和
最终 observation/state/位置逐元素一致。但交替顺序、四组、单环境 20-step 基准为：

```text
fused_median_seconds=1.065169700
sequential_median_seconds=1.074079000
median_improvement=0.829483%
exact_qos_and_final_view_match=true
decision=REJECT_AND_REMOVE
artifact=logs/nonformal_uav_controller_rollout_fastpath_20260724_pm1/benchmark.py
```

环境计算而非 pipe 往返仍占主导。该原型增加约百行 worker 协议却只改善 `0.83%`，因此未
进入源码或 Git。后续不要在没有新 profile 证据时重复这条优化。

## 第二批高复用优化（2026-07-24）

三个只读 Scout 分别检查了通信/物理热路径、跨 runner 重复基础设施和现有性能验收入口。
交叉证据选出了三个不改变模型或浮点归约顺序的执行修复：

1. Scenario 7 的 `reset()` / `step()` 以前先由父环境构造完整 observation/state，能量状态更新后又
   立即丢弃并重建。现在只对 Scenario 7 延迟父层 view materialization；最终公开 observation、state、
   info 字段顺序和 RNG 保持逐字节一致。普通父环境仍走原路径。
2. `_compute_uav_frontend_capacity()` 的 FDMA 分支以前对每个已连接用户重复计算同一 path loss、SINR
   和谱效率。现在保存首次计算的谱效率，只重新缩放分配带宽；每个用户每次容量计算只请求一次
   path loss/SINR。
3. 单次 `_compute_uav_to_user_sinr()` 内的 UAV/user/config/unavailable cache identity 原本会随每个
   干扰源重新全量验证。现在函数入口仍严格验证一次，然后只在该无状态突变的标量计算内部传递已验证
   cache；下一次顶层计算仍重新 fail-closed 验证，因此直接位置试探、配置变化和 service mask 变化的
   旧失效语义不变。

CPU 单线程、8 个独立 seed、每个 5 step、交替先后顺序的 S7-S1 对照，将这三项新实现与“保留此前
三项 fast path、仅恢复本批旧行为”的基线比较。每步完整 transition 和环境 RNG 逐项相同：

```text
fast_seconds=[0.414171600,0.328924000,0.378398300,0.361600600,0.348457300,0.322271000,0.342698300,0.349769700]
baseline_seconds=[0.425212100,0.412071300,0.421199600,0.392997500,0.418694900,0.393569900,0.406771100,0.431950600]
fast_median_seconds=0.349113500
baseline_median_seconds=0.415383100
incremental_median_improvement=15.953851%
exact_transition_and_rng_match=true
```

聚焦验收：`scenario7_energy_aware_test.py` 42 项全部通过；
`ha_ctse_process_uav_temp_loss_g1_test.py` 16 项全部通过。共享 runner 套件的 24 项中 23 项通过；唯一失败
发生在未修改的 checkpoint 篡改测试，其构造同时触发两个既有错误，当前实现先报
`terminal training completion marker conflicts`，而测试只接受更低优先级的
`duplicate or misdirected`。该错误优先级与本批环境数值路径无关，本批不改 runner 合同。

Scout 还识别了充电站最近邻、energy observation 矩阵和全局 generation token 候选。前两项主要影响
S2--S4，后者必须覆盖代码与测试中的直接数组写入；它们没有本批同等级的低风险证据，暂不实现。尤其
不以 generation token 取代现有跨顶层调用的 exact array/mask validation。

## 第三批定向路损复用（2026-07-24）

三个只读 Scout 分别检查了 UAV 通信、toy rollout/PPO 和跨 runner 基础设施。toy 轨迹在 CPU 上的
多数 `.to(cpu)` 本身不复制；autoregressive prefix、hidden recurrence 和逐步环境转移是真因果循环。
跨 arm 复用 persistent UAV worker 则会扩大 reset、RNG、cache 与生命周期证明面。两者均不在没有
新 profile 的情况下实现。

保留的单一改动扩展现有 exact-state communication snapshot，新增有向
`(tx_type, tx_idx, rx_type, rx_idx)` 路损 payload。`_compute_uav_to_uav_sinr()`、
`_get_link_capacity()` 和 backhaul 干扰链路现在共享同一步的 A2A/A2G/G2A 标量结果。所有路损公式、
发射功率、干扰源遍历与 `np.sum` 顺序保持不变；位置、配置、不可用 mask 和 reset 仍由原 snapshot
identity 失效。proposed-position guard 不调用索引式 helper，因此继续走原始标量路径且不会污染快照。

一条聚焦 spy 测试证明有向 link 序列结果逐元素相同且三类底层路损调用总数下降。Scenario 7 的 43
项测试与临时离队 UAV wrapper 的 16 项测试全部通过，其中原有五步 cached/scalar transition、state、
routing 和 RNG 精确对照继续通过。

CPU 单线程基准使用 8 个 seed、每 seed 5 step、3 次重复并交替先后顺序，只关闭本批新增缓存：

```text
samples_per_side=24
fast_median_seconds=0.344788850
scalar_median_seconds=0.372964150
incremental_median_improvement=7.554426%
exact_transition_and_rng_match=true
artifact=logs/nonformal_uav_directional_path_loss_cache_20260724_pm1/result.json
decision=KEEP
```

此前 `20%` 保留线针对需要跨文件扩大通信缓存接口的实现。本批是现有单文件 snapshot 的小型 payload
补全，在已经高度优化的基线上仍稳定减少约 `7.55%`，且没有增加 schema、持久遥测或兼容分支，因此
按研究仓库的敏捷小代码原则保留。批量距离矩阵、浮点归约重排与 worker 池跨 arm 复用继续冻结。

## 第四批共享 PPO 首次回放复用（2026-07-24）

第二轮 Scout 复核后拒绝继续合并 UAV frontend SINR 与 relaxed graph
capacity：前者使用严格 MCS/FDMA，后者是连续近似，合并会改变通信语义。
跨运行 ledger、metric mask 和 bootstrap 也没有足够收益，且会扩大 RNG、
resume 与失效证明面。

保留的唯一改动位于 toy/UAV 共用训练热路：一次 PPO update 原先先以
`no_grad` 完整 replay 做一致性审计，然后在任何参数变化前为第一个 PPO
pass 再做完全相同的 replay。现在第一次 replay 保留梯度图，同时在
`no_grad` 下从同一输出读取审计指标，并直接供第一个 pass 使用；第一次
`optimizer.step()` 后缓存立即失效，后续 pass、actor 后 critic、下一条轨迹
仍重新 replay。没有跨 step、episode、run 的状态缓存。

该规则应用于 G17、G18、G19、G28 与 UAV 的活跃优化器。调用计数测试证明
普通两-pass update 从 3 次 replay 降到 2 次；G19/G28 双优化器路径只删除
更新前的重复 replay，参数变化后的 critic replay 完整保留。五组聚焦测试
共 55 项通过。

CPU 单线程、10 对交替顺序的 G17 两-pass 微基准，以“额外执行一次无状态
preflight replay”精确模拟旧路径：

```text
old_median_seconds=1.117076900
optimized_median_seconds=0.890227250
median_improvement=20.307434%
metrics_exact_equal=true
maximum_parameter_error=0.0
artifact=logs/nonformal_shared_first_replay_reuse_20260724_pm1/result.json
decision=KEEP
```

该证据只验收执行去重，不改变 PPO、梯度、RNG、生命周期、replay tolerance
或任何科学结果。

## 第五批 Scout 复用收口（2026-07-24）

在 G31 toy 结果准备向 UAV 提升时，三个只读 Scout 复核了 UAV 通信前端、G1
控制/runner、以及跨 toy/UAV 的训练基础设施。没有发现新的高收益、低语义风险
复用点：严格 MCS/FDMA SINR 与 relaxed graph capacity 不是同一个物理量，合并会
改变通信模型；跨 run 的 metric、bootstrap 和 serialization 缓存收益低，却会扩大
RNG、resume 和失效证明面。它们均不实现。

本轮唯一源码修复是 G1 的 routing 实现：`FIXED_MASK_REC` 原先仅是 metadata，
与 OPEN 走同一个 anonymous-content order。现在 FIXED 使用 active-first 的物理槽位
顺序，OPEN 保持原有内容顺序。该项用于保证实验比较真实存在，不宣称性能收益。
UAV G1 core/runner 共 41 项测试通过。

因此性能优化在当前 profile 证据下收口：继续保留定向 A2A/A2G/G2A 路损快照
（增量中位改善 `7.554426%`）以及共享 PPO 首次梯度 replay（中位改善
`20.307434%`）；没有新 profile 前不继续堆叠 cache 或 worker 协议。

## C++ 批量环境后端边界（2026-07-25）

用户将长期 UAV 基础设施方向升级为 C++ 重构。只读 Scout 证明，最高收益边界不是把 Python
环境逐行翻译，而是一次调用处理完整 batch/step 的无状态 C++ 核心：融合位置积分、定向
A2A/A2G/G2A 路损、SINR/capacity 与连接矩阵，最终替换逐环境 Python step 和 Pipe 往返。

Python 继续唯一持有 RNG namespace/draw order、energy ledger、生命周期事件、reward/observation、
source evidence、PPO/checkpoint 和 analyzer。C++ 不创建 RNG、不持久化环境状态、不写 artifact。
逐步 Python oracle 必须验证生命周期、mask/event、通信、奖励、观测和 RNG；默认目标是 bitwise
一致，不能用放宽 tolerance 换速度。交替单线程微基准至少达到 `20%` 中位改善才保留首个跨文件
native slice。

完整边界位于 `docs/research/designs/UAV_CPP_BATCH_ENV_BACKEND.md`。本机当前缺少 MSVC、CMake、
Ninja 与独立 pybind11；PyTorch CPU 的 `cpp_extension` 可用。工具链安装等待当前正式 Python
进程终态后执行，避免安装器资源与重启行为干扰 iteration 23。该决策不修改在途源、不产生实验
证据，也不消耗结论性迭代。
