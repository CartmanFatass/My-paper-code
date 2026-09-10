**选择一次新的、原比较不变的独立训练配对 B/EXPLORE，暂不 PARK 当前开场保持段 residual-MC 家族。** 这一次续行的问题是：在不改损失、任务、预算和最终 sampled 评价的情况下，另一套独立从头训练所得策略，是否仍只给出所选尺度内的包差，还是出现实质正差或反向损失，从而改变继续研究这个固定包的理由。选择的是一个新增配对，不是寻找阳性 seed，不是系数调整，也不是更大的重复计划。B01 仍是 **WITHIN、绝对 MEI=0.01、一个独立训练配对**；本次不把它改判成功或统计等价。[^card][^result][^brief]

我不同意 DM 此时暂停这个具体家族的建议，但认为那是有根据的竞争选择。使我选择再看一对的，是三件事的结合：已有完整、非零且比较意义明确的干预；其原生点差为正而尚未达到所选尺度；在训练随机性这一层只有一个观察，同时已有可复用的实现和实际配对进程成本。任何一件事单独都不构成继续投入的充分理由。这里购买的是一次有限的跨训练实例观察，不是用“还不能排除有效”支持无穷重试，也不是声称两对就能判明总体效应。[^result][^intake][^facts]

**这是已接受机制内部的一次有限续行，不是第三次 RECAST。** 保留 recasts=2、旧 D6 action-choice／source-countdown-search 家族的 PARK，以及现有 Portfolio 生命周期、优先级和争用顺序。本次没有新家族、C 提升或 UAV 进入决定；只选下文这一项新 B，其数值 master、实际卡和执行绑定由同一 DM 在新结果不可见时落实。Pro 不运行它。[^direction][^brief]

## B01 已经回答了什么

原卡第 5 节的 WITHIN 行明确表示：在包含两端的 ±0.01 内，没有所选尺度上的改善理由去重复不变惩罚；小正差和更低残差不是成功。这一原有结果读法与一对预算的结束都保留。原卡、原完整响应和原 intake 没有把它定义成整个 residual 家族的失败，也没有把 B 变成消费一次后永不允许新问题的 C 对象。[^card][^applied][^intake]

本次直接读取的原 E0 给出以下完整最终 sampled 结果，非重新拟合或重新抽样的结果：

| 配对差 | 均值 | 条件评价 SE | 负差 episode |
| --- | ---: | ---: | ---: |
| RESIDUAL-MC − MLP-MC | +0.0067374074558942025 | 0.0055965465359414865 | 14/32 |
| RESIDUAL-MC − H | +0.007086659468526168 | 0.011858107098025586 | 15/32 |
| MLP-MC − H | +0.00034925201263196577 | 0.00934944486292681 | 18/32 |

三个平均 J 分别为 0.1549340414324733、0.14819663397657912 和 0.14784738196394714。全部 96 个最终 J 非负，但“没有负 J”不等于处理优于比较器：上表的所有负差仍然存在。两个 learner 的平均值均高于 H，却都没有在对 H 的差上达到 0.01。H 是已达到的参考，不是最优值；调优同信息 headroom 仍缺失。这里没有建立稳定、实质的可用时长控制。[^result][^intake]

原 E0 的 COMPLETE、空 limits、完整 primary／H、零 partial steps 与技术接受记录相符。每臂完成 512 个训练 episode 和 1,024 次 Adam；每臂实际有 1,500 个合格保持段 pair，处理臂四 epoch 共计算 6,000 个残差项，没有零 pair rollout。244 个 rollout 各有六个 pair，另 12 个各有三个。这里的 1,500 是时间段样本数，不是独立训练实例数；不能用它扩大 n，也不能把此次 WITHIN 解释成没训练、空处理或没有合格保持。[^result][^intake]

两臂均为 66,441 参数，总位移／初始 L2 为 0.4964386918799212 和 0.5153558478035093。它们证明来源 recipe 确实发生了学习更新，不能证明新增残差产生了有益控制。合格 pair 总数相同也不意味着两臂轨迹、动作或梯度相同。原训练 d4 数为 1,383/2,560 和 1,361/2,560，最终 d4 频率为 0.5625 和 0.54375；不据此挑选保持更多的臂或另设事后指标。[^result][^intake]

## 为什么再看一个训练实例，而不是现在暂停或改损失

