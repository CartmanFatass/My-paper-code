# 五方向科学动因、难点与当前边界

## 总览

| 方向 | 为什么值得研究 | 当前最强事实 | 当前真正阻塞 | 最小下一决策 |
| --- | --- | --- | --- | --- |
| FRRIE | 严格包含的宽模型未必在有限预算下优于结构化紧模型；变量 roster 的 inductive bias 可能影响学习效率 | 原生/批处理/worker 等价与纯计划 gate 已建立；没有 B01 学习结果 | 完整 512-update paired train/eval/checkpoint/telemetry 链仍不完备 | 完成 Slice B 后运行 3-seed matched B/EXPLORE 学习曲线 |
| VNFC | executor 在 episode 内丢失后，共享策略既要处理 membership change，也必须把同一物理状态映射为同一物理动作 | R01 有可达 binary64 near-tie presentation action flip；R01 已关闭但无 return 极性 | 新 R02 finite action law 尚有四个定义闭合缺口，A0 未实现 | 修完四项定义并跑一次 304-row non-result A0 |
| CBSC | OWNER、semantic epoch、capability 和 receiver content 的 currentness 可能形成有限预算 recurrent inductive bias | exact factorial 有狭窄 protocol value；LR01 unresolved；在线 B1 尚未运行 | 最终消费者不能从 raw evidence 独立重算 mechanical/RAW competence；缺完整容量投影 | 修 consumer recompute 与容量 gate，随后 3-seed online B1 |
| SCDMP | H/R 事件顺序可能在同一基础控制器上改变候选动作价值；应与单纯非交换代数分离 | 新 multi-foundation/state/k B01 已冻结；首次 RUN 因 telemetry 缺陷无科学极性 | “旧 master 不可读”与“retry 复用 master”冲突，尚无 replacement identity 决定 | 将其按 B/EXPLORE fresh named attempt 还是 same-identity replacement 明确化，然后运行 |
| UCOPE | 主动付费探测是否有外部价值，必须先有 competent policy；COUNT/RAW 是之后的表示效率问题 | B1 三臂均 0/3 competent；odd/even audit 仍 0 competent/near，route 未被旧 map 覆盖 | 不是工程 blocker，而是科学选择：继续换 optimizer/conditioning，还是 PARK/RECAST | 先做新的 direction-local Convergence；禁止重跑 audit |

## FRRIE — finite-resource relational inductive efficiency

### 动因

FRRIE 针对一个常被“表达能力包含”掩盖的问题：`EDGE_FLEX` 严格包含 `PHY_TRUST`，但在固定
更新数、相同信息、相同参数量和相同环境工作下，更宽的 residual projection/optimizer package
未必更容易学。紧结构可能通过 shrinkage、preconditioning、梯度路径或 host-aligned convention
取得有限预算优势。这个问题对 variable-`N` 有意义，因为训练在 `N={9,15}`、评价包含 held-out
`N={6,21}`，但当前 B01 不包含 episode 内 churn。

### 机制预测与最强替代

- 预测：在 `RIDGEGATE-2Z/RSCF` host 上，tight `PHY_TRUST` 在 512 updates 内更快形成有效
  native-return 曲线，并且优势在 semantic-column reassociation cut 下消失或显著减弱。
- containing null：同信息 `EDGE_FLEX` 有能力实现所有 tight 行为；任何 tight 优势首先可能只是
  优化路径、regularization 或 conditioning，而不是 relational semantics。
- 另一个 null：若 projection 从未 contact，两臂可能沿受观测训练路径等价；但 contact 本身只证明
  轨迹可分叉，不证明 return 优势。

### 当前证据

- R01/R02 的高成本 conclusion-bearing mean objects 已关闭或延后；这不阻止新的 B/EXPLORE。
- B01 已冻结为 3 seeds，可扩至 5；完整 checkpoints `{0,32,64,128,256,512}`，train/held-out
  roster、INTACT/reassociation、competence/contact/resource 观测均已定义。
