# FRRIE R09 A03 tape 隔离探针结果简报 — 2026-09-06

**一句话**：三臂全部失败，而且**不导入 torch、不开 tracer 的 T0 臂也失败**（128 条 tape 成功后，第三批出现 `fields(dataclass)` 返回 `tuple_iterator` 的 Python 级不可能对象）。按卡片读法为 `A03_CORRUPTION_WITHOUT_TORCH`：损坏不需要 torch 扩展或 pdb，嫌疑落在 wsl_4070 上的解释器构建（uv 管理的 CPython 3.10.21，Clang 22.1.3）、numpy 1.26.3 wheel 或主机本身。卡片后果：**在此基底上不再启动 R09，直到所有者回答主机/解释器问题**。

## 事实

| 臂 | torch | tracer | 失败前完成 | 失败 | wall |
| --- | --- | --- | --- | --- | --- |
| T0 | 无 | 无 | 2 × 64 tape | `AttributeError: 'tuple_iterator' … 'name'` | 8 s |
| T1 | 有 | 无 | 512 评估 tape + 2 × 64 | `SystemError: error return without exception set` | 31 s |
| T2 | 有 | pdb | 至少评估 + 更新 1 | SIGSEGV（`rng.py:185 validate`） | 84 s |

所有完成阶段的摘要在各臂之间、以及与本地 Windows 运行完全一致（0f0fb392…、7e155dc5…），即损坏表现为异常/信号，不是静默错误 tape。三臂都在 31 s 的 tape 工作内复现；这是该家族第四到第六个不同的失败（R09 段错误、A01 tuple_iterator、A02 basin 越界）。同样字节在本地 conda CPython 3.10 上正常完成。

## 预测评分

DM 预测「仅 torch 或仅 pdb 下损坏」，把「无 torch 也损坏」列为最不可能——**预测错误**。所有者槽位未填。

## 需要所有者回答的问题（方向层，已写入 owner item）

节点 wsl_4070 的 `/home/wu/.venvs/hmasd` 解释器（uv CPython 3.10.21 / Clang 22.1.3）+ numpy 1.26.3 在纯 Python 地址哈希循环中产生运行时对象损坏。选项：
- (a) **推荐**：A04 探针——同一 T0 工作分别在节点上另一解释器构建（系统 CPython 或非 uv 构建）下、以及在同一 uv 解释器但换 numpy wheel 下重复，区分解释器 / wheel / 主机；零科学、分钟级。DM 在操作员盘点节点解释器后按委托冻结 A04 卡。
- (b) 把 R09 全链移到本地 Windows 环境执行（R09 的 native 构建未预声明主机可移植性，不作为启动，仅作备选问题）。
- (c) FRRIE 在此边界停车，等所有者处理节点。

详情：`docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_R09_SEGFAULT_A03_TAPE_ISOLATION_INTAKE_20260906.md`；证据 `a03_tape_isolation_20260906/`。
