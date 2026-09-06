# 开启一个首对 B，只回答冻结宿主上的小预算包比较

我的方向层决定是：选择 **RCLE-TBCFV-B01-PERSIST-VS-FLEX，一个 B/EXPLORE 首对**，在既定 TBCFV 宿主上比较 C1P1-COMMON-PERSISTENT 与 FLEX-REKEY；本次只纳入一个配对训练种子，每臂 200 次更新、每次 64 个训练 episode，最终 checkpoint 在八个 held-out 格上各评估 256 个 episode。主比较保留恢复时间 τ，但限于 **ACTIVE_CONTINUATION 的 8→12 和 12→8 两格**，两格等权；其余六格及八格总均值完整保留为伴随描述，不把静态和物理新纪元混入“成员变化后延续旧任务”的主问题。

理由不是持久公共计划已获支持，而是现有含括关系尚未回答有限学习预算的恢复性能；一次真正可比的学习观察，比先补齐上参考、调优通用基线或完整机制解释，更直接地决定下一小笔投入。该选择只形成可写卡的首个探索对象及工程边界，不接受任何源码、不启动调用、不冻结 C，不修改宿主、规范、Portfolio 生命周期、容量、优先级、融合或注册，也不授权定义卡的五臂二十 block 完整方案。[宿主卡：Question and decision value、Direct-value estimands][host]；[方向记录：2026-09-01 recast][direction]；[经验规范 §11.8–11.9][evidence]

## 证据支持什么，以及最强反对意见

**直接观察。** 当前定义卡仍是 definition_only，且 empirical_authorization=false。已列 A1 普查确认没有当前宿主数值结果，没有合格的数值上参考，也没有调优的同信息通用学习器结果；H_A1 是 NOT_IDENTIFIED，不是零。23 个实现文件和七份 preactivity JSON 是普查记录的存量，不是 23 个已验证可执行模块或七次实验。此次所读代码提供了实际算法和执行路径的静态证据，但没有构建成功、训练成功或任何 TBCFV 性能、成本的实测证据。[宿主卡：Scientific activity boundary][host]；[A1 结果 §§1–3][census]；[曝光与成本记录][exposure]

**最强支持是一个可区分的有限预算预测。** 保持公共计划可能减少成员边界处不必要的重写与个体化，使同样的训练量更容易产生低未服务需求和较快恢复。FLEX 的两个更新头末层归零可实现处理策略，且扩展从第一次更新即可训练，因此这不是通过剥夺比较器信息或可表达策略制造的优势。不过，函数类含括只排除了“FLEX 表达不了处理策略”这一解释，没有证明两臂优化轨迹、有效梯度分配、访问分布或学习难度相同。[宿主卡：Frozen learned arms、Strongest alternative explanation][host]；[packages.py：initialize_plans、transition_plans][packages]

**最强反对意见不是旧结果的负号，而是新比较也可能几乎没有学习。** 同一公共集合表示、角度排序和确定性 decoder 可能已经足以协调；公共 latent 可能被忽略；FLEX 也可能保留或改进处理包。更具体地，卡片规定每个非零更新的全参数欧氏步长只有 0.0005，故 200 次更新的路径长度上界仅为 0.1，末参数位移还可能因零梯度或方向抵消而更小。这是从冻结更新式推导的上界，不是已测位移，更不是“200 次足够学会”的证明。两臂均不改善时，低曝光、优化困难和宿主恢复指标饱和都仍是活解释，不能判定持久计划普遍无用。[宿主卡：Training, matching, and checkpoint law][host]

历史 CPC 的 16 种子结果是在不同宿主上，两项主差值均落在其 ±0.03 无实质带内；A1 所引另一 80 扇区宿主上，脚本化 REPLAN 在两种变化方向都描述性优于 CARRY。这些是反对过度乐观的背景，不是 TBCFV 极性。旧 B1/B2、CPC、信息必要性停止边界全部保留，不以本 B 重开或“救回”。[CPC intake：EM conclusion、Claim ceiling][cpc]；[A1 结果 §§4、6][census]

## 首对的实际问题、算法与匹配

