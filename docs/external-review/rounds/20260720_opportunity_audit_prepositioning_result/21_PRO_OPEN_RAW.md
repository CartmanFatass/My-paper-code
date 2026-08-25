1. Result validity and exact evidence delta

审阅结论：接受本轮注册结果为有效的

HINDSIGHT_REACHABLE_PREPOSITIONING_REDUCTION

但必须同时保留上一轮 G0 的终局状态：

INVALID_CLEAN_SUPPLIED_EXECUTOR_OPPORTUNITY_CONTRACT

本轮是一个新的、只读的有效诊断，不能追溯性地把原 G0 升级为 PASS、VALID_FAIL 或 MIXED。

仓库事实：实现与分析有效。 三个行为臂在原 256 个 evaluation ledgers 上的 P/S/U 均被逐 episode 精确复现；frontier、order、primitive-action identity、future-ledger isolation、唯一贡献分类、tiny-DP/brute-force 等价、零 optimizer step 和零 parameter drift 全部通过。

G_H=1 的精确含义：

hindsight solver 不能改变 membership、wave、gap、frontier、order、reward 或 supplied executor；

它只能在实际出现的 frontier 上选择 IDLE/PERSIST/SHORT；

它可以读取完整未来 ledger，因此是非因果的 structural ceiling；

joint aggregate 的 P/S/U 均为 1，不是分别从不同轨迹取得的三个 marginal maxima。

由于每项 episode score 都不超过 1，而所选轨迹的平均 P 与平均 S 都等于 1，可推出每个被评估 episode 都存在一条受实际 frontier 约束、同时达到 P=S=1 的 hindsight 轨迹。DP 只对实际 frontier 枚举动作，非 frontier commitment保持不变，并只在相同未来相关状态内进行 Pareto pruning；tiny instance又与 brute force完全一致。

因此，G_H=1 排除了：

原 1..19 opportunity gaps 与 Generic-SHORT 任务在结构上根本无法达到联合 0.95 floor。

它没有建立：

causal、actor-information-matched policy 能达到该 floor；

learned policy接近 hindsight optimum；

F1 working prefix有价值；

hierarchy优于普通 recurrent control。

PREWAVE 归因是本轮最强行为增量。 Learned-minus-current-oracle 的完成 SHORT work 差异为：

贡献类别	平均 excess work
PREWAVE_SHORT	+10.613281
POSTWAVE_SINGLETON	-1.621094
POSTWAVE_MULTIOWNER_FIRST	-0.425781
POSTWAVE_MULTIOWNER_LATER	-1.898438
OTHER_OR_NO_TIMELY_OPPORTUNITY	0

PREWAVE_SHORT 相对每一个其他类别的 paired-bootstrap lower bound 都严格大于零，因此它是注册意义下唯一 decisive category。

其正确解释是：

Learned policy 相对 myopic oracle 的额外已完成 SHORT work，主要来自 wave 到达前已经维持为 SHORT 的成员，而不是 wave 到达后、多 owner frontier 中 later token 利用 earlier applied edit 所产生的补充工作。

它不证明所有 learned SHORT work 都来自 pre-positioning，也不证明 pre-positioning 对所有任务必要；它只定位了本任务、该 checkpoint、相对当前 oracle的主要 excess-work 来源。

Working-prefix 读数进一步削弱 F1-specific 解释，但不能说 prefix 完全无作用。

later-token rows：2700

mean TV：0.081369

completion/recovery-associated rows：1263

其中正向 rows：166

associated directional mean：-0.039538

missing-SHORT increase：-0.013745

registered positive-direction flag：false。

所以 working summary 确实改变了 checkpoint-local action distribution；但平均变化不朝注册的“减少重复 PERSIST／补足 SHORT”方向运输。166 个局部正向 row说明不能声称“从无正向 prefix effect”，而负的 aggregate direction说明也不能把这些局部 row升级为合作或utility证据。该读数始终只是同一 F1 checkpoint内替换summary source的diagnostic，不是F0 treatment，也不是F1 utility counterfactual。

