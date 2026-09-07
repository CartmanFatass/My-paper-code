**选择打开一个不同的、有限的真实学习问题：开展 CBSC-OPPORTUNITY-CREDIT-B04，用新 seed 21217 的一组 RAW/STRUCT 配对训练，统一采用“本次所选动作的决策加结算实得回报”及对应的 decision-only value 监督。保持每臂 48 次 rollout、768 次 Adam 更新，只在更新 0 和 48 评价；主量仍是更新 48 的配对原生回报差，同时报告两臂相对 REQUEST_ONLY 的表现。** 选择包括一次针对新目标与主输出的有界工程检查，不包括追加 seed、192 更新、旧 GAE 对照或政策搜索。

理由是现在已有一个可由源码说明、直接针对学习目标的变化：当前动作既不改变后续宿主状态，也不进入后续循环输入，而旧价值目标仍覆盖后续机会。缩短信用目标并使 critic 学习同一个局部量，比仅等待原训练包运行更久更有针对性；公开请求参照又能揭示最容易被误认成当前性收益的改善。这足以支持一次探索投资，**不证明旧 GAE 错误、方差一定降低或新方法一定改善。** 原不变 48 更新家族的暂停和两次局部零差异全部保留；本次是同一当前性表示假说下的不同学习包，不是撤销旧决定，也不是机制 recast。Portfolio 生命周期、优先级、容量及其他方向不变。[设计 intake「Concrete preferred B04 design」「Decisions this intake produces」][1]、[原完整决定 §§二–四][5]。

## 一、哪些事实支持这次选择，哪些反证仍然有效

### 旧零差异是真实学习结果，不是未运行或充分能力的证明

B02/21203 的两臂终点均为 10.7125，B03/21209 均为 10.5875；每个运行的 32 个终点差值全部为零。更新 12、24、48 的每次受训 greedy 评价，两臂都选择全 REFRESH。每个正式臂实际完成 48 次 rollout 和 768 次 Adam 更新，初始相对参数位移在 18.6828676061%–20.3270553056% 之间。B03 训练采样并非只有 REFRESH：RAW/STRUCT 分别采过 243/237 次 SERVE 和 458/410 次 SAFE，但最后一批已分别集中为 191/192 次 REFRESH。[B02 结果「Direct measurements」「Actual learner and evaluation exposure」][6]、[B03 结果「Actual learning and actions」][7]、[曝光文件 `observed_formal_arms`][2]。

因此，原暂停仍有充分的投资理由：继续不变协议没有新的定向干预。但这些事实不证明探索充分、梯度消失、固定刷新最优、所有 seed 等价或当前性无用。两个 seed 也同时改变初始化、训练随机性及程序生成的评价世界，不能拆成 64 个独立训练样本，更不能只解释为初始化变化。[B03 结果「Primary observation and run-level context」][7]、[家族 intake「Bounded evidence, support and contradiction」][4]。

### 新理由来自实际动作依赖，而非把 GAE 认定为缺陷

源码给出了三个彼此一致的事实。`host.py::build_stochastic` 先生成公共事件、状态、decision 和 settlement 的完整 tape，接口没有策略动作参数；`ledger.py::apply_native_action` 返回原 state，REFRESH 不持久修复后续 cache；`engine.py::_rollout_from_panel` 先从公共观察产生整段循环网络输出，再抽样动作，并仅把该动作的 decision/settlement ledger 填进 rewards。动作和奖励不回填为后续循环输入。[host 第 1–6 行、`_decision_token`、`build_stochastic`][8]、[ledger `native_ledger`、`apply_native_action`][9]、[engine `build_observations`、`_rollout_from_panel`][10]。

与之对照，`ppo.py::compute_gae` 用 gamma=1、lambda=0.95 在 primitive 时间轴上传播 TD residual；现有 actor 的规范化**已经只覆盖 decision 行**，不存在本次发现的“把全部 token 混进优势规范化”的错误。现有 `_train_minibatch` 的 value loss 则对全部 152 行取均方误差。提案改变的是回报预测范围及与之匹配的监督位置，不是修正一个已证实的全 token 规范化 bug。[PPO `compute_gae`、`_train_minibatch`][11]。

