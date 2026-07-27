# 第 29 轮算法迭代报告

## 本轮问题

G38 检验一个直接的架构降维命题：在保持相同十维训练图、参数量、初始化、训练曝光和 critic 的前提下，
将 active actor 输入的后四个坐标固定为注册常量，再把这四列的仿射贡献精确折叠进 bias，所得真实六输入
部署 actor 是否仍能保持容量 6/8/12、fixed/random 条件下的能力，并在 `0.05` 界内不劣于 FULL10。

## 实现、纠正审计与正式运行

- 修复源提交：`ea93b15eabf68c35ba8e459ca8527e56d2988db8`。
- 代码科学纠正复核：精确 `AUDIT_DISPOSITION=ALIGNED`。
- 修复源非正式预检：30 cells、26,880 transitions、120 optimizer steps，15 个 FOLD6 cells 的折叠误差全为 `0.0`。
- 正式运行：`logs/formal_continuous_roster_six_coordinate_cs_g38_cpu_20260726_ea93b15_r2`。
- 平台：CPU、`torch 2.7.0+cpu`、单线程，无 CUDA 或混合后端。
- 规模：3 replicates、2 arms、90 cells、每 cell 128 episodes、1,013,760 条真实 transitions、3,600 optimizer steps、10,000 bootstrap。
- 复杂度：`H=48`、`K_search=0`、hypothetical transitions 为 0，无 nested rollout/replanning。
- train/evaluate/analyze 总序列化时间为 `2249.9623112000045` 秒，低于 28,800 秒上限。

第一次旧源正式尝试因浮点归约顺序导致 fold-equivalence 操作无效，已计零轮并保持只读。本轮是修复后新 assignment、
新运行根的完整执行，没有复用或挽救旧结果。

## 机械有效性

正式终态为 `formal=true`、`status=COMPLETE`、`operational_valid=true`、`operational_errors=[]`。
PM 独立验证得到：

1. source commit、`ALIGNED` 复核、V1 token、修复源 preflight 绝对路径和三份 digest 精确绑定；
2. 3 replicate、90-cell、训练/评估 transition、optimizer、bootstrap 和种子库存闭合；
3. 45 个 FOLD6 conclusion-bearing cells 全部通过单轨迹 fold audit，全部六类最大误差精确为 `0.0`；
4. 注册 validator 返回空错误列表，analysis 对 train/evaluation digest 的绑定一致；
5. 冻结 selector 独立重算结果与 stored branch 完全一致。

## 冻结机械结果

```text
SIX_COORDINATE_ARCHITECTURAL_REDUCTION_SUFFICIENT_G38
```

| 指标 | 95% CI / 状态 | 冻结判定 |
|---|---:|---:|
| source valid | `true` | 通过 |
| FULL10 access pass | `true` | 通过 |
| FOLD6 access pass | `true` | 通过 |
| fold equivalence | `45/45`, all maxima `0.0` | 通过 |
| FULL10−FOLD6 primary | `[-0.01009, -0.00313, 0.00841]` | 完全位于 `[-0.05,0.05]` |
| six-coordinate noninferior | `true` | 通过 |
| material information advantage | `false` | 未触发 |

## External Pro 科学裁决

待正式结果复核。External Pro 必须给出该分支的精确结论范围、保留/退役单元、CDC/portfolio/ledger 修改、
三分支科研 disposition，以及在 `CONTINUE` 时的一个当前调度动作；该调度不把其他 live/parked 方向变成
无效或退役。PM 不在此处自行解释六坐标充分性、全局历史冗余或研究组合优先级。

本轮是有效结论性第 29 轮；自动研究链剩余 8 轮。G33 仍保持用户放弃状态，不得复活。
