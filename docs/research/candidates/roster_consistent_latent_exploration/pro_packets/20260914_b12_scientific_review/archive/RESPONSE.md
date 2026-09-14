**独立科学审查结论：B12 的完整记录与已列源码支持三个同时成立的有限观察——相对本次初始化有真实学习，相对 nearest 有服务收益，相对 fixed greedy 的 sampled U/full-Y 仍有劣势；未发现已经证实、足以撤销这些 B12 主比较的科学缺陷。** 但 B11 的未定位 SIG11 仍是共享运行路径的完整性风险，不能由 D1 或 B12 成功消除。B10/B12 只能作为三次科学调用尝试中的两个已完成1024端点描述，不能冒充无缺失的训练总体样本。[B12 E0，完整性、Frozen observables、Missingness][e0]；[B11 failure intake，Exact execution、D1 collection][failure]。

**对后继的科学意见：所提 retained-checkpoint modal-versus-greedy 比较有明确而有限的决策价值，比再做一条 unchanged sampled fit 更直接地回答“已学得权重是否值得配另一种执行法则保留”。我支持把它作为这个问题来论证，而不把它视为已经准备完毕或必须执行的实验。** 它必须确实运行组合分布的确定性众数，正确恢复每个原模型和原评价随机地址，并把结果限于两个被保留的已完成实例及其已见面板。另有一项需要明说的规范边界：零更新的推断测量并不自动满足现行“ordinary B”的非零更新条款；后续卡需要说明适用范围，不能以旧训练次数代替本次更新，也不应为凑标签而补训。[B12 intake，Actual continuation][intake]；[study.py，evaluate、rollout、_run][study]；[policy.py，PhasePolicy、phase_log_probabilities][policy]；[证据规范 §§11.4、11.8.6、11.9][spec]。

PARK 是有力的竞争意见：当前 sampled 方法已经两次完成并落后于同支持的强规则，modal 也可能只恢复 greedy 行为而没有新用途价值。反过来，真实初始化学习、nearest 收益和局部恢复优势不能被归零，已有数据也没有显示 trained mode 的表现。当前方向在固定输入中为 ACTIVE，实际选定的是完成审查和 DM 回应；本文件不选择新调用、不下达 PARK/CLOSE，也不变更两项既有窄 HOLD。[DIRECTION，Current DM position、Current scientific question][direction]；[intake，Options、opposing observations][intake]。

## 一、实质发现、设计缺口和不应混淆的判断

**对已完成 B12：没有发现已证实的 reward、合法信息、实际策略似然、训练终点或 primary 配对错误。对拟议后继：有具体的实现/复用条件和一个证据类别适用问题需要在既有 DM 回应及后续对象说明中处理。** 这些不是已经发生的新实验缺陷，更不是审查通过令牌。

| 审查事项 | 发现及精确依据 | 实际后果与相称处理 |
|---|---|---|
| B12 测量及学习 | 新 seed32/object 域、1024 更新、四512面板与 actual combined likelihood 在已列源码和记录中相符。[card12][card12] [study][study] [a12][a12] | 保留该实例的正 G_U、正 D_n、负 D_g 和全部后果。没有据此补跑、换终点或整体隔离 B12 的理由；也不声称已独立验证所有底层依赖。 |
| B11 缺失与共享运行风险 | SIG11 发生于164个完整更新后；D1 不含初始评价前缀，B12 也没有提供致错栈或修复。[failure][failure] | 不补造 B11 终值，不称完成样本无选择性，不把成功退出当成运行安全证明。未来使用相同 native 路径仍保留该风险。 |
| Modal 不是现成 evaluator 模式 | `rollout` 对所有非 nearest/greedy 角色仍调用 `sampled_phase`；模型默认 `greedy_anchored=False`，该布尔值不是 state_dict 中的参数。[study][study] [policy][policy] | 仅改 role 名、调用 eval/no_grad 或仅载入权重都不足以实现所提对象。未来明确组合 logits 的 argmax、固定 tie、锚定标志与只读 checkpoint；不在本轮实现。 |
| 1024新评价的最小规模有条件 | 原 key、run_block、cell/scenario 地址和 native 法则必须与各自旧 greedy 面板相符；现有代码支持这种地址化设计，但本次未读取原始面板字节或底层 native 实现。[study，uniforms、evaluate、rollout][study] | 复用原始逐场景参照行可有科学依据；不能用旧均值配新世界。实际不能保持时，后续卡计入必要的新参照评价，不伪称原最小工作成立。 |
| 零更新后继的类别 | §11.4 仍把实际 learner 和非零更新列为 ordinary B 条款，§11.8.6仍要求真实 learner/trainer；现有命名例外不适用于 RCLE。[spec][spec] | 当前提案尚未错误执行，也未必已把“选项B”命名为证据类B。应明确是零新增训练的条件执行测量；若要按 ordinary B立项，需处理这项具体条款适用/有限例外，而不是默许合规、冒充新学习或添加无用训练。 |
| 服务/恢复取舍 | “modal gain with acceptable recovery”尚不是一个已定义的标量用途规则；现有 sampled 结果已显示 U 与 tau可异向。[intake][intake] [recorded][recorded] | 以后没有事先明确的实际取舍，就只报告服务与恢复向量；不因 U胜或U平就自动宣布整体成功或无价值，不事后挑恢复阈值。 |

这些问题的后果各有边界。当前记录已经承认完成者偏倚、未修复运行风险和后继未执行，我不把这些已披露限制谎称为 DM 已经作出的错误推断。需要防止的是在后续卡、实现或结论中丢掉它们；其中错误的 checkpoint 恢复、modal 分支或随机地址会真正改变所测对象，不能仅靠措辞补救。[intake][intake]；[spec §§8.1、11.8.5–11.8.7][spec]。

