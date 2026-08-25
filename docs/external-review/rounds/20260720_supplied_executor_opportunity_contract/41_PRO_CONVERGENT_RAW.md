1. Evidence-validity disposition

处置：保留注册分类 INVALID_CLEAN_SUPPLIED_EXECUTOR_OPPORTUNITY_CONTRACT，不得升级为 PASS、VALID_FAIL 或 MIXED。

这不是实现失败。结果 JSON 明确同时记录了 implementation_valid=true 与科学状态 INVALID_CLEAN_SUPPLIED_EXECUTOR_OPPORTUNITY_CONTRACT；全部 M0 均为真，包括精确 high likelihood/value replay、零 low likelihood/row/update/gradient、learned/frozen update-zero 一致、learned-only high drift、active-only masks、owner-local physical-time credit、JOIN/LEAVE/REJOIN/terminal state、survivor continuity，以及 mid-segment checkpoint 和 fail-closed restore。

正式暴露也完全符合合同：16 个环境、horizon 80、250 updates、320,000 primitive transitions、1,000 high optimizer steps、零 low optimizer steps和每 arm 256 个评价 episode。Supplied executor 是 IDLE/PERSIST/SHORT 的零参数恒等映射，high optimizer只拥有 commitment policy 与 event critic。

无效的是注册比较器的科学前提。结果为：

routing oracle：P/S/U=0.978699/0.660807/0.819753；

frozen high：1.0/0/0.5；

learned high：0.942383/0.938639/0.940511；

learned-minus-frozen utility CI95：[0.435689,0.440511,0.445251]。

分类器按预注册优先级先检查 oracle 的三项均值是否全部达到 0.95；oracle失败后立即返回 INVALID_CLEAN_SUPPLIED_EXECUTOR_OPPORTUNITY_CONTRACT，随后才是 frozen sufficiency 与 learned access 分支。因此 learned 数值即使满足其自身绝对门和增益门，也不能越过 oracle-first prerequisite。

仍然科学可用的次级证据

以下证据可以继续用于组合加权和下一诊断设计：

Event runtime、概率、credit 和 checkpoint 路径是可工作的。 失败不能归因于断梯度、低层泄漏、错误 replay、成员状态丢失或损坏的 resume。

完整的“F1 high/event training package”在这个固定任务、固定原语和固定机会过程上具有强训练效应。 Learned 与 frozen 从 byte-equal high tensors 开始；只有 learned arm 更新，随后在同一评价 ledgers 上产生约 +0.4405 的 paired utility gain。这证明 high graph 并非完全失活，也证明其输入与机会历史含有可利用的任务信息。

Learned policy 的高短任务得分是真实行为结果，而不是 supplied low learner 的伪信号。 Supplied mode中的low actor/critic是parameterless sentinel；测试还明确拒绝调用low inference、low replay或joint high+low PPO。

这些次级证据不能建立：

当前 opportunity contract 在注册 floor 上具有可达性；

F1 applied-prefix 相对 F0 的独立贡献；

一般意义上的 high-credit 成功；

learned low-level skills；

hierarchy efficacy、合作贡献、异质 lifetime、迁移或相对 direct MARL 的优势。

Supplied labels直接等于任务 primitive，不能被称为 learned skills；项目原则也要求 skill claim必须同时建立 intervention-sensitive execution、持续后果、shortcut排除、自然使用和联合价值。

2. Divergent factual adjudication
Oracle claim：接受 Open-Pro，拒绝 Gemini 的“oracle 必为上界”

完整的 constructive_actions 是每个 primitive step 都可重选动作的规则：保持一个 PERSIST owner；wave活跃时，其余尚未贡献的成员执行 SHORT；其余时间执行 IDLE。

当前 routing oracle 并没有获得这种逐步控制权。实现先对完整当前状态计算 constructive actions，然后只向当前 private opportunity frontier 中的成员 teacher-force相应建议；不在frontier的成员继续执行旧skill。

与此同时：

short wave只有4个primitive steps；

一个成员必须连续2步SHORT才贡献；

每次policy opportunity之后，不论动作是KEEP还是SET，都会重新从整数1..19采样下一个gap。