- 原生 A/RECON 已证明 scalar/batch、1/2/4-worker 一致；FP32 primitive→return 重复推导缺陷已修。
- full512 Slice A 的纯计划/source/admission contract 已 `CLEAN` 并推送。
- Slice B 是未提交 WIP：checkpoint codec/bridge、synthetic shard 描述符有局部 green，但没有最新
  combined suite、独立 review、resume suffix、kappa/parameter inventory 或 authoritative full512
  paired-shard validation。
- 没有 B01 algorithm observation，科学对象未消费。

### 主要难点

科学上，必须把“结构化 prior 有用”与“宽包在此 optimizer/budget 下更难训练”分开。B/EXPLORE
可以报告 package signal，但不能宣称 graphon truth、representation necessity 或一般跨 `N` 优越性。
工程上，真正缺的是一条完整、可审计但不过度仪式化的 512-update paired training/evaluation 链，
而不是更多静态证明。

### 审阅模型应回答

1. 当前 B01 是否已经是最小、诚实的 finite-budget discriminator？
2. 哪些 full512 telemetry/checkpoint 要求直接保护 paired comparison，哪些可以降为普通 diagnostics？
3. 是否应在 Slice B 完成后立即运行 3 seeds，而不是继续扩 formal panel？
4. 若 EDGE competent 且 tight signal 不稳定/不存在，应该关闭 B01 package effect、PARK 方向，还是换 host？

### Claim ceiling

只支持固定 host、3/5 seeds、固定预算的 tight-versus-containing projection/optimizer-package
preliminary signal/null/counterexample。不支持一般 relational semantics、arbitrary-`N`、churn、UAV、
安全或部署。

## VNFC — variable-N fleet churn

### 动因

VNFC 研究 episode 内一次未预告 executor loss 后的恢复。共享 MAPR policy 不仅要接受不同 roster，
还要保证同一物理状态在不同 row presentation 下产生相同物理 joint command；否则所谓
permutation/presentation safety 在实际有限精度执行中并不存在。最终 B 问题比较 MAPR、严格包含的
`DIRECT-SET-AR` 与 competent `BCRH-PERSIST`，训练 `N={3,5}`，held-out `N=7`。

### 机制预测与最强替代

- 预测：presentation-safe MAPR 能从 unshaped external return 学到 loss recovery，并在 untouched
  `N=7` 呈现方向性恢复信号。
- containing null：DIRECT 接收相同信息并严格包含 MAPR，可能同样或更好地学习；任何 MAPR 优势
  只能是有限预算 inductive bias。
- engineering null：presentation 差异只是 validator 报告问题。R01 的 source-only counterexample
  否定这一 null：约 `5.55e-17` 的 aligned logit 差使 canonical 选 physical agent、reverse 选 null。

### 当前证据

- R01 formal DEBUG 在 prerequisite 阶段 fail-closed；没有 return、checkpoint、arm 或 algorithm polarity。
- source-only `N=5/reverse` near-tie witness 证明当前有限动作语义可发生 physical action flip。
- Pro 已决定 `CLOSE_AND_REVISE_R01`；方向未关闭。
- R02 选择单一候选 law `VNFC-R02-ORC-B64-Q52-U64-V1`，计划以 opaque-rank canonicalization、
  scalar binary64、52-bit exact masses 和 uint64-midpoint physical CDF 定义 deterministic/stochastic/
  replay/gradient/optimizer 同一语义。
- A0 计划 304 top-level rows，但 CM 未启动、A0 未运行。
- 更晚 critic 指出四个未闭合项：数学 kernel/dependency bytes、primitive token 1–3 cardinality、CDF
  subaddress 命名与 endpoint 规则、74 logical steps 对 292 presentation-specific evaluations 的区分。

### 主要难点

科学难点是 canonical opaque rank 会成为 constitutive action/tie/CDF channel。它可保证同一固定 rank
下 presentation conformance，却不证明 rank relabel invariance 或完全匿名的 membership policy。
必须决定这是可接受的物理序列化约定，还是悄然改变了原机制。工程难点是以一个足够小的 oracle
实现 finite law，而不是搭建可选 kernel 菜单。

