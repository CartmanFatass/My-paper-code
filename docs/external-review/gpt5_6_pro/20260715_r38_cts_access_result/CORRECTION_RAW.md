你的四点批评都成立。前一版 **“S7-S1 ordinary recurrent MAPPO access calibration” 应撤回**：它把“已有正向锚点是 HMASD”与“重新要求另一类策略 MAPPO 先证明可访问”混在了一起，因而既不能隔离 temporal mechanism，也不能在失败时合理停止 HA-CTSE。

修正后的 Route A 不是再做 ordinary-MAPPO access gate，而是：

# **R39-S7：HMASD-compatible temporal-decoupling gate**

其唯一问题是：

[
\boxed{
\text{已建立 S7 access 的 fixed-}k\text{ HMASD}
;\longrightarrow;
\text{只替换同步刷新为 per-agent KEEP/SET}
;\longrightarrow;
\text{是否保留服务能力并真实使用异步 lifetime}
}
]

历史 HMASD 运行只作为**正向参考和 warm-start 来源**；真正的实验 comparator 必须是当前代码中重新实例化的、与 treatment 同源同预算的 fixed-(k) HMASD-compatible arm。Route A 原文也要求“用 HMASD reference 作为正向 access anchor，并注册能恢复实际 HMASD/HA-CTSE 问题的最小 matched gate”，而不是再要求普通 MAPPO 单独解锁 S7。

---

## 1. 正确的三种证据角色

必须区分：

### 历史 standing reference

历史 HMASD S7-S1：

* 约 480K steps 首次达到 coverage 0.7；
* 约 800K steps 首次达到 coverage 0.9；
* 后期 mean coverage 为 `0.9639`；
* 归档运行到 2.112M steps。

它证明 S7-S1 对 **HMASD policy class** 是可访问的，但由于 exposure 和实现版本差异，只能作为 reference，不能直接充当 R39 的因果 control。

### 当前 fixed-(k) control

这是 R39 的实际基线：

[
\pi^{\mathrm{fixed}}_{\mathrm{HMASD}}
]

保留原 HMASD 的：

* 低层 discoverer；
* individual/team semantic loop；
* 网络规模；
* optimizer；
* actor/critic inputs；
* 每 (k_0) 步全体同步刷新；
* 原生 S7 reward、observation 和 dynamics。

### 当前 asynchronous treatment

[
\pi^{\mathrm{async}}_{\mathrm{HMASD}}
]

与 control 完全相同，唯一算法差异是：

[
\text{full refresh every }k_0
\quad\longrightarrow\quad
\text{all-agent check every }k_0
+\text{per-agent KEEP/SET}.
]

因此，这不是“MAPPO 能不能解 S7”，而是一个真正的 temporal isolation：

[
\text{same successful skill/cooperation substrate}
\rightarrow
\text{different renewal semantics}.
]

---

# 2. 正向锚点不能只来自历史运行

两臂从同一个归档 HMASD S7-S1 checkpoint 分叉。使用 standing reference 的最终 2.112M checkpoint，或者仓库注册的等价最终 checkpoint 路径；具体文件路径必须在 ExpRecord 中冻结。

在任何 optimizer update 前，必须完成 **M0 exact warm-start compatibility**：

对 64 个 paired S7 reset groups，在 treatment 的 `full_refresh_compat` 模式下，验证：

[
\max |\mu^{fixed}*{a}-\mu^{compat}*{a}|\le10^{-6},
]

[
\max |\log p^{fixed}-\log p^{compat}|\le10^{-6},
]

并且逐步完全相同：

* sampled team/individual skills；
* primitive actions；
* recurrent hidden states；
* environment transitions；
* external rewards；
* coverage traces。

只有 bit-level/数值容差内 parity 通过后，treatment 才解除 `full_refresh_compat`，启用 learnable KEEP/SET。这样“fixed-(k) 是 exact warm start”成为验证事实，而不是设计口号。