**支持暂停的最强理由**是：B01 正好没有提供原卡选定尺度上的重复依据，完整 MLP-MC 仍有竞争力，而且没有哪项已测观察把梯度抵销、共同裁剪、后继噪声或遗漏历史定位成应修复的缺陷。继续执行一个不变比较，可能只再得到一次小差，不能保证解决不确定性。源实现已经被接受、进程很短，也不能把科研时间、整合工作和机会成本视为零。[^card][^intake][^brief]

**反对现在暂停的最强理由**不只是“n=1”。这是在完整原生 learner 上、明确非零处理之后得到的正点差，而不是只有预测损失更好；它离所选尺度并非已经被一个精确负结论隔开。现有条件 SE 也不能成为排除有用训练总体效应的工具，因为它根本不估计训练总体不确定性。再加上已有 323.02 秒完整科学配对进程的实测锚点，一次相同规模的新训练配对，是当前能增加尚未观察到的训练实例维度、又不引入新干预解释的最小实证延伸。[^result][^intake][^foundations][^empirical]

我的判断是，这个有限增量目前值得付出。具体决策价值在于：如果第二实例仍在 ±0.01 内，就多了一份没有所选尺度改善的观察，暂停这个固定包会更有依据；如果出现低于 −0.01 的差，则对不稳健或有害的担忧得到直接包级反例；如果出现大于 0.01 的差，则首次得到该尺度上的本地原生信号，值得在保留 B01 WITHIN 的前提下重新评估后续投入。这些结果都可能改变建议，不是只有阳性才能被接受。两实例仍不能排除评价噪声或可靠估计训练效应分布，因此这不是一个承诺给出稳定优劣结论的试验。[^methods][^brief]

这也明确了本次相对于旧读法新增的理由：**B01 没有通过原效果尺度；本次仍选择一次以跨训练实例变动为问题、以已测工作量为成本依据的独立重复。** 不是把原小正差重新命名为成功，也不是把原卡改成“只要大于零就再跑”。当前规范 §§6.1、11.8.2–3 允许有明确复制目的的新 B，同时不赋予无限算力。规范只是允许这项选择，并没有强迫所有 WITHIN 对象都继续；这是针对当前具体包的局部投入判断。[^card][^methods]

不选择改系数、改裁剪或改后继梯度，是因为现在最有价值的新增观察仍是同一个包在另一次真实学习后的结果。若现在同时改损失和训练来源，新的差无法与 B01 的实例变化分开解释；而当前没有直接证据优先指向哪一种修改。未定位缺陷不禁止探索性修改，但在本次仅能选择一对的范围内，我不为此增加另一项未测假设。也不增加旧 checkpoint 的评价：那只能补充同一拟合策略的执行观察，不能增加独立训练实例，且不在给定范围内。[^learner][^study][^foundations][^empirical]

## 基础知识怎样限定这一选择

FOUNDATIONS §4 区分表示能力、带条件的理论关系和有限学习结果。因此，完整 MLP 能表示有关关系并不能证明当前预算已经学会它；反过来，残差具有清楚的代数式也不能保证它改善 PPO 后的策略。FOUNDATIONS §6 和实证专题进一步区分完整包比较、组件归因、训练实例与条件评价。这些区分实际改变了本次设计：保留整个算法包不变，新增一个从头训练实例，不用更多 episode 冒充更多 seed，不新增归因控制来替代原生性能问题。[^foundations][^empirical]

新配对后，两次训练结果的离散仍同时含有训练生成过程和有限评价的变动；仅看两个端点不能干净分解这两部分。可以描述“两个独立训练配对下观察到的差”，不能声称已经估准训练方差，或把不同 seed 编号本身当作独立性证明。独立性要由新的初始化、训练随机流和 reset 来源，以及不复用旧权重／数据的生成过程来落实。[^empirical][^methods]

端到端正差也只属于这个完整 residual-MC 包。它不会独自排除一般正则化、裁剪改变、数值优化、样本后继噪声或 critic 不含 actor 历史的解释。这里放弃的是独有保持／semigroup 因果归因及稳定总体优势，不是对 reward、信息访问、真实训练和 primary 的必要检查。无需显著性、先有阳性、精确上界、调优 headroom 或新颖性证明作为这一次 B 的前置条件。[^methods][^empirical]

## 选定新 B 的精确定义