## 二、B12 的固定设计和实际学习链

### 新对象、原法则和四个真实角色

B12 是在 B11失败后另行说明的新对象 `RCLE-TBCFV-B12-GREEDY-ANCHORED-1024-INDEPENDENT`，unscreened seed32/run_block0；不是继续 B11 的参数、优化器、baseline、RNG 或未完训练。B12卡明确继承 B11卡的 Fixed scientific object、Observable and prospective interpretation 及工作计数；变化是新对象域/seed以及用于观察故障的 debugger/faulthandler，不是新的 policy/native 修复。[card12，DM selection、Exact scientific mapping][card12]；[card11，相应继承段][card11]。

`study.run_b12_exposure1024` 检查32，进入 `_run(..., B12_OBJECT, 1024, True)`。后者用该对象和seed生成 key，建立模型、自己的优化器和八个零起始 baseline，先评价初始化，再完成1024个64-episode块，最后保存 `final1024.pt`并评价 final/greedy/nearest。局部 `final_role`传到 checkpoint、面板与 contrasts；文件开头为旧入口保留的 `ROLES/final256`并没有取代此链。不存在由可见代码显示的 B12/旧终点混用。[study，run_b12_exposure1024、_run、contrasts][study]。

每个训练块为八个6/10训练格各八episode，经两个native32 batch组成。评价是八个8/12格各64场景，分别属于初始化、sampled final1024、fixed greedy、attained nearest；四角色不是四次训练。没有中途用 held-out 面板选最佳 checkpoint，也没有把最后32个训练更新的平均回报改成评价端点。[study，_run、evaluate][study]；[card11，Fixed scientific object][card11]。

### 合法公共信息、共同动作及实际似然

native120-sector、六beacon、H64、四tick claims及t24成员/epoch变更不变。`rollout`先应用需要的 event，再读取当前公共快照、按当前N分组并发出行动，最后推进物理服务。survivor物理状态属于原实体，departure不留行动行，newcomer按原生规律加入；rank来自当前实体而不是持久学习身份。nearest同样在自身的事件后快照上调用已有 scripted kernel。[card11，Fixed scientific object][card11]；[study，rollout][study]。

相位s对应整个team的循环配额映射 `a_i=b[(r_i+s) mod N]`。`quota_arrays`使用int64位置、rank、demand与beacon，保留半圈clockwise tie；greedy在同一N个映射上最小化当前总绝对环形距离，平局选最小phase。锚定分支复用同一整数signed距离，不从浮点特征反推tie。给定当前合法公共信息，实际分布为

\[
q(s\mid x)=.9\,\mathbf1\{s=g(x)\}+.1/N,
\qquad
\pi_\theta(s\mid x)=\frac{q(s\mid x)e^{z_\theta(s,x)}}{\sum_aq(a\mid x)e^{z_\theta(a,x)}}.
\]

`phase_log_probabilities`在统一log_softmax之前加q.log；`sampled_phase`用这同一分布的CDF选择一次phase，返回同一log probability和整队target。没有每个实体重抽phase，也没有N倍复制共同似然。这是可见的策略/评分一致性，不是本次运行了梯度或环境测试。[policy，quota_arrays、phase_features、phase_log_probabilities、sampled_phase、greedy_phase][policy]。

实际loss使用全64tick的native Y，而不是后40tick U或F奖励：

\[
Y_e=1-\frac1{64}\sum_{t=0}^{63}u_{e,t},\qquad
S_e=\sum_{t\in\{0,4,\ldots,60\}}\log\pi_\theta(s_{e,t}\mid x_{e,t}),\qquad
L=-\operatorname{mean}_{64}\{\operatorname{stop}(Y_e-\beta_{c(e)})S_e\}.
\]

每块一次backward和Adam（lr=.0003、betas=.9/.999、eps=1e-8、weight_decay=0、foreach=False），然后才更新 `.95*old_baseline+(1-.95)*cell_mean_Y`。非有限loss/gradient在参数步骤前拒绝；没有teacher、critic、imitation、F penalty、temperature sweep或额外导数。训练Y与评价post-event U并非同一量，但这是已声明的设计，不是新发现的目标错误。[policy，adam_update][policy]；[study，_run][study]；[card11][card11]。

保留2,561参数的shared assignment encoder/mean pooling/phase scorer，普通fan-in初始化且最后scalar层为零。初始策略是q，不是deterministic greedy；log-prior每次行动都存在，学习后却没有“.9的greedy保留率”或“.1/N的动作概率下界”保证。正支持不保证有限探索充分，参数共享与公共dispatch也不证明信用分配或有用协调。greedy与学习法则共享协调设施，nearest不需要phase消息；不能称等通信/等算力或无通信分散执行比较。[policy，PhasePolicy、phase_log_probabilities][policy]；[foundations §§3–4][foundations]。

## 三、B12 的实际服务、恢复和证据精度

以下均沿用固定分析/比较文件的已发表数值，仅缩短展示精度；没有本次重算、bootstrap、检验或新统计。两个primary路径为ACTIVE_CONTINUATION 8→12、12→8，权重各1/2；所有差均为比较者U减sampled final U，正号有利于final。[a12，primary_means、comparison][a12]。

| 主路径等权量 | Own initialization | Sampled final1024 | Fixed greedy | Attained nearest |
|---|---:|---:|---:|---:|
| U | .185538736979 | .120507812500 | .106372070313 | .276888020833 |
| 40U | 7.421549479167 | 4.820312500000 | 4.254882812500 | 11.075520833333 |
| Direct full-Y | .805430094401 | .865743001302 | .881408691406 | .720230102539 |
| Failure-coded tau | 20.3203125 | 21.5234375 | 21.6953125 | 39.4531250 |

