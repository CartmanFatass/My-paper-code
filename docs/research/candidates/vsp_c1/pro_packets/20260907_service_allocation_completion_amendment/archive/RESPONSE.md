**决定：选择 A。在方向层对已形成的三队列服务分配决定作一次明确、仅限本对象的修订：允许聚焦发布修复被技术接受后，另行安排一个且仅一个完整的 LQ-EXCLUDE 补测调用，上限 120 秒，读取原有两个学习器的终点，在原定全部 256 条评价 tapes 上补齐固定规则及三项配对比较。** 这一次例外改变的是原答复第“五”节及原卡 §§5–7 的“参照必须置于第二调用、不得新增第三调用”边界；不增加学习、学习器评价或独立训练实例，不重开其他家族，不修改仓库规范。原 GENERIC 调用仍是退出 1 的失败调用；补测即使成功，也只能形成“保留失败历史、经结果知情修订补齐参照”的证据，不能改写为原两调用前瞻成功。当前答复是科学选择，不是修复代码接受、CM 派工或 Root 的进程启动命令。[原决定，§§五–六][previous]；[原卡，§§5–7][card]；[修订范围，Exact existing clauses affected、Option A][scope]

最强理由是尚缺的量仍会改变一个具体控制器选择，而不是给已经很小的 FACTOR 差值增加精度。已知 Δ=J_F−J_G，却不知道 J_R，因此不知道两学习器是否值得相对无需训练的规则继续投入。E_F=J_F−J_R、E_G=J_G−J_R 满足 E_F−E_G=Δ；小 Δ 约束二者的距离，不决定二者位于规则之上还是之下。补一个预先指定的规则值，可以区分“保留直接规则”“有局部学习政策用途、但没有乘性结构增益理由”“均无足够实用区分”。这正是原卡的问题，不是事后更换比较器。[原卡，§§1、5][card]；[科学 intake，§§2、6][intake]

**B 是真正合理的备选。** 0.00651042 的学习器差不到 MEI，即使补测也不会产生 MEI 量级的表示优势；修复、检查、导入和发布都有成本，固定规则也不是最优控制器。我不以沉没工作、旧调用很短或新增梯度为零否定 B。仍选择 A，是因为这项剩余比较能直接回答当前用途问题，且不必重新训练、挑选数据、调参或寻找新宿主。选择止于这一补测；它不产生“所有缺失结果都必须补齐”的一般规则。[修订范围，Evidence and decision value、Option B][scope]

## 一、保留的观察与不能改变的读法

以下是固定证据中的已测量事实，不是本咨询的新实验。两个学习器均完成 256 次 Adam 更新及 0、64、128、192、256 五点评价；每个终点含两个周期各 128 个有索引的情节。[执行记录，Final technical return、Saved-array collection][execution]；[分析文件，endpoint_J、FACTOR_minus_GENERIC、auc、initial_to_final][analysis]

| 既有量 | FACTOR | GENERIC | FACTOR − GENERIC |
| --- | ---: | ---: | ---: |
| 更新 256 等权 J | 0.758911132813 | 0.752400716146 | +0.006510416667 |
| 更新 256，d=2 | 0.753092447917 | 0.751383463542 | +0.001708984375 |
| 更新 256，d=6 | 0.764729817708 | 0.753417968750 | +0.011311848958 |
| 初始等权 J | 0.748453776042 | 0.751139322917 | −0.002685546875 |
| 原定五点 AUC | 0.759221394857 | 0.757858276367 | +0.001363118490 |
| 终点减初始的等权变化 | +0.010457356771 | +0.001261393229 | 不替代主终点 |

Δ 对应平均每情节多完成 0.625 件工作，MEI 仍为 J 的 0.025，即 2.4 件工作。两个周期均为小正差，不删除；条件评价标准误 0.002109066044 仅描述这两个固定政策的配对评价噪声，不是独立训练人群的误差或稳定优势证据。全部五点、逐周期 TD 损失、初值与原生后果继续保留。两个学习器更新 192 的均值都高于最终值，也不能据此改用较好 checkpoint。[intake，§2][intake]；[分析文件，fixed_curves][analysis]

现有事实是“学习器之间有低于 MEI 的局部正差；规则相对价值未测”。它既不是规则获胜，也不是学习器获胜，更不能把参照缺失当成 Δ 无效。无论 J_R 后来是什么，原卡中要求 Δ≥0.025 的 FACTOR-over-GENERIC 较大收益条件都不会因本次补测而成立。[原卡，§5][card]

