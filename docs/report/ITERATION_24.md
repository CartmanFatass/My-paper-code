# 第 24 轮算法迭代报告

## 本轮科学问题

G31 已经证明：在一个预先配置的有限 packing capacity 内，continuous
recurrent policy 可以处理 episode 中的临时离开、重入、新加入和终止离开，
并同时保留即时服务与延迟信用能力。本轮 G32 进一步检验：只在 capacity 8
训练得到的同一 checkpoint，能否不重训、不做评估期优化、也不使用
checkpoint adapter，直接 strict-load 到 capacity 6、8、12 的模型实例。

本轮还使用 capacity 8/12 精确 padding 对照：两者执行同一个
`4→3→6→5` active lifecycle 过程，capacity 12 只增加四个永久 inactive
槽位。共同 active 成员的 observation、value、deterministic action、reward、
hidden state 和 lifecycle transition 必须精确一致。

## 环境、算法与运行条件

- 环境：无 UAV 物理量的 48-step continuous-service toy。
- 训练容量：8；评估容量：6、8、12。
- roster：训练与评估都含 episode 内 leave/rejoin/fresh-join/terminal-leave；
  capacity 12 的 held-out 过程达到 active count 10。
- 算法：G31 的 realized-future-tail 与 direction-balanced actor update；G32
  删除 learned parameter 对最大 packing capacity 的形状依赖，使用 active-set
  聚合、`log1p(active_count)` 和固定宽度 critic state。
- 训练：3 个 replicate，每个 replicate 100 次 fast update、100 次
  return-to-go update、8 个并行环境、2 次 PPO pass。
- 评估：每个注册 cell 128 个 episode，共 30 个 cell、3,840 个 utility
  观测；10,000 次层次 bootstrap；评估 optimizer step 为 0。
- 平台：本机 AMD CPU，`torch 2.7.0+cpu`，单线程；无 CUDA、后端混合或
  跨后端比较。
- 正式源码：`fbce3609b11353634d1b4acb20cb27372de40bf2`。
- 正式运行：`logs/formal_runtime_capacity_g32_cpu_20260725_fbce360_r1`。

## 正式结果

训练、评估、分析全部自然完成，退出码均为 0；分析器报告
`formal=true`、`status=COMPLETE`、`operational_valid=true` 且无 operational
error。冻结的 first-match 分支为：

```text
USABLE_RUNTIME_CAPACITY_G32
```

| 指标 | 95% CI 或结果 | 冻结门槛 |
|---|---:|---:|
| capacity 8 utility | `[0.95025, 0.95520, 0.95910]` | LCB `≥ 0.90` |
| capacity 6 utility | `[0.93757, 0.94355, 0.94802]` | LCB `≥ 0.90` |
| capacity 12 utility | `[0.94832, 0.94981, 0.95128]` | LCB `≥ 0.90` |
| held-out final-minus-zero gain | `[0.36581, 0.53720, 0.64719]` | LCB `> 0` |
| 最差 held-out replicate mean | `0.94284` | `≥ 0.85` |
| held-out stochastic mean | `0.87591` | `≥ 0.80` |

三个 mapping diagnostic 的相关系数均高于 `0.9898`，MAE 均低于
`0.0166`。capacity 8/12 padding 对照中，共同成员的全部注册连续字段误差
为精确 `0.0`，生命周期完全相同，附加 inactive 行保持精确零。

## External Pro 科学裁决

External Pro 在固定结果分支不变的前提下给出：

```text
SUPPORTED_RETAINED_USABLE_CONFIGURED_CAPACITY_CONTINUOUS_ROSTER_G32
```

因此 G31 与 G32 合并后，形成了一个在已登记 toy family 中可用的
continuous dynamic-roster 算法测试版。其精确支持范围是：

1. 每条 trajectory 开始前选择一个有限 packing capacity；
2. 同一 capacity-8 checkpoint 可无适配 strict-load 到配置容量 6、8、12；
3. 配置容量内仍可发生运行时成员数量和 lifecycle 变化；
4. learned actor/critic 参数形状不需要绑定最大 packing capacity；
5. 永久 inactive padding 不改变共同 active 成员的行为。

这一结果不只是 state-dict 兼容性，因为跨容量 utility、held-out gain、
stochastic stability、mapping 和 lifecycle gate 也全部通过；但它也不是
无界动态容量结论。

## 对科研方向的影响

本轮保留以下最小科研单元：capacity-generic learned parameterization、
非序列化的 runtime capacity metadata、active-only representation、
lifecycle-owned recurrence，以及 G31 的 realized-future-tail / direction-
balanced credit。G32 没有独立证明 G31 credit 的因果必要性，也没有证明它
相对 G31 的性能优势。

在已登记 capacity 6/8/12 toy family 内，以下替代解释被关闭：

- 跨配置容量使用必须让 learned tensor 形状绑定最大容量；
- 从 capacity 8 迁移到 6/12 必须重训、切片、改 key 或使用 adapter；
- 单纯增加永久 inactive padding 必然改变共同成员行为。

单条 trajectory 运行中改变 tensor width 仍未实现，但在当前主张下，它是
hidden-state 搬运和 tensor packing 的代码覆盖问题，不应自动消耗科研迭代。
只有用户未来把保护主张扩展为“运行中不得预先声明容量上界”时，它才重新
成为科学问题。

## 本轮不能推出的结论

- 任意容量、任意 active count、任意 process law 或随机 horizon；
- trajectory 中途实时改变 packing tensor width；
- UAV 通信、充电或失灵场景中的可用性；
- 异步 skill lifetime、环境无关 intrinsic reward 增益或比较优势；
- G31 credit 的独立因果必要性；
- recurrence 相对直接 current-demand 反应式控制器的必要性。

UAV temporary-loss G1 与 charge-rotation G2 仍是
`SOURCE_NOT_IDENTIFIABLE`，不能被 G32 追溯性改写。

## 下一科学边界

External Pro 选择的唯一下一动作是：

```text
UAV_LOCALIZED_DEMAND_BURST_G33_DESIGN_ASSERTION_AUDIT
```

该动作只冻结一个 source-identifiable 的 S7-S1 局部需求突增源，不训练
learner。它保持 8 架固定 physical/service roster、原 Scenario-7 物理与外部
reward；未来 burst onset、持续时间、位置和强度不可见，当前 per-user demand
可见但不得泄漏目标 UAV assignment。设计必须同时给出 future-blind
constructive control、ledger-blind no-reallocation control、physical
reachability oracle、matched ordinary recurrent null，以及正负 branch witness。

只有物理可达、constructive access、no-reallocation 差距和“所有 access-level
最优解都必须在 burst 后重新分配空间服务”同时成立，才允许进入后续代码与
计算边界。该 G33 audit 本身不消耗结论性迭代。

## 迭代计数与证据

第 24 轮消耗 1 次有效结论性迭代；二十轮自动研究链仍剩 13 次。External
Pro 的完整原文与机械 intake 位于：

- `docs/external-review/rounds/20260725_runtime_capacity_g32_formal_result_review/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260725_runtime_capacity_g32_formal_result_review/50_MECHANICAL_INTAKE_RECORD.md`