| 比较 | 已发表均值 | 条件场景SE | 近似条件normal95% |
|---|---:|---:|---|
| G_U | +.065030924479 | .006706874634 | [.051885450196,.078176398762] |
| D_n | +.156380208333 | .008084232377 | [.140535112873,.172225303793] |
| D_g | −.014135742187 | .003001076558 | [−.020017852241,−.008253632134] |

正G_U是相对于这个新初始化的学习，不因greedy更好而消失。起点本身已经优于nearest；E0给出的初始优势为.091349283854，新增自身学习为.065030924479。这个算术区分不能被升级成“anchor的因果效应分解”。D_n是整个已训练package对nearest的服务差，不是纯新增训练或纯通信效果。[e0，Frozen observables][e0]；[a12，primary_means][a12]。

两项参照的+.025U是各自局部兴趣尺度，不作用于G_U。D_n超过它，D_g仍为负。B12的D_g条件区间即使落在±.025之内，也没有把原正收益尺度变成事前等价/非劣边界；更不建立训练总体等价。102个U平局也不证明策略、轨迹或恢复相同。[card11，Observable][card11]；[a12，comparison][a12]；[spec §11.7、§11.8.5][spec]。

| Primary路径 | G_U（有利/不利/平局） | D_n（有利/不利/平局） | D_g（有利/不利/平局） |
|---|---|---|---|
| Active8→12 | +.076497395833（36/2/26） | +.201627604167（63/1/0） | −.013476562500（0/10/54） |
| Active12→8 | +.053564453125（40/7/17） | +.111132812500（56/8/0） | −.014794921875（1/15/48） |

对greedy合计1/25/102，不是所有场景都不利；对初始化和nearest所有格的均值有利，也不是没有不利episode。主路径不替代完整八格，八格也不是八个独立训练实例。[a12，comparison.paths][a12]。

### 全部八格服务与恢复

下表active为ACTIVE_CONTINUATION，new为NEW_EPOCH。全八格full-Y与U保持相同的角色优劣方向：final胜初始化/nearest而输greedy；完整各格Y、F、40U原数均保留在固定分析和RECORDED_COMPARISON中，Y是direct terminal endpoint而非由U重建。[a12，all_eight_cell_means][a12]；[recorded，all_eight_cells][recorded]。

| 格 | U_init | U_final | U_greedy | U_nearest |
|---|---:|---:|---:|---:|
| 8→8 active | .237500000000 | .186279296875 | .171875000000 | .330859375000 |
| 8→8 new | .243994140625 | .198779296875 | .181933593750 | .326513671875 |
| 12→12 active | .107617187500 | .019140625000 | .000000000000 | .235677083333 |
| 12→12 new | .109765625000 | .053515625000 | .025781250000 | .265625000000 |
| 8→12 active | .119661458333 | .043164062500 | .029687500000 | .244791666667 |
| 8→12 new | .138964843750 | .057942708333 | .036002604167 | .232649739583 |
| 12→8 active | .251416015625 | .197851562500 | .183056640625 | .308984375000 |
| 12→8 new | .266601562500 | .211083984375 | .189306640625 | .323925781250 |

以下每格为“tau均值；tau40失败码数/64”。三个quota角色的F始终为零，nearest F为正；零F是申领数量身份，不是学习获得的安全或物理覆盖保证。[a12，all_eight_cell_means][a12]。

| 格 | Initialization | Final1024 | Greedy | Nearest |
|---|---|---|---|---|
| 8→8 active | 36.875；56/64 | 39.03125；59/64 | 40；64/64 | 39；61/64 |
| 8→8 new | 20.640625；29/64 | 21.140625；32/64 | 20.390625；31/64 | 39.875；63/64 |
| 12→12 active | .515625；0/64 | .09375；0/64 | 0；0/64 | 40；64/64 |
| 12→12 new | 1.890625；0/64 | 1.171875；0/64 | 1.03125；0/64 | 40；64/64 |
| 8→12 active | 6.65625；0/64 | 5.265625；0/64 | 5.265625；0/64 | 39.40625；63/64 |
| 8→12 new | 5.578125；0/64 | 5.15625；0/64 | 4.703125；0/64 | 38.796875；62/64 |
| 12→8 active | 33.984375；49/64 | 37.78125；59/64 | 38.125；61/64 | 39.5；63/64 |
| 12→8 new | 22.796875；31/64 | 18.953125；27/64 | 18.5；27/64 | 38.53125；61/64 |

final的tau对初始化5改善/3损害，对greedy2改善/5损害/1平，对nearest7改善/1损害。active12→8对初始化恶化3.796875，却比greedy好.34375、比nearest好1.71875；这就是反对“一概无价值”的具体事实。active8→8对nearest的+.03125小均值损害，与59/64对61/64的较少失败码同时存在。均值、失败次数、U和Y不等价，不能把一种后果替代另一种。[recorded，recovery_tau_cell_signs、all_eight_cells][recorded]；[e0，Recovery][e0]。

tau40是未满足既定恢复窗口的失败编码，不是40tick内必然恢复，更不是运行时崩溃的代填值。主路径final的0/64与59/64必须分别保留，不能用小的primary greedy-tau均值收益掩盖后一条路径。`study.reading`只接收三个U差，所以其单一`no_increment_over_greedy`标签本来就不能概括这些恢复事实；当前人工intake补充混合后果是必要且正确的。[study，reading][study]；[a12][a12]。