卡的主张应写成：在冻结的 TBCFV、指定训练律和小预算下，观察持久公共计划包相对于同信息严格含括 FLEX 包，在未见 roster 的活动延续变化上的恢复差异，判断是否值得独立训练重复。绑定的 MARL 结构是 **agent 数量变化和成员变动后的协调恢复**。DM 草案中的“other-agent partial observability”不能当作本宿主的已识别原因：卡片明确给各臂相同公共状态汇总，刻意排除了私有线索聚合。这里可以研究有限预算协调与探索几何，不重建信息必要性主张。[DM 提案：开头的 claim/binding structure][options]；[宿主卡：Question、Shared maximum learned architecture][host]

宿主保持 120 扇区、六个服务信标、H=64、t_c=24、原需求与位置过程、六个始终合法的 beacon claim，以及同一 MOVE-TO-CLAIM decoder。训练每个更新含八格各八个 episode：6→6、10→10、6→10、10→6，分别交叉 ACTIVE_CONTINUATION 和 NEW_EPOCH。一个参数向量跨所有训练和评估格复用；held-out 的 8→8、12→12、8→12、12→8 与两种 epoch 条件不发生梯度、微调、归一化重估或模型选择。[宿主卡：Frozen physical host][host]

只有两臂真实学习。处理臂在活动成员变化处保持共同 z；FLEX 可使用共同及个体更新头。两臂均分配卡片的 26,161 个标量，同种子内复制相同初始张量，保留原事件噪声和公共随机数的语义配对；环境位置、成员到离和 epoch 外生变量配对，而不能在策略分歧后强迫两臂访问同一状态或采取同一动作。原卡关于公共 draw 和 actor draw 的配对条件仍适用。[宿主卡：Shared maximum architecture、Science-level probability law][host]

训练保持原来停止梯度的 Normal score 项、actor log-probability 项、64 episode 联合 loss、每 block 一次 backward 和归一化全向量的 plain-SGD 更新。各臂八个 stopped cell baseline 独立，先更新参数，再以 0.95/0.05 规则更新 baseline。DM 所称“各自优化器/归一化状态”在此应落实为这些实际存在的状态：原算法没有 Adam 状态或学习回报归一化，不得为套用通用 runner 而新增。FLEX 末层起点为零但保持可训练，处理臂的两个头硬屏蔽；不加入 entropy、辅助 reward、额外预训练或调参。[宿主卡：Training law][host]；[empirical_runner.py：execute_training_update 及更新调用][runner]

选择一个种子而非两个，是为了先用最小真实配对暴露新路径的学习、测量和成本问题，而不是假定一个种子足以代表训练分布。200 次和 256 episode/格是本次选定的有限探索尺度，不是从当前成本或功效数据算出的充分数；不存在此类数据。旧方向文字中的“三到五种子”和完整定义卡的二十 block 不转化为首 B 的入场要求。[方向记录：2026-09-01 recast][direction]；[经验规范 §§5.2、11.1、11.8.3][evidence]

## 主测量、MEI、曲线与统计单位

每个 episode 严格沿用 τ 的定义：在 h=0,…,36 中找第一个使 u_(24+h) 到 u_(24+h+3) 连续为零的偏移；不存在则记 40。报告的是这种失败编码下的有界恢复分数，不是推断出的未删失平均恢复时间。两条活动变化路径分别报告两臂均值、FLEX 减处理的差及 τ=40 比例；主汇总是这两个路径差的算术平均，正值有利于处理包。不得删除未形成可见计划、未恢复或表现差的 episode。[宿主卡：Treatment-blind physical endpoints、Direct-value estimands][host]

伴随主测量报告 U=(1/40)Σ_(t=24)^63 u_t，及 40U 这一累计**归一化**未服务需求。40U 不是原始 service-unit 数；需要原始单位时，在每格恒定的边界后 roster 下应再乘 N_after。八个 held-out 格均公开 τ、U 及可直接得到的 Y；八格总均值是预先声明的次要描述。NEW_EPOCH 同时改了信标与需求程序，其结果不能被称作纯粹的“抹掉计划身份”因果对照。保留已有 F 可作描述，但不为 F 新增必须的机制推断链。[宿主卡：Frozen physical host、Endpoints、Mechanism family][host]

