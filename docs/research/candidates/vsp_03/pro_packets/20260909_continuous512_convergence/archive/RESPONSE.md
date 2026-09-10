**我选择（a）：选择这项三组全新 G、每组连续训练至 update512 的有界 B/EXPLORE 预算比较。**每组保持同一个模型和 Adam，从第1次更新连续走到512；在完成128和512次更新时，各执行一次包含 greedy G、stochastic G、R0、R 的固定评价面板，每种执行使用1,024个世界。主要量始终是 **update512 的 greedy G−R0**；128面板只为解释同一训练过程的预算变化，不另算训练实例，也不用于选最佳 checkpoint。采用候选中的10801、10802、10803三组键，每组完整调用上限60秒；180秒仅是三组完整调用上限之和。

**这是在原共享服务机制内对训练预算的有限重入，不是第二次 RECAST，累计 recasts 保持1。**旧的独立 update128 终点追加序列继续暂停；本次只开放上述三个 continuous512 fit 及其内置128参照，不恢复旧的同预算 seed8 备选，不重开 N1 或 T/初始化问题。原暂停决定没有授予这次重入，综合建议和准备工作也没有授予运行；本回复现在选择科学内容，卡片冻结、实现和实际运行仍须落入后续具体有界任务。本轮只交付答复及通知，不修改维护状态。

最小理由是：原结果只观察了128预算下不同训练产物，而本候选直接观察**同一学习过程再接收384批新数据并继续更新后，固定终点相对规则的表现及其变化**。这可能改变是否继续投入普通确定性调度的判断。两个旧独立小正值和已测完整路径支持承担这项受限成本，但不证明128训练不足或512一定更好。**最强反方仍是 readiness 已经有用，seed5的损失大于两个正点，延长训练可能只增加小幅、不确定甚至不利的原生权衡。**我采纳 DM 的推荐，但不把它说成显然优于暂停，更不把一个较长预算包装为收敛或能力认证。

## 一、旧暂停与这次选择的关系

[原 post-B05 完整决定第三至五节][pause]明确暂停的是既有目标法则、固定两个控制器、八 tick 共享槽、公开14特征、generic G、128×128个完整训练 episode，以及最终128的 greedy G−R0/R 比较组合；没有选择新更新数、训练实例、旧权重评价或诊断。[已应用 intake 第三、六节][accepted]和[方向记录的 post-B05 段][direction]确认该处置已经应用，而不只是 DM 的建议。原结论是可逆的投入边界，不是总体无效定理或整个 VSP03 的 PARK。

本次改变总训练量和预先指定的评价结构：最终终点由128改为512，增加同一 fit 内的128参照，另选三组全新初始化及数据流。它必须作为一项明确结果启发的新 B 记录，不能回写旧卡或把后来512的结果算作旧128主要量的成功。新研究中的128面板是这项预算比较不可分离的早期测量，不是以新名字恢复一批独立128试验。（[候选卡第一、三至四节][card]；[准备 intake 第一至二节][prep]。）

不计第二次 RECAST 的依据是实际科学内容，而非名称或代码行数：目标、公开信息、动作及资源后果、团队信用、G的表示与学习方法、R0/R和确定性用途均保持，没有引入替代协调机制、另一主机或新的初始化干预。改变的是同一配方的训练预算与固定测量安排。在已有暂停下由本方向节点明确开放这项有限比较，不意味着每个普通 B 都需要先走一次 Pro；同样也不意味着任何同主机改动都自动不算重铸。（[AGENTS 第二节][agents]；[证据规范第五点二节及第十一点八至九节][spec]。）

[综合建议的 VSP03 行、第五点三节及第六节][synthesis]提出了连续512而非15次网格训练的方向，也注明它不是执行分配。当前准备记录进一步把180秒解释为完整 fit 调用之和，并解决连续状态、固定面板和期限实现选择。我采用的是这些已明确的候选边界，不采用综合报告中其他方向的优先级、算法或后续建议。

## 二、支持、反证与尚未解决的问题

以下旧数值来自本题指定版本的[已接受 post-B05 intake 第二节][accepted]，不是本轮重新计算或评价。每列是一个独立训练的 G；同列内的规则和模式共用其1,024个评价世界。

