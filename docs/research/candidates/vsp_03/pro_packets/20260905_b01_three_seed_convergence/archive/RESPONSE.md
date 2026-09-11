**我决定暂缓当前这个固定 N1、以第 128 次更新为主要终点的规则初始化比较，不追加原样种子或更新，也不在本轮另选新 B 或多智能体重铸。**最小理由是：三个独立训练配对均在原定主要样本上达到 T=G=F，连提交时刻和原生回报组成也相同；已经选择的复制因此没有留下需要靠再做一次相同终局比较来解决的新分歧。早期原生回报优势是真实的、值得保留的局部初始化信号，但目前不能把它提升为训练超越固定规则、胜任早期通用方法上的优势，或持续到完整预算的收益。

这个选择只暂缓当前具体比较，不关闭事件感知终止学习，不决定 Portfolio 生命周期、优先级或融合，也不把 B 写成已消耗的 C。**最强的反对理由同样成立：早期正差异重复出现，而且三组完整运行只用了合计 12.293 秒；一个明确研究早期使用价值的新 B 完全可能值得做。**我没有把这种可能性判为失败，只是不把尚未选定的早期使用问题、评价器诊断或耦合任务自动接在本次复制之后。

## 一、原结果的完整读法

下述科学来源均取自 `CartmanFatass/My-paper-code` 的固定版本 `4dff9af4944f3d5c119030d31d35ec37ee7b7d29`。短文件名对应末节所列完整路径；章节和 JSON 键说明具体依据。实时 Issue 只作为讨论上下文，不替代固定证据。

