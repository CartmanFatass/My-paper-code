# 交接：env 迁移到 C++

## 用户意图

**尽可能将 env 迁移到 C++ 以加速计算。**

参考点（用户提供）：用户在另一个项目中使用同一套 C++ 方案，获得约 **60×** 加速。
该方案在用户处经长期实验验证，是成熟稳定的做法。

---

## 未提交的工作树改动

两个文件，均为纯 Python 优化，**未提交**：

- `envs/pettingzoo/scenario_base.py`
- `envs/pettingzoo/scenario7_energy_aware.py`

内容：

1. `_compute_distance`：`np.sqrt(np.sum((pos1-pos2)**2))` → `np.float64(math.sqrt(dx*dx+dy*dy+dz*dz))`
2. `_is_uav_unavailable` / `_is_uav_motion_disabled` / `_is_uav_in_limp_home`：移除即时求值的
   `getattr(self, ..., np.ones(...))` 默认值（属性恒存在，旧写法每次调用都分配并丢弃）
3. `_communication_config_signature`：按对象身份缓存 `mcs_table` 元组；12 个标量字段保持每次实时读取

diff 备份：`<scratchpad>/optimizations.patch`

---

## 验证状态

| 项目 | 结果 |
|---|---|
| 25 步 rollout 位摘要（改动前 vs 改动后） | 一致：`33a269148dc13b01c38e79f655e2c89a29856d53b33b3517a6b6b8fa15bc8211` |
| 同摘要在 `use_native_geometry` 开/关 | 一致 |
| `native_geometry_integration_test` + `uav_cpp_backend_oracle_test` + `scenario7_energy_aware_test` | 60 passed |
| 全量 `tests/` | 超 600s 未跑完，**未确认** |

摘要口径：每步哈希 `sinr_matrix`、`connections`、`user_serving_uav`、`uav_positions`、
`user_positions`、`uav_battery_ratios` 的原始字节（不做舍入）。

---

## 实测速度

同进程内三臂交错、每步翻转顺序、带 null 对照臂（本机同一份代码在不同测量块间有 ~3×
热降频摆动，跨进程或分块测量不可用）。

| 改动 | 加速 | null 噪声底 |
|---|---|---|
| 上述三项 Python 优化 | **1.434×**（native 开）/ **1.440×**（native 关） | 0.012 / 0.015 |
| 矩阵化改动（已提交 `dab23b0a`） | 1.052× | 0.019 |

---

## 单步耗时分布（cProfile，native 开，累积占比）

| 子树 | cum% | calls/step |
|---|---|---|
| `_get_link_capacity` | 29.9% | 528 |
| `_find_widest_path_to_ground_bs` | 26.5% | 8 |
| `_cached_link_sinr` | 18.8% | 248 |
| `_update_channel_state` | 15.5% | 1 |
| `_compute_sinr` | 13.6% | 240 |
| `_get_observation` | 12.6% | 8 |
| `_compute_uav_to_user_sinr` | 11.8% | 240 |
| `_compute_link_sinr` | 8.1% | 72 |
| `_compute_air_to_air_path_loss` | 4.4% | 616 |
| `_compute_interference_radius` | 0.4% | 312 |

子树互相嵌套，占比**不可相加**。

`_find_widest_path_to_ground_bs`（`scenario_base.py:5142`）是 heapq 驱动的最宽路径
Dijkstra，内层对每个邻居调用 `_get_link_capacity`。

---

## C++ 现状

| 项 | 值 |
|---|---|
| 源文件 | `ha_ctse_process/native/uav_geometry_backend.cpp`（已跟踪） |
| 加载器 | `ha_ctse_process/uav_cpp_backend.py`，`torch.utils.cpp_extension` JIT 编译 |
| 编译标志 | Windows：`/O2 /std:c++17 /EHsc /fp:precise`；其他：`-O3 -std=c++17 -ffp-contract=off -fno-fast-math` |
| 开关 | `env.use_native_geometry`，默认 `False` |
| 位相同验证 | `tests/uav_cpp_backend_oracle_test.py`，312/312 元素，max_ulp 0 |