**本 B 的 MEI 选择为 τ 的 4 个 physical tick，以及 U 的绝对 0.05。** 前者是边界后窗口的 10%，且相当于一个 claim 周期；后者相当于 40 tick 窗口内两个归一化未服务需求 tick。它们体现 DM 对值得继续投入的服务差的判断，不是实测的操作者偏好、普遍行业标准或已证明可检测的效应。低 U 区间不用相对百分比避免不稳定分母。这两个数用于解释初步结果，不是显著性门槛。[DM 提案：选项一][options]；[经验规范 §11.7][evidence]

尤其不能把 U 的 0.05 MEI 偷换成原完整 C 对象的 0.02 非劣界，或把本 B 的点估计解释为通过原 72-tail 规则。原卡的 win/no-material/competence 谓词仍属于原完整对象，本次不用它们判定一个两臂单种子探索是否“有效”。[宿主卡：Simultaneous inference、Literal exhaustive result map][host]；[经验规范 §§11.1、11.8.1][evidence]

学习曲线保存每次更新已有训练 episode 的 Y 汇总，按训练格及总体可读；每 25 次更新给一个展示点，同时保留全部 200 个 block 的原始汇总，不只保留八个好看的点。横轴同时标更新数与累计环境交互。这里的“每 25 次”不是另做一轮 held-out evaluation，也不产生可选择的中间 checkpoint；唯一用于 held-out 比较的是第 200 次更新后的模型。如此得到完整学习曲线而不悄悄增加评估或选择曝光。[方向 recast][direction]；[宿主卡：Training law][host]

单种子内可报告按 cell 分层、以配对 scenario 为单位的 Monte Carlo 标准误或描述性区间；现有 NumPy 的均值、配对差和方差计算已足以给这个观察，不需要引入新统计框架。不得将同一 episode 的 agent、tick、重复 checkpoint 或八个格当成独立训练种子。即使评估误差很小，一个训练种子仍不能估计训练种子总体不确定性；不用单种子 t 检验或 episode bootstrap 冒充稳定优越性。必要的最小存量是可按同一 scenario 对齐的 τ/U 读数、各格完成数、失败编码及训练曲线，不要求全轨迹或全部中间张量。[经验规范 §§11.8.3–11.8.6][evidence]

## 零学习器参考：选最近信标，不选伪装成脚本的 C0P0

我选择附上 **INDEPENDENT-NEAREST** 的一行参考，并同时保留八格细目：在同一组最终 held-out 外生 scenarios 上，每格 256 episode，共 2,048 个，只评估一次、不训练、不搜索参数、不看学习结果改脚本。它在每次 claim 选择最近信标、距离并列按较小 beacon 编号，不使用 plan latent。其具体作用是给 τ、U 的当前宿主水平一个易解释的非协调参照，帮助区分“双臂恢复指标都饱和”与“相对差异小”的读法，而不是提前证明学习器有资格参赛。[宿主卡：Treatment-independent opportunity and competence prerequisites][host]

C0P0-PRIVATE-REFRESH 是学习臂，不是零学习器“无计划脚本”。FLEX 目前也只是待训练的含括比较器，不是已经调优且被测为 competent 的 generic baseline。因此，这一参考和首对完成后仍不自动补齐 A1 所需的 upper/generic 配对，更不能把 Y 的代数上界代入当实测上参考。H_A1 在缺少该配对时继续标未识别。[A1 结果 §3][census]；[A1 intake：Next discriminator][intake]

参考实现具有简单的逐 agent、逐六个 beacon 扫描结构，但“秒级成本”没有实测支持，本决定不采用这一断言。它的执行计入总账和预算；参考行若因独立技术问题缺失，应明确缺失及用途损失，而不能据此抹掉已经独立可信的两臂主比较。[曝光与成本记录：prospective_scripted_reference_row][exposure]；[经验规范 §11.8.7][evidence]

## 完整工作量与支出边界

