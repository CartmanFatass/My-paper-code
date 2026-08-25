1. Evidence-validity disposition

接受注册结果 HINDSIGHT_REACHABLE_PREPOSITIONING_REDUCTION，同时永久保留原 G0 的 INVALID_CLEAN_SUPPLIED_EXECUTOR_OPPORTUNITY_CONTRACT。

本轮审计是一个新的、有效的只读证据源，而不是对原 G0 的追溯性修复。全部审计项为真：learned、frozen 与 current-oracle 在原 256 个 evaluation ledgers 上逐 episode 精确复现；frontier/order 一致；hindsight 只能修改实际 frontier owner；未来 ledger 只进入 solver；tiny DP 与 brute force 等价；贡献分类唯一；high/low optimizer step 与参数漂移均为零；checkpoint 和注册 header 均精确。

新的证据增量有三项：

结构性机会权限可达。 受实际 membership、wave、opportunity frontier、order 和 supplied executor 约束的非因果 hindsight controller 达到联合 P/S/U=1/1/1，所以原 1..19 gap 与任务本身并非结构性地无法跨过联合 0.95 floor。由于每个 episode score 上界均为 1，三个平均值均为 1 还意味着每个被评估 episode 都存在一条同时达到 P=S=1 的合法 frontier-constrained trajectory。

Learned 相对 current oracle 的额外 SHORT work 被定位到 wave 前。 PREWAVE_SHORT=+10.613281，且它相对其他所有类别的 paired-bootstrap LCB 均严格为正；singleton、multi-owner-first 与 multi-owner-later 的 excess 均为负。

F1 working-summary 路径存在，但没有注册方向上的正向运输。 2,700 个 later-token row 的 mean TV 为 0.081369，证明 working summary 会改变checkpoint-local distribution；但 missing-SHORT change、completion/recovery-associated directional mean 分别为 -0.013745 和 -0.039538，positive-direction flag 为 false。166 个局部正向 row 阻止“prefix 在任何地方都没有影响”的过强结论，却不足以支持合作或 utility claim。

因此，上一轮的 结构不可达解释被否定，current routing oracle 也应永久退出“upper bound”角色；但原 G0 仍然 INVALID，因为它预注册的 comparator prerequisite 实际失败，后续审计不能改变其分支历史。

本轮不能建立：

actor-information-matched causal policy 能达到 hindsight ceiling；

learned policy接近最优；

learned controller“只是”记忆了calendar；

F1相对F0的因果utility优势；

learned skills、skill semantics或heterogeneous learned lifetime；

hierarchy相对information-matched direct recurrence的优势；

transfer、合作或integration资格。

Supplied labels仍是零参数的 primitive commands，而不是learned skills。Pre-positioning、long KEEP和高task utility都不能替代项目规定的 intervention-sensitive、persistent、shortcut-resistant、natural且externally load-bearing skill证据。

2. Divergent factual adjudication
Structural authority

Repository fact。 Hindsight solver只在实际发生的frontier上枚举IDLE/PERSIST/SHORT，非frontier commitments保持不变；未来信息只进入solver，不进入三条行为replay。其episode DP只在相同future-relevant control state内做Pareto pruning，并有tiny-ledger brute-force等价控制。

正确解释。 当前opportunity authority在非因果意义上足以完成任务。

不支持。 它不是deployable oracle、policy baseline、causal information sufficiency证明，也不是原G0的修复。

PREWAVE attribution

Repository fact。 Learned-minus-current-oracle的主要extra completed work来自PREWAVE_SHORT，而非wave后multi-owner later token。这个结论是相对于当前myopic oracle的贡献差，而不是对learned policy全部SHORT work的完整因果分解。

合理推断。 Learned controller利用了pre-positioning、持久primitive mark和long KEEP。

不能升级的结论。 不能称其为skill semantics、cooperative option discovery或heterogeneous learned lifetime。

Calendar memorization

高可信推断，但不是repository fact。 当前任务暴露physical time，wave来自固定candidate windows，wave长度与SHORT streak均固定，而supplied label直接等于task primitive；这些性质确实允许一个time-aware finite-state controller提前配置。