原失败边界也有具体证据。源码中 `Budget.checkpoints` 为 tuple，`configuration()` 将 `vars(budget)` 放入 summary；原 runner JSON 读取 FACTOR，而把 `run()` 返回的原生 GENERIC summary 直接传给 `publish_comparison`。`reporting.compare` 比较完整 budget 时先遇到 list/tuple 表示差异，故在 `evaluate_rule()` 之前退出。E0 的静态算术与保存文件核对表明两个已保存 JSON budget 相同；错误消息不构成真实预算不同的证据。我读到的调用顺序与这一解释相符，但未在本轮重跑失败或直接读取远端原始 summary。[experiment.py，Budget、configuration、run][experiment]；[原 runner，main 中比较与规则调用顺序][runner]；[reporting.py，compare][reporting]；[执行记录，Exact failure and coverage limitation][execution]

原测试中的 `synthetic_summary` 只放 seed/updates，且发布测试将两臂都 JSON 往返，确实没有覆盖完整 checkpoints 的混合表示。它以前通过的事实保持，但不能继续作为这个生产边界已被覆盖的证据。[test_contract.py，synthetic_summary、test_primary_publication_three_contrasts_auc_initial_and_missing_rule][tests]

## 二、明确修订哪几句，保留哪些限制

原答复第“五”节把固定规则和配对发布放在第二个完整调用内，并禁止第三调用；第“六”节允许保留 learner-only Δ，但没有自动补第三调用的许可。原卡 §§5–7 承接了这些条款。这是实际授权边界，不是 JSON 修复自然附带的权限，也不能用证据规范 §11.8.7 或两次 2,700 秒 cap 的未用时间绕过。[原决定，§§五–六][previous]；[原卡，§§5–7][card]

**本次例外仅为：允许在原两个调用之后，以新修复源码、独立新输出根和新执行句柄，完成一次“原固定规则的剩余评价＋基于保存数据的配对发布”，全过程最多 120 秒。** 对该补测不再要求其发生在已经结束的 GENERIC 进程内；相应允许这唯一第三调用。禁止借用原 cap、重置时钟、重跑学习器、自动重试或增加第四调用的限制继续成立。其他回报、信息、模型、周期、样本、主终点、MEI、AUC、预测和家族边界均不变。原任务、原答复、原卡、退出记录、traceback 和原始产物保持原文，本修订单独并列记录，不追溯覆盖它们。[修订范围，Option A][scope]

这是原决定的有范围修订，不是全项目证据或工程规范例外。§11.8.7 允许保存未损坏的依赖，§5.2、§11.8–11.9 允许明确标注的结果知情探索；它们并不自动分配新调用。本次明确选择解决了原对象的调用限制，后续仍按现行职责接受修复源码，再由后来单独下达的 Root 执行命令绑定新源码 SHA、只读输入、输出根、句柄及停止命令。不得把本答复理解为已经实施或启动，也不添加新的审批层。[证据规范，§§5.2、11.8.6–11.9][spec]；[AGENTS，§§2、4–5][agents]；[条件交接，第1、5项][handoff]

## 三、唯一补测的固定数据、行为和发布

读取 E0 所列原远端工作树 `/home/wu/hmasd-worktrees/vspc1-service-allocation-b01-seed402-20260907` 下 `temp/directions/vsp_c1/exp/k4_service_allocation_b01_seed402_20260907/FACTOR/summary.json` 与对应 `GENERIC/summary.json`，保留原来源 `faf786e135b3f55e535c898e17e646dcc341bdec`。它们及原目录只读。输入需要是已经核对过的两份完整保存结果，而非抄录的均值、重新生成的学习轨迹或后来挑选的模型。新规则及联合输出写到另一个补测根，不覆盖原 learner summary 或伪造原 runner 当时的配对文件。[执行记录，Artifacts and return route][execution]；[条件交接，第2–3项][handoff]