主导工作是两臂 × 一个训练种子 × 200 更新 × 64 episode × 64 physical tick，以及最终评估。每个 claim clock 的 actor 对当前各 agent 的六个 beacon 打分，训练还包含图保留、score loss、一次联合 backward 和参数更新。原语义 RNG、native reset/event/step、张量构造与输出均有成本；只有环境 tick 数无法推断这些开销。这里不做 6^N 联合动作枚举，不做轨迹搜索，不运行 coherent/fragmented 的匹配机会普查，也不通过“有限搜索”替代 learner。[宿主卡：Architecture、Training law][host]；[empirical_runner.py：execute_learned_batch、execute_training_update][runner]；[经验规范 §11.9][evidence]

以下为设计计数，不是已发生曝光或计时：

| 工作 | episode 数 | environment tick 数 |
| --- | ---: | ---: |
| 每臂训练 | 12,800 | 819,200 |
| 每臂最终八格评估 | 2,048 | 131,072 |
| 每臂合计 | 14,848 | 950,272 |
| 两臂合计 | 29,696 | 1,900,544 |
| 最近信标参考一次 | 2,048 | 131,072 |
| 两臂与参考合计 | 31,744 | 2,031,616 |

两臂总共两个真实训练实例，至多 400 次 backward/联合参数更新调用；零梯度更新和实际位移另如实记录。曲线从既有训练汇总得到，不增加 rollout。两臂 25,600 个训练 episode 合计才是完整卡 5,120,000 训练 episode 的 0.5%，不是每臂 0.5%。完整 7,741,440 episode 方案只说明规模，不给当前对象任何运行授权或加速估计。[曝光与成本记录][exposure]；[宿主卡：Science-level probability law and future counts][host]

**本对象主动采用每臂、每训练种子完整逻辑调用不超过 2,700 s 的硬上限；并把本次整个首对执行投入限制在 5,400 s 的累计执行 wall 内。** 后一个本地预算还包括实际支付的一次共享 native 构建、所选工程测量、必需执行检查、一次参考行和归并发布，不能把它们藏在两臂之外免费追加。各项按实际归属只记一次；共享准备占用总预算，意味着两臂不能都先用满 2,700 s 再追加准备成本。编辑和人工/代理推理时间不冒充实验执行 wall；外部排队、复制和传输另述，未测记未测。源码与测试仍受原工程预算约束。这是本次选择的保守投入边界，不把 runtime spec 的调查阈值误说成它自动批准的 cap 或额度。[runtime：General requirements §§1–3][runtime]；[工程范围 §5][engineering]

每臂计时覆盖该臂实际支付的 import/初始化、训练、最终评估、必需检查及发布，不能拆 phase、脚本或续跑来重置时钟。Study 同时报告 elapsed critical path 与各调用 wall 之和；逐次执行不暗示无限的后续调用预算。参考失败不追补、失败臂不替换，未用完的额度不是重复尝试的许可。[runtime §§1–2、7][runtime]

目前没有可信的数值 wall 投影。A1 的十五分钟和前身的四十五分钟都是声明上限，不是当前宿主成本测量。CM 的完整估计至少区分：初始化；200 个真实 64-episode 训练 block；2,048 个 learned evaluation episode；必要检查与输出；另有共享构建和脚本部分。**脚本 episode 的耗时只测到宿主/脚本路径，测不到 learned forward、图保留、backward 或模型输出开销，不能乘以 episode 数就声称得到了每臂成本律。** 未覆盖项继续标为未知或明确假设的估计。[曝光与成本记录：measured、unknown][exposure]；[empirical_runner.py：学习与脚本路径][runner]；[runtime §3][runtime]

已有可信投影若超过本地硬上限，不启动超限设计。DM 可在任何真实学习发生前记录一次两臂对称的更新数或每格评估数缩减，并相应重述实际问题；不能只缩一个臂、只留有利格或通过换算法解决预算。这里选定的基准仍是 200/256，而不是一个可以事后选择的菜单。成本未知本身不要求再造独立校准实验：实际 B 的首个训练 block 可给自身 wall 和学习开销，但必须计入该 B 的种子、64 episode、一次更新和总时钟，不丢弃、不重置为“正式第一步”。若那时暴露出无法在预算内完成，按下面的技术停止处理，不能把事后缩短的运行冒充完整的 200-update 对象。这样保留真实尝试的有限风险，而不把一个假的脚本外推当作可执行性证明。[经验规范 §§11.4、11.8.7、11.9][evidence]；[AGENTS §5][agents]

