# Sequences 02–12：候选局部工程侦察与单候选科学审计任务表

这是一份合并的语义交接文档，但不是把候选合并成一个科学对象。它覆盖原队列的 sequence 02–12，顺序固定，每次只处理一个候选。sequence 01 的 FOLR brief 已另行发布；三个 parked 候选不在本文件中，也不得执行。

Code Manager 对每项先做候选局部的只读工程侦察，判断实际代码、数据接口和有限实例能否承载该候选的最小判别器；随后准备一份单候选 External Pro 科学审计问题。完成一项后，先向 Explorer 返回自然语言结论和确切证据，再进入下一项。顺序是一种工作组织方式，不是文档格式 admission gate。

本文件不授予代码修改、训练、运行、实验或计算权限。缺少实例对象只能记录为实际 blocker，不能解释为科学 NO_GO。只读侦察也不产生候选的正负科学 disposition。External Pro 的科学判断、后续 toy contract 和任何计算授权仍分别遵循其当前权限边界。

## 02 — EC4G-R1 的执行行为差异普查

目标版本是 `CAND-VAP-EC4G-R1@adversarial-revision-v7`。当前只允许判断一个窄问题：七臂 receipt decomposition 是否在支持有效的单元中产生了不同于“使用完全相同估计量的 Direct-tau”的真实执行决策。若两者执行映射相同，或者差异只存在于标签而不改变动作，EC4G 的 operational gate 没有独立价值。

最小判别器是 `EC4G-EXECUTION-DIGEST-CENSUS-D1`：冻结 EC4G 与 Direct-tau 的动作映射和决策规则、可接受 receipt 域、相干的 arm mean/covariance 对象、成本、support/executor measure、fallback digest，以及 payload-preserving donor intervention，然后对有限域做零 rollout 普查。结果必须明确落入：完全等价、仅标签不同、行为不一致、合同不完整。只有支持上正质量的行为不一致，才可能为后续随机比较打开科学问题。

只读侦察需要找到并画出：receipt 的产生和 cross-fit 路径；七臂 mean/covariance 的绑定；EC4G 与 Direct-tau 的阈值、成本、uncertainty 和 fallback 输入；最终 action/digest 映射；support 与 executor measure；donor payload 替换是否保留除目标 payload 外的一切执行路径。特别检查所谓 uncertainty 是否只是估计误差或支持差异，而非 aleatoricity。

最强简单 null 是在相同 cross-fitted receipt、support、executor measure、成本和 uncertainty 输入下运行 Direct-tau threshold。若映射未冻结，差异为空、仅为标签、落在无支持或零质量单元，或者未来 outer upper bound 非正，应删除或停用 operational gate，而不是继续训练或 rollout。

建议 External Pro 审计：有限 receipt/action 域能否证明两种规则存在真实动作分歧；donor intervention 是否只改 payload 而未改变 estimator/support；两边资源和不确定性输入是否真正相同；若 D1 通过，什么独立 lower-bound margin 才足以允许外层随机比较。当前不支持 incremental gate value、event-source mutual information、executor invariance、partner-family transfer 或 adaptive-policy value。

## 03 — UCOPE 的 count-state 有效性

目标版本是 `CAND-VSP-07-UCOPE@adversarial-revision-v6`。最窄主张是：在一个冻结的有限 marked-renewal family 中，latent law 持续不变时，结构状态和 exposure 相同的历史可能仅因 first-hit counts 不同而需要不同的 Bayes-optimal next effective period；count-informed 策略必须切换，而 objective-matched count-blind null 在匹配历史上采取相同动作。在 homogeneous hazard 或每次独立重抽 latent law 的边界中，count 价值必须消失。

最小判别器 `UCOPE-COUNT-STATE-D1` 要精确枚举 16 个冻结历史，验证 matched action switch、count-blind failure、两个 zero-effect boundaries，以及 alias、censor、tape、state、identity invariants。应冻结 predictive kernel、带版本的 count/exposure state、recurrence unit、posterior score、physical-time AUC 目标、完整 effective-period quotient、共同 pre-outcome tape 和 count-blind structural-greedy null，并在运行前固定冷启动、tie-break、margin 和物理时间分母。