唯一实际政策评价为现有 `evaluate_rule(Budget(seed=402))`。周期顺序仍为 (2,6)，各 128 情节，每情节 48 tick；用原 NumPy 1.26.3 和原 `tapes` 的 PCG64/SeedSequence：到达为 `[402,31,d,0]`，初始 h 为 `[402,32,d,0]`，数组形状分别为 (128,48,3) 与 (128,)，保持原生成顺序和整数/浮点抽样方式。不更换命名空间、批次大小、形状、随机数库或消费顺序来获得一批“等分布”的替代样本。训练随机流不调用。这是重建同一批既定外生输入，不是增加独立评价样本。[原卡，§4][card]；[experiment.py，rng、tapes、evaluate_rule][experiment]

规则每情节从自己的 (2,2,2) 队列与该 tape 的 h 开始：在续约时按旧 h 预测伙伴当前动作，从另两条队列选最长者，并列取最低编号，保持 d 步。伙伴逐 tick 用当时队长和旧 h 响应；服务、到达、容量 4 截断和 h 更新顺序保持。三队列 Bernoulli(0.5) 到达、固定伙伴、两工人和全情节已服务件数/96 不变。**只共享外生 tapes；不重放任何学习器的队列、动作或伙伴轨迹给规则，也不让规则在持有段中重选焦点动作。**[原卡，§§2–3][card]；[experiment.py，partner_action、lq_exclude、tick、collect][experiment]

不调用 `run()`、`QNetwork`、优化器或 learner evaluator，不执行原 runner 的 `--describe`，后者也会初始化模型。普通模块导入可以定义类，不能实例化；补测入口自行设置现有单线程限制，不靠调用训练入口设置。保持 CPU float32、一个 compute thread、规则原批次为每周期 128；训练 batch16 保持历史定义但完全不用。现有 `collect(None,...)` 会构造状态/段张量，这仍是实际工作，却不是 Q 评分、参数更新或额外训练样本；不为了“零模型”重写这个已接受的规则路径。[experiment.py，collect、evaluate_rule、run][experiment]；[原 runner，main][runner]；[条件交接，第3项][handoff]

发布使用全部原学习终点索引与这次 256 个规则终点，保留 Δ、E_F、E_G 的逐周期值、等权均值及每一对比的条件标准误 `0.5×sqrt(s_2²/128+s_6²/128)`。三项对比共用数据、满足 `E_F−E_G=Δ`，不是三次独立成功。仍保留原五点 AUC、初值到终点变化及原生后果；新增的 initial-relative-to-rule 只需原初始均值减规则均值，不重新评价初始模型。AUC 仍是原五点梯形积分除以 256，不给固定规则另造五点曲线。比较/发布算术必须保留原读数，不能靠数值舍入、筛点或重加权越过 MEI。[原卡，§5][card]；[reporting.py，contrast、auc、compare][reporting]

## 四、仅为这一依赖修复，验证不变成补跑

选择条件交接中三个路径的聚焦范围：`experiments/candidates/vsp_c1/k4_service_allocation_b01/reporting.py`、新增的薄入口 `scripts/complete_vspc1_k4_service_allocation_b01.py`，以及原 `tests/experiments/candidates/vsp_c1/k4_service_allocation_b01/test_contract.py` 中的发布 fixture。`experiment.py` 和原 learner runner 均不修改。修复只消除等值 checkpoint 序列的 list/tuple 表示差异，保留对真正不同 seed、预算数值、checkpoint 值或顺序的拒绝；不能删除 budget 比较、排序成集合、丢字段或用宽松强制转换掩盖不同数据。[条件交接，第2–4项][handoff]；[reporting.py，compare][reporting]

采用一个完整调用不超过 300 秒的聚焦合成 fixture，最多三个纯发布案例：完整预算的 loaded/native 等值混合表示能给出原 learner-only 算术；合成规则加入后可写读全部三对比且 Δ、SE、五点 AUC、初值变化保持；一个真实 checkpoint 内容或顺序差异仍被拒绝。其他已有种子/预算比较与专用入口不建模型、不走训练的保证，由这次只读独立审阅核对。合成数据用字面值与普通数组算术，不调用模型、优化器、环境、规则或 RNG；不重放原九测试全套，不做 seed402 tape 探针或完整 runner smoke。读入模块本身不等于调用其中的宿主/规则函数，fixture 也不应调用这些路径。[原测试，发布 fixture][tests]；[条件交接，第4–5项][handoff]