将本次唯一新增对象称为 **SCDMP-NATIVE-HOLD-RESIDUAL-B02：不变比较的单个独立训练配对**。这个名称用于区分已完成的 B01，不是新的损失家族。它只增加一次从头训练的实例，不改变下列学习语义。数值 master 尚未分配；同一 DM 在新结果不可见时一次明确分配、记录并固定，不能使用 B01 的 8201 或按表现挑选、替换 master。[^brief][^facts]

**处理和比较器。** 两侧继续使用相同 recurrent duration actor 和完整 136→128→128→1 tanh critic，各 66,441 参数。MLP-MC 保持原 `policy_loss + 0.5*L_MC − 0.01*mean_entropy`；RESIDUAL-MC 保持 `policy_loss + 0.5*(L_MC + 1.0*L_seg) − 0.01*mean_entropy`。系数 1 不调，不加 gate、head、参数、target network 或第三 learner。[^card][^learner]

L_MC 是每个两-episode rollout 全部 512 行的完整 MC MSE，gamma=1、无 terminal bootstrap。每条实际 episode 的 t∈{1,2,3}，只要该行已存 remaining-hold 有任一 agent 非零，就取一个团队标量 (t,4) pair。R_t:4 只含 r_t…r_3，不含 r_4；V_4 是同一 episode 的 t4 新动作前输入在当前 epoch 的预测。L_seg 对这些实际 pair 的 `(V_t−R_t:4−V_4)^2` 取均值，无 pair 为零。两个端点均保留梯度，不按 held-agent 数复制团队样本，不跨 episode 配对，也不按已见回报或更新后策略重新选择端点。[^card][^learner]

原 `segment_pairs`、`residual_loss`、`update` 的实现已经直接表明这些语义：remaining-hold 列为 119、123、127、131、135；同一完整 batch 的 critic 输出供两端使用；原 rollout 的 MC target、采集时 value 形成的归一化 detached advantages，在四 epoch 内保持不变；总 loss 仍经过一次 backward、原联合 norm clip 和一次 Adam。新对象不改变这条路径。[^learner]

**任务与动作后果。** 保持五个固定 UAV、50 uniform 用户、256 primitive steps、原 native motion/channel/service、团队奖励、reset／constructor 和终止规则。t0 才选择 d1/d4；t1–3 可有 remaining hold，t4 恢复 primitive 反馈。未保持 agent 仍能行动，各 actor GRU 持续观察。critic 不新增 actor 隐藏历史或刚选动作信息；没有 roster、时长权限、环境或信息集变化。[^card][^brief]

实际作用链仍是原生保持运动／服务回报和存储输入 → critic 的 MC 加双端残差梯度 → 当前联合裁剪及以后 rollout 的 baseline → 原有 detached normalized advantages 和 compound PPO → 随后局部 sampled 动作 → 完整 native return。新增残差没有直接可微地进入 actor 参数；共同裁剪仍可立即改变 actor 更新尺度，未来 baseline 也可改变后续优势。不能为了“公平”把这条已接受的间接路径删掉。[^learner][^card]

来源 intake §§3–4 的奖励路径代数仍适用：G_t=R_t:4+G_4，故双端残差等于 e_t−e_4。它不是用 G_4 重写 MC，也不是把 V_4 stop-gradient 后的半梯度 TD。该来源的已有文献检索把它归为已知 sampled residual-gradient fitting；本次只引用这项明确归属的来源判断，没有访问其本地文献库或原论文。段内不是恒定联合动作，critic 输入也未被证明充分 Markov；单次实际后继不提供平方期望 Bellman 残差的无偏梯度保证。[^source]

**训练、随机性和评价。** 每臂 512 个完整训练 episode，256 个两-episode rollout，每 rollout 四 epoch，共 1,024 次真实 Adam；保持 chunk32、lr3e-4、PPO clip0.2、joint clip0.5、agent_compound、CPU FP32/thread1。不改变训练长度，不增加 replay，不选择中间或最佳 checkpoint。[^card][^study]

新的 master 记为 s，沿来源 b=100000×s 的域安排：初始化 b+11，训练动作／时长 b+21、b+22，训练 reset 从 b+1000 起，最终 reset 从 b+2000 起，最终动作／时长从 b+3000、b+4000 起，并保持原 episode 索引和 constructor 语义。两臂由共同初始化模板开始，但持有私有 generator 对象；它们不能互相消耗可变流。新配对不复用旧权重、旧训练数据或旧随机流状态。配对不承诺相同 on-policy 轨迹或保持暴露，也不允许强制相同动作来取得它们。[^study][^empirical]

