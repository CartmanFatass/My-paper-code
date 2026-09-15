**选择 A：以有界、仍不确定的 B/EXPLORE 结论结束本轮 baseline × interruption 探索及其原样延长，不选择新的实验对象。** 结题标签为 **CLOSE_OBJECT——本轮已声明配方、宿主和十五轮预算的探索阶段结题**，不是“续约无效”、FLAT 稳定胜出、等效或整个 FSD 关闭。十五轮高 batch 续约主量为 +.0098374427 J，重要性读数是 `small_signed`，但区间仍同时容纳有意义的正、负效果；两个未调优跨信息包差都负向指向，区间也包括零。现有记录足以结束这一次投入，并不足以把任何一种方法改成已证优胜者。（[本轮完整结果，Result and rule applied verbatim][result]；[机器读数，primary、contrasts][numbers]。）

我不采纳 DM 的 B 推荐。一个 FLAT 配方筛选可以是合法的开发性 B，但所提“三个设置、每设置一个 fit、唯一最终面板”既不消除私有 FLAT 与中央条件技能路径的信息差异，也不能凭选出的有限终点交付所声称的首个同信息 headroom。将其准确改称小规模 FLAT 配方探索后，它仍有潜在用途；本轮却没有足够理由把中断研究的下一步转成这项筛选，或把筛选设为所有后续工作的必经前置。C 可以增加固定十五轮对比的精度，D 可以提出不同预算的问题；我没有把它们判成无信息，只是不选择这一次追加投入。以下给出完整比较理由，而不是要求先取得一个更强结论才允许研究。（[DM intake，Decisions this intake produces][intake]；[信息审计][prep]；[规范 §§11.7–11.11][spec]。）

**Authentic D0 继续默认；2026-09-12 U 的五轮、完整 I1280 可选用途范围不变；已完成两块 factorial 的原读数不变。** 本次不改 FSD 的 ACTIVE/HIGH、席位、优先级或 Portfolio 生命周期。“无下一对象”只描述这个问题在本轮的研究选择，不释放席位，也不撤销任何不依赖本对象的已授权工作。（[U 完整答复，§§一、二、六][u]；[当前 Position][direction]。）

## 一、结题的准确范围与可以保留的声明

本次结束的是：Scenario 1，固定六架 UAV、五十用户，H500、J=6U/500，既有 CPU FP32／四线程学习路径下，FLAT／D1280／I1280 的声明配方，四个新训练块、十五次 16-lane rollout，以及预先声明的第 5、10、15 轮面板所组成的探索阶段。既不扩大到所有训练长度、阈值、flat 实现或层次方法，也不把另一个预算的问题宣布为经验阴性。（[原卡 §§2–3、8–9][card]。）

可用于本轮 intake 的结题措辞是：

> 在四个独立训练块的固定十五轮终点，高 batch 下 I1280−D1280 的平均点估计为小幅正向，按原 .05 J 重要性规则为 small_signed；训练块层面的工作模型区间包括零，且不在 ±.05 J 内，故大小与方向仍未充分分辨。D1280−FLAT 与 I1280−FLAT 的平均点估计负向，未达到原卡“负差且区间排除零”的较强读法；它们是未调优跨信息包差，不是同信息 headroom。阶段结题保留全部原始观察，不以新增原样块、FLAT 筛选或更长训练自动接续。此结论不证明任何方法等效或稳定优劣。

这里的“结题”有实际含义：不再把本轮 S 视作尚未完成的比较，不用较早面板代替十五轮主量，也不选择下一 tranche 或预算延长来修饰结果。它是接受剩余不确定性的研究取舍，不是声称剩余问题不存在。两条主张明确没有被本轮建立：一是额外续约在十五轮有稳定、值得默认采用的收益；二是技能包在这个预算上胜过私有 FLAT。反过来，“这两条主张尚未建立”也不等于其反命题已经成立。（[结果，主量与全部 contrasts][result]；[规范 §4、§7、§11.11][spec]。）

## 二、原规则：重要性和不确定性分别读取

本轮以原卡 §8 和已经确认的 FLAT k 修正为准，不采用卡前部尚未更新的六块、headroom 或复合显著性措辞。实际对象是十二个原始 fit、四块；FLAT 是 `off → mappo → k=10`。k=10 的决定性理由是匹配 actor／critic 的梯度截断长度，而不是此前已经撤回的“长 k 不可运行”。它没有消除执行信息差异。（[Portfolio S 完整决定][investment]；[卡 §8][card]；[12:55Z 确认记录][flat-correction]。）