只读侦察需要定位：first-hit count 与 exposure 的更新位置和版本语义；period alias/censor 的规范化；动作候选和实际物理时长；posterior/score 计算；随机 tape 在 outcome 前的冻结点；AUC 的时间分母；structural-greedy null 可见的信息。还要确认 16 个历史是否能从实际状态构造，匹配历史是否真的共享完整结构状态和身份。

最强 null 是信息匹配的 structural greedy：按未覆盖的支持质量除以物理成本选择动作并使用确定性 tie-break。通过需要 count 导致匹配状态下的精确动作切换、null 失败、两个零效应边界不依赖 count、所有不变量成立，且精确 physical-time AUC 增益为正。若 persistence/version 不闭合、没有 decision-relevant count distinction、零效应边界仍敏感、结果依赖 alias/identity、使用 post-outcome tape 或 AUC 非正，应停止。

建议 External Pro 审计：16-history 表是否真的在固定结构状态下形成 count-induced switch；effective-period quotient 是否完整；count-blind null 是否在匹配历史上严格相同且两种零效应边界能擦除 count；physical-time AUC 的 estimand、分母和 margin 是否精确。当前不支持目标环境确实具有持久 latent law、任务回报改进、count acquisition value、joint exploration、online retirement、transfer 或一般 Bellman 有效性。

## 04 — ORBIT-LITE 的八单元 shadow-read

目标版本是 `CAND-VAP-ORBIT-LITE@adversarial-revision-v8`。这个候选现在只允许识别：在 owner match 固定且 provenance 经过认证时，payload content 是否与 role 发生 readout sensitivity 交互。它不能识别 owner-specificity、自然策略是否使用该信息、utility 或 coordination。

最小判别器 `ORBIT-8CELL-SHADOW-READ-D1` 是确定性的 `B × role × Q` 八单元 cloned shadow-read audit。`B` 只能来自 source-time sibling writes；必须冻结 owner/epoch/phase/clocks、writer sigma-field、共同 support 和 cell weights、byte-equivalent Q routing、ancestry replay、final-residual zero-marginal audit、equal-weight cloned reads，以及 immutable `P_c` fit/version receipt、role map、prior cache snapshot、current history、legal mask 和 read clock。

只读侦察要追踪 source-time sibling write、cache 内容与 provenance、owner/epoch 校验、Q 的字节级路由、clone 是否可变、role mapping、legal mask、最终 residual 和 strict temporal null 的全部输入。需要证明在 strict temporal/lookup null 中，`B` 的 payload bytes 和所有派生 metadata 都不可见，同时其他支持和权重不变。

最强 null 是按 role 匹配、owner-agnostic 的 temporal proxy，并允许完整 matched lookup-label 实现。通过需要 same-owner sibling B 可实现、support/provenance/epoch 闭合、Q 等价、temporal null 对 B 零可见、clone 不可变、zero-marginal closure 通过，并且若提出 interaction 主张，centered logit role×history interaction 非零。任一前提失败都应停止。owner-specificity 需要另一个 content-held-fixed owner-match factor；utility 和 natural use 也需要独立干预。

建议 External Pro 审计：sibling writes 能否只改变 same-owner history；Q 在八格中是否字节等价且 ancestry replay 足够；strict temporal null 是否真的擦除全部 B 路径；若 mixed difference 非零，在提出 owner-specificity 或 utility 前还缺什么精确检验。当前不支持 owner-private semantics、自然 policy use、task utility、held-out coordination 或 directed exploration。

## 05 — RECCT-LITE 的依赖非干扰闭合

目标版本是 `CAND-VAP-RECCT-LITE@adversarial-revision-v8`。候选只保留 semantics-free、orientation-paired signed-credit gate 的窄主张：`G_SD` 是 optimizer-matched 的 sign-destroyed direct null；只有精确 noninterference 成立时，才可能隔离 signed orientation information。primary gate 只能读取机器枚举的 pretreatment whitelist；outcome、audit、owner、semantic psi 及其 descendants 禁止进入 primary decision，semantic path 只能 shadow 运行。

