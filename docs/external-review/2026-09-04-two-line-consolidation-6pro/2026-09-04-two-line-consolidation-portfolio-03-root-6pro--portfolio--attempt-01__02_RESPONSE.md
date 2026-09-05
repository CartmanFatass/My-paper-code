**请求 ID：** `2026-09-04-two-line-consolidation-portfolio-03-root-6pro`
**Packet 固定参考：** `CartmanFatass/My-paper-code@b35eadf954a0bc56f3291f3b3d2b9ece0748e4a9`

# 最终 Portfolio 决定

**采用两父线整合，但修改候选方案对 VNFC R03 的保留：本轮仅保留 FSD E3 与 FRRIE contact-active R128 R02 两项既有科学投资；VNFC R03、CBSC online B1/r07 与 UCOPE 数值审计均暂时 PARK。**

这是本次“两条紧凑研究线”目标下的**可逆边际投资判断**，不是对各方向科学价值的总体排序，也不是以缺少 headroom、证明、完整能力或技术就绪为由否定 B 类研究。VNFC 的合法因果普查、CBSC 的协议价值、UCOPE 的正付费获取信号都必须保留，不能因 PARK 被改写为负结果。

```text
FINAL_PORTFOLIO_DECISION =
  ADOPT_TWO_LINE_CONSOLIDATION_WITH_VNFC_R03_PARKED

DECISION_AUTHORITY = PRO_FINAL
DECISION_FORMED = true
BLOCKER = NONE
```

本节点已形成最终决定。以下是应记录的组织和投资状态；**本回复没有修改仓库，也没有恢复或执行实验。**

## 1. OWNER_DIRECT_CONSTRAINTS 与 TWO_LINE_STRUCTURE

Owner 已直接决定：整合为灵活 agent 数量与灵活 skill duration 两条资助父线，相似研究收为子方向，并允许暂时撤回较低优先级投资。当前 packet 又明确授权这一目标内的可逆重组和 PARK，因此旧有“不批量 PARK、不融合、五条独立 DM 链”的安排不能否决本次实施。具体来源处置与对象排序，是本节点在该授权内作出的判断，**不冒称 Owner 已逐项点名，也不另造一次批准等待。**  

| 唯一资助父线                    | 研究组织范围                                          |    来源数 | 本轮保留投资                        | PARKED |
| ------------------------- | ----------------------------------------------- | -----: | ----------------------------- | -----: |
| `flexible_agent_count`    | 已见 roster 上的集合／关系表示；成员变化后的恢复、状态保留与配置机制储备        |     12 | FRRIE contact-active R128 R02 |     11 |
| `flexible_skill_duration` | 中断与续约；duration-conditioned value、事件终止、获取与信用机制储备 |     10 | FSD E3                        |      9 |
| **合计**                    | **恰好两条资助父线**                                    | **22** | **2 个 ACTIVE_SUBDIRECTION**   | **20** |

这里的来源数包含下文标明的**行政保管储备**。这些条目只被分配证据保管责任，尚未被认定为 N 或 duration 科学问题；两线均可引用其适用资产。**共享 PARKED 储备不是第三条资助线，也没有独立常驻 DM。**

新 N 父线是组织节点，不是旧 VNFC 的改名，更不是第 23 个新科学对象。duration 父线沿用既有 ID，但不因此改写其 D2/E 系列含义。未来明确恢复执行后，每条父线各一条常驻顶层 DM 链；不增设子方向永久 DM 链，也不增加固定的嵌套 worker 或实验数量上限。当前执行暂停保持不变。

N 对象把 duration 固定为声明参数；duration 对象把 N 固定为声明参数。跨线复用不合并结果，不产生联合 variable-N-plus-duration 算法。

## 2. SOURCE_DISPOSITION_TABLE

下表每个既有来源 ID **恰好出现一次**。`ACTIVE_SUBDIRECTION` 在此表示暂停期间仍保留未来投资位置，**不表示正在执行**。重入触发是重新考虑投资的条件，不是自动启动许可，也不是新增的全局 B 类准入门槛。

全表的共同事实基础是候选的两张 22 来源表及固定参考下的 Portfolio 生命周期记录；更具体的原始说明列于 EVIDENCE。

