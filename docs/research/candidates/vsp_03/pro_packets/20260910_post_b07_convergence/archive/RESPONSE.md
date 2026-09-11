**我选择（a）：暂停不变的 ordinary-G、continuous512、固定128/512评价、公开固定 N=2 共享服务槽、greedy 替代 R0/R 的窄家族，不选择后继。**本轮不选择新的 fit、随机键、额外评价或更长训练。旧独立128、N1与T/初始化家族的暂停保持；没有引入新机制，不计第二次 RECAST，累计 recasts 仍为1。这是可逆的方向内研究处置，不是整个 VSP03 的 PARK，也不改变 Portfolio 生命周期、优先级或其他方向的推进。

我略同意 DM 这次的暂停推荐，但理由必须保留两个不同结论：**B07再次获得正的最终原生收益；它没有再次获得正的 greedy 128→512变化。**这次独立训练已经回答了所选的有限重复问题：终点优势在这个新实例中保留，继续训练的 greedy 净改善没有保留，随机执行却确实恢复。我的取舍是保留这一有内容的结果，在这里暂歇不变追加序列，而不是再购买一个同配方实例。不是把负Q当成负primary，也不是先要求稳定采用结论才允许继续研究。

**反对暂停的最强证据很实在：B06三个最终greedy控制器均胜过两条规则，其中一个超过0.02；B07的最终greedy与stochastic也都胜过两条规则；已测同配方完整调用仅8.380174–8.927880秒。**因此（b）仍是可信、合规的备选。暂停可能过早搁置普通调度学习的真实收益；没有数据足以证明下一个fit的决策价值为零。我选择的是当前边际投入的轻微偏好，不是统计拒绝、算法失败定理或“四次之后必须停止”的规则。以下观察、推断和未选备选分别说明。[本题建议 §§2–4][question]；[B07 intake §§2–8][b07]；[B06 intake §§3–8][b06]。

## 一、B07的主要结果成立，负Q没有把它取消

B07原卡把固定512的greedy G−R0设为唯一主要量，把同一fit的128→512配对变化Q设为解释量。已接受intake适用的是“最终胜两规则、终点有收益但Q为负”分支。**readiness没有赢得这次样本的最终比较。**也不能因为128的greedy均值稍高，就把它事后改选为本次主要终点。[B07原始冻结卡 §§1、4–5][card]；[B07 intake §§2–3][b07]。

| B07固定执行 | update128原生均值 | update512原生均值 |
| --- | ---: | ---: |
| greedy G | 0.3583056640625 | 0.35669921875 |
| stochastic G | 0.2967041015625 | 0.3568994140625 |
| R0 | 0.3451318359375 | 0.3451318359375 |
| R | 0.343623046875 | 0.343623046875 |

两端点的全部五个比较都保留。下表个别末位沿用来源显示精度，不是本轮重新估计。

| B07原生差 | update128 | update512 |
| --- | ---: | ---: |
| greedy G−R0 | +0.013173828125 | **+0.0115673828125** |
| greedy G−R | +0.014682617188 | +0.013076171875 |
| stochastic G−R0 | −0.048427734375 | +0.011767578125 |
| stochastic G−R | −0.046918945313 | +0.0132763671875 |
| stochastic G−自身greedy | −0.0616015625 | +0.0002001953125 |

主要量的条件world SD/SE为 **0.09613782948786226 / 0.0030043071714956956**。实际逐world配对Q为 **−0.0016064453125**，其条件SD/SE为 **0.05288252531171355 / 0.0016525789159910485**。Q的负点与其条件SE处于相近量级；负号是真实记录，精度限制也是真实限制。它没有建立训练总体的退化、等价、收敛或优化器故障。[本题计数 `accepted_B07.primary`、`paired_Q`][counts]；[B07 intake §3][b07]。

具体地，令 `d(u,e)=J(Ggreedy,u,e)−J(R0,u,e)`，则 `b(e)=d(512,e)−d(128,e)`，Q是1,024个实际b值的均值。两个面板使用相同world、phase和评价随机流；Q的样本SD从这些b值计算，SE=SD/32，而不是把两个端点的独立方差相加。R0虽在差中代数抵销，其实际执行面板仍保存。此处说明统计对象，不声称本轮重新计算了b或方差。[原连续预算答复 §四][continuous]；[B07原卡 §4][card]。