以下数值来自已发布 reducer，不是本轮重算。区间为 iid-normal block-contrast 工作模型下的 Student-t 95% 区间，四块时 df=3；模型覆盖率没有被现有小样本验证。

| 十五轮对比 | 块均值 J | 样本 SD | 均值 SE | 工作模型区间 | 正确读法 |
| --- | ---: | ---: | ---: | --- | --- |
| SI1280：I1280−D1280，主量 | +.0098374427 | .0788586533 | .0394293267 | [−.1156424464, +.1353173319] | small_signed；interval_includes_zero；interval_inside_mei=false |
| GAP_D：D1280−FLAT | −.0452634555 | .0563425387 | .0281712693 | [−.1349157030, +.0443887921] | 未调优跨信息包差，负向点估计，区间含零 |
| GAP_I：I1280−FLAT | −.0354260128 | .0931173391 | .0465586696 | [−.1835943228, +.1127422972] | 未调优跨信息包差，负向点估计，区间含零 |

来源：[RESULT_SUMMARY.json，contrasts、primary][numbers]。GAP_D／GAP_I 没有被另行赋予主量的 .05 J MEI；对 GAP_D 的事前区间预测也不是它的科学分支。主量 .05 J 是已经选择的、考虑额外学习成本的发展目标，不是要求效果大于某个 SD，也不是 .05 的效果必须显著才“存在”。原对象重要性和不确定性分开报告的规则完整保留。（[卡 §4 经 §8 修订][card]；[FLAT 修正记录][flat-correction]；[规范 §11.11][spec]。）

### 全部块和面板不能用均值遮住

| 训练块 | SI1280 第5轮 | 第10轮 | 第15轮 | GAP_D 第15轮 | GAP_I 第15轮 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 772203 | +.05508808 | +.07618917 | +.09835977 | +.00423585 | +.10259562 |
| 772303 | +.14073948 | +.10539972 | +.04471497 | −.10792924 | −.06321428 |
| 772403 | −.00679584 | +.12837682 | −.08340338 | +.00043235 | −.08297103 |
| 772503 | +.01002085 | −.10265063 | −.02032159 | −.07779277 | −.09811436 |

这张表保留正向、反向及变号路径；完整三臂、四块、三个面板的全部 arm scores 和另外两个差值的逐面板记录仍由原结果和机器文件逐项保留，不选择其中一个面板或子集重新判定。（[结果，All endpoints、Contrasts per rollout][result]；[机器 blocks][numbers]。）

四块 SI1280 的面板均值依次为 +.0497631425、+.0518287708、+.0098374427 J。第 5 轮点估计仍低于 .05，第 10 轮略高于 .05，但二者均是事先声明的中间观察，不是可以替换主量的“真实效果”。十五轮各臂平均点估计为 FLAT .451037、D1280 .405773、I1280 .415611 J。这里只能说本次点均值的排序不利于技能包，不能据此切换默认方案。（[结果，All endpoints 的 four-block mean 行][result]；[机器 contrasts][numbers]。）

## 三、对 DM 三个推断的保留与收窄

**第一，“续约优势到十五轮未保持”可以保留为已观察均值的描述，不能扩成一般的训练越久越差。** 772203 的点对比持续上升，772303 下降，另外两块变号。现有结果没有给出新的跨面板均值差区间，本轮也不计算它。因此，“均值变小”和“已经识别稳定衰减规律”是不同结论。上述路径支持不把早期增益外推到十五轮，而不是支持任意未来预算的负面预报。（[intake，Scientific reading 第1点][intake]；[结果逐面板表][result]。）

**第二，“FLAT 不低于技能包”必须限制到这次观察到的平均点估计。** GAP_D、GAP_I 的区间都包括零；原卡“负 gap 且区间排除零”分支并未达到。本轮不能说 FLAT 已经被证明非劣、等效或稳定更好。较小信息通路的 FLAT 在这些点观察中有竞争力，确实削弱了当前技能包价值的乐观解释；但有限训练下，给 flat actor 更多信息可能帮助也可能妨碍学习，私有 FLAT 的得分不为一个尚未测试的 central-input flat 实现提供单调性能保证。Portfolio S 决定已经明确了这个限制。（[intake，第2点][intake]；[investment，Three design choices][investment]。）

**第三，保留明显的轨迹内运动，不接受“已经证明轨迹内变动主导、所以更多训练块无用”的归因。** FLAT 772503 的 .312032→.530132，以及 D1280 同块 .439014→.506588→.452340，是同一个训练过程在不同更新位置产生的不同策略的面板读数，不是同一固定策略的重复测量。它们显示这些检查点没有共同稳定排序；它们本身不是对方差来源的分解。（[intake，第3点及 continuation 理由][intake]；[结果 All endpoints][result]。）

