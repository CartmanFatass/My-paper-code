**保留窄停止，当前不选择任何后继。** 选择所列方案(a)：保留 DIRECT，维持 B07 固定 OWN_COMMAND_MEAN 和 B06 联合抽样执行规则的两项已接受窄停止；不把停止扩大为保留宿主上整个普通来源应用家族的关闭或重构。首次普通合法应用时的 RETAIN/COPY/SHADOW 议程仍未解决，但本轮不为它配置新的实验、诊断、种子、卡片或继续评估任务。

理由是：B07 已经用完整原生服务回答了所选固定均值的性能问题，负差分与能量增加支持停止该候选；B06 的不同联合执行规则也有自己的不利结果。本次有界源码／问题评估没有提出值得购买的具体新干预，足以决定**现在不安排后继**，却没有把这两项不同干预的负结果变成整个普通来源应用家族的投资结论。保留这个区分不要求先证明家族不可能成功，也不要求为了保持议程未决而继续消耗计算。[本次问题 intake §§2–7][question]；[B07 intake §§2–3、5–6][intake]；[证据规范 §§3–5.2、11.8–11.9][method]。

## 一、停止的精确单位与本轮改变

B07 的停止单位是：在已接受的 GROUND-TERMINAL-LINEAR-CLEARANCE-A03 信息／所有权宿主、修正普通续约边界、STRUCTURED/LOW_LR 学习器及既定曝光下，使用固定 `3*tanh(m+a_prev/3)` 取代新训练匹配对照的 `3*tanh(m)` 这一 OWN_COMMAND_MEAN 候选的当前扩展。它不是对所有自车状态输入、所有残差控制、所有学习目标或所有来源选择机制的拒绝。[B07 E0 §1][evidence]；[DIRECTION 的 B07结果及窄停止段][direction]。

B06 已停止的是同一最终控制器的联合高斯运动／Bernoulli意图抽样执行相对模态执行的扩展。它与 B07 的两臂重新学习及最终模态比较不是同一处理或同一估计量，不能把两个负均值合并为一份普通来源家族的重复检验。DIRECT 留作本例已有开发默认，不被升级为最优控制器、安全策略或稳定占优基线。[P53 source intake §§3–4][source]；[本次问题 intake §§2–5][question]。

本轮新增的方向层决定，仅是把“暂无候选，停止范围待决”收敛为**窄边界保持、无后继选定**。既有 B07 负分支不是本轮才生效，既有 B06 停止也未被撤销。不新增第二个 B07 种子、系数反转／调优、辅助损失变体、来源分支或下一轮抽象筛选。P62 明确允许没有具体候选时作这个范围决定，因此无需虚构一个实验才能完成任务。[P62 handoff 的 Return route、Budget/stop/report][handoff]；[问题 intake §§6–7][question]。

## 二、B07的完整负结果与全部相反事实同时保留

B07 是一个匹配训练种子127的 B/EXPLORE 观察。主量仍是四个条件等权的最终 OWN−DIRECT 服务差分，不是初末差之差。E0 保留的全部初始／最终服务如下；本次使用已接受的记录，不重新运行归约或读取未列出的底层结果文件。[E0 §§2–3、5][evidence]；[冻结卡 §4][card]。

| 条件 | DIRECT初始 | DIRECT最终 | OWN初始 | OWN最终 | 最终OWN−DIRECT | DIRECT初末变化 | OWN初末变化 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| TARGET_VISUAL_MASK / K8 | 604 | 770 | 473 | 549 | −221 | +166 | +76 |
| TARGET_VISUAL_MASK / K4_TO_K12 | 446 | 400 | 495 | 474 | +74 | −46 | −21 |
| TERRAIN_RELAY_MASK / K8 | 699 | 910 | 655 | 581 | −329 | +211 | −74 |
| TERRAIN_RELAY_MASK / K4_TO_K12 | 365 | 692 | 385 | 627 | −65 | +327 | +242 |
| **等条件均值** | **528.5** | **693** | **502** | **557.75** | **−135.25** | **+164.5** | **+55.75** |

