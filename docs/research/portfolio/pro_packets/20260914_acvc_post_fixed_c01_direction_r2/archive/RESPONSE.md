**ACVC CONTINUE，保持 MEDIUM、recasts2 和现有席位；下一目标选择一个全新的4096回合 C-only 学习程序，前瞻固定1024／4096两个快照，并在全部学习结束后完成各自的 C／F／own-dwell 评价。当前不采纳可逆 PARK 建议，不 RECAST、不 CLOSE，也不追加或重跑已消费的六程序 C01。**

理由是：六程序研究已经支持固定1024配方下、工作模型限定的期望增量；先前配对研究又真实观察到，参照继续学习时 F 的增量减小但未消失。现在值得购买的是这条已具有限用途的执行路径在更大训练曝光下是否仍有开发价值，而不是继续证明原 C01 合格。一次新的配对 B 能使后期消失、反转或仍有用的增量影响其使用范围；这份信息在本次判断中值得额外工作，但没有被量化为正的净信息价值。[当前报告][report]；[完整实际结果审查][review]。

## 一、已完成的结果：支持成立，范围没有自动扩大

六个首次抽取的原始程序全部完成。每个程序真实训练 C 策略1024回合、更新2048次，随后由 C、F、own-dwell 私有加载同一个最终模型，各评价64个世界。F 和 dwell 是执行包，不是另行拟合的策略；评价期间循环状态及历史变化不等于参数学习。原来的两个主量得到：

| 主量 | 六个完整fit-panel单位的均值 J | 冻结区间 J |
| --- | ---: | --- |
| F−C | +0.096377354920 | [0.074826981257, 0.117927728584] |
| F−own-dwell | +0.064088940259 | [0.035375804426, 0.092802076092] |

两个未舍入下界均严格超过0.01 J，故保留 **JOINT_ABOVE_MEI**，该有效完整 C01 已消费。抽样是前瞻 M=10000…19999、Q=20000…29999 的独立均匀有放回抽取，经固定学习与评价映射形成六个单位；首次十二次抽取均保留，没有筛选或替换。不同seed标签本身不是独立性依据，重复标签若出现也不会被删除。[科学卡 §§2—5][card]；[实际首次抽样][draw]；[完整E0][e0]。

推断单位是一次完整拟合及其有限面板，不是384个评价世界。冻结方法使用单位标准差、SE=s/√6和t(.9875,5)=3.1633814497486235；两个97.5%双侧边际区间的至少95%同时覆盖，只在声明的iid-normal完整fit-panel均值模型下成立。共享F导致的相关性不破坏Bonferroni构造，但六个有利均值和正确算术不能验证神经训练分布的校准。评价噪声已经进入单位间变异，不另加或扣除；这些是均值区间，不是未来单个策略的预测区间。没有新校准、normality pilot或替代区间是保留本结果的前提。[主量记录][analysis]；[完整审查及DM回应][review-intake]。

有用的简单控制和不利尾部同样进入判断。绝对 C/F/dwell 均值为0.120916419617／0.217293774537／0.153204834278 J，dwell−C描述性增量为0.032288414661 J。F因此不只是胜过原动作，也超过一个确有帮助的own-dwell包。然而 F−C有30/384个不利世界、最差−0.144286152878 J；F−dwell有56/384、最差−0.149130332897 J；dwell自身对C也有84/384个损失。这些嵌套计数不支持独立世界二项风险推断，不能认证F或dwell安全，亦不自动支持默认部署。[E0，各单位及全部尾部][e0]。

C的六个绝对均值介于0.063243095491与0.165554704375之间。更新、位移和训练曲线不证明调优充分、胜任或收敛；低于另一次已观察终点也不独自诊断欠训练。F与dwell各自触发、轨迹、循环反馈及队友反应不同，干预数是后果而非匹配剂量。固定F的收益仍是完整包效应，不隔离retrace、历史必要性或触发机制。[review，Useful controls and surviving contrary evidence][review]。

