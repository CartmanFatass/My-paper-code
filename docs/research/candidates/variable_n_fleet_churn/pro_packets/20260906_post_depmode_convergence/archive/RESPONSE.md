**最终决定：暂停当前 B01 的 N7 直接回报比较族——即在既定两区、单次成员损失宿主，现有 MAPR-4／DIRECT-SET-AR 拓扑、公开输入和终点回报 PPO 配置下，继续追求这组方法的比较优势。此刻不选择新的训练、额外记录分析或第三次 recast。已经完成的单次采样对逐 token 贪心问题，按其分支 3 在当前曝光结束。**

暂停的理由不是“没有学会”、没有精确 headroom、种子不够显著，或方向排序低。两个学习器都已经两次表现出真实恢复学习；尚未得到的是足以支持继续围绕当前 MAPR 特有价值追加相同工作的判别信号。上一轮具体提出的部署方式解释也没有带来可用的完整原生收益。当前需要一个有不同决策含义的学习问题，而不是再给同一小幅分离增加精度，或将未解释的差距自动转换成新的诊断工程。[两种子结果][S11]；[部署方式结果第 1—3 节][S1]；[上轮完整决定第六节][S9]

这是对**当前比较族下一步投入的可逆暂停**，不是关闭所有 N7 学习、成员变化后的共享策略研究或整个 VNFC 方向。B01 的正面学习结果和所有不利比较均保留；B/EXPLORE 没有由这次暂停产生的消费状态。下面限定暂停依据，并指出 DM 提案中不能作为依据的部分。

## 一、已获得的科学信息：共同学习成立，特有优势仍未建立

B01 的两个独立训练种子，每臂均完成 64 轮 × 32 个完整训练 episode、12,288 个联合 transition，以及四个 PPO epoch × 八个 minibatch 所构成的每轮 32 次、每臂总计 2,048 次优化。DIRECT 的参数和残差输出真实移动，回报也改善，不能把它当成未活动的空对照。两种子总共是两个训练样本对，初始化／中点／终点与后续评价均不增加这个数量。[两种子 intake，曝光和原生权衡部分][S11]；[实际 PPO 更新函数][S18]

| 原 B01 的 `R_fail_60` 读数 | 第一个训练种子 | 第二个训练种子 |
| --- | ---: | ---: |
| MAPR 最终减初始化 | +0.204127604 | +0.199453125 |
| DIRECT 最终减初始化 | +0.188658854 | +0.195520833 |
| 最终 MAPR 减 DIRECT，总体 | +0.015468750 | +0.003932292 |
| 最终 MAPR 减 DIRECT，区 1 | +0.028072917 | −0.029322917 |
| 最终 MAPR 减 BCRH，总体 | −0.041822917 | −0.060911458 |
| 最终 DIRECT 减 BCRH，总体 | −0.057291667 | −0.064843750 |

这些是保存结果的既有读数，不是本轮复算或重跑。两个种子的两个学习器在两个分区均取得恢复学习增益，其他三个原生指标相对初始化也改善；但各最终学习器在两个分区的 `R_fail_60`、`U_total`、`U_intact`、`J_ext` 均值均低于固定 BCRH。MAPR 相对 DIRECT 的两个总体正号保留，平均差 0.009700521 也保留；分区换号和服务权衡使它不能被描述为一致的优势。小差异同样不证明两算法等价。[两种子结果，“Per-seed results and native tradeoffs”][S11]

**对暂停最强的反对意见**是：共同学习确实明显，MAPR 的两个总体差都为正，训练还没有被证明饱和，而且一组完整真实 B 的实际成本只是数百秒。第二种子中 DIRECT 从中点到终点仍增加约 0.051016 的恢复回报，第一种子两臂也有后半程增益。更长训练可能有效，一个约 0.01 的效果也可能在某个明确用途下值得精确估计。这些可能性不能因本轮暂停而被改写成不可能。[同一 intake 的曲线解读及成本][S11]

不过，可能性不等于当前已经选出了值得继续支付的那一个问题。现有观察首先支持通用共享策略学习，而非 MAPR 独有收益。若只是原样补 seed，主要新增的是对这个小分离及其变异的描述；若只是延长训练，主要新增的是预算依赖。二者均可合法研究，但本轮没有一个明确的应用、效应精度目标或具体训练干预，使它们比保留当前结论、等待一个有区别的提案更有决策价值。这里没有要求先取得显著性、全部 seed 同号或成功的先导实验。

