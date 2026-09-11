**最终选择是继续成员损失后的共享策略恢复研究，但不再为当前64轮、确定性执行的MAPR–DIRECT小差异原样追加训练种子。唯一下一观察，是对两个种子已经保存的四个最终策略，进行一次固定参数、同一新评价面板上的“训练时原分布单次采样执行，对照当前逐token贪心执行”的原生回报比较。** 保留固定BCRH参照，不增加训练、不挑选检查点、不搜索更好的命令或轨迹，也不改写两次B01的原结果。

选择这一观察，不是因为随机执行已被证明更好，而是因为源码给出了一个具体、可直接改变已训练策略实际回报、且尚未测量的区别：收集训练数据时传入分类采样的uniforms，正式评价时传入`None`，执行逐token贪心。两个学习器都确实学到了恢复行为，但目前读数只回答其贪心执行版本的表现。先比较这两种完整执行方式，比继续估计同一小差异、直接增加训练量，或重新寻找策略类最大值，更接近“已有学习成果能否转化为更好的原生恢复”这一下一决策。[实际收集与更新路径][S7]；[正式评价路径][S8]；[动作选择实现][S9]

这是已有真实训练B研究中的一个**部署方式后续比较**，不是新的训练实验。新增优化为零必须如实报告，不能冒充又完成了一轮学习；它也不是未来任何新B的必经诊断。下文给出这一单一观察的范围、成本和停止边界。

## 一、两个种子已经回答了什么，还没有回答什么

两份完整结果均使用真实环境、同信息的两个学习器和实际PPO更新。每臂每种子64轮、每轮32个完整episode，合计2,048个训练episode、12,288个joint transitions和2,048次optimizer step；三次评价分别位于初始化、32轮和64轮。DIRECT并非一个未活动的空对照：其参数和残差输出都移动，原生学习增益也接近MAPR。[两种子科学intake，“Complete second-seed exposure and cost”][S1]；[两份技术接受][S5]、[S6]

| `R_fail_60`主要读数 | 训练种子2026090501 | 训练种子2026090503 |
| --- | ---: | ---: |
| MAPR最终值 | 0.263658854 | 0.241848958 |
| DIRECT最终值 | 0.248190104 | 0.237916667 |
| 固定BCRH | 0.305481771 | 0.302760417 |
| MAPR最终减初始化 | +0.204127604 | +0.199453125 |
| DIRECT最终减初始化 | +0.188658854 | +0.195520833 |
| MAPR最终减DIRECT最终 | +0.015468750 | +0.003932292 |
| 上一行在zone 1的差异 | +0.028072917 | −0.029322917 |
| MAPR最终减BCRH | −0.041822917 | −0.060911458 |
| DIRECT最终减BCRH | −0.057291667 | −0.064843750 |

表中数值来自既有逐种子读数和已经计算的对照表，不是本次重跑或重新选择后的结果。[完整对照表][S2]；[首种子intake][S13]；[两种子intake][S1]

**最强正面证据是共同学习的重复出现。** 两臂、两个分区在两次训练中都取得了原生恢复增益，且其他三个原生指标相对初始化也改善。有效运行中MAPR有89,090个参数，DIRECT有148,739个参数；MAPR相对参数位移为0.292124／0.304535，DIRECT为0.256309／0.270141。它们支持“这些真实共享策略在该N7分布和预算上学到了恢复行为”，不能仅归功于MAPR特有结构。[机器曝光记录][S4]；[两种子intake][S1]

**最强反证是活跃的DIRECT能够解释大部分共同改善，而MAPR特有的终点分离小且有区域异质性。** 两个MAPR–DIRECT aggregate差异都为正，这是应保留的直接事实；但zone 1换号，不能称一致的分区优势。既有工具给出的两种子平均差异0.009700521及样本标准差0.008157508只是描述，不是稳定优势的区间，也不是等价结论。少数种子可以支持下一笔有理由的探索，不必先达到显著性；同样，两个正号也不自动要求继续购买相同观察。[run级描述统计][S3]；[证据规范§11.8.2—11.8.4][S17]