B07只有一个独立训练过程：一个模型、一个连续Adam、两次固定端点评价。两个checkpoint、八个执行面板、1,024个共同world和512条训练曲线都不增加训练样本数。条件world不确定性不是训练总体区间，也不能从这一个fit估计跨fit SD。B07是在看到B06后另行选定的探索性重复，不能并入B06并改称新的四fit主要总体。[B07 intake §§1、3][b07]；[经验专题“随机性有层级”][empirical]。

随机执行的恢复必须更新旧认识。它在128时对两规则及自身greedy都亏损，到512时已胜两规则。最终stochastic−greedy的 **+0.0002001953125** 远小于其条件SE **0.003747222**，既不能说stochastic仍在这次最终样本上输给greedy，也不能说建立了稳定的模式优势。原主要用途和主要量不随这个新正号切换。[B07 intake §3][b07]。

## 二、原生计账说明不同后果，不识别唯一原因

任务效用始终是两个job的 `200*success−10*attempt−waiting_ticks` 之和除以400。B07的已保存计账如下；正净值不删除负分项，负净值也不删除等待节省。

| B07比较 | 成功贡献 | 尝试成本贡献 | 等待贡献 | 净差 |
| --- | ---: | ---: | ---: | ---: |
| 最终greedy−R0 | +0.00830078125 | −0.00322265625 | +0.0064892578125 | +0.0115673828125 |
| greedy128→512，即Q | −0.0029296875 | −0.0005859375 | +0.0019091796875 | −0.0016064453125 |
| 最终stochastic−greedy | −0.00048828125 | −0.00029296875 | +0.000981445313 | +0.000200195313 |

最终greedy相对R0，每团队多0.0166015625个成功、少等2.595703125 ticks，但增加0.12890625次尝试。继续训练期间，greedy少0.005859375个成功、多0.0234375次尝试；节省0.763671875个等待ticks不足以抵销这些成本。相反，stochastic128→512增加0.1572265625个成功、减少0.0263671875次尝试，同时多等7.630859375 ticks，净恢复 **+0.0601953125**。所以“继续训练没有greedy改善”与“随机策略恢复”可以同时成立，不能用其中一个覆盖另一个。[B07 intake §4][b07]；[本题入口 §2][question]。

这是一组原生结果的计账恒等式，不是新的反事实实验。继续训练同时增加经验、梯度更新和两控制器的共同适应，不能把Q进一步命名为纯优化步数因果效应。尝试增加、少等待或阻塞计数也不单独识别正确协调或错过的反事实机会。

绑定结构仍是时间抽象和终止选择：两个固定controller各有一个job，在公开错开的机会时钟选择SUBMIT或CONTINUE；SUBMIT占唯一服务槽八次转移，失败也不提前释放，可能移除伙伴的未来或最后机会。目标演化、等待与团队后果保留到t=40，每个有效动作获得扣除已发生奖励之后的真实剩余团队回报。actor和critic接收相同14个公开own/partner事件、readiness与时钟特征，不见未来tape或未来成功；训练时共享并共同适应G，评价时冻结。[B07原卡 §§2–3][card]；[B07 intake §4][b07]。

共享奖励和耦合动作不能自行证明分散信息处理或MARL特异因果贡献。这个host没有roster变化、私有观测或评价期伙伴学习，全公开集中式调度仍可解释这些控制器的收益。“原生权衡可解释”在这里仅指收益组成和作用路径可读，不表示已经定位了唯一学习机制。[FOUNDATIONS §§3、5][foundations]实际限制的是这一归因，而不是否认有限调度研究的价值。

## 三、B06与旧128记录单列，不能把后来结果拼成新主要总体

B06原先选定的三个连续fit有完整最终主要量与Q。下表精确值来自其接受记录及相应DIRECTION段；Q的条件SE沿intake显示精度列出。

