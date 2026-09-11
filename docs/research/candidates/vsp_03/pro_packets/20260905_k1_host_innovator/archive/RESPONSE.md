**我选择一个直接的 B/EXPLORE：在新定义、固定 \(N=1\) 的持久目标任务上，比较“事件锁存规则软启动的完成／继续 learner”与“同信息、同网络、同预算的通用 learner”，把最小 host、动作消费者和原生回报实现纳入这同一个对象。**另保留一个无训练的固定事件规则参考，用来区分学习后的改善与规则本身的收益；不另开上界计算、完整普查或历史重构前置。

最低必要理由是：这项比较第一次让 VSP-03 的历史事件真正影响任务提交时机，并通过后续任务成败产生回报；它不重复已经完成的 K2 corridor 公共续约参考，也不需要假定旧事件源已经认证。选择单控制器，是为了先回答最小的终止学习问题，而不是用几个互不耦合的 agent 制造 MARL 表象。它的上限明确是**单控制器、有限预算的终止学习探索**。当前材料允许这样直接进入 B，不要求先证明精确 headroom 或机制价值。

**本节点决定已形成，没有来源访问 blocker；本回答没有运行实验或修改仓库，也没有产生新的经验结果。**旧 VSP-03 审计、A01 缺失事实及 FSD 完整停止边界均保持原义。 

## 依据：为什么选这个比较，而不是继续旧 corridor

以下仓库证据均读取自 `CartmanFatass/My-paper-code` 的固定版本 `b96ee986c47ccede71637bbd4904d6b4b83affca`。

**VSP-03 当前缺的是实现和测量，不是已观察到的零价值。**A01 的结果是共同人口、原生回报上界、胜任通用 baseline 及其暴露缺失，因此 headroom 不可计算。旧审计没有绑定真实目标负事件源，环境、policy、learner、optimizer、evaluation、return 和 lookup 活动均为零。`future_bound_manifest` 明确只是测试契约；`evaluate_boundary` 等函数支持的是先判定、后更新，以及负事件锁存穿过 re-entry 的语义，不是原生任务收益。

旧 A01 的后续建议曾偏向先定义无 learner host/reference；本次采用的 §11.8 和当前设计说明已允许把必要 host 实现放入直接 B。**改变的是新对象的启动顺序，不是回写旧普查。**

### 与现有资产的实际兼容性

| 维度             | 现有 corridor 的事实                                                                          | 本次复用与不复用边界                                                  |
| -------------- | ---------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| Observation    | 公开时间、lease freshness、segment age、角色、区域、zone、change flag、dwell age、lagged cue             | 可复用批处理和时间记录习惯；这些字段不是新任务的现成 observation                      |
| Action         | 原生 role 与 `RENEW/KEEP`；续约支付一个零服务 step                                                    | 新任务是 `COMPLETE/CONTINUE`，必须实现自己的消费者，不能把续约 mask 政名           |
| Information    | K2 的 flag 加旧 cue 能恢复新 latent；epoch 变化持续作废 lease                                          | 新任务的目标离开后可以返回；历史离开不自动使未来任务失败。两者不是同一事件语义                     |
| Reward         | 每个 primitive step 的原生服务平均值                                                               | 新任务采用实际交付、尝试耗费和等待成本；不迁移旧回报数值或 margin                        |
| Population     | 既有 E3/E4 为固定 N6、K2、Z4、两区域、H400；coupling 关闭                                               | 新对象固定 N1、一个目标、一种控制角色，无 joint consequence，因此不作 MARL 特异性声明    |
| Budget／learner | 七个可复用 baseline 单元仅支持原 homogeneous host 的固定时钟结果；driver 经抽象 skill、actor、mask、存储和 update 执行 | 不借用旧 baseline 成绩或 checkpoint。新比较训练自己的通用 learner，不假定旧恢复路径已就绪 |

这些区分来自 `config.py`、`host.py::step/observations`、`references.py::GreedyOnPublicState`、`hmasd_driver.py::run_rollout` 及 baseline 结果。尤其是，`update=False` 并不证明恢复了已训练策略；替换 renew mask 也不自动同步 skill 状态和 segment bookkeeping。

### FSD 的完整边界不变