| 旧固定128原生团队回报差 | seed5 | seed6 | seed7 |
| --- | ---: | ---: | ---: |
| greedy G−R0，旧主要量 | −0.013974609375 | +0.0026123046875 | +0.0023291015625 |
| greedy G−R | −0.014775390625 | +0.0017041015625 | +0.0034423828125 |
| stochastic G−R0 | −0.0290673828125 | −0.0487548828125 | −0.0515283203125 |
| stochastic G−R | −0.0298681640625 | −0.0496630859375 | −0.0504150390625 |
| stochastic G−自身 greedy | −0.0150927734375 | −0.0513671875 | −0.053857421875 |

旧主要描述均值为−0.0030110677083333365，实例分数样本 SD 为0.009495761444457974。seed7主要量的条件世界 SD/SE 为0.245449634472/0.007670301077，正点小于该条件 SE。这些量同时保留：不能据负均值删除两个正点，也不能以正号多数建立稳定替代价值。实例分数的变化包含有限评价变化，不是纯训练方差；自适应续跑也不是一次性冻结的确认性抽样。

原生组成显示，近似的小净收益可以来自不同权衡。seed7对R0的成功、尝试成本、等待贡献分别为+0.0048828125、−0.002880859375、+0.0003271484375；seed6对应为+0.00146484375、−0.00087890625、+0.0020263671875。seed5成功贡献为零，尝试节省+0.0017822265625不足以抵销等待损失−0.0157568359375。它们支持测量继续训练之后的实际成功、尝试和等待，而不支持预先断言一个统一的失败原因。（[已接受 intake 第二节][accepted]。）

最强支持不是“多跑通常更好”，而是已有 G 确实能够产生略胜两个合法固定参照的 greedy 控制器，而继续训练这一段此前没有被观察。本候选能区分：更长预算形成新收益、仅改善但仍输给规则、最终有收益却并非来自128之后的改善，以及继续训练平坦或反向。这些都是会影响下一步投入的有限观察。

最强反证也没有消失：无需训练的 readiness 是真实竞争方案；更长训练可能仍没有值得保留的净收益。原随机亏损还表明概率策略与确定性读出不是同一性能量。原熵系数在第64次更新已归零，不能将最终随机亏损解释成“尚未关闭的熵项”，更不能随512预算重新拉长熵调度。训练目标、优化轨迹、数据覆盖与固定 greedy 阈值的关系仍未被唯一识别。（[候选卡第二节][card]；[CM 可行性报告的实现边界第二项][cm]。）

原 P74 关于“同配置的新独立观察本身可以有 B 价值”的纠正继续成立。选择预算比较不需要贬低普通重复，也不需要制造一个新用途；它只是本次具体提出、比再增加一个独立128终点多回答了一个沿训练过程变化的问题。[原暂停回复第三至四节][pause]仍允许将来基于同用途重新选择。这里没有以少种子、低于MEI、缺少headroom或缺少稳定优势作为启动门槛。

三组而非一组的价值，是让同一128→512问题出现在三个新的学习实现中，避免仅凭单条轨迹决定是否继续研究预算效应。一个连续 fit 已经是合法的局部 B；我接受 owner 候选的三组规模，是因为它以明确三倍工作购买跨 fit 的描述，不是因为三组具有法定充分性、功效保证或全阳性要求。它仍可能得到三个不精确的结果，暂停因而始终是可信的相反取舍。（[准备 intake 第二至三节][prep]；[证据规范第十一点八点三节][spec]。）

## 三、选定比较的科学语义

### 连续学习，而不是重启两次128或复用旧权重

保留两个固定 controller/job、公开错开机会时钟、每人一个任务及唯一服务槽。两个目标均演化完整40次转移；占据时离开概率1/(d+4)，缺席时返回概率1/2。只有本方时钟、任务尚未提交且槽空闲时才有 SUBMIT/CONTINUE；提交不可撤销，失败也占满八次转移，完成和释放先于下一边界决策。忙槽强制等待不产生虚假梯度行。原生效用为两项任务的 `200*success−10*attempt−waiting_ticks` 之和除以400，包含初始等待、最后机会后的等待和目标尾部。每个有效动作获得直到t=40的真实剩余团队回报，扣除已发生团队奖励；gamma=1，终局bootstrap=0。（[候选卡第二节][card]；[原始 P76 冻结卡第二节][p76]。）

actor和critic继续使用相同14个公开自身/伙伴事件、readiness及日历特征，不增加未来目标样本、最终成败或特权 critic 输入。双方训练时共同适应同一 G，面板评价时冻结。共享团队奖励和耦合机会没有因此证明去中心化、私有信息处理或 MARL 特异的因果收益；全公开集中式调度的解释仍成立。[FOUNDATIONS 第三、五节][foundations]在这里实际限制的是归因，不是算法进入资格。

