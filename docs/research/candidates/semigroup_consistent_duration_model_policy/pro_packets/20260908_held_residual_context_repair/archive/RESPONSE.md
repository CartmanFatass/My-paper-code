**选择原候选 SCDMP-NATIVE-HOLD-RESIDUAL-B01，作为一次方向局部的 B/EXPLORE；确认先前完整答复的对象选择，也确认其“新的实质 RECAST”分类。** 这是本次读取固定证据后形成的裁决，不是确认旧交付回执。值得选择的理由是：在已有完整原生学习器上，这个双端残差确实改变 critic 的梯度耦合，却不增加信息、模型参数、训练交互或优化器调用；一个不扩展的直接配对能回答它是否改善最终 sampled 策略的完整原生回报。这个问题的收益预期不强，但有明确的局部决策价值，足以支持所给的一次比较，不足以支持更大的研究承诺。[^1][^12]

**本次只选择这一对，不恢复旧 D6 搜索，也不选第二方案。** 原有 RECAST_D6 和其后的方向局部 PARK 保持历史意义；新的重定向是从跨 k 动作价值共享及其人口寻找，转向现有原生 actor–critic 的残差-MC 损失耦合。实际 recast 的计数与顺序后果由同一 DM 按现有所有者规则记录，不能以“只是纠正交付”或“普通改卡”隐藏。我不修改方向、Portfolio 或 UAV 进入状态，也不把先前未应用的答复算成已经执行的 B。[^3][^4][^15]

## 旧答复的科学内容与交付冲突分别处理

我完整读取了保留的旧 RESPONSE，另读了其 intake 所述的完整答案／短回执区别，以及 reconciliation 中的单次 Send、自然完成、归档和 retired-context 冲突。旧答复确实选择了这一个残差-MC 配对并明确称为实质 RECAST；intake 说明其应用因已确认的所有者对话政策冲突而被阻止，并非科学段落缺失或残差方法已失败。短聊天链接回执不是完整研究答案；transport 的 scientific_decision_formed 字段也不能代替对全文的科学判断。[^14][^15][^16]

因此，旧答案是需要正面评价的已披露材料，不是本次必须服从的结论。我的确认基于下述源码差异、反证、成本和结果用途，而不是“已经有人回答过”。本次明确纠正请求允许形成新的裁决；这不追溯豁免旧交付，也不从单次 Send、模型标签或成功归档推导任何科学正号。旧答案未应用意味着本次仍在选择原来那一个对象，不是另加一对 learner、一次新证据筛选或另一次候选变更。[^14][^15][^16]

## 为什么这是有价值的重入，而不是旧家族复活

旧 PARK 针对的是：先在源状态／倒计时搜索谱系中找到两个时长各有实质优势的人口，再据此启动共享 Q(s,z,k) 的 D6/D8 学习问题。A01 的六个状态一边倒地支持 k13；A02 唯一另外选定的人口在 321 个候选 mission 后未能建立。旧 intake 明确没有再给人口、倒计时、learner 或自动衍生对象权限，也明确没有否定整个 SCDMP 或抽象 D6 架构。[^3][^4]

本候选的人口和坐标来自已实际使用的五 UAV 原生学习 recipe，而非为了修补 R7=0 或 A02 的失败而选择。干预作用于真实采集后的学习目标，保留完整同信息 MLP，并经既有 actor 更新路径作用于真实运动／服务和完整回报；其不同结果会改变是否继续研究这个固定惩罚的建议。这满足旧重入记录所要求的“搜索谱系外、不同机制、独立人口依据、原生动作后果和决策相关对象”，但不是靠历史祖先或名字自动获得价值。[^1][^3][^11]

