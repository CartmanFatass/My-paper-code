**ACVC CONTINUE，保持 MEDIUM、recasts2 和现有席位。下一目标选择一项六个全新训练—评价程序的固定1024配方研究，前瞻按单任务、假设限定的 C-BENCH 问题设计；不 PARK、不 RECAST、不 CLOSE。** 理由是：配对暴露研究已经显示 F 的增量随本程序继续学习而缩小，却没有消失；对已经变得更有用的 own-dwell，后期 F 仍有实际均值增量。现在值得购买的不是又一个暴露切点，而是同一配方在新学得 proposer 上的期望增量及其不确定性。六个程序是本次选择的有限投入，不是充分性、正态性或成功概率定理。当前已完成结果仍各属其原来的 B 范围；本答复不把尚未冻结、执行的新研究写成已取得的 C 结论。[当前报告][report]；[配对结果及限制][paired-e0]。

## 一、从重开到配对结果：假说得到支持，也被收窄

原 Portfolio 重开 ACVC，是为了研究固定 F 在新学得策略上的用途，而不仅保留旧终点参考；它没有承诺稳定优势，也没有要求每完成一项就自动追加。原 DM 已真正执行 B03、longer-C 和 paired-exposure，并完整回应审查，不能将这段工作描述为再次进入后只整理文档。原 PARK 接受训练间不确定性、保留有限参考的理由仍可辩护；本次需在新增证据上重新比较投入。[完整重开决定][reopen]；[实际应用][application]；[历史 PARK][park]。

下表保留五个不同聚集场景学习程序的六个限定终点，而不是将它们合成确认研究：

| 学习程序／终点 | F−C，J | F−own-dwell，J | 两项比较的不利世界 |
| --- | ---: | ---: | --- |
| K/B01，512训练 | +0.1240730245 | +0.0767409650 | 1/64；8/64 |
| B02，512训练 | +0.1045935590 | +0.0607090077 | 4/64；11/64 |
| B03，512训练 | +0.1436987981 | +0.1178477937 | 6/64；5/64 |
| longer-C，1024训练 | +0.1292634628 | +0.0635578296 | 1/64；15/64 |
| paired，同一程序512快照 | +0.1405118427 | +0.1191862743 | 5/64；7/64 |
| paired，同一程序1024快照 | +0.1132431734 | +0.0687279633 | 9/64；10/64 |

各原主量分别保持严格大于0.01 J的 UP 读法。三个旧512程序的绝对成绩并不一致；尤其 B03 较大的差值伴随较低的 C/dwell 回报，而 F 几乎等于 B02。因此不能把差值增大解释为 F 本身改进。longer-C 与旧程序改变了训练和评价随机根，也不能单靠历史减法识别训练时长效果。[K][k-e0]；[B02][b02-e0]；[B03 E0][b03-e0]；[B03审查回应][b03-intake]；[longer-C E0][long-e0]。

配对对象更进一步：一个新程序真正完成1024训练回合、2048次更新，保存两个事先指定快照，全部学习结束后才运行六个私有评价面板。其指定主量为逐世界计算的

\[
G_{\mathrm{dwell}}=\overline{(F_{1024}-D_{1024})-(F_{512}-D_{512})}
=-0.050458310943283916\ J,
\]

原规则为 DECREASE；辅助的 G_C 为 −0.02726866928374775 J。直接变化保留了同世界和同程序的协方差，不能用独立标准误相加替代。四个终点 UP 与增量 DECREASE 并存，没有统计或逻辑矛盾。[配对 E0，终点与变化][paired-e0]。

绝对 C/F/dwell 从512快照的0.0835366160/0.2240484587/0.1048621844，变为1024快照的0.2110828649/0.3243260383/0.2555980750 J：三者都更好，参照改善更快。较大早期增量不等于早期 F 更好；这个程序的 C 后期成绩更强，不证明普遍胜任、单调学习、已收敛，或单独由新增数据而非优化曝光造成。两个相关快照仍只是一条学习程序，64个世界不是64次训练。[完整配对审查][paired-review]。