相对上一轮的精确 portfolio delta：

O／结构不可达解释被否定。 当前oracle仍不是有效upper bound，但exact opportunity authority本身可达。

R／scheduled pre-positioning + long KEEP显著增强。

P／F1 applied-prefix cooperative assignment显著削弱并应park。

D／ordinary recurrent null保持强势。

Learned-executor问题仍未识别。 Fixed supplied primitives不能判断历史shared low executor为何失败。

原G0、Iteration-5 spatial carrier、Iteration-5 C1以及R29、R31–R33均保持关闭。

2. Two-to-four-candidate causal portfolio

以下四个候选不构成 successor 排名。

Candidate R — Scheduled recurrent persistent-mark control

机制： 一个member-local recurrent mark policy在外生opportunity上选择持久primitive mark；在机会之间保持当前mark。它利用physical time、当前任务状态、membership事件和hidden进行预配置，不需要later-on-earlier working-prefix coupling。

解释的证据： decisive PREWAVE excess、multi-owner-later负差、working-prefix平均方向为负。

最终能力潜力： anonymous JOIN/LEAVE/REJOIN、survivor continuity与异步persistent commitments；但不自动提供learned skill semantics。

置信度： 对当前toy为高；对最终通用目标为中等。

替换账本：

retain：lifecycle store、active masks、external opportunities、KEEP/SET语义、gamma^Δ owner credit；

delete：F1 working-prefix依赖及其合作贡献claim；

replace：F1 editor替换为initial-context／independent scheduled mark policy；

add：无新latent、critic、posterior或reward。

最强反证： 在一个去除calendar shortcut、信息匹配的任务上，scheduled mark policy失败，而具有natural learned skills的hierarchy产生held-out external advantage。

分离观察： 把absolute time与未来load decorrelate后，pre-positioning收益是否消失，而在线process evidence驱动的适应是否仍存在。

Candidate K — Benchmark calendar identifiability failure

机制： Generic-SHORT 把physical time暴露给policy，wave只从固定candidate windows到达，supplied labels又直接等于三种任务primitive；因此一个有限状态calendar controller可以预先保持“一名PERSIST，其余SHORT”附近的配置。

解释的证据： hindsight perfect authority、learned excess由PREWAVE主导、within-wave多owner贡献为负。

最终能力潜力： 它不是算法候选，而是“当前benchmark未识别目标能力”的因果解释。

置信度： 高。

替换账本：

retain：dynamic membership、terminal external reward、active-time opportunities和严格credit；

delete：由固定candidate windows和primitive-as-skill造成的shortcut；

replace：benchmark evidence boundary，而非policy模块；

minimally add：使load timing、required persistence和member-specific temporal demand真正需要在线适应的任务条件。

最强反证： 在未见且不可由absolute time预测的schedule上，现有learned controller仍稳定产生同类pre-positioning advantage，而简单calendar／finite-state null失败。

分离观察： time-only或candidate-window-only controller在held-out schedule上的性能上界。

Candidate D — Information-matched direct active-set recurrence

机制： primitive-time recurrent policy直接学习持续与响应行为；所谓skill lifetime只是hidden-state持续性，不需要显式skill object。

解释的证据： clean carrier上的direct recurrent learner已取得接近完美的deterministic与stochastic access，而多轮hierarchy运行尚未建立material naturally executable skills。

最终能力潜力： 一个共享ordinary MARL algorithm处理runtime membership；是否足以支持最终decentralized heterogeneous-lifetime能力仍未确定。

置信度： 当前carrier上高；最终目标上中等。

替换账本：

retain：anonymous membership、survivor recurrence、active masks、centralized training critic；

delete：high policy、skill labels、KEEP/SET actor、semantic objective；

replace：两级policy替换为primitive recurrence；

add：无。