然而现有source没有time-only matched arm、held-out schedule intervention或calendar-permutation counterfactual。因此Gemini的“policy只是记忆calendar”措辞过强。正确说法是：

当前证据高度支持calendar-compatible pre-positioning reduction，但尚未将absolute-time memorization与其他causal recurrent use完全分离。

Working-prefix evidence

Repository fact。 Working summary改变了later-token distribution，并存在166个局部正向associated rows。

收敛裁决。 当前toy上的load-bearing P claim被显著削弱并应park：multi-owner-later excess为负，aggregate directional read为负，而且不存在F0 causal treatment。不能说prefix数学上完全无效，也不能以TV或少量positive rows声称cooperative assignment。架构合同本身要求working prefix改变common-support relative scores，并相对capacity/collector/credit/data matched F0提高外部utility，才能具有不可约内容。

Persistent-mark semantics

Repository fact。 一个active skill/primitive mark会在两次外生机会之间保持；KEEP继续active age，temporary LEAVE冻结state、mark、age与gap，REJOIN恢复，physical-time reward以γ
Δ
进入owner event return。

科学解释。 这验证了persistent command与事件所有权基础设施。

不支持。 当前mark是supplied primitive，不是learned closed-loop skill；其持续长度主要受外生gap和KEEP影响，也没有lifetime heterogeneity、shared-renewal或unseen-duration estimand。Gemini提出的continuous write/read mark是一个新候选接口，不是本轮已验证对象。

“必须超过RNN记忆长度”

拒绝为无依据提案。 一个合格benchmark应通过held-out schedule、online process evidence、information matching和temporal controls区分ordinary recurrence与persistent abstraction，而不是人为延长间隔、截短BPTT或削弱RNN直到direct policy失败。人为制造memory failure不能证明hierarchy必要。

3. Weighted causal portfolio
K — 当前benchmark存在calendar-identifiability限制

权重：高。

固定candidate windows、可见physical time、固定4-step wave、固定2-step SHORT streak以及primitive-as-label，使pre-positioning能够在没有learned skill abstraction的条件下取得高utility。它解释了PREWAVE dominance、负的multi-owner-later excess以及负的working-prefix aggregate direction。

最强反证： 在绝对时间和candidate-window无法预测的held-out schedules上，time/calendar-only matched controller失败，而具有相同信息和容量的causal adaptive controller仍可靠访问。

退休条件： 一个经过资格审查的noncalendar benchmark证明calendar/static null无法解释行为与外部价值。K是benchmark解释，不是production module。

D — Information- and communication-matched direct recurrence

权重：高；当前经验领先者和强制null。

Clean carrier上的primitive recurrent learner已取得接近完美的deterministic/stochastic access；多轮hierarchy evidence则尚未建立material naturally executable skills。

最强反证： 一个learned-skill hierarchy在control frequency、actor-visible information、communication、容量、environment exposure和optimizer exposure匹配时，在未见roster、schedule及active-lifetime distributions上提供material external-utility或sample-efficiency优势。

当前direct actor每个primitive step均可行动，并读取active-set aggregate与earlier-action prefix，因此是强access null，但不是无需信息匹配即可用于最终decentralized superiority claim的现成比较器。

R — Persistent event abstraction without a learned-skill claim

权重：中。

R保留anonymous lifecycle、外生per-member opportunities、persistent mark、KEEP/SET、owner-local γ
Δ
 credit和survivor continuity；删除F1 working-prefix dependence以及“learned skill/cooperative editor”解释。其最简形式是same-information scheduled recurrent mark controller。

当前toy对R提供了机制存在性证据：稀疏机会之间保持mark和pre-positioning有用。但它没有证明该抽象相对primitive recurrence具有load-bearing价值。

最强反证与合并条件：

在合格benchmark上，information-matched direct recurrence与scheduled mark controller等价或更优：R并入D，mark被解释为普通controller state。