只评价各自最终 sampled 策略的 32 个 episode，再在同样 32 个 reset 上评价 H；H 不是第三个 learner。保留原 J=完整团队总回报/256，主要量为新配对的 Δ₂=mean(J_RESIDUAL,e−J_MLP,e)。所有 episode、两项 J−H、条件 SE、负差数量、实际 pair／残差项和训练／评价计数均保留。原 B01 的 Δ₁ 只作为已完成的历史同比较端点，不重新评价它，不池化别的 gate 或 T/G 试验。[^card][^study][^result]

## 新观察的有限读法与停止边界

绝对 MEI 仍为 0.01。任务、J 量纲和比较目的均未变化，没有理由追着 B01 降低尺度。0.7/50=0.014 仍只解释原尺度的服务覆盖量纲，不保证额外服务人数，也不构成 H 上界。[^card]

| 新配对完整且可信的结果 | 对当前家族的局部读法 |
| --- | --- |
| Δ₂>0.01 | 首次在这个尺度上得到一个 residual-MC 包级正信号。与 B01 WITHIN 并列，可在全结果 intake 后讨论是否值得进一步投入；不能写成两次 UP、稳定优势或自动分配第三配对。 |
| −0.01≤Δ₂≤0.01 | 得到第二个未达到所选尺度的实例。我的建议将转向暂停这个不变开场 residual-MC 包，不追加一个以寻找阳性为目的的第三配对；不宣称两方法等价或所有残差方法失败。 |
| Δ₂<−0.01 | 新实例实质偏向完整 MC。与 B01 的小正差一同作为跨实例表现不稳健的包级警讯，建议暂停该固定包；不能据此证明训练总体均值为负，也不自动改系数。 |
| learner 主比较不完整 | 不给依赖缺失的完整预算包作性能判断。保留独立可信的已完成行、计数和异常；不换 seed 补齐。H 缺失只限制其相关结论，只要 learner 主比较独立完整，就保留后者。 |

这是一项新 B 的事前结果解释和下一建议，不追溯替换 B01 的原规则，也不是 C 的显著性检验或消费规则。下一 seed 不需要正号，负号和零附近结果都能提供选择价值；无论哪一行，本次都没有自动后继。[^methods]

两个 learner 相对 H 的差须与 Δ₂ 并列，不能选择性隐藏。若任一臂低于 H，收窄可用控制表述；若两臂都低于 H，即使 Δ₂>0.01，也只是比本次较弱的完整 MC 更好，并未建立有用时长控制。B01 两项对 H 均未达 0.01 的事实继续保留。拟合、残差下降、参数移动或更多保持不能救原生损失。[^card][^intake]

若新配对没有实际非零残差暴露，无 pair 处理仍是合法执行事实，但不能称为检验了非零惩罚效果；如实限定结论，不强制时长、不替换 population、不重跑补暴露。少量暴露也不变成发布门槛。按实际 pair 数归一化，使稀疏行不等于同样小的梯度权重；本次不据数量把处理判为弱干预或已定位失败原因。[^learner][^source]

最小分析工具就是沿用源码 `primary_from_rows` 的最终配对差统计，再把 Δ₁、Δ₂ 及各自条件 SE／H 差并列。若同一 DM 给出两实例等权平均，应明确是保留两个完整端点的描述，不改变每个原对象的标签；不能挑较好者，也不能把 64 个评价 episode 当作 64 次训练。两实例间 SD 至多是很不稳定的描述，不能消掉评价噪声、充当纯训练方差或支撑稳定优势。无需为此新增 bootstrap 服务、框架迁移或额外评价调用。[^study][^methods][^empirical]

## 已知工作量、未知成本和相称接受

这一次新增配对的主乘数保持为：2×512×256 训练加 3×32×256 最终评价，合计 **286,720 native team steps、2,048 次 Adam、96 个最终评价 episode**。每臂训练 131,072 步；两侧各一个新 learner，新增独立训练单位为一对。每训练臂至多 1,536 个合格 pair，处理臂四 epoch 至多 6,144 个 scalar 残差项。没有候选、联合动作、轨迹、controller 或 solver 搜索，没有旧权重评价、先行 A、额外训练流或中间模型选择。[^facts][^card]