**最强支持是后期 F 仍超过有用的 dwell，而最强反证是其损害尾部。** 后期 F−dwell 有10/64不利世界，最差 −0.2238660859 J；F−C有9/64不利，dwell−C本身也有20/64不利。F/dwell干预数从6286/2952变为6422/4724，来自各自不同的轨迹、循环反馈和队友响应，不是匹配剂量。不能归因于纯 retrace、历史必要性或抑制动作；这些频率和最小值也不是新策略的校准风险估计。没有预定服务—尾部损失准则，本次不追溯添加安全阈值或把 F 升为通用默认。[配对 E0][paired-e0]；[完整审查与 DM 回应][paired-intake]。

假说由“F是否在又一个新终点有用途”推进到：**在明确的1024训练配方及聚集场景抽样法则下，F相对原C和own-dwell的期望完整程序增量，是否各超过0.01 J。** 这是性能问题，不是学习门控的新胜利。固定 F 的运行状态随历史变化，不等于其参数在评价中学习；两次 train-F/common-F 比较的 −0.0260962125、−0.0573421958 J、学习门控低于 F、以及 uncertain/delayed 家族的停止全部保留。[方向综合][direction]；[训练使用负结果][train-f]。

## 二、为什么选六个固定配方程序，而不是较小 B 或 PARK

**最强 PARK 方案**是保留这些已经有用但有限的执行参考，不再为更广的未来策略判断投入。反方很具体：损害尾部相当大，增量会随训练改变；即使新研究得到均值支持，也未必足以决定实际默认使用，更不能解决组件原因。完整支持和维护成本未知；六次拟合仍可能只得到假设限定或不确定的结论。我接受这些限制，不把累计正均值当作继续权利，也不声称已算出正的净信息价值。

我仍偏向这一次有限继续，关键是**开发问题已经稳定到可抽样的一套完整配方**。先前较低 C/dwell 成绩留下了“F是否主要利用较弱 proposer”的具体疑问；longer-C取得后期用途观察，配对研究又在同一程序 C/dwell 明显改善时观察到衰减后的正增量。这不排除未来反转，但使“只在弱终点偶然有益”的解释不再覆盖全部已见事实。把下一投入转向固定配方下的新完整程序，比继续加训练切点或寻找更大的差值更能改变是否维护这条可选 F 路径的判断。[longer-C完整审查][long-review]；[配对完整审查][paired-review]。

**一或两个新 B 程序仍是可信的较低成本备选。** 一个失败、交叉或有用终点可以改变开发建议，根本不需要先“解决总体不确定性”。最新审查对此的纠正我接受，不能拿证据等级否定小 B。选择六个的区别，是现在愿意为一个共同前瞻抽样与分析计划多支付若干完整程序，获得同配方单位之间的分布信息，而不是在每个新终点之后再决定是否继续采样。这样直接服务于本轮所问的期望增量，也限制事后改变样本停止位置的空间；不保证样本足够精确或没有选择历史。[配对 DM 回应][paired-intake]。

六不是最优样本数或通用下限。相对于两个程序，多四个程序的原生参考工作约为4×296.30=1185.20秒，尚未包含完整支持；我在已存在可复用学习路径、后期双对照增量仍有实际尺度、并且不增加中途面板或搜索的条件下，选择支付这一额外信息成本。若只需要一个新反例，小 B更省；若只需要保存旧资产，PARK更省。本次选择研究固定配方未来用途，才使这笔额外工作有具体目的。没有新用户、阳性pilot或原因诊断的前置要求。

不再选择另一条512/1024配对程序，因为当前目标不是继续估计暴露变化；固定1024并不代表它已经最优，而是选择在已见更强参照仍不能消除 F 增量的曝光处评估未来表现。不在新数据出来后转回差值较大的512终点。不存在新增尾部控制器、超参数搜索或已停止门控家族的自动重开。

## 三、唯一下一目标、统计含义与有限工作