每个 fit 仅构造一个2,083参数的 generic G：actor/direct共1,570、critic513，保留原网络、公开事件输入和可训练own-b系数；输出残差、偏置和direct-b从原generic零值开始。保留 Adam lr0.001、betas(0.9,0.999)、eps1e−8、weight_decay0及原actor/critic objective。512个batch各128个完整joint episodes，每batch一次真实backward和Adam step；批内参数固定，不补齐策略依赖的梯度行，不新增epoch、replay、裁剪或归一化。（[候选卡第二节][card]；[CM 实现边界第一至二项][cm]。）

同一模型和Adam从update1连续到512，128面板后从129继续。训练episode地址不中断、不回到零；不重置动量、步数或学习随机性，不从128权重重建模型或恢复优化器。熵系数始终为 `0.01*max(0,(64−update)/63)`，第64至512次更新均为零；它既不重启也不按新总预算重标度。旧冻结runner不改，原共享环境、模型、objective不重写。

因此128→512对比包含额外384个batch的环境经验、相应真实更新和共同适应，不能进一步命名为“单独增加优化步数的因果效应”。这正是当前整个训练预算变化的有限问题，不必额外拆成一个数据固定实验。表示能力、有限训练表现和渐近收敛属于不同层次；两点曲线既不能先证明128未收敛，也不能在平坦时证明512已经收敛。（[FOUNDATIONS 第四、六节][foundations]；[经验专题“先分清在比较什么”][empirical]。）

### 新 fit、评价隔离与快照

明确采用 fit keys **10801/10802/10803**，Torch初始化 **50801/50802/50803**，G arm恒为1。目标流沿 `[302,fit,split,episode,target]` 的PCG64/SeedSequence地址，phase取target=2；训练split100、episode0…65535，更新u从 `(u−1)*128` 起；评价split200、world0…1023。动作流为 `[303,fit,split,mode,1,episode]`，训练mode0、随机评价mode1，17个均匀量按固定日历位置使用，未用位置不移位。不载入任何旧模型、优化器、世界或随机状态。（[候选卡第三节][card]；[计数文件 RNG_design][counts]。）

三个 fit 通过声明的生成过程分离，而非仅因数字标签不同就证明独立；CM转述的既有键检查也不是统计独立性的证明。每个 fit 内，128与512使用**相同的评价世界、phase和随机评价动作tapes**，刻意形成共同随机数配对；这些地址与训练和其他fit分开。greedy与R0/R不消耗动作tape。“私有评价流”指隔离的随机流，不是给actor增加私有观测。

两个面板都紧接已完成的相应Adam更新进行。使用新环境数组、无梯度，不改变模型参数、Adam、训练RNG或全局更新号；面板不能触发调参、早停、选模式或选择下一训练数据。CM静态阅读记录称现有MLP无dropout、batchnorm或循环状态，地址式采样及rollout可支持这些约束；这是其可行性发现，不是本轮已测试新driver。（[CM 实现边界第三至四项][cm]。）

R0仍在合法机会own b=1时提交；R只增加原先的ready、pending、有未来机会且驻留年龄严格更大的伙伴让行条件，平手提交。greedy严格logit>0提交，零和负值继续。不调弱规则，不添加截止期例外。按照本次精确候选，两个checkpoint各实际执行四面板；R0/R即使在同世界上由确定性法则给出相同记录，也各执行并计入工作，不能静默缓存删除。（[候选卡第二至三节][card]；[CM Exact workload][cm]。）

仅保留128和512两个即时权重快照、checkpoint区分的面板及每fit512条训练曲线。128快照应在该边界就序列化已分离的张量，不能保留会随训练变动的live state_dict引用直到512才写出。不能以保存快照为由构造额外模型、保存全中间策略或新增恢复/optimizer checkpoint系统。文件不得覆盖128面板；初始、首步、128和512尺度/位移在正常路径记录。上述是真正改变的连续状态与出版连接风险，不是要求重跑旧环境fixture。（[候选卡第三、七节][card]；[CM 实现边界第五项][cm]。）

## 四、主要量、预算差与不确定性

令i表示三个新fit之一，e表示其1,024个评价世界，u属于{128,512}。用该面板实际记录定义

\[
d_{i,u,e}=J_{i,u,e}^{G,greedy}-J_{i,u,e}^{R0},\qquad
D_{i,u}=\frac{1}{1024}\sum_e d_{i,u,e}.
\]