我的具体投资判断是：不选后继仍是有力的竞争选择，因为保持相关支持少、方法已有包含关系、完整 MLP 可能足够，且原生时长控制近期有不利结果。不过，选一次已有完整 recipe 上的直接训练比较，能比先找保持语义的独有证明更直接地回答当前性能问题。保留 MC 锚点、无新增参数、固定系数和一对总预算，使这一次干预足够明确和可停止；这些限制并不保证正结果或运行成本。[^1][^2][^9][^10]

按证据规范 §11.8–11.9，不把未知 headroom、缺少双向时长占优人口、没有完整支持或唯一机制解释当作 B 的机械门槛，也不将这样的门槛搬到先行 A。移除这些前提所放弃的是精确最优性、完整支持和独有保持／semigroup 归因，不是 reward、information、training 或 primary 的可信性。这里无需规范例外。选择新损失家族是真正改变学习机制问题；仅降低诊断负担本身不是 RECAST。[^12]

## 源码差异、推导和实际因果路径

直接读取的 learner 用完整 episode 的 primitive rewards 做反向累积和，没有末端 bootstrap；采集记录的是动作前的 critic 输入和值，更新阶段才构造 MC targets。Actor 与 critic 分离，critic 是完整 136→128→128→1 tanh MLP；actor 的五条 GRU 历史在保持期间仍逐 primitive 步更新。源码事实 JSON 所保留的原 environment 接口片段说明，critic 输入是归一化全局状态及五个有序 prior-command／remaining-hold 块，不含 actor 隐藏历史，也不含此刻刚选择的动作和时长。[^2][^5][^6]

在同一已观察 episode 上，令 G_t 为 r_t 至 r_255 的回报和，R_t:4 为 r_t 至 r_3 的和，e_t=V_t−G_t。由奖励路径定义可得：

G_t = R_t:4 + G_4，

V_t − R_t:4 − V_4 = e_t − e_4。

所以 R_t:4+G_4 只是原 MC 目标；若把尾部改成 stopgrad(V_4)，就是多步半梯度 TD。选定项则对两个当前 critic 预测都求梯度：

∇(V_t−R_t:4−V_4)^2 = 2(e_t−e_4)(∇V_t−∇V_4)。

这是两个误差之间的耦合，不是独立 MC MSE 的简单重写，也不是 VSPC1 增加 640 参数的 remaining-hold 门控。该推导是奖励定义上的代数，不是本次运行的数值结果或 FP32 逐位相等保证。[^1][^5][^7]

一个重要限制随之可见：若已有 critic 在相关行上已经把全部 MC 误差拟合为零，新增项也为零；候选没有增加独立标签或额外信息。其可能价值在有限预算下的优化路径和正则化，而不是一个新的回报恒等式。共同实际未来尾部在误差差中消去，是提出这个干预的理由；它并不证明随机梯度方差更小、bias 消失或控制一定改善。t4 的预测本身仍会受随机状态、当前参数和未进入 critic 的历史影响。这些是从已读目标及输入定义得到的推断，不是已测效果。[^1][^2][^5]

来源 intake §4 已把双端梯度归入已有 sampled residual-gradient fitting，并说明随机转移的 double-sampling 限制及梯度抵销问题。我沿用的是这份明确归属的来源 reconnaissance，没有在本次另读论文或搜索文献；不将局部检索未命中当作新颖性证据。已知包含关系限定方法表述，不代替对一次性能探索价值的判断。[^1]

这里也没有确定性联合转移：只有 t0 选择 d1/d4，非零 remaining-hold 只可能出现在 t1–3，t4 全部恢复 primitive 反馈；期间未保持的 agent 仍能抽动作，GRU 继续观察。critic 的当前输入未被证明是充分 Markov 状态。因此，一个实际后继的双端梯度不能被称为平方“期望 Bellman 残差”的无偏梯度。候选优化的就是实际批次上的 sampled loss，不引入第二后继、模型转移、额外回放或未来 actor 信息。[^1][^2][^5][^6]