在固定第十五轮这个估计目标下，初始化、探索、数据和优化共同决定整条学习路径；不同训练实例在共同终点处于不同状态，本来就是完整训练实例变异的一部分。每块有限评价面板还带来条件误差。不能仅因轨迹内摆动大于约 .008–.021 J 的条件对比 SE，就把训练块 SD 分解为“seed 部分”和一个独立的“轨迹相位部分”，或宣称某部分占主要比例。跨时间变化的误差还取决于配对和相关性，不能把单面板 SE 直接当作变化量的 SE。本轮不拟合这种分解，也没有据此识别优化未收敛的唯一原因。（[机器各 block 的 by_rollout 条件 SE][numbers]；[规范 §§11.8.3、11.11][spec]；[双轴方案 §3][programme]。）

**更多独立块仍可能提高固定十五轮平均对比的精度；它们不会让每一条学习轨迹变平，但也无需先让轨迹变平才有一个有效的固定预算 estimand。** 同样，更多训练轮数也不保证更窄的跨块分布。本次不选择 C 或 D，依据是下一观察对当前取舍的价值和实际工作，而不是把这两种有用但不同的研究目标宣布为统计上不可行。

## 四、保留完整学习包含义、最强支持和最强反证

D1280／I1280 均保留六个团队／个体 latent、固定团队 k10、个体与团队 cap10、团队 gap 为无穷、age off 和逐 primitive step 响应的私有 recurrent actor。两者的主要配置差异是个体 gap 的无穷与 .25；共同 coordinator batch 为1280。续约改变真实决策、段长／credit、所收集的行、优化分组的实际输入和后来策略，因此 SI1280 是**固定 batch 设置下的实现路径 simple effect**，不是只隔离物理时机的效应。（[卡 §2][card]；[factorial，Native meaning][factorial]。）

FLAT 则是常数单技能、学习私有 actor 和中央 critic、coordinator 与两种 discriminator 都不更新的同栈 reduction；coordinator 为赋常数技能仍可有前向调用，不能把“零 coordinator 优化”写成“该网络完全不被调用”。三臂都实时响应原生观察，held skill 并不使 D1280 保持固定速度。技能路径能把中央 state／joint observations 经 skill 带到行动中，而 FLAT 的中央 critic 只是训练输入；相同宿主、critic 或数值精度不等于相同执行信息。（[卡 §§2、8][card]；[prep，Baseline information audit][prep]；[flat-correction][flat-correction]。）

原生链仍是：自身及队友运动改变固定成员的局部服务几何；合法协调输入和既有 skill 状态决定是否重选；各自 recurrent actor 输出连续运动；native coverage／quality／altitude reward 和本臂数据进入保留的 primitive-time discount、terminal、credit 与 PPO 路径。没有新成员变化、观察到达时钟或外接公共 lease mask。FLAT 的不同信息路径以及高层学习／内在项的有无均属于 GAP 的完整包差，不应归成“层次结构本身”的净贡献。（[prep，信息审计][prep]；[卡 §2][card]；[factorial，Native meaning, exposure and cost][factorial]。）

**支持继续研究的最强当前证据**是 772203 的十五轮 SI1280 +.09835977 J、同块 I1280−FLAT +.10259562，以及 772303 保留的正 SI1280 和早期几个正面板。六块 rollout-5 描述性累计也仍正向指向。这些事实意味着潜在收益没有被一条普遍反证消灭，足以让新的有用途问题继续合法；不能因为选择结题就删除它们。（[result][result]；[numbers，rollout5_accumulation][numbers]。）

**反对继续原样发展的最强证据**是 772403 的十五轮 SI1280 −.08340338 J、另一块的负值、两个包差在终点的负向均值，以及 I1280 的较大实际工作。十二个 fit 提供了此前没有的 flat 比较和较长预算读数，却没有给出把这个十五轮续约配置继续作为发展重点的强点向收益。尤其不能用第五或第十轮的读数回避第十五轮。这个反面记录支持停止本轮追加，而不是支持稳定 D0／FLAT 优势或所有续约方法无价值。（[result，Contrasts、Resources][result]。）

## 五、为什么 A 优于本次给出的 B、C、D

### B：不把一个合法的小筛选，包装成它不能交付的 headroom

对 B 有三个必须分开的层次。