每fit主要量是 **D(i,512)**，三个主要分数全部报告。仅在三个512主要量均完整时，给出它们的算术均值与ddof=1的描述性样本SD。每个面板同时保留四个绝对回报、greedy G−R、三个stochastic对照以及各配对世界差的条件SD/SE；不只报一个有利均值。（[候选卡第四节][card]。）

解释性预算差定义为

\[
b_{i,e}=d_{i,512,e}-d_{i,128,e},\qquad
Q_i=D_{i,512}-D_{i,128}=\frac{1}{1024}\sum_e b_{i,e}.
\]

在相同世界、相同R0法则下，R0在这个差中代数抵销，所以Q也就是两次greedy G回报的配对变化；其实际规则面板仍保留。条件不确定性应来自**逐世界的 b(i,e)**：样本SD用ddof=1，条件SE为SD/32。不能把两个面板当独立样本，简单相加两个SE的平方来替代配对计算；共同世界使协方差相关，不能预告一定降低多少方差。既有逐世界差值汇总方式即可完成这一目的，无需bootstrap、额外模拟或新统计服务。这里是对选定统计量的推导，并非本轮已产生数值。（[候选卡第四节][card]；[经验专题“随机性有层级”][empirical]。）

三组连续fit就是三个训练单位，不是六个checkpoint、24个执行面板或24,576次独立训练。世界SE针对固定策略及指定动作随机实现；跨fit的SD还含有限评价变化，不能称纯训练方差。Q的三个实例也只是三条相关预算轨迹上的描述。新包是在旧结果之后选择，但新键与固定512终点在新结果前指定；应称结果启发的前瞻执行 B，不称一项独立于开发选择的确认研究。

旧seed5/6/7仍为单列的128自适应序列，seed4仍为发现样本，不与新128面板或512主要量合并成跨预算总体均值。训练曲线是采集时的随机训练回报，不是另有512个held-out测量；固定512主要量不是两个面板中的最大值，也不允许选择三个fit中最好的控制器后用其原评价集认证使用价值。[FOUNDATIONS 第六节][foundations]和[经验专题][empirical]在这里具体决定了单位、固定终点与选择限制。

若某fit缺512，保留该fit的缺失原因、实际训练数及可信128面板，但不给它填0、128分数或最佳checkpoint，也不把其缺失当成科学负结果。其余完整512分数继续报告；有必要汇总时明确是已完成fit的描述、n为实际数，不伪称三fit完整主要均值，也不假定完成子集是随机无偏样本。若同fit缺可信128而512可信，512端点可保留，Q及其配对解释则缺失。这是按依赖限制主张，不是为了凑齐三次成功而补跑。（[候选卡第六节][card]；[证据规范第十一点八点七节][spec]。）

## 五、什么结果会改变下一步

主要终点和预算变化必须分开解读；下表不是新增显著性阈值或自动运行规则。

| 观察组合 | 允许的有限解释与下一步方向 |
| --- | --- |
| 512 greedy超过R0和R，且同fit Q为正 | 同时支持所测较长预算控制器和沿这些训练路径的改善；若达到原0.02量级并有相应原生组成，更值得考虑另一个明确有限问题。仍无稳定优势或纯优化因果结论。 |
| Q为正，但512仍低于规则 | 有预算敏感的改善，却没有该终点替代readiness的证据；不能只报Q把主要问题写成成功。 |
| 512超过规则，但Q很小或为负 | 端点支持成立，未表明128之后的额外预算带来它；可能128已经同样好或更好，但不得把128改选成本次主要量。 |
| Q平坦、反向或跨fit混合，512也无清楚规则收益 | 削弱继续花费于这一预算方案的局部理由；如实停止或返回剩余问题，不证明收敛、最优、表示极限或整个方向失败。 |

只超过R0而未超过R，结论限于R0比较；所有实例分数和G−R一并可见，不能用跨fit均值遮住反例。随机执行继续亏损时，正向主张限于预先选定的greedy用途；随机改善而greedy不改善不能替换主要答案。成功、尝试、等待及原有机会/阻塞量用于原生计账，不单独把少等待、少阻塞或参数移动当价值。（[候选卡第四至五节][card]。）