## 四、B11缺失、D1及未解释运行风险的准确含义

B11的第一个supervisor以125在准入/科学构造前失败，记录把它定位为外层argument边界丢失并作了pre-start修正。之后唯一被准入的科学调用才是seed31、40.83秒、SIG11/139的尝试。前者不是第四个科学fit，但其失败和支持费用不能删除。[failure，Exact execution][failure]。

该科学尝试有164个完整更新、10,496个已记录训练episode、671,744训练ticks和512个完整初始化评价episode；至少704,512个完整ticks，崩溃中的额外工作未知。没有final1024 checkpoint、final/greedy/nearest面板或summary。因此不能从160的旧console进度或164条curve推算终值，不能令D_g=0、令tau=40来补缺，也不能把该root删除后称“两次独立试验均成功”。[failure，PARTIAL_EVIDENCE段][failure]。

static review没有找到具体可达的OOB/UAF，并不排除所有native/绑定/生命周期错误。缺少部分C导出异常隔离、autograd内存压力只是候选；SIG11、可用内存和有界graph生命周期并未证明bad_alloc、terminate或泄漏。无可用致错栈，不能由地址片段或猜测下达语义修复。[failure，Static review intake][failure]。

D1实际付出了192个synthetic更新、12,288episodes/786,432ticks、39.69秒；“非科学fit”不等于零计算。它使用新synthetic root且没有B11的初始化评价前缀，未复现不能排除allocator历史或数据相关原因。B12包含完整前缀并最终成功，比D1多说明该完整科学路径在另一个root/调试器环境下能完成一次；它仍不是seed31复现、因果定位或修复。gdb/faulthandler是故障观察手段，不是防止内存错误的安全层。[failure，D1 selection、collection][failure]；[card12，Execution][card12]。

**B12不是仅凭exit0而接受。** E0报告了source/object/action-law、全1024记录、实际backward/Adam、四个唯一键面板、有限FP64参数与optimizer状态、所有endpoint/paired reductions以及原始归档的核对；这给出比“JSON可读”更强的直接记录依据。与此同时，同一输出的重算与summary一致不是独立native reward oracle，有限/范围正确也不能排除所有silent corruption。[e0，Source、analysis checks][e0]。

相称结论是：现有列出证据没有建立B12输出已损坏，故保留它的有限比较；共享SIG11风险未消失，故不认证全运行路径无错。若以后取得具体故障证据，按它实际影响的reward、state、training或measurement依赖限制旧/新主张，保留独立可信事实。当前不要求完整历史重放、全域内存证明或无目的synthetic重复；未来modal虽去掉反向传播，仍共享native reset/event/step等路径，不能先称它已绕开未定位故障。[spec §11.8.7][spec]；[study，rollout][study]。

### 两个完成者究竟说明什么

B10与B12分别为seed30/32、同1024终点、独立生成训练及评价实例。G_U为+.061531575521/+.065030924479，D_n为+.154589843750/+.156380208333，D_g为−.019075520833/−.014135742187。固定RECORDED_COMPARISON给出的完成者描述均值为+.06328125、+.155485026042、−.016605631510；只能如此命名，不能附一个忽略B11的总体CI或成功概率。[a10，comparison][a10]；[recorded，primary_across_completed_instances][recorded]。

未知崩溃可能与数据、轨迹或资源历史有关，不能假设终值缺失与策略表现无关；也不能声称已证明存在某种特定选择偏差。两个评价root不同，所以跨实例差同时包含训练和条件评价变动，不是纯训练方差。所有格、面板、curve点都不增加独立训练样本。normal95区间只是一个fit内基于已声明语义耦合的近似；点质量/平局多，不构成精确覆盖率或联合两参照置信保证。[card11，coupling、ceiling][card11]；[a12，comparison][a12]；[empirical，随机性有层级][empirical]。

B09的seed29/final256保留G_U+.05126953125、D_n+.1460205078125、D_g−.0317708333333及其恢复损害；它不是B10/B12的同终点重复或配对预算control。不同显示差距不能被归为多训练、锚定或Adam的因果效应。此前B10审查指出另一条1024观察确有辨别力；B11尝试和B12完成了这类实际工作，并不意味着该建议如今要求无限追加独立fit。[b09，Strongest support、ceiling][b09]；[review10，第五节][review10]。

## 五、具体后继：modal比较的价值及可用的耦合

### 它回答一个真实但更窄的问题

所提新执行法则是

\[
m_\theta(x)=\operatorname*{argmax}_{s}\{\log q(s\mid x)+z_\theta(s,x)\},\qquad
\mu_\theta(s\mid x)=\mathbf1\{s=m_\theta(x)\}.
\]

这是在每个当前状态选最高概率动作，不是最大化未来return，也不是寻找整条最可能轨迹。它改变执行法则和随后状态分布，不能回头将B10/B12 frozen sampled端点改称“实际上应当用argmax”。训练还是原先的stochastic full-Y训练，推断包是新提出、结果知情、尚未运行的对象。[intake，B的定义][intake]；[policy，phase_log_probabilities][policy]。

零scorer时q(g)=.9+.1/N严格大于其他q=.1/N，因此初始modal action在每个合法公共状态均等于fixed greedy。若两者采用相同native法则与外生地址，从相同初始物理状态起，它们逐步给出相同行动，成员事件的自身占位也随之相同。**所以fixed greedy可同时担当这个modal问题的未训练mode参照；不需额外跑一个重复的零scorer modal面板来证明该有限定义关系。** 这是一段源码/策略定义推论，不是新测量或要求遍历全状态的证明工程。[policy，初始化、q与greedy_phase][policy]；[study，rollout][study]。