`Delta_mean = 557.75−693 = −135.25`，满足原卡 `<=−24` 的负分支；+24仍是原卡在1,200-tick范围上的2%开发尺度，不是本轮新设的家族排除阈值。一个+74条件没有被隐藏，也不把固定主均值变成带内或未决；同样，三个负条件不是“所有条件皆负”的结论。无需统计显著性或所有条件同号才可按该有限结果停止候选。[intake §2][intake]；[冻结卡 §5][card]。

全部16个初始／最终episode均实际完成1,200 tick，共19,200 tick，没有提前评价终止或未执行余段。每臂／阶段各4行、4,800 tick。不能以缩短共同观察期、按存活长度归一化、选最好条件或更换终点来改善该均值。[E0 §§2–3][evidence]。

同一初始参数并未使两个参数化的初始控制器相同。DIRECT的+164.5和OWN的+55.75是各自接口下的初末伴随观察；OWN在TARGET/K4_TO_K12和TERRAIN/K8分别低于自身初始21和74，DIRECT也有−46条件。正初末均值既不能替代最终差分，也不独立识别学习速度、初始化偏置或干预对学习过程的纯贡献。[intake §3][intake]；[card §4][card]。

| 最终条件 | DIRECT无效提交 | OWN无效提交 | OWN−DIRECT能量 |
| --- | ---: | ---: | ---: |
| TARGET_VISUAL_MASK / K8 | 0 | 0 | +8,783.0389 |
| TARGET_VISUAL_MASK / K4_TO_K12 | 75 | 0 | +24,222.2865 |
| TERRAIN_RELAY_MASK / K8 | 4 | 0 | +9,166.2085 |
| TERRAIN_RELAY_MASK / K4_TO_K12 | 40 | 32 | +12,690.8255 |
| **合计无效提交／平均能量差** | **119** | **32** | **+13,715.5899** |

最终无效提交均值由29.75降至8，是原生事件计数改善，必须保留；第一个条件是0对0，不称四条件都减少。没有提交机会分母就不能称为拒绝概率改善。OWN最终能量在四个等时长条件均更高；DIRECT／OWN最终能量均值分别为283,737.1103／297,452.7002。初始无效提交合计32／91、初始能量均值266,703.9264／296,285.8062也保持其阶段身份，不混入最终主比较。[E0 §3][evidence]。

训练与评价分开：DIRECT／OWN训练服务为29,426／29,548，无效提交为4,366／4,405，分离越界为1／2，终止事件各32，训练能量约15,122,722.5574／15,933,012.0818。不能用OWN稍高的训练服务或较少的最终无效提交挽救最终服务损失。所有评价行的其他六类硬事件为零，不抹去训练越界，也不是安全或零风险结论。[E0 §3；intake §3][evidence]。

两臂各实际完成16更新、65,536普通转移、512 optimizer steps；相对初始范数的参数L2位移分别为 **0.04690254949701972／0.0484554855508188**。真实优化和参数移动发生了，但它们不是候选价值、学习充分性或来源机制成功的证据。四条件和16个episode都不是独立训练种子；两个learner共同构成一个配对观察，而非两个独立配对。[E0 §2][evidence]；[机器曝光记录 historical_B07][cost]。

原DM和本节点记录的低置信度 `Delta_mean>0` 预测**未命中**。此前只说跨越+24不确定，没有数字概率，不能给它补造校准分数，也不能把提前列出的反向可能性重记为正号预测成功。owner预测仍为未取得。本轮没有新实验，因而不对已知结果另包装一个“事前预测”。[intake §3][intake]；[card §5][card]。

## 三、为什么不把无后继扩大为保留宿主的家族关闭

**支持本轮无后继的最强证据**，是已选OWN固定均值的−135.25原生损失、所有最终条件能量增加，叠加另一项已结束联合执行规则的−77.5及当前没有获提名的具体新原生价值假设。继续运行已停止的处理不会仅因“来源尚未测得”而获得理由。源码可编辑、存在多个损失项或还有尚未试过的系数，本身也不是一个已说明价值的下一研究问题。[问题 intake §§2–5][question]。

