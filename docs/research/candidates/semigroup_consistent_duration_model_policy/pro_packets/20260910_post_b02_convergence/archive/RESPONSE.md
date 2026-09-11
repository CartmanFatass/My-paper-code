**决定在方向局部 PARK 当前固定开场 held-residual-MC 包；本次不选择第三个原样配对、损失修改或先行诊断。** 上次为增加一个独立训练实例而选择的 B02 已经完整完成，得到第二个正点差、但仍在原绝对 MEI=0.01 内的原生结果。这个结果没有否定残差方法，却使“继续原样重复以寻找所选尺度收益”的当前投入理由更弱；现有材料也没有给出一个比暂停更值得选择的具体新处理问题。这是对这个有限包的投入判断，不是等价检验、负总体均值结论或整个 SCDMP 的关闭。[^b02-intake][^b02-card][^b02-e0]

**两个正点差、真实非零学习和较低的已测进程成本，是反对本次暂停的最强证据，必须保留。** 我不把它们改成负结果；它们足以使“小的有用正则化效应”继续成立为一种可能，也使今后有明确理由的 B 仍然合理。但它们没有自动产生第三个配对的研究目的。当前选择的是可重入的窄范围暂停，而不是要求先证明该方法无效才允许停止，或先证明有效才允许重入。[^facts][^b02-intake][^methods]

## 暂停的最小单元

暂停的是这条具体续行家族：在既有五 UAV、50 uniform 用户、256 primitive-step 原生任务上，保持完整同信息 MLP-MC、原 duration actor 与训练配方，仅对真实开场 t1–3 到同 episode 的 t4 加入系数 1 的双端残差均值，并继续用相同有限训练预算及最终 sampled 原生回报判断价值。它包括没有新增研究理由的原样配对续跑；不是暂停所有残差梯度、所有时间一致性损失、所有时长学习或整个已接受的机制空间。[^b01-card][^b02-card]

本次不形成新家族或第三次 RECAST。旧 D6 action-choice／source-countdown-search 家族维持其独立的 PARK，recasts=2 及现有 Portfolio 生命周期、优先级、容量和争用顺序不变。当前暂停也不是撤销第二次实质 recast：那个决定选中了一个不同的学习问题，B01 和 B02 已经提供该问题的真实观察，不能因现在停止追加投入而抹去其历史意义。[^direction]

## 两个实例的原生结果与真实暴露

两个原对象都保持各自原卡的 **WITHIN**，尺度仍为包含两端的 ±0.01。B02 的原表明确将第二个 WITHIN 解释为建议窄范围暂停，并明确不是等价或广泛残差方法失败。前轮完整答复也事前写明，第二实例若仍处于该尺度内，建议将转向暂停当前不变包。这里采纳这一建议，是在读到实际 B02、正面权衡反证之后形成的家族决定；不是说原卡早已自动执行了 PARK。[^b01-card][^b02-card][^prior]

下表保留原 E0 的主结果与 H 对照；数值是原记录，不是本咨询重新采样或运行所得：

| 原对象及比较 | 平均差 | 条件评价 SE | 负差 episode |
| --- | ---: | ---: | ---: |
| B01／8201：RESIDUAL-MC − MLP-MC | +0.0067374074558942025 | 0.0055965465359414865 | 14/32 |
| B02／8202：RESIDUAL-MC − MLP-MC | +0.0036580559726658735 | 0.009076161383550479 | 12/32 |
| B01：RESIDUAL-MC − H | +0.007086659468526168 | 0.011858107098025586 | 15/32 |
| B01：MLP-MC − H | +0.00034925201263196577 | 0.00934944486292681 | 18/32 |
| B02：RESIDUAL-MC − H | +0.0029985050167081395 | 0.011735783142938593 | 14/32 |
| B02：MLP-MC − H | −0.000659550955957733 | 0.014463146814519831 | 17/32 |