非测试补丁总变更 `A+D≤150`，其中新入口 `≤100` 行，仍在普通 2,000 非测试研究行、600 runner 行限制内；fixture 的一次 300 秒上限独立于补测的 120 秒，不挪用时间，也不拆分逻辑变更重置额度。工程 scope §4 新设施为 none：不引入通用序列化/验证框架、guard、恢复、重试/租约、注册或服务。若修复、验证或只读审阅暴露必须越出这些路径/语义/预算的具体问题，就保留缺口返回；本选择没有自动扩展修复或再次验证调用的额度。这里描述的是后续可实施范围，当前没有补丁、测试通过或技术接受的新事实。[工程规范，§§3–5][engineering]；[条件交接，第5项][handoff]

## 五、完整曝光、成本与一次停止

主导新增工作是一个规则×两个周期×128 情节×48 tick，加上读取保存数组、重建 tapes、普通统计和写读发布；不是策略树、轨迹搜索或更换比较器。每次续约预测一次伙伴当前选择，逐 tick 又有实际伙伴选择，不能漏算前者。[COMPLETION_COUNTS，proposed_if_option_A][counts]

| 数量 | 既有实际 | 本次若实施的新增 | 补测成功后的合计 |
| --- | ---: | ---: | ---: |
| 独立配对训练实例 | 1 | 0 | 1 |
| 学习器调用 / 规则专用调用 | 2 / 0 | 0 / 1 | 2 / 1 |
| 训练情节 | 8,192 | 0 | 8,192 |
| Adam 更新 | 512 | 0 | 512 |
| 评价情节 | 2,560 | 256 | 2,816 |
| 训练加评价联合 tick | 516,096 | 12,288 | 528,384 |
| 标量 Q 评分 | 1,138,688 | 0 | 1,138,688 |

新增规则有 4,096 次续约决策、12,288 次实际伙伴选择和 4,096 次规则内部伙伴预测，共 16,384 次标量伙伴选择；两周期重建 36,864 个到达 uniform 抽样及 256 个初始 h 抽样，均来自既定流。读取两个学习器共 512 个终点行，输出三个控制器共 768 个终点行及三组相关配对差。张量、数组、导入与发布成本不因“零 Q/零梯度”消失。这些是机器文件的前瞻计数，不是本轮实际完成量。[counts，proposed_if_option_A、totals_if_completion_succeeds][counts]

**120 秒覆盖这个新完整调用的全部链条：启动/导入、紧邻评价前的同节点新内存准入、输入读取、tape 重建、全部规则步、三比较发布/readback、元数据和退出。** 使用原 `wsl_4070` 与 `/home/wu/.venvs/hmasd/bin/python`、既有 detached `agent-task` 和 Root 观察；物理与有效可用内存均须新测得至少 4 GiB，准入失败则不进入科学工作。准入也在同一外层时钟内，不能把它、规则或发布移到预算外。本例外不允许资源重试、另换节点、改变输入或开启第四调用。[条件交接，第3、5项][handoff]；[compute 配置，nodes.wsl_4070][compute]；[AGENTS，§§5、7][agents]

原两调用完整 wall 为 6.52 与 4.84 秒，合计 11.36 秒；CPU 合计 8.58 秒。这里的“完整计时”包括失败 GENERIC 的完整进程寿命，不表示该任务成功。新专用调用 wall/CPU、修复与审阅耗时未知；120 秒是本次选择的 cap，不是旧余额或测得预测。机器文件的 `11.36+120=131.36` 只是已用调用 wall 加新 cap 的算术，不是 study elapsed、全部项目成本或新运行预报；合成检查和工程时间另计。无需追加成本实验来决定这次范围，也不能以旧调用很短保证补测可在 cap 内完成。[执行记录，Terminal, resource and exposure facts][execution]；[counts，cost_projection][counts]

在这一调用完成、具体失败或 120 秒上限处停止，不再追加规则评价、重新采样或自动修复调用。保留实际已达阶段和可信计数：若规则数据可信但后续联合发布失败，保留已得规则结果与尚缺发布，不把它重算一遍；若规则没有完成，就继续保留原 learner-only 证据。只缺资源遥测的部分记为 `resources_unmeasured`，不能回填原 GENERIC 缺失 RSS，也不能把真实准入失败当可忽略遥测。没有补测数据时不宣称累计达到 528,384 tick 或三控制器完整比较。[修订范围，Option A][scope]；[证据规范，§11.8.7][spec]

## 六、缺失观察怎样改变决定，预测如何保留

原主量始终是 Δ，规则对比只补齐原本并列的问题，不把新的比较改成一个能挽救 FACTOR 的替代主指标。[原卡，§5][card]