一是**有限开发筛选**：在同一私有 FLAT 信息结构下，前瞻改变三个 learning-rate 或 entropy 设置，各训练一次、报告每个终点，是允许的 B。每设置只有一个 fit，会把设置差别和各自学习实例的差别混在一起；即使用共同外生安排也不能凭一个训练块获得跨训练实例精度。它仍能给开发提供局部候选，不必先取得显著性、重复正值或基线认证才能运行。

二是**选出的参照水平**：若用同一批结果选最高者，其得分包含选择暴露，不能被改称典型的、稳定的配方水平。保留全部结果与选择规则可使这一开发事实诚实可用，但不能消除有限选择的不确定性。这个问题不会因为当前未调优 FLAT 的点均值较高而消失。TASK 提到的 ACVC 异议在这个推断层面同样适用；ACVC 原答复不在本次 manifest 中，我没有读取或借用其未提供的具体理由。（[本轮 TASK，选项B][task]；[规范 §§11.8.3–4、11.11][spec]。）

三是**§11.7 headroom**：当前提出的私有 FLAT 调参不改变 actor 信息，仍与中央条件技能包跨信息；也没有同时给出一个在适当比较条件下成立的上参照。规范定义的 headroom 需要明确上参照和调优的同信息 generic baseline，连同 seeds／curves 的含义。它不要求把 baseline 证明为全局最优，但也不是给一个最高被选终点改名便成立。把 FLAT 变成 central-input actor 则是信息接口和方法问题的实质变化，不是仅更改学习率。（[规范 §11.7][spec]；[prep 的三种 baseline 候选][prep]；[investment 的 GAP 修正][investment]。）

**因此我拒绝的是本轮 B 所声称的用途及其作为下一步的优先价值，不是一般拒绝小样本调参。** 未调优 FLAT 已有真实同宿主、同交互量的比较记录；本轮无需先把它调得更高，才能承认十五轮技能包的点向差距。若 B 只返回更高的 FLAT 被选终点，它增加开发线索但不解决同信息问题；若更低或分散，也不推翻已经完成的 FLAT 点观察，更不证明技能包胜出。它对当前“是否延长这轮续约包发展”的增量有限。将题目另改为实际选择一个 FLAT 使用配方可能有价值，但本轮没有选择那个新发展目标。

这也不是以 headroom 缺失为停止理由：缺失继续如实记录，既不等于零，也不强迫先完成一套 sweep。双轴方案的 baseline 准备优先没有把每个后续对象变成等待基线通过的批次，已经完成的 S 也提供了真实、虽非同信息的基础比较。当前不选 B 不取消更广的 baseline 研究问题。（[programme §§2–5][programme]；[spec §§11.7、11.9、11.11][spec]。）

### C：重复能改善精度，但本轮不购买新的精度目标

C 可以用更多独立块缩小固定十五轮对比的不确定性；当前 CI 很宽，所以它是认真可考虑的备选。我不采纳 DM 所说“轨迹运动不被消除，所以更多相同块没有价值”的理由，也不把四块当作足够数量的定理。

但它会继续购买同一已明确的有限终点问题，尚未带来一个需要更精确决定的默认切换或开发选择。当前主量小正、包差负向、I 工作更多，而默认和五轮可选范围可以在如实保留不确定性的情况下维持。选择 A 接受仍不能区分某些 .03–.05 J 效果的代价；不是要求先证明没有效果才能停止。若以后选择一个具体精度目标，原卡明确规定额外 tranche 是新的 Portfolio 投资问题，本次没有选取块数或累计停止规则。（[card §8][card]；[investment，Endpoints, independence and accumulation][investment]。）

### D：三十轮可以定义新终点，但不能许诺稳定排序

一个固定三十轮、所有面板保留的真实比较是合法的不同预算 B。它能观察十五轮之后的表现，不必先证明“早期欠训练”是原因。可是“等到 .1–.2 J 的运动停止再判排序”不是一个已经定义好的有限 endpoint；三十轮也没有保证轨迹变平。若按事后最平的区间或最好面板挑选，问题又变成选择过的停止／checkpoint 规则，不能继续沿用固定终点的声明。

将 D 准确限定为三十轮对比后，本轮仍没有足够具体的用途使我选择近似翻倍的单 fit 工作。S 已把五轮延长到十五轮，并显示不同块不是共同地向同一个排序靠拢；这不证明三十轮无益，却削弱了“再延长一次就会解决排序”的依据。用更少块换更长轨迹还减少独立训练信息。此处不选 D，而不是把“收敛已证明”设成 D 的启动门槛。（[result，全部曲线][result]；[task，选项D][task]；[spec §§11.8–11.11][spec]。）

