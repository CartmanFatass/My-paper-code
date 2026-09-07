**方向层决定：停止 B06 所测试的联合高斯运动／Bernoulli 意图抽样规则的当前扩展投入；本轮不选择新的 A 或 B，也不追加任何科学调用。** 最小停止单位是在修正 A03 宿主、既有 LOW_LR 学习器及普通续约边界上，用这项联合抽样法替换同一最终控制器模态执行的探索支线。保留模态作为本实例的开发默认。依据仍是 **B/EXPLORE 的有限原生比较**，不是新的 C 结论，不是整个 DISH 或首次普通合法应用 RETAIN/COPY/SHADOW 议程的 PARK、CLOSE 或 RECAST。

理由是已购买的执行法则问题得到了可读的原生答案：固定主差分为 **−77.5 服务 tick**，四个条件均值均负于 −24，且抽样的条件平均无效提交和能量都增加。没有必要再购买一次测量，才能承认这些结果并选择当前不扩展该规则。与此同时，一个训练实例、每条件两个样本和两个个别正样本，远不足以证明随机执行普遍较差。因此本决定是限定投入对象的停止，而非排除所有随机策略、组件变体或来源机制。[科学 intake §§1–4、7][intake]；[冻结卡 §§1、4–5][card]；[证据规范 §§5.2、11.8][method]。

## 一、保留完整主量，而不是把不利均值变成所有轨迹的结论

B06 的直接比较单位是同一个 seed113 LOW_LR 的 update16 控制器：两个执行模式共享最终参数、log_std、预测头及固定的检查点 Welford；每个 episode 从相应相同 reset、新鲜 native／循环状态开始。四个条件是 TARGET_VISUAL_MASK／TERRAIN_RELAY_MASK × K8／K4_TO_K12，均为 speed4、slot0、block0。主量先平均每个条件的两个抽样样本，再对四个条件等权：

`Delta_exec = (1/4) Σ_r [(J_S,r,0 + J_S,r,1)/2 − J_M,r]`。

| 条件 | 初始模态 | 最终模态 | 样本0 | 样本1 | 样本均值 | 抽样均值−模态 | 模态−初始 | 抽样均值−初始 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| TARGET_VISUAL_MASK / K8 | 250 | 459 | 362 | 371 | 366.5 | −92.5 | +209 | +116.5 |
| TARGET_VISUAL_MASK / K4_TO_K12 | 359 | 593 | 497 | 607 | 552 | −41 | +234 | +193 |
| TERRAIN_RELAY_MASK / K8 | 417 | 454 | 364 | 356 | 360 | −94 | +37 | −57 |
| TERRAIN_RELAY_MASK / K4_TO_K12 | 453 | 1143 | 1146 | 975 | 1060.5 | −82.5 | +690 | +607.5 |
| **等条件均值** | **369.75** | **662.25** | — | — | **584.75** | **−77.5** | **+292.5** | **+215** |

表格对应原始 `summary.json` 的 `primary.rows`、`learner.evaluation_rows`、`reference.reference_rows` 和 `sampled.evaluation_rows`；`DM_READBACK.json` 的 `rows`、`primary` 是对这些结果的已提供只读复算，不是另一份独立实验。[原始 summary][summary]；[DM 复算][readback]。

主差分约为本次模态均值的 −11.70%、完整 1,200-tick 范围的 −6.46%，即原卡 24-tick 有用变化尺度的 −3.23 倍。这里的四个负条件均值是事实，不是新增“所有条件必须同号”的判据。真正使第4分支适用的是原有 `Delta_exec<=−24`，无需另行发明严重性阈值。[intake §§2、4][intake]；[readback 的相对量][readback]。

两个正样本必须保留：TARGET/K4_TO_K12 的 sample1 为 607，比模态高14；TERRAIN/K4_TO_K12 的 sample0 为1146，比模态高3。不能把结果写成八个抽样 episode 全部变差，也不能挑这两条替代规定的两样本平均。其存在说明逐轨迹后果有变化，并不独立估计抽样回报的期望或训练总体效应；四个条件也不是四个训练种子。