我的推论限于这个计算图：固定策略参数、保留当前公共历史时，当前抽样动作不改变以后机会的公共历史、循环状态输入或动作分布；于是后续机会的奖励不提供由**这个动作**造成的期望 score-function 信用。用本次 decision 加 settlement 的实得总回报构造局部信用，是对同一不折扣 episode-return 目标有根据的估计器选择。共享参数对其他机会的影响仍由那些机会的训练项承担，完整循环梯度也仍然存在。这个理由不意味着各机会的公共状态独立，更不意味着改动后的有限样本 PPO 与旧更新逐步等价。PPO clipping、批内规范化、baseline 误差及共享 actor/critic 优化仍可能改变偏差、方差和行为；本轮没有测量它们，也不保证删掉未来项一定降低实际梯度方差。[源码依据][8]、[10]、[11]；[设计 intake「Question-driven source retrieval and what it changes」][1]。

**最强次选仍是保持暂停、不买新实验。** 两个真实零差异，加上一个无需 owner/epoch 记忆就能提高旧得分的公开请求规则，可能意味着这个 host 的语义学习收益很有限。局部目标也可能仍学到全刷新，或仅学会活动请求区别。选择 B04 不是因为这个反证被排除，而是因为已有具体、对称、无需加数据量或搜索的目标改动，且能在一次小比较中同时看到表示差异与简单规则缺口。只改 actor、保留原剩余回报 critic 在数学上仍可提供动作无关 baseline，但并没有落实本次要测试的局部价值预测；单独取消 critic 或扩大熵、预算、宿主改动则会另换问题。故本轮保留提案的完整信用目标包，不再增加消融维度。192 更新仍不选，但没有被永久禁止。[设计及备选][1]、[原完整决定 §三][5]、[证据规范 §§5.2、11.8.2、11.9][15]。

## 二、选定的训练定义：不留下隐含的算法选择

这是两臂共同的、明示的新学习包。对于八 episode rollout 中的第 e 个 episode、第 q 个机会，q=0,…,23，令 t_q=12+6q：

\[
G_{e,q}=\operatorname{stopgrad}(r_{e,t_q}+r_{e,t_q+1}),\qquad
A_{e,q}=G_{e,q}-\operatorname{stopgrad}(V_{\rm old}(H_{e,t_q})).
\]

r 来自**本次实际所选动作**的既有 FP32 rollout reward 行。两项相加必须保留 REFRESH 的负决策成本与延迟正结算；不使用未选动作的 reward、全 Q、VALID、oracle action 或 teacher。G 是原生实得奖励监督，不是新的 reward shaping；奖励不成为 policy、adapter 或 critic 的观察输入。目标与 old value 在该 rollout 的全部四 epoch 中保持固定，不在每个 minibatch 用新 value 重新生成优势。[设计「Concrete preferred B04 design」][1]、[engine `_rollout_from_panel`][10]。

按原方法在该 rollout 的全部 8×24=192 个 decision 上一次性规范化：

\[
\mu_A=\frac1{192}\sum_{e,q}A_{e,q},\quad
s_A^2=\frac1{192}\sum_{e,q}(A_{e,q}-\mu_A)^2,\quad
\widetilde A_{e,q}=\frac{A_{e,q}-\mu_A}{\sqrt{s_A^2}+10^{-8}}.
\]

这是分母在平方根**外**加 epsilon、按总体二阶矩计算的原形式；不是每个 episode、每个 minibatch 分别规范化，也不包含 forced-WAIT 行。保留旧 log probability、合法动作和 clipping 0.20 的 PPO actor loss。critic 在每个双 episode minibatch 的 48 个 decision 行上拟合**未规范化的 G**，取这些行的均方误差；不把其他 256 个 primitive 行的零占位也算进均值。总 loss 保持 actor loss + 0.50×该 value loss − 0.01×decision entropy，不增加 value clipping、辅助损失或额外更新。[原数值和优化约定：PPO `PPOConfig`、`compute_gae`、`_train_minibatch`][11]；以上局部目标与监督选择采用[设计][1]。

完整 152-token 循环展开、完整 episode BPTT、每个 episode 的 recurrence reset、四 epoch×四个双 episode minibatch 和 Adam 顺序不变。**删除非 decision 的直接 value loss，不是删除那些公共事件输入，也不是把每个机会伪装为环境终止或在机会边界截断 hidden state。** 早期 OWNER/semantic 事件仍能通过循环网络影响后面 decision 的梯度。最后一个机会的 settlement 同样计入 G。[engine 观察及终止行][10]、[PPO rollout 与更新定义][11]。