保留 post-E4 对**现行固定 N6/K2/Z4、两区域、H400、公开 flag/cue、既有 HMASD skill/actor 路径上的 policy-gap 学习收益分支**的 PARK；不选择其续训、阈值重调、mask 干预、K3、Q-head 或 team-credit 改写。这是可逆对象族选择，不是新经验阴性或整个方向关闭。

同时保留 E3 的全部有效观察：原 H0 只覆盖 `c=c_Z=.25`、原大差异行和每臂 20 rollouts／128,000 transitions；small seed 2 的合格正例 `+0.033291585286` 不被抹去，small seed 3 的正观察仍带比较器能力不足限制，medium／large 六个合格配对亏损、两个事件路径窗口和不等 optimizer 暴露均不改义。E4 仍为三种 law、288 候选、零 learner 的完整 A；其报告的 switching-reference 机会已由公共 greedy 解释，不成为本次新 learner 的收益证据。

## 下一步：只实施这个最小 B 比较

**下面的环境、模型和数量均是本次前瞻设计，不是声称仓库已经存在的实现或结果。**

### 1. 新 host：等待后提交一项不可撤回的任务

固定一个 agent，角色为“任务提交控制器”；固定一个目标，整集内身份不变。没有伙伴、成员变化、替换、probe、通信限制或私有信息干预。这里实际绑定的是**终止时机**，不是多 agent 协作。

每集有一个工作请求，primitive horizon 为 **40 ticks**，状态时刻为 \(0,\ldots,40\)。每个 tick 都实际执行；动作完成后仍推进剩余物理时间，不提前截断 episode。

目标状态 \(y_t\in\{0,1\}\) 表示是否处于可作业区域，\(d_t\) 为当前连续驻留年龄。初始 \(y_0=1,d_0=0\)。新模拟过程定义为：

$$
\Pr(y_{t+1}=0\mid y_t=1,d_t)=\frac{1}{d_t+4},
\qquad
\Pr(y_{t+1}=1\mid y_t=0)=\frac12.
$$

留在区域时年龄加一；离开或重新进入时年龄归零。该 law 没有与四 tick 确认窗口重合的硬阈值。所有转移随机量按 episode 和 primitive tick 编址，独立于 policy 动作；未来随机量不进入观察。

事件发生在半整数时刻 \(t+\tfrac12\)，决策发生在整数边界，因此没有事件与决策并列时序的歧义。目标负事件是这个**新模拟器自己产生的 \(1\to0\) 转移**，不是旧审计来源的认证。

决策机会为 \(t=0,4,\ldots,32\)，最多九次；两种动作对两臂同样合法：

* **CONTINUE：**继续等待四 ticks；在最后机会 \(t=32\) 继续，则等待到 \(t=40\)，按未提交任务结束。
* **COMPLETE：**结束确认 option，立即启动一个不可撤回、持续八 ticks 的实际任务。只有未来八个服务采样时刻全部处于区域内，才完成交付。期间任何一次服务失败均使这次任务失败，但仍执行完整八 ticks；此后不再提供新任务或决策。

因此，**过去区间发生过离开—返回，不能直接判未来任务失败；过去区间干净，也不能保证未来交付成功。**这切断了“奖励就是对 certifier 的赞同”的循环定义。

原生回报用整数账计算。设 \(S\) 为成功交付指示，\(A\) 为是否尝试提交，\(W\) 为提交前实际等待的 primitive ticks，则

$$
R=\frac{200S-10A-W}{200}.
$$

成功交付贡献一个任务单位，尝试成本为 \(0.05\)，等待成本为每 tick \(0.005\)。未提交者保留全部 40 ticks 的等待成本；失败尝试保留尝试成本和已发生等待。回报不按决策次数归一化，也不因长 hold 少记尾部。这个 reward 是新 toy 的任务假设，不是现实部署效用的认证。

### 2. 信息与机制：只改变软启动，不改变可访问事实

两臂共用一个公开历史处理器：

$$
a=\text{上个继续边界是否为正},\qquad
e=\text{armed 区间内是否出现过负事件},\qquad
b=a\,y(1-e).
$$

负事件锁存穿过 re-entry；边界先读取再更新；继续时令 \(a\leftarrow y,e\leftarrow0\)，提交或 episode reset 清除两位。这里借用的是旧规则的可读语义，不是旧来源认证。