| B06 fit | D128：greedy−R0 | D512：greedy−R0 | Q | Q的条件world SE |
| --- | ---: | ---: | ---: | ---: |
| 10801 | +0.02076171875 | +0.02599609375 | +0.005234375 | 0.006870996 |
| 10802 | +0.01107421875 | +0.0145068359375 | +0.0034326171875 | 0.007779798 |
| 10803 | +0.0000439453125 | +0.0096875 | +0.0096435546875 | 0.007561877 |

B06的原三fit主要均值 **+0.016730143229166668**、描述性样本SD **0.008378536806060969** 和Q均值 **+0.006103515625000007** 保持原义。第一个最终主要点超过0.02，不能以原均值落在0.02内而抹去它。前两个fit在128已具有相当部分最终收益，正Q并不解释全部终点优势。三个Q的条件不确定性也保留，没有因全为正就转成稳定预算收益。[B06 intake §§2–3、7][b06]；[DIRECTION的Accepted B06段][direction]。

其他模式也不能压成一个“全部恢复”标签。以下保留B06来源的九位小数展示：

| B06比较 | 10801 | 10802 | 10803 |
| --- | ---: | ---: | ---: |
| 128 stochastic−R0 | −0.025283203 | −0.051904297 | −0.035034180 |
| 128 stochastic−R | −0.026679687 | −0.053222656 | −0.034882812 |
| 128 stochastic−自身greedy | −0.046044922 | −0.062978516 | −0.035078125 |
| 512 greedy−R | +0.024599609 | +0.013188477 | +0.009838867 |
| 512 stochastic−R0 | +0.029052734 | +0.007993164 | +0.004389648 |
| 512 stochastic−R | +0.027656250 | +0.006674805 | +0.004541016 |
| 512 stochastic−自身greedy | +0.003056641 | −0.006513672 | −0.005297852 |

B06所有最终greedy与stochastic都胜两规则，但10802、10803的最终stochastic仍低于自身greedy；其原三fit模式差均值为负。每个最终greedy−R0的收益都支付更多尝试成本；继续训练的三个Q也都增加尝试成本，其中10801增加等待，而10802、10803牺牲成功以换取较多等待节省。因此B06的正Q不是各项后果同时改善，B07的负Q也没有撤销那些已观察正值。[B06 intake §4][b06]。

旧独立128序列仍有自己的比较、评价变化和适应性选择历史：

| 旧独立128比较 | seed5 | seed6 | seed7 |
| --- | ---: | ---: | ---: |
| greedy G−R0 | −0.013974609375 | +0.0026123046875 | +0.0023291015625 |
| greedy G−R | −0.014775390625 | +0.0017041015625 | +0.0034423828125 |
| stochastic G−R0 | −0.0290673828125 | −0.0487548828125 | −0.0515283203125 |
| stochastic G−R | −0.0298681640625 | −0.0496630859375 | −0.0504150390625 |
| stochastic G−自身greedy | −0.0150927734375 | −0.0513671875 | −0.053857421875 |

该序列的主要描述均值−0.0030110677083333365、样本SD0.009495761444457974以及seed7条件SD/SE 0.245449634472/0.007670301077不变。seed4继续单列为结果启发的发现。N1三组最终T=G=F及早期局部正值、早期greedy G不提交和早期规则比较不足的限制，旧T/R0保存记录一致以及各自暂停，都不被新的512收益修写。[post-B05接受intake §§2–3][old]；[DIRECTION历史与最强支持/反证段][direction]。

旧128的损失不是新512必然不佳的证据；新512的正值也不能反向证明旧结果无效或128必然训练不足。B06的n=3、B07的n=1和旧序列分开解释，不新增四fit primary，不把不同世界和学习历史的旧新均值差归因于单独延长预算。既有P64/P65无learner、无primary的失败不是零endpoint，也不是训练复制。[B06 intake §8][b06]；[旧接受intake §3][old]。

## 四、为何略选暂停：边际研究取舍，不是门槛或自动分支

此前[Portfolio答复的VSP03小节][portfolio]选择一个新同预算fit，目的不是只凑正号，而是观察新的学习历史是否改变继续开发的判断；它同时把“再得小终点正值”列为倾向结束不变重复的情形。B07现在给出这种终点，同时没有命中正Q预期。这使暂歇具有与原选择目的相接的理由，但那段叙事不是预先冻结的强制停机定理，更不能改造成0.02有效性门槛。