## CM 的最小工程准备及当前实现缺口

必须明确一个容易被代码存量掩盖的事实：所读 `__main__.py` 的 run/repair-resume 调用 execute_full_panel，并没有这个两臂、单 seed、200-update、256-episode B 的选择接口。所读 `empirical_runner.py` 的旧路径要求二十个 block 的 binding，创建全部 learned packages，训练循环到 800，逐臂逐格评估 2,048 episode，并调用完整的 prerequisite/value/mechanism reducer。它不是“编译完成就能直接跑”的本 B。[__main__.py：build_parser、main][main]；[empirical_runner.py：validate_materialized_binding、_new_block_runtime、execute_run_block、_cell_mean、registered_block_aggregates][runner]

CM 因而需要在普通 research 范围内实现最小 B 适配：复用 host、model、package、loss 和 update 计算，只创建实际两臂及一个配对 seed，传入所选预算，保留训练曲线和最终 τ/U/Y，发布一个可读的结果。不能伪造旧 lease/certificate、用 TEST 身份穿过旧二十 block 检查，或删去原完整 C 的必要量后仍称“同一完整对象”。新 B 不依赖旧 72-tail 发布器及其全部恢复链，故不继承那些机制与恢复保证；它仍需自己的真实主测量和完整比较语义。这是待 CM 实施的范围，不是本答复已经接受或改好的补丁。[经验规范 §§11.6、11.8.6–11.8.8][evidence]；[工程范围 §§3–5][engineering]

启动准备包括在 wsl_4070 对确切已提交、已推送源码的首次 native 构建，以及**一次最多 300 s 的零学习器脚本可执行性/成本测量**。为使其工作也有限，我选择至多八格各一个八-episode batch，即总计至多 64 个 episode、4,096 个环境 tick；达到 episode 数或 wall 上限即结束，不追加测量批次，不搜索最快配置。使用与最终 held-out 评估分开的准备样本，只问 native 生命周期、事件及输出能否执行、实际 wall/RSS 是什么，不用其服务高低挑种子、改宿主或抬高首 B 入场门槛。若发生目标宿主交互，即使 learner 数为零，也必须计入实际非学习交互曝光；不能继续宣称 TBCFV 从未执行。成功达到 64 episode 也不产生算法效果或完整 learner 成本结论。[TASK 的工程边界][task]；[runtime §§3、7][runtime]

旧 preflight 不能原样充当这个零学习器测量：所读代码会走 synthetic runner/frontier 链，并由 _new_block_runtime 创建模型。采用与本问题相称的最小脚本入口，不为一次准备移植这套历史证书和恢复设施。[empirical_runner.py：result-blind preflight 的 full_runner_chain、_synthetic_empirical_frontier_chain][runner]

仅保留一个针对实际改变路径及主输出的适度检查：确认真实回报、t_c 事件/claim/运动顺序、τ 的四 tick 与 40 失败编码、两臂初始对应及 FLEX 更新头的实际梯度路径、64 episode 联合更新和最终输出可读。复用已有可信检查；不得将其扩成所有历史重放、穷举包含性、跨平台 bit equality 或额外机制 gate。源码新增累计不超过 2,000 行、runner 不超过 600 行，普通测试仍按原五分钟预算及其 runner smoke 边界执行；不足就报具体缺口，而不是删去主测量或再加无限测试额度。不要新增 registry、validator、guard、worker pool、lease、retry 或壁钟/RSS 之外的遥测框架。[工程范围 §§3–5][engineering]；[经验规范 §11.8.6、11.8.8][evidence]

曝光记录要区分历史零曝光与 §11.4 所要求的“预算内能怎样移动”。CM 可从已有初始化律、参数清单和更新式机械生成 200×0.0005=0.1 的路径上界及对应初始化尺度说明，不为此创建额外学习器或试跑；实际非零更新、初始化范数及最终位移在被计费的真实 B 内记录。不得把路径上界当位移下界，也不另发任意 exposure-ratio 合格线。零历史曝光记录说明咨询没做实验，但不能替代对拟运行学习算法的曝光说明。[宿主卡：Architecture、Training law][host]；[经验规范 §11.4][evidence]