## 二、从原重开理由到现在的假说更新

原重开决定希望研究固定F在新学得proposer上的用途，而不是只存放两个旧终点。B03、longer-C、配对暴露和六程序C01都已经实际执行并完成科学回应；前次CONTINUE没有落成文档空转。随后选择六程序，是把开发问题固定到一套配方，对跨新完整程序的期望增量取得相称证据。现在这项特定问题已经在其声明限定内得到回答，不能继续把它写成“尚缺首个总体观察”，也不能把完成C本身当作方向停止理由。[原重开全文][reopen]；[前次135行裁决][previous]；[完整应用回应][previous-intake]。

先前同一程序的512／1024配对有重要区别于历史跨seed减法的信息：绝对C从0.0835366160增至0.2110828649 J，F和dwell也提高；F−dwell却从0.1191862743降至0.0687279633 J，指定变化为−0.050458310943 J。即参照改善更快、增量衰减，但后期F仍有用。协方差由直接逐世界变化保留；两个快照是一条学习程序，不是两次独立拟合。这支持研究曝光敏感性，却不能预言4096会继续衰减、越过零或使C必然更强。[完整配对E0][paired-e0]；[配对审查与回应][paired-intake]。

本次发展的假说因此是：**固定F的增量可能不仅存在于已确认的有限1024配方中，也可能在同法则更多学习所实际达到的策略上仍值得维护；相反，若更充分训练后的C或own-dwell已经足够，F的扩展用途会受限。** 这是使用范围的有限学习问题，不是C01的修复或组件原因诊断。一个程序只能给出局部答案；即使训练四倍，也不保证达到调优上限。

原均匀场景五fit C01保持其不同人口与正态工作模型限定，不能与新聚集C混池。学习门控低于固定F、两次train-F/common-F的−0.026096212471与−0.057342195754 J、已停止的uncertain/delayed家族和全部不利世界保持。新对象只继续train-C／执行F用途，不借正结果重开这些失败包或清零recast历史。[方向综合][direction]；[旧均匀C01][uniform]；[训练使用负结果][train-f]。

## 三、为何不同意本次PARK偏好

**最强PARK方案**是接受当前已取得的有限配方知识，保留固定F作为可选研究参考，暂不扩大到更长学习。它有三个实质理由：现有参考已经有资格明确保存；4096是另一个曝光区间、可能仍未产生更强proposer；额外训练、工程与完整结果解释有真实机会成本，即使均值继续有利也不能解决尾部接受性或机制问题。DM并未否认新B有价值，Reviewer也没有给出停止定理。我接受这份反方的科学合理性，不把PARK建议误报为结果无效、权限不足或仅仅“对象做完”。[完整报告的取舍][report]；[全部审查回应][review-intake]。

我仍选择继续，关键在于**是否愿意研究超出1024配方的F维护价值**。我现在愿意购买这一有边界的扩展，因为：

**参照学习敏感性已有直接观察，而不是只剩可随意增加的超参数。** 同程序的真实改善及增量衰减使更长训练成为与F用途直接相关的检验。六程序的有利结果说明该路径不只是一个选中的偶然端点，但没有回答更多学习后还是否需要它。这个问题不要求先证明C欠训练，也不把欠缺tuned headroom变成门槛。

**不同结果会改变实际开发动作。** 在更强的实际参照旁仍有用，会支持把可选F继续带入更高曝光研究；后期对C不利，或不能再超过有用dwell，会限制这种扩展，而不撤销1024结论。若C没有改善，所得结果仍能描述更长配方，但对“更强策略下是否需要F”的解释更弱；这一风险必须接受，不筛掉弱fit，也不自动加长至8192来寻找预期情形。

**两快照的一次真实训练是这个问题的相称成本。** 它不需要重新训练共享前缀、搜索控制器或购买一套4096总体研究。沿用现有配对逻辑，额外的1024面板服务于同程序变化，避免再次用旧C01与新终点相减来推断曝光效果。它比同配方再加一个fit更贵，但获得的是后一设计不能提供的变化信息，而非更高证据等级的标签。