### 审阅模型应回答

1. exact bitwise physical-action conformance 是否由该 claim 真正需要，还是 distributional/decision-level
   conformance 已足够？
2. `ORC-B64-Q52-U64-V1` 是否是合理且最小的修复，还是把 opaque rank 提升为不应存在的行为通道？
3. 四个文档缺口闭合后，304-row A0 是否过大；哪个子集是决定性 falsifier，哪个是必要完整 gate？
4. A0 pass 后是否应立即运行一次 fresh R02 DEBUG，以免继续停留在无 return 的形式层？

### Claim ceiling

A0 pass 只支持固定 physical state、固定 episode opaque ranks 和冻结 scalar kernel 下的 finite-panel
co-presentation conformance，以及准备一次 fresh R02 DEBUG。它不支持 learnability、return、recovery、
一般 permutation invariance、任意 `N` 或 UAV 结论。

## CBSC — capability-bound semantic currentness

### 动因

CBSC 关注四个容易混淆的 public-history 轴：OWNER continuity、semantic epoch refresh、当前 carrier
capability、receiver-addressed content correctness。exact factorial 已表明，在冻结的一次机会协议里，
current correct content 与 executable capability 有狭窄原生价值；但 unrestricted RAW 与 CBSC rowwise
相等，所以没有 representation necessity。新的在线 B01 问题是：在 24-opportunity partial-observation
host 上，typed currentness adapter 是否让相同 recurrent PPO 在有限预算内更容易学会正确
`SERVE/REFRESH/SAFE_FALLBACK`。

### 机制预测与最强替代

- 预测：relation-aligned currentness register 更容易把最新 OWNER/epoch 与 body、receiver、capability
  组合，表现为 native return 和 endogenous action 改善。
- containing null：`RAW-GRU` 接收完整相同 primitive history，理论上能实现同一规则；STRUCT 的任何
  优势只能是 finite-resource learning bias。
- `PI-GRU` 控制普通 recency/index；`DERANGED-CURRENTNESS-GRU` 控制同结构/同工但错误语义配对。

### 当前证据

- exact factorial：36,864 rows、15 audits，狭窄 protocol value 成立，RAW equality 成立。
- offline `CBSC-LR01` 完整但 `UNRESOLVED`：三个 worst-block 指标为负，且 0/24 通过 STRUCT endpoint；
  既不支持 robust structured advantage，也不支持 practical equivalence 或 uniform inferiority。
- Online `CBSC-OMRC-B01` 的 host、recurrent PPO、3-seed B1、可选 2-seed B2、raw-publication 与
  Convergence responsibility 已冻结。
- B0 只做 instrumentation，绝对 nonpolar。B1 尚未运行。
- 本地完整 15-table chain 大部实现，但未提交且 `REPAIR_REQUIRED`。
- 最终 HIGH：consumer validator 仍可能接受“篡改 mechanical/RAW competence 后重新计算 self-hash”
  的 packet，因为它未从 bound raw evidence 独立重算 `compute_b1_mechanical`。
- 另缺 full-formal canonical payload 的 result-blind capacity projection。

### 主要难点

科学上，必须让 STRUCT 对 RAW/PI/DERANGED 的差异真正来自 currentness-aligned inductive bias，不能由
不公平参数、interaction、optimizer exposure 或 comparator incompetence解释。由于 host 高度合成，
positive 结果仍只是一个 finite-host B signal。工程上，当前最后的 consumer recomputation 是合理的
artifact integrity，但不应继续把 metrics-only publication 扩成替代真实 B1 的形式工程。

### 审阅模型应回答

1. 四臂设计是否足以区分 semantic currentness、generic memory/conditioning 和 predictive index？
2. host/return law 是否过度 stipulated，以至于即使 positive 也缺乏算法价值？
3. 修完 consumer recompute 与容量 projection 后，是否应立即运行 B1 三 seeds？
4. RAW 若不 competent，应如何最小修 learner，而不把 comparator failure误写成 STRUCT signal？