保留的完整作用路径是：保持动作的真实运动与服务回报 → 存储的动作前状态和既有承诺 → critic 双端残差与全部行的 MC 锚点 → 原有 actor/critic 联合梯度裁剪及以后 rollout 的 baseline → 归一化后 detach 的 advantages 与 compound PPO → 后续局部抽样动作 → 完整 native return。额外项没有直接通向 actor 参数的可微路径；但联合裁剪可能即时改变 actor 梯度的缩放，critic 变化还会影响后续采集的 advantages。当前 rollout 的 advantages 在四个 epoch 内仍固定，不能把这次改动写成每个 epoch 重算 advantage 或直接用 TD 优势训练 actor。[^5][^6][^8]

## 最强支持、最强反证与剩余解释

最强支持是已经核实的非冗余梯度干预、完整 MC 参照和可读的原生学习路径，而不是借另一个方向的正号。最强反对则是：新增耦合可能只把少数 opening 行和一个带误差的 t4 预测绑在一起，对真实控制无益甚至有害；完整 MLP 也许已经能学到有用关系。共同随机尾部的代数消去并不能排除这些反对。[^1][^5]

必须并列保留的既有观察如下；这些比较器和干预不同，不能汇总成残差处理的样本。

| 固定来源观察 | 对本次选择的含义 |
| --- | --- |
| VSPC1 master8101：GATED−MLP +0.0293656586，GATED−H +0.0194005494，MLP−H −0.0099651092；六个 GATED−MLP、七个 GATED−H 负 episode | 是损失不变、增加门控参数的另一个 n=1 包观察。正号不转移给残差损失；完整 MLP 低于 H 和训练方差未知都保留。 |
| UCOPE B02 master7001：T−G −0.0472671044，T−H −0.0224883084 | 实际时长能力在该实例中未带来更好的完整原生回报。 |
| UCOPE B02 master7002：T−G −0.0061362058，T−H −0.0243921875；两对 T−G 均值 −0.0267016551 | 两组 T−G 均负、两个 T−H 也负，是对乐观可用控制预期的更近反证，不是新残差已失败。 |
| SCDMP A01：W=2498，R7=0，R13=1；A02 在 321 个候选 mission 后未建立完整人口 | 旧 action-choice 搜索基础没有得到原拟议的双向支持。A02 的 K 量未观测，不是零，也没有新的时长对比符号。 |

表中事实来自原结果 intake／技术接受记录；更早 UCOPE6902 的 T−G −0.0503654、T−H −0.0332645 和 6901 的 G−H −0.0282038 也留作不利背景，不和当前候选混作重复。UCOPE 的科学方向处置仍属于其 DM。[^3][^9][^10]

仍无法区分的解释包括：一般残差正则化而非保持边界、完整 MLP 的冗余拟合能力、相邻端点梯度抵销、后继噪声／遗漏 actor 历史造成有害耦合，以及联合裁剪改变 actor 学习而非 baseline 更准确。若出现正结果，这些解释仍然成立；若只看到拟合或残差下降而 native return 变差，就没有性能成功。[^1][^5][^9]

尤其不能把“支持少”误写成“干预弱到可忽略”。每个两-episode rollout 最多六个团队 pair，但 L_seg 按实际 pair 数取均值，而 L_MC 按全部 512 row 取均值，两者在括号内权重同为 1。来源最大非零保持比例 0.01171875 并不是辅助梯度的权重比例。少量 pair 可能对优化有较大影响，包含对同一 episode 的 t4 预测反复施加耦合的相关性；这既是可能有价值的正则化，也是可能伤害训练的原因。按原候选保留系数 1，不新增权重搜索或最低保持数量门槛。[^1][^2]

## 本次选定的唯一比较

选定一个全新 master8201 配对：RESIDUAL-MC 与 MLP-MC。两侧都保留完整 critic 和相同 recurrent duration actor，每个 learner 66,441 参数；不加入门控、额外 head 或第三 learner。H 只是 attained reference。原五 UAV、50 uniform 用户、256 primitive 秒、native motion/channel/service、actor 观察和动作权限、团队奖励及 terminal law 全部保留。[^1][^2][^6][^8]