我的排序是定性、close-call的，没有预测获益概率、净价值优势或证明所有其他用途都较差。它既不要求六个正结果才能开展B，也不因为本次成功就授予无限续跑。报告与审查倾向先整理方向判断并非生命周期否决；完整审查提出的新B反方案和其所有限定已经进入这次决定，而不是只引用它有利的一句。[review，Report versus the strongest further experiment][review]。

较小的同1024配方新B仍可发现交叉或改变精度判断，不能因只有一两次fit而被否定。但本轮两个期望差在原资格下已获支持，没有一个当前需要通过同配方加样本解决的具体边界争议；我不选择它作为默认第七次观察。风险敏感研究、调优或机制控制也可能有价值，但本次没有选中对应损失函数或因果问题，不追加为资格前提。[实证规范 §§11.8—11.9][spec]。

## 四、唯一下一DM目标、测量与有限后果

原Astra/max DM在现有ACVC方向内推进**一个新C-only4096回合B/EXPLORE程序**，在完成1024及4096训练回合所对应更新后分别保留快照。两快照都保留；全部学习结束后，才对两者分别执行C/F/own-dwell三个私有64世界面板。继续学习不从另一个加载实例重启；评价不反馈训练，不训练F或dwell。保持聚集五UAV／五十用户／H256、合法信息、私有GRU64、训练专用critic、原奖励J=S/256及CPU FP32/thread1的学习语义。

新随机身份、源码、卡和命令由DM前瞻定义，没有在此虚构已冻结对象。它不是延长任何C01原始fit，不继承六个旧模型的状态，也不是换名重跑seed。common外生评价地址只匹配所声明随机条件，不强制三包轨迹、触发次数或hidden state相同。

新对象分别记录各终点的

\[
\Delta_Q(h)=\frac1{64}\sum_w[J_{F,h,w}-J_{Q,h,w}],\quad Q\in\{C,D\},\ h\in\{1024,4096\},
\]

以及直接逐世界计算的变化 \(G_Q=\overline{(F_{4096}-Q_{4096})-(F_{1024}-Q_{1024})}\)。F−own-dwell是较强的增量对照；F−C、绝对C/F/dwell和全部不利世界也完整保留。端点是否有用与增量是否衰减分开解释，沿用该问题的局部0.01 J尺度时前瞻写明严格/含边界含义；不把C01的联合t区间规则搬到一条学习程序。

条件变化不确定性保留快照及同世界协方差，不能把两个SE当作独立后相加。两个终点不是两次训练，共享F的两对照也不是独立证据。完整的更长程序若出现有用后期增量，只新增该程序的B观察；若均值尺度内，不推等价；若反转，限制相应用途而不抹掉已完成C；若必需端点受损，不用成功子集或旧面板拼补其比较。真实失败按依赖处理，保留窄事实和实际曝光。[配对方法及局限][paired-review]；[FOUNDATIONS §6][foundations]。

| 下一对象工作 | 有限数量 |
| --- | ---: |
| 新训练程序／训练回合 | 1／4096 |
| 两回合rollout／Adam-backward | 2048／8192 |
| 快照／私有评价加载 | 2／6 |
| 最终评价回合 | 384 |
| 训练／评价ticks | 1048576／98304 |
| 合计回合／team ticks | **4480／1146880** |

该选择不包含调参、选择最佳快照、复制共享前缀、额外初始面板、轨迹搜索或自动下一fit。四倍终点是本次有实质曝光差的有限提案，不是最优预算定理。新结果即使仍有疑问也可以完整结束，不形成“必须一直训练到C更强”的过程。[当前报告的具体反方案][report]。

当前C01维持假设限定的期望主张；下一对象维持局部B主张，不自动升级到4096总体结论。两者均不提供默认部署、安全、纯数据或优化因果、retrace/历史组件原因、调优余量、迁移或正式UAV证据。未来若实际决策变成损害尾部是否可接受，需要对应的前瞻问题，不追溯发明本轮安全阈值。