## 二、部署方式结果足以结束这一小问题，不足以排除所有执行原因

此次评价固定两个训练种子的四个 round-64 最终策略，参数位移均为 0。在同一个新的 64 世界面板上，每个策略分别以原分布单次采样和原逐 token 贪心执行；两区各 32 世界，BCRH 在同一面板执行一次。其本质是已有学习结果的固定策略性能延伸，没有新增学习者。[机器摘要的 config、checkpoints、exposure][S2]；[部署方式卡][S5]

| 策略 | `SAMPLE − GREEDY` 的总体 `R_fail_60`，均值 ± SE | 总体 `U_total` 差，约数 |
| --- | ---: | ---: |
| 第一个训练种子／MAPR | −0.006536 ± 0.0178 | −0.0330 |
| 第一个训练种子／DIRECT | −0.003646 ± 0.0036 | −0.0435 |
| 第二个训练种子／MAPR | −0.005599 ± 0.0082 | −0.0252 |
| 第二个训练种子／DIRECT | +0.016901 ± 0.0121 | −0.0224 |

三个恢复差为负，一个为正，且四个策略的总体 `J_ext` 都下降。第二种子 DIRECT 的正恢复差是实测事实，不能抹掉；它伴随总服务及原训练目标的损失，也不能单独命名为完整恢复方案改善。卡上分支 3 的条件满足，故保留其当前曝光下结束、不追加温度、多抽样、新面板或检查点的处置。[结果 intake 第 1—2 节][S1]；[摘要的 primary_contrast_means][S2]；[卡的事前读取规则][S5]

需要收窄三类措辞。

**第一，“执行方式已被排除为解释”过强。** 实际排除的是在这一组固定策略、这一面板和一次采样的投入边界内，把这两种预定执行方式的切换作为下一条可用改进路径；不是对所有部署规则、训练分布或差距根因的普遍排除。0.10 是描述尺度，而且大于当前约 0.055—0.074 的总体 BCRH 差距；单凭“未超过 0.10”本来就不能证明部署方式不可能影响这段差距。这里结束小问题的依据还包括混合恢复方向、四个总体 `J_ext` 的损失及上轮明确的停止边界。“在噪声内”也只能保留为描述，不能替代等价性或零效应检验。现有 SE 是固定策略、一个面板下的 episode 级描述量，不是训练种子总体的不确定性。[摘要 uncertainty 字段][S2]；[上轮解释边界][S9]；[证据规范 §11.8.3—11.8.5][S21]

**第二，回放验证只支持实际检查过的范围。** 结果 intake 和 `deployment_mode.py::b01_greedy_replay` 指向工程检查中的“第一个训练种子 MAPR，在其原 B01 评价面板上，64／64 行、十二个字段一致”。正式新面板的摘要中 `b01_greedy_replay` 为 `null`。这支持新入口的该条贪心解码路径，不支持“四个策略的新面板 GREEDY 行都与各自旧面板逐行相等”。新世界 master 与原回放 master 本来不同。四份参数装载和零位移另有直接记录；不需要为本次方向选择追加四份历史回放，也不因此撤销已接受的固定策略观察。[结果 intake 第 1 节][S1]；[CM 的冻结输入与验证范围][S6]；[回放与正式 run 函数][S17]；[摘要][S2]

**第三，约 0.055—0.074 是总体差距的概括，不能套给每个分区或每条 episode。** 例如摘要中第二种子 DIRECT 的 SAMPLE 减 BCRH 为总体 −0.056927，而区 1 是 −0.051563、区 2 是 −0.062292。保留分区均值落后这一观察，不将一个总体区间说成所有分区共用的数值区间，更不说每条轨迹都落后。[摘要末个策略参照对照的 strata][S2]。这些是解释范围的校正，不是选择重做评价的理由。

评价随机域采用已登记的 `conclusion/cut-derangement` 标签，但使用专用 master 和 `eval-actions/<record>/<arm>`／`eval-action/...` 用途。已读实现和接收记录没有给出与训练流共享 master、用途或地址的具体相关性来源；不能仅因标签沿用就判为科学缺陷。[`evaluation_uniform_supplier`][S17]；[CM “Semantics as implemented”][S6]；[接收决定][S1]