原 Astra/max DM继续现有 `codex/acvc` 作者工作区，设计并执行**六个全新、前瞻抽样的1024回合 C-only 学习程序**。每个程序只取唯一最终checkpoint，分别在 C、固定F、own-predicate dwell下作64世界的私有评价。保持聚集五UAV/五十用户/H256、合法信息、私有GRU64、训练专用critic、原奖励和CPU FP32/thread1学习语义。评价沿各包自己的历史、实际动作和循环状态演化；共同外生世界不强迫触发、干预次数或轨迹相同。C是策略标签，不是证据等级。[当前报告，有限候选][report]。

设 r 为新完整学习—评价程序，Q∈{C,D}，

\[
D_{r,Q}=\frac1{64}\sum_{w=1}^{64}(J_{r,F,w}-J_{r,Q,w}),\qquad
\widehat\mu_Q=\frac1{6}\sum_{r=1}^{6}D_{r,Q}.
\]

目标是所声明训练及评价抽样法则下的两个期望 \(\mu_C,\mu_D\)，而非纯训练方差。每个完整fit及有限面板是一个抽样单位，单位等权；评价噪声已进入单位间变异，不从中扣掉或再重复加一次。两项对比共享F，联合表述不能以独立性相乘。保留每单位两项差、绝对C/F/dwell、全部不利世界和学习记录。

**本答复选择研究投入，不冒称新 C 卡、抽样法则或统计方法已冻结。** DM须在新问题相关结果出现前完成既有C所需的配方、抽样单位、随机流/面板、固定数目及停止、缺失处理、不确定性假设和双主量联合读法。使用常规统计工具和最少适用分析即可；不新增正态性pilot、功效仿真或校准服务作为启动前提。若使用小样本参数工作模型，其覆盖只能条件于该模型；六个观测或全为正不能验证神经训练分布。旧均匀C01的五-fit t区间只有其iid-normal工作模型下的资格，不能照搬为新聚集任务的校准证书。[C01最终推断][c01]；[实证规范§§11.8—11.9][spec]。

现有K/B02/B03、longer-C及配对两个快照均作为开发历史，不进入新六程序的确认样本，也不用于挑选未来最佳seed或checkpoint。前瞻新卡可以明确本次设计受旧结果启发；无需假装动机与结果无关。不存在自动第七fit、丢弃弱策略或因区间跨越边界而继续补样本。真实故障按依赖与前瞻规则保留，不把缺失程序编码为零、负值，或只分析成功子集却声称完成原目标。后续必要修复遵守既有规则，不借行政closeout扩展科学对象。

结果对开发的含义如下：双期望增量获得所声明模型和联合读法下的支持，将加强该固定配方的有限可选用途依据，但不自动成为部署默认；仅胜C而不能支持胜own-dwell，则复杂F的额外价值仍未确立；点估计有利而精度不足，可完整结束研究并报告不确定，不等于失败或等价；有实质负面证据则削弱相应用途，保留历史正观察并重新比较维护、修改与PARK。任何分支都不自动产生下一实验或方向结局。均值问题仍不能认证尾部可接受性，风险敏感用途须有另行前瞻定义的问题，不能追溯发明阈值。

| 工作 | 单个程序 | 六程序合计 |
| --- | ---: | ---: |
| 训练／最终评价回合 | 1024／192 | 6144／1152 |
| Adam／backward更新 | 2048 | 12288 |
| 训练／评价ticks | 262144／49152 | 1572864／294912 |
| 总ticks | 311296 | **1867776** |
| 最终checkpoint／私有加载 | 1／3 | 6／18 |

总7296回合；不训练共享前缀两次，不保留512中途评价，不加初始回报面板、候选搜索或嵌套控制器/轨迹调用。新增跨程序推断所需的是这些真实学习单位，不是把评价世界放大成独立样本。[报告计数][report]。

## 四、资源、同伴机会与应用

单个final-only1024程序的296.30秒，给六程序原生墙时之和提供 **1777.8秒参考**；不是未来报价、线性加速律或study elapsed保证。候选native3000秒/support4800秒仍是可前瞻修订的DM计划，不是owner硬cap或已核算余额。配对对象的324.92秒是完整native链，不是内部311.58秒或收集观察时长。已列五个cluster开发程序的1114.44秒、3584训练/1152评价/7168更新/1212416ticks只是一组资源合计，不是统计池，也不是整个方向的CPU、支持或生命周期成本。[报告成本][report]；[配对E0][paired-e0]。