目前条件化 nonanticipation theorem 和四 mask map 已写清，但没有实际实例证书。仍缺：机器可读的 field/tensor whitelist；模型、方程、目标、正则和 solver；optimizer/scheduler/scaler/clipping/accumulation；完整 fold/transformation ancestry graph；RNG seeds/namespaces/counters；阈值、margin 和成本；`G_SC/G_SD/G_SEM/G_pi` 映射；threshold/hysteresis truth table；partner/common clone manifests 及 conformance receipts。

只读侦察应定位 whitelist 和 tensor schema、mask 方程、fold/transform ancestry、optimizer 与 RNG clone、四个 gate map、literal-00 初始化，以及 real/shadow 与 partner/common clone 的数据流。需要逐字段回答 primary gate 是否能间接读取 audit、owner、outcome、psi 或 descendant。

最小下一步是在一个不可变实例上一次性检查：audit-seed/outcome substitution；preprocessing/fold ancestry isolation；orientation swap/order invariance；real-shadow equality 加 literal-00 hysteresis；hidden-input rejection、semantic isolation 和 dependency closure。出现未分类输入、不完整 ancestry、audit/owner 泄漏、psi-dependent primary mask、optimizer/RNG 不一致、real/shadow 不等或非 literal-00 初始化即停止，不进入 return-bearing discriminator。

建议 External Pro 审计：给定 whitelist/ancestry ledger 是否仍存在禁止路径；`G_SC` 与 `G_SD` 是否在 optimizer/update/RNG 上完全匹配；四 mask map 是否在 orientation swap 与 real/shadow 之间不变；什么最小有限 receipt 能反驳 noninterference 而不引入语义或回报主张。当前不支持 semantic mediation、real-churn correctness、retrospective responsibility、held-out cooperation、partner co-adaptation 或长期 utility。

## 06 — SCOPE-1S 的实际 Q16 证书

目标版本是 `CAND-VAP-SCOPE-1S@adversarial-revision-v7`。窄主张是：在一个实际 Q16 same-current-context 单元中，完整 historical carrier 包含所有 behavior-reachable current-only bytes 都没有的 outcome-relevant information。`X` 必须是行动前 current-only ancestry 的字节完备集合，`K` 是精确 compatibility key；audit labels 和 prior descendants 除了注册 carrier 外不得到达行为路径，actor/writer/reader/injection/normalization/partner/RNG tape 的 policy-generation distance 为零。

现有有限 witness 只证明逻辑一致性：same-X crossover 可取 `[[60,-4],[-4,60]]`，reversal gap 64，TV=1，current-only optimum 32，正确 import 60，derangement 28；它没有证明实际 Q16 存在这些对象。仍缺 byte-level X ancestry manifest、逐 cell 的 X/K/support 与 target-donor counts、实际 same-X crossover matrix、完整 current-only Bayes-envelope 枚举、无固定点且执行路径相同的 donor permutation、H=64 interference certificate 和 zero policy-generation-distance 证据。

只读侦察应追踪 Q16 cell/carrier 的所有 bytes 和 ancestry、X/K/support 表、current-only comparator 的完整信息、donor 选择与注入路径、H=64 的 spillover，以及 actor/partner/normalization/RNG 的版本和更新距离。必须识别一个有正支持的 same-X、outcome-divergent pair，而不是用抽象矩阵替代实际实例。

最小检查一次性验证：X ancestry 完整；support/compatibility；same-X crossover 和 TV；完整 X-measurable Bayes envelope；target-independent donor path；H=64 interference closure。X 不完整、没有支持上的 crossover、Bayes envelope 追平 candidate、donor/path 或 interference 闭合失败，都只影响本候选并停止升级。

建议 External Pro 审计：X 是否真为字节完备 current context 且排除历史 payload；Q16 中是否存在实际 same-X alias pair；完整 Bayes envelope 是否封住了 current-only 能力；donor derangement 与 H=64 spillover 能否在零 policy distance 下无泄漏地闭合。当前不支持 target-instance identifiability、historical-information necessity、broad transport、utility 或 semantic interpretation。

## 07 — EOCIV-LITE 的四臂校准与路由闭合