MEI保持 **0.02绝对原生效用**，等于八个总等待tick/400的尺度，不随噪声、SD或新预算改动。小正、小负和零都按实际值保留；既不要求三fit全正，也不因一个点低于MEI而取消可信观察。tuned N2 headroom仍缺失而非零，R0/R有用但未调优且不是上界。候选记录的低置信度 `abs(mean_i D(i,512))<=0.02` 可在正式卡中保持为幅度预测；本轮不评分、不把均值的抵销当每fit都小，也不虚构owner的正号预测。（[候选卡第五节][card]；[证据规范第十一点七节][spec]。）

这三个fit及两个固定面板就是此次选定的下一判别。无论结果多有利，都没有自动2048、第四fit、十seed、因果诊断或C/UAV分配；无论结果多不利，也不把B变成已消耗的C。到完整包或实际停止边界后，DM依据全部结果返回具体投入判断。两个时间点不负责证明收敛，三个训练实例不负责证明稳定优越性。

## 六、实际工作、完整成本与失败边界

工作数量采用[机器计数文件的 per_fit、study 与 cost_projection][counts]，与[CM基于当前循环形状的 Exact workload][cm]相符。本轮没有构造模型、随机流或环境来复算。主乘数是 **3 fit×512更新×128完整joint episodes×40 ticks×2 targets**，加 **3 fit×2面板×4执行×1,024世界×40 ticks×2 targets**。

| 工作 | 每fit | 三fit合计 |
| --- | ---: | ---: |
| 新共享G模型/参数 | 1 / 2,083 | 3个模型，各2,083 |
| 训练joint episodes | 65,536 | 196,608 |
| 训练team ticks / target transitions | 2,621,440 / 5,242,880 | 7,864,320 / 15,728,640 |
| 真实backward / Adam steps | 512 / 512 | 1,536 / 1,536 |
| 两面板评价episodes | 8,192 | 24,576 |
| 评价team ticks / target transitions | 327,680 / 655,360 | 983,040 / 1,966,080 |
| 全部joint episodes | **73,728** | **221,184** |
| 全部team ticks / target transitions | **2,949,120 / 5,898,240** | **8,847,360 / 17,694,720** |
| rollout模型batch calls上界 | 8,772 | 26,316 |
| 额外科学验证模型/episode/update/evaluation | 0/0/0/0 | 0/0/0/0 |

前向上界只计rollout模型调用，不含objective、critic和反向更新。实际有效/梯度行仍由策略及槽状态决定，不能按上界补齐。R0/R无网络调用仍有目标演化和输出工作。新增面板是这项科学问题的指定测量，已纳入评价数量，不冒称零暴露；额外科学验证才是零。没有嵌套候选、联合动作穷举、未来轨迹、solver或策略搜索。

一fit已能回答一次局部预算变化；三fit明确付三倍这项工作。相对一个已完成128 fit，单个continuous512训练更新四倍、评价面板两倍、总episode/tick为3.6倍。相对独立重启128再训512，连续方案不重复训练共同前缀；不购买15fit网格、2048预算或从大量策略中挑最大值。此处没有声称这些有限计数本身证明便宜，只把必要工作和不需要的维度分清。（[计数文件 known_work_ratios_to_P76][counts]；[CM Exact workload/Cost projection][cm]。）

完整每fit成本为 `admission/import/startup + G初始化 + 512*C(128,40,2) + 2×4*E(1024,40,2) + 两个指定快照与面板的必要检查/读回/发布 + 实际退出及子进程终止`。C包含采集、目标演化、有效策略调用、团队信用和真实更新；E包含相应执行的完整原生轨迹与结果。不要让快照、128面板、共享启动或末尾出版消失在计时外。

保留已有事实：P67完整wall **3.253184秒**、unit CPU **3.278770秒**；P76完整monotonic wall **4.191728秒**、unit CPU **3.500596秒**。P76 supervisor 的 wall-clock Duration=6秒是另一读数，不用较小的科学/权重读回时间替换完整边界。这些事实来自[已接受 intake 第四节][accepted]与[CM成本部分][cm]，不是本轮现场测量。

按两次完整旧路径各乘四，CM给出的规划数是 **13.012736–16.766912秒/fit，三fit调用之和39.038208–50.300736秒**。训练、评价和启动不同比例增长，因此这是粗外推，不是统计区间、未来上界或可靠完成概率；尤其不能由“启动并不乘四”就断言它必然保守。策略行数、较长学习中的数值行为、写盘和争用仍可能改变实际成本。新wall、CPU、峰值资源、位移和准备/收集工作都未测，不能填零，也不另跑pilot或profiler来使它们看似确定。