## 三、接受暂停的最小范围，但不接受 DM 的全部理由

DM 的暂停建议中，“缺少 headroom 记录”和“second-recast 后排序最低”不应进入本次科学否定链。前者是尚未建立的诊断记录，后者是调度事实。现行 §11.7—11.9 不允许把精确 upper、完整 headroom 或唯一机制归因变成普通 B 的前置；`AGENTS.md` 也明确区分排序与生命周期。[DM 提案][S7]；[证据规范][S21]；[权限与排序条款][S24]

历史控制器 A/RECON 的 `CH-D` 是 headroom bracket 未解决：特权路径在一个世界给出 `7/60`，总体下界为 `7/960`，区 1 为零、区 2 为 `7/480`；宽松物理上界不能把未识别变成无机会。该记录并未给出一个经过调优、同信息的 generic learner 配对上参照，也不能使 BCRH 成为当前学习者的已证上界。[原 A/RECON intake][S14]；[当前方向历史记录][S15]

本次暂停严格覆盖：**B01 当前宿主、MAPR／DIRECT、公开 actor 输入、未加塑形的 `J_ext = 0.5 R_fail_60 + 0.5 U_total`、既有终点 GAE／PPO 训练与 64 轮配置所形成的比较族，以及仅为挽救这组已见小差异而继续的同配置重复。** 它不是“所有 N7 直接回报方案均不可研究”。已经结束的部署方式子问题保持自己的停止边界；不通过改名重新增加温度、采样次数或检查点。

这一暂停允许如下保留结论同时成立：真实学习重复出现；MAPR 的两个旧总体差为正；DIRECT 是实际学习的合理同信息对照，但并非已证最优调参基线；固定 BCRH 的原生均值更高；未测的表示、信用分配、优化曝光或信息差异仍可能重要。后四者没有被部署方式评价唯一定位。[两种子 intake][S11]；[实际学习路径][S18]

## 四、为什么不在本轮另选信息、信用或记录分析

### 信息提案不能把控制器计算免费算作现有公开输入

DM 举例的“向 actor 暴露 BCRH 同信息候选评分”尚不是完整比较。BCRH 与 learner 的逐字段信息等价本来没有建立；候选评分还包含控制器的计算和先验。这样的输入可以成为一个合法的新方法，但必须说明新增了哪些原始信息或计算结果、对照能否得到同样输入，以及究竟检验信息增益、控制器辅助还是表示方式。不能沿用“同信息”三个字就把这些问题当成已经解决。[DM 选项 2][S7]；[B01 处理与比较条款][S12]；[固定参照函数][S19]

工作量也会变化：若在每个学习臂的每个实际训练决策上调用一次完整 BCRH 来构造特征，仅原样规模的训练就有 `2 × 2,048 × 6 = 24,576` 次调用，尚未计评价、输入组装和发布；原 B01 只是固定参照评价中的 384 次。这个计数是对该假设实现的条件推导，不是对某个已实现新方法的实测，也不允许把旧 384 次的时长直接乘 64 当保证成本。因不同臂到达的状态不同，也不能默认合并它们的控制器工作。[B01 实际曝光][S11]；[`experiment.bcrh` 与训练循环][S19]

这不是禁止控制器辅助学习，而是说明该类别尚未给出一个优先于当前暂停的、处理和对照含义明确的最小问题。本轮不为它购买候选评分 census、beam 或另一个可行性 A。

### 信用提案需要选清一个改动，而不是将目标替换叫作信用修复

源码显示当前更新把整条 episode 的 `J_ext` 交给 `gae_terminal`，再归一化 advantage 并进行 PPO。因此，改变时间信用或分区信用具有明确的可修改位置；这是一条可思考的算法路径，不是必须先排除的禁止选项。然而，“从终点回报改为分区服务差”尚未说明是保持同一原生目标的信用估计改动，还是重新加权奖励、删除完整服务目标，或增加新的动作依赖基线。它们回答不同问题。[`learning.py::update`][S18]；[B01 原生目标][S12]

