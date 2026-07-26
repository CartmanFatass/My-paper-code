# 第 25 轮算法迭代报告

## 本轮问题

G32 已证明同一个 capacity-8 checkpoint 可以在配置容量 6、8、12 上无适配
strict-load，并在固定的 12/24/36 roster 事件日程下保持可用。第 25 轮 G34
检验更强但仍有界的问题：冻结 G32 checkpoint、不再训练，把 membership edit
的时间、顺序、幅度和 active-count trajectory 换成预先冻结的 episode-random
四事件过程，能否仍通过相同的主要门槛。

随机过程每个 episode 恰好发生 `L/R/J/T` 四类事件，使用三个冻结顺序，事件时间
位于 5 到 43、相邻至少 5 步、避开 4 的倍数；三个 replicate 对顺序与 capacity-8
profile 做 43/43/42 轮换平衡。固定参考仍使用 G32 的 12/24/36 日程，随机与固定
分支共享 base ledger 和 action stream。

## 实现、外审与运行条件

- 冻结源：`CONTINUOUS_ROSTER_RANDOM_PROCESS_G34_P0`，`H=48`，容量 6/8/12。
- checkpoint：精确复用 G32 的三组 zero/final checkpoint；G34 optimizer step 为 0。
- 代码源提交：`15f95889f4a318905ba45a1977b5e9079d114545`。
- code-science 首轮外审发现检查点绑定和汇总指标可被错误证据绕过；PM 仅修复这两点。
- 唯一一次 correction-only 复核返回精确 `AUDIT_DISPOSITION=ALIGNED`。
- 正式运行：`logs/formal_continuous_roster_random_process_g34_cpu_20260726_15f9588_r1`。
- 平台：AMD CPU，`torch 2.7.0+cpu`，单线程，无 CUDA、后端混用、重试或恢复。
- 规模：3 replicates、60 cells、7,680 episodes、368,640 条真实 48-step transition、
  10,000 次冻结层次 bootstrap；理论 search `K=0`。
- Experiment Operator 前台持有一次运行，三阶段退出码均为 0，总耗时 125.6 秒。

## 机械有效性

终态为 schema 2、`formal=true`、`status=COMPLETE`、
`operational_valid=true`、`operational_errors=[]`。PM 独立验证了：

1. 每个 model cell 都重新 strict-load 其 replicate/kind/capacity 对应的 G32
   checkpoint，并与序列化的 before/after digest 精确相等；
2. 每个 episode 都有 48 步 reward 与实际 roster-size trace，所有结论指标从轨迹
   重算后与汇总一致；
3. 60 个 cell、7,680 个 episode、368,640 条 transition、零 optimizer step、
   lifecycle 和 process pairing 全部闭合；
4. 从 analyzer predicate inputs 复现的 first-match 分支与文件完全一致。

## 冻结结果

```text
SUPPORTED_BOUNDED_RANDOM_PROCESS_TRANSPORT_G34
```

| 指标 | 95% CI / 数值 | 门槛 |
|---|---:|---:|
| random utility，capacity 6 | `[0.94248, 0.94724, 0.95081]` | LCB `>= 0.90` |
| random utility，capacity 8 | `[0.94938, 0.95306, 0.95585]` | LCB `>= 0.90` |
| random utility，capacity 12 | `[0.94379, 0.94650, 0.94910]` | LCB `>= 0.90` |
| random event-window，最小 capacity LCB | `0.91131` | `>= 0.85` |
| random process-segment，最小 capacity LCB | `0.91275` | `>= 0.85` |
| random-minus-fixed，最小 LCB | `-0.00507` | `>= -0.05` |
| learned gain | `[0.34837, 0.53801, 0.66985]` | LCB `> 0` |
| random stochastic pooled | `[0.88315, 0.88599, 0.88932]` | LCB `>= 0.80` |
| 最差 random replicate mean | `0.94691` | `>= 0.85` |

capacity-8 的 time-rotation 注释为 `LOAD_BEARING`；reactive-ablation 注释为
`UNDERPOWERED`。按冻结契约，它们不能挽救或推翻主要分支。PM 不据此自行判断
recurrence 或绝对时间的一般因果必要性。

## 科学裁决待办

该有效分支消耗 1 次结论性迭代，自动研究链还剩 12 次。External Pro 将在固定
分支不变的前提下决定：最强支持主张、必要限制、最强反例、应保留/淘汰的最小
科研单元、CDC/portfolio/ledger 精确修改，以及唯一下一项科研动作。完成该裁决
前，本报告不扩展 G34 的科学含义，也不选择 successor。