所以当前oracle是“逐步constructive rule的无前瞻frontier投影”，不是同一机会权限下的最优策略，也不是有效upper bound。Oracle失败证明当前比较器前提无效；它不证明event runtime或supplied primitives本身失败。

Gemini提出通过平滑、放宽或调优oracle并删除0.95门，属于明确禁止的结果后救援，不能采纳。

Pre-positioning claim：保留为高可信假设，不能升级为已证明事实

Learned high可以看到physical time、active count、wave active、remaining steps/work、当前任务进度、自身owner/streak/contribution、active age和previous primitive action；实际未来wave选择仍未直接暴露。

因此，一个causal recurrent policy确实可能：

在固定候选wave windows之前预先将非owner成员设为SHORT；

在wave之间KEEP SHORT，而不是按当前oracle改回IDLE；

长期保留一个PERSIST成员；

membership churn后重建上述组成。

Learned相对oracle少量牺牲P并显著提升S，与这种解释一致。但当前结果文件只归档了episode outcomes和均值；评价函数没有把decision、primitive和contribution trace写入结果，因此预配置解释尚未被直接分解。

Discount / switching claim：作为当前因果解释予以拒绝

Gemini认为learned policy可能通过频繁切换来重置event clock或“利用”γ
Δ
。现有实现与该说法不符：

每次opportunity之后都会采样新gap，无论选择KEEP还是SET；policy不能通过切换决定下一次机会时刻。

Primitive transition只会让active age加一、gap减一并按physical time累积team reward；event timing保持外生。

环境只有terminal external reward，没有premature-termination reward或switch penalty。

Owner return按照真实elapsed physical time计算，临时离开是critic-only truncation；M0已验证owner-local credit。

High drift 2.067886只能证明参数明显变化，不能证明discount exploit。未来若trace显示异常高switch rate，可把它作为诊断；当前不能把它当作观察到的机制，更不能通过改reward或增加termination penalty“修复”。

Spatial / proximity claim：拒绝

注册任务是categorical Generic-SHORT，primitive support仅为IDLE/PERSIST/SHORT，没有连续空间、proximity threshold、拦截或振荡。Clean actuator position/velocity只是与任务旁路的audit state，不进入observation、critic、reward或task dynamics。

Supplied executor也是对skill整数的精确恒等映射，而不是会在“特定空间边界”失败的controller。

3. Weighted causal portfolio

科学问题仍然开放，但本轮只保留四个active causal candidates。Factorized learned executor B和simplex command C仍有价值，放入第9节parked portfolio，不作为当前四个live slots。

O — Opportunity-comparator / authority mismatch

相对权重：高；置信度：高。

机制。 当前oracle将一个需要每步更新的rule投影到稀疏frontier，却没有预配置、保持规划或机会可达性计算。其失败可能完全来自比较器定义，而非event runtime。

解释的证据。 它直接解释oracle S=0.6608、learned S=0.9386，也与4-step wave、2-step streak和1–19 gap的时间尺度冲突一致。

最强反证。 即使拥有完整未来ledger、但严格受相同frontier约束的hindsight solver，也无法让同一组256个episodes的平均P/S/U同时达到0.95。这会把问题从“myopic oracle”改写成“精确 opportunity qualification合同结构性不可达”。

合并/退休。

Hindsight ceiling不可达：O并入“exact contract infeasible”，退休当前qualification合同。

Hindsight可达且current-oracle regret主要来自pre-positioning：退休当前oracle作为upper bound，保留event runtime。

一个未来严格actor-information-matched causal planner清除floor后，O才算完全解析；本轮不通过调heuristic完成该工作。

D — Information-matched direct active-set recurrence

相对权重：高；对当前carrier置信度高，对最终目标充分性置信度中等。

机制。 Primitive-time recurrent policy直接编码持久、响应和leave/rejoin行为，不需要显式skill object或event abstraction。

证据。 Clean carrier上的direct recurrent policy已经取得近乎完美的deterministic/stochastic任务访问，因此它仍是强制ordinary-MARL null。