目前已经可以作出一个有限而明确的描述：B06的最终控制器与继续训练变化均为正；另行选择的B07保留了终点收益及随机恢复，却没有重复greedy继续改善。下一次不变fit仍会增加真实信息，但主要是在这个已明确的“终点收益与继续变化不等同”问题上补充另一个实现。我现在更愿意保留这组发现和未决变异，而不继续逐例购买同样的终点/Q组合。这个判断不需要先建立可日常采用G的稳定结论，也不声称已充分刻画收益分布。

支持继续的论证不能弱化：B07是新的真实训练产物，而不是重评旧权重；最终两种模式都胜两条未降弱规则，B06还有超过MEI的点。一个新fit可能显示较大收益、终点损失，或者另一种Q与原生牺牲关系，从而改变研究取舍。当前完整成本也不构成“太贵”的反对理由。**我没有数值计算出继续的期望净价值为负；只是接受在仍有潜在收益时结束这一轮不变追加的风险。**这就是本次close-call，而非用少量结果包装确定停止结论。[本题建议 §3][question]；[证据规范 §§11.8.2–11.9][spec]。

有两处历史措辞须限定义解，不能变成继承的科学义务。B07 intake §8与DIRECTION中的“未来需要新的/改变的决策问题”，若被读成必须有新用途、算法或机制才准追加同配置fit，就与本TASK及§11.8.2–3冲突；本轮不采纳这种读法，也不改写旧文。当前需要的是再一个观察有什么边际用途，而本题（b）已经提供了合规用途。类似地，DM“没有具体处理改动”只说明本次没有别的已提出候选，不是拒绝（b）的必要理由。P74关于**同配置独立观察本身可有B价值**的纠正继续成立。[本题入口 §§1、3][question]；[旧接受intake §2][old]。

随机亏损、缺headroom、缺唯一原因、未收敛、未显著或未达到某个seed数，都没有被用作本次启动/停止门槛。尤其不能继续沿用“最终随机模式都亏损”的旧事实：B06、B07的最终规则比较已经改变。我的暂停理由针对不变比较的当前追加价值，而不是否认这项变化。

## 五、最小暂停范围、权限与复审条件

暂停范围只包含已测试组合：持久目标法则、固定两个job/controller、公开错开机会时钟、八tick共享槽、完整t=40原生团队效用与信用、相同14公开特征、generic初始化的共享2,083参数actor–critic、原Adam lr=0.001及objective、同一model/Adam连续512×128个完整训练episode、固定128/512四模式面板、512严格logit>0的greedy−R0主要量与实际逐world Q，以及R和stochastic的既有解释比较。[B07原卡 §§2–6][card]。

R0仍在合法机会own b=1时提交；R保留对pending、ready、仍有未来机会且驻留年龄严格更大伙伴的让行条件，年龄平手提交。不降低规则强度、不改奖励或信息、不移除失败后的占槽或终局等待。暂停不是“公开事件特征没有价值”，也不选择新host、T重开、阈值改变、2048、网格或诊断搜索。

这是对此窄家族的新增可逆处置，而不是把B07的单次分配完成追溯成已经暂停家族。原连续预算答复仅开放B06三个fit；B07来自后来的独立选定，不能叫作B06余额。当前（a）不改那些选择与原始结果。没有新表示、信息或协调机制，故没有第二次RECAST，recasts=1；旧独立128、N1、T暂停保持，Portfolio与UAV状态均不由本答复处置。[原连续预算答复开头及§一][continuous]；[B07原卡 §1][card]。

当前owner的独立滚动推进规则也保持：B07的no-successor原本只结束B07分配，不要求等待任何批次、兄弟结果或清理。此次进入方向节点，是因为拟议（a）改变家族处置，不是因为普通同预算fit普遍需要Pro。若本轮选（b），其身份与有限执行可以由DM按对象层绑定；本轮选择（a）后，今后改变这个具体暂停仍按既有家族权限处理，但不能据此为其他普通B增设审批。独立授权工作不等本节点或其他方向。[AGENTS §§2–5][agents]；[本题入口 §1][question]。