没有新的损失计算类型：延续的处理臂继续承担原双端残差的索引、运算及梯度贡献；完整 batch critic 输出仍可复用，不增加网络 forward、单独 backward 或 optimizer 调用。比较器继续统计合格 pair 而不施加残差。这里是“不比 B01 多一种算法工作”，不是新配对零成本；两套从头训练及评价的完整成本都会再次发生。[^learner][^study]

每臂来源成本式为 131072×c_collection + 1024×c_update + 8192×c_eval + 完整开销，第二臂另有 8192 个 H 步及配对发布。B01 的完整科学配对进程 wall=323.02 秒、CPU=321.77 秒、peak RSS=558232 KiB 是实际规划参考，不是新 seed 的上界，也不是完整工程工时。原内部配对计时 304.5700655610417 秒不含整个外部边界；精确完整逐臂成本仍未测，不能把内部臂计时冒充它。整个已测配对进程小于任一 1800 秒臂上限，支持来源的保守 cap 判断，但不保证新执行同样如此。[^result][^facts]

本次选择不依赖假定“只有几分钟所以成本可忽略”，而依赖已存在可复用实现、无需新诊断／搜索维度，以及这一单配对确实增加一个不同层级的观察。新增文档、绑定、必要检查和 collection 的工作仍存在且未完整计价；不声称已算出精确的信息价值／成本比，也不做额外成本实验。[^brief][^engineering]

保留 **1800 秒/臂、3600 秒/完整逻辑配对**，覆盖实际执行的邻接启动、导入初始化、训练、最终评价、必要检查、publication/readback 和 exit，第二臂含 H 与配对输出。不得切片重置时钟、借第二臂额度掩盖第一臂超限或用不含 exit 的计时认证完整上限。超限或主要依赖失败就停止此次选定执行，保留已完成事实；不能自动重试、调参或增加 seed。独立可信的回报与真实 cap breach 分开陈述，工程异常不是科学负号。[^card][^methods]

同一 DM 按当前工程规范负责技术接受及独立的科学 intake；复用已接受学习实现和既有有效检查。新对象需要正确的卡／master／输出绑定，不能把新结果写成旧 B01 或覆盖其结果。只对实际改变的绑定行为和主要输出做相称核对；若实际 diff 涉及科学语义、numerics、RNG、recurrent state 等高风险路径，则按 §7.3 进行适用的独立 review。单纯换到预先固定的新 master 不自动要求重做整个算法或 native suite 的历史验证。原十七项检查、synthetic smoke 和已接受 review 是来源接受事实，我没有在本咨询重跑它们。[^intake][^engineering]

工程 scope §4 不需要新增机械设施。普通研究源码、runner 和测试预算继续适用；不新增统计服务、字节守卫、重试层、全历史回放或一个通用 Pro 启动关卡。未来实际运行仍使用原 remote-first wsl_4070、CPU FP32/thread1、已发布确切源码、detached 监督和紧邻运行的实际节点物理／有效可用内存均至少 4 GiB 的 admission。新 allocation、source 和 handle 由同一 DM 在执行前落实；本次没有新 handle。[^brief][^facts][^engineering]

原 E0 的零科学工作 shell 提交纠正、两个被 runtime policy 拒绝删除的测试 scratch 目录，以及 summary 的 resources_unmeasured 标签均保留。它们不被本次解释成残差失败，也不要求为本次新问题重现或绕过旧清理限制。外部 wall／CPU／RSS 是它们各自范围内的可信观察，不意味着资源记录每一项都齐全。[^result][^intake]

## 最终家族边界与来源范围

**最终决定是：当前 opening-held residual-MC 家族仅通过上述一个不变比较的新独立训练配对继续，拒绝此时立即 PARK 的建议。** 这不否认 B01 没有达到 MEI；它让下一次有限投入专门增加一个训练实例，而不添加新的损失或归因问题。若这个单配对之后仍没有足够局部理由，暂停的最小单元就是原生开场 t1–3→t4、完整 MC 锚定、系数 1 的当前包；不是所有 residual-gradient、全部 duration 学习或整个 SCDMP。未来任何有具体原生动作／credit 理由的新问题仍需按其实际范围提出，不能靠先找阳性、显著性、精确上界或昂贵诊断作为隐含重入门槛。[^brief][^methods]