## 五、资源、同伴机会与实际应用

单个同1024配方B可沿用1216回合／311296ticks／2048更新结构；相比之下，所选配对B是真实的额外训练投入，不因“只有一个fit”就很小。报告的1185.2秒是4×旧final-only296.30秒的粗略native参考，包含不同训练／评价比例，不能当作测得的新耗时、线性规律或总成本保证。新工程、检查、观察、审查和维护仍有UNKNOWN；不先做profiling或历史成本普查来消除未知。

已完成C01的native墙时1733.09秒、aggregateCPU1732.73秒、maxRSS556932KiB，区别于3054.763358秒dispatch至观察终态。8.513秒测试墙时只是支持子集。五项早期cluster程序加六个C01的已知native合计2847.53秒，是费用子集而非统计池或生命周期总账；历史支持/provider/agent成本不清零、不伪称全部合规。[E0及完整执行记录][e0]；[实际执行事实][execution]。

support600秒、旧500/unit及3000native/4800support规划、普通watchdog和报告closeout计划，都不构成停止、Send或新启动门槛，也不是现成剩余额度。DM前瞻制定和修订所选有限工作的普通计划，保持真实owner/platform约束与新冻结的科学终点；实际watchdog若终止就记录终止，不能伪装为连续原运行。每次真实调用保留既有remote-first路线、相邻物理及有效可用内存4GiB准入，不增加付费容量或改变同伴承诺。[runtime §1][runtime]；[AGENTS §§1—6][agents]。

固定全局快照中MGTAP已应用固定1e-4新配对目标，尚未绑定新卡/调用；FOLR的唯一A−G比较已经落实，G完成均值−0.966484375、native1178.68秒，原增强A于19:39:55 UTC接受并由同批Monitor接管，尚无A−G结果。13401.737549秒臂间控制延迟不是G计算时间，也不是全部测得的active support。不能因G单臂结果或旧B03终态改变该已接受工作。[实际同伴交接][peer-context]；[FOLR当前执行][folr-execution]。

ACVC继续占用现有一席，与MGTAP的有限配置重复和FOLR的新完整程序比较竞争研究注意力及共同资源；没有量化跨方向收益排序。本次愿意为明确的更长训练用途问题投入，而不是因为某方向已获C标签就优先。保持三占用、零预留、零空缺，不选择替代方向、不重开RCLE，也不把同伴暂未启动误算为空位。[全局报告][global]；[固定登记][registry]。

原DM读入全文、回应这一与其PARK建议不同的价值判断，并推进新B的前瞻定义、相称工程接受、执行保全和完整结果/独立审查回应。无需另一张Root批准或逐fit Portfolio许可。若出现具体科学冲突，带完整证据回到同一对话；不单方把本决定换成另一个比较。已消费C的六个原始模型和全部记录继续保全，已完成远端回收不重复，creator-owned被拒测试清理不通过另一删除者或整树回收绕过。[当前协议][protocol]；[peer原则][peers]。

## 六、实际材料访问与未验证范围

我先读取了完整当前报告，再读取新结果及实际审查／DM回应。新报告、E0、完整研究intake、全部74行独立答复及其逐项回应、实际抽样、科学卡指定范围和完整EXECUTION_FACTS均已访问；长返回的截断部分以重叠行窗口补齐。没有决策关键正文缺失。