| 来源 ID                                              | 父线／子族；投资处置                                              | 支持本次处置的证据                                                                               | 必须保留的相反证据／限制                                                                                                       | 保留对象或重入触发                                                                                                                                                      |
| -------------------------------------------------- | ------------------------------------------------------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `finite_resource_relational_inductive_efficiency`  | **N／集合与关系权重约束；ACTIVE_SUBDIRECTION**                     | 三个完整 512-update 根均未触发 tight projection；R02 直接检验这个已定位的非激活问题，已有冻结卡与后续远端就绪记录。              | 激活不等于关系特异性；可能只是通用收缩。EDGE 比较器仍可能偏弱，且当前只在已见 `N={9,15}` 上训练、评估，不是 held-out N 迁移证据。                                    | **仅保留既有 contact-active R128 R02**，不重复旧无接触根，不预订下一阶梯。                                                                                                            |
| `variable_n_fleet_churn`                           | **N／成员损失恢复与因果控制；PARKED**                                | K1024 只修复一处剪枝损失并追平控制，没有增加 headroom 下界。R03 尚未实现，回答的是受限因果策略类，不是 MAPR 学习器效果。               | R03 已从全未来 tape 搜索改为合法历史的一次偏离，确有不同的识别价值；zone-2 row-3 的 `7/60` 个别见证仍成立。不能说该普查无用。                                     | 当 N 线的当前选择真正转为“是否投入该成员损失恢复 host”，且 R03 的稳健／局部／无 material headroom 分支会改变选择时，重新考虑**原 R03**。保留 second-recast；不自动开启 MAPR、宽 K 或多偏离搜索。                               |
| `roster_consistent_latent_exploration`             | **N／成员变化后的状态保留与重建；PARKED**                              | 当前 TBCFV 无结果，也没有当前 host 的 upper／tuned-generic 配对；不维持独立推进链。                              | 精确重算关闭的是信息必要性主张，不是有限工作量下的恢复价值。                                                                                     | 在实际成员变化 learner 上，persistent-common 与 containing FLEX 的保留／重建比较成为下一项决策相关干预。                                                                                     |
| `vap_folr_core`                                    | **N／成员变化后的状态保留与重建；PARKED**                              | B3 writer competence 与 generic baseline 尚缺；既有 B1 中简单 latch 的均值高于 S03。                   | 技术接受的 B1 确实记录了记忆使用：S03 `0.85205` 对 RESET `0.5`；latch `0.97021`。也不能说 latch 每个 seed 都更好：93038 反向。该索引并非已完成的科学 intake。 | 实际恢复问题需要保留状态时，以简单 latch 为重要控制，明确 writer 与同信息 generic 的比较；不把 B1 改写为 typed-memory 优越性。                                                                           |
| `degraded_incumbent_shadow_handover`               | **N／恢复时的状态来源选择；PARKED**                                 | RETAIN/COPY/SHADOW B01 无科学结果；C03 因冻结测试未被 checkout 而零收集，代码仍未接受。                          | source review 曾通过；checkout 问题是技术依赖，不是 shadow handover 的负科学证据。                                                      | 共享恢复问题中，首次触发时选 RETAIN、COPY 或 SHADOW 成为关键未知，并解决既有 checkout 依赖；当前不为此另开维护链。                                                                                       |
| `vsp_02`                                           | **N／保留与重建中的 optimizer-state 干预；PARKED**                 | 旧 host 的匹配终端 greedy gap 精确为零，且没有成员变化事件。                                                 | 终端相等不说明瞬态学习路径相等；carry/reset 仍可能影响恢复速度。                                                                             | 只在实际成员变化 learner 上，作为 Adam CARRY/RESET 的有界干预重入，保留瞬态曲线而非另建独立方向。                                                                                                 |
| `metric_ground_transport_allocation`               | **N／配置几何；PARKED**                                       | 两个旧 C 对象都在 efficacy 前停止；ORACLE 存在，但没有有效的最终 FREE 比较结果。                                   | 物理几何与严格包含的 FREE 对照仍是有用资产；不能从未运行的比较推出 metric 无效。                                                                    | 某个保留的 N host 确实受耦合配置几何限制时，再考虑 METRIC/FREE 的有限预算比较；不恢复旧 C 对象。                                                                                                   |
| `capability_bound_semantic_currentness`            | **N 行政保管／currentness 共享储备；PARKED**                      | 当前 online B1 尚未建立与 N 或 duration 行动／回报的具体联系；r07 未创建。旧精确协议中 CBSC 与 unrestricted RAW 逐行相同。 | 协议价值真实为正；RAW 包含不否定有限资源学习优势。r06 是解释器失败，修复与远端 readiness 已通过，是重要可复用资产。                                                | 先给出成员变化或续约场景中“currentness → 合法动作／原生回报”的具体联系，并说明原 online B1 能否原义回答。需要改变 host／estimand 时另立前瞻对象，不把它冒称原 r07。                                                       |
| `acvc`                                             | **N 行政保管／历史 veto 与信用共享储备；PARKED**                       | 两个先前 learner 均输给固定控制；证书区间 `0.0221975 < 0.25 ≤ 0.2990524` 仍未决。                           | 合法历史的正动作价值已经精确成立，不能广泛关闭历史价值。                                                                                       | 先有保留 host 对 history-aware veto 的实际需求；沿旧证书家族重入仍须满足其既有 lower／upper 证书重入边界，保留 second-recast，不重开被停止的 learner 或 full-DP 对象。                                         |
| `scope_1s`                                         | **N 行政保管／记忆与信息切断共享储备；PARKED**                           | Q16 的 `60−32=28` 来自信息集差异，不是同信息算法优势；无真实 learner 或 tuned generic 配对。                      | 该精确信息切断控制仍有价值。                                                                                                     | 某条保留线的真实信息流确实需要该 carrier/current-only/deranged 对照时再用，不单独构建基础设施。                                                                                                |
| `orbit_shadow_read`                                | **N 行政保管／角色与记忆共享储备；PARKED，延续既有状态**                      | 有 owner-role action-kernel 敏感性，没有 return-bearing learner 对象。                            | kernel 可行动性及 role-blind／validity-only 控制应保留。                                                                       | 出现独立的原生动作／回报后果，并有匹配 owner-role、owner-blind、validity-only 比较。                                                                                                   |
| `active_post_churn_population_flow_identification` | **N 行政保管／独立 population-flow 储备；PARKED，延续既有状态**          | 当前 CCF 退化为 two-event XOR/DFA，不因名称含 churn 就归为 N 算法。                                      | 独立的 non-reducible censored-flow 问题仍未被否定。                                                                           | 满足既有重入要求：匹配低阶边际但需要相反原生动作／回报、且能区别于 competent low-order controller 的非 XOR／非 DFA 构造。                                                                              |
| `flexible_skill_duration`                          | **duration／policy-gap 中断与续约；ACTIVE_SUBDIRECTION，兼父线来源** | E3 已有 `10/18` 有效单元，保留的异质 hazard 比较直接对应 duration 行动与原生回报。                                | E2 为有效 `NEITHER`；改变段长不保证事件对齐或收益。`c=0.25` 来自 E2 后的探索选择，不是独立确认。                                                      | **仅保留原 E3**。既有下一单元仍为未创建的 `medium_d0_seed3`；八个未启动单元不在本次启动。全 18 单元有效前不判 aggregate branch。                                                                        |
| `semigroup_consistent_duration_model_policy`       | **duration／跨 k 价值共享与 D8 比较；PARKED**                     | A01 只建立单向 `k=13` 偏好；A02 在完整事件相位人口成立前按规则停止；当前 D6 家族已有明确 Pro PARK。                        | A02 没有 duration-policy contrast，不是反对抽象 D6 架构的证据；独立人口中的事件相位价值仍可能存在。                                                 | 必须是 A01/A02 source/countdown 搜索谱系外、结果前提出的不同 native-action-linked 机制；满足条件仅重开原 Convergence，不直接授权对象。                                                              |
| `commitment_residual_triggered_options`            | **duration／residual interruption 备选干预；PARKED**          | B01-R1 为 `BR-E / COMPARATOR_WEAK`；尚不能识别 residual 优势。远端 materialization 失败未产生新观察。        | RAW 存在 SHORT 与 LONG 之间 KEEP／REPLAN 能力翻转，checkpoint-phase 不稳定是具体而非泛泛的替代解释。                                          | 当 residual versus policy-gap 真正成为 duration 线的下一判别时，再考虑既有 RAW-only `252..264` trace；它只诊断 RAW，不给 residual 效果或自然 KEEP prevalence 结论。                              |
| `vsp_03`                                           | **duration／事件终止控制；PARKED**                              | 当前没有实例化 return host、upper 或 tuned baseline，不维持单独 host／DM 梯级。                            | one-hit、dwell、debounce、hysteresis 是合理控制，不因 host 缺失而被否定。                                                            | 在既有 duration 研究中成为必要的事件终止控制时重入；不因此自动打开 E4 或新独立方向。                                                                                                              |
| `ucope`                                            | **duration／获取—续约候选接口；PARKED**                           | 当前审计仍在数值／root 诊断链内，未建立与本轮 duration host 的具体联系；审计实现另有 `98/295=33.22%` 的 scope blocker。   | PA-B 中 5/6 策略取得 `+0.021437` 净获取值；后续覆盖修复 tail，却引入错误 paid roots，完整能力仍为 3/6。不能抹去 PA-B，也不能把不完整能力当成该 B 结果无效。            | 明确“购买信息改变续约／duration 决策”的实际问题，且当前 root 诊断对它必要，再重新考虑最小审计或另案对象；不额外批准 orchestration 例外，不移植 oracle-signed shaping 为部署目标。                                           |
| `vsp_c1`                                           | **duration／period representation 与组合控制；PARKED**         | identity-by-period toy 尚无可执行 return population，也无 headroom 两项。                          | held-out composition 是合法问题，缺少生产 host 不是机制负结果。                                                                      | 只作为既有 duration 研究所需的组合控制重入；固定 N，不扩成联合 N+k 家族。                                                                                                                  |
| `eociv_lite`                                       | **duration 行政保管／receiver-addressed credit 共享储备；PARKED** | B10 增加固定向量曝光未救回绝对 receiver 表现；当前 receiver-addressed 家族已局部 PARK。                         | 相对 `J` 随曝光增大，A1 初始化有正局部信号；这不是“receiver 内容普遍有害”。                                                                    | 某条保留线需要一个真正不同的信用机制，并遵守原家族 PARK；不以相对收益或加曝光为由重复现有家族。                                                                                                             |
| `recct_lite`                                       | **duration 行政保管／target intervention 共享储备；PARKED**       | one-port host 上 LR/RL pointer 变化没有 target effect，当前 upper 与 generic 配对均缺。               | 只关闭该 host 的等效干预；不能转移 EOCIV 的极性。                                                                                    | 保留 learner 上出现 consequence-distinct 的 LR/RL/no-update target 干预，并能测到近端变化及下游回报。                                                                                 |
| `ec4g_r1`                                          | **duration 行政保管／receipt-content credit 共享储备；PARKED**    | B1 activity aggregation 无效，不能填补 native-return headroom；结构差异不等于学习收益。                     | leave-cell 行为的结构差异仍是可用机制线索。                                                                                        | 在保留线的实际 receipt stream 上做必要的 content ablation，并有有效同信息控制；不另建独立基础设施链。                                                                                            |
| `expressibility_gated_renewal_credit_relay`        | **duration 行政保管／关系分解信用共享储备；PARKED，延续既有状态**              | generic critic 赢得所有直接估计诊断；当前 factorization 已被 Pro PARK，且算术工作不等，不能声称效率优势。                | factorized 温度一精确 utility 高约 `0.0120448`；两臂均 8/8 greedy competent、sampled utility 相同，不能删除该正差。                       | 仅接受另行授权、前瞻定义的新机制：共同 calibration/trust 下的 scale-invariant native advantage，面对 competent containing comparator；不重开 unchanged repeat、local B02 或 telemetry rerun。 |

