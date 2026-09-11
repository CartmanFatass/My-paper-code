**最终选择：暂停当前不变的 48 更新 RAW/STRUCT 直接回报比较家族，不再购买第三组同协议训练；本轮也不选择所提 192 更新备选或其他新实验。** 停止的最小单位是 `CBSC-DYNAMIC-CACHE-2R-1C-v1` 上、既有两种 adapter 与循环 PPO 配置、48 次 rollout 更新、固定 greedy 评价的这项重复比较。不是暂停全部直接回报研究，不是关闭 CBSC，不是机制 recast，也不改变 Portfolio 生命周期或优先级。

理由不是“两次零已经证明没有作用”，而是：两次真实独立配对运行不仅终点差值为零，而且在全部已记录的受训评价点上都呈现同一固定刷新行为。第二次运行已经完成了检验首次现象是否再次出现的有界任务。继续不变协议主要增加同一现象的重复次数；192 更新则是科学上允许、成本上具有可行依据的备选，但在当前证据下，我不把单纯延长同一学习过程选为下一笔投入。这是有不确定性的家族投资取舍，不是统计等价裁决或不可实施判定。[B02 intake「Separate next object」][5]、[B03 intake「Bounded interpretation」「Decisions this intake produces」][8]、[本轮提案「Concrete alternatives and their decision value」][1]。

## 一、当前结果是什么，而不是什么

两个对象的主量都是固定更新 48 处、同一运行内 32 个匹配评价 episode 的原生回报差均值：

\[
 d_{s,e}=R_{\mathrm{STRUCT},s,48,e}-R_{\mathrm{RAW},s,48,e},\qquad
 \widehat\Delta_s=\frac1{32}\sum_{e=0}^{31}d_{s,e}.
\]

下表是已发布的实际结果，不是本次重新执行模型所得。

| 独立配对运行 | 两臂各自的共同曲线：更新 0 / 12 / 24 / 48 | 终点 RAW / STRUCT | 32 个终点差值 | 同面板 ALWAYS_SAFE |
| --- | --- | --- | --- | --- |
| B02，21203 | 0.6875 / 10.7125 / 10.7125 / 10.7125 | 10.7125 / 10.7125 | 全部为 0 | 4.0625 |
| B03，21209 | 2.415625 / 10.5875 / 10.5875 / 10.5875 | 10.5875 / 10.5875 | 全部为 0 | 4.0375 |

每臂在更新 12、24、48 的每次评价中，都在全部 768 个机会选择 REFRESH；对应回报与同面板 ALWAYS_REFRESH 一致。因此，这里不是正负 episode 差值互相抵消形成均值零，而是相同公共 tape 上相同的已记录 greedy 动作产生相同原生结果。该观察只覆盖这些评价世界及 checkpoint，不能扩展为所有历史、所有状态或所有随机动作分布都相同。[B02 结果「Direct measurements」][4]、[B03 结果「Primary observation and run-level context」][7]、[B03 分析 `episode_differences`、`arms.curves`][9]。

既有 MEI 为每 episode 0.25 原生回报；两次观测差值均在其内。**“观测为零”不等于“总体效应已被夹在 ±0.25 内”。** 两运行描述性均值各为 10.65；配对差值的已观测样本标准差为零，只描述这两个值，不能产生零宽的总体不确定区间或稳定等价结论。独立单位是两次配对运行，不是四个臂、64 个评价 episode，或 512 次跨 checkpoint 评价执行。两 seed 同时改变初始化、训练随机性及程序生成的评价世界，不能把跨运行差异只归因于初始化。[两 seed 汇总 `unit`、`inference`、`paired_differences`][10]、[B03 卡「Why this one additional pair」][6]。

这也不是“优化器没运行”的零。每个正式臂都完成 48 次 rollout、768 次实际 Adam 更新、384 个新训练 episode、58,368 次训练转移及 9,216 个训练决策，并保留有限 loss、状态和主测量记录。初始相对参数位移如下；位移证明活动，不证明有用的条件动作已被学会。[曝光成本 `observed_formal_arms`][2]、[B03 CM 结果「Final complete pair and independent readback」][11]。

