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

## External Pro 科学裁决

External Pro 保持正式分支不变，并给出绑定科研裁决：

```text
SUPPORTED_RETAINED_USABLE_CONFIGURED_CAPACITY_BOUNDED_RANDOM_PROCESS_CONTINUOUS_ROSTER_G34
```

G34 在 G32 之上新增的精确结论是：同一组只在 capacity 8、固定 12/24/36
日程上训练的 checkpoint，可零训练迁移到配置容量 6/8/12 的 G34-P0 四事件
随机时间/顺序 family，同时保持 deterministic access、event/segment 服务、
stochastic stability、正 learned gain 与 lifecycle 正确性。

在 P0 范围内，以下解释被关闭：checkpoint 只有依赖固定 12/24/36 日程和 atomic
R+J 才能工作。但不能将结果扩展成任意过程律、重复 leave/rejoin、任意事件数、
任意 cohort、`H≠48`、capacity 6/8/12 之外、trajectory 中途改变 capacity、
time-free robustness、UAV transport、recurrence 必要性或 G31 credit 必要性。

## 诊断与最强剩余解释

time-rotation 的 `LOAD_BEARING` 只说明该精确 checkpoint 在 G34-P0 上实质依赖
正确 normalized absolute time；它不说明策略记忆 12/24/36，也不证明所有策略
都必须使用时间。reactive-ablation 的 `UNDERPOWERED` 同时删除 hidden、age 与
previous action，既不能证明 current-state 已足够，也不能证明 recurrence 必要。

最强剩余简单解释是：策略主要是使用 current load、target mix、active-set 与
真实时间的直接映射器，而 lifecycle recurrence 或 realized-future-tail credit
未必是 process transport 的必要原因。

## 唯一下一科研动作

```text
CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_DESIGN_ASSERTION_AUDIT
```

该动作只做零计算设计审计，冻结 freshly paired recurrent 与强
current-state/feedforward null。两臂必须保持 actor-visible current fields、
centralized critic、active-set、action prefix、true time、age、previous action、
G31 credit、参数量、交互、optimizer exposure、配对初始化和 final-checkpoint
规则一致；唯一因果差异是 actor 是否跨 primitive step 与 lifecycle boundary
携带 learned recurrent hidden state。

设计审计需冻结主估计量 `U_recurrent-U_current-state`、margin、seed、whole-episode
层次置信区间、共同 access gate 与互斥 first-match 分支，并提供 current-state null
可表达已登记 constructive load/mix mapping 的正向表示 witness。`H=48`、
`K_search=0`、hypothetical transitions 为 0，后续任何实现仍受 nonformal 20 分钟、
formal 8 小时上限约束。

第 25 轮消耗 1 次有效结论性迭代，自动研究链还剩 12 次。G33 及其衍生线继续按
用户指令保持放弃和禁止复活。