目标版本是 `CAND-VAP-EOCIV-LITE@adversarial-revision-v8`。只允许估计注册范围内的四臂交互：`Γ=(μ_LS−μ_LR)−(μ_CS−μ_CR)`，其中 LS 是 learned-selective，LR 是 learned-always-real，CS 是 constant-selective，CR 是 constant-always-real。selector 只能看到冻结的 `W−`；每次 receiver write 前必须先经过 native neutral；current payload、future outcomes 和 arm identity 禁止进入 selector。

arm semantics、target-independent semi-Markov null、HARD_OPEN 和 zero-Jacobian 要求已写清，但没有实例化 clocks、folds、kernels、critical graph、margins、routes、test vectors 或 receipts。仍缺 frozen trigger/cluster ID/exact H/event clock；lifecycle function/support cells/W− allowlist；native-neutral kernels/physical envelope；四个 ancestry-disjoint 数据池；threshold grids、`q_c` 和 semi-Markov kernels；sham-score kernels 与 balance tolerances；critical graph/deadlines/HARD_OPEN table；所有 margins、α、return scale 和 simultaneous procedure；parameter/recurrent-write graph；payload vectors、common tapes 与确定性 receipts。

只读侦察应定位 trigger/clock/lifecycle、四臂 route table、四个 fold ancestry、native-neutral 与 semi-Markov null kernel、sham-score balance、critical graph/HARD_OPEN deadlines，以及 parameter write/gradient graph。重点证明 LR 与 CR 的 always-real 行为在 target-independent null 下等价，并确认 learned selector 没有 current/future/arm leakage。

最小检查依次验证 payload-pair closure、LR≈CR always-real equivalence、selective-arm exhaustive mapping、gradient/pre-actuation route closure 和 outcome-sealed-null conformance。arm 含糊、fold overlap、缺 native neutral、critical graph 无支持、clock 不完整、margin 不唯一、gradient 未闭合或 LR/CR 不等，都应停止。

建议 External Pro 审计：四臂 payload 与 clock 是否严格定义；fold ancestry 和 W− allowlist 是否排除全部泄漏；native-neutral、HARD_OPEN 和 zero-Jacobian 是否可机械见证；support、simultaneous margins 与 sham-score balance 是否足以识别 Γ。当前不支持 broad causal credit、semantic coordination、partner adaptation、一般回报提升或跨任务迁移。

## 08 — ROSTER-SMF-BI 的 access/resource fork

目标版本是 `CAND-VAP-ROSTER-SMF-BI@adversarial-revision-v6`。科学对象是互斥的访问/资源分叉：如果在匹配资源合同下可以完整、原子地读取 roster，就应使用 exact census total，并淘汰生产 HT estimator；只有当 sampling necessity 被证明、inclusion probabilities 已知且为正、estimand 是注册的线性 pre-transform total 时，Horvitz–Thompson 才保留。任何 unbiasedness 都不能自动穿过 nonlinear policy transform。

符号上，full access 使用 `A ∧ F ∧ C_all`，sampling 使用 `A ∧ G ∧ U ∧ C_selected ∧ ¬C_all`，但两支都未实例化。仍缺 feature-node access registry、atomic snapshot、G0 sampler dependency/commit record、componentwise `R_max`、匹配的 `R_all/R_selected` ledgers、summary-gradient/autograd contract、exact-aggregate service record、access-trace semantics、linear estimand 与 protected/bulk-frame binding，以及完整 sampling support 和 `pi_i/pi_ij` 表。

只读侦察需要追踪 roster snapshot 到 feature acquisition、exact aggregation、summary 和 autograd；判断全部 roster rows 是否能在行动前合法寻址或流式读取；记录 full 与 selected access 的峰值内存、带宽、延迟和 gradient-edge exposure；确认 sampler 只读取 cheap G0 字段并在 expensive read/prefetch 前 commit；找到线性 pre-transform total 和第一个 nonlinear consumer。

最强 null 是同 snapshot、actor path、gradient mode 与 common-plus-marginal resource ledger 下的 `FULL_ROSTER_STREAMING_TOTAL`。绑定十个对象和一个组件级资源上限后只评估一次 access truth table。full access 通过即采用 census 并退休 HT；否则 HT 只有在 immutable population、positive known inclusion、linear estimand、forbidden-access exclusion 和精确算术全部通过时才可保留。support、inclusion、snapshot 或 access 失败则停在本候选。