原生服务代价不能被主指标掩盖。两种子的两个最终学习器，在两个分区的`R_fail_60`、`U_total`、`U_intact`和`J_ext`分区均值上全部低于BCRH。MAPR相对DIRECT也并非四指标处处改善：第一种子zone 1的`U_intact`为负差，zone 2的`U_total`和`J_ext`有负差；第二种子zone 1的恢复、总服务和`J_ext`为负差，尽管完整区域的其他量可能改善。这些是分区统计，不是“每个episode都更差”的断言。[两个完整intake][S13]、[S1]

`0.10 R_fail_60`仍是原卡的描述量级。不能把未达到它写成失败门槛，也不能把0.0097附近的差异先验宣布无用。当前停止原样补种子的理由是**下一决策价值**：共同学习已被两次观察到；继续同一配置主要增加对这个小分离的精度，而当前尚未要求论文级精确估计，也没有证据表明这就是最值得优先解决的问题。[原科学卡，“Expected reading”][S11]；[第二种子卡][S12]

## 二、为什么选择执行方式，而不是又一次训练或搜索

### 一个已经落到真实源码的区别

`learning.py::rollout`在训练时生成四token的uniforms，评价时不给uniforms；`torch_models.py::MAPR4.forward`据此分别进行分类采样和最大logit选择。DIRECT沿用这个动作路径，并在后续token的分数中加入依赖已选前缀的残差；前面选中的agent还会改变后续可用mask。`CanonicalOpaqueRankForward`保持实体对应，传递uniforms，并把动作映射回原生物理实体。[收集路径][S7]；[MAPR4.forward和DirectSetAR.prefix_adjustment][S9]；[canonical动作封装][S10]

据此可以提出一个有限、可证伪的假说：**训练得到的分布经逐token贪心提取后，其原生回报可能不同于直接执行该分布；差异可能涉及前缀协调，而不仅是一个孤立动作的随机扰动。** 这是本次推论，不是已有结果。逐token贪心不等于求整个joint command的全局最优，更不等于按原生价值选择动作；但采样也不因此必然优于贪心。

这个区别并不构成B01的评价错误。原卡明确把其最终评价策略作为读数，现有比较有效。新比较改变的是部署策略的定义和相应回报估计量，必须另行命名并保留旧读法。它不能反过来把原有BCRH差距“修正掉”。

### 对这一选择的最强反对意见

现有数据并未直接显示任何损失来自贪心提取。训练分布可能仍保留低价值探索概率，单次采样可能降低四个最终策略的表现；即使改善，也可能是两个学习器共有的执行效果，而非MAPR结构收益。固定参数比较还不能修复表示、信用分配或优化不足。**这些反对意见限制可解释结论，但正是该小比较能够直接回答的风险，而不是要求先做全因果定位的理由。**

另外两个正常方案仍然科学上合法，只是本轮不选。继续同配置独立种子可用于更精确描述小效应，不能因缺少显著性就否定其价值；增加同信息训练曝光也可研究预算依赖，不能因模型已学习就宣称饱和。尤其第二种子MAPR后半段恢复变化很小而DIRECT仍明显上升，第一种子两臂后半段均上升，这并不足以证明任何一臂达到最优。不过，这两个方案都继续支付完整训练，而执行方式的差异可以直接使用全部四个已训练终点策略观察。[两种子intake，“Per-seed results and native tradeoffs”][S1]

不选择精确upper、one-deviation census、beam或best-of-many轨迹搜索。当前需要比较的是两个**预先明确的实际执行方式**，不是为每个世界挑更好的模式或命令。比较完不能逐episode取较高回报，也不能在多条采样轨迹中挑赢家。这是采样回报比较，不是以更小预算恢复搜索前置。[证据规范§11.9][S17]

## 三、唯一下一观察的科学核心

### 固定模型与两个执行臂

将该后续比较命名为“**N7固定终点策略的单次采样与逐token贪心比较**”。它属于已有B/EXPLORE结果的有限性能评价延伸，不声称新增学习效应或新增独立训练证据。