新目标没有跨机会 bootstrap；旧 GAE 的 lambda 不参与它。不能通过把旧 gamma 设为零或简单令 lambda=0 冒充这个算法：前者会漏掉需要的延迟结算，后者的旧 TD 形式仍含下一行 value。保留不折扣原生回报语义，并在新配置说明中明确“局部 sampled return、decision-only value”，而不是声称旧 B01 GAE 配置仍定义全部训练含义。[PPO `compute_gae`][11]、[ledger 奖励定义][9]。

这一改动同时改变目标 horizon 和匹配 critic 监督的行集及尺度，我把它们选为一个一致的信用学习组件，**不把它们的效果分别归因**。无需为当前 B 扩成两因素消融。保持原 121,349 参数模型、168 通道公共输入、RAW FIFO 和 STRUCT adapter、CPU FP32、初始化、Adam learning rate 3e-4、betas(0.9,0.999)、epsilon 1e-8、weight decay 0、梯度范数上限 0.5，以及采样和 minibatch 随机地址。RAW 与 STRUCT 两臂均采用上述新目标，不能用“新目标 STRUCT 对旧 GAE RAW”。[设计的保留项][1]、[PPO 数值约定][11]。

## 三、REQUEST_ONLY 的用途，以及不能借它声称什么

选定的 REQUEST_ONLY 仅在 decision 时读取公开 `request_active`：活跃时 REFRESH，非活跃时 SAFE_FALLBACK；其他时刻遵守原 forced-WAIT。它不读 evaluator state、VALID、oracle 或未来信息，也不向 learner 提供标签。其动作先由公共 flag 决定，再交原生 evaluator 计分。源码中的 `_decision_token` 明确公开该 flag，ledger 明确给出相应奖励。[host `_decision_token`][8]、[ledger `native_ledger`][9]。

设一个 24 机会 episode 有 n 个活跃请求。按现有 ledger，

\[
R_{\rm all\ refresh}=0.6n-0.4(24-n)=n-9.6,\qquad
R_{\rm request\ only}=0.6n,\qquad
R_{\rm all\ safe}=0.2n.
\]

包内机器算术由此给出下表。**这是已见结果后的代数推论，不是本节点新执行了旧策略，也不是 tuned headroom 或新的独立训练证据。** 它说明仅修正非活跃请求的刷新，就能产生比原 MEI 大得多的旧面板改善，因而先前“优于初始化和 ALWAYS_SAFE”不能当作已具备充分条件决策能力。[曝光文件 `outcome_informed_public_request_reference`][2]、[旧实测][6]、[7]。

| 旧运行 | 原全 REFRESH 均值 | 推得的 REQUEST_ONLY 均值 | 规则相对旧策略增益 |
| --- | ---: | ---: | ---: |
| 21203 | 10.7125 | 12.1875 | 1.475 |
| 21209 | 10.5875 | 12.1125 | 1.525 |

B04 必须在**新 seed 的实际同一组 tape**上计分，不能把这两个旧推导数值当作新面板基线。RAW 的完整调用一次性对 32 条 tape 计分 ALWAYS_REFRESH、ALWAYS_SAFE、REQUEST_ONLY；STRUCT 复用这些已记录同面板参照。三者是低成本背景，不增加训练臂、独立样本或搜索，也不替代 full-history RAW 这一学习对照。[设计与计数][1]、[2]。

REQUEST_ONLY 相等的回报本身也不证明两策略动作相同：只有动作记录确实支持时，才说学到了同一个请求规则；否则只能说得分尚未超过该参照。即便超过 REQUEST_ONLY，也不能单凭两臂结果断言收益专来自 owner/epoch 当前性；公开 content、capability 的条件选择和 generic conditioning 都仍可能解释收益。当前两臂设计不购买 PI/DERANGED 或语义干预，所以不作这些排除。反之，REQUEST_ONLY 不含当前性历史却能改善旧分数，并不是当前性历史无用的证明。[设计的机制与 claim limits][1]、[原完整决定 §§二、五][5]。

## 四、固定比较、主测量及结果的有限含义