## 3. INITIAL_INVESTMENT：为何修改 VNFC、但仍 PARK CBSC 与 UCOPE

### 保留的对象顺序

**N 线：仅保留 FRRIE contact-active R128 R02。**
它不需要先以一个新的局部动作 census 来证明值得做：既有证据已经定位到 treatment 从未激活，R02 直接让这个差异在真实 learner 上接受检验。其收益是区分“原结果由不激活造成”与“激活后仍小、混合、负向或比较器不胜任”，不是证明 relation specificity 或变人数迁移。完成其未来有效 intake 后再选下一项，**不预订第二个根、下一种 box 或 held-out roster 实验。**

**duration 线：仅保留 E3 原对象的剩余部分。**
理由不是已经花了十个单元的沉没成本，而是剩余观察仍可回答同一个明确问题：异质 hazard 下，D2 是否通过 native event-to-renewal 路径胜过 competent D0。三个 hazard 行、三个 seed、两臂的原意义不变；不能拿当前不完整面板提前宣布 H1/H0。此后不自动预订 E4、E5、UAV 或任何新 threshold。

上述是**既有对象的保留顺序，不是本次选择新的 result-bearing invocation 或 sweep。**

### VNFC R03：有科学区别，但暂不占当前投资位置

支持保留 R03 的最强理由是：它改变了信息边界，使用因果历史而非 privileged full tape，并可给出受限合法策略类中的实际动作价值。这不是对失败宽度搜索的机械重复，A/RECON 也不应因没有 learner 而一概降级。