**仍可能改变判断的直接经验观察**是：在新的独立连续训练历史上，同时看到固定D512、greedy−R、实际配对Q、两种执行模式及成功/尝试/等待组成，从而决定是否值得再投入这个普通确定性方案。更多评价旧权重可以改进旧策略的条件精度，却不能替代新的训练产物；更多checkpoint或policy search也不能冒充独立fit。本轮没有选择这一观察。

复审不要求先有阳性、跨过MEI或提出新算法。只须在未来的具体选择中说明：这个同用途新观察出现不同的D512/Q/原生组合时，会怎样影响是否保留或继续研究该控制方案；不能仅为维持链条、凑样本数或得到全正而续跑。若有实际来源矛盾威胁原生奖励、信息、训练或primary，应先按其依赖澄清；这是具体完整性问题，不是先行穷举或重新验收全部历史的要求。没有在此预留新随机键、run或复审日程。

## 六、备选（b）的完整工作和已测成本

选（a）新增科学工作为零；仍须真实比较（b）需要做什么。它是最小的一fit直接B，而非一个应先完成的诊断。计数来自本题 `future_option_b_unselected` 与原连续预算记录，不是本轮模型或配置试跑。[本题计数][counts]；[原连续预算答复 §六][continuous]。

| 未选择的一fit备选 | 工作 |
| --- | ---: |
| 新独立fit / 新模型 / 参数 | 1 / 1 / 2,083 |
| 训练主乘数 | 1×512更新×128 joint episodes×40 ticks×2 targets |
| 训练episode / team ticks / target transitions | 65,536 / 2,621,440 / 5,242,880 |
| 真实backward / Adam steps | 512 / 512 |
| 评价主乘数 | 1×2固定端点×4模式×1,024共同worlds×40 ticks×2 targets |
| 评价episode / team ticks / target transitions | 8,192 / 327,680 / 655,360 |
| 总episode / team ticks / target transitions | **73,728 / 2,949,120 / 5,898,240** |
| rollout模型batch calls上界 | 8,772，不含objective/critic/backward |
| 额外科学验证model/episode/update/evaluation | 0/0/0/0 |
| 嵌套候选、联合动作、未来轨迹、policy search或solver搜索 | 0 |

评价面板是已计入的科学测量，不是零暴露；零的是额外科学验证。R0/R没有模型或优化步骤，但仍有真实目标演化及输出成本。实际有效/梯度行依赖动作和槽状态，不能按上界补训练。没有指数联合动作或轨迹搜索藏在这个工作量里。

完整成本为 `admission/import/startup + G初始化 + 512*C(128,40,2) + 2×4*E(1024,40,2) + 两个即时快照/面板的必要发布读回 + 实际退出和子进程终止`。C包括真实采集、团队信用及一次更新；E包括相应执行的完整原生轨迹。现在已有相同continuous512配方的实测，不必只靠旧128的四倍外推：

| 既有调用，分别保留 | 完整wall，秒 | aggregate CPU，秒 |
| --- | ---: | ---: |
| B06 /10801 | 8.888241 | 8.762 |
| B06 /10802 | 8.718389 | 8.712 |
| B06 /10803 | 8.380174 | 8.313 |
| B07 /10804 | 8.927880 | 9.244309 |

这是运行成本的并列，不是科学primary池化。B06三项wall之和25.986804秒，与其457.616116秒study elapsed是不同窗口；B07的单次manager-origin-to-Finished窗口为8.927880秒。后者不包括全部作者、staging、monitor、收集和集成工作。旧外推与实际读数都保留，不由低wall推断新速度提升或未来保证。[B06 intake §6][b06]；[B07 intake §5][b07]。

未来新fit的wall、CPU、位移、资源与支持工作仍未知。当前8.38–8.93秒仅是有力规划依据，不是上界，也不是“收益/秒”排序或足以定量认证继续一定划算的模型。本次暂停不是成本超限裁决，不另买pilot、profiler、时间校准或所谓免费精确分析。