每臂 512 条完整训练 episode，每两条形成 512-row rollout，共 256 个 rollout；每个 rollout 四个 epoch，合计 1,024 次真实 Adam。保留 chunk32、lr3e-4、PPO clip0.2、joint grad clip0.5、CPU FP32 单线程，以及 agent_compound PPO。比较器的目标仍是原 policy_loss + 0.5×L_MC − 0.01×mean_entropy；处理臂唯一变化为：

policy_loss + 0.5×(L_MC + 1.0×L_seg) − 0.01×mean_entropy。

L_MC 覆盖全部 512 行。对同一实际 episode 的 t∈{1,2,3}，仅当该行已存 remaining-hold 中任一 agent 非零时，加入一个团队标量 (t,4) pair，不按 held-agent 数复制，不跨 episode 连接，不按回报或更新后策略重选端点。R_t:4 包含 r_t…r_3 而不包含 r_4；V_4 使用该 episode 在 t4 新 primitive 动作前已存的 critic 输入。L_seg 是实际 pair 的平方残差均值，无 pair 时为零。每个 epoch 从当前完整 batch critic 输出取两端，两个端点都保留梯度；奖励、mask 与原 targets 不成为新的可微或重采样路径。[^1][^2][^5]

Advantage 保持原来源方法：用采集时的 value 与完整 MC return 构造，按 rollout 归一化、detach，并在四 epoch 内固定。不能利用新增项顺便替换 targets、重算 advantages、改 compound likelihood、屏蔽原 MC 行或改变 actor 信息。两臂 on-policy 轨迹和 hold/pair 暴露可分离；配对的是初始化与外生 reset／RNG recipe，不是强制所有训练轨迹相同。[^5][^6][^8]

随机性沿 b=100000×8201 的原来源域安排，初始化 b+11，训练动作／时长 b+21、b+22，训练 reset b+1000 起，最终 reset b+2000 起，最终动作／时长 b+3000、b+4000 起；同源匹配但各臂持有私有 generator 对象，不能互相消耗可变流。保留原 reset 与构造语义。历史 master8101 代码及旧权重不覆盖、不纳入这次评估。[^1][^8]

只评最终 sampled 策略，各 32 个 episode，再在相同 32 个 reset 上评 H；不选最佳或中间 checkpoint，不转 greedy，不增加 TD、gate、非保持段、强制时长或其他 learner 比较。不声称优于普通 TD 或 VSPC1 gate。[^1][^8]

## 下一观察能决定什么

主要量为 32 个 reset 配对差 δ_e=J_RESIDUAL,e−J_MLP,e 的均值 Δ，J 为原生团队总回报除以 256。报告全部 episode、两项 J−H、实际 hold row／pair 数及条件评价 SE。已有配对差统计和 primary 读回路径就是最小有用工具观察；无需新增统计框架、bootstrap 服务或一次先行诊断。若使用 s_δ/√32，它只描述本次训练所得策略和该评价抽样条件下的变动，不估计训练总体方差。独立训练单位为 n=1，不是 32。[^1][^8][^12]

绝对 MEI=0.01 保持为本次原生时间平均团队回报的解释尺度。来源给出的单个持续服务用户 coverage 贡献 0.7/50=0.014 解释其量纲，不是保证能多服务一个用户，也不是从 H 推导的上界。经调优的同信息 upper-minus-baseline headroom 仍缺失；H 是已达到的参照，不是最优值。[^1][^9][^12]