这些观察不应互相抵销其含义。B02 处理相对完整 MC 的点差为正，而完整 MC 相对 H 的点差为负；前者不抹去后者，后者也不使独立可信的主比较无效。B02 的三个平均 J 分别为 0.14436567679417747、0.14070762082151161 和 0.14136717177746932。两次处理臂对 H 的点差都为正但小于 0.01，不能由此建立稳定、有选定尺度收益的可用时长控制。H 是已达到的参考，不是上界；调优同信息 headroom 仍缺失，不能用 H 推算比例 headroom 或判定最优性。[^b01-e0][^b02-e0]

负差计数用于保留不利观察，不是新的投票式 primary。B02 比 B01 少两个处理−MC 负差 episode，却有更小的平均差，已经说明不能以“更多 episode 获胜”替换原平均原生回报。也不能因为所有最终 J 非负而忽略上述比较中的损失。两个对象均未挑最佳 checkpoint、改 greedy 或删除不利 episode。[^b01-e0][^b02-e0][^study]

这不是空处理。B01 每臂有 1,500 个实际合格保持段 pair，处理臂跨四 epoch 共 6,000 个残差项；B02 每臂有 1,494 个，处理臂共 5,976 个。B02 的 256 个训练 rollout 中，242 个各有六个 pair、14 个各有三个，没有零 pair rollout。比较器记录合格 pair，但不施加残差。这里的 pair 是同 episode 两个时间端点的团队标量样本，不能冒充独立训练配对。[^b01-e0][^b02-e0]

每个对象的两臂都各训练 512 条完整 episode、进行 1,024 次实际 Adam，并各有 32 条最终 sampled 评价；H 另有 32 条评价。B02 两个 66,441 参数 learner 的总位移／初始 L2 为 0.4040849090800015 和 0.5128799408218019，critic 比值为 0.5639214998023688 和 0.7650236554643457。duration head 从零初始化，其相对位移无定义，绝对位移分别为 0.20008046925067902 和 0.24749335646629333。这些事实确认真实训练和非零干预已经发生，不是收益或因果解释。B02 两臂最终 d4 频率同为 0.5，也不能推出策略、动作或轨迹相同。[^b02-e0]

B02 的原 E0 保留 COMPLETE、空 limits、完整 learner/H primary、零 partial steps 及完整 publication/readback；collection_checks 记录了全部 1,120 个 episode、512 个 rollout、2,048 次实际 Adam、96 个最终行和两个有限 FP32 checkpoint 的核对。B02 intake 接受了这些事实。我读到的是这份直接结果与既有接受记录，没有重新执行其 checkpoint 解串、哈希比对或环境测试；没有发现本次科学判断需要的 primary 依赖缺口。[^b02-e0][^b02-intake]

## 为什么两次小正差仍不足以选择本轮第三次投入

反对暂停的证据有实质分量。两个独立从头训练的包都给出正的原生点差，且都确实执行了双端残差；这比一次未训练的代理指标或一次空处理更支持继续考虑这个机制。科学进程分别为 323.02 秒和 295.03 秒，也使另一次同规模比较在已有成本记录上看起来可行。n=2 仍然很小，因此不能排除有用的跨训练效应，更不能把没有统计显著性当成拒绝 B 的理由。[^b01-e0][^b02-e0][^facts]

但“仍可能有效”与“现在选哪一个后续”是不同判断。上次选择 B02 的具体价值，是不改任何处理语义，增加第一个跨训练实例的观察，并让 WITHIN、实质正差或反向损失各自改变投入建议。现在这个新增观察已经获得：第二个实例仍未达到原先为本包选择的效果尺度，而不是一个需要补救的失败运行。第三个原样配对当然还会增加信息，信息增量不为零；只是本轮没有另一个明确用途，使继续缩小同一包的不确定性比按原边界暂停更有价值。[^prior][^b02-card][^b02-intake]

这里没有从两个点证明收益必然小于 0.01，也没有把“两个 WITHIN”变成所有 B 的停机定律。选择暂停的依据，是当前原生目标和效果尺度、已完成的针对性独立复核、完整 MC 持续有竞争力，以及没有被选定的下一处理问题这几件事的组合。未知训练总体并不要求把每个开放问题都继续抽样到可以作 C 结论；反过来，原卡的暂停建议也不能永久禁止今后的具体新 B。现行 §§6.1、11.8–11.9 同时允许有复制目的的继续与针对最小单元的停止，不把任一种变成机械规则。[^methods]