使用新配对训练 seed **21217**，两臂从新模型与新 Adam 状态开始，沿既有 B1_RUN 随机 namespace 使用同一初始化、训练世界、动作 uniforms 和 minibatch 地址；新对象有独立外层身份及输出。每臂 TRAIN episode ID 0–383，各出现一次，48 个八 episode rollout。两臂共享完整公共历史，但其训练动作可以不同；配对的是随机来源，不是强制相同动作。[设计][1]、[实际 direct runner `run_arm`][12]、[engine `_training_action_uniforms`][10]。

评价固定为更新 **0、48**，各用同一组 32 个 EVAL_STOCHASTIC episode ID 0–31，和训练 split 分开；greedy、无适应、逐 episode 重置循环状态。主要量唯一为：

\[
d_e=R_{S,48,e}-R_{R,48,e},\qquad
\widehat\Delta=\frac1{32}\sum_{e=0}^{31}d_e.
\]

另预先保留两臂相对请求参照的逐 episode 差及均值，\(u_{a,e}=R_{a,48,e}-R_{{\rm request\ only},e}\)。它们用于解释同一个主差异，且 \(\bar u_S-\bar u_R=\widehat\Delta\)，不是额外的独立实验。保存两 checkpoint 的各臂绝对回报、每 episode 的 24 个动作、决策与结算贡献，以及全部终点配对差，不选最好 checkpoint、episode、metric 或 seed。省去 12、24 评价意味着不再声称最早学会时间或完整早期曲线，不改变固定终点问题。[设计][1]、[direct runner `native_record`、`pair_results`][12]。

MEI 保留 **0.25 原生回报/episode**，约为理论 24 单位最大回报的 1.04%；用途是下一笔投资的实际尺度，不是显著性、等价区间或实测 headroom 的比例。正、零、负都按实际符号报告；负差异即使处于 MEI 内也仍为负。[曝光文件 `mei`][2]、[证据规范 §§11.7、11.8][15]。

若 STRUCT 的差异超过 MEI，同时绝对回报及 REQUEST_ONLY 背景表明有值得重复的学习收益，可建议下一次保持比较再用一至两个新独立 seed；并非现在已经选择这些运行。若只是弥补 RAW 没学会公开请求区别的缺口，保留真实表示差异但标明对照受限，不称当前性价值。若两臂都超过 REQUEST_ONLY 而彼此差异小，可报告新包中的共同原生学习表现，不能改称 STRUCT 优势。若仍全刷新、落后参照、近零或反向，则完整保留结果，本项投入结束，没有自动加熵、加预算或继续直到转正。[设计的 interpretation][1]、[证据规范 §§11.8.2–11.8.4][15]。

没有同 seed 的旧 GAE 臂，不能从 B04 与 B02/B03 的跨运行差值估计“替换 GAE 的因果收益”，也不能唯一归因于目标 horizon 或 value loss。新方法一个配对 seed 不能估计训练 seed 总体不确定性；32 个 episode 和两个 checkpoint 不增加独立训练样本。可以报告单次条件于已训策略的完整差值分布，但本轮不要求用重采样制造总体区间。旧两组不与 B04 合并成同一个三 seed 算法比较。[设计 claim ceiling][1]、[证据规范 §§4、11.8.3、11.9][15]。

本轮的定性预期与设计中的弱预测相符：公开请求处理较容易获得改善，STRUCT-minus-RAW 仍可能在 MEI 内；对解锁 owner/epoch 利用没有已测依据。这是前瞻工作假说，不是成功概率。原两次零、选择背景和所有者未作预测的事实保留。[设计「Provisional DM prediction」及其后段][1]。

## 五、交给 CM 的最小完整目标与必要验证

**目标与路径。** 实现一个小型、具名的 B04 research learner/module、薄 runner 和一次聚焦工程检查，直接复用既有公共投影、真实 rollout、循环模型、原生计分和必要状态保存逻辑。`direct_return_b02.py` 当前仅支持 B02/B03，且直接构造旧 `RecurrentPPOTrainer`；`train_rollout` 明确调用 `compute_gae`，所以不能只改对象名、seed 或输出配置就声称已实现 B04。需要真正的新局部目标及 decision-only value 更新路径；不修改旧 B02/B03 的实际行为，不建设通用 trainer factory、registry、worker pool、profiler 或旧十五表系统。[direct runner `expected_seed`、`run_arm`][12]、[PPO `train_rollout`][11]。