| 完整且可信的观察 | 本次局部解释与建议边界 |
| --- | --- |
| Δ>0.01 | 一个可能值得在全结果 intake 后再考虑独立配对的包级原生信号。不是稳定优势，不要求所有 episode 为正，也不自动分配下一 seed。 |
| −0.01≤Δ≤0.01 | 在所选尺度内没有明确改善理由来重复这个不变惩罚；包含两端边界。不等于统计等价，不把小正号或更低残差当成功。 |
| Δ<−0.01 | 这个实例偏向完整 MC；保留损失，不自动调参、换 seed、补预算或另选方案。不能据此关闭所有残差方法或整个 SCDMP。 |
| 主要依赖不完整 | 不给依赖缺失的完整预算包作性能裁决；独立可信的已完成行、计数和异常仍报告。缺 H 只限制 H 相关结论，不自动抹去独立完整的 learner 主比较。 |

若任一臂低于 H，须与 Δ 并列并收窄可用控制语言；尤其两臂都低于 H 时，即使处理相对对照有正差，也没有建立有用的时长控制。残差更好、参数位移或 predictor 拟合准确都不能救原生损失。所有 batch 都无合格 pair 时，零辅助项是合法的观测分支，但没有检验到非零残差干预效果；不能为取得暴露而重抽时长、重跑或改人口。[^1][^2][^12]

这些读法决定的是这个具体有限包值不值得继续局部研究，不是 C 确认或整个方向的永久消费规则。当前不分配任何自动后继；缺少强结论也不被转换成先做额外 A 的要求。[^12]

## 工作量、成本和必要检查

主工作量是 2 fits×512×256 训练步，加 3×32×256 最终评价步：总计 286,720 native team steps、2,048 次 Adam 和 96 个最终评价 episode。两侧各一个新 learner，独立训练 pair 为一；没有候选策略、联合动作、轨迹分支或 solver 的嵌套搜索，没有额外 replay 或中间 checkpoint 选择。主要工作来自原生采集和既有 recurrent PPO 更新，而非一个被“有限”二字掩盖的搜索普查。[^1][^2][^8]

每臂 131,072 个训练 row，最多 1,536 个非零保持 row；处理臂四 epoch 累计最多 6,144 个新增 scalar 残差项。比较器可按既有接口报告保持数，但不为它增加辅助损失或虚构残差工作以凑相同计算。复用完整 batch critic 输出不需要额外网络 forward、单独 backward 或 optimizer 调用；索引、残差运算及计算图中的新增梯度贡献仍是实际算法计算，不能称为零成本。[^1][^2][^5]

每臂成本保持为 131072×c_collection + 1024×c_update + 8192×c_eval + 完整开销；第二臂另有 8192 个 H 步和配对发布。处理臂的 c_update 含新残差贡献，不能假定与对照完全一样。来源 VSPC1 的完整外部 wall 308.63 秒是已测规划锚点，不是新损失的上界或速度优势。增量 wall／CPU 未测；有限计数、批处理、无新增参数都不证明实际成本必然低。本次不增加成本实验或 profiling 来取得资格。[^1][^9][^12]

保留每臂完整 cap 1,800 秒、整对 3,600 秒，覆盖 admission 邻接启动、导入初始化、训练、最终评价、必要检查、publication/readback 和 exit。第二臂含 H 与整对输出；不能按阶段切片、重置计时、借第二臂额度掩盖第一臂超限，或只引用不含 exit 的内部 wall。实际后续沿 remote_first wsl_4070 的 CPU FP32 单线程与 exact committed accepted source 执行，运行时才取得新鲜 admission 和 detached accepted handle。本咨询没有新的 handle、资源测量或候选成本保证。[^1][^8][^11]

超限或主要依赖失败，停止这一次选定执行并保留已完成事实，不自动重试、加臂、调系数或加 seed。预算合规和性能符号分别报告：超限不能当作科学负号；独立可信的已完成回报也不能被用来掩盖真实 cap breach。缺失 publication/readback 依实际受影响的数据判断，不能凭缺少回执断言此前没有任何结果。[^8][^12]