历史 HMASD 只是说明这样的 access 水平曾经存在；当前 fixed-(k) arm 必须在本轮重新通过 access gate。

---

# 3. 精确 service metric

撤销模糊的：

[
service\ metric\ge0.5.
]

R39 使用环境每个 evaluation primitive step 的原生字段：

[
c_{e,t}=\texttt{coverage}_{e,t}\in[0,1].
]

固定报告三个统计量。

### Mean coverage

[
C_{\mathrm{mean}}
=================

\frac{1}{EH}
\sum_{e=1}^{E}
\sum_{t=1}^{H}c_{e,t}.
]

### Full-coverage step fraction

[
C_{\mathrm{full}}
=================

\frac{1}{EH}
\sum_{e,t}
\mathbf 1[c_{e,t}=1.0].
]

这对应项目已经冻结的 S7-S1 最小业务门槛：至少一半 evaluation primitive steps 达到 `coverage == 1.0`。

### Zero-service episode fraction

[
F_{\mathrm{zero}}
=================

\frac1E
\sum_e
\mathbf1
\left[
\max_{t\le H}c_{e,t}=0
\right].
]

若环境还输出 throughput/QoS，可以保留为 diagnostic，但不参与这个 temporal gate 的 PASS。

---

# 4. R39 最小 matched experiment

## 初始化

两臂从同一 HMASD S7-S1 final checkpoint、相同 optimizer-compatible migration state 分叉。

## Arms

```text
fixed_k_hmasd
async_keep_set_hmasd
```

除 temporal controller 外全部相同。

## Exposure

每臂追加：

[
320{,}000
]

environment transitions。

使用 checkpoint manifest 中原生的：

* `num_envs`;
* rollout length；
* PPO epochs；
* recurrent sequence length；
* minibatch；
* actor/critic hidden size；
* skill cardinality；
* entropy coefficients；
* optimizer state和 learning rate。

不重新选择一套 MAPPO 配置。320K 只作为 mechanism gate；项目原则已经明确 160K/320K 不能替代约 1M-scale 的最终 HMASD parity 结论。

## Evaluation

每臂：

* 64 paired stochastic S7-S1 episodes；
* 完全相同 reset seeds；
* 独立但配对的 policy-action RNG；
* 10,000 次 paired-episode percentile bootstrap。

---

# 5. 分支顺序

## M0 — Exact compatibility

要求：

* pre-training full-refresh parity 全部通过；
* 两臂初始参数中共享参数完全一致；
* treatment 只新增 KEEP/SET 所需参数；
* low actor、semantic/discriminator、critic 和 environment paths 不发生未注册差异；
* optimizer-update exposure一致。

M0 失败：

```text
INVALID_R39_COMPATIBILITY
```

唯一下一动作：

> 修复 fixed-(k) compatibility/migration；不能评价 S7、R30 或 HA-CTSE。

---

## M1 — Current fixed-(k) positive anchor

当前 control 必须同时满足：

[
C_{\mathrm{mean}}^{fixed}\ge0.90,
]

[
C_{\mathrm{full}}^{fixed}\ge0.50,
]

[
F_{\mathrm{zero}}^{fixed}\le0.10.
]

M1 失败：

```text
INVALID_R39_SUBSTRATE_REPRODUCTION
```

这不是 HA-CTSE 科学失败。唯一下一动作：

> 停止 treatment 解释，修复当前实现与 standing HMASD reference 之间的可比性。

这正面解决了“为什么普通 MAPPO 失败足以停止 HA-CTSE”的问题：**它不再会。** 只有同策略类的 fixed-(k) HMASD control 成功，treatment 才可被判定。

---

## M2 — Async service preservation

定义 paired treatment-minus-control 差异：

[
\Delta C_{\mathrm{mean}}
========================

## C_{\mathrm{mean}}^{async}

C_{\mathrm{mean}}^{fixed},
]

[
\Delta C_{\mathrm{full}}
========================

## C_{\mathrm{full}}^{async}

C_{\mathrm{full}}^{fixed},
]