建议 External Pro 审计：两条 access predicates 在实例绑定后是否互斥且穷尽；证明 full-roster streaming 或 exact aggregate 超出资源上限所需的最小证书；adaptive sampling without replacement 下 HT 需要哪些 frozen population/owner-epoch 条件；任何 nonlinear downstream proposition 是否可识别。当前不支持 census 可用时的 HT superiority、nonlinear design-unbiasedness、broad roster robustness、task value 或跨 regime transport。

## 09 — VSP-02 的八状态 escrow oracle

目标版本是 `CAND-VSP-02@adversarial-revision-v8`。最多能保留的主张是：exactly-once ledger、absolute-target transport 和 raw-gradient calculation 可作为 conformance objects；它们不证明 physical duration actionability 或 adaptive value。candidate-specific duration 优势在 exact same-information、full-horizon tabular selector 下尚未识别。

符号上已有五分支 absolute-target 与 conservation 公式、raw gradient `μ_x p_x(1-p_x)[Q_x(L)-Q_x(S)]`、W+ reward-level crossing `Δ_F=-γ/2, Δ_P=γ/4`、W0 pathwise equivalence/zero-gradient counterexample，以及 exact tabular nesting。但 literal total transducer 与实际物理世界缺失。旧的每世界 20-path 计数并不穷尽：必须证明 canonical quotient 和 ignored-bit invariance，或者改为每世界 32 valid paths 加 32 version-invalid mirrors，W+/W0 共 128 base paths，再另加 mutation cases。

仍缺 total escrow transition function、具体 W+ physical-state kernel 与 W0 instance、target objective/bootstrap binding、event/release/tombstone/version-closure schemas、完整 timing tensor/selector schema、冻结的 primitive/partner policies 与 tapes、正确 coverage roster、代数独立 conformance fixture，以及 simultaneous interrupt-natural 和 owner-departure fixtures。

只读侦察应定位 escrow state enum 与总事件转移、ownership/idempotency/tombstone/release；检查 `INTERRUPT` 优先于 `NATURAL`、`TERMINAL` 优先于 `HORIZON`、全部 records close 后才推进 version；追踪 target、bootstrap、behavior/target version 和 raw gradient；确认 short/long duration 是否在 W+ 改变实际 primitive trajectory、在 W0 保持相同；审查测试生成器的 tape bits 和路径数；确认 candidate 与 tabular null 共享全部 predecision information 与资源。

最强 null 是 `HORIZON_FLUSH_TABULAR_DURATION_NULL`，包含相同有限 predecision information 上的所有合法映射。最小下一步只运行 deterministic oracle：总状态/事件覆盖、exactly-once score/release、target、conservation、gradient、W+/W0、null nesting、路径覆盖和 precedence/version mutations。转移含糊、重复/缺失 score、target 错、非法 bootstrap、stale version、非法共享路径、零 physical/value contrast 或 exact-null reproduction 都应停止。

建议 External Pro 审计：八状态事件优先级是否构成 total exactly-once transducer；128-path 是否穷尽或能否严格 quotient；absolute-target/gradient 公式在 semi-Markov clock 下是否仍成立；在 exact tabular nesting 下，什么最小资源限制才产生 candidate-specific prediction。当前不支持 adaptive superiority、nominal duration 即 physical actionability、生产环境非零 gradient、partner co-adaptation 或广泛泛化。

## 10 — VSP-04 的三模式有理 knockoff 证书

目标版本是 `CAND-VSP-04-MATCHED-BOUNDARY-REQUEST-TRIAD@adversarial-revision-v8`。authentic request 相对 path-matched null 可以讨论 provisioned channel 下的 package value；某个具体 generic predictor 相对 null 可以讨论该 predictor 的 admitted value。但在 exact decision equivalence 下，`T-K` 只能是应为零的 conformance quantity，不能识别 provenance、intent 或 request semantics。

一般有理证书已经明确：同一个 `q_h(w)` 必须在 IND、OR、SOFT 三种模式上共同满足堆叠系统 `Aq=b, 0≤q≤1`，同时匹配 raw propensity、完整 post-interface path mass 和每个 action-specific risk mass。不可行性可由有理向量 `y` 证明：`yᵀb > Σ_j max(0,(Aᵀy)_j)`。现在没有有限 coefficient matrix、witness 或 separator，因此可行与不可行都未实例化。