`D_modal=+292.5` 是同一模态接口下完整控制器初末变化，包含参数与 Welford 的变化；`G_sampled_vs_init=+215=D_modal+Delta_exec` 同时包含学习和执行法则变化。后者不是同接口的纯学习增益，也不是第三个独立样本。两个总体初始相对均值为正，反对把本次读成“学习本身无效”；但抽样相对初始化的 TERRAIN/K8 **−57** 仍在。零更新参考既不是调优上界，也不是安全或最优控制器。[冻结卡 §§3–4][card]；[intake §2][intake]。

全部 **16 个 episode 均实际执行1,200 tick，共19,200 tick**；没有提前终止，没有未执行余段，native terminal 均为固定范围结束。原卡的提前终止／余段零服务规则保持不变，本例只是未触发提前终止。不能把 B04 那次提前分离终止带入本次解释，也不能改用存活时长归一化或删行。[summary 的各 episode 与 actual_exposure][summary]；[readback][readback]。

## 二、原生代价和分母必须与服务一起读

| 面板 | episode数／实际tick | invalid_commit 原始合计 | 每episode均值 | 能量均值 | 普通合法换主 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 初始模态 | 4／4,800 | 31 | 7.75 | 268,778.5278 | 0 |
| 最终模态 | 4／4,800 | 14 | 3.5 | 273,979.2808 | 0 |
| 最终抽样 | 8／9,600 | 255 | 31.875 | 278,621.9235 | 0 |

原始255对14涉及不同的 episode 数，不能直接当成等曝光事件比较。按先两样本平均、再四条件等权的同一口径，抽样每episode无效提交多 **28.375**，四个条件的增量分别为 **56、4、45、8.5**。相应模态计数是0／13／0／1；两条抽样计数依次为45与67、17与17、45与45、3与16。这些是事件计数，不是每次提交机会的拒绝概率，也不证明 Bernoulli 意图是唯一原因。[readback：rows、native_panels][readback]。

能量均值多 **4,642.6427（约1.69%）**；四个条件均值的增加分别约为3,200.9471、10,524.7583、1,478.9342、3,365.9314。所有比较均有完整等时长终局，因此不是由较短生存期制造的能量差。这里服务下降、事件增加和能量增加共同支持不扩展当前规则；不需要修改 reward，把事件或能量事后加权成一个新主量。[readback][readback]；[冻结卡 §4][card]。

六个其他评估硬事件类别——buffer_clear、command_slew_breach、dual_owner、dual_payload、separation_breach、token_gap——在所有16行均为零。这个有限记录不构成安全证明或零事件率。训练阶段另有 **1,030 次 invalid_commit、3 次 separation_breach、35 次 terminal events**，训练服务26,159，普通合法换主为零。不能将训练事件与最终评估平均混合，更不能把最终没有 separation_breach 扩大成整个学习链无伤害。[summary：learner.training_hard_events、training_terminals、training_service][summary]；[intake §§3、5][intake]。

所有参考及最终行的合法换主均为零、首时刻均为 null、换主后服务均为零。原卡以实际首次非零 `cas_applied` 的 native post-step tick 定义首时刻，不用1,200作为缺失哨兵。当前只有普通 incumbent 服务的比较，没有观察到可用的来源干预切点。[冻结卡 §4][card]；[readback 的 first-transfer 与 native_panels][readback]。

## 三、该比较识别了什么，没有识别什么

B06 保留原 LOW_LR 学习器：STRUCTURED、raw service-Q、原 mean-MSE／BCE-with-logits／PPO及其余辅助目标、正常训练 Welford 更新，两个原 AdamW 参数组均为3e-5。它不是重新打开已结束的 service-Q sigmoid／联合 NLL 包。模态与抽样在普通续约时分别使用运动均值／高斯运动，以及概率阈值／Bernoulli 的 prepare、commit；非续约保持命令与原有处理，native 投影、证书和所有权应用不变。[冻结卡 §§2–3][card]；[summary：learner.configuration][summary]。