最强反证： 一个learned-skill hierarchy在控制频率、actor-visible information、communication、参数量、环境与optimizer exposure匹配时，对未见roster和lifetime提供material external-utility或sample-efficiency优势。

分离观察： 信息匹配后的hierarchy-minus-direct held-out utility，而不是训练内label可解码性。

当前direct actor并非严格local-only：它读取active-member embedding sum、log(1+N)和同一primitive frontier中的earlier-action counts。因此它是强access null，但在最终比较前必须匹配通信与控制权限。

Candidate P — Applied-prefix value exists only in a different coordination regime

机制： 在真正需要同一multi-owner frontier内反协调的任务中，later owner可能需要读取earlier applied commitments；当前toy恰好主要由跨时间pre-positioning解决，所以未暴露该价值。

解释的证据： mean TV证明F1图中存在working-summary参数路径。

最强冲突： 当前最直接的行为证据全部逆向：multi-owner-later excess为负，associated directional mean为负，且没有F0 causal comparator。

置信度： 低。

替换账本：

retain：F0/F1共享的lifecycle、credit、collector与representation spine；

delete：在当前Generic-SHORT上继续为prefix辩护；

replace：只在确实需要simultaneous assignment的未来evidence source中重新提出P；

add：不增加模块。

最强反证： 在非calendar benchmark中，architecture-matched F0仍匹配F1，或F1 distributional dependence不运输到external utility。

分离观察： future task中multi-owner later-token common-support directional shift与实际completion/recovery之间的paired external effect。

架构合同本身也规定：F1只有在earlier applied edits改变common-support relative scores，并相对容量、collector、credit和数据合同匹配的F0提高utility时，才具有不可约内容。

3. Toy-line stop or reuse analysis

精确 Generic-SHORT supplied-executor F1 toy line应停止继续扩展。

本轮已经完成该toy能够提供的主要科学信息：

dynamic-membership lifecycle、mask、survivor continuity、event credit和checkpoint实现可用；

exact exogenous frontier authority在hindsight意义上足以完成任务；

原myopic routing oracle不是upper bound；

learned high在fixed primitives下能学习高utility的task-local persistent configuration；

该增益主要来自pre-wave placement与long KEEP；

当前数据不支持load-bearing multi-owner applied prefix。

继续在同一toy上训练F0/F1、加入learned executor、改变schedule或扩展seed，只会重新包装已被识别的calendar scheduling问题，而不会增加对最终skill abstraction的识别力。注册分支本身已把该结果定义为停止本toy上的F1扩展。

可以复用的不是task conclusion，而是基础设施与负面原则：

typed JOIN／temporary LEAVE／REJOIN／terminal LEAVE；

active-only routing与epoch-safe state；

exogenous per-member opportunity ledger；

owner-local physical-time return；

exact order、mask和working-prefix replay；

mid-segment fail-closed checkpoint；

frontier-constrained Pareto DP及行为贡献归因；

“myopic full-step oracle投影到稀疏frontier可能不是upper bound”这一设计警告。

不能复用为正向算法证据的内容：

supplied labels作为learned skills；

pre-positioning作为skill semantics；

long KEEP作为heterogeneous learned lifetime；

F1 working-summary TV作为cooperation；

hindsight planner作为可部署policy；

learned-versus-frozen task gain作为hierarchy superiority。

因此，当前toy对最终目标的最佳角色是：

一个已完成的runtime/credit基础设施正控制，加上一个“calendar-prepositioning会冒充temporal abstraction”的反例。

4. Ordinary-MARL reduction

需要区分两个ordinary reductions。

机制级 reduction：scheduled recurrent mark policy

与当前event controller完全共享：

membership spine；

exogenous opportunities；

fixed primitive executor；

owner-event return；

control frequency；

active-set representation；

但只根据initial active context和owner recurrence选择mark，不读取同frontier earlier edits。这是F0意义上的最强简单解释。F0与F1的正式合同本来就要求相同module graph、tensor width、critic、collector和数据合同，唯一区别是initial summary与working summary。

