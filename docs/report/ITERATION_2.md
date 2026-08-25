# 第 2 轮结论性迭代：G1 普通 recurrence 足够

## 本轮科学问题与运行前决策

本轮在独立 access-positive source 上比较 OR、DUM 和 EHC，检验两步 cue 所需
的跨时间行为是否必须依赖 event-held commitment。冻结主估计量为 EHC 相对
OR/DUM 的效用增益，并把访问与 source identifiability 放在机制结论之前。

## 实验环境与证据

```text
source_commit=de9a315b4969ee6920be08a3d911d559fe362f03
run=logs/formal_access_positive_ehc_g1_cpu_20260723_de9a315_r2
backend=cpu
torch_threads=1
formal=true
checkpoints=15
evaluation_files=60
```

注册 operator 完成 train/evaluate/analyze，所有阶段退出码为 0。正式验证闭合
全部 checkpoint、评估、source control 与 causal audit，且没有临时结果残留。
最大组效用 CI95 为 `[0.9293551, 0.9420615]`，显著越过 `0.80` 访问门槛。

## 登记结果

| 组 | 平均效用 | CI95 |
|---|---:|---:|
| OR | 0.9344202 | [0.9268957, 0.9420615] |
| DUM | 0.9344202 | [0.9268957, 0.9420615] |
| EHC | 0.9349483 | [0.9293551, 0.9410610] |

两项 EHC 增益均为 `0.0005281`，CI95
`[-0.0014028, 0.0026465]`，上界远低于冻结的 `0.10` 有意义增益门槛。
登记分支为：

```text
ORDINARY_EXPLANATION_G1
```

## 对科学决策的影响

- 普通 per-member recurrence 足以完成这个精确的生命周期内 cue-memory 任务。
- G1 的 commitment channel 对自然行为近乎装饰性：存在机会与 K-bin 覆盖并不
  等于链路对动作或价值有实际作用。
- 精确 G1 被永久关闭；C-EHC 被缩小到 creator 离开后仍需跨生命周期传递状态的
  场景。
- 下一步不是增大模型或调参，而是建立匿名 creator-to-successor 的信息所有权
  边界。
- 本轮消耗第 2 次结论性迭代，结束时剩余 3 次。

## 本轮不能支持的结论

本轮不能推出 event-held state 在所有任务上无用，也不能推出 temporal credit
普遍不是瓶颈。它只否定在这一精确 source 上相对普通 recurrence 的增量价值。

## 下一边界

构建 `CROSS_LIFECYCLE_COMMITMENT_HANDOFF_G2`：creator 观察 bit 后终止离开，
successor 以全新 per-member state 加入；同时必须加入 persistent TEAM_REC 作为
比 per-member recurrence 更强的简单解释。