实际研究链是：路线／退化及续约事件 → 两个物理实体的局部因果观测与真实消息 → 当前 owner／standby 所属的 active／shadow 循环状态 → 联合运动与意图选择 → native 投影、证书及所有权处理 → 完整服务、能量与事件。最终参数和 Welford固定，不等于两种执行的后续循环状态相同；不同动作产生不同轨迹和后来的观测、消息及预测输入。这些动态后果属于本次联合执行法则的总比较，不能从最终事件汇总中拆成运动噪声、意图噪声及其交互的单独效果。[card §§2–4][card]；[intake §3][intake]。

因此，“抽样的无效提交更多”不是“Bernoulli 噪声导致全部服务损失”的诊断。运动可改变随后证书／消息条件，意图可改变后续信息与动作，二者共同作用；现有结果也不定位历史学习率、归一化、辅助目标或循环共适应的原因。私有标签克隆中的 promotion 属于监督标签生成，不是普通合法换主。[card §§2–4][card]。

来源议程中的三个层次保持分开：**普通合法换主**是实际 native 事件；**可用来源原点**还需在真正首次应用切点具备该来源比较所需的状态与输入；**COPY−RETAIN、SHADOW−COPY 的价值**则需匹配来源干预及其完整后果。即使未来一次普通换主出现，也不会自动证明后两者。本例三者没有被依次建立，来源量仍是未估计，绝不能填零或判负。若未来发生换主，时间上的换主后服务也不直接证明包的物理来源或换主的因果收益。[card §4][card]。

**对本次停止最强的异议**是只有一个训练实例和每条件两个样本，另一个控制器可能改变差分符号；组件单独抽样也可能优于联合抽样。这些都是实质不确定性，而不是已经排除的解释。它们阻止总体负结论，却不迫使每个有限开发选择都等到总体结论才可停止。

## 四、已测成本与替代对象的价值比较

### 完成的 B06 不是廉价零学习探针

实际有一次初始化及一次真实学习，**16×32×128=65,536** 普通训练转移，**16×4×8=512** optimizer steps；只选择 update16。十六个更新的两组 LR 及损失／梯度有限性读数均可读。参数L2位移 **1.711241358519297**，初始范数 **38.248183881577795**，相对位移 **0.04474046045735298**。这表明本次发生了真实学习，不证明更新最优或足够支持换主。[summary：actual_exposure、learner.curves、parameter_movement][summary]；[E0 的 Focused technical acceptance][evidence]。

原生训练计算不只有普通转移数。N=65,536，实际 eligible E=7,631，私有后果步 H 未测，`0<=H<=20E=152,620`；所以 `2N+2E+H` 为 **146,334–298,954** 次原生训练调用。next-label steps为65,536，next-mask有效数65,501，二者不能混用。抽样评价实际R=1,240次续约，对应4,960次normal、2,480次Bernoulli、12,400次uniform。标签和抽样是算法工作，不是验证开销；另有前向、critic、recurrent replay、backward、optimizer、构建／加载及输出。[readback：actual_exposure][readback]。

完整计费为 **215.02秒 OS整链wall＋10秒既有检查＋1秒保守收集读回收费＝226.02秒**，在原1,800秒上限内。runner较窄的204.713815717秒不能替代OS范围，其已分摊prior11秒也不再加一次。OS user+system CPU221.09秒只覆盖该链，早期检查CPU未测；supervisor215秒为整数时长，查询时的uptime不是运行时长。Git暂存／传输失败及修复发生在科学启动前，不构成另一份负实验或额外被接受的invocation。[E0 的 Execution、Work/resources][evidence]；[intake §5][intake]。

OS最大RSS656,375,808 bytes与runner各自self／reaped-child最大值635,867,136 bytes范围不同，不能相加成同时内存。scratch和精确H继续未测；这些缺口不损坏已测原生主量，也不要求为了作本次开发停止再加profile或扩展native接口。[evidence][evidence]。

### 最强具体替代：一个新独立训练实例的相同比较

这项替代确有科学价值：它会观察联合执行损失是否出现在另一随机实例上。新结果若转成有用正均值且代价可接受，会削弱“现在不继续开发该规则”的理由；再次负向会增加有限一致性；带内或相反的行模式会显示条件性。但它不追溯改变seed113结果，也不因又有一个实例就建立总体负结论。新的初始化、训练随机、派生reset及评价抽样均会变化，所以一次新结果还不是孤立估计“纯训练种子方差成分”。