| 运行 | RAW 相对参数位移 | STRUCT 相对参数位移 |
| --- | ---: | ---: |
| 21203 | 19.6469845478% | 18.7238671667% |
| 21209 | 20.3270553056% | 18.6828676061% |

选择历史同样保留：B02 的正向预测未获支持；B03 事先弱预测再次落在 MEI 内并大量刷新，获得了这一次观察的支持。后者不能补救前者，也不能把第二次探索包装成预先独立于 B02 结果设计的确认研究。[B02 intake「Scientific reading and prediction」][5]、[B03 卡「Prediction, MEI, headroom and interpretation」][6]、[B03 intake「Evidence and rule applied」][8]。

## 二、暂停的依据、最强反证与残余不确定性

**支持暂停不变协议的最强证据，是重复的行为平台，而不只是终点均值零。** 两臂在两个运行中都已于首个受训评价点更新 12 呈现全刷新，后续更新 24 和 48 未在记录的 greedy 评价中产生分化。B03 的训练日志也显示行为集中：RAW 共采样 243 次 SERVE、8,515 次 REFRESH、458 次 SAFE；STRUCT 为 237、8,569、410。最后一批 RAW 为 191 次 REFRESH 加 1 次 SAFE，STRUCT 为 192 次 REFRESH。[B03 结果「Actual learning and actions」][7]、[B03 分析 `sampled_training_actions`、`last_update_sampled_actions`][9]。

这些事实排除了“训练从未采到其他动作”这种说法，但没有证明探索已充分、熵已严格为零、梯度消失、存在不可逃离的局部最优，或继续训练必定无效。固定 greedy 动作相同也不要求两臂 logits、随机策略概率或参数相同。当前可支持的表述是：**这个有限学习包在两次观察中学到了较初始化和 SAFE 更好的固定策略，却没有显示结构化表示的原生性能增益。** 它没有建立能有效利用当前性变化的强同信息对照；对照受限不使已测零差异失效，但限制了机制解释。[B02 结果][4]、[B03 结果][7]。

机制问题仍是 systems / information flow：一个学习控制器从公开的 ownership、semantic/content 与 capability 事件中形成接收者相关状态，再选择有原生决策和 settlement 后果的动作。两个 receiver 是环境实体，不是两个共同学习的 agent。RAW 接收完整公共历史及既有 FIFO；STRUCT 的额外关系表示是该历史的确定性加工。因此，RAW 是信息上的包含空假设，但不是已经证明在这个预算下达到最优的循环 PPO。不能用信息包含关系替代有限预算学习比较。[B03 卡「Learner, comparator, primary measurement and protected semantics」][6]、[本轮提案「The mechanism and the alternative explanations」][1]。

**反对现在暂停的最强理由也成立：** 直接路径已能提供可信主测量，实际调用成本不高，且较少的受训动作变化可能来自优化或探索限制，而不是表示没有潜在收益。一次对称训练干预或更长训练仍可能出现有用的原生差异。只因没有先前阳性、显著性、精确 upper 或唯一根因而拒绝这种 B，会违反当前证据规范。我不作这种拒绝，也不声称已估计其成功概率。[证据规范 §§5.2、11.8.2、11.9][20]。

但“还可能有改善”本身不能使每一个更长预算都成为必买的下一步。本次第二个 seed 已经提供了重复性信息；在受训 greedy 行为多次保持不变的情况下，我选择停止继续购买原协议，也不把四倍曝光作为自动补救。这一判断允许残余未知存在，不要求先证明暂停在所有未来结果下都最优。

历史证据只能提供边界，不能充当更多相同实验。exact factorial 在另一单机会对象上保留窄协议价值及 RAW 逐行相等；LR01 在其固定 24 块离线学习比较中有正负异质性，仍是 UNRESOLVED。它们既不能并入当前两个 seed 的样本量，也不能把当前局部零升级为“当前性无用”。LR01 文档中的旧生命周期建议不作为本轮处置依据。[exact factorial intake「Scientific interpretation and contradiction」][13]、[LR01 intake「Disposition」][14]、[DIRECTION 顶部当前证据与历史定义区分][12]。

## 三、192 更新备选：有意义且可能负担得起，但本轮不选

### 它实际能判别什么