必要检查只覆盖新增目标及主比较：同 episode 的 t1–3→t4 索引／奖励区间、两个端点梯度、mask 与无 pair 分支、完整 MC 和 actor 项、固定 detached advantages、primary 汇总及配对 RNG。独立 review 针对受影响学习路径；复用未改动 native 接口的既有检查，不重复整个 native 环境 suite 或完整历史回放。特别不能要求“新增 loss 后 actor 更新必须逐位不变”，因为保留的 joint clipping 本身就是可能的间接作用路径。工程 scope §4 需要 none；现行 research／runner／test 预算仍适用，不能为这个对象新增校验服务、重试框架或第五种 B 准入关卡。[^5][^12][^13]

来源机器记录的 MLP 为 66,441 参数、1,024 次实际 Adam，total displacement/initial-L2=0.4681669210，critic 比值 0.7238134732。这表明既有 recipe 在来源预算中能移动，不是新 penalty 已经有效或已发生位移。来源零初始化 duration head 的相对位移无定义，应保留绝对位移的解释，不能用极小分母制造巨大暴露；新增残差没有自己的参数组。实际后续报告真实 exposure，不增设每个参数组必须移动的普遍门槛。[^2][^6][^12]

## 依赖、交回路径和最终边界

当前 main-derived 固定证据树缺 environment.py 的事实仍保留。我本次没有读取其未列入清单的原完整文件，而是读取 DM 在 source-facts JSON 中从已指明原 UCOPE 提交直接保留的 hold／feature／team reward 片段；learner、policy、VSPC1 critic 与 study 则是在本次固定版本实际读到的文件。这个区别足以支持当前 source-based 选择，却不代表当前拼装源码已能直接运行或已获得实现接受。[^1][^2][^5][^6][^7][^8]

选定后的最小工程依赖，是同一 CM 按原已接受源码补齐环境依赖、保持接口与 native 语义，连同新增损失做相称检查及受影响学习路径 review。若补齐失败，只返回具体执行缺口；不换环境、不改人口，也不把整合失败当作科学负结果。本次没有授权 Pro 编码、测试或运行 learner。[^1][^11][^12]

这份完整新裁决由同一 DM 直接 intake，随后进入这一个对象的卡、CM 实现／review、accepted source、单次已选有界执行、全部结果收集与科学 intake；Root 依原路径集成和观察。没有新的 Portfolio 实现批准层。旧未应用答复保持原样，当前实际 RECAST 的仓库记录及相应顺序后果不在这份文件中代改；旧 PARK 不是一次新 recast，也不因当前选择而解除其 D6 源状态／倒计时搜索边界。[^3][^4][^11][^15]

最后的方向结论仍是：**确认选择原残差-MC 配对，并确认新的实质 RECAST；只继续这个有限损失包，旧 D6 action-choice 家族维持 PARK。** 最小下一科学观察就是这一对最终 sampled 策略的完整原生 Δ，连同两项对 H、负 episode、条件 SE、实际支持和真实成本。没有独有保持或 semigroup 归因、方法新颖性裁决、期望 Bellman 保证、确定性／充分 Markov 假设、稳定优势、gate／TD 优势、迁移、安全、部署、C 提升或自动 UAV 进入结论。

## 实际读取与来源归属

本次通过 GitHub connector 读取了下列十六条清单路径；科学依据使用原十三面，后三面只用于旧答复及交付冲突的披露。读取版本统一为 `7ba73a1be84be571f436d0499f3dbd5111802678`。原十三面的字节不变性是固定 TASK 披露的 DM 核对事实，我没有另做跨提交字节比较，也没有将额外三面或当前 Issue 评论当成新实验。DIRECTION 的判断限于 D6 recast／family park；证据规范的判断限于 §§4、5.2、11.4、11.7–11.9，工程规范限于 §§4–5；旧 RESPONSE 已全文读取。没有遇到清单路径访问缺口。