| 选择 | 它能改变的当前判断 | 主要工作／未测量 |
| --- | --- | --- |
| **本次选定：保留既有测量并停止该支线当前扩展** | 对已观察控制器保留模态，不继续追加当前联合规则 | 0新科学调用；不补造总体结论 |
| 一个新独立LOW_LR实例、相同最终模态／两样本比较 | 另一随机实例能否使联合抽样重新成为值得开发的执行候选 | 1 learner；65,536普通转移、512 steps；4初始＋4最终模态＋8抽样＝16 episode，至多19,200评价tick；新E/H/R与耗时未测 |
| 对seed113再加政策样本 | 更细地描述这个固定控制器的抽样变化 | 不增加训练实例；另有真实episode成本；不能当成当前读法的必做复核 |
| 只抽样运动或只抽样意图等新B | 一个不同执行法则相对同检查点模态的原生表现 | 新科学处理；联合结果没有给出其单独增益或原因分解；本轮未选择任何组件配置或网格 |

新独立实例仍只需要一个learner，不需为相同模态checkpoint重复训练。其原生训练界为 **131,072–1,572,864**，评价抽样uniform至多96,000，均在已提供成本文件中；新E/H/R不得用B06实测值冒充。两个保留抽样轨迹不是best-of-many搜索，没有a^N／b^H候选树或来源fork；若加入全组件、强度、checkpoint、reset搜索，就另增了当前判断不需要的维度。[EXPOSURE_AND_COST 的 unselected_one_seed_B_alternative][cost]；[card §6][card]。

B06的226.02秒可作相同规模工作的**条件性规划参照**，不是新对象完成保证；没有证据表明这项替代必然超过拟议1,800秒完整cap，也不能把已有程序、有限计数或零新代码称为零成本。若它被选择，检查、build/cache、加载、学习／标签、全部评价、归约和发布都属同一完整界。**本轮没有选择这项替代，因此没有冻结新seed、给出新运行预算或委派实现。** 旧未用额度1,573.98秒不转成下一次额度。[cost][cost]；[readback：cost_seconds][readback]。

本次不购买该替代的理由是**问题价值的取舍，而非工具、费用或方法上的禁止**：现有同信息模态对照已提供完整服务，联合规则在固定主量及每个条件平均代价上均无当前采用理由；我们也没有要发表“模态在训练总体稳定优越”的结论。再买一例主要减少跨实例不确定性，但目前没有必须靠消除这种不确定性才能作出的采用决定。选择把这一不确定性作为结论边界保留，比把每个残余可能都转换为追加调用更符合当前开发问题。该判断并不声称测得了信息价值／时间比，也不否定未来有具体使用需求时重新选择有限跟进的合理性。[method §§11.8.1–11.8.3、11.9][method]。

组件B可以在没有先前正组件结果时合法提出；**缺少正结果本身不是否决门槛**。本轮不选它，是因为无效提交增量没有定位组件原因，现有提案也没有给出一个比已测模态更值得采用的特定组件法则及独立理由。以“也许某个组合有效”为由同时买运动／意图／强度网格，或为找出正例而改阈值、换reset、扩展样本，不是这次窄问题的必要工作。不存在先做完整原因诊断才允许未来B的要求。

## 五、冻结读法、预测及停止后的科学边界

原卡第4行由 `Delta_exec<=−24` 直接触发；第6行由全部12个最终评价episode无合法换主触发。第1行有用正执行增量、第2行相对获益但低于初始化、第5行出现合法换主均不适用。第3行所容纳的有限样本不确定性仍需说明，但不能据两个个别正样本把主量改写成带内；第7行受损／未完成不适用，缺少scratch或H不抹去其独立可信结果。[冻结卡 §5][card]；[intake §4][intake]。