现有结果没有证明终点信用就是共同差距的原因，本轮也不要求先证明它。选择一个新 B 所需的是一个具体更新定义、合理对照、有限曝光和能改变下一决定的正反读数，而不是预先证明改动成功。仅列出“改信息或信用”还不足以让我选其中某项；我不把这些未定设计填成一个貌似可直接执行的卡。

### 既有记录分析有可用输入，但目前缺少会改变选择的读数

保存的策略和 BCRH episode 文件以及 `grid_readout` 已提供世界配对、失败区、原生分子／分母、违规字段及 20 秒恢复语境。主要 mode 差、同模式算法差和参照差已经在摘要中按总体和分区给出。再做相同均值或显著性计算不会自动产生新的信息／信用干预。[episode 字段样读][S3]、[S4]；[`grid_readout`][S17]

DM 所举“按初始拓扑解释差距”的分析还需要对应的决策前拓扑或动作信息。已读发布构造并不将完整初始拓扑、actor logits、PPO advantage 或全部动作轨迹写入这些 episode 文件；不能凭 `world` 编号或 20 秒恢复状态把它们补出来。20 秒语境也不能充当精确恢复延迟或唯一信用瓶颈。[`rollout` 的 episode 发布字段][S18]；[固定策略入口的发布][S17]

因此不选择一次名义上“便宜”的分析，随后再为缺失输入重开环境、模型或记录框架。这不禁止将来对已有记录提出一个具体、足以改变选择的问题；只是本轮没有选定这样的读数。文档将该选项写为“seconds”是规划性描述，不是已观察的运行费用。[曝光与成本文档][S8]

第三次 recast 也未被选择。不是因为它会触发排序标记，而是本轮没有形成比上述现有问题更明确的新事件、角色、信息、学习干预及原生后果链。一个新标签本身不提供决策价值。

## 五、按真实工作量比较成本，而不是按余额寻找实验

已有最小完整学习比较的一组主工作可写为：

`2 学习臂 × 1 个训练种子对 × 64 轮 × 32 episode × 6 联合决策`，

外加每臂 `64 × 4 PPO epoch × 8 minibatch` 的 2,048 次优化、每臂三个 64-episode 评价点，以及 64 个完整 BCRH 参照 episode。合计每次 4,544 个完整 episode、1,090,560 个 native ticks、两臂共 4,096 次 optimizer step。四 token 动作选择、PPO 和固定 BCRH 内部评分是算法工作，不是为本次咨询附加的验证。[两种子实际计数][S11]；[B01 卡的成本段][S12]；[完整训练／评价程序][S19]

两次有效完整调用实测分别为 388.75 与 306.68 秒 wall，均值 347.715 秒；对应 CPU 为 388.53 与 305.83 秒。它们是现有实现的实际费用，不是一个改变了信息、网络、信用或训练长度的新方法的上界。已有条件投影约 431.17 和 328.55 秒也没有这种保证；更早短检查的 282.61 秒投影曾低估完整运行。故本轮并不声称“再训一次算不动”，而是没有选定值得支付这个完整工作的问题。[两种子 intake][S11]；[上轮完整答复的费用记录][S9]

部署方式评价本身没有训练和优化：四个固定策略 × 两个模式 × 64 episode，再加 BCRH 64 episode，共 576 条完整轨迹；512 个策略 episode 对应 3,072 次联合决策，SAMPLE 消耗 6,144 个 token 抽取，BCRH 有 384 次完整调用，总计 138,240 个 native ticks。机器摘要给出参数位移全为零，BCRH 阶段约 34.905 秒；这些就是本次评价实际支付的工作，不是新的训练样本。[机器摘要 exposure 与 timings][S2]

**费用记录有两个不同计时边界，应并列保留。** intake 记录 runner 完整 wall 约 44.47 秒，外层 `/usr/bin/time` 为 45.69 秒；两者均低于 180 秒。文档的 827.76 秒累计是 `783.29 + 44.47`，其中 783.29 已包含此前不完整 formal01，不能写成仅两次有效训练加本次评价。如果按同一外层完整调用口径，将 intake 所报 45.69 秒与原外层累计相加，则得到 **828.98 秒**；这是据已列数字作出的口径一致化推导，不是新测量，也不在本回复中覆盖原台账。检查链及更早未完整计时的诊断另有范围，不能补零。[新结果遥测段][S1]；[费用文档][S8]；[旧累计分账][S11]