采用 **每fit60秒完整cap**。最早manager起点统一覆盖admission、imports、初始化、连续训练、两个评价面板及必要读回/发布、实际退出和后代终止；工作50秒、清理58秒、硬终止59秒，均从同一起点计算。内部driver不得保留独立的120秒预算或在128面板后重置计时；内外应服从这个同一60秒框架及50秒工作边界。原卡的120秒不是新包可继承的余额。（[候选卡第六节][card]；[CM 实现边界第六项][cm]。）

**180秒是三项60秒完整调用cap之和，不是整项研究elapsed截止时间。**顺序执行的staging间隙、控制平面和收集可使研究elapsed更长；并发也没有自动三倍速度或60秒完成保证。本次不新建全局期限、pool或调度器。已有普通分离调用和其责任安排足够，真实研究elapsed与调用wall之和分别记录；已包含在fit内的admission不再被移到外面。

实际执行保持remote-first wsl_4070、CPU float32单计算线程、float64世界及精确已提交源码；每fit各在实际节点完成新的相邻resource admission，物理和有效可用内存均须达到既有4 GiB要求。过去通过记录不准入新fit，旧峰值RSS不保证512峰值。各fit采用分离的detached进程，也避免在同一解释器反复设置原Torch interop线程状态；不引入新的分布式方法。（[候选卡第六至七节][card]；[CM实现边界第六项][cm]。）

后来具体分配时，每个具名fit至多一次accepted invocation，三个计划不按回报符号停止。某一fit完成、拒绝、失败或超时，其本次额度结束，不替换、retry、resume、fallback、追加评价或补第四fit。单fit失败不等于另一具名fit必须失败，也不要求三次都成功；存在威胁共享奖励、信息、训练、比较或主要量的具体shared defect时，暂停依赖的后续launch进行修复和分配核对，不能盲跑，也不能把修复变成重跑失败fit的许可。所有可信记录保留，接受状态不明则核对同一调用状态，不另起替身。

## 七、相称工程与本轮权限

原CM的结论是：现有driver硬编码128、单终点及120秒，需要薄层连续driver、checkpoint输出与期限连接变更；shared science无需重写，既有task-local adapter可接受60/reserve10。**可行性不等于新实现已验收。**本轮未读取清单外源码、未执行tests或验收该driver；不把CM的静态判断写成已经通过的实现。（[CM Minimum implementation boundaries][cm]。）

后续真正改变的高影响边界是模型/Adam/更新连续性、128评价隔离、私有地址与同世界配对、即时快照、512主要量和完整60秒时钟。沿现有权限做针对这些变化的相称检查与必要独立review，复用未变的环境、规则、奖励和生命周期证据；不能仅因新launch重新买旧smoke或额外科学fixture。计数中的额外科学validation仍为零；若以后具体缺陷确实需要超出它的观察，应明确返回受影响范围和额度问题，不暗加调用。

工程§4只复用已具名的task-local期限/终止适配器，用于“包含出版及后代的完整fit wall≤60秒”。不新增恢复框架、通用validator、注册表、provenance门禁、遥测服务或worker pool。原2,000行非测试源码、600行runner及原研究目录累计测试预算保持；新对象/面板不是重置预算的理由，30%编排比例仍是审查信号而非科学有效性判据。（[工程范围第四至五节][eng]；[证据规范第十一点八点六至八节][spec]。）

本轮咨询新增科学导入、模型、随机master、训练、episode、optimizer step、评价、诊断、test、profiling及科学提交均为零；没有发起额外Pro请求。P76初始L2为5.815270900726318、最终相对位移0.4608034745910933只支持原配方确实曾移动，不预测512位移或收益，更不能把512乘学习率当Adam位移界。（[计数文件 historical_exposure_reused 与 new_preparation_exposure][counts]。）

N1的三组最终T=G=F及早期正值、早期greedy G不提交和缺早期规则/随机评价的限制保留；旧T/R0样本一致、旧随机损失、seed4发现与全部原主要量保持原义。P64/P65的无学习无主要量失败不算零endpoint，旧失败和spent allocation不因新包被修写。新结果也不认证旧事件来源、重开其他方向或更改Portfolio生命周期、优先级、容量和UAV状态。（[原完整暂停回复第六节][pause]；[已接受 intake 第二至三、六至七节][accepted]。）