第三个配对若仅以“再给一个 seed，也许会超过 0.01”为理由，会把原先有限的观察目的延长成等待选定尺度正号的序列。若改说“必须更多 seed 才能暂停”，则会把并未请求的总体确认义务反过来强加给停止决定。两者都不是本次选择的研究问题。我也不以 seed 必须全部改善、先行阳性、headroom、方法新颖性或唯一机制归因作为任何 B 的否决条件。[^methods]

不选损失修改，不是因为必须先定位每个缺陷。当前证据允许小的有用正则化、优化／共同裁剪、端点误差抵消、后继噪声、遗漏历史和条件评价波动等解释，却没有给其中某一项更强的、足以在本轮优先选择具体干预的依据。随手挑一个系数、裁剪安排或后继处理，并不能仅凭 WITHIN 就称为针对已证实问题的修复；事后改评价指标也不能替代新问题。一个基于源码或学习原理的明确干预假设今后可以成立，不必等到缺陷被实验证实；本次并未选择这样的新对象。[^source][^learner][^b02-intake]

## 推断边界与存活机制

两对象各有一个独立训练配对；B02 采用新的初始化、optimizer、数据和随机流状态，没有重新评价 B01 权重。臂内比较保留匹配初始化与外生 reset、私有 generator 和各自 on-policy 轨迹。这些生成事实，而非两个不同 seed 编号本身，支持把它们读作两个训练配对。每对 32 个评价 episode 只描述该对已拟合策略的条件表现，不能得到 64 次独立训练。[^b02-card][^b02-intake][^study]

已有工具给出的两配对描述性均差为 +0.00519773171428。两个小正号与一个小的正则化收益相容，也与其他效应和评价波动相容；其大小、符号和两个端点间的描述性 SD 都不能可靠刻画纯训练总体。每个端点已经混合了训练实例差异与有限评价误差；两个估计值相近不证明训练方差小。这里不用条件 SE 代替训练 SE，不做等价判断，不从两次正号制造总体正号概率，也不重新运行统计或重采样。[^facts][^b02-e0][^empirical]

FOUNDATIONS §4 对“可表示”“有理论关系”和“有限训练实际学到”作了区分：完整 MLP 有表示能力不证明它已学会全部有用关系；双端残差有清楚代数也不保证控制提升。FOUNDATIONS §6 与实证专题对训练实例、条件评价和完整包／组件归因的区分，实际限制了本次结论：保留两个包级观察，不把它们写成稳定优势，也不通过增设一整套归因实验取得暂停资格。知识材料帮助界定事实能说明什么，不替我或 DM 决定投入。[^foundations][^empirical]

被暂停包的学习路径仍然成立：开场 d1/d4 选择形成 t1–3 的真实保持；同 episode 的动作前输入与 r_t…r_3 进入完整 MC 加双端 value-error 耦合；经共同梯度裁剪及以后 rollout 的 baseline，影响原有 detached normalized PPO advantages、后续 sampled 动作和完整原生回报。其他未保持 agent 仍可行动，各 actor GRU 仍持续接收 primitive 观察；critic 不包含 actor 隐藏历史或刚选择的动作。残差没有直接通向 actor 参数的可微路径，但保留的共同裁剪可以立即改变 actor 梯度缩放，baseline 还会影响后续采集。[^learner][^b02-card][^b02-intake]

在已记录奖励路径上，G_t=R_t:4+G_4，所以 V_t−R_t:4−V_4=e_t−e_4。实际处理对两端都求梯度；用 G_4 拼接只是原 MC，用 stopgrad(V_4) 则是另一种半梯度 TD。现有来源文献核对将本处理归入已知 sampled residual-gradient fitting；本次复用其明确归属的核对结果，没有另读本地文库或原论文。共同实际尾部在误差差中消去，不意味着新增信息、无偏的平方期望 Bellman 残差梯度或更低随机梯度方差。段内也不能假定联合动作恒定、转移确定或 critic 输入充分 Markov。[^source]

