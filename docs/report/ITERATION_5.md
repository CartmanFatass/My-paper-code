# 第 5 轮结论性迭代：计数保持 roster 仍无访问

## 本轮科学问题与运行前决策

第 4 轮中，ROSTER_ATTN 平均效用最高但访问区间跨越 0.90，且不同训练种子差异明显。本轮只修改
一个算法对象：把 softmax 归一化 roster 聚合替换为保持绝对 commitment multiplicity 的
`ROSTER_SUM`。环境、需求分布、外部奖励、观察、生命周期事件、PPO、预算、阈值和因果电池全部不变。

三个新训练的同运行比较组为：

- `ROSTER_SUM`：学习 token 均值加原始 effect 计数跳连；
- `ROSTER_ATTN`：第 4 轮的归一化 attention 算法路径，作为直接算法控制；
- `TEAM_REC`：普通持久 recurrent 公共历史，作为任务级控制。

主估计量为 `G_attn=U_ROSTER_SUM-U_ROSTER_ATTN`，同时保留
`G_team=U_ROSTER_SUM-U_TEAM_REC`。访问必须由 ROSTER_SUM 自己达到，其他组不能代替。

## 实验环境、预算与证据闭合

```text
source_commit=64a04fafd5abd4e2955382063a97bff290548513
run=logs/formal_count_preserving_roster_g4_cpu_20260723_64a04fa_r1
backend=cpu
torch=2.7.0+cpu
torch_threads=1
formal=true
replicates=5
updates_per_arm_replicate=120
episodes_per_update=512
ppo_passes=4
evaluation_episodes_per_cell=512
bootstrap_repetitions=10000
```

固定 Luna-low 实验子代理在前台一次完成 `train -> evaluate -> analyze`，退出码均为 0，没有重启。
Project Manager 随后独立运行正式校验器并重算 first-match。闭合结果包括：

- 15 个最终 checkpoint；
- 120 个评估文件，共 61,440 条记录；
- 640 条 ROSTER_SUM 因果审计；
- 完整 source controls、独立 G4 seeds、需求 ledger、每组相等 exposure、optimizer/RNG、
  CPU/线程/授权 token、审计 arm 与效用重算；
- `operational_valid=true`、`source_identifiable=true`，无临时残留。

## 登记结果

| 指标 | 均值 | CI95 |
|---|---:|---:|
| TEAM_REC utility | 0.8484375 | [0.8378906, 0.8583008] |
| ROSTER_ATTN utility | 0.8801758 | [0.8703101, 0.8899414] |
| ROSTER_SUM utility | 0.8738281 | [0.8580078, 0.8875000] |
| `G_attn` | -0.0063477 | [-0.0243164, 0.0119141] |
| `G_team` | 0.0253906 | [0.0030273, 0.0411133] |

ROSTER_SUM 的效用 UCB 为 0.8875，低于冻结的 0.90 访问门槛，因此 first-match 第 3 步登记：

```text
NO_ACCESS_COUNT_ROSTER_G4
```

后续指标不能越过该分支。自然效用均值为 0.85156，精确最优动作概率为 0.30778，roster 干预 TV
为 0.14388，adapted 相对 replayed 的效用增益为 0.06875；策略仍会响应 roster，但没有形成可访问的
精确需求匹配。

## 对本轮科学决策的影响

- “只要显式保持 commitment 数量就能解决访问不稳”被否定。ROSTER_SUM 的表示包含线性充分的
  demand-minus-count 路径，但在同样 PPO 与预算下仍未可靠学会。
- `G_attn` 区间跨越 0 且远低于 0.10，计数跳连没有优于归一化 attention；它是合理接口属性，
  不是已经验证的算法贡献。
- 第 4、5 轮都出现“roster 干预会改变策略，但自然行为能力不足”。因此输入敏感性不能替代访问、
  自然 mediation 或任务优势证据。
- source controls 与构造性 oracle 继续有效；当前证据更指向共享策略优化/访问稳定性，而不是 source
  不可识别。由于该任务是一阶段 demand-served 决策，简单的长时序 credit 解释也不能直接救援结果。
- 精确 G4 永久关闭，不重跑、不调参、不扩预算、不放宽门槛、不用低优先级指标改写结果。

## 五轮整体结论

| 轮次 | 登记结果 | 最小科学影响 |
|---:|---|---|
| 1 | `NO_ACCESS_THIS_BENCHMARK` | 原 G0 对无法在该 benchmark 上识别机制。 |
| 2 | `ORDINARY_EXPLANATION_G1` | 个体 recurrence 足够解释生命周期内记忆。 |
| 3 | `TEAM_REC_SUFFICIENT_HANDOFF_G2` | EHC 链路真实，但一个全局 bit 可由 TEAM_REC 完全保存。 |
| 4 | `UNDERPOWERED_ACCESS_USEFUL_ROSTER_G3` | roster attention 有响应且均值最好，但访问不稳定、优势未成立。 |
| 5 | `NO_ACCESS_COUNT_ROSTER_G4` | 显式计数保持没有修复访问，也没有优于 attention。 |

五轮没有建立 EHC 或 roster 表示相对普通 recurrence 的算法优势；但也没有证明这类机制普遍无用。
可靠结论是：生命周期持有状态可以真实影响行为，但当前 recurrence/attention/count 接口在冻结的 PPO
预算下都没有把它稳定转化为 held-out 的需求匹配能力。

## 本轮不能支持的结论与终止边界

本轮不能证明所有 count-preserving set encoder 都失败，不能证明更强优化器、不同 credit estimator
或更一般 MARL 环境不会受益，也不能把跨运行均值差异当作因果比较。它只关闭精确 G4 包。

本轮消耗第 5 次、也是最后一次结论性迭代：

```text
terminal_disposition=FIVE_ITERATION_CHAIN_COMPLETE
autonomous_research_grant=EXHAUSTED
iterations_remaining=0
successor_status=not_authorized
```

如果开启新的研究链，最小建议问题是“在固定 count-sufficient 表示与同一 source 下，能否通过一个
预注册的优化/访问分离实验判断失败来自策略优化而非表示”。当前流程不自动启动该动作。