先前DM和本节点所记 **`Delta_exec<=−24，低置信度`** 在−77.5上获得符号与阈值量级命中。它不是精确预测−77.5；没有记录概率，也不能称作概率校准。与之竞争的 `>=+24且权衡值得开发` 没有出现。预测命中不增加训练样本，更不把猜想中的噪声损害变成组件因果。没有记录换主次数下限，因此不为零换主补记一个预测成功。[card §5][card]；[intake §4][intake]。

本轮未选新实验，不对已知B06结果重新包装一个前瞻预测，也不把未购买的新种子的结果写成必然负向。当前无需更多证据即可执行的唯一科学后果是：**结束这项联合执行规则的当前追加投入，保留本例模态默认与全部证据，不自动增加seed、样本、训练时长、组件处理或来源干预。** 这是可依据未来具体问题重新评估的开发决定，不是永久禁止随机执行的规则。

完整诊断、精确策略最大值、全支持census、强制首换主见证和历史replay均不购买。代价是明确放弃组件原因、最优性、普遍可达／不可达、精确轨迹等价及来源价值等更强结论，而不是把这些工作转移为下一个强制A。两样本和单训练实例不足以给出训练总体置信区间；本次选择不获取该结论。若后来要比较学习表现的可重复性，独立训练实例比同checkpoint补episode更直接，但这条方法意见不构成自动实验或额外Pro启动门。[method §§4、5.1–5.2、11.4、11.8–11.9][method]。

没有新的科研实现需要工程范围§4设施；不新增scheduler、registry、guard、source-fork框架或profiler服务。也没有为了“证明可以停止”重跑smoke、原始测试或历史仿真。普通源码／runner／测试预算和既有科学完整性要求保持，而本次没有使用新科学计算额度。[工程范围 §§4–5][scope]。

## 六、早期学习率结果与来源议程保持原义

B04／seed89的LOW_LR−CONTROL为 **+182.75**，LOW_LR低于自己的初始化57；CONTROL的TARGET/K8提前在684 tick分离终止及固定余段零服务仍保留。B05／seed101差分为 **+236.25**，LOW_LR高于自己初始化219.75，CONTROL初末差−16.5；同时保留TARGET/K4_TO_K12的 **−277**、LOW_LR的 **209次invalid_commit**、CONTROL评估零无效提交、双方完整终局，以及CONTROL **3次训练合法换主**。两个LR配对的+209.5只作描述，不能加入本次B06成为“三个LR配对”。[前次完整决定 §一及§八][prior]。

B06没有3e-4对照，其问题是同一3e-5最终checkpoint的执行法则。它的模态初末增益不重新裁定B04／B05的LR效应；B06训练／评估无换主也不删除B05的三次训练事件。历史训练与评估的分布、权重、Welford及曝光差异仍阻止用那些训练事件认定“模态是缺少换主的唯一原因”。前次结束的预测包扩展、B03／B02的各自限定读法和历史R02关闭不被本次重新打开。[prior 开篇、§一、§八][prior]。

首次普通合法应用时的RET​AIN/COPY/SHADOW问题仍未被否定；COPY／RETAIN已经足够、deadline replay可包含增益、checkpoint／角色共适应等替代解释也未被排除。这里不因没有来源支持而判整个方向失败，不为了让来源议程显得成功而强制触发换主。与此同时，议程尚未被否定也不等于已有另一个选定、可无限推进的实验。

本决定不改变Portfolio生命周期、优先级、工作集、容量、融合或注册状态，不替Portfolio安排下一方向；Root执行及Portfolio规划按其现有分工处理。本轮具体问题的窄停止不能被转写为整个DISH的PARK／CLOSE／RECAST。需要的科学取舍已经在此形成，不把它变成等待额外审批或补全C义务的暂停。[AGENTS §§1–2、4–5、8][agents]；[本次固定TASK的范围][task]。

## 七、实际读取与交付更正的边界

科学材料统一使用 **`6b45ea47bea500bea11f1215080653a8df19bdd6`**。本次是交付授权更正，不是新实验或换证据版本：复用本对话前一受阻轮通过连接GitHub已读取的同一不可变材料，并补读下列当前相关内容。未通过先前附件、moving branch、外部镜像或清单外文献补全科学事实。

