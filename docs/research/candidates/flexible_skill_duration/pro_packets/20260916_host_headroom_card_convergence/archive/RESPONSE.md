**选择 C：不冻结原 headroom 卡；以一个更小、明确匹配执行信息权限的“同宿主基线校准 B01”替代它作为首项 CONFIRM 比较。** 新对象只比较 standing D1280 与下文定义、经过有限学习率选择的中央输入 flat（CF）；删除这一对象中的 I1280 臂。保留每 fit 45 轮、每五轮一个面板、第五个独立确认训练块之后的完整读数，不改宿主、原生目标或 D1280 配方。六个调参 fit 加十个确认 fit，共十六个，而不是二十一个。新对象的主要量是**相同外生信息权限和中央信息刷新时点下的有限预算方法差值**，不是已被证明的上界减基线，也不预先承诺完成严格 §11.7 headroom。（[原卡 §§1–6][card]；[信息审计][prep]；[规范 §11.7][spec]。）

作此选择的原因有三项：原卡的私有 FLAT 仍不具备技能路径实际使用的中央执行信息；把 pooled arm SD 的倍数当成效果、无效和关闭的门槛，与本次采用的推断校准冲突；当前 standing D1280 和综述中约 .67 J 的数值都没有提供这个宿主、信息与预算下已成立的上参照。多给训练轮数和种子不能修复这三种含义错误。另一方面，新的所有者决定确实选择了同信息基线问题，现有记录也足以说明该问题有实际价值；因此不选择 D 所要求的“这个宿主上没有可辩护的确认对象”。（[approved set][approved]；[lanes §§3、5、9][lanes]；[规范 §§11.8、11.11][spec]。）

以下给出唯一替代对象的完整科学定义及可直接采用的结果规则。本选择不是源码接受、实际开跑、默认切换、C-BENCH 晋级或生命周期决定。它也不是通过改名宣布原卡合格：**原卡作为“私有 FLAT 即同信息 headroom”的卡被拒绝；下文是不同的、结果知情提出但前瞻固定的新比较。**

## 一、原卡哪里必须改变

### 同一宿主与中央 critic，不等于同一执行信息

已列信息审计明确记录：D2 协调器读取 global state 与 joint observations，生成会影响动作的 skills；私有 flat 的 actor 只读取自己的 observation、常数 skill 和自己的 recurrent state。critic 的 global state 属于训练输入，不会自动成为 actor 执行时可用的信息。学习率调优不改变这个事实。（[restart preparation，Baseline information audit and bounded work plan][prep]；[已完成卡 §2][old-card]。）

所以，原卡“信息匹配另作问题”可以支持一个**明确跨信息的完整包比较**，却不能同时支持“本卡交付 tuned same-information baseline”。原卡声称已经满足上次第二项 reopening fact，也不成立：上次条件包括明确的同信息接口，而不是仅有更多 seeds、训练长度和 ordinary cost。新所有者授权为重新选择问题提供了当前权限；它没有把一个未实现的信息接口变成事实。（[上次完整答复 §§五、八][previous]；[原卡 §§1–2][card]；[control §§2、7][control]。）

最小的信息合格候选，是**在同一栈保留 flat 的原生 PPO、动作、critic 和私有 recurrent state，为其 actor 明确接入当前层次方法合法使用的中央信息**。这不需要导入另一个上游 MAPPO trainer，也不需要限制现有层次臂或改 reward。它确实需要一个新的输入适配面，不能继续写成“全部已实现、仅改常量”。“合格候选”指信息定义合格，不是已经证实它训练充分、最优或实测性能高。（[prep 的 central-input flat 选项][prep]。）

### 信息匹配仍不自动构成 §11.7 headroom

§11.7 的记录需要具名上参照和调优的同信息 generic baseline，并说明其 seeds、曲线和比较条件。这里没有必要证明 baseline 全局最优；但不能把尚未建立上参照地位的 standing D1280 直接称作 upper，也不能把两个有限训练配方的任意有符号差值当作已测剩余能力空间。即使改成 CF，当前能可靠定义的仍是 **D1280−CF 的方法差值**。（[spec §11.7][spec]。）

这揭示了本 TASK 的一个具体冲突：一方面要求严格 §11.7 同信息 headroom，另一方面把“no information-matched comparison”列入原卡上限，并明确排除中央输入 flat。原样同时满足是不可能的。本答复使用 TASK 明列的 **C——不同首项对象** 来解决，而不是默默豁免规范：选同信息基线校准，放弃“本对象必定完成严格 headroom”的承诺。若持久记录中仍保留 headroom 这个工作标题，结果必须另标 `headroom_record: not established`，不能用标题代替结论。这里不选择一个额外 oracle、搜索或上参照实验来补齐它。（[TASK，Research question、Requested decision、scope][task]；[approved][approved]。）

### .079 不是原卡所说的 arm-level SD；2s／1s 不是所需推断