核返回 4 个矩阵：

| 输出 | 形状 | 当前是否被消费 |
|---|---|---|
| `next_uav_positions` | batch×uav×3 | 否 |
| `access_path_loss` | batch×uav×user | **是** → `cache["user_path_loss_matrix"]`，由 `_cached_user_path_loss` 索引 |
| `air_path_loss` | batch×uav×uav | 否 |
| `base_path_loss` | batch×uav×bs | 否 |

其他事实：

- 加载器对全部 4 个输出各做一次 `np.isfinite().all()` 全矩阵扫描（`uav_cpp_backend.py:341`）
- `cpp/` 是 `ha_ctse_process/native/` 的**未跟踪同内容副本**，加载器不读它
- `tests/native_geometry_integration_test.py::test_default_is_off_without_anyone_setting_it`
  断言开关默认关闭

---

## 已知约束

- `tests/scenario7_energy_aware_test.py::test_step_link_cache_reuses_exact_state_and_bypasses_trial_inputs`
  在**步内**修改 `noise_power` 并要求缓存检测到 —— 这个环境会在步内评估试探性配置。
  对 `_communication_config_signature` 做整签名按步 memo 会使该测试变红（已实测）。
- `_compute_distance` 返回 `np.float64` 而非 Python `float`：距离为 0 可达（air-to-air 环中
  uav 对自身），`float` 除零抛 `ZeroDivisionError`，`np.float64` 给 `inf`。
- `np.sum` 对 3 元素 float64 左结合求和，`math.sqrt(dx*dx+dy*dy+dz*dz)` 与之位相同：
  实测 60008/60008 一致；重结合对照 `dx*dx+(dy*dy+dz*dz)` 差异 6761/60008（证明该比较有分辨力）。
  **不要改动这组括号。**
- `docs/research/cdc/EVIDENCE_NOTES/20260730_STEP2_USER_VELOCITIES_WRITERS.md` 记录：
  IEEE 754 要求 `sqrt` 正确舍入，不要求 `sin`/`cos`。

---

## 环境与工具

**Python 解释器**：`C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe`
`python` / `py` 不在 PATH；Bash 工具下 `python` 指向 Microsoft Store 桩，不可用。用 PowerShell 全路径调用。

**建 env 必须走** `audit_d7_s_event_aligned.build_pinned_env` 并显式传 `user_world_seed`。
直接构造 + `reset(seed=...)` 不能确定用户世界 —— 同一进程内先后构造的两个 env 在未步进前
`user_positions` 就不同。见 `tests/native_geometry_integration_test.py` 中 `_build` 的 docstring。

**可复用测量脚本**（在本 session 的 scratchpad 内）：

| 脚本 | 用途 |
|---|---|
| `bench_opt.py` | 同进程交错三臂 + null 对照，用 `types.MethodType` 逐实例还原旧实现来比较优化前后 |
| `bench_paired.py` | 比较 `use_native_geometry` 开/关 |
| `digest.py` | 25 步 rollout 位摘要 |
| `prof.py` | self-time + 每步调用计数 |
| `ceiling.py` | 指定子树的累积占比 |
| `bitwise_distance.py` | 位相同抽样 + 重结合负例对照 |

---

## 共用仓库状态

- 本轮期间**另一会话**向 `untied-k` 推进了 8 个提交，HEAD `3c4f2af1` → `efb1973d`
- `dab23b0a "Keep the native matrix a matrix, and stop re-paying the loop it retires"`
  是本轮早先的矩阵化改动及其测试改动，由那条线提交
- 本轮测量期间落地的 4 个提交（`0de24c03` / `167c59c7` / `2879f0da` / `efb1973d`）均为文档，
  未触及环境代码
- `docs/project/CURRENT_WORK.md` 的 `active_pm_session` 由那条线持有；本文件未改动它