DM 选项中“每臂沿用 B01 完整上限”的表述也不能直接继承。B01 的 2,700 秒是原卡明确选择的**两学习臂、固定参照、必要准备和发布的累计正式总额**，不是每臂各自 2,700 秒；第二种子的 900 秒也在其内。一个真正新对象需要说明自己的完整工作范围，不自动继承或重置余额。运行规范的调查阈值同样不产生额度。[B01 成本与停止边界][S12]；[第二种子卡][S13]；[运行规范一般要求 §1—§3][S23]

本轮没有选中新的实验性调用，所以不为暂停附带 profiling、成本证明、记录重建或新基线训练。新路径的单位费用继续是未知，而非零；这不妨碍现在形成方向选择。上述时间边界差异也不需要通过再跑一次来解决。

## 六、什么改变后可以重开，以及始终保留什么

重开所需的是**下一问题的决策价值发生具体变化**，而不是先补齐一般证明。以下是重新考虑的充分理由类型，不是本轮同时选择的多个任务，也不是额外验收层。

一个新的学习提案，可以从现有可复用路径明确选择一个信息、表示、信用或优化干预，并交代它怎样沿“成员损失 → 幸存实体和角色责任 → 可用信息 → 物理动作或信用 → 实际学习曝光 → 完整原生后果”发挥作用。它应有真正训练的合理对照、匹配且披露的信息／工作范围，并说明正向、混合或反向结果分别改变什么后续选择。**不要求先有阳性 pilot、精确上界、唯一历史根因，或已经证明其改善回报。** 有限实现准备可以属于新的 B；不能仅以“尚未实现”否定一个意义清楚的研究问题。[证据规范 §11.8—§11.9][S21]

对于不改变当前方法的 seed 或训练预算跟进，则应出现一个明确的新决策用途：例如为何对当前量级差异取得更精确描述会改变方法取舍，或为何一次预定的预算比较能区分有实际价值的学习阶段，而不是只期待最终转正。所需精度、反向结果及原生服务代价应与那个用途对应；无需将 0.10、全正号或统计显著变成通用门槛。本轮没有为这样的跟进划定新 seed、额外轮数或自动续跑权限。

若已有材料出现一个直接威胁奖励、信息、训练或主要测量的具体事实，它可以触发只针对依赖路径的修复或明确再分析。当前 HMAC／SIGSEGV 未唯一定位仍被保存；它们既不被两次成功运行“治愈”，也不自动阻塞所有可信新路径。未来不相关的新方法不必先重放这些故障的全部历史。[两种子完整性限制][S11]；[证据规范 §11.8.7][S21]

原 B01 两个种子的初始／中点／终点、全部原生指标、DIRECT 活动、参数和 checkpoint、完整失败分账继续保留；本次八个策略／模式单元、BCRH 配对、四个主差及其分区行也继续保留。旧跨 N 负面、R09 无效包、有限特权 witness、R03 未完成和 E01 工程停止均不改判。当前同分布学习不能唯一解释旧跨 N 失败，固定策略评价不能变成新的学习证据。[方向历史边界][S15]；[上轮完整答复第六节][S9]

不据此产生稳定 MAPR 优势、等价性、BCRH 最优或严格同信息 headroom、普遍执行方式无效、跨平台／重复 churn／UAV 泛化或安全部署主张。已报告的无违规只属于所观察的有限 episode。

**因此，眼下没有下一实验或分析对象；当前比较族暂停，部署方式子问题结束，成员变化后的共享学习问题保留为开放研究问题。** 不改变 Portfolio 的 ACTIVE／PARKED、priority、容量、融合或注册，不增加或重置已有两次 recast。科学分支暂停不等于把方向改为 PARKED，也不授权本节点重排队列。现有 DM 在已有 intake 中记录这一范围即可；不新增规范、审批或独立验证服务。[决策阶梯][S24]；[Portfolio 记录][S16]；[普通工程边界][S22]

## 七、实际读取、来源及未核验范围