下表C/为 `docs/research/candidates/degraded_incumbent_shadow_handover/`；P/为C/下 `pro_packets/20260907_post_b06_convergence/`。

| 允许的实际科学来源 | 阅读范围及复用说明 |
| --- | --- |
| [C/DISH_SAMPLED_EXECUTION_B06_RESULT_INTAKE_20260907.md][intake] | 本轮完整读取§§1–7，包含尾部；其文献覆盖是DM报告，不冒称本节点另查了本地库 |
| [C/DISH_SAMPLED_EXECUTION_B06_RESULT_EVIDENCE_20260907.md][evidence] | 本轮全文；少量标点编码异常不影响数值，与原始JSON／intake对照，不改写原文件 |
| [C/sampled_execution_b06_20260907_run01/summary.json][summary] | 复用前轮在同SHA上的完整分段阅读，含十六更新、四模态、四参考、八抽样及全部字段；本轮补读1–90行的曝光／配置，返回相同blob `fb07f917b27cab5639bbf4ceb6fb835b72482d8d` |
| [C/sampled_execution_b06_20260907_run01/DM_READBACK.json][readback] | 本轮全文；派生复算不计为重复实验 |
| [C/DISH_SAMPLED_EXECUTION_B06_SCIENCE_CARD_20260906.md][card] | 本轮全文，分段补齐§§6–7；不将卡冻结时的未执行状态当成后来未完成 |
| [C/pro_packets/20260906_post_b05_convergence/archive/RESPONSE.md][prior] | 本轮1–40、130–180行；复用前轮同SHA已读的§六完整预测及§七，未递归跟随其清单外引用 |
| [P/EXPOSURE_AND_COST.json][cost] | 本轮全文；已测工作与未选择替代分开 |
| [P/ISSUE_SNAPSHOT.json][snapshot] | 复用前轮同SHA完整快照及七条历史交付；记录快照时刻2026-09-07 15:49:53.340745 UTC |
| [docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md][method] | 本轮35–112及345–末尾，含§§4、5.1–5.2、11.4、11.7–11.9 |
| [docs/project/ENGINEERING_SCOPE_SPEC.md][scope] | 本轮48–102行，§§4–5；不使用旧对象专属附款 |
| [AGENTS.md][agents] | 复用前轮同SHA已读§§1–2、4–5、8及相关正文；不把其指向其他路径的链接当作扩大本次读取／写入权限 |

以上十一项均有实际连接读取；复用与本轮新读取分列，不冒称重跑了检查、重新审计了源码或读取了清单外底层文件。当前没有妨碍形成窄停止决定的证据访问缺口。精确H、scratch、总体不确定性、组件原因、来源原点及来源价值的未知，只限制各自较强主张。

本轮在 **2026-09-07 19:05:27 UTC（12:05:27 PDT）之前**已实际读取 [Issue4][issue] 正文及七条既有交付评论；其正文仍是post-B05历史讨论，最近既有交付为 [post-B05评论][comment-b05]，不取代本次post-B06固定问题。其余已读评论为 [post-B02][comment-b02]、[post-A01][comment-a01]、[post-A02][comment-a02]、[post-B03][comment-b03]、[post-witness][comment-witness]、[post-B04][comment-b04]。写入前再次检查了当前分支、目标与新评论。

交付溯源另外读取了固定归档版本 **`dba5cfc8a58eba9a0c1b2cefb9e954f3c92a7e71`** 的 [BLOCKER_RESPONSE.md][old-blocker] 和 [TRANSPORT_FACTS.json][old-transport]。它们只证明旧请求终止于交付基底冲突，不是旧科学裁决，更不是B06的新证据。本次 [更正TASK][task] 明确允许在该基底的普通后继HEAD上只新增不同的 `20260907_post_b06_delivery_correction/archive/RESPONSE.md`；旧response路径及归档均不改动。交付分支推进与固定科学证据是两回事。

本次没有执行项目代码、模型初始化、native状态／episode、backward、optimizer step、测试或实验；没有实施任何科学状态或Portfolio变更。唯一交付范围是本文和一条含固定提交文件链接的Issue评论。**科学结论已经形成：本次联合抽样规则停止当前扩展，不选择下一科学调用；来源议程保持未被否定，全部有限结果及不确定性原样保留。**