旧 D6 家族依其原决定维持 PARK；本次不使用 A01 的 R7=0 或 A02 的 321-mission 人口失败重新搜索来源，也不把 VSPC1 gate 或 UCOPE T/G 的历史结果并作 residual 配对。已接受第二次 recast 不被再次计数，没有生命周期、优先级、capacity、C 或 UAV 进入修改。完整新裁决由同一 DM intake，随后按当前规范准备这一对象和执行绑定，Root 沿既有路线集成；没有额外 owner 确认或 Portfolio 实现批准层。[^direction][^intake][^brief][^engineering]

这里没有稳定优势、统计等价、唯一保持／semigroup 因果、新颖性、期望 Bellman 保证、TD／gate 优势、跨任务迁移、安全或部署结论。两个实例也不会自动取得这些结论。最小下一科学观察只有新配对的完整最终 sampled 原生 Δ₂，连同两项对 H、所有负差、条件评价不确定性、真实非零暴露和完整成本。

本次通过 GitHub connector 访问了清单中的全部十四条路径，分别使用下列引用标明的有效完整提交，没有以一个统一新 SHA 替换原卡、结果或实现。对 E0 直接读取了原规则、两臂／总计数、全部三臂最终 J 与三组配对差、支持和资源／接受字段，并查看了 final_episode_rows 的相关片段；没有逐行重做全部训练或轨迹审核、checkpoint 解串或原 CM 的技术验证。已应用的原 RESPONSE 在本对话此前按相同不可变提交完整读回，本次复用其全文并重新核对开头选择／recast，未重开旧交付争议。没有决策关键路径的访问缺口。

当前知识材料只使用被指定的 FOUNDATIONS §§4、6 和实证专题来限定推断；当前规范只采用 TASK 明列的适用章节，不借无关对象的例外改变本比较。P56 文献分类引用的是其已披露 reconnaissance，没有另访问原论文、本地文库或未列入清单的链接。交付分支和 Issue 的读取只核实交付，不提供新科学输入。本咨询没有执行代码，没有模型／环境构造、native／synthetic steps、训练、评价、optimizer、replay、profiling、support search 或新科学调用；不存在本次 learner 位移。