仍缺 finite H cells 与 rational weights；显式 G 声明和 W cells；U/proxy/request-descendant closure ledger；冻结的 IND/OR/SOFT interfaces 与 nonsaturation branches；legal actions 和完整 asymmetric loss vectors；有理 propensity/path/action-risk tables；positive support floor `η`；receiver policy/recurrent state 与 shadow-R bindings；timing/ordering/metadata/cost tables；finite rational random tape；以及 `q_h(w)` witness 或 dual separator。

只读侦察要追踪 receiver 在 checkpoint 前可见的状态、recurrent tensors、非焦点消息/缺失、时间戳、排序、roster version 和 checkpoint identity 以闭合 H；追踪 generic K 的所有输入和训练更新以证明它只使用 W 与独立冻结 tape；审计 source state、request logits、identity、metadata、queue/retry/ack 和后续行为造成的 U 泄漏；检查三种 interface、support 与 saturation；定位 legal actions、loss table、receiver clone 与 shadow-R invariance。N 必须是 path-matched decision-null carrier，而非简单 literal silence。

最强 null 是一个 W-measurable K，同时在三模式中匹配 propensity、path mass 和完整 action-risk vector。最小下一步是在不事后扩充 features 的条件下物化一个 immutable rational instance，并只求解一次固定系统，返回完整 witness 或精确 dual separator；witness 还必须通过 common support、path、recurrent state、shadow-R 和逐 cell/aggregate `T-K=0`。closure 含糊、使用排除信息、support/path/adaptation/recurrence 不匹配或任何精确非零 residual 都应停止。

建议 External Pro 审计：path mass 加完整 action-risk matching 是否足够且必要；三模式的最小 finite branch representation 如何避免积分掉非焦点输入；dual separator 必须暴露哪些行才能排除 discretization/omitted support；零 conformance 应逐 cell 还是仅 aggregate。当前不支持 request provenance、intent、semantic source value、individual causal credit、cross-partner meaning 或 relearned convention value。

## 11 — VSP-05 的有限 census semantic veto

目标版本是 `CAND-VSP-05@adversarial-revision-v7`。只允许在一个预注册、有限、single-owner、monotone service-completion event census 中，比较 stateless allowlist-only saturated lookup veto 与 no-veto hard gate，目标是降低 lineage-weighted alias-first-latch risk，同时满足冻结的 true-acceptance 和 physical-delay 约束。MLP-specific value 已无科学必要；handoff safety 是独立的 exactly-once 义务，不能从 veto 指标推断。

符号上已经分离 finite-support choice、MLP-to-lookup representational equivalence 和 semantic veto/physical handoff，但没有注册实例。仍缺 E_SC1 event 与 ex-ante base-lineage registry、finite tuple schema 和完整 `X*` census、固定 intervention registry、去重有序 opportunity tapes、current-time label provenance、identical-tuple contradiction/fold-support 表、teacher/student taint proof、canonical lookup、acceptance/risk/delay margins、sequential-oracle feasibility，以及实际 handoff transition/model-check object。

只读侦察应追踪 event parser、immutable-token deduplicator、tuple serializer 的全部输入、teacher-label provenance、shared encoders、recurrence、normalization、sampling、calibration、threshold/checkpoint 路径，以及 safe-wait/handoff interface 与 atomic public commit primitive。必须确认 teacher/student 间只允许 cross-lineage scalar labels，且结果 registry 不是看过 outcome 后选择的。

最强 null 是完整 finite tuple domain 上的 saturated exact lookup；MLP 只作 diagnostic，下游 comparator 是 no-veto hard gate。最小下一步先冻结 registry、tuple domain 与 tapes，再建立直接 `x -> {Y}` 表。任何 tuple 同时出现两个 labels、fold support 退出或 registry outcome-selected 都立即停止。只有 singleton-label、support-closed census 才继续做 taint、invariance、sequential 与 handoff 检查。通过还要求 age/occupancy/frame-refinement invariance、可行 deterministic tuple rule、所有 margins 通过，并且 handoff 在错误 ack 和 adversarial latch 下仍 exactly-once safe。

