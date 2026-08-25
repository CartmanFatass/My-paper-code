# 第 27 轮算法迭代报告

## 本轮问题

G35 已证明，在其精确 P0 源、训练预算和完整当前信息下，清零 learned actor carry
的 CS checkpoint 对 REC 在 0.05 margin 下非劣。G36 不重新训练 checkpoint，而是只在
执行时将 actor observation 的 true time、lifecycle age 与两个 previous-action 字段
替换为独立、source-valid 的 donor history-proxy bundle，用来检验这些真实传感字段或其
与当前上下文的一致性是否仍是精确 G35 CS final checkpoints 的承载单元。

## 实现、外审与正式运行

- 冻结源：`CONTINUOUS_ROSTER_HISTORY_PROXY_FREE_CS_G36_P0`，`H=48`，容量 6/8/12。
- 修复后代码源提交：`8f1cd60068426ac2c0a35ef2d9f4d624b1a01c04`。
- 设计审计：`IDENTIFIABLE_BOUNDED_HISTORY_PROXY_SUBSTITUTION_G36_DESIGN`。
- 首次 code-science 审计发现 full-width observation 预先物化；最小修复后 correction recheck
  返回精确 `AUDIT_DISPOSITION=ALIGNED`。
- 正式运行：`logs/formal_continuous_roster_history_proxy_free_cs_g36_cpu_20260726_8f1cd60_r1`。
- 平台：CPU，`torch 2.7.0+cpu`，单线程；无 CUDA、重试、恢复、fallback 或混合后端。
- 规模：3 replicates、3 capacities、36 cells、每 cell 128 episodes、4,608 episodes、
  221,184 条真实 transitions、0 training transitions、0 optimizer steps、10,000 bootstrap。
- 复杂度：`K_search=0`、hypothetical transitions 为 0，无 nested rollout/replanning。
- evaluation/analyze 序列化时间总和为 `167.964783299998` 秒，低于 28,800 秒上限。

## 机械有效性

正式终态为 `formal=true`、`status=COMPLETE`、`operational_valid=true`、
`operational_errors=[]`。PM 独立重验得到：

1. 精确 G35 formal manifests、analysis 和各 replicate CS final checkpoints 全部 strict-load；
2. 同提交 nonformal preflight 的绝对路径和两份 digest 被正式 manifest 精确绑定；
3. donor 支持、actor-only 零读取、零 checkpoint update、proxy/action 配对、36-cell inventory、
   episode/process identity、lifecycle 与全部 48-step trace 闭合；
4. 重新生成 10,000 次层级 bootstrap 后，完整 metrics 与 stored analysis 完全一致；
5. evaluation manifest SHA-256 为
   `03b6ae2bca6f284524b442bd642dd306b8a8db7e6103d177e6982bfeea864bf6`。

## 冻结机械结果

```text
HISTORY_PROXY_FREE_CHECKPOINT_SUFFICIENT_G36
```

| 指标 | 95% CI / 状态 | 冻结判定 |
|---|---:|---:|
| registered source access | `true` | 通过 |
| intervention access | `true` | 通过 |
| fixed stochastic pooled | `[0.87737, 0.88497, 0.88951]` | LCB `>=0.80` |
| random stochastic pooled | `[0.88355, 0.89127, 0.89600]` | LCB `>=0.80` |
| minimum fixed/random replicate mean | `0.94264 / 0.94363` | 均 `>=0.85` |
| primary registered-minus-intervention | `[-0.00248, 0.00010, 0.00357]` | UCB `<=0.05` |
| largest registered-minus-intervention UCB | `0.00753` | `<=0.05` |
| `proxy_noninferior` | `true` | 通过 |
| `material_proxy_loss` | `false` | 未触发 |

## External Pro 科学裁决

External Pro 原样接受机械分支，并裁决：

```text
SUPPORTED_RETAINED_BOUNDED_ACTUAL_HISTORY_SENSOR_BUNDLE_SUBSTITUTION_G36
```

在精确 G35 CS final checkpoints、`H=48`、容量 6/8/12 以及 G32 fixed / G34-P0
bounded-random source 内，actor 不需要取得目标 episode 的真实 time、lifecycle age
和两个 previous-action 字段；冻结的 active-count-conditioned、source-valid donor bundle
足以保持全部 access 门槛，并在 0.05 margin 下对注册执行非劣。最小关闭单元是该真实一致
四字段 bundle 对这些 checkpoint 的必要性或大于 0.05 的 material benefit。

该结论是传感替代，不是把十维架构删除成六维，也不支持 zeros、常数、任意噪声、全局
memoryless、移除 active mask/lifecycle state、移除 critic true time 或否定 G31 credit。
四个 history-shaped 坐标和 G36 donor 的内部 joint coherence 仍被保留。唯一下一动作是：

```text
CONTINUOUS_ROSTER_HISTORY_PROXY_COHERENCE_G37_DESIGN_ASSERTION_AUDIT
```

本轮是有效结论性第 27 轮；自动研究链剩余 10 轮。G33 及其衍生线仍保持用户放弃状态，
禁止复活。