**保留语义与身份。** 同一 tape 的选择动作仍经 `Action[name]` 转换，由 `native_record` 核对 decision+settlement 总回报；不把训练 loss、G 的规范化值或 REQUEST_ONLY 分数当 episode-return。保留真实模型/optimizer/counters 和读回；新外层配置与保存状态的配套记录必须明确局部回报 horizon、value 监督位置和 B04 身份。旧 RNG namespace 或复用 tensor 保存格式不等于“仍是旧 B01 learner”。原 `PPOConfig` 的严格旧定义不是新算法语义的完整描述，不能只发布它而隐去目标变化。[12]、[PPO `PPOConfig`][11]。

本轮清单没有 `checkpoint.py` 等全部传递依赖，因而没有独立确认其新路径适配签名或 snapshot 封装已工作；也没有已实现 B04 diff。CM 应在具名的新路径中以小型显式状态记录表达上述含义，保留旧 payload 的原意，不伪造旧配置、绕开校验或污染历史文件。若实际序列化/恢复接口无法在所选范围内诚实容纳它，返回具体接口与缺失字段；这是一项待实现的局部依赖，不是要求先重建整个历史框架。本次选择决定算法与测量，不替代源码接受。[设计「Dominant work, execution and source implications」][1]。

**一次检查。** 选择工程 seed **21211**，两臂各一个真实八 episode rollout、各 16 次 Adam 更新，单条评价 tape 在更新 0、1 各评价一次，合计 32 次 Adam、2,432 训练转移、608 评价转移。包括 import、实际 learner/evaluator、保存读回和宽限的整次工程调用上限 **60 秒**；它只验证改动，不进入科学主估计，也不需要达到某个收益。已有未改路径检查复用，不在正式两臂边界再重复仿真 smoke。[曝光文件 `proposed_added_verification`][2]、[证据规范 §11.8.6][15]。

在这一次检查内，用少量构造 reward/value 数组加真实路径覆盖以下具体风险：局部 G 包括本次 settlement、没有未来机会 bootstrap；value target 使用未规范化 G，value loss 只对 decision 行取均值；实际 chosen-action reward、公共 REQUEST_ONLY 决策、两臂终点配对和写入读回与声明一致；真实计数、loss 和参数变化可读。比如活跃 REFRESH 的目标应按 FP32 语义对应 -0.4+1，而不是 -0.4。保持原 dtype/尺度相称的检查，不新增统一 1e-12 或跨平台逐位一致门槛。[奖励与原训练路径][9]、[10]、[11]；[所选验证边界][1]。

**特别澄清测试的两个依赖边界。** 修改以后机会的 reward、固定 old values 时，较早机会的未规范化 G 和 A 应不变；但整批优势均值与标准差会改变，所以不能要求所有最终规范化优势也不变。那会误伤本次明确保留的批内规范化。同样，检查非 decision 输出不直接进入 value loss，不能要求非 decision 时刻的 hidden/共享参数梯度为零，因为完整 BPTT 刻意保留历史信用。这些是依据上述公式和现有循环训练结构得出的检查要求，不是新仿真实验或因果定位任务。[PPO 原规范化与完整 episode minibatch][11]。

**接受与范围。** CM 直接完成这项小改动，按当前规则保留与信用目标科学风险相称的独立审阅，不规定多层实现者链或再加审核角色。普通累计新增非测试源码不超过 2,000 行、runner 不超过 600 行；30% 编排比例仅作必要性审查信号，旧 B1 repair 例外不续期。现有 focused 账 **132.15/300 秒**，本次 60 秒以内的实际检查继续记入同一账，其他必要短检查同样如实计入；余额不是自动重试配额。覆盖不足就返回具体缺项，不删除奖励/信息/主测量验证来凑预算。[AGENTS「Workflow calibration」「Focused reading and engineering handoffs」][14]、[工程 scope §§3–5][16]、[曝光文件][2]。

## 六、完整工作量、成本和结束边界