原结果中的 .0788586533 是十五轮 **I1280−D1280 配对对比**的四块样本 SD，不是三个 arm 水平的共同 SD。把它改称“宿主 arm 噪声”已混淆统计对象。再由确认数据的 pooled arm SD 定义效果门槛，还会使 H 的判定受 I1280 这个并非 H 操作数的臂影响，并丢失配对协方差。两个臂共享外生条件时，均值差的精度取决于配对差值的变异，不是 pooled arm SD 本身。（[E0，primary、Contrasts per rollout][result]；[机器读数][numbers]；[原卡 §§4–5][card]。）

五个确认训练块已经满足 lanes §5 的“至少两个”路径；那个条款是“至少两个，**或**有理由的 MEI 至少覆盖记录的 spread”，不是要求满足两项，更不是重新采用综述 R3 的 2 SD／1 SD 规则。保留 .08 作为有独立效用理由的 MEI 本可以讨论，但“它恰好等于原 SD”不是这里的理由。下文采用固定 .05 J 发展尺度，将重要性和不确定性完全分开，不保留 4-of-5 的通过门槛。（[lanes §5][lanes]；[spec §11.11][spec]；[programme §3][programme]。）

### 分支不能制造无效、代码错误或生命周期结论

点估计落入 ±s 不证明“宿主不奖励 skills”。FLAT 胜出也不证明实现错误：可能是固定配方、有限优化、表示、信息组织或训练权利不同。仅给 flat 调参是本对象公开采用的不对称开发权，不是整个 HMASD 算法已经被公平调到最佳后的排名。（[programme §4，Scenario 1 首项比较][programme]；[spec §§4、11.8.4][spec]。）

当前 approved set 的退出描述是 headroom 卡和一个 follow-up 的组合，而原卡在第一项 small/negative 结果后就写自动 CLOSE，二者不一致。更重要的是，新的 control 决定把 Portfolio review 留给所有者触发。结果可以形成准确的关闭建议或继续理由，不能自己触发 Portfolio、安排 hazard host、更改生命周期，或把“next card is interruption”当成自动拨款。既不新增一次逐结果批准，也不从目前的第一张卡删除所有者保留的决定权。（[approved，Reopening / exit conditions][approved]；[control §§1–3][control]；[lanes §3][lanes]。）

## 二、旧证据支持什么，反对什么

已完成 S 的主要事实继续原样成立：

| 十五轮量 | 已接受均值 J | 已接受工作模型 95% 区间 | 限定读法 |
| --- | ---: | --- | --- |
| I1280−D1280 | +.0098374427 | [−.1156424464,+.1353173319] | 原 .05 MEI 下 small_signed；区间含零且不在 MEI 内 |
| D1280−私有 FLAT | −.0452634555 | [−.1349157030,+.0443887921] | 未调优跨信息包差；不是等效或 FLAT 非劣 |
| I1280−私有 FLAT | −.0354260128 | [−.1835943228,+.1127422972] | 同上，不是严格 headroom |

主量四块为 +.09835977、+.04471497、−.08340338、−.02032159；第 5／10 轮的块均值 +.04976314／+.05182877 不替换第十五轮。新四块与旧两块合成的 rollout-5 +.04287702、区间 [−.02320115,+.10895519] 保持原“结果知情描述性积累”，本轮不重新聚合。（[result，三个结果表][result]；[numbers][numbers]。）

**最强支持继续做一个不同基线问题**，是当前仍没有信息匹配的 flat 读数，而私有 FLAT 已在实测点水平上有竞争力；同时 772203 的十五轮 I1280−D1280 +.09835977 以及其他正向观察表明，并非所有学习历史都反对该体系。不同块、不同预算的排序变化使一个明确固定预算的基线校准有实际价值，而不是证明新 CF 一定较强。（[result，All endpoints][result]；[prep，信息审计][prep]。）

**最强反证**，是同一已完成对象中主量小正但很不精确、两个包差负向、两个主量块为负，以及更高 I1280 工作。新方案不能靠把预算从十五轮增到四十五轮承诺排序稳定。FLAT 772503 的 .312032→.530132，D1280 同块的 .439014→.506588→.452340，说明不同检查点的策略确实变化；它们不是方差分解。当前 intake 已撤回“更多独立块无益”的推断，这个更正保留。更长训练可能帮助或妨碍任何一臂，五块也不保证精度。（[intake，Scientific reading and limits][intake]。）

约 .67 J 只在被列出的 advisory review 中以历史覆盖率和 host-family 推断出现；本轮清单没有一个与当前 reward、信息、配方、预算相同的 .67 J 原始参考。原生目标还有 quality 和 altitude penalty，不能从 coverage .96 推出当前任务的 J 下界。review 的 R1、R3、R5 是可批评的建议，后来的 owner-approved programme 已纠正其中的 SD 门槛和参考尺度解释。删除新卡的“achievable reference .67”、以它衡量训练充分程度的文字及其 headroom 用法；可以把该数值留在历史文献讨论里，但不能进入本对象主量、能力门槛或参照曲线。（[review §§1、5.2、7][review]；[programme §§2–3][programme]。）

## 三、替代对象：同信息有限预算基线校准 B01