建议 External Pro 审计：runtime tuple 是否确定 current-time label；taint graph 是否排除 clock/outcome/teacher/recurrent/selection leakage；ordered tapes 与 margins 是否避免 opportunity multiplicity 伪造改进；handoff transition 是否在错误 ack 下保持物理安全和 exactly-once ownership。当前不支持 MLP superiority、open-support generalization、sample efficiency、E_SC1 外的语义身份、recurrent inference、partner adaptation、cross-class transport 或从 veto 推导 handoff safety。

## 12 — MSSR 的 pre-action persistence 闭合

目标版本是 `CAND-VSP-06-MSSR@adversarial-revision-v8`。historical `P` persistence 只有在完整 persistent-state closure 中存在一个支持上的 pre-action residual，且 full current action-visible context 无法重建它时才保留。条件式

`Δ_KB = C_A W_P [r_P(P-) - r_P(B_P(X0,q_b))]`

精确决定第一次动作中 KEEP 与 current-rebuild 的 policy equivalence。另一个独立问题是候选 gate 是否不同于 factorized closure：

`G_FACT(u_F,u_S,u_P) = (u_F u_S u_P, u_S, u_S u_P)`。

若两者在所有支持输入上相同，gate-selection novelty 应独立退休。现有 nonzero binary witness 只证明逻辑可能，不证明实际 MSSR 有相同 support 或路径。

仍缺实际 S/P/F 的语义、owner、dimension 和 byte layout；完整 persistent-state census 与 read/write DAG；legal worlds 和 KEEP/RESET/FORCED_CONTENT；current-free `N_S/N_P/N_F`；完整 current-context key 与 `B_P` table；真实 action head、`r_P/W_P` 与 schedule；支持上的 identical-current/distinct-P pair；`G_MSSR` truth table；non-target equality、frozen partner、paired RNG 和 finite-precision tolerances。

只读侦察要枚举每个 persistent buffer、cache、normalizer、router、external memory、RNG state 和 actor-visible side channel；导出 dependency-closed intervention；检查 current-free initializers、完整 `B_P`、P 到第一次 action 的直接路径、recurrence 前的评分时序、legal masks/gates，以及 partner/parameters/gradients/normalization/RNG 的冻结。关键是确认 P 未在 readout 前被覆盖，且存在完全相同 current context、不同历史 P 的正支持 pair。

最强 persistence null 是 `P_CURRENT_REBUILD`：完整 current-visible context 上的冻结确定性 lookup，输出与 KEEP 相同 support 的 P representation；gate null 是上述 `G_FACT`。最小下一步先绑定完整 manifest 与 DAG，再对一个 preregistered CHANGE_F pair 计算 centered residual 并比较完整 truth table，不 rollout、不训练。manifest 不完整、P 在 closure 外泄漏、P 被覆盖或 action-null、无共同支持 pair、current rebuild 与 KEEP 等价、residual policy-null，或 candidate gate 在全部支持上等于 factorized gate，都应停止相应主张。

建议 External Pro 审计：manifest/DAG 是否足以保证 intervention closure；实际时序中 centered residual 是否为 recurrence 前 policy separation 的充要条件；common-support pair 与数值规则是否真实；`G_MSSR` 是否在任何 reachable supported cell 与 `G_FACT` 不同。当前不支持实际 historical-P persistence、semantic memory、learned-detector necessity、独立 F/S/P 语义、task value、cross-partner transport 或 broad multiscale utility。

## 每项回传与队列边界

每完成一个 sequence，请先在 `docs/project/handoffs/code_manager_to_explorer/` 写自然语言优先的候选局部结果，或向 Explorer 任务 `019fc29d-ef93-7681-abba-2b9d63a866cf` 发送原生消息。结果至少应说明：实际代码/接口位置、只读数据流重建、可用或缺失的实例对象、建议的单候选 External Pro 审计边界，以及为什么当前工程观察尚未构成科学 disposition。

返回一项结果后再继续下一项；不要跨候选复用未审计的实例、support、null、证据或结论。任何运行、修改或计算都需要在相应单候选科学合同冻结后，由现行权限另行决定。