主导算法工作是 **2 臂×1 seed×48 rollout×8 episode**，每个 rollout 做 **4 epoch×4 minibatch**，以及 **2 臂×2 checkpoint×32 episode** 的学习策略评价。每条 episode 仍有 152 primitive transitions；局部 credit 不缩短循环展开。三条固定参照在 RAW 已生成的 32 条 tape 上计分一次，共 96 ledger passes、2,304 个动作分数；不生成更多世界，也不构成候选政策搜索。没有联合动作指数枚举、轨迹树或嵌套 controller/solver。[曝光文件 `source_constants`、`proposed`][2]。

| 正式工作 | 每臂 | 配对合计 |
| --- | ---: | ---: |
| 训练 episode | 384 | 768 |
| 训练 transitions | 58,368 | 116,736 |
| 训练 decision | 9,216 | 18,432 |
| Rollout 更新 | 48 | 96 |
| 实际 Adam 更新 | 768 | 1,536 |
| 学习策略评价执行 | 64 | 128 |
| 评价 transitions | 9,728 | 19,456 |
| 训练加评价 transitions | 68,096 | **136,192** |

上表采用包内机器计数，工程检查的 **3,040 transitions/32 Adam** 单列，不混入正式曝光。保留原生环境、learner、评价和主输出是必要工作；旧全历史 replay、全 support、motif/twin、全中间数组和政策搜索不是这个新问题的前置。相比旧未选 192 方案，本次通过改变问题而非提高剂量获得判别，且不额外引入因果消融臂。[2]、[原完整决定 §三][5]、[证据规范 §11.9][15]。

完整成本律按实际链条记录：启动及 admission + host 构造 + 48 个投影/rollout/PPO 区块 + 两个 eval32/checkpoint 阶段 + RAW 参照计分 + 输出读回 + STRUCT 配对发布 + 结束宽限。B02 的完整 RAW/STRUCT 实测为 79.69/90.78 秒，B03 为 59.53/58.67 秒；四臂之和 288.67 秒。包内两倍较大旧同臂的 **159.38/181.56 秒**仅是有余量的规划场景，不是新路径实测或保证上界。新目标、host 负载及序列化成本未知；少两次评价或不用 GAE 不构成已测加速，也不能把 wall 称为 aggregate CPU 或含控制面等待的 study elapsed。[旧结果成本][6]、[7]、[曝光文件 `cost_reference`][2]。

选择 **RAW 后 STRUCT、最多两个正式完整调用，每臂 600 秒**，包含前述全部阶段和终止宽限；配对计算不能移到未计时的第三调用。RAW 的分数不决定是否执行已选 STRUCT：主路径完整则继续完成配对；实际 primary/资源/范围故障则按依赖停止。执行仍使用配置的 `wsl_4070`、`/home/wu/.venvs/hmasd/bin/python`、CPU FP32、一个科研进程和一个计算线程，不换 GPU、解释器或并行拓扑。每次实际工程/正式调用前都有该节点新测的物理及有效可用内存至少 4 GiB；精确源码正常提交、集成后由已有 detached supervisor 执行，并交现有独立 monitor 观察。配置本身不是本轮资源已通过或运行已发生的证据。[设计执行段][1]、[计算配置][17]、[AGENTS §§5、7–8][14]。

本项投入结束于完整配对 intake，或具体新目标/公共信息/原生 reward/真实训练/配对主测量缺陷、必要覆盖或接口范围缺口、完整调用 cap。失败保留已发生的日志和较窄可信事实，不把未完成主差异填成零；缺可选 telemetry 只限制相应资源主张。没有自动重跑工程仿真或正式调用、加 seed、改熵、延长训练、改宿主或扩成搜索。常规静态实现修正依已有权限处理，不因而生成新的 result-bearing 调用额度。[1]、[证据规范 §§4、11.4、11.8.7–11.8.8][15]。

## 七、决定的最终边界、实际读取及仍未知事项

本次打开的是新局部信用学习包中的表示比较，不是原家族第三次不变重复。目标和配套 value 定义发生实质改变，故有新的对象和解释范围；但当前性关系表示可能改善同信息 RAW 的有限学习表现这一机制假说未换，**不增加机制 recast 计数**。恢复调度记录仅恢复准备和推进问题，未预先选择 B04；旧 intake 末尾的调度暂停已由该记录更新，而科学家族暂停没有被它撤销。本决定也不撤销它。[家族 intake][4]、[原完整决定 §四][5]、[恢复调度记录][13]。