这个备选不是第三次不变的 48 更新重复。它用一个新配对运行，保持两种表示、原生环境、模型和 PPO 不变，把每臂 rollout 从 48 增到 192，固定在 48 和 192 各评估 32 个世界。它可以观察：这条新训练轨迹在较长总曝光后，是否离开样本中的全刷新行为，以及更新 192 的 STRUCT-minus-RAW 原生回报是否出现差异。保留更新 48 提供同一轨迹的预算背景，无需挑最好 checkpoint。[本轮提案「One new bounded exposure comparison」][1]。

它不能单凭一个新运行把原因唯一归为优化剂量。每次 rollout 使用新 episode，故增加的既是环境数据，也是 optimizer 更新；它改变的是整个曝光包，而非在固定数据上单独增加 Adam 步。它也没有随机化多个训练预算组来估计总体预算因果效应。这些是措辞边界，**不是要求它扩张成多预算、多 seed 因果设计的理由**。其较窄的新预算性能问题本来就可以用普通 B 回答。[实际 runner `run_arm`][16]、[PPO `train_rollout`][18]。

### 主导工作和必要性

备选的主要工作可以直接写成：两臂 × 一个配对 seed × 192 次八 episode rollout；每个 rollout 做四 epoch × 四个双 episode minibatch 的完整循环训练，再加每臂两次 eval32。单个 episode 保留 152 次 primitive transition。没有候选策略搜索、联合动作枚举、未来轨迹分叉或重复 solver。两个 receiver 不产生一个需要枚举的多学习 agent 联合动作空间。[曝光成本 `unselected_192_update_alternative`][2]、[PPO 常量、`EpisodeRollout`、`train_rollout`][18]。

| 192 更新备选工作 | 每臂 | 两臂合计 |
| --- | ---: | ---: |
| 训练 episode | 1,536 | 3,072 |
| 训练转移 | 233,472 | 466,944 |
| 训练决策 | 36,864 | 73,728 |
| 实际 Adam 步 | 3,072 | 6,144 |
| 学习策略评价执行 | 64 | 128 |
| 评价转移 | 9,728 | 19,456 |
| 训练加评价转移 | 243,200 | 486,400 |

上述计数来自包内机器计算。RAW 的两个固定参照在既有 32 个评价世界上另做 64 次 ledger 计分，不产生新的独立训练样本。真实训练、必要评价、checkpoint 和主结果读回是算法观察的必要工作；旧十五表、历史重建、全 support 和政策搜索不是这个问题的必要验证。[曝光成本][2]。

只保留更新 48、192 而不再评估 0、12、24，是合理的主张缩小：不再声称完整早期学习曲线或最早分化时间，但最终原生表现及一个 48 更新背景仍然可读。它并不需要继承历史四臂、三 seed 的 B1b，也不需要先用精确、beam 或 best-of-many 搜索证明值得学习。当前问题不存在必须付费解决的组合搜索依赖；本轮不另选任何这样的诊断。[证据规范 §§11.8.1、11.8.6、11.9][20]。

### 成本依据与实际实现边界

现有四个正式完整调用合计 288.67 秒；B02 唯一的真实工程检查另为 6.97 秒。B03 没有新增仿真检查，其五个纯绑定检查另保守计 0.69 秒，当前记录的目录 focused 账为 132.15/300 秒。不能把测试消耗清零，也不能把这些量与控制面等待或聚合 CPU 混为一谈。[B02 结果「Complete execution cost and receipts」][4]、[B03 结果「Complete costs, receipts and evidence」][7]、[B03 CM 结果「Final source mapping and proportionate check」][11]。

| 臂 | B03 完整实测 wall | B03 host 生成 / 48 个更新区块实测秒数 | 包内 192 阶段外推 | 四倍 B02 整次调用场景 |
| --- | ---: | ---: | ---: | ---: |
| RAW | 59.53 s | 6.67605 / 48.33841 | 224.57 s | 318.76 s |
| STRUCT | 58.67 s | 7.10284 / 48.31928 | 224.94 s | 363.12 s |