但本次保留它，会在 N 父线下同时维持一个**另一个 host 上、尚未实现的控制器普查投资**。它既不回答 FRRIE 的激活问题，也不提供 tuned-generic headroom 或 MAPR 效果；其后续 learner 又没有被当前决定打开。因此我不接受“已冻结、可能便宜”足以保留它的论据，尤其不能用 K1024 的 18 秒给它定价。

**PARK R03 是本轮缩小投资面的选择，不是证明它被 FRRIE 支配。** 如果下一次 N 线取舍的关键变成成员损失恢复，原 R03 可以优先于新的 FRRIE 延伸重新进入考虑；不要求它先通过未知 headroom 数值门槛。second-recast 记录继续附着于 VNFC，而不是被新父线清零。

### CBSC：协议价值与技术接近就绪都成立，但不是本轮自动续投理由

精确 factorial 中，currentness、receiver-correct content、OWNER 信息及保留内容都有正协议价值；与此同时，CBSC 与 unrestricted same-primitive RAW 最优逐行相同。后者只限制**表示必要性或最优值优势**，并不排除有限资源 learnability 的收益。

r06 解释器失败已经复现，窄修复与远端 readiness 的 `17 passed / B1_FORMAL_READY` 也已经记录。不能把它说成科学失败，更不能以旧失败作为删除成果的理由。