Scheduled mark在held-out schedule/lifetime上显著优于direct：R上升，但仍只是temporal abstraction，不自动成为skill evidence。

其优势只能通过calendar、supplied labels或task-specificlifetime cue取得：退休R的通用claim。

B — Learned executor remains a conditional downstream bottleneck

权重：低、条件性保留。

历史Stage C和Iterations 4–5显示shared skill-conditioned low actor未形成material natural semantics；fixed primitives又表明high/event graph至少能够学习一个task-local策略。这使“learned executor仍是瓶颈”保持可能，但没有证明factorized adapters是正确替换。

激活条件： 必须先有一个benchmark证明persistent abstraction相对matched direct具有外部负载价值。之后才可比较capacity-matched shared executor与factorized executor。

退休条件： Adapters只有gradient、logit或action diversity，没有persistent natural behavior、held-out external value，或hierarchy仍不优于direct。

P — Applied-prefix assignment value

处置：parked，不占当前live slot。

当前证据明显反对P在Generic-SHORT上的load-bearing解释，但166个局部positive rows和非零TV阻止全局永久否定。只有未来出现非calendar、不可通过pre-positioning解决、自然包含multi-owner simultaneous assignment的任务时，P才可重新进入active portfolio。届时必须使用architecture-matched F0 treatment，而不是checkpoint-local summary substitution。

4. Toy-line stop and broader research boundary

精确的Generic-SHORT supplied-executor F1 toy line已经完成，应停止。

本toy已经提供其可提供的全部主要信息：

anonymous JOIN、temporary LEAVE、REJOIN、terminal LEAVE、active masks和survivor continuity工作；

exogenous opportunity ledger、owner-local duration credit、exact order/mask/replay和mid-segment checkpoint工作；

实际sparse frontier authority在hindsight意义上足够；

current routing oracle不是upper bound；

learned high可在fixed primitives下形成高utility persistent configuration；

增益主要来自PREWAVE placement与long KEEP；

当前证据不支持load-bearing F1 applied-prefix composition。

因此不得在同一toy上：

训练新的F0/F1 pair；

改wave、gap、schedule或oracle；

加learned executor；

做schedule-shift来为F1争取新分支；

加intrinsic、posterior、hazard、graph、critic、team latent或communication；

增加seed、budget或改threshold。

可复用的是runtime、probability、credit、checkpoint和审计工具，以及两条负面原则：

将full-step constructive rule投影到稀疏frontier后，它未必仍是upper bound。

Predictable calendar + persistent marks会伪装成temporal abstraction或skill-lifetime进展。

停止该toy并不退休更广泛的variable-membership plus variable-lifetime目标。项目使命仍要求一个共享算法支持episode内membership churn和不同成员的自然skill lifetime；当前toy只是不足以识别这个目标。

5. Selected next evidence source or stop

选择一个新的独立证据源：

BENCHMARK_IDENTIFIABILITY_AND_ORDINARY_ACCESS_G0

它不是Generic-SHORT的变体或救援，也不包含hierarchy、F0/F1、learned skill、intrinsic reward或新module。其唯一问题是：

能否构造一个在anonymous dynamic membership下结构可达、ordinary recurrent controller可访问、calendar/static pre-positioning不能解决、且shared/fixed lifetime约束确实造成外部损失的最小benchmark？

这是当前最高信息增益的source，因为在任何新skill或hierarchy实现之前，它可以同时：

确认或拒绝K；

建立或否定ordinary access；

验证heterogeneous lifetime是否真正load-bearing；

为未来D-vs-R提供可识别基座；

在失败时产生真实stop，而不是继续制造toy。

它不是一串隐藏gate：hindsight authority、calendar null、shared-lifetime null和ordinary recurrent learner必须出现在同一个冻结合同、同一个结果和互斥分支中。

不选择以下来源：

Existing-checkpoint calendar reanalysis： 可以加强“当前checkpoint利用calendar”的描述，但不会改变Generic-SHORT toy stop，也不能确定下一个通用算法。

Information-matched D-vs-R matrix： 当前没有合格的load-bearing benchmark，直接比较会把task shortcut与architecture effect混合。