阶段外推使用 `T48 + 3 × (host + 48-update sum)`，把其他完整调用成本保持不变，不另外计入删去两次评价的节省。四倍整次 B02 只是另一粗场景。**两者都不是实测新运行、保证上界、统计区间或加速比。** 状态与动作、host 构造、序列化、运行负载和更大预生成 tape 集合的实际成本仍有不确定性。现有数据足以讨论这个投资，不需要为本次决策另开 profiling 或校准实验。[B03 分析 `arms.cost`][9]、[曝光成本 `projection_formula`、`projections`、`uncertainty`][2]。

所提完整 cap 仍是每臂 600 秒、最多两个正式调用，包含 admission、启动、host、训练、评价、checkpoint、发布读回、STRUCT 配对及结束宽限。已有投影没有给出超限拒绝依据；不能把本轮不选说成算力不足。也不能把 288.67 秒说成 study elapsed 或 aggregate CPU，更不能据 B03 比 B02 快就声称 C++、batching 或 GPU 加速。[曝光成本][2]、[runtime 规范一般要求 §§1–7][22]。

实际源码支持一种较小的 profile 修改，但尚不存在可直接调用的 192 模式：`direct_return_b02.py::run_arm` 的正式值仍写为 `(48,32)` 与 `(0,12,24,48)`，`expected_seed` 只绑定 B02/B03；CLI 仅提供现有对象、seed、arm、输出及 RAW 结果参数。`native_record` 已使用 `Action[name]` 并核对 decision 加 settlement；`pair_results` 已计算最终 episode 差值。故不需要复活旧发布系统，但仍需一个明示的新 profile，而不能臆造现成的 `--updates 192` 接口。PPO 本身按连续新 episode ID 更新计数，当前配置验证严格限制其参数；改变熵或 GAE 不是现有 CLI 的自由选项。[直接 runner `expected_seed`、`native_record`、`pair_results`、`run_arm`][16]、[CLI `main`][17]、[PPO `PPOConfig`、`train_rollout`][18]。

**不选 192 的决定性理由是本轮的边际判别价值，而不是它缺少精确解释或尚未实现。** 它有一个合法的“更长曝光能否改变行为”问题，却继续沿用两个运行中已出现行为平台的训练包。现有事实没有证明延长无效，也没有提供比“也许晚一些会变”更具体的支持。面对当前是否继续购买这项比较的选择，我倾向保留这个未知而停止投入。成本较低使这一取舍值得承认不确定性，但不会单独使其成为必须执行的实验。拒绝的是这一次投资，不是把 192 或任何预算改动永久列为不允许。

## 四、暂停边界与真正有价值的下一判别

此次家族暂停覆盖：同一动态 host、同一完整公共信息、原 RAW FIFO 与 STRUCT currentness adapter、原 CPU FP32 循环 PPO、48 个八 episode rollout，以及更新 48 的 greedy stochastic-panel 原生回报比较。**只换 seed 或外层对象名字，仍是这个不变协议的续购，本轮不再选择。** B02/B03 均保持完整有效的局部 B 结果；没有新源码任务、第三组训练、192 延长、历史发布重试或精确诊断获得本次选择。此处没有 C 式“消费后不得研究”的含义。[B03 卡停止边界][6]、[B03 intake][8]、[证据规范 §5.2、§11.8][20]。

暂停不覆盖所有新的当前性学习问题，也不以先取得阳性、强基线认证、精确 headroom 或根因证明作为重新提出 B 的条件。更值得日后提出的判别是：**一个有明确学习理由、只改变一个训练环节并对 RAW/STRUCT 对称实施的新比较，是否改变固定刷新的受训行为及其完整原生回报；表示差异是否随之出现。** 其理由可以直接来自这里的行为集中现象，不需要先证明“探索不足”是唯一原因。

这句话是下一问题的边界，不是暗中选择某个熵系数、GAE 改法、host 重写或新的 seed。现有资料不足以在这些改动之间指定一种“已知会有效”的措施；本轮也不把它们展开成超参数或策略搜索。以后若形成一个具体实现方案，应直接比较实际学习策略的固定终点 native return，并并列两臂绝对回报、动作分布及便宜的同面板参照。只出现更多 SERVE、较高熵、decoder 改善或更大参数位移，不能替代原生表现；改变宿主分布或奖励时，则是新问题，必须保留旧零且明确新的比较含义。[本轮提案「Convergence may instead select」][1]、[证据规范 §§4、5.2、11.8.2、11.9][20]。