两臂得到完全相同的公开事件历史、时间、驻留年龄和固定身份信息；送入网络的共同充分状态为

$$
x=(t/40,\ y,\ d/40,\ a,\ e,\ b).
$$

身份和角色是两臂共同已知的常量。该 host 的转移只依赖当前 \(y,d\)，剩余机会由 \(t\) 决定，因此无需让通用控制器先从长序列重建已经公开的年龄。**连派生规则位 \(b\) 也交给通用比较器，不把特征工程的信息优势藏在 treatment 里。**

两个 learner 使用完全相同的模型：

* Actor：`6→32→32→1`，两个 tanh 隐层，另有一个从 \(b\) 到 logit 的可训练直连系数。
* Critic：`6→32→1`，tanh 隐层。
* 按这个结构，每臂计划为 **1,571 个可训练参数**；实际实现由机器重新计数。

唯一干预是 actor 初始化：

$$
\ell_T(x)=g_\theta(x)+2\log(3)b-\log(3),\qquad
\ell_G(x)=g_\theta(x)
$$

作为初始值；两臂共同的输出残差初始为零，其他对应权重配对初始化。于是 treatment 初始提交概率为 \(b=1\) 时 \(0.75\)、否则 \(0.25\)，通用臂初始为 \(0.5\)。**所有系数随后都可训练，没有永久 veto、硬动作 mask 或强制遵守规则。**

这是一项明确的**事件规则初始化偏置**比较，不冒充新信息、不同策略类或已证明的记忆机制。

通用比较器的可信性来自完整公开状态、相同动作空间、相同网络和学习预算，不来自“generic”这个名字。其**实际胜任程度仍要由运行观察**；不能在训练前认证，也不能在运行后利用一个明显未学会任务的比较器宣称强学习优势。

### 3. 真实学习和评估闭环

采用一个最小的 episodic actor–critic：完整 episode 采样，计算 Monte Carlo return-to-go，以 critic 为 baseline 做策略梯度；联合 Adam 更新，学习率 \(10^{-3}\)，无 replay、无隐藏优化 epoch、无参数 sweep。熵系数从 \(0.01\) 在前 64 次更新线性降到零，后续为零。

执行链必须实际闭合为：

> 模拟事件 → 共同公开状态 → actor 采样原生动作 → host 执行等待／八 tick 任务及完整终局 → 存储动作、实际持续时间和原生奖励 → return-to-go／critic／梯度更新 → 固定 checkpoint evaluator → 逐 episode 原生回报及组成项。

不用原 HMASD skill/role 中间层，不复用旧 checkpoint、normalizer 或 publication 系统；因而不继承那些未经验证的恢复或反事实路径，也不需要重构它们来解释新任务。

训练与主要评价均采用有限 horizon、**primitive discount \(\gamma=1\)**。一般的半马尔可夫目标应写成

