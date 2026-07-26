# 第 26 轮算法迭代报告

## 本轮问题

第 25 轮 G34 已表明，G32 的配置容量 checkpoint 可在冻结的四事件随机
roster 过程上保持有界输送。G35 在不改变当前信息、真实时间、age、
previous action、G31 credit、参数量、优化暴露和评估源的前提下，比较两个
从零配对训练的同构臂：REC 跨 primitive step 传递 learned hidden state，CS 则将
该状态精确清零。该设计的结论上限只是 G35-P0 内的 current-state sufficiency
或有限预算下的 recurrent inductive-bias advantage，不是全局 recurrence necessity。

## 实现、外审与正式运行

- 冻结源：`CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_P0`，`H=48`，容量 6/8/12。
- 代码源提交：`f626dfd8a345ef670e08e601344b67e28ffb3563`。
- 设计审计：`IDENTIFIABLE_EMPIRICAL_REACTIVE_REDUCTION_G35_DESIGN`。
- code-science correction-only 复核：精确 `AUDIT_DISPOSITION=ALIGNED`。
- 正式运行：`logs/formal_continuous_roster_reactive_reduction_g35_cpu_20260726_f626dfd_r1`。
- 平台：AMD CPU，`torch 2.7.0+cpu`，单线程，无 CUDA、后端混用、重试、恢复或 fallback。
- 规模：3 replicates、2 arms、99 evaluation cells、12,672 evaluation episodes、
  1,069,056 条真实 transition、3,600 次训练 optimizer step；评估 optimizer step 为 0。
- 复杂度：`K_search=0`、hypothetical transitions 为 0，无 nested rollout/replanning。
- 序列化三阶段时间和为 2,039.713663 秒，低于 28,800 秒上限。

## 机械有效性

终态为 schema 2、`formal=true`、`status=COMPLETE`、
`operational_valid=true`、`operational_errors=[]`。Experiment Operator 唯一一次返回的
train/evaluate/analyze 退出码均为 0。PM 独立验证了：

1. REC/CS 的零点与最终 checkpoint 全部 strict-load，参数、训练暴露、replay
   和 lifecycle 契约闭合；
2. 每个结论指标均从序列化 48-step trace 重算，与汇总一致；
3. 两份 manifest 的 SHA-256 与 analyzer 绑定完全一致；
4. 从 analyzer predicate inputs 复现的 first-match 分支与存储文件完全一致。

## 冻结机械结果

```text
CURRENT_STATE_REDUCTION_SUFFICIENT_G35
```

| 指标 | 95% CI / 状态 | 冻结判定 |
|---|---:|---:|
| CS common access | `true` | 通过 |
| REC common access | `true` | 通过 |
| REC-minus-CS pooled | `[-0.01735, -0.00812, 0.00071]` | UCB `<= 0.05` |
| capacity 6 REC-minus-CS | `[-0.01453, -0.01055, -0.00664]` | UCB `<= 0.05` |
| capacity 8 REC-minus-CS | `[-0.01934, -0.00865, 0.00304]` | UCB `<= 0.05` |
| capacity 12 REC-minus-CS | `[-0.01800, -0.00525, 0.00541]` | UCB `<= 0.05` |
| `current_state_sufficient` | `true` | CS-sufficient 先匹配 |
| `recurrent_advantage` | `false` | 未触发 |

## External Pro 边界

上述名称只是不可改写的注册机械分支。PM 不把它自行扩展成“全局不需要
recurrence”，也不自行修改 CDC、选择 successor 或授权新计算。External Pro 将决定
精确科学含义、保留/退休单元、最强剩余替代解释、CDC/组合/台账编辑以及唯一下一
科研动作。本轮是有效结论性第 26 轮，自动研究链剩余 11 轮。G33 依然被用户放弃，
不得复活。