对象固定为两个已接受训练种子的MAPR和DIRECT各一个round-64最终checkpoint，四个全部纳入。不用初始化或midpoint替换其中任何一个，不比较多个checkpoint后再挑选。四个模型保持保存的参数、CPU binary64、canonical实体／角色对应、原生mask及四token语法不变。[两份技术接受的checkpoint记录][S5]、[S6]；[checkpoint与评价代码][S8]

同一模型的两个执行臂是：

- **逐token贪心**：保持B01正式评价的`uniforms=None`路径、原tie与合法mask。
- **原分布单次采样**：保持模型现有masked categorical分布，每次joint decision只产生一个合法四token命令；不调温度、不截top-k、不改变logits、不添加随机混合率。沿完整episode顺序执行，不多采样再择优。

这是两个预定部署策略，不是一个“见到结果就选模式”的混合策略。两者均不给actor增加世界编号、种子、未来tape、BCRH输出或其他新信息。

### 人口、随机性和原生后果

保持同一个8→7、两区、一次未预告executor loss的原生host；不引入join、replacement、重复churn或跨N评价。绑定的MARL结构仍是成员损失后，幸存实体以四token联合分配协调恢复；本轮操纵的是同一共享策略的动作提取方式，不是环境或成员事件。

使用**一个新的64-episode评价面板**，两失败区各32个，全部四个checkpoint及两种执行方式共用这些外生世界。为避免与旧训练／评价坐标混同，选定新的评价命名空间`VNFC-N7-B01-DEPLOYMENT-MODE-20260905`，外生评价master为`2026090505`，采样动作master为`2026090506`；动作地址区分原训练seed、算法、world、epoch和token。每个checkpoint／world只运行一次采样轨迹。共用外生世界用于配对，不要求不同模型或模式产生相同状态轨迹。

BCRH-PERSIST在该新面板运行64个完整episode一次，结果供全部比较复用；不调优，不借旧面板的BCRH均值当新面板配对值。完整内部scorer／checker成本继续存在。[现有固定BCRH评价函数][S8]

每条episode仍完成包含prehistory的240个native ticks，以及120秒post-loss终局。主要读数为`R_fail_60`，并列`U_total`、`U_intact`、`J_ext = 0.5 R_fail_60 + 0.5 U_total`、原生flags及已有20秒恢复观察。20秒观察不改称精确恢复延迟。[原卡的原生定义][S11]；[terminal_metrics与rollout][S7]

### 估计量与有限解释

对算法a及原训练种子s，主要量是同一checkpoint在该面板上的配对差：

$$
\widehat\delta_{a,s}
=\frac{1}{64}\sum_{i=1}^{64}
\left[R_i(\pi^{\mathrm{sample}}_{a,s};\xi_{a,s,i})
-R_i(\pi^{\mathrm{greedy}}_{a,s})\right].
$$

它是固定已训练策略下、包含新世界和采样动作随机性的有限回报测量，不是新的训练增益。每个checkpoint分别报告aggregate与两个分区，不只给四模型合并均值。同步报告同一模式下MAPR–DIRECT的配对差、各模式与BCRH的原生差距，以及上述其他原生指标；不能只保留改善最大的模式或指标。

对MAPR–DIRECT仍可作声明范围内的同信息比较；对BCRH仍只作原生控制器参照，**不增加逐字段信息等价或严格因果headroom归因**。两个旧训练seed仍然只是两个训练seed。共用新面板改善比较的对应关系，但不能使它们变成四个或八个独立训练样本，也不能消除原两次训练与评价变异尚未分离的事实。

对这一后续问题仍沿用0.10作为显著原生变化的描述尺度，不新造必须过线的判定门槛。小变化是否值得后续，须结合原来约0.04—0.06的aggregate BCRH差距、其他服务代价及实现成本解释，而不是只看是否越过0.10。

预期解释与falsifier如下：