| 若补测得到的事实 | 有限读法与下一选择 |
| --- | --- |
| 规则不低于两学习器，或没有学习器获得相对规则的有用回报增益 | 保留小正 Δ，但本对象不给继续这项参数化比较提供实用理由；更倾向保留直接规则，不自动延长或另找相似宿主。不能宣布规则最优或学习永远无效。 |
| 至少一个学习器相对规则有清楚的 MEI 量级收益，且没有均值掩盖的实质周期损失 | 支持这个固定实例中学习政策相对该规则的用途；仍不满足 FACTOR 相对 GENERIC 的 MEI 条件。它可使后续考虑“学习政策与规则”的独立问题有依据，而不是自动扩大 FACTOR 的 seed 数；任何后续调用均未在这里选择。 |
| 只有一个周期有收益、另一期有损失，或参照比较靠近 MEI 且条件误差不足以分辨 | 保存每期原生代价与不确定性，不改权重、不删情节；本次停止，不追加样本去跨线。 |
| 规则或配对主依赖仍缺失/受损 | 只保留可独立相信的观察；原 Δ 不被撤销，未知规则值不当成负结果，也不宣布本次补测成功。 |

这组读法有信息价值，因为当前小 Δ 对未知的规则绝对水平没有定论。但它不会选择部署政策或证明 competence；LQ-EXCLUDE 只是一个透明合法的实用参照，不是调优 headroom、最优解或唯一合理调度器。若收益在原初始化就已存在，新增相对规则的读数也不能把整个差值归于 256 次学习。[原卡，§§1、3、5][card]

**原工作预测 `J_R≥min(J_F,J_G)` 保持，不重写。当前 J_R 缺失，仍不可评分。** 补测后若两个学习器均高于规则，按原指定读数记为不吻合，并报告条件误差；不能因 Δ 小而改成预测命中，也不要求出现 MEI 量级的反驳才承认方向预测失误。预测中的强 FACTOR-over-both 情形不可能由补一个规则值改变已知的 FACTOR−GENERIC 差；不用它制造新“通过”标准。所有者预测未取得，不代写。[原决定，§六][previous]；[原卡，§5][card]；[intake，§5][intake]

成功补齐最多得到原三队列、固定响应伙伴、两个持有时长和固定预算下，一个已训练政策对的局部比较。它不产生稳定优越、等价、负迁移原因、唯一乘性/共享因果、严格低秩收益、未见周期迁移、伙伴共适应、最优性或部署证据。真正的训练已经由原两次调用完成；本次零新增训练不需要伪装成一次独立算法训练实验，也不把真实规则评价伪装成零曝光文档工作。[证据规范，§§4、5.2、11.8–11.9][spec]

## 七、实际访问和最终边界

本次清单内 17 个证据路径均经 GitHub 连接器在固定版本 `5bf466820a2d17c07388a8499913aa265383d838` 成功访问。重点实际读取了修订/交接/计数全文，原卡及原答复受影响段落，E0、intake、分析字段，发布/实际规则/原 runner/相关 fixture 源码；规范按相关条款读取，包含完整 §§11.8–11.9。没有沿其中引用读取未列文件、可变 main、本地文件替代物或外部论文。原始远端 summary、日志和机器环境的实时状态没有在本轮独立取得；关于它们的观察明确依据清单内 E0、intake 与分析，不声称已经再验证运行或新修复。[execution][execution]；[intake][intake]；[analysis][analysis]；[scope][scope]；[handoff][handoff]