仍未知的是：新目标实际训练后的收益与行为、两臂的泛化和训练 seed 变异、局部目标相对于旧 GAE 的因果效果、horizon 与 value 行集各自的贡献、匹配 tuned-generic/upper headroom，以及历史 SIGSEGV/不同 TypeError 的根因。旧 B1/r05 隔离不变。新的完整比较也不证明语义特异性、PI/DERANGED 排除、稳定表示优势、精确等价、一般 MARL 协作、成员变化或 UAV 迁移。没有这些更强证据不阻止本次普通 B，也不授权宣称它们。[1]、[4]、[15]。

所有决策依据中的科研文件均按固定版本 `5c46871cdcde1dbe1332a5bc22a6c13c45de4ba5` 通过连接的 GitHub 读取。17 条列明路径均可访问，实际范围如下；D/ 表示 `docs/research/candidates/capability_bound_semantic_currentness/`，S/ 表示 `experiments/candidates/capability_bound_semantic_currentness/`。源码引用按实际函数，未展开清单外依赖；结果数值和审阅事实来自给定结果/机器算术，未声称本节点重新载入 checkpoint 或复算未列明原始 artifacts。

| 证据路径 | 实际读取范围 |
| --- | --- |
| [D/CBSC_OPPORTUNITY_CREDIT_B04_DESIGN_INTAKE_20260906.md][1] | 全文，末段续读 |
| [D/pro_packets/20260906_opportunity_credit_convergence/EXPOSURE_AND_COST.json][2] | 全文 |
| [D/pro_packets/20260906_opportunity_credit_convergence/ISSUE_SNAPSHOT.json][3] | 全文 |
| [D/CBSC_DIRECT_RETURN_FAMILY_CONVERGENCE_INTAKE_20260905.md][4] | 全文 |
| [D/pro_packets/20260905_two_seed_family_convergence/archive/RESPONSE.md][5] | 全文，分段补齐 |
| [D/CBSC_DIRECT_RETURN_B02_RESULT_EVIDENCE_20260905.md][6] | 全文 |
| [D/CBSC_DIRECT_RETURN_B03_RESULT_EVIDENCE_20260905.md][7] | 全文 |
| [S/omrc_b01/host.py][8] | 1–110、470–600 行；模块说明、decision token、settlement、stochastic 构造 |
| [S/omrc_b01/ledger.py][9] | 全文 |
| [S/omrc_b01/engine.py][10] | 1–310、375–418 行；公共投影、真实 rollout、评价主体 |
| [S/omrc_b01/ppo.py][11] | 1–240、300 行至文件末尾；配置、GAE、更新与 loss |
| [S/direct_return_b02.py][12] | 全文 |
| [docs/research/portfolio/decisions/2026-09-06-resume-codex-after-claude-handoff.md][13] | 全文，当前 CBSC 准备权限 |
| [AGENTS.md][14] | 1–175、285–435 行；当前工作校准、决定层级及执行/完整性边界 |
| [docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md][15] | 1–135、365 行至文件末尾；含 §§4、5.2、11.4、11.7–11.9 |
| [docs/project/ENGINEERING_SCOPE_SPEC.md][16] | 1–112 行；普通 §§3–5 |
| [.codex/hmasd-compute.toml][17] | 全文 |

另外读取了可变的 [Issue 7 正文][18]，并在 2026-09-06 20:23 PDT（2026-09-07 03:23 UTC）附近复查完整评论列表：当时只有[旧两 seed 家族决定的交付评论][19]，与本轮固定快照相符，不是这次机会信用问题的已有交付。没有沿讨论中的其他版本链接替换固定科研证据。设计 intake 的 GAE/ACAC 文献段作为作者的检索报告阅读，没有在本轮独立打开论文、外部索引或清单外本地资料；本次选择的直接依据是列明 host、reward 和 learner 路径，而非把文献报告当作 CBSC 成效证明。[3]、[1]。

本次新增环境转移、optimizer 更新、评价和参数位移测量均为零，也没有新 profiling、policy search 或模型执行。**已形成的是上述单一有界 B04 选择；尚未发生的是 B04 源码接受、资源准入、实际执行及科学结果。**