| 实际观察 | 支持的有限解释与后续边界 |
| --- | --- |
| 原分布采样带来有意义的恢复／目标收益，且不是靠更差的其他服务掩盖 | 支持这四个固定策略中相应策略的执行方式具有实际价值；若两算法共同改善，首先是共同执行效果，不是MAPR特有学习优势。下一笔训练是否采用该部署方式，再由实际效果决定，不自动追加。 |
| 采样没有改善、反向，或主要增益被`J_ext`／其他原生服务损失抵消 | 本轮“贪心提取是可利用的性能损失来源”预测在这些策略上不获支持；结束该执行方式小问题，不加温度、不多抽动作或面板直到转正。不能据此证明所有随机策略都无价值。 |
| 模型／种子／分区之间混合，小差异仍主导 | 保留异质性，不能逐世界选择执行方式或声称等价。没有清楚的新决策收益时，停止本项，不把提高统计精度自动变成下一任务。 |

这些是解释和投入边界，不是用少量数据认证总体优势的统计分类器。特别是，本轮不承诺采样改善，也不以四个checkpoint必须同号作为有效性条件。

## 四、完整工作量与成本：不再购买训练，也不隐藏参照成本

### 已经支付的真实学习账单

两次有效完整调用实测388.75和306.68秒wall，388.53和305.83 CPU秒。它们总计695.43秒wall；连同同seed的不完整formal01，正式累计为783.29秒wall、774.61 CPU秒。计入两次已计时工程检查后为808.90秒wall、800.40 CPU秒；更早诊断的未完整计时仍是缺口，不填零。[机器曝光与费用记录][S4]

两份同源完整单位成本律的条件投影分别为431.170369与328.549531秒：

| 条件投影分项 | 第一完整运行提供的单位成本 | 第二完整运行提供的单位成本 |
| --- | ---: | ---: |
| MAPR完整训练／评价工作 | 170.353471秒 | 129.530782秒 |
| DIRECT完整训练／评价工作 | 201.228809秒 | 150.383305秒 |
| 固定BCRH | 46.377076秒 | 37.746742秒 |
| 共享准备、世界、记账与发布 | 13.211012秒 | 10.888702秒 |

它们不是新任务的实际成本，更不是保证上界。更早282.611秒短检查投影曾低估388.75秒完整运行，不能把估计误差或第二次较快结果解释成已知加速原因。[第一完整intake的成本说明][S13]；[第二技术接受][S6]

最小同类完整训练B的主工作为两学习臂×一个seed对×64轮×32episode×六次joint decision；每臂再有64×四PPO epochs×八minibatch的2,048次真实更新、三次64episode评价，以及全组384次BCRH调用。第一完整运行的实测更新阶段分别为MAPR 113.412477秒、DIRECT 135.175703秒，明显不是只有环境推进和验证开销。[CM完整阶段计时][S5]

### 所选后续的精确计划计数

以下是从已列明循环推导的计划计数，不是本次执行记录：

| 工作 | 所选一次后续比较 |
| --- | ---: |
| 已训练终点策略 | 2个原训练seed×2个算法＝4个 |
| 每个策略的执行方式 | 2种，均完整报告 |
| 新增训练episode／round／optimizer step | 0／0／0 |
| 学习策略评价episode | 4×2×64＝512 |
| 固定BCRH评价episode | 64 |
| 完整episode总计 | 576 |
| 学习策略joint decisions | 512×6＝3,072 |
| 固定BCRH完整调用 | 64×6＝384 |
| 含prehistory的native ticks | 576×240＝138,240 |

学习策略的四token顺序选择和BCRH的内部候选评分是算法本身的工作；本轮不另外展开所有joint command或未来轨迹。相对于完整B的一组4,544个episode、两臂共4,096次优化，这项比较没有优化工作，交互也更少；**但不能用episode比率外推wall比率**，因为384次BCRH完整调用并未减少，而且checkpoint装载、新采样评价及发布还有各自成本。

完整成本范围应写为：