L_seg 按实际 pair 数取均值，L_MC 按全部 512 row 取均值；因此直接支持稀疏并不等于梯度权重按行占比同样小。非零暴露排除了本实例的空处理解释，却没有测出辅助梯度在整体更新中到底有多大、是否抵消或是否有益。不能从 loss 大小、位移、相等 d4 频率或共同裁剪的存在，事后指定唯一原因。更低残差或 predictor 拟合也不能救原生损失。[^learner][^b02-e0]

## 成本确实低，但本次不是因超预算而暂停

两次已接受的工作及成本如下，均来自原 E0：

| 已完成对象 | Native team steps | 实际 Adam | 最终评价 episode | 完整科学进程 wall | CPU | Peak RSS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| B01 | 286,720 | 2,048 | 96 | 323.02 秒 | 321.77 秒 | 558,232 KiB |
| B02 | 286,720 | 2,048 | 96 | 295.03 秒 | 294.08 秒 | 553,832 KiB |

合计是 573,440 native steps、4,096 Adam、192 个最终评价 episode 和 618.05 秒科学进程 wall。这个跨两次调用的 wall 总和不是统一研究的 elapsed critical path，也不包括全部准备、检查、review、分析、collection、归档或控制平面工时。原 resources_unmeasured 标签与实际可得的外部 wall／CPU／RSS 各自保留。不能把部分成本记录冒充全工程成本，也不能因仍有未测部分而否认已经测到的低进程成本。[^b01-e0][^b02-e0][^facts]

我比较过给定的最小第三配对，而不是拿它与一个不必要的大搜索比较。该备选仍是 2×512×256 训练加 3×32×256 最终评价，即再增加 286,720 步、2,048 Adam 和 96 个最终 episode；至多每训练臂 1,536 个合格 pair、处理四 epoch 6,144 个 scalar 残差项。没有候选、联合动作、轨迹、controller 或 solver 搜索，主要工作是原生采集与已有 recurrent PPO 更新。复用 batch critic 输出不增加额外网络 forward、单独 backward 或 optimizer 调用，但索引、残差及梯度贡献仍是算法成本，两套重新训练绝不是零成本。[^facts][^learner][^study]

来源成本式仍为每臂 131072×c_collection +1024×c_update +8192×c_eval +完整开销；第二臂另含 8192 个 H 步及整对 publication/readback/exit。按最大已测完整配对 323.02 秒保守地向两臂各计一次，得到 323.02 秒/臂、646.04 秒/对的规划投影。它不是已测逐臂成本或新的上界；若改变处理，增量成本仍未知。原 1800 秒/臂、3600 秒/完整配对链不可按阶段重置或相互借用。[^facts][^b02-card]

这些数量支持“第三配对看起来可负担”，而不是“它因成本必须被拒绝”。本次暂停是当前新增观察的决策价值判断：先前特意选择的独立复核已经完成，在原用途与尺度下又得到一个 WITHIN；不能仅因有预算余量就继续分配相同实验。已花费的两次成本也不是必须停止或继续的沉没成本理由。我没有测算精确的信息价值／成本比，更没有假定别的方向具有更高收益；Portfolio 排名不在本请求内。[^prior][^facts][^methods]

本次不提出 cost experiment、profiling、精确上界、支持普查或因果诊断。因而没有一个先行 A 可以被误当作未来 B 的准入条件。相应放弃的仍是精确最优性、完整机制归因与总体确认，不是对真实 reward、信息、训练和 primary 的保护。工程 scope §4 需要 none；没有新增验证框架、字节守卫、调度或重试设施。[^methods][^engineering]

## 有用但不设隐性门槛的重入条件

重入的核心是一个能说明“下一观察将改变什么选择”的具体理由，而不是一张先证明成功的证书。这个理由可以直接来自已有源码、已有结果或明确的学习假设；不要求先跑阳性 toy、先取得显著性、精确上界、完整 headroom 或逐个诊断存活解释。两次 WITHIN 及其原 MEI 和不利 episode 必须继续作为已知背景，而不能被换名或选择性引用消除。[^methods]