### 未列对象：存在不同问题，不自动成为更高价值的接续

准备记录中的 direct fixed-k HMASD versus central-input flat 是真正不同的同信息方法问题。私有 FLAT 的好分数不能逻辑上否定它，也不能直接验证它；新的 actor 输入、ego identity 及实际接口需要自己的明确方法定义。另一方面，当前记录没有表明该问题在这一节点比结题具有更高净价值，也没有给出新接口的已测成本。它不是给 B 的“same-information”标签补一句话便完成的修改。（[prep，Baseline information audit and bounded work plan][prep]。）

同理，重新加入低 batch 因素可追问 factorial 的依赖线索，但这会重新购买别的比较，不能因为 S 未测 MB／INT 就自动安排。没有选择新信息结构、阈值搜索、beam／best-of-many、全轨迹诊断或 another source census。不存在本轮暗含的第五个对象。

## 六、工作量和普通成本计划的比较

### 已完成 S 的费用与有效性

每个原始 fit 完成 120,000 个训练 team steps、240 个训练回合、15 个 update stages、三个 32-world H500 面板即 48,000 个评价 steps、2 次 learner/evaluator 构造；十二个 fit 合计 **1,440,000 训练＋576,000 评价 steps，180 update stages，24 models**。这是四个独立训练块的比较，不是十二个独立的主量样本，更不是 36 个面板或 1,152 个评价回合的训练重复。（[result，Counts, receipts and integrity][result]。）

Actor 和 critic 在每个 fit 各有 33,750 次 optimizer calls；D1280 coordinator 为225，I1280 依块为960／1065／990／1050，FLAT 为0；两类 discriminator 在 D/I 中继续更新、FLAT 为0。共同 actor 更新次数没有让全部训练计算匹配。初次队列 quoting 问题的既有核对保留：没有已经存在的 I 进程被重复运行，没有替代或补选结果。技术接受和科学效果分别成立，本轮没有复跑验证。（[result，Counts、Deviations][result]；[intake，What was checked][intake]。）

| 原臂 | 四个 whole-command wall，秒 | 已记录臂总和，秒 |
| --- | --- | ---: |
| FLAT | 2022.50／2589.24／2551.63／2594.40 | 9757.77 |
| D1280 | 2642.05／2637.78／2617.32／3428.12 | 11325.27 |
| I1280 | 6369.48／6550.17／6353.28／5045.10 | 24318.03 |

总和 **45,401.07秒**。原 24,000–30,000秒是普通计划，不是 cap；当前运行有三至四个本对象 fit 及其他已记录工作竞争资源。不能把超出计划记成失败，不能把 summed wall 当整个研究 elapsed，也不能把这些竞争条件下的数值当未来串行速率。峰值 RSS 按原报告约为1.2／2.8／3.8 GiB，每个实际调用的物理／有效可用内存均通过≥4 GiB 准入；峰值 RSS 本身不是未来准入凭据。（[result，Resources][result]；[spec §11.8.1][spec]。）

### 未选备选的主导规模

下表只是由候选定义展开的**前瞻工作算式**，没有运行代码、重分析历史结果或分配新预算。

| 备选规模 | 训练 team steps | 评价 team steps／panels | Update stages／模型构造 | 实测成本能提供的参照 |
| --- | ---: | --- | --- | --- |
| B 示例：3个FLAT设置、各1 fit、15轮、sole-final | 3×15×16×500=360,000 | 3×32×500=48,000／3 panels | 45／6 | 现有FLAT每fit2022.50–2594.40秒包含3面板；不能冒称sole-final新成本或逐面板可减的固定费用 |
| C：每追加1个三臂训练块、15轮、3面板 | 360,000 | 144,000／9 panels | 45／6 | 原三臂whole-command记录可作同形工作锚；新竞争、轨迹与完整支持费用未知 |
| D：每1个三臂块、30轮、每5轮一面板 | 720,000 | 288,000／18 panels | 90／6 | 约2×同形单fit费用仅是情景；不保证未来renewal rows、优化量或wall按比例变化 |

B 的设置尚未选择，D 的训练块数也未选择；表中“每块”不构成隐含拨款。三个方案均有真实 collection／PPO／evaluator 工作，没有本题要求的嵌套候选轨迹搜索；增加面板与增加训练块的科学作用不同。I 的 coordinator 工作受实际 joint rows 影响，不能只按 fit 数认定它与 FLAT 同价。（[task，备选定义][task]；[card §5][card]；[result，实际 counters 与 whole-command wall][result]。）