未选备选保持一个**完整60秒cap**，从最早manager起点覆盖实际节点admission、imports、初始化、连续学习、128/512两面板、快照、发布读回、实际退出和后代终止。工作50秒、清理58秒、硬终止59秒均从同一起点计时；面板、脚本或阶段不重置。没有120秒旧额度或B06的180秒包余额转入下一fit。[本题入口 §4][question]；[B07原卡 §6][card]。

若未来明确选择并绑定（b），应保留一model/Adam连续更新、从64起为零且不拉长或重启的原熵调度，训练/评价私有地址隔离、同fit两checkpoint的共同world/phase/action tapes、严格greedy阈值、固定512primary及真实逐world Q。不得加载旧权重、重置优化器、选最好checkpoint或把最终stochastic的小正差改成新primary。仅在对象层绑定一个全新身份和预测；本轮不虚构这些已存在。

原remote-first wsl_4070、CPU float32单计算线程、float64 worlds、精确已提交源码及逐调用实际节点的新鲜资源admission保持；旧通过记录不能准入新fit。至多一次accepted invocation，完成、拒绝、失败或超时结束该次额度，不自动retry、替换、resume、fallback、加评、更长预算或后继。接受不明须核对原调用，不另起替身。512缺失不填128或0；128损坏而512可信则保留512、标明Q缺失；威胁共享奖励、信息、learner或primary的具体缺陷按依赖处理，可信部分保留。[B07原卡 §§3–6][card]；[证据规范 §11.8.7][spec]。

本咨询不需要工程§4机制；备选只复用原卡已命名的完整期限adapter。原2,000行非测试源码、600行runner及累计测试预算保持，30%编排比例仍为审查信号。B07记录的已测目录subtotal为63.4287585秒，另有早期部分未计时命令，不能据此宣称精确余额；新fit不会重置300秒allowance。只检查后来真正改变的binding和受影响primary，复用可信环境/learner/面板证据，不因launch再做旧fixture、历史重放或新通用validator。[工程规范 §§4–5][eng]；[B07 intake §6][b07]。

## 七、真实暴露、有限结论与实际读取

B07的接受记录不是“只有文档”：一个2,083参数G完成512次backward/Adam、65,536训练及8,192评价episodes、377,648个梯度行、431,296个全部决策行和8,716次rollout模型batch调用。初始总L2为5.835648059844971，最终位移L2为5.499176502227783，相对初始尺度0.9423420408210624。它们证明真实训练暴露，不能替代原生效应或证明学习机制。[本题计数 `accepted_B07`][counts]；[B07 intake §5][b07]。

learner peak RSS为493,867,008 bytes；cgroup headroom/current/max按记录未测，不填零，也不据此否定可信主要量。B06/B07的出版修复、旧技术label、子进程终止记录与局部scratch删除被拒均保留其各自含义；本轮不重演、不绕过、不清理。那些技术开放项没有被当成科学负号或跨方向等待条件。[B06 intake §§5–6][b06]；[B07 intake §§5–6][b07]。

预测也有更新而非一律“只预测幅度”：B06的低置信度三fit均值幅度预测命中，并非逐fit都在0.02内；B07明确的 **0<D512≤0.02命中，而Q>0未命中**，两个结果均完整所以不能写成未评分。owner预测未取得。本题计数记录了准备时的空review/override读取；本轮未读取清单外owner表，不声称进行了新的全局owner核查。[B06 intake §7][b06]；[B07 intake §7][b07]；[本题计数 `owner_boundary`][counts]。

MEI保持0.02绝对效用，即八个总等待tick/400的解释尺度，不是等价带、显著性线或样本数门槛；调优的当前N2 headroom仍缺失而非零，R0/R是有用且合法的固定对手，不是上界。两个checkpoint不能证明收敛；有限fit不证明稳定优劣；共享奖励、公开调度和参数移动不识别唯一MARL原因。[FOUNDATIONS §§3–6][foundations]、[经验专题][empirical]在本答复中具体约束的是主要量、单位、配对、归因与继续训练解释，不导入其他会话选择。