一种可用理由是在同一已接受机制内，提出一个明确的 loss／credit 改动，说明它改变哪一段信息到梯度再到原生动作的路径、为什么可能改善当前性能、最强的简单替代解释是什么，并由完整同信息 MLP-MC 和真实最终 sampled 原生回报作直接比较。它不需要事先证明旧实现有 bug，也不需要先把所有替代解释排除。这里没有选定某个具体改动，更没有授权系数网格或最优 seed 搜索。[^source][^methods]

原比较本身也不是永久禁区。今后若有具体的使用或研究决定确实依赖它的跨训练变动，可以重新说明为什么增加一个训练实例现在会改变该决定，以及各类结果怎样影响下一建议；这可以构成新的复制理由，不必先有一个 UP。仅说“n 仍然小”“必须补足某个通用 seed 数”或“下一次可能达到阈值”不足以说明本轮之外的新价值。这个区别是问题选择，不是统计显著性或普遍配额。[^methods][^empirical]

任何实际重入只需在既有卡／任务与同一 DM 的正常 intake 中把问题、单一处理或复制目的、比较器、独立单位、原生 primary、真实工作量和停止边界说明清楚，不新增批准层。若用途确实要求不同的效果尺度，必须说明新对象自己的科学理由，不能把 B01/B02 追溯改判；本次并不改变 0.01。若所需变化实际上换了机制家族或任务权限，应明确提出范围问题，而不是在本暂停下偷开新家族或第三次 recast。[^methods][^engineering]

本次没有选定下一科学 discriminator：没有第三个 master、learner、loss 变体、旧权重评价或诊断调用。上述是将来重新提出问题的条件，不是现在分配的实验，也不是新的通用 Pro 启动关卡。当前暂停无需等待某个缺失 headroom、显著性或清理回执才能成立。[^methods]

## 交回、保留事项与实际阅读范围

由同一 DM 对这份完整裁决作现行 owner/spec conformance intake，并在其既有权限内记录这个最小包的 PARK；Root 负责原有路由和集成。Pro 本次只交付本文与对应评论，不修改源码、方向或 Portfolio 状态。若将来另有实际选定的 B，其确切 allocation、适用检查／高风险 review、已发布 source、原 remote-first wsl_4070 CPU FP32/thread1、紧邻执行的物理及有效可用内存均至少 4 GiB admission、detached 监督和完整成本边界再由该实际对象落实。本次没有新 handle。[^b02-card][^engineering]

原 E0 的文档写入／stdout 编码修复、无科学曝光的准备操作和被 policy 拒绝的测试 scratch 清理，都保持各自工程含义。它们既不使完整 primary 失效，也不是残差方法的科学负号。B02 intake/E0 记录已在删除远端执行 checkout 前完成原证据保留；这是我从固定记录读到的归档事实，不是本咨询重新访问了远端或验证了 ZIP。旧 B01 的工程限制和历史 quarantine 不在本次解除，也不为处理它们新增操作。[^b02-e0][^b02-intake]

科学阅读覆盖清单的十五个有效路径／版本。新增的准备事实、B02 卡、B02 E0、B02 intake、更新后的 DIRECTION 和确切 B02 study 已通过 GitHub connector 读取；前轮完整 RESPONSE 在本对话已按同一不可变提交全文读回，本轮复用全文并重新核对其结果／停止段。B01 原卡和 E0、P56 source intake §§3–4、未改 learner、当前证据／工程规范以及 FOUNDATIONS §§4、6 和实证专题，复用本对话此前按清单相同提交取得的直接内容，未用新 SHA 替换它们。以下引用逐项保留路径、完整提交与使用章节。

对 B02 E0 的读取包括原规则、两臂及总计数、三个完整配对差数组与统计、最终均值、训练支持、资源／collection／deviation 和两实例汇总字段，以及 final_episode_rows 的相关片段；不是重新逐行审核全部训练轨迹或重复 DM 的技术接受。没有决策关键来源的访问缺口。未跟随清单外链接、原论文、本地文库、moving main 或旧讨论作为科学输入；当前分支和 Issue 读取只用于交付核实。