一个对称改动下的新两臂比较，只能判断那个新训练包里的表示对比；没有额外干预设计时，不声称它唯一定位了旧故障或估计了该改动的总体因果效应。也不要求两臂先胜过固定刷新才能运行或保留结果。新鲜配对运行若值得选择，正、零、负都应完整进入 intake；是否再购买一至两个独立 seed 由那次问题及观察决定，不运行到每个符号都转正。这是正常 B 迭代，不新增审批或分析服务。[证据规范 §§11.8.2–11.8.4、11.9][20]。

当前无需再计算一个置信区间来决定暂停。已有 `summarize_runs.py` 产物明确以训练运行为单位并只作描述，足够报告本轮证据。更多 episode、同 checkpoint 重评或对两个零反复 bootstrap，都不能补出新的训练重复；本次不调用新的统计、数值或 profiling 工具。[两 seed 汇总][10]。

## 五、继续保留的科学责任和未知

直接路径成功只支持 B02/B03 的这些执行。旧 SIGSEGV 和随后不同 TypeError 的根因仍未知，原 B1/r05 隔离与完整旧发布缺口不变；不会因本次暂停而修复，也不会因新路径成功而消失。另一方面，既有调用没有已报告的主要回报、公共信息、真实训练或配对缺陷，不能仅凭历史异常撤销当前完整局部零。[B02 Pro intake「Scientific support, contradiction and retained history」][15]、[B02 结果末段][4]、[B03 CM 结果][11]。

未来合适的新 B 仍要保护实际 host 与合法动作、同信息比较、原生 decision 加 delayed-settlement 回报、真实环境/optimizer 工作以及可读主测量。已有可信路径的检查可以复用；只对实际改变的行为和主输出作相称验证，不在每个新 launch 重跑仿真 smoke。逐实际调用资源准入和完整预算不变，普通 2,000 行源码、600 行 runner 与既有测试账不因换名重置；30% 编排比例仅作审查信号。这里没有请求或默许规范例外。[证据规范 §§11.4、11.8.6–11.8.8][20]、[工程 scope §§3–5][21]。

不要求旧十五表、motif/twin、全 support、PI/DERANGED 重建或跨平台逐位相等，是因为本轮及所讨论的新两臂性能问题不主张相应更强结论。**语义特异性、排除 generic conditioning 或 PI/DERANGED、稳定等价、最优固定策略、一般 MARL 协作、变量人口以及 UAV 迁移，均不在证据上限内。** 缺少 tuned generic/upper headroom 继续记为未知，而不是零，也不是暂停理由。[B03 卡「Claim ceiling」及预测章节][6]、[证据规范 §§11.7–11.9][20]。

本轮的科学更新至此为止：两个独立配对运行在声明预算和评价世界上重复了零表示差异与固定刷新；该不变协议不再获得当前续购。潜在的有限学习表示收益、较长曝光结果、最佳训练改动及历史异常原因仍未被决定。减少无关诊断不是机制 recast；此次选择更没有改变机制命题。[AGENTS §2][19]、[证据规范 §11.8.8][20]。

## 六、实际证据读取范围

科研文件均通过连接的 GitHub 按固定版本 `09664be0bb9d8ff843ce70389764c10e779e4b64` 读取。22 个列明证据路径均可访问；下表区分全文与实际节选。数字、核对结果和运行事实来自列明的结果文档及机器分析，不宣称本节点重新载入 checkpoint、复跑模型或独立复算未列明原始文件。本轮新增训练、Adam 更新、评价执行、搜索与参数位移测量均为零。

表中 `D/` 为 `docs/research/candidates/capability_bound_semantic_currentness/`，`P/` 为其 `pro_packets/20260905_two_seed_family_convergence/`。每个链接都定位同一固定版本。