Learned-executor B： persistent abstraction本身尚未证明比direct有价值，立即替换low executor属于在未识别边上增加机制。

Matched F0/F1： 当前分支明确park P，并禁止同toy训练。

选择依据符合项目要求：先选择能够改变portfolio权重、造成候选退休或产生真实stop的最小source，而不是因实现方便而选择实验。

本建议不授权任务设计、代码或计算。

6. Exact estimand, comparator and information contract
Benchmark能力合同

新benchmark必须是独立任务，而非修改Generic-SHORT的wave参数。它至少满足：

episode内anonymous JOIN、temporary LEAVE、REJOIN、genuine JOIN和terminal LEAVE；

survivor recurrent state连续；

workload onset不能由absolute time或有限candidate windows充分预测；

当前causal local/process observations在需求发生时提供适应信息；

不同active members的最优commitment长度真实不同；

membership churn会改变最优assignment与持续时间；

shared renewal或统一fixed duration在部分episodes中结构性受损；

primitive action形成multi-step closed-loop process，而不是label直接等于task role；

外部reward为task-native，算法不读task-shaped intrinsic、identity或role；

train与held-out在schedule、roster和required-duration distributions上有事前登记的变化，但policy-visible字段保持相同语义。

四个比较对象

1. H：frontier/control-constrained hindsight authority

非因果；

可读完整未来schedule、membership和demand ledger；

只能使用任务注册的合法control authority；

只回答结构可达性，绝不是policy baseline。

2. C：calendar/static recurrent null

causal；

与ordinary learner拥有相同网络宽度、参数数、optimizer exposure、active-set communication和control frequency；

对online process-demand字段使用固定零值，只可读取absolute time、active count、membership-event flags、current command与自身hidden；

用于检验calendar、roster phase或static pre-positioning是否足以解决held-out任务。

3. S：shared-renewal/fixed-lifetime hindsight ceiling

非因果并拥有完整未来信息；

与H使用相同行为支持；

额外约束所有active members只能在一个shared renewal clock更新，或必须使用同一registered lifetime；

用来检验heterogeneous individual lifetime是否为任务的结构必要条件，而不是算法质量。

4. D：causal ordinary recurrent access controller

无skill、高层token、KEEP/SET actor、intrinsic或task shaping；

读取current anonymous local process evidence、membership flags和一个明确计费的permutation-compatible active-set summary；

与C使用相同参数、optimizer、environment exposure、control frequency、communication和evaluation；

routing keys、identity、future ledger、reward history和oracle fields均不可见。

Primary estimands

令任务原生的两个归一化components为A,B，utility为U∈[0,1]。

结构可达性：

G
H
	​

=min(
A
ˉ
H
	​

,
B
ˉ
H
	​

,
U
ˉ
H
	​

).

Calendar shortcut gap：

Δ
K
	​

=
U
ˉ
D
heldout
	​

−
U
ˉ
C
heldout
	​

.

Heterogeneous-lifetime pressure：

Δ
T
	​

=
U
ˉ
H
heldout
	​

−
U
ˉ
S
heldout
	​

.

Ordinary access：

Δ
D
	​

=
U
ˉ
D,final
heldout
	​

−
U
ˉ
D,zero
heldout
	​

.

合同必须在实现前冻结：

G
H
	​

的绝对component/utility floors；

Δ
K
	​

,Δ
T
	​

,Δ
D
	​

的material margins和paired confidence rules；

train/held-out schedule、roster、duration distributions；

model、budget、optimizer exposure和checkpoint选择。

不得在观察结果后修改。

Source不能建立

即使全部通过，也只建立：

一个结构可达、ordinary-access-valid、calendar-null-resistant且使heterogeneous lifetimes具有外部压力的benchmark。

它不能建立R优于D、learned skills、P、B、hierarchy价值、transfer或integration资格。下一次D-vs-R是另一个独立因果source。

7. Mutually exclusive branches and portfolio updates
INVALID_BENCHMARK_IDENTIFIABILITY_G0