本咨询没有代码执行、模型／环境构造、native／synthetic steps、训练、评价、optimizer、replay、profiling、support search 或新科学调用。本次没有 learner，其参数位移不适用。**最终结论保持为：窄范围 PARK 当前固定开场 t1–3→t4、完整 MC 锚定、系数 1 的 residual-MC 包；保留两次真实的小正点差及 WITHIN，不选择本轮后继，不推出任何一般残差失败、稳定优势、等价、负总体均值、唯一保持／semigroup 因果、期望 Bellman 保证、TD/gate 优劣、迁移、安全、部署、C 或 UAV 进入结论。**

[^b02-intake]: [docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_NATIVE_HOLD_RESIDUAL_B02_INTAKE_20260910.md](https://github.com/CartmanFatass/My-paper-code/blob/859b0b2ed9f1c1eaa3bbc650c558befeca2b5bba/docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_NATIVE_HOLD_RESIDUAL_B02_INTAKE_20260910.md)，§§1–7，尤其 §§2–4 的原规则、独立单位、原生/H 结果及机制解释，§§5–7 的成本、建议与保留边界。

[^b02-card]: [docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_NATIVE_HOLD_RESIDUAL_B02_SCIENCE_CARD_20260910.md](https://github.com/CartmanFatass/My-paper-code/blob/78397e045e135e3b55a6d6af06a1227d50996f46/docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_NATIVE_HOLD_RESIDUAL_B02_SCIENCE_CARD_20260910.md)，原 §§1–7，特别是 §4 原 WITHIN 行、§§2–3 不变处理与独立训练、§5 计数／成本／cap；不使用后续未列入清单的卡修订。

[^b02-e0]: [docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_NATIVE_HOLD_RESIDUAL_B02_RESULT_EVIDENCE_20260910.json](https://github.com/CartmanFatass/My-paper-code/blob/859b0b2ed9f1c1eaa3bbc650c558befeca2b5bba/docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_NATIVE_HOLD_RESIDUAL_B02_RESULT_EVIDENCE_20260910.json)，rule_verbatim/rule_reading、summary、computed_primary、computed_final_means、training_summary、final_episode_rows、collection_checks、process_resources/cost_scope、deviations、two_pair_accounting；接受与工具数值均归属于原 E0。

[^facts]: [docs/research/candidates/semigroup_consistent_duration_model_policy/pro_packets/20260910_post_b02_convergence/PREPARATION_FACTS.json](https://github.com/CartmanFatass/My-paper-code/blob/d4cc1673479e708dc1f9bbfd5ba5e48810e03da6/docs/research/candidates/semigroup_consistent_duration_model_policy/pro_packets/20260910_post_b02_convergence/PREPARATION_FACTS.json)，accepted_evidence、two_pair_descriptive_summary、two_pair_accounting、prospective_one_pair_not_allocated、actual_consultation_exposure；规划数量不是新增执行或分配。

[^prior]: [docs/research/candidates/semigroup_consistent_duration_model_policy/pro_packets/20260910_post_b01_convergence/archive/RESPONSE.md](https://github.com/CartmanFatass/My-paper-code/blob/2b1a8d7a8395827ed654dac120641710e6a6c87a/docs/research/candidates/semigroup_consistent_duration_model_policy/pro_packets/20260910_post_b01_convergence/archive/RESPONSE.md)，完整原决定，特别是“为什么再看一个训练实例，而不是现在暂停或改损失”“新观察的有限读法与停止边界”（本轮重新读取第 67–92 行）及最终家族边界。

[^direction]: [docs/research/candidates/semigroup_consistent_duration_model_policy/DIRECTION.md](https://github.com/CartmanFatass/My-paper-code/blob/859b0b2ed9f1c1eaa3bbc650c558befeca2b5bba/docs/research/candidates/semigroup_consistent_duration_model_policy/DIRECTION.md)，“D6 action-choice family park — 2026-09-04”“Native held-segment residual-MC recast — 2026-09-09”“Native held-segment residual-MC B01 result — 2026-09-09”“Unchanged residual-MC independent pair B02 — 2026-09-10”“Native held-segment residual-MC B02 result — 2026-09-10”。

[^b01-card]: [docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_NATIVE_HOLD_RESIDUAL_B01_SCIENCE_CARD_20260909.md](https://github.com/CartmanFatass/My-paper-code/blob/5d52c5e5bed047e8e32fde575952133a7817b9d2/docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_NATIVE_HOLD_RESIDUAL_B01_SCIENCE_CARD_20260909.md)，§§1–7，特别是 §3 loss、§5 原 MEI／WITHIN 与 §§6–7 预算；复用前轮相同提交的直接读取。

[^b01-e0]: [docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_NATIVE_HOLD_RESIDUAL_B01_RESULT_EVIDENCE_20260909.json](https://github.com/CartmanFatass/My-paper-code/blob/e5ed770301e8f5bac9fd77063edd24bee550fb5f/docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_NATIVE_HOLD_RESIDUAL_B01_RESULT_EVIDENCE_20260909.json)，rule_verbatim/rule_reading、summary.primary/counts/limits/status、training_summary、final_episode_rows、process_resources、cost_scope 与 collection_checks；复用原直接记录，不重新采样。

[^study]: [experiments/candidates/scdmp_variable_k/native_hold_residual_b01/study.py](https://github.com/CartmanFatass/My-paper-code/blob/f079c753052f95f01754e50676a59d7541fd683c/experiments/candidates/scdmp_variable_k/native_hold_residual_b01/study.py)，Config、Deadline、primary_from_rows、checkpoint_identity、run_pair，私有匹配 RNG、最终 sampled/H 评价与完整计数／发布边界；直接读源码，未导入执行。

[^learner]: [experiments/candidates/scdmp_variable_k/native_hold_residual_b01/learner.py](https://github.com/CartmanFatass/My-paper-code/blob/7d0fc9d0091e046617493a1b23bbbf07297821cf/experiments/candidates/scdmp_variable_k/native_hold_residual_b01/learner.py)，segment_pairs、residual_loss、update；复用前轮完整直接源码读取，保留原双端梯度、归一化、MC、advantages 与 joint clipping。

[^source]: [docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_NATIVE_RETURN_COMPOSITION_P56_SOURCE_INTAKE_20260908.md](https://github.com/CartmanFatass/My-paper-code/blob/21a801279bd449c09907f5cf040efa693ae345a3/docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_NATIVE_RETURN_COMPOSITION_P56_SOURCE_INTAKE_20260908.md)，仅 §§3–4 的代数、梯度、间接 actor 路径及已核实文献覆盖；复用来源 reconnaissance，不声称本轮访问了其原论文或本地语料。

[^methods]: [docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md](https://github.com/CartmanFatass/My-paper-code/blob/4e8ce22f5263a4ebbf096cca6c4af225a0559831/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md)，TASK 采用的适用 §§4、5.2、6.1、11.4、11.7–11.10；复用相同提交的直接阅读，不采用无关对象例外，不以新方法重写历史对象。

[^foundations]: [docs/rl-marl-foundations-20260907/FOUNDATIONS.md](https://github.com/CartmanFatass/My-paper-code/blob/4e8ce22f5263a4ebbf096cca6c4af225a0559831/docs/rl-marl-foundations-20260907/FOUNDATIONS.md)，仅 §§4、6；表示／理论／有限学习、完整包归因及训练与评价单位的解释材料，不是投入权威。

[^empirical]: [docs/rl-marl-foundations-20260907/topic-notes/04_EMPIRICAL.md](https://github.com/CartmanFatass/My-paper-code/blob/4e8ce22f5263a4ebbf096cca6c4af225a0559831/docs/rl-marl-foundations-20260907/topic-notes/04_EMPIRICAL.md)，“随机性有层级”“完整方法比较与机制归因”“证据的力度随主张变化”；复用同提交直接阅读，不跟随未列入清单的链接。

[^engineering]: [docs/project/ENGINEERING_SCOPE_SPEC.md](https://github.com/CartmanFatass/My-paper-code/blob/4e8ce22f5263a4ebbf096cca6c4af225a0559831/docs/project/ENGINEERING_SCOPE_SPEC.md)，§§4–5 及适用 §7 接受／高风险 review；复用同提交直接阅读，保留普通源码、runner、检查预算和实际风险边界，不新增机械设施或批准层。