$$
\sum_{j=0}^{\Delta-1}\gamma^j r_{t+j}
+\gamma^\Delta V(x'),
$$

本对象因此就是实际累计原生回报。最后 CONTINUE 的八 tick 等待、COMPLETE 后的任务窗口和无决策尾部全部计入实际时间；终局 bootstrap 为零，不能每次边界只乘一个固定 discount 来替代实际持续时间。

评估采用相同的确定性 greedy 动作，logit 恰为零时统一 CONTINUE；关闭学习。额外的唯一无训练参考是固定 \(b\) 规则，等于 treatment 初始化时的 greedy policy。它只回答“学习后是否超过已有固定规则”，不是 upper 或调优通用 baseline。

### 4. 第一对训练的数量与暴露

只选择**一对独立启动的 treatment／generic 训练**，配对训练 seed 为 1；两臂共享按 episode／tick 编址的外生随机性，模型和 optimizer 状态独立。训练与评价随机流分开，不复用 FSD 的 tape 或训练状态。

| 工作项                               |                                            每个学习臂的计划 |
| --------------------------------- | --------------------------------------------------: |
| 环境 batch                          |                                     128 个完整 episode |
| 训练 batch／optimizer step           |                                             128／128 |
| 训练 episode                        |                                              16,384 |
| 训练 primitive transitions          |                                             655,360 |
| 实际决策样本                            |                                至多 147,456；按实际提交时间记录 |
| 中间评价                              |                         update 32、64，各 128 episodes |
| 主要评价                              |                           update 128，1,024 episodes |
| 总评价 episode／primitive transitions |                                        1,280／51,200 |
| 配置与选择                             | 一个配置；主要 checkpoint 固定为 update 128，无最佳 checkpoint 搜索 |

每次优化最多处理 `1,152×6` 的决策输入；采样时 actor 的活动 batch 至多 `128×6`。环境和 buffer 保持在 CPU，primitive 时间顺序不并行化。

固定规则在相同的 1,024 个主要评价 episode 上运行，增加 40,960 ticks、零更新。一次针对性检查使用八个完整 40-tick 合成 episode，覆盖初始 armed、离开返回、未来交付失败、最后机会与未提交终局，增加 320 ticks；它不是完整 support census。

因此，第一对比较连同这个参考和检查，计划总量为：

$$
2(655{,}360+51{,}200)+40{,}960+320
=\mathbf{1{,}454{,}400}
$$

个 primitive ticks；训练 optimizer step 合计 **256**。变长决策行数、policy forward、梯度承载样本数、失败与实际完成量必须分别机器记录，不能把上界当实测。

机器暴露记录至少包含各网络参数数目、初始化 L2/RMS、首次及最终更新后的位移和相对初始化比值、实际 optimizer steps、训练与评价 episode／transition、固定评价点及配置选择。**这些是后续必须产生的记录；本次实际新增训练、更新、模型和评估仍为零。**已有暴露文件中的参数位移不适用，不是 absent generic learner 的零位移。

### 5. 先删不必要工作，再确定成本边界

| 本次不做的工作                                            | 删除后的主张限制                                   |
| -------------------------------------------------- | ------------------------------------------ |
| 精确 upper、Bellman 最优解                               | 不报告最优性 gap 或可回收 headroom                   |
| 全部合法历史／support census                              | 不声称覆盖全部历史、失败型态或策略                          |
| 完整调优 sweep、全部 one-hit/dwell/debounce/hysteresis 臂表 | 只比较声明的两个 learner 配置和一个固定规则，不排除其他强 baseline |
| 无变化的重复 smoke、跨平台逐位重放                               | 不声称 bit identity；仍检查新行为和主要回报路径             |
| 全中间数组、全轨迹和全部 checkpoint 重构                         | 保留逐 episode 主要结果、曲线、暴露和失败，但不声称完整历史重演       |
| 旧 VSP／FSD 失败的完整复现与唯一根因定位                           | 新比较不依赖这些旧路径，不解释或修复其历史失败                    |
| 新 C++、GPU、worker pool、性能扫描平台                       | 只采用单进程、单计算线程、进程内数组／tensor batching，不作加速结论  |

这些删除缩小的是工作集合；**节约秒数未测，不能填入收益。**这与 §11.8 的主张依赖原则及当前工程／runtime 规范一致。

实际环境、actor 采样、return 构造、critic 与梯度更新、三个固定评价点、规则参考、必要检查和发布不能删除。研究级实现采用一个环境／学习模块和一个薄 runner，保持既有 2,000 行非测试源码、600 行 runner 及测试预算，不建设恢复、调度或验证平台。

**整次逻辑调用上限选为 1,800 秒**：一个科研进程内顺序完成两臂、共享检查、规则参考与最终输出。这个数是本次选择的计算额度，不是耗时预测；分阶段或分文件不重置。

对每臂 \(q\)，成本账采用

$$
P_q=I_q
+128\,C_q(128,40)
+10\,E_q(128,40)
+O_q,
$$

其中 \(C_q\) 包括一个完整训练 batch 的环境、policy、回报构造和一次 optimizer step；\(E_q\) 为一个完整评价 batch；\(I_q,O_q\) 分别为初始化与该臂输出。整次账再加共享 import、八 episode 检查、八个固定规则评价 batch、汇总及必要读回。

上述各阶段秒数目前全部**未测**。后续在实际节点用本次正常执行的完整 batch 记录成本并更新逐臂投影，已发生的训练保留为训练暴露，不额外建立 pilot、丢弃首轮或重启挑快配置。计划采用已列记录中的 CPU 执行路径；节点、解释器和资源状态仍须在实际调用时确认并重新准入。不得把旧串行时间除以核心数，也不得把 E4 的 2.35／3.09 秒或 E3 的 66,087.00043219907 秒当作新对象预测。

停止于完成规定比较，或到达整次 cap／发生影响必要路径的具体故障。不能为完成预算而缩短 episode、少跑提交后的八 ticks、删除尾部成本或挑选较早 checkpoint 冒充主要终点。未完成部分没有科学负极性；已可信完成的较早配对评价可按其实际较小预算报告，必须同时说明原定主要终点未完成。

## 反证：什么结果会改变判断

主要量为 update 128 在 1,024 个配对 episode 上的

$$
\Delta J=\operatorname{mean}(R_T-R_G).
$$

同时报告两臂及固定规则的绝对回报、成功交付率、等待 ticks、尝试次数、失败尝试和未提交率；事件后提交、离开—返回样本的结果只作带样本数的诊断。没有 oracle 时，不把每次失败提交或继续都命名为“反事实最优动作错误”。

描述性 MEI 取 **0.02 原生任务单位／episode**，相当于一次四 tick 等待的成本。这是解释尺度，不是启动门槛、显著性要求或新的硬阴性规则。

**支持信号。**若 treatment 在主要原生回报上优于通用臂，可报告这个配置和预算下的初步比较信号。若它还超过固定规则，并出现规则不能解释的有益动作调整，才有额外依据说真实学习改善了事件规则的原生后果；仍不证明学习是必要的。

**更窄的信号。**若 treatment 胜过通用臂，却不优于固定规则，保留正差值，但解释应停在“规则初始化／有限预算配置差异”；不能说已经获得超越公共脚本的学习价值。若 generic 明显未学会基本任务或持续弱于简单规则，明确比较器能力不足，不利用其败绩宣称强通用优势。中间点改善而最终回报下降，也只报告早期预算的局部现象，不择优替换主要 checkpoint。

**零或相反结果。**generic 追平，削弱这项初始化偏置在当前预算下的新增价值；treatment 因过度等待、错过期限或提交失败而亏损，是对该偏置的直接反证。它们不反证一切事件感知终止。只有记录显示具体问题——例如先验妨碍在临近期限时覆盖旧规则——才据此提出有理由的新 B 调整，不自动扩训练或换一个容易出正结果的 host。

最强替代解释始终保留：公开驻留年龄已经足够、普通 MLP 能学会相同决策、收益只来自初始化、事件频率与等待价格造成排序，以及实际决策样本数量随策略而变。**参数移动、布尔分歧和事件相关性都不能替代原生回报。**

配对 episode SE 只描述给定已训练 policy 的评价噪声；一个训练 seed 不能估计训练种子总体的不确定性。一次可信比较即可支持有界后续；阳性后优先同一比较的一到两个新增独立训练 starts，保留首个及后续所有正、零、负、失败、曲线和暴露，不跑到全阳性。重评同一 checkpoint 不算新训练，逐 seed 复验不需要重新建立机制家族或逐个送 Pro。论文级比较再承担公平调优、开发／最终评价分离、独立训练和与声明相称的不确定性负担。

## 未知与实际读取范围

尚未观察到的是：新 host 的实现正确性、两臂实际学习能力、generic 是否达到有说服力的能力、原生回报排序、训练 seed 变化，以及实际节点上的时间和内存。这些不是已发现的算法失败，也不是阻止当前对象定义的缺失环境事实。新实现必须在本次 B 内解决它实际依赖的 reward、信息、训练或主要测量问题；不能将这些未知写成已经通过的验收。

清单中的 **25 个路径均成功读取**。下表区分实际内容范围；没有沿文内链接读取清单外来源，也没有独立重算旧 E3/E4、检查旧原始 checkpoint 或执行代码。

| 实际读取路径                                                                                                              | 使用范围                                                                                        |
| ------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| `docs/research/candidates/vsp_03/VSP03_K1_HOST_DESIGN_EVIDENCE_20260905.md`                                         | 全文；直接 B 建议、兼容性、可移除负担、成本边界                                                                   |
| `docs/research/candidates/vsp_03/pro_packets/20260905_k1_host_innovator/EXPOSURE_AND_COST.json`                     | 全文；历史与当前零暴露、新成本未知                                                                           |
| `docs/research/candidates/vsp_03/DIRECTION.md`                                                                      | 全文；身份、K1 归属、历史位置                                                                            |
| `docs/research/candidates/vsp_03/CODE_SCIENCE_INDEX.md`                                                             | 全文；旧审计范围与未来来源限制                                                                             |
| `docs/research/candidates/vsp_03/VSP03_HEADROOM_CENSUS_A01_SCIENCE_CARD_20260904.md`                                | 全文；原普查问题、人口、比较器和规则                                                                          |
| `docs/research/candidates/vsp_03/VSP03_HEADROOM_CENSUS_A01_RESULT_EVIDENCE_20260904.md`                             | 全文；缺失 tuple、零运行与原建议                                                                         |
| `docs/research/candidates/vsp_03/VSP03_HEADROOM_CENSUS_A01_INTAKE_20260904.md`                                      | 全文；接受范围和未选择后继的边界                                                                            |
| `docs/research/candidates/vsp_03/VSP03_A1_EVENT_CERTIFIED_BOUNDARY_CONFIRMATION_RESULT.json`                        | 全文；source、activity、规则与未执行字段                                                                 |
| `experiments/candidates/vsp_03/event_certified_boundary_confirmation.py`                                            | 定义及相关函数；future manifest、source/parity、锁存、reset、boundary、truth audit 与部分 trace；未声称逐行审阅其余发布代码 |
| `docs/research/portfolio/decisions/2026-09-04-adopt-nine-routes-and-resume.md`                                      | 全文；组织共享与停止家族边界                                                                              |
| `docs/external-review/2026-09-04-two-line-consolidation-6pro/OWNER_FOLLOWUP_02_RESPONSE.md`                         | 全文；修订后的路线与兼容资产共享理由                                                                          |
| `docs/research/candidates/flexible_skill_duration/DIRECTION.md`                                                     | 全文；E3/E4 与当前 PARK                                                                           |
| `docs/research/candidates/flexible_skill_duration/pro_packets/20260905_e3_complete_convergence/archive/RESPONSE.md` | 完整回复，包括末尾最终裁决                                                                               |
| `docs/research/candidates/flexible_skill_duration/pro_packets/20260905_post_e4_convergence/archive/RESPONSE.md`     | 完整回复，包括停止范围、反证、未知、重入与最终裁决                                                                   |
| `docs/research/candidates/flexible_skill_duration/FSD_POST_E4_CONVERGENCE_INTAKE_20260905.md`                       | 全文；完整裁决的应用与归档完成                                                                             |
| `docs/research/candidates/flexible_skill_duration/FSD_E3_HETEROGENEOUS_HAZARD_RESULT_EVIDENCE_20260905.md`          | 全文；全部配对、双窗口、暴露与成本                                                                           |
| `docs/research/candidates/flexible_skill_duration/FSD_E4_CENSUS_RESULT_EVIDENCE_20260905.md`                        | 全文；三 law、公共 null、零 learner 与成本                                                              |
| `docs/research/baselines/relay_corridor/BASELINE_SET_RESULT_20260904.md`                                            | 全文；七个有效单元及缺失比较器                                                                             |
| `envs/relay_corridor/config.py`                                                                                     | 全文；固定归属、动作维度、参数和网格                                                                          |
| `envs/relay_corridor/host.py`                                                                                       | 全文；事件、epoch、lease、原生奖励、公开观察与时间顺序                                                            |
| `envs/relay_corridor/references.py`                                                                                 | DP、枚举、公开 greedy、固定／open-loop 及原生 rollout 接口                                                 |
| `envs/relay_corridor/hmasd_driver.py`                                                                               | 全文；模型构造、动作／mask、存储与更新                                                                       |
| `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md`                                                               | 正文及完整 §11，特别是 §11.8.1–11.8.8                                                                |
| `docs/project/ENGINEERING_SCOPE_SPEC.md`                                                                            | 正文、预算及对象限定附款边界                                                                              |
| `docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md`                                                                     | 通用要求及 VNFC 附款；确认该附款不适用于本对象                                                                  |

**下一步仅是记录并实现上述一个 B 对象，完成第一对真实比较。**不补做一个先行的上界／普查项目，不复活 FSD 的已停分支；结果最多支持这个新 N1 host 上的有限预算初始化与终止学习判断，不支持旧事件源认证、MARL 特异价值、稳定优越性、迁移或部署能力。