以下是本次选择的完整对象定义，不是多个待挑选方案。建议名称为 `FSD_MATCHED_INFORMATION_BASELINE_B01`；证据类别 **B**，流程 lane **CONFIRM**。CONFIRM 是本次所有者的流程要求，不等于 C-BENCH 或稳定总体声明。（[lanes §§1、3、5][lanes]。）

### 1. 问题、处理和比较器

**问题：**在固定 360,000 training team steps 下，standing D1280 相对经过所述有限学习率选择的中央输入 flat，有没有值得继续考虑的原生性能增量？它比较两个完整学习方法，不证明“层次结构是必要的”，也不测量中断增量 SI45。

| 项目 | D1280 | CF：中央输入 flat |
| --- | --- | --- |
| 构造 | 已接受 D2 固定时钟路径；individual/team gap 均为 numeric +infinity | ordinary off → mappo；常数单 team/individual skill；再显式 k=10 |
| 高层学习 | standing coordinator batch1280；原 discriminator 和 credit 语义 | coordinator、两种 discriminator 不优化；discriminator intrinsic reward 关闭 |
| 持有与反应 | k10、caps10/10、age off；私有 recurrent primitive actor 每步反应 | 常数 skill；每步反应；每 UAV 独立持有自己的 GRU state |
| Flat 的额外设计 | 不改变此臂输入或配方 | 接入下述合法中央快照及 ego identity；只改变必要的 actor 输入投影 |
| 调参权 | 零新调参；standing 配方 | 仅 stage 0 的三点学习率乘数 |
| 共同条件 | Scenario 1、六架固定 UAV、五十用户、H500、原 reward/terminal、J=6U/500、CPU FP32、四线程、16 training lanes、原 PPO 和独立 evaluator | 同左，除明确声明的 flat 输入和调参差异 |

**CF 信息接口精确定义：**在 lane reset 的初始决策步以及其后与 D1280 共用的 k10 团队决策时点，读取本臂当前合法 global state 和六个按固定 UAV 身份排序的 joint observations，形成中央快照。中央快照仅在这些时点刷新；中间九步保持最近快照，不额外读取新的中央变量。每步 actor 输入是本 UAV 最新私有 observation、最近中央快照、固定六维 ego one-hot、常数 skill 及本 UAV 自身 GRU state。reset 清除本 lane 的旧快照和 recurrent state，再用新回合初始信息建立快照。禁止使用未来状态、未来 reward、最优动作、别臂轨迹或新增环境内部信息。

这个刷新限制是本替代设计的前瞻选择：避免给 flat 每步新的中央观测，却把比较器的中央协调输入限制在 k10；也避免把中央 critic 的输入误当执行权限。两者有相同的外生信息来源和中央刷新机会，但 D1280 用离散 skills 编码、CF 用原始快照输入，表示、带宽利用和学习过程并不相同。因此这仍是明确的信息组织／完整方法对比，不是隔离 hierarchy 因果效应的实验。CF 应命名为中央输入 flat，不能再称私有 actor MAPPO。这个接口在所读审计中是有依据的候选方向，具体适配器并没有被本节点实现或验证。（[prep，Baseline information audit][prep]；[old-card §2][old-card]。）

保留现有 actor 的 hidden width、连续动作头、critic 输入、PPO 损失和 primitive-time 折扣／GAE／终止语义；除输入宽度必需的投影外，不引入新 encoder 搜索、attention、termination head 或另一套 trainer。当前观测与快照中的同类连续量复用相应 observation/state normalization 语义；ego identity 不做运行统计。CF 评估时使用自己的最终 normalization 状态，不从 D1280 或其他 seed 复制。原生 reward 不因报告 J 而缩放训练目标。

I1280 **不在本对象中**。它最昂贵，而本次第一问题是基线与固定时钟 reference；删除这五个确认 fit 不会影响 D1280−CF 的定义。相应明确放弃 SI45、HI45、以及任何“本卡同时确认中断”的声明；不能从旧 SI 值补齐它们。D1280 是本实验的高 batch 固定时钟 reference，不凭“authentic default”这个字样把历史 U 的 batch128 默认对照替换掉。（[previous，§七][previous]；[card §§2、4][card]。）

### 2. Stage 0：一个完整的有限选择程序

保留原三点 grid **λ∈{0.5,1,2}**，每点两个独立训练块，各45轮。对 CF 实际参与训练的 actor 和 critic optimizer 的每个 parameter group，学习率等于 standing 对应学习率乘 λ；既有 schedule 若存在，乘数作用于该 schedule 的输出且只乘一次。其他 optimizer 属性、entropy、网络宽度、k、损失权重均不调。没有 coordinator/discriminator 更新，因此不得把它们的数值字段当作新增调参因子。

使用原提议的 tuning training bases **772603、772703**，evaluation bases **782603、782703**。每个 λ/seed fit 都从头构造自身模型、optimizer、normalizer、buffer、RNG 与 evaluator；共同外生初始化／reset 地址只用于已声明的配对，不共享学习状态。各候选运行同样45轮与九个面板，选择只用各候选两个 **J45** 的平均。