| 材料范围 | 本轮实际处理 |
| --- | --- |
| 新C01科学与执行 | [报告][report]、[E0][e0]、[完整研究intake][intake]、[74行审查][review]、[DM审查回应][review-intake]全文；[卡][card]指定科学/推断/停止范围与实际前瞻修正；[首次抽样][draw]、[EXECUTION_FACTS][execution]完整读取 |
| 已发表数值 | [INTAKE_ANALYSIS][analysis]的主量、全部六单位主差及相关绝对值/费用字段检索，与完整E0的全部单位/18面板汇总交叉读取；未把检索到整份文件说成逐一复核所有raw向量或曲线 |
| 历史与前次判断 | 核对当前固定ref的Git blob与本会话此前实际读完的版本相同，复用完整[配对E0][paired-e0]、[配对intake][paired-intake]、[73行审查][paired-review]、[longer-C E0][long-e0]、[旧均匀C][uniform]、[训练F负结果][train-f]和[PARK知识][park]；同样复用完整[前次135行决定][previous]与[原重开答复][reopen]。本次新读取完整[前次应用intake][previous-intake] |
| 全局与同伴 | [报告][global]全文、[registry][registry]的根/Portfolio及三占位相关完整字段、[peer-context][peer-context]全文；重新读取完整[MGTAP科学intake][mgtap-science]和[139行裁决][mgtap-decision]，其[应用][mgtap-intake]核对同blob后复用；[FOLR唯一澄清][folr-decision]、[完整应用intake][folr-intake]和[当前EXECUTION][folr-execution]均实际读取 |
| 当前控制与方法 | [协议][protocol]全文；[AGENTS][agents]§§1—6、[peer][peers]相关范围、[规范][spec]§§7—8/11.4/11.7—11.10、[FOUNDATIONS][foundations]§6、[实证专题][empirical]前三节、[runtime][runtime]§1经同blob核对复用此前实际读取正文；本轮另读规范§5.3 |

主科学材料采用6f5788081986ee9f5b06bc236d8f6f1497dd7eb2；卡/抽样/analysis采用a94e4ae95bb8c558cf8d18e0d62f0f906ce9393a；最新审查采用9a655b28b5ac33935f88954c32b7a06b84c3252e；控制/全局采用5a4528317b2b2942efa0c4fdc3914ee7e034625f。下面引用保留每个具体文件的完整固定URL。固定ref首行读取及blob匹配只用于确认可复用内容，不被描述为新的全文阅读。

没有执行代码、加载模型、复核原始archive二进制或读取清单外helper。原生完整性和逐行数值验证是DM已有执行记录；独立审查的源码覆盖也不冒称本轮亲自重做。基础知识实际用于区分fit、相关快照、条件世界以及完整包与因果组件，不产生额外seed配额、阳性pilot、强参照合格门槛或校准服务。

**最终保持ACVC CONTINUE：实施一次新1024／4096配对B，研究更大C学习曝光下固定F相对于原C和有用dwell的增量。当前C01结论保留，后继没有预定结果或自动续期。** 本交付形成方向决定，不是已建立新卡、调用或修改共享生命周期记录的回执。