我没有发现阻止选择这项有限B的具体科学或规范冲突。当前列明的规范章节是适用要求；FOUNDATIONS和经验专题用于上述单位、连续过程、因果与收敛边界，不具有另立seed配额、教材普查或owner确认门槛的权力。没有展开SESSION_CHOICES或清单外文献、原论文、库索引及源码依赖；先前时钟/行动信用/普通termination文献仅按候选与已接受记录复用，未声称本轮原论文复核。（[证据规范第十一点十节][spec]。）

完整答复由原DM进行当前规范内intake；Root随后给出具体有界实现/执行任务，既有独立观察、CM技术接受与DM科学解释责任保持。科学选择、实际分配、accepted handle、结果和维护状态是不同事实。本次没有冻结新卡、创建handle、派发运行或修改DIRECTION，也不增加一次Portfolio科学咨询作为普通中间步骤。

## 八、实际访问版本与未验证事项

入口TASK在用户指定的 `0a4f092be84e2fcbeb8b9bed77780a993c5e9546` 完整分段读取。其余14个允许路径均成功通过GitHub读取，按清单有效版本而不是默认分支取证。为避免旧卡与新方法版本混淆，版本分组如下：候选四文件为 `5a5f7c549c51c3ad9106fc94bd884a34b3f4427a`；旧暂停答复为 `3da3a0c44ff7296c19e85342a56ee3128dce1451`；已应用intake与DIRECTION为 `47f8983ed0a241106cdbe8368cb37851f50c7ebd`；原P76卡为 `3eda7ac6dd9d1f888ccff7799d5616e0eb19867f`；综合建议为 `dae6a74bbf8e402a3ea47256176f5795eb277206`；规范与知识五文件为 `090da20372152c7ceecf6c54c70f3f0587439a08`。下列链接分别固定到这些版本。

| 实际路径 | 读取和科学使用范围 |
| --- | --- |
| [docs/research/candidates/vsp_03/VSP03_CONTINUOUS512_CANDIDATE_SCIENCE_CARD_20260909.md][card] | 全文第一至八节；候选定义、两面板、预算、停止与权限 |
| [docs/research/candidates/vsp_03/VSP03_CONTINUOUS512_PROSPECTIVE_COUNTS_20260909.json][counts] | 全文；已算工作、地址设计、外推与零新增暴露 |
| [docs/research/candidates/vsp_03/VSP03_CONTINUOUS512_CM_FEASIBILITY_20260909.md][cm] | 全文；源码可行性、原硬编码、快照/随机性/时钟边界与成本 |
| [docs/research/candidates/vsp_03/VSP03_CONTINUOUS512_PREPARATION_INTAKE_20260909.md][prep] | 全文第一至六节；推荐、反方、概念使用与准备边界 |
| [docs/research/candidates/vsp_03/pro_packets/20260909_post_b05_convergence/archive/RESPONSE.md][pause] | 全文143行；实际暂停、所有旧证据及未选后继 |
| [docs/research/candidates/vsp_03/VSP03_POST_B05_CONVERGENCE_INTAKE_20260909.md][accepted] | 全文第一至七节；应用、全部三实例、历史成本和未选128备选 |
| [docs/research/candidates/vsp_03/VSP03_B05_P76_SCIENCE_CARD_20260909.md][p76] | 第二至六节及紧邻段；原冻结语义和120秒历史边界 |
| [docs/research/candidates/vsp_03/DIRECTION.md][direction] | Scientific question；Current position中的P67/P74/P76/post-B05及最强支持反证，未展开evidence tree |
| [docs/research/portfolio/pro_packets/20260909_third_party_planning_comparison/RESEARCH_PLAN_SYNTHESIS_CODEX_20260909.md][synthesis] | 为定位读取前部与相关窗口；实际采用仅第四节VSP03行、第五点三节VSP03及第六节成本/非执行性限定，不对其他方向作决定 |
| [docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md][spec] | 第四、第五点二、第十一点四及完整第十一点七至十节，和邻接限定 |
| [docs/rl-marl-foundations-20260907/FOUNDATIONS.md][foundations] | 全文返回，科学使用第三至六节；不跟随未列链接 |
| [docs/rl-marl-foundations-20260907/topic-notes/04_EMPIRICAL.md][empirical] | 全文；比较层级、随机单位、选择、开销和主张力度 |
| [docs/project/ENGINEERING_SCOPE_SPEC.md][eng] | 第四至五节及普通校准的邻接窗口；不使用其他方向附款 |
| [AGENTS.md][agents] | 第二至六节相关范围与紧邻段；方向/对象权限、完整预算与共享交付 |