### Claim ceiling

只支持本 host、本 recurrent-PPO package、3/5 named seeds 的 preliminary signal、null、instability、
generic-control explanation 或 adverse counterexample。不支持 representation necessity、自然频率、
通信/credit、variable population、UAV、安全或部署。

## SCDMP — semigroup-consistent duration-model policy

### 动因

SCDMP 的核心不是“事件算子不交换”这一代数事实，而是 H→R 与 R→H 是否在一个 competent
order-erased foundation 上改变原生候选动作价值。新 B01 将 fixed-state/single-foundation 的旧
对象扩为 two foundations、six reachable first-legal-boundary state twins、`k={7,13}`、18 actions，
用 development tapes 选 matched/swapped/common candidates，再在 disjoint held-out tapes 上比较 raw
return gaps 与完整曲线。

### 机制预测与最强替代

- 预测：graph-matched action 在多个 foundation/state/k cell 上持续优于 swapped 和 strongest
  graph-blind common action。
- strongest null：order-erased foundation 加 common action 已吸收全部有用状态；H/R 非交换只改变
  内部 tuple，不改变决策相关 return。
- leakage null：若用同一 future tapes 选择并评价动作，表观 order value 只是 selector overfit；因此
  development/held-out tapes 必须分离。

### 当前证据

- 旧 FCEOV `.3` 是有效 nonpass，只关闭其 fixed-state/fixed-k/single-foundation 562-tape object；它不
  建立零或负 order value。
- Portfolio 以 B/EXPLORE 标准重新激活方向；Innovator 选择 `SCDMP-MF-RS-MK-ORDER-VALUE-B01`。
- 工程侧 telemetry race、atomic traversal、artifact-bound readiness 已修，full package `514 passed`，
  reviewer `CLEAN`，commit `92a3b7c2` 已推送。
- 首次 RUN-01 因 `telemetry_measurement_failed` quarantined，未读 outcome、无极性、未消费对象。
- 当前 science card 一方面要求 retry 不 redraw master/q，另一方面 quarantine 又禁止读取/复用旧
  master/q，导致没有唯一 replacement identity。Innovator packet 尚未形成外部决定。

### 主要难点

科学难点是 foundation competence、reachable-state construction、`k` 变化和 order treatment 必须
同时可解释；否则结果只说明某个 action ranking。流程难点可能被高估：这是 B/EXPLORE，A/B 本来允许
fresh named attempts。最新模型应挑战“必须复用同一 master”的规则是否把 B 错当成 one-shot C；
若未读 outcome，一个 fresh outcome-blind RNG identity 可能是更诚实的下一 attempt，而不是科学 recast。

### 审阅模型应回答

1. B01 是否真正测试 event-order value，还是仍混入 foundation/state/k selection？
2. replacement identity blocker 是否有科学必要；最小合法 fresh-attempt law 是什么？
3. 18-action development ranking + held-out evaluation是否足够防止 selector bias？
4. 当前最值得运行的是 action-value scout，还是应直接实现一个 policy learner/benchmark？

### Claim ceiling

只支持两个 foundations、六个 reachable cells、两个 `k`、冻结 simulator/action catalogue 下的
bounded exploratory order-value signal或反例。不支持一般 semigroup/duration policy、完整 support、
UAV transfer、安全或部署。

## UCOPE — uncertainty-conditioned observation and paid evidence

### 动因

UCOPE 将两个问题严格排序：先问 policy 是否会在 observable context 下为诊断 probe 支付真实
service/time/energy cost并获得外部价值；只有 acquisition 成立后，才问 protected COUNT 相对同信息
RAW 是否有 finite-budget representation residual。这样避免把“模型不会基本决策”误解为 acquisition
无价值，也避免把 COUNT 的统计充分性误写成信息优势。

### 机制预测与最强替代

- 预测：competent FLEX learner 在特定 context 选择 PROBE、其他 context 立即 commit，并在 held-out
  effective period 上获得正 external value。