本次 PARK 的决定性理由是：**当前 online B1 是单控制器 cache/currentness 问题，尚未说明它改变哪一个保留的 N 或 duration 决策。** 技术资产保留，r07 继续未创建。重入需要具体问题联系，而不是再做一次协议证书，也不是证明 RAW 无法表示 CBSC。

### UCOPE：明确承认最强正证据，仍 PARK 当前审计

PA-B 不是只有“学到了价值符号”：五个通过策略确实在唯一有利 context 购买信息，并取得完整的 `+0.021437` 净增益；失败策略是拒绝付费。这里是 **3 seeds × 2 folds 的六个策略**，不是六个独立 seed，更不是总体成功率估计。

后续 THREE-WITNESS 将 tail agreement 从比较器的 4/6 提高到 6/6，但修复的两项产生了净值为负处的额外 PROBE，完整 competence 仍为 3/6。该结果没有重新评估 paid-acquisition 分支，不能据此撤销 PA-B；它也未区分“learned tail 改变 root targets”与“root 优化残差”两种原因。

所以数值审计有真实问题可问。我的 PARK **不是因为 3/6 competence 不允许 B，也不是因为 33.22% 的工程问题产生科学负极性**；而是当前审计尚未对应本轮 duration host 的获取—续约选择，继续维持它会保留一条独立诊断投资链。保留其正结果、失败定位和审计草案边界，不为赶到“可运行”而增加 scope 例外。

## 4. MERGERS_AND_NONMERGERS

**本 packet 没有证成任何一对现有科学对象在“问题、比较器、estimand、下一对象”四轴上的等价。因此本次批准的科学对象等价合并数为零。** 真正合并的是管理、研究议程及可复用资产，不是结果或 estimand。

| 归并组                   | 四轴检查中的关键差别                                                                                                                     | 本次处理                                                       |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------- |
| FSD、CRTO、VSP-03       | FSD 问异质 hazard 下的 D2−D0 回报与事件路径；CRTO 问 residual 相对 RAW 的有限预算动作 regret；VSP-03 尚无实例化 host。下一对象分别为 E3、RAW trace、未定义。              | 归为一个“中断与续约”管理子族；保留 policy-gap、residual、事件规则的具名区别。当前只投资 E3。 |
| SCDMP 与 FSD           | D6/D8 区别是跨 k 价值学习共享，目标是 competent native composite-action choice 所需样本／更新；D2 改变 mid-segment interruption authority。             | 共享 duration 父线，不合并机制或结果；D6 当前家族 PARK 不因归组解除。               |
| RCLE、FOLR、DISH、VSP-02 | 分别关心 common state、typed memory、状态来源以及 optimizer state；内容、比较器和恢复／学习 estimand 不同。                                                | 合为状态保留与重建的管理子族，保留各 intervention 标签；不合并为一个“记忆算法效果”。         |
| FRRIE 与 MGTAP         | role-weight projection 对 containing EDGE，与物理配置几何对 FREE，不是同一个问题、host 或处理。                                                       | 可复用 roster 表达与适用控制思想；不拼接 return，不转移 metric／relation 特异性。   |
| CBSC、ACVC 与信用类储备      | protocol action value、history veto、receiver addressing、target intervention、receipt content、critic factorization 的 estimand 不同。 | 只共享证据接口与适用控制。RAW 包含、精确正值或某一家族负结果都不跨来源转移。                   |
| UCOPE 与 FSD           | 当前一个测付费获取／root-tail 能力，一个测中断续约；尚无共同 native acquisition-to-renewal 链。                                                           | 只保留候选接口，不科学融合，不把 oracle-signed hinge 变成 FSD 训练目标。          |