本轮不应在同一toy上再训练这个F0；但科学解释上，当前数据已经更接近该reduction，而不是F1-specific合作。

端到端 reduction：primitive-time direct recurrence

它完全删除event abstraction，每个primitive step直接选择action。Clean direct结果已经建立task access，所以任何完整hierarchy claim最终必须超过它，而不是只超过frozen high。

在宣称hierarchy超过ordinary MARL前，至少还缺：

learned而非supplied executor；

intervention-sensitive且persistent的behaviors；

natural-policy use；

shortcut与calendar null；

actor-visible information与communication匹配；

control-authority／optimizer exposure匹配；

未见membership schedules与active-lifetime distributions；

material external utility或sample-efficiency advantage。

若显式skill只是把IDLE/PERSIST/SHORT换成三个label，或仅把ordinary recurrent state显式化，则应归约为scheduled MARL，而不是视为新的hierarchical capability。

5. Variable lifetime and learned-skill boundary

必须区分三个对象。

Persistent mark

一个离散控制mark在两次外生opportunity之间保持。其持续时间部分由外生gap决定，连续KEEP可延长active run。

Supplied primitive

本轮的label与primitive action严格恒等：

0 -> IDLE
1 -> PERSIST
2 -> SHORT

executor参数数目为零，不存在low likelihood、low replay、low optimizer或low gradient。

Learned skill

至少需要：

z经learned low policy产生可干预的closed-loop behavior；

effects跨有意义process window持续；

超出execution noise、action tape和task shortcut；

在natural policy中被使用；

跨context、member和lifetime可复用；

对external joint capability有负载价值。

本轮建立的是第一种对象，使用的是第二种executor，完全没有建立第三种对象。

Event runtime确实正确区分：

physical time；

opportunity time；

owner-event depth；

active skill age；

continuous KEEP run；

membership boundary。

Temporary absence冻结state、skill、age与gap，REJOIN恢复；external membership event没有actor likelihood；gamma按真实physical duration进入return。

但pre-wave long KEEP不能据此称为“variable-lifetime efficacy”，因为：

没有learned skill；

没有lifetime heterogeneity estimand；

没有shared-renewal或fixed-lifetime comparator；

没有unseen-duration test；

一个近静态配置可能完成任务。

未来合格的lifetime evidence必须证明：不同成员因在线状态而自然产生不同active execution lengths，这些长度对任务有因果价值，并且不是absolute-time calendar、duration catalogue或task-specific lifetime reward的产物。

Intrinsic boundary不变：不得读取goal、identity、role、contact、phase、distance、success、progress或external reward；当前action-determined clean actuator继续只能audit，不能复活C1或R29。

6. Benchmark identifiability

当前 Generic-SHORT 更清楚地识别了：

sparse opportunities
+ persistent primitive marks
+ predictable duty windows
-> useful pre-positioning

而不是：

reusable learned skills
+ heterogeneous semantic lifetimes
+ applied-prefix cooperation

其shortcut来源组合包括：

physical time是policy-visible；

wave arrivals来自固定candidate sets；

wave duration固定为4步；

contribution固定需要2步SHORT streak；

task最优结构接近“一名PERSIST，其余SHORT”；

supplied label直接等于task action；
-未来精确arrival虽隐藏，但candidate calendar高度受限。

G_H=1说明控制权限足够；PREWAVE dominance说明learned policy利用权限的方式主要是提前维持mark。两者联合表明，当前benchmark的主要难点是sparse-opportunity calendar planning，而不是skill semantics。

未来真正load-bearing的任务应具备以下性质，而不是预先指定某个模块：

load onset不能由absolute time或固定candidate window充分预测；

train与held-out中的schedule、roster和duration分布发生明确变化；

optimal behavior需要根据在线局部process evidence调整，而不是长期固定一组primitive labels；

member-specific duty duration真实不同，且membership churn改变最优commitment；

skill候选对应多步closed-loop process，而不是单一task action；