$$
T_{\mathrm{next}}=
T_{\mathrm{import/build/load/world}}
+64\sum_{s\in\{1,2\},a\in\{M,D\}}
\left(c^{\mathrm{greedy}}_{a,s}+c^{\mathrm{sample}}_{a,s}\right)
+64c^{\mathrm{BCRH}}
+T_{\mathrm{output/readback}}.
$$

每个episode单位包含reset、公开观察、actor、native stepping和完整终局；共享准备只计一次，BCRH单位包含完整控制器／checker工作。优化项为零是所选设计的实际定义，不是把未知成本设零。

旧实测中每臂192个贪心评价episode合计约3.29和3.43秒，固定BCRH64episode约37.75—46.38秒，这为一个小评价后续提供了具体费用依据。但独立装载四份checkpoint、采样策略到达的新状态、新路径的构造和发布尚未计时，不能给出已验证的完整秒数或承诺线性缩放。[第一完整运行阶段计时][S5]；[第二完整运行费用][S6]

**本轮明确选择一次完整评价调用，wall上限180秒，计入原B01的2,700秒累计正式额度。** 这是基于上述具体问题和已有评价费用选择的小额后续，不是从余额自动推导的权限，也不增加原总额；若用满，已记录正式累计最多963.29秒。180秒是停止上限，不是新成本实测、保证上界或必须花完的目标。准备中若发现该完整路径无法合理容纳，就返回具体缺口，不先开一个新的成本实验，不临场减模型、删不利模式或改面板。

调用必须包含实际支付的import、专用编译、四份参数装载、评价、完整原生参照及发布；不能把其中某项移出计时获得表面合规。既有未测工程工作单列，必要的源码审查／focused验证也如实记录，不宣称全部研究工作只有963.29秒。沿用现有单线程CPU路径，不借E01四参与者例外或未经测量的并行节省。整次wall、已有OS CPU账和RSS各报各的，不把wall乘线程数当CPU实测。[运行规范一般要求§1—§8][S19]

## 五、实现依据、必要验证与尚缺事实

已有`experiment.py::checkpoint`保存并读回model和optimizer状态，两份技术接受确认六个checkpoint各自存在并已被复制；但独立读者只核对其metadata，本节点也没有打开远端checkpoint。因此，**“四个指定最终参数可供装载”有保存记录支持，“新的评价专用入口已经就绪”没有支持**。后者属于本次有界CM实现准备，而非另外的科学证明任务。[两份技术接受][S5]、[S6]；[保存函数与主runner][S8]

现有`experiment.py::run`会初始化并训练两个模型，不能原样调用它却把任务报告成仅评价。新的最小路径应直接装载四个指定final模型，分别调用已经存在的canonical动作分支和native环境，显式使用新的evaluation-action随机域，不调用`learning.update`，不产生新优化器工作，也不因参数文件暂时不可读而重新训练替代。训练用采样路径已经实际运行；将其用于评价所需的RNG、计数及输出接线仍需适度检查。[learning.py][S7]；[experiment.py][S8]；[canonical封装][S10]

需要的检查只触及这个变化：装载的模型对应正确算法、原训练seed和round64；评价过程不更新参数；两种模式的实体、mask和物理命令合法对应；采样使用声明的独立评价随机域，不读未来或挑选结果；原生服务／需求仍生成正确主要读数；全部八个策略／模式单元及BCRH结果可读。复用已有N7环境、PPO和主要发布检查，不重做旧52／304行法则面板、全历史replay、所有candidate记录、跨平台bit一致或重复smoke。[CM复用边界][S14]；[证据规范§11.8.5—11.8.8][S17]

工程上不需要新的分布式、worker pool、resume、自动retry、registry或验证服务；保持普通2,000新增源码行、600行runner和既有测试预算，不因小任务另加框架。本轮明确保留已有解释器`-X faulthandler`的单次fatal事件栈观察，以便该真实运行路径再出故障时留下已有工具能给的事实；它不是定期profiling、根因定位前置或额外重跑。它及必要输出成本均在整次计时内。其他方向的对象限定例外及E01并行配置不迁移。[工程规范§3—§5][S18]；[原B01执行补充][S11]