科学材料统一从 `CartmanFatass/My-paper-code` 的固定提交 `04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111` 经连接的 GitHub 读取。下表给出实际范围；选段读取不等于全文审计，尤其不声称逐行重新计算了 512 条策略轨迹或全部 11,000 余行摘要。此次采用已接受的完整结果，同时检查机器计数、关键原生统计、程序测量定义和上述具体范围差异。底层未列出的模型、训练函数或远端 checkpoint 没有被另外打开或执行。

表中 D 为 `docs/research/candidates/variable_n_fleet_churn/`，E 为 `experiments/candidates/variable_n_fleet_churn_n7_direct_b01/`，P 为 D 下的 `pro_packets/20260906_post_depmode_convergence/`。

| 实际读取来源 | 范围 |
| --- | --- |
| [D/VNFC_N7_B01_DEPLOYMENT_MODE_EVAL_RESULT_INTAKE_20260905.md][S1] | 全文 |
| [D/evidence/b01_depmode_formal_20260905_01/summary.json][S2] | 1—480、1020—1260、10800 至末尾；配置、参数、曝光、部分均值／对照及结尾主差、计时 |
| [同目录 evaluation_episodes.json][S3] | 1—122 行，检查记录字段及前两条完整 episode；未全文复算 |
| [同目录 bcrh_episodes.json][S4] | 1—121 行，检查相应参照字段及前两条完整 episode；未全文复算 |
| [D/VNFC_N7_B01_DEPLOYMENT_MODE_EVAL_SCIENCE_CARD_20260905.md][S5] | 全文 |
| [D/VNFC_N7_B01_DEPLOYMENT_MODE_EVAL_CM_RECORD_20260905.md][S6] | 实现、冻结参数、测量语义、局部验证与成本段；长响应末尾执行命令未作完整审阅 |
| [P/EVIDENCE_AND_OPTIONS.md][S7] | 全文，作为可质疑提案 |
| [P/EXPOSURE_AND_COST.json][S8] | 完整 JSON，区分文档推导与新测量 |
| [D/pro_packets/20260905_b01_two_seed_convergence/archive/RESPONSE.md][S9] | 全文，分窗口补齐 |
| [D/VNFC_B01_TWO_SEED_CONVERGENCE_INTAKE_20260905.md][S10] | 全文 |
| [D/VNFC_N7_DIRECT_RETURN_B01_TWO_SEED_RESULT_INTAKE_20260905.md][S11] | 全文 |
| [D/VNFC_N7_DIRECT_RETURN_B01_SCIENCE_CARD_20260905.md][S12] | 1—135 行，问题、处理、曝光与完整预算 |
| [D/VNFC_N7_DIRECT_RETURN_B01_SEED02_CARD_20260905.md][S13] | 全文 |
| [D/VNFC_CONTROLLER_HEADROOM_A_RECON_R01_INTAKE_20260904.md][S14] | 全文，历史 bracket 与解释边界 |
| [D/DIRECTION.md][S15] | 1—180 行，当前学习问题、既有决定与相关历史 |
| [docs/research/portfolio/PORTFOLIO.md][S16] | 开头和方向表，含 VNFC 行；未用陈旧执行文字覆盖新结果 |
| [E/deployment_mode.py][S17] | 全文，分窗口补齐 |
| [E/learning.py][S18] | 全文 |
| [E/experiment.py][S19] | 全文，分窗口补齐 |
| [E/native.py][S20] | 全文；不等于已读其继承的全部 R09 依赖 |
| [docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md][S21] | 350 行至末尾，含 §11.4、§11.7、完整 §11.8—§11.9 |
| [docs/project/ENGINEERING_SCOPE_SPEC.md][S22] | 1—100 行，一般规则及预算 |
| [docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md][S23] | 一般要求 §1—§7 及 §8 开头；不以历史 E01 附款给后继分配资源 |
| [AGENTS.md][S24] | 1—170 行，决策、排序及委托 |
| [docs/project/GITHUB_RESEARCH_COLLABORATION.md][S25] | 全文 |
| [P/ISSUE_SNAPSHOT.json][S26] | 完整 JSON；它是准备时的固定快照 |