限制。 当前direct actor每个primitive step均可行动，并读取active-member embedding sum、log(1+N)以及同一步earlier-action counts；它拥有比event controller更密集的控制权与更强team-context bandwidth，不能直接充当F1-prefix的机制匹配比较器。

最强反证。 Learned、自然使用且shortcut-resistant的hierarchy，在相同actor-visible information、communication、参数/optimizer exposure和held-out roster/lifetime条件下，提供material external-utility或sample-efficiency优势。

合并/退休。 Supplied primitives或高训练内utility不能削弱D。只有learned executor和matched held-out advantage可使其下降。

R — Simpler scheduled recurrent mark policy / F0 suffices

相对权重：中高；置信度：中高。

机制。 Learned gain可能只需要current active-set state、time/task fields、per-member recurrence、exogenous opportunities和persistent marks；不需要同一frontier内later owner读取earlier applied edits。最小替换是F0 initial-summary policy，而不是删除全部event runtime。

替换账本。

保留membership、opportunity、supplied executor、KEEP/SET、event critic和owner credit；

删除F1 working-prefix dependence；

仅把architecture_mode=f1替换为f0；

不增加latent、critic、posterior或scheduler。

架构合同明确规定F0和F1必须共享网络图、容量、collector、credit和数据合同，唯一区别是initial summary与working summary。

最强反证。 在有效比较器下，F1相对byte-equal F0表现出multi-owner-specific common-support directional shift，并获得正的paired external utility advantage。

合并/退休。

F0匹配F1：将P并入R，停止把applied-prefix当作贡献。

Learned gain主要来自pre-wave配置、singleton frontiers或固定calendar：R显著上升。

F1在matched multi-owner rows稳定胜出：R下降但不消失，D仍保留。

P — F1 applied-prefix cooperative assignment value

相对权重：低至中；置信度：低。

机制。 同一multi-owner frontier内，later owner根据earlier已经应用的commitments避免重复PERSIST并补充SHORT composition。

已有证据。 代码具有真实working-summary路径，earlier token被立即写入working skill set，later token据此计算distribution。

尚缺证据。 当前实验只有F1 learned arm和F1 frozen arm，没有F0；learned-minus-frozen无法识别applied-prefix。Result JSON也只说明architecture_mode=f1。

最强反证。

Learned excess short work主要由wave到达前已处于SHORT的成员产生；

singleton frontiers与multi-owner frontiers具有相同收益；

stored-token working-versus-initial read仅产生common-logit变化，或不预测完成工作；

后续matched F0与F1 utility相同。

合并/退休。 F0 noninferior或prefix dependence无外部transport时，将P并入R或作为decorative dependence关闭。

4. Selected next evidence source or stop

选择一个新的、单一、evaluation-only evidence contract：

READ_ONLY_OPPORTUNITY_AUTHORITY_AND_USE_AUDIT

它是“read-only opportunity-feasibility audit”和“existing-checkpoint opportunity-use decomposition”的一个更严格合并版本，但只有一个runner、一次固定ledger replay和一个terminal result；不是隐藏的两轮实施顺序。

核心问题

在不改变task、gap、frontier、threshold或learner的条件下，注册的机会权限是否至少在hindsight意义上能达到原0.95联合floor；若能，learned相对current oracle的收益主要来自pre-positioning/long KEEP，还是来自multi-owner F1 working-prefix composition？

这是当前最高的信息增益来源，因为它可能：

直接证明exact opportunity contract结构性不可达并停止该toy线；

证明current oracle只是myopic comparator；

在不训练F0的情况下决定P是否值得进入下一次matched F0/F1 review；

将learned signal归约为task-calendar/scheduled recurrence，从而停止不必要的hierarchy扩展。

它不改变原INVALID状态，也不“修复”oracle。

延后的替代来源

纯same-information causal oracle test暂缓。 当前actor-visible history形成一个部分可观测、history-dependent planning问题；在没有精确information-state定义前，另写一个“更聪明oracle”很容易退化为调heuristic。Gemini提出的relaxed oracle正是这种禁止的救援。

Matched F0/F1 training暂缓。 在尚不清楚当前机会权限是否结构可达、learned gain是否只是pre-positioning之前直接训练F0，会同时保留无效比较器并增加新训练证据。