D6/D8 与 D2 的区别在原文中是明确区分，不是名称整理产生的新解释。EGRCR 当前 finite-resource 问题与其历史 exact-population relay 问题也必须分开，不能从旧 generic equality 推导所有有限数据 factorization 都无价值。

VSP-03、VSP-02、VSP-C1 可不再维护独立研究议程，而分别成为事件终止、optimizer-state、period-composition 的备选控制；**这不等于这些 PARKED 控制已经进入当前 E3 或 R02 的冻结臂表。**

## 5. INITIAL_INVESTMENT_AND_COST

### Headroom 的使用边界

沿用 section 11 的定义：在可兼容的 host、population、return 和预算解释下，记录 stated upper reference 与 tuned same-information generic baseline 的差。缺失保持未知；upper 可以有声明的额外信息，但不能因此把它当成合法同信息策略。Headroom 是描述与排序输入，不是统一投资门槛或新增 B 启动门槛。

本 packet **没有提供可用于完整跨方向排序的 headroom 配对**。尤其：

* E3 的 exact duration margin 和 D0 fixed-clock sweep，不自动等于 tuned-generic headroom；FRRIE 的 UNIFORM 也不是 tuned generic。
* VNFC 的受限搜索／物理 upper、ACVC 的证书区间、UCOPE 的 target acquisition gain，均不能替代其缺失的完整配对。
* CBSC 的旧精确 RAW equality 不能给 online B1 定价；FOLR 的 upper=1 不能填补 B3 baseline。
* VSP-02 的精确零只属于旧 host 的匹配终端 greedy gap；Scope 的 28 是信息集差，不是算法可争取空间。

### 已测成本与未来锚点分开记录

| 对象／观察窗口              | 可据此记录的成本                                                                                                                                                                    | 不能据此推出的事项                                                                     |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| **FSD E3，保留**        | 原训练律为 `20 × (64.6 + 0.769u)` 秒，另加 `1,648.64` 秒 carded evaluation，并用 15% timing margin。D0 small 约 1.16 h；D0 medium/large 约 1.68 h；D2 mechanical-maximum 约 4.63 h；每臂 cap 8 h。 | E3 已完成单元总实际成本未在此快照聚合；不能把预测当实测，也不能用并行降低每臂 charge。                              |
| **FRRIE R02，保留**     | 128 updates/arm，CPU FP32。旧同形 R128 约 383.3 直接归属秒/arm、总计 2,017.96 秒，来自 local Windows。原 cap 为 4 直接归属小时/arm、总 8 小时。                                                             | 远端 CPU 速度未知；旧时间不是新运行保证，也不是 GPU 性能。                                            |
| **FRRIE 历史同机窗口**     | 三根 panel `19,204.580804 s`；加较早 R128 后，四个有效结果的观察窗为 `21,222.544508/4 = 5,305.636127 s`。                                                                                       | 不是全方向生命周期成本，也不代表以后每个有效结果的期望成本。                                                |
| **VNFC K1024 与 R03** | K1024 runner wall `18.210753208 s`，`wsl_4070` CPU；supervisor 21 s 分列。                                                                                                       | **R03 未实现、成本未知**。K1024 的廉价不为 R03 或 MAPR learner 定价。                           |
| **CBSC**             | 旧 exact factorial 约 96 s，intake 未给 node/device。                                                                                                                             | online B1 无有效结果；r07 成本未知。不能以精确枚举成本代替学习成本。                                     |
| **UCOPE**            | PA-B 为 Windows CPU 单线程，wall `61.827 s`、CPU `61.516 s`。THREE-WITNESS 总 wall `84.843 s`，两臂 charged wall 分别 `62.506/62.641 s`，均各自含共享生成 charge。                                 | 不把两臂 charged wall 相加冒充总 wall；不外推为所有 UCOPE 进展都便宜。候选给审计的 `185.481 s` 规划锚不是审计实测。 |
| **其他有限 A 成本**        | ACVC R02 runner `2.288506334 s` 与 project-cost `7.251637622 s` 分列；SCDMP 当前 DIRECTION 另记 A02 wall `4.797502100002021 s`；Scope census `1.488 s`。                              | 这些不是 learner 效率。SCDMP 该段未给可用于横向比较的完整硬件范围；其有界停止也不等于完成 duration-policy 对照。      |

上述成本分别来自候选、E3/R02 卡、UCOPE 两份结果与 SCDMP 当前结果分节。

其余来源的当前 learner 成本或完整历史分母，仍按候选记录为未测。online B1、DISH B01 等零有效结果对象的“成本／有效结果”比率是**未定义**，不是零。

FRRIE R02 的既有机器 exposure 描述保留为：

