# 第 28 轮算法迭代报告

## 本轮问题

G36 表明，对精确 G35 CS final checkpoints，目标 episode 的真实 time、age 与两个
previous-action 字段可以由一个内部一致的、active-count-conditioned donor bundle
替代。G37 不重新训练 checkpoint，也不重跑 G36；它保持四个坐标各自的完整经验边际与
合法 support，却让每列独立选择 donor snapshot 并独立打乱成员行，从而只检验跨坐标、
跨成员的 joint coherence 是否是这些 checkpoint 的承载单元。

## 实现、外审与正式运行

- 冻结源：`CONTINUOUS_ROSTER_HISTORY_PROXY_COHERENCE_G37_P0`，`H=48`，容量 6/8/12。
- 修复后代码源提交：`87f4dfbe56b36f31d34f134a3c350bd766fae8d7`。
- 设计审计：`IDENTIFIABLE_BOUNDED_FACTORIZED_HISTORY_PROXY_COHERENCE_G37_DESIGN`。
- code-science 审计返回精确 `AUDIT_DISPOSITION=ALIGNED`。
- 正式运行：`logs/formal_continuous_roster_history_proxy_coherence_g37_cpu_20260726_87f4dfb_r1`。
- 平台：CPU，`torch 2.7.0+cpu`，单线程；无 CUDA、重试、恢复、fallback 或混合后端。
- 规模：3 replicates、3 capacities、36 cells、每 cell 128 episodes、4,608 episodes、
  221,184 条真实 transitions、0 training transitions、0 optimizer steps、10,000 bootstrap。
- 复杂度：`K_search=0`、hypothetical transitions 为 0，无 nested rollout/replanning。
- evaluation/analyze 序列化时间总和为 `300.5915559999958` 秒，低于 28,800 秒上限。

## 机械有效性

正式终态为 `formal=true`、`status=COMPLETE`、`operational_valid=true`、
`operational_errors=[]`。PM 独立重验得到：

1. 精确 G35 CS final checkpoints 与 G36 joint-donor artifacts 全部 strict-load，G36 未重跑；
2. 同提交 nonformal preflight 的绝对路径与两份 digest 被正式 manifest 精确绑定；
3. donor support、四列独立 snapshot/permutation 地址、fixed/random tape reuse、action pairing、
   36-cell inventory、lifecycle 与全部 48-step trace 闭合；
4. 注册 validator 返回空错误列表，stored evaluation digest 与 analysis 绑定一致；
5. 冻结 selector 独立重算分支与 stored branch 完全一致。

## 冻结机械结果

```text
MIXED_UNDERPOWERED_HISTORY_PROXY_COHERENCE_G37
```

| 指标 | 95% CI / 状态 | 冻结判定 |
|---|---:|---:|
| source / G36 reference valid | `true / true` | 通过 |
| factorized fixed utility LCB，capacity 6/8/12 | `0.90157 / 0.88889 / 0.88919` | 仅 capacity 6 达到 `0.90` |
| factorized random utility LCB，capacity 6/8/12 | `0.90072 / 0.88549 / 0.89054` | 仅 capacity 6 达到 `0.90` |
| fixed/random stochastic pooled LCB | `0.84787 / 0.85213` | 均达到 `0.80` |
| minimum fixed/random replicate mean | `0.89294 / 0.89188` | 均达到 `0.85` |
| primary joint-minus-factorized | `[0.00639, 0.02160, 0.05154]` | UCB 略高于 `0.05` |
| largest component UCB | `0.09007` | 仅作冻结诊断 |
| factorized access pass / confident fail | `false / false` | 均未闭合 |
| coherence noninferior / material loss | `false / false` | 均未闭合 |

## External Pro 科学裁决

External Pro 原样接受机械分支并裁决：

```text
MIXED_DIRECTIONAL_FACTORIZATION_COST_RETAIN_G36_CLOSE_G37_P0
```

主区间完全大于零，只支持“完整 factorization 对这些精确 checkpoint 有方向明确的平均
损失”，并关闭该冻结 estimand 的零平均效应点原假设。它没有证明 factorized donor
noninferior，没有证明其绝对 access，也没有证明 joint coherence 具有大于 0.05 的 material
necessity。G36 的内部 coherent donor 仍是接受边界；G37-P0 按 mixed 关闭，禁止追加 seed、
episode、bootstrap、checkpoint 或改变阈值救援。

唯一下一动作是：

```text
CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_DESIGN_ASSERTION_AUDIT
```

G38 不继续拆 donor，而是审计 fresh matched training：FULL10_CS 使用十维实际输入；
FOLD6_CS 在训练期把 6:10 固定为冻结常量，并在训练后把常量列贡献精确折叠进 bias，形成
真正的六输入部署 actor。设计审计本身零计算，保持 G31 credit、G32/G34 source、critic、
配对 exposure、`H=48`、`K_search=0` 与既有八小时上限。

本轮是有效结论性第 28 轮；自动研究链剩余 9 轮。G33 及其衍生线仍保持用户放弃状态，
禁止复活。