本轮新增模型、world、随机对象、训练、optimizer steps、评价、重放、诊断、tests、profiling和科学调用均为零，没有发起额外Pro请求。本轮只形成并交付（a），没有执行维护状态变化、修改DIRECTION/卡/source/main/Portfolio，也没有创建新科学root或handle。当前所需规范条款已直接读取；历史中“必须改变问题”的过强读法已在第四节明确排除，不存在据它默设门槛或允许规范例外。

本轮成功通过GitHub读取14个允许证据路径；有效提交分别固定在下列链接中，而不是从交付分支后续内容取科学结论。入口TASK另在用户指定的 `a0bd913a4bd1d10270171586cca8ed2a2d792281` 分段读取。

| 实际证据路径（链接含完整有效提交） | 实际阅读/使用范围 |
| --- | --- |
| [docs/research/candidates/vsp_03/VSP03_POST_B07_QUESTION_INTAKE_20260910.md][question] | 全文§§1–4；选项、当前独立推进、close-call、备选计数与边界 |
| [docs/research/candidates/vsp_03/VSP03_POST_B07_COUNTS_20260910.json][counts] | 全文；已接受B07摘录、成本、暴露、未选备选与owner读取边界 |
| [docs/research/candidates/vsp_03/VSP03_B07_CONTINUOUS512_SCIENCE_CARD_20260910.md][card] | 全文§§1–7；原冻结问题、随机性、端点/Q、预测、完整cap及工程约束 |
| [docs/research/candidates/vsp_03/VSP03_B07_INTAKE_20260910.md][b07] | 全文§§1–8；模式、配对不确定性、原生计账、成本、预测与单分配结束 |
| [docs/research/candidates/vsp_03/VSP03_B06_INTAKE_20260909.md][b06] | 全文§§1–8；原三fit、各端点/Q、模式和成本、原下一观察推荐 |
| [docs/research/candidates/vsp_03/pro_packets/20260909_continuous512_convergence/archive/RESPONSE.md][continuous] | 首段、§一及§四–六相关段；原三fit有限重入、统计/预算/失败边界，非重新全篇验收 |
| [docs/research/candidates/vsp_03/VSP03_POST_B05_CONVERGENCE_INTAKE_20260909.md][old] | §§2–4、6–7与邻接窗口；原128暂停、旧全部比较及同用途B合法性 |
| [docs/research/portfolio/pro_packets/20260910_next_five_chains/archive/RESPONSE.md][portfolio] | 定位窗口中仅采用“VSP03: one replication at the observed budget...”小节；不采用其他方向选择 |
| [docs/research/candidates/vsp_03/DIRECTION.md][direction] | Scientific question、相关旧N1限定，Current position的post-B05/continuous512/B06/B07及最强支持反证；未展开evidence tree |
| [docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md][spec] | §4、§5.2、§11.4、完整§11.7–11.10及邻接限定；未采用其他对象例外 |
| [docs/rl-marl-foundations-20260907/FOUNDATIONS.md][foundations] | §§3–6相关正文及邻接尾段；没有跟随SESSION_CHOICES或文献链接 |
| [docs/rl-marl-foundations-20260907/topic-notes/04_EMPIRICAL.md][empirical] | 全文；比较对象、随机层级、归因、开销及证据力度 |
| [docs/project/ENGINEERING_SCOPE_SPEC.md][eng] | §§4–5及普通校准/邻接窗口；不借用其他方向附款扩scope |
| [AGENTS.md][agents] | §§2–6及邻接范围；现有层级、无人值守、2026-09-10独立滚动、完整成本与共享Git |

本题入口与计数使用 `32b0bfb4e78a55b50b04febc49592993107c2edd`；B07卡使用 `adcff0a92559ac5552e24a9861e2b65572b478c5`；B07 intake与DIRECTION使用 `4b1682acfc45a2c2acde6688302aba8fdac8883a`；B06 intake使用 `09e1e048b7422247729962a410e4d91af42a23c8`。原连续预算答复、旧128接受intake及Portfolio来源分别使用表中各自的原始提交。规范与两个知识文件、工程规范及AGENTS均使用 `0daac38f47e911d0286e0a3c72d59902a2dccd25`，没有用它们的新版本回写旧卡。