采用远程优先、确切提交、现有 detached supervision 和逐次准入。每个实际调用须在执行节点紧邻启动测得 physical/effective available memory 均至少 4 GiB；上一次调用或本地控制面的 receipt 不可代用。硬件名中有 4070 不意味着本算法已经走 GPU 或获得任何倍率加速；不默许精度、设备、RNG、batch/update 语义或多进程拓扑改变。本答复不访问执行节点、不运行 admission，也不声称 native 或整个学习链已被验证。[AGENTS §§5、7–8][agents]；[runtime §§4–5][runtime]

## 停止边界与结果怎样改变下一步

首次 native 构建失败、脚本可执行性出现错误或超出其有限界限、资源准入失败、所需适配超普通源码/验证预算，均停止本次启动尝试，保留已有日志、退出信息和实际计数，返回具体技术缺口。不能因此宣称 C1P1 或 FLEX 不会学习，不能自动开第二个 A、换 host、改 dtype、追加 retry 或替换 seed。后续修复是否值得投入由现有职责在新任务中决定，不是本次额度的隐含尾部。[经验规范 §11.8.7][evidence]；[AGENTS §8][agents]

真实 B 一旦开始，达到硬 cap、主量非有限、奖励/信息/事件顺序不符、缺臂、训练曝光不对称或 held-out 发生适配时，不能给依赖这些条件的完整包比较结论。第一臂已损坏且无法形成本次配对时，不自动用第二臂消耗剩余额度；第二臂损坏则保存第一臂的可信单臂事实，不另找配对 seed。技术停止不是不利科学极性。仅可选资源遥测或独立参考行缺失时按实际依赖降级描述，不把它升级为主比较损坏。[经验规范 §§4、11.8.7][evidence]；[AGENTS §8：Telemetry rule][agents]

有效首对的阅读叙事如下。这是 §11.7 要求的早期解释，不是 C 级预注册成功判据，也不要求区间先显著才能继续：

| 观察 | 当前改变 | 不允许的推论 |
| --- | --- | --- |
| 主 Δτ 达到约 4 tick 的处理有利差，且 U 没有显示达到自身 MEI 的反向损失 | 保留这个有限预算包作为值得独立重复的候选，同时呈现每条路径和任何较小 U 损失 | 不称稳定优越、已证明非劣、充分 competent 或 commonality/persistence 机制成立 |
| Δτ 有约 −4 tick 的反向差，或处理包有实质 U 损失 | 降低对当前预算下限制 FLEX 的支持；真实且清楚的反向结果也可值得一次独立重复 | 不关闭整个 RCLE，不推出所有预算、所有 N 或所有持久状态都无价值 |
| 点差在 τ ±4、U ±0.05 的兴趣带内 | 记录本次未见值得主张的 material 差；优先判断学习量、删失及训练 seed 不确定性，而非追逐更精确的小差 | 不称等价、零效应，或通过原 C 的 no-material 分支 |
| 两条路径相反、τ 与 U 有交易、误差跨越 MEI，或 τ 几乎全为 40 | 报混合/未决；U 和曲线保留其独立含义 | 不事后挑赢家路径，不改以 U 为主，不排除失败 episode |
| 主比较损坏 | 只接受独立可信的更窄事实与技术计数 | 不报算法正负极性，不用局部成功补齐完整对象 |

如果首对可信且比较含义清楚，我的默认后续建议是**下一笔单独记录的投入再加一个新的独立配对训练 seed**，保持同一比较和评估；需要一至两个新 seed 时依成本及实际波动作对象层选择。本次并未给这些后续 seed 额度。首对不必为正，不必显著；不得“跑到全为正”，也不能以更多 evaluation episode 代替独立训练。后续若改预算或算法，明确为看过本结果后的新 B，不称独立确认旧配方。[经验规范 §§11.8.2–11.8.3][evidence]