触发： dynamics/reward错误、future leakage、calendar/direct输入不匹配、communication/control-frequency不匹配、solver不精确、replay/checkpoint/count/RNG失败。

更新：

只修具体缺陷；

K、D、R、B和parked P权重不变；

不修改task、model、budget或threshold。

REJECT_BENCHMARK_STRUCTURALLY_UNREACHABLE

触发： H未通过事前登记的联合authority floors。

更新：

拒绝该benchmark；

K不被检验；

D/R/B/P均不可解释；

不以reward shaping、更多budget或oracle字段救援。

由于这是Generic-SHORT结束后的独立qualification，不自动制造下一个synthetic toy；控制器应回到最终benchmark requirement或停止当前toy-search程序。

REJECT_BENCHMARK_CALENDAR_IDENTIFIABLE

触发： C达到绝对task floors，或Δ
K
	​

未达到事前material margin。

更新：

K在该benchmark上得到支持；

D的成功只说明access，不能支持adaptive capability；

R/B/P均不具识别力；

拒绝benchmark并停止在其上做算法比较。

REJECT_BENCHMARK_NO_HETEROGENEOUS_LIFETIME_PRESSURE

触发： S满足task floors，或Δ
T
	​

未达到material margin。

更新：

Benchmark可能需要online adaptation，但不需要不同individual lifetimes；

R的variable-lifetime解释下降；

B和P不进入；

D保持ordinary solution；

拒绝其作为最终目标的lifetime test。

NO_ACCESS_BENCHMARK_ORDINARY_CONTROL

触发： H通过、calendar与shared-lifetime null均失败，但D未通过绝对access及Δ
D
	​

门。

更新：

不读取任何hierarchy implication；

D的最终充分性不被否定，只是当前benchmark/model/budget未建立access；

R/B/P全部保持未识别；

不通过扩大RNN、预算、seed或加入intrinsic救援；

停止该benchmark的算法线。

PASS_BENCHMARK_IDENTIFIABILITY_AND_ORDINARY_ACCESS

触发： authority通过；calendar null失败；shared-lifetime ceiling显示material loss；ordinary direct同时通过绝对access、learning-gain和held-out gates。

更新：

K在该benchmark上显著下降；

D继续作为高权重null；

R首次成为可识别的algorithmic alternative；

下一次可审阅source是严格information-matched的D-vs-scheduled-R comparison，但本branch不自动授权；

B仍保持条件性：只有R先相对D取得held-out material advantage，learned executor问题才变得可识别；

P继续park，除非benchmark自然产生不可pre-position的multi-owner same-frontier反协调。

整体停止边界

当前Generic-SHORT toy已经停止。更广泛的synthetic abstraction line在以下任一条件满足时应停止：

新benchmark结构不可达、calendar-null仍充分或ordinary access失败；

合格benchmark上R与D等价；

learned skills无法形成natural persistent behavior；

skills存在但没有held-out external value；

唯一成功需要task fields、identity、duration catalogue、retired effect reward或module stack。

8. Minimal boundary and prohibited changes

未来若控制器依据既有authority单独 operationalize，本source的最小写入面应限制为：

docs/research/designs/NONCALENDAR_HETEROGENEOUS_COMMITMENT_BENCHMARK_G0.md

完整task、information、comparator、threshold、seed、budget和branch合同；

ha_ctse_process/noncalendar_commitment_testbed.py

新的独立environment、ledger、hindsight与shared-lifetime controls；

scripts/run_noncalendar_commitment_benchmark_g0.py

一个runner、一个terminal result；

tests/ha_ctse_process_noncalendar_commitment_benchmark_g0_test.py

structural feasibility、calendar masking、membership、RNG、replay和checkpoint检查；

必要时新增一个task-local direct wrapper，但不得改写既有Generic-SHORT direct结果或其scientific contract。

以下内容保持read-only：

原Generic-SHORT testbed；

clean-process carrier；

supplied-executor G0和opportunity audit；

原checkpoints、results和dispositions；

Iteration-5 carrier/C1；