```text
updates=128
adam_lr=0.0003
nominal_lr_exposure=0.0384
init_half_range=0.05
nominal_exposure_over_init_half_range=0.768
initial_projection_changed_coordinates=5
```

这是原卡的预算与构造记录，不是本次新增 learner exposure，也不替代未来实际参数位移观测。

**因此，本决定没有宣称 FSD 按秒比 UCOPE 更划算。** 它选择的是当前目标下更直接、已有明确原生行动路径的两项 learner 判别，同时承认被 PARK 项目可能在未来具备更高边际价值。

## 6. PORTFOLIO_EFFECTS、暂停与 source-lineage

相对固定参考下的 19 ACTIVE／3 PARKED 来源，本决定保留两个 ACTIVE_SUBDIRECTION，**将其中 17 个来源的当前投资改为 PARKED，并保持三个既有 PARKED 来源不变**。没有来源被删除或科学性 CLOSED；没有结果被吸收为另一方向的极性。固定参考的旧生命周期表是本次修改前状态，而不是对当前新决定的否决。

VNFC 与 ACVC 的 second-recast 都保留在各自来源谱系中。未来重入时，新父线名称不能重置其 recast 历史、恢复已停止的搜索或洗掉既有反证。原 source IDs、证据路径、provider bindings、无效尝试隔离及已完成对象的含义全部保留。

执行状态继续是：

```text
PAUSED_AT_CLEAN_BOUNDARY / OWNER_DIRECT
当前授权推进的顶层 DM 链：0
本次新选择或启动的实验：0
```

E3 的八个未启动单元、FRRIE 的未创建 result task/admission、CBSC 的未创建 r07、VNFC 的未开始 R03 工程及 UCOPE 未运行审计，都保持其原暂停边界。B on UAV 不需要先获得 toy superiority、定理或数值 headroom，但**本决定既没有冻结也没有启动 UAV 对象**。 

清单中的 exposure receipt 记录：新增环境 episodes、transitions、models、optimizer steps、evaluations、result roots、selected experiments、parameter displacement 全为零，`sweep=false`，`experiment_pause=retained`。这与本节点只形成既有证据上的 Portfolio 决定一致。

## 7. RATIFICATION_CHANGES 与 OWNER_RATIFICATION_TEXT

**已覆盖的 OWNER_DIRECT 实施范围：** 两父线结构、新 N 组织节点、22 来源归档、可逆投资 PARK、共同管理子族、保留对象顺序，以及未来恢复后的每父线一条常驻顶层 DM 模型。这些细节由本 PRO_FINAL 在现有授权内决定，不另列“等待 Owner 批准”阻塞。

**本次选定的额外越界动作：无。**

恢复执行、开放联合 N+k 科学对象、复活有特定 Pro PARK 边界的家族、修改冻结 scientific meaning、放宽工程 scope 或增加新资源政策，均不在本次决定中被批准。它们若以后被提出，须按其各自权限另案处理，不能夹带在归组实施里。

可直接记录的精确文本为：

> **OWNER_DIRECT：本次建立两条父线、归档全部 22 个来源、执行本 PRO_FINAL 指定的可逆 PARK 与保留顺序，属于 Owner 已直接授权的两线精简实施范围，不增加第二次批准等待。RATIFICATION_CHANGES=NONE。研究执行暂停保持不变；本记录不授权恢复实验、不开放联合 variable-N-plus-duration 对象、不解除既有 Pro 家族停止边界、不修改冻结科学含义，也不批准工程 scope 例外。**

## 8. EVIDENCE：实际读取路径

**清单内 17/17 路径均通过连接的 GitHub connector 成功取回。** 下表给出实际使用的正文范围；长 DIRECTION 文件中的历史段落没有被当成最新状态，文件内部链接也不等于已读取那些额外文件。

以下所有路径均位于顶部完整固定参考 **`b35eadf954a0bc56f3291f3b3d2b9ece0748e4a9`**，不是默认分支或各文件内部列出的历史 launch SHA。