HMAC异常、formal01的SIGSEGV及其core仍未唯一定位。两次完整同源运行不能证明这些问题消失；但当前已接受的主要读数也不因无唯一根因而被抹掉。若新评价实际遇到装载、奖励、信息或主要测量问题，保留其具体依赖缺口并停止，不把不完整结果写成八个单元全部完成，更不按剩余余额自动重试。[技术接受的限制][S5]、[S6]；[证据规范§11.8.7][S17]

run级统计工具已经正确描述了两个训练seed，本次无须再运行它来决定是否“够显著”。后续评价可用现有配对readout或小范围表格分析，先每个checkpoint、模式和分区聚合；模式、checkpoint和episode不能变成新的训练样本。无需为了提出这个问题新增工具测试、框架迁移或profiling轮。[既有统计输出][S3]；[scientific-tools说明][S22]

## 六、保留的历史与决策边界

旧跨N负面不能与当前N7同分布读数混合后断言训练roster是唯一原因；训练曝光和执行条件也曾改变。旧R09包的277／1,024个consistent-relabel失败仍限制其原价值归因；新的规范与当前两次有效运行不追溯改判它。特权`7/60`单世界witness、aggregate下界`7/960`、zone 1为0和zone 2为`7/480`保留为原先有限证据，不充当可学因果headroom。R03仍未完成，E01仍是已经结束的工程成本观察，不重开搜索或计时。[此前完整方法裁决][S15]；[当前DIRECTION的历史边界][S16]

本轮结束的是**为了当前64轮贪心终点比较而无差别填充同配置训练seed的这一续投方式**，不是证明MAPR无效、两算法等价，或关闭成员变化后的共享学习方向。下一观察的四个固定策略比较也只支持其声明的执行方式与新面板；若没有可用信号就结束这一小问题，不制造温度／seed／checkpoint梯级。未来有明确的新学习干预仍可按其自身价值提出，不必先通过该诊断。

本次是现有方向层的有界科学选择，不晋升C，不改Portfolio生命周期、优先级、融合、资源总额或既有`recasts=2`。新部署估计量已明确命名，但不是因调整诊断负担而自动增加机制recast。源码和运行接受仍由现有CM路径负责；不追加逐项所有者批准或新的验收层。[现行权限和规范优先关系][S20]；[当前方向记录][S16]

## 七、实际读取范围

本次科学来源统一读取于`CartmanFatass/My-paper-code`的固定提交`fda5174f6277fa8eadce950f9f6b2cb232ee12a4`。下面22条列明证据都已访问；“选段”不声称读过未列出的后续实现或它们引用的所有底层文件。长响应的必要截断部分已在相同路径、相同提交补读。任务文件按用户给出的固定版本读取；Issue正文与评论只用于核查交付是否存在，没有作为可变科学输入，也没有跟随其中的旧证据链接。

表中D表示`docs/research/candidates/variable_n_fleet_churn/`，E表示`experiments/candidates/variable_n_fleet_churn_n7_direct_b01/`。