**反对更宽关闭的最强证据**不仅是来源量未估计。B07确有+74条件、最终无效提交改善和正自身初末均值；B04/B05的LOW_LR−CONTROL分别为+182.75和+236.25，保留了真实有限改进。后者同时有−277条件、LOW_LR的209次最终无效提交，以及训练CONTROL的**三次普通合法换主**。这些事实并不救活B07或B06，却反对将记录概括为“该宿主没有可学习的原生控制或没有发生过普通应用”。[B07 intake §3][intake]；[B05 intake §§4–5][b05]。

历史的正证据也不夸大：B04的LOW_LR仍比自身初始化低57，CONTROL曾在tick684提前终止；B05的LOW_LR初末+219.75、CONTROL初末−16.5，以及−277和−116的条件损失保留。两LR配对的+209.5仅作描述，B06/B07不是它们的追加重复。B05的三次训练换主发生在CONTROL训练路径，不保证B07最终策略换主，也没有提供匹配的RETAIN/COPY/SHADOW效果。[B05 intake §§4–5][b05]。

B06的不利结论亦不反向改写：−77.5联合抽样损失、最终模态／抽样无效提交均值3.5／31.875、抽样能量+4,642.6427与零最终换主保持；两条个别抽样胜出14和3、模态初末+292.5、抽样相对初始模态+215且TERRAIN/K8为−57也保持。训练的1,030无效提交、3次分离越界、35次终止与评价分列。这不是B07持续加速度有害的因果证据。[P53 source intake §4][source]；[DIRECTION相关停止记录][direction]。

方案(b)在概念上可以是一项**有界投资停止**，并不必先证明不可能性、稳定劣势或穷尽所有方法。我不选它，原因不是给关闭额外设置证明门槛，而是当前记录的决策覆盖仍集中在两个具名处理及一次有界提名评估。当前两个方案都不购买科学调用；方案(a)已经解决“现在停止投入、无具体下一步”的实际问题，而无需再赋予未直接检验的普通来源应用家族一个更大的停止范围。现有正反证据和有限筛选没有使这个额外范围更值得选择。[问题 intake §§3、5–7][question]；[method §§4、5.2、11.8.1–11.8.4][method]。

这不是“永远不能关闭未解决问题”，也不是“有残余可能就必须持续研究”。本次采取的是**不资助当前未提出的后继，同时保留家族问题的未决状态**。没有命令DM再次筛选到找出候选，没有开放式修复计划，更没有为了避免收益未知而自动生成下一任务。

## 四、源码能证明路径存在，不能替未提出的干预证明价值

保留的普通学习链为：续约事件 → 每个物理车辆按当前owner选择incumbent／shadow循环副本 → 既有观测和消息 → 普通运动及prepare／commit提案 → native投影、消息及应用处理 → 原生服务与事件 → 真实PPO和共享辅助目标更新。prepare来自incumbent、commit来自standby shadow，二者随后序列化在native owner槽；序列化位置不等于神经决策的信息归属。[P53 source intake §2][source]；[问题 intake §3][question]。

本次读取的native消费者显示：pending intent先核对原certificate、readiness／snapshot时序、owner／epoch／序列、共同SOURCE、电量、几何和动作变化等；成功才更新所有权并触发普通循环状态提升。当前续约投影在新origin certificate调用之前更新`s.a`。稍后服务用实际送达数据的年龄、误差和链路条件判定。投影后的动作、较少无效提交、一次原生应用以及有价值的来源状态，是不同事实，不能互相替代。[native `complete_prepared_tick`，433–497][native]。

按照已接受的P53信息图，actor的自车加速度可用；但重复的prepare／warmup字段不是本地可查询的完整origin／readiness／version证书。partner字段在保留的presence标记下读取当前native partner值，另有native摘要字段，故该A03宿主并不支持“严格只使用新鲜通信数据”的去中心化主张。本次保留这个信息上限，不将其升级为新的观察接口修复任务。[source §2][source]。