Issue 5 正文及六条既有评论实际读回并作交付查重；其中[原服务分配交付评论](https://github.com/CartmanFatass/My-paper-code/issues/5#issuecomment-5571198932)链接的是原决定，不是本修订。阅读阶段时钟观测为 2026-09-07 08:53:38 PDT（15:53:38 UTC）；与固定快照的 15:27:40 UTC 及原评论的 13:15:42 UTC 分开。评论不替代固定科学文件，也没有扩大修订权限。[固定 Issue 快照][snapshot]

本咨询新增模型初始化、优化、环境步、政策评价、RNG 或测试执行均为零；未实施修复、测试、资源准入或实验。原参数移动 FACTOR 2.103224039、GENERIC 1.003329992 是已读既有训练证据，补测不建模型，不需要另做 can-move 实验。[分析文件，initial_norms、final_displacements][analysis]；[counts，new_preparation_exposure][counts]

**最终选择只有 A 的一次 120 秒规则补测例外和与之对应的聚焦修复范围。当前三控制器赋值仍未完成，直到后来真实补测证据补齐才可改变该状态；原失败调用永不改判成功。双队列不追加、公开计划家族结束、A01/D6 历史边界、K4 开放及 Portfolio 权限均保持原义。**

[scope]: https://github.com/CartmanFatass/My-paper-code/blob/5bf466820a2d17c07388a8499913aa265383d838/docs/research/candidates/vsp_c1/pro_packets/20260907_service_allocation_completion_amendment/AMENDMENT_SCOPE.md
[handoff]: https://github.com/CartmanFatass/My-paper-code/blob/5bf466820a2d17c07388a8499913aa265383d838/docs/research/candidates/vsp_c1/pro_packets/20260907_service_allocation_completion_amendment/CM_REPAIR_HANDOFF.md
[counts]: https://github.com/CartmanFatass/My-paper-code/blob/5bf466820a2d17c07388a8499913aa265383d838/docs/research/candidates/vsp_c1/pro_packets/20260907_service_allocation_completion_amendment/COMPLETION_COUNTS.json
[card]: https://github.com/CartmanFatass/My-paper-code/blob/5bf466820a2d17c07388a8499913aa265383d838/docs/research/candidates/vsp_c1/VSPC1_K4_SERVICE_ALLOCATION_B01_SCIENCE_CARD_20260907.md
[previous]: https://github.com/CartmanFatass/My-paper-code/blob/5bf466820a2d17c07388a8499913aa265383d838/docs/research/candidates/vsp_c1/pro_packets/20260907_service_allocation_convergence/archive/RESPONSE.md
[execution]: https://github.com/CartmanFatass/My-paper-code/blob/5bf466820a2d17c07388a8499913aa265383d838/docs/research/candidates/vsp_c1/VSPC1_K4_SERVICE_ALLOCATION_B01_EXECUTION_20260907.md
[intake]: https://github.com/CartmanFatass/My-paper-code/blob/5bf466820a2d17c07388a8499913aa265383d838/docs/research/candidates/vsp_c1/VSPC1_K4_SERVICE_ALLOCATION_B01_INTAKE_20260907.md
[analysis]: https://github.com/CartmanFatass/My-paper-code/blob/5bf466820a2d17c07388a8499913aa265383d838/docs/research/candidates/vsp_c1/VSPC1_K4_SERVICE_ALLOCATION_B01_ANALYSIS_20260907.json
[reporting]: https://github.com/CartmanFatass/My-paper-code/blob/5bf466820a2d17c07388a8499913aa265383d838/experiments/candidates/vsp_c1/k4_service_allocation_b01/reporting.py
[experiment]: https://github.com/CartmanFatass/My-paper-code/blob/5bf466820a2d17c07388a8499913aa265383d838/experiments/candidates/vsp_c1/k4_service_allocation_b01/experiment.py
[runner]: https://github.com/CartmanFatass/My-paper-code/blob/5bf466820a2d17c07388a8499913aa265383d838/scripts/run_vspc1_k4_service_allocation_b01.py
[tests]: https://github.com/CartmanFatass/My-paper-code/blob/5bf466820a2d17c07388a8499913aa265383d838/tests/experiments/candidates/vsp_c1/k4_service_allocation_b01/test_contract.py
[spec]: https://github.com/CartmanFatass/My-paper-code/blob/5bf466820a2d17c07388a8499913aa265383d838/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[engineering]: https://github.com/CartmanFatass/My-paper-code/blob/5bf466820a2d17c07388a8499913aa265383d838/docs/project/ENGINEERING_SCOPE_SPEC.md
[agents]: https://github.com/CartmanFatass/My-paper-code/blob/5bf466820a2d17c07388a8499913aa265383d838/AGENTS.md
[compute]: https://github.com/CartmanFatass/My-paper-code/blob/5bf466820a2d17c07388a8499913aa265383d838/.codex/hmasd-compute.toml
[snapshot]: https://github.com/CartmanFatass/My-paper-code/blob/5bf466820a2d17c07388a8499913aa265383d838/docs/research/candidates/vsp_c1/pro_packets/20260907_service_allocation_completion_amendment/ISSUE_SNAPSHOT.json