| 证据路径 | 实际读取范围 |
| --- | --- |
| [P/EVIDENCE_AND_OPTIONS.md][1] | 全文 |
| [P/EXPOSURE_AND_COST.json][2] | 全文 |
| [P/ISSUE_SNAPSHOT.json][3] | 全文 |
| [D/CBSC_DIRECT_RETURN_B02_RESULT_EVIDENCE_20260905.md][4] | 全文 |
| [D/CBSC_DIRECT_RETURN_B02_INTAKE_20260905.md][5] | 全文 |
| [D/CBSC_DIRECT_RETURN_B03_SCIENCE_CARD_20260905.md][6] | 全文 |
| [D/CBSC_DIRECT_RETURN_B03_RESULT_EVIDENCE_20260905.md][7] | 全文 |
| [D/CBSC_DIRECT_RETURN_B03_INTAKE_20260905.md][8] | 全文 |
| [D/CBSC_DIRECT_RETURN_B03_DM_ANALYSIS_20260905.json][9] | 全文 |
| [D/CBSC_DIRECT_RETURN_TWO_SEED_SUMMARY_20260905.json][10] | 全文 |
| [D/CBSC_DIRECT_RETURN_B03_CM_RESULT_20260905.md][11] | 全文 |
| [D/DIRECTION.md][12] | 第 1–190 行，含顶部当前证据及历史边界 |
| [D/CBSC_EXACT_FACTORIAL_RESULT_INTAKE_20260830.md][13] | 全文 |
| [D/CBSC_LR01_RESULT_INTAKE_20260831.md][14] | 全文 |
| [D/CBSC_DIRECT_RETURN_B02_PRO_INTAKE_20260905.md][15] | 全文 |
| [experiments/candidates/capability_bound_semantic_currentness/direct_return_b02.py][16] | 全文 |
| [scripts/run_cbsc_direct_return_b02.py][17] | 全文 |
| [experiments/candidates/capability_bound_semantic_currentness/omrc_b01/ppo.py][18] | 全文，分段读取 |
| [AGENTS.md][19] | 第 1–125 行，重点 §§1–3 |
| [docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md][20] | 第 1–145 行、第 230 行至末尾；含 §§4、5.2、11.4、11.8、11.9 |
| [docs/project/ENGINEERING_SCOPE_SPEC.md][21] | 第 1–115 行，含普通 §§3–5；未展开历史对象附款 |
| [docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md][22] | 一般要求 §§1–7 及 §8 开头；未展开其他方向附款 |

另按清单读取了可变的 [Issue 7 正文及评论列表][23]。交付前本次核对时间约为 2026 年 9 月 5 日 18:30 PDT，即 9 月 6 日 01:30 UTC。正文与固定 `ISSUE_SNAPSHOT.json` 的实质内容一致，评论列表当时为空，因此没有已有评论链接或额外讨论证据可引用。Issue 自报更新时间为 2026-09-06T01:12:37Z，是讨论元数据，不是此次查阅时间或新的实验时间。没有沿正文中的其他版本链接替换固定证据，也未扩展科研读取至清单外源码、原始输出目录或外部论文。