但原始**sampled q初始化**不等于该modal初始化，不能拿旧G_U直接解释新mode的学习增量。trained mode是否会超过greedy尚未知：它可能只是减少非贪心抽样，也可能在某些状态作不同的有用选择，或者比greedy更差。保留两个完成checkpoint、对各自原面板直接观察这一区别，能改变“仅用固定规则还是继续开发trained modal控制器”的选择，因而并非必须先找到新客户才能问。[intake，successor reasoning][intake]；[foundations §§4、6][foundations]。

### 原随机地址复用在源码层面有依据，但要用对

`_run`的key是原对象ID/seed字符串的SHA256。`evaluate`对每个held-out cell固定 `EpisodeCoordinate(0, cell, 0, i)`、i=0…63，按0…31和32…63构成native32 batches。`rollout`将同一key、run_block0和这些坐标传给fixture/event生成；policy uniforms则由另一组带`joint-quota-phase`标签的语义地址取得。固定greedy分支不消费policy uniforms。这是地址化而非可见的顺序消费设计：不用sampled phase uniforms本身不需要移动外生随机流。[study，_run、evaluate、rollout、phase_uniforms][study]。

对应两个base，应分别使用B10的原对象域/seed30与B12的原对象域/seed32。新实验可以有新的文档/输出身份，但不能把新身份同时作为外生key后继续声称复用了旧greedy世界；也不能交叉用B10参照评B12模型。每行按各自base、cell、scenario与原保存的greedy行配对，不能只读一个总均值。[study，相应函数][study]；[a10，identity/evaluation][a10]；[a12，identity/evaluation][a12]。

newcomer/event生成发生在各角色自己的batch状态上。modal必须从原初始世界出发，沿自己的target/movement历史重新取得公共快照及事件结果，不能在sampled轨迹快照上离线挑phase，再继承原reward或强迫使用旧占位。相同外生随机地址允许各自不同的物理后果；配对不要求两个控制器具有相同的事件后位置。[study，rollout的materialize_events_compact/apply_event][study]；[card11，within-instance coupling][card11]。

在这些条件及原native/fixture/tie/reward法则保持下，旧greedy逐行输出是已经测过的合法比较者，**不因时间上先于modal就必须全部重跑**。不过本次清单没有原始512行文件、checkpoint二进制或完整native依赖；我能确认可行的key/坐标/调用路径，不能代替未来实际文件与环境绑定。若新对象更改世界生成、原生语义、参照规则或发生相关修复，便不能再承诺原配对；届时在卡中计入必要的新参照面板，并明确它回答哪个总体。这个依赖检查不等于增加全历史replay或跨平台bit一致门槛。[study][study]；[spec §§11.8.5–11.8.7][spec]。

### 需要改动的最小合同，不是现在已经实现的功能

`PhasePolicy()`默认未锚定；`greedy_anchored`是普通Python布尔属性，不在`state_dict`参数中。checkpoint同时保存了模型参数和`action_law`等元数据。因此未来加载必须恢复该属性为True并核对B10/B12、FP64及组合law；不能仅以“权重都载入成功”断言策略正确，也不能再次initialize覆盖训练权重。[policy，PhasePolicy.__init__][policy]；[study，checkpoint保存][study]。

当前`rollout`的非greedy/nearest分支总是sampled_phase。`torch.no_grad()`只是禁用梯度记录，`model.eval()`也不会把这套显式CDF抽样替换成argmax。modal需明确使用**实际组合log概率或等价组合logits**的argmax，取对应整队targets；不是argmax裸z，也不是直接调用greedy_phase而把网络丢掉。训练后logits可能并列，后续卡应固定结果无关的tie（例如沿用phase索引最小者），不能看回报再选。[study，rollout、evaluate][study]；[policy，phase_log_probabilities、sampled_phase][policy]。

这不是在报告已发生的modal bug：modal还未实现。相称的未来验证只针对加载身份/属性、确定性分支、原地址耦合和所需原生输出；不需要构造额外训练实例、诊断菜单或新框架。冻结权重的mode可以经过不同实体状态，但不产生新的parameter learning。[spec §11.8.6][spec]；[empirical，比较对象、随机层级][empirical]。

## 六、后继结果怎样读，以及明确的规范适用问题

科学上最小充分产品是每个保留base的原生modal-versus-greedy条件面板，保留两条primary路径及全部八格U/F/tau/tau40/40U/direct-Y。可以用 \(D^{mode}_{g,b}=\frac12\sum_{p}(\bar U_{g,b,p}-\bar U_{mode,b,p})\)说明所测差，b分别指B10、B12；这只是提案estimand的明示，不是本轮新结果或新分配。[intake，Potential minimum work][intake]。

有意义的正modal差会提供这两个保留实例上新执行package的开发理由；只有一个base有利或不同路径/量冲突，必须按base保留，不能挑赢家汇总。U相等而tau改善时仍有局部恢复事实；U改善而tau损害时不能默认“acceptable recovery”。没有真实用途取舍或预先说明的局部尺度，就报告向量并由DM说明决策理由，不事后加兑换率。即使旧sampled .025仍作比较背景，也不能据它自动给新的modal包授予原“both references”成功标签；本提案主要比较者是greedy，并未新增nearest评价。[intake，reading intentions][intake]；[recorded，实际量间冲突][recorded]。

modal与greedy的逐行U相等最多是这些面板的相等，不证明所有状态/seed/策略等价；U劣势也不排除局部恢复价值。若进一步观察到每一步行动均相同，那才是更窄、另外可报告的行为事实，不能由endpoint平局反推。mode比原sampled好的差可以描述为该checkpoint、该面板下执行法则改变的总后果；仍不识别纯随机性、信用、优化器或训练总体因果机制。[policy][policy]；[empirical，完整方法比较与机制归因][empirical]。