[完整结果证据](https://github.com/CartmanFatass/My-paper-code/blob/4dff9af4944f3d5c119030d31d35ec37ee7b7d29/docs/research/candidates/vsp_03/VSP03_B01_SEEDS123_RESULT_EVIDENCE_20260905.md)的“All selected outcomes”及 [ANALYSIS.json](https://github.com/CartmanFatass/My-paper-code/blob/4dff9af4944f3d5c119030d31d35ec37ee7b7d29/docs/research/candidates/vsp_03/results/b01_seeds123/ANALYSIS.json)的 `seeds.*.endpoints` 给出全部规定端点。下表的“未测”不是零，也不能用主要终点的 F 代填。

| 独立训练配对 | 更新 | T 平均原生回报 | G 平均原生回报 | T−G | F 平均原生回报 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 32 | 0.365390625 | −0.2 | 0.565390625 | 未测 |
| 1 | 64 | 0.3671875 | −0.2 | 0.5671875 | 未测 |
| 1 | 128 | 0.3755859375 | 0.3755859375 | 0 | 0.3755859375 |
| 2 | 32 | 0.26453125 | −0.2 | 0.46453125 | 未测 |
| 2 | 64 | 0.35453125 | 0.097578125 | 0.256953125 | 未测 |
| 2 | 128 | 0.363779296875 | 0.363779296875 | 0 | 0.363779296875 |
| 3 | 32 | 0.288984375 | −0.2 | 0.488984375 | 未测 |
| 3 | 64 | 0.37109375 | 0.37109375 | 0 | 未测 |
| 3 | 128 | 0.385927734375 | 0.385927734375 | 0 | 0.385927734375 |

第 32、64 次更新各评价每臂 128 集，第 128 次各评价 1,024 集。三个主要比较不仅均值相等：每个配对自己的 1,024 条 T/G/F 原生记录都匹配，包括提交时刻、成功、尝试和等待。它加强了“这些实际样本上未显示最终初始化增益”的判断，却不是所有可达状态上的策略等价，更不是三个网络的概率输出或参数相等。

第 32 次更新，G 在三个 128 集评价中都完全不提交；第 64 次，G 的未提交集数分别为 128、79、8，T 为 4、10、8。因此只能说三个训练实例都在第 128 次的观测点追平，其中第三组在第 64 次已追平；不能从稀疏端点确定另两组的精确追平时刻。G 早期的 greedy 行为不足必须与每个正差值同时报告，而不是删去正值或隐去不足。训练使用随机动作，故早期 greedy 不提交也不等于没有真实探索和更新。（同上，`non_submission_counts`；科学卡“Learning, randomness and object-tier numerical details”。）

[PRIMARY_RUN_SUMMARY.json](https://github.com/CartmanFatass/My-paper-code/blob/4dff9af4944f3d5c119030d31d35ec37ee7b7d29/docs/research/candidates/vsp_03/results/b01_seeds123/PRIMARY_RUN_SUMMARY.json)正确地每个独立训练配对、每臂只取一个主要分数：T、G 的平均值均为 0.37509765625，三个配对差均为零。这里差值的样本标准差为零，不代表总体方差为零；原有条件 episode 标准误也不能充当训练总体不确定性。六个 learner 构成三个配对差的样本，不是六个独立处理效应样本，更不是把评价 episode 当训练重复。

早期结果没有被“最终持平”抵销。已有工具汇总在第 32 次的平均 T−G 为 0.5063020833、配对间样本标准差为 0.0526125522；第 64 次分别为 0.2747135417、0.2840105444。这是不同早期追平速度的描述，不能据此补出完整学习曲线面积、累计训练回报或精确收敛速度。（`ANALYSIS.json::endpoint_descriptive_summary`。）原卡主要终点仍为第 128 次，0.02 的 MEI 仍是解释尺度，不变成事后等价界或阴性阈值。

## 二、这些证据支持什么，仍不能区分什么

**最强支持是“通用 learner 在实际有限训练后追到了现成规则”，而不是一个形式零值。**共同信息、同网络和相同 episode/update 预算，加上实际任务行为及 F 的参照，使三个主要零差异具有清楚的比较含义。G 在主要样本上达到 F 的行为，是相对于这个简单参考的实际胜任证据；它不是经过完整调优的通用方法认证，也不证明 F 或 G 最优。T 也没有在这些主要样本上显示超越 F 的改善。（[科学卡](https://github.com/CartmanFatass/My-paper-code/blob/4dff9af4944f3d5c119030d31d35ec37ee7b7d29/docs/research/candidates/vsp_03/VSP03_B01_SCIENCE_CARD_20260905.md)的“Information, treatment and strongest selected comparator”“Focused check, stopping and result branches”；完整结果证据。）

原生后果并非对布尔规则的打分。COMPLETE 真正提交不可撤回的八 tick 任务，只有未来八个服务采样全部在区内才交付成功；CONTINUE 支付实际等待，未提交支付全部 40 ticks 的等待成本。回报为 `(200*success−10*attempt−waiting_ticks)/200`，完整 episode 的服务和尾部均执行。早期差异因而确是这个 toy 的原生回报差异，不是代理指标或 certifier 一致率；但 toy 的任务效用不是现实部署效用认证。（科学卡“Environment and complete native consequence”；[b01.py](https://github.com/CartmanFatass/My-paper-code/blob/4dff9af4944f3d5c119030d31d35ec37ee7b7d29/experiments/candidates/vsp_03/vsp03_b01/b01.py)的 `rollout`、`return_to_go`。）

仍存的解释分为三类，现有证据没有要求必须选出唯一一种。

**初始化与 greedy 读出。**源码显示 T 初始提交概率按 b 为 0.75/0.25，G 为 0.5，且 greedy 的零 logit 统一选 CONTINUE；F 正是 T 初始化时的 greedy 规则。这样的起点足以使“较早出现有用的确定性提交行为”成为可信解释。训练后的早期 logit 分布和随机策略评价没有在本清单中形成对应观测，故不能断言全部差异只是阈值现象，也不能断言训练已经改善了 F。初始 T 的 greedy 等于 F，是定义事实；训练到第 32、64 次仍等于 F，则不是已测事实。（`b01.py::Model`、`rollout`、`run`；`VSP03_B01_SEEDS123_INTAKE_20260905.md`的“Reading the result”。）

**公开驻留年龄与普通函数学习。**目标转移由当前 y、d 决定，剩余机会由 t 决定；两臂都得到 y、d、时间和 a/e/b。因此这不是 treatment 独占历史信息的比较。普通 MLP 学会与公共规则相近的提交边界，与最终记录一致是相容的解释；它不证明事件特征永远无用，也不抹去初始化可能改变优化过程的价值。（科学卡“Information, treatment and strongest selected comparator”。）

**策略诱发的训练样本不同。**虽然每臂都是 16,384 个训练 episode 和 128 次联合 Adam 更新，T/G 的有效决策与梯度行并不相同：三组分别为 53,473/42,139、53,848/40,998、54,471/40,416。合计为 161,792/123,553。原任务提交越早，后续有效决策越少；这既可能参与学习轨迹差异，也是当前算法行为的一部分。不能把“相同 episode/update 预算”写成“完全相同梯度样本或计算量”，也不应为追求行数相同而事后补训练或把 actor 目标改为逐行归一化。参数位移和非零梯度证明有训练暴露，不证明机制有效。（完整结果证据“Actual learning exposure”；`ANALYSIS.json::seeds.*.exposure`；`b01.py::objective`。）

等待价格、事件频率和截止机会也可能影响排序。现有材料没有将这些因素逐一干预，更没有记录一个足以指定新改动的独特失败原因。此处的“未区分”是解释范围，不是原比较无效，也不是先做全量诊断的要求。

## 三、为什么本轮选择暂缓，而不是另开一个早期 B

我赞成 DM 建议的范围，但不采用“主终点为零，所以没有值得保留的学习信号”这种理由。真正完成的科学更新是：原本有意义的有限预算初始化比较已经获得三个有效主要零差异，同时获得三个早期正差异和不同追平时点。重复完全相同的主要比较还能增加样本，但其边际决策价值已小于第一次及两次事先选定的复制；本次没有据此选择第四组。

**对暂缓最有力的反证，是重复的早期原生收益，而不只是运行便宜。**在真正关心训练早期使用表现的研究问题中，更早能交付任务本身就可能是有效收益，不要求先超过 F，更不要求排除所有机制解释。相同预算的普通初始化较慢，也不当然是比较“不公平”；不过，现有早期胜利确实发生在一个完全不提交的 greedy G 上，必须用这个有限含义命名。暂停可能错过一个值得研究的 warm-start 效果，这是本选择保留的不确定性。

我仍不在本轮选择新的早期 B，原因是目前最清楚的后续只是重新界定“何时使用已训练策略、用哪种执行策略衡量早期价值”。这可以成为一个正当的新性能问题，但不能把已看到有利的第 32 次直接改作旧卡主终点。另一个候选是补随机评价和同期 F 来区分读出效应与规则本身；它会缩小早期解释，却不会自动产生超越规则的学习事实或更强的最终回报结论。本轮不把这种解释细化选为下一项投资，也不要求先重建旧中间 checkpoint 才准研究其他问题。

这里没有把“超过 F”“已有正 headroom”或“机制解释完整”设为继续条件。即使没有任何正值，只要一个具体的新学习比较能改变下一科学选择，仍可直接进入 B。反过来，当前的正值也不自动授予一串新评价、新 seeds 或新 host。**暂缓的对象是当前比较的继续投入，不是早期结果的可信性，也不是新 B 的合法性。**这符合证据规范 §11.8.1–11.8.3、§11.9；不是用规范禁止了探索，而是本轮在允许的选项中作了最小选择。

## 四、暂停边界与真正有用的重入事实

边界限定为当前持久目标 N1 host、共同公开信息与 1,571 参数模型、T/G 初始化干预、每臂 128×128 个完整 40-tick 训练 episode、固定第 128 次主要评价的继续比较。原有结果继续有效，B 没有 C 式消费状态；不追加种子、更新、调参、强制计时或自动改 host。这里也不选一个声称更有 MARL 意义、但实为若干独立控制器并列的新问题。

有用的重入事实不是“找到一个新的正种子”，而是**比较所服务的科学选择发生了具体变化**。例如，早期使用预算及其原生任务目标被明确选为待研究问题，并说明为什么该预算值得研究而不只是因为已观察到该点为正；或现有任务证据指出一个具体提交／等待后果，使某项明确的学习改动有机会改变实际回报。这样的事实可以来自已有证据和一个有理由的新设计，不必先花钱产生阳性结果。若未来研究早期使用，必须同时说清实际执行的是 greedy 还是随机策略、简单 F 的角色，以及通用比较器在相同可访问信息和所给预算上的实际行为；不能只沿用“generic”这个名字认证它胜任。

若另选真正耦合的终止学习问题，最低必要区别应是：一个 agent 的继续或提交会改变伙伴可行的后续行动、任务成功条件、共享资源或团队原生回报，因而伙伴的决策会反过来影响本 agent 的终止收益。仅相加若干本任务回报不满足这个区别。当前清单没有给出已经选择并实现的此类任务、共同后果和胜任比较器；本轮因此不声称已经完成重铸，也不把这些未定设计拆成一串必须先做的 A。这里说明的是不同问题成立所需的含义，不是授予新模拟器或新实验的工作范围。

**本轮没有选定一个待执行的后继实验或诊断。**所以上述重入说明不携带隐含的 arms、seed、评价或 solver 额度；下一判别是先形成一个能说明其决策用途的具体性能问题，而不是先证明最优策略、穷举 support 或做 headroom 搜索。将来实际选择新的 B 时，应在同一问题内写出其真实数量、完整调用 cap 和停止条件，并标注受本次结果启发；不需要所有 seed 阳性、再走多轮 Pro、换框架或先做计时试验。

## 五、已有成本、可复用实现与本次停止范围

已完成工作不是抽象的“有限算法”。机器记录的 dominant 数量如下，全部包含在当前来源中，无需再运行模型或模拟器来获得这些计数。

| 工作项 | 每个完整训练配对 | 三个配对合计 |
| --- | ---: | ---: |
| 训练 learner | T、G 各一个 | 六个 learner，三个独立配对 |
| 训练 | 每臂 128 更新×128 集×40 ticks | 768 次联合 optimizer.step |
| learner 评价 | 每臂更新 32/64 各 128 集，128 为 1,024 集 | 保留全部九个配对端点 |
| 固定 F | 1,024 集×40 ticks，零更新 | 3,072 集，零更新 |
| 已有集成检查 | 8 集×40 ticks，单次 backward、零 optimizer.step | 24 集，零 optimizer.step |
| 全部完整 episode 执行 | 36,360 | 109,080 |
| 全部 primitive ticks | 1,454,400 | 4,363,200 |

每臂训练为 655,360 ticks，评价为 51,200 ticks；配对总数还包括 F 的 40,960 ticks 和已有检查的 320 ticks。没有嵌套候选、joint-action、未来轨迹搜索或 solver 调用；最多九个实际决策边界不是九层前瞻搜索。（科学卡“Counts, exposure and cost”；完整结果证据“Actual learning exposure”；`ANALYSIS.json::totals`。）

原完整每臂成本律为 `I_q+128*C_q(128,40)+10*E_q(128,40)+O_q`，C 含采样、原生回报和一次联合更新；整个配对再加共享 import／检查、八个 F batch、汇总和发布读回。实测完整 runner 时间分别为 **2.364870157、5.905074235、4.023389709 秒，合计 12.293334101 秒**。这比单看训练循环更完整，但仍不把 Git、SSH、外部控制与排队全部宣称为已计入的研究总耗时。新增两组的 supervisor-clock 95 秒包括间隔，不等于两组 runner wall 之和；完整 aggregate CPU 和 live thread census 未测。（`VSP03_B01_SEEDS23_TECHNICAL_COLLECTION_20260905.md`的“Execution and resource facts”“Measured phases”；`ANALYSIS.json::cost_terms`、`whole_invocation`、`totals`。）

以第一组速率估计后两组共 4.729740314 秒，实际为 9.928463944 秒，原条件预测低估了成本。原因未定位，不应凭空归因于争用、内核或实现缺陷；也不需要因此另开强制 profiling。原来每组的 **1,800 秒是完整调用硬 cap，不是运行预测，更不是下一实验的可支配余额**。本轮既不沿用它扩展实验，也不按核心数折算速度。

真正可复用的是已经读取的 `b01.py` 中的 `tapes`、`Model`、`rollout`、`objective`、`metrics` 和完整输出路径：单进程、CPU float32、按 episode 向量化，40 tick 因果顺序保持，真实 actor–critic 与原生评价已经闭合。薄 runner 的存在和 CLI 单行修正来自技术记录；本轮没有另外读取未列出的 runner。已有秒级实测只支持原工作形状的成本认识，不能认证新耦合 host 或新评价形状同样便宜。

学习、完整原生后果、所选主要评价、信息与预算记录是算法比较需要的工作。八例检查及必要发布读回是既有验证／测量工作，已独立计数；它们不是额外训练样本。本轮不增加精确 upper、历史 census、候选搜索、全 checkpoint 重建、跨平台逐位复现或重复 smoke。相应放弃的强主张分别是最优性 gap、全支持覆盖、唯一机制、全历史重演和数值等价；不放弃原生回报、真实训练、同信息比较及主要测量完整性。

现行工程规范的 2,000 行研究源码、600 行 runner 和适度测试预算仍适用，30% 编排比例只是审查信号；没有新 machinery 或对象限定例外被本结论授权。运行规范的完整逻辑调用原则不允许分阶段重置预算，也不把“有限”“零 learner”“native”当廉价证明。（`ENGINEERING_SCOPE_SPEC.md` §3–5；`MARL_RUNTIME_ENGINEERING_SPEC.md` General requirements §1–4、§7；证据规范 §11.8.6–§11.9。）

**本次咨询实际新增模型、训练 arms、独立训练 starts、updates、batch、episode、tick、评价点、评价调用及嵌套搜索／solver 调用均为零；后继科学运行也没有被本轮选入。**不存在一个正在执行、可以续领 cap 的新逻辑调用。读取与交付本身耗时未测，零科学暴露不意味着零总成本。停止规则就是结束已完成有限复制的追加投入并交付这个方向内结论，而不是等到获得阳性或等到用尽历史 cap。

## 六、证据等级与保留的历史

本结论是 B/EXPLORE 下的有界投入选择，不是论文级否定。三个样本不能建立稳定优越性或总体等价；不设置全 seeds 阳性、精确重复或置信区间坍缩的规则。未来论文级性能主张才按其实际任务、选择历史和主张范围承担公平比较、独立训练及合适不确定性，不能用“三个种子”这个数目自动兑换充分性。（[MARL_EMPIRICAL_EVIDENCE_SPEC.md](https://github.com/CartmanFatass/My-paper-code/blob/4dff9af4944f3d5c119030d31d35ec37ee7b7d29/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md) §5.2、§6.1、§11.8.2–§11.8.5、§11.9。）

选择历史保持完整：最初 Innovator 选择最小真实 N1 B；seed 1 的主要零值与早期正值随后被观察；seed 2/3 在各自结果未知时被选为有限复制；本轮三个结果都已知。任何由此产生的新设计都属于结果启发，不能冒充结果未知的旧卡确认。DM 的原预测与三个结果相容，但不是一个经过校准的预测成功率，也不代替本次判断。（`VSP03_B01_SEED1_INTAKE_20260905.md`；`VSP03_B01_SEEDS23_FOLLOWUP_20260905.md`；`VSP03_B01_SEEDS123_INTAKE_20260905.md`。）

旧 VSP-03 的事件来源缺口没有被新模拟器认证。本轮也不重新解释 FSD：按已读[前序 Innovator 完整归档](https://github.com/CartmanFatass/My-paper-code/blob/4dff9af4944f3d5c119030d31d35ec37ee7b7d29/docs/research/candidates/vsp_03/pro_packets/20260905_k1_host_innovator/archive/RESPONSE.md)“FSD 的完整边界不变”，保留现行固定 N6/K2/Z4、两区域、H400、公开 flag/cue、既有 HMASD skill/actor 路径的 policy-gap 家族停止范围。其 small seed 2 的合格正值 +0.033291585286、small seed 3 带比较器不足限定的正值，以及 medium/large 六个合格配对亏损均不被本结论抵销；E4 的公共 greedy 解释也不是当前 N1 learner 的收益证据。本轮没有直接重读那些清单外 FSD 原文件，历史限定来自此处列明的完整归档及 `DIRECTION.md`，不声称新增历史核验。

没有规范例外被提出或默许。交付文件、评论、完整篇幅和进程成功都不是科学结论成立的保证；成立范围来自上述实际比较、反证和有限选择。本轮不修改方向状态、主分支或 Portfolio。

## 七、实际读取范围与未验证事项

本轮通过连接的 GitHub 成功读取以下 18 个允许的证据路径，全部使用前述固定科学版本。长文件分段读取；表中对规范、附录和源码的范围作具体限定，不以链接标题冒充阅读。入口 `TASK.md` 另按用户指定的固定任务版本读取，不作为经验结果来源。

| 实际证据路径 | 实际读取和使用范围 |
| --- | --- |
| `AGENTS.md` | 正文 §1–8 及所取 Appendix A 段落；科学边界、暴露、工程与写入范围，不声称完整读取其余附录 |
| `docs/research/candidates/vsp_03/pro_packets/20260905_b01_three_seed_convergence/CURRENT_DELIVERY_AUTHORITY.md` | 全文；当前交付背景，不扩大本轮权限 |
| `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md` | 全文，含完整 §11.8、§11.9 |
| `docs/project/ENGINEERING_SCOPE_SPEC.md` | 正文职责、§3–5 要求与预算、后续适用条款及对象附款边界 |
| `docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md` | General requirements §1–8；另读 VNFC 专属附款部分以确认不适用于本对象，不声称完整核验该附款 |
| `.agents/skills/hmasd-scientific-tools/SKILL.md` | 全文；已有计算、每训练 run 汇总及具体工具用途 |
| `docs/research/candidates/vsp_03/DIRECTION.md` | 全文；当前问题、三组观察、历史停止边界 |
| `docs/research/candidates/vsp_03/pro_packets/20260905_k1_host_innovator/archive/RESPONSE.md` | 完整归档；原 N1 选择、数量、读法、反证、FSD 边界及其自身阅读限定 |
| `docs/research/candidates/vsp_03/VSP03_B01_SCIENCE_CARD_20260905.md` | 全文；任务、T/G/F、信息、学习、主要终点与原解释规则 |
| `docs/research/candidates/vsp_03/VSP03_B01_SEEDS23_FOLLOWUP_20260905.md` | 全文；结果知情顺序、预先选定两组、CLI 修正、数量和停止 |
| `docs/research/candidates/vsp_03/VSP03_B01_SEED1_INTAKE_20260905.md` | 全文；第一组读法、局部正值、复制理由 |
| `docs/research/candidates/vsp_03/VSP03_B01_SEEDS123_RESULT_EVIDENCE_20260905.md` | 全文；全部端点、真实暴露、完整成本、测量与来源限制 |
| `docs/research/candidates/vsp_03/VSP03_B01_SEEDS123_INTAKE_20260905.md` | 全文；DM 综合、尚待本轮选择的建议与未测事项 |
| `docs/research/candidates/vsp_03/results/b01_seeds123/ANALYSIS.json` | 全文；三个种子的端点、暴露、阶段成本、总量及已有 artifact 定位信息 |
| `docs/research/candidates/vsp_03/results/b01_seeds123/PRIMARY_RUN_SUMMARY.json` | 全文；每训练 run 的主要分数和完整配对差 |
| `docs/research/candidates/vsp_03/VSP03_B01_SEEDS23_TECHNICAL_COLLECTION_20260905.md` | 全文；两组执行、验收、counts、成本和读回事实 |
| `experiments/candidates/vsp_03/vsp03_b01/b01.py` | 全文静态阅读；环境、动作、原生回报、模型、训练、评价和输出链；没有执行 |
| `docs/research/candidates/vsp_03/pro_packets/20260905_b01_three_seed_convergence/ISSUE_SNAPSHOT.json` | 全文；固定讨论快照及空评论集合 |

另于 **2026-09-06 01:10 UTC 左右（2026-09-05 18:10 PDT）**通过 GitHub connector 读取 [Issue #6](https://github.com/CartmanFatass/My-paper-code/issues/6) 正文并读取完整评论集合。正文仍为 DM 的综合与待决问题；其 `updated_at` 为 2026-09-06T00:37:18Z；评论集合为空，因此这次科学阅读没有可列的既存评论 permalink。随后产生的交付评论只链接本文，不构成新增科学证据。未跟随正文中的其他版本链接，也未读取清单外讨论。

没有科学来源访问缺口。目标文件不存在属于交付前检查结果，不是研究证据缺失。本轮未运行源码、未新建模型、未加载或重建原始 checkpoint、未直接读取清单外原始逐集文件、未独立复现 CM 的验收或重新运行统计工具。表中数值来自已读机器分析与固定结果记录，源码阅读只核对其可见工作形状，不把记录的技术验收冒充本轮新验收。早期 F、随机 checkpoint 评价、完整训练曲线的额外分析、总体策略关系、最优性、唯一因果解释和新耦合 host 成本仍未验证；这些限制不阻止当前最小范围的暂缓选择。

**最终选择保持为：暂缓当前 N1 完整预算初始化比较，保留全部早期局部正信号及其限制，不追加原样运行，不关闭事件感知终止学习，也不在本轮默许一个新的实验或 Portfolio 处置。**