共享辅助路径确实存在。本次所读engine将四个masked辅助loss平均，以0.1加入policy、0.5 value和−0.01 entropy项，然后一次backward、梯度裁剪及optimizer step。这个源码事实只说明梯度路径，不测量任务间梯度冲突，更不决定去掉、隔离或重加权任一项的原生收益。未观察到某个修复原因并不禁止一个另有理由的B；但仅凭这个可操作位置，本轮没有形成一个特定替代处理。[engine 620–647，尤其638–641][engine]；[问题 intake §3][question]。

文献也不补出缺失的提名理由。固定`LITERATURE_SCOPE.json`记录190项正式目录中的12个元数据命中、排除两个合成fixture，并说明GPVD所查段落属于价值分解中的动作样本梯度保护、状态分组和内在奖励，不是本研究的循环PPO辅助loss干预。UTE的既有段落关于Gridworld／Atari动作重复，只保留持续不当动作可能有害这一反对解释；它未识别B07原因。本节点读取的是这些限定的检索记录和intake，没有另查论文、扫描全库或验证所有命中。既不移植新的价值分解／奖励包，也不宣称那些方法无效或文献中没有可用办法。[问题 intake §4][question]；[LITERATURE_SCOPE 的 verified_sources、coverage_limit][literature]；[P53 §6][source]。

全部B07训练和评价均无普通合法换主，首时刻为null、换主后服务为零。因此普通incumbent服务主量仍有效；**来源原点资格、COPY−RETAIN和SHADOW−COPY仍未估计，不能填零、判负或称不可能**。私有未来标签克隆中的promotion是监督工作，不是可替代的普通来源原点。B05的普通训练事件也只证明发生过路径事实；来源价值仍需相应实际普通切点上的匹配来源干预，后者不是任何普通服务B的先决条件。本次不购买该干预、强制事件、特权mask或私有见证。[card §4][card]；[intake §§2–3][intake]；[source §2][source]。

## 五、已知工作、真实学习参照与不购买的理由

已完成B07保留两个learner、131,072普通转移、1,024 optimizer steps和16个完整评价episode。实际eligible数DIRECT24,846、OWN24,835使`2N+2E+H`训练调用界分别为180,764–677,684及180,742–677,442，合计 **361,506–1,355,126**。H仍未测，合计上界993,620；零换主不等于私有标签后果工作为零。[E0 §§3–4][evidence]；[cost：historical_B07][cost]。

成本只按其真实范围报告：CM计入的463.243287086秒加DM归约／发布0.5902971秒，得到 **463.83358418601877秒已计小计**；分摊DIRECT约231.859461804秒、OWN约231.974122382秒。另有未单独计时的syntax check，0.02秒closure及1秒final-write还是注明的allowance，不是全部实际尾部时间。因此不能把小计写成精确整链测量，或宣称已严格证明完整费用符合历史cap。已计部分未见超限、原生科学结果有效、完整费用仍有缺口，可以同时成立。[E0 §4][evidence]；[intake §4][intake]；[cost][cost]。

完整聚合CPU、scratch峰值和精确H未测。self与reaped-child的629,612,544-byte RSS是各自最大值，不相加成同时进程树峰值。已有清理被策略阻止的scratch保持原状；本轮不重试、不绕过，也不把清理变成科学前置条件。资源缺口只限制依赖它们的主张，不抹去服务读数。[E0 §4][evidence]。

为判断无后继是否只是用诊断替代学习，本轮明确比较了材料给出的**最小真实B工作尺度**：