这些工作并非已知超预算，也不是因为昂贵就科学上不合法。我选择 A 的主要原因是当前下一问题的决策价值不足，而成本使继续询问必须有更具体的用途；不凭有限性认定便宜，也不以小样本无法“认证”为由否定一切开发。普通估算可由 DM 根据实际条件调整，不把新的 profiling 或 timing probe 作为 prerequisite。（[spec §§11.8.1、11.9][spec]。）

**本轮选择的新科研工作为零。** 没有新 fit、model/load、科学 RNG、训练或评价 steps、optimizer update、test、profiling、checkpoint replay 或数值重分析。文档、连接器、provider 和作者工作不是零成本，其完整费用未测；不从原 S 的 ordinary plan 推出可结转余额。本节点没有新增 hard cap、科学运行或 Portfolio 投资申请。

## 七、factorial、累计与 U：不混合三个不同问题

**原两块 factorial 保留其原 .01 J 读法。** 高 batch simple effect 为 −.026440300139166675 和 +.08464985087421936 J，原平均 +.029104775367526342、SD .0785525991、SE .0555450755，原 df1 区间约 [−.67666233,+.73487188]。它仍是原卡的局部正均值信号，具有一个 adverse block 和很弱的训练精度。当前 .05 J 不追溯改变该分支。（[factorial，Result and rule applied verbatim][factorial]。）

MB 均值 −.00280123、INT 均值 −.03983204 及原各块符号全部保留；两块 factorial 的多个对比共享同一批 fit，不是多个独立实验。S 去掉低 batch 两臂只缩小了新问题，不能据此宣布 batch 等效、interaction 已定或纯 duration attribution 成立。（[factorial，All newly trained endpoints and factorial contrasts][factorial]；[investment，Why S][investment]。）

**当前已经允许的 rollout-5 累计只按原 reducer 报告：**

| 组 | SI1280_5 均值 J | 原工作模型区间／限制 |
| --- | ---: | --- |
| S 新四块 | +.0497631425 | [−.0553179867,+.1548442717]，df3 |
| 已完成 factorial 两块 | +.0291047754 | 原两块精度很弱，单独先报告 |
| 六块描述性累计 | +.0428770201 | [−.0232011546,+.1089551949]，df5；SD .0629649931、SE .0257053508 |

累计是**结果知情的描述性积累**，不是 prospective independent confirmation，也不是用旧模型重做的结果。区间包括零，并非已经紧贴或排除零。本轮没有添加其他面板或 U 五对，没有计算新的 pooled primary。原 factorial 和当前 reducer 对历史组区间各保留其既有数值口径，不在本次重新归约。（[numbers，rollout5_accumulation][numbers]；[card §8][card]。）

**U 的对象则是 I1280 对 authentic D0／batch128 的完整包用途，不是 I1280 对 D1280 的 simple effect。** U 的五个原差值 +.0569774672、+.2062859041、−.0124304306、+.0125548057、+.0737976492 及各自 .01 J 分支、条件不确定性、adverse worlds、额外成本全部保留。其“同宿主、同配方、五轮预算的有限可选方案，D0 默认”继续成立于该原用途范围。（[U，§§一–三][u]。）

当前十五轮 S 没有同预算 D128 臂，不直接重新检验 U 的原包对比；六块 SI1280_5 也不能被偷换成 U 的复现。新的结果使“U 的认可可外推到十五轮、归于续约或代表胜过 FLAT”的措辞更没有依据，但这本来就不在 U 的许可范围。**保留旧结论与增加新限制可以同时做到，不需撤回一个未曾作出的强声明。** Authentic D0 留作默认不是用本轮 D1280 自动替换其配方，也不是将 FLAT 的点排序改成默认政策。（[u][u]；[card §§2、8][card]。）

## 八、结题边界、重新打开的事实与当前权限

本轮最终科学选择是 A，不把“再选哪个机制／实验”留给 Root 补写。立即应在既有 intake 中保留：完整 S 已完成、上述原规则和推断收窄、当前不选择 B/C/D 或其他对象、factorial 和 U 的边界不变。没有必要另造一个“不确定性解决后才能结题”的门槛。