ordinary information-matched recurrent controller首先能取得access；

static calendar／pre-positioning controller有明确性能上界；

external reward保持任务原生，算法不读取task-shaped intrinsic；

最终比较同时读取natural execution、held-out external value与sample efficiency。

这样的任务才可能区分：

calendar scheduling；

ordinary recurrence；

persistent event abstraction；

reusable learned skill abstraction；

applied-prefix team assignment。

7. Two or three next-evidence candidates

以下三个是并列的未来证据候选，不构成选择或授权。

Evidence candidate A — Benchmark identifiability contract

Comparator：

absolute-time／candidate-window finite-state prepositioning null；

causal ordinary recurrent controller；

clearly labeled non-causal hindsight authority ceiling。

Estimand：

held-out schedule上adaptive controller相对calendar null的external utility；

static-null ceiling；

causal ordinary access；

membership与duration变化的分层效应。

Mutually exclusive branches：

calendar null仍成功：候选benchmark不识别temporal abstraction；

calendar null失败、ordinary recurrent通过：benchmark具有adaptive access；

hindsight通过但ordinary recurrent失败：NO_ACCESS，不读取hierarchy；

hindsight也失败：任务/权限设计不可达。

Portfolio update：

分离K与D，并决定是否存在讨论R/P/B的基础。

Prohibited rescue：

不通过reward shaping、身份、角色、扩大budget或改变threshold制造access。

Minimal boundary：

先完成任务与comparator合同、constructive feasibility和static-shortcut analysis；不含skill learner或intrinsic reward。

Evidence candidate B — Information-matched ordinary-control matrix

仅在一个已通过identifiability与access的任务上讨论。

Comparator：

primitive-time direct recurrent controller；

same-information、same-communication、same-capacity的scheduled persistent-mark controller；

control-authority差异必须显式计费。

Estimand：

unseen roster／schedule／duration上的external utility与sample efficiency；

scheduled abstraction相对primitive recurrence的增量。

Mutually exclusive branches：

两者等价：D上升，event abstraction没有负载价值；

direct胜出：scheduled commitment可能造成响应限制；

scheduled mark胜出：persistent event abstraction有价值，但仍不是skill evidence；

两者均无access：停止算法归因。

Portfolio update：

区分D与R；不直接支持P或learned skills。

Prohibited rescue：

不加入posterior、learned timing、graph、team latent或new critic。

Minimal boundary：

只有一个控制粒度／persistent-mark causal edge；相同observation、reward与训练资源。

Evidence candidate C — Conditional learned-executor necessity source

仅当一个未来benchmark已经证明persistent abstraction本身负载有效时才有识别力。

Comparator：

capacity-matched shared skill-conditioned low executor；

factorized discrete executor；

same high/event spine；

information-matched direct null。

Estimand：

natural executable differentiation；
-跨JOIN/REJOIN、age和held-out schedule的稳定性；

factorized-minus-shared external utility；

hierarchy-minus-direct held-out advantage。

Mutually exclusive branches：

factorized形成natural semantics并提高held-out utility：executor-interference解释上升；
2.只增加logit/action diversity：任意diversity，退休该替换；

shared与factorized等价：共享executor不是主要瓶颈；

hierarchy都不优于direct：skill abstraction不load-bearing。

Portfolio update：

更新learned-executor候选，而不重新打开当前toy的P。

Prohibited rescue：

不加入Iteration-5 C1、R29/R31–R33 effect reward、更多skills、simplex、hazard或task shaping。

Minimal boundary：

只替换low executor parameterization；其他概率、credit、数据、预算与checkpoint合同保持一致。

8. Valuable unselected ideas

Actor-information-matched causal planner

Hindsight只证明authority，不证明causal information sufficiency。严格的belief/history-equivalent planner仍有理论价值；当前park，因为在未定义充分information state前，它很容易退化成调heuristic或oracle rescue。

Applied-prefix P on a non-calendar coordination task