[
\Delta F_{\mathrm{zero}}
========================

## F_{\mathrm{zero}}^{async}

F_{\mathrm{zero}}^{fixed}.
]

要求：

[
\Delta C_{\mathrm{mean}}\ge-0.05,
]

[
\Delta C_{\mathrm{full}}\ge-0.05,
]

[
\Delta F_{\mathrm{zero}}\le0.10.
]

另外，三个 paired bootstrap interval 都不得跨越相反方向的安全界限。

---

## M3 — Genuine lifetime decoupling

在 treatment 后半段 exposure 和最终 evaluation 中，必须同时满足：

[
\text{full-sync SET rate}\le0.50,
]

[
\frac{H(Z\mid SET)}{\log K}\ge0.80,
]

[
\min_zP(Z=z\mid SET)\ge0.05,
]

[
\min
\left[
P(T_i>4k_0),
P(T_i\le4k_0)
\right]
\ge0.05,
]

以及：

[
\text{mean pairwise lifetime-correlation}<0.90.
]

最后一个条件排除所有 agent 虽名义上独立、实际上仍使用同一 renewal schedule。

---

# 6. 互斥科学分支

## `PASS_R39_TEMPORAL_DECOUPLING`

条件：

M0、M1、M2、M3 全通过。

仅支持：

> 从同一个已具有 S7 服务能力的 HMASD checkpoint 出发，将同步 fixed-(k) 刷新替换成 per-agent KEEP/SET，可以在短期内保持服务水平并产生真实非同步、非退化的 lifetime 使用。

唯一下一动作：

> 注册约 1M additional steps、paired seeds 的完整 fixed/shared versus per-agent-lifetime 验证。

---

## `VALID_FAIL_R39_ASYNC_SERVICE`

条件：

M0/M1 通过，M2 失败。

支持：

> 当前 R30-style temporal migration 在一个已验证可访问的 HMASD substrate 上损害服务能力。

唯一下一动作：

> 退休当前 KEEP/SET temporal formulation；不回到 toy、MAPPO access 或 intrinsic sweep。

---

## `VALID_FAIL_R39_NO_DECOUPLING`

条件：

M0/M1/M2 通过，M3 失败。

支持：

> treatment 保留服务，但退化成同步或近固定 lifetime，因此没有证明 decoupled-lifetime contribution。

唯一下一动作：

> 退休当前 decoupling claim；保留其作为 fixed/shared control，不做 coefficient rescue。

---

# 7. Route A 的逻辑张力如何消除

Route A 的含义是：

> 不再要求自建 toy 或普通 MAPPO 为 HMASD 研究预先解锁 access；回到一个已经有 HMASD 正向证据的真实 substrate，并用同策略家族做最小因果比较。

因此修正后的流程不是：

[
\text{historical HMASD success}
\rightarrow
\text{ordinary MAPPO must re-prove S7 access}
\rightarrow
\text{then test R30},
]

而是：

[
\text{historical HMASD reference}
\rightarrow
\text{current fixed-}k\text{ HMASD reproduction}
\rightarrow
\text{matched temporal replacement}.
]

历史 run 设置阈值和提供 checkpoint；当前 fixed-(k) arm证明当轮 substrate 与实现仍然有效；async arm只承担 temporal intervention 的因果差异。

这也修正失败解释：

* fixed-(k) 失败：**实现/复现不可比，不能判断 HA-CTSE**；
* fixed-(k) 成功而 async 失败：才是当前 temporal formulation 的科学失败；
* 两者成功但 lifetime 同步：不能宣称 decoupling；
* 两者成功且 lifetime 异质：才允许进入长期 paired temporal gate。

因此，正确的唯一路线仍是 Return to S7-S1，但它应被注册为：

[
\boxed{
\textbf{HMASD-compatible fixed-}k
\quad\textbf{vs}\quad
\textbf{HMASD-compatible per-agent KEEP/SET}
}
]

而不是 ordinary MAPPO access calibration。