| 实际读取文件 | 范围 |
| --- | --- |
| [AGENTS.md][S20] | 1—160行：权限、规范优先及委托相关部分 |
| [docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md][S17] | 1—175行及325行至文件末尾；包括完整§11.8—§11.9以及§11.4、§11.7 |
| [docs/project/ENGINEERING_SCOPE_SPEC.md][S18] | 1—125行：一般规则及预算，另见历史附款开头 |
| [docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md][S19] | 1—145行：一般要求全文及E01附款的配置／保护范围开头 |
| [docs/research/portfolio/PORTFOLIO.md][S21] | 开头至当前方向表，包括VNFC行；只取生命周期／优先级背景，不用旧执行文字覆盖新结果 |
| [D/DIRECTION.md][S16] | 1—165行：两种子当前结论及相关历史边界 |
| [D/pro_packets/20260905_validation_method_convergence/archive/RESPONSE.md][S15] | 全文 |
| [D/VNFC_N7_DIRECT_RETURN_B01_SCIENCE_CARD_20260905.md][S11] | 全文，含执行补充 |
| [D/VNFC_N7_DIRECT_RETURN_B01_SEED02_CARD_20260905.md][S12] | 全文 |
| [D/VNFC_N7_DIRECT_RETURN_B01_RESULT_INTAKE_20260905.md][S13] | 全文 |
| [D/VNFC_N7_DIRECT_RETURN_B01_TWO_SEED_RESULT_INTAKE_20260905.md][S1] | 全文 |
| [D/VNFC_N7_DIRECT_RETURN_B01_FORMAL02_TECHNICAL_ACCEPTANCE_20260905.md][S5] | 全文 |
| [D/VNFC_N7_DIRECT_RETURN_B01_SEED02_TECHNICAL_ACCEPTANCE_20260905.md][S6] | 全文 |
| [D/evidence/b01_two_seed_intake_20260905/two_seed_contrasts.csv][S2] | 全文 |
| [D/evidence/b01_two_seed_intake_20260905/independent_run_summary.json][S3] | 完整JSON |
| [D/evidence/b01_two_seed_intake_20260905/exposure_for_consultation.json][S4] | 完整JSON |
| [D/VNFC_N7_DIRECT_RETURN_B01_CM_HANDOFF_20260905.md][S14] | 全文 |
| [E/learning.py][S7] | 全文 |
| [E/experiment.py][S8] | 全文 |
| [experiments/candidates/variable_n_fleet_churn_bpcr_r09/torch_models.py][S9] | 全文 |
| [scripts/run_vnfc_bpcr_r02.py][S10] | 1—230行，包含canonical输入、forward及模型类构造；未读其余历史检查梯级 |
| [.agents/skills/hmasd-scientific-tools/SKILL.md][S22] | 全文；未读取其未列明脚本或外链 |

`PORTFOLIO.md`和Issue里仍有早期“尚无正式运行”的执行文字；本轮采用固定版本中完整两种子intake及技术接受作为科学事实，不把早期状态当作新阻塞。已接受结果的完整底层episode读回是CM和独立读者的记录，本次不声称自己重新解析了全部episode或重开了远端checkpoint。

没有列明路径、固定ref或连接器访问缺口。剩余未知是：四份参数装载到新评价入口的实际完成状态、单次采样的原生后果、完整新调用时间、BCRH逐字段信息差异、旧异常根因及总体训练变异。这些未知分别限制其相关主张，不要求先证明整个方向成功或完成精确upper。此次咨询新增训练、更新和评价曝光均为零；本文的下一观察是科学选择，不是已经执行的实验。[咨询曝光记录][S4]