**选择规则：**取平均 J45 最大的 λ；若存在完全相同的最大值，只在最大值集合内按 **1、0.5、2** 的固定顺序选第一个。若 0.5 与2并列最高而1较低，选0.5，不能按旧句“ties go to1”选择一个非最大值。没有事后 near-tie 容差、最好世界／seed／中间面板选择或补跑。保留六个完整候选结果和选择暴露，不把选中者的 tuning 分数当作最终 reference level。

六个预定 fit 中任何一个缺失、非有限或发生影响选择量的完整性问题，stage 0 标为 `SELECTION_INCOMPLETE`，不从剩余候选中悄悄选择，不自动回退1×，不启动 stage 1。保留可信已有事实，无自动 retry、replacement 或重抽 seed。全体完成后，将唯一 λ 和选择依据固定在 stage0 记录中，**早于任何 stage-1 fit 或 panel 的读取**。这样确认结果不会反向选择学习率。

两 tuning seeds 与确认 seeds 完全分离，是本设计相比上次被拒绝的“一设置一 fit、直接报最高终点”的实质改善；它仍只完成这个有限 grid 的选择，不证明选中 λ 最优或选择程序在重复调参数据上的稳定性。（[card §3][card]；[spec §§11.8.3–4、11.11][spec]。）

### 3. Stage 1：五个全新独立确认块

训练 bases **772803、772903、773003、773103、773203**；评价 bases **782803、782903、783003、783103、783203**。每块 D1280 与 CF 各一个从头训练实例。每个 fit 45轮×16 lanes×500步，共360,000 training team steps、720训练回合、45 update stages。

每 fit 只构造一个学习模型和一个独立 evaluator。在更新完第5、10、15、20、25、30、35、40、45轮后，各用该块同一组32个固定世界地址跑一个 H500 deterministic panel；第45轮唯一主终点，其余八点全部为曲线。每次同步本臂权重和 evaluation-mode normalizers，重置评价环境、skill／timer／快照／RNN，保存并恢复训练 RNG，且不得改变训练 normalizer、buffer 或其他学习状态。仅 RNG wrapper 不足以证明这些状态隔离。

共同随机数的含义是本设计的初始外生世界安排，不是“相同 seed 编号保证相同轨迹”。不同输入形状不允许宣称两个网络初始化逐元素相同；能匹配的共有随机消费者须明确，其他随机消耗和后续探索保持 arm-local。评价 panel 中每个 pair 共享外生世界地址，动作和原生轨迹可以不同。拟议 seed 的数字是前瞻身份，不表示本节点审计过整个仓库证明其从未使用。

所有确认 fit 无论前一臂或 tuning 的分数如何，都按选定方案执行；只有真实完整性、资源或平台限制改变可执行性。不按“训练似乎收敛”提前停止，不延长至曲线平坦，不改用最好 checkpoint，不追加第六块或第十面板。45轮是固定资源条件，不是收敛证明。（[card §3][card]；[old-card §3][old-card]；[spec §§4、11.8.3、11.8.6][spec]。）

## 四、主量与穷尽的预注册规则

### 1. 估计目标与不确定性

对确认块 b，令 J45 为该 fit 的32个最终原生世界分数的均值，定义

`G_b = J45(D1280,b) − J45(CF_λ*,b)`。

唯一主量为五块 G_b 的等权平均。报告五个原始 G_b、两臂五个 J45、各块32个有序世界差值及其条件 SD／SE，另报告 G_b 的 sample SD `s_G`、`SE_G=s_G/sqrt(5)` 和 `mean(G) ± t_(.975,4) × SE_G`。这个 df4 区间采用预先声明的 iid-normal 配对块差工作模型，覆盖率没有由五块验证；它条件于 stage0 已选定 λ，不包含重新运行整个 tuning 过程的额外变异。

删除三臂 pooled s、df12 和由它驱动的判定。两臂水平 SD 可以描述性报告，但不替代配对差值 SD；正／负／零块数全部列出，不用4-of-5作通过门槛。曲线同样按预定各轮完整报告，不选面板、不跨时间汇成新的主量、不与旧十五轮 S、factorial 或 U 五对合并。（[spec §§11.8.3、11.11][spec]；[programme §3][programme]。）

**MEI 固定为 .05 J absolute。** 这是本节点为这项较长、实际有成本的方法选择采用的前瞻发展尺度：只有达到这个平均每步加权原生回报增量，才把点估计称为值得继续发展的差异。它沿用此前已经明示的本宿主成本敏感发展尺度，但不是由旧 SD 推出，也不是项目通用门槛；旧 .01 和其他对象 .05 的结果均不重判。J 同时包含 coverage、quality 与 altitude，.05 J 不能简称为五个百分点覆盖率。新测到的 SD 只改变精度报告，不改变 MEI。（[result，原 MEI 修正][result]；[programme §§2–3][programme]。）

### 2. 所有完整有限主量的读法