[1]: https://github.com/CartmanFatass/My-paper-code/blob/5c46871cdcde1dbe1332a5bc22a6c13c45de4ba5/docs/research/candidates/capability_bound_semantic_currentness/CBSC_OPPORTUNITY_CREDIT_B04_DESIGN_INTAKE_20260906.md
[2]: https://github.com/CartmanFatass/My-paper-code/blob/5c46871cdcde1dbe1332a5bc22a6c13c45de4ba5/docs/research/candidates/capability_bound_semantic_currentness/pro_packets/20260906_opportunity_credit_convergence/EXPOSURE_AND_COST.json
[3]: https://github.com/CartmanFatass/My-paper-code/blob/5c46871cdcde1dbe1332a5bc22a6c13c45de4ba5/docs/research/candidates/capability_bound_semantic_currentness/pro_packets/20260906_opportunity_credit_convergence/ISSUE_SNAPSHOT.json
[4]: https://github.com/CartmanFatass/My-paper-code/blob/5c46871cdcde1dbe1332a5bc22a6c13c45de4ba5/docs/research/candidates/capability_bound_semantic_currentness/CBSC_DIRECT_RETURN_FAMILY_CONVERGENCE_INTAKE_20260905.md
[5]: https://github.com/CartmanFatass/My-paper-code/blob/5c46871cdcde1dbe1332a5bc22a6c13c45de4ba5/docs/research/candidates/capability_bound_semantic_currentness/pro_packets/20260905_two_seed_family_convergence/archive/RESPONSE.md
[6]: https://github.com/CartmanFatass/My-paper-code/blob/5c46871cdcde1dbe1332a5bc22a6c13c45de4ba5/docs/research/candidates/capability_bound_semantic_currentness/CBSC_DIRECT_RETURN_B02_RESULT_EVIDENCE_20260905.md
[7]: https://github.com/CartmanFatass/My-paper-code/blob/5c46871cdcde1dbe1332a5bc22a6c13c45de4ba5/docs/research/candidates/capability_bound_semantic_currentness/CBSC_DIRECT_RETURN_B03_RESULT_EVIDENCE_20260905.md
[8]: https://github.com/CartmanFatass/My-paper-code/blob/5c46871cdcde1dbe1332a5bc22a6c13c45de4ba5/experiments/candidates/capability_bound_semantic_currentness/omrc_b01/host.py
[9]: https://github.com/CartmanFatass/My-paper-code/blob/5c46871cdcde1dbe1332a5bc22a6c13c45de4ba5/experiments/candidates/capability_bound_semantic_currentness/omrc_b01/ledger.py
[10]: https://github.com/CartmanFatass/My-paper-code/blob/5c46871cdcde1dbe1332a5bc22a6c13c45de4ba5/experiments/candidates/capability_bound_semantic_currentness/omrc_b01/engine.py
[11]: https://github.com/CartmanFatass/My-paper-code/blob/5c46871cdcde1dbe1332a5bc22a6c13c45de4ba5/experiments/candidates/capability_bound_semantic_currentness/omrc_b01/ppo.py
[12]: https://github.com/CartmanFatass/My-paper-code/blob/5c46871cdcde1dbe1332a5bc22a6c13c45de4ba5/experiments/candidates/capability_bound_semantic_currentness/direct_return_b02.py
[13]: https://github.com/CartmanFatass/My-paper-code/blob/5c46871cdcde1dbe1332a5bc22a6c13c45de4ba5/docs/research/portfolio/decisions/2026-09-06-resume-codex-after-claude-handoff.md
[14]: https://github.com/CartmanFatass/My-paper-code/blob/5c46871cdcde1dbe1332a5bc22a6c13c45de4ba5/AGENTS.md
[15]: https://github.com/CartmanFatass/My-paper-code/blob/5c46871cdcde1dbe1332a5bc22a6c13c45de4ba5/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[16]: https://github.com/CartmanFatass/My-paper-code/blob/5c46871cdcde1dbe1332a5bc22a6c13c45de4ba5/docs/project/ENGINEERING_SCOPE_SPEC.md
[17]: https://github.com/CartmanFatass/My-paper-code/blob/5c46871cdcde1dbe1332a5bc22a6c13c45de4ba5/.codex/hmasd-compute.toml
[18]: https://github.com/CartmanFatass/My-paper-code/issues/7
[19]: https://github.com/CartmanFatass/My-paper-code/issues/7#issuecomment-5556115060