| 工作因素 | 仅用于尺度比较的真实B例子 |
| --- | --- |
| 比较单位 | 2个训练臂、1个匹配训练种子，对照为新训练的同信息DIRECT/LOW_LR |
| 学习 | 每臂16×32×128=65,536普通转移、512 optimizer steps；配对131,072及1,024 |
| 最终评价 | 每臂仅update16、四个完整条件，共8个episode、至多9,600 tick |
| native标签工作 | 每臂`2N+2E+H`，N=65,536、0≤E≤N、0≤H≤20E；131,072–1,572,864调用，配对262,144–3,145,728 |
| 其他算法工作 | 每臂2,048次batch32普通策略前向，另有recurrent replay、critic、backward／optimizer、构建加载与发布 |
| 额外验证 | 仅在实际有改变时作一项聚焦的changed-behavior／primary覆盖，复用可信检查；不是另一科学调用 |
| 选择与搜索 | 无候选／轨迹树、无来源fork；没有a^N或b^H的前置搜索 |

这张表**没有候选处理、种子、master、卡片或新cap**，不是一个隐含获准的B。初始参考仅在所选主张需要初末比较时另有用途，并非这个假想最终服务主量的门槛；它们在已经完成的B07中仍是原卡必须保留的16行的一部分，不能追溯删去。标签是原学习算法工作，不可为了显得便宜而无声移除。[cost：minimal_real_B_scale_comparison_only][cost]；[问题 intake §5][question]。

B07的已计小计和其16行评价，与上述8行最终评价尺度不同；不能仅减掉八行便声称已测新运行时间，也不能从有限调用数、native代码、并行核数或预算倍数推断成本优势。未来未指定处理的E/H、检查及runtime未知。历史1,800秒／臂和3,600秒／对不延续为新额度。本轮不购买的原因不是昂贵、缺少headroom或不能完成，而是**没有具体新干预及其足以支持当前购买的差异化原生价值理由**。[cost][cost]。

一项新的负后跟进不必先有正结果或因果定位；参数移动、可运行源码和一个可承受的配置算术也不自动构成购买义务。若以后有具体问题，独立训练用于相应重复性，源状态干预用于相应来源归因；本轮没有选择它们。完整gate census、精确最大值、历史replay、成本校准运行、强制换主见证及全原因诊断都不追加，也不移到一个先行A。相应放弃总体稳定性、最优性、普遍可达性、组件原因及来源价值等更强结论。[method §§11.4、11.7–11.9][method]。

## 六、终止于当前范围，不制造新等待条件

无需任何新科学观察即可作出本次范围选择。仍未知的是未测控制器／干预的表现、当前效应的训练总体变化、持久性或辅助梯度的因果作用、可用普通来源原点及匹配来源价值。未知保留为结论边界，不被自动转换为必须完成的评估清单。

本决定没有科学／规范冲突需要例外：P62的无具体候选分支允许本次回答，证据规范允许基于有限结果停止最小单位，且未要求正向重复、完全解释、调优上界或更强C类别。工程范围§4不需新增设施；没有实现、测试或§5预算使用／超限。也不新设reviewer、审批、Pro启动条件或验证服务。[handoff][handoff]；[method §§5.2、11.4、11.8][method]；[工程范围 §§4–5][engineering]。

既有委托链完成本决定的常规接收后，本次无后继路线即告穷尽，而不是等待修复、更多文献或另一个抽象评估。本节点不替Portfolio配置工作集、优先级、容量或生命周期，不把“目前没有获选任务”改称整个DISH已PARK／CLOSE，也不登记RECAST或UAV验证进入。规范中的普通后继执行权不把本文的无后继变成一个未写出的科学任务。[问题 intake §7][question]；[AGENTS §§1–2、4–6][agents]。

因此实际科学后果只有：**维持DIRECT和两个具名窄停止；本轮零新科学调用；保留普通来源应用家族的未决状态，不选择更宽家族关闭。** 这是形成的范围决定，不是证据无法访问或尚未作出选择。

## 七、实际读取与交付边界

科学材料统一在 **c201e9eb5a71a4b0785a9104156d1dca6df2fbf9** 经连接GitHub读取。没有采用本对话附带的旧A02／A05请求、移动分支科学内容、外部镜像、本地克隆或清单外文件补齐本轮证据。下表C/为`docs/research/candidates/degraded_incumbent_shadow_handover/`，R/为`experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/`，P/为C/下`pro_packets/20260908_p62_post_b07_scope/`。