此外，在本轮写入前，于 2026 年 9 月 6 日经连接器直接读取了 [Issue 1 正文][I0]及当时全部三条评论：[原工具问题][I1]、[协作试点摘要][I2]、[上一轮交付通知][I3]。连接器没有返回本次读取的精确时分秒；快照的 `2026-09-06T10:22:17+00:00` 是快照作者的读取时间，不冒充本节点观察时间。Issue 中“尚无正式训练结果”和方向记录中的旧暂停属于更早状态，不能覆盖本轮固定版本的完整结果；没有跟随其中未列出的旧链接取得新的科学输入。

没有列明路径、固定引用或连接器访问缺口。仍未知的是总体训练变异、未检验学习干预的效果与成本、BCRH 逐字段信息差异、旧故障根因，以及四个固定策略以外的部署收益。它们限制各自相关主张，不妨碍形成这个最小暂停决定。本次咨询未新增模型、环境步骤、训练、优化或评价，也未执行任何仓库代码。[文档性曝光行][S8]

[S1]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/research/candidates/variable_n_fleet_churn/VNFC_N7_B01_DEPLOYMENT_MODE_EVAL_RESULT_INTAKE_20260905.md
[S2]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/research/candidates/variable_n_fleet_churn/evidence/b01_depmode_formal_20260905_01/summary.json
[S3]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/research/candidates/variable_n_fleet_churn/evidence/b01_depmode_formal_20260905_01/evaluation_episodes.json
[S4]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/research/candidates/variable_n_fleet_churn/evidence/b01_depmode_formal_20260905_01/bcrh_episodes.json
[S5]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/research/candidates/variable_n_fleet_churn/VNFC_N7_B01_DEPLOYMENT_MODE_EVAL_SCIENCE_CARD_20260905.md
[S6]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/research/candidates/variable_n_fleet_churn/VNFC_N7_B01_DEPLOYMENT_MODE_EVAL_CM_RECORD_20260905.md
[S7]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/research/candidates/variable_n_fleet_churn/pro_packets/20260906_post_depmode_convergence/EVIDENCE_AND_OPTIONS.md
[S8]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/research/candidates/variable_n_fleet_churn/pro_packets/20260906_post_depmode_convergence/EXPOSURE_AND_COST.json
[S9]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/research/candidates/variable_n_fleet_churn/pro_packets/20260905_b01_two_seed_convergence/archive/RESPONSE.md
[S10]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/research/candidates/variable_n_fleet_churn/VNFC_B01_TWO_SEED_CONVERGENCE_INTAKE_20260905.md
[S11]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/research/candidates/variable_n_fleet_churn/VNFC_N7_DIRECT_RETURN_B01_TWO_SEED_RESULT_INTAKE_20260905.md
[S12]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/research/candidates/variable_n_fleet_churn/VNFC_N7_DIRECT_RETURN_B01_SCIENCE_CARD_20260905.md
[S13]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/research/candidates/variable_n_fleet_churn/VNFC_N7_DIRECT_RETURN_B01_SEED02_CARD_20260905.md
[S14]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/research/candidates/variable_n_fleet_churn/VNFC_CONTROLLER_HEADROOM_A_RECON_R01_INTAKE_20260904.md
[S15]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/research/candidates/variable_n_fleet_churn/DIRECTION.md
[S16]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/research/portfolio/PORTFOLIO.md
[S17]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/experiments/candidates/variable_n_fleet_churn_n7_direct_b01/deployment_mode.py
[S18]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/experiments/candidates/variable_n_fleet_churn_n7_direct_b01/learning.py
[S19]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/experiments/candidates/variable_n_fleet_churn_n7_direct_b01/experiment.py
[S20]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/experiments/candidates/variable_n_fleet_churn_n7_direct_b01/native.py
[S21]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[S22]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/project/ENGINEERING_SCOPE_SPEC.md
[S23]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md
[S24]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/AGENTS.md
[S25]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/project/GITHUB_RESEARCH_COLLABORATION.md
[S26]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/research/candidates/variable_n_fleet_churn/pro_packets/20260906_post_depmode_convergence/ISSUE_SNAPSHOT.json
[I0]: https://github.com/CartmanFatass/My-paper-code/issues/1
[I1]: https://github.com/CartmanFatass/My-paper-code/issues/1#issuecomment-5555371099
[I2]: https://github.com/CartmanFatass/My-paper-code/issues/1#issuecomment-5555521310
[I3]: https://github.com/CartmanFatass/My-paper-code/issues/1#issuecomment-5556114589