Direct recurrent rerun不选。 Clean direct access已经成立；重复运行不会解释oracle miss或F1 contribution。

这一选择符合“先用最小source改变组合权重或产生真实stop，而不是选择最容易注册的实验”的收敛原则。

5. Exact estimand and comparator
Frozen data boundary

审计只使用：

精确提交 ab68b88ea0861e133c51dc80ec9fbcca6a600db7；

正式run的update_000_high.pt和latest_high_only.pt；

evaluation IDs 0..255；

task/evaluation/opportunity/action/bootstrap seeds 97057/77057/87057/107057及原stream IDs；

horizon 80、membership schedule、wave candidates、4-step deadline、2-step streak；

gap distribution Uniform{1,…,19}；

supplied mapping 0/1/2 → IDLE/PERSIST/SHORT；

原oracle联合floor P/S/U≥0.95；

deterministic high evaluation和10,000次paired episode bootstrap。

不得追加episode或新seed。

Comparator status and information access

定义四个对象：

Learned F1 π
L
	​

：causal；只使用实际policy-visible observations、current skills/ages、join/rejoin flags、high hidden、working active-set summary和当前frontier。

Frozen F1 π
0
	​

：causal；与learned update-zero byte-equal，不接受optimizer step。

Current routing oracle π
M
	​

：causal但并非information-matched；它直接读取当前environment对象，计算完整constructive rule，再只作用于当前frontier。

Frontier-constrained hindsight ceiling H：非因果；可读取该episode完整未来membership、wave、opportunity和frontier ledger，但只能在实际已发生的frontier上选择skill，并必须使用相同supplied executor。它不能改变gap、frontier order、membership、wave或reward。

Hindsight对象只回答机会权限的结构可达性，绝不是算法baseline、causal oracle或learned-policy comparator。

Primary structural estimand

对每个episode e，精确枚举或动态规划所有受实际frontier约束的skill-action序列，得到可达结果集：

Y
e
	​

={(P
e
	​

,S
e
	​

,U
e
	​

)}.

然后定义：

G
H
	​

=
y
e
	​

∈Y
e
	​

, e=0,…,255
max
	​

min(
P
,
S
,
U
).

原机会floor在hindsight权限下可达，当且仅当：

G
H
	​

≥0.95.

这一写法要求存在一组真实action sequences，使三个平均指标同时过门；不能分别报告来自不同轨迹的max P和max S来伪造joint feasibility。

Policy-use decomposition

对每一个实际完成的short work unit，按产生该unit的成员在wave arrival时的skill和随后setting event唯一分类：

PREWAVE_SHORT：wave到达时已经SHORT，贡献前没有wave内SET-to-SHORT；

POSTWAVE_SINGLETON：到达后在frontier size 1的event转为SHORT；

POSTWAVE_MULTIOWNER_FIRST：在multi-owner frontier的第一个token转为SHORT；

POSTWAVE_MULTIOWNER_LATER：在multi-owner frontier中，已有earlier applied edits之后转为SHORT；

OTHER_OR_NO_TIMELY_OPPORTUNITY。

对类别 c 计算：

Δ
c
	​

=mean
e
	​

[W
e,c
learned
	​

−W
e,c
current oracle
	​

].

某类只有在其相对所有其他类别的paired episode-bootstrap差值LCB均大于零时才称为decisively dominant；否则进入mixed branch。这样无需事后发明比例阈值。

同时读取：

wave arrival前SHORT active share；

到t
w
	​

+2前具有可用opportunity的owner数；

within-wave SET-to-SHORT次数；

persistent owner loss后的恢复延迟；

frontier size、token position和membership-boundary strata；

fixed candidate-window前的SHORT配置是否集中，用于判断task-calendar reduction。

F1-specific audit-only read

对learned F1中frontier_size>1且token_position>0的同一个stored token，固定observation、skills、ages、mask、hidden和parameters，只将summary source从working替换为initial，读取：

TV(p
work
	​

,p
init
	​

)

以及是否减少duplicate PERSIST、增加缺失SHORT的directional shift。现有runtime已经提供不采样、不改变state的replay_token_distribution路径。