CM报告有少量标点编码显示异常，但所需数量、循环、随机地址、快照和期限说明完整可辨；没有将其替换或把未读源码当成本轮直接源码核验。除此之外没有决策关键访问缺口。未验证的事项是新driver实际正确性、真实512性能与位移、评价隔离的实现、未来资源与完整耗时，以及总体训练规律和现实UAV映射；这些保持未测，不伪装成已经完成的验收或阴性结论。

另按交付要求读取Issue6正文及七条既有评论，没有本轮continuous512的匹配交付；未沿评论链接获取其他科学版本。写入前目标路径不存在，分支核对为指定交付基底的后裔。分支、文件及评论核对只证明交付，不证明算法收益。

**最终选择仍是（a）：三个全新、各连续512更新的普通G预算比较，128/512固定四面板，512 greedy−R0为主要量，同fit预算差为解释；每fit完整60秒、三fit上限之和180秒、每fit至多一次accepted invocation，保留全部符号与失败。仅此有限重入，不恢复旧独立128追加序列，不计第二次RECAST，recasts保持1，不预授2048、第四fit或任何C/UAV/Portfolio处置。**

[card]: https://github.com/CartmanFatass/My-paper-code/blob/5a5f7c549c51c3ad9106fc94bd884a34b3f4427a/docs/research/candidates/vsp_03/VSP03_CONTINUOUS512_CANDIDATE_SCIENCE_CARD_20260909.md
[counts]: https://github.com/CartmanFatass/My-paper-code/blob/5a5f7c549c51c3ad9106fc94bd884a34b3f4427a/docs/research/candidates/vsp_03/VSP03_CONTINUOUS512_PROSPECTIVE_COUNTS_20260909.json
[cm]: https://github.com/CartmanFatass/My-paper-code/blob/5a5f7c549c51c3ad9106fc94bd884a34b3f4427a/docs/research/candidates/vsp_03/VSP03_CONTINUOUS512_CM_FEASIBILITY_20260909.md
[prep]: https://github.com/CartmanFatass/My-paper-code/blob/5a5f7c549c51c3ad9106fc94bd884a34b3f4427a/docs/research/candidates/vsp_03/VSP03_CONTINUOUS512_PREPARATION_INTAKE_20260909.md
[pause]: https://github.com/CartmanFatass/My-paper-code/blob/3da3a0c44ff7296c19e85342a56ee3128dce1451/docs/research/candidates/vsp_03/pro_packets/20260909_post_b05_convergence/archive/RESPONSE.md
[accepted]: https://github.com/CartmanFatass/My-paper-code/blob/47f8983ed0a241106cdbe8368cb37851f50c7ebd/docs/research/candidates/vsp_03/VSP03_POST_B05_CONVERGENCE_INTAKE_20260909.md
[p76]: https://github.com/CartmanFatass/My-paper-code/blob/3eda7ac6dd9d1f888ccff7799d5616e0eb19867f/docs/research/candidates/vsp_03/VSP03_B05_P76_SCIENCE_CARD_20260909.md
[direction]: https://github.com/CartmanFatass/My-paper-code/blob/47f8983ed0a241106cdbe8368cb37851f50c7ebd/docs/research/candidates/vsp_03/DIRECTION.md
[synthesis]: https://github.com/CartmanFatass/My-paper-code/blob/dae6a74bbf8e402a3ea47256176f5795eb277206/docs/research/portfolio/pro_packets/20260909_third_party_planning_comparison/RESEARCH_PLAN_SYNTHESIS_CODEX_20260909.md
[spec]: https://github.com/CartmanFatass/My-paper-code/blob/090da20372152c7ceecf6c54c70f3f0587439a08/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[foundations]: https://github.com/CartmanFatass/My-paper-code/blob/090da20372152c7ceecf6c54c70f3f0587439a08/docs/rl-marl-foundations-20260907/FOUNDATIONS.md
[empirical]: https://github.com/CartmanFatass/My-paper-code/blob/090da20372152c7ceecf6c54c70f3f0587439a08/docs/rl-marl-foundations-20260907/topic-notes/04_EMPIRICAL.md
[eng]: https://github.com/CartmanFatass/My-paper-code/blob/090da20372152c7ceecf6c54c70f3f0587439a08/docs/project/ENGINEERING_SCOPE_SPEC.md
[agents]: https://github.com/CartmanFatass/My-paper-code/blob/090da20372152c7ceecf6c54c70f3f0587439a08/AGENTS.md