- strongest null：RAW 包含相同 count 的充分信息；任何 COUNT 优势只是 finite-resource invariance/
  optimization bias。另一 null 是所有 package 共同受 optimizer exposure、conditioning 或 odd→even
  extrapolation限制，尚未达到 acquisition 可解释门。

### 当前证据

- 历史 R03 是 complete support failure；BELIEF v2 是 0/10 competence；structural certificate 只有
  17/20 tail-agreement pass。它们都没有 acquisition 或 COUNT/RAW 极性。
- 新 B1 包含 122,880 episodes、614,400 transitions、8,640 optimizer updates、18 policies、72
  checkpoints；三臂均 `0/3` competent，acquisition 未评价，COUNT/RAW 保持锁定。
- Pro Convergence 决定 `CONTINUE`，但退休 unchanged B1 repeat，只准 read-only odd/even A/RECON。
- retained odd-support audit：72/72 finite+unique，0 competent/near；FT-FLEX 对 BC 仅 update 160 有
  transient `4:1` clear，final 为 `3:2` 且无相邻曲线分离；MT 与 FT final 6/6 tail/root identical；
  across-arm similarity 只在 update 40 为真。旧 result map 未唯一覆盖该组合，route 为
  `MAP_NOT_UNIQUE_NEW_CONVERGENCE_REQUIRED`。
- 审计不能重跑；新 Convergence packet尚未发送，本地不能代决 lifecycle。

### 主要难点

现在的难点已经不是 artifact 或资源，而是研究价值选择：连续多个 competence-first对象都显示共同
learnability failure，但 package 间又存在短暂/异质差异，尚不足以简单断言“共同失败所以 PARK”。
必须在一个便宜 optimizer/conditioning discriminator 与停止投资之间作选择，且不能在 competence
之前重新打开 acquisition 或 COUNT/RAW。

### 审阅模型应回答

1. 当前 odd/even 证据是否已足够建议 PARK，还是 transient FT-FLEX/BC separation 值得一个新 B？
2. 若只允许一个新对象，应测试 optimizer exposure、target schedule、conditioning，还是更换 learner
   family？必须说明它怎样改变 Portfolio 决策。
3. 三个历史 family 的 competence failure 是否具有跨对象累积意义，还是 host/package差异使其不可合并？
4. UCOPE 与 CBSC 是否保持分离：CBSC 是 passive currentness，UCOPE 是主动付费干预；只有何种证据
   才支持融合？

### Claim ceiling

当前只支持本 finite host/package/budget 下 competence 未建立，以及 odd/even failure pattern。
不支持 paid information 无价值、COUNT/RAW 等价或优劣、一般 UCOPE、MARL/UAV、transfer、安全或部署。

## 跨方向审阅重点

### 不应轻易合并

- FRRIE 与 VNFC 都触及 variable `N`，但 FRRIE 是 fixed-roster finite-budget inductive efficiency；
  VNFC 是 episode 内 membership loss、physical action semantics 与 recovery return。
- CBSC 与 UCOPE 都涉及 information/currentness，但 CBSC 是 passive public-history encoding；UCOPE
  是主动、付费、改变后续信息集的 intervention。
- SCDMP 的 event-order value 与上述四者没有相同 estimand；它最多共享 telemetry/runner 工程。

### 可共享工程但不转移科学极性

fresh 4 GiB admission、Windows process-tree telemetry、create-once publication、quarantine、typed
checkpoint inventory、worker equivalence、immutable evaluation loading都可复用。任何方向的 positive/
negative outcome均不能随工程组件转移。

### 最新模型应重点挑战

1. 五方向是否把过多资源花在不会改变 B/EXPLORE 结论的 formal artifact contract 上。
2. 哪些方向已经有足够 ready 的 real learner/environment，应优先运行而非继续定义。
3. 哪些 direction-local问题其实只是一个 package/object 应关闭，而方向仍有新的可执行问题。
4. 无容量上限时应保持并行，但 Root attention 应优先给能最快产生有效 learner observation 的对象。