这些面板曾用于选择后继问题，所以它们虽然原来是training-held-out，现在不是对新modal提案未见的独立确认集。两套权重又是完成者中的保留对象。全部结果必须标明post-outcome、retained-base、reused-scenario与B11缺失；不因新增rollouts就称新增独立fits。未来若作场景dispersion/近似区间，也不能把忽略设计选择与缺失的区间称训练总体保证。本有限开发问题不因此必须先购买新面板或C类研究。[intake，explicit new post-outcome observation][intake]；[spec §§11.8.2–11.8.5][spec]。

**具体规范问题需要诚实保留。** 所列现行证据规范§11.4仍要求ordinary B中的真实learner及非零更新，§11.8.6仍写真实learner/trainer；§11.4.1的零新fit例外明确只属于ACVC命名对象。拟议modal测量则明确零fitting/backward/Adam。这里不能把“选项B”误当已经宣告“证据类B”，也不能指控尚未选择的卡已违规；但若未来准备以ordinary B名义开展，按这些字面条款有一个真实适用缺口。[spec §§11.4、11.4.1、11.8.6][spec]；[intake，Options、Potential minimum work][intake]。

相称处理是：DM在既有后续对象说明中明确这是一项**固定已训练策略的新推断法则测量，零新增学习**，并说明所采用的适用条款。若必须使用B标签，则需由实际有权处理规范的责任方给出仅覆盖该零更新执行测量的显式有限适用/例外，保留native观测、信息、原生后果、缺失、成本和非总体claim限制；本审查不自行颁发该例外。不存在已列RCLE例外时不预称普通B合规，也不借ACVC条款通用化。反过来，补做一次无意义optimizer步骤、把真实新rollout改叫旧数据reanalysis，或强迫升级C，都不是科学修正。只读源码检查属于设计论证，不替代未来native modal结果。[spec §§8.1、11.8.1、11.9–11.10][spec]。

这一点影响未来标签/条款适用，不影响已有完整训练的B12，不要求重开本轮任务或再发咨询，也不证明modal问题科学上不值得问。当前TASK只要求review并明确未分配新调用，因此本轮可以完整给出设计评价和这个具体限制。[task，Requested decision、Additional caller constraints][task]。

## 七、与 unchanged replication 和 PARK 的真实比较

DM暂偏向modal而非第三个完成fit，有可辩护的理由：已有两条完成的sampled1024实例都显示正学习、nearest收益和greedy劣势；直接观察当前权重的mode，针对“是否值得采用另一执行package”而非继续估计同一sampled law的实例变动。新问题并不是搜一个更好seed、选最佳checkpoint或扫温度；greedy还同时提供zero-scorer mode参照，使局部学习后的modal价值有清楚的零基准。[intake，successor options][intake]；[policy][policy]。

**最强反对意见仍是PARK，而不是要求更高证据类。** 两个完整sampled端点已经不支持当前U/full-Y用途上替代greedy，后继可能仅去掉抽样而复制已有规则。若没有人会因为modal结果改变保留/采用这个控制器的选择，少量rollouts也仍是低价值程序；开发、绑定、收集和共享运行风险可能超过新增信息的价值。不能以“运行便宜”“必须维持ACTIVE”或争取一个阳性为理由不断改推断包。[intake，C alternative][intake]；[spec §§7–8、11.9][spec]。

但现在也不能先称modal无用：B12的参数学习真实，fixed greedy并非已证策略类最优，small sampled deficit不决定其最可能行动的服务。局部有利tau也说明不能用单一“负”概括整个机制。我的意见是保留这个**一次、明确、有限的条件比较问题**的科学价值，按第五、六节把对象说清；是否当前投入仍由DM负责。不得将这句话变成Reviewer替DM选定card、seed、数量上限或生命周期。[a12][a12]；[recorded][recorded]；[agents §2][agents]。

另一条unchanged1024 fit仍有辨别力，但回答的是新的独立训练/评价实例是否重现，而不是这些保留权重的modal表现。它也不能自动消除B11缺失或估计纯训练方差。后继转向modal是在选择不同问题，不是原独立-instance建议从来没有价值；原建议已经经B11尝试和B12完成落实。PARK、modal、再做sampled实例都是可以有理由的选择，当前证据不唯一强迫其中之一。[card12，选择理由][card12]；[review10，第五节][review10]；[intake][intake]。

任何未来结果，无论阳性、相等、混合、负面或再次缺失，都保留原B10/B11/B12与D1；不得用“modal未成功”自动生成下一种decoder/seed。没有承诺将研究进行到positive，也没有把反选项变成定时咨询或先行诊断任务。[spec §11.8.2–11.8.3][spec]。

## 八、完整工作、成本和硬边界

B12实际记录为1fit、65,536训练episode、1024 backward/Adam和2,048评价episode，总4,325,376 native ticks、2,112个native32 batches。训练1,048,576 team phase draws、8,388,608 phase heads、71,303,168 assignment rows；sampled初始化/final再加1,703,936 rows。每clock的N-phase×N-entity评分和greedy整数归约是算法工作，不是本次审查额外验证，更不是6^N联合动作或未来trajectory search。[card11，Work计数][card11]；[card12，Exact mapping][card12]；[task，exposure][task]。

所有2,561参数改变，初始范数5.812717459442、位移8.837685548196、1024步均非零；训练first/last32平均Y为.814785003663/.880042012533。它们支持真实训练的记录，但只有native评价差才说明这里的服务学习；位移不等于能力、曲线改善不证明收敛或还需几步。[a12，checkpoint、observed_curve][a12]。