| 重要性标签 | 唯一数值条件 | 当次科学读法与固定后果 |
| --- | --- | --- |
| D_REFERENCE_ABOVE | mean(G)>+.05 | 这五块上的 D1280 固定配方有发展尺度的正向点差。保留 D1280 作为有局部支持的比较 reference；形成可供后续用途判断的记录，不自动安排中断对象或改变默认。 |
| SMALL_SIGNED | −.05≤mean(G)≤+.05 | 这五块的点差在兴趣区间内，保留符号；不证明等效、宿主不需要 skills 或没有可改善空间。完成本对象，不自动追加训练。 |
| CF_REFERENCE_ABOVE | mean(G)<−.05 | 这五块上所选 CF 相对 standing D1280 有发展尺度的优势点观察；削弱该 D1280 配方在此预算的竞争理由，提交有界方法比较记录，不诊断代码错误，不撤销历史 FSD 结果。 |

每一行再附**独立的不确定性标签**：区间下端>0 为 `INTERVAL_POSITIVE`；上端<0 为 `INTERVAL_NEGATIVE`；否则为 `INTERVAL_INCLUDES_ZERO`。端点恰为零属于包含零。另记录闭区间是否完全包含在 [−.05,+.05] 内；是也只称工作模型条件下的小幅度读数，不称等效。`SMALL_SIGNED + INTERVAL_INCLUDES_ZERO + not_inside_mei` 明确写“重要性小点估计，真实幅度和方向未分辨”；不能缩成 INDISTINGUISHABLE。

大点差配宽区间，同样是大点差但未定精度，不得把“未显著”转成无效；小点差配窄单向区间则是方向较清楚但小于兴趣尺度。n=5及符号计数不保证泛化。若 s_G=0，原样报告退化的样本计算和模型限制，不宣称训练总体没有波动。

### 3. 不完整／无效也是已登记分支

`SELECTION_INCOMPLETE` 按前述 stage0 规则结束本对象的依赖链。Stage1 少于五个完整、可比、有限的配对，或出现影响 reward、信息、训练／评价隔离、身份或主量的缺陷，读为 `PRIMARY_INCOMPLETE_OR_INVALID`；不填补缺失臂、不按零差、不删去负块、不让曲线代替J45。保留每个独立可信的完成臂、配对和实际暴露，清楚标出 available n；不把不足五块的统计伪装成完整预注册主量，n=1时没有训练样本 SD／SE。

该分支不是算法负结果，也不授权 retry、seed替换、追加面板或增加预算。已明确的普通资源限制、publication缺失及其依赖读法，可以由 DM 按此规则完成事实 intake，而不是自动形成又一轮 Pro。

### 4. 什么时候仍需要结果 review

**以上规则足以读取所有完整有限数值结果、混合块符号、宽区间、未变平曲线，以及已定义的不完整／受损情形。** 本节点不要求看到每个正常结果。仅在出现规则没有覆盖、确实改变比较含义的事件，或 DM 对应用规则提出实质异议时，使用 lanes 已有的例外 review 路径；不能因为不喜欢符号、区间宽、恰在边界或未到 .67 而称“落在规则之外”。（[lanes §3][lanes]。）

所有分支都终结本对象并保留原结果。关于整个方向的 CLOSE、换 hazard host、是否使用下一周期预算或默认切换，只能是附有实际证据的建议；不由标签自动执行。不自动发送 Portfolio 问题，所有者触发 review 时再读其备忘。APPROVED_SET 的 headroom＋follow-up 条件既没有被本卡改写，也不构成这里已安排第二个 fit 对象的许可。（[control §§1–3][control]；[approved][approved]。）

## 五、工作量、成本与实现接受边界

### 确切科学暴露

| 量 | Stage0：3设置×2块CF | Stage1：2臂×5块 | 总计 |
| --- | ---: | ---: | ---: |
| 从头 fits | 6 | 10 | 16 |
| 训练 team steps | 2,160,000 | 3,600,000 | 5,760,000 |
| 评价 team steps | 864,000 | 1,440,000 | 2,304,000 |
| 评价 panels | 54 | 90 | 144 |
| Update stages | 270 | 450 | 720 |
| Learner/evaluator 构造 | 12 | 20 | 32 |

这些是由所选设计展开的前瞻算式，不是新运行或历史数据重分析。每 fit 的训练量是45×16×500，评价量是9×32×500；parallel lanes、世界和检查点都不增加确认训练块数。Stage0是模型选择暴露，不混入五块确认均值。无轨迹树、组合动作枚举、候选宽度搜索、pilot、额外 performance validation panel 或模型复用。

D1280 coordinator 工作依 standing law 为每轮15次、每fit675次；CF为0。若保持已接受 discoverer sampler/epochs，actor、critic 各约101,250次 optimizer calls/fit是由十五轮33,750次的线性计数推得的计划值，实际接受仍以真实计数为准。输入投影变大不意味着步数变多，却可能增加每步代价；共同 update stages 从来不等于 matched compute。（[old-card §5][old-card]；[result，Counts][result]。）