[^card]: [docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_NATIVE_HOLD_RESIDUAL_B01_SCIENCE_CARD_20260909.md](https://github.com/CartmanFatass/My-paper-code/blob/5d52c5e5bed047e8e32fde575952133a7817b9d2/docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_NATIVE_HOLD_RESIDUAL_B01_SCIENCE_CARD_20260909.md)，§§1–7，特别是 §3 原 loss、§4 RNG／最终评价、§5 WITHIN 原行、§§6–7 预算和停止。

[^result]: [docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_NATIVE_HOLD_RESIDUAL_B01_RESULT_EVIDENCE_20260909.json](https://github.com/CartmanFatass/My-paper-code/blob/e5ed770301e8f5bac9fd77063edd24bee550fb5f/docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_NATIVE_HOLD_RESIDUAL_B01_RESULT_EVIDENCE_20260909.json)，rule_verbatim、rule_reading、summary.arms/counts/primary/limits/status、training_summary、final_episode_rows、process_resources、cost_scope、collection_checks、deviations。机器观察引用原 E0，不是本次重算。

[^intake]: [docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_NATIVE_HOLD_RESIDUAL_B01_INTAKE_20260909.md](https://github.com/CartmanFatass/My-paper-code/blob/40b27ad1862c4c3201ce1b073377d587f3fc715c/docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_NATIVE_HOLD_RESIDUAL_B01_INTAKE_20260909.md)，§§1、3–8，原 WITHIN／无后继 allocation、全部反证、独立单位、技术接受和成本的来源归属。

[^brief]: [docs/research/candidates/semigroup_consistent_duration_model_policy/pro_packets/20260910_post_b01_convergence/SCIENCE_BRIEF.md](https://github.com/CartmanFatass/My-paper-code/blob/a1d06fadc6a6875a1d52a7b318a809150486f156/docs/research/candidates/semigroup_consistent_duration_model_policy/pro_packets/20260910_post_b01_convergence/SCIENCE_BRIEF.md)，§§1、3–7；DM 暂停建议与保留的单配对备选，不是预先形成的方向决定。

[^facts]: [docs/research/candidates/semigroup_consistent_duration_model_policy/pro_packets/20260910_post_b01_convergence/PREPARATION_FACTS.json](https://github.com/CartmanFatass/My-paper-code/blob/a1d06fadc6a6875a1d52a7b318a809150486f156/docs/research/candidates/semigroup_consistent_duration_model_policy/pro_packets/20260910_post_b01_convergence/PREPARATION_FACTS.json)，accepted_B01、prospective_one_pair_counts_not_allocated、actual_consultation_exposure、machine_exposure_line、measured_historical_exposure_line；未来计数不是已经发生的运行。

[^learner]: [experiments/candidates/scdmp_variable_k/native_hold_residual_b01/learner.py](https://github.com/CartmanFatass/My-paper-code/blob/7d0fc9d0091e046617493a1b23bbbf07297821cf/experiments/candidates/scdmp_variable_k/native_hold_residual_b01/learner.py)，R_COLUMNS、segment_pairs、residual_loss、update；直接读源码，未导入或执行。

[^study]: [experiments/candidates/scdmp_variable_k/native_hold_residual_b01/study.py](https://github.com/CartmanFatass/My-paper-code/blob/7d0fc9d0091e046617493a1b23bbbf07297821cf/experiments/candidates/scdmp_variable_k/native_hold_residual_b01/study.py)，Config、Deadline、primary_from_rows、checkpoint_identity、run_pair，训练／final sampled／H、私有 RNG、计数和发布读回。

[^source]: [docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_NATIVE_RETURN_COMPOSITION_P56_SOURCE_INTAKE_20260908.md](https://github.com/CartmanFatass/My-paper-code/blob/21a801279bd449c09907f5cf040efa693ae345a3/docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_NATIVE_RETURN_COMPOSITION_P56_SOURCE_INTAKE_20260908.md)，仅 §§3–4：误差差代数、半梯度／双端残差／gate 区分、间接 actor 路径、已有文献检索的实际覆盖和局限。

[^methods]: [docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md](https://github.com/CartmanFatass/My-paper-code/blob/4e8ce22f5263a4ebbf096cca6c4af225a0559831/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md)，适用 §§4、5.2、6.1、11.4、11.7–11.10；独立训练、复制目的、问题／成本校准、原结果保护及失败依赖解释，不采用无关对象例外。

[^foundations]: [docs/rl-marl-foundations-20260907/FOUNDATIONS.md](https://github.com/CartmanFatass/My-paper-code/blob/4e8ce22f5263a4ebbf096cca6c4af225a0559831/docs/rl-marl-foundations-20260907/FOUNDATIONS.md)，仅 §§4、6：表示／理论与有限学习、完整包与组件归因、训练与条件评价。这些知识限定推断，不独立选择投入。

[^empirical]: [docs/rl-marl-foundations-20260907/topic-notes/04_EMPIRICAL.md](https://github.com/CartmanFatass/My-paper-code/blob/4e8ce22f5263a4ebbf096cca6c4af225a0559831/docs/rl-marl-foundations-20260907/topic-notes/04_EMPIRICAL.md)，“随机性有层级”“完整方法比较与机制归因”“证据的力度随主张变化”；没有跟随未列入清单的来源链接。

[^engineering]: [docs/project/ENGINEERING_SCOPE_SPEC.md](https://github.com/CartmanFatass/My-paper-code/blob/4e8ce22f5263a4ebbf096cca6c4af225a0559831/docs/project/ENGINEERING_SCOPE_SPEC.md)，§§4–5 及适用 §§7.1–7.3，普通预算、DM 接受和实际高风险 diff 的相称 review，不增加机械设施或一般启动关卡。

[^direction]: [docs/research/candidates/semigroup_consistent_duration_model_policy/DIRECTION.md](https://github.com/CartmanFatass/My-paper-code/blob/40b27ad1862c4c3201ce1b073377d587f3fc715c/docs/research/candidates/semigroup_consistent_duration_model_policy/DIRECTION.md)，仅“D6 action-choice family park — 2026-09-04”“Native held-segment residual-MC recast — 2026-09-09”“Native held-segment residual-MC B01 result — 2026-09-09”。

[^applied]: [docs/research/candidates/semigroup_consistent_duration_model_policy/pro_packets/20260908_held_residual_context_repair/archive/RESPONSE.md](https://github.com/CartmanFatass/My-paper-code/blob/ac1d97f5920fe2dfc88698681d389af0b907dbfe/docs/research/candidates/semigroup_consistent_duration_model_policy/pro_packets/20260908_held_residual_context_repair/archive/RESPONSE.md)，开头对象／实质 recast、“下一观察能决定什么”“工作量、成本和必要检查”“依赖、交回路径和最终边界”；已应用的完整历史选择，不是自动后继权限。