本次只进行了来源阅读、上述推导和这份交付，没有代码执行、模型／环境构造、native 或 synthetic steps、训练、评价、optimizer、replay、profiling 或新科学结果调用。新 learner 的 parameter displacement 不适用。未访问未列入清单的源文件、运行目录、论文原文、镜像或本地 clone；交付分支与 Issue 的读取仅服务交付核实，未替换科学版本。

[^1]: [docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_NATIVE_RETURN_COMPOSITION_P56_SOURCE_INTAKE_20260908.md](https://github.com/CartmanFatass/My-paper-code/blob/7ba73a1be84be571f436d0499f3dbd5111802678/docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_NATIVE_RETURN_COMPOSITION_P56_SOURCE_INTAKE_20260908.md)，§§2–4（源码、梯度、文献归属），§§5–6（候选与成本），§§7–9（反证及继续路径）。

[^2]: [docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_NATIVE_RETURN_COMPOSITION_P56_SOURCE_FACTS_20260908.json](https://github.com/CartmanFatass/My-paper-code/blob/7ba73a1be84be571f436d0499f3dbd5111802678/docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_NATIVE_RETURN_COMPOSITION_P56_SOURCE_FACTS_20260908.json)，sources、held_interface_excerpts、source_budget_reference_only、prior_mlp_exposure、actual_p56_exposure、unselected_candidate。

[^3]: [docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_D6_A02_POPULATION_CONVERGENCE_INTAKE_20260904.md](https://github.com/CartmanFatass/My-paper-code/blob/7ba73a1be84be571f436d0499f3dbd5111802678/docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_D6_A02_POPULATION_CONVERGENCE_INTAKE_20260904.md)，“Decision executed without local override”“Direct observations retained”“Exact re-entry condition”。

[^4]: [docs/research/candidates/semigroup_consistent_duration_model_policy/DIRECTION.md](https://github.com/CartmanFatass/My-paper-code/blob/7ba73a1be84be571f436d0499f3dbd5111802678/docs/research/candidates/semigroup_consistent_duration_model_policy/DIRECTION.md)，“D6 cross-k Q-sharing recast — 2026-09-04”及“D6 action-choice family park — 2026-09-04”。

[^5]: [experiments/candidates/ucope/uav_motion_prefix_b01/learner.py](https://github.com/CartmanFatass/My-paper-code/blob/7ba73a1be84be571f436d0499f3dbd5111802678/experiments/candidates/ucope/uav_motion_prefix_b01/learner.py#L12-L212)，returns_to_go（12–14）、collect_episode（29–155）、optimizer_for（173–176）、update（179–212）。

[^6]: [experiments/candidates/ucope/uav_motion_prefix_b01/policy.py](https://github.com/CartmanFatass/My-paper-code/blob/7ba73a1be84be571f436d0499f3dbd5111802678/experiments/candidates/ucope/uav_motion_prefix_b01/policy.py)，Actor/Critic、templates、arm_copy、joint_terms、sample 及 parameter_groups／exposure。

[^7]: [experiments/candidates/vsp_c1/native_hold_value_b01/critic.py](https://github.com/CartmanFatass/My-paper-code/blob/7ba73a1be84be571f436d0499f3dbd5111802678/experiments/candidates/vsp_c1/native_hold_value_b01/critic.py#L14-L32)，GatedCritic 与 models：保留完整 MLP，门控增加 640 参数，两个 actor 均有 duration head。

[^8]: [experiments/candidates/vsp_c1/native_hold_value_b01/study.py](https://github.com/CartmanFatass/My-paper-code/blob/7ba73a1be84be571f436d0499f3dbd5111802678/experiments/candidates/vsp_c1/native_hold_value_b01/study.py)，Config、Deadline、primary_from_rows、run_pair（84–251），RNG、完整训练、final sampled／H 评价及 publication/readback。

[^9]: [docs/research/candidates/vsp_c1/VSPC1_NATIVE_HOLD_VALUE_B01_INTAKE_20260908.md](https://github.com/CartmanFatass/My-paper-code/blob/7ba73a1be84be571f436d0499f3dbd5111802678/docs/research/candidates/vsp_c1/VSPC1_NATIVE_HOLD_VALUE_B01_INTAKE_20260908.md)，§§2–4：原生结果、负 episode、支持、包含解释、n=1 及完整外部 wall。

[^10]: [docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B02_P47_7002_AND_JOINT_TECHNICAL_ACCEPTANCE_20260908.md](https://github.com/CartmanFatass/My-paper-code/blob/7ba73a1be84be571f436d0499f3dbd5111802678/docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B02_P47_7002_AND_JOINT_TECHNICAL_ACCEPTANCE_20260908.md)，“Existing arithmetic-only aggregate”“Preserved limitations and return”；技术接受和算术事实不代替其 DM 方向裁决。

[^11]: [docs/research/portfolio/handoffs/2026-09-08-p56-scdmp-native-return-composition-question.md](https://github.com/CartmanFatass/My-paper-code/blob/7ba73a1be84be571f436d0499f3dbd5111802678/docs/research/portfolio/handoffs/2026-09-08-p56-scdmp-native-return-composition-question.md)，Target/deliverable、Source constraints、Acceptance/return、Budget/stop；只沿当前 TASK 授权范围形成决策，不执行其中其他角色的操作。

[^12]: [docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md](https://github.com/CartmanFatass/My-paper-code/blob/7ba73a1be84be571f436d0499f3dbd5111802678/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md)，§§4、5.2、11.4、11.7–11.9，尤其问题选择、B 直接比较、独立训练单位、依赖限定和相称成本／验证。

[^13]: [docs/project/ENGINEERING_SCOPE_SPEC.md](https://github.com/CartmanFatass/My-paper-code/blob/7ba73a1be84be571f436d0499f3dbd5111802678/docs/project/ENGINEERING_SCOPE_SPEC.md)，§§4–5；本候选无需新增所列机械设施，普通源码／runner／test 预算保留。

[^14]: [docs/research/candidates/semigroup_consistent_duration_model_policy/pro_packets/20260908_held_residual_convergence/archive/RESPONSE.md](https://github.com/CartmanFatass/My-paper-code/blob/7ba73a1be84be571f436d0499f3dbd5111802678/docs/research/candidates/semigroup_consistent_duration_model_policy/pro_packets/20260908_held_residual_convergence/archive/RESPONSE.md)，已全文读取；开头对象／RECAST 结论以及后续反证、预算、结果与边界，是本次明确确认的先前建议，不是新实证。

[^15]: [docs/research/candidates/semigroup_consistent_duration_model_policy/pro_packets/20260908_held_residual_convergence/CONVERGENCE_INTAKE.md](https://github.com/CartmanFatass/My-paper-code/blob/7ba73a1be84be571f436d0499f3dbd5111802678/docs/research/candidates/semigroup_consistent_duration_model_policy/pro_packets/20260908_held_residual_convergence/CONVERGENCE_INTAKE.md)，§§2–3、7：全文／短回执区别、已确认 retired-context 冲突及条件性同 DM 路径；§6 记录实际 recast 的后续计数／顺序后果。

[^16]: [docs/research/candidates/semigroup_consistent_duration_model_policy/pro_packets/20260908_held_residual_convergence/archive/RECONCILIATION_FACTS.json](https://github.com/CartmanFatass/My-paper-code/blob/7ba73a1be84be571f436d0499f3dbd5111802678/docs/research/candidates/semigroup_consistent_duration_model_policy/pro_packets/20260908_held_residual_convergence/archive/RECONCILIATION_FACTS.json)，send_evidence、archive_status、wait_status、return_receipt、github_delivery、policy_reconciliation；仅为交付事实，不提供科学符号。