### Ordinary cost plan，不是时限判据

已测的十五轮 whole-command windows 是私有FLAT 2022.50–2594.40秒、D1280 2617.32–3428.12秒、I1280 5045.10–6550.17秒，总45401.07秒；测量发生在资源竞争中，不能当成未竞争串行速率。原卡四十五轮的工作锚为私有FLAT约6100–7800秒、D1280约7900–10300秒、I1280约15100–19700秒，均为外推而非新实测。（[result，Resources][result]；[card §6][card]。）

新对象有十一项CF工作和五项D1280工作。若CF暂按原私有FLAT的成本锚代入，原生和为 **106600–137300秒**；这只是参考算术，**不含中央输入适配所增加的成本**。完整成本法则是

`11 × whole_wall(CF45) + 5 × whole_wall(D1280_45) + necessary_support`。

为给出可使用的 ordinary 起始计划，而不是把CF的未知藏为零，本节点采用 **CF每fit约12000秒、D1280每fit约10300秒，原生合计约183500秒**。CF的12000是围绕私有FLAT外推锚、为新输入路径留余量的前瞻计划选择，不是测得的中央输入速率、上界或性能预测；必要的实现／检查／发布／intake支持和provider费用另外保持UNKNOWN。DM可依实际代码规模、竞争与完成记录修订这个普通计划，不需要先运行新的profiling实验，也不能因计划变化改变已开始的45轮终点。（[spec §§11.8.1、11.9][spec]。）

本方案少了五个最昂贵的I1280 fit，但不能因此证明一定更省全部工作。即使节点可并行四个fit，stage0先于stage1的依赖、同一时刻各臂RSS、调度空档、运行长度和实际fresh admission也会限制makespan，不能把sum直接除以四后许诺15–20小时。当前CF的RSS和实际wall均未测；私有FLAT约1.2 GiB不是其内存保证，20核也不是可用容量保证。

这是**一个**由两阶段构成的CONFIRM对象，十六fit计入同一个七日窗口的standing object预算，不拆成多个对象、不继承旧S余额。本选择不新增Portfolio预算；它给出该一个对象的科学规模与普通计划。实际需要超出standing额度或遇到所有者／平台硬约束时，保留实际缺口，按已有所有者控制处理，不让ordinary estimate变成科学失败或暗中放大预算。更改APPROVED_SET的正式首对象表述属于既有权限；这里不把“基线校准”登记为已经完成的严格headroom。（[lanes §7][lanes]；[control][control]。）

### 只有真实依赖需要在实现中修正

原卡“薄入口＋不需独立review”的L0不能原样用于CF。新的输入面必须贯穿真实collector、存储／recurrent replay和evaluator；缓存身份、刷新时点、normalization及reset均需要一致，不能只给采集actor增字段而训练replay仍用旧输入。薄文件在自身命名空间写`ROLLOUTS=45`，也不证明被import函数实际读到45；参数必须到达实际loop、panel schedule、summary和reducer。这是需由实际实现接受解决的依赖，不是本节点已发现的生产代码故障，因为runner源码不在本轮manifest。（[card §7][card]；[prep][prep]。）

针对改变的契约保留局部测试：中央数据字段／时点及lane reset；训练、replay和evaluator输入一致；CF active optimizer multiplier且D1280不变；stage0所有最大值tie情形；完整45／九面板绑定；主量和不确定性边界、零方差、缺失配对及无效selection。复用未改的数值／环境证据，不要求重跑完整S或增加有结果的smoke。涉及新actor输入、numerics、RNG或result identity的diff，按lanes §6既有风险条款接受独立技术review；纯记录或真正不改语义的薄入口不因本响应另造审查层。（[lanes §6][lanes]；[spec §§4、11.8.6–7][spec]。）

每个实际fit仍须 exact committed source、CPU FP32四线程、remote-first WSL、物理和有效available memory均≥4 GiB的当次准入、detached supervision及独立evaluator。代码读取、review与必要tests属于未来实现成本；本响应未运行它们。没有资源失败或不完整输出被自动改写为负科学分支。

## 六、为什么不是 A、B 或 D；新旧权限如何衔接

A不能选择：原卡的比较含义和结果规则同时有明确问题。B若仅修规则、不改private-FLAT接口，就仍不能交付所有者点名的同信息基线；若一并改变输入、独立单位解释、主量和I臂，则已不只是保持原对象的小修正。故我显式选C，避免用“freeze with corrections”掩盖实质改题。

C相对于原方案保留了有用部分：有限grid、两次tuning重复与独立五块评估、固定45轮、完整曲线以及真实same-host learner。它把当前最重要的缺口——baseline实际可用的信息——变成明确可实现的比较内容，且不再同时购买尚不必要的I1280确认臂。这个对象没有证明headroom“存在”；它提供未来决定该如何解释reference和有限配方差值所需的直接观测，而非先做完美基线认证的通用关卡。