[report]: https://github.com/CartmanFatass/My-paper-code/blob/6f5788081986ee9f5b06bc236d8f6f1497dd7eb2/docs/research/candidates/acvc/ACVC_POST_C01_DIRECTION_REPORT_20260914.md
[e0]: https://github.com/CartmanFatass/My-paper-code/blob/6f5788081986ee9f5b06bc236d8f6f1497dd7eb2/docs/research/candidates/acvc/ACVC_CLUSTER_FIXED_RECIPE_C01_RESULT_EVIDENCE_20260914.md
[intake]: https://github.com/CartmanFatass/My-paper-code/blob/6f5788081986ee9f5b06bc236d8f6f1497dd7eb2/docs/research/candidates/acvc/ACVC_CLUSTER_FIXED_RECIPE_C01_INTAKE_20260914.md
[review]: https://github.com/CartmanFatass/My-paper-code/blob/9a655b28b5ac33935f88954c32b7a06b84c3252e/docs/research/candidates/acvc/pro_packets/20260914_cluster_fixed_recipe_c01_scientific_review_r2/archive/RESPONSE.md
[review-intake]: https://github.com/CartmanFatass/My-paper-code/blob/6f5788081986ee9f5b06bc236d8f6f1497dd7eb2/docs/research/candidates/acvc/pro_packets/20260914_cluster_fixed_recipe_c01_scientific_review_r2/INTAKE.md
[card]: https://github.com/CartmanFatass/My-paper-code/blob/a94e4ae95bb8c558cf8d18e0d62f0f906ce9393a/docs/research/candidates/acvc/ACVC_CLUSTER_FIXED_RECIPE_C01_SCIENCE_CARD_20260914.md
[draw]: https://github.com/CartmanFatass/My-paper-code/blob/a94e4ae95bb8c558cf8d18e0d62f0f906ce9393a/docs/research/candidates/acvc/ACVC_CLUSTER_FIXED_RECIPE_C01_PROSPECTIVE_FACTS_20260914.json
[analysis]: https://github.com/CartmanFatass/My-paper-code/blob/a94e4ae95bb8c558cf8d18e0d62f0f906ce9393a/docs/research/candidates/acvc/evidence/cluster_fixed_recipe_c01_20260914/INTAKE_ANALYSIS.json
[execution]: https://github.com/CartmanFatass/My-paper-code/blob/6f5788081986ee9f5b06bc236d8f6f1497dd7eb2/docs/research/candidates/acvc/evidence/cluster_fixed_recipe_c01_20260914/EXECUTION_FACTS.json
[direction]: https://github.com/CartmanFatass/My-paper-code/blob/6f5788081986ee9f5b06bc236d8f6f1497dd7eb2/docs/research/candidates/acvc/DIRECTION.md
[paired-e0]: https://github.com/CartmanFatass/My-paper-code/blob/6f5788081986ee9f5b06bc236d8f6f1497dd7eb2/docs/research/candidates/acvc/ACVC_CLUSTER_PAIRED_EXPOSURE_B01_RESULT_EVIDENCE_20260914.md
[paired-intake]: https://github.com/CartmanFatass/My-paper-code/blob/6f5788081986ee9f5b06bc236d8f6f1497dd7eb2/docs/research/candidates/acvc/ACVC_CLUSTER_PAIRED_EXPOSURE_B01_INTAKE_20260914.md
[paired-review]: https://github.com/CartmanFatass/My-paper-code/blob/68fed46f448312827f38b4b4f9bade36e2aedc35/docs/research/candidates/acvc/pro_packets/20260914_cluster_paired_exposure_b01_scientific_review/archive/RESPONSE.md
[long-e0]: https://github.com/CartmanFatass/My-paper-code/blob/6f5788081986ee9f5b06bc236d8f6f1497dd7eb2/docs/research/candidates/acvc/ACVC_CLUSTER_LONGER_C_B01_RESULT_EVIDENCE_20260914.md
[uniform]: https://github.com/CartmanFatass/My-paper-code/blob/6f5788081986ee9f5b06bc236d8f6f1497dd7eb2/docs/research/candidates/acvc/ACVC_FRESH_DENSE_PACKAGE_C01_INTAKE_20260911.md
[train-f]: https://github.com/CartmanFatass/My-paper-code/blob/6f5788081986ee9f5b06bc236d8f6f1497dd7eb2/docs/research/candidates/acvc/ACVC_FIXED_F_TRAINING_USE_B02_INTAKE_20260912.md
[park]: https://github.com/CartmanFatass/My-paper-code/blob/6f5788081986ee9f5b06bc236d8f6f1497dd7eb2/docs/research/candidates/acvc/PARK.md
[previous]: https://github.com/CartmanFatass/My-paper-code/blob/902df04e46a4cea8fe788baed14ca8c447cf18ea/docs/research/portfolio/pro_packets/20260914_acvc_post_paired_direction/archive/RESPONSE.md
[previous-intake]: https://github.com/CartmanFatass/My-paper-code/blob/6f5788081986ee9f5b06bc236d8f6f1497dd7eb2/docs/research/portfolio/pro_packets/20260914_acvc_post_paired_direction/INTAKE.md
[reopen]: https://github.com/CartmanFatass/My-paper-code/blob/5a4528317b2b2942efa0c4fdc3914ee7e034625f/docs/research/portfolio/pro_packets/20260914_rcle_park_vacancy_selection/archive/RESPONSE.md
[peer-context]: https://github.com/CartmanFatass/My-paper-code/blob/6f5788081986ee9f5b06bc236d8f6f1497dd7eb2/docs/research/candidates/acvc/ACVC_POST_C01_PEER_CONTEXT_20260914.md
[global]: https://github.com/CartmanFatass/My-paper-code/blob/5a4528317b2b2942efa0c4fdc3914ee7e034625f/docs/research/portfolio/PORTFOLIO.md
[registry]: https://github.com/CartmanFatass/My-paper-code/blob/5a4528317b2b2942efa0c4fdc3914ee7e034625f/.codex/hmasd-dm-sessions.toml
[mgtap-science]: https://github.com/CartmanFatass/My-paper-code/blob/d03ee1f04f7c0ea9dc2e7ae5ae817b75511a5f80/docs/research/candidates/metric_ground_transport_allocation/MGTAP_LR_SELECTION_B01_INTAKE_20260914.md
[mgtap-decision]: https://github.com/CartmanFatass/My-paper-code/blob/d03ee1f04f7c0ea9dc2e7ae5ae817b75511a5f80/docs/research/candidates/metric_ground_transport_allocation/pro_packets/20260914_lr_selection_portfolio_direction/archive/RESPONSE.md
[mgtap-intake]: https://github.com/CartmanFatass/My-paper-code/blob/d03ee1f04f7c0ea9dc2e7ae5ae817b75511a5f80/docs/research/candidates/metric_ground_transport_allocation/pro_packets/20260914_lr_selection_portfolio_direction/INTAKE.md
[folr-decision]: https://github.com/CartmanFatass/My-paper-code/blob/5a4528317b2b2942efa0c4fdc3914ee7e034625f/docs/research/candidates/vap_folr_core/pro_packets/20260914_post_b03_portfolio_direction/archive/clarification_01/RESPONSE.md
[folr-intake]: https://github.com/CartmanFatass/My-paper-code/blob/5a4528317b2b2942efa0c4fdc3914ee7e034625f/docs/research/candidates/vap_folr_core/pro_packets/20260914_post_b03_portfolio_direction/INTAKE.md
[folr-execution]: https://github.com/CartmanFatass/My-paper-code/blob/5a4528317b2b2942efa0c4fdc3914ee7e034625f/docs/research/candidates/vap_folr_core/entity_history_augmentation_b01_781601/EXECUTION.md
[protocol]: https://github.com/CartmanFatass/My-paper-code/blob/5a4528317b2b2942efa0c4fdc3914ee7e034625f/docs/project/PORTFOLIO_DECISION_PROTOCOL.md
[agents]: https://github.com/CartmanFatass/My-paper-code/blob/5a4528317b2b2942efa0c4fdc3914ee7e034625f/AGENTS.md
[peers]: https://github.com/CartmanFatass/My-paper-code/blob/5a4528317b2b2942efa0c4fdc3914ee7e034625f/docs/project/PEER_DM_COORDINATION.md
[spec]: https://github.com/CartmanFatass/My-paper-code/blob/5a4528317b2b2942efa0c4fdc3914ee7e034625f/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[foundations]: https://github.com/CartmanFatass/My-paper-code/blob/5a4528317b2b2942efa0c4fdc3914ee7e034625f/docs/rl-marl-foundations-20260907/FOUNDATIONS.md
[empirical]: https://github.com/CartmanFatass/My-paper-code/blob/5a4528317b2b2942efa0c4fdc3914ee7e034625f/docs/rl-marl-foundations-20260907/topic-notes/04_EMPIRICAL.md
[runtime]: https://github.com/CartmanFatass/My-paper-code/blob/5a4528317b2b2942efa0c4fdc3914ee7e034625f/docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md