全部历史支持/provider/agent、未来工程及维护尾项继续UNKNOWN，不清零、不由未测推定耗尽。support600s、普通wall和watchdog允许估计误差，不是Send、启动、升级或PARK门槛。每个实际调用仍须遵守既有远端路线、相邻物理/有效可用内存4GiB准入、真实owner/platform限制及冻结科学终点；不得挪用同伴承诺或新增付费容量。已被策略拒绝的creator-owned scratch清理不能另换删除者或整树删除绕过，也不构成科学停止理由。[运行规范§1][runtime]；[longer-C故障及回应][long-intake]。

全局固定快照中，MGTAP已应用固定1e-4新配对目标，尚未发布后继卡/seed/native；FOLR的唯一A−G目标已落实，G于15:36:55 UTC接受运行并由同批Monitor重新接管，A仍选定而未启动，尚无新最终比较。不能用其历史B03终态冒充新G已经结束，也不等待它完成来审批ACVC。[MGTAP应用][mgtap]；[FOLR唯一决定应用][folr]；[实际执行][folr-execution]。

这两条工作与ACVC有不同问题和成本；本次不把不同宿主的回报或更新数作数值排名。机会成本真实存在：六程序延后了仅保存参考或将ACVC席位用于别处的可能性。我仍选择在现有席位支付一次固定配方研究，而不重排同伴或预选替代。派生Portfolio报告仍有配对审查“待回”的旧列，以完整审查和最新DM回应校正；这不是新的缺口。[全局报告][global]；[登记表][registry]。

原DM读入全文、回应实质问题并应用CONTINUE后，直接推进前瞻设计、相称的工程接受、实际运行、保全和完整科学回应。需要的C设计严谨性是所选期望主张的证据负担，不是每次拟合的Portfolio许可；无需Root再次批准，也不要求复问已经完成的审查。保持MEDIUM/recasts2、旧失败家族和C01已消费状态。若研究条件发生实质冲突或日后需方向处置，以实际证据重新报告；不因本次选择六个程序获得无限后续配额。[当前协议][protocol]；[同伴规则][peers]。

## 五、实际来源访问与结论上限

本轮通过GitHub读取TASK列出的全部29项材料之指定范围；完整性要求为全文的报告、结果、审查及回应均实际读取，长返回截断处作重叠分段补齐。没有决策关键正文缺失。下列链接均保留对应固定版本和路径，所列范围是本轮访问，而不是从题名推断内容：

| 材料组 | 实际访问范围 |
| --- | --- |
| 当前ACVC综合 | [报告][report]全文；[DIRECTION][direction]当前综合与保留边界；[PARK][park]全文 |
| 最新配对研究 | [E0][paired-e0]全文；[73行独立审查][paired-review]全文至EOF；[intake及完整DM回应][paired-intake]全文 |
| 暴露改变及过程 | [longer-C E0][long-e0]、[intake][long-intake]、[71行独立审查][long-review]全文；[B03 E0][b03-e0]和[完整intake/回应][b03-intake] |
| 有利、不利及资格历史 | [K E0][k-e0]、[B02 E0][b02-e0]、[C01完整intake含最终资格][c01]、[训练-F B02完整intake][train-f] |
| 重开与全局 | [完整先前裁决][reopen]和[完整应用回应][application]；[全局报告][global]全文；[registry][registry]相关三占位及Portfolio/协调字段；[MGTAP intake][mgtap]、[FOLR intake][folr]及[EXECUTION][folr-execution]的当前决定/工作范围 |
| 当前控制和方法 | [AGENTS][agents]§§1—6；[协议][protocol]与[peer规则][peers]全文；[实证规范][spec]§§7—8、11.4、11.7—11.10；[FOUNDATIONS][foundations]§6；[实证专题][empirical]前三节；[runtime][runtime]§1 |