D也不选择：现有数据反对的是若干有限配方和较强解读，并未说明任何同信息确认对象在此宿主都不合理。原生学习历史中仍有正、负对比和尚未测的合法输入候选。当前owner已经明确提出这项基线用途，因此本轮与上次“没有选定的新问题”的边界不同。上次CLOSE_OBJECT以及对私有FLAT sweep的批评不撤回，也不被解释为永久禁止新baseline问题。（[previous，§八][previous]；[approved][approved]。）

严格§11.7上参照的缺口不能靠本节点凭空补齐。把校准结果留作有界方法差值是可完成的科学任务；若所有者在后续review要求首对象必须单独交付严格upper-minus-baseline，则需要明确那一上参照或改变交付目的，而不是把本结果改标签。本轮不为这点自动发送Portfolio、选择新oracle实验或提出规范例外。这是明示的交付范围收窄，不是把缺失headroom当作不能进行真实B的理由。

原card预测的INDISTINGUISHABLE .45、FLAT_ABOVE .25、HIERARCHY_ABOVE .15、UNRESOLVED .15及SI-positive .20绑定原来的2s规则，保留为被替代草案的预测，不能用新规则给它们评分。DM可在新对象任何科学输出前另记新预测；没有新预测不增加科学启动门槛，本节点不编造新概率。

## 七、旧结论与新的结果后果均不越界

十五轮S继续是small_signed、有正负块、区间广的完整B；不会因本次提出CF而被称为不合法。原五轮factorial的高batch simple effect与其原 .01规则保持；旧U五个完整包观察仍是 I1280 对batch128 authentic D0，不是当前D1280−CF。其五轮有限可选用途、原负对、额外成本以及D0默认都保留；没有四十五轮保证、组件因果、跨宿主或C-BENCH晋级。（[direction，Position][direction]；[previous，§七][previous]。）

新对象即便CF较强，也只说明所选CF程序和standing D1280在给定曝光的比较，不证明原实现错误、host不需要hierarchy、所有中断无益或旧U无效。D1280较强则提供这个完整fixed-clock方案相对这次有限tuning-baseline的局部依据，不证明层次必要性或baseline已最优。小差或广区间结束当次观测而保留未知，不自动投票决定研究方向。CF的输入被如实匹配不意味着它一定更容易训练，45轮也不宣称达到 .67 或reference主分支的5e6-step能力。

lanes的新审批频率与当前normative method可以同时遵守：**现在一次freeze审阅，之后按完整规则intake，非例外不另作result review；生命周期仍留给所有者触发的review。** 这不是恢复旧的每对象Portfolio调用，也不是把CONFIRM当作无需准确比较定义的标章。（[lanes §§3、5、7][lanes]；[control §§1–3][control]；[spec §11.11][spec]。）

## 八、实际固定源访问与未验证项

本次实际访问全部十四个manifest路径。科学代码、原fit目录、外部论文、.67参考原始记录及未列依赖均未展开；引用审计的源码事实明确属于所读审计报告，不冒称本节点直接检查了新CF实现。

| 已读取路径 | 有效版本与范围 |
| --- | --- |
| [FSD_HOST_HEADROOM_B01_PROSPECTIVE_CARD_20260916.md][card] | b8c41ad27f85c9269a9e25adc4e9836af650061b；全文，两个stage、原规则、成本和L0 |
| [FSD_BASELINE_INTERRUPTION_B01_RESULT_EVIDENCE_20260915.md][result] | 同上；完整结果、全部arm/block/panel、暴露和成本 |
| [FSD_BASELINE_INTERRUPTION_B01_INTAKE_20260915.md][intake] | 同上；原规则、已经收窄的三个推断、当前结题 |
| [baseline_interruption_b01_20260915/RESULT_SUMMARY.json][numbers] | 同上；读取机器资源并定位十二项J_by_rollout，未重算raw outcomes |
| [FSD_BASELINE_INTERRUPTION_B01_PROSPECTIVE_CARD_20260915.md][old-card] | 同上；§§2–5，旧定义与实际结果对应；前部历史headroom措辞不恢复 |
| [20260915_post_baseline_interruption_convergence/archive/RESPONSE.md][previous] | 同上；原A、私有FLAT筛选异议、U范围及§八重开条件 |
| [FSD_RESTART_PREPARATION_INTAKE_20260914.md][prep] | 同上；baseline构造、信息审计及中央输入候选 |
| [DIRECTION.md][direction] | 同上；Scientific question及Position |
| [2026-09-15-workflow-lanes.md][lanes] | 999e838cf764928b11d484f2232fde24a43f949f；全文，CONFIRM／review／standing budget |
| [2026-09-15-portfolio-control-and-approved-set.md][control] | 同上；全文，owner-triggered review、approved set和边界 |
| [APPROVED_SET.md][approved] | 同上；全文，首对象与原退出条件 |
| [FOUNDATIONS_AND_METHODOLOGY_CRITICAL_REVIEW_20260914.md][review] | 同上；§§3、6、7及实际出现 .67的§§1、5.2；建议不作为规范 |
| [MARL_EMPIRICAL_EVIDENCE_SPEC.md][spec] | 同上；§4、§7、§8.1、§11.4、§§11.7–11.11 |
| [TWO_AXIS_RESEARCH_PROGRAMME_20260914.md][programme] | 同上；§§2–5，参考尺度、MEI／精度、baseline和归因 |