这是checkpoint-local diagnostic，不是F0 treatment。它最多说明当前F1使用了working summary；不能证明F1训练价值或utility causality。

本source不能建立

actor-visible、same-information causal oracle能否达到0.95；

F1相对F0的因果utility advantage；

general high-credit optimality；

learned skill semantics；

heterogeneous lifetime efficacy；

hierarchy优于matched direct；

transfer或integration资格。

6. Mutually exclusive branches and portfolio updates
A. INVALID_OPPORTUNITY_AUTHORITY_AUDIT

触发： 无法逐episode复现原learned/frozen/current-oracle outcomes；frontier/gap ledger不一致；hindsight solver在小规模brute-force对照上不等价；未来信息泄漏到learned/current arms；或trace分类不唯一。

处置：

只修分析实现；

原INVALID结果、O/D/R/P权重全部不变；

不修改任何科学输入或重新训练。

B. HINDSIGHT_OPPORTUNITY_FLOOR_UNREACHABLE

触发： G
H
	​

<0.95。

解释： 即便读取完整未来ledger，同样的frontiers和supplied primitives也无法让平均P/S/U同时达到注册floor。失败不只是myopic oracle，而是exact task-gap-floor组合结构性不可达。

组合更新：

O： 从“oracle misspecification”合并为“exact opportunity qualification infeasible”；当前oracle和整个G0 qualification合同退休。

D： 上升；仍是唯一有效task-access evidence。

R、P： 在本toy上不可识别，不得训练F0/F1救援。

Toy stop： 停止当前supplied-executor opportunity toy线。不得改gap、deadline或threshold制造可达性。

C. HINDSIGHT_REACHABLE_PREPOSITIONING_REDUCTION

触发：

G
H
	​

≥0.95；

PREWAVE_SHORT在learned-minus-current-oracle excess work中decisively dominant；

POSTWAVE_MULTIOWNER_LATER不dominant；

working-versus-initial directional read未形成明确的multi-owner贡献关联。

解释： Current oracle失败主要因为不做持久预配置；learned gain可归约为time-aware commitment retention，若行为又集中在固定wave candidate windows，则进一步归约为task-calendar finite-state scheduling。

组合更新：

O： 当前oracle作为upper bound退休；event runtime保留。

R： 显著上升，成为最简解释。

P： 强烈下调并park；没有理由立即训练F0/F1。

D： 保持高权重；supplied hierarchy没有显示相对ordinary recurrence的独特价值。

Toy stop： 停止在该toy上扩展F1。将结果视为scheduled-controller reduction，而非hierarchy进展。

D. HINDSIGHT_REACHABLE_MULTIOWNER_PREFIX_CANDIDATE

触发：

G
H
	​

≥0.95；

POSTWAVE_MULTIOWNER_LATER在learned excess work中decisively dominant；

working-versus-initial distribution产生正的directional shift；

该shift集中在later tokens并与实际short completion或persistent recovery关联。

解释： 当前数据首次提供了F1 applied-prefix可能load-bearing的有方向诊断，但仍不是F1-vs-F0因果结论。

组合更新：

O： 当前myopic oracle退休为upper bound；hindsight只证明authority，不证明causal information sufficiency。

P： 上升至中等，成为下一次review中matched F0/F1 source的首要候选。

R： 仍live，因为同一现象仍可能由F0训练获得；只有matched comparison能区分。

D： 始终保留。

Toy line： 不停止，但本branch只使matched F0/F1成为未来可审阅方案；不自动授权训练。

B： 继续park，不能在high assignment尚未被因果确认前替换learned executor。

E. HINDSIGHT_REACHABLE_MIXED_OR_UNIDENTIFIED

触发： G
H
	​

≥0.95，但没有任何贡献类别decisively dominant，working-summary read与utility不一致，或现有checkpoint replay不能唯一归因。

组合更新：

O： 仍支持“current oracle不是上界”，但无法进一步分解。

R、P： 均保持不确定，不合并、不晋级。

D： 保持高权重。

Toy stop： 停止当前toy线，不增加episode、不合并strata、不以F0训练弥补不识别。后续只能由独立最终目标证据重新提出问题。