| 编号  | 实际读取的精确路径                                                                                                                             | 本决定主要使用的章节／字段                                                                               |
| --- | ------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| E1  | `docs/research/portfolio/decisions/2026-09-04-two-line-consolidation-candidate.md`                                                    | Owner request；22-source organization；Headroom and compute；Retained-object planning anchors。 |
| E2  | `docs/research/portfolio/decisions/2026-09-04-two-line-consolidation-exposure.json`                                                   | mode、22 IDs、全部零新增 exposure 字段、pause。                                                        |
| E3  | `docs/research/portfolio/PORTFOLIO.md`                                                                                                | lifecycle 表；paused working set；2026-09-04 execution snapshot。                               |
| E4  | `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md`                                                                                 | §§4–8、11.1–11.7，尤其 B 准入、N/k 分离及描述性 headroom。                                                |
| E5  | `docs/research/portfolio/decisions/2026-09-04-owner-intervention-surfaces.md`                                                         | 原决定与后续 revision 的历史先后；成本、recast、软介入。                                                        |
| E6  | `docs/research/candidates/flexible_skill_duration/FSD_E3_HETEROGENEOUS_HAZARD_SCIENCE_CARD_20260904.md`                               | 问题、D0/D2、population、estimands、branches、cost、exposure。                                       |
| E7  | `docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_B01_CONTACT_ACTIVE_R128_R02_SCIENCE_CARD_20260904.md` | §§1–8：非激活、处理／包含比较器、真实 work、成本与解释边界。                                                         |
| E8  | `docs/research/candidates/variable_n_fleet_churn/DIRECTION.md`                                                                        | Current controller-headroom reconnaissance；R03 causal boundary；section-11 recast。           |
| E9  | `docs/research/candidates/ucope/UCOPE_PAID_ACQUISITION_B01_RESULT_EVIDENCE_20260903.md`                                               | Work accounting；A_paid；competence；cost；interpretation/locks。                                |
| E10 | `docs/research/candidates/ucope/UCOPE_THREE_WITNESS_HINGE_R01_RESULT_EVIDENCE_20260904.md`                                            | Bounded result；root consequence；exposure；charged/total cost；limits。                         |
| E11 | `docs/research/candidates/capability_bound_semantic_currentness/CBSC_EXACT_FACTORIAL_RESULT_INTAKE_20260830.md`                       | Exact contrasts；RAW containment；protocol versus learnability。                               |
| E12 | `docs/research/candidates/vap_folr_core/FOLR_B1_OWNER_EPOCH_SURVIVOR_BIT_LEARNABILITY_CODE_SCIENCE_INDEX.md`                          | 八 seed 表；latch 控制；technical/scientific authority boundary。                                  |
| E13 | `docs/research/candidates/acvc/DIRECTION.md`                                                                                          | Current position；exact lower/upper certificate；bounded re-entry。                            |
| E14 | `docs/research/candidates/eociv_lite/DIRECTION.md`                                                                                    | B9R1/B10；absolute/relative 区别；family-only PARK。                                             |
| E15 | `docs/research/candidates/expressibility_gated_renewal_credit_relay/DIRECTION.md`                                                     | 2026-09-04 current disposition；finite-resource cycle；旧 exact-family 区别。                     |
| E16 | `docs/research/candidates/semigroup_consistent_duration_model_policy/DIRECTION.md`                                                    | D6/D8 与 D2 区别；section-11 correction；A01、A02、最终 D6 family PARK。                              |
| E17 | `docs/research/candidates/commitment_residual_triggered_options/DIRECTION.md`                                                         | empirical reopening；Balanced-residual B01-R1；RAW-only trace 与解释限制。                          |

## 9. UNCERTAINTY

**尚未观察的结果仍未观察。** E3 不能提前汇总；FRRIE R02、VNFC R03、CBSC r07 与 UCOPE 当前审计均没有本 packet 可据以判定的新结果。本决定也未独立复算原始日志、检查未列出的代码、审计 checkpoint 或验证实时进程状态。

**不存在完整成本优势证明。** PARK 的理由是当前组织目标下的边际投资取舍，而不是已证成的跨方向 ROI 排序。特别是 VNFC R03 可能成为有价值且便宜的后续判别，但其成本未知；CBSC 的技术资产可能缩短未来实现路径；UCOPE 已显示真实局部获取价值。这些都是反对长期遗忘它们的理由。

**证据版本没有被混同。** 候选与 exposure receipt 内部记录的 `source_commit=1283588908943dd63e303e11e46acad0f2eba477` 是其生成时的证据快照标签；本次实际读取参考仍是顶部的 `b35eadf954a0bc56f3291f3b3d2b9ece0748e4a9`。这不构成切换参考，也不把旧状态当成实时状态。

**历史措辞不新增规则。** PA-B 旧文出现“consumed”的表述，而控制性 evidence spec 明确 A/B 无一次性 consumption 状态。本决定不改写历史文本，也不以该措辞制造新的 B 禁止重复规则；同样不借 section 11 解除已有具名家族的 Pro PARK 边界。

**最终边界：两条资助父线、两项保留投资、二十项可逆 PARK；没有第三条资助线，没有科学对象等价合并，没有实验恢复。DECISION_FORMED=true；BLOCKER=NONE。**