R29、R31–R33 families。

明确禁止：

relabel或重跑原G0；

在同一toy训练F0/F1；

改原toy schedule、gap、wave或threshold；

result后修改新benchmark seed、budget、model、horizon、reward或margin；

通过人为延长间隔、截短BPTT、冻结hidden或缩小RNN来制造direct failure；

task-shaped intrinsic、identity、role、progress、success、contact、phase或reward输入；

supplied skill labels、duration catalogue或lifetime payment；

graph、field、slot、attention、communication、team latent、posterior、hazard、new critic和reward stack；

best-checkpoint选择、结果后增加seed或合并strata；

将hindsight未来信息暴露给causal policy。

这些禁止项延续“valid negative不得通过seed、budget、model、threshold、reward或改名救援”的项目合同。

本建议不授权任何上述文件创建、训练或计算。

9. Valuable unselected ideas and integration conditions
Existing-checkpoint calendar reanalysis

有助于确认当前learned checkpoint对candidate windows的依赖程度，但不会改变Generic-SHORT toy stop，也不能证明F1-vs-F0或通用hierarchy价值。只有用于档案性mechanism analysis、且无需修改schedule或重新训练时才值得恢复。

Information-matched D-vs-R control matrix

这是通过新benchmark qualification后的最高优先候选。它应只改变primitive-time direct recurrence与scheduled persistent marks这一个因果边，并严格匹配information、communication、capacity、control authority和optimizer exposure。当前提前执行会把benchmark shortcut混入architecture结论。

Actor-information-matched causal planner

Hindsight只证明authority。一个严格belief/history-equivalent planner仍有理论价值，但必须先给出非启发式的sufficient-information-state定义。否则它会退化为oracle tuning。

P on a noncalendar multi-owner task

P并未被全局退休。只有未来任务自然要求多个owners在同一frontier内做不可通过pre-positioning解决的反协调，且working-prefix directional change与external completion/recovery有paired运输时，才重新激活。

Factorized learned executor B

保留为conditional replacement。它必须等待：

qualifying benchmark通过；

R相对D显示material held-out value；

之后只比较capacity-matched shared vs factorized low executor。

不得同时加入posterior、intrinsic、simplex或new credit。

Continuous explicit marks

Gemini的continuous read/write mark可作为R的未来替代接口，但当前没有证据证明discrete mark是瓶颈。只有scheduled discrete abstraction已具价值、而连续non-vertex control提供额外held-out能力时才值得提出。

Learned opportunity hazard

继续关闭。它会改变opportunity authority，并需要完整的survival、intensity、termination和censoring likelihood；不能作为calendar或myopic-oracle问题的scheduler-only修复。

Integration conditions

任何hierarchical或learned-skill candidate进入独立integration review前，必须同时具备：

learned而非supplied executor；

anonymous runtime JOIN、temporary LEAVE、REJOIN和terminal LEAVE；

survivor state continuity与active-only masks；

exact behavior probability、RNG、replay和mid-segment checkpoint；

physical、opportunity、event、segment及active-lifetime clocks和γ
Δ
 credit正确；

intervention-sensitive、persistent、execution-noise/shortcut-resistant且naturally used的skills；

不由calendar、action tape、identity、role或task-shaped intrinsic解释；

不同成员的heterogeneous active-time lifetime具有可测因果价值；

actor-visible information、communication、capacity、control authority、environment和optimizer exposure与direct recurrent null匹配；

在未见roster、schedule和lifetime distributions上取得material external-utility或sample-efficiency优势；

贡献来自一个明确替换，而不是模块累积。

最终收敛建议：接受有效的pre-positioning reduction，永久停止Generic-SHORT supplied-executor F1 toy扩展；保留K/D/R/B的加权组合并park P；唯一下一证据建议为独立的 BENCHMARK_IDENTIFIABILITY_AND_ORDINARY_ACCESS_G0。该source先证明任务本身能够排除calendar shortcut、需要heterogeneous lifetime且允许ordinary access，之后才有资格讨论D-vs-R或learned executor。