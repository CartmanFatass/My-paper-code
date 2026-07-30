# env 迁移到 C++ —— 现状

## 用户意图

**尽可能将 env 迁移到 C++ 以加速计算。**

参考点（用户提供）：用户在另一个项目中使用同一套 C++ 方案，获得约 **60×** 加速。
该方案在用户处经长期实验验证，是成熟稳定的做法。模板即 `cpp/`（未跟踪）里的
toy 后端：Python 保留状态、生命周期与失败关闭边界，C++ 只做批量确定性算术。

## 已落地

| 阶段 | 内容 | 提交 |
|---|---|---|
| 纯 Python 优化（无需工具链） | `_compute_distance` 标量化、getattr 默认值移除、mcs_table 按身份缓存 | `cd6471b3`，实测 1.434× |
| 通信内核整体迁移（阶段 1） | 每步一次原生调用产出全部通信矩阵 | 本提交，实测 **1.61×**（叠加在 1.43× 之上） |

阶段 1 的内容：`step_communication_batch`（`ha_ctse_process/native/uav_geometry_backend.cpp`，
加载器 `ha_ctse_process/uav_cpp_backend.py`）一次算出 10 个输出——access/air/base
路径损耗、user/uav-uav/uav-bs 干扰加噪声（dBm）矩阵、bs→uav 干扰加噪声向量
（与基站索引无关，源码已验证）、三个链路容量矩阵。`_refresh_step_communication_cache`
一次预填；`_cached_link_sinr`、`_compute_uav_to_user_sinr`、`_compute_uav_to_uav_sinr`、
`_get_link_capacity` 命中矩阵直读。失效判定完全留在 Python
（`_current_step_communication_cache` 原样），步内 `noise_power` 变更照旧被侦测。
旧内核的位置积分接口（`next_uav_positions`/速度/掩码）已删除，Python 独占运动。

**开关不变：`env.use_native_geometry`，默认 False。** 位相同已端到端证明，
但采纳它进入任何正式运行仍是一次显式决定。

## 验证状态（本轮，全部由 PM 亲自复核）

| 项目 | 结果 |
|---|---|
| 25 步 rollout 位摘要（HEAD 基线 = 改后 flag 关 = 改后 flag 开） | 三者一致：`76318efca6174873001c067afa9189319c8e9cabddea1c6af380967462799489` |
| oracle：10 个输出逐元素位比较（fdma 开/关、双 UAV 同位退化例、1-ULP 负例） | `tests/uav_cpp_backend_oracle_test.py`，6 passed |
| 集成 + scenario7 + distance 位测试 | 65 passed（四个文件合跑） |
| 同进程三臂交错基准（8 块 × 10 步 + null 对照） | **1.608×**（70.87 → 44.07 ms/step），null 噪声底 1.082× |

摘要口径：每步哈希 `sinr_matrix`、`connections`、`user_serving_uav`、`uav_positions`、
`user_positions`、`uav_battery_ratios` 的原始字节。脚本已入库（见下）。

## 位相同的三个关键约束（改动内核前必读）

- `np.sum` 对 float64 列表在长度 ≤7 时与从左到右顺序求和位相同，**长度 8 起分歧**
  （实测 787/2000 不一致）。内核干扰求和按 k 升序顺序累加，因此
  `_prefill_communication_natively` 在 `n_uavs > 8` 时失败关闭地拒绝。
- `(dx*dx+dy*dy)+dz*dz` 的结合顺序不可动（重结合实测 6761/60008 不一致）。
- `a-(a-b)` 不保证还原 `b`：uav-uav 对角元（1e-6 距离钳位，自链路）经
  rx−sinr 往返会差 1 ULP。对角元无任何消费者；oracle 测试为此直接从干扰和推导
  参考值，注释里有实测数字。

## 单步耗时分布（迁移前 cProfile，flag 关时仍适用）

`_get_link_capacity` 29.9% / `_find_widest_path_to_ground_bs` 26.5% /
`_cached_link_sinr` 18.8% / `_update_channel_state` 15.5% / `_compute_sinr` 13.6% /
`_get_observation` 12.6%。子树嵌套，占比不可相加。阶段 1 把前五项的算术
全部搬进原生调用；剩余 Python 大头是 `_get_observation` 的组装、
`_simulate_packet_flow`、指标/奖励计算，以及 240 对/步的 `_compute_sinr`
Python 调用外壳（现在每次只做两次矩阵索引 + 减法）。

## 下一阶段候选（按迁移后 flag 开的 cProfile，25 步 1.411s）

1. **`_current_step_communication_cache` 本身：新的第一名。** 26,400 次 / 25 步
   = 1,056 次/步，0.616s 累积（≈44%）——算术搬走后，剩下的主导成本是每次访问
   重建 config 签名 + 4 个 `np.array_equal`（81,750 次调用，0.388s）。这是纯
   开销、零物理。风险也最高：步内试探性配置变更（`noise_power` 中途改动的守卫
   测试）正是这套重验证存在的理由。任何"脏标记/信任窗口扩宽"方案都必须先清点
   步内每一个可能改动签名字段或位置数组的写点，再谈缓存判定的降价。
2. `_get_observation`（0.293s 累积，含 `_graph_service_potential` 0.277s——
   scenario7 奖励整形的松弛求解器占了观测大头）：纯组装 + 独立求解器，
   勿与路由 Dijkstra 合并。
3. `_update_channel_state` 的 240 对循环：向量化 sinr_matrix 填充
   （`tx_power − access_pl − user_ipn` 逐元素即位相同的表达式等价本轮已论证；
   未实施，且受 scenario7 不可用掩码语义约束）。
4. `_simulate_packet_flow` 与指标计算。

Dijkstra 本体保留 Python（heapq 平局语义即路径身份），其内层
`_get_link_capacity` 已是 O(1) 矩阵读；路由阶段剩余的 0.49s 里大部分其实是
上面第 1 条的重验证成本，不是图搜索本身。

## 环境与工具

**Python 解释器**：`C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe`
（`python`/`py` 是 Microsoft Store 桩，不可用。）

**建 env 必须走** `audit_d7_s_event_aligned.build_pinned_env` 并显式传
`user_world_seed`。直接构造 + `reset(seed=...)` 不能确定用户世界。

**测量脚本（已入库，不再随 session 消失）**：

| 脚本 | 用途 |
|---|---|
| `scripts/env_bit_digest.py <repo_root> [--native]` | 25 步 rollout 位摘要 |
| `scripts/env_bench_interleaved.py <repo_root>` | 同进程交错三臂基准 + null 对照 |

## 其他事实

- `cpp/` 是未跟踪目录：UAV 后端旧副本 + 用户参考的 toy 后端模板。加载器不读它。
- 主检出里 `scripts/audit_d7_s_event_aligned.py` 有另一会话的在途改动，本线未触碰。
- `docs/project/CURRENT_WORK.md` 的 `active_pm_session` 由另一条线持有；本文件未改动它。