主要科学文件固定于07b848fadd57ed50af3632dbd60655f45ea666ab，方法/全局固定于1fabe79ebbf826138801b7e096278c2edda5d58a；两份独立审查分别使用其清单指定的68fed46f448312827f38b4b4f9bade36e2aedc35和fcd806cb2b1f99158540d8f7d1123a9df249b214。除此仅为本任务交付核对目标分支、文件及Issue状态，没有用移动分支重写科学快照。

我没有运行代码、读取模型二进制、重算原始逐回合数组或审计清单外helper。原生行、checkpoint、协方差验证和故障处理归属于已读的DM执行记录及独立审查，不是本轮新产生的第二次证据。基础知识在本决定中实际区分了训练程序、相关快照与评价世界，以及固定执行包和组件因果；没有产生seed配额、阳性pilot、最优上界或校准先行门槛。[基础§6][foundations]；[实证专题][empirical]。

**最终选择仍为ACVC CONTINUE：做一次前瞻六程序、固定1024、最终C/F/own-dwell的有限期望增量研究。当前结果不升级，未来结论随实际抽样、假设、精度与损害记录而限定。** 本次交付只形成这项方向决定及其完整理由；没有冻结新C卡、改写代码/证据/registry或启动研究，也不改变其他两席。

[report]: https://github.com/CartmanFatass/My-paper-code/blob/07b848fadd57ed50af3632dbd60655f45ea666ab/docs/research/candidates/acvc/ACVC_POST_PAIRED_DIRECTION_REPORT_20260914.md
[direction]: https://github.com/CartmanFatass/My-paper-code/blob/07b848fadd57ed50af3632dbd60655f45ea666ab/docs/research/candidates/acvc/DIRECTION.md
[park]: https://github.com/CartmanFatass/My-paper-code/blob/07b848fadd57ed50af3632dbd60655f45ea666ab/docs/research/candidates/acvc/PARK.md
[paired-intake]: https://github.com/CartmanFatass/My-paper-code/blob/07b848fadd57ed50af3632dbd60655f45ea666ab/docs/research/candidates/acvc/ACVC_CLUSTER_PAIRED_EXPOSURE_B01_INTAKE_20260914.md
[paired-e0]: https://github.com/CartmanFatass/My-paper-code/blob/07b848fadd57ed50af3632dbd60655f45ea666ab/docs/research/candidates/acvc/ACVC_CLUSTER_PAIRED_EXPOSURE_B01_RESULT_EVIDENCE_20260914.md
[paired-review]: https://github.com/CartmanFatass/My-paper-code/blob/68fed46f448312827f38b4b4f9bade36e2aedc35/docs/research/candidates/acvc/pro_packets/20260914_cluster_paired_exposure_b01_scientific_review/archive/RESPONSE.md
[long-intake]: https://github.com/CartmanFatass/My-paper-code/blob/07b848fadd57ed50af3632dbd60655f45ea666ab/docs/research/candidates/acvc/ACVC_CLUSTER_LONGER_C_B01_INTAKE_20260914.md
[long-e0]: https://github.com/CartmanFatass/My-paper-code/blob/07b848fadd57ed50af3632dbd60655f45ea666ab/docs/research/candidates/acvc/ACVC_CLUSTER_LONGER_C_B01_RESULT_EVIDENCE_20260914.md
[long-review]: https://github.com/CartmanFatass/My-paper-code/blob/fcd806cb2b1f99158540d8f7d1123a9df249b214/docs/research/candidates/acvc/pro_packets/20260914_cluster_longer_c_b01_scientific_review/archive/RESPONSE.md
[b03-intake]: https://github.com/CartmanFatass/My-paper-code/blob/07b848fadd57ed50af3632dbd60655f45ea666ab/docs/research/candidates/acvc/ACVC_CLUSTER_DEPLOYMENT_B03_INTAKE_20260914.md
[b03-e0]: https://github.com/CartmanFatass/My-paper-code/blob/07b848fadd57ed50af3632dbd60655f45ea666ab/docs/research/candidates/acvc/ACVC_CLUSTER_DEPLOYMENT_B03_RESULT_EVIDENCE_20260914.md
[b02-e0]: https://github.com/CartmanFatass/My-paper-code/blob/07b848fadd57ed50af3632dbd60655f45ea666ab/docs/research/candidates/acvc/ACVC_CLUSTER_DEPLOYMENT_B02_RESULT_EVIDENCE_20260913.md
[k-e0]: https://github.com/CartmanFatass/My-paper-code/blob/07b848fadd57ed50af3632dbd60655f45ea666ab/docs/research/candidates/acvc/ACVC_CLUSTER_DEPLOYMENT_B01_RESULT_EVIDENCE_20260912.md
[c01]: https://github.com/CartmanFatass/My-paper-code/blob/07b848fadd57ed50af3632dbd60655f45ea666ab/docs/research/candidates/acvc/ACVC_FRESH_DENSE_PACKAGE_C01_INTAKE_20260911.md
[train-f]: https://github.com/CartmanFatass/My-paper-code/blob/07b848fadd57ed50af3632dbd60655f45ea666ab/docs/research/candidates/acvc/ACVC_FIXED_F_TRAINING_USE_B02_INTAKE_20260912.md
[reopen]: https://github.com/CartmanFatass/My-paper-code/blob/1fabe79ebbf826138801b7e096278c2edda5d58a/docs/research/portfolio/pro_packets/20260914_rcle_park_vacancy_selection/archive/RESPONSE.md
[application]: https://github.com/CartmanFatass/My-paper-code/blob/1fabe79ebbf826138801b7e096278c2edda5d58a/docs/research/portfolio/pro_packets/20260914_rcle_park_vacancy_selection/INTAKE.md
[global]: https://github.com/CartmanFatass/My-paper-code/blob/1fabe79ebbf826138801b7e096278c2edda5d58a/docs/research/portfolio/PORTFOLIO.md
[registry]: https://github.com/CartmanFatass/My-paper-code/blob/1fabe79ebbf826138801b7e096278c2edda5d58a/.codex/hmasd-dm-sessions.toml
[mgtap]: https://github.com/CartmanFatass/My-paper-code/blob/1fabe79ebbf826138801b7e096278c2edda5d58a/docs/research/candidates/metric_ground_transport_allocation/pro_packets/20260914_lr_selection_portfolio_direction/INTAKE.md
[folr]: https://github.com/CartmanFatass/My-paper-code/blob/1fabe79ebbf826138801b7e096278c2edda5d58a/docs/research/candidates/vap_folr_core/pro_packets/20260914_post_b03_portfolio_direction/INTAKE.md
[folr-execution]: https://github.com/CartmanFatass/My-paper-code/blob/1fabe79ebbf826138801b7e096278c2edda5d58a/docs/research/candidates/vap_folr_core/entity_history_augmentation_b01_781601/EXECUTION.md
[agents]: https://github.com/CartmanFatass/My-paper-code/blob/1fabe79ebbf826138801b7e096278c2edda5d58a/AGENTS.md
[protocol]: https://github.com/CartmanFatass/My-paper-code/blob/1fabe79ebbf826138801b7e096278c2edda5d58a/docs/project/PORTFOLIO_DECISION_PROTOCOL.md
[peers]: https://github.com/CartmanFatass/My-paper-code/blob/1fabe79ebbf826138801b7e096278c2edda5d58a/docs/project/PEER_DM_COORDINATION.md
[spec]: https://github.com/CartmanFatass/My-paper-code/blob/1fabe79ebbf826138801b7e096278c2edda5d58a/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[foundations]: https://github.com/CartmanFatass/My-paper-code/blob/1fabe79ebbf826138801b7e096278c2edda5d58a/docs/rl-marl-foundations-20260907/FOUNDATIONS.md
[empirical]: https://github.com/CartmanFatass/My-paper-code/blob/1fabe79ebbf826138801b7e096278c2edda5d58a/docs/rl-marl-foundations-20260907/topic-notes/04_EMPIRICAL.md
[runtime]: https://github.com/CartmanFatass/My-paper-code/blob/1fabe79ebbf826138801b7e096278c2edda5d58a/docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md