FSD相对路径前缀为`docs/research/candidates/flexible_skill_duration/`；其余完整路径见下面固定链接。TASK按fd9502467d0d0439f33ca250e5e4ab580e3bdffd读取；Issue10和交付分支只用于确认交付及避免重复。命名为20260916的卡、以及前一日PDT晚间owner记录，按其已固定版本理解，不由本轮另行推断任何当前运行已经开始或完成。

没有decision-critical connector/path缺口。本节点没有模型、fit、checkpoint load、环境步、optimizer step、test、profiling或科研数值重分析；前瞻计数和普通成本是设计推导，不是新证据。完整文档／连接器／provider成本未测，不称零成本。

**给主人的结论：拒绝原样headroom卡，选择上述十六fit的同信息基线校准作为唯一替代首对象；保留严格headroom尚未成立的标签。** 不能让一个重新引入的2SD规则、一个跨信息baseline或一个不可比的 .67数值自动决定FSD去留。正确的结果规则现在已经完整给出；未来无论强正、小差、负向、宽区间还是已定义的不完整情况，都按规则保留事实和限制，不自动增加对象、切换默认或触发生命周期review。

[task]: https://github.com/CartmanFatass/My-paper-code/blob/fd9502467d0d0439f33ca250e5e4ab580e3bdffd/docs/research/candidates/flexible_skill_duration/pro_packets/20260916_host_headroom_card_convergence/TASK.md
[card]: https://github.com/CartmanFatass/My-paper-code/blob/b8c41ad27f85c9269a9e25adc4e9836af650061b/docs/research/candidates/flexible_skill_duration/FSD_HOST_HEADROOM_B01_PROSPECTIVE_CARD_20260916.md
[result]: https://github.com/CartmanFatass/My-paper-code/blob/b8c41ad27f85c9269a9e25adc4e9836af650061b/docs/research/candidates/flexible_skill_duration/FSD_BASELINE_INTERRUPTION_B01_RESULT_EVIDENCE_20260915.md
[intake]: https://github.com/CartmanFatass/My-paper-code/blob/b8c41ad27f85c9269a9e25adc4e9836af650061b/docs/research/candidates/flexible_skill_duration/FSD_BASELINE_INTERRUPTION_B01_INTAKE_20260915.md
[numbers]: https://github.com/CartmanFatass/My-paper-code/blob/b8c41ad27f85c9269a9e25adc4e9836af650061b/docs/research/candidates/flexible_skill_duration/baseline_interruption_b01_20260915/RESULT_SUMMARY.json
[old-card]: https://github.com/CartmanFatass/My-paper-code/blob/b8c41ad27f85c9269a9e25adc4e9836af650061b/docs/research/candidates/flexible_skill_duration/FSD_BASELINE_INTERRUPTION_B01_PROSPECTIVE_CARD_20260915.md
[previous]: https://github.com/CartmanFatass/My-paper-code/blob/b8c41ad27f85c9269a9e25adc4e9836af650061b/docs/research/candidates/flexible_skill_duration/pro_packets/20260915_post_baseline_interruption_convergence/archive/RESPONSE.md
[prep]: https://github.com/CartmanFatass/My-paper-code/blob/b8c41ad27f85c9269a9e25adc4e9836af650061b/docs/research/candidates/flexible_skill_duration/FSD_RESTART_PREPARATION_INTAKE_20260914.md
[direction]: https://github.com/CartmanFatass/My-paper-code/blob/b8c41ad27f85c9269a9e25adc4e9836af650061b/docs/research/candidates/flexible_skill_duration/DIRECTION.md
[lanes]: https://github.com/CartmanFatass/My-paper-code/blob/999e838cf764928b11d484f2232fde24a43f949f/docs/research/portfolio/decisions/2026-09-15-workflow-lanes.md
[control]: https://github.com/CartmanFatass/My-paper-code/blob/999e838cf764928b11d484f2232fde24a43f949f/docs/research/portfolio/decisions/2026-09-15-portfolio-control-and-approved-set.md
[approved]: https://github.com/CartmanFatass/My-paper-code/blob/999e838cf764928b11d484f2232fde24a43f949f/docs/research/portfolio/APPROVED_SET.md
[review]: https://github.com/CartmanFatass/My-paper-code/blob/999e838cf764928b11d484f2232fde24a43f949f/docs/Claude_docs/reviews/FOUNDATIONS_AND_METHODOLOGY_CRITICAL_REVIEW_20260914.md
[spec]: https://github.com/CartmanFatass/My-paper-code/blob/999e838cf764928b11d484f2232fde24a43f949f/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[programme]: https://github.com/CartmanFatass/My-paper-code/blob/999e838cf764928b11d484f2232fde24a43f949f/docs/research/portfolio/TWO_AXIS_RESEARCH_PROGRAMME_20260914.md