[1]: https://github.com/CartmanFatass/My-paper-code/blob/09664be0bb9d8ff843ce70389764c10e779e4b64/docs/research/candidates/capability_bound_semantic_currentness/pro_packets/20260905_two_seed_family_convergence/EVIDENCE_AND_OPTIONS.md
[2]: https://github.com/CartmanFatass/My-paper-code/blob/09664be0bb9d8ff843ce70389764c10e779e4b64/docs/research/candidates/capability_bound_semantic_currentness/pro_packets/20260905_two_seed_family_convergence/EXPOSURE_AND_COST.json
[3]: https://github.com/CartmanFatass/My-paper-code/blob/09664be0bb9d8ff843ce70389764c10e779e4b64/docs/research/candidates/capability_bound_semantic_currentness/pro_packets/20260905_two_seed_family_convergence/ISSUE_SNAPSHOT.json
[4]: https://github.com/CartmanFatass/My-paper-code/blob/09664be0bb9d8ff843ce70389764c10e779e4b64/docs/research/candidates/capability_bound_semantic_currentness/CBSC_DIRECT_RETURN_B02_RESULT_EVIDENCE_20260905.md
[5]: https://github.com/CartmanFatass/My-paper-code/blob/09664be0bb9d8ff843ce70389764c10e779e4b64/docs/research/candidates/capability_bound_semantic_currentness/CBSC_DIRECT_RETURN_B02_INTAKE_20260905.md
[6]: https://github.com/CartmanFatass/My-paper-code/blob/09664be0bb9d8ff843ce70389764c10e779e4b64/docs/research/candidates/capability_bound_semantic_currentness/CBSC_DIRECT_RETURN_B03_SCIENCE_CARD_20260905.md
[7]: https://github.com/CartmanFatass/My-paper-code/blob/09664be0bb9d8ff843ce70389764c10e779e4b64/docs/research/candidates/capability_bound_semantic_currentness/CBSC_DIRECT_RETURN_B03_RESULT_EVIDENCE_20260905.md
[8]: https://github.com/CartmanFatass/My-paper-code/blob/09664be0bb9d8ff843ce70389764c10e779e4b64/docs/research/candidates/capability_bound_semantic_currentness/CBSC_DIRECT_RETURN_B03_INTAKE_20260905.md
[9]: https://github.com/CartmanFatass/My-paper-code/blob/09664be0bb9d8ff843ce70389764c10e779e4b64/docs/research/candidates/capability_bound_semantic_currentness/CBSC_DIRECT_RETURN_B03_DM_ANALYSIS_20260905.json
[10]: https://github.com/CartmanFatass/My-paper-code/blob/09664be0bb9d8ff843ce70389764c10e779e4b64/docs/research/candidates/capability_bound_semantic_currentness/CBSC_DIRECT_RETURN_TWO_SEED_SUMMARY_20260905.json
[11]: https://github.com/CartmanFatass/My-paper-code/blob/09664be0bb9d8ff843ce70389764c10e779e4b64/docs/research/candidates/capability_bound_semantic_currentness/CBSC_DIRECT_RETURN_B03_CM_RESULT_20260905.md
[12]: https://github.com/CartmanFatass/My-paper-code/blob/09664be0bb9d8ff843ce70389764c10e779e4b64/docs/research/candidates/capability_bound_semantic_currentness/DIRECTION.md
[13]: https://github.com/CartmanFatass/My-paper-code/blob/09664be0bb9d8ff843ce70389764c10e779e4b64/docs/research/candidates/capability_bound_semantic_currentness/CBSC_EXACT_FACTORIAL_RESULT_INTAKE_20260830.md
[14]: https://github.com/CartmanFatass/My-paper-code/blob/09664be0bb9d8ff843ce70389764c10e779e4b64/docs/research/candidates/capability_bound_semantic_currentness/CBSC_LR01_RESULT_INTAKE_20260831.md
[15]: https://github.com/CartmanFatass/My-paper-code/blob/09664be0bb9d8ff843ce70389764c10e779e4b64/docs/research/candidates/capability_bound_semantic_currentness/CBSC_DIRECT_RETURN_B02_PRO_INTAKE_20260905.md
[16]: https://github.com/CartmanFatass/My-paper-code/blob/09664be0bb9d8ff843ce70389764c10e779e4b64/experiments/candidates/capability_bound_semantic_currentness/direct_return_b02.py
[17]: https://github.com/CartmanFatass/My-paper-code/blob/09664be0bb9d8ff843ce70389764c10e779e4b64/scripts/run_cbsc_direct_return_b02.py
[18]: https://github.com/CartmanFatass/My-paper-code/blob/09664be0bb9d8ff843ce70389764c10e779e4b64/experiments/candidates/capability_bound_semantic_currentness/omrc_b01/ppo.py
[19]: https://github.com/CartmanFatass/My-paper-code/blob/09664be0bb9d8ff843ce70389764c10e779e4b64/AGENTS.md
[20]: https://github.com/CartmanFatass/My-paper-code/blob/09664be0bb9d8ff843ce70389764c10e779e4b64/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[21]: https://github.com/CartmanFatass/My-paper-code/blob/09664be0bb9d8ff843ce70389764c10e779e4b64/docs/project/ENGINEERING_SCOPE_SPEC.md
[22]: https://github.com/CartmanFatass/My-paper-code/blob/09664be0bb9d8ff843ce70389764c10e779e4b64/docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md
[23]: https://github.com/CartmanFatass/My-paper-code/issues/7