需要明确一个实际的现行规范边界：本轮采用的 **§8.1 和 §11.9 将 Direction Pro 定义为独立科学审阅，将最终方向／家族／生命周期解释交给 Portfolio**。因此，TASK 的泛化“Direction 决定”措辞在这里落实为明确的 A 科学审阅选择和 CLOSE_OBJECT 范围；它不是本节点另作 Portfolio 的永久家族关闭、PARK_DIRECTION、CLOSE_DIRECTION 或席位决定。DM 对本完整意见进行现有 intake，涉及正式方向家族停启或争议解释时按该既有权限处理；普通范围内研究并不因本意见新增长期的逐实验审批层。本轮既不发起新的 Portfolio 请求，也不以此权限澄清代替科学回答。（[spec §§8.1、11.9][spec]；[task，scope][task]。）

A 中的 “ACTIVE-idle” 只可表述为**本问题当前没有选定的新对象**，不能被当成已修改的资源／生命周期字段。当前 FSD ACTIVE/HIGH 和 occupied slot 不由本响应改变。若要永久停止整个 renewal-versus-flat 机制家族，现有 B 证据及本轮权限都不支持把它静默扩写进去。

**具体重新打开的事实**应改变实际研究选择，而不只是改变日期或增加一个可运行命令。例如，出现一个需要在明确三十轮预算下选择既有方案的真实使用需求；出现已明确合法执行信息、实际方法定义及完整普通成本的同信息比较需求；另行合法取得的可信结果或实际 reward／信息／learner 依赖事实实质改变现有解读。这些情况可触发一个新的、如实标记为结果知情的问题。它们不是现在预约的实验，也不要求先完成一轮阳性试验、完整诊断或 headroom 认证才允许提出问题。

没有新用途或事实时，不为了把区间或符号变得整齐而恢复相同阶段。新的独立块可以被重新论证，训练长度也可以另定；其价值需对应当时要作出的选择，而不是被本次结题永久禁止或自动承诺。

## 九、实际固定来源访问与局限

本次通过 connected GitHub connector 读取了以下 **12 个 manifest 科学／方法路径**，有效版本均为 `a8b0e332ea68554de7a1b07bf037d8469c228884`；TASK 另在指定 `76af8709713ae71fb9d398a4998c5558a5f4b143` 读取。文中链接均固定到相应来源，不以交付分支替代证据版本。

| 实际读取路径 | 使用范围 |
| --- | --- |
| [FSD_BASELINE_INTERRUPTION_B01_INTAKE_20260915.md][intake] | 全文；规则、三项推断、成本／预测、选项和当前边界 |
| [FSD_BASELINE_INTERRUPTION_B01_RESULT_EVIDENCE_20260915.md][result] | 全文；三臂四块三面板、全部对比、累计、计数、资源和偏差 |
| [baseline_interruption_b01_20260915/RESULT_SUMMARY.json][numbers] | 分段读至文件末尾；每块各臂分数、条件 SE、aggregate、primary、累计及 source 字段 |
| [FSD_BASELINE_INTERRUPTION_B01_PROSPECTIVE_CARD_20260915.md][card] | §§2–5、7–9及相邻来源说明；以已应用 §8 与确认修正为准 |
| [Portfolio S archive/RESPONSE.md][investment] | 完整 S 选择、FLAT/GAP/MEI/累计修正、成本和 no-extension |
| [2026-09-15-fsd-flat-k-correction.md][flat-correction] | 全文；确认 k10 的实际理由与原比较不变 |
| [U archive/RESPONSE.md][u] | 完整实质结论及相关范围；配方、原五对、用途限制、完成与复议边界 |
| [FSD_INTERRUPTION_BATCH_B01_RESULT_EVIDENCE_20260915.md][factorial] | 完整两块 factorial 结果、原规则、所有对比、暴露与局限 |
| [FSD_RESTART_PREPARATION_INTAKE_20260914.md][prep] | baseline construction、信息审计和三种候选方法的有界工作计划 |
| [DIRECTION.md][direction] | Scientific question 和 Position 顶部的 S／factorial／U 段落 |
| [MARL_EMPIRICAL_EVIDENCE_SPEC.md][spec] | 题定 §4、§7、§8.1、§11.4、§§11.7–11.11 |
| [TWO_AXIS_RESEARCH_PROGRAMME_20260914.md][programme] | §§2–5；基线、独立训练、因果和用途负担的校准 |

表中 FSD 简写路径的前缀为 `docs/research/candidates/flexible_skill_duration/`，其余完整路径见固定链接。一次 programme 定位读取越过文件末尾而返回空，随后所需 §5 已在正确范围读到；不存在该来源不可访问的问题。Issue10 正文、历史评论、分支和目标路径只为核对交付与避免重复而读取，不构成新的科学来源或运行授权。