[S1]: https://github.com/CartmanFatass/My-paper-code/blob/fda5174f6277fa8eadce950f9f6b2cb232ee12a4/docs/research/candidates/variable_n_fleet_churn/VNFC_N7_DIRECT_RETURN_B01_TWO_SEED_RESULT_INTAKE_20260905.md
[S2]: https://github.com/CartmanFatass/My-paper-code/blob/fda5174f6277fa8eadce950f9f6b2cb232ee12a4/docs/research/candidates/variable_n_fleet_churn/evidence/b01_two_seed_intake_20260905/two_seed_contrasts.csv
[S3]: https://github.com/CartmanFatass/My-paper-code/blob/fda5174f6277fa8eadce950f9f6b2cb232ee12a4/docs/research/candidates/variable_n_fleet_churn/evidence/b01_two_seed_intake_20260905/independent_run_summary.json
[S4]: https://github.com/CartmanFatass/My-paper-code/blob/fda5174f6277fa8eadce950f9f6b2cb232ee12a4/docs/research/candidates/variable_n_fleet_churn/evidence/b01_two_seed_intake_20260905/exposure_for_consultation.json
[S5]: https://github.com/CartmanFatass/My-paper-code/blob/fda5174f6277fa8eadce950f9f6b2cb232ee12a4/docs/research/candidates/variable_n_fleet_churn/VNFC_N7_DIRECT_RETURN_B01_FORMAL02_TECHNICAL_ACCEPTANCE_20260905.md
[S6]: https://github.com/CartmanFatass/My-paper-code/blob/fda5174f6277fa8eadce950f9f6b2cb232ee12a4/docs/research/candidates/variable_n_fleet_churn/VNFC_N7_DIRECT_RETURN_B01_SEED02_TECHNICAL_ACCEPTANCE_20260905.md
[S7]: https://github.com/CartmanFatass/My-paper-code/blob/fda5174f6277fa8eadce950f9f6b2cb232ee12a4/experiments/candidates/variable_n_fleet_churn_n7_direct_b01/learning.py
[S8]: https://github.com/CartmanFatass/My-paper-code/blob/fda5174f6277fa8eadce950f9f6b2cb232ee12a4/experiments/candidates/variable_n_fleet_churn_n7_direct_b01/experiment.py
[S9]: https://github.com/CartmanFatass/My-paper-code/blob/fda5174f6277fa8eadce950f9f6b2cb232ee12a4/experiments/candidates/variable_n_fleet_churn_bpcr_r09/torch_models.py
[S10]: https://github.com/CartmanFatass/My-paper-code/blob/fda5174f6277fa8eadce950f9f6b2cb232ee12a4/scripts/run_vnfc_bpcr_r02.py
[S11]: https://github.com/CartmanFatass/My-paper-code/blob/fda5174f6277fa8eadce950f9f6b2cb232ee12a4/docs/research/candidates/variable_n_fleet_churn/VNFC_N7_DIRECT_RETURN_B01_SCIENCE_CARD_20260905.md
[S12]: https://github.com/CartmanFatass/My-paper-code/blob/fda5174f6277fa8eadce950f9f6b2cb232ee12a4/docs/research/candidates/variable_n_fleet_churn/VNFC_N7_DIRECT_RETURN_B01_SEED02_CARD_20260905.md
[S13]: https://github.com/CartmanFatass/My-paper-code/blob/fda5174f6277fa8eadce950f9f6b2cb232ee12a4/docs/research/candidates/variable_n_fleet_churn/VNFC_N7_DIRECT_RETURN_B01_RESULT_INTAKE_20260905.md
[S14]: https://github.com/CartmanFatass/My-paper-code/blob/fda5174f6277fa8eadce950f9f6b2cb232ee12a4/docs/research/candidates/variable_n_fleet_churn/VNFC_N7_DIRECT_RETURN_B01_CM_HANDOFF_20260905.md
[S15]: https://github.com/CartmanFatass/My-paper-code/blob/fda5174f6277fa8eadce950f9f6b2cb232ee12a4/docs/research/candidates/variable_n_fleet_churn/pro_packets/20260905_validation_method_convergence/archive/RESPONSE.md
[S16]: https://github.com/CartmanFatass/My-paper-code/blob/fda5174f6277fa8eadce950f9f6b2cb232ee12a4/docs/research/candidates/variable_n_fleet_churn/DIRECTION.md
[S17]: https://github.com/CartmanFatass/My-paper-code/blob/fda5174f6277fa8eadce950f9f6b2cb232ee12a4/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[S18]: https://github.com/CartmanFatass/My-paper-code/blob/fda5174f6277fa8eadce950f9f6b2cb232ee12a4/docs/project/ENGINEERING_SCOPE_SPEC.md
[S19]: https://github.com/CartmanFatass/My-paper-code/blob/fda5174f6277fa8eadce950f9f6b2cb232ee12a4/docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md
[S20]: https://github.com/CartmanFatass/My-paper-code/blob/fda5174f6277fa8eadce950f9f6b2cb232ee12a4/AGENTS.md
[S21]: https://github.com/CartmanFatass/My-paper-code/blob/fda5174f6277fa8eadce950f9f6b2cb232ee12a4/docs/research/portfolio/PORTFOLIO.md
[S22]: https://github.com/CartmanFatass/My-paper-code/blob/fda5174f6277fa8eadce950f9f6b2cb232ee12a4/.agents/skills/hmasd-scientific-tools/SKILL.md
