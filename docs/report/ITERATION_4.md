# 第 4 轮结论性迭代：G3 的访问证据不足

## 本轮科学问题与运行前决策

本轮检验：在匿名成员异步加入、续期和替换时，显式的生命周期 commitment roster
能否比持久 TEAM_REC 和不读取 roster 的编辑器更好地学习需求匹配，并迁移到未见过的
成员数 N=4 与长时间间隔。主估计量冻结为
`G_team=U_ROSTER_ATTN-U_TEAM_REC`，外部效用只计算真实服务的需求；重复 effect 可以最优，
零需求 effect 不应获得奖励。访问门槛 0.90、有效增益门槛 0.10 和 first-match 顺序均在运行前冻结。

## 实验环境、预算与证据闭合

```text
source_commit=3f636aa7ad43b406734f2f34472ba12ee4e0cd77
run=logs/formal_useful_effect_roster_g3_cpu_20260723_3f636aa_r1
backend=cpu
torch=2.7.0+cpu
torch_threads=1
formal=true
replicates=5
arms=NO_ROSTER,TEAM_REC,ROSTER_ATTN
updates_per_arm_replicate=120
episodes_per_update=512
ppo_passes=4
evaluation_episodes_per_cell=512
bootstrap_repetitions=10000
```

固定的 Luna-low 实验子代理在前台完成 `train -> evaluate -> analyze`，三阶段退出码均为 0，
且没有重启或重试。Project Manager 随后独立运行正式校验器并重算首匹配分支。最终闭合：

- 15 个最终 checkpoint；
- 120 个评估文件，共 61,440 条评估记录；
- 640 条 held-out-joint 因果审计；
- 完整 source controls、需求/deficit/event ledger、checkpoint exposure、RNG、CPU 与线程身份；
- `operational_valid=true`、`source_identifiable=true`，无临时或 latest 残留。

## 登记结果

| 指标 | 均值 | CI95 |
|---|---:|---:|
| NO_ROSTER utility | 0.8522461 | [0.8471680, 0.8572266] |
| TEAM_REC utility | 0.8441406 | [0.8359375, 0.8524414] |
| ROSTER_ATTN utility | 0.8938477 | [0.8633789, 0.9163086] |
| `G_team` | 0.0497070 | [0.0226563, 0.0699219] |
| `G_null` | 0.0416016 | [0.0096680, 0.0651367] |

ROSTER_ATTN 的均值最高，但其访问区间跨越冻结的 0.90 门槛，因此 first-match 第 4 步登记：

```text
UNDERPOWERED_ACCESS_USEFUL_ROSTER_G3
```

后续指标不能越过该分支改写结论。因果电池中，natural utility 为 0.89727，roster 干预 TV
为 0.14329，adapted 相对 replayed 的效用增益为 0.12695；但精确最优动作概率只有 0.33648，
完整电池未通过。这说明策略会响应 roster 干预，但尚未证明可靠访问或精确需求匹配。

## 对本轮科学决策的影响

- 显式 roster 的平均效用高于两个普通控制，且干预会改变行为和效用；因此 roster 通道并非
  完全装饰性结构。
- 该结果仍不能支持算法优势：访问门槛未被置信地下界越过，两个增益的 UCB 也都低于 0.10。
- 五个 ROSTER_ATTN replicate 的 held-out-joint 均值约为
  `0.893/0.904/0.923/0.914/0.836`。不确定性主要来自训练种子稳定性，而不是 512 条评估样本不足；
  单纯增加评估行数不是合适的下一步。
- 精确 G3 包到此关闭，不重跑、不调门槛、不增加同名预算，也不用低优先级指标救援结果。
- C-EHC 仍是可能解释，但没有获得支持；C-COORD 获得“roster 会影响行为”的局部证据，尚未获得
  “稳定访问并显著优于 TEAM_REC”的证据。

## 本轮不能支持的结论

本轮不能证明 ROSTER_ATTN 优于 TEAM_REC 或 NO_ROSTER，不能证明 event-held roster 已经形成通用
MARL 算法贡献，也不能把因果干预的正响应解释成完整的自然 mediation。反过来，它也不能证明
显式 roster 无用：有效分支只是访问证据不足，而不是 NO_ACCESS 或普通控制充分。

## 下一边界

本轮消耗第 4 次结论性迭代，剩余 1 次。下一步先执行零计算的
`COUNT_PRESERVING_ROSTER_ENCODER_G4_DERIVATION`：推导一种保持绝对 commitment multiplicity 的
置换不变 roster 聚合，并用当前 G3 结果判断它是否比继续使用 softmax 归一化 attention 更可能解决
跨种子访问不稳定。该推导不消耗迭代；只有形成独立、冻结的算法与证据合同后，才可使用最后一次
正式迭代。