本次最直接的反证是：在有效、匹配的小预算观察中，FLEX 恢复不劣或更快，或处理包的恢复收益伴随实质累计未服务损失。它削弱的是“该包在这个预算和两条活动变化路径上有值得继续主张的净服务优势”，而非表达必要性或普遍机制。无差异加上弱学习曲线只能把投入问题推向曝光/学习性不确定性，不能宣布机制已被唯一否定。

## 不选择的对象及放弃的更强主张

不先建 upper/generic：那能改变 A1 缺失字段，却不是本轮最直接的包比较；调优 generic 本身需要真实 B 训练，不能作为“零学习器 A”隐藏在前置任务里。不单开成本 A：首次 native 可执行性属于上述有限 CM 准备；失败只形成待处理技术缺口，不自动新增科学对象。不跑完整五臂二十 block：首对不需要 factorial、机会普查和 72 尾同时推断；完整方案也没有当前成本依据。不卡停、也不回前身宿主：有明确有限的问题与已定义方法可试，缺 headroom 或旧宿主结果不能代替本宿主观察。[A1 intake：Next discriminator][intake]；[DM 提案：Options][options]；[经验规范 §§11.7–11.9][evidence]

相应放弃的是：相对于已经证明 competent 的比较器的结论、完整 target opportunity/headroom 结论、commonality 与 persistence 的分量归因、fragmentation 中介解释、纯 commitment-reset 因果效果、稳定总体优越性和 C 的同时误差控制。本 B 最多给出**这个冻结 toy、这个有限预算、这些已观察训练实例和 held-out 格上的初步性能信号或反例**。它不外推任意 N、其他 roster 轨迹、variable-k、UAV 仿真、飞行、实时安全或部署。[宿主卡：Strongest alternative explanation、Maximum claim ceiling][host]

## 实际访问、未验证部分与出处

任务文本按所给 `727a2d70c5a609ec5c874b8bbe6b5d698a4e0667` 读取；下列 17 个科学/协作来源均经已连接 GitHub 读取，科学引用统一固定在 `9324b08d0e50181ceefef507ec9c892f7580f7b4`，没有用默认分支、镜像、本地 clone 或未列出的链接替代。完整读取了宿主卡、方向记录、两份 A1 文档、CPC intake、三个辅助文件、__main__.py、packages.py、RESEARCH_MAP、经验规范、AGENTS 与协作文档；工程范围读取到所需 §§1–5，runtime 读取到 General requirements 所需 §§1–7。empirical_runner.py 只读与本决定有关的 1–250、751–1020、1651–1930、2101–2390、2441–2730 行；不声称审计了整个模块或其导入闭包。