当前toy上的证据明显反对P，但不构成对所有任务的全局否定。只有未来任务天然包含大规模simultaneous frontier、反协调约束，且pre-positioning不能解决时，P才值得重新进入active portfolio。

Schedule-shift frozen evaluation

可以检验当前learned checkpoint是否记忆candidate calendar，但不会改变本轮“停止该toy上的F1扩展”的结论，也不能提供F1-vs-F0 causality，因此当前park。

Factorized executor B

Fixed primitives表明high graph不是完全失活，但不证明历史shared low failure由parameter interference造成。B只保留为未来load-bearing benchmark上的replacement candidate。

Simplex process command C

只有one-hot learned skills已成立，且non-vertex composition带来B无法复现的held-out process value时才有独立意义；当前加入只会增加ordinary-recurrence reduction风险。

Learned opportunity hazard

保持关闭。学习event time需要完整survival、intensity、termination和censoring likelihood，会改变当前authority合同；不能把它用作myopic oracle失败的scheduler-only修复。

Representation扩展

InforMARL支持shared、permutation-safe active-set encoding原则，但其fixed-config runner不解决episode内membership。Graph、attention、slot或communication只能在实际证明sum/count信息不足后作为替换，而不能和skill、hazard、posterior同时堆叠。

时间与event-credit原则

ACAC提供gamma按真实微时间、lambda按owner-event深度的可复用原则；ACE提供per-member readiness与dropout pressure，但固定roster/buffer和错误duration return不能迁移。

9. Stop and integration conditions

当前exact supplied-executor Generic-SHORT line的停止条件已经满足。

理由不是opportunity不可达，而是：

authority可达；

excess work由PREWAVE唯一主导；

multi-owner-later为负；

working-prefix aggregate direction为负；

supplied primitives不是learned skills；

direct recurrent access已成立。

因此不应在同一toy上：

训练F0/F1；

更换oracle；

改wave/gap/schedule；

加learned executor；

加intrinsic、posterior、hazard、graph、critic或team latent；

扩seed、budget或threshold。

Candidate merge／retire条件：

R并入ordinary MARL： 若未来scheduled persistent-mark policy与direct recurrence等价，则把event marks视为普通controller state，而非hierarchy。

K退休： 只有一个去calendar、held-out schedule benchmark证明当前解释不能复现时，calendar-identifiability解释才下降。

P退休： 在未来真正multi-owner、非prepositionable任务中，matched F0仍noninferior，或working-prefix dependence不运输到external utility。

D下降： 只有learned-skill hierarchy在信息、通信、控制权限、容量和exposure匹配时取得held-out material advantage。

Learned-executor路线退休： learned z只有label/logit差异，不能形成persistent natural behavior，或形成behavior但不优于direct。

整个skill/hierarchy研究线应停止于以下任一情形：

未来load-bearing benchmark仍由direct或scheduled mark controller充分解决；

所有learned executor都无法产生natural、persistent、shortcut-resistant skills；

skills可执行但没有held-out external value；
4.唯一成功依赖task fields、identity、role、duration catalogue或退休effect reward；

只有模块堆栈才能产生效果，无法归因；

ordinary access本身未建立。

进入独立integration review的必要条件：

learned而非supplied executor；

anonymous runtime JOIN／LEAVE／REJOIN和survivor continuity；

exact active masks、probability、RNG、replay和mid-segment checkpoint；

physical／opportunity／event／segment clocks及gamma^Δ credit正确；

intervention-sensitive、persistent、nuisance-resistant、natural skills；

heterogeneous active-time lifetime具有因果价值；

无calendar、identity、task-shaped intrinsic或action-tape shortcut；

与information- and communication-matched direct recurrent policy比较；

在未见roster、schedule和lifetime上取得material external-utility或sample-efficiency优势；

贡献来自一个明确替换，而非模块累积。

本轮结果只支持停止当前toy上的F1扩展并更新plural portfolio；它不授权任何后续实现、训练或集成。
