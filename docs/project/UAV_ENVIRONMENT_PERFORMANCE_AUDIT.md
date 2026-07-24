# UAV 环境性能审计与轻量实现边界

```text
status=PM_ACCEPTED_ENGINEERING_BOUNDARY
algorithm_iteration_environment=toy_default
uav_environment_role=promoted_candidate_validation_only
reviewed_uav_wrapper_commit=b125efd205e302666aea78b286d6857f8ecf9286
reviewed_s7_core_commit=a2908ba578b27f5b5ce783a659ea3cfedb0c8f09
formal_result_semantics_change=false
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

## 调度

当前正在执行的 G1 正式流水线继续使用其冻结源码，终态前不得修改它会加载的
环境或 runner。之后算法循环回到 toy env。A/B fast path 在下一次 PM 决定将
toy-supported 候选晋升到 heavy UAV 环境之前实现并验收即可。