7. Minimal implementation and prohibited changes
未来若获得独立授权，允许的最小写入面

仅新增：

ha_ctse_process/dynamic_roster_opportunity_audit.py

materialize_exogenous_frontiers

solve_frontier_hindsight_pareto

classify_short_contributions

read_working_vs_initial_distributions

scripts/run_clean_process_opportunity_authority_audit.py

一个evaluation-only runner；

一个terminal JSON：
result/clean_supplied_executor_opportunity_authority_audit.json

tests/ha_ctse_process_clean_opportunity_authority_audit_test.py

current-result逐episode复现；

tiny-horizon DP与brute force等价；

full-step authority可复现constructive结果；

action/frontier约束；

future-ledger只进入hindsight solver；

零optimizer、零parameter drift。

以下文件必须保持read-only：

ha_ctse_process/dynamic_roster_testbed.py

ha_ctse_process/dynamic_roster_clean_process_testbed.py

ha_ctse_process/variable_roster_event.py

ha_ctse_process/dynamic_roster_supplied_executor.py

原runner、原tests、原result和原checkpoints。

现有runtime已经保留decision、primitive和reward traces，新的runner可通过独立replay读取，不需要改变behavior path。

若analysis无法在不修改core probability、opportunity、credit、mask或checkpoint语义的情况下完成，应返回IMPLEMENTATION_BOUNDARY_MISMATCH，而不是扩大scope。

明确禁止

不得：

降低或替换oracle 0.95 floor；

平滑、放宽、调参或训练current oracle；

修改gap 1..19、wave windows、deadline、streak、membership或horizon；

修改reward、utility定义或加入switch/termination penalty；

改seed、episode数、bootstrap数、budget、model或checkpoint选择；

增加best-checkpoint或stochastic-only解释；

训练F0、F1、direct、oracle、low actor或新critic；

加入intrinsic、posterior、effect reward、graph、communication、slot、team latent、simplex、hazard或scheduler；

使用identity、role、routing key或未来ledger训练任何policy；

复活R29、R31-CFEI、R32-IFEPG、R33-IRSC或Iteration-5 C1；

用新的carrier或action-derived process channel救援本结果。

所有有效negative均为终局约束；不得通过改名字或超参数重开。

本节只是未来operational boundary，不授权代码、checkpoint读取、运行或算力。

8. Ordinary-MARL, lifetime and integration boundary
Ordinary-MARL null

Clean direct recurrent result继续作为mandatory end-to-end null，但要区分比较层级：

对F1 applied-prefix的机制比较器： F0 scheduled recurrent policy，因为它共享opportunities、fixed executor、event credit、控制频率和信息合同。

对完整hierarchy价值的最终比较器： information- and communication-matched primitive recurrent policy。

当前direct policy逐primitive step行动，并读取active-set summary和earlier-action prefix；若未来hierarchical low只读local observation与skill，两者必须统一信息或明确计费communication，否则direct胜出可能来自更强执行带宽。

Membership and survivor state

本轮M0有效证明了：

genuine JOIN从零high state开始；

temporary LEAVE冻结high state、skill、age和gap；

REJOIN恢复同一lifecycle并增加epoch；

terminal LEAVE删除high state和skill；

unaffected survivor continuity；

active-only masks和严格mid-segment resume。

这些事实可复用；oracle invalid不撤销它们。

Lifetime claim ceiling

现有runtime区分physical time、opportunity time、owner-event depth和skill active age，KEEP可形成不同长度的active execution run。架构合同也规定外部membership event无actor likelihood，真实lifetime是连续KEEP累计的active time。

但本轮没有建立heterogeneous learned lifetime：

executor是固定primitive，不是learned skill；

没有lifetime breadth、heterogeneity或held-out duration estimand；

task可能由近静态“一名PERSIST、其余SHORT”解决；

没有与shared renewal、fixed lifetime或information-matched direct进行temporal comparison。

因此只能声称clock、credit和state ownership实现有效，不能声称variable-lifetime efficacy。

Intrinsic boundary