[Issue #8][issue] 的实时正文和全部评论通过 connector 实际可读；本次交付前复核在 2026-09-06 约 17:02 UTC，评论列表为空，故没有已有讨论评论 permalink 可以引用。固定 ISSUE_SNAPSHOT 的 read_at=16:13 UTC 是另一时点，不冒充此次访问时间。Issue 正文指向早一版无 r02 的 packet 路径；未跟随，该文字不改变当前 TASK 的固定证据或交付范围。目标分支检查时仍在约定 base，目标 RESPONSE.md 读取为 404，未发现可复用的已有回复。[Issue 快照][snapshot]；[协作约定：Overall cutover][collaboration]

没有读取白名单外的 models.py、native 后端、配置、其他 baseline 或节点配置；因此没有独立验证完整含括实现、构建 ABI、远程环境、实际 precision/device 路由、机器内存或成本。23 文件库存和当前历史零曝光是所列记录的事实，不是本次跨节点执行普查。这些未验证项限制“已经可运行”的措辞，但不阻止依据明确宿主和现有静态实现选择一个有界 B 及其实际工程边界。

本次咨询只读证据和形成此决定，没有执行项目代码、测试、实验、构建、RNG materialization、模型创建、native state、transition、backward、optimizer step 或 evaluation。最小新观察仍然是上述首对，不是先取得完整机制证明。

[task]: https://github.com/CartmanFatass/My-paper-code/blob/727a2d70c5a609ec5c874b8bbe6b5d698a4e0667/docs/research/candidates/roster_consistent_latent_exploration/pro_packets/20260906_tbcfv_first_b_innovator_r02/TASK.md
[host]: https://github.com/CartmanFatass/My-paper-code/blob/9324b08d0e50181ceefef507ec9c892f7580f7b4/docs/research/candidates/roster_consistent_latent_exploration/RCLE_TARGET_BOUND_COMMITMENT_FRAGMENTATION_VALUE_SCIENCE_CARD.md
[direction]: https://github.com/CartmanFatass/My-paper-code/blob/9324b08d0e50181ceefef507ec9c892f7580f7b4/docs/research/candidates/roster_consistent_latent_exploration/DIRECTION.md
[census]: https://github.com/CartmanFatass/My-paper-code/blob/9324b08d0e50181ceefef507ec9c892f7580f7b4/docs/research/candidates/roster_consistent_latent_exploration/RCLE_GUIDANCE_A1_HEADROOM_CENSUS_RESULT_EVIDENCE_20260904.md
[intake]: https://github.com/CartmanFatass/My-paper-code/blob/9324b08d0e50181ceefef507ec9c892f7580f7b4/docs/research/candidates/roster_consistent_latent_exploration/RCLE_GUIDANCE_A1_HEADROOM_CENSUS_INTAKE_20260904.md
[cpc]: https://github.com/CartmanFatass/My-paper-code/blob/9324b08d0e50181ceefef507ec9c892f7580f7b4/docs/research/candidates/roster_consistent_latent_exploration/RCLE_CPC_R04_COMPLETE_RESULT_INTAKE.md
[options]: https://github.com/CartmanFatass/My-paper-code/blob/9324b08d0e50181ceefef507ec9c892f7580f7b4/docs/research/candidates/roster_consistent_latent_exploration/pro_packets/20260906_tbcfv_first_b_innovator_r02/EVIDENCE_AND_OPTIONS.md
[exposure]: https://github.com/CartmanFatass/My-paper-code/blob/9324b08d0e50181ceefef507ec9c892f7580f7b4/docs/research/candidates/roster_consistent_latent_exploration/pro_packets/20260906_tbcfv_first_b_innovator_r02/EXPOSURE_AND_COST.json
[snapshot]: https://github.com/CartmanFatass/My-paper-code/blob/9324b08d0e50181ceefef507ec9c892f7580f7b4/docs/research/candidates/roster_consistent_latent_exploration/pro_packets/20260906_tbcfv_first_b_innovator_r02/ISSUE_SNAPSHOT.json
[main]: https://github.com/CartmanFatass/My-paper-code/blob/9324b08d0e50181ceefef507ec9c892f7580f7b4/experiments/candidates/roster_consistent_latent_exploration_tbcfv/__main__.py
[packages]: https://github.com/CartmanFatass/My-paper-code/blob/9324b08d0e50181ceefef507ec9c892f7580f7b4/experiments/candidates/roster_consistent_latent_exploration_tbcfv/packages.py
[runner]: https://github.com/CartmanFatass/My-paper-code/blob/9324b08d0e50181ceefef507ec9c892f7580f7b4/experiments/candidates/roster_consistent_latent_exploration_tbcfv/empirical_runner.py
[map]: https://github.com/CartmanFatass/My-paper-code/blob/9324b08d0e50181ceefef507ec9c892f7580f7b4/docs/research/RESEARCH_MAP.md
[evidence]: https://github.com/CartmanFatass/My-paper-code/blob/9324b08d0e50181ceefef507ec9c892f7580f7b4/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[engineering]: https://github.com/CartmanFatass/My-paper-code/blob/9324b08d0e50181ceefef507ec9c892f7580f7b4/docs/project/ENGINEERING_SCOPE_SPEC.md
[runtime]: https://github.com/CartmanFatass/My-paper-code/blob/9324b08d0e50181ceefef507ec9c892f7580f7b4/docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md
[agents]: https://github.com/CartmanFatass/My-paper-code/blob/9324b08d0e50181ceefef507ec9c892f7580f7b4/AGENTS.md
[collaboration]: https://github.com/CartmanFatass/My-paper-code/blob/9324b08d0e50181ceefef507ec9c892f7580f7b4/docs/project/GITHUB_RESEARCH_COLLABORATION.md
[issue]: https://github.com/CartmanFatass/My-paper-code/issues/8