没有阻止形成这个方向选择的访问缺口。未直接读取或重新验证清单外源码、原始world行、summary、权重、图片、journal、资源现场或论文；数值及技术事实来自上列接受记录和机器摘录，不是本轮独立复现。原有文献核查仅通过这些记录复用，不声称本轮打开论文或完成新的库覆盖。未来fit表现/位移/完整成本、总体重复性、唯一原因和现实映射仍未验证，暂停没有把这些未知变成负结果。

另按交付要求读取Issue6正文及八条既有评论，均为此前轮次，没有本轮post-B07匹配交付；未沿其不同版本链接扩展科学输入。写入前本轮目标不存在，共享分支已核对为本题交付基底后裔。交付核对只证明文件与通知，不证明算法价值。

**最终处置保持（a）：暂歇不变continuous512、固定128/512面板、公开固定N2共享槽的ordinary-G greedy替代R0/R窄家族，保留B07正终点、负Q和随机恢复，保留B06及旧128/N1/T全部相反与正向证据；不选后继、不增第二次RECAST，recasts=1。此决定只及本家族，不产生整方向PARK、Portfolio处置或跨方向同步门槛。**

[question]: https://github.com/CartmanFatass/My-paper-code/blob/32b0bfb4e78a55b50b04febc49592993107c2edd/docs/research/candidates/vsp_03/VSP03_POST_B07_QUESTION_INTAKE_20260910.md
[counts]: https://github.com/CartmanFatass/My-paper-code/blob/32b0bfb4e78a55b50b04febc49592993107c2edd/docs/research/candidates/vsp_03/VSP03_POST_B07_COUNTS_20260910.json
[card]: https://github.com/CartmanFatass/My-paper-code/blob/adcff0a92559ac5552e24a9861e2b65572b478c5/docs/research/candidates/vsp_03/VSP03_B07_CONTINUOUS512_SCIENCE_CARD_20260910.md
[b07]: https://github.com/CartmanFatass/My-paper-code/blob/4b1682acfc45a2c2acde6688302aba8fdac8883a/docs/research/candidates/vsp_03/VSP03_B07_INTAKE_20260910.md
[b06]: https://github.com/CartmanFatass/My-paper-code/blob/09e1e048b7422247729962a410e4d91af42a23c8/docs/research/candidates/vsp_03/VSP03_B06_INTAKE_20260909.md
[continuous]: https://github.com/CartmanFatass/My-paper-code/blob/5af9c448879bba3129df32e07a788839658f8a4f/docs/research/candidates/vsp_03/pro_packets/20260909_continuous512_convergence/archive/RESPONSE.md
[old]: https://github.com/CartmanFatass/My-paper-code/blob/47f8983ed0a241106cdbe8368cb37851f50c7ebd/docs/research/candidates/vsp_03/VSP03_POST_B05_CONVERGENCE_INTAKE_20260909.md
[portfolio]: https://github.com/CartmanFatass/My-paper-code/blob/08e989073839fe5f0f91c6a8ad90a399bee37b6c/docs/research/portfolio/pro_packets/20260910_next_five_chains/archive/RESPONSE.md
[direction]: https://github.com/CartmanFatass/My-paper-code/blob/4b1682acfc45a2c2acde6688302aba8fdac8883a/docs/research/candidates/vsp_03/DIRECTION.md
[spec]: https://github.com/CartmanFatass/My-paper-code/blob/0daac38f47e911d0286e0a3c72d59902a2dccd25/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[foundations]: https://github.com/CartmanFatass/My-paper-code/blob/0daac38f47e911d0286e0a3c72d59902a2dccd25/docs/rl-marl-foundations-20260907/FOUNDATIONS.md
[empirical]: https://github.com/CartmanFatass/My-paper-code/blob/0daac38f47e911d0286e0a3c72d59902a2dccd25/docs/rl-marl-foundations-20260907/topic-notes/04_EMPIRICAL.md
[eng]: https://github.com/CartmanFatass/My-paper-code/blob/0daac38f47e911d0286e0a3c72d59902a2dccd25/docs/project/ENGINEERING_SCOPE_SPEC.md
[agents]: https://github.com/CartmanFatass/My-paper-code/blob/0daac38f47e911d0286e0a3c72d59902a2dccd25/AGENTS.md