潜在modal最小新增为两个保留base各512episode，合计1,024episode/65,536ticks/32 native32 batches、零fit/backward/Adam；它仍需在每次当前行动上计算所有N个phase score及N×N assignment。无训练反向图并不意味着零模型加载、零native工作或零运行风险。两组原参照只有在实际可复用时才不增加新评价；否则后续计入相应greedy面板。相比之下，另一个unchanged fit的67,584episode/4,325,376ticks包含完整训练。这说明新增**曝光**明显不同，不是已测wall比例或收益/秒。[task，potential modal work][task]；[intake，Potential minimum work][intake]；[study、policy][study] [policy]。

B12的192.81秒和peak RSS1,235,208KiB属于完整admission/debugger/build/initialization/training/evaluation/publication链，不是纯trainer时间，也不与B10的无相同instrumentation时间/RSS构成受控性能比较。记录有normal inferior exit、完整端点和原始核对；gdb后置查询的`No current process`不被单独误读为训练失败，也不靠gdb自身exit code认证科学完成。实际准入仍须本节点/本调用满足要求，旧RSS不是新准入。[e0，Source、execution][e0]；[card12，Execution][card12]。

已给出的四条完整/部分链之和为434.68秒：B10 161.35、B11 40.83、D1 39.69、B12 192.81。它是异构instrumentation调用的已知顺序wall和，不是elapsed critical path、aggregate CPU、总支持或全部agent寿命成本。B10历史support下界627.289636秒及相对旧计划的偏差保留；额外tool/network/reviewer/Transport/provider/agent/monitor/integration尾项UNKNOWN，不归零也不从其他表重复相加。[recorded，cost][recorded]；[e0，Deviations、costs][e0]。

当前明确采用的§11.8.1和runtime§1区分普通DM时间计划、operational watchdog、真实owner/platform限制与冻结科学曝光。B12的一次started调用、1024更新和四面板是真实对象边界；1800秒watchdog是防止stranded process的工程控制。旧300/600/900计划或合理估计不自动成为新stop/Send/审批门槛，普通支持计划可由DM在其权限内前瞻说明调整；这不允许擦除历史偏差、声称原计划合规、重置累计费用或把第二次科学调用假扮原调用延续。[spec §11.8.1][spec]；[runtime §1][runtime]；[agents §2][agents]。

未来modal的额外native、加载/build和完整support未测，甚至可能由support主导；不把192.81秒按tick比例外推为保证，也不默认另买pilot/profiler。已有计数与明示unknown足以讨论研究价值。当前没有新运行分配，本审查新增模型、fit、科学RNG、episode/tick、backward/Adam、评价、重分析、tests和profiling均为零。[intake，实际选定工作][intake]；[task，review boundary][task]。

## 九、实际访问、知识作用及最终意见

本轮通过GitHub访问了固定TASK及全部18个清单路径。新B12/B11记录、两份执行源码和当前规范直接读取；对本会话已经全文读取的B10 review、B10 all-cell分析、B09 intake，在指定版本返回同一blob后复用对应内容。没有沿import、hash清单或历史引用取得清单外文件，也没有把delivery HEAD当科学输入。

| 有效版本 | 实际采用范围 |
|---|---|
| `d3db2215fc12cf6e42a2e1af529bb60a29970357` | [B12 card][card12]全文；[B11 card][card11]被采用的科学对象/观察/计数与执行边界；[B12 E0][e0]全文；[B12 intake][intake]全文；[B11 failure intake][failure]全文。 |
| 同上 | [B12 INTAKE_ANALYSIS][a12]source/counts、checkpoint/curve、所有primary/path、全部八格U/F/tau/Y/40U/tau40；[RECORDED_COMPARISON][recorded]全文；[B10 INTAKE_ANALYSIS][a10]本轮主量窗口及相同blob的已读全格内容；[DIRECTION][direction]Current DM position和Current scientific question。 |
| `0366a47e6a5b58a75dabdbb2772a33a0cdcb0eeb` | [B10完整review][review10]核对blob后复用本会话全文，特别是正学习/起点区分、独立1024观察的价值及非生命周期命令。 |
| `d741be527662c5cec18ed03ae03531658059dff6` | [B09 intake][b09]观测、原生损害、256终点及claim限制；旧权限/cap文字不作为新约束。 |
| `15eaa7ea655a0f42a0ec3986927487892bdce212` | [study.py][study]、[policy.py][policy]全文只读；没有执行、读取其未列imports或加载checkpoint。 |
| `be8ad6604041bd3e68767b7f51bdf412078b8260` | [证据规范][spec]§§7–8、11.4、11.7–11.10；[AGENTS][agents]角色定义与§2；[runtime规范][runtime]§1。相邻窗口文本不扩大任务。 |
| 同上 | [FOUNDATIONS][foundations]§§3–4、6；[04_EMPIRICAL][empirical]比较层级、随机单位、package/归因、return/cost和claim强度。 |

这些知识在本题的实际作用是：共同合法信息不证明协调价值；训练参数改变与冻结权重的执行法则改变不是同一行为；完成者场景精度不能代替独立训练/缺失机制；有用开发观察不需要先获得exact maximum或完整病因。它们解释审查边界，不替DM选择生命周期，也不自行创造零更新对象的规范例外。[foundations][foundations]；[empirical][empirical]；[spec §11.10][spec]。