Intrinsic reward在本轮恒为零。未来任何signal必须具有跨环境相同的数学与输入合同，不能读取task goal、role、identity、progress、contact、phase、success或external reward。

Clean actuator由action tape确定，继续保持audit-only；不能重启C1或q_d reward。

Literature use

从ACAC吸收的是γ按真实physical elapsed time、λ按owner-event depth推进；不吸收固定n_agent外壳。

从ACE吸收per-member readiness和dropout压力，但不吸收固定buffer和缺少γ
T
i
	​

的return。

从InforMARL吸收shared/permutation-safe active-set表示原则，但不能把跨固定N泛化当作episode内JOIN/REJOIN。

这些原则不能成为graph、attention或communication模块堆栈的默认授权。

Later integration prerequisites

任何hierarchical candidate进入独立integration review前，必须同时满足：

有效scientific comparator与同carrier ordinary access；

learned而非supplied的executor；

intervention-sensitive、persistent、nuisance-resistant且自然使用的skills；

anonymous JOIN、temporary LEAVE、REJOIN、terminal LEAVE与survivor continuity；

physical/opportunity/event/segment clocks和γ
Δ
 credit正确；

exact probability、mask、RNG、replay与mid-segment checkpoint；

actor-visible information与direct baseline匹配；

在未见membership schedules和active-lifetime distributions上，对direct产生material external-utility或sample-efficiency优势；

不依赖task-shaped intrinsic、identity、role、duration catalogue或module stack。

当前结果不满足第2、3、7、8项，不能进入integration。

9. Valuable unselected ideas
Exact actor-information-matched causal planner

这是最有价值的未选想法。它可在hindsight authority可达、但trace audit仍mixed时回答“真正causal、无未来信息的event policy能否过0.95”。当前不选，因为需要严格定义history-equivalence或belief state；直接编写一个更聪明heuristic会成为oracle tuning。未来只有在第6节D/E分支后、且能给出非启发式information-state合同时才恢复。

Architecture-matched F0 versus F1 training

继续保留。只有HINDSIGHT_REACHABLE_MULTIOWNER_PREFIX_CANDIDATE出现后，它才有足够信息增益。该比较必须byte-equal初始化，保持相同membership、opportunities、executor、critic、credit、seeds、transitions和optimizer exposure，只改变initial-summary与working-summary。现阶段直接训练会跳过当前invalid comparator与行为归因问题。

Factorized learned executor B

保留为downstream candidate，但不进入active four。固定primitive结果说明high graph可训练，却不证明shared low executor interference是历史失败的原因。B只有在有效high/F0-F1路径已经建立后，才能以capacity-matched shared-vs-factorized replacement测试；不得同时加入posterior或intrinsic。

Simplex command C

继续park。它只有在one-hot learned executor已形成可执行skills、high path有效，而non-vertex composition仍提供B无法复现的held-out价值时才有独立意义。当前加入continuous latent只会增加ordinary-recurrence reduction风险。

Schedule-shift frozen evaluation

可检查learned high是否记忆固定wave candidate calendar。它不作为当前selected source的独立arm；本次trace audit已经先读取skill changes是否集中于candidate windows。只有calendar signal明确且需要验证分布外脆弱性时，才值得单独注册未见schedule评价。

Local-information direct comparator

对最终integration至关重要，但不是修复oracle invalid所需的最小证据。它应在某个learned hierarchy已经满足skill semantics后，用来消除当前direct actor的active-set和primitive-prefix信息优势。

Learned opportunity hazard / point process

保持关闭。它需要完整的survival、intensity、termination和censoring likelihood，并会改变opportunity authority；不能作为current oracle失败的scheduler-only救援。

Action-null-resistant physical process

未来真实环境若包含不能由start state与action tape决定的local consequences，可重新讨论process semantics。当前clean actuator没有这种residual，因此不应重新接入posterior或intrinsic reward。

最终收敛建议：保留原INVALID终局；以一次READ_ONLY_OPPORTUNITY_AUTHORITY_AND_USE_AUDIT作为唯一下一证据建议。它不修改oracle、不训练policy，并可在同一source中产生结构性stop、scheduled-reduction结论或为未来matched F0/F1提供明确的条件。