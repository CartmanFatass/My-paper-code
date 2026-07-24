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
- `scenario_base.py` 为每次权威 `_update_channel_state()` 建立精确状态快照，复用 UAV-user
  路损、定向 link SINR 与 capacity；干扰半径和噪声线性值按其参数签名复用。
- 快照逐项校验 UAV/user/ground-BS 坐标、不可用 mask 和通信配置。位置试探、配置变化、
  服务退出或恢复均走原标量路径；试探结果不写入快照，恢复原状态后仍可命中原快照。
- 原标量公式、干扰源遍历与 `np.sum` 顺序保持不变；没有批量化或浮点归约重排。
- `scenario7_energy_aware_test.py` 的 37 项聚焦测试全部通过；其中包含五步缓存/未缓存结构化
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

## 调度

当前正在执行的 G1 正式流水线继续使用其冻结源码，终态前不得修改它会加载的
环境或 runner。之后算法循环回到 toy env。A/B fast path 在下一次 PM 决定将
toy-supported 候选晋升到 heavy UAV 环境之前实现并验收即可。