| 实际读取的允许路径 | 范围 |
| --- | --- |
| [C/DISH_POST_B07_DIRECTION_QUESTION_INTAKE_20260908.md][question] | 全文§§1–7及尾部；作为建议而非已经执行的范围决定 |
| [C/DISH_OWN_COMMAND_MEAN_B07_RESULT_INTAKE_20260908.md][intake] | 全文，分段补齐§§5–6；复用已接受事实 |
| [C/DISH_OWN_COMMAND_MEAN_B07_RESULT_EVIDENCE_20260908.md][evidence] | 全文§§1–5；没有递归读取未列的raw summary、checkpoint或receipt |
| [C/DISH_OWN_COMMAND_MEAN_B07_SCIENCE_CARD_20260908.md][card] | 75–245，完整相关§§4–5，并读相邻语义、曝光段 |
| [C/DIRECTION.md][direction] | 952–1035，最终P53选择及B07结果／窄停止段 |
| [C/DISH_CONTROL_LOW_LR_B05_RESULT_INTAKE_20260906.md][b05] | 105–180，两个LR实例、反例、普通训练换主与实际学习记录 |
| [C/DISH_P53_NATIVE_PROPOSAL_SOURCE_INTAKE_20260908.md][source] | 45–199及211–250，§§2–4、6与相邻工作说明；旧“拟议”时态作为历史读取 |
| [R/native/rbhr_r06_production_backend.cpp][native] | 433–497，为核对普通应用、投影顺序及独立服务谓词；未调用helper |
| [R/production_training_engine.py][engine] | 620–647，masked辅助loss到实际共享更新路径 |
| [P/EXPOSURE_AND_COST.json][cost] | 全文，历史实测／小计、零曝光和未分配的B尺度分开 |
| [P/LITERATURE_SCOPE.json][literature] | 全文检索记录；未另访问本地目录、论文或官方网页 |
| [P/ISSUE_SNAPSHOT.json][snapshot] | 读取单行JSON正文及历史评论，长输出另定位post-B06／P53评论及尾部状态；不以历史标题替代本题 |
| [docs/research/portfolio/handoffs/2026-09-08-p62-dish-post-b07-direction-choice.md][handoff] | 全文，含无候选分支、范围及零科学预算 |
| [docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md][method] | 35–112及365–末尾，含§§3–5.2、11.4、11.7–11.9 |
| [AGENTS.md][agents] | 1–426，完整相关§§1–2、4–6及相邻正文；不递归打开其引用 |
| [docs/project/ENGINEERING_SCOPE_SPEC.md][engineering] | 48–102，§§4–5及相邻说明；不采用旧对象专属例外 |

十六条允许科学路径均实际访问；范围读取不冒称全文或所有底层证据已重新审计。没有妨碍本次范围决定的访问缺口。文学术来源的设定判断按固定检索记录归属，未声称独立复查论文；数值按已接受E0、intake及机器记录归属，未执行新分析脚本。

在 **2026-09-08 22:38:03 UTC（15:38:03 PDT）之前**，本轮已实际读取可变[Issue4][issue]正文及最近的[P53交付评论][prior-comment]；当时显示九条历史评论，最近创建／更新时间2026-09-08T18:11:43Z。该时间是评论时间，不是本轮读取时刻。固定快照包含同一历史讨论，长行输出已定位相关尾部。写入前另查当前HEAD、目标文件及此后新评论；固定TASK允许在其科学基底的普通后继上仅新增本轮响应，分支推进不改变科学证据版本。[固定TASK授权段][task]。

本轮没有构造模型、执行项目代码／native helper、训练、评价、replay、profiling、测试或科学调用；没有修改card、DIRECTION、Portfolio、main或其他既有路径，也不重试受限scratch清理。零科学曝光不等于阅读、推理和交付的控制面时间为零。唯一写入范围是本文与一条含固定提交文件链接的交付评论；最终交付状态以新读取的实际分支HEAD、该提交上的本文和本轮Issue评论为准。