[intake]: https://github.com/CartmanFatass/My-paper-code/blob/6b45ea47bea500bea11f1215080653a8df19bdd6/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_SAMPLED_EXECUTION_B06_RESULT_INTAKE_20260907.md
[evidence]: https://github.com/CartmanFatass/My-paper-code/blob/6b45ea47bea500bea11f1215080653a8df19bdd6/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_SAMPLED_EXECUTION_B06_RESULT_EVIDENCE_20260907.md
[summary]: https://github.com/CartmanFatass/My-paper-code/blob/6b45ea47bea500bea11f1215080653a8df19bdd6/docs/research/candidates/degraded_incumbent_shadow_handover/sampled_execution_b06_20260907_run01/summary.json
[readback]: https://github.com/CartmanFatass/My-paper-code/blob/6b45ea47bea500bea11f1215080653a8df19bdd6/docs/research/candidates/degraded_incumbent_shadow_handover/sampled_execution_b06_20260907_run01/DM_READBACK.json
[card]: https://github.com/CartmanFatass/My-paper-code/blob/6b45ea47bea500bea11f1215080653a8df19bdd6/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_SAMPLED_EXECUTION_B06_SCIENCE_CARD_20260906.md
[prior]: https://github.com/CartmanFatass/My-paper-code/blob/6b45ea47bea500bea11f1215080653a8df19bdd6/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260906_post_b05_convergence/archive/RESPONSE.md
[cost]: https://github.com/CartmanFatass/My-paper-code/blob/6b45ea47bea500bea11f1215080653a8df19bdd6/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260907_post_b06_convergence/EXPOSURE_AND_COST.json
[snapshot]: https://github.com/CartmanFatass/My-paper-code/blob/6b45ea47bea500bea11f1215080653a8df19bdd6/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260907_post_b06_convergence/ISSUE_SNAPSHOT.json
[method]: https://github.com/CartmanFatass/My-paper-code/blob/6b45ea47bea500bea11f1215080653a8df19bdd6/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[scope]: https://github.com/CartmanFatass/My-paper-code/blob/6b45ea47bea500bea11f1215080653a8df19bdd6/docs/project/ENGINEERING_SCOPE_SPEC.md
[agents]: https://github.com/CartmanFatass/My-paper-code/blob/6b45ea47bea500bea11f1215080653a8df19bdd6/AGENTS.md
[task]: https://github.com/CartmanFatass/My-paper-code/blob/25c93b776b8d8a8d706ef1259601775d15210594/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260907_post_b06_delivery_correction/TASK.md
[old-blocker]: https://github.com/CartmanFatass/My-paper-code/blob/dba5cfc8a58eba9a0c1b2cefb9e954f3c92a7e71/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260907_post_b06_convergence/archive/accepted_old_request/BLOCKER_RESPONSE.md
[old-transport]: https://github.com/CartmanFatass/My-paper-code/blob/dba5cfc8a58eba9a0c1b2cefb9e954f3c92a7e71/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260907_post_b06_convergence/archive/accepted_old_request/TRANSPORT_FACTS.json
[issue]: https://github.com/CartmanFatass/My-paper-code/issues/4
[comment-b02]: https://github.com/CartmanFatass/My-paper-code/issues/4#issuecomment-5557093321
[comment-a01]: https://github.com/CartmanFatass/My-paper-code/issues/4#issuecomment-5558729980
[comment-a02]: https://github.com/CartmanFatass/My-paper-code/issues/4#issuecomment-5560502547
[comment-b03]: https://github.com/CartmanFatass/My-paper-code/issues/4#issuecomment-5561089362
[comment-witness]: https://github.com/CartmanFatass/My-paper-code/issues/4#issuecomment-5562295763
[comment-b04]: https://github.com/CartmanFatass/My-paper-code/issues/4#issuecomment-5563973543
[comment-b05]: https://github.com/CartmanFatass/My-paper-code/issues/4#issuecomment-5565621457