明确未独立读取/执行的是原始panel和checkpoint二进制、native kernel/绑定实现、runner/gdb完整日志、分析脚本及全量support ledger。本review采用它们在清单中已经记录的核对事实，而不假称重新核对原始数据或证明共享运行安全。没有决策必要的清单源访问失败；未取得原始字节是上述复用/运行认证的边界，不是一个凭空新增的科研启动障碍。

**最终意见：保留B12的正初始化学习、nearest收益、greedy U/full-Y劣势及相反方向的恢复事实；将B10/B12限为三次尝试中的两个已完成端点，B11缺失和D1有限非复现不被抹除。** 对后继，modal-versus-greedy确有有限、不同于重复fit的辨别力，源码支持有条件的原地址/参照复用；实际modal分支、模型属性恢复、按base耦合及零更新条款适用需要明确。PARK依然是有根据的价值判断备选，任何modal正值也不能修复旧sampled结果、证明纯随机性机制或抵销恢复损害。当前完成的是实质独立科学审查；DM回应这些发现并拥有最终研究/生命周期选择，本文件不分配调用、资金或跨方向动作。

[task]: https://github.com/CartmanFatass/My-paper-code/blob/0d8a29cb832da3e998c97133ee0dd325801ad08b/docs/research/candidates/roster_consistent_latent_exploration/pro_packets/20260914_b12_scientific_review/delivery/TASK.md
[card12]: https://github.com/CartmanFatass/My-paper-code/blob/d3db2215fc12cf6e42a2e1af529bb60a29970357/docs/research/candidates/roster_consistent_latent_exploration/RCLE_B12_FINAL1024_SCIENCE_CARD_20260914.md
[card11]: https://github.com/CartmanFatass/My-paper-code/blob/d3db2215fc12cf6e42a2e1af529bb60a29970357/docs/research/candidates/roster_consistent_latent_exploration/RCLE_B11_FINAL1024_REPLICATION_SCIENCE_CARD_20260914.md
[e0]: https://github.com/CartmanFatass/My-paper-code/blob/d3db2215fc12cf6e42a2e1af529bb60a29970357/docs/research/candidates/roster_consistent_latent_exploration/RCLE_B12_FINAL1024_RESULT_EVIDENCE_20260914.md
[intake]: https://github.com/CartmanFatass/My-paper-code/blob/d3db2215fc12cf6e42a2e1af529bb60a29970357/docs/research/candidates/roster_consistent_latent_exploration/RCLE_B12_FINAL1024_INTAKE_20260914.md
[a12]: https://github.com/CartmanFatass/My-paper-code/blob/d3db2215fc12cf6e42a2e1af529bb60a29970357/docs/research/candidates/roster_consistent_latent_exploration/b12_final1024_s32_20260914/INTAKE_ANALYSIS.json
[recorded]: https://github.com/CartmanFatass/My-paper-code/blob/d3db2215fc12cf6e42a2e1af529bb60a29970357/docs/research/candidates/roster_consistent_latent_exploration/b12_final1024_s32_20260914/RECORDED_COMPARISON.json
[failure]: https://github.com/CartmanFatass/My-paper-code/blob/d3db2215fc12cf6e42a2e1af529bb60a29970357/docs/research/candidates/roster_consistent_latent_exploration/RCLE_B11_PARTIAL_FAILURE_INTAKE_20260914.md
[a10]: https://github.com/CartmanFatass/My-paper-code/blob/d3db2215fc12cf6e42a2e1af529bb60a29970357/docs/research/candidates/roster_consistent_latent_exploration/b10_greedy_anchored_1024_20260913/INTAKE_ANALYSIS.json
[review10]: https://github.com/CartmanFatass/My-paper-code/blob/0366a47e6a5b58a75dabdbb2772a33a0cdcb0eeb/docs/research/candidates/roster_consistent_latent_exploration/pro_packets/20260913_b10_scientific_review/archive/RESPONSE.md
[b09]: https://github.com/CartmanFatass/My-paper-code/blob/d741be527662c5cec18ed03ae03531658059dff6/docs/research/candidates/roster_consistent_latent_exploration/RCLE_B09_GREEDY_ANCHORED_PHASE_INTAKE_20260913.md
[direction]: https://github.com/CartmanFatass/My-paper-code/blob/d3db2215fc12cf6e42a2e1af529bb60a29970357/docs/research/candidates/roster_consistent_latent_exploration/DIRECTION.md
[study]: https://github.com/CartmanFatass/My-paper-code/blob/15eaa7ea655a0f42a0ec3986927487892bdce212/experiments/candidates/roster_consistent_latent_exploration/joint_quota_phase/study.py
[policy]: https://github.com/CartmanFatass/My-paper-code/blob/15eaa7ea655a0f42a0ec3986927487892bdce212/experiments/candidates/roster_consistent_latent_exploration/joint_quota_phase/policy.py
[spec]: https://github.com/CartmanFatass/My-paper-code/blob/be8ad6604041bd3e68767b7f51bdf412078b8260/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[foundations]: https://github.com/CartmanFatass/My-paper-code/blob/be8ad6604041bd3e68767b7f51bdf412078b8260/docs/rl-marl-foundations-20260907/FOUNDATIONS.md
[empirical]: https://github.com/CartmanFatass/My-paper-code/blob/be8ad6604041bd3e68767b7f51bdf412078b8260/docs/rl-marl-foundations-20260907/topic-notes/04_EMPIRICAL.md
[agents]: https://github.com/CartmanFatass/My-paper-code/blob/be8ad6604041bd3e68767b7f51bdf412078b8260/AGENTS.md
[runtime]: https://github.com/CartmanFatass/My-paper-code/blob/be8ad6604041bd3e68767b7f51bdf412078b8260/docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md