本判断依赖原 accepted intake 和已提交 reducer 对实际 source、计数、评价及比较完整性的记录。我读了这些记录，没有重新执行 reducer、审查未列出的 runner／agent 实现、展开原 fit 目录或加载模型；前瞻工作表达式也不是新实验结果。TASK 所述 ACVC 观点没有被冒充为独立读过的 ACVC 原答复；未展开任何未列文献或历史证据树。旧上传的 E3/E4 packet 不替代本轮固定 TASK。

所有本题需要的列出来源均可访问。没有由访问缺口迫使的停止；科学选择 A 来自上述证据和下一问题价值。必要的具体收窄是：FLAT 点排序不等于非劣结论，曲线运动不等于方差分解，私有 FLAT 调参不等于同信息 headroom，Direction review 不替代 Portfolio 的方向最终权限。它们不损坏已接受的原始结果，也不要求修改规范或补做实验才能完成本节点。

**给主人的建议：本轮按 A 结题，保留不确定性而不追跑；D0 不退位，五轮可选 I1280 不越界。** 最有用的新事实已经是第一组真实 flat 对比及早期差异没有在十五轮均值上保持的观察。最重要的未知仍是更广训练实例／预算下的收益与同信息方法价值；目前不把这些未知自动变成三设置 sweep、追加块或三十轮计划。这个结题是停止一次扩展，不是宣布 FSD 无效。

[intake]: https://github.com/CartmanFatass/My-paper-code/blob/a8b0e332ea68554de7a1b07bf037d8469c228884/docs/research/candidates/flexible_skill_duration/FSD_BASELINE_INTERRUPTION_B01_INTAKE_20260915.md
[result]: https://github.com/CartmanFatass/My-paper-code/blob/a8b0e332ea68554de7a1b07bf037d8469c228884/docs/research/candidates/flexible_skill_duration/FSD_BASELINE_INTERRUPTION_B01_RESULT_EVIDENCE_20260915.md
[numbers]: https://github.com/CartmanFatass/My-paper-code/blob/a8b0e332ea68554de7a1b07bf037d8469c228884/docs/research/candidates/flexible_skill_duration/baseline_interruption_b01_20260915/RESULT_SUMMARY.json
[card]: https://github.com/CartmanFatass/My-paper-code/blob/a8b0e332ea68554de7a1b07bf037d8469c228884/docs/research/candidates/flexible_skill_duration/FSD_BASELINE_INTERRUPTION_B01_PROSPECTIVE_CARD_20260915.md
[investment]: https://github.com/CartmanFatass/My-paper-code/blob/a8b0e332ea68554de7a1b07bf037d8469c228884/docs/research/portfolio/pro_packets/20260915_fsd_baseline_interruption_investment/archive/RESPONSE.md
[flat-correction]: https://github.com/CartmanFatass/My-paper-code/blob/a8b0e332ea68554de7a1b07bf037d8469c228884/docs/research/portfolio/decisions/2026-09-15-fsd-flat-k-correction.md
[u]: https://github.com/CartmanFatass/My-paper-code/blob/a8b0e332ea68554de7a1b07bf037d8469c228884/docs/research/candidates/flexible_skill_duration/pro_packets/20260912_post_five_pair_use_convergence/archive/RESPONSE.md
[factorial]: https://github.com/CartmanFatass/My-paper-code/blob/a8b0e332ea68554de7a1b07bf037d8469c228884/docs/research/candidates/flexible_skill_duration/FSD_INTERRUPTION_BATCH_B01_RESULT_EVIDENCE_20260915.md
[prep]: https://github.com/CartmanFatass/My-paper-code/blob/a8b0e332ea68554de7a1b07bf037d8469c228884/docs/research/candidates/flexible_skill_duration/FSD_RESTART_PREPARATION_INTAKE_20260914.md
[direction]: https://github.com/CartmanFatass/My-paper-code/blob/a8b0e332ea68554de7a1b07bf037d8469c228884/docs/research/candidates/flexible_skill_duration/DIRECTION.md
[spec]: https://github.com/CartmanFatass/My-paper-code/blob/a8b0e332ea68554de7a1b07bf037d8469c228884/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[programme]: https://github.com/CartmanFatass/My-paper-code/blob/a8b0e332ea68554de7a1b07bf037d8469c228884/docs/research/portfolio/TWO_AXIS_RESEARCH_PROGRAMME_20260914.md
[task]: https://github.com/CartmanFatass/My-paper-code/blob/76af8709713ae71fb9d398a4998c5558a5f4b143/docs/research/candidates/flexible_skill_duration/pro_packets/20260915_post_baseline_interruption_convergence/TASK.md