[question]: https://github.com/CartmanFatass/My-paper-code/blob/c201e9eb5a71a4b0785a9104156d1dca6df2fbf9/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_POST_B07_DIRECTION_QUESTION_INTAKE_20260908.md
[intake]: https://github.com/CartmanFatass/My-paper-code/blob/c201e9eb5a71a4b0785a9104156d1dca6df2fbf9/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_OWN_COMMAND_MEAN_B07_RESULT_INTAKE_20260908.md
[evidence]: https://github.com/CartmanFatass/My-paper-code/blob/c201e9eb5a71a4b0785a9104156d1dca6df2fbf9/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_OWN_COMMAND_MEAN_B07_RESULT_EVIDENCE_20260908.md
[card]: https://github.com/CartmanFatass/My-paper-code/blob/c201e9eb5a71a4b0785a9104156d1dca6df2fbf9/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_OWN_COMMAND_MEAN_B07_SCIENCE_CARD_20260908.md
[direction]: https://github.com/CartmanFatass/My-paper-code/blob/c201e9eb5a71a4b0785a9104156d1dca6df2fbf9/docs/research/candidates/degraded_incumbent_shadow_handover/DIRECTION.md#L952-L1035
[b05]: https://github.com/CartmanFatass/My-paper-code/blob/c201e9eb5a71a4b0785a9104156d1dca6df2fbf9/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_CONTROL_LOW_LR_B05_RESULT_INTAKE_20260906.md#L105-L180
[source]: https://github.com/CartmanFatass/My-paper-code/blob/c201e9eb5a71a4b0785a9104156d1dca6df2fbf9/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_P53_NATIVE_PROPOSAL_SOURCE_INTAKE_20260908.md
[native]: https://github.com/CartmanFatass/My-paper-code/blob/c201e9eb5a71a4b0785a9104156d1dca6df2fbf9/experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/native/rbhr_r06_production_backend.cpp#L433-L497
[engine]: https://github.com/CartmanFatass/My-paper-code/blob/c201e9eb5a71a4b0785a9104156d1dca6df2fbf9/experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_training_engine.py#L620-L647
[cost]: https://github.com/CartmanFatass/My-paper-code/blob/c201e9eb5a71a4b0785a9104156d1dca6df2fbf9/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260908_p62_post_b07_scope/EXPOSURE_AND_COST.json
[literature]: https://github.com/CartmanFatass/My-paper-code/blob/c201e9eb5a71a4b0785a9104156d1dca6df2fbf9/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260908_p62_post_b07_scope/LITERATURE_SCOPE.json
[snapshot]: https://github.com/CartmanFatass/My-paper-code/blob/c201e9eb5a71a4b0785a9104156d1dca6df2fbf9/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260908_p62_post_b07_scope/ISSUE_SNAPSHOT.json
[handoff]: https://github.com/CartmanFatass/My-paper-code/blob/c201e9eb5a71a4b0785a9104156d1dca6df2fbf9/docs/research/portfolio/handoffs/2026-09-08-p62-dish-post-b07-direction-choice.md
[method]: https://github.com/CartmanFatass/My-paper-code/blob/c201e9eb5a71a4b0785a9104156d1dca6df2fbf9/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[agents]: https://github.com/CartmanFatass/My-paper-code/blob/c201e9eb5a71a4b0785a9104156d1dca6df2fbf9/AGENTS.md
[engineering]: https://github.com/CartmanFatass/My-paper-code/blob/c201e9eb5a71a4b0785a9104156d1dca6df2fbf9/docs/project/ENGINEERING_SCOPE_SPEC.md
[task]: https://github.com/CartmanFatass/My-paper-code/blob/1b0ac54fb61485da73ac9290387f3f6cf30dc65c/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260908_p62_post_b07_scope/TASK.md
[issue]: https://github.com/CartmanFatass/My-paper-code/issues/4
[prior-comment]: https://github.com/CartmanFatass/My-paper-code/issues/4#issuecomment-5589714012
